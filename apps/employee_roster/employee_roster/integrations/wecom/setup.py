"""企业微信集成所需字段安装。"""
from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def ensure_wecom_custom_fields() -> None:
	create_custom_fields(
		{
			"Employee": [
				{
					"fieldname": "hr_wecom_id",
					"label": "企业微信账号",
					"fieldtype": "Data",
					"insert_after": "hr_wechat",
					"in_standard_filter": 1,
				},
				{
					"fieldname": "wecom_last_synced_on",
					"label": "企微最后同步时间",
					"fieldtype": "Datetime",
					"insert_after": "hr_wecom_id",
					"read_only": 1,
				},
			],
			"Department": [
				{
					"fieldname": "wecom_department_id",
					"label": "企业微信部门 ID",
					"fieldtype": "Data",
					"insert_after": "department_name",
					"unique": 1,
					"in_standard_filter": 1,
				},
				{
					"fieldname": "wecom_last_synced_on",
					"label": "企微最后同步时间",
					"fieldtype": "Datetime",
					"insert_after": "wecom_department_id",
					"read_only": 1,
				},
			],
			"Employee Checkin": [
				{
					"fieldname": "wecom_record_id",
					"label": "企业微信打卡记录 ID",
					"fieldtype": "Data",
					"insert_after": "device_id",
					"unique": 1,
					"read_only": 1,
				},
				{
					"fieldname": "wecom_exception_type",
					"label": "企微异常类型",
					"fieldtype": "Data",
					"insert_after": "wecom_record_id",
					"read_only": 1,
				},
				{
					"fieldname": "wecom_group_id",
					"label": "企微打卡规则 ID",
					"fieldtype": "Data",
					"insert_after": "wecom_exception_type",
					"read_only": 1,
				},
				{
					"fieldname": "wecom_raw_data",
					"label": "企微原始数据",
					"fieldtype": "Long Text",
					"insert_after": "wecom_group_id",
					"hidden": 1,
					"read_only": 1,
				},
			],
			"Attendance": [
				{
					"fieldname": "wecom_daily_key",
					"label": "企业微信日报键",
					"fieldtype": "Data",
					"insert_after": "attendance_date",
					"unique": 1,
					"read_only": 1,
				},
				{
					"fieldname": "wecom_raw_data",
					"label": "企微日报原始数据",
					"fieldtype": "Long Text",
					"insert_after": "wecom_daily_key",
					"hidden": 1,
					"read_only": 1,
				},
			],
		},
		ignore_validate=True,
		update=True,
	)
	_migrate_duplicate_employee_field()
	for doctype in ("Employee", "Department", "Employee Checkin", "Attendance"):
		frappe.clear_cache(doctype=doctype)


def _migrate_duplicate_employee_field() -> None:
	"""早期实现曾新增 wecom_userid；迁入既有 hr_wecom_id 后移除重复字段。"""
	duplicate = "Employee-wecom_userid"
	if not frappe.db.exists("Custom Field", duplicate):
		return
	if frappe.get_meta("Employee", cached=False).has_field("hr_wecom_id"):
		for row in frappe.get_all(
			"Employee",
			filters={"wecom_userid": ["is", "set"]},
			fields=["name", "wecom_userid", "hr_wecom_id"],
		):
			if not row.hr_wecom_id:
				frappe.db.set_value(
					"Employee", row.name, "hr_wecom_id", row.wecom_userid
				)
	frappe.delete_doc("Custom Field", duplicate, force=True, ignore_permissions=True)
	if frappe.db.exists("Custom Field", "Employee-wecom_section"):
		frappe.delete_doc(
			"Custom Field",
			"Employee-wecom_section",
			force=True,
			ignore_permissions=True,
		)


def execute() -> None:
	ensure_wecom_custom_fields()


def schema_status() -> dict[str, bool]:
	return {
		"monthly_doctype": bool(
			frappe.db.exists("DocType", "WeCom Attendance Monthly")
		),
		"employee_userid": bool(
			frappe.get_meta("Employee").has_field("hr_wecom_id")
		),
		"department_id": bool(
			frappe.db.exists("Custom Field", "Department-wecom_department_id")
		),
		"checkin_record_id": bool(
			frappe.db.exists("Custom Field", "Employee Checkin-wecom_record_id")
		),
		"attendance_daily_key": bool(
			frappe.db.exists("Custom Field", "Attendance-wecom_daily_key")
		),
	}
