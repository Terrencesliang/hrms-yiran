# Copyright (c) 2026 stillgroup
# License: MIT
import json
import os

import frappe

from employee_roster.hr_roster.page.employee_archive.employee_archive import seed_document_types


def after_install():
	from employee_roster.patches.post_fixture_sync.ensure_employee_group_name_field import execute as ensure_group_name_field
	from employee_roster.hr_roster.attendance_deduction.setup import setup_attendance_deduction_module
	from employee_roster.hr_roster.org_fields import ensure_org_custom_fields

	seed_document_types()
	ensure_group_name_field()
	ensure_org_custom_fields()
	sync_hr_roster_sidebar()
	setup_attendance_deduction_module()


ARCHIVE_SIDEBAR_ITEM = {
	"added": 0,
	"child": 0,
	"collapsible": 0,
	"hidden": 0,
	"icon": "folder-open",
	"indent": 0,
	"is_default_module": 0,
	"keep_closed": 0,
	"label": "员工档案库",
	"link_to": "employee-archive",
	"link_type": "Page",
	"open_in_new_tab": 0,
	"show_arrow": 0,
	"type": "Link",
}


def sync_sidebar():
	"""Ensure HR Setup sidebar contains the employee archive page."""
	if not frappe.db.exists("Sidebar", "HR Setup"):
		return
	doc = frappe.get_doc("Sidebar", "HR Setup")
	if any(row.link_to == "employee-archive" for row in doc.items):
		return
	roster_idx = next(
		(idx for idx, row in enumerate(doc.items) if row.link_to == "roster"),
		None,
	)
	items = [row.as_dict() for row in doc.items]
	items.insert((roster_idx + 1) if roster_idx is not None else len(items), ARCHIVE_SIDEBAR_ITEM.copy())
	doc.items = []
	for row in items:
		doc.append("items", row)
	doc.save(ignore_permissions=True)
	frappe.db.commit()


def sync_hr_roster_sidebar():
	"""Load curated hr_roster sidebar (pages only, no setup doctypes)."""
	path = os.path.join(
		frappe.get_app_path("employee_roster"),
		"hr_roster",
		"sidebar",
		"hr_roster",
		"hr_roster.json",
	)
	if not os.path.exists(path):
		return
	with open(path, encoding="utf-8") as handle:
		data = json.load(handle)
	sidebar_name = data.get("name") or data.get("module") or "hr_roster"
	if frappe.db.exists("Sidebar", sidebar_name):
		doc = frappe.get_doc("Sidebar", sidebar_name)
	else:
		doc = frappe.get_doc({"doctype": "Sidebar", "name": sidebar_name})
	for key, value in data.items():
		if key in ("doctype", "items", "name"):
			continue
		doc.set(key, value)
	doc.items = []
	for row in data.get("items", []):
		doc.append("items", row)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
