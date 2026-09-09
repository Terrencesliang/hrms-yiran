"""腾讯电子签企业自建应用回调验签、解密和幂等处理。"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Any

import frappe
from frappe.utils import now_datetime

CALLBACK_STATUS_MAP = {
	1: "Pending",
	2: "Signing",
	3: "Rejected",
	4: "Completed",
	5: "Expired",
	6: "Cancelled",
	8: "Pending",
	9: "Signing",
	16: "Error",
	21: "Cancelled",
}
TERMINAL_STATUSES = {"Completed", "Rejected", "Expired", "Cancelled"}


class CallbackVerificationError(frappe.PermissionError):
	pass


def _config_value(name: str) -> str:
	return str(
		os.getenv(f"TENCENT_ESIGN_{name.upper()}")
		or frappe.conf.get(f"tencent_esign_{name}")
		or ""
	).strip()


def _decrypt(encrypted: str, callback_key: str) -> bytes:
	try:
		from cryptography.hazmat.primitives import padding
		from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
	except ImportError as exc:
		raise CallbackVerificationError("腾讯电子签回调加密依赖未安装") from exc

	key = callback_key.encode("utf-8")
	if len(key) != 32:
		raise CallbackVerificationError("腾讯电子签 CallbackUrlKey 必须为 32 字节")
	try:
		ciphertext = base64.b64decode(encrypted, validate=True)
		decryptor = Cipher(algorithms.AES(key), modes.CBC(key[:16])).decryptor()
		padded = decryptor.update(ciphertext) + decryptor.finalize()
		unpadder = padding.PKCS7(128).unpadder()
		return unpadder.update(padded) + unpadder.finalize()
	except Exception as exc:
		raise CallbackVerificationError("腾讯电子签回调解密失败") from exc


def verify_and_decrypt_callback(
	headers: dict[str, str], raw_body: bytes
) -> tuple[bool, dict[str, Any] | None]:
	"""按腾讯电子签 Content-Signature 规则校验原始请求体并解密消息。"""
	token = _config_value("callback_token")
	if not token:
		raise CallbackVerificationError("腾讯电子签回调签名 Token 未配置")

	normalized_headers = {str(key).lower(): str(value) for key, value in headers.items()}
	signature = normalized_headers.get("content-signature", "")
	expected = "sha256=" + hmac.new(token.encode(), raw_body, hashlib.sha256).hexdigest()
	if not signature or not hmac.compare_digest(signature, expected):
		raise CallbackVerificationError("腾讯电子签回调签名验证失败")

	try:
		envelope = json.loads(raw_body)
	except (TypeError, ValueError) as exc:
		raise CallbackVerificationError("腾讯电子签回调不是有效 JSON") from exc

	if "encrypt" in envelope:
		callback_key = _config_value("callback_key")
		if not callback_key:
			raise CallbackVerificationError("腾讯电子签回调加密 Key 未配置")
		try:
			payload = json.loads(_decrypt(str(envelope["encrypt"]), callback_key))
		except (TypeError, ValueError, UnicodeDecodeError) as exc:
			raise CallbackVerificationError("腾讯电子签回调明文不是有效 JSON") from exc
	else:
		payload = envelope
	if not isinstance(payload, dict):
		raise CallbackVerificationError("腾讯电子签回调消息结构无效")
	return True, payload


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
	sensitive_fragments = ("idcard", "mobile", "bank", "account")

	def redact(value: Any) -> Any:
		if isinstance(value, dict):
			return {
				key: ("***" if any(part in key.lower() for part in sensitive_fragments) else redact(item))
				for key, item in value.items()
			}
		if isinstance(value, list):
			return [redact(item) for item in value]
		return value

	return redact(payload)


def _apply_flow_event(event: Any, payload: dict[str, Any]) -> None:
	data = payload.get("MsgData") or {}
	flow_id = str(data.get("FlowId") or "")
	signing_name = frappe.db.exists("Contract Signing", {"flow_id": flow_id})
	if not signing_name:
		event.error = "未找到对应的合同签署记录"
		event.save(ignore_permissions=True)
		return

	signing = frappe.get_doc("Contract Signing", signing_name)
	status_code = int(data.get("FlowCallbackStatus") or 0)
	next_status = CALLBACK_STATUS_MAP.get(status_code)
	if next_status and not (
		signing.status in TERMINAL_STATUSES and next_status not in TERMINAL_STATUSES
	):
		signing.status = next_status
	signing.vendor_status = str(data.get("FlowCallbackShowStatus") or status_code)
	signing.document_id = data.get("DocumentId") or signing.document_id
	signing.last_synced_on = now_datetime()
	if signing.status == "Completed" and not signing.completed_on:
		signing.completed_on = now_datetime()
	if signing.status == "Cancelled" and not signing.cancelled_on:
		signing.cancelled_on = now_datetime()
	signing.error_status = ""
	signing.save(ignore_permissions=True)

	event.contract_signing = signing.name
	event.processed = 1
	event.processed_on = now_datetime()
	event.error = ""
	event.save(ignore_permissions=True)
	if signing.status == "Completed" and not signing.signed_file:
		frappe.enqueue(
			"employee_roster.integrations.tencent_esign.service.archive_signed_contract",
			signing_name=signing.name,
			queue="short",
			enqueue_after_commit=True,
		)


def handle_callback() -> dict[str, bool]:
	raw_body = frappe.request.get_data(cache=False, as_text=False)
	headers = {str(key): str(value) for key, value in frappe.request.headers.items()}
	verified, payload = verify_and_decrypt_callback(headers, raw_body)
	if not verified or payload is None:
		frappe.throw("腾讯电子签回调验签尚未配置或验证失败", CallbackVerificationError)

	if payload.get("MsgType") != "FlowStatusChange":
		return {"ok": True}
	event_key = str(payload.get("MsgId") or "")
	if not event_key:
		raise frappe.ValidationError("回调缺少 MsgId")
	if frappe.db.exists("Contract Signing Event", {"event_key": event_key}):
		return {"ok": True}
	data = payload.get("MsgData") or {}
	if not data.get("FlowId"):
		raise frappe.ValidationError("合同状态回调缺少 FlowId")
	event = frappe.get_doc(
		{
			"doctype": "Contract Signing Event",
			"provider": "Tencent",
			"event_key": event_key,
			"flow_id": data.get("FlowId"),
			"event_type": payload.get("MsgType"),
			"payload": frappe.as_json(_redact_payload(payload)),
			"processed": 0,
		}
	).insert(ignore_permissions=True)
	_apply_flow_event(event, payload)
	return {"ok": True}
