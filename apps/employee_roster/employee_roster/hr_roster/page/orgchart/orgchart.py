# Copyright (c) 2026 stillgroup
# License: MIT
import csv
import io
from collections import Counter, defaultdict

import frappe
from frappe import _
from frappe.utils import cint, getdate, today

from employee_roster.hr_roster.org_fields import (
	COMPANY_ORG_FIELDS,
	DEPARTMENT_ORG_FIELDS,
	db_table_has_column,
)

ALL_DEPTS = "All Departments"
NON_FULLTIME_TYPES = {"Part-time", "Intern", "Contract"}
ORG_TYPES = ("部门", "公司", "组")
COMPANY_PREFIX = "__company__"


def _get_all_company_names():
	return frappe.db.get_all("Company", pluck="name")


def _resolve_company(company: str | None = None) -> str | None:
	company = company or frappe.db.get_single_value("Global Defaults", "default_company")
	if company:
		return company
	companies = _get_all_company_names()
	return companies[0] if companies else None


def _has_dept_org_fields() -> bool:
	return db_table_has_column("Department", "org_code")


def _has_company_org_fields() -> bool:
	return db_table_has_column("Company", "org_head")


def _company_id(company: str | None) -> str:
	return f"{COMPANY_PREFIX}{company or 'default'}"


def _is_company_node(name: str | None) -> bool:
	return bool(name) and str(name).startswith(COMPANY_PREFIX)


def _is_all_departments(row) -> bool:
	return (row.department_name or "") == ALL_DEPTS or (row.name or "") == ALL_DEPTS


@frappe.whitelist()
def get_org_tree(company: str | None = None):
	"""返回组织架构树形数据：Department 树 + 每节点员工数 / 负责人。"""
	company = _resolve_company(company)
	dept_fields = [
		"name",
		"department_name",
		"parent_department",
		"is_group",
		"lft",
		"rgt",
		"company",
		"disabled",
	]
	if _has_dept_org_fields():
		dept_fields.extend(DEPARTMENT_ORG_FIELDS)

	filters = {"disabled": 0}

	dept_rows = frappe.db.get_all(
		"Department",
		fields=dept_fields,
		filters=filters,
		order_by="lft asc",
		limit_page_length=None,
	)
	if not dept_rows:
		return _empty_tree(company)

	emp_by_dept, emp_name_map, company_emps = _load_active_employees(company)
	nodes = {}
	for d in dept_rows:
		if _is_all_departments(d):
			continue
		if company and d.company and d.company != company:
			continue
		head_id = getattr(d, "department_head", None) if _has_dept_org_fields() else None
		supervisor_id = getattr(d, "supervisor", None) if _has_dept_org_fields() else None
		nodes[d.name] = {
			"name": d.name,
			"title": d.department_name,
			"is_group": bool(d.is_group),
			"parent_department": d.parent_department,
			"org_code": getattr(d, "org_code", "") or "",
			"org_abbr": getattr(d, "org_abbr", "") or "",
			"org_type": getattr(d, "org_type", None) or "部门",
			"staff_quota": cint(getattr(d, "staff_quota", 0) or 0),
			"effective_date": str(getattr(d, "effective_date", "") or ""),
			"department_head": head_id or "",
			"supervisor": supervisor_id or "",
			"enable_cost_center": cint(getattr(d, "enable_cost_center", 0) or 0),
			"org_remark": getattr(d, "org_remark", "") or "",
			"own_employee_count": 0,
			"own_parttime_count": 0,
			"employee_count": 0,
			"parttime_count": 0,
			"head_name": emp_name_map.get(head_id, "") if head_id else "",
			"supervisor_name": emp_name_map.get(supervisor_id, "") if supervisor_id else "",
			"children": [],
		}

	roots = []
	for d in dept_rows:
		if _is_all_departments(d) or d.name not in nodes:
			continue
		node = nodes[d.name]
		parent = d.parent_department
		if parent and parent in nodes:
			nodes[parent]["children"].append(node)
		else:
			roots.append(node)

	roots.sort(key=lambda n: (n["title"] != "总经办", n["title"]))
	for node in nodes.values():
		node["children"].sort(key=lambda n: n["title"])
		if not node["head_name"]:
			node["head_name"] = _infer_head_name(node["name"], nodes, emp_by_dept, emp_name_map)

	emp_by_org, orphan_emps = _bucket_members(company_emps, nodes)
	for name, node in nodes.items():
		own_emps = emp_by_org.get(name) or []
		node["own_employee_count"] = len(own_emps)
		node["own_parttime_count"] = sum(1 for e in own_emps if e["employment_type"] in NON_FULLTIME_TYPES)

	for root in roots:
		_roll_up_counts(root)

	_attach_members(nodes, emp_by_org)

	company_title, company_abbr, company_meta = _company_meta(company, emp_name_map)
	total_emp = len(company_emps)
	total_parttime = sum(1 for e in company_emps if e["employment_type"] in NON_FULLTIME_TYPES)
	if not company:
		total_emp = sum(n["employee_count"] for n in roots)
		total_parttime = sum(n["parttime_count"] for n in roots)

	company_root = {
		"name": _company_id(company),
		"title": company_title,
		"is_group": True,
		"is_company": True,
		"org_code": "",
		"org_abbr": company_abbr,
		"org_type": "公司",
		"staff_quota": company_meta.get("staff_quota") or 0,
		"department_head": company_meta.get("org_head") or "",
		"supervisor": company_meta.get("org_supervisor") or "",
		"employee_count": total_emp,
		"parttime_count": total_parttime,
		"head_name": company_meta.get("head_name") or "",
		"supervisor_name": company_meta.get("supervisor_name") or "",
		"children": roots + [_member_node(e) for e in orphan_emps],
	}

	companies = frappe.get_all(
		"Company",
		fields=["name", "company_name", "abbr"],
		order_by="company_name asc",
	)
	return {
		"roots": [company_root],
		"total": len(nodes),
		"company": company,
		"company_name": company_title,
		"company_abbr": company_abbr,
		"companies": companies,
	}


