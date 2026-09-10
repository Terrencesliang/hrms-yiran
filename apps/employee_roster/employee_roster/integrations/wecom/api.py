"""企业微信集成的管理端接口。"""
from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from .attendance import sync_attendance_period
from .client import configuration_status
from .service import (
	bind_employee_userids_by_mobile,
	send_robot_text,
	send_text,
	sync_contacts,
)


def _require_hr_manager() -> None:
	if "HR Manager" not in frappe.get_roles():
		frappe.throw("仅人事经理可执行企业微信同步", frappe.PermissionError)


@frappe.whitelist()
def get_configuration_status() -> dict[str, Any]:
	_require_hr_manager()
	return configuration_status()


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
def send_test_robot_message(content: str = "人事系统企业微信群机器人连接测试成功") -> dict[str, Any]:
	_require_hr_manager()
	return send_robot_text(content)
