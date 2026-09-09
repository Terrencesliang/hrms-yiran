# Copyright (c) 2026 stillgroup
# License: MIT
from __future__ import annotations

import json

import frappe
from frappe.model.document import Document

ALLOWED_EMPLOYEE_FIELDS = {
	"name",
	"employee_name",
	"cell_number",
	"personal_email",
	"company_email",
	"date_of_joining",
	"designation",
	"department",
	"company",
	"gender",
}
ALLOWED_CONTRACT_FIELDS = {
	"address",
	"contract_end",
	"contract_start",
	"start_date",
	"end_date",
	"designation",
	"gender",
	"id_number",
	"join_date_text",
	"mobile",
	"number_text",
	"probation",
	"probation_end_date",
	"job_title",
	"sign_time",
	"work_location",
	"salary",
	"contract_term",
}
ALLOWED_ACTOR_KEYS = {"employee_actor_id", "corp_actor_id", "actors"}
ALLOWED_SIGN_KEYS = {
	"valid_days",
	"subject",
	"auto_fill_finalize",
	"auto_finish",
	"business_id",
}


def _json_object(doc: Document, fieldname: str) -> dict:
	value = doc.get(fieldname)
	if not value:
		return {}
	try:
		parsed = json.loads(value) if isinstance(value, str) else value
	except (TypeError, ValueError) as exc:
		raise frappe.ValidationError(f"{fieldname} 必须是有效 JSON") from exc
	if not isinstance(parsed, dict):
		raise frappe.ValidationError(f"{fieldname} 必须是 JSON 对象")
	return parsed


def _validate_sources(value: object) -> None:
	if isinstance(value, dict):
		for item in value.values():
			_validate_sources(item)
	elif isinstance(value, list):
		for item in value:
			_validate_sources(item)
	elif isinstance(value, str) and value.startswith("$employee."):
		if value.removeprefix("$employee.") not in ALLOWED_EMPLOYEE_FIELDS:
			raise frappe.ValidationError(f"不允许映射员工字段: {value}")
	elif isinstance(value, str) and value.startswith("$contract."):
		if value.removeprefix("$contract.") not in ALLOWED_CONTRACT_FIELDS:
			raise frappe.ValidationError(f"不允许映射合同字段: {value}")


class ContractSignTemplate(Document):
	def validate(self) -> None:
		field_mapping = _json_object(self, "field_mapping")
		actor_config = _json_object(self, "actor_config")
		sign_config = _json_object(self, "sign_config")
		_validate_sources(field_mapping)
		_validate_sources(actor_config)
		unknown_actor = set(actor_config) - ALLOWED_ACTOR_KEYS
		unknown_sign = set(sign_config) - ALLOWED_SIGN_KEYS
		if unknown_actor:
			raise frappe.ValidationError(
				f"actor_config 含不允许字段: {', '.join(sorted(unknown_actor))}"
			)
		if unknown_sign:
			raise frappe.ValidationError(
				f"sign_config 含不允许字段: {', '.join(sorted(unknown_sign))}"
			)
		if not self.enabled or (self.provider or "Fadada") != "Fadada":
			return
		required = {
			"供应商模板 ID": self.provider_template_id or self.template_id,
			"印章 ID": self.seal_id,
			"员工 Actor ID": self.employee_actor_id,
			"企业 Actor ID": self.corp_actor_id,
		}
		missing = [label for label, value in required.items() if not value]
		if missing:
			raise frappe.ValidationError(
				f"启用法大大模板前必须配置: {', '.join(missing)}"
			)
		if not actor_config.get("actors"):
			raise frappe.ValidationError("启用法大大模板前必须配置 actors")
		try:
			int(self.seal_id)
		except (TypeError, ValueError) as exc:
			raise frappe.ValidationError("法大大印章 ID 必须为数字") from exc
