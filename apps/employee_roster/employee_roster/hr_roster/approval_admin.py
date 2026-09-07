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
from employee_roster.hr_roster.approval_hr_presets import (
	HR_APPROVAL_FORMS,
	HR_PROCESS_ROLES,
)

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

SEED_TEMPLATES = []  # templates are synced 1:1 from Approval Form (see _sync_templates_from_forms)

# Old template names → current form names (rename during sync)
LEGACY_TEMPLATE_RENAMES = {
	"入职": "录用",
	"离职": "离职申请表",
	"请假申请": "请假",
	"加班申请": "加班",
	"补卡申请": "补卡",
	"调薪": "薪资调整",
}

GROUP_TO_CATEGORY = {
	"考勤审批": "考勤",
	"人事审批": "人事",
}

FORM_CATEGORY_OVERRIDE = {
	"薪资调整": "薪资",
}


SEED_CACHE_KEY = "employee_roster:approval_data_ready"


def _clear_approval_seed_cache() -> None:
	try:
		frappe.cache.delete_value(SEED_CACHE_KEY)
	except Exception:
		pass


def ensure_approval_seeded() -> None:
	"""Cheap read-path guard: only seed when the site has no forms yet.

	Full seed + template sync is expensive and must not run on every list request.
	"""
	if frappe.cache.get_value(SEED_CACHE_KEY):
		return
	if not frappe.db.exists("DocType", "Approval Form"):
		return
	if frappe.db.count("Approval Form") > 0:
		frappe.cache.set_value(SEED_CACHE_KEY, 1, expires_in_sec=6 * 3600)
		return
	seed_approval_admin_data()


def _require_admin_permission(permission_type: str = "read") -> None:
	if "System Manager" in frappe.get_roles():
		return
	if not frappe.has_permission("Approval Form", permission_type):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _ensure_hr_process_roles() -> None:
	for role_name in HR_PROCESS_ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			}
		).insert(ignore_permissions=True)


def _seed_hr_approval_forms(*, form_meta) -> None:
	"""Create/update the 7 HR forms from the org process chart."""
	has_form_schema = form_meta.has_field("form_schema_json")
	has_business_hook = form_meta.has_field("business_hook")

	for row in HR_APPROVAL_FORMS:
		process = row["process"]
		process_json = json.dumps(process, ensure_ascii=False)
		summary = row["process_summary"]
		schema_json = dumps_schema(row.get("form_schema") or {"fields": []})
		exists = frappe.db.exists(
			"Approval Form",
			{"form_name": row["form_name"], "group": row["group"]},
		)
		if exists:
			doc = frappe.get_doc("Approval Form", exists)
			doc.process_json = process_json
			doc.process_summary = summary
			doc.description = row["description"]
			doc.icon = row["icon"]
			doc.color = row["color"]
			doc.sort_order = row["sort_order"]
			doc.status = "使用中"
			doc.visibility = "全公司"
			if has_form_schema:
				doc.form_schema_json = schema_json
			doc.save(ignore_permissions=True)
			continue

		payload = {
			"doctype": "Approval Form",
			"form_name": row["form_name"],
			"group": row["group"],
			"icon": row["icon"],
			"color": row["color"],
			"description": row["description"],
			"visibility": "全公司",
			"status": "使用中",
			"process_summary": summary,
			"process_json": process_json,
			"sort_order": row["sort_order"],
		}
		if has_form_schema:
			payload["form_schema_json"] = schema_json
		if has_business_hook:
			payload["business_hook"] = ""
		frappe.get_doc(payload).insert(ignore_permissions=True)


def _template_category_for_form(form_name: str, group: str) -> str:
	if form_name in FORM_CATEGORY_OVERRIDE:
		return FORM_CATEGORY_OVERRIDE[form_name]
	return GROUP_TO_CATEGORY.get(group) or "其他"


def _migrate_legacy_templates() -> None:
	for old, new in LEGACY_TEMPLATE_RENAMES.items():
		if not frappe.db.exists("Approval Template", old):
			continue
		if old == new:
			continue
		if frappe.db.exists("Approval Template", new):
			frappe.delete_doc("Approval Template", old, ignore_permissions=True, force=True)
		else:
			frappe.rename_doc("Approval Template", old, new, force=True)


