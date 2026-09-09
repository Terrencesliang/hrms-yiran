"""将升级前的电子签数据明确标记为腾讯, 避免默认供应商误判。"""
from __future__ import annotations

import frappe


def execute() -> None:
	if frappe.db.table_exists("Contract Sign Template"):
		for row in frappe.get_all(
			"Contract Sign Template",
			filters={"template_id": ["!=", ""]},
			fields=["name", "provider", "provider_template_id", "template_id"],
		):
			if row.provider in ("", None, "Fadada"):
				frappe.db.set_value(
					"Contract Sign Template",
					row.name,
					{
						"provider": "Tencent",
						"provider_template_id": row.provider_template_id or row.template_id,
					},
					update_modified=False,
				)
	if frappe.db.table_exists("Contract Signing"):
		for row in frappe.get_all(
			"Contract Signing",
			filters={"flow_id": ["!=", ""]},
			fields=["name", "provider", "sign_task_id"],
		):
			if not row.sign_task_id and row.provider in ("", None, "Fadada"):
				frappe.db.set_value(
					"Contract Signing", row.name, "provider", "Tencent", update_modified=False
				)
	if frappe.db.table_exists("Contract Signing Event"):
		for row in frappe.get_all(
			"Contract Signing Event",
			filters={"flow_id": ["!=", ""]},
			fields=["name", "provider", "sign_task_id"],
		):
			if not row.sign_task_id and row.provider in ("", None, "Fadada"):
				frappe.db.set_value(
					"Contract Signing Event",
					row.name,
					"provider",
					"Tencent",
					update_modified=False,
				)
