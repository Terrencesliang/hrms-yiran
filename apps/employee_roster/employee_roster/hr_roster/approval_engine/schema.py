# Copyright (c) 2026 stillgroup
# License: MIT
"""Form schema validation and helpers."""

from __future__ import annotations

import json
import re
from typing import Any

import frappe
from frappe import _

ALLOWED_FIELD_TYPES = {
	"text",
	"textarea",
	"number",
	"date",
	"select",
	"multiselect",
	"attachment",
	"employee",
	"department",
}

_FIELD_KEY_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")


def parse_json(value: Any, default: Any = None) -> Any:
	if value is None or value == "":
		return default if default is not None else {}
	if isinstance(value, (dict, list)):
		return value
	try:
		return json.loads(value)
	except (TypeError, ValueError):
		frappe.throw(_("JSON 格式无效"))


def empty_schema() -> dict:
	return {"fields": []}


def normalize_schema(schema: Any) -> dict:
	data = parse_json(schema, empty_schema())
	if not isinstance(data, dict):
		frappe.throw(_("表单 Schema 必须是对象"))
	fields = data.get("fields") or []
	if not isinstance(fields, list):
		frappe.throw(_("fields 必须是数组"))
	normalized = []
	seen = set()
	for idx, raw in enumerate(fields):
		if not isinstance(raw, dict):
			frappe.throw(_("第 {0} 个字段配置无效").format(idx + 1))
		ftype = (raw.get("type") or "text").strip()
		if ftype not in ALLOWED_FIELD_TYPES:
			frappe.throw(_("不支持的字段类型：{0}").format(ftype))
		key = (raw.get("key") or "").strip()
		if not key or not _FIELD_KEY_RE.match(key):
			frappe.throw(_("字段 key 无效：{0}").format(key or "(空)"))
		if key in seen:
			frappe.throw(_("字段 key 重复：{0}").format(key))
		seen.add(key)
		label = (raw.get("label") or key).strip()
		field = {
			"key": key,
			"label": label,
			"type": ftype,
			"required": 1 if raw.get("required") else 0,
			"placeholder": raw.get("placeholder") or "",
			"options": raw.get("options") or [],
			"default": raw.get("default"),
		}
		if ftype in ("select", "multiselect") and not field["options"]:
			field["options"] = []
		normalized.append(field)
	return {"fields": normalized}


def validate_form_data(schema: dict, data: Any) -> dict:
	schema = normalize_schema(schema)
	payload = parse_json(data, {})
	if not isinstance(payload, dict):
		frappe.throw(_("表单数据必须是对象"))
	out: dict[str, Any] = {}
	for field in schema["fields"]:
		key = field["key"]
		val = payload.get(key)
		if field["required"] and (val is None or val == "" or val == []):
			frappe.throw(_("请填写：{0}").format(field["label"]))
		if val is None or val == "":
			continue
		ftype = field["type"]
		if ftype == "number":
			try:
				out[key] = float(val)
			except (TypeError, ValueError):
				frappe.throw(_("{0} 必须是数字").format(field["label"]))
		elif ftype == "multiselect":
			if isinstance(val, str):
				out[key] = [v.strip() for v in val.split(",") if v.strip()]
			elif isinstance(val, list):
				out[key] = val
			else:
				frappe.throw(_("{0} 选项格式无效").format(field["label"]))
		else:
			out[key] = val
	return out


def dumps(schema: dict) -> str:
	return json.dumps(schema, ensure_ascii=False)
