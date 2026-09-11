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

DEFAULT_NEXT_PATH = "/desk/hr-home"
STATE_TTL_SECONDS = 600
ALLOWED_NEXT_PREFIXES = ("/desk/", "/app/", "/wecom_home")


def oauth_public_base_url(config: WeComConfig | None = None) -> str:
	config = config or WeComConfig.load()
	if config.oauth_base_url:
		return config.oauth_base_url.rstrip("/")
	return get_url().rstrip("/")


def oauth_callback_url(config: WeComConfig | None = None) -> str:
	# 走 API 回调，避免 Website 整页渲染拖慢扫码登录。
	return (
		f"{oauth_public_base_url(config)}"
		"/api/method/employee_roster.integrations.wecom.api.wecom_sso_callback"
	)


def _state_secret(config: WeComConfig) -> bytes:
	raw = f"{config.corp_id}:{config.app_secret}:wecom-oauth"
	return hashlib.sha256(raw.encode()).digest()


def sanitize_next_path(next_path: str | None) -> str:
	path = str(next_path or "").strip() or DEFAULT_NEXT_PATH
	if not path.startswith("/"):
		path = f"/{path}"
	if path.startswith("//") or "://" in path:
		return DEFAULT_NEXT_PATH
	path_only = path.split("?", 1)[0]
	if path_only == "/wecom_home" or path_only.startswith("/wecom_home/"):
		return path
	if not path.startswith(("/desk/", "/app/")):
		return DEFAULT_NEXT_PATH
	# 当前 Frappe 的规范 Desk 前缀是 /desk；直接转换可省掉 /app -> /desk 的 301。
	if path.startswith("/app/"):
		path = f"/desk/{path[len('/app/'):]}"
	return path


def to_post_login_path(next_path: str | None) -> str:
	"""扫码成功后直接进入目标页（默认人事主页）。"""
	return sanitize_next_path(next_path)


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
	row = frappe.db.sql(
		"""
		select e.user_id
		from "tabEmployee" e
		inner join "tabUser" u on u.name = e.user_id
		where e.hr_wecom_id = %s
		  and e.status = 'Active'
		  and coalesce(e.user_id, '') <> ''
		  and u.enabled = 1
		limit 1
		""",
		(userid,),
	)
	if not row:
		raise frappe.ValidationError(
			"未找到已绑定该企微账号的在职员工，或员工未关联系统用户"
		)
	return str(row[0][0])


def login_system_user(user: str) -> None:
	from frappe.auth import LoginManager

	login_manager = getattr(frappe.local, "login_manager", None)
	if login_manager is None:
		login_manager = LoginManager()
		frappe.local.login_manager = login_manager
	login_manager.login_as(user)
	# 确保 sid 落库后再 302，避免会话未提交导致回跳失败页。
	frappe.db.commit()


def complete_oauth_login(code: str, state: str | None = None) -> dict[str, Any]:
	"""用授权 code 完成登录，返回跳转路径。"""
	config = WeComConfig.load()
	next_path = decode_oauth_state(state, config=config)
	client = WeComClient(config)
	userid = resolve_userid_from_code(code, client=client)
	user = find_system_user_by_wecom_userid(userid)
	login_system_user(user)
	redirect_to = to_post_login_path(next_path)
	# 后台预热 Desk boot，用户稍后点「人事主页」时更容易命中缓存。
	enqueue_boot_warmup(user)
	return {
		"user": user,
		"userid": userid,
		"redirect_to": redirect_to,
		"desk_next": sanitize_next_path(next_path),
	}


def warm_bootinfo_for_user(user: str | None = None) -> None:
	"""为指定用户构建并缓存 Desk bootinfo。"""
	from types import SimpleNamespace

	from frappe.sessions import get as get_session_boot

	user = (user or frappe.session.user or "").strip()
	if not user or user == "Guest":
		return

	frappe.set_user(user)
	# sessions.get 在无 request 时会读 frappe.local.request；补一个轻量占位。
	if not getattr(frappe.local, "request", None):
		frappe.local.request = SimpleNamespace(method="GET", path="/desk/hr-home")
	try:
		frappe.cache.hdel("bootinfo", user)
		get_session_boot()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "企微登录 boot 预热失败")


def enqueue_boot_warmup(user: str | None = None) -> None:
	"""异步预热，不阻塞扫码回调 302。"""
	user = (user or frappe.session.user or "").strip()
	if not user or user == "Guest":
		return
	try:
		frappe.enqueue(
			"employee_roster.integrations.wecom.oauth.warm_bootinfo_for_user",
			user=user,
			queue="short",
			timeout=120,
			enqueue_after_commit=True,
			job_id=f"wecom-boot-warmup:{user}",
			deduplicate=True,
		)
	except Exception:
		# 队列不可用时不阻塞登录。
		pass


def warm_access_token() -> None:
	"""登录页预热 access_token，减少扫码回调时的 gettoken 耗时。"""
	try:
		WeComClient().get_access_token("app")
	except Exception:
		pass


def oauth_entry_info(next_path: str | None = None) -> dict[str, Any]:
	try:
		config = WeComConfig.load()
	except WeComConfigurationError as exc:
		return {"configured": False, "message": str(exc)}
	warm_access_token()
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
