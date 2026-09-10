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


def _require_permission(doctype: str, permission_type: str = "read", doc=None) -> None:
	if frappe.session.user == "Guest" or not frappe.has_permission(doctype, permission_type, doc=doc):
		frappe.throw(_("您没有访问 {0} 的权限").format(_(doctype)), frappe.PermissionError)


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


def _is_intern_designation(designation: str | None) -> bool:
	"""职位为「实习生」视为实习生（按职位列精确匹配）。"""
	return (designation or "").strip() == "实习生"


def _build_stats(rows):
	status_counts = {}
	employment_counts = {}
	intern = 0
	fulltime = 0
	for row in rows:
		status = row.status or ""
		status_counts[status] = status_counts.get(status, 0) + 1
		if status == "Active" and getattr(row, "employment_type", None):
			employment_counts[row.employment_type] = employment_counts.get(row.employment_type, 0) + 1
		# 全职 / 实习生按在职员工的职位列统计，不依赖 employment_type
		if status == "Active":
			if _is_intern_designation(getattr(row, "designation", None)):
				intern += 1
			else:
				fulltime += 1

	employment_counts["Intern"] = intern
	employment_counts["Full-time"] = fulltime

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
def get_roster_data() -> dict:
	"""返回员工花名册数据：顶部统计 + 员工表格"""
	_require_permission("Employee")
	all_rows = frappe.get_list(
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
def update_employee_fields(employee: str, field: str, value: str) -> dict:
	"""双击编辑: 更新 Employee 记录的指定字段值 (仅允许白名单字段)."""
	allowed = {"cell_number", "group_name", "status"}
	if field not in allowed:
		frappe.throw(_("不允许编辑字段: {0}").format(field))

	doc = frappe.get_doc("Employee", employee)
	_require_permission("Employee", "write", doc=doc)
	if field == "group_name" and not frappe.db.has_column("Employee", "group_name"):
		frappe.throw(_("Employee 表无 group_name 字段"))
	doc.set(field, value or "")
	doc.save()
	return {"ok": True, "employee": employee, "field": field, "value": value}


@frappe.whitelist()
def search_employees(
	keyword: str | None = None, department: str | None = None, status: str | None = None
) -> list[dict]:
	"""搜索/筛选员工"""
	_require_permission("Employee")
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

	rows = frappe.get_list(
		"Employee",
		fields=_EMPLOYEE_FIELDS,
		filters=filters,
		or_filters=or_filters,
		order_by="employee_number asc",
		limit_page_length=None,
	)
	return [_serialize_row(r) for r in rows]


@frappe.whitelist()
def get_groups() -> list[str]:
	"""返回已存在的组别列表"""
	_require_permission("Employee")
	rows = frappe.get_list(
		"Employee",
		fields=["group_name"],
		filters=[["group_name", "is", "set"]],
		limit_page_length=None,
	)
	groups = {r.group_name for r in rows if r.group_name and r.group_name not in ("-", "(空)", "")}
	return sorted(groups)


@frappe.whitelist()
def get_departments() -> list[str]:
	"""返回部门列表"""
	_require_permission("Department")
	return frappe.get_list("Department", pluck="department_name", order_by="department_name asc")


@frappe.whitelist()
def get_employee_stats(company: str | None = None) -> dict:
	"""Employee 列表页顶部统计条数据（可按公司过滤）。"""
	_require_permission("Employee")
	filters = []
	if company:
		filters.append(["company", "=", company])

	rows = frappe.get_list(
		"Employee",
		fields=["status", "employment_type", "designation", "group_name"],
		filters=filters,
		limit_page_length=None,
	)
	return _build_stats(rows) if rows else _empty_stats()
