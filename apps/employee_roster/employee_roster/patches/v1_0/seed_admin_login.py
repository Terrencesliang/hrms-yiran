"""Enable login with username `admin` / password `admin` for local HR Pro."""

from __future__ import annotations

import frappe
from frappe.utils.password import update_password


def execute():
	ss = frappe.get_single("System Settings")
	changed = False
	if not cint_safe(ss.allow_login_using_user_name):
		ss.allow_login_using_user_name = 1
		changed = True
	if changed:
		ss.save(ignore_permissions=True)

	if not frappe.db.exists("User", "Administrator"):
		return

	user = frappe.get_doc("User", "Administrator")
	user.enabled = 1
	user.send_welcome_email = 0
	if frappe.db.has_column("User", "username") and user.username != "admin":
		frappe.db.sql(
			"update `tabUser` set username=null where username=%s and name!=%s",
			("admin", "Administrator"),
		)
		user.username = "admin"
	user.save(ignore_permissions=True)

	# Seed demo password once so login form defaults work out of the box.
	if frappe.db.get_default("hr_pro_admin_login_seeded") != "1":
		update_password("Administrator", "admin")
		frappe.db.set_default("hr_pro_admin_login_seeded", "1")

	frappe.clear_cache()


def cint_safe(value) -> int:
	try:
		return 1 if int(value or 0) else 0
	except Exception:
		return 0
