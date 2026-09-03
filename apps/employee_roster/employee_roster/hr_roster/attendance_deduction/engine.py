# Copyright (c) 2026 stillgroup
# License: MIT
"""月度考勤指标采集与扣款计算引擎。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

import frappe
from frappe.utils import flt, getdate

from employee_roster.hr_roster.doctype.attendance_group.attendance_group import get_employee_deduction_rule


@dataclass
class AttendanceMetrics:
	late_entries: list[dict] = field(default_factory=list)
	early_exits: list[dict] = field(default_factory=list)
	missing_punches: list[dict] = field(default_factory=list)
	absents: list[dict] = field(default_factory=list)

	@property
	def late_entry_count(self) -> int:
		return len(self.late_entries)

	@property
	def late_entry_minutes(self) -> float:
		return sum(flt(r.get("minutes")) for r in self.late_entries)

	@property
	def early_exit_count(self) -> int:
		return len(self.early_exits)

	@property
	def early_exit_minutes(self) -> float:
		return sum(flt(r.get("minutes")) for r in self.early_exits)

	@property
	def missing_punch_count(self) -> int:
		return len(self.missing_punches)

	@property
	def absent_count(self) -> int:
		return len(self.absents)

	@property
	def absent_hours(self) -> float:
		return sum(flt(r.get("hours")) for r in self.absents)


def collect_attendance_metrics(employee: str, start_date, end_date) -> AttendanceMetrics:
	start_date = getdate(start_date)
	end_date = getdate(end_date)
	metrics = AttendanceMetrics()

	attendance_rows = frappe.get_all(
		"Attendance",
		filters={
			"employee": employee,
			"docstatus": 1,
			"attendance_date": ["between", [start_date, end_date]],
		},
		fields=[
			"name",
			"attendance_date",
			"status",
			"shift",
			"late_entry",
			"early_exit",
			"in_time",
			"out_time",
			"working_hours",
		],
		order_by="attendance_date asc",
	)

	shift_cache: dict[str, dict] = {}
	for row in attendance_rows:
		shift = _get_shift(row.shift, shift_cache)
		if row.late_entry and row.in_time and shift:
			minutes = _late_minutes(row.in_time, shift)
			if minutes > 0:
				metrics.late_entries.append(
					{"date": row.attendance_date, "minutes": minutes, "attendance": row.name}
				)
		if row.early_exit and row.out_time and shift:
			minutes = _early_minutes(row.out_time, shift)
			if minutes > 0:
				metrics.early_exits.append(
					{"date": row.attendance_date, "minutes": minutes, "attendance": row.name}
				)
		if row.status == "Absent":
			hours = flt(row.working_hours) or flt(shift.get("standard_working_hours") if shift else 8) or 8
			metrics.absents.append({"date": row.attendance_date, "hours": hours, "attendance": row.name})

	attended_dates = {getdate(r.attendance_date) for r in attendance_rows}
	checkins = frappe.get_all(
		"Employee Checkin",
		filters={
			"employee": employee,
			"time": ["between", [start_date, end_date + timedelta(days=1)]],
		},
		fields=["name", "time", "log_type", "shift"],
		order_by="time asc",
	)
	checkins_by_date: dict = {}
	for log in checkins:
		d = getdate(log.time)
		if d < start_date or d > end_date:
			continue
		checkins_by_date.setdefault(d, []).append(log)

	for d, logs in checkins_by_date.items():
		types = {l.log_type for l in logs}
		if "IN" in types and "OUT" not in types:
			metrics.missing_punches.append({"date": d, "reason": "missing_out"})
		elif "OUT" in types and "IN" not in types:
			metrics.missing_punches.append({"date": d, "reason": "missing_in"})

	for d in _scheduled_dates_without_leave(employee, start_date, end_date, attended_dates):
		if d not in checkins_by_date:
			metrics.missing_punches.append({"date": d, "reason": "no_checkin_no_attendance"})

	return metrics


def _scheduled_dates_without_leave(employee, start_date, end_date, attended_dates) -> list:
	"""应出勤但未生成 Attendance 的工作日（排除请假）。"""
	from hrms.hr.utils import get_holidays_for_employee

	holiday_rows = get_holidays_for_employee(employee, start_date, end_date, raise_exception=False) or []
	holidays = {getdate(h["holiday_date"]) for h in holiday_rows}
	leave_dates = set(
		frappe.get_all(
			"Leave Application",
			filters={
				"employee": employee,
				"docstatus": 1,
				"from_date": ["<=", end_date],
				"to_date": [">=", start_date],
				"status": "Approved",
			},
			pluck="name",
		)
	)
	_ = leave_dates  # reserved for future strict leave-day lookup
	leave_day_set: set = set()
	for la in frappe.get_all(
		"Leave Application",
		filters={
			"employee": employee,
			"docstatus": 1,
			"from_date": ["<=", end_date],
			"to_date": [">=", start_date],
			"status": "Approved",
		},
		fields=["from_date", "to_date"],
	):
		cur = getdate(la.from_date)
		end = getdate(la.to_date)
		while cur <= end:
			if start_date <= cur <= end_date:
				leave_day_set.add(cur)
			cur += timedelta(days=1)

	missing = []
	cur = start_date
	while cur <= end_date:
		if cur.weekday() < 5 and cur not in holidays and cur not in attended_dates and cur not in leave_day_set:
			missing.append(cur)
		cur += timedelta(days=1)
	return missing


def _get_shift(shift_name: str | None, cache: dict) -> dict | None:
	if not shift_name:
		return None
	if shift_name not in cache:
		fields = [
			"name",
			"start_time",
			"end_time",
			"late_entry_grace_period",
			"early_exit_grace_period",
			"enable_late_entry_marking",
			"enable_early_exit_marking",
		]
		meta = frappe.get_meta("Shift Type")
		if meta.has_field("standard_working_hours"):
			fields.append("standard_working_hours")
		cache[shift_name] = frappe.db.get_value(
			"Shift Type",
			shift_name,
			fields,
			as_dict=True,
		)
	return cache.get(shift_name)


def _late_minutes(in_time, shift: dict) -> float:
	grace = int(shift.get("late_entry_grace_period") or 0)
	in_time = _as_datetime(in_time)
	start = _combine_datetime(in_time, shift.get("start_time"))
	if not in_time or not start:
		return 0
	threshold = start + timedelta(minutes=grace)
	delta = in_time - threshold
	return max(delta.total_seconds() / 60, 0)


def _early_minutes(out_time, shift: dict) -> float:
	grace = int(shift.get("early_exit_grace_period") or 0)
	out_time = _as_datetime(out_time)
	end = _combine_datetime(out_time, shift.get("end_time"))
	if not out_time or not end:
		return 0
	threshold = end - timedelta(minutes=grace)
	delta = threshold - out_time
	return max(delta.total_seconds() / 60, 0)


def _as_datetime(dt):
	from frappe.utils import get_datetime

	if not dt:
		return None
	return get_datetime(dt)


def _combine_datetime(dt, time_value):
	from datetime import datetime, time as time_cls

	if not dt or time_value is None:
		return None
	d = getdate(dt)
	if isinstance(time_value, timedelta):
		return datetime.combine(d, time_cls.min) + time_value
	if hasattr(time_value, "hour") and hasattr(time_value, "minute"):
		return datetime.combine(d, time_value)
	from frappe.utils import get_datetime

	return get_datetime(f"{d} {time_value}")


def calculate_deductions(rule_name: str, metrics: AttendanceMetrics, employee: str, end_date) -> tuple[list[dict], float]:
	rule = frappe.get_doc("Attendance Deduction Rule", rule_name)
	lines: list[dict] = []
	total = 0.0

	for item in rule.rule_items:
		if not item.enabled:
			continue
		item_lines, amount = _calc_item(item, rule, metrics, employee, end_date)
		lines.extend(item_lines)
		total += amount

	return lines, flt(total, 2)


def _calc_item(item, rule, metrics: AttendanceMetrics, employee: str, end_date) -> tuple[list[dict], float]:
	mode = item.calc_mode
	item_type = item.item_type

	if mode == "None":
		return [], 0

	if mode == "Per Minute":
		return _calc_per_minute(item_type, item, metrics)

	if mode == "Salary Percent":
		return _calc_salary_percent(item_type, item, metrics, employee, end_date)

	if mode == "Tiered":
		return _calc_tiered(item_type, rule, metrics)

	return [], 0


def _calc_per_minute(item_type: str, item, metrics: AttendanceMetrics) -> tuple[list[dict], float]:
	rate = flt(item.rate_per_minute)
	if rate <= 0:
		return [], 0
	if item_type == "Late Entry":
		minutes = metrics.late_entry_minutes
	elif item_type == "Early Exit":
		minutes = metrics.early_exit_minutes
	else:
		return [], 0
	amount = minutes * rate
	if amount <= 0:
		return [], 0
	return [
		{
			"item_type": item_type,
			"occurrence_date": None,
			"metric_value": minutes,
			"metric_unit": "minutes",
			"tier_label": f"Per Minute × {rate}",
			"deduction_amount": amount,
			"remarks": f"Total {minutes:.0f} minutes",
		}
	], amount


def _calc_salary_percent(item_type: str, item, metrics: AttendanceMetrics, employee: str, end_date) -> tuple[list[dict], float]:
	if item_type != "Absent" or metrics.absent_count == 0:
		return [], 0
	base = _get_base_salary(employee, end_date, item.base_salary_component)
	percent = flt(item.salary_percent)
	amount = base * percent / 100 * metrics.absent_count
	return [
		{
			"item_type": item_type,
			"occurrence_date": None,
			"metric_value": metrics.absent_count,
			"metric_unit": "count",
			"tier_label": f"{percent}% of base × {metrics.absent_count}",
			"deduction_amount": amount,
			"remarks": f"Base salary {base}",
		}
	], amount


def _get_base_salary(employee: str, date, component: str | None) -> float:
	from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
		get_assigned_salary_structure,
	)

	structure = get_assigned_salary_structure(employee, date)
	if not structure:
		return 0
	rows = frappe.get_all(
		"Salary Detail",
		filters={"parent": structure, "parenttype": "Salary Structure"},
		fields=["salary_component", "amount"],
	)
	if component:
		for row in rows:
			if row.salary_component == component:
				return flt(row.amount)
	for row in rows:
		if frappe.db.get_value("Salary Component", row.salary_component, "type") == "Earning":
			return flt(row.amount)
	return 0


def _calc_tiered(item_type: str, rule, metrics: AttendanceMetrics) -> tuple[list[dict], float]:
	tiers = rule.get_tiers_for_item(item_type)
	if not tiers:
		return [], 0
	lines: list[dict] = []
	total = 0.0

	if item_type == "Late Entry":
		for occ in metrics.late_entries:
			amt, label = _match_tier(tiers, occ["minutes"], "Per Occurrence Minutes")
			if amt > 0:
				lines.append(_line(item_type, occ["date"], occ["minutes"], "minutes", label, amt))
				total += amt
	elif item_type == "Early Exit":
		for occ in metrics.early_exits:
			amt, label = _match_tier(tiers, occ["minutes"], "Per Occurrence Minutes")
			if amt > 0:
				lines.append(_line(item_type, occ["date"], occ["minutes"], "minutes", label, amt))
				total += amt
	elif item_type == "Missing Punch":
		count = metrics.missing_punch_count
		amt, label = _match_tier(tiers, count, "Monthly Count")
		if amt > 0:
			lines.append(_line(item_type, None, count, "monthly_count", label, amt, f"{count} times in period"))
			total += amt
	elif item_type == "Absent":
		for occ in metrics.absents:
			amt, label = _match_tier(tiers, occ["hours"], "Occurrence Hours")
			if amt > 0:
				lines.append(_line(item_type, occ["date"], occ["hours"], "hours", label, amt))
				total += amt

	return lines, total


def _match_tier(tiers: list[dict], value: float, unit: str) -> tuple[float, str]:
	value = flt(value)
	for tier in tiers:
		if tier.get("tier_unit") != unit:
			continue
		min_v = flt(tier.get("min_value"))
		max_v = flt(tier.get("max_value"))
		if value < min_v:
			continue
		if max_v and value > max_v:
			continue
		amount = flt(tier.get("amount"))
		if tier.get("deduction_type") == "Per Unit Amount":
			deduction = value * amount
			label = f"{min_v}-{max_v or '∞'} {unit}, {amount}/unit"
		else:
			deduction = amount
			label = f"{min_v}-{max_v or '∞'} {unit}, fixed {amount}"
		return deduction, label
	return 0, ""


def _line(item_type, date, metric, unit, label, amount, remarks=None) -> dict:
	return {
		"item_type": item_type,
		"occurrence_date": date,
		"metric_value": metric,
		"metric_unit": unit,
		"tier_label": label,
		"deduction_amount": amount,
		"remarks": remarks or "",
	}


@frappe.whitelist()
def preview_deduction(employee: str, start_date: str, end_date: str) -> dict:
	rule_name = get_employee_deduction_rule(employee)
	if not rule_name:
		frappe.throw("Employee is not assigned to an active Attendance Group with a rule")
	metrics = collect_attendance_metrics(employee, start_date, end_date)
	lines, total = calculate_deductions(rule_name, metrics, employee, end_date)
	return {
		"rule": rule_name,
		"metrics": {
			"late_entry_count": metrics.late_entry_count,
			"late_entry_minutes": metrics.late_entry_minutes,
			"early_exit_count": metrics.early_exit_count,
			"early_exit_minutes": metrics.early_exit_minutes,
			"missing_punch_count": metrics.missing_punch_count,
			"absent_count": metrics.absent_count,
			"absent_hours": metrics.absent_hours,
		},
		"lines": lines,
		"total_deduction": total,
	}


def create_or_update_summary(
	employee: str,
	start_date,
	end_date,
	payroll_entry: str | None = None,
	submit: bool = True,
) -> frappe.model.document.Document:
	start_date = getdate(start_date)
	end_date = getdate(end_date)

	group_row = frappe.get_all(
		"Attendance Group Member",
		filters={"employee": employee, "parenttype": "Attendance Group"},
		fields=["parent"],
		limit=1,
	)
	if not group_row:
		frappe.throw(f"No Attendance Group for employee {employee}")

	group = frappe.get_doc("Attendance Group", group_row[0].parent)
	if not group.is_active or not group.deduction_rule:
		frappe.throw(f"Attendance Group {group.name} is inactive or has no rule")

	existing = frappe.get_all(
		"Attendance Deduction Summary",
		filters={
			"employee": employee,
			"start_date": start_date,
			"end_date": end_date,
			"docstatus": ["<", 2],
		},
		pluck="name",
		limit=1,
	)

	metrics = collect_attendance_metrics(employee, start_date, end_date)
	lines, total = calculate_deductions(group.deduction_rule, metrics, employee, end_date)

	if existing:
		old = frappe.get_doc("Attendance Deduction Summary", existing[0])
		if old.docstatus == 1:
			old.cancel()
		frappe.delete_doc("Attendance Deduction Summary", old.name, force=1)

	doc = frappe.new_doc("Attendance Deduction Summary")

	doc.update(
		{
			"employee": employee,
			"start_date": start_date,
			"end_date": end_date,
			"posting_date": end_date,
			"attendance_group": group.name,
			"deduction_rule": group.deduction_rule,
			"payroll_entry": payroll_entry,
			"late_entry_count": metrics.late_entry_count,
			"late_entry_minutes": metrics.late_entry_minutes,
			"early_exit_count": metrics.early_exit_count,
			"early_exit_minutes": metrics.early_exit_minutes,
			"missing_punch_count": metrics.missing_punch_count,
			"absent_count": metrics.absent_count,
			"absent_hours": metrics.absent_hours,
			"total_deduction": total,
		}
	)
	doc.set("deduction_lines", lines)
	doc.save()

	if submit:
		doc.submit()

	return doc
