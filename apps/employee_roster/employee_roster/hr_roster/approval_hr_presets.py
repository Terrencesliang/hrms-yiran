# Copyright (c) 2026 stillgroup
# License: MIT
"""Preset HR approval processes (录用 / 转正 / 离职 / 调岗 / 薪资等)."""

from __future__ import annotations

from employee_roster.hr_roster.approval_engine.process_schema import summarize_process

# Roles used by presets (created on seed if missing)
HR_PROCESS_ROLES = [
	"总经理",
	"副总",
	"HRBP",
	"人事",
	"费用会计",
	"人事组",
]


def _start():
	return {"id": "start", "type": "start", "label": "发起人", "props": {}}


def _end():
	return {"id": "end", "type": "end", "label": "结束", "props": {}}


def _approver(nid: str, label: str, **props):
	base = {"assignee_type": "role", "mode": "or", "field_perms": {}}
	base.update(props)
	return {"id": nid, "type": "approver", "label": label, "props": base}


def _cc(nid: str, label: str, **props):
	base = {"assignee_type": "role"}
	base.update(props)
	return {"id": nid, "type": "cc", "label": label, "props": base}


def _process(*middle):
	return {"nodes": [_start(), *middle, _end()]}


# --- process definitions matching the org chart ---

PROCESS_录用 = _process(
	_approver("ap_gm", "总经理", role="总经理"),
	_cc("cc_vp_hr", "副总、人事", roles=["副总", "人事"]),
)

PROCESS_转正申请表 = _process(
	_approver("ap_dept", "部门负责人", assignee_type="department_head"),
	_approver("ap_vp", "副总", role="副总"),
	_cc("cc_hrbp", "HRBP", role="HRBP"),
)

PROCESS_离职申请表 = _process(
	_approver("ap_hrbp", "HRBP", role="HRBP"),
	_approver("ap_dept", "部门负责人", assignee_type="department_head"),
	_approver("ap_vp", "副总", role="副总"),
)

PROCESS_离职交接表 = _process(
	_approver("ap_cost", "费用会计", role="费用会计"),
	_approver(
		"ap_handover",
		"交接人",
		assignee_type="form_field",
		field="handover_employee",
		resolve_as="employee",
	),
)

PROCESS_补贴申请 = _process(
	_approver("ap_dept", "部门负责人", assignee_type="department_head"),
	_approver("ap_hr", "人事", role="人事"),
)

PROCESS_调岗 = _process(
	_approver("ap_dept", "部门负责人", assignee_type="department_head"),
	_approver(
		"ap_to_dept",
		"调入部门负责人",
		assignee_type="form_field",
		field="to_department",
		resolve_as="department_head",
	),
	_approver("ap_hrbp", "HRBP", role="HRBP"),
	_cc("cc_hr_group", "人事组", role="人事组"),
)

PROCESS_薪资调整 = _process(
	_approver(
		"ap_chain",
		"多级部门负责人",
		assignee_type="reports_to_chain",
		levels=3,
		mode="or",
	),
	_approver("ap_vp", "副总", role="副总"),
	_cc("cc_gm_hr", "总经理、人事", roles=["总经理", "人事"]),
)


SCHEMA_调岗 = {
	"fields": [
		{"key": "from_department", "label": "原部门", "type": "department", "required": 1},
		{"key": "to_department", "label": "调入部门", "type": "department", "required": 1},
		{"key": "to_designation", "label": "调入岗位", "type": "text", "required": 0},
		{"key": "effective_date", "label": "生效日期", "type": "date", "required": 1},
		{"key": "reason", "label": "调岗原因", "type": "textarea", "required": 1},
	]
}

SCHEMA_离职交接表 = {
	"fields": [
		{"key": "last_working_day", "label": "最后工作日", "type": "date", "required": 1},
		{
			"key": "handover_employee",
			"label": "交接人",
			"type": "employee",
			"required": 1,
		},
		{"key": "handover_items", "label": "交接事项", "type": "textarea", "required": 1},
		{"key": "attachment", "label": "附件", "type": "attachment", "required": 0},
	]
}

