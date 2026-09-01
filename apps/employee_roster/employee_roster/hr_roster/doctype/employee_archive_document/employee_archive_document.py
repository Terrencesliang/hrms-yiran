# Copyright (c) 2026 stillgroup
# License: MIT
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class EmployeeArchiveDocument(Document):
	def validate(self):
		if self.file:
			self.status = "Uploaded"
			if not self.uploaded_by:
				self.uploaded_by = frappe.session.user
			if not self.uploaded_on:
				self.uploaded_on = now_datetime()
		else:
			self.status = "Pending"

		existing = frappe.db.exists(
			"Employee Archive Document",
			{"employee": self.employee, "document_type": self.document_type, "name": ("!=", self.name)},
		)
		if existing:
			frappe.throw(_("This employee already has a record for document type {0}").format(self.document_type))
