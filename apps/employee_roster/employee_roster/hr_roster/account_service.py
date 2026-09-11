# Copyright (c) 2026 stillgroup
# License: MIT
"""员工登录账号的创建与绑定。"""

from __future__ import annotations

import re

import frappe
from frappe.utils.password import update_password


DEFAULT_PASSWORD = "123456"
EMPLOYEE_CENTER_ROLE = "Employee Center User"


def _account_email(employee) -> str:
	"""使用真实邮箱；没有邮箱时生成稳定且不会对外发信的内部账号标识。"""
	for value in (employee.company_email, employee.personal_email):
		email = str(value or "").strip().lower()
		if email and not frappe.db.exists("User", email):
			return email
	seed = re.sub(r"[^a-zA-Z0-9]+", "-", employee.name).strip("-").lower()
	return f"{seed}@users.yiran.local"


def _unique_username(employee) -> str:
	name = str(employee.employee_name or employee.first_name or employee.name).strip()
	if not frappe.db.exists("User", {"username": name}):
		return name
	suffix = str(employee.employee_number or employee.name).strip()
	return f"{name}-{suffix}"


def ensure_employee_account(doc, method=None) -> str | None:
	"""为在职员工创建最低权限账号；绝不覆盖已有账号及其密码。"""
	if doc.status != "Active" or doc.user_id:
		return doc.user_id or None

	if not frappe.db.exists("Role", EMPLOYEE_CENTER_ROLE):
		return None

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": _account_email(doc),
			"username": _unique_username(doc),
			"first_name": doc.employee_name or doc.first_name or doc.name,
			"full_name": doc.employee_name or doc.first_name or doc.name,
			"user_type": "System User",
			"enabled": 1,
			"send_welcome_email": 0,
			"language": "zh",
			"roles": [{"role": EMPLOYEE_CENTER_ROLE}],
		}
	)
	user.flags.ignore_password_policy = True
	user.insert(ignore_permissions=True)
	update_password(user.name, DEFAULT_PASSWORD)
	if frappe.db.has_column("User", "hr_must_change_password"):
		frappe.db.set_value("User", user.name, "hr_must_change_password", 1, update_modified=False)
	frappe.db.set_value("Employee", doc.name, "user_id", user.name, update_modified=False)
	doc.user_id = user.name
	return user.name


def provision_existing_employee_accounts() -> dict[str, int | list[dict[str, str]]]:
	created = skipped = failed = 0
	errors: list[dict[str, str]] = []
	for row in frappe.get_all(
		"Employee",
		filters={"status": "Active", "user_id": ["is", "not set"]},
		pluck="name",
		order_by="name asc",
		limit_page_length=0,
	):
		try:
			if ensure_employee_account(frappe.get_doc("Employee", row)):
				created += 1
			else:
				skipped += 1
		except Exception as exc:
			failed += 1
			errors.append({"employee": row, "error": str(exc)[:240]})
	return {"created": created, "skipped": skipped, "failed": failed, "errors": errors[:20]}
