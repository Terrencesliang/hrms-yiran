"""Enable username login and ensure admin/admin maps to Administrator."""

from __future__ import annotations

import frappe
from frappe.utils.password import check_password, update_password


def execute():
	# 1) System Settings: allow login with username
	ss = frappe.get_single("System Settings")
	ss.allow_login_using_user_name = 1
	# Keep email login path usable when name==email for other users
	if hasattr(ss, "allow_login_using_mobile_number"):
		# leave as-is
		pass
	ss.save(ignore_permissions=True)

	# 2) Administrator profile
	has_username = frappe.db.has_column("User", "username")
	user = frappe.get_doc("User", "Administrator")
	user.enabled = 1
	user.send_welcome_email = 0
	if has_username:
		frappe.db.sql(
			"update `tabUser` set username=null where username=%s and name!=%s",
			("admin", "Administrator"),
		)
		user.username = "admin"
	user.save(ignore_permissions=True)

	# 3) Password
	update_password("Administrator", "admin")
	frappe.db.commit()

	# Clear settings cache so login sees the new flag immediately
	frappe.clear_cache()
	frappe.db.commit()

	# 4) Verify credential path
	from frappe.core.doctype.user.user import User

	found = User.find_by_credentials("admin", "admin")
	check_password("Administrator", "admin")

	print(
		{
			"allow_login_using_user_name": frappe.get_system_settings("allow_login_using_user_name"),
			"username": frappe.db.get_value("User", "Administrator", "username"),
			"find_by_credentials": found,
			"password_ok": True,
		}
	)
