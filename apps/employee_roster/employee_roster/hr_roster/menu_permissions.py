# Copyright (c) 2026 stillgroup
# License: MIT

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from urllib.parse import urlparse

import frappe
from frappe import _


PLATFORM_ROLE = "平台超级管理员"
ENTERPRISE_ROLE = "企业管理员"
HR_ROLE = "人事管理员"
EMPLOYEE_ROLE = "普通员工"
SYSTEM_ROLE_TITLES = (PLATFORM_ROLE, ENTERPRISE_ROLE, HR_ROLE, EMPLOYEE_ROLE)
MANAGEMENT_INTERNAL_ROLE = "Enterprise Admin"

MODULES = (
	("HR Setup", "人事", "user-group"),
	("Shift & Attendance", "考勤", "calendar"),
	("hr_roster", "审批", "check-circle"),
	("Contract", "合同", "file"),
	("Recruitment", "招聘", "user-add"),
	("Payroll", "薪资", "book"),
	("Employee Center", "员工中心", "user"),
	("System Management", "系统管理", "settings"),
)

STATIC_CHILDREN = {
	"Contract": (
		("概览", "Page", "contract-overview"),
		("合同签署", "Page", "contract-signing-pending"),
		("合同档案库", "Page", "contract-archive"),
		("设置", "Page", "contract-seals"),
	),
	"Employee Center": (
		("员工中心", "Page", "employee-center/home"),
		("入职资料填写", "Page", "employee-center/onboarding"),
		("申请补贴", "Page", "employee-center/subsidy"),
		("调岗调薪", "Page", "employee-center/job-change"),
		("离职申请", "Page", "employee-center/resignation"),
		("离职交接", "Page", "employee-center/handover"),
		("我的申请", "Page", "employee-center/applications"),
	),
	"System Management": (
		("权限管理", "Page", "permission-management"),
		("人员角色分配", "Page", "role-assignment"),
	),
}

SYSTEM_ROLE_DESCRIPTIONS = {
	"enterprise_admin": "管理本企业角色与菜单",
	"hr_admin": "访问企业人事业务模块",
	"employee": "仅访问员工中心",
}

LABELS = {
	"Home": "主页", "Dashboard": "数据面板", "Employee Checkin": "打卡记录",
	"Attendance Rules": "考勤规则", "Payroll Entry": "薪资发放",
	"Salary Structure Assignment": "薪资结构分配", "Salary Slip": "工资条",
	"Additional Salary": "额外薪资", "Salary Withholding": "薪资暂扣",
	"Salary Register": "薪资登记表", "Salary Component": "薪资项目",
	"Salary Structure": "薪资结构", "Hiring Pipeline": "招聘流程",
	"Job Opening": "职位开放", "Job Applicant": "应聘者", "Interview": "面试",
	"Job Offer": "录用通知", "Appointment Letter": "录用函", "Job Requisition": "用人申请",
	"Staffing Plan": "编制计划", "Employee Referral": "内部推荐",
	"Recruitment Analytics": "招聘分析", "Approval Forms": "审批表单",
	"Approval Templates": "审批模板库", "Interview Type": "面试类型",
	"Job Opening Template": "职位模板", "Appointment Letter Template": "录用函模板",
	"Job Offer Term Template": "录用条款模板", "Job Portal": "招聘门户",
	"Settings": "设置", "Employee CTC Break-up": "员工成本明细",
	"Income Tax Deductions": "个税扣缴", "Professional Tax Deductions": "职业税扣缴",
	"General Ledger": "总账", "Accounts Payable": "应付账款", "Payroll Settings": "薪资设置",
}

HR_SETUP_HIDDEN = {"Company", "Branch", "Department", "Designation", "Employee Group", "Employee Grade", "HR Settings", "Settings"}
ATTENDANCE_ALLOWED = {"Employee Checkin", "attendance-rules", "Attendance Rules", "打卡记录", "考勤规则"}


def parent_key(module: str) -> str:
	return f"module::{module}"


def child_key(module: str, link_type: str, link_to: str) -> str:
	return f"item::{module}::{link_type or 'Page'}::{link_to}"


def role_code(company: str | None, system_key: str | None = None, title: str | None = None) -> str:
	seed = "::".join((company or "platform", system_key or "custom", title or ""))
	return f"business-role-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:16]}"


