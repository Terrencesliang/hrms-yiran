# Copyright (c) 2026 stillgroup
# License: MIT
"""把历史 `/app/roster` 侧栏入口迁移到唯一的 Employee 列表入口。"""

import frappe


def execute():
	for sidebar_name in ("HR Setup", "hr_roster"):
		if not frappe.db.exists("Sidebar", sidebar_name):
			continue
		doc = frappe.get_doc("Sidebar", sidebar_name)
		changed = False
		has_employee_entry = any(row.link_to == "Employee" for row in doc.items)
		for row in list(doc.items):
			if row.link_to != "roster":
				continue
			if has_employee_entry:
				doc.remove(row)
				changed = True
				continue
			row.label = "员工花名册"
			row.link_type = "DocType"
			row.link_to = "Employee"
			row.type = "Link"
			has_employee_entry = True
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
