# Copyright (c) 2026 stillgroup
# License: MIT
"""Approval admin center: form list, template library, seed data."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint

from employee_roster.hr_roster.approval_engine.process_schema import (
	DEFAULT_PROCESS,
	summarize_process,
)
from employee_roster.hr_roster.approval_engine.schema import dumps as dumps_schema

DEFAULT_PROCESS_SUMMARY = summarize_process(DEFAULT_PROCESS)

LEAVE_SCHEMA = {
	"fields": [
		{
			"key": "leave_type",
			"label": "假期类型",
			"type": "select",
			"required": 1,
			"options": ["年假", "事假", "病假", "调休", "其他"],
		},
		{"key": "from_date", "label": "开始日期", "type": "date", "required": 1},
		{"key": "to_date", "label": "结束日期", "type": "date", "required": 1},
		{"key": "days", "label": "天数", "type": "number", "required": 1},
		{"key": "reason", "label": "事由", "type": "textarea", "required": 1},
		{"key": "attachment", "label": "附件", "type": "attachment", "required": 0},
	]
}

OUT_SCHEMA = {
	"fields": [
		{"key": "out_date", "label": "外出日期", "type": "date", "required": 1},
		{"key": "destination", "label": "目的地", "type": "text", "required": 1},
		{"key": "reason", "label": "事由", "type": "textarea", "required": 1},
		{"key": "employee_contact", "label": "联系人", "type": "employee", "required": 0},
	]
}

FORM_SEED_EXTRAS = {
	"请假": {"form_schema": LEAVE_SCHEMA, "business_hook": "leave_application"},
	"外出": {"form_schema": OUT_SCHEMA, "business_hook": "out_of_office"},
}

SEED_GROUPS = [
	{"group_name": "考勤审批", "sort_order": 1},
	{"group_name": "人事审批", "sort_order": 2},
]

SEED_FORMS = [
	{
		"form_name": "外出",
		"group": "考勤审批",
		"icon": "location",
		"color": "#0FC6C2",
		"description": "员工因公临时外出申请",
		"sort_order": 1,
	},
	{
		"form_name": "请假",
		"group": "考勤审批",
		"icon": "calendar",
		"color": "#165DFF",
		"description": "各类假期申请",
		"sort_order": 2,
	},
	{
		"form_name": "出差",
		"group": "考勤审批",
		"icon": "public",
		"color": "#722ED1",
		"description": "出差行程与费用相关审批",
		"sort_order": 3,
	},
	{
		"form_name": "补卡",
		"group": "考勤审批",
		"icon": "clock-circle",
		"color": "#F77234",
		"description": "漏打卡补卡申请",
		"sort_order": 4,
	},
	{
		"form_name": "加班",
		"group": "考勤审批",
		"icon": "thunderbolt",
		"color": "#F53F3F",
		"description": "加班时长申请",
		"sort_order": 5,
	},
	{
		"form_name": "调休",
		"group": "考勤审批",
		"icon": "swap",
		"color": "#00B42A",
		"description": "加班调休申请",
		"sort_order": 6,
	},
]

SEED_TEMPLATES = [
	{
		"template_name": "入职",
		"category": "人事",
		"icon": "user-add",
		"color": "#165DFF",
		"description": "用于新员工入职申请；审批通过后可进入入职办理状态",
		"default_group": "人事审批",
		"sort_order": 1,
	},
	{
		"template_name": "离职",
		"category": "人事",
		"icon": "user",
		"color": "#F53F3F",
		"description": "员工离职申请，审批通过后进入离职流程",
		"default_group": "人事审批",
		"sort_order": 2,
	},
	{
		"template_name": "请假申请",
		"category": "考勤",
		"icon": "calendar",
		"color": "#0FC6C2",
		"description": "员工请假审批模板，可按假期类型扩展字段",
		"default_group": "考勤审批",
		"sort_order": 3,
	},
	{
		"template_name": "加班申请",
		"category": "考勤",
		"icon": "thunderbolt",
		"color": "#F77234",
		"description": "加班审批模板，支持按部门条件分支（二期）",
		"default_group": "考勤审批",
		"sort_order": 4,
	},
	{
		"template_name": "补卡申请",
		"category": "考勤",
		"icon": "clock-circle",
		"color": "#722ED1",
		"description": "漏打卡补卡审批模板",
		"default_group": "考勤审批",
		"sort_order": 5,
	},
	{
		"template_name": "调薪",
		"category": "薪资",
		"icon": "trophy",
		"color": "#F7BA1E",
		"description": "员工调薪申请模板",
		"default_group": "人事审批",
		"sort_order": 6,
	},
	{
		"template_name": "用章申请",
		"category": "行政",
		"icon": "stamp",
		"color": "#86909C",
		"description": "公司用章审批模板",
		"default_group": "人事审批",
		"sort_order": 7,
	},
]


def _require_admin_permission(permission_type: str = "read") -> None:
	if "System Manager" in frappe.get_roles():
		return
	if not frappe.has_permission("Approval Form", permission_type):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def seed_approval_admin_data() -> None:
	"""Idempotent seed for groups, sample forms, and templates."""
	if not frappe.db.exists("DocType", "Approval Form Group"):
		return

	for row in SEED_GROUPS:
		if frappe.db.exists("Approval Form Group", row["group_name"]):
			continue
		frappe.get_doc(
			{
				"doctype": "Approval Form Group",
				"group_name": row["group_name"],
				"sort_order": row["sort_order"],
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

	process_json = json.dumps(DEFAULT_PROCESS, ensure_ascii=False)
	empty_schema_json = json.dumps({"fields": []}, ensure_ascii=False)

	for row in SEED_FORMS:
		exists = frappe.db.exists(
			"Approval Form",
			{"form_name": row["form_name"], "group": row["group"]},
		)
		extras = FORM_SEED_EXTRAS.get(row["form_name"], {})
		schema_json = dumps_schema(extras["form_schema"]) if extras.get("form_schema") else empty_schema_json
		if exists:
			# backfill schema/hook for existing seed forms when empty
			doc = frappe.get_doc("Approval Form", exists)
			dirty = False
			if extras.get("form_schema") and (
				not doc.form_schema_json or doc.form_schema_json.strip() in ("", "{}", '{"fields":[]}')
			):
				doc.form_schema_json = schema_json
				dirty = True
			if extras.get("business_hook") and not doc.business_hook:
				doc.business_hook = extras["business_hook"]
				dirty = True
			if not doc.process_json:
				doc.process_json = process_json
				doc.process_summary = DEFAULT_PROCESS_SUMMARY
				dirty = True
			if dirty:
				doc.save(ignore_permissions=True)
			continue
		frappe.get_doc(
			{
				"doctype": "Approval Form",
				"form_name": row["form_name"],
				"group": row["group"],
				"icon": row["icon"],
				"color": row["color"],
				"description": row["description"],
				"visibility": "全公司",
				"status": "使用中",
				"process_summary": DEFAULT_PROCESS_SUMMARY,
				"process_json": process_json,
				"form_schema_json": schema_json,
				"business_hook": extras.get("business_hook") or "",
				"sort_order": row["sort_order"],
			}
		).insert(ignore_permissions=True)

	for row in SEED_TEMPLATES:
		tpl_schema = empty_schema_json
		if row["template_name"] == "请假申请":
			tpl_schema = dumps_schema(LEAVE_SCHEMA)
		elif row["template_name"] in ("外出",):
			tpl_schema = dumps_schema(OUT_SCHEMA)
		if frappe.db.exists("Approval Template", row["template_name"]):
			tpl = frappe.get_doc("Approval Template", row["template_name"])
			if (
				row["template_name"] == "请假申请"
				and (not tpl.form_schema_json or tpl.form_schema_json.strip() in ("", "{}", '{"fields":[]}'))
			):
				tpl.form_schema_json = dumps_schema(LEAVE_SCHEMA)
				tpl.process_json = process_json
				tpl.default_process_summary = DEFAULT_PROCESS_SUMMARY
				tpl.save(ignore_permissions=True)
			continue
		frappe.get_doc(
			{
				"doctype": "Approval Template",
				"template_name": row["template_name"],
				"category": row["category"],
				"icon": row["icon"],
				"color": row["color"],
				"description": row["description"],
				"is_system": 1,
				"default_group": row["default_group"],
				"default_process_summary": DEFAULT_PROCESS_SUMMARY,
				"form_schema_json": tpl_schema,
				"process_json": process_json,
				"sort_order": row["sort_order"],
			}
		).insert(ignore_permissions=True)

	frappe.db.commit()


@frappe.whitelist()
def list_approval_groups():
	_require_admin_permission("read")
	seed_approval_admin_data()
	groups = frappe.get_all(
		"Approval Form Group",
		filters={"enabled": 1},
		fields=["name", "group_name", "sort_order"],
		order_by="sort_order asc, group_name asc",
	)
	for g in groups:
		g["form_count"] = frappe.db.count("Approval Form", {"group": g.name})
	return groups


@frappe.whitelist()
def list_approval_forms(group: str | None = None, keyword: str | None = None):
	_require_admin_permission("read")
	seed_approval_admin_data()
	filters: dict = {}
	if group:
		filters["group"] = group
	or_filters = None
	if keyword:
		kw = f"%{keyword.strip()}%"
		or_filters = [
			["form_name", "like", kw],
			["description", "like", kw],
			["process_summary", "like", kw],
		]
	rows = frappe.get_all(
		"Approval Form",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"form_name",
			"group",
			"status",
			"visibility",
			"icon",
			"color",
			"description",
			"process_summary",
			"source_template",
			"sort_order",
			"modified",
		],
		order_by="sort_order asc, form_name asc",
	)
	return rows


@frappe.whitelist()
def list_approval_templates(category: str | None = None, keyword: str | None = None):
	_require_admin_permission("read")
	seed_approval_admin_data()
	filters: dict = {}
	if category and category != "全部":
		filters["category"] = category
	or_filters = None
	if keyword:
		kw = f"%{keyword.strip()}%"
		or_filters = [
			["template_name", "like", kw],
			["description", "like", kw],
		]
	return frappe.get_all(
		"Approval Template",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"template_name",
			"category",
			"description",
			"icon",
			"color",
			"default_group",
			"default_process_summary",
			"is_system",
			"sort_order",
		],
		order_by="sort_order asc, template_name asc",
	)


@frappe.whitelist()
def use_approval_template(template_name: str, group: str | None = None):
	_require_admin_permission("write")
	if not template_name:
		frappe.throw(_("请指定模板"))
	tpl = frappe.get_doc("Approval Template", template_name)
	target_group = group or tpl.default_group
	if not target_group:
		# fallback first enabled group
		target_group = frappe.db.get_value(
			"Approval Form Group",
			{"enabled": 1},
			"name",
			order_by="sort_order asc",
		)
	if not target_group:
		frappe.throw(_("请先创建审批表单分组"))

	form_name = tpl.template_name
	# avoid confusing duplicate display names in same group
	existing = frappe.db.count(
		"Approval Form",
		{"form_name": form_name, "group": target_group},
	)
	if existing:
		form_name = f"{tpl.template_name} ({existing + 1})"

	doc = frappe.get_doc(
		{
			"doctype": "Approval Form",
			"form_name": form_name,
			"group": target_group,
			"icon": tpl.icon or "file",
			"color": tpl.color or "#165DFF",
			"description": tpl.description,
			"visibility": "全公司",
			"status": "使用中",
			"process_summary": tpl.default_process_summary or DEFAULT_PROCESS_SUMMARY,
			"process_json": tpl.process_json or json.dumps(DEFAULT_PROCESS, ensure_ascii=False),
			"form_schema_json": tpl.form_schema_json
			or json.dumps({"fields": []}, ensure_ascii=False),
			"source_template": tpl.name,
			"sort_order": 99,
		}
	)
	doc.insert(ignore_permissions=True)
	return {
		"name": doc.name,
		"form_name": doc.form_name,
		"group": doc.group,
	}


@frappe.whitelist()
def save_approval_form(payload: str | dict):
	_require_admin_permission("write")
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	name = data.get("name")
	fields = {
		"form_name": data.get("form_name"),
		"group": data.get("group"),
		"status": data.get("status") or "使用中",
		"visibility": data.get("visibility") or "全公司",
		"icon": data.get("icon") or "file",
		"color": data.get("color") or "#165DFF",
		"description": data.get("description") or "",
		"process_summary": data.get("process_summary") or "",
		"sort_order": cint(data.get("sort_order")),
	}
	if not fields["form_name"] or not fields["group"]:
		frappe.throw(_("表单名称和分组为必填"))

	if name and frappe.db.exists("Approval Form", name):
		doc = frappe.get_doc("Approval Form", name)
		doc.update(fields)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": "Approval Form", **fields})
		doc.insert(ignore_permissions=True)
	return {"name": doc.name, "form_name": doc.form_name}


@frappe.whitelist()
def save_approval_group(payload: str | dict):
	_require_admin_permission("write")
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	name = data.get("name")
	group_name = (data.get("group_name") or "").strip()
	if not group_name:
		frappe.throw(_("分组名称不能为空"))
	sort_order = cint(data.get("sort_order"))
	enabled = 1 if data.get("enabled", 1) else 0

	if name and frappe.db.exists("Approval Form Group", name):
		doc = frappe.get_doc("Approval Form Group", name)
		# rename if needed
		if doc.group_name != group_name:
			frappe.rename_doc("Approval Form Group", doc.name, group_name, force=True)
			doc = frappe.get_doc("Approval Form Group", group_name)
		doc.sort_order = sort_order
		doc.enabled = enabled
		doc.save(ignore_permissions=True)
	else:
		if frappe.db.exists("Approval Form Group", group_name):
			frappe.throw(_("分组已存在：{0}").format(group_name))
		doc = frappe.get_doc(
			{
				"doctype": "Approval Form Group",
				"group_name": group_name,
				"sort_order": sort_order,
				"enabled": enabled,
			}
		)
		doc.insert(ignore_permissions=True)
	return {"name": doc.name, "group_name": doc.group_name}


@frappe.whitelist()
def delete_approval_group(name: str):
	_require_admin_permission("delete")
	if not name:
		frappe.throw(_("请指定分组"))
	count = frappe.db.count("Approval Form", {"group": name})
	if count:
		frappe.throw(_("该分组下仍有 {0} 个表单，无法删除").format(count))
	frappe.delete_doc("Approval Form Group", name, ignore_permissions=True)
	return {"ok": True}


def verify_approval_admin_setup():
	"""CLI helper: bench execute employee_roster.hr_roster.approval_admin.verify_approval_admin_setup"""
	seed_approval_admin_data()
	groups = list_approval_groups()
	forms = list_approval_forms(group="考勤审批")
	templates = list_approval_templates(category="人事")
	used = use_approval_template("入职")
	sidebar_links = []
	if frappe.db.exists("Sidebar", "hr_roster"):
		sidebar_links = [row.link_to for row in frappe.get_doc("Sidebar", "hr_roster").items]
	return {
		"groups": [(g.name, g.form_count) for g in groups],
		"forms": [f.form_name for f in forms],
		"templates": [t.template_name for t in templates],
		"used": used,
		"sidebar": sidebar_links,
		"page": bool(frappe.db.exists("Page", "approvals")),
		"total_forms": frappe.db.count("Approval Form"),
	}
