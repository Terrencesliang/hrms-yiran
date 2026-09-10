"""企业微信打卡流水、日报与扣款汇总衔接。"""
from __future__ import annotations

import hashlib
from datetime import date, datetime, time, timedelta
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import get_system_timezone, getdate, now_datetime

from employee_roster.hr_roster.attendance_deduction.engine import create_or_update_summary

from .client import WeComClient


def _chunks(items: list[str], size: int = 100) -> Iterable[list[str]]:
	for index in range(0, len(items), size):
		yield items[index : index + size]


def _employees_by_userid() -> dict[str, str]:
	return {
		str(row.hr_wecom_id): str(row.name)
		for row in frappe.get_all(
			"Employee",
			filters={"status": "Active", "hr_wecom_id": ["is", "set"]},
			fields=["name", "hr_wecom_id"],
		)
		if row.hr_wecom_id
	}


def _timestamp(value: date | datetime, *, end_of_day: bool = False) -> int:
	day = getdate(value)
	dt = datetime.combine(
		day, time.max if end_of_day else time.min, tzinfo=ZoneInfo(get_system_timezone())
	)
	return int(dt.timestamp())


def _local_datetime(timestamp: int) -> datetime:
	return datetime.fromtimestamp(
		timestamp, ZoneInfo(get_system_timezone())
	).replace(tzinfo=None)


def _record_id(row: dict[str, Any]) -> str:
	parts = (
		row.get("userid"),
		row.get("checkin_time"),
		row.get("checkin_type"),
		row.get("deviceid"),
		row.get("groupid"),
		row.get("schedule_id"),
		row.get("timeline_id"),
	)
	return hashlib.sha256("|".join(str(item or "") for item in parts).encode()).hexdigest()


def _log_type(value: str) -> str:
	if value == "上班打卡":
		return "IN"
	if value == "下班打卡":
		return "OUT"
	return ""


def sync_checkins(
	start_date: str | date,
	end_date: str | date,
	*,
	client: WeComClient | None = None,
) -> dict[str, Any]:
	start = getdate(start_date)
	end = getdate(end_date)
	if end < start:
		raise frappe.ValidationError("企微打卡同步结束日期不能早于开始日期")
	client = client or WeComClient()
	employee_map = _employees_by_userid()
	created = duplicate = skipped = 0
	for window_start in (
		start + timedelta(days=offset) for offset in range(0, (end - start).days + 1, 30)
	):
		window_end = min(end, window_start + timedelta(days=29))
		for userids in _chunks(list(employee_map)):
			for row in client.get_checkin_data(
				userids, _timestamp(window_start), _timestamp(window_end, end_of_day=True)
			):
				employee = employee_map.get(str(row.get("userid") or ""))
				log_type = _log_type(str(row.get("checkin_type") or ""))
				checkin_time = int(row.get("checkin_time") or 0)
				if not employee or not log_type or not checkin_time:
					skipped += 1
					continue
				record_id = _record_id(row)
				if frappe.db.exists("Employee Checkin", {"wecom_record_id": record_id}):
					duplicate += 1
					continue
				frappe.get_doc(
					{
						"doctype": "Employee Checkin",
						"employee": employee,
						"time": _local_datetime(checkin_time),
						"log_type": log_type,
						"device_id": str(row.get("deviceid") or "")[:140],
						"checkin_type": (
							"外勤打卡"
							if str(row.get("checkin_type") or "") == "外出打卡"
							else "办公地点"
						),
						"wecom_record_id": record_id,
						"wecom_exception_type": str(row.get("exception_type") or "")[:140],
						"wecom_group_id": str(row.get("groupid") or ""),
						"wecom_raw_data": frappe.as_json(row),
					}
				).insert(ignore_permissions=True)
				created += 1
	return {"created": created, "duplicate": duplicate, "skipped": skipped}


def _day_datetime(day: date, seconds: int | None) -> datetime | None:
	if not seconds:
		return None
	return datetime.combine(day, time.min) + timedelta(seconds=int(seconds))


def _apply_daily_row(row: dict[str, Any], employee_map: dict[str, str]) -> str:
	base = row.get("base_info") or {}
	summary = row.get("summary_info") or {}
	userid = str(base.get("acctid") or "")
	employee = employee_map.get(userid)
	report_timestamp = int(base.get("date") or 0)
	if not employee or not report_timestamp:
		return "skipped"
	attendance_date = _local_datetime(report_timestamp).date()
	daily_key = f"{userid}:{attendance_date.isoformat()}"
	exceptions = {
		int(item.get("exception") or 0): item
		for item in row.get("exception_infos") or []
	}
	standard_seconds = int(summary.get("standard_work_sec") or 0)
	checkin_count = int(summary.get("checkin_count") or 0)
	# 休息日不制造“出勤”，有假勤审批的无打卡日交给 HRMS 请假流程生成 Attendance。
	if checkin_count == 0 and (
		standard_seconds == 0 or bool(row.get("holiday_infos"))
	):
		return "skipped"
	status = "Absent" if 4 in exceptions or (standard_seconds > 0 and checkin_count == 0) else "Present"
	values = {
		"status": status,
		"working_hours": float(summary.get("regular_work_sec") or 0) / 3600,
		"in_time": _day_datetime(attendance_date, summary.get("earliest_time")),
		"out_time": _day_datetime(attendance_date, summary.get("lastest_time")),
		"late_entry": int(1 in exceptions),
		"early_exit": int(2 in exceptions),
		"wecom_raw_data": frappe.as_json(row),
	}
	existing = frappe.db.get_value(
		"Attendance", {"employee": employee, "attendance_date": attendance_date}, "name"
	)
	if existing:
		doc = frappe.get_doc("Attendance", existing)
		if getattr(doc, "wecom_daily_key", "") != daily_key:
			return "conflict"
		if doc.docstatus == 1:
			return "unchanged"
		doc.update(values)
		doc.save(ignore_permissions=True)
		doc.submit()
		return "updated"
	doc = frappe.get_doc(
		{
			"doctype": "Attendance",
			"employee": employee,
			"attendance_date": attendance_date,
			"wecom_daily_key": daily_key,
			**values,
		}
	).insert(ignore_permissions=True)
	doc.submit()
	return "created"


