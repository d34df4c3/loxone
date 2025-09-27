import frappe

from loxone.loxone.doctype.miniserver.miniserver import Miniserver
from loxone.loxone.doctype.loxone_user_group.loxone_user_group import LoxoneUserGroup


class LoxoneUserGroupMapper:
	"""Mapper class for Loxone User Group document.

	This class is responsible for mapping data from Miniserver JSON to Loxone User Group document.
	Attributes:
		doc (LoxoneUserGroup): The Loxone User Group document to map data to.
	"""
	def __init__(self, doc: LoxoneUserGroup, ms_doc: Miniserver) -> None:
		"""Initialize the mapper with a Loxone User Group document."""
		self.doc = doc
		self.ms_doc = ms_doc
	
	def load(self, data: dict) -> None:
		"""Map data from JSON to the document fields.
		
		Args:
			data (dict): The data to map.
				- uuid (str): The UUID of the user group.
				- name (str): The name of the user group.
				- description (str): The description of the user group.
				- type (str): The type of the user group.
				- userRights (int): The user rights of the user group.
		"""
		self.load_miniserver()
		self.load_uuid(data)
		self.load_name(data)
		self.load_description(data)

	def load_miniserver(self) -> None:
		if self.doc.lx_miniserver is None:
			self.doc.lx_miniserver = self.ms_doc.name
		if self.doc.lx_miniserver != self.ms_doc.name:
			frappe.throw(f"Loxone User {self.doc.lx_name} is assigned to a different Miniserver ({self.doc.lx_miniserver}) than the current one ({self.ms_doc.name}).")

	def load_uuid(self, data: dict) -> None:
		if 'uuid' not in data:
			frappe.throw("Loxone User Group UUID not found in data.")
		self.doc.lx_uuid = data['uuid']

	def load_name(self, data: dict) -> None:
		if 'name' not in data:
			frappe.throw("Loxone User Group name not found in data.")
		self.doc.lx_name = data['name']

	def load_description(self, data: dict) -> None:
		self.doc.lx_description = data['description']
