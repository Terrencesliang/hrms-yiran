# -*- coding: utf-8 -*-
import frappe
from frappe.query_builder.functions import Count

@frappe.whitelist()
def get_children(parent: str | None = None, company: str | None = None, exclude_node: str | None = None):
	"""返回部门组织架构树的子节点, 供 HierarchyChart 渲染。
	根节点(parent 为空)时返回公司下一级部门（含总经办，并列展示）。
	"""
	Department = frappe.qb.DocType("Department")

	query = frappe.qb.from_(Department).select(
		Department.department_name.as_("name"),
		Department.name.as_("id"),
		Department.lft,
		Department.rgt,
		Department.is_group,
	).where(Department.disabled == 0)

	# 判断 parent 是否为根调用
	if parent and parent.strip() and parent != "All Departments":
		query = query.where(Department.parent_department == parent)
	elif not parent or parent == "All Departments":
		# 根调用: 返回 All Departments 下的一级部门
		query = query.where(Department.parent_department == "All Departments")

	if exclude_node:
		query = query.where(Department.name != exclude_node)

	if company and company != "All Companies":
		query = query.where(Department.company == company)

	query = query.orderby(Department.lft)
	departments = query.run(as_dict=True)

	for dept in departments:
		dept.title = get_employee_count(dept.id)
		child_count = get_child_department_count(dept.id, dept.lft, dept.rgt)
		dept.connections = child_count
		dept.expandable = bool(child_count)

	return departments


@frappe.whitelist()
def get_employee_count(department: str | None = None) -> int:
	"""统计某部门(含其子部门)内所有在职员工数."""
	Department = frappe.qb.DocType("Department")
	Employee = frappe.qb.DocType("Employee")

	if not department:
		return frappe.db.count("Employee", filters={"status": "Active"})

	# 用 lft/rgt 捕获该部门及全部子部门
	dept = frappe.db.get_value("Department", department, ["lft", "rgt"], as_dict=True)
	if not dept:
		return 0

	sub_dept_names = (
		frappe.qb.from_(Department)
		.select(Department.name)
		.where((Department.lft >= dept.lft) & (Department.rgt <= dept.rgt))
	).run(as_list=True)
	names = [r[0] for r in sub_dept_names] or [department]

	return frappe.db.count(
		"Employee",
		filters=[["status", "=", "Active"], ["department", "in", names]],
	)


@frappe.whitelist()
def get_child_department_count(dept: str, lft: int, rgt: int) -> int:
	Department = frappe.qb.DocType("Department")
	query = (
		frappe.qb.from_(Department)
		.select(Count(Department.name))
		.where((Department.lft > lft) & (Department.rgt < rgt) & (Department.disabled == 0))
	).run()
	return query[0][0]
