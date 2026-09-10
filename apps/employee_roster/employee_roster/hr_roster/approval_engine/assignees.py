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
	form_data: dict[str, Any] | None = None,
	allow_fallback: bool = True,
) -> list[str]:
	"""Return list of User ids."""
	props = props or {}
	form_data = form_data or {}
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
		roles = props.get("roles")
		if isinstance(roles, str):
			roles = [r.strip() for r in roles.split(",") if r.strip()]
		if not roles:
			role = props.get("role") or "HR Manager"
			roles = [role]
		for role in roles:
			role_users = frappe.get_all(
				"Has Role",
				filters={"role": role, "parenttype": "User"},
				pluck="parent",
			)
			users.extend([u for u in role_users if u and u != "Guest"])
	elif assignee_type == "department_head":
		users.extend(
			_users_for_department_head(
				_department_of_employee(applicant_employee),
			)
		)
	elif assignee_type == "form_field":
		field = (props.get("field") or "").strip()
		raw = form_data.get(field) if field else None
		resolve_as = (props.get("resolve_as") or "employee").strip()
		if raw:
			if resolve_as == "user":
				if isinstance(raw, list):
					users.extend([x for x in raw if x])
				else:
					users.append(raw)
			elif resolve_as == "department_head":
				dept = raw if isinstance(raw, str) else None
				users.extend(_users_for_department_head(dept))
			else:
				# employee (default)
				emps = raw if isinstance(raw, list) else [raw]
				for emp in emps:
					u = get_user_for_employee(emp)
					if u:
						users.append(u)
	elif assignee_type == "reports_to_chain":
		# Prefer expanding into sequential nodes in runtime; here return chain users
		# for single-node fallback (会签/或签 depending on mode).
		levels = int(props.get("levels") or 3)
		users.extend(
			_users_for_reports_to_chain(applicant_employee, levels=levels)
		)
	else:
		# reports_to (default)
		reports_to = None
		if applicant_employee:
			reports_to = frappe.db.get_value("Employee", applicant_employee, "reports_to")
		if reports_to:
			u = get_user_for_employee(reports_to)
			if u:
				users.append(u)

	users = list(dict.fromkeys([u for u in users if u]))
	if users or not allow_fallback:
		return users

	# fallback: HR Manager so flow never stalls in demo
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


def user_preview_card(user: str) -> dict[str, Any]:
	full_name = frappe.db.get_value("User", user, "full_name") or user
	avatar = frappe.db.get_value("User", user, "user_image") or ""
	return {
		"user": user,
		"full_name": full_name,
		"avatar": avatar,
	}


def build_process_preview(
	process: dict[str, Any] | list | str | None,
	*,
	applicant_employee: str | None,
	applicant_user: str | None,
	form_data: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
	"""Resolve process nodes into UI-friendly preview steps for start modal."""
	from employee_roster.hr_roster.approval_engine.process_schema import normalize_process

	form_data = form_data or {}
	process = normalize_process(process)
	nodes = process.get("nodes") or []
	expanded: list[dict[str, Any]] = []
	for node in nodes:
		ntype = node.get("type")
		if ntype in ("start", "end"):
			continue
		if ntype == "approver" and (node.get("props") or {}).get("assignee_type") == "reports_to_chain":
			expanded.extend(
				build_reports_to_chain_nodes(node, applicant_employee=applicant_employee)
			)
			continue
		if ntype in ("approver", "cc"):
			expanded.append(node)

	steps: list[dict[str, Any]] = []
	for node in expanded:
		props = node.get("props") or {}
		users = resolve_assignees(
			props,
			applicant_employee=applicant_employee,
			applicant_user=applicant_user,
			form_data=form_data,
			allow_fallback=False,
		)
		empty = not users
		steps.append(
			{
				"id": node.get("id"),
				"type": node.get("type"),
				"label": node.get("label") or ("抄送人" if node.get("type") == "cc" else "审批人"),
				"assignee_type": props.get("assignee_type") or "",
				"people": [user_preview_card(u) for u in users],
				"empty": empty,
				"auto_approve_hint": bool(empty and node.get("type") == "approver"),
				"locked": True,
			}
		)
	return steps


def _department_of_employee(employee: str | None) -> str | None:
	if not employee:
		return None
	return frappe.db.get_value("Employee", employee, "department")


def _users_for_department_head(dept: str | None) -> list[str]:
	if not dept:
		return []
	head = None
	meta = frappe.get_meta("Department")
	for fieldname in ("department_head", "leave_approver", "approver"):
		if meta.has_field(fieldname):
			head = frappe.db.get_value("Department", dept, fieldname)
			if head:
				break
	if not head:
		return []
	if frappe.db.exists("Employee", head):
		u = get_user_for_employee(head)
		return [u] if u else []
	if frappe.db.exists("User", head):
		return [head]
	return []


def _users_for_reports_to_chain(employee: str | None, *, levels: int = 3) -> list[str]:
	"""Walk reports_to up to `levels` managers (unique users, bottom → top)."""
	users: list[str] = []
	current = employee
	seen_emp: set[str] = set()
	for _ in range(max(1, levels)):
		if not current or current in seen_emp:
			break
		seen_emp.add(current)
		manager = frappe.db.get_value("Employee", current, "reports_to")
		if not manager or manager in seen_emp:
			break
		u = get_user_for_employee(manager)
		if u and u not in users:
			users.append(u)
		current = manager
	return users


def build_reports_to_chain_nodes(
	base_node: dict[str, Any],
	*,
	applicant_employee: str | None,
) -> list[dict[str, Any]]:
	"""Expand a reports_to_chain approver into sequential per-manager nodes."""
	props = dict(base_node.get("props") or {})
	levels = int(props.get("levels") or 3)
	users = _users_for_reports_to_chain(applicant_employee, levels=levels)
	if not users:
		# keep original node so resolve_assignees fallback can still run
		return [base_node]
	out = []
	for idx, user in enumerate(users, start=1):
		nid = f"{base_node.get('id') or 'chain'}_{idx}"
		out.append(
			{
				"id": nid,
				"type": "approver",
				"label": f"{base_node.get('label') or '上级'}（第{idx}级）",
				"props": {
					"assignee_type": "user",
					"user": user,
					"mode": props.get("mode") or "or",
					"field_perms": props.get("field_perms") or {},
				},
			}
		)
	return out
