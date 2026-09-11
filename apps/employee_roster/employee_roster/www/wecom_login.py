# Copyright (c) 2026 stillgroup
# License: MIT
"""企业微信网页授权免登入口与回调。"""
from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import escape_html

no_cache = 1


def get_context(context):
	context.no_cache = 1
	context.show_sidebar = False
	code = frappe.form_dict.get("code")
	state = frappe.form_dict.get("state")
	next_path = frappe.form_dict.get("next") or frappe.form_dict.get("redirect_to")
	error = frappe.form_dict.get("error")

	if error:
		from urllib.parse import unquote

		context.title = _("企微登录失败")
		raw = unquote(str(frappe.form_dict.get("message") or "")).strip()
		context.error_message = escape_html(raw) if raw else _(
			"登录失败，请返回登录页重试，或联系人事确认账号绑定。"
		)
		return context

	if code:
		# 兼容旧回调地址：转到轻量 API，避免在 Website 上下文里做登录。
		from urllib.parse import urlencode

		from employee_roster.integrations.wecom.oauth import oauth_public_base_url

		query = urlencode({"code": code, "state": state or ""})
		frappe.local.flags.redirect_location = (
			f"{oauth_public_base_url()}"
			f"/api/method/employee_roster.integrations.wecom.api.wecom_sso_callback?{query}"
		)
		raise frappe.Redirect

	try:
		from employee_roster.integrations.wecom.oauth import build_authorize_url

		frappe.local.flags.redirect_location = build_authorize_url(next_path=next_path)
		raise frappe.Redirect
	except frappe.Redirect:
		raise
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "企业微信授权跳转失败")
		context.title = _("企微登录不可用")
		context.error_message = escape_html(str(exc)[:300])
		return context
