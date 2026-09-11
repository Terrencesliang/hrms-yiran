# Copyright (c) 2026 stillgroup
# License: MIT

import frappe


def execute():
	from employee_roster.hr_roster.menu_permissions import ensure_system_roles, role_code

	ensure_system_roles()
	for user in frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name"):
		if user in {"Guest", "Administrator"}:
			continue
		roles = set(frappe.get_roles(user))
		if "System Manager" in roles:
			continue
		company = frappe.db.get_value("Employee", {"user_id": user}, "company") or frappe.defaults.get_user_default("Company", user)
		if not company:
			continue
		system_key = "enterprise_admin" if "Enterprise Admin" in roles else "hr_admin" if roles & {"HR Manager", "HR User"} else "employee"
		title = {"enterprise_admin": "企业管理员", "hr_admin": "人事管理员", "employee": "普通员工"}[system_key]
		business_role = role_code(company, system_key, title)
		if not frappe.db.exists("HR Business Role", business_role):
			continue
		if frappe.db.exists("HR User Business Role", {"user": user, "company": company, "business_role": business_role}):
			continue
		frappe.get_doc({"doctype": "HR User Business Role", "user": user, "company": company, "business_role": business_role, "enabled": 1}).insert(ignore_permissions=True)

