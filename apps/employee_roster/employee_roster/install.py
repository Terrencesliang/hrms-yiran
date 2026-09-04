# Copyright (c) 2026 stillgroup
# License: MIT
import json
import os

import frappe

from employee_roster.hr_roster.page.employee_archive.employee_archive import seed_document_types


def after_install():
	from employee_roster.patches.post_fixture_sync.ensure_employee_group_name_field import execute as ensure_group_name_field
	from employee_roster.patches.v1_0.ensure_employee_checkin_day_fields import (
		ensure_employee_checkin_day_fields,
	)
	from employee_roster.hr_roster.attendance_deduction.setup import setup_attendance_deduction_module
	from employee_roster.hr_roster.org_fields import ensure_org_custom_fields

	from employee_roster.hr_roster.approval_admin import seed_approval_admin_data

	seed_document_types()
	ensure_group_name_field()
	ensure_org_custom_fields()
	ensure_employee_checkin_day_fields()
	sync_hr_roster_sidebar()
	setup_attendance_deduction_module()
	seed_approval_admin_data()


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
	sidebar_name = "hr_roster"

	# Heal accidental title-based rename (e.g. to 审批)
	if frappe.db.exists("Sidebar", "审批") and not frappe.db.exists("Sidebar", sidebar_name):
		frappe.rename_doc("Sidebar", "审批", sidebar_name, force=True)
		frappe.db.commit()
	elif frappe.db.exists("Sidebar", "审批") and frappe.db.exists("Sidebar", sidebar_name):
		frappe.delete_doc("Sidebar", "审批", force=True, ignore_permissions=True)
		frappe.db.commit()

	if frappe.db.exists("Sidebar", sidebar_name):
		doc = frappe.get_doc("Sidebar", sidebar_name)
	else:
		doc = frappe.new_doc("Sidebar")
		doc.name = sidebar_name

	doc.app = data.get("app") or "employee_roster"
	doc.module = "hr_roster"
	# Keep ASCII title — display label is overridden in unified_sidebar.js as「审批」
	doc.title = "hr_roster"
	doc.header_icon = data.get("header_icon") or "approve"
	doc.standard = 1
	doc.items = []
	for row in data.get("items", []):
		payload = {k: v for k, v in row.items() if k != "doctype"}
		doc.append("items", payload)
	doc.flags.ignore_version = True
	prev_dev = frappe.conf.developer_mode
	frappe.conf.developer_mode = 1
	try:
		if doc.is_new():
			doc.insert(ignore_permissions=True)
		else:
			doc.save(ignore_permissions=True)
	finally:
		frappe.conf.developer_mode = prev_dev
	frappe.db.commit()
