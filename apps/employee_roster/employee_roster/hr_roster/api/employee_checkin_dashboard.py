# Copyright (c) 2026 stillgroup
# License: MIT
"""员工打卡 List View 顶部统计 + 日汇总（日出勤结果/时长/最早上班/最晚下班）。

统计卡按「人」去重，口径可重叠：
- 出勤：筛选范围内有打卡记录的人（含迟到、缺卡），是另外三项的超集
- 上下班打卡：至少有一天同时有 IN 与 OUT
- 迟到：至少有一天最早上班时间晚于规则上班时间(shift_start)
- 缺卡：至少有一天缺少上班(IN)或下班(OUT)

表格「日出勤结果」仍互斥：缺卡 > 迟到 > 出勤（完整打卡且未迟到）。
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

import frappe
from frappe.utils import get_datetime, get_timespan_date_range, getdate


RESULT_PRESENT = "出勤"
RESULT_LATE = "迟到"
RESULT_MISSING = "缺卡"


def _hhmm(dt) -> str:
	if not dt:
		return ""
	return get_datetime(dt).strftime("%H:%M")


@frappe.whitelist()
def get_checkin_dashboard(
	timespan: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
) -> dict:
	"""按时间范围聚合打卡日汇总，供 List View 统计卡与表格列使用。"""
	start_dt, end_dt = _resolve_range(timespan, from_date, to_date)
	summaries = _build_day_summaries(start_dt, end_dt)
	stats, employees_by_result = _aggregate_stats(summaries)
	# key: "employee|YYYY-MM-DD" → 日汇总，前端按打卡行的 employee+date 回填列
	by_key = {f"{s['employee']}|{s['attendance_date']}": s for s in summaries}
	return {
		"stats": stats,
		"summaries": by_key,
		"employees_by_result": employees_by_result,
		"range": {
			"from": start_dt.isoformat(sep=" ") if start_dt else None,
			"to": end_dt.isoformat(sep=" ") if end_dt else None,
			"timespan": timespan,
		},
	}


def _resolve_range(
	timespan: str | None,
	from_date: str | None,
	to_date: str | None,
) -> tuple[datetime | None, datetime | None]:
	if timespan:
		# Frappe 标准 Timespan：today / this week / this month ...
		span = get_timespan_date_range(timespan)
		if span:
			start, end = span
			return get_datetime(start), get_datetime(end) + timedelta(days=1) - timedelta(seconds=1)

	if from_date and to_date:
		start = get_datetime(from_date)
		end = get_datetime(to_date)
		# 若只传日期，把结束日扩到当天 23:59:59
		if len(str(to_date)) <= 10:
			end = get_datetime(getdate(to_date)) + timedelta(days=1) - timedelta(seconds=1)
		return start, end

	# 无时间筛选（全部）：不截断，由调用方自行承担数据量
	return None, None


def _build_day_summaries(start_dt: datetime | None, end_dt: datetime | None) -> list[dict]:
	filters: dict = {}
	if start_dt and end_dt:
		filters["time"] = ["between", [start_dt, end_dt]]

	logs = frappe.get_all(
		"Employee Checkin",
		filters=filters,
		fields=[
			"name",
			"employee",
			"employee_name",
			"time",
			"log_type",
			"shift",
			"shift_start",
			"shift_end",
		],
		order_by="time asc",
		limit_page_length=None,
	)
	if not logs:
		return []

	grouped: dict[tuple[str, str], list] = defaultdict(list)
	for log in logs:
		d = getdate(log.time)
		grouped[(log.employee, str(d))].append(log)

	shift_start_cache: dict[str, object] = {}
	summaries: list[dict] = []
	for (employee, day), day_logs in grouped.items():
		summaries.append(_summarize_employee_day(employee, day, day_logs, shift_start_cache))
	return summaries


def _summarize_employee_day(
	employee: str,
	day: str,
	day_logs: list,
	shift_start_cache: dict,
) -> dict:
	in_logs = [l for l in day_logs if l.log_type == "IN"]
	out_logs = [l for l in day_logs if l.log_type == "OUT"]

	# 无明确 Log Type 时，按时间首尾兜底（兼容历史数据）
	if not in_logs and not out_logs and day_logs:
		in_logs = [day_logs[0]]
		out_logs = [day_logs[-1]] if len(day_logs) > 1 else []

	first_in = min((l.time for l in in_logs), default=None)
	last_out = max((l.time for l in out_logs), default=None)
	has_in = bool(in_logs)
	has_out = bool(out_logs)
	has_both = has_in and has_out

	# 规则上班时间：优先打卡行上的 shift_start，否则取班次 start_time + 当天日期
	rule_start = None
	for l in day_logs:
		if l.shift_start:
			rule_start = get_datetime(l.shift_start)
			break
	if not rule_start:
		shift_name = next((l.shift for l in day_logs if l.shift), None)
		rule_start = _shift_start_on_date(shift_name, day, shift_start_cache)

	is_late = False
	if has_in and rule_start and first_in and get_datetime(first_in) > get_datetime(rule_start):
		is_late = True

	# 缺卡优先于迟到
	if not has_both:
		result = RESULT_MISSING
	elif is_late:
		result = RESULT_LATE
	else:
		result = RESULT_PRESENT

	work_hours = 0.0
	if first_in and last_out:
		delta = get_datetime(last_out) - get_datetime(first_in)
		work_hours = round(float(delta.total_seconds()) / 3600, 2)

	return {
		"employee": employee,
		"employee_name": day_logs[0].employee_name,
		"attendance_date": day,
		"result": result,
		"work_hours": work_hours,
		"first_in": _hhmm(first_in),
		"last_out": _hhmm(last_out),
		"first_in_dt": str(first_in) if first_in else None,
		"last_out_dt": str(last_out) if last_out else None,
		"has_both_punches": has_both,
		"is_late": is_late,
		"rule_start": str(rule_start) if rule_start else None,
	}


def _shift_start_on_date(shift_name: str | None, day: str, cache: dict):
	if not shift_name:
		return None
	if shift_name not in cache:
		cache[shift_name] = frappe.db.get_value("Shift Type", shift_name, "start_time")
	start_time = cache[shift_name]
	if not start_time:
		return None
	day_date = getdate(day)
	if isinstance(start_time, timedelta):
		return datetime.combine(day_date, (datetime.min + start_time).time())
	if hasattr(start_time, "hour"):
		return datetime.combine(day_date, start_time)
	return get_datetime(f"{day} {start_time}")


def _aggregate_stats(summaries: list[dict]) -> tuple[dict, dict]:
	"""人数按员工去重。出勤含迟到/缺卡，因此出勤 >= 上下班打卡。"""
	present = {s["employee"] for s in summaries}
	late = {s["employee"] for s in summaries if s["is_late"]}
	missing = {s["employee"] for s in summaries if s["result"] == RESULT_MISSING}
	both = {s["employee"] for s in summaries if s["has_both_punches"]}
	employees_by_result = {
		RESULT_PRESENT: sorted(present),
		RESULT_LATE: sorted(late),
		RESULT_MISSING: sorted(missing),
		"both_punches": sorted(both),
	}
	return {
		"present": len(present),
		"both_punches": len(both),
		"late": len(late),
		"missing": len(missing),
		"total_employee_days": len(summaries),
	}, employees_by_result
