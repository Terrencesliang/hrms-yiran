# Copyright (c) 2026 stillgroup
# License: MIT
"""当前登录人的个人中心与账号安全接口。"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.core.doctype.user.user import test_password_strength
from frappe.utils import formatdate
from frappe.utils.password import check_password, is_password_reused, update_password

from employee_roster.hr_roster.approval_engine.assignees import get_employee_for_user
from employee_roster.hr_roster.menu_permissions import get_user_company


def _current_user() -> str:
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("请先登录"), frappe.PermissionError)
	return user


def _employee_payload(user: str) -> dict | None:
	name = get_employee_for_user(user)
	if not name or not frappe.db.exists("Employee", name):
		return None
	doc = frappe.get_doc("Employee", name)
	reports_to_name = frappe.db.get_value("Employee", doc.reports_to, "employee_name") if doc.reports_to else ""
	return {
		"name": doc.name,
		"employee_name": doc.employee_name or doc.first_name or "",
		"employee_number": doc.employee_number or "",
		"status": doc.status or "",
		"image": doc.image or "",
		"company": doc.company or "",
		"department": doc.department or "",
		"group_name": doc.get("group_name") or "",
		"designation": doc.designation or "",
		"branch": doc.get("branch") or "",
		"employment_type": doc.employment_type or "",
		"date_of_joining": str(doc.date_of_joining or "")[:10],
		"gender": doc.gender or "",
		"date_of_birth": str(doc.date_of_birth or "")[:10],
		"cell_number": doc.cell_number or "",
		"personal_email": doc.personal_email or "",
		"company_email": doc.company_email or "",
		"current_address": doc.current_address or "",
		"reports_to_name": reports_to_name or "",
		"wecom_bound": bool(doc.get("hr_wecom_id")),
	}


@frappe.whitelist()
def get_context() -> dict:
	user = _current_user()
	account = frappe.db.get_value(
		"User",
		user,
		["name", "username", "full_name", "user_image", "last_login", "last_password_reset_date", "enabled"],
		as_dict=True,
	) or {}
	business_roles = []
	if frappe.db.table_exists("HR User Business Role"):
		company = get_user_company(user)
		assignments = frappe.get_all(
			"HR User Business Role",
			filters={"user": user, "company": company, "enabled": 1},
			pluck="business_role",
		)
		if assignments:
			business_roles = frappe.get_all(
				"HR Business Role",
				filters={"name": ["in", assignments], "enabled": 1},
				pluck="role_title",
			)
	return {
		"account": {
			"user_id": account.get("name") or user,
			"username": account.get("username") or user,
			"full_name": account.get("full_name") or user,
			"avatar": account.get("user_image") or "",
			"enabled": bool(account.get("enabled")),
			"last_login": str(account.get("last_login") or ""),
			"last_password_reset_date": formatdate(account.get("last_password_reset_date")) if account.get("last_password_reset_date") else "尚未修改",
			"must_change_password": bool(frappe.db.has_column("User", "hr_must_change_password") and frappe.db.get_value("User", user, "hr_must_change_password")),
			"roles": business_roles,
		},
		"employee": _employee_payload(user),
	}


@frappe.whitelist(methods=["POST"])
def change_my_password(current_password: str, new_password: str, confirm_password: str) -> dict:
	user = _current_user()
	if new_password != confirm_password:
		frappe.throw(_("两次输入的新密码不一致"))
	if len(new_password or "") < 8:
		frappe.throw(_("新密码至少需要 8 位"))
	if not any(char.isalpha() for char in new_password) or not any(char.isdigit() for char in new_password):
		frappe.throw(_("新密码需要同时包含字母和数字"))
	try:
		check_password(user, current_password)
	except frappe.AuthenticationError:
		frappe.throw(_("当前密码不正确"), frappe.AuthenticationError)
	if is_password_reused(user, new_password):
		frappe.throw(_("新密码不能与当前密码相同"))
	result = test_password_strength(new_password)
	feedback = result.get("feedback") if result else None
	if feedback and not feedback.get("password_policy_validation_passed", False):
		frappe.throw(_("新密码强度不足，请增加长度并混合使用字母、数字和符号"))
	update_password(user, new_password, logout_all_sessions=True)
	frappe.db.set_value("User", user, "last_password_reset_date", frappe.utils.today())
	if frappe.db.has_column("User", "hr_must_change_password"):
		frappe.db.set_value("User", user, "hr_must_change_password", 0, update_modified=False)
	frappe.db.commit()
	return {"message": "密码修改成功", "must_change_password": False}
