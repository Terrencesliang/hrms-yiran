"""法大大“基于签署任务模板”合同业务适配层。"""
from __future__ import annotations

import json
import uuid
from typing import Any
from urllib.parse import urlparse

import frappe
import requests
from frappe.utils import add_days, add_to_date, get_datetime, now_datetime
from frappe.utils.file_manager import save_file

from .client import FadadaClient, FadadaConfig
from .pdf_preview import (
	FADADA_PAGE_HEIGHT,
	FADADA_PAGE_WIDTH,
	render_filled_preview,
)

STATUS_MAP = {
	"task_created": "Draft",
	"fill_progress": "Pending",
	"fill_completed": "Pending",
	"sign_progress": "Signing",
	"sign_completed": "Pending",
	"task_finished": "Completed",
	"task_terminated": "Cancelled",
	"task_cancelled": "Cancelled",
	"task_canceled": "Cancelled",
	"task_rejected": "Rejected",
	"task_expired": "Expired",
}
PHASE_MAP = {
	"task_created": "Preparing",
	"fill_progress": "Preparing",
	"fill_completed": "Ready",
	"sign_progress": "Signing",
	"sign_completed": "Finishing",
	"task_finished": "Finished",
	"task_terminated": "Terminated",
	"task_cancelled": "Terminated",
	"task_canceled": "Terminated",
	"task_rejected": "Terminated",
	"task_expired": "Terminated",
}
TERMINAL_STATUSES = {"Completed", "Cancelled", "Rejected", "Expired"}


def map_vendor_status(status: str | None, termination_type: str | None = None) -> str:
	status_key = str(status or "").lower()
	if status_key != "task_terminated":
		return STATUS_MAP.get(status_key, "Pending")
	reason = str(termination_type or "").lower()
	if "reject" in reason:
		return "Rejected"
	if "expire" in reason or "timeout" in reason:
		return "Expired"
	return "Cancelled"


def map_vendor_phase(status: str | None) -> str:
	return PHASE_MAP.get(str(status or "").lower(), "Unknown")


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
	message = str(exc).replace("\r", " ").replace("\n", " ")
	return f"{type(exc).__name__}: {message[:1000]}"


def _mapped_value(employee: Any, contract_fields: dict[str, Any], reference: Any) -> Any:
	if not isinstance(reference, str):
		return reference
	if reference.startswith("$contract."):
		return contract_fields.get(reference.removeprefix("$contract."), "")
	if reference.startswith("$employee."):
		fieldname = reference.removeprefix("$employee.")
		if fieldname != "name" and not employee.meta.has_field(fieldname):
			raise frappe.ValidationError(f"员工字段不存在: {fieldname}")
		return getattr(employee, fieldname, "")
	return reference


def _resolve(value: Any, employee: Any, contract_fields: dict[str, Any]) -> Any:
	if isinstance(value, dict):
		return {key: _resolve(item, employee, contract_fields) for key, item in value.items()}
	if isinstance(value, list):
		return [_resolve(item, employee, contract_fields) for item in value]
	return _mapped_value(employee, contract_fields, value)


def _normalise_actor(
	config: dict[str, Any], employee: Any, contract_fields: dict[str, Any]
) -> dict[str, Any]:
	resolved = _resolve(config, employee, contract_fields)
	if "actor" in resolved:
		actor_entry = resolved
		actor = actor_entry["actor"]
	else:
		actor = {
			"actorId": resolved.get("actor_id") or resolved.get("actorId"),
			"actorType": resolved.get("actor_type") or resolved.get("actorType") or "person",
			"actorName": resolved.get("name") or resolved.get("actorName"),
			"permissions": resolved.get("permissions") or ["fill", "sign"],
			"notification": {
				"notifyWay": resolved.get("notify_way") or "mobile",
				"sendNotification": bool(resolved.get("send_notification", True)),
				"notifyAddress": resolved.get("mobile") or resolved.get("notifyAddress"),
			},
		}
		if resolved.get("actor_open_id"):
			actor["actorOpenId"] = resolved["actor_open_id"]
		actor_entry = {"actor": actor}
		if resolved.get("sign_config"):
			actor_entry["signConfigInfo"] = resolved["sign_config"]
		if resolved.get("sign_fields"):
			actor_entry["signFields"] = resolved["sign_fields"]
	if not actor.get("actorId"):
		raise frappe.ValidationError("参与方配置缺少模板 actorId")
	if not actor.get("actorName"):
		raise frappe.ValidationError(f"参与方 {actor['actorId']} 缺少真实姓名")
	notification = actor.get("notification") or {}
	if actor.get("actorType") == "person" and not (
		actor.get("actorOpenId") or notification.get("notifyAddress")
	):
		raise frappe.ValidationError(f"参与方 {actor['actorId']} 缺少手机号或 openId")
	return actor_entry


