"""回填法大大合同企业参与方标识。"""
import frappe


def execute() -> None:
	if not (
		frappe.db.table_exists("Contract Signing")
		and frappe.db.table_exists("Contract Sign Template")
	):
		return
	company_by_template = {
		row.name: row.corp_actor_id
		for row in frappe.get_all(
			"Contract Sign Template",
			filters={"provider": "Fadada"},
			fields=["name", "corp_actor_id"],
		)
		if row.corp_actor_id
	}
	for row in frappe.get_all(
		"Contract Signing",
		filters={"provider": "Fadada"},
		fields=["name", "sign_template", "company_actor_id"],
	):
		if not row.company_actor_id and company_by_template.get(row.sign_template):
			frappe.db.set_value(
				"Contract Signing",
				row.name,
				"company_actor_id",
				company_by_template[row.sign_template],
				update_modified=False,
			)
