# Copyright (c) 2026 stillgroup
# License: MIT
"""Row-level protection for employee self-service approval records."""

from __future__ import annotations

import frappe


ADMIN_ROLES = {"System Manager", "HR Manager"}


def approval_instance_query(user: str | None = None) -> str:
	user = user or frappe.session.user
	if not user or user == "Guest":
		return "1 = 0"
	if ADMIN_ROLES.intersection(frappe.get_roles(user)):
		return ""
	escaped = frappe.db.escape(user)
	return (
		f"(`tabApproval Instance`.applicant_user = {escaped} OR EXISTS ("
		"SELECT 1 FROM `tabApproval Task` task "
		"WHERE task.instance = `tabApproval Instance`.name "
		f"AND task.assignee = {escaped}))"
	)


def approval_instance_has_permission(doc, user: str | None = None, permission_type: str | None = None):
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False
	if ADMIN_ROLES.intersection(frappe.get_roles(user)):
		return True
	if permission_type not in (None, "read", "select"):
		return False
	if doc.applicant_user == user:
		return True
	return bool(frappe.db.exists("Approval Task", {"instance": doc.name, "assignee": user}))