def _normalise_field(
	selector: str, config: Any, employee: Any, contract_fields: dict[str, Any]
) -> tuple[str, dict[str, Any], bool]:
	if isinstance(config, dict):
		source = config.get("source")
		field = {
			key: value
			for key, value in {
				"fieldDocId": config.get("doc_id") or config.get("fieldDocId"),
				"fieldId": config.get("field_id") or config.get("fieldId"),
				"fieldKey": config.get("field_key") or config.get("fieldKey"),
				"fieldName": config.get("field_name") or config.get("fieldName"),
			}.items()
			if value
		}
		if not any(key in field for key in ("fieldId", "fieldKey", "fieldName")):
			field["fieldId"] = selector
		actor_id = str(config.get("actor_id") or config.get("actorId") or "")
		required = bool(config.get("required", False))
	else:
		source = config
		field = {"fieldId": selector}
		actor_id = ""
		required = False
	value = _mapped_value(employee, contract_fields, source)
	if required and value in (None, "", []):
		raise frappe.ValidationError(f"必填模板控件 {selector} 未取得值")
	field["fieldValue"] = "" if value is None else str(value)
	return actor_id, field, required


def build_template_payload(
	template: Any,
	employee: Any,
	trans_reference: str,
	contract_fields: dict[str, Any] | None = None,
	*,
	enable_company_free_sign: bool = False,
) -> dict[str, Any]:
	contract_fields = contract_fields or {}
	field_mapping = parse_json_config(template.field_mapping, dict)
	actor_config = parse_json_config(template.actor_config, dict)
	sign_config = parse_json_config(template.sign_config, dict)
	actors_config = actor_config.get("actors") or []
	if not actors_config:
		actors_config = [
			{
				"actor_id": actor_config.get("employee_actor_id"),
				"actor_type": "person",
				"name": "$employee.employee_name",
				"mobile": "$employee.cell_number",
			}
		]
	actors = [
		_normalise_actor(item, employee, contract_fields)
		for item in actors_config
		if isinstance(item, dict)
	]
	employee_actor_id = str(
		getattr(template, "employee_actor_id", "")
		or actor_config.get("employee_actor_id")
		or ""
	)
	corp_actor_id = str(
		getattr(template, "corp_actor_id", "")
		or actor_config.get("corp_actor_id")
		or ""
	)
	if employee_actor_id and corp_actor_id:
		order = [str(item.get("actor", {}).get("actorId") or "") for item in actors]
		if employee_actor_id not in order or corp_actor_id not in order:
			raise frappe.ValidationError("员工或企业 actorId 未出现在参与方配置")
		employee_actor = actors[order.index(employee_actor_id)]
		corp_actor = actors[order.index(corp_actor_id)]
		employee_order = (employee_actor.get("signConfigInfo") or {}).get("orderNo")
		corp_order = (corp_actor.get("signConfigInfo") or {}).get("orderNo")
		if employee_order is None or corp_order is None:
			raise frappe.ValidationError("员工和企业参与方必须显式配置签署顺序 orderNo")
		if int(employee_order) >= int(corp_order):
			raise frappe.ValidationError("签署顺序必须为员工先签、企业后签")
		corp_actor.setdefault("signConfigInfo", {})[
			"requestVerifyFree"
		] = enable_company_free_sign
	if seal_id := str(getattr(template, "seal_id", "") or "").strip():
		if not corp_actor_id:
			raise frappe.ValidationError("配置印章时必须显式配置企业 actorId")
		corp_actor = next(
			(item for item in actors if str(item["actor"].get("actorId")) == corp_actor_id),
			None,
		)
		if not corp_actor:
			raise frappe.ValidationError("企业 actorId 与参与方配置不一致")
		sign_fields = corp_actor.get("signFields") or []
		if not sign_fields:
			raise frappe.ValidationError("企业参与方必须配置至少一个签章控件")
		try:
			numeric_seal_id = int(seal_id)
		except ValueError as exc:
			raise frappe.ValidationError("法大大印章 ID 必须为数字") from exc
		for sign_field in sign_fields:
			if isinstance(sign_field, dict):
				sign_field["sealId"] = numeric_seal_id
	by_actor = {str(item["actor"]["actorId"]): item for item in actors}
	default_actor_id = str(
		employee_actor_id
		or (actors[0]["actor"]["actorId"] if actors else "")
	)
	for selector, mapping in field_mapping.items():
		actor_id, field, _required = _normalise_field(
			str(selector), mapping, employee, contract_fields
		)
		target = by_actor.get(actor_id or default_actor_id)
		if not target:
			raise frappe.ValidationError(f"模板控件 {selector} 引用了未知 actorId")
		target.setdefault("fillFields", []).append(field)
		permissions = target["actor"].setdefault("permissions", [])
		if "fill" not in permissions:
			permissions.append("fill")
	config = FadadaConfig.load()
	expires_time = str(
		int(
			get_datetime(
				add_days(now_datetime(), int(sign_config.get("valid_days", 30)))
			).timestamp()
			* 1000
		)
	)
	payload = {
		"initiator": {"idType": "corp", "openId": config.corp_open_id},
		"signTaskSubject": str(
			sign_config.get("subject")
			or f"{template.template_name}-{employee.employee_name}-{trans_reference[-8:]}"
		)[:200],
		"signTemplateId": template.provider_template_id or template.template_id,
		"expiresTime": expires_time,
		"autoStart": False,
		"autoFillFinalize": bool(sign_config.get("auto_fill_finalize", True)),
		"autoFinish": bool(sign_config.get("auto_finish", True)),
		"signInOrder": True,
		"transReferenceId": trans_reference,
		"actors": actors,
	}
	if enable_company_free_sign and (business_id := str(
		getattr(template, "business_id", "") or sign_config.get("business_id") or ""
	).strip()):
		payload["businessId"] = business_id[:32]
		payload["freeSignType"] = "business"
	return payload


