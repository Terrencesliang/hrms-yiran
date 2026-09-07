# Copyright (c) 2026 stillgroup
# License: MIT

import frappe
from frappe.model.document import Document


class ApprovalInstance(Document):
	pass


def on_doctype_update():
	"""Composite index for batch delete / runtime lookups by form + status."""
	frappe.db.add_index("Approval Instance", ["approval_form", "status"])
