# Copyright (c) 2026 stillgroup
# License: MIT
"""Notification helpers for approval runtime."""

from __future__ import annotations

import frappe


def notify_users(
	users: list[str] | None,
	*,
	subject: str,
	message: str,
	document_type: str | None = None,
	document_name: str | None = None,
) -> None:
	seen = set()
	for user in users or []:
		if not user or user in seen or user == "Guest":
			continue
		seen.add(user)
		try:
			notification = frappe.new_doc("Notification Log")
			notification.for_user = user
			notification.type = "Alert"
			notification.subject = subject
			notification.email_content = message
			if document_type and document_name:
				notification.document_type = document_type
				notification.document_name = document_name
			notification.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Approval notify failed")
		try:
			if frappe.db.get_value("User", user, "email"):
				frappe.sendmail(
					recipients=[user],
					subject=subject,
					message=message,
					delayed=True,
					reference_doctype=document_type,
					reference_name=document_name,
				)
		except Exception:
			# mail optional
			pass