SCHEMA_录用 = {
	"fields": [
		{"key": "candidate_name", "label": "候选人", "type": "text", "required": 1},
		{"key": "department", "label": "录用部门", "type": "department", "required": 1},
		{"key": "designation", "label": "岗位", "type": "text", "required": 1},
		{"key": "join_date", "label": "预计入职日", "type": "date", "required": 1},
		{"key": "remark", "label": "备注", "type": "textarea", "required": 0},
	]
}

SCHEMA_转正申请表 = {
	"fields": [
		{"key": "probation_end", "label": "试用期结束日", "type": "date", "required": 1},
		{"key": "self_summary", "label": "试用期总结", "type": "textarea", "required": 1},
		{"key": "attachment", "label": "附件", "type": "attachment", "required": 0},
	]
}

SCHEMA_离职申请表 = {
	"fields": [
		{"key": "last_working_day", "label": "预计最后工作日", "type": "date", "required": 1},
		{"key": "reason", "label": "离职原因", "type": "textarea", "required": 1},
	]
}

SCHEMA_补贴申请 = {
	"fields": [
		{"key": "subsidy_type", "label": "补贴类型", "type": "text", "required": 1},
		{"key": "amount", "label": "金额", "type": "number", "required": 1},
		{"key": "reason", "label": "申请说明", "type": "textarea", "required": 1},
		{"key": "attachment", "label": "附件", "type": "attachment", "required": 0},
	]
}

SCHEMA_薪资调整 = {
	"fields": [
		{"key": "current_salary", "label": "当前薪资", "type": "number", "required": 0},
		{"key": "new_salary", "label": "调整后薪资", "type": "number", "required": 1},
		{"key": "effective_date", "label": "生效日期", "type": "date", "required": 1},
		{"key": "reason", "label": "调整原因", "type": "textarea", "required": 1},
	]
}


def _form(
	form_name: str,
	*,
	process: dict,
	description: str,
	sort_order: int,
	color: str,
	icon: str,
	schema: dict | None = None,
):
	return {
		"form_name": form_name,
		"group": "人事审批",
		"icon": icon,
		"color": color,
		"description": description,
		"sort_order": sort_order,
		"process": process,
		"process_summary": summarize_process(process),
		"form_schema": schema or {"fields": []},
	}


# Idempotent seed list (process overwritten on each seed)
HR_APPROVAL_FORMS = [
	_form(
		"录用",
		process=PROCESS_录用,
		description="员工录用审批；通过后抄送副总与人事",
		sort_order=1,
		color="#165DFF",
		icon="user-add",
		schema=SCHEMA_录用,
	),
	_form(
		"转正申请表",
		process=PROCESS_转正申请表,
		description="试用期转正申请",
		sort_order=2,
		color="#0FC6C2",
		icon="check-circle",
		schema=SCHEMA_转正申请表,
	),
	_form(
		"离职申请表",
		process=PROCESS_离职申请表,
		description="员工离职申请审批",
		sort_order=3,
		color="#F53F3F",
		icon="user",
		schema=SCHEMA_离职申请表,
	),
	_form(
		"离职交接表",
		process=PROCESS_离职交接表,
		description="离职物资/工作交接；交接人由表单字段指定",
		sort_order=4,
		color="#F77234",
		icon="swap",
		schema=SCHEMA_离职交接表,
	),
	_form(
		"补贴申请",
		process=PROCESS_补贴申请,
		description="各类补贴申请",
		sort_order=5,
		color="#F7BA1E",
		icon="gift",
		schema=SCHEMA_补贴申请,
	),
	_form(
		"调岗",
		process=PROCESS_调岗,
		description="内部调岗；需填写调入部门",
		sort_order=6,
		color="#722ED1",
		icon="branch",
		schema=SCHEMA_调岗,
	),
	_form(
		"薪资调整",
		process=PROCESS_薪资调整,
		description="薪资调整；先按汇报链多级审批",
		sort_order=7,
		color="#00B42A",
		icon="trophy",
		schema=SCHEMA_薪资调整,
	),
]
