# Copyright (c) 2026 stillgroup
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document


class HRBusinessRole(Document):
	def validate(self):
		self.role_title = (self.role_title or "").strip()
		if not self.role_title:
			frappe.throw(_("角色名称不能为空"))

		filters = {"role_title": self.role_title, "enabled": 1}
		if self.company:
			filters["company"] = self.company
		else:
			filters["company"] = ["is", "not set"]
		duplicate = frappe.db.exists("HR Business Role", filters)
		if duplicate and duplicate != self.name:
			frappe.throw(_("同一企业内不能存在同名角色"))

		seen = set()
		clean_rows = []
		for row in self.menu_permissions or []:
			key = (row.menu_key or "").strip()
			if not key or key in seen:
				continue
			seen.add(key)
			row.menu_key = key
			clean_rows.append(row)
		self.set("menu_permissions", clean_rows)

	def on_trash(self):
		if self.is_system_role:
			frappe.throw(_("系统角色不能删除"))
		if frappe.db.exists("HR User Business Role", {"business_role": self.name, "enabled": 1}):
			frappe.throw(_("该角色仍有账号使用，请先取消分配"))

