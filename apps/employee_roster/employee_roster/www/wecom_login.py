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

	if code:
		try:
			from employee_roster.integrations.wecom.oauth import complete_oauth_login

			result = complete_oauth_login(str(code), str(state or ""))
			frappe.local.flags.redirect_location = result["redirect_to"]
			raise frappe.Redirect
		except frappe.Redirect:
			raise
		except Exception as exc:
			frappe.log_error(frappe.get_traceback(), "企业微信免登失败")
			context.title = _("企微登录失败")
			context.error_message = escape_html(str(exc)[:300])
			return context

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
