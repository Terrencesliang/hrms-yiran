# Copyright (c) 2026 stillgroup
# License: MIT
"""Seed the five employee self-service forms into the existing approval engine."""

import json

import frappe


FORMS = {
	"onboarding": ("入职员工资料填写", "完善入职资料并提交 HR 审核", "employee_center_onboarding", [
		("gender", "性别", "select"), ("date_of_birth", "出生日期", "date"),
		("cell_number", "手机号", "text"), ("personal_email", "个人邮箱", "text"),
		("current_address", "现居地址", "textarea"), ("permanent_address", "户籍地址", "textarea"),
		("id_number", "身份证号", "text"), ("education", "最高学历", "select"),
		("school", "毕业院校", "text"), ("major", "专业", "text"),
		("emergency_contact_name", "紧急联系人", "text"), ("emergency_phone", "紧急联系电话", "text"),
		("bank_name", "开户银行", "text"), ("bank_ac_no", "银行卡号", "text"),
	]),
	"subsidy": ("申请补贴", "提交餐补、车补及相关凭证", "employee_center_subsidy", [
		("details_summary", "补贴明细", "textarea"), ("meal_total", "餐补合计", "number"),
		("vehicle_total", "车补合计", "number"), ("total_amount", "总金额", "number"),
	]),
	"job-change": ("调岗调薪申请", "申请调岗、晋升、降级或调薪", "employee_center_job_change", [
		("change_type", "异动类型", "select"), ("new_department", "调入部门", "department"),
		("new_designation", "调整后岗位", "text"), ("new_grade", "调整后职级", "text"),
		("current_salary", "原薪资", "number"), ("new_salary", "调整后薪资", "number"),
		("effective_date", "生效日期", "date"), ("reason", "申请原因", "textarea"),
		("additional_notes", "补充说明", "textarea"),
	]),
	"resignation": ("离职申请表", "提交离职日期、原因与交接人", "employee_center_resignation", [
		("planned_resignation_date", "计划离职日期", "date"), ("handover_employee", "离职交接人", "employee"),
		("resignation_reason", "离职原因", "select"), ("reason_description", "原因说明", "textarea"),
	]),
	"handover": ("离职交接表", "维护工作、资产与账号交接清单", "employee_center_handover", [
		("resignation_application", "关联离职申请单", "text"),
		("handover_progress", "交接进度", "text"), ("items_summary", "交接清单", "textarea"),
	]),
}


def _process():
	return {
		"nodes": [
			{"id": "start", "type": "start", "label": "发起人", "props": {}},
			{"id": "hr", "type": "approver", "label": "HR 审批", "props": {"assignee_type": "role", "role": "HR Manager", "mode": "or", "field_perms": {}}},
			{"id": "end", "type": "end", "label": "结束", "props": {}},
		]
	}


def execute():
	group = frappe.db.get_value("Approval Form Group", {"group_name": "员工中心"}, "name")
	if not group:
		group_doc = frappe.get_doc({"doctype": "Approval Form Group", "group_name": "员工中心", "sort_order": 5, "enabled": 1})
		group_doc.insert(ignore_permissions=True)
		group = group_doc.name
	for sort_order, (application_type, (title, description, hook, fields)) in enumerate(FORMS.items(), 1):
		name = frappe.db.get_value("Approval Form", {"form_name": title}, "name")
		doc = frappe.get_doc("Approval Form", name) if name else frappe.new_doc("Approval Form")
		doc.update({
			"form_name": title,
			"group": group,
			"description": description,
			"status": "使用中",
			"visibility": "全公司",
			"icon": "file",
			"color": "#165DFF",
			"sort_order": sort_order,
			"process_summary": "HR 审批",
			"process_json": json.dumps(_process(), ensure_ascii=False),
			"business_hook": hook,
			"form_schema_json": json.dumps({"fields": [
				{"key": key, "label": label, "type": kind, "required": 0, "options": []}
				for key, label, kind in fields
			]}, ensure_ascii=False),
		})
		if doc.is_new(): doc.insert(ignore_permissions=True)
		else: doc.save(ignore_permissions=True)
	frappe.clear_cache()
