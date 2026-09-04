# Copyright (c) 2026 stillgroup
# License: MIT
"""Payroll Entry 与 Salary Slip 集成。"""
import frappe
from frappe import _
from frappe.utils import flt

from employee_roster.hr_roster.attendance_deduction.engine import create_or_update_summary
from employee_roster.hr_roster.doctype.attendance_deduction_settings.attendance_deduction_settings import (
	get_attendance_deduction_settings,
)
from employee_roster.hr_roster.doctype.attendance_group.attendance_group import get_employee_deduction_rule


@frappe.whitelist()
def create_attendance_deduction_summaries(payroll_entry: str) -> None:
	"""从 Payroll Entry 批量生成并提交考勤扣款汇总。"""
	doc = frappe.get_doc("Payroll Entry", payroll_entry)
	doc.check_permission("write")

	employees = [row.employee for row in doc.employees]
	created = 0
	skipped = 0
	errors = []

	for employee in employees:
		if not get_employee_deduction_rule(employee):
			skipped += 1
			continue
		try:
			create_or_update_summary(
				employee,
				doc.start_date,
				doc.end_date,
				payroll_entry=doc.name,
				submit=True,
			)
			created += 1
		except Exception as exc:
			errors.append(f"{employee}: {exc}")

	msg = _("Created {0} attendance deduction summaries, skipped {1} (no group/rule).").format(created, skipped)
	if errors:
		msg += "<br>" + "<br>".join(errors[:5])
	frappe.msgprint(msg, indicator="green" if created else "orange", alert=True)


def adjust_salary_slip_payment_days(doc, method=None):
	"""旷工仅走扣款规则时，不把旷工重复扣计薪天数。"""
	settings = get_attendance_deduction_settings()
	if settings.get("absent_affects_payment_days"):
		return
	if not get_employee_deduction_rule(doc.employee):
		return
	if flt(doc.absent_days) > 0:
		doc.payment_days = flt(doc.payment_days) + flt(doc.absent_days)
		doc.absent_days = 0


def on_payroll_entry_submit(doc, method=None):
	settings = get_attendance_deduction_settings()
	if not settings.get("create_on_payroll"):
		return
	if not doc.employees:
		return
	for row in doc.employees:
		if not get_employee_deduction_rule(row.employee):
			continue
		existing = frappe.db.exists(
			"Attendance Deduction Summary",
			{
				"employee": row.employee,
				"start_date": doc.start_date,
				"end_date": doc.end_date,
				"docstatus": 1,
			},
		)
		if not existing:
			create_or_update_summary(
				row.employee,
				doc.start_date,
				doc.end_date,
				payroll_entry=doc.name,
				submit=True,
			)
