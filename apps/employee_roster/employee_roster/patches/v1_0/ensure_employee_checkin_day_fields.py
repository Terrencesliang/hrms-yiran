# Copyright (c) 2026 stillgroup
# License: MIT
"""为 Employee Checkin 注册日汇总「虚拟」展示字段（不改物理表）。

值由 List View 调用 get_checkin_dashboard 后在 formatters 中渲染。
使用 is_virtual=1，避免 ALTER TABLE（站点 DB 用户可能不是表 owner）。
"""
from __future__ import annotations

import frappe


FIELD_SPECS = [
	{
		"fieldname": "day_attendance_section",
		"fieldtype": "Section Break",
		"label": "日出勤汇总",
		"insert_after": "overtime_type",
		"collapsible": 1,
	},
	{
		"fieldname": "day_attendance_result",
		"label": "日出勤结果",
		"fieldtype": "Select",
		"options": "\n出勤\n迟到\n缺卡",
		"insert_after": "day_attendance_section",
		"read_only": 1,
		"in_list_view": 1,
		"is_virtual": 1,
		"description": "当日考勤结论：出勤=完整打卡且未迟到；迟到=上班晚于规则上班时间；缺卡=缺 IN 或 OUT",
	},
	{
		"fieldname": "day_work_hours",
		"label": "日出勤时长",
		"fieldtype": "Float",
		"precision": "2",
		"insert_after": "day_attendance_result",
		"read_only": 1,
		"in_list_view": 1,
		"is_virtual": 1,
		"description": "最早上班至最晚下班的小时数",
	},
	{
		"fieldname": "column_break_day_att",
		"fieldtype": "Column Break",
		"insert_after": "day_work_hours",
	},
	{
		"fieldname": "day_first_in",
		"label": "最早上班时间",
		"fieldtype": "Data",
		"insert_after": "column_break_day_att",
		"read_only": 1,
		"in_list_view": 1,
		"is_virtual": 1,
	},
	{
		"fieldname": "day_last_out",
		"label": "最晚下班时间",
		"fieldtype": "Data",
		"insert_after": "day_first_in",
		"read_only": 1,
		"in_list_view": 1,
		"is_virtual": 1,
	},
]


def execute():
	ensure_employee_checkin_day_fields()


def ensure_employee_checkin_day_fields():
	"""写入 Custom Field 元数据；失败时不阻断（前端仍可注入列）。"""
	for spec in FIELD_SPECS:
		cf_name = f"Employee Checkin-{spec['fieldname']}"
		try:
			if frappe.db.exists("Custom Field", cf_name):
				# 补齐 is_virtual，避免后续 migrate 再尝试加物理列
				if spec.get("is_virtual") and not frappe.db.get_value("Custom Field", cf_name, "is_virtual"):
					frappe.db.set_value("Custom Field", cf_name, "is_virtual", 1, update_modified=False)
				continue

			doc = frappe.get_doc(
				{
					"doctype": "Custom Field",
					"dt": "Employee Checkin",
					**spec,
				}
			)
			# insert 可能触发 schema sync；虚拟字段不应 ALTER 物理表
			doc.flags.ignore_validate = True
			doc.insert(ignore_permissions=True)
		except Exception as exc:
			frappe.log_error(
				title="ensure_employee_checkin_day_fields",
				message=f"{cf_name}: {exc}",
			)
			# 无表 owner 权限时跳过，List View JS 会运行时注入列
			continue

	frappe.clear_cache(doctype="Employee Checkin")
