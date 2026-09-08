"""腾讯电子签合同后端 API。"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from employee_roster.integrations.tencent_esign import callback as callback_handler
from employee_roster.integrations.tencent_esign import service
from employee_roster.integrations.tencent_esign.client import (
	ConfigurationError,
	TencentESignClient,
	configuration_status,
)

ALLOWED_ROLES = {"HR Manager", "System Manager"}
LIST_STATUS_MAP = {
	"pending": ["Pending", "Signing"],
	"signed": "Completed",
	"void": ["Cancelled", "Rejected", "Expired", "Error"],
}


def _require_manager() -> None:
	if frappe.session.user == "Guest" or not ALLOWED_ROLES.intersection(frappe.get_roles()):
		frappe.throw(_("无权访问电子签合同"), frappe.PermissionError)


def _require_doctype_permission(doctype: str, permission_type: str = "read") -> None:
	_require_manager()
	if not frappe.has_permission(doctype, permission_type):
		frappe.throw(_("无权执行此操作"), frappe.PermissionError)


def _signing(name: str, permission_type: str = "read") -> Any:
	_require_doctype_permission("Contract Signing", permission_type)
	doc = frappe.get_doc("Contract Signing", name)
	if not frappe.has_permission("Contract Signing", permission_type, doc=doc):
		frappe.throw(_("无权访问该签署记录"), frappe.PermissionError)
	return doc


def _safe_external_call(
	callback: Callable[[], Any], *, signing: Any | None = None
) -> dict[str, Any]:
	try:
		return {"ok": True, "data": callback()}
	except ConfigurationError as exc:
		return {"ok": False, "configured": False, "error": str(exc)}
	except Exception as exc:
		if signing is not None:
			service.mark_operation_error(signing, exc)
		else:
			frappe.log_error(title="腾讯电子签调用失败", message=type(exc).__name__)
		frappe.throw(_("腾讯电子签调用失败, 请查看错误日志或签署记录"))


@frappe.whitelist(methods=["GET"])
def get_templates() -> dict[str, Any]:
	_require_doctype_permission("Contract Sign Template", "read")
	return {
		"configuration": configuration_status(),
		"templates": frappe.get_all(
			"Contract Sign Template",
			filters={"enabled": 1},
			fields=["name", "template_name", "description", "seal_id", "modified"],
			order_by="template_name asc",
		),
	}


@frappe.whitelist(methods=["POST"])
def preview_contract(
	template: str, employee: str, contract_fields: dict[str, Any] | str | None = None
) -> dict[str, Any]:
	_require_doctype_permission("Contract Signing", "create")
	fields = service.parse_json_config(contract_fields, dict)
	return _safe_external_call(lambda: service.preview_contract(template, employee, fields))


@frappe.whitelist(methods=["POST"])
def create_contract_signing(
	template: str,
	employee: str,
	trans_reference: str | None = None,
	contract_fields: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_doctype_permission("Contract Signing", "create")
	fields = service.parse_json_config(contract_fields, dict)
	try:
		doc = service.create_contract_signing(template, employee, trans_reference, fields)
	except ConfigurationError as exc:
		return {"ok": False, "configured": False, "error": str(exc)}
	except Exception:
		frappe.throw(_("电子签合同发起失败, 请查看签署记录中的错误状态"))
	if doc.status == "Error":
		return {"ok": False, "error": doc.error_status, "signing": doc.as_dict()}
	return {"ok": True, "signing": doc.as_dict()}


@frappe.whitelist(methods=["GET"])
def list_contract_signings(
	employee: str | None = None,
	status: str | None = None,
	start: int = 0,
	page_length: int = 20,
) -> dict[str, Any]:
	_require_doctype_permission("Contract Signing", "read")
	filters: dict[str, Any] = {}
	if employee:
		filters["employee"] = employee
	if status:
		mapped_status = LIST_STATUS_MAP.get(status.lower(), status)
		filters["status"] = ["in", mapped_status] if isinstance(mapped_status, list) else mapped_status
	start = max(0, cint(start))
	page_length = max(1, min(cint(page_length), 100))
	return {
		"rows": frappe.get_all(
			"Contract Signing",
			filters=filters,
			fields=[
				"name",
				"employee",
				"employee_name",
				"sign_template",
				"status",
				"vendor_status",
				"flow_id",
				"document_id",
				"trans_reference",
				"requested_on",
				"started_on",
				"completed_on",
				"cancelled_on",
				"error_status",
				"modified",
			],
			order_by="modified desc",
			start=start,
			page_length=page_length,
		),
		"total": frappe.db.count("Contract Signing", filters),
	}


@frappe.whitelist(methods=["GET"])
def get_contract_signing(name: str) -> dict[str, Any]:
	return _signing(name).as_dict()


@frappe.whitelist(methods=["POST"])
def get_sign_url(
	name: str, jump_url: str | None = None, expired_on: int = 1800
) -> dict[str, Any]:
	doc = _signing(name)

	def action() -> Any:
		template = frappe.get_doc("Contract Sign Template", doc.sign_template)
		employee = frappe.get_doc("Employee", doc.employee)
		payload = service.build_template_payload(template, employee, doc.trans_reference)
		result = TencentESignClient().create_sign_url(
			doc.flow_id,
			payload["approvers"],
			jump_url=jump_url or "",
			expired_on=max(1800, min(cint(expired_on), 7776000)),
		)
		urls = result.get("FlowApproverUrlInfos") or []
		url = (urls[0].get("SignUrl") or urls[0].get("LongUrl")) if urls else ""
		return {"sign_url": url, "request_id": result.get("RequestId")}

	return _safe_external_call(action, signing=doc)


@frappe.whitelist(methods=["POST"])
def urge_contract(name: str) -> dict[str, Any]:
	doc = _signing(name, "write")
	return _safe_external_call(
		lambda: TencentESignClient().remind_flow(doc.flow_id), signing=doc
	)


@frappe.whitelist(methods=["POST"])
def cancel_contract(name: str, reason: str = "业务方撤销合同") -> dict[str, Any]:
	doc = _signing(name, "write")

	def action() -> Any:
		result = TencentESignClient().cancel_flow(doc.flow_id, reason)
		doc.status = "Cancelled"
		doc.vendor_status = "CANCELED"
		doc.cancelled_on = now_datetime()
		doc.error_status = ""
		doc.save()
		return result

	return _safe_external_call(action, signing=doc)


@frappe.whitelist(methods=["POST"])
def download_signed_contract(name: str) -> dict[str, Any]:
	doc = _signing(name)
	if doc.status != "Completed":
		raise frappe.ValidationError(_("合同尚未签署完成"))
	if doc.signed_file:
		return {"ok": True, "data": {"download_url": doc.signed_file, "archived": True}}

	def action() -> dict[str, Any]:
		result = TencentESignClient().describe_file_urls(doc.flow_id)
		files = result.get("FileUrls") or []
		return {
			"download_url": files[0].get("Url") if files else "",
			"request_id": result.get("RequestId"),
		}

	return _safe_external_call(action, signing=doc)


@frappe.whitelist(methods=["POST"])
def sync_contract_status(name: str) -> dict[str, Any]:
	doc = _signing(name, "write")
	result = _safe_external_call(lambda: service.sync_contract_status(doc), signing=doc)
	if result.get("ok") and hasattr(result["data"], "as_dict"):
		result["data"] = result["data"].as_dict()
	return result


@frappe.whitelist(allow_guest=True, methods=["POST"])
def handle_tencent_callback() -> dict[str, bool]:
	return callback_handler.handle_callback()
