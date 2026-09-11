"""企业微信集成的管理端接口。"""
from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from .attendance import sync_attendance_period
from .client import configuration_status, connection_status
from .oauth import complete_oauth_login, oauth_entry_info
from .service import (
	bind_employee_userids_by_mobile,
	provision_system_users_for_wecom_employees,
	send_robot_text,
	send_text,
	send_textcard,
	sync_contacts,
)


def _require_hr_manager() -> None:
	if "HR Manager" not in frappe.get_roles():
		frappe.throw("仅人事经理可执行企业微信同步", frappe.PermissionError)


@frappe.whitelist()
def get_configuration_status() -> dict[str, Any]:
	_require_hr_manager()
	return configuration_status()


@frappe.whitelist()
def get_connection_status() -> dict[str, Any]:
	_require_hr_manager()
	return connection_status()


@frappe.whitelist()
def get_oauth_entry_url(next_path: str | None = None) -> dict[str, Any]:
	"""返回企微免登/扫码登录链接，供配置可信域名后测试。"""
	_require_hr_manager()
	return oauth_entry_info(next_path)


@frappe.whitelist(allow_guest=True)
def get_web_login_config(next_path: str | None = None) -> dict[str, Any]:
	"""登录页扫码组件公开配置（不含 Secret）。"""
	return oauth_entry_info(next_path)


@frappe.whitelist(allow_guest=True)
def wecom_sso_callback(code: str | None = None, state: str | None = None) -> None:
	"""企微扫码/OAuth 轻量回调：登录后 302，避免 Website 模板渲染。"""
	from urllib.parse import quote

	code = code or frappe.form_dict.get("code")
	state = state or frappe.form_dict.get("state")
	try:
		result = complete_oauth_login(str(code or "").strip(), state)
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = result["redirect_to"]
	except Exception as exc:
		# Postgres 异常后事务可能已中止，先 rollback 才能写 Error Log。
		try:
			frappe.db.rollback()
		except Exception:
			pass
		try:
			frappe.log_error(frappe.get_traceback(), "企业微信免登失败")
			frappe.db.commit()
		except Exception:
			pass
		message = quote(str(exc)[:180], safe="")
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = f"/wecom_login?error=1&message={message}"


@frappe.whitelist(allow_guest=True, methods=["POST"])
def complete_wecom_login(code: str, state: str | None = None) -> dict[str, Any]:
	"""扫码/授权成功后的 code 换会话（Guest 可调用）。"""
	if frappe.session.user and frappe.session.user != "Guest":
		from .oauth import decode_oauth_state

		return {
			"user": frappe.session.user,
			"redirect_to": decode_oauth_state(state),
			"already_logged_in": True,
		}
	return complete_oauth_login(str(code or "").strip(), state)


@frappe.whitelist(methods=["POST"])
def run_contact_sync(create_missing: int | str | None = None) -> dict[str, Any]:
	_require_hr_manager()
	return sync_contacts(
		create_missing=None if create_missing is None else bool(cint(create_missing))
	)


@frappe.whitelist(methods=["POST"])
def bind_existing_employees(limit: int | str = 100) -> dict[str, Any]:
	_require_hr_manager()
	return bind_employee_userids_by_mobile(limit=cint(limit))


@frappe.whitelist(methods=["POST"])
def provision_wecom_employee_users(
	limit: int | str = 0,
	fetch_remote_profile: int | str = 1,
) -> dict[str, Any]:
	"""为已绑定企微的员工创建系统 User 并回写 user_id。"""
	_require_hr_manager()
	return provision_system_users_for_wecom_employees(
		limit=cint(limit),
		fetch_remote_profile=bool(cint(fetch_remote_profile)),
		commit_every=20,
	)


@frappe.whitelist(methods=["POST"])
def run_attendance_sync(
	start_date: str,
	end_date: str,
	build_deductions: int | str = 0,
) -> dict[str, Any]:
	_require_hr_manager()
	return sync_attendance_period(
		start_date, end_date, build_deductions=bool(cint(build_deductions))
	)


@frappe.whitelist(methods=["POST"])
def send_test_message(userid: str, content: str = "人事系统企业微信连接测试成功") -> dict[str, Any]:
	_require_hr_manager()
	return send_text(userid, content)


@frappe.whitelist(methods=["POST"])
def send_test_textcard(
	userid: str,
	title: str = "人事系统测试卡片",
	description: str = "点击打开 HR 首页（需已配置免登可信域名）",
	next_path: str = "/app/hr-home",
) -> dict[str, Any]:
	_require_hr_manager()
	from .oauth import build_authorize_url

	return send_textcard(
		userid,
		title=title,
		description=description,
		url=build_authorize_url(next_path=next_path),
		btntxt="打开",
	)


@frappe.whitelist(methods=["POST"])
def send_test_robot_message(content: str = "人事系统企业微信群机器人连接测试成功") -> dict[str, Any]:
	_require_hr_manager()
	return send_robot_text(content)
