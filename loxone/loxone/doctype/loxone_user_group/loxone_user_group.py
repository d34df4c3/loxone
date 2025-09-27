# Copyright (c) 2025, Julien Becker and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from loxone import logger
from loxone.loxone.doctype.loxone_miniserver.loxone_miniserver import LoxoneMiniserver

from typing import cast

class LoxoneUserGroup(Document):
	# begin: auto-generated types
	# ruff: noqa

	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from loxone.loxone.doctype.loxone_link_group_bookingresource.loxone_link_group_bookingresource import LoxoneLinkGroupBookingResource

		lx_auto_assign: DF.Check
		lx_booking_resources: DF.Table[LoxoneLinkGroupBookingResource]
		lx_description: DF.Data | None
		lx_miniserver: DF.Link
		lx_name: DF.Data | None
		lx_uuid: DF.Data
	# ruff: noqa
	# end: auto-generated types


	def on_trash(self) -> None:
		"""Handle cleanup when the Loxone User Group document is deleted."""
		logger.info(f"LoxoneUserGroup - Deleting Loxone User Group: {self.lx_name} ({self.name})")

		if not getattr(self.flags, 'triggered_by_loxone', False):
			frappe.throw(
				title="Deletion Error",
				msg=f"The user group ({self.lx_name}) is not managed by Dokos.<br/>It can only be deleted by the MiniServer."
			)
				
	@staticmethod
	def get_doc(name: str) -> "LoxoneUserGroup":
		"""Get a LoxoneUserGroup document by name."""
		return cast(LoxoneUserGroup, frappe.get_doc("Loxone User Group", name))

def load_user_groups_from_miniserver(ms_doc: LoxoneMiniserver) -> None:
	"""Load user groups from the MiniServer."""
	from loxone.loxone.doctype.loxone_user_group.mapper import LoxoneUserGroupMapper
	logger.info(f"LoxoneUserGroup - Loading user groups from MiniServer: {ms_doc.name}")

	ms = ms_doc.get_miniserver()
	user_groups = ms.get_user_groups()

	for group in user_groups:
		if group.get('type') == 4:  # Ignore system groups
			logger.info(f"LoxoneUserGroup - Skipping admin group: {group['name']}")
			continue

		doc_name = frappe.db.exists("Loxone User Group", {"lx_miniserver": ms_doc.name, "lx_uuid": group.get('uuid')})
		if doc_name is None:
			doc = cast(LoxoneUserGroup, frappe.new_doc("Loxone User Group"))
			doc.flags.triggered_by_loxone = True
			LoxoneUserGroupMapper(doc, ms_doc).load(group)
			doc.insert()
			logger.info(f"LoxoneUserGroup - New group: {doc.lx_name}")
		else:
			doc = cast(LoxoneUserGroup, frappe.get_doc("Loxone User Group", str(doc_name)))
			doc.flags.triggered_by_loxone = True
			LoxoneUserGroupMapper(doc, ms_doc).load(group)
			doc.save()
			logger.info(f"LoxoneUserGroup - Updated group: {doc.lx_name}")

def delete_all(ms_name: str) -> None:
	"""Delete all Loxone User Groups for a given MiniServer."""
	user_groups = frappe.get_all("Loxone User Group", filters={"lx_miniserver": ms_name})
	for group in user_groups:
		group_doc = LoxoneUserGroup.get_doc(group.name)
		group_doc.flags.triggered_by_loxone = True
		group_doc.delete()
		logger.info(f"LoxoneUserGroup - Deleted: {group_doc.lx_name} ({group_doc.name})")