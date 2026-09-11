# Copyright (c) 2026 stillgroup
# License: MIT

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"User": [
				{
					"fieldname": "hr_must_change_password",
					"label": "首次登录需修改密码",
					"fieldtype": "Check",
					"default": "0",
					"hidden": 1,
					"insert_after": "last_password_reset_date",
				}
			]
		},
		update=True,
	)
	frappe.db.set_single_value("System Settings", "allow_login_using_user_name", 1)
	from employee_roster.hr_roster.account_service import provision_existing_employee_accounts

	provision_existing_employee_accounts()