def _translated(label: str) -> str:
	translated = _(label) if label else ""
	return LABELS.get(label, translated if translated and translated != label else label)


def _normalize_url(value: str) -> str:
	path = urlparse(value or "").path.strip("/")
	parts = path.split("/") if path else []
	if parts and parts[0] in {"app", "desk"}:
		parts = parts[1:]
	return "/".join(parts)


def _sidebar_children(module: str) -> list[dict]:
	if module in STATIC_CHILDREN:
		return [{"key": child_key(module, kind, target), "label": label, "link_type": kind, "target": target} for label, kind, target in STATIC_CHILDREN[module]]
	if not frappe.db.exists("Sidebar", module):
		return []
	doc = frappe.get_doc("Sidebar", module)
	children, seen = [], set()
	for item in doc.items:
		if item.type != "Link" or item.hidden:
			continue
		label, target = str(item.label or ""), str(item.link_to or "")
		if module == "HR Setup" and (label in HR_SETUP_HIDDEN or target in HR_SETUP_HIDDEN):
			continue
		if module == "Shift & Attendance" and not ({label, target} & ATTENDANCE_ALLOWED):
			continue
		link_type = str(item.link_type or "Page")
		if module == "HR Setup" and label in {"Home", "主页"}:
			target, link_type = "hr-home", "Page"
		elif module == "HR Setup" and label in {"Dashboard", "数据面板"}:
			target, link_type = "hr-dashboard", "Page"
		elif link_type == "URL":
			target = _normalize_url(str(item.url or target))
		if not target:
			continue
		key = child_key(module, link_type, target)
		if key in seen:
			continue
		seen.add(key)
		children.append({"key": key, "label": _translated(label), "link_type": link_type, "target": target})
	return children


def get_menu_catalog() -> list[dict]:
	return [{"key": parent_key(module), "module": module, "label": label, "icon": icon, "children": _sidebar_children(module)} for module, label, icon in MODULES]


def all_menu_keys(catalog: list[dict] | None = None) -> set[str]:
	catalog = catalog or get_menu_catalog()
	return {entry["key"] for entry in catalog} | {child["key"] for entry in catalog for child in entry["children"]}


def default_menu_keys(system_key: str, catalog: list[dict] | None = None) -> set[str]:
	catalog = catalog or get_menu_catalog()
	if system_key in {"platform_super", "enterprise_admin"}:
		return all_menu_keys(catalog)
	allowed_modules = {
		"hr_admin": {"HR Setup", "Shift & Attendance", "hr_roster", "Contract", "Recruitment", "Payroll", "Employee Center"},
		"employee": {"Employee Center"},
	}.get(system_key, set())
	return {key for entry in catalog if entry["module"] in allowed_modules for key in [entry["key"], *[child["key"] for child in entry["children"]]]}


def _first_company() -> str | None:
	return frappe.db.get_value("Company", {}, "name")


