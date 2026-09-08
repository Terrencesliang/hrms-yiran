# Copyright (c) 2026 stillgroup
# License: MIT
"""为员工打卡增加独立的打卡方式，并修正列表中文元数据。"""
from __future__ import annotations

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


CUSTOM_FIELD = {
	"fieldname": "checkin_type",
	"label": "打卡方式",
	"fieldtype": "Select",
	"options": "办公地点\n外勤打卡",
	"default": "办公地点",
	"insert_after": "log_type",
	"in_list_view": 1,
	"in_standard_filter": 1,
	"description": "办公地点打卡或外勤打卡",
}


def execute():
	field_name = "Employee Checkin-checkin_type"
	if frappe.db.exists("Custom Field", field_name):
		doc = frappe.get_doc("Custom Field", field_name)
		for key, value in CUSTOM_FIELD.items():
			setattr(doc, key, value)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Employee Checkin",
				**CUSTOM_FIELD,
			}
		)
		doc.insert(ignore_permissions=True)

	# 原字段值仍保持 IN/OUT，仅将所有界面标签统一为中文。
	make_property_setter(
		"Employee Checkin",
		"log_type",
		"label",
		"打卡动作",
		"Data",
		validate_fields_for_doctype=False,
	)

	# 旧补丁将虚拟结果列设成 Select，Frappe 会把选项误当表达式求值。
	# 列值来自聚合接口，Data 更符合其只读展示用途。
	result_field = "Employee Checkin-day_attendance_result"
	if frappe.db.exists("Custom Field", result_field):
		frappe.db.set_value(
			"Custom Field",
			result_field,
			{"fieldtype": "Data", "options": None},
			update_modified=False,
		)

	frappe.clear_cache(doctype="Employee Checkin")
