# Copyright (c) 2026 stillgroup
# License: MIT
"""企微扫码后的轻量落地页：不进 Desk，避免 bootinfo 冷启动。"""
from __future__ import annotations

from urllib.parse import quote, unquote

import frappe
from frappe import _

no_cache = 1
base_template_path = "templates/wecom_shell.html"

ALLOWED_CONTINUE_PREFIXES = ("/desk/", "/app/")


def _safe_continue(raw: str | None) -> str:
	path = unquote(str(raw or "").strip())
	if not path.startswith("/"):
		return ""
	if path.startswith("//") or "://" in path:
		return ""
	if not path.startswith(ALLOWED_CONTINUE_PREFIXES):
		return ""
	if path.startswith("/app/"):
		path = f"/desk/{path[len('/app/') :]}"
	return path


def get_context(context):
	context.no_cache = 1
	context.show_sidebar = False
	context.title = _("HR Pro")

	if frappe.session.user in (None, "Guest"):
		next_q = quote("/wecom_home", safe="/")
		frappe.local.flags.redirect_location = f"/login?redirect-to={next_q}"
		raise frappe.Redirect

	full_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	employee_name = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user, "status": "Active"},
		"employee_name",
	)
	context.display_name = str(employee_name or full_name)
	context.continue_path = _safe_continue(
		frappe.form_dict.get("continue") or frappe.form_dict.get("next")
	)

	try:
		from employee_roster.integrations.wecom.oauth import enqueue_boot_warmup

		enqueue_boot_warmup(frappe.session.user)
	except Exception:
		pass
	return context