def _empty_tree(company: str | None):
	company_title, company_abbr, _meta = _company_meta(company, {})
	companies = frappe.get_all("Company", fields=["name", "company_name", "abbr"], order_by="company_name asc")
	return {
		"roots": [
			{
				"name": _company_id(company),
				"title": company_title,
				"is_group": True,
				"is_company": True,
				"org_type": "公司",
				"staff_quota": 0,
				"employee_count": 0,
				"parttime_count": 0,
				"head_name": "",
				"supervisor_name": "",
				"children": [],
			}
		],
		"total": 0,
		"company": company,
		"company_name": company_title,
		"company_abbr": company_abbr,
		"companies": companies,
	}


def _company_meta(company: str | None, emp_name_map: dict) -> tuple[str, str, dict]:
	if not company:
		return "公司", "", {}
	fields = ["company_name", "abbr"]
	if _has_company_org_fields():
		fields.extend(COMPANY_ORG_FIELDS)
	row = frappe.db.get_value("Company", company, fields, as_dict=True) or {}
	org_head = row.get("org_head") or ""
	org_supervisor = row.get("org_supervisor") or ""
	return (
		row.get("company_name") or company,
		row.get("abbr") or "",
		{
			"org_head": org_head,
			"org_supervisor": org_supervisor,
			"staff_quota": cint(row.get("staff_quota") or 0),
			"head_name": emp_name_map.get(org_head, "") if org_head else "",
			"supervisor_name": emp_name_map.get(org_supervisor, "") if org_supervisor else "",
		},
	)


def _load_active_employees(company: str | None):
	filters = {"status": "Active"}
	if company:
		filters["company"] = company
	fields = [
		"name",
		"employee_name",
		"employee_number",
		"department",
		"designation",
		"employment_type",
		"reports_to",
	]
	if frappe.db.has_column("Employee", "group_name"):
		fields.append("group_name")
	rows = frappe.get_all(
		"Employee",
		filters=filters,
		fields=fields,
		limit_page_length=None,
	)
	by_dept = defaultdict(list)
	name_map = {}
	items = []
	for row in rows:
		item = {
			"name": row.name,
			"employee_name": row.employee_name,
			"employee_number": row.employee_number or "",
			"designation": row.designation or "",
			"employment_type": row.employment_type or "",
			"reports_to": row.reports_to,
			"department": row.department,
			"group_name": _clean_group_name(getattr(row, "group_name", None)),
		}
		items.append(item)
		if row.department:
			by_dept[row.department].append(item)
		name_map[row.name] = row.employee_name
	return by_dept, name_map, items


