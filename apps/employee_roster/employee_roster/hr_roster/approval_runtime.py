# Copyright (c) 2026 stillgroup
# License: MIT
"""Whitelisted APIs for approval designer + workspace runtime."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint

from employee_roster.hr_roster.approval_admin import _require_admin_permission
from employee_roster.hr_roster.approval_engine import runtime
from employee_roster.hr_roster.approval_engine.assignees import get_employee_for_user
from employee_roster.hr_roster.approval_engine.process_schema import (
	DEFAULT_PROCESS,
	normalize_process,
	summarize_process,
)
from employee_roster.hr_roster.approval_engine.schema import (
	dumps as dumps_schema,
	empty_schema,
	normalize_schema,
	parse_json,
)


def _require_login() -> None:
	if frappe.session.user == "Guest":
		frappe.throw(_("请先登录"), frappe.PermissionError)


def _user_can_see_form(form) -> bool:
	if form.status != "使用中":
		return False
	if form.visibility != "自定义":
		return True
	rules = parse_json(form.visibility_json, {}) or {}
	roles = set(rules.get("roles") or [])
	departments = set(rules.get("departments") or [])
	employees = set(rules.get("employees") or [])
	user_roles = set(frappe.get_roles())
	if roles and user_roles.intersection(roles):
		return True
	emp = get_employee_for_user()
	if emp and employees and emp in employees:
		return True
	if emp and departments:
		dept = frappe.db.get_value("Employee", emp, "department")
		if dept and dept in departments:
			return True
	# if no rules configured, treat as company-wide
	if not roles and not departments and not employees:
		return True
	return False


@frappe.whitelist()
def get_form_design(name: str):
	_require_admin_permission("read")
	if not name or not frappe.db.exists("Approval Form", name):
		frappe.throw(_("表单不存在"))
	doc = frappe.get_doc("Approval Form", name)
	schema = normalize_schema(doc.form_schema_json or empty_schema())
	process = normalize_process(doc.process_json or DEFAULT_PROCESS)
	return {
		"name": doc.name,
		"form_name": doc.form_name,
		"group": doc.group,
		"status": doc.status,
		"visibility": doc.visibility,
		"visibility_json": parse_json(doc.visibility_json, {}),
		"business_hook": doc.business_hook or "",
		"form_schema": schema,
		"process": process,
		"process_summary": doc.process_summary or summarize_process(process),
	}


@frappe.whitelist()
def save_form_design(payload: str | dict):
	_require_admin_permission("write")
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	name = data.get("name")
	if not name or not frappe.db.exists("Approval Form", name):
		frappe.throw(_("表单不存在"))
	schema = normalize_schema(data.get("form_schema") or data.get("form_schema_json"))
	process = normalize_process(data.get("process") or data.get("process_json"))
	summary = data.get("process_summary") or summarize_process(process)
	doc = frappe.get_doc("Approval Form", name)
	doc.form_schema_json = dumps_schema(schema)
	doc.process_json = json.dumps(process, ensure_ascii=False)
	doc.process_summary = summary
	if "visibility" in data and data.get("visibility"):
		doc.visibility = data.get("visibility")
	if "visibility_json" in data:
		doc.visibility_json = json.dumps(
			parse_json(data.get("visibility_json"), {}),
			ensure_ascii=False,
		)
	if "business_hook" in data:
		doc.business_hook = data.get("business_hook") or ""
	doc.save(ignore_permissions=True)
	return {
		"name": doc.name,
		"process_summary": doc.process_summary,
		"form_schema": schema,
		"process": process,
	}


@frappe.whitelist()
def get_template_design(name: str):
	_require_admin_permission("read")
	if not name or not frappe.db.exists("Approval Template", name):
		frappe.throw(_("模板不存在"))
	doc = frappe.get_doc("Approval Template", name)
	return {
		"name": doc.name,
		"template_name": doc.template_name,
		"form_schema": normalize_schema(doc.form_schema_json or empty_schema()),
		"process": normalize_process(doc.process_json or DEFAULT_PROCESS),
		"default_process_summary": doc.default_process_summary,
	}


@frappe.whitelist()
def save_template_design(payload: str | dict):
	_require_admin_permission("write")
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	name = data.get("name")
	if not name or not frappe.db.exists("Approval Template", name):
		frappe.throw(_("模板不存在"))
	schema = normalize_schema(data.get("form_schema") or data.get("form_schema_json"))
	process = normalize_process(data.get("process") or data.get("process_json"))
	doc = frappe.get_doc("Approval Template", name)
	doc.form_schema_json = dumps_schema(schema)
	doc.process_json = json.dumps(process, ensure_ascii=False)
	doc.default_process_summary = data.get("process_summary") or summarize_process(process)
	doc.save(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def list_startable_forms(keyword: str | None = None):
	_require_login()
	filters = {"status": "使用中"}
	or_filters = None
	if keyword:
		kw = f"%{keyword.strip()}%"
		or_filters = [["form_name", "like", kw], ["description", "like", kw]]
	rows = frappe.get_all(
		"Approval Form",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"form_name",
			"group",
			"icon",
			"color",
			"description",
			"process_summary",
			"visibility",
			"sort_order",
		],
		order_by="sort_order asc, form_name asc",
	)
	out = []
	for row in rows:
		doc = frappe.get_doc("Approval Form", row.name)
		if _user_can_see_form(doc):
			out.append(row)
	return out


@frappe.whitelist()
def get_start_form(name: str):
	_require_login()
	if not name or not frappe.db.exists("Approval Form", name):
		frappe.throw(_("表单不存在"))
	doc = frappe.get_doc("Approval Form", name)
	if not _user_can_see_form(doc):
		frappe.throw(_("无权发起该审批"), frappe.PermissionError)
	return {
		"name": doc.name,
		"form_name": doc.form_name,
		"description": doc.description,
		"form_schema": normalize_schema(doc.form_schema_json or empty_schema()),
		"process_summary": doc.process_summary,
	}


@frappe.whitelist()
def start_approval(form_name: str, form_data: str | dict | None = None):
	_require_login()
	data = frappe.parse_json(form_data) if isinstance(form_data, str) else (form_data or {})
	doc = frappe.get_doc("Approval Form", form_name)
	if not _user_can_see_form(doc):
		frappe.throw(_("无权发起该审批"), frappe.PermissionError)
	return runtime.start_instance(form_name, data)


@frappe.whitelist()
def complete_approval_task(
	task_name: str,
	action: str,
	comment: str | None = None,
	form_data: str | dict | None = None,
):
	_require_login()
	data = frappe.parse_json(form_data) if isinstance(form_data, str) else form_data
	return runtime.complete_task(task_name, action, comment, data)


@frappe.whitelist()
def cancel_approval(instance_name: str, comment: str | None = None):
	_require_login()
	return runtime.cancel_instance(instance_name, comment)


@frappe.whitelist()
def transfer_approval_task(task_name: str, to_user: str, comment: str | None = None):
	_require_login()
	return runtime.transfer_task(task_name, to_user, comment)


@frappe.whitelist()
def list_workspace_items(view: str = "todo", keyword: str | None = None, limit: int = 50):
	_require_login()
	view = (view or "todo").strip()
	limit = min(cint(limit) or 50, 200)
	user = frappe.session.user

	if view == "todo":
		tasks = frappe.get_all(
			"Approval Task",
			filters={"assignee": user, "status": "待处理", "task_type": "approve"},
			fields=[
				"name",
				"instance",
				"node_label",
				"status",
				"creation",
				"modified",
			],
			order_by="modified desc",
			limit_page_length=limit,
		)
		return _enrich_tasks(tasks, keyword)

	if view == "done":
		tasks = frappe.get_all(
			"Approval Task",
			filters={
				"assignee": user,
				"task_type": "approve",
				"status": ["in", ["已同意", "已驳回", "已转交"]],
			},
			fields=[
				"name",
				"instance",
				"node_label",
				"status",
				"action",
				"acted_on",
				"creation",
				"modified",
			],
			order_by="acted_on desc",
			limit_page_length=limit,
		)
		return _enrich_tasks(tasks, keyword)

	if view == "cc":
		tasks = frappe.get_all(
			"Approval Task",
			filters={"assignee": user, "task_type": "cc"},
			fields=[
				"name",
				"instance",
				"node_label",
				"status",
				"creation",
				"modified",
			],
			order_by="modified desc",
			limit_page_length=limit,
		)
		return _enrich_tasks(tasks, keyword)

	# my initiated
	filters = {"applicant_user": user}
	or_filters = None
	if keyword:
		kw = f"%{keyword.strip()}%"
		or_filters = [["form_title", "like", kw], ["name", "like", kw]]
	rows = frappe.get_all(
		"Approval Instance",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"form_title",
			"status",
			"current_node_label",
			"creation",
			"modified",
			"finished_on",
		],
		order_by="modified desc",
		limit_page_length=limit,
	)
	for r in rows:
		r["item_type"] = "instance"
	return rows


def _enrich_tasks(tasks: list, keyword: str | None) -> list:
	out = []
	kw = (keyword or "").strip().lower()
	for t in tasks:
		inst = frappe.db.get_value(
			"Approval Instance",
			t.instance,
			["form_title", "status", "applicant_user", "applicant_employee"],
			as_dict=True,
		) or {}
		row = {
			**t,
			"form_title": inst.get("form_title"),
			"instance_status": inst.get("status"),
			"applicant_user": inst.get("applicant_user"),
			"applicant_employee": inst.get("applicant_employee"),
			"item_type": "task",
		}
		if kw:
			blob = f"{row.get('form_title') or ''} {row.get('node_label') or ''} {row.get('name')}".lower()
			if kw not in blob:
				continue
		out.append(row)
	return out


@frappe.whitelist()
def get_workspace_detail(instance_name: str | None = None, task_name: str | None = None):
	_require_login()
	task = None
	if task_name:
		task = frappe.get_doc("Approval Task", task_name)
		instance_name = task.instance
		if task.assignee != frappe.session.user and "System Manager" not in frappe.get_roles():
			# allow applicant to view instance via task link only if cc/approve assignee
			if frappe.db.get_value("Approval Instance", instance_name, "applicant_user") != frappe.session.user:
				frappe.throw(_("无权查看"), frappe.PermissionError)

	if not instance_name or not frappe.db.exists("Approval Instance", instance_name):
		frappe.throw(_("实例不存在"))
	inst = frappe.get_doc("Approval Instance", instance_name)
	user = frappe.session.user
	is_admin = "System Manager" in frappe.get_roles() or "HR Manager" in frappe.get_roles()
	involved = (
		inst.applicant_user == user
		or is_admin
		or frappe.db.exists("Approval Task", {"instance": inst.name, "assignee": user})
	)
	if not involved:
		frappe.throw(_("无权查看"), frappe.PermissionError)

	timeline = frappe.get_all(
		"Approval Task",
		filters={"instance": inst.name},
		fields=[
			"name",
			"node_id",
			"node_label",
			"task_type",
			"assignee",
			"status",
			"action",
			"comment",
			"acted_on",
			"creation",
			"mode",
		],
		order_by="creation asc",
	)
	field_perms = {}
	if task and task.task_type == "approve" and task.status == "待处理":
		process = normalize_process(inst.process_snapshot_json)
		for node in process["nodes"]:
			if node["id"] == task.node_id:
				field_perms = (node.get("props") or {}).get("field_perms") or {}
				break

	return {
		"instance": {
			"name": inst.name,
			"form_title": inst.form_title,
			"approval_form": inst.approval_form,
			"status": inst.status,
			"applicant_user": inst.applicant_user,
			"applicant_employee": inst.applicant_employee,
			"current_node_label": inst.current_node_label,
			"form_schema": normalize_schema(inst.form_schema_json or empty_schema()),
			"form_data": parse_json(inst.form_data_json, {}),
			"process": normalize_process(inst.process_snapshot_json or DEFAULT_PROCESS),
			"creation": inst.creation,
			"finished_on": inst.finished_on,
			"hook_result": parse_json(inst.hook_result_json, {}),
		},
		"task": (
			{
				"name": task.name,
				"node_id": task.node_id,
				"node_label": task.node_label,
				"task_type": task.task_type,
				"status": task.status,
				"assignee": task.assignee,
			}
			if task
			else None
		),
		"timeline": timeline,
		"field_perms": field_perms,
		"can_cancel": inst.status == "进行中" and (inst.applicant_user == user or is_admin),
	}


@frappe.whitelist()
def workspace_stats():
	_require_login()
	user = frappe.session.user
	return {
		"todo": frappe.db.count(
			"Approval Task",
			{"assignee": user, "status": "待处理", "task_type": "approve"},
		),
		"done": frappe.db.count(
			"Approval Task",
			{
				"assignee": user,
				"task_type": "approve",
				"status": ["in", ["已同意", "已驳回", "已转交"]],
			},
		),
		"mine": frappe.db.count("Approval Instance", {"applicant_user": user}),
		"cc": frappe.db.count("Approval Task", {"assignee": user, "task_type": "cc"}),
	}
