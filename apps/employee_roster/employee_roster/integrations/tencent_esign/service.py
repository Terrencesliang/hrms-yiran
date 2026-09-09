"""合同签署业务编排。"""
from __future__ import annotations

import base64
import json
import uuid
from typing import Any

import frappe
import requests
from frappe.utils import add_days, get_datetime, now_datetime
from frappe.utils.file_manager import save_file

from .client import TencentESignClient

STATUS_MAP = {
	"INIT": "Draft",
	"PREPARE": "Draft",
	"REVIEW": "Pending",
	"WAIT_START": "Pending",
	"EXECUTING": "Pending",
	"START": "Signing",
	"RUNNING": "Signing",
	"SIGNING": "Signing",
	"FINISHED": "Completed",
	"COMPLETE": "Completed",
	"COMPLETED": "Completed",
	"CANCEL": "Cancelled",
	"CANCELED": "Cancelled",
	"CANCELLED": "Cancelled",
	"REJECTED": "Rejected",
	"EXPIRED": "Expired",
	"ABORTED": "Error",
	"ERROR": "Error",
	"RELIEVED": "Cancelled",
}


def map_vendor_status(status: str | None) -> str:
	return STATUS_MAP.get(str(status or "").upper(), "Pending")


def parse_json_config(value: str | dict | list | None, expected: type) -> Any:
	if value in (None, ""):
		return expected()
	if isinstance(value, expected):
		return value
	try:
		parsed = json.loads(value)
	except (TypeError, ValueError) as exc:
		raise frappe.ValidationError("电子签模板 JSON 配置无效") from exc
	if not isinstance(parsed, expected):
		raise frappe.ValidationError("电子签模板 JSON 配置类型无效")
	return parsed


def _safe_error(exc: Exception) -> str:
	"""只持久化异常类型及截断消息, 不记录请求体、凭据或堆栈。"""
	message = str(exc).replace("\r", " ").replace("\n", " ")
	return f"{type(exc).__name__}: {message[:1000]}"


def _mapped_value(employee: Any, contract_fields: dict[str, Any], reference: Any) -> Any:
	if not isinstance(reference, str):
		return reference
	if reference.startswith("$contract."):
		return contract_fields.get(reference.removeprefix("$contract."), "")
	fieldname = reference.removeprefix("$employee.")
	if reference.startswith("$employee.") or employee.meta.has_field(fieldname) or fieldname == "name":
		return getattr(employee, fieldname, "")
	return reference


def _resolve(value: Any, employee: Any, contract_fields: dict[str, Any]) -> Any:
	if isinstance(value, dict):
		return {key: _resolve(item, employee, contract_fields) for key, item in value.items()}
	if isinstance(value, list):
		return [_resolve(item, employee, contract_fields) for item in value]
	return _mapped_value(employee, contract_fields, value)