def _clean_group_name(value: str | None) -> str:
	name = (value or "").strip()
	if name in ("", "-", "(空)"):
		return ""
	return name


def _org_descendant_ids(node: dict) -> set[str]:
	ids = {node["name"]}
	for child in node.get("children") or []:
		if child.get("is_employee"):
			continue
		ids |= _org_descendant_ids(child)
	return ids


def _resolve_member_parent(emp: dict, nodes: dict) -> str | None:
	"""优先挂到花名册组别对应的下级组织，否则挂到部门。"""
	dept_id = emp.get("department")
	group = emp.get("group_name") or ""
	dept_node = nodes.get(dept_id) if dept_id else None

	if group:
		candidates = [n for n in nodes.values() if n.get("title") == group]
		if dept_node:
			allowed = _org_descendant_ids(dept_node)
			nested = [n for n in candidates if n["name"] in allowed]
			if nested:
				return nested[0]["name"]
		elif len(candidates) == 1:
			return candidates[0]["name"]

	if dept_id in nodes:
		return dept_id
	return None


def _bucket_members(company_emps: list, nodes: dict) -> tuple[dict, list]:
	by_org = defaultdict(list)
	orphans = []
	for emp in company_emps:
		parent = _resolve_member_parent(emp, nodes)
		if parent:
			by_org[parent].append(emp)
		else:
			orphans.append(emp)
	orphans.sort(key=lambda e: ((e.get("employee_name") or ""), e["name"]))
	return by_org, orphans


def _member_node(emp: dict) -> dict:
	return {
		"name": f"__emp__{emp['name']}",
		"employee": emp["name"],
		"title": emp.get("employee_name") or emp["name"],
		"is_employee": True,
		"org_type": "员工",
		"org_code": emp.get("employee_number") or "",
		"designation": emp.get("designation") or "",
		"employment_type": emp.get("employment_type") or "",
		"employee_number": emp.get("employee_number") or "",
		"employee_count": 0,
		"parttime_count": 0,
		"staff_quota": 0,
		"head_name": emp.get("designation") or "",
		"supervisor_name": "",
	}


def _attach_members(nodes: dict, emp_by_org: dict) -> None:
	for name, node in nodes.items():
		members = sorted(
			emp_by_org.get(name) or [],
			key=lambda e: ((e.get("employee_name") or ""), e["name"]),
		)
		if not members:
			continue
		node["children"] = (node.get("children") or []) + [_member_node(e) for e in members]


def _roll_up_counts(node: dict) -> None:
	emp = node.get("own_employee_count") or 0
	part = node.get("own_parttime_count") or 0
	for child in node.get("children") or []:
		_roll_up_counts(child)
		emp += child.get("employee_count") or 0
		part += child.get("parttime_count") or 0
	node["employee_count"] = emp
	node["parttime_count"] = part


def _collect_descendant_names(node: dict) -> list[str]:
	names = [node["name"]]
	for child in node.get("children") or []:
		names.extend(_collect_descendant_names(child))
	return names


def _infer_head_name(dept_name: str, nodes: dict, emp_by_dept: dict, emp_name_map: dict) -> str:
	node = nodes.get(dept_name)
	if not node:
		return ""
	names = _collect_descendant_names(node)
	cnt = Counter()
	for name in names:
		for emp in emp_by_dept.get(name) or []:
			if emp.get("reports_to"):
				cnt[emp["reports_to"]] += 1
	if not cnt:
		return ""
	top = cnt.most_common(1)[0][0]
	return emp_name_map.get(top) or ""


@frappe.whitelist()
def search_employees(txt: str | None = None, company: str | None = None) -> list[dict]:
	txt = (txt or "").strip()
	filters = {"status": "Active"}
	if company:
		filters["company"] = company
	or_filters = None
	if txt:
		or_filters = {
			"employee_name": ["like", f"%{txt}%"],
			"name": ["like", f"%{txt}%"],
			"employee_number": ["like", f"%{txt}%"],
		}
	rows = frappe.get_all(
		"Employee",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "employee_name", "department", "designation"],
		limit_page_length=20,
		order_by="employee_name asc",
	)
	return [
		{
			"name": row.name,
			"employee_name": row.employee_name,
			"department": row.department or "",
			"designation": row.designation or "",
		}
		for row in rows
	]


