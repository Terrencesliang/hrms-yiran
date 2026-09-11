"""企业微信定时同步任务。"""
from __future__ import annotations

import frappe
from frappe.utils import add_days, get_first_day, nowdate

from employee_roster.integrations.wecom.attendance import (
	build_deduction_drafts,
	sync_checkins,
	sync_daily_attendance,
	sync_monthly_report,
)
from employee_roster.integrations.wecom.client import WeComConfigurationError
from employee_roster.integrations.wecom.service import sync_contacts


def _configured() -> bool:
	try:
		from employee_roster.integrations.wecom.client import WeComConfig

		WeComConfig.load()
		return True
	except WeComConfigurationError:
		return False


def sync_recent_attendance() -> None:
	if not _configured():
		return
	today = nowdate()
	try:
		sync_checkins(add_days(today, -2), today)
		sync_daily_attendance(add_days(today, -2), add_days(today, -1))
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "企业微信近期考勤同步失败")


def sync_contacts_daily() -> None:
	if not _configured():
		return
	try:
		sync_contacts()
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "企业微信通讯录同步失败")


def prepare_previous_month_deductions() -> None:
	"""每月 2 日生成上月扣款草稿，保留人工复核和提交环节。"""
	if not _configured():
		return
	this_month = get_first_day(nowdate())
	start = get_first_day(add_days(this_month, -1))
	end = add_days(this_month, -1)
	try:
		sync_checkins(start, end)
		sync_daily_attendance(start, end)
		sync_monthly_report(start, end)
		build_deduction_drafts(start, end)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "企业微信月度考勤扣款草稿生成失败")


def recent_attendance_error() -> dict | None:
	rows = frappe.get_all(
		"Error Log",
		filters={"method": "企业微信近期考勤同步失败"},
		fields=["creation", "error"],
		order_by="creation desc",
		limit=1,
	)
	if not rows:
		return None
	return {"creation": rows[0].creation, "error": str(rows[0].error or "")[-1000:]}
