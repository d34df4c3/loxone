# Copyright (c) 2025, Julien Becker and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from loxone.api.MiniServer import MiniServer
from loxone.api import MiniServer
from frappe.utils import now
from loxone import logger
import frappe
from typing import cast

class Miniserver(Document):
	# begin: auto-generated types
	# ruff: noqa

	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		lx_auto_assign_keycode: DF.Check
		lx_auto_create_user: DF.Check
		lx_auto_enable_user: DF.Check
		lx_conn_password: DF.Data
		lx_conn_url: DF.Data
		lx_conn_user: DF.Data
		lx_loxapp3: DF.JSON
		lx_loxapp3_dt: DF.Datetime | None
		lx_name: DF.Data
		lx_serial: DF.Data
	# ruff: noqa
	# end: auto-generated types


	########## Cache properties ##########
	__miniserver: MiniServer.MiniServer | None = None

	########## Hooks ##########
	def before_validate(self) -> None:	
		if getattr(self.flags, 'in_insert', False):
			self.on_update_url()
			return

		old_doc = cast('Miniserver', self.get_doc_before_save())
		if old_doc.lx_conn_url != self.lx_conn_url:
			self.on_update_url()

	def validate(self):
		old_doc = cast('Miniserver', self.get_doc_before_save())
		validate_serial(self, old_doc)

	def on_trash(self):
		"""Handle cleanup when the Miniserver document is deleted."""
		logger.info(f"Deleting Miniserver: {self.lx_name} ({self.name})")

		# Delete LoxoneUser
		import loxone.loxone.doctype.loxone_user.loxone_user as loxone_user
		loxone_user.delete_all(self.name) # type: ignore

		# Delete LoxoneGroup
		import loxone.loxone.doctype.loxone_user_group.loxone_user_group as loxone_user_group
		loxone_user_group.delete_all(self.name) # type: ignore

		# Delete NFC Code Touch Device
		import loxone.loxone.doctype.nfc_code_touch_device.nfc_code_touch_device as nfc_code_touch_device
		nfc_code_touch_device.delete_all(self.name) # type: ignore

	def on_update_url(self) -> None:
		"""Update the URL of the Miniserver."""
		validate_url(self.lx_conn_url)
		validate_connectivity(self.lx_conn_url, self.lx_conn_user, self.lx_conn_password)

		ms = self.get_miniserver(True)

		import json
		self.lx_name = ms.name
		self.lx_serial = ms.serial_number
		self.lx_loxapp3 = json.dumps(ms.loxapp3(), indent=4)
		self.lx_loxapp3_dt = now()

		frappe.msgprint(
			title="MiniServer",
			msg=f"Connected to MiniServer '{self.lx_name}' ('{self.lx_serial}').",
			indicator="green"
		)

	def get_miniserver(self, load_loxapp3 = False) -> MiniServer.MiniServer:
		ms = self.__miniserver or MiniServer.get_instance(self.lx_conn_url, self.lx_conn_user, self.lx_conn_password)

		if load_loxapp3 and not ms.is_loaded():
			ms.load()

		self.__miniserver = ms
		return ms
	
	@staticmethod
	def get_doc(name: str) -> "Miniserver":
		"""Get a Miniserver document by name."""
		return cast(Miniserver, frappe.get_doc("Miniserver", name))


def validate_url(url: str) -> None:
	if not url:
		frappe.throw("Connection URL cannot be empty.")

	from urllib.parse import urlparse
	parsed_url = urlparse(url)
	if not parsed_url.scheme or not parsed_url.netloc:
		frappe.throw(
			title= "Invalid URL format.",
			msg="Please provide a valid URL including scheme (http/https) and netloc (domain or IP), and optionally a port number.<br/><br/>" \
				"Example: http://example.com:8080"
		)

def validate_connectivity(url: str, user: str, password: str) -> str:
    """Check if the connection to the Loxone Miniserver is valid."""
    return MiniServer.get_instance(url, user, password).get_status()


def validate_serial(doc: Miniserver, old_doc: Miniserver | None) -> None:
	# If this is a new Miniserver, we need to check if the serial number is unique.
	if old_doc is None and frappe.db.exists("Miniserver", {"lx_serial": doc.lx_serial}):
		frappe.throw(
			title="Duplicate Serial Number",
			msg=f"A Miniserver with serial '{doc.lx_serial}' already exists."
		)

	# If the serial number has changed, raise an error.
	if old_doc and doc.lx_serial != old_doc.lx_serial:
		frappe.throw(
			title="Serial Number Change",
			msg=f"Cannot change the serial number of a Miniserver. Old: {old_doc.lx_serial}, New: {doc.lx_serial}"
		)

def create_or_update_devices(ms_doc: Miniserver) -> None:
	"""Create or update devices based on the MiniServer configuration."""

	create_or_update_nfc_code_touch_devices(ms_doc)
	nfcs = ms_doc.get_miniserver(True).get_nfc_code_touches()
	msg = f"Devices detected: {len(nfcs)} NFC Code Touch devices:" \
		"<ul>" + \
		"".join([f"<li>{nfc.name} ({nfc.uuid})</li>" for nfc in nfcs]) + \
		"</ul>" + \
		f"Please check the NFC Code Touch devices at <a href='/app/nfc-code-touch-device/'>NFC Code Touch Device</a>."

	frappe.msgprint(
		title="MiniServer Devices Updated",
		msg=msg,
		indicator="green"
	)

def create_or_update_nfc_code_touch_devices(ms_doc: Miniserver) -> None:
	"""Create or update NFC Code Touch devices based on the MiniServer configuration."""
	from loxone.loxone.doctype.nfc_code_touch_device.nfc_code_touch_device import NFCCodeTouchDevice

	for nfc in ms_doc.get_miniserver(True).get_nfc_code_touches():
		NFCCodeTouchDevice.create_or_update(ms_doc, nfc)
	