def sync_daily_attendance(
	start_date: str | date,
	end_date: str | date,
	*,
	client: WeComClient | None = None,
) -> dict[str, Any]:
	start = getdate(start_date)
	end = getdate(end_date)
	if end < start:
		raise frappe.ValidationError("企微日报同步结束日期不能早于开始日期")
	client = client or WeComClient()
	employee_map = _employees_by_userid()
	result = {"created": 0, "updated": 0, "unchanged": 0, "conflict": 0, "skipped": 0}
	for userids in _chunks(list(employee_map)):
		rows = client.get_checkin_daydata(
			userids, _timestamp(start), _timestamp(end)
		)
		for row in rows:
			result[_apply_daily_row(row, employee_map)] += 1
	return result


def fetch_monthly_report(
	start_date: str | date,
	end_date: str | date,
	*,
	client: WeComClient | None = None,
) -> list[dict[str, Any]]:
	start = getdate(start_date)
	end = getdate(end_date)
	client = client or WeComClient()
	rows: list[dict[str, Any]] = []
	for userids in _chunks(list(_employees_by_userid())):
		rows.extend(
			client.get_checkin_monthdata(
				userids, _timestamp(start), _timestamp(end)
			)
		)
	return rows


def sync_monthly_report(
	start_date: str | date,
	end_date: str | date,
	*,
	client: WeComClient | None = None,
) -> dict[str, Any]:
	start = getdate(start_date)
	end = getdate(end_date)
	employee_map = _employees_by_userid()
	created = updated = skipped = 0
	for row in fetch_monthly_report(start, end, client=client):
		base = row.get("base_info") or {}
		summary = row.get("summary_info") or {}
		userid = str(base.get("acctid") or "")
		employee = employee_map.get(userid)
		if not employee:
			skipped += 1
			continue
		exceptions = {
			int(item.get("exception") or 0): item
			for item in row.get("exception_infos") or []
		}

		def exception_value(code: int, fieldname: str) -> float:
			return float((exceptions.get(code) or {}).get(fieldname) or 0)

		report_key = f"{userid}:{start.isoformat()}:{end.isoformat()}"
		values = {
			"employee": employee,
			"wecom_userid": userid,
			"start_date": start,
			"end_date": end,
			"work_days": int(summary.get("work_days") or 0),
			"regular_days": int(summary.get("regular_days") or 0),
			"rest_days": int(summary.get("rest_days") or 0),
			"except_days": int(summary.get("except_days") or 0),
			"regular_work_hours": float(summary.get("regular_work_sec") or 0) / 3600,
			"standard_work_hours": float(summary.get("standard_work_sec") or 0) / 3600,
			"late_count": int(exception_value(1, "count")),
			"late_minutes": exception_value(1, "duration") / 60,
			"early_count": int(exception_value(2, "count")),
			"early_minutes": exception_value(2, "duration") / 60,
			"missing_punch_count": int(exception_value(3, "count")),
			"absent_count": int(exception_value(4, "count")),
			"absent_hours": exception_value(4, "duration") / 3600,
			"raw_data": frappe.as_json(row),
			"last_synced_on": now_datetime(),
		}
		if frappe.db.exists("WeCom Attendance Monthly", report_key):
			doc = frappe.get_doc("WeCom Attendance Monthly", report_key)
			doc.update(values)
			doc.save(ignore_permissions=True)
			updated += 1
		else:
			frappe.get_doc(
				{
					"doctype": "WeCom Attendance Monthly",
					"report_key": report_key,
					**values,
				}
			).insert(ignore_permissions=True)
			created += 1
	return {"created": created, "updated": updated, "skipped": skipped}


def build_deduction_drafts(start_date: str | date, end_date: str | date) -> dict[str, Any]:
	"""基于已提交企微日报创建扣款草稿；绝不替换已提交汇总。"""
	start = getdate(start_date)
	end = getdate(end_date)
	created = skipped = failed = 0
	errors: list[dict[str, str]] = []
	for employee in _employees_by_userid().values():
		submitted = frappe.db.exists(
			"Attendance Deduction Summary",
			{
				"employee": employee,
				"start_date": start,
				"end_date": end,
				"docstatus": 1,
			},
		)
		if submitted:
			skipped += 1
			continue
		try:
			create_or_update_summary(employee, start, end, submit=False)
			created += 1
		except Exception as exc:
			failed += 1
			errors.append({"employee": employee, "error": str(exc)[:300]})
	return {"created": created, "skipped": skipped, "failed": failed, "errors": errors[:50]}


def sync_attendance_period(
	start_date: str | date,
	end_date: str | date,
	*,
	build_deductions: bool = False,
) -> dict[str, Any]:
	client = WeComClient()
	result: dict[str, Any] = {
		"checkins": sync_checkins(start_date, end_date, client=client),
		"daily_attendance": sync_daily_attendance(start_date, end_date, client=client),
		"monthly_report": sync_monthly_report(start_date, end_date, client=client),
		"synced_on": now_datetime(),
	}
	if build_deductions:
		result["deduction_drafts"] = build_deduction_drafts(start_date, end_date)
	return result