@frappe.whitelist()
def create_org_unit(
	title: str,
	company: str | None = None,
	parent: str | None = None,
	org_code: str | None = None,
	org_abbr: str | None = None,
	org_type: str | None = None,
	department_head: str | None = None,
	supervisor: str | None = None,
	staff_quota: int | str | None = None,
	effective_date: str | None = None,
	enable_cost_center: int | str | None = None,
	org_remark: str | None = None,
) -> dict:
	if not frappe.has_permission("Department", "create"):
		frappe.throw(_("没有权限新增组织"), frappe.PermissionError)

	title = (title or "").strip()
	if not title:
		frappe.throw(_("组织名称不能为空"))

	company = _resolve_company(company)
	if not company:
		frappe.throw(_("请先设置默认公司"))

	org_type = (org_type or "部门").strip()
	if org_type not in ORG_TYPES:
		org_type = "部门"

	parent_name = _resolve_parent(parent, company)
	_ensure_parent_is_group(parent_name)

	if org_code and _has_dept_org_fields() and frappe.db.exists("Department", {"org_code": org_code}):
		frappe.throw(_("组织代码已存在"))

	doc = frappe.new_doc("Department")
	doc.department_name = title
	doc.company = company
	doc.parent_department = parent_name
	doc.is_group = 1
	doc.disabled = 0
	if _has_dept_org_fields():
		doc.org_code = (org_code or "").strip()
		doc.org_abbr = (org_abbr or "").strip()
		doc.org_type = org_type
		doc.department_head = department_head or None
		doc.supervisor = supervisor or None
		doc.staff_quota = cint(staff_quota or 0) or None
		doc.effective_date = getdate(effective_date) if effective_date else getdate(today())
		doc.enable_cost_center = 1 if cint(enable_cost_center) else 0
		doc.org_remark = (org_remark or "").strip()
	doc.insert()
	return {"name": doc.name, "title": doc.department_name}


@frappe.whitelist()
def update_org_person(org_name: str, role: str, employee: str | None = None) -> dict:
	role = (role or "").strip()
	employee = (employee or "").strip() or None
	if role not in ("head", "supervisor"):
		frappe.throw(_("非法字段"))

	if _is_company_node(org_name):
		company = org_name.replace(COMPANY_PREFIX, "", 1)
		if not frappe.has_permission("Company", "write"):
			frappe.throw(_("没有权限修改公司信息"), frappe.PermissionError)
		if not _has_company_org_fields():
			frappe.throw(_("请先执行 migrate 以启用组织字段"))
		field = "org_head" if role == "head" else "org_supervisor"
		frappe.db.set_value("Company", company, field, employee)
		return {
			"name": org_name,
			"role": role,
			"employee": employee or "",
			"employee_name": frappe.db.get_value("Employee", employee, "employee_name") if employee else "",
		}

	if not frappe.has_permission("Department", "write"):
		frappe.throw(_("没有权限修改组织"), frappe.PermissionError)
	if not _has_dept_org_fields():
		frappe.throw(_("请先执行 migrate 以启用组织字段"))
	field = "department_head" if role == "head" else "supervisor"
	frappe.db.set_value("Department", org_name, field, employee)
	return {
		"name": org_name,
		"role": role,
		"employee": employee or "",
		"employee_name": frappe.db.get_value("Employee", employee, "employee_name") if employee else "",
	}


@frappe.whitelist()
def get_org_import_template() -> dict:
	header = "组织名称,组织代码,组织简称,组织类型,上级组织,组织负责人,编制人数,启用日期"
	sample = "示例组,DEMO01,示例,部门,总经办,,5," + today()
	return {
		"filename": "org_import_template.csv",
		"content": f"{header}\n{sample}\n",
	}