def _free_sign_authorized(template: Any, client: FadadaClient) -> bool:
	seal_id = str(getattr(template, "seal_id", "") or "")
	business_id = str(getattr(template, "business_id", "") or "")
	result = client.list_seals({"openCorpId": client.config.corp_open_id})
	seals = result.get("sealInfos") or result.get("list") or []
	seal = next(
		(item for item in seals if str(item.get("sealId") or "") == seal_id),
		None,
	)
	if not seal or str(seal.get("sealStatus") or "").lower() not in {
		"enable",
		"enabled",
		"normal",
		"active",
		"1",
	}:
		return False
	infos = seal.get("freeSignInfos") or []
	if isinstance(infos, dict):
		infos = [infos]
	for info in infos:
		if not isinstance(info, dict):
			continue
		info_business_id = str(
			info.get("businessId") or info.get("businessSceneId") or ""
		)
		status = str(
			info.get("status")
			or info.get("freeSignStatus")
			or info.get("grantStatus")
			or ""
		).lower()
		if info_business_id == business_id and status in {
			"enable",
			"enabled",
			"effective",
			"active",
			"opened",
			"success",
			"1",
		}:
			return True
	return False


def assert_signing_ready(template: Any, payload: dict[str, Any]) -> None:
	required = {
		"印章 ID": getattr(template, "seal_id", ""),
		"员工 Actor ID": getattr(template, "employee_actor_id", ""),
		"企业 Actor ID": getattr(template, "corp_actor_id", ""),
	}
	if missing := [label for label, value in required.items() if not value]:
		raise frappe.ValidationError(
			f"法大大模板未完成自动盖章配置: {', '.join(missing)}"
		)
	if not payload.get("signInOrder"):
		raise frappe.ValidationError("法大大合同必须启用员工先签、企业后签")


def assert_remote_sign_order(
	detail: dict[str, Any], employee_actor_id: str, company_actor_id: str
) -> None:
	if not detail.get("signInOrder"):
		raise frappe.ValidationError(
			"法大大远端模板未启用顺序签署; 请设置乙方顺序 1、甲方顺序 2"
		)
	orders = {}
	for row in detail.get("actors") or []:
		info = row.get("actorInfo") or row.get("actor") or {}
		orders[str(info.get("actorId") or "")] = row.get("signOrderNo")
	employee_order = orders.get(employee_actor_id)
	company_order = orders.get(company_actor_id)
	if (
		employee_order is None
		or company_order is None
		or int(employee_order) >= int(company_order)
	):
		raise frappe.ValidationError(
			"法大大远端模板签署顺序不正确; 请设置乙方顺序 1、甲方顺序 2"
		)


def _template(name: str) -> Any:
	doc = frappe.get_doc("Contract Sign Template", name)
	if not doc.enabled:
		raise frappe.ValidationError("电子签模板已停用")
	if (doc.provider or "Fadada") != "Fadada":
		raise frappe.ValidationError("该模板不是法大大模板")
	if not (doc.provider_template_id or doc.template_id):
		raise frappe.ValidationError("法大大模板 ID 未配置")
	return doc


def _first_value(data: dict[str, Any], *keys: str) -> str:
	for key in keys:
		if value := data.get(key):
			return str(value)
	return ""


def _employee_actor_id(template: Any, payload: dict[str, Any]) -> str:
	actor_config = parse_json_config(template.actor_config, dict)
	if actor_id := (
		getattr(template, "employee_actor_id", "")
		or actor_config.get("employee_actor_id")
	):
		return str(actor_id)
	for item in payload.get("actors") or []:
		actor = item.get("actor") or {}
		if actor.get("actorType") == "person":
			return str(actor.get("actorId") or "")
	return ""


def _company_actor_id(template: Any, payload: dict[str, Any]) -> str:
	actor_config = parse_json_config(template.actor_config, dict)
	if actor_id := (
		getattr(template, "corp_actor_id", "") or actor_config.get("corp_actor_id")
	):
		return str(actor_id)
	for item in payload.get("actors") or []:
		actor = item.get("actor") or {}
		if actor.get("actorType") == "corp":
			return str(actor.get("actorId") or "")
	return ""


def _actor_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
	for key in ("actors", "actorList", "list"):
		if isinstance(data.get(key), list):
			return [item for item in data[key] if isinstance(item, dict)]
	return []