def get_user_company(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if frappe.db.table_exists("HR User Business Role"):
		company = frappe.db.get_value("HR User Business Role", {"user": user, "enabled": 1}, "company", order_by="modified desc")
		if company:
			return company
	company = frappe.db.get_value("Employee", {"user_id": user, "status": ["!=", "Left"]}, "company")
	return company or frappe.defaults.get_user_default("Company", user) or _first_company()


def is_platform_admin(user: str | None = None) -> bool:
	user = user or frappe.session.user
	return user == "Administrator" or "System Manager" in frappe.get_roles(user)


def _assigned_roles(user: str, company: str | None) -> list[dict]:
	if not company or not frappe.db.table_exists("HR User Business Role"):
		return []
	rows = frappe.get_all("HR User Business Role", filters={"user": user, "company": company, "enabled": 1}, fields=["business_role"], order_by="creation asc")
	result = []
	for row in rows:
		role = frappe.db.get_value("HR Business Role", row.business_role, ["role_title", "system_key", "enabled"], as_dict=True)
		if role and role.enabled:
			result.append({"business_role": row.business_role, "role_title": role.role_title, "system_key": role.system_key})
	return result


def _fallback_system_key(user: str) -> str:
	roles = set(frappe.get_roles(user))
	if user == "Administrator" or "System Manager" in roles:
		return "platform_super"
	if MANAGEMENT_INTERNAL_ROLE in roles:
		return "enterprise_admin"
	if roles & {"HR Manager", "HR User"}:
		return "hr_admin"
	return "employee"


def get_effective_access(user: str | None = None, company: str | None = None) -> dict:
	user, company = user or frappe.session.user, company or get_user_company(user)
	catalog = get_menu_catalog()
	if is_platform_admin(user):
		return _access_payload(company, all_menu_keys(catalog), catalog, True, [PLATFORM_ROLE])
	assigned, keys, titles = _assigned_roles(user, company), set(), []
	for row in assigned:
		titles.append(row["role_title"])
		doc = frappe.get_doc("HR Business Role", row["business_role"])
		keys |= {item.menu_key for item in doc.menu_permissions} or default_menu_keys(row["system_key"], catalog)
	if not assigned:
		fallback = _fallback_system_key(user)
		keys = default_menu_keys(fallback, catalog)
		titles = {"enterprise_admin": [ENTERPRISE_ROLE], "hr_admin": [HR_ROLE], "employee": [EMPLOYEE_ROLE]}[fallback]
	can_manage = any(row["system_key"] == "enterprise_admin" for row in assigned) or _fallback_system_key(user) == "enterprise_admin"
	return _access_payload(company, keys, catalog, can_manage, titles)


def _access_payload(company: str | None, keys: set[str], catalog: list[dict], can_manage: bool, titles: list[str]) -> dict:
	known_routes, allowed_routes = {}, []
	for entry in catalog:
		for child in entry["children"]:
			link_type = child["link_type"]
			target = child["target"]
			routes = [target]
			if link_type == "DocType":
				routes += [f"List/{child['target']}", f"Form/{child['target']}"]
			elif link_type == "Report":
				routes = [f"query-report/{target}"]
			elif link_type == "Dashboard":
				routes = [f"dashboard-view/{target}"]
			for route in routes:
				known_routes[route] = child["key"]
				if child["key"] in keys and route not in allowed_routes:
					allowed_routes.append(route)
	default_route = "employee-center/home"
	for entry in catalog:
		allowed_child = next((child for child in entry["children"] if child["key"] in keys), None)
		if entry["key"] in keys and allowed_child:
			default_route = allowed_child["target"]
			break
	return {"company": company, "allowed_menu_keys": sorted(keys), "known_routes": known_routes, "allowed_routes": allowed_routes, "default_route": default_route, "can_manage_permissions": can_manage, "role_titles": titles}


def _require_login():
	if frappe.session.user == "Guest":
		frappe.throw(_("请先登录"), frappe.PermissionError)


def _require_manage(company: str | None = None):
	_require_login()
	if is_platform_admin():
		return
	access = get_effective_access(company=company)
	if not access["can_manage_permissions"] or (company and access["company"] != company):
		frappe.throw(_("你没有权限管理该企业的角色"), frappe.PermissionError)


def ensure_system_roles(company: str | None = None) -> list[str]:
	catalog, created = get_menu_catalog(), []
	if not frappe.db.exists("Role", MANAGEMENT_INTERNAL_ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": MANAGEMENT_INTERNAL_ROLE, "desk_access": 1}).insert(ignore_permissions=True)
	definitions = [("platform_super", PLATFORM_ROLE, None)]
	companies = [company] if company else frappe.get_all("Company", pluck="name")
	definitions += [(key, title, company_name) for company_name in companies for key, title in (("enterprise_admin", ENTERPRISE_ROLE), ("hr_admin", HR_ROLE), ("employee", EMPLOYEE_ROLE))]
	for system_key, title, company_name in definitions:
		code = role_code(company_name, system_key, title)
		if frappe.db.exists("HR Business Role", code):
			if system_key == "platform_super":
				frappe.db.set_value("HR Business Role", code, "company", None, update_modified=False)
			continue
		doc = frappe.get_doc({"doctype": "HR Business Role", "role_code": code, "role_title": title, "company": company_name or "", "role_category": "系统角色", "system_key": system_key, "is_system_role": 1, "enabled": 1, "description": "系统预置角色"})
		if system_key == "platform_super":
			doc.company = None
		for key in sorted(default_menu_keys(system_key, catalog)):
			doc.append("menu_permissions", {"menu_key": key})
		doc.insert(ignore_permissions=True)
		created.append(doc.name)
	return created


@frappe.whitelist()
def get_my_menu_access(company: str | None = None):
	_require_login()
	return get_effective_access(company=company)


@frappe.whitelist()
def get_permission_management_context(company: str | None = None, role: str | None = None):
	company = company or get_user_company()
	_require_manage(company)
	ensure_system_roles(company)
	companies = frappe.get_all("Company", pluck="name", order_by="company_name asc") if is_platform_admin() else [company]
	roles = frappe.get_all("HR Business Role", filters={"company": company, "enabled": 1}, fields=["name", "role_title", "role_category", "is_system_role", "description", "system_key"], order_by="is_system_role desc, creation asc")
	roles = [item for item in roles if item.system_key != "platform_super"]
	for item in roles:
		item.description = SYSTEM_ROLE_DESCRIPTIONS.get(item.system_key, item.description or "")
		item["assigned_count"] = frappe.db.count("HR User Business Role", {"business_role": item.name, "enabled": 1})
	selected = role if role and any(item.name == role for item in roles) else (next((item.name for item in roles if item.role_title == HR_ROLE), roles[0].name if roles else None))
	selected_keys = [row.menu_key for row in frappe.get_doc("HR Business Role", selected).menu_permissions] if selected else []
	return {"company": company, "companies": companies, "roles": roles, "selected_role": selected, "selected_menu_keys": selected_keys, "menu_catalog": get_menu_catalog(), "is_platform_admin": is_platform_admin()}


@frappe.whitelist(methods=["POST"])
def save_role_menu_permissions(role: str, menu_keys: list | str | None = None):
	doc = frappe.get_doc("HR Business Role", role)
	_require_manage(doc.company)
	if doc.system_key == "platform_super":
		frappe.throw(_("平台超级管理员权限由系统统一维护"))
	if isinstance(menu_keys, str):
		menu_keys = json.loads(menu_keys)
	clean, valid = {str(key) for key in (menu_keys or [])}, all_menu_keys()
	clean &= valid
	for entry in get_menu_catalog():
		child_keys = {child["key"] for child in entry["children"]}
		if clean & child_keys:
			clean.add(entry["key"])
		if entry["key"] not in clean:
			clean -= child_keys
	doc.set("menu_permissions", [])
	for key in sorted(clean):
		doc.append("menu_permissions", {"menu_key": key})
	doc.save(ignore_permissions=True)
	frappe.clear_cache()
	return {"role": doc.name, "menu_keys": sorted(clean), "message": "权限已保存并生效"}


@frappe.whitelist(methods=["POST"])
def create_business_role(company: str, role_title: str, description: str = "", copy_from: str | None = None):
	_require_manage(company)
	role_title = (role_title or "").strip()
	if not role_title:
		frappe.throw(_("请输入角色名称"))
	if role_title in SYSTEM_ROLE_TITLES:
		frappe.throw(_("该名称为系统角色名称，请使用其他名称"))
	doc = frappe.get_doc({"doctype": "HR Business Role", "role_code": role_code(company, title=role_title), "role_title": role_title, "company": company, "role_category": "自定义角色", "is_system_role": 0, "enabled": 1, "description": (description or "").strip()})
	if copy_from:
		source = frappe.get_doc("HR Business Role", copy_from)
		if source.company != company:
			frappe.throw(_("只能复制当前企业的角色"))
		for row in source.menu_permissions:
			doc.append("menu_permissions", {"menu_key": row.menu_key})
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "role_title": doc.role_title, "message": "角色创建成功"}


@frappe.whitelist(methods=["POST"])
def assign_business_roles(user: str, company: str, roles: list | str | None = None):
	_require_manage(company)
	role_names = _validate_assignment(company, user, roles)
	_apply_business_roles(user, company, role_names)
	return {"message": "账号角色已更新", "roles": role_names}


@frappe.whitelist(methods=["POST"])
def assign_business_roles_bulk(users: list | str | None, company: str, roles: list | str | None = None):
	_require_manage(company)
	if isinstance(users, str):
		users = json.loads(users)
	users = list(dict.fromkeys(str(user) for user in (users or []) if user))
	if not users:
		frappe.throw(_("请选择需要分配角色的员工"))
	if len(users) > 100:
		frappe.throw(_("单次最多为 100 名员工分配角色"))
	role_names = _normalize_role_names(roles)
	for user in users:
		_validate_assignment(company, user, role_names)
	for user in users:
		_apply_business_roles(user, company, role_names)
	return {"message": f"已更新 {len(users)} 名员工的角色", "count": len(users), "roles": role_names}


def _normalize_role_names(roles: list | str | None) -> list[str]:
	if isinstance(roles, str):
		roles = json.loads(roles)
	return list(dict.fromkeys(str(role) for role in (roles or []) if role))


def _validate_assignment(company: str, user: str, roles: list | str | None) -> list[str]:
	role_names = _normalize_role_names(roles)
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		frappe.throw(_("平台超级管理员不支持企业内分配"))
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": user, "company": company},
		["name", "status"],
		as_dict=True,
	)
	if not employee:
		frappe.throw(_("该账号未绑定当前企业的员工档案"))
	if employee.status != "Active":
		frappe.throw(_("只能为在职员工分配角色"))
	valid_rows = frappe.get_all(
		"HR Business Role",
		filters={"company": company, "enabled": 1},
		fields=["name", "system_key"],
	)
	valid = {row.name for row in valid_rows if row.system_key != "platform_super"}
	if any(role not in valid for role in role_names):
		frappe.throw(_("包含无效或其他企业的角色"))
	return role_names