@frappe.whitelist()
def import_org_units(file_url: str, company: str | None = None) -> dict:
	if not frappe.has_permission("Department", "create"):
		frappe.throw(_("没有权限导入组织"), frappe.PermissionError)
	if not file_url:
		frappe.throw(_("请上传 CSV 文件"))

	company = _resolve_company(company)
	rows = _read_attached_csv(file_url)
	created = 0
	updated = 0
	skipped = []
	for idx, row in enumerate(rows, start=2):
		title = (row.get("组织名称") or row.get("title") or "").strip()
		if not title:
			skipped.append({"row": idx, "reason": _("组织名称不能为空")})
			continue
		try:
			org_code = (row.get("组织代码") or row.get("org_code") or "").strip()
			existing = _find_existing_department(title, org_code, company)
			payload = {
				"org_code": org_code,
				"org_abbr": (row.get("组织简称") or row.get("org_abbr") or "").strip(),
				"org_type": (row.get("组织类型") or row.get("org_type") or "部门").strip() or "部门",
				"parent": (row.get("上级组织") or row.get("parent") or "").strip(),
				"department_head": _resolve_employee_by_name(
					(row.get("组织负责人") or row.get("department_head") or "").strip(),
					company,
				),
				"staff_quota": row.get("编制人数") or row.get("staff_quota") or 0,
				"effective_date": (row.get("启用日期") or row.get("effective_date") or "").strip(),
			}
			if existing:
				_update_existing_department(existing, payload, company)
				updated += 1
			else:
				create_org_unit(
					title=title,
					company=company,
					parent=_resolve_parent_label(payload["parent"], company),
					org_code=payload["org_code"],
					org_abbr=payload["org_abbr"],
					org_type=payload["org_type"],
					department_head=payload["department_head"],
					staff_quota=payload["staff_quota"],
					effective_date=payload["effective_date"] or today(),
				)
				created += 1
		except Exception as exc:
			skipped.append({"row": idx, "reason": str(exc)})
	return {"created": created, "updated": updated, "skipped": skipped, "total": len(rows)}


def _read_attached_csv(file_url: str) -> list[dict]:
	file_doc = frappe.get_doc("File", {"file_url": file_url})
	content = file_doc.get_content()
	if isinstance(content, bytes):
		content = content.decode("utf-8-sig")
	else:
		content = (content or "").lstrip("\ufeff")
	reader = csv.DictReader(io.StringIO(content))
	return [row for row in reader if any((value or "").strip() for value in row.values())]


def _find_existing_department(title: str, org_code: str, company: str | None):
	if org_code and _has_dept_org_fields():
		name = frappe.db.get_value("Department", {"org_code": org_code}, "name")
		if name:
			return name
	filters = {"department_name": title}
	if company:
		filters["company"] = company
	return frappe.db.get_value("Department", filters, "name")


def _update_existing_department(name: str, payload: dict, company: str | None) -> None:
	doc = frappe.get_doc("Department", name)
	if payload.get("parent"):
		doc.parent_department = _resolve_parent_label(payload["parent"], company) or doc.parent_department
	if _has_dept_org_fields():
		if payload.get("org_code"):
			doc.org_code = payload["org_code"]
		if payload.get("org_abbr"):
			doc.org_abbr = payload["org_abbr"]
		if payload.get("org_type"):
			doc.org_type = payload["org_type"]
		if payload.get("department_head"):
			doc.department_head = payload["department_head"]
		if payload.get("staff_quota") not in (None, ""):
			doc.staff_quota = cint(payload["staff_quota"])
		if payload.get("effective_date"):
			doc.effective_date = getdate(payload["effective_date"])
	doc.save()


def _resolve_employee_by_name(label: str, company: str | None) -> str | None:
	if not label:
		return None
	filters = {"employee_name": label, "status": "Active"}
	if company:
		filters["company"] = company
	return frappe.db.get_value("Employee", filters, "name") or frappe.db.get_value("Employee", label, "name")


def _resolve_parent_label(label: str, company: str | None) -> str | None:
	if not label:
		return _all_departments_for(company)
	if _is_company_node(label):
		return _all_departments_for(company)
	company_title = frappe.db.get_value("Company", company, "company_name") if company else None
	if label in {company, company_title}:
		return _all_departments_for(company)
	found = frappe.db.get_value("Department", {"department_name": label, "company": company}, "name") if company else None
	if found:
		return found
	if frappe.db.exists("Department", label):
		return label
	return _all_departments_for(company)


def _resolve_parent(parent: str | None, company: str | None) -> str:
	if not parent or _is_company_node(parent):
		return _all_departments_for(company)
	return parent


def _all_departments_for(company: str | None) -> str:
	if frappe.db.exists("Department", ALL_DEPTS):
		return ALL_DEPTS
	if company:
		abbr = frappe.get_cached_value("Company", company, "abbr")
		candidate = f"{ALL_DEPTS} - {abbr}"
		if abbr and frappe.db.exists("Department", candidate):
			return candidate
		found = frappe.db.get_value(
			"Department",
			{"department_name": ALL_DEPTS, "company": company},
			"name",
		)
		if found:
			return found
	frappe.throw(_("找不到公司根组织（All Departments），请先在部门中维护根节点"))
	return ALL_DEPTS


