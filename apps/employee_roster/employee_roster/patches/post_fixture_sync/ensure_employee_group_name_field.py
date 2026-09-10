# Copyright (c) 2026 stillgroup
# License: MIT
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field
from frappe.model.meta import get_meta


def execute():
	_ensure_custom_field()
	_ensure_db_column()


def _ensure_custom_field():
	name = "Employee-group_name"
	if frappe.db.exists("Custom Field", name):
		cf = frappe.get_doc("Custom Field", name)
		changed = False
		if cf.fieldtype != "Autocomplete":
			cf.fieldtype = "Autocomplete"
			changed = True
		if cf.label != "组别":
			cf.label = "组别"
			changed = True
		if changed:
			cf.flags.ignore_validate = True
			cf.save()
		return

	create_custom_field(
		"Employee",
		{
			"fieldname": "group_name",
			"label": "组别",
			"fieldtype": "Autocomplete",
			"insert_after": "department",
			"in_list_view": 1,
		},
		ignore_validate=True,
	)


def _ensure_db_column():
	if frappe.db.has_column("Employee", "group_name"):
		return

	meta = get_meta("Employee", cached=False)
	frappe.db.updatedb("Employee", meta)
	frappe.db.commit()
