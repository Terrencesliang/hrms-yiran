# Copyright (c) 2026 stillgroup
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document


class HRUserBusinessRole(Document):
	def validate(self):
		role_company = frappe.db.get_value("HR Business Role", self.business_role, "company")
		if role_company and self.company != role_company:
			frappe.throw(_("账号所属企业必须与角色所属企业一致"))
		duplicate = frappe.db.exists(
			"HR User Business Role",
			{
				"user": self.user,
				"business_role": self.business_role,
				"company": self.company,
				"enabled": 1,
			},
		)
		if duplicate and duplicate != self.name:
			frappe.throw(_("该账号已经拥有此角色"))

