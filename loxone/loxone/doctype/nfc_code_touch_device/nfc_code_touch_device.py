# Copyright (c) 2025, Julien Becker and contributors
# For license information, please see license.txt

# import frappe
from typing import cast
import frappe
from frappe.model.document import Document
from loxone.loxone.doctype.miniserver.miniserver import Miniserver
from loxone.api.Control.NfcCodeTouch import NfcCodeTouch
from loxone import logger

class NFCCodeTouchDevice(Document):
	# begin: auto-generated types
	# ruff: noqa

	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		lx_miniserver: DF.Link
		lx_name: DF.Data
		lx_uuid: DF.Data
	# ruff: noqa
	# end: auto-generated types

	########## Hooks ##########
	def on_trash(self):
		logger.info(f"Deleting NFC Code Touch Device: {self.lx_name} ({self.name})")

		if not getattr(self.flags, 'triggered_by_loxone', False):
			frappe.throw(title="Deletion Error", msg="NFC Code Touch Device can only be deleted by the MiniServer.")

		codes = frappe.get_all("NFC Code Touch Code", filters={"lx_nfc_device": self.name})
		for code in codes:
			code_doc = frappe.get_doc("NFC Code Touch Code", code.name)
			code_doc.flags.triggered_by_loxone = True
			code_doc.delete()

	@staticmethod
	def get_doc(name: str) -> "NFCCodeTouchDevice":
		"""Get a NFCCodeTouchDevice document by name."""
		return cast(NFCCodeTouchDevice, frappe.get_doc("NFC Code Touch Device", name))

	def load_from_device(self, nfc: NfcCodeTouch) -> None:
		self.lx_name = nfc.name
		self.lx_uuid = nfc.uuid

	def create_or_update_codes(self, nfc: NfcCodeTouch) -> None:
		"""Create or update NFC Codes for the NFC Code Touch Device."""
		from loxone.loxone.doctype.nfc_code_touch_code.nfc_code_touch_code import NFCCodeTouchCode

		for code in nfc.codes():
			nfc_code = NFCCodeTouchCode.create_or_update(self, code)

def create_or_update(ms_doc: Miniserver, nfc: NfcCodeTouch) -> Document:
	"""Create or update the NFC Code Touch device based on the provided NFC Code Touch."""
	nfc_doc_name = frappe.db.exists("NFC Code Touch Device", {"lx_miniserver": ms_doc.name, "lx_uuid": nfc.uuid})

	if not nfc_doc_name:
		doc = cast(NFCCodeTouchDevice, frappe.new_doc("NFC Code Touch Device"))
		doc.lx_miniserver = ms_doc.name # type: ignore
		doc.load_from_device(nfc)
		doc.insert()
		logger.info("Inserted NFC Code Touch Device: %s", doc.as_json())
	else:
		doc = NFCCodeTouchDevice.get_doc(str(nfc_doc_name))
		doc.load_from_device(nfc)
		doc.save()
		logger.info("Updated NFC Code Touch Device: %s", doc.as_json())

	doc.create_or_update_codes(nfc)
	return doc

def delete_all(ms_name: str) -> None:
	"""Delete all NFC Code Touch Devices for a given MiniServer."""
	nfc_devices = frappe.get_all("NFC Code Touch Device", filters={"lx_miniserver": ms_name})
	for device in nfc_devices:
		nfc_doc = NFCCodeTouchDevice.get_doc(device.name)
		nfc_doc.flags.triggered_by_loxone = True
		nfc_doc.delete()
		logger.info(f"Deleted NFC Code Touch Device: {nfc_doc.lx_name} ({nfc_doc.name})")