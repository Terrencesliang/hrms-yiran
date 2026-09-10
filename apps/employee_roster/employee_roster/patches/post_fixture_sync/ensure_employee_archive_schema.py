# Copyright (c) 2026 stillgroup
# License: MIT
"""补齐员工档案子表 DocType 与扩展字段。"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from employee_roster.hr_roster.employee_detail_schema import (
	CHILD_DOCTYPES,
	EXTRA_SCALAR_FIELDS,
	TABLE_FIELDS,
)


def execute():
	_ensure_child_doctypes()
	_ensure_extra_fields()
	frappe.clear_cache(doctype="Employee")


def _ensure_child_doctypes():
	for spec in CHILD_DOCTYPES:
		name = spec["name"]
		if frappe.db.exists("DocType", name):
			_sync_child_fields(spec)
			continue
		doc = frappe.get_doc(
			{
				"doctype": "DocType",
				"name": name,
				"module": spec["module"],
				"custom": 0,
				"istable": 1,
				"editable_grid": 1,
				"engine": "InnoDB",
				"fields": [
					{
						"fieldname": f.get("fieldname"),
						"fieldtype": f.get("fieldtype"),
						"label": f.get("label"),
						"reqd": f.get("reqd", 0),
						"in_list_view": f.get("in_list_view", 0),
						"options": f.get("options"),
						"default": f.get("default"),
					}
					for f in spec["fields"]
				],
				"permissions": [],
			}
		)
		doc.insert(ignore_permissions=True)


def _sync_child_fields(spec):
	"""已存在的子表：补缺失字段。"""
	meta = frappe.get_meta(spec["name"])
	existing = {df.fieldname for df in meta.fields}
	doc = frappe.get_doc("DocType", spec["name"])
	changed = False
	for f in spec["fields"]:
		if f["fieldname"] in existing:
			continue
		doc.append(
			"fields",
			{
				"fieldname": f.get("fieldname"),
				"fieldtype": f.get("fieldtype"),
				"label": f.get("label"),
				"reqd": f.get("reqd", 0),
				"in_list_view": f.get("in_list_view", 0),
				"options": f.get("options"),
				"default": f.get("default"),
			},
		)
		changed = True
	if changed:
		doc.save(ignore_permissions=True)


def _ensure_extra_fields():
	fields = []
	for f in EXTRA_SCALAR_FIELDS:
		fields.append({**f})
	for f in TABLE_FIELDS:
		fields.append(
			{
				"fieldname": f["fieldname"],
				"fieldtype": "Table",
				"label": f["label"],
				"options": f["options"],
				"insert_after": f["insert_after"],
			}
		)
	create_custom_fields({"Employee": fields}, ignore_validate=True)
