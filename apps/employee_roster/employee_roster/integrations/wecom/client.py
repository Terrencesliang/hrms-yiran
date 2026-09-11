"""企业微信服务端 API 客户端。

配置从环境变量或 site_config 读取，密钥不进入数据库和仓库。应用、通讯录和
打卡可使用不同 Secret，并按凭证隔离 access_token 缓存。
"""
from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from typing import Any, Literal

import frappe
import requests

API_BASE_URL = "https://qyapi.weixin.qq.com"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
TOKEN_ERROR_CODES = {40014, 42001, 42007, 42009}


class WeComConfigurationError(RuntimeError):
	"""企业微信配置不完整。"""


class WeComAPIError(RuntimeError):
	"""企业微信返回业务或协议错误。"""

	def __init__(self, code: int, message: str, operation: str = ""):
		super().__init__(f"企业微信接口错误 {code}: {message}")
		self.code = code
		self.operation = operation


@dataclass(frozen=True)
class WeComConfig:
	corp_id: str
	agent_id: int
	app_secret: str
	contact_secret: str = ""
	checkin_secret: str = ""
	default_company: str = ""
	robot_webhook: str = ""
	create_missing_employees: bool = False
	oauth_base_url: str = ""

	@classmethod
	def load(cls) -> WeComConfig:
		def value(name: str, default: Any = "") -> Any:
			return os.getenv(f"WECOM_{name}") or frappe.conf.get(f"wecom_{name.lower()}") or default

		def flag(name: str, default: bool = False) -> bool:
			raw = value(name, default)
			if isinstance(raw, bool):
				return raw
			return str(raw).strip().lower() in {"1", "true", "yes", "on"}

		try:
			agent_id = int(value("AGENT_ID", 0))
		except (TypeError, ValueError) as exc:
			raise WeComConfigurationError("企业微信 AGENT_ID 必须为整数") from exc
		config = cls(
			corp_id=str(value("CORP_ID")).strip(),
			agent_id=agent_id,
			app_secret=str(value("APP_SECRET")).strip(),
			contact_secret=str(value("CONTACT_SECRET")).strip(),
			checkin_secret=str(value("CHECKIN_SECRET")).strip(),
			default_company=str(value("DEFAULT_COMPANY")).strip(),
			robot_webhook=str(value("ROBOT_WEBHOOK")).strip(),
			create_missing_employees=flag("CREATE_MISSING_EMPLOYEES"),
			oauth_base_url=str(value("OAUTH_BASE_URL")).strip().rstrip("/"),
		)
		missing = [
			label
			for label, item in (
				("CORP_ID", config.corp_id),
				("AGENT_ID", config.agent_id),
				("APP_SECRET", config.app_secret),
			)
			if not item
		]
		if missing:
			raise WeComConfigurationError(f"企业微信配置缺失: {', '.join(missing)}")
		return config

	def secret_for(self, scope: str) -> str:
		if scope == "contacts":
			return self.contact_secret
		if scope == "checkin":
			return self.checkin_secret or self.app_secret
		return self.app_secret


def configuration_status() -> dict[str, Any]:
	try:
		config = WeComConfig.load()
	except WeComConfigurationError as exc:
		return {"configured": False, "provider": "WeCom", "message": str(exc)}
	return {
		"configured": True,
		"provider": "WeCom",
		"corp_id": config.corp_id,
		"agent_id": config.agent_id,
		"contact_secret_configured": bool(config.contact_secret),
		"checkin_secret_configured": bool(config.checkin_secret),
		"default_company": config.default_company,
		"robot_webhook_configured": bool(config.robot_webhook),
		"create_missing_employees": config.create_missing_employees,
		"oauth_base_url": config.oauth_base_url,
	}