def _actor_snapshot(signing: Any, actors_data: dict[str, Any]) -> list[dict[str, Any]]:
	template = frappe.get_doc("Contract Sign Template", signing.sign_template)
	employee_id = str(
		getattr(template, "employee_actor_id", "") or signing.provider_actor_id or ""
	)
	company_id = str(getattr(template, "corp_actor_id", "") or "")
	snapshot = []
	for row in _actor_rows(actors_data):
		info = row.get("actorInfo") or row.get("actor") or {}
		actor_id = str(info.get("actorId") or row.get("actorId") or "")
		item = {
			"actorId": actor_id,
			"actorType": str(info.get("actorType") or row.get("actorType") or ""),
			"fillStatus": str(row.get("fillStatus") or ""),
			"signStatus": str(row.get("signStatus") or ""),
			"signTime": row.get("signTime"),
		}
		snapshot.append(item)
		if actor_id == employee_id:
			signing.employee_sign_status = item["signStatus"]
			if item["signStatus"] in {
				"signed",
				"sign_completed",
				"sign_finished",
				"completed",
			} and not signing.employee_signed_on:
				signing.employee_signed_on = now_datetime()
			elif (
				str(signing.vendor_status).lower() != "fill_progress"
				and item["signStatus"] in {"wait_sign", "signing", "sign_progress"}
			):
				signing.stage = "EmployeeSigning"
		if actor_id == company_id:
			signing.company_fill_status = item["fillStatus"]
			signing.company_sign_status = item["signStatus"]
			if item["signStatus"] in {
				"signed",
				"sign_completed",
				"sign_finished",
				"completed",
			} and not signing.company_signed_on:
				signing.company_signed_on = now_datetime()
			elif (
				signing.employee_sign_status
				in {"signed", "sign_completed", "sign_finished", "completed"}
				and item["signStatus"] in {"wait_sign", "signing", "sign_progress"}
			):
				signing.stage = "CompanySigning"
	if (
		str(signing.vendor_status).lower() == "fill_progress"
		and signing.company_fill_status in {"wait_fill", "filling"}
	):
		signing.stage = "Preparing"
	return snapshot


def apply_vendor_detail(
	signing: Any,
	detail: dict[str, Any],
	actors_data: dict[str, Any] | None = None,
) -> Any:
	vendor_status = _first_value(detail, "signTaskStatus", "taskStatus", "status")
	if not vendor_status:
		raise frappe.ValidationError("法大大未返回签署任务状态")
	signing.vendor_status = vendor_status
	signing.stage = map_vendor_phase(vendor_status)
	signing.status = map_vendor_status(
		vendor_status, _first_value(detail, "terminationType", "terminationReason")
	)
	signing.provider_file_id = (
		_first_value(detail, "fileId", "docFileId") or signing.provider_file_id
	)
	if actors_data is not None:
		signing.actor_status = frappe.as_json(_actor_snapshot(signing, actors_data))
	signing.last_synced_on = now_datetime()
	signing.next_retry_on = None
	if signing.status == "Completed" and not signing.completed_on:
		signing.completed_on = now_datetime()
	signing.error_status = ""
	signing.save(ignore_permissions=True)
	return signing


def _fill_template_values(
	client: FadadaClient, sign_task_id: str, payload: dict[str, Any]
) -> None:
	values: list[dict[str, Any]] = []
	for item in payload.get("actors") or []:
		for field in item.get("fillFields") or []:
			doc_id = field.get("fieldDocId")
			values.append(
				{
					"docId": str(doc_id or ""),
					"fieldId": field.get("fieldId"),
					"fieldValue": field.get("fieldValue", ""),
				}
			)
	if values:
		client.fill_field_values(sign_task_id, values)
	if not payload.get("autoFillFinalize", False):
		client.finalize_docs(sign_task_id)


