# Copyright (c) 2026 stillgroup
# License: MIT
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.model.meta import get_meta

DEPARTMENT_ORG_FIELDS = [
	"org_code",
	"org_abbr",
	"org_type",
	"staff_quota",
	"effective_date",
	"department_head",
	"supervisor",
	"enable_cost_center",
	"org_remark",
]

COMPANY_ORG_FIELDS = ["org_head", "org_supervisor", "staff_quota"]


def get_org_custom_fields():
	return {
		"Department": [
			{
				"fieldname": "org_code",
				"label": "组织代码",
				"fieldtype": "Data",
				"insert_after": "department_name",
				"in_list_view": 1,
			},
			{
				"fieldname": "org_abbr",
				"label": "组织简称",
				"fieldtype": "Data",
				"insert_after": "org_code",
			},
			{
				"fieldname": "org_type",
				"label": "组织类型",
				"fieldtype": "Select",
				"options": "部门\n公司\n组",
				"default": "部门",
				"insert_after": "org_abbr",
			},
			{
				"fieldname": "staff_quota",
				"label": "编制人数",
				"fieldtype": "Int",
				"insert_after": "org_type",
			},
			{
				"fieldname": "effective_date",
				"label": "启用日期",
				"fieldtype": "Date",
				"insert_after": "staff_quota",
			},
			{
				"fieldname": "department_head",
				"label": "组织负责人",
				"fieldtype": "Link",
				"options": "Employee",
				"insert_after": "effective_date",
			},
			{
				"fieldname": "supervisor",
				"label": "分管领导",
				"fieldtype": "Link",
				"options": "Employee",
				"insert_after": "department_head",
			},
			{
				"fieldname": "enable_cost_center",
				"label": "启用费用中心类型",
				"fieldtype": "Check",
				"insert_after": "supervisor",
			},
			{
				"fieldname": "org_remark",
				"label": "备注",
				"fieldtype": "Small Text",
				"insert_after": "enable_cost_center",
			},
		],
		"Company": [
			{
				"fieldname": "org_head",
				"label": "组织负责人",
				"fieldtype": "Link",
				"options": "Employee",
				"insert_after": "company_name",
			},
			{
				"fieldname": "org_supervisor",
				"label": "分管领导",
				"fieldtype": "Link",
				"options": "Employee",
				"insert_after": "org_head",
			},
			{
				"fieldname": "staff_quota",
				"label": "编制人数",
				"fieldtype": "Int",
				"insert_after": "org_supervisor",
			},
		],
	}


def db_table_has_column(doctype: str, column: str) -> bool:
	"""Check the real database table, ignoring Frappe's stale table_columns cache."""
	table = f"tab{doctype}"
	cache = getattr(frappe.local, "_org_table_columns", None)
	if cache is None:
		cache = {}
		frappe.local._org_table_columns = cache
	if table not in cache:
		if getattr(frappe.db, "db_type", None) == "postgres":
			schema = getattr(frappe.db, "db_schema", None) or "public"
			cols = frappe.db.sql(
				"""
				SELECT column_name
				FROM information_schema.columns
				WHERE table_name = %s AND table_schema = %s
				""",
				(table, schema),
				pluck=True,
			)
		else:
			cols = frappe.db.sql(
				"""
				SELECT column_name
				FROM information_schema.columns
				WHERE table_name = %s AND table_schema = DATABASE()
				""",
				(table,),
				pluck=True,
			)
		cache[table] = {str(col).lower() for col in (cols or [])}
	return column.lower() in cache[table]


def ensure_org_custom_fields():
	create_custom_fields(get_org_custom_fields(), ignore_validate=True, update=True)
	for doctype in ("Department", "Company"):
		try:
			frappe.client_cache.delete_value(f"table_columns::tab{doctype}")
		except Exception:
			pass
		meta = get_meta(doctype, cached=False)
		frappe.db.updatedb(doctype, meta)
		try:
			frappe.client_cache.delete_value(f"table_columns::tab{doctype}")
		except Exception:
			pass
	frappe.clear_cache(doctype="Department")
	frappe.clear_cache(doctype="Company")
	frappe.db.commit()
