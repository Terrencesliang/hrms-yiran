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
	"""在 Shift & Attendance 侧边栏增加考勤规则等入口。"""
	if not frappe.db.exists("Sidebar", "Shift & Attendance"):
		return

	new_items = [
		{
			"child": 0,
			"collapsible": 1,
			"icon": "scale",
			"indent": 1,
			"label": "考勤管理",
			"type": "Section Break",
		},
		{
			"child": 1,
			"collapsible": 1,
			"icon": "scale",
			"indent": 0,
			"label": "考勤规则",
			"link_to": "attendance-rules",
			"link_type": "Page",
			"type": "Link",
		},
		{
			"child": 1,
			"collapsible": 1,
			"icon": "users",
			"indent": 0,
			"label": "考勤分组",
			"link_to": "Attendance Group",
			"link_type": "DocType",
			"type": "Link",
		},
		{
			"child": 1,
			"collapsible": 1,
			"icon": "receipt",
			"indent": 0,
			"label": "月度扣款汇总",
			"link_to": "Attendance Deduction Summary",
			"link_type": "DocType",
			"type": "Link",
		},
		{
			"child": 1,
			"collapsible": 1,
			"icon": "settings",
			"indent": 0,
			"label": "考勤扣款设置",
			"link_to": "Attendance Deduction Settings",
			"link_type": "DocType",
			"type": "Link",
		},
	]

	doc = frappe.get_doc("Sidebar", "Shift & Attendance")
	existing_links = {row.link_to for row in doc.items if row.link_to}
	if "attendance-rules" in existing_links:
		return

	items = [row.as_dict() for row in doc.items]
	# insert after Dashboard
	idx = next((i for i, r in enumerate(items) if r.get("link_to") == "Attendance"), 2)
	for offset, item in enumerate(new_items):
		items.insert(idx + offset, item)

	doc.items = []
	for row in items:
		doc.append("items", row)
	doc.save(ignore_permissions=True)
