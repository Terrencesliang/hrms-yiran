"""法大大 FASC OpenAPI v5.1 窄客户端。

签名算法与接口路径取自法大大官方 Python SDK v5.1。官方 SDK 固定依赖
requests==2.24.0/urllib3==1.25.10, 且仅说明在 Python 3.8 开发, 因此本项目
不直接引入 SDK, 而是在现有 requests 上复现其签名算法和最小请求面。
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any

import frappe
import requests

SUCCESS_CODE = "100000"
SIGN_TYPE = "HMAC-SHA256"
TOKEN_CACHE_KEY = "employee_roster:fadada:access_token"
AUTH_ERROR_CODES = {"100004", "100005", "100006", "401", "INVALID_TOKEN", "TOKEN_EXPIRED"}
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class ConfigurationError(RuntimeError):
	"""法大大配置不完整。"""


class FadadaAPIError(RuntimeError):
	"""法大大返回业务或协议错误。"""

	def __init__(self, code: str, message: str, request_id: str = ""):
		super().__init__(f"法大大接口错误 {code}: {message}")
		self.code = code
		self.request_id = request_id


@dataclass(frozen=True)
class FadadaConfig:
	app_id: str
	app_secret: str
	server_url: str
	corp_open_id: str
	api_sub_version: str = "5.1"

	@classmethod
	def load(cls) -> FadadaConfig:
		def value(name: str, default: str = "") -> str:
			return str(
				os.getenv(f"FADADA_{name}")
				or frappe.conf.get(f"fadada_{name.lower()}")
				or default
			).strip()

		config = cls(
			app_id=value("APP_ID"),
			app_secret=value("APP_SECRET"),
			server_url=value("SERVER_URL").rstrip("/"),
			corp_open_id=value("CORP_OPEN_ID"),
			api_sub_version=value("API_SUB_VERSION", "5.1"),
		)
		missing = config.missing_fields()
		if missing:
			raise ConfigurationError(f"法大大配置缺失: {', '.join(missing)}")
		if not config.server_url.startswith(("https://", "http://")):
			raise ConfigurationError("法大大 SERVER_URL 必须是 HTTP(S) 地址")
		return config

	def missing_fields(self) -> list[str]:
		return [
			name
			for name, value in (
				("APP_ID", self.app_id),
				("APP_SECRET", self.app_secret),
				("SERVER_URL", self.server_url),
				("CORP_OPEN_ID", self.corp_open_id),
			)
			if not value
		]


def configuration_status() -> dict[str, Any]:
	try:
		config = FadadaConfig.load()
	except ConfigurationError as exc:
		return {"configured": False, "provider": "Fadada", "message": str(exc)}
	return {
		"configured": True,
		"provider": "Fadada",
		"server_url": config.server_url,
		"api_sub_version": config.api_sub_version,
		"corp_open_id_configured": True,
	}


def canonical_json(data: Any) -> str:
	"""与官方 Python SDK 的默认 json.dumps 线格式保持一致。"""
	return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def canonical_parameters(parameters: dict[str, str]) -> str:
	return "&".join(f"{key}={value}" for key, value in sorted(parameters.items()))


def calculate_signature(parameters: dict[str, str], timestamp: str, app_secret: str) -> str:
	"""复现官方 HashUtils.sign: SHA256(params) 后做两阶段 HMAC-SHA256。"""
	params_hash = hashlib.sha256(canonical_parameters(parameters).encode()).hexdigest().encode()
	derived_key = hmac.new(app_secret.encode(), timestamp.encode(), hashlib.sha256).digest()
	return hmac.new(derived_key, params_hash, hashlib.sha256).hexdigest()


def signed_headers(
	config: FadadaConfig,
	biz_content: str | None,
	*,
	access_token: str = "",
	timestamp: str | None = None,
	nonce: str | None = None,
) -> dict[str, str]:
	timestamp = timestamp or str(int(time.time() * 1000))
	headers = {
		"X-FASC-App-Id": config.app_id,
		"X-FASC-Sign-Type": SIGN_TYPE,
		"X-FASC-Timestamp": timestamp,
		"X-FASC-Nonce": nonce or uuid.uuid4().hex,
		"X-FASC-Api-SubVersion": config.api_sub_version,
	}
	if access_token:
		headers["X-FASC-AccessToken"] = access_token
	else:
		headers["X-FASC-Grant-Type"] = "client_credential"
	parameters = dict(headers)
	if biz_content is not None:
		parameters["bizContent"] = biz_content
	headers["X-FASC-Sign"] = calculate_signature(parameters, timestamp, config.app_secret)
	return headers


class FadadaClient:
	"""仅开放合同模板签署流程所需接口。"""

	def __init__(
		self,
		config: FadadaConfig | None = None,
		*,
		session: requests.Session | None = None,
		timeout: tuple[int, int] = (5, 30),
		max_retries: int = 2,
	):
		self.config = config or FadadaConfig.load()
		self.session = session or requests.Session()
		self.timeout = timeout
		self.max_retries = max(0, max_retries)

	def _cache(self) -> Any:
		return frappe.cache

	def _token_cache_key(self) -> str:
		scope = hashlib.sha256(
			f"{self.config.app_id}|{self.config.server_url}".encode()
		).hexdigest()[:20]
		return f"{TOKEN_CACHE_KEY}:{scope}"

	def get_access_token(self, *, force_refresh: bool = False) -> str:
		cache = self._cache()
		cache_key = self._token_cache_key()
		if not force_refresh and (cached := cache.get_value(cache_key)):
			return cached.decode() if isinstance(cached, bytes) else str(cached)
		data = self._request("/service/get-access-token", None, use_token=False)
		token = str(data.get("accessToken") or "")
		if not token:
			raise FadadaAPIError("INVALID_RESPONSE", "获取凭证响应缺少 accessToken")
		expires_in = int(data.get("expiresIn") or data.get("expires_in") or 7200)
		cache.set_value(cache_key, token, expires_in_sec=max(60, expires_in - 300))
		return token

	def _request(
		self, path: str, payload: dict[str, Any] | None, *, use_token: bool = True
	) -> dict[str, Any]:
		biz_content = None if payload is None else canonical_json(payload)
		token = self.get_access_token() if use_token else ""
		refreshed = False
		for attempt in range(self.max_retries + 1):
			started = time.monotonic()
			try:
				response = self.session.post(
					f"{self.config.server_url}{path}",
					data={} if biz_content is None else {"bizContent": biz_content},
					headers=signed_headers(
						self.config, biz_content, access_token=token
					),
					timeout=self.timeout,
				)
			except (requests.Timeout, requests.ConnectionError):
				if attempt >= self.max_retries:
					raise
				time.sleep(0.25 * (2**attempt))
				continue
			if response.status_code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
				retry_after = response.headers.get("Retry-After")
				delay = float(retry_after) if retry_after and retry_after.isdigit() else 0.25 * (2**attempt)
				time.sleep(min(delay, 2.0))
				continue
			response.raise_for_status()
			try:
				body = response.json()
			except ValueError as exc:
				raise FadadaAPIError("INVALID_RESPONSE", "响应不是有效 JSON") from exc
			code = str(body.get("code") or "")
			request_id = str(response.headers.get("X-FASC-Request-Id") or "")
			frappe.logger("fadada").info(
				{
					"operation": path,
					"status_code": response.status_code,
					"vendor_code": code,
					"request_id": request_id,
					"duration_ms": round((time.monotonic() - started) * 1000),
					"attempt": attempt + 1,
				}
			)
			if use_token and not refreshed and code.upper() in AUTH_ERROR_CODES:
				token = self.get_access_token(force_refresh=True)
				refreshed = True
				continue
			if code != SUCCESS_CODE:
				raise FadadaAPIError(
					code or "UNKNOWN",
					str(body.get("msg") or "未知错误"),
					request_id,
				)
			data = body.get("data")
			return data if isinstance(data, dict) else {}
		raise FadadaAPIError("RETRY_EXHAUSTED", "法大大请求重试次数已耗尽")

	def get_templates(self, payload: dict[str, Any]) -> dict[str, Any]:
		return self._request("/sign-template/get-list", payload)

	def get_template_detail(self, payload: dict[str, Any]) -> dict[str, Any]:
		return self._request("/sign-template/get-detail", payload)

	def get_template_edit_url(self, template_id: str) -> dict[str, Any]:
		return self._request(
			"/template/edit/get-url",
			{
				"openCorpId": self.config.corp_open_id,
				"templateId": template_id,
			},
		)

	def create_with_template(self, payload: dict[str, Any]) -> dict[str, Any]:
		return self._request("/sign-task/create-with-template", payload)

	def create(self, payload: dict[str, Any]) -> dict[str, Any]:
		return self._request("/sign-task/create", payload)

	def get_file_upload_url(self, file_type: str = "doc") -> dict[str, Any]:
		return self._request("/file/get-upload-url", {"fileType": file_type})

	def process_file(self, fdd_file_url: str, file_name: str) -> dict[str, Any]:
		return self._request(
			"/file/process",
			{
				"fddFileUrlList": [
					{
						"fileType": "doc",
						"fddFileUrl": fdd_file_url,
						"fileName": file_name,
						"fileFormat": "pdf",
					}
				]
			},
		)

	def fill_field_values(
		self, sign_task_id: str, doc_field_values: list[dict[str, Any]]
	) -> dict[str, Any]:
		return self._request(
			"/sign-task/field/fill-values",
			{"signTaskId": sign_task_id, "docFieldValues": doc_field_values},
		)

	def list_fields(self, sign_task_id: str) -> dict[str, Any]:
		return self._request("/sign-task/field/list", {"signTaskId": sign_task_id})

	def finalize_docs(self, sign_task_id: str) -> dict[str, Any]:
		return self._request("/sign-task/doc-finalize", {"signTaskId": sign_task_id})

	def get_edit_url(self, payload: dict[str, Any]) -> dict[str, Any]:
		return self._request("/sign-task/get-edit-url", payload)

	def get_preview_url(self, payload: dict[str, Any]) -> dict[str, Any]:
		return self._request("/sign-task/get-preview-url", payload)

	def start(self, sign_task_id: str) -> dict[str, Any]:
		return self._request("/sign-task/start", {"signTaskId": sign_task_id})

	def get_actor_url(self, payload: dict[str, Any]) -> dict[str, Any]:
		return self._request("/sign-task/actor/get-url", payload)

	def get_detail(self, sign_task_id: str) -> dict[str, Any]:
		data = self._request("/sign-task/app/get-detail", {"signTaskId": sign_task_id})
		for key in ("signTask", "signTaskInfo", "taskDetail"):
			if isinstance(data.get(key), dict):
				return {**data, **data[key]}
		return data

	def list_actors(self, sign_task_id: str) -> dict[str, Any]:
		data = self._request("/sign-task/actor/list", {"signTaskId": sign_task_id})
		if any(isinstance(data.get(key), list) for key in ("actors", "actorList", "list")):
			return data
		detail = self.get_detail(sign_task_id)
		return {"actors": detail.get("actors") or []}

	def list_seals(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
		return self._request(
			"/seal/get-list",
			payload or {"openCorpId": self.config.corp_open_id},
		)

	def get_seal_detail(self, seal_id: str) -> dict[str, Any]:
		return self._request(
			"/seal/get-detail",
			{"openCorpId": self.config.corp_open_id, "sealId": seal_id},
		)

	def get_seal_free_sign_url(self, payload: dict[str, Any]) -> dict[str, Any]:
		return self._request("/seal/free-sign/get-url", payload)

	def urge(self, sign_task_id: str) -> dict[str, Any]:
		return self._request("/sign-task/urge", {"signTaskId": sign_task_id})

	def cancel(self, sign_task_id: str, reason: str) -> dict[str, Any]:
		return self._request(
			"/sign-task/cancel",
			{"signTaskId": sign_task_id, "terminationNote": reason[:200]},
		)

	def delete(self, sign_task_id: str) -> dict[str, Any]:
		return self._request("/sign-task/delete", {"signTaskId": sign_task_id})

	def get_download_url(self, payload: dict[str, Any]) -> dict[str, Any]:
		return self._request("/sign-task/owner/get-download-url", payload)

	def get_evidence_report_url(self, sign_task_id: str) -> dict[str, Any]:
		return self._request(
			"/sign-task/evidence-report/get-download-url",
			{"signTaskId": sign_task_id},
		)
