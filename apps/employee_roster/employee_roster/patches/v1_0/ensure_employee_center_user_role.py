# Copyright (c) 2026 stillgroup
# License: MIT

import frappe


ROLE_NAME = "Employee Center User"
PAGE_NAME = "employee-center"
PAGE_ROLES = (
	"Employee Center User",
	"Employee",
	"HR User",
	"HR Manager",
	"System Manager",
)
HR_DESK_ROLES = (
	"HR User",
	"HR Manager",
	"System Manager",
)
# Pages that previously had empty roles (open to every Desk user).
HR_ONLY_PAGES = (
	"hr-home",
	"hr-dashboard",
	"roster",
	"orgchart",
	"org-diagram",
	"employee-archive",
	"attendance-rules",
	"recruiting-active",
	"recruiting-hired",
	"recruiting-rejected",
	"contract-overview",
	"contract-archive",
	"contract-initiate",
	"contract-packages",
	"contract-templates",
	"contract-seals",
	"contract-signing-pending",
	"contract-signing-signed",
	"contract-signing-void",
)


def execute():
	"""Create the least-privilege Desk role used by ordinary employee accounts."""
	_ensure_role()
	_ensure_page_roles()
	_lock_hr_only_pages()
	_ensure_employee_read_perm()


def _ensure_role() -> None:
	if frappe.db.exists("Role", ROLE_NAME):
		frappe.db.set_value(
			"Role",
			ROLE_NAME,
			{"desk_access": 1, "home_page": "desk/employee-center/home"},
			update_modified=False,
		)
		return
	frappe.get_doc(
		{
			"doctype": "Role",
			"role_name": ROLE_NAME,
			"desk_access": 1,
			"home_page": "desk/employee-center/home",
		}
	).insert(ignore_permissions=True)


def _ensure_page_roles() -> None:
	if not frappe.db.exists("Page", PAGE_NAME):
		return
	page = frappe.get_doc("Page", PAGE_NAME)
	existing = {row.role for row in page.roles}
	changed = False
	for role in PAGE_ROLES:
		if role in existing:
			continue
		page.append("roles", {"role": role})
		changed = True
	if changed:
		page.save(ignore_permissions=True)


def _lock_hr_only_pages() -> None:
	"""Empty Page.roles means any Desk user; lock HR modules to HR roles only."""
	for name in HR_ONLY_PAGES:
		if not frappe.db.exists("Page", name):
			continue
		page = frappe.get_doc("Page", name)
		if page.roles:
			# Already restricted — do not wipe custom grants, but never allow
			# Employee Center User onto these HR ops pages.
			if any(row.role == ROLE_NAME for row in page.roles):
				page.roles = [row for row in page.roles if row.role != ROLE_NAME]
				page.save(ignore_permissions=True)
			continue
		for role in HR_DESK_ROLES:
			page.append("roles", {"role": role})
		page.save(ignore_permissions=True)


def _ensure_employee_read_perm() -> None:
	"""Allow Employee Center User to pass HRMS app gate via own Employee record."""
	filters = {
		"parent": "Employee",
		"role": ROLE_NAME,
		"permlevel": 0,
	}
	name = frappe.db.exists("Custom DocPerm", filters)
	if name:
		frappe.db.set_value(
			"Custom DocPerm",
			name,
			{"read": 1, "select": 1, "if_owner": 1},
			update_modified=False,
		)
		return

	frappe.get_doc(
		{
			"doctype": "Custom DocPerm",
			"parent": "Employee",
			"parenttype": "DocType",
			"parentfield": "permissions",
			"role": ROLE_NAME,
			"permlevel": 0,
			"read": 1,
			"select": 1,
			"write": 0,
			"create": 0,
			"delete": 0,
			"if_owner": 1,
		}
	).insert(ignore_permissions=True)