def _editor_field(field: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
	config = next(
		(
			value
			for key, value in field.items()
			if key.startswith("field")
			and key not in {"fieldId", "fieldName", "fieldKey", "fieldType"}
			and isinstance(value, dict)
		),
		{},
	)
	return {
		"field_id": str(field.get("fieldId") or ""),
		"field_name": str(field.get("fieldName") or ""),
		"field_type": str(field.get("fieldType") or ""),
		"source": str(mapping.get("source") or ""),
		"position": field.get("position") or {},
		"width": float(config.get("width") or 160),
		"height": float(config.get("height") or 30),
		"font_size": float(config.get("fontSize") or 16),
		"alignment": str(config.get("alignment") or "left"),
	}


def get_editor_preview(
	template_name: str,
	employee_name: str,
	contract_fields: dict[str, Any] | None = None,
	*,
	force_refresh: bool = False,
) -> dict[str, Any]:
	template = _template(template_name)
	employee = frappe.get_doc("Employee", employee_name)
	payload = build_template_payload(
		template, employee, f"editor-{uuid.uuid4().hex}", contract_fields
	)
	client = FadadaClient()
	detail = client.get_template_detail(
		{
			"ownerId": {
				"idType": "corp",
				"openId": client.config.corp_open_id,
			},
			"signTemplateId": template.provider_template_id or template.template_id,
		}
	)
	base_pdf_url = str(getattr(template, "base_pdf_file", "") or "")
	if force_refresh or not base_pdf_url:
		sign_task_id = ""
		try:
			created = client.create_with_template(payload)
			sign_task_id = _first_value(created, "signTaskId")
			if not sign_task_id:
				raise frappe.ValidationError("法大大未返回模板底稿任务 ID")
			task_detail = client.get_detail(sign_task_id)
			docs = task_detail.get("docs") or []
			doc_id = str(docs[0].get("docId") or "") if docs else ""
			request = {
				"ownerId": {
					"idType": "corp",
					"openId": client.config.corp_open_id,
				},
				"signTaskId": sign_task_id,
				"fileType": "doc",
			}
			if doc_id:
				request["id"] = doc_id
			download = client.get_download_url(request)
			download_url = _first_value(download, "downloadUrl", "url")
			if not download_url:
				raise frappe.ValidationError("法大大未返回模板底稿下载地址")
			old_file_url = base_pdf_url
			file_doc = _save_private_file(
				f"{template.name}-base.pdf",
				_download_vendor_pdf(download_url),
				"Contract Sign Template",
				template.name,
				"base_pdf_file",
			)
			template.base_pdf_file = file_doc.file_url
			template.save(ignore_permissions=True)
			base_pdf_url = file_doc.file_url
			if old_file_url and old_file_url != base_pdf_url:
				if old_file := frappe.db.get_value(
					"File", {"file_url": old_file_url}, "name"
				):
					frappe.delete_doc("File", old_file, ignore_permissions=True)
		finally:
			if sign_task_id:
				try:
					client.delete(sign_task_id)
				except Exception:
					frappe.log_error(
						title="法大大模板底稿临时任务清理失败",
						message=f"{sign_task_id}\n{frappe.get_traceback()}",
					)
	mapping = parse_json_config(template.field_mapping, dict)
	fields = []
	for doc in detail.get("docs") or []:
		for field in doc.get("docFields") or []:
			field_id = str(field.get("fieldId") or "")
			if field_id in mapping:
				fields.append(_editor_field(field, mapping[field_id]))
	return {
		"base_pdf_url": base_pdf_url,
		"fields": fields,
		"page_width": FADADA_PAGE_WIDTH,
		"page_height": FADADA_PAGE_HEIGHT,
	}


def _base_pdf_content(
	template: Any, employee: Any, contract_fields: dict[str, Any]
) -> bytes:
	if not getattr(template, "base_pdf_file", ""):
		get_editor_preview(template.name, employee.name, contract_fields)
		template.reload()
	file_name = frappe.db.get_value(
		"File", {"file_url": template.base_pdf_file}, "name"
	)
	if not file_name:
		raise frappe.ValidationError("合同模板底稿文件不存在; 请刷新模板底稿")
	content = frappe.get_doc("File", file_name).get_content()
	return content if isinstance(content, bytes) else bytes(content)


def _upload_filled_pdf(client: FadadaClient, content: bytes) -> str:
	upload = client.get_file_upload_url()
	upload_url = _first_value(upload, "uploadUrl")
	fdd_file_url = _first_value(upload, "fddFileUrl")
	if not upload_url or not fdd_file_url:
		raise frappe.ValidationError("法大大未返回文件上传地址")
	host = (urlparse(upload_url).hostname or "").lower()
	if not upload_url.startswith("https://") or not (
		host == "fadada.com" or host.endswith(".fadada.com")
	):
		raise frappe.ValidationError("法大大文件上传地址不受信任")
	response = requests.put(
		upload_url,
		data=content,
		headers={"Content-Type": "application/pdf"},
		timeout=60,
	)
	response.raise_for_status()
	processed = client.process_file(
		fdd_file_url, f"contract_{uuid.uuid4().hex[:12]}.pdf"
	)
	files = processed.get("fileIdList") or []
	file_id = str(files[0].get("fileId") or "") if files else ""
	if not file_id:
		raise frappe.ValidationError("法大大未返回已填合同文件 ID")
	return file_id


def _direct_sign_payload(
	template: Any,
	employee: Any,
	contract_fields: dict[str, Any],
	payload: dict[str, Any],
	client: FadadaClient,
) -> dict[str, Any]:
	detail = client.get_template_detail(
		{
			"ownerId": {
				"idType": "corp",
				"openId": client.config.corp_open_id,
			},
			"signTemplateId": template.provider_template_id or template.template_id,
		}
	)
	filled_pdf = render_filled_preview(
		_base_pdf_content(template, employee, contract_fields),
		detail,
		payload.get("actors") or [],
	)
	file_id = _upload_filled_pdf(client, filled_pdf)
	result = json.loads(json.dumps(payload))
	result.pop("signTemplateId", None)
	sign_field_ids = {
		str(field.get("fieldId") or "")
		for actor in result.get("actors") or []
		for field in actor.get("signFields") or []
	}
	doc_fields = [
		field
		for doc in detail.get("docs") or []
		for field in doc.get("docFields") or []
		if str(field.get("fieldId") or "") in sign_field_ids
	]
	for actor in result.get("actors") or []:
		actor.pop("fillFields", None)
		permissions = actor.get("actor", {}).get("permissions") or []
		actor.get("actor", {})["permissions"] = [
			permission for permission in permissions if permission != "fill"
		]
		for field in actor.get("signFields") or []:
			field["fieldDocId"] = file_id
	result["docs"] = [
		{
			"docId": file_id,
			"docName": f"contract_{employee.name}.pdf",
			"docFileId": file_id,
			"docFields": doc_fields,
		}
	]
	for field in result["docs"][0]["docFields"]:
		field["position"] = field.get("position") or {}
	result["autoStart"] = True
	result["autoFillFinalize"] = True
	return result


def preview_contract(
	template_name: str,
	employee_name: str,
	contract_fields: dict[str, Any] | None = None,
	trans_reference: str | None = None,
) -> dict[str, Any]:
	template = _template(template_name)
	employee = frappe.get_doc("Employee", employee_name)
	reference = (trans_reference or f"preview-{uuid.uuid4().hex}").strip()
	signing = None
	sign_task_id = ""
	if trans_reference and (
		existing := frappe.db.exists("Contract Signing", {"trans_reference": reference})
	):
		signing = frappe.get_doc("Contract Signing", existing)
		if signing.employee != employee.name or signing.sign_template != template.name:
			raise frappe.ValidationError("预览幂等键已被其他员工或模板占用")
		if signing.status in {"Cancelled", "Rejected", "Expired"}:
			reference = f"{uuid.uuid4().hex}-{employee.name}"[:64]
			signing = None
		else:
			sign_task_id = signing.sign_task_id or ""

	payload = build_template_payload(template, employee, reference, contract_fields)
	client = FadadaClient()
	if sign_task_id:
		if signing.status != "Draft":
			raise frappe.ValidationError("仅草稿签署任务可以刷新预览")
		client.delete(sign_task_id)
		signing.sign_task_id = ""
		signing.provider_file_id = ""
		signing.error_status = ""
		signing.save(ignore_permissions=True)
		# 远端删除不可回滚; 先固化本地清理以免恢复陈旧任务 ID。
		frappe.db.commit()
		sign_task_id = ""
	if not sign_task_id:
		created = client.create_with_template(payload)
		sign_task_id = _first_value(created, "signTaskId")
		if not sign_task_id:
			raise frappe.ValidationError("法大大未返回 signTaskId")
		try:
			_fill_template_values(client, sign_task_id, payload)
		except Exception:
			client.delete(sign_task_id)
			raise
		if trans_reference:
			signing = (
				signing
				or frappe.get_doc(
					{
						"doctype": "Contract Signing",
						"provider": "Fadada",
						"employee": employee.name,
						"sign_template": template.name,
						"trans_reference": reference,
						"status": "Draft",
						"requested_on": now_datetime(),
						"requested_by": frappe.session.user,
						"contract_fields": frappe.as_json(contract_fields or {}),
						"is_preview": 1,
						"preview_expires_on": add_days(now_datetime(), 1),
					}
				).insert(ignore_permissions=True)
			)
			signing.sign_task_id = sign_task_id
			signing.provider_file_id = _first_value(created, "fileId", "docFileId")
			signing.provider_actor_id = _employee_actor_id(template, payload)
			signing.company_actor_id = _company_actor_id(template, payload)
			signing.vendor_status = "task_created"
			signing.status = "Draft"
			signing.is_preview = 1
			signing.preview_expires_on = add_days(now_datetime(), 1)
			signing.contract_fields = frappe.as_json(contract_fields or {})
			signing.save()

	detail = client.get_detail(sign_task_id)
	docs = detail.get("docs") or []
	doc_id = str(docs[0].get("docId") or "") if docs else ""
	if signing and doc_id:
		signing.provider_file_id = doc_id
		signing.save()
	download_request: dict[str, Any] = {
		"ownerId": {
			"idType": "corp",
			"openId": FadadaConfig.load().corp_open_id,
		},
		"signTaskId": sign_task_id,
		"fileType": "doc",
	}
	if doc_id:
		download_request["id"] = doc_id
	pdf = client.get_download_url(download_request)
	link = client.get_preview_url({"signTaskId": sign_task_id})
	external_preview_url = _first_value(
		link,
		"signTaskPreviewEmbedUrl",
		"signTaskPreviewUrl",
		"url",
		"previewUrl",
	)
	pdf_url = _first_value(pdf, "downloadUrl", "url")
	filled_preview_url = ""
	if signing and pdf_url:
		try:
			template_detail = client.get_template_detail(
				{
					"ownerId": {
						"idType": "corp",
						"openId": client.config.corp_open_id,
					},
					"signTemplateId": template.provider_template_id
					or template.template_id,
				}
			)
			filled_pdf = render_filled_preview(
				_download_vendor_pdf(pdf_url),
				template_detail,
				payload.get("actors") or [],
			)
			old_preview = signing.preview_file
			preview_file = _save_private_file(
				f"{signing.name}-preview.pdf",
				filled_pdf,
				"Contract Signing",
				signing.name,
				"preview_file",
			)
			signing.preview_file = preview_file.file_url
			signing.save(ignore_permissions=True)
			filled_preview_url = preview_file.file_url
			if old_preview and old_preview != filled_preview_url:
				if old_file := frappe.db.get_value(
					"File", {"file_url": old_preview}, "name"
				):
					frappe.delete_doc("File", old_file, ignore_permissions=True)
		except Exception:
			frappe.log_error(
				title="合同已填 PDF 预览生成失败",
				message=f"{signing.name}\n{frappe.get_traceback()}",
			)
	return {
		"preview_url": external_preview_url or filled_preview_url or pdf_url,
		"external_preview_url": external_preview_url,
		"fallback_preview_url": filled_preview_url or pdf_url,
		"preview_is_filled": bool(filled_preview_url and not external_preview_url),
		"preview_is_official": bool(external_preview_url),
		"sign_task_id": sign_task_id,
		"signing": signing.name if signing else "",
		"trans_reference": reference,
	}


def create_contract_signing(
	template_name: str,
	employee_name: str,
	trans_reference: str | None = None,
	contract_fields: dict[str, Any] | None = None,
) -> Any:
	trans_reference = (trans_reference or uuid.uuid4().hex).strip()
	signing = None
	if existing := frappe.db.exists("Contract Signing", {"trans_reference": trans_reference}):
		signing = frappe.get_doc("Contract Signing", existing)
		if signing.employee != employee_name or signing.sign_template != template_name:
			raise frappe.ValidationError("签署幂等键已被其他员工或模板占用")
		if signing.status in TERMINAL_STATUSES:
			return signing
		if signing.provider == "Fadada" and signing.sign_task_id and signing.is_preview:
			FadadaClient().delete(signing.sign_task_id)
			signing.sign_task_id = ""
			signing.provider_file_id = ""
			signing.is_preview = 0
			signing.preview_expires_on = None
			signing.status = "Draft"
			signing.save(ignore_permissions=True)
		if signing.provider == "Fadada" and signing.sign_task_id:
			try:
				client = FadadaClient()
				template = _template(signing.sign_template)
				employee = frappe.get_doc("Employee", signing.employee)
				payload = build_template_payload(
					template,
					employee,
					signing.trans_reference,
					parse_json_config(signing.contract_fields, dict),
					enable_company_free_sign=False,
				)
				assert_signing_ready(template, payload)
				apply_vendor_detail(
					signing,
					client.get_detail(signing.sign_task_id),
					client.list_actors(signing.sign_task_id),
				)
				if signing.status in {"Draft", "Pending", "Error"} and signing.stage in {
					"Preparing",
					"Ready",
					"Unknown",
				}:
					if str(signing.vendor_status or "").lower() in {
						"",
						"task_created",
						"fill_progress",
					}:
						_fill_template_values(client, signing.sign_task_id, payload)
					client.start(signing.sign_task_id)
					signing.started_on = signing.started_on or now_datetime()
					apply_vendor_detail(
						signing,
						client.get_detail(signing.sign_task_id),
						client.list_actors(signing.sign_task_id),
					)
			except Exception as exc:
				signing.status = "Error"
				signing.error_status = _safe_error(exc)
				signing.retry_count = int(signing.retry_count or 0) + 1
				signing.last_retry_on = now_datetime()
				signing.next_retry_on = add_to_date(
					now_datetime(), minutes=min(60, 2 ** min(signing.retry_count, 6))
				)
				signing.save()
			return signing
	template = _template(template_name)
	employee = frappe.get_doc("Employee", employee_name)
	contract_fields_json = frappe.as_json(contract_fields or {})
	if signing is None:
		signing = frappe.get_doc(
			{
				"doctype": "Contract Signing",
				"provider": "Fadada",
				"employee": employee.name,
				"sign_template": template.name,
				"trans_reference": trans_reference,
				"status": "Draft",
				"requested_on": now_datetime(),
				"requested_by": frappe.session.user,
				"contract_fields": contract_fields_json,
			}
		).insert(ignore_permissions=True)
	else:
		signing.contract_fields = contract_fields_json
		signing.save(ignore_permissions=True)
	try:
		payload = build_template_payload(
			template,
			employee,
			trans_reference,
			contract_fields,
			enable_company_free_sign=False,
		)
		client = FadadaClient()
		assert_signing_ready(template, payload)
		payload = _direct_sign_payload(
			template, employee, contract_fields or {}, payload, client
		)
		created = client.create(payload)
		signing.sign_task_id = _first_value(created, "signTaskId")
		if not signing.sign_task_id:
			raise frappe.ValidationError("法大大未返回 signTaskId")
		signing.provider_file_id = _first_value(created, "fileId", "docFileId")
		signing.provider_actor_id = _employee_actor_id(template, payload)
		signing.company_actor_id = _company_actor_id(template, payload)
		signing.status = "Pending"
		signing.started_on = now_datetime()
		signing.save()
		detail = client.get_detail(signing.sign_task_id)
		try:
			assert_remote_sign_order(
				detail, signing.provider_actor_id, signing.company_actor_id
			)
		except Exception:
			client.cancel(signing.sign_task_id, "远端模板签署顺序配置不正确")
			raise
		apply_vendor_detail(signing, detail, client.list_actors(signing.sign_task_id))
	except Exception as exc:
		signing.status = "Error"
		signing.error_status = _safe_error(exc)
		signing.retry_count = int(signing.retry_count or 0) + 1
		signing.last_retry_on = now_datetime()
		signing.next_retry_on = add_to_date(
			now_datetime(), minutes=min(60, 2 ** min(signing.retry_count, 6))
		)
		signing.save()
	return signing


def sync_contract_status(signing: Any) -> Any:
	client = FadadaClient()
	return apply_vendor_detail(
		signing,
		client.get_detail(signing.sign_task_id),
		client.list_actors(signing.sign_task_id),
	)


def mark_operation_error(signing: Any, exc: Exception) -> None:
	signing.error_status = _safe_error(exc)
	signing.save()
	frappe.log_error(
		title="法大大合同操作失败",
		message=f"{signing.name}\n{frappe.get_traceback()}",
	)


def download_payload(signing: Any) -> dict[str, Any]:
	config = FadadaConfig.load()
	payload: dict[str, Any] = {
		"ownerId": {"idType": "corp", "openId": config.corp_open_id},
		"signTaskId": signing.sign_task_id,
		"fileType": "doc",
	}
	if signing.provider_file_id:
		payload["id"] = signing.provider_file_id
	return payload


def _download_vendor_pdf(url: str, *, max_size: int = 25 * 1024 * 1024) -> bytes:
	parsed = urlparse(url)
	host = (parsed.hostname or "").lower()
	if parsed.scheme != "https" or not (
		host == "fadada.com" or host.endswith(".fadada.com")
	):
		raise frappe.ValidationError("法大大下载地址不是受信任的 HTTPS 域名")
	response = requests.get(url, timeout=30)
	response.raise_for_status()
	if len(response.content) > max_size:
		raise frappe.ValidationError("法大大归档文件超过允许大小")
	if not response.content.startswith(b"%PDF-"):
		raise frappe.ValidationError("法大大归档文件不是有效 PDF")
	return response.content


def _save_private_file(
	filename: str,
	content: bytes,
	attached_to_doctype: str,
	attached_to_name: str,
	attached_to_field: str,
) -> Any:
	stem, separator, extension = filename.rpartition(".")
	storage_name = (
		f"{stem}-{uuid.uuid4().hex[:8]}.{extension}"
		if separator
		else f"{filename}-{uuid.uuid4().hex[:8]}"
	)
	return save_file(
		storage_name,
		content,
		attached_to_doctype,
		attached_to_name,
		is_private=1,
		df=attached_to_field,
	)


def archive_signed_contract(signing_name: str) -> dict[str, Any]:
	signing = frappe.get_doc("Contract Signing", signing_name)
	if signing.signed_file:
		return {"file_url": signing.signed_file, "already_archived": True}
	if signing.status != "Completed" or not signing.sign_task_id:
		raise frappe.ValidationError("仅可归档已完成的电子签合同")
	signing.archive_status = "Archiving"
	signing.save(ignore_permissions=True)
	try:
		result = FadadaClient().get_download_url(download_payload(signing))
		download_url = _first_value(result, "downloadUrl", "url")
		if not download_url:
			raise frappe.ValidationError("法大大未返回已签合同下载地址")
		file_doc = _save_private_file(
			f"{signing.name}.pdf",
			_download_vendor_pdf(download_url),
			"Contract Signing",
			signing.name,
			"signed_file",
		)
		signing.signed_file = file_doc.file_url
		signing.archive_status = "Archived"
		signing.archived_on = now_datetime()
		signing.archive_error = ""
		signing.error_status = ""
		try:
			report = FadadaClient().get_evidence_report_url(signing.sign_task_id)
			report_url = _first_value(
				report, "downloadUrl", "reportDownloadUrl", "url"
			)
			if report_url:
				audit = _save_private_file(
					f"{signing.name}-evidence.pdf",
					_download_vendor_pdf(report_url, max_size=10 * 1024 * 1024),
					"Contract Signing",
					signing.name,
					"audit_file",
				)
				signing.audit_file = audit.file_url
		except Exception:
			frappe.log_error(
				title="法大大证据报告归档失败",
				message=f"{signing.name}\n{frappe.get_traceback()}",
			)
		signing.save(ignore_permissions=True)
		return {"file_url": file_doc.file_url}
	except Exception as exc:
		signing.archive_status = "Failed"
		signing.archive_retry_count = int(signing.archive_retry_count or 0) + 1
		signing.archive_error = _safe_error(exc)
		signing.next_retry_on = add_to_date(
			now_datetime(), minutes=min(60, 2 ** min(signing.archive_retry_count, 6))
		)
		signing.save(ignore_permissions=True)
		raise
