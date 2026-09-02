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

    # 建立父子关系 — 公司下一级部门（含总经办）并列展示，跳过 All Departments 容器
    ALL_DEPTS = "All Departments"
    roots = []
    for d in dept_rows:
        if d.disabled or d.name == ALL_DEPTS:
            continue
        node = nodes[d.name]
        p = d.parent_department
        if p and p in nodes and p != ALL_DEPTS:
            nodes[p]["children"].append(node)
        else:
            roots.append(node)

    roots.sort(key=lambda n: (n["title"] != "总经办", n["title"]))
    for node in nodes.values():
        node["children"].sort(key=lambda n: n["title"])

    company_title = frappe.db.get_value("Company", company, "company_name") if company else None
    company_title = company_title or company or "公司"
    total_emp = (
        frappe.db.count("Employee", filters={"status": "Active", "company": company}) or 0
        if company
        else sum(n["employee_count"] for n in roots)
    )

    company_root = {
        "name": f"__company__{company or 'default'}",
        "title": company_title,
        "is_group": True,
        "is_company": True,
        "employee_count": total_emp,
        "head_name": "",
        "children": roots,
    }

    return {
        "roots": [company_root],
        "total": len(nodes.values()),
        "company": company,
        "company_name": company_title,
    }


@frappe.whitelist()
def get_org_diagram(company: str | None = None):
    """返回可视化架构图数据：公司 → 部门 → 负责人 → 岗位编制。"""
    tree = get_org_tree(company)
    roots = tree.get("roots") or []
    if not roots:
        return {"company_name": "", "general_manager": "", "departments": []}

    company_node = roots[0]
    departments = []
    for dept in company_node.get("children") or []:
        departments.append(_build_diagram_department(dept, dept.get("title") or ""))

    departments.sort(key=lambda d: (d["title"] != "总经办", d["title"]))
    gm = _get_general_manager(tree.get("company"))
    return {
        "company_name": company_node.get("title") or tree.get("company_name") or "",
        "company_emp_count": company_node.get("employee_count") or 0,
        "general_manager": gm,
        "departments": departments,
    }


def _build_diagram_department(dept_node, dept_title):
    dept_names = _collect_dept_names(dept_node)
    manager_emp = _find_department_manager_employee(dept_names, dept_title)
    manager = _format_manager_label(dept_title, manager_emp)
    roles = _get_designation_counts(
        dept_names,
        exclude_names={manager_emp.get("employee_name")} if manager_emp else set(),
    )

    from collections import Counter

    role_counter = Counter()
    for role in roles:
        role_counter[role["title"]] += role["count"]

    merged_roles = [{"title": title, "count": count} for title, count in role_counter.items()]
    merged_roles.sort(key=lambda r: (-r["count"], r["title"]))

    return {
        "name": dept_node.get("name"),
        "title": dept_title or dept_node.get("title"),
        "employee_count": dept_node.get("employee_count") or 0,
        "manager": manager,
        "roles": merged_roles,
    }


def _find_department_manager_employee(dept_names, dept_title):
    rows = frappe.get_all(
        "Employee",
        filters=[["status", "=", "Active"], ["department", "in", dept_names]],
        fields=["name", "employee_name", "designation"],
        limit_page_length=None,
    )
    dept_hint = (dept_title or "").replace("部", "")
    best = None
    for row in rows:
        designation = (row.designation or "").strip()
        if not designation:
            continue
        if "经理" in designation or "主管" in designation or "负责人" in designation:
            score = 0
            if dept_title and dept_title in designation:
                score += 3
            if dept_hint and dept_hint in designation:
                score += 2
            if "经理" in designation:
                score += 1
            if not best or score > best["score"]:
                best = {"score": score, "employee_name": row.employee_name, "designation": designation}
    return best


def _format_manager_label(dept_title, manager_emp):
    if not manager_emp:
        return ""
    designation = manager_emp.get("designation") or ""
    name = manager_emp.get("employee_name") or ""
    if designation and name and name not in designation:
        return f"{designation} {name}"
    if designation:
        return designation
    if dept_title and name:
        return f"{dept_title}部经理 {name}"
    return name


def _get_designation_counts(dept_names, exclude_names=None):
    exclude_names = exclude_names or set()
    rows = frappe.get_all(
        "Employee",
        filters=[["status", "=", "Active"], ["department", "in", dept_names]],
        fields=["employee_name", "designation"],
        limit_page_length=None,
    )
    from collections import Counter

    counter = Counter()
    for row in rows:
        if row.employee_name in exclude_names:
            continue
        title = (row.designation or "").strip() or "未设置岗位"
        if "经理" in title and "部" in title:
            continue
        counter[title] += 1
    return [{"title": title, "count": count} for title, count in counter.items()]


def _get_department_manager(dept_names):
    manager = _find_department_manager_employee(dept_names, "")
    return _format_manager_label("", manager) if manager else ""


def _collect_dept_names(node):
    names = [node["name"]]
    for child in node.get("children") or []:
        names.extend(_collect_dept_names(child))
    return names


def _get_general_manager(company):
    if not company:
        return ""
    rows = frappe.get_all(
        "Employee",
        filters=[
            ["status", "=", "Active"],
            ["company", "=", company],
            ["designation", "like", "%总经理%"],
        ],
        fields=["employee_name", "designation"],
        limit=1,
    )
    if rows:
        row = rows[0]
        return f"{row.designation or '总经理'} {row.employee_name}".strip()
    return ""


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


ERPNext_DEFAULT_DEPARTMENTS = [
    "Accounts",
    "Marketing",
    "Sales",
    "Purchase",
    "Operations",
    "Production",
    "Dispatch",
    "Customer Service",
    "Human Resources",
    "Management",
    "Quality Management",
    "Research & Development",
    "Legal",
]


def disable_erpnext_default_departments():
    """禁用 ERPNext 创建公司时自带的英文空部门。"""
    disabled = []
    skipped = []

    for dept_name in ERPNext_DEFAULT_DEPARTMENTS:
        for row in frappe.get_all(
            "Department",
            filters={"department_name": dept_name, "disabled": 0},
            fields=["name", "department_name"],
        ):
            if frappe.db.count("Employee", {"department": row.name}):
                skipped.append(row.name)
                continue
            doc = frappe.get_doc("Department", row.name)
            doc.disabled = 1
            doc.save(ignore_permissions=True)
            disabled.append(doc.department_name)

    frappe.db.commit()
    return {"disabled": disabled, "skipped": skipped}

