# Copyright (c) 2026 stillgroup
# License: MIT
"""Resolve approval / cc assignees from node props."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def get_employee_for_user(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if not user or user in ("Guest", "Administrator"):
		# Administrator may still map to an employee in some sites
		pass
	return frappe.db.get_value("Employee", {"user_id": user}, "name")


def get_user_for_employee(employee: str | None) -> str | None:
	if not employee:
		return None
	return frappe.db.get_value("Employee", employee, "user_id")


def resolve_assignees(
	props: dict[str, Any] | None,
	*,
	applicant_employee: str | None,
	applicant_user: str | None,
) -> list[str]:
	"""Return list of User ids."""
	props = props or {}
	assignee_type = (props.get("assignee_type") or "reports_to").strip()
	users: list[str] = []

	if assignee_type == "user":
		u = props.get("user") or props.get("users")
		if isinstance(u, list):
			users.extend([x for x in u if x])
		elif u:
			users.append(u)
	elif assignee_type == "employee":
		emps = props.get("employee") or props.get("employees") or []
		if isinstance(emps, str):
			emps = [emps]
		for emp in emps:
			u = get_user_for_employee(emp)
			if u:
				users.append(u)
	elif assignee_type == "role":
		role = props.get("role") or "HR Manager"
		role_users = frappe.get_all(
			"Has Role",
			filters={"role": role, "parenttype": "User"},
			pluck="parent",
		)
		users.extend([u for u in role_users if u and u != "Guest"])
	elif assignee_type == "department_head":
		dept = None
		if applicant_employee:
			dept = frappe.db.get_value("Employee", applicant_employee, "department")
		if dept:
			# Prefer Department.department_head / custom leave_approver style fields if present
			head = None
			meta = frappe.get_meta("Department")
			for fieldname in ("department_head", "leave_approver", "approver"):
				if meta.has_field(fieldname):
					head = frappe.db.get_value("Department", dept, fieldname)
					if head:
						break
			if head:
				# may be Employee or User
				if frappe.db.exists("Employee", head):
					u = get_user_for_employee(head)
					if u:
						users.append(u)
				elif frappe.db.exists("User", head):
					users.append(head)
	else:
		# reports_to (default)
		reports_to = None
		if applicant_employee:
			reports_to = frappe.db.get_value("Employee", applicant_employee, "reports_to")
		if reports_to:
			u = get_user_for_employee(reports_to)
			if u:
				users.append(u)

	# fallback: HR Manager so flow never stalls in demo
	users = list(dict.fromkeys([u for u in users if u]))
	if not users:
		fallback = frappe.get_all(
			"Has Role",
			filters={"role": "HR Manager", "parenttype": "User"},
			pluck="parent",
			limit=5,
		)
		users = [u for u in fallback if u and u != "Guest"]
	if not users and applicant_user and applicant_user != "Guest":
		# last resort: self (visible for admin testing)
		users = [applicant_user]
	if not users:
		frappe.throw(_("无法解析审批人，请检查流程节点配置或组织汇报关系"))
	return users
