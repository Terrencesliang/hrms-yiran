"""法大大 X-FASC-* 回调验签与幂等处理。"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs

import frappe
from frappe.utils import get_datetime, now_datetime

from .client import FadadaClient, FadadaConfig, calculate_signature
from .service import apply_vendor_detail

CALLBACK_WINDOW_SECONDS = 300
ALLOWED_EVENTS = {
	"sign-task-created",
	"sign-task-started",
	"sign-task-signed",
	"sign-task-finished",
	"sign-task-terminated",
	"sign-task-status-changed",
	"sign-task-actor-signed",
}


class CallbackVerificationError(frappe.PermissionError):
	pass


def _headers(headers: dict[str, str]) -> dict[str, str]:
	return {str(key).lower(): str(value) for key, value in headers.items()}


def extract_raw_biz_content(headers: dict[str, str], raw_body: bytes) -> str:
	"""提取用于签名的 bizContent 字符串, 绝不重序列化其中 JSON。"""
	normalized = _headers(headers)
	if value := normalized.get("bizcontent"):
		return value
	try:
		text = raw_body.decode("utf-8")
	except UnicodeDecodeError as exc:
		raise CallbackVerificationError("法大大回调不是 UTF-8") from exc
	if text.startswith(("bizContent=", "bizcontent=")):
		values = parse_qs(text, keep_blank_values=True).get("bizContent") or parse_qs(
			text, keep_blank_values=True
		).get("bizcontent")
		return values[0] if values else ""
	# 部分网关将 bizContent 原样作为 application/json 请求体转发。
	return text


def verify_callback(
	headers: dict[str, str], raw_body: bytes, config: FadadaConfig | None = None
) -> tuple[str, dict[str, Any]]:
	config = config or FadadaConfig.load()
	normalized = _headers(headers)
	required = {
		"X-FASC-App-Id": normalized.get("x-fasc-app-id", ""),
		"X-FASC-Sign-Type": normalized.get("x-fasc-sign-type", ""),
		"X-FASC-Timestamp": normalized.get("x-fasc-timestamp", ""),
		"X-FASC-Nonce": normalized.get("x-fasc-nonce", ""),
		"X-FASC-Event": normalized.get("x-fasc-event", ""),
	}
	if not all(required.values()):
		raise CallbackVerificationError("法大大回调缺少必需 X-FASC-* 请求头")
	if required["X-FASC-App-Id"] != config.app_id:
		raise CallbackVerificationError("法大大回调 App ID 不匹配")
	if required["X-FASC-Sign-Type"] != "HMAC-SHA256":
		raise CallbackVerificationError("法大大回调签名算法不受支持")
	try:
		timestamp_ms = int(required["X-FASC-Timestamp"])
	except ValueError as exc:
		raise CallbackVerificationError("法大大回调时间戳无效") from exc
	if abs(time.time() - timestamp_ms / 1000) > CALLBACK_WINDOW_SECONDS:
		raise CallbackVerificationError("法大大回调时间戳超出允许窗口")
	if required["X-FASC-Event"] not in ALLOWED_EVENTS:
		raise CallbackVerificationError("法大大回调事件类型不受支持")
	biz_content = extract_raw_biz_content(headers, raw_body)
	parameters = dict(required)
	parameters["bizContent"] = biz_content
	expected = calculate_signature(
		parameters, required["X-FASC-Timestamp"], config.app_secret
	)
	signature = normalized.get("x-fasc-sign", "")
	if not signature or not hmac.compare_digest(signature, expected):
		raise CallbackVerificationError("法大大回调签名验证失败")
	nonce_key = (
		f"employee_roster:fadada:callback_nonce:{config.app_id}:"
		f"{required['X-FASC-Nonce']}"
	)
	nonce_value = hashlib.sha256(
		f"{required['X-FASC-Event']}|{biz_content}|{signature}".encode()
	).hexdigest()
	if previous := frappe.cache.get_value(nonce_key):
		if isinstance(previous, bytes):
			previous = previous.decode()
		if str(previous) != nonce_value:
			raise CallbackVerificationError("法大大回调 nonce 已被其他请求使用")
	else:
		frappe.cache.set_value(
			nonce_key, nonce_value, expires_in_sec=CALLBACK_WINDOW_SECONDS
		)
	try:
		payload = json.loads(biz_content)
	except (TypeError, ValueError) as exc:
		raise CallbackVerificationError("法大大回调 bizContent 不是有效 JSON") from exc
	if not isinstance(payload, dict):
		raise CallbackVerificationError("法大大回调 bizContent 结构无效")
	return required["X-FASC-Event"], payload


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
	sensitive = ("mobile", "phone", "cert", "idcard", "bank", "account", "address")

	def redact(value: Any) -> Any:
		if isinstance(value, dict):
			return {
				key: ("***" if any(part in key.lower() for part in sensitive) else redact(item))
				for key, item in value.items()
			}
		if isinstance(value, list):
			return [redact(item) for item in value]
		return value

	return redact(payload)


def _event_key(event_type: str, payload: dict[str, Any]) -> str:
	if event_id := payload.get("eventId") or payload.get("eventSerialNo"):
		return f"fadada:{event_id}"
	stable = "|".join(
		str(payload.get(key) or "")
		for key in ("signTaskId", "eventTime", "signTaskStatus", "actorId")
	)
	return "fadada:" + hashlib.sha256(f"{event_type}|{stable}".encode()).hexdigest()


def _event_datetime(value: Any) -> datetime | None:
	if value in (None, ""):
		return None
	try:
		if str(value).isdigit():
			number = int(value)
			if number > 10_000_000_000:
				number /= 1000
			return datetime.fromtimestamp(number, tz=UTC).replace(tzinfo=None)
		return get_datetime(value)
	except (TypeError, ValueError, OverflowError):
		return None


def _apply_event(event_doc: Any, payload: dict[str, Any]) -> None:
	sign_task_id = str(payload.get("signTaskId") or "")
	signing_name = frappe.db.exists("Contract Signing", {"sign_task_id": sign_task_id})
	if not signing_name:
		event_doc.error = "未找到对应的合同签署记录"
		event_doc.save(ignore_permissions=True)
		return
	signing = frappe.get_doc("Contract Signing", signing_name)
	event_time = _event_datetime(payload.get("eventTime"))
	last_event_time = _event_datetime(getattr(signing, "last_event_time", None))
	if event_time and last_event_time and event_time < last_event_time:
		event_doc.contract_signing = signing.name
		event_doc.processed = 1
		event_doc.processed_on = now_datetime()
		event_doc.error = "已忽略早于最后处理时间的乱序事件"
		event_doc.save(ignore_permissions=True)
		return
	client = FadadaClient()
	detail = client.get_detail(sign_task_id)
	apply_vendor_detail(signing, detail, client.list_actors(sign_task_id))
	if event_time:
		signing.last_event_time = event_time
		signing.save(ignore_permissions=True)
	event_doc.contract_signing = signing.name
	event_doc.processed = 1
	event_doc.processed_on = now_datetime()
	event_doc.error = ""
	event_doc.save(ignore_permissions=True)
	if (
		str(signing.vendor_status).lower() == "task_finished"
		and not signing.signed_file
	):
		frappe.enqueue(
			"employee_roster.integrations.fadada.service.archive_signed_contract",
			signing_name=signing.name,
			queue="short",
			enqueue_after_commit=True,
		)


def handle_callback() -> dict[str, str]:
	raw_body = frappe.request.get_data(cache=False, as_text=False)
	headers = {str(key): str(value) for key, value in frappe.request.headers.items()}
	event_type, payload = verify_callback(headers, raw_body)
	sign_task_id = str(payload.get("signTaskId") or "")
	if not sign_task_id:
		raise frappe.ValidationError("法大大回调缺少 signTaskId")
	event_key = _event_key(event_type, payload)
	if frappe.db.exists("Contract Signing Event", {"event_key": event_key}):
		return {"msg": "success"}
	try:
		event_doc = frappe.get_doc(
			{
				"doctype": "Contract Signing Event",
				"event_key": event_key,
				"provider": "Fadada",
				"sign_task_id": sign_task_id,
				"flow_id": sign_task_id,
				"event_type": event_type,
				"event_time": _event_datetime(payload.get("eventTime")),
				"payload": frappe.as_json(_redact_payload(payload)),
				"processed": 0,
			}
		).insert(ignore_permissions=True)
	except frappe.UniqueValidationError:
		return {"msg": "success"}
	_apply_event(event_doc, payload)
	return {"msg": "success"}