def _sync_templates_from_forms() -> None:
	"""Keep Approval Template 1:1 with enabled Approval Form (name / process / schema)."""
	if not frappe.db.exists("DocType", "Approval Template"):
		return

	_migrate_legacy_templates()

	forms = frappe.get_all(
		"Approval Form",
		filters={"status": "使用中"},
		fields=[
			"name",
			"form_name",
			"group",
			"icon",
			"color",
			"description",
			"process_summary",
			"process_json",
			"form_schema_json",
			"sort_order",
		],
		order_by="group asc, sort_order asc, form_name asc",
	)
	keep_names = set()
	# stable sort across groups: 考勤 first then 人事
	group_rank = {"考勤审批": 0, "人事审批": 1}
	forms = sorted(
		forms,
		key=lambda f: (group_rank.get(f.group, 9), cint(f.sort_order), f.form_name or ""),
	)

	for idx, form in enumerate(forms, start=1):
		keep_names.add(form.form_name)
		category = _template_category_for_form(form.form_name, form.group)
		process_json = form.process_json or json.dumps(DEFAULT_PROCESS, ensure_ascii=False)
		summary = form.process_summary or DEFAULT_PROCESS_SUMMARY
		schema_json = form.form_schema_json or json.dumps({"fields": []}, ensure_ascii=False)
		payload = {
			"template_name": form.form_name,
			"category": category,
			"icon": form.icon or "file",
			"color": form.color or "#165DFF",
			"description": form.description or "",
			"is_system": 1,
			"default_group": form.group,
			"default_process_summary": summary,
			"form_schema_json": schema_json,
			"process_json": process_json,
			"sort_order": idx,
		}
		if frappe.db.exists("Approval Template", form.form_name):
			tpl = frappe.get_doc("Approval Template", form.form_name)
			dirty = False
			for key, value in payload.items():
				if tpl.get(key) != value:
					tpl.set(key, value)
					dirty = True
			if dirty:
				tpl.save(ignore_permissions=True)
		else:
			frappe.get_doc({"doctype": "Approval Template", **payload}).insert(ignore_permissions=True)

	# drop system templates that no longer map to an enabled form
	orphans = frappe.get_all(
		"Approval Template",
		filters={"is_system": 1},
		pluck="name",
	)
	for name in orphans:
		if name not in keep_names:
			frappe.delete_doc("Approval Template", name, ignore_permissions=True, force=True)

	_clear_approval_seed_cache()
	frappe.cache.set_value(SEED_CACHE_KEY, 1, expires_in_sec=6 * 3600)


def seed_approval_admin_data() -> None:
	"""Idempotent seed for groups, sample forms, and templates."""
	if not frappe.db.exists("DocType", "Approval Form Group"):
		return

	_ensure_hr_process_roles()

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
	form_meta = frappe.get_meta("Approval Form")
	has_form_schema = form_meta.has_field("form_schema_json")
	has_business_hook = form_meta.has_field("business_hook")

	_seed_hr_approval_forms(form_meta=form_meta)

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
			if has_form_schema and extras.get("form_schema"):
				current_schema = (getattr(doc, "form_schema_json", None) or "").strip()
				if current_schema in ("", "{}", '{"fields":[]}'):
					doc.form_schema_json = schema_json
					dirty = True
			if has_business_hook and extras.get("business_hook") and not getattr(doc, "business_hook", None):
				doc.business_hook = extras["business_hook"]
				dirty = True
			if not doc.process_json:
				doc.process_json = process_json
				doc.process_summary = DEFAULT_PROCESS_SUMMARY
				dirty = True
			if dirty:
				doc.save(ignore_permissions=True)
			continue
		payload = {
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
			"sort_order": row["sort_order"],
		}
		if has_form_schema:
			payload["form_schema_json"] = schema_json
		if has_business_hook:
			payload["business_hook"] = extras.get("business_hook") or ""
		frappe.get_doc(payload).insert(ignore_permissions=True)

	_sync_templates_from_forms()
	frappe.cache.set_value(SEED_CACHE_KEY, 1, expires_in_sec=6 * 3600)
	frappe.db.commit()


