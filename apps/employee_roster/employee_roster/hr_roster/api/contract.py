"""供应商中立的电子签合同后端 API (默认法大大)。"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from employee_roster.integrations.fadada import callback as fadada_callback
from employee_roster.integrations.fadada import service as fadada_service
from employee_roster.integrations.fadada.client import ConfigurationError as FadadaConfigurationError
from employee_roster.integrations.fadada.client import (
	FadadaAPIError,
	FadadaClient,
	FadadaConfig,
	configuration_status,
)
from employee_roster.integrations.tencent_esign import service as tencent_service
from employee_roster.integrations.tencent_esign.client import (
	ConfigurationError as TencentConfigurationError,
)
from employee_roster.integrations.tencent_esign.client import TencentESignClient

ALLOWED_ROLES = {"HR Manager", "System Manager"}
LIST_STATUS_MAP = {
	"pending": ["Pending", "Signing"],
	"signed": "Completed",
	"void": ["Cancelled", "Rejected", "Expired", "Error"],
}
CONFIGURATION_ERRORS = (FadadaConfigurationError, TencentConfigurationError)
SIGNING_DTO_FIELDS = (
	"name",
	"employee",
	"employee_name",
	"sign_template",
	"provider",
	"status",
	"vendor_status",
	"stage",
	"sign_task_id",
	"provider_file_id",
	"provider_actor_id",
	"company_actor_id",
	"actor_status",
	"employee_sign_status",
	"company_fill_status",
	"company_sign_status",
	"flow_id",
	"document_id",
	"trans_reference",
	"requested_on",
	"started_on",
	"completed_on",
	"cancelled_on",
	"last_synced_on",
	"archive_status",
	"archived_on",
	"retry_count",
	"last_retry_on",
	"archive_retry_count",
	"signed_file",
	"error_status",
	"modified",
)


def _provider(doc: Any) -> str:
	return str(getattr(doc, "provider", "") or "Fadada")


def _service_for_provider(provider: str) -> Any:
	return tencent_service if provider == "Tencent" else fadada_service


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
	except CONFIGURATION_ERRORS as exc:
		return {"ok": False, "configured": False, "error": str(exc)}
	except Exception as exc:
		if signing is not None:
			_service_for_provider(_provider(signing)).mark_operation_error(signing, exc)
		else:
			frappe.log_error(
				title="电子签调用失败",
				message=f"{type(exc).__name__}: {exc}\n{frappe.get_traceback()}",
			)
		if isinstance(exc, (frappe.ValidationError, FadadaAPIError)):
			frappe.throw(str(exc))
		frappe.throw(_("电子签调用失败, 请查看错误日志或签署记录"))


def _dto(doc: Any) -> dict[str, Any]:
	data = {field: doc.get(field) for field in SIGNING_DTO_FIELDS}
	if data.get("error_status"):
		data["error_status"] = "电子签处理失败; 请重试或由管理员查看服务端错误日志"
	return data


def _require_status(doc: Any, allowed: set[str], action: str) -> None:
	if doc.status not in allowed:
		raise frappe.ValidationError(
			_("{0}状态不允许{1}").format(doc.status, action)
		)


@frappe.whitelist(methods=["GET"])
def get_templates() -> dict[str, Any]:
	_require_doctype_permission("Contract Sign Template", "read")
	return {
		"configuration": configuration_status(),
		"templates": frappe.get_all(
			"Contract Sign Template",
			filters={"enabled": 1},
			fields=[
				"name",
				"template_name",
				"provider",
				"provider_template_id",
				"source_type",
				"description",
				"seal_id",
				"business_id",
				"employee_actor_id",
				"corp_actor_id",
				"modified",
			],
			order_by="template_name asc",
		),
	}


@frappe.whitelist(methods=["POST"])
def preview_contract(
	template: str,
	employee: str,
	contract_fields: dict[str, Any] | str | None = None,
	trans_reference: str | None = None,
) -> dict[str, Any]:
	_require_doctype_permission("Contract Signing", "create")
	template_doc = frappe.get_doc("Contract Sign Template", template)
	integration = _service_for_provider(_provider(template_doc))
	fields = integration.parse_json_config(contract_fields, dict)
	if _provider(template_doc) == "Fadada":
		return _safe_external_call(
			lambda: integration.preview_contract(
				template, employee, fields, trans_reference
			)
		)
	return _safe_external_call(lambda: integration.preview_contract(template, employee, fields))


@frappe.whitelist(methods=["POST"])
def get_contract_editor_preview(
	template: str,
	employee: str,
	contract_fields: dict[str, Any] | str | None = None,
	force_refresh: int | str = 0,
) -> dict[str, Any]:
	_require_doctype_permission("Contract Signing", "create")
	template_doc = frappe.get_doc("Contract Sign Template", template)
	if _provider(template_doc) != "Fadada":
		raise frappe.ValidationError(_("动态合同底稿目前仅支持法大大模板"))
	fields = fadada_service.parse_json_config(contract_fields, dict)
	return _safe_external_call(
		lambda: fadada_service.get_editor_preview(
			template,
			employee,
			fields,
			force_refresh=bool(cint(force_refresh)),
		)
	)


@frappe.whitelist(methods=["POST"])
def create_contract_signing(
	template: str,
	employee: str,
	trans_reference: str | None = None,
	contract_fields: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_doctype_permission("Contract Signing", "create")
	template_doc = frappe.get_doc("Contract Sign Template", template)
	integration = _service_for_provider(_provider(template_doc))
	fields = integration.parse_json_config(contract_fields, dict)
	try:
		doc = integration.create_contract_signing(template, employee, trans_reference, fields)
	except CONFIGURATION_ERRORS as exc:
		return {"ok": False, "configured": False, "error": str(exc)}
	except Exception:
		frappe.throw(_("电子签合同发起失败, 请查看签署记录中的错误状态"))
	if doc.status == "Error":
		return {"ok": False, "error": doc.error_status, "signing": _dto(doc)}
	return {"ok": True, "signing": _dto(doc)}


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
	rows = frappe.get_all(
		"Contract Signing",
		filters=filters,
		fields=list(SIGNING_DTO_FIELDS),
		order_by="modified desc",
		start=start,
		page_length=page_length,
	)
	return {
		"rows": [_dto(row) for row in rows],
		"total": frappe.db.count("Contract Signing", filters),
	}


@frappe.whitelist(methods=["GET"])
def get_contract_signing(name: str) -> dict[str, Any]:
	return _dto(_signing(name))


@frappe.whitelist(methods=["POST"])
def get_sign_url(
	name: str,
	jump_url: str | None = None,
	expired_on: int = 1800,
	actor_type: str = "employee",
) -> dict[str, Any]:
	doc = _signing(name)
	_require_status(doc, {"Pending", "Signing"}, "获取签署链接")
	if actor_type not in {"employee", "company"}:
		raise frappe.ValidationError(_("签署参与方类型无效"))
	if actor_type == "company" and _provider(doc) != "Fadada":
		raise frappe.ValidationError(_("当前供应商不支持企业盖章链接"))

	def action() -> Any:
		if _provider(doc) == "Fadada":
			payload: dict[str, Any] = {"signTaskId": doc.sign_task_id}
			if actor_type == "company":
				if doc.stage not in {"Preparing", "CompanySigning"}:
					raise frappe.ValidationError(_("尚未进入企业确认或盖章节点"))
				template = frappe.get_doc("Contract Sign Template", doc.sign_template)
				actor_id = doc.company_actor_id or template.corp_actor_id
			else:
				actor_id = doc.provider_actor_id
			if actor_id:
				payload["actorId"] = actor_id
			if jump_url:
				payload["redirectUrl"] = jump_url
			result = FadadaClient().get_actor_url(payload)
			return {
				"sign_url": fadada_service._first_value(
					result,
					"actorSignTaskUrl",
					"actorSignTaskEmbedUrl",
					"url",
					"actorUrl",
					"signUrl",
				)
			}
		template = frappe.get_doc("Contract Sign Template", doc.sign_template)
		employee = frappe.get_doc("Employee", doc.employee)
		payload = tencent_service.build_template_payload(
			template, employee, doc.trans_reference
		)
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
	_require_status(doc, {"Pending", "Signing"}, "催办")
	if _provider(doc) == "Fadada":
		return _safe_external_call(
			lambda: FadadaClient().urge(doc.sign_task_id), signing=doc
		)
	return _safe_external_call(
		lambda: TencentESignClient().remind_flow(doc.flow_id), signing=doc
	)


@frappe.whitelist(methods=["POST"])
def cancel_contract(name: str, reason: str = "业务方撤销合同") -> dict[str, Any]:
	doc = _signing(name, "write")
	_require_status(doc, {"Draft", "Pending", "Signing"}, "撤销")

	def action() -> Any:
		if _provider(doc) == "Fadada":
			result = FadadaClient().cancel(doc.sign_task_id, reason)
		else:
			result = TencentESignClient().cancel_flow(doc.flow_id, reason)
		doc.status = "Cancelled"
		doc.vendor_status = (
			"task_cancelled" if _provider(doc) == "Fadada" else "CANCELED"
		)
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
		if _provider(doc) == "Fadada":
			result = FadadaClient().get_download_url(
				fadada_service.download_payload(doc)
			)
			return {
				"download_url": fadada_service._first_value(
					result, "downloadUrl", "url"
				)
			}
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
	integration = _service_for_provider(_provider(doc))
	result = _safe_external_call(
		lambda: integration.sync_contract_status(doc), signing=doc
	)
	if result.get("ok") and hasattr(result["data"], "as_dict"):
		result["data"] = _dto(result["data"])
	return result


@frappe.whitelist(methods=["POST"])
def retry_contract(name: str) -> dict[str, Any]:
	doc = _signing(name, "write")
	_require_status(doc, {"Draft", "Pending", "Completed", "Error"}, "重试")
	integration = _service_for_provider(_provider(doc))
	if doc.archive_status == "Failed" and doc.status == "Completed":
		result = _safe_external_call(
			lambda: integration.archive_signed_contract(doc.name), signing=doc
		)
	else:
		doc.retry_count = int(doc.retry_count or 0) + 1
		doc.last_retry_on = now_datetime()
		doc.save(ignore_permissions=True)
	if doc.archive_status != "Failed" and _provider(doc) == "Fadada" and doc.sign_task_id:
		result = _safe_external_call(
			lambda: integration.sync_contract_status(doc), signing=doc
		)
	elif doc.archive_status != "Failed":
		result = _safe_external_call(
			lambda: integration.create_contract_signing(
				doc.sign_template,
				doc.employee,
				doc.trans_reference,
				integration.parse_json_config(doc.contract_fields, dict),
			),
			signing=doc,
		)
	if result.get("ok") and hasattr(result.get("data"), "as_dict"):
		result["data"] = _dto(result["data"])
	return result


@frappe.whitelist(methods=["GET"])
def get_fadada_seals() -> dict[str, Any]:
	_require_doctype_permission("Contract Sign Template", "read")
	config = FadadaConfig.load()
	return _safe_external_call(
		lambda: FadadaClient(config).list_seals(
			{"openCorpId": config.corp_open_id}
		)
	)


@frappe.whitelist(methods=["GET"])
def get_fadada_seal_status(seal_id: str) -> dict[str, Any]:
	_require_doctype_permission("Contract Sign Template", "read")
	return _safe_external_call(lambda: FadadaClient().get_seal_detail(seal_id))


@frappe.whitelist(methods=["POST"])
def get_fadada_seal_authorization_url(
	seal_id: str,
	business_id: str,
	redirect_url: str | None = None,
) -> dict[str, Any]:
	_require_doctype_permission("Contract Sign Template", "write")
	config = FadadaConfig.load()
	try:
		numeric_seal_id = int(seal_id)
	except ValueError as exc:
		raise frappe.ValidationError(_("法大大印章 ID 必须为数字")) from exc
	if not business_id.strip():
		raise frappe.ValidationError(_("业务场景 ID 不能为空"))
	payload: dict[str, Any] = {
		"openCorpId": config.corp_open_id,
		"sealIds": [numeric_seal_id],
		"businessId": business_id,
	}
	if redirect_url:
		payload["redirectUrl"] = redirect_url
	return _safe_external_call(lambda: FadadaClient(config).get_seal_free_sign_url(payload))


@frappe.whitelist(methods=["POST"])
def get_fadada_template_edit_url(template: str) -> dict[str, Any]:
	_require_doctype_permission("Contract Sign Template", "write")
	doc = frappe.get_doc("Contract Sign Template", template)
	if _provider(doc) != "Fadada":
		raise frappe.ValidationError(_("该模板不是法大大模板"))
	template_id = doc.provider_template_id or doc.template_id
	return _safe_external_call(
		lambda: FadadaClient().get_template_edit_url(template_id)
	)


@frappe.whitelist(methods=["POST"])
def configure_fadada_template(
	template: str,
	seal_id: str,
	business_id: str = "",
) -> dict[str, Any]:
	_require_doctype_permission("Contract Sign Template", "write")
	doc = frappe.get_doc("Contract Sign Template", template)
	if _provider(doc) != "Fadada":
		raise frappe.ValidationError(_("该模板不是法大大模板"))
	try:
		numeric_seal_id = int(seal_id)
	except ValueError as exc:
		raise frappe.ValidationError(_("法大大印章 ID 必须为数字")) from exc
	business_id = business_id.strip()
	if len(business_id) > 32:
		raise frappe.ValidationError(_("业务场景 ID 不能超过 32 个字符"))
	config = FadadaConfig.load()
	client = FadadaClient(config)
	detail = client.get_template_detail(
		{
			"ownerId": {"idType": "corp", "openId": config.corp_open_id},
			"signTemplateId": doc.provider_template_id or doc.template_id,
		}
	)
	template_actors = detail.get("actors") or []
	actor_config = fadada_service.parse_json_config(doc.actor_config, dict)
	actors = actor_config.get("actors") or []
	by_id = {
		str((item.get("actor") or {}).get("actorId") or ""): item
		for item in actors
		if isinstance(item, dict)
	}
	employee_id = str(doc.employee_actor_id or actor_config.get("employee_actor_id") or "")
	corp_id = str(doc.corp_actor_id or actor_config.get("corp_actor_id") or "")
	for item in template_actors:
		info = item.get("actorInfo") or item.get("actor") or {}
		actor_id = str(info.get("actorId") or "")
		actor_type = str(info.get("actorType") or "")
		if actor_type == "person" and not employee_id:
			employee_id = actor_id
		if actor_type == "corp" and not corp_id:
			corp_id = actor_id
	if not employee_id or not corp_id or employee_id == corp_id:
		raise frappe.ValidationError(_("无法从签署模板识别员工和企业参与方"))
	if employee_id not in by_id or corp_id not in by_id:
		raise frappe.ValidationError(_("本地参与方配置与法大大模板不一致"))
	by_id[employee_id].setdefault("signConfigInfo", {})["orderNo"] = 1
	corp_entry = by_id[corp_id]
	corp_entry.setdefault("signConfigInfo", {}).update(
		{"orderNo": 2, "requestVerifyFree": True}
	)
	template_corp = next(
		(
			item
			for item in template_actors
			if str(
				(item.get("actorInfo") or item.get("actor") or {}).get("actorId") or ""
			)
			== corp_id
		),
		{},
	)
	sign_fields = template_corp.get("signFields") or corp_entry.get("signFields") or []
	if not sign_fields:
		raise frappe.ValidationError(_("法大大模板中的企业参与方没有签章控件"))
	corp_entry["signFields"] = [
		{**field, "sealId": numeric_seal_id}
		for field in sign_fields
		if isinstance(field, dict)
	]
	actor_config.update(
		{
			"employee_actor_id": employee_id,
			"corp_actor_id": corp_id,
			"actors": actors,
		}
	)
	doc.seal_id = str(numeric_seal_id)
	doc.business_id = business_id
	doc.employee_actor_id = employee_id
	doc.corp_actor_id = corp_id
	doc.actor_config = frappe.as_json(actor_config)
	doc.save()
	return {
		"ok": True,
		"template": {
			"name": doc.name,
			"seal_id": doc.seal_id,
			"business_id": doc.business_id,
			"employee_actor_id": doc.employee_actor_id,
			"corp_actor_id": doc.corp_actor_id,
		},
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def handle_tencent_callback() -> dict[str, bool]:
	from employee_roster.integrations.tencent_esign import callback

	return callback.handle_callback()


@frappe.whitelist(allow_guest=True, methods=["POST"])
def handle_fadada_callback() -> dict[str, str]:
	return fadada_callback.handle_callback()
