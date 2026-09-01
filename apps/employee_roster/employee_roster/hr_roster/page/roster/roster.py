# Copyright (c) 2026 stillgroup
# License: MIT. See LICENSE
import frappe
from frappe import _

_EMPLOYEE_FIELDS = [
	"name",
	"employee_name",
	"employee_number",
	"department",
	"designation",
	"employment_type",
	"date_of_joining",
	"branch",
	"status",
	"group_name",
	"cell_number",
]


def _serialize_row(row):
	return {
		"name": row.name,
		"employee_name": row.employee_name,
		"employee_number": row.employee_number,
		"department": row.department,
		"designation": row.designation,
		"employment_type": row.employment_type or "",
		"date_of_joining": row.date_of_joining,
		"branch": row.branch,
		"group_name": row.group_name if row.group_name and row.group_name not in ("-", "(空)") else "",
		"cell_number": row.cell_number or "",
		"status": row.status or "",
	}


def _build_stats(rows):
	status_counts = {}
	employment_counts = {}
	for row in rows:
		status = row.status or ""
		status_counts[status] = status_counts.get(status, 0) + 1
		if status == "Active" and row.employment_type:
			employment_counts[row.employment_type] = employment_counts.get(row.employment_type, 0) + 1

	group_counts = {}
	for row in rows:
		if row.group_name and row.group_name not in ("-", "(空)", ""):
			group_counts[row.group_name] = group_counts.get(row.group_name, 0) + 1

	return {
		"total": len(rows),
		"active": status_counts.get("Active", 0),
		"left": status_counts.get("Left", 0),
		"inactive": status_counts.get("Inactive", 0),
		"suspended": status_counts.get("Suspended", 0),
		"status_counts": status_counts,
		"group_counts": group_counts,
		"employment_counts": employment_counts,
	}


@frappe.whitelist()
def get_roster_data():
	"""返回员工花名册数据：顶部统计 + 员工表格"""
	all_rows = frappe.db.get_all(
		"Employee",
		fields=_EMPLOYEE_FIELDS,
		order_by="employee_number asc",
		limit_page_length=None,
	)
	if not all_rows:
		return {"tables": [], "stats": _empty_stats()}

	return {
		"tables": [_serialize_row(r) for r in all_rows],
		"stats": _build_stats(all_rows),
	}


def _empty_stats():
	return {
		"total": 0,
		"active": 0,
		"left": 0,
		"inactive": 0,
		"suspended": 0,
		"status_counts": {},
		"group_counts": {},
		"employment_counts": {},
	}


@frappe.whitelist()
def update_employee_fields(employee: str, field: str, value: str):
	"""双击编辑: 更新 Employee 记录的指定字段值 (仅允许白名单字段)."""
	allowed = {"cell_number", "group_name", "status"}
	if field not in allowed:
		frappe.throw(_("不允许编辑字段: {0}").format(field))

	if field == "group_name":
		if not frappe.db.has_column("Employee", "group_name"):
			frappe.throw(_("Employee 表无 group_name 字段"))
		frappe.db.set_value("Employee", employee, "group_name", value or "")
	else:
		frappe.db.set_value("Employee", employee, field, value or "")

	frappe.db.commit()
	return {"ok": True, "employee": employee, "field": field, "value": value}


@frappe.whitelist()
def search_employees(keyword: str | None = None, department: str | None = None, status: str | None = None):
	"""搜索/筛选员工"""
	filters = []
	if department:
		filters.append(["department", "=", department])
	if status:
		filters.append(["status", "=", status])

	or_filters = []
	if keyword:
		kw = f"%{keyword}%"
		or_filters = [
			["employee_name", "like", kw],
			["cell_number", "like", kw],
			["employee_number", "like", kw],
		]

	rows = frappe.db.get_all(
		"Employee",
		fields=_EMPLOYEE_FIELDS,
		filters=filters,
		or_filters=or_filters,
		order_by="employee_number asc",
		limit_page_length=None,
	)
	return [_serialize_row(r) for r in rows]


@frappe.whitelist()
def get_groups():
	"""返回已存在的组别列表"""
	rows = frappe.db.get_all(
		"Employee",
		fields=["group_name"],
		filters=[["group_name", "is", "set"]],
		limit_page_length=None,
	)
	groups = {r.group_name for r in rows if r.group_name and r.group_name not in ("-", "(空)", "")}
	return sorted(groups)


@frappe.whitelist()
def get_departments():
	"""返回部门列表"""
	return frappe.db.get_all("Department", pluck="department_name", order_by="department_name asc")


@frappe.whitelist()
def get_employee_stats(company: str | None = None):
	"""Employee 列表页顶部统计条数据（可按公司过滤）。"""
	filters = []
	if company:
		filters.append(["company", "=", company])

	rows = frappe.db.get_all(
		"Employee",
		fields=["status", "employment_type", "group_name"],
		filters=filters,
		limit_page_length=None,
	)
	return _build_stats(rows) if rows else _empty_stats()