def _ensure_parent_is_group(parent_name: str) -> None:
	if not parent_name or not frappe.db.exists("Department", parent_name):
		return
	if not cint(frappe.db.get_value("Department", parent_name, "is_group")):
		frappe.db.set_value("Department", parent_name, "is_group", 1)


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
		if dept.get("is_employee"):
			continue
		departments.append(_build_diagram_department(dept, dept.get("title") or ""))

	departments.sort(key=lambda d: (d["title"] != "总经办", d["title"]))
	gm_info = _get_general_manager_info(tree.get("company"))
	return {
		"company": tree.get("company") or company,
		"company_name": company_node.get("title") or tree.get("company_name") or "",
		"company_emp_count": company_node.get("employee_count") or 0,
		"general_manager": gm_info.get("label") or "",
		"general_manager_info": gm_info,
		"companies": tree.get("companies") or [],
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

	role_counter = Counter()
	for role in roles:
		role_counter[role["title"]] += role["count"]

	merged_roles = [{"title": title, "count": count} for title, count in role_counter.items()]
	merged_roles.sort(key=lambda r: (-r["count"], r["title"]))

	unit = _diagram_unit(dept_node)
	unit.update(
		{
			"title": dept_title or dept_node.get("title"),
			"manager": manager,
			"manager_info": {
				"employee": manager_emp.get("name") if manager_emp else "",
				"name": manager_emp.get("employee_name") if manager_emp else (dept_node.get("head_name") or ""),
				"designation": manager_emp.get("designation") if manager_emp else "",
				"image": manager_emp.get("image") if manager_emp else "",
				"label": manager,
			},
			"roles": merged_roles,
		}
	)
	return unit


def _diagram_unit(node):
	"""组织单元（部门/组）→ 下级组织 children + 直属成员 members，供架构图递归渲染。"""
	children = node.get("children") or []
	sub_units = [c for c in children if not c.get("is_employee")]
	members = [c for c in children if c.get("is_employee")]
	return {
		"name": node.get("name"),
		"title": node.get("title") or "",
		"org_type": node.get("org_type") or "部门",
		"employee_count": node.get("employee_count") or 0,
		"staff_quota": node.get("staff_quota") or 0,
		"head_name": node.get("head_name") or "",
		"supervisor_name": node.get("supervisor_name") or "",
		"children": [_diagram_unit(c) for c in sub_units],
		"members": [
			{
				"name": m.get("name"),
				"employee": m.get("employee") or "",
				"title": m.get("title") or "",
				"designation": m.get("designation") or "",
				"employment_type": m.get("employment_type") or "",
			}
			for m in members
		],
	}


def _find_department_manager_employee(dept_names, dept_title):
	rows = frappe.get_all(
		"Employee",
		filters=[["status", "=", "Active"], ["department", "in", dept_names]],
		fields=["name", "employee_name", "designation", "image"],
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
				best = {
					"score": score,
					"name": row.name,
					"employee_name": row.employee_name,
					"designation": designation,
					"image": row.image or "",
				}
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
	counter = Counter()
	for row in rows:
		if row.employee_name in exclude_names:
			continue
		title = (row.designation or "").strip() or "未设置岗位"
		if "经理" in title and "部" in title:
			continue
		counter[title] += 1
	return [{"title": title, "count": count} for title, count in counter.items()]


def _collect_dept_names(node):
	if node.get("is_employee"):
		return []
	names = [node["name"]]
	for child in node.get("children") or []:
		names.extend(_collect_dept_names(child))
	return names


def _get_general_manager(company):
	manager = _get_general_manager_info(company)
	return manager.get("label") or ""


def _get_general_manager_info(company):
	if not company:
		return {}
	rows = frappe.get_all(
		"Employee",
		filters=[
			["status", "=", "Active"],
			["company", "=", company],
			["designation", "like", "%总经理%"],
		],
		fields=["name", "employee_name", "designation", "image"],
		limit_page_length=1,
	)
	if rows:
		row = rows[0]
		return {
			"employee": row.name,
			"name": row.employee_name or "",
			"designation": row.designation or "总经理",
			"image": row.image or "",
			"label": f"{row.designation or '总经理'} {row.employee_name}".strip(),
		}
	return {}


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
