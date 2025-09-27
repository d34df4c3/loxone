# Copyright (c) 2025, Julien Becker and contributors
# For license information, please see license.txt

from datetime import datetime
from typing import cast
import pytz

import frappe
from frappe.model.document import Document
from loxone.api.Control.NfcCodeTouch import Code, CodeType
from loxone.loxone.doctype.nfc_code_touch_device.nfc_code_touch_device import NFCCodeTouchDevice
from loxone import logger

brussels_tz = pytz.timezone("Europe/Brussels")

class NFCCodeTouchCode(Document):
	# begin: auto-generated types
	# ruff: noqa

	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		lx_code: DF.Data
		lx_default_output: DF.Literal["Output 1", "Output 2", "Output 3", "Output 4", "Output 5", "Output 6"]
		lx_managed_by_dokos: DF.Check
		lx_name: DF.Data
		lx_nfc_device: DF.Link
		lx_output_1: DF.Check
		lx_output_2: DF.Check
		lx_output_3: DF.Check
		lx_output_4: DF.Check
		lx_output_5: DF.Check
		lx_output_6: DF.Check
		lx_time_from: DF.Datetime | None
		lx_time_to: DF.Datetime | None
		lx_type: DF.Literal["0 - Permanent", "1 - One-Time", "2 - Time-Dependent", "3 - Valid Until", "4 - Valid From", "5 - Deactivated"]
		lx_user: DF.Link | None
		lx_uuid: DF.Data
	# ruff: noqa
	# end: auto-generated types

	########### Hooks ##########
	def on_trash(self):
		logger.info(f"Deleting NFC Code Touch Code: {self.lx_name} ({self.name})")
		# If the code is managed by Dokos, we delete it from the device.
		if self.lx_managed_by_dokos == 1:
			self.delete_from_device()
			return
		# If the code is not managed by Dokos
		# ... triggered but Loxone module, skip the deletion.
		if getattr(self.flags, 'triggered_by_loxone', False):
			return
		# Otherwise, we throw an error.
		frappe.throw(
			title="Deletion Error",
			msg=f"The code ({self.lx_name}) is not managed by Dokos.<br/>It can only be deleted by the MiniServer")

	def on_update(self):
		# If the code is managed by Dokos, we update it on the device.
		if self.lx_managed_by_dokos == 1:
			logger.info(f"on_update {self.__dict__}")

			if getattr(self.flags, 'in_insert', False):
				self.create_on_device()
				logger.info(f"NFC Code Touch Code: {self.lx_name} created on device.")
			else:
				self.update_on_device()
				logger.info(f"NFC Code Touch Code: {self.lx_name} updated on device.")

			return
		# If the code is not managed by Dokos
		# ... but triggered but Loxone module, skip the update.
		if getattr(self.flags, 'triggered_by_loxone', False):
			return
		# Otherwise, we throw an error.
		frappe.throw(
			title="Update Error",
			msg=f"The code ({self.lx_name}) is not managed by Dokos.<br/>It can only be updated by the MiniServer."
		)
	
	@staticmethod
	def get_doc(name: str) -> "NFCCodeTouchCode":
		"""Get a NFCCodeTouchCode document by name."""
		return cast(NFCCodeTouchCode, frappe.get_doc("NFC Code Touch Code", name))

	@staticmethod
	def create_or_update(parent_doc: NFCCodeTouchDevice, code: Code) -> Document:
		code_doc_name = frappe.db.exists("NFC Code Touch Code", {"lx_nfc_device": parent_doc.name, "lx_uuid": code.uuid})

		if not code_doc_name:
			doc = cast(NFCCodeTouchCode, frappe.new_doc("NFC Code Touch Code"))
			doc.lx_nfc_device = parent_doc.name # type: ignore
			doc.lx_managed_by_dokos = 0
			doc.load_from_code(code)
			doc.flags.triggered_by_loxone = True
			doc.insert()
			logger.info("Inserted NFC Code Touch Code: %s", doc.as_json())
		else:
			doc = NFCCodeTouchCode.get_doc(str(code_doc_name))
			doc.load_from_code(code)
			doc.flags.triggered_by_loxone = True
			doc.save()
			logger.info("Updated NFC Code Touch Code: %s", doc.as_json())

		return doc

	def load_from_code(self, code: Code) -> None:
		"""Load the NFC Code Touch Code document from the provided Code object."""
		self.lx_name = code.name
		self.lx_uuid = code.uuid
		if not self.lx_code:
			self.lx_code = "Unknown"
		self.lx_type = NFCCodeTouchCode.__decode_type(code.type)
		self.lx_time_from = NFCCodeTouchCode.__to_date_str(code.time_from)
		self.lx_time_until = NFCCodeTouchCode.__to_date_str(code.time_to)
		self.lx_output_1 = code.outputs[0]
		self.lx_output_2 = code.outputs[1]
		self.lx_output_3 = code.outputs[2]
		self.lx_output_4 = code.outputs[3]
		self.lx_output_5 = code.outputs[4]
		self.lx_output_6 = code.outputs[5]
		self.lx_default_output = NFCCodeTouchCode.__decode_default_output(code.default_output)

	def delete_from_device(self) -> None:
		"""Delete the NFC Code Touch Code from the device."""
		code = self.__load_code()
		if code.delete():
			logger.info(f"Deleted NFC Code Touch Code: {self.lx_name} ({self.name}) from device.")
		else:
			logger.error(f"Failed to delete NFC Code Touch Code: {self.lx_name} ({self.name}) from device.")
			frappe.throw(
				title="Error Deleting NFC Code Touch Code",
				msg=f"Failed to delete NFC Code Touch Code: {self.lx_name} ({self.name}) from the device."
			)
	
	def create_on_device(self) -> None:
		"""Create the NFC Code Touch Code on the device."""
		code = self.__load_code()
		code.create()
		self.lx_uuid = code.uuid
		logger.info(f"Created NFC Code Touch Code: {self.lx_name}")
	
	def update_on_device(self) -> None:
		"""Update the NFC Code Touch Code on the device."""
		code = self.__load_code()
		code.update()
		logger.info(f"Updated NFC Code Touch Code: {self.lx_name}")
	
	def __load_code(self, uuid_only: bool = False) -> Code:
		"""Load the NFC Code Touch Code document into a Code object."""
		from loxone.api.Control.NfcCodeTouch import NfcCodeTouch, CodeBuilder
		from loxone.loxone.doctype.miniserver.miniserver import Miniserver

		nfc_doc = NFCCodeTouchDevice.get_doc(self.lx_nfc_device)
		ms_doc = Miniserver.get_doc(nfc_doc.lx_miniserver)

		nfc = NfcCodeTouch(ms_doc.get_miniserver().client, nfc_doc.lx_uuid, nfc_doc.lx_name)

		return (CodeBuilder(nfc)
			.uuid(self.lx_uuid)
			.name(self.lx_name)
			.code(self.lx_code)
			.type(NFCCodeTouchCode.__encode_type(self.lx_type))
			.time_from(NFCCodeTouchCode.__to_datetime(self.lx_time_from))
			.time_to(NFCCodeTouchCode.__to_datetime(self.lx_time_to))
			.set_output(1, self.lx_output_1 == 1)
			.set_output(2, self.lx_output_2 == 1)
			.set_output(3, self.lx_output_3 == 1)
			.set_output(4, self.lx_output_4 == 1)
			.set_output(5, self.lx_output_5 == 1)
			.set_output(6, self.lx_output_6 == 1)
			.default_output(NFCCodeTouchCode.__encode_default_output(self.lx_default_output))
			.build())

	@staticmethod
	def __to_datetime(date_str: str | datetime | None) -> datetime | None:
		"""Convert a date string to a datetime string."""
		if isinstance(date_str, datetime):
			return date_str
		
		if not date_str or date_str == "":
			return None
		return brussels_tz.localize(datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S'))
	
	@staticmethod
	def __to_date_str(date: datetime) -> str:
		"""Convert a datetime object to a date string."""
		if not date:
			return ""
		return date.strftime('%Y-%m-%d %H:%M:%S')

	# Single map for both encode and decode
	__code_type_map = {
		CodeType.PERMANENT: "0 - Permanent",
		CodeType.ONE_TIME: "1 - One-Time",
		CodeType.TIME_DEPENDENT: "2 - Time-Dependent",
		CodeType.VALID_UNTIL: "3 - Valid Until",
		CodeType.VALID_FROM: "4 - Valid From",
		CodeType.DEACTIVATED: "5 - Deactivated",
	}
	__code_type_reverse_map = {v: k for k, v in __code_type_map.items()}

	@staticmethod
	def __decode_type(code_type: CodeType) -> str:
		return NFCCodeTouchCode.__code_type_map.get(code_type, "Unknown")

	@staticmethod
	def __encode_type(type_str: str) -> CodeType:
		return NFCCodeTouchCode.__code_type_reverse_map.get(type_str, CodeType.DEACTIVATED)
	
	# Static list of output strings for encoding and decoding
	__output_list = [
			"Output 1",
			"Output 2",
			"Output 3",
			"Output 4",
			"Output 5",
			"Output 6",
		]

	@staticmethod
	def __decode_default_output(default_output: int) -> str:
		if 1 <= default_output <= len(NFCCodeTouchCode.__output_list):
			return NFCCodeTouchCode.__output_list[default_output - 1]
		return NFCCodeTouchCode.__output_list[0]

	@staticmethod
	def __encode_default_output(output_str: str) -> int:
		try:
			return NFCCodeTouchCode.__output_list.index(output_str) + 1
		except ValueError:
			return 1
