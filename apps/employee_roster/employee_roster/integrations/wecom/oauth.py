"""企业微信网页授权免登（阶段 4）。"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import quote, urlencode

import frappe
from frappe.utils import get_url

from .client import WeComClient, WeComConfig, WeComConfigurationError

DEFAULT_NEXT_PATH = "/app/hr-home"
STATE_TTL_SECONDS = 600
ALLOWED_NEXT_PREFIX = "/app/"


def oauth_public_base_url(config: WeComConfig | None = None) -> str:
	config = config or WeComConfig.load()
	if config.oauth_base_url:
		return config.oauth_base_url.rstrip("/")
	return get_url().rstrip("/")


def oauth_callback_url(config: WeComConfig | None = None) -> str:
	return f"{oauth_public_base_url(config)}/wecom_login"


def _state_secret(config: WeComConfig) -> bytes:
	raw = f"{config.corp_id}:{config.app_secret}:wecom-oauth"
	return hashlib.sha256(raw.encode()).digest()


def sanitize_next_path(next_path: str | None) -> str:
	path = str(next_path or "").strip() or DEFAULT_NEXT_PATH
	if not path.startswith("/"):
		path = f"/{path}"
	if path.startswith("//") or "://" in path:
		return DEFAULT_NEXT_PATH
	if not path.startswith(ALLOWED_NEXT_PREFIX):
		return DEFAULT_NEXT_PATH
	return path


def encode_oauth_state(next_path: str | None = None, *, config: WeComConfig | None = None) -> str:
	config = config or WeComConfig.load()
	payload = {
		"n": sanitize_next_path(next_path),
		"t": int(time.time()),
	}
	body = base64.urlsafe_b64encode(
		json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
	).decode().rstrip("=")
	sig = hmac.new(_state_secret(config), body.encode(), hashlib.sha256).hexdigest()[:24]
	return f"{body}.{sig}"


def decode_oauth_state(state: str | None, *, config: WeComConfig | None = None) -> str:
	config = config or WeComConfig.load()
	raw = str(state or "").strip()
	if "." not in raw:
		return DEFAULT_NEXT_PATH
	body, sig = raw.rsplit(".", 1)
	expected = hmac.new(_state_secret(config), body.encode(), hashlib.sha256).hexdigest()[:24]
	if not hmac.compare_digest(sig, expected):
		return DEFAULT_NEXT_PATH
	padding = "=" * (-len(body) % 4)
	try:
		payload = json.loads(base64.urlsafe_b64decode(body + padding).decode())
	except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
		return DEFAULT_NEXT_PATH
	created = int(payload.get("t") or 0)
	if abs(int(time.time()) - created) > STATE_TTL_SECONDS:
		return DEFAULT_NEXT_PATH
	return sanitize_next_path(str(payload.get("n") or ""))


def build_authorize_url(
	*,
	next_path: str | None = None,
	state: str | None = None,
	config: WeComConfig | None = None,
) -> str:
	config = config or WeComConfig.load()
	state = state or encode_oauth_state(next_path, config=config)
	query = urlencode(
		{
			"appid": config.corp_id,
			"redirect_uri": oauth_callback_url(config),
			"response_type": "code",
			"scope": "snsapi_base",
			"state": state,
			"agentid": str(config.agent_id),
		},
		quote_via=quote,
	)
	return f"https://open.weixin.qq.com/connect/oauth2/authorize?{query}#wechat_redirect"


def build_web_login_url(
	*,
	next_path: str | None = None,
	state: str | None = None,
	config: WeComConfig | None = None,
) -> str:
	"""PC 端企业微信扫码登录（SSO 跳转）。"""
	config = config or WeComConfig.load()
	state = state or encode_oauth_state(next_path, config=config)
	query = urlencode(
		{
			"login_type": "CorpApp",
			"appid": config.corp_id,
			"agentid": str(config.agent_id),
			"redirect_uri": oauth_callback_url(config),
			"state": state,
			"lang": "zh",
		},
		quote_via=quote,
	)
	return f"https://login.work.weixin.qq.com/wwlogin/sso/login?{query}"


def web_login_panel_params(
	*,
	next_path: str | None = None,
	config: WeComConfig | None = None,
) -> dict[str, Any]:
	"""供前端 createWWLoginPanel 使用的公开参数（不含 Secret）。"""
	config = config or WeComConfig.load()
	state = encode_oauth_state(next_path, config=config)
	return {
		"login_type": "CorpApp",
		"appid": config.corp_id,
		"agentid": str(config.agent_id),
		"redirect_uri": oauth_callback_url(config),
		"state": state,
		"redirect_type": "callback",
		"lang": "zh",
	}


def resolve_userid_from_code(code: str, *, client: WeComClient | None = None) -> str:
	client = client or WeComClient()
	body = client.get_user_info_by_code(code)
	userid = str(body.get("userid") or body.get("UserId") or "").strip()
	if not userid:
		raise frappe.ValidationError(
			"未能获取企微 UserID，请确认成员在自建应用可见范围内且授权有效"
		)
	return userid


def find_system_user_by_wecom_userid(userid: str) -> str:
	user = frappe.db.get_value(
		"Employee",
		{"hr_wecom_id": userid, "status": "Active"},
		"user_id",
	)
	if not user:
		raise frappe.ValidationError(
			"未找到已绑定该企微账号的在职员工，或员工未关联系统用户"
		)
	if not frappe.db.exists("User", user) or frappe.db.get_value("User", user, "enabled") != 1:
		raise frappe.ValidationError("关联系统用户不存在或已禁用")
	return str(user)


def login_system_user(user: str) -> None:
	from frappe.auth import LoginManager

	frappe.local.login_manager = LoginManager()
	frappe.local.login_manager.login_as(user)
	frappe.db.commit()


def complete_oauth_login(code: str, state: str | None = None) -> dict[str, Any]:
	"""用授权 code 完成登录，返回跳转路径。"""
	config = WeComConfig.load()
	next_path = decode_oauth_state(state, config=config)
	userid = resolve_userid_from_code(code)
	user = find_system_user_by_wecom_userid(userid)
	login_system_user(user)
	return {"user": user, "userid": userid, "redirect_to": next_path}


def oauth_entry_info(next_path: str | None = None) -> dict[str, Any]:
	try:
		config = WeComConfig.load()
	except WeComConfigurationError as exc:
		return {"configured": False, "message": str(exc)}
	state = encode_oauth_state(next_path, config=config)
	return {
		"configured": True,
		"callback_url": oauth_callback_url(config),
		"authorize_url": build_authorize_url(state=state, config=config),
		"web_login_url": build_web_login_url(state=state, config=config),
		"panel": web_login_panel_params(next_path=next_path, config=config),
		"next_path": sanitize_next_path(next_path),
		"oauth_base_url": oauth_public_base_url(config),
	}