def connection_status() -> dict[str, Any]:
	"""无副作用探测应用、通讯录和打卡接口；机器人仅报告配置状态。"""
	client = WeComClient()
	result: dict[str, Any] = {
		"app": {"ok": False},
		"contacts": {"ok": False},
		"checkin": {"ok": False, "verified": False},
		"robot": {
			"ok": bool(client.config.robot_webhook),
			"verified": False,
			"message": "已配置但未发送测试消息",
		},
	}

	def error(exc: Exception) -> dict[str, Any]:
		return {
			"ok": False,
			"error": str(exc)[:500],
			"code": getattr(exc, "code", None),
		}

	try:
		client.request(
			"GET",
			"/cgi-bin/agent/get",
			params={"agentid": client.config.agent_id},
		)
		result["app"] = {"ok": True}
	except Exception as exc:
		result["app"] = error(exc)

	try:
		client.get_access_token("contacts", force_refresh=True)
		departments = client.list_departments()
		result["contacts"] = {"ok": True, "department_count": len(departments)}
	except Exception as exc:
		result["contacts"] = error(exc)

	sample_userid = frappe.db.get_value(
		"Employee",
		{"status": "Active", "hr_wecom_id": ["is", "set"]},
		"hr_wecom_id",
	)
	sample_source = "employee"
	if not sample_userid:
		try:
			remote_users = client.list_user_ids()
			sample_userid = next(
				(
					str(row.get("userid"))
					for row in remote_users
					if row.get("userid")
				),
				"",
			)
			sample_source = "remote_contact"
		except Exception:
			sample_userid = ""
	if sample_userid:
		try:
			end = int(time.time())
			client.get_checkin_data([str(sample_userid)], end - 3600, end)
			result["checkin"] = {
				"ok": True,
				"verified": True,
				"sample_source": sample_source,
			}
		except Exception as exc:
			result["checkin"] = {**error(exc), "verified": True}
	else:
		result["checkin"]["message"] = "尚无已绑定企微 UserID 的员工，无法验证打卡权限"
	return result


def remote_user_shape() -> dict[str, Any]:
	"""只返回响应结构，不输出成员隐私。"""
	client = WeComClient()
	rows = client.list_user_ids()
	userid = next((str(row.get("userid")) for row in rows if row.get("userid")), "")
	if not userid:
		return {"member_count": len(rows), "has_sample": False}
	user = client.get_user(userid)
	return {
		"member_count": len(rows),
		"has_sample": True,
		"keys": sorted(user),
		"userid_returned": bool(user.get("userid")),
		"name_returned": bool(user.get("name")),
		"mobile_returned": bool(user.get("mobile")),
	}