def _apply_business_roles(user: str, company: str, role_names: list[str]) -> None:
	frappe.db.delete("HR User Business Role", {"user": user, "company": company})
	for role in role_names:
		frappe.get_doc({"doctype": "HR User Business Role", "user": user, "company": company, "business_role": role, "enabled": 1}).insert(ignore_permissions=True)
	enterprise_role = frappe.db.get_value("HR Business Role", {"company": company, "system_key": "enterprise_admin"}, "name")
	user_doc = frappe.get_doc("User", user)
	if enterprise_role in role_names and MANAGEMENT_INTERNAL_ROLE not in frappe.get_roles(user):
		user_doc.add_roles(MANAGEMENT_INTERNAL_ROLE)
	elif enterprise_role not in role_names and MANAGEMENT_INTERNAL_ROLE in frappe.get_roles(user):
		user_doc.remove_roles(MANAGEMENT_INTERNAL_ROLE)
	frappe.clear_cache(user=user)


@frappe.whitelist()
def get_role_assignment_context(company: str | None = None):
	company = company or get_user_company()
	_require_manage(company)
	ensure_system_roles(company)
	from employee_roster.hr_roster.page.orgchart.orgchart import get_org_tree

	org_data = get_org_tree(company)
	employee_ids: list[str] = []

	def collect(nodes):
		for node in nodes or []:
			if node.get("is_employee") and node.get("employee"):
				employee_ids.append(node["employee"])
			collect(node.get("children"))

	collect(org_data.get("roots"))
	employee_rows = frappe.get_all(
		"Employee",
		filters={"name": ["in", employee_ids]} if employee_ids else {"name": ""},
		fields=["name", "user_id", "image", "department", "group_name", "designation", "status"],
		limit_page_length=None,
	)
	employees = {row.name: row for row in employee_rows}
	users = [row.user_id for row in employee_rows if row.user_id]
	assigned = defaultdict(list)
	if users:
		for row in frappe.get_all(
			"HR User Business Role",
			filters={"company": company, "enabled": 1, "user": ["in", users]},
			fields=["user", "business_role"],
			limit_page_length=None,
		):
			assigned[row.user].append(row.business_role)

	def enrich(nodes):
		for node in nodes or []:
			if node.get("is_employee"):
				row = employees.get(node.get("employee"))
				node["user_id"] = row.user_id if row else ""
				node["image"] = row.image if row else ""
				node["assigned_roles"] = assigned.get(row.user_id, []) if row and row.user_id else []
			enrich(node.get("children"))

	enrich(org_data.get("roots"))
	role_context = get_permission_management_context(company)
	return {
		"company": company,
		"companies": role_context["companies"],
		"is_platform_admin": role_context["is_platform_admin"],
		"roles": role_context["roles"],
		"roots": org_data.get("roots") or [],
		"organization_count": org_data.get("total") or 0,
	}


def has_menu_access(menu_key: str, user: str | None = None, company: str | None = None) -> bool:
	return menu_key in set(get_effective_access(user=user, company=company)["allowed_menu_keys"])


def require_menu_access(menu_key: str, user: str | None = None, company: str | None = None):
	if not has_menu_access(menu_key, user=user, company=company):
		frappe.throw(_("你没有权限访问该功能"), frappe.PermissionError)
