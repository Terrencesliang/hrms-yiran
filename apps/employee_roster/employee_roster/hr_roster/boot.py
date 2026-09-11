# Copyright (c) 2026 stillgroup
# License: MIT

import frappe


def boot_session(bootinfo):
	"""把首次改密状态放入当前会话，不向前端暴露其他用户数据。"""
	user = frappe.session.user
	bootinfo.hr_must_change_password = bool(
		user not in {"", "Guest"}
		and frappe.db.has_column("User", "hr_must_change_password")
		and frappe.db.get_value("User", user, "hr_must_change_password")
	)
