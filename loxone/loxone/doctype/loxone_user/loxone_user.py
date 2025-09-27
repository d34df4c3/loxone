# Copyright (c) 2025, Julien Becker and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from loxone import logger
from loxone.loxone.doctype.loxone_miniserver.loxone_miniserver import LoxoneMiniserver

from typing import cast
from loxone.api.MiniServer import MiniServer

class LoxoneUser(Document):
	# begin: auto-generated types
	# ruff: noqa

	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from loxone.loxone.doctype.loxone_link_user_group.loxone_link_user_group import LoxoneLinkUserGroup

		lx_dokos_user: DF.Link | None
		lx_groups: DF.Table[LoxoneLinkUserGroup]
		lx_keycode: DF.Data | None
		lx_managed_by_dokos: DF.Check
		lx_miniserver: DF.Link
		lx_name: DF.Data
		lx_state: DF.Literal["0 - Permanent", "1 - Disabled", "2 - Enabled Until", "3 - Enabled From", "4 - Time-Dependent"]
		lx_uuid: DF.Data
		lx_valid_from: DF.Datetime | None
		lx_valid_until: DF.Datetime | None
	# ruff: noqa
	# end: auto-generated types


	########## Hooks ##########
	def before_validate(self) -> None:
		if getattr(self.flags, 'triggered_by_loxone', False):
			# If the user is created by Loxone, we do not want to validate the insert method.
			# This is to prevent the user from being created again on the Miniserver.
			return
		
		if getattr(self.flags, 'in_insert', False):
			create_user_in_miniserver(self)
			return

	def on_update(self) -> None:
		if getattr(self.flags, 'triggered_by_loxone', False):
			# If the user is updated by Loxone, we do not want to update the Miniserver.
			# This is to prevent the user from being updated again on the Miniserver.
			return

		if not self.lx_managed_by_dokos:
			frappe.throw(
				title="Update Error",
				msg=f"The user ({self.lx_name}) is not managed by Dokos.<br/>It can only be updated by the MiniServer."
			)

		save_user_in_miniserver(self)

	def on_trash(self) -> None:
		"""Handle cleanup when the Loxone User document is deleted."""
		if not self.lx_managed_by_dokos:
			return

		delete_user_from_miniserver(self)
		logger.info(f"LoxoneUser - Deleting: {self.name}")

	@staticmethod
	def get_doc(name: str) -> "LoxoneUser":
		"""Get a LoxoneUser document by name."""
		return cast(LoxoneUser, frappe.get_doc("Loxone User", name))


def load_users_from_miniserver(ms_doc: LoxoneMiniserver) -> None:
	"""Load users from the MiniServer and create/update LoxoneUser documents."""
	logger.info(f"LoxoneUser - Loading users from MiniServer: {ms_doc.name}")

	ms = ms_doc.get_miniserver()
	users = ms.get_users()

	# Create/Update existing users
	for user in users:
		if user.get('isAdmin', False):
			logger.info(f"LoxoneUser - Skipping admin user: {user['name']}")
			continue

		user_details = ms.get_user(user['uuid'])
		user_doc_name = frappe.db.exists("Loxone User", {"lx_miniserver": ms_doc.name, "lx_uuid": user['uuid']})
		if not user_doc_name:
			create_user_from_miniserver(ms_doc, user_details)
		else:
			update_user_from_miniserver(ms_doc, str(user_doc_name), user_details)

	# Delete users that are not in the MiniServer anymore
	expected_uuid = [u['uuid'] for u in users]
	user_doc_to_delete = frappe.get_list('Loxone User',
		filters={
			'lx_miniserver': ms_doc.name,
			'lx_uuid': ['not in', expected_uuid]
		},
		pluck='name')

	for doc_name in user_doc_to_delete:
		doc = LoxoneUser.get_doc(doc_name)
		doc.flags.triggered_by_loxone = True
		doc.delete()
		logger.info(f"LoxoneUser - Deleted user: {doc.lx_name} ({doc.name})")	

def create_user_from_miniserver(ms_doc: LoxoneMiniserver, user_details: dict) -> None:
	from loxone.loxone.doctype.loxone_user.mapper import LoxoneUserMapper

	logger.debug(f"LoxoneUser - Creating user: {user_details}")
	doc = cast(LoxoneUser, frappe.new_doc("Loxone User"))
	doc.flags.triggered_by_loxone = True
	doc.lx_managed_by_dokos = 0
	LoxoneUserMapper(doc, ms_doc).load(user_details)
	doc.insert()
	logger.info(f"LoxoneUser - New user: {doc.lx_name}")