@frappe.whitelist()
def list_approval_groups():
	_require_admin_permission("read")
	ensure_approval_seeded()
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
	ensure_approval_seeded()
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
	ensure_approval_seeded()
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
	existing = frappe.db.get_value(
		"Approval Form",
		{"form_name": form_name, "group": target_group},
		"name",
	)
	if existing:
		# already synced — do not create 请假 (2) duplicates
		doc = frappe.get_doc("Approval Form", existing)
		return {
			"name": doc.name,
			"form_name": doc.form_name,
			"group": doc.group,
			"existed": True,
		}

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
			"form_schema_json": tpl.form_schema_json or json.dumps({"fields": []}, ensure_ascii=False),
			"source_template": tpl.name,
			"sort_order": cint(tpl.sort_order),
		}
	)
	doc.insert(ignore_permissions=True)
	_sync_templates_from_forms()
	return {
		"name": doc.name,
		"form_name": doc.form_name,
		"group": doc.group,
		"existed": False,
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
	_sync_templates_from_forms()
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


@frappe.whitelist()
def delete_approval_forms(names: str | list | None = None):
	"""Batch delete Approval Form docs. Blocks if any form has running instances."""
	_require_admin_permission("delete")

	# normalize input: JSON string / list / scalar → unique ordered names
	if isinstance(names, str):
		raw = names.strip()
		if raw.startswith("["):
			names = frappe.parse_json(raw)
		elif raw:
			names = [raw]
		else:
			names = []
	elif names is None:
		names = []
	elif not isinstance(names, (list, tuple)):
		names = [names]

	unique_names: list[str] = []
	seen: set[str] = set()
	for item in names:
		if item is None:
			continue
		name = str(item).strip() if not isinstance(item, str) else item.strip()
		if not name or name in seen:
			continue
		seen.add(name)
		unique_names.append(name)

	if not unique_names:
		return {"ok": True, "deleted": [], "count": 0}

	# 1 query: which of these forms still exist
	existing = set(
		frappe.get_all(
			"Approval Form",
			filters={"name": ["in", unique_names]},
			pluck="name",
		)
	)
	candidates = [n for n in unique_names if n in existing]
	if not candidates:
		return {"ok": True, "deleted": [], "count": 0}

	# 1 query: any running instances among candidates (all-or-nothing)
	if frappe.db.exists("DocType", "Approval Instance"):
		running_rows = frappe.get_all(
			"Approval Instance",
			filters={"approval_form": ["in", candidates], "status": "进行中"},
			fields=["approval_form"],
		)
		if running_rows:
			counts: dict[str, int] = {}
			for row in running_rows:
				form = row.approval_form
				counts[form] = counts.get(form, 0) + 1
			titles = {
				r.name: r.form_name
				for r in frappe.get_all(
					"Approval Form",
					filters={"name": ["in", list(counts)]},
					fields=["name", "form_name"],
				)
			}
			blocked = [
				f"{titles.get(form, form)}（{cnt} 条进行中）"
				for form, cnt in counts.items()
			]
			frappe.throw(_("以下表单仍有进行中的审批，无法删除：{0}").format("、".join(blocked)))

	# Keep frappe.delete_doc semantics (hooks / link checks / on_trash).
	# Typical admin batch is tens of rows; no raw SQL / no chunking needed.
	deleted: list[str] = []
	for name in candidates:
		frappe.delete_doc("Approval Form", name, ignore_permissions=True)
		deleted.append(name)

	_sync_templates_from_forms()
	return {"ok": True, "deleted": deleted, "count": len(deleted)}


def verify_approval_admin_setup():
	"""CLI helper: bench execute employee_roster.hr_roster.approval_admin.verify_approval_admin_setup"""
	seed_approval_admin_data()
	groups = list_approval_groups()
	forms = list_approval_forms(group="考勤审批")
	templates = list_approval_templates(category="人事")
	used = use_approval_template("录用")
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
