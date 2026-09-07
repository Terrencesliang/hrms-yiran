# Copyright (c) 2026 stillgroup
# License: MIT
"""install 后初始化考勤扣款模块。"""
import frappe

from employee_roster.hr_roster.attendance_deduction.fixtures import (
	DEFAULT_RULES,
	ensure_salary_component,
	ensure_settings,
	seed_default_rules,
)


def setup_attendance_deduction_module() -> None:
	ensure_salary_component()
	ensure_settings()
	seed_default_rules()
	sync_attendance_sidebar()
	frappe.db.commit()


def sync_attendance_sidebar() -> None:
	"""Ensure 考勤规则入口存在，并隐藏其它考勤侧边栏项。"""
	if not frappe.db.exists("Sidebar", "Shift & Attendance"):
		return

	new_item = {
		"child": 0,
		"collapsible": 1,
		"hidden": 0,
		"icon": "scale",
		"indent": 0,
		"label": "考勤规则",
		"link_to": "attendance-rules",
		"link_type": "Page",
		"type": "Link",
	}

	doc = frappe.get_doc("Sidebar", "Shift & Attendance")
	existing_links = {row.link_to for row in doc.items if row.link_to}
	changed = False
	if "attendance-rules" not in existing_links:
		items = [row.as_dict() for row in doc.items]
		checkin_idx = next(
			(i for i, row in enumerate(items) if row.get("link_to") == "Employee Checkin"),
			len(items),
		)
		items.insert(checkin_idx + 1, new_item)
		doc.items = []
		for row in items:
			doc.append("items", row)
		changed = True

	if changed:
		doc.save(ignore_permissions=True)

	prune_attendance_sidebar_links()


ATTENDANCE_ALLOWED_LINK_TO = {
	"Employee Checkin",
	"attendance-rules",
}
ATTENDANCE_ALLOWED_LABELS = {
	"Employee Checkin",
	"Attendance Rules",
	"打卡记录",
	"考勤规则",
}


def prune_attendance_sidebar_links() -> None:
	"""Keep only check-in records and attendance rules in 考勤 sidebar."""
	if not frappe.db.exists("Sidebar", "Shift & Attendance"):
		return
	doc = frappe.get_doc("Sidebar", "Shift & Attendance")
	changed = False
	for row in doc.items:
		if row.type == "Section Break":
			if not int(row.hidden or 0):
				row.hidden = 1
				changed = True
			continue
		if row.type != "Link":
			continue
		allowed = row.link_to in ATTENDANCE_ALLOWED_LINK_TO or row.label in ATTENDANCE_ALLOWED_LABELS
		if allowed:
			if int(row.hidden or 0):
				row.hidden = 0
				changed = True
		elif not int(row.hidden or 0):
			row.hidden = 1
			changed = True
	if changed:
		doc.save(ignore_permissions=True)
