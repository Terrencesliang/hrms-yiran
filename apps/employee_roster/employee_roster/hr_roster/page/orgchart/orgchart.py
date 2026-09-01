# Copyright (c) 2026 stillgroup
# License: MIT
import frappe
from frappe.utils.nestedset import get_ancestors_of


def _get_all_company_names():
    return frappe.db.get_all("Company", pluck="name")


@frappe.whitelist()
def get_org_tree(company: str | None = None):
    """返回组织架构树形数据：Department 树 + 每节点员工数 / 负责人。
    返回结构: {root: {name, emp_count, children: [...]}}
    其中每节点: {name, title, is_group, employee_count, in_hand_count, head_name, children}
    """
    company = company or frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        companies = _get_all_company_names()
        company = companies[0] if companies else None

    # 取所有部门
    dept_rows = frappe.db.get_all(
        "Department",
        fields=["name", "department_name", "parent_department", "is_group", "lft", "rgt", "company", "disabled"],
        order_by="lft asc",
        limit_page_length=None,
    )
    if not dept_rows:
        return {"roots": [], "total": 0}

    # 构建 name -> node
    nodes = {}
    for d in dept_rows:
        if d.disabled:
            continue
        # 统计该部门(含子部门)员工数
        dept_names_under = _dept_names_under(d.name, dept_rows)
        emp_count = frappe.db.count(
            "Employee",
            filters=[["status", "=", "Active"], ["department", "in", dept_names_under]],
        ) or 0
        head = _get_head_name(d.name, dept_names_under)
        nodes[d.name] = {
            "name": d.name,
            "title": d.department_name,
            "is_group": bool(d.is_group),
            "parent_department": d.parent_department,
            "employee_count": emp_count,
            "head_name": head,
            "children": [],
        }

    # 建立父子关系
    roots = []
    for d in dept_rows:
        if d.disabled:
            continue
        node = nodes[d.name]
        p = d.parent_department
        if p and p in nodes:
            nodes[p]["children"].append(node)
        else:
            roots.append(node)

    # 视觉根: 以「总经办」为根, 跳过 All Departments 聚合容器
    ZJ = "总经办 - 依然电商"
    if ZJ in nodes:
        roots = [nodes[ZJ]]
    else:
        roots.sort(key=lambda n: (n["name"] != ZJ, n["name"]))

    for node in nodes.values():
        node["children"].sort(key=lambda n: (n["name"] != ZJ, n["name"]))

    return {"roots": roots, "total": len([n for n in nodes.values()])}


def _dept_names_under(dept_name, all_rows):
    """返回 dept_name 及其所有子部门的 name 列表(基于 lft/rgt)."""
    target = None
    for r in all_rows:
        if r.name == dept_name:
            target = r
            break
    if not target:
        return [dept_name]
    res = []
    for r in all_rows:
        if r.lft >= target.lft and r.rgt <= target.rgt:
            res.append(r.name)
    return res or [dept_name]


def _get_head_name(dept_name, dept_names_under):
    """尝试推断负责人: 部门内 reports_to 指向本部门员工的、被指向次数最多的员工."""
    try:
        # 找该部门下有 reports_to 的员工
        emp_rows = frappe.db.get_all(
            "Employee",
            fields=["name", "employee_name", "reports_to", "department"],
            filters=[["status", "=", "Active"], ["department", "in", dept_names_under]],
            limit_page_length=None,
        )
        if not emp_rows:
            return ""
        # 统计每个被 reports_to 指向的上级出现的次数
        from collections import Counter
        cnt = Counter()
        for e in emp_rows:
            if e.reports_to:
                cnt[e.reports_to] += 1
        if not cnt:
            return ""
        top = cnt.most_common(1)[0][0]
        # top 可能是 doctype 名 ref, 找员工名
        emp_name = frappe.db.get_value("Employee", top, "employee_name") if top else ""
        return emp_name or top
    except Exception:
        return ""
