# Copyright (c) 2026 stillgroup
# License: MIT
"""Approval instance runtime: start / complete / cancel."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from employee_roster.hr_roster.approval_engine.assignees import (
	get_employee_for_user,
	resolve_assignees,
)
from employee_roster.hr_roster.approval_engine.expressions import eval_expression
from employee_roster.hr_roster.approval_engine.hooks_registry import run_business_hook
from employee_roster.hr_roster.approval_engine.notifications import notify_users
from employee_roster.hr_roster.approval_engine.process_schema import normalize_process
from employee_roster.hr_roster.approval_engine.schema import dumps as dumps_schema
from employee_roster.hr_roster.approval_engine.schema import normalize_schema, validate_form_data


def _loads(value: Any, default: Any = None) -> Any:
	if value is None or value == "":
		return default
	if isinstance(value, (dict, list)):
		return value
	return json.loads(value)


def start_instance(form_name: str, form_data: dict | str | None = None) -> dict:
	if not form_name or not frappe.db.exists("Approval Form", form_name):
		frappe.throw(_("审批表单不存在"))
	form = frappe.get_doc("Approval Form", form_name)
	if form.status != "使用中":
		frappe.throw(_("该审批表单已停用"))

	applicant_user = frappe.session.user
	applicant_employee = get_employee_for_user(applicant_user)

	schema = normalize_schema(form.form_schema_json)
	data = validate_form_data(schema, form_data or {})
	process = normalize_process(form.process_json)

	doc = frappe.get_doc(
		{
			"doctype": "Approval Instance",
			"approval_form": form.name,
			"form_title": form.form_name,
			"applicant_user": applicant_user,
			"applicant_employee": applicant_employee,
			"status": "进行中",
			"form_schema_json": dumps_schema(schema),
			"form_data_json": json.dumps(data, ensure_ascii=False),
			"process_snapshot_json": json.dumps(process, ensure_ascii=False),
			"business_hook": form.business_hook or "",
			"current_node_id": "",
			"current_node_label": "",
		}
	)
	doc.insert(ignore_permissions=True)

	_advance_from(doc, after_node_id=None)
	doc.reload()
	return {"name": doc.name, "status": doc.status}


def complete_task(
	task_name: str,
	action: str,
	comment: str | None = None,
	form_data: dict | str | None = None,
) -> dict:
	action = (action or "").strip()
	if action not in ("approve", "reject", "transfer"):
		frappe.throw(_("无效操作"))

	task = frappe.get_doc("Approval Task", task_name)
	if task.status != "待处理":
		frappe.throw(_("任务已处理"))
	if task.assignee != frappe.session.user and "System Manager" not in frappe.get_roles():
		frappe.throw(_("无权处理该任务"), frappe.PermissionError)
	if task.task_type == "cc":
		frappe.throw(_("抄送任务无需审批操作"))

	instance = frappe.get_doc("Approval Instance", task.instance)
	if instance.status != "进行中":
		frappe.throw(_("流程已结束"))

	if form_data is not None:
		schema = normalize_schema(instance.form_schema_json)
		# merge editable fields
		current = _loads(instance.form_data_json, {})
		incoming = validate_form_data(schema, form_data)
		# only overwrite keys present in payload for writable fields
		perms = _node_field_perms(instance, task.node_id)
		merged = dict(current)
		for key, val in incoming.items():
			perm = perms.get(key) or "read"
			if perm == "write":
				merged[key] = val
		instance.form_data_json = json.dumps(merged, ensure_ascii=False)
		instance.save(ignore_permissions=True)

	if action == "transfer":
		# handled via transfer_task API; keep for completeness
		frappe.throw(_("请使用转交接口"))

	task.status = "已同意" if action == "approve" else "已驳回"
	task.action = "同意" if action == "approve" else "驳回"
	task.comment = comment or ""
	task.acted_on = now_datetime()
	task.save(ignore_permissions=True)

	if action == "reject":
		_reject_instance(instance, task)
		return {"name": instance.name, "status": instance.status}

	if _node_fully_approved(instance, task.node_id):
		_cancel_pending_siblings(instance.name, task.node_id, except_task=task.name)
		_advance_from(instance, after_node_id=task.node_id)
	instance.reload()
	return {"name": instance.name, "status": instance.status}


def cancel_instance(instance_name: str, comment: str | None = None) -> dict:
	instance = frappe.get_doc("Approval Instance", instance_name)
	if instance.applicant_user != frappe.session.user and "System Manager" not in frappe.get_roles():
		frappe.throw(_("仅发起人可撤销"), frappe.PermissionError)
	if instance.status != "进行中":
		frappe.throw(_("流程已结束，无法撤销"))
	instance.status = "已撤销"
	instance.finished_on = now_datetime()
	instance.current_node_id = ""
	instance.current_node_label = ""
	instance.save(ignore_permissions=True)
	_close_open_tasks(instance.name, status="已取消", comment=comment or "发起人撤销")
	notify_users(
		_open_assignees(instance.name),
		subject=_("审批已撤销：{0}").format(instance.form_title),
		message=comment or _("发起人已撤销申请"),
		document_type="Approval Instance",
		document_name=instance.name,
	)
	return {"name": instance.name, "status": instance.status}


def transfer_task(task_name: str, to_user: str, comment: str | None = None) -> dict:
	task = frappe.get_doc("Approval Task", task_name)
	if task.status != "待处理":
		frappe.throw(_("任务已处理"))
	if task.assignee != frappe.session.user and "System Manager" not in frappe.get_roles():
		frappe.throw(_("无权转交"), frappe.PermissionError)
	if not to_user or not frappe.db.exists("User", to_user):
		frappe.throw(_("转交目标用户无效"))

	task.status = "已转交"
	task.action = "转交"
	task.comment = comment or ""
	task.acted_on = now_datetime()
	task.save(ignore_permissions=True)

	new_task = frappe.get_doc(
		{
			"doctype": "Approval Task",
			"instance": task.instance,
			"node_id": task.node_id,
			"node_label": task.node_label,
			"task_type": task.task_type,
			"assignee": to_user,
			"status": "待处理",
			"mode": task.mode,
		}
	)
	new_task.insert(ignore_permissions=True)
	notify_users(
		[to_user],
		subject=_("审批转交：{0}").format(task.node_label or task.instance),
		message=comment or _("有一条审批待办已转交给你"),
		document_type="Approval Task",
		document_name=new_task.name,
	)
	return {"name": new_task.name}


def _reject_instance(instance, task) -> None:
	instance.status = "已驳回"
	instance.finished_on = now_datetime()
	instance.current_node_id = task.node_id
	instance.current_node_label = task.node_label
	instance.save(ignore_permissions=True)
	_close_open_tasks(instance.name, status="已取消", comment=_("流程已驳回"))
	notify_users(
		[instance.applicant_user],
		subject=_("审批已驳回：{0}").format(instance.form_title),
		message=task.comment or _("你的申请已被驳回"),
		document_type="Approval Instance",
		document_name=instance.name,
	)


def _node_fully_approved(instance, node_id: str) -> bool:
	tasks = frappe.get_all(
		"Approval Task",
		filters={"instance": instance.name, "node_id": node_id, "task_type": "approve"},
		fields=["name", "status", "mode"],
	)
	if not tasks:
		return True
	mode = (tasks[0].mode or "or").lower()
	approved = [t for t in tasks if t.status == "已同意"]
	pending = [t for t in tasks if t.status == "待处理"]
	if mode == "and":
		return len(pending) == 0 and len(approved) == len(tasks)
	return len(approved) >= 1


def _cancel_pending_siblings(instance_name: str, node_id: str, except_task: str | None = None) -> None:
	filters = {"instance": instance_name, "node_id": node_id, "status": "待处理"}
	for row in frappe.get_all("Approval Task", filters=filters, pluck="name"):
		if except_task and row == except_task:
			continue
		doc = frappe.get_doc("Approval Task", row)
		doc.status = "已取消"
		doc.acted_on = now_datetime()
		doc.save(ignore_permissions=True)


def _close_open_tasks(instance_name: str, status: str, comment: str = "") -> None:
	for name in frappe.get_all(
		"Approval Task",
		filters={"instance": instance_name, "status": "待处理"},
		pluck="name",
	):
		doc = frappe.get_doc("Approval Task", name)
		doc.status = status
		doc.comment = comment
		doc.acted_on = now_datetime()
		doc.save(ignore_permissions=True)


def _open_assignees(instance_name: str) -> list[str]:
	return frappe.get_all(
		"Approval Task",
		filters={"instance": instance_name, "status": "待处理"},
		pluck="assignee",
	)


def _node_field_perms(instance, node_id: str) -> dict:
	process = normalize_process(instance.process_snapshot_json)
	for node in process["nodes"]:
		if node["id"] == node_id:
			return (node.get("props") or {}).get("field_perms") or {}
	return {}


def _advance_from(instance, after_node_id: str | None) -> None:
	instance.reload()
	process = normalize_process(instance.process_snapshot_json)
	nodes = process["nodes"]
	form_data = _loads(instance.form_data_json, {})

	# Build linear walk with condition expansion
	sequence = _expand_sequence(nodes, form_data)
	start_idx = -1
	if after_node_id:
		for i, n in enumerate(sequence):
			if n["id"] == after_node_id:
				start_idx = i
				break
	next_nodes = sequence[start_idx + 1 :]

	while next_nodes:
		node = next_nodes[0]
		next_nodes = next_nodes[1:]
		if node["type"] == "start":
			continue
		if node["type"] == "end":
			_finish_approved(instance)
			return
		if node["type"] == "cc":
			_create_cc_tasks(instance, node)
			# cc does not block; continue
			continue
		if node["type"] == "approver":
			_create_approve_tasks(instance, node)
			instance.current_node_id = node["id"]
			instance.current_node_label = node["label"]
			instance.save(ignore_permissions=True)
			return
		# unknown / parallel fallback: skip
	_finish_approved(instance)


def _expand_sequence(nodes: list[dict], form_data: dict) -> list[dict]:
	out: list[dict] = []
	for node in nodes:
		if node["type"] == "condition":
			branch = _pick_branch(node, form_data)
			if branch:
				out.extend(_expand_sequence(branch.get("nodes") or [], form_data))
			continue
		if node["type"] == "parallel":
			# Phase 2.4 light support: run branches sequentially for simplicity
			for branch in (node.get("props") or {}).get("branches") or []:
				out.extend(_expand_sequence(branch.get("nodes") or [], form_data))
			continue
		out.append(node)
	return out


def _pick_branch(node: dict, form_data: dict) -> dict | None:
	branches = (node.get("props") or {}).get("branches") or []
	default = None
	for branch in branches:
		if branch.get("is_default"):
			default = branch
			continue
		expr = branch.get("expression") or ""
		if expr and eval_expression(expr, form_data):
			return branch
	return default or (branches[0] if branches else None)


def _create_approve_tasks(instance, node: dict) -> None:
	props = node.get("props") or {}
	users = resolve_assignees(
		props,
		applicant_employee=instance.applicant_employee,
		applicant_user=instance.applicant_user,
	)
	mode = (props.get("mode") or "or").lower()
	created = []
	for user in users:
		task = frappe.get_doc(
			{
				"doctype": "Approval Task",
				"instance": instance.name,
				"node_id": node["id"],
				"node_label": node["label"],
				"task_type": "approve",
				"assignee": user,
				"status": "待处理",
				"mode": "and" if mode == "and" else "or",
			}
		)
		task.insert(ignore_permissions=True)
		created.append(user)
	notify_users(
		created,
		subject=_("待审批：{0}").format(instance.form_title),
		message=_("你有一条新的审批待办"),
		document_type="Approval Instance",
		document_name=instance.name,
	)


def _create_cc_tasks(instance, node: dict) -> None:
	props = node.get("props") or {}
	users = resolve_assignees(
		props,
		applicant_employee=instance.applicant_employee,
		applicant_user=instance.applicant_user,
	)
	for user in users:
		task = frappe.get_doc(
			{
				"doctype": "Approval Task",
				"instance": instance.name,
				"node_id": node["id"],
				"node_label": node["label"],
				"task_type": "cc",
				"assignee": user,
				"status": "已抄送",
				"mode": "or",
				"acted_on": now_datetime(),
			}
		)
		task.insert(ignore_permissions=True)
	notify_users(
		users,
		subject=_("审批抄送：{0}").format(instance.form_title),
		message=_("有一条审批抄送给你"),
		document_type="Approval Instance",
		document_name=instance.name,
	)


def _finish_approved(instance) -> None:
	instance.reload()
	instance.status = "已通过"
	instance.finished_on = now_datetime()
	instance.current_node_id = "end"
	instance.current_node_label = "结束"
	instance.save(ignore_permissions=True)
	notify_users(
		[instance.applicant_user],
		subject=_("审批已通过：{0}").format(instance.form_title),
		message=_("你的申请已通过"),
		document_type="Approval Instance",
		document_name=instance.name,
	)
	try:
		run_business_hook(instance)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Approval business hook failed")