def build_template_payload(
	template: Any,
	employee: Any,
	trans_reference: str,
	contract_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
	contract_fields = contract_fields or {}
	field_mapping = parse_json_config(template.field_mapping, dict)
	actor_config = parse_json_config(template.actor_config, dict)
	sign_config = parse_json_config(template.sign_config, dict)

	form_fields = [
		{
			"ComponentName": component,
			"ComponentValue": str(_mapped_value(employee, contract_fields, source) or ""),
		}
		for component, source in field_mapping.items()
	]
	approvers = _resolve(actor_config.get("approvers") or [], employee, contract_fields)
	if not approvers:
		approvers = [
			{
				"ApproverType": 1,
				"ApproverName": employee.employee_name,
				"ApproverMobile": employee.cell_number,
				"NotifyType": sign_config.get("notify_type", "SMS"),
			}
		]
	if template.seal_id and sign_config.get("seal_component_id"):
		form_fields.append(
			{"ComponentId": sign_config["seal_component_id"], "ComponentValue": template.seal_id}
		)
	return {
		"flow_name": str(
			sign_config.get("flow_name")
			or f"{template.template_name}-{employee.employee_name}-{trans_reference[-8:]}"
		)[:200],
		"flow_type": str(sign_config.get("flow_type") or template.template_name)[:200],
		"description": str(sign_config.get("description") or ""),
		"deadline": int(
			sign_config.get("deadline")
			or get_datetime(add_days(now_datetime(), int(sign_config.get("valid_days", 30)))).timestamp()
		),
		"unordered": bool(sign_config.get("unordered", False)),
		"approvers": approvers,
		"form_fields": form_fields,
		"user_data": base64.b64encode(
			json.dumps({"trans_reference": trans_reference}).encode()
		).decode(),
	}


def _template(name: str) -> Any:
	doc = frappe.get_doc("Contract Sign Template", name)
	if not doc.enabled:
		raise frappe.ValidationError("电子签模板已停用")
	return doc


def preview_contract(
	template_name: str, employee_name: str, contract_fields: dict[str, Any] | None = None
) -> dict[str, Any]:
	template = _template(template_name)
	employee = frappe.get_doc("Employee", employee_name)
	payload = build_template_payload(
		template, employee, f"preview-{uuid.uuid4().hex}", contract_fields
	)
	client = TencentESignClient()
	flow = client.create_flow(
		flow_name=payload["flow_name"],
		approvers=payload["approvers"],
		flow_type=payload["flow_type"],
		description=payload["description"],
		deadline=payload["deadline"],
		unordered=payload["unordered"],
		user_data=payload["user_data"],
	)
	document = client.create_document(
		template_id=template.template_id,
		flow_id=flow["FlowId"],
		form_fields=payload["form_fields"],
		need_preview=True,
		file_name=payload["flow_name"],
	)
	return {
		"preview_url": document.get("PreviewUrl") or document.get("PreviewFileUrl"),
		"request_id": document.get("RequestId"),
	}


def create_contract_signing(
	template_name: str,
	employee_name: str,
	trans_reference: str | None = None,
	contract_fields: dict[str, Any] | None = None,
) -> Any:
	trans_reference = (trans_reference or uuid.uuid4().hex).strip()
	if existing := frappe.db.exists("Contract Signing", {"trans_reference": trans_reference}):
		return frappe.get_doc("Contract Signing", existing)

	template = _template(template_name)
	employee = frappe.get_doc("Employee", employee_name)
	signing = frappe.get_doc(
		{
			"doctype": "Contract Signing",
			"provider": "Tencent",
			"employee": employee.name,
			"sign_template": template.name,
			"trans_reference": trans_reference,
			"status": "Draft",
			"requested_on": now_datetime(),
			"requested_by": frappe.session.user,
			"contract_fields": frappe.as_json(contract_fields or {}),
		}
	).insert()
	try:
		payload = build_template_payload(template, employee, trans_reference, contract_fields)
		client = TencentESignClient()
		flow = client.create_flow(
			flow_name=payload["flow_name"],
			approvers=payload["approvers"],
			flow_type=payload["flow_type"],
			description=payload["description"],
			deadline=payload["deadline"],
			unordered=payload["unordered"],
			user_data=payload["user_data"],
		)
		signing.flow_id = flow["FlowId"]
		signing.vendor_status = "CREATED"
		signing.status = "Pending"
		signing.save()

		document = client.create_document(
			template_id=template.template_id,
			flow_id=signing.flow_id,
			form_fields=payload["form_fields"],
			file_name=payload["flow_name"],
		)
		signing.document_id = document.get("DocumentId")
		signing.save()

		started = client.start_flow(signing.flow_id)
		signing.vendor_status = started.get("Status") or "START"
		signing.status = map_vendor_status(signing.vendor_status)
		signing.started_on = now_datetime()
		signing.error_status = ""
		signing.save()
	except Exception as exc:
		signing.status = "Error"
		signing.error_status = _safe_error(exc)
		signing.save()
	return signing


def sync_contract_status(signing: Any) -> Any:
	response = TencentESignClient().describe_flow_info([signing.flow_id])
	details = response.get("FlowDetailInfos") or []
	if not details:
		raise frappe.ValidationError("腾讯电子签未返回合同状态")
	detail = details[0]
	vendor_status = detail.get("FlowStatus") or detail.get("Status") or ""
	signing.vendor_status = vendor_status
	signing.status = map_vendor_status(vendor_status)
	signing.last_synced_on = now_datetime()
	if signing.status == "Completed" and not signing.completed_on:
		signing.completed_on = now_datetime()
	signing.error_status = ""
	signing.save()
	return signing


def mark_operation_error(signing: Any, exc: Exception) -> None:
	signing.error_status = _safe_error(exc)
	signing.save()


def archive_signed_contract(signing_name: str) -> dict[str, Any]:
	"""下载已签 PDF 并作为私有附件归档到签署记录。"""
	signing = frappe.get_doc("Contract Signing", signing_name)
	if signing.signed_file:
		return {"file_url": signing.signed_file, "already_archived": True}
	if signing.status != "Completed" or not signing.flow_id:
		raise frappe.ValidationError("仅可归档已完成的电子签合同")

	result = TencentESignClient().describe_file_urls(signing.flow_id)
	files = result.get("FileUrls") or []
	download_url = files[0].get("Url") if files else ""
	if not download_url:
		raise frappe.ValidationError("腾讯电子签未返回已签合同下载地址")

	response = requests.get(download_url, timeout=30)
	response.raise_for_status()
	max_bytes = 25 * 1024 * 1024
	if len(response.content) > max_bytes:
		raise frappe.ValidationError("已签合同超过 25MB 无法自动归档")
	file_doc = save_file(
		f"{signing.name}.pdf",
		response.content,
		"Contract Signing",
		signing.name,
		is_private=1,
	)
	signing.signed_file = file_doc.file_url
	signing.error_status = ""
	signing.save(ignore_permissions=True)
	return {"file_url": file_doc.file_url, "request_id": result.get("RequestId")}