class WeComClient:
	def __init__(
		self,
		config: WeComConfig | None = None,
		*,
		session: requests.Session | None = None,
		timeout: tuple[int, int] = (5, 30),
		max_retries: int = 2,
	):
		self.config = config or WeComConfig.load()
		self.session = session or requests.Session()
		self.timeout = timeout
		self.max_retries = max(0, max_retries)

	def _token_cache_key(self, scope: str) -> str:
		secret_hash = hashlib.sha256(self.config.secret_for(scope).encode()).hexdigest()[:16]
		return f"employee_roster:wecom:access_token:{self.config.corp_id}:{scope}:{secret_hash}"

	def get_access_token(self, scope: str = "app", *, force_refresh: bool = False) -> str:
		cache_key = self._token_cache_key(scope)
		if not force_refresh and (cached := frappe.cache.get_value(cache_key)):
			return cached.decode() if isinstance(cached, bytes) else str(cached)
		secret = self.config.secret_for(scope)
		if not secret:
			raise WeComConfigurationError(f"企业微信 {scope} Secret 未配置")
		body = self._send(
			"GET",
			"/cgi-bin/gettoken",
			params={"corpid": self.config.corp_id, "corpsecret": secret},
			use_token=False,
		)
		token = str(body.get("access_token") or "")
		if not token:
			raise WeComAPIError(-1, "获取凭证响应缺少 access_token", "/cgi-bin/gettoken")
		expires_in = int(body.get("expires_in") or 7200)
		frappe.cache.set_value(cache_key, token, expires_in_sec=max(60, expires_in - 300))
		return token

	def request(
		self,
		method: Literal["GET", "POST"],
		path: str,
		*,
		scope: str = "app",
		params: dict[str, Any] | None = None,
		payload: dict[str, Any] | None = None,
	) -> dict[str, Any]:
		params = dict(params or {})
		params["access_token"] = self.get_access_token(scope)
		refreshed = False
		while True:
			try:
				return self._send(method, path, params=params, payload=payload)
			except WeComAPIError as exc:
				if refreshed or exc.code not in TOKEN_ERROR_CODES:
					raise
				params["access_token"] = self.get_access_token(scope, force_refresh=True)
				refreshed = True

	def _send(
		self,
		method: str,
		path: str,
		*,
		params: dict[str, Any] | None = None,
		payload: dict[str, Any] | None = None,
		use_token: bool = True,
	) -> dict[str, Any]:
		for attempt in range(self.max_retries + 1):
			started = time.monotonic()
			try:
				response = self.session.request(
					method,
					f"{API_BASE_URL}{path}",
					params=params,
					json=payload if method == "POST" else None,
					timeout=self.timeout,
				)
			except (requests.Timeout, requests.ConnectionError):
				if attempt >= self.max_retries:
					raise
				time.sleep(0.25 * (2**attempt))
				continue
			if response.status_code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
				time.sleep(0.25 * (2**attempt))
				continue
			response.raise_for_status()
			try:
				body = response.json()
			except ValueError as exc:
				raise WeComAPIError(-1, "响应不是有效 JSON", path) from exc
			code = int(body.get("errcode") or 0)
			frappe.logger("wecom").info(
				{
					"operation": path,
					"status_code": response.status_code,
					"vendor_code": code,
					"duration_ms": round((time.monotonic() - started) * 1000),
					"attempt": attempt + 1,
				}
			)
			if code:
				raise WeComAPIError(code, str(body.get("errmsg") or "未知错误"), path)
			return body
		raise WeComAPIError(-1, "请求重试次数已耗尽", path)

	def list_departments(self) -> list[dict[str, Any]]:
		# 2022-08 起，新增可信 IP 的通讯录同步助手只能读取部门 ID，
		# 部门名称等详情必须改用自建应用（且受应用可见范围限制）。
		id_rows = self.request(
			"GET", "/cgi-bin/department/simplelist", scope="contacts"
		).get("department_id") or []
		allowed_ids = {str(row.get("id")) for row in id_rows}
		detail_rows = self.request("GET", "/cgi-bin/department/list").get("department") or []
		return [
			row
			for row in detail_rows
			if str(row.get("id")) in allowed_ids or str(row.get("id")) == "1"
		]

	def list_user_ids(self) -> list[dict[str, Any]]:
		rows: list[dict[str, Any]] = []
		cursor = ""
		while True:
			body = self.request(
				"POST",
				"/cgi-bin/user/list_id",
				scope="contacts",
				payload={"cursor": cursor, "limit": 10000},
			)
			rows.extend(body.get("dept_user") or [])
			cursor = str(body.get("next_cursor") or "")
			if not cursor:
				return rows

	def list_visible_users(self) -> list[dict[str, Any]]:
		body = self.request(
			"GET",
			"/cgi-bin/user/simplelist",
			params={"department_id": 1, "fetch_child": 1},
		)
		return body.get("userlist") or []

	def get_user(self, userid: str) -> dict[str, Any]:
		return self.request("GET", "/cgi-bin/user/get", params={"userid": userid})

	def get_userid_by_mobile(self, mobile: str) -> str:
		body = self.request("POST", "/cgi-bin/user/getuserid", payload={"mobile": mobile})
		return str(body.get("userid") or "")

	def send_message(self, payload: dict[str, Any]) -> dict[str, Any]:
		return self.request("POST", "/cgi-bin/message/send", payload=payload)

	def get_user_info_by_code(self, code: str) -> dict[str, Any]:
		"""网页授权 code 换取访问用户身份（userid）。"""
		return self.request(
			"GET",
			"/cgi-bin/auth/getuserinfo",
			params={"code": str(code or "").strip()},
		)

	def get_checkin_data(
		self, userids: list[str], start_timestamp: int, end_timestamp: int
	) -> list[dict[str, Any]]:
		body = self.request(
			"POST",
			"/cgi-bin/checkin/getcheckindata",
			scope="checkin",
			payload={
				"opencheckindatatype": 3,
				"starttime": start_timestamp,
				"endtime": end_timestamp,
				"useridlist": userids,
			},
		)
		return body.get("checkindata") or []

	def get_checkin_daydata(
		self, userids: list[str], start_timestamp: int, end_timestamp: int
	) -> list[dict[str, Any]]:
		body = self.request(
			"POST",
			"/cgi-bin/checkin/getcheckin_daydata",
			scope="checkin",
			payload={
				"starttime": start_timestamp,
				"endtime": end_timestamp,
				"useridlist": userids,
			},
		)
		return body.get("datas") or []

	def get_checkin_monthdata(
		self, userids: list[str], start_timestamp: int, end_timestamp: int
	) -> list[dict[str, Any]]:
		body = self.request(
			"POST",
			"/cgi-bin/checkin/getcheckin_monthdata",
			scope="checkin",
			payload={
				"starttime": start_timestamp,
				"endtime": end_timestamp,
				"useridlist": userids,
			},
		)
		return body.get("datas") or []
