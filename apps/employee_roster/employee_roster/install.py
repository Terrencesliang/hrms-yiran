# Copyright (c) 2026 stillgroup
# License: MIT
import json
import os

import frappe

from employee_roster.hr_roster.page.employee_archive.employee_archive import seed_document_types


def hide_hr_setup_workspace():
	"""Hide legacy Frappe HR Setup workspace; 人事默认入口改为 hr-home。"""
	if not frappe.db.exists("Workspace", "HR Setup"):
		return
	if frappe.db.get_value("Workspace", "HR Setup", "is_hidden"):
		return
	frappe.db.set_value("Workspace", "HR Setup", "is_hidden", 1, update_modified=False)
	frappe.db.commit()


HR_SETUP_HIDDEN_LINK_TO = {
	"Company",
	"Branch",
	"Department",
	"Designation",
	"Employee Group",
	"Employee Grade",
	"HR Settings",
	"Settings",
}
HR_SETUP_HIDDEN_SECTIONS = {"Setup"}


def hide_hr_setup_sidebar_links():
	"""Hide master-data links under 人事 — managed via org pages instead."""
	if not frappe.db.exists("Sidebar", "HR Setup"):
		return
	doc = frappe.get_doc("Sidebar", "HR Setup")
	changed = False
	for row in doc.items:
		if row.type == "Section Break" and row.label in HR_SETUP_HIDDEN_SECTIONS:
			if not int(row.hidden or 0):
				row.hidden = 1
				changed = True
		elif row.type == "Link" and (
			row.link_to in HR_SETUP_HIDDEN_LINK_TO or row.label in HR_SETUP_HIDDEN_LINK_TO
		):
			if not int(row.hidden or 0):
				row.hidden = 1
				changed = True
	if changed:
		# Existing sidebar fixtures can retain links to deleted Workspaces/Pages.
		# Hiding unrelated setup entries must not make migrations fail on those stale rows.
		doc.flags.ignore_links = True
		doc.save(ignore_permissions=True)
		frappe.db.commit()


def after_install():
	from employee_roster.patches.post_fixture_sync.ensure_employee_group_name_field import execute as ensure_group_name_field
	from employee_roster.patches.post_fixture_sync.ensure_cn_employee_fields import execute as ensure_cn_employee_fields
	from employee_roster.patches.post_fixture_sync.ensure_employee_archive_schema import execute as ensure_employee_archive_schema
	from employee_roster.patches.v1_0.ensure_employee_checkin_day_fields import (
		ensure_employee_checkin_day_fields,
	)
	from employee_roster.hr_roster.attendance_deduction.setup import setup_attendance_deduction_module
	from employee_roster.hr_roster.org_fields import ensure_org_custom_fields

	from employee_roster.hr_roster.approval_admin import seed_approval_admin_data

	seed_document_types()
	ensure_group_name_field()
	ensure_cn_employee_fields()
	ensure_employee_archive_schema()
	ensure_org_custom_fields()
	ensure_employee_checkin_day_fields()
	sync_hr_roster_sidebar()
	hide_hr_setup_sidebar_links()
	hide_hr_setup_workspace()
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
	"""Ensure HR Setup sidebar contains archive + Arco 主页/数据面板。"""
	if not frappe.db.exists("Sidebar", "HR Setup"):
		return
	doc = frappe.get_doc("Sidebar", "HR Setup")
	changed = False

	has_employee_entry = any(row.link_to == "Employee" for row in doc.items)
	for row in list(doc.items):
		if row.link_to == "roster":
			if has_employee_entry:
				doc.remove(row)
				changed = True
				continue
			row.label = "员工花名册"
			row.link_type = "DocType"
			row.link_to = "Employee"
			row.type = "Link"
			has_employee_entry = True
			changed = True
		elif row.label in ("Home", "主页") and (
			row.link_type != "Page" or row.link_to != "hr-home"
		):
			row.link_type = "Page"
			row.link_to = "hr-home"
			row.type = "Link"
			changed = True
		elif row.label in ("Dashboard", "数据面板") and (
			row.link_type != "Page" or row.link_to != "hr-dashboard"
		):
			row.link_type = "Page"
			row.link_to = "hr-dashboard"
			row.type = "Link"
			changed = True

	if not any(row.link_to == "employee-archive" for row in doc.items):
		roster_idx = next(
			(idx for idx, row in enumerate(doc.items) if row.link_to == "Employee"),
			None,
		)
		items = [row.as_dict() for row in doc.items]
		items.insert(
			(roster_idx + 1) if roster_idx is not None else len(items),
			ARCHIVE_SIDEBAR_ITEM.copy(),
		)
		doc.items = []
		for row in items:
			doc.append("items", row)
		changed = True

	if changed:
		doc.save(ignore_permissions=True)
		frappe.db.commit()

	hide_hr_setup_sidebar_links()
	hide_hr_setup_workspace()


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
	doc.flags.ignore_links = True
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
	hide_hr_setup_sidebar_links()