def update_user_from_miniserver(ms_doc: LoxoneMiniserver, user_doc_name: str, user_details: dict) -> None:
	from loxone.loxone.doctype.loxone_user.mapper import LoxoneUserMapper

	logger.debug(f"LoxoneUser - Updating user: {user_details}")
	doc = LoxoneUser.get_doc(user_doc_name)
	doc.flags.triggered_by_loxone = True
	LoxoneUserMapper(doc, ms_doc).load(user_details)
	doc.save()
	logger.info(f"LoxoneUser - Updated user: {doc.lx_name}")

def create_user_in_miniserver(doc: LoxoneUser) -> None:
	# Create user on Miniserver
	ms_doc = LoxoneMiniserver.get_doc(doc.lx_miniserver)
	ms = ms_doc.get_miniserver()
	uuid = ms.create_user(doc.lx_name)
	if uuid is None:
		frappe.throw(f"Failed to create user '{doc.lx_name}' on MiniServer '{doc.lx_miniserver}'.")
	doc.lx_uuid = uuid

	# Ensure user is created and name has not changed, otherwise update the name
	user_details = ms.get_user(uuid)
	if user_details['name'] != doc.lx_name:
		logger.warning(f"LoxoneUser - Create User - User name mismatch: expected '{doc.lx_name}', got '{user_details['name']}' from Miniserver. Updating Dokos name.")
		doc.lx_name = user_details['name']

	# Assign keycode
	if ms_doc.lx_auto_assign_keycode:
		logger.info(f"LoxoneUser - Assigning keycode to user {doc.lx_name} on Miniserver")
		doc.lx_keycode = generate_keycode_in_miniserver(ms, uuid)

def generate_keycode_in_miniserver(ms: MiniServer, uuid: str, attempts: int = 15) -> str:
	"""Generate a unique keycode for the user on the MiniServer.
		Attempts to generate a keycode up to the specified number of attempts.
		Args:
			uuid (str): The UUID of the user to assign the keycode to.
			attempts (int): Number of attempts to generate a unique keycode.
		Returns:
			str: The generated unique keycode.
		Raises:
			frappe.ValidationError: If a unique keycode cannot be generated after the specified attempts.
	"""
	import random
	import time

	while attempts > 0:
		keycode = "{:06d}".format(random.randint(0, 999999))
		success = ms.set_keycode(uuid, keycode)

		if not success:
			attempts -= 1
			logger.warning(f"LoxoneUser - Keycode {keycode} already exists on Miniserver. Remaining attempts: {attempts}.")
			time.sleep(1)
		else:
			logger.info(f"LoxoneUser - Successfully generated unique keycode {keycode} for user {uuid}.")
			return keycode

	logger.error(f"LoxoneUser - Failed to generate unique keycode for user {uuid} after multiple attempts.")
	frappe.throw(f"Failed to generate unique keycode for user {uuid} after multiple attempts. Please try again.")

def save_user_in_miniserver(doc: LoxoneUser) -> None:
	from loxone.loxone.doctype.loxone_user.mapper import LoxoneUserSerializer

	# Update global fields
	user_dict = LoxoneUserSerializer(doc).serialize()
	logger.info(f"LoxoneUser - Updating Loxone User on Miniserver: {user_dict}")
	ms = LoxoneMiniserver.get_doc(doc.lx_miniserver).get_miniserver()
	ms.update_user(user_dict)

	# Sync the user groups
	expected_uuids = frappe.get_list('Loxone User Group',
			filters={'name': ['in', [g.lx_group_id for g in doc.lx_groups]]},
			pluck='lx_uuid'
		)
	actual_uuids = [g['uuid'] for g in ms.get_user(doc.lx_uuid).get('usergroups', [])]

	for group_uuid in set(actual_uuids) - set(expected_uuids):
		logger.info(f"LoxoneUser - Removing user group {group_uuid} from user {doc.lx_name} on Miniserver")
		ms.remove_user_from_group(doc.lx_uuid, group_uuid)

	for group_uuid in set(expected_uuids) - set(actual_uuids):
		logger.info(f"LoxoneUser - Adding user group {group_uuid} to user {doc.lx_name} on Miniserver")
		ms.assign_user_to_group(doc.lx_uuid, group_uuid)

def delete_all(ms_name: str) -> None:
	"""Delete all Loxone Users for a given MiniServer."""
	users = frappe.get_all("Loxone User", filters={"lx_miniserver": ms_name})
	for user in users:
		user_doc = LoxoneUser.get_doc(user.name)
		user_doc.flags.triggered_by_loxone = True
		user_doc.delete()
		logger.info(f"LoxoneUser - Deleted: {user_doc.lx_name} ({user_doc.name})")

def delete_user_from_miniserver(doc: LoxoneUser) -> None:
	"""Delete the Loxone User from the MiniServer."""
	ms = LoxoneMiniserver.get_doc(doc.lx_miniserver).get_miniserver()
	ms.delete_user(doc.lx_uuid)