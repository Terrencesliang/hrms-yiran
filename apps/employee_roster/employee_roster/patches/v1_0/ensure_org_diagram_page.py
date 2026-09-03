import json
import os

import frappe


def execute():
	"""Ensure org-diagram Page exists on sites that missed the initial import."""
	if frappe.db.exists("Page", "org-diagram"):
		return

	path = os.path.join(
		frappe.get_app_path("employee_roster"),
		"hr_roster",
		"page",
		"org_diagram",
		"org_diagram.json",
	)
	with open(path, encoding="utf-8") as handle:
		data = json.load(handle)

	frappe.get_doc(data).insert(ignore_permissions=True)
	frappe.db.commit()
