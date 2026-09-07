# Copyright (c) 2026 stillgroup
# License: MIT
"""Reload Approval Form schema fields and clear failed patch state."""

import frappe


def execute():
	# Ensure DocType JSON fields (form_schema_json etc.) are synced to DB
	frappe.reload_doc("hr_roster", "doctype", "approval_form", force=True)
	frappe.reload_doc("hr_roster", "doctype", "approval_instance", force=True)
	frappe.reload_doc("hr_roster", "doctype", "approval_task", force=True)
	frappe.reload_doc("hr_roster", "page", "approval_workspace", force=True)
	frappe.reload_doc("hr_roster", "page", "approval_form_designer", force=True)
	frappe.reload_doc("hr_roster", "page", "approval_templates", force=True)
	frappe.reload_doc("hr_roster", "page", "approvals", force=True)

	from employee_roster.hr_roster.approval_admin import seed_approval_admin_data
	from employee_roster.install import sync_hr_roster_sidebar

	seed_approval_admin_data()
	sync_hr_roster_sidebar()
	frappe.clear_cache()
