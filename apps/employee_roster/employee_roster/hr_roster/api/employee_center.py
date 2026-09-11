# Copyright (c) 2026 stillgroup
# License: MIT
"""Employee self-service APIs.

All queries in this module derive the employee from ``frappe.session.user``.
The client must never provide an Employee id for self-service operations.
"""

from __future__ import annotations

from collections import Counter

import frappe
from frappe import _
from frappe.model.naming import make_autoname
from frappe.utils import cint, flt, getdate, now_datetime

from employee_roster.hr_roster.approval_engine.assignees import get_employee_for_user
from employee_roster.hr_roster.approval_engine import runtime as approval_engine_runtime
from employee_roster.hr_roster.approval_engine.assignees import build_process_preview
from employee_roster.hr_roster.approval_engine.process_schema import normalize_process
from employee_roster.hr_roster.approval_engine.schema import normalize_schema
from employee_roster.hr_roster.approval_runtime import list_startable_forms


APPLICATION_MODULES = (
	{
		"key": "onboarding",
		"title": "入职资料填写",
		"description": "完善个人资料、联系方式和入职附件",
		"keywords": ("入职", "员工资料"),
	},
	{
		"key": "subsidy",
		"title": "申请补贴",
		"description": "提交餐补、车补及相关凭证",
		"keywords": ("补贴", "餐补", "车补"),
	},
	{
		"key": "job-change",
		"title": "调岗调薪",
		"description": "发起调岗、晋升、降级或调薪申请",
		"keywords": ("调岗", "调薪", "晋升", "降级"),
	},
	{
		"key": "resignation",
		"title": "离职申请表",
		"description": "提交离职日期、原因及审批申请",
		"keywords": ("离职申请",),
	},
	{
		"key": "handover",
		"title": "离职交接表",
		"description": "维护工作、资产和账号交接进度",
		"keywords": ("离职交接", "交接"),
	},
)


def _require_login() -> str:
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("请先登录"), frappe.PermissionError)
	return user


def _current_employee(*, required: bool = True):
	user = _require_login()
	employee_name = get_employee_for_user(user)
	if not employee_name:
		if required:
			frappe.throw(_("当前账号尚未关联员工档案，请联系 HR 处理"), frappe.PermissionError)
		return None
	if not frappe.db.exists("Employee", employee_name):
		frappe.throw(_("当前账号关联的员工档案不存在"), frappe.DoesNotExistError)
	return frappe.get_doc("Employee", employee_name)


def _display_employee(doc) -> dict:
	reports_to_name = ""
	if doc.reports_to:
		reports_to_name = frappe.db.get_value("Employee", doc.reports_to, "employee_name") or doc.reports_to
	return {
		"name": doc.name,
		"employee_name": doc.employee_name or doc.first_name or "",
		"employee_number": doc.employee_number or "",
		"status": doc.status or "",
		"department": doc.department or "",
		"designation": doc.designation or "",
		"company": doc.company or "",
		"branch": doc.get("branch") or "",
		"employment_type": doc.employment_type or "",
		"date_of_joining": str(doc.date_of_joining or "")[:10],
		"image": doc.image or "",
		"reports_to": doc.reports_to or "",
		"reports_to_name": reports_to_name,
	}


def _profile_progress(doc) -> dict:
	fields = (
		("employee_name", "姓名"),
		("gender", "性别"),
		("date_of_birth", "出生日期"),
		("cell_number", "手机号"),
		("personal_email", "个人邮箱"),
		("current_address", "现居地址"),
		("bank_name", "开户银行"),
		("bank_ac_no", "银行卡号"),
		("hr_attach_id_front", "身份证附件"),
		("hr_attach_photo", "个人照片"),
	)
	missing = [label for fieldname, label in fields if not doc.get(fieldname)]
	total = len(fields)
	completed = total - len(missing)
	return {
		"completed": completed,
		"total": total,
		"percent": round(completed / total * 100) if total else 0,
		"missing": missing,
	}


def _module_catalog() -> list[dict]:
	forms = list_startable_forms() or []
	result = []
	for config in APPLICATION_MODULES:
		matched = next(
			(
				row
				for row in forms
				if any(
					keyword in f"{row.get('form_name') or ''} {row.get('group') or ''}"
					for keyword in config["keywords"]
				)
			),
			None,
		)
		result.append(
			{
				"key": config["key"],
				"title": config["title"],
				"description": config["description"],
				"available": bool(matched),
				"approval_form": matched.get("name") if matched else "",
				"approval_form_name": matched.get("form_name") if matched else "",
			}
		)
	return result


def _status_counts(user: str) -> dict:
	rows = frappe.db.sql(
		"""
		SELECT status, COUNT(*) AS total
		FROM `tabApproval Instance`
		WHERE applicant_user = %(user)s
		GROUP BY status
		""",
		{"user": user},
		as_dict=True,
	)
	counts = Counter({row.get("status") or "": cint(row.get("total")) for row in rows})
	total = sum(counts.values())
	return {
		"all": total,
		"draft": counts.get("草稿", 0),
		"pending": counts.get("进行中", 0) + counts.get("审批中", 0),
		"approved": counts.get("已通过", 0),
		"rejected": counts.get("已驳回", 0),
		"withdrawn": counts.get("已撤销", 0) + counts.get("已撤回", 0),
	}


@frappe.whitelist()
def get_context() -> dict:
	"""Return the signed-in employee's self-service context."""
	user = _require_login()
	doc = _current_employee(required=False)
	roles = set(frappe.get_roles(user))
	if not doc:
		return {
			"employee": None,
			"profile": {"completed": 0, "total": 0, "percent": 0, "missing": []},
			"application_stats": _status_counts(user),
			"modules": [],
			"capabilities": {
				"can_use_employee_center": False,
				"can_submit": False,
				"can_manage_hr": bool(roles.intersection({"HR Manager", "HR User", "System Manager"})),
				"can_approve": bool(roles.intersection({"HR Manager", "System Manager"})),
			},
		}
	return {
		"employee": _display_employee(doc),
		"profile": _profile_progress(doc),
		"application_stats": _status_counts(user),
		"modules": _module_catalog(),
		"capabilities": {
			"can_use_employee_center": True,
			"can_submit": doc.status != "Left",
			"can_manage_hr": bool(roles.intersection({"HR Manager", "HR User", "System Manager"})),
			"can_approve": bool(roles.intersection({"HR Manager", "System Manager"})),
		},
	}


def _normalized_status(status: str | None) -> list[str] | None:
	mapping = {
		"draft": ["草稿"],
		"pending": ["进行中", "审批中"],
		"approved": ["已通过"],
		"rejected": ["已驳回"],
		"withdrawn": ["已撤销", "已撤回"],
	}
	return mapping.get((status or "").strip())


@frappe.whitelist()
def list_my_applications(
	status: str | None = None,
	application_type: str | None = None,
	date_from: str | None = None,
	date_to: str | None = None,
	keyword: str | None = None,
	limit_start: int = 0,
	page_length: int = 20,
) -> dict:
	"""List only applications initiated by the current session user."""
	user = _require_login()
	filters: dict = {"applicant_user": user}
	if application_type in APPLICATION_TITLES:
		filters["application_type"] = application_type
	if date_from and date_to:
		filters["creation"] = ["between", [f"{date_from} 00:00:00", f"{date_to} 23:59:59"]]
	status_values = _normalized_status(status)
	if status_values:
		filters["status"] = ["in", status_values]

	or_filters = None
	keyword = (keyword or "").strip()
	if keyword:
		like = f"%{keyword}%"
		or_filters = [["name", "like", like], ["form_title", "like", like]]

	page_length = min(max(cint(page_length) or 20, 1), 50)
	limit_start = max(cint(limit_start), 0)
	rows = frappe.get_all(
		"Approval Instance",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"application_no",
			"application_type",
			"approval_form",
			"form_title",
			"status",
			"current_node_label",
			"creation",
			"submitted_at",
			"modified",
			"finished_on",
		],
		order_by="modified desc",
		limit_start=limit_start,
		limit_page_length=page_length + 1,
	)
	has_more = len(rows) > page_length
	rows = rows[:page_length]
	for row in rows:
		row["status_key"] = _status_key(row.get("status"))
		row["application_no"] = row.get("application_no") or row.get("name")
		row["submitted_at"] = row.get("submitted_at") or row.get("creation")
	return {"rows": rows, "has_more": has_more, "next_start": limit_start + len(rows)}


def _status_key(status: str | None) -> str:
	if status == "草稿":
		return "draft"
	if status in ("进行中", "审批中"):
		return "pending"
	if status == "已通过":
		return "approved"
	if status == "已驳回":
		return "rejected"
	if status in ("已撤销", "已撤回"):
		return "withdrawn"
	return "unknown"


APPLICATION_TITLES = {
	"onboarding": "入职员工资料填写",
	"subsidy": "申请补贴",
	"job-change": "调岗调薪申请",
	"resignation": "离职申请表",
	"handover": "离职交接表",
}


def _parse_payload(payload) -> dict:
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	if not isinstance(payload, dict):
		frappe.throw(_("申请数据格式无效"))
	return payload


def _require_instance_owner(name: str):
	if not name or not frappe.db.exists("Approval Instance", name):
		frappe.throw(_("申请不存在"), frappe.DoesNotExistError)
	doc = frappe.get_doc("Approval Instance", name)
	if doc.applicant_user != frappe.session.user:
		frappe.throw(_("无权操作该申请"), frappe.PermissionError)
	return doc


def _application_form(application_type: str):
	if application_type not in APPLICATION_TITLES:
		frappe.throw(_("不支持的申请类型"))
	name = frappe.db.get_value(
		"Approval Form",
		{"form_name": APPLICATION_TITLES[application_type], "status": "使用中"},
		"name",
	)
	if not name:
		frappe.throw(_("该业务尚未配置审批流程，请联系管理员"))
	return frappe.get_doc("Approval Form", name)


def _employee_snapshot(employee) -> dict:
	return {
		"employee": employee.name,
		"applicant": employee.employee_name,
		"employee_number": employee.employee_number or "",
		"company": employee.company or "",
		"department": employee.department or "",
		"designation": employee.designation or "",
		"employment_type": employee.employment_type or "",
		"date_of_joining": str(employee.date_of_joining or "")[:10],
	}


@frappe.whitelist()
def get_application_setup(application_type: str, instance_name: str | None = None) -> dict:
	"""Return authoritative options, profile snapshot, draft and approval preview."""
	employee = _current_employee()
	form = _application_form(application_type)
	draft = None
	if instance_name:
		doc = _require_instance_owner(instance_name)
		if doc.application_type != application_type:
			frappe.throw(_("申请类型不匹配"))
		draft = {
			"name": doc.name,
			"status": doc.status,
			"data": frappe.parse_json(doc.form_data_json or "{}"),
		}
	return {
		"application_type": application_type,
		"title": APPLICATION_TITLES[application_type],
		"employee": _employee_snapshot(employee),
		"profile_defaults": {
			"gender": {"Male": "男", "Female": "女"}.get(employee.get("gender"), employee.get("gender") or ""),
			"date_of_birth": str(employee.get("date_of_birth") or "")[:10],
			"cell_number": employee.get("cell_number") or "",
			"personal_email": employee.get("personal_email") or "",
			"current_address": employee.get("current_address") or "",
			"permanent_address": employee.get("permanent_address") or "",
			"education": employee.get("education") or "",
			"bank_name": employee.get("bank_name") or "",
			"bank_ac_no": employee.get("bank_ac_no") or "",
			"current_salary": employee.get("ctc") or None,
		},
		"draft": draft,
		"options": {
			"departments": frappe.get_all("Department", filters={"disabled": 0}, pluck="name", order_by="name", limit_page_length=500),
			"designations": frappe.get_all("Designation", pluck="name", order_by="name", limit_page_length=500),
			"employees": frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "employee_name", "employee_number"], order_by="employee_name", limit_page_length=500),
		},
		"resignation_applications": frappe.get_all(
			"Approval Instance",
			filters={"applicant_user": frappe.session.user, "application_type": "resignation", "status": ["in", ["进行中", "已通过"]]},
			fields=["name", "application_no", "status"],
			order_by="modified desc",
			limit_page_length=20,
		),
		"process_preview": build_process_preview(
			normalize_process(form.process_json),
			applicant_employee=employee.name,
			applicant_user=frappe.session.user,
			form_data=(draft or {}).get("data") or {},
		),
	}


def _required(data: dict, fields: tuple[tuple[str, str], ...]) -> None:
	for key, label in fields:
		if data.get(key) in (None, "", []):
			frappe.throw(_("请填写：{0}").format(label))


def _validate_application(application_type: str, data: dict, *, submitting: bool) -> dict:
	data = dict(data)
	if application_type == "subsidy":
		details = data.get("details") or []
		meal_total = sum(flt(row.get("meal_amount")) for row in details)
		vehicle_total = sum(flt(row.get("vehicle_amount")) for row in details)
		data.update({"meal_total": meal_total, "vehicle_total": vehicle_total, "total_amount": meal_total + vehicle_total})
		data["details_summary"] = "；".join(
			f"{row.get('overtime_date') or '未填日期'} 餐补 {flt(row.get('meal_amount')):.2f} 元 / 车补 {flt(row.get('vehicle_amount')):.2f} 元"
			for row in details
		)
	elif application_type == "handover":
		items = data.get("items") or []
		completed = len([row for row in items if row.get("handover_status") == "已完成"])
		data["handover_progress"] = f"已完成 {completed} / {len(items)} 项"
		data["items_summary"] = "；".join(f"{row.get('category')}·{row.get('item_name')}（{row.get('handover_status') or '未开始'}）" for row in items)
	if not submitting:
		return data
	if application_type == "onboarding":
		_required(data, (("gender", "性别"), ("date_of_birth", "出生日期"), ("cell_number", "手机号"), ("personal_email", "个人邮箱"), ("id_number", "身份证号"), ("signature", "签名")))
		if data.get("truth_confirmed") is not True:
			frappe.throw(_("请确认信息真实、完整"))
		if not str(data.get("cell_number", "")).isdigit() or len(str(data["cell_number"])) != 11:
			frappe.throw(_("手机号格式不正确"))
	elif application_type == "subsidy":
		details = data.get("details") or []
		if not isinstance(details, list) or not details:
			frappe.throw(_("请至少添加一条补贴明细"))
		meal_total = vehicle_total = 0.0
		for idx, row in enumerate(details, 1):
			_required(row, (("overtime_date", f"第 {idx} 行加班日期"), ("clock_time", f"第 {idx} 行打卡时间"), ("punch_attachment", f"第 {idx} 行打卡记录截图")))
			meal = flt(row.get("meal_amount"))
			vehicle = flt(row.get("vehicle_amount"))
			if meal < 0 or meal > 25:
				frappe.throw(_("第 {0} 行餐补不能超过 25 元").format(idx))
			hour = int(str(row.get("clock_time") or "0").split(":")[0] or 0)
			if hour < 22 and vehicle > 30:
				frappe.throw(_("第 {0} 行 22 点前车补不能超过 30 元").format(idx))
			if hour >= 22 and vehicle > 100:
				frappe.throw(_("第 {0} 行车补不能超过 100 元").format(idx))
			if hour >= 22 and vehicle and not row.get("taxi_attachment"):
				frappe.throw(_("第 {0} 行 22 点后请上传打车单截图").format(idx))
			meal_total += meal
			vehicle_total += vehicle
		data.update({"meal_total": meal_total, "vehicle_total": vehicle_total, "total_amount": meal_total + vehicle_total})
	elif application_type == "job-change":
		_required(data, (("change_type", "异动类型"), ("effective_date", "生效日期"), ("reason", "申请原因")))
		if data["change_type"] == "调岗":
			_required(data, (("new_department", "调入部门"), ("new_designation", "调整后岗位")))
		elif data["change_type"] in ("晋升", "降级"):
			_required(data, (("new_designation", "调整后岗位"), ("new_grade", "调整后职级")))
		else:
			_required(data, (("current_salary", "原薪资"), ("new_salary", "调整后薪资")))
	elif application_type == "resignation":
		_required(data, (("planned_resignation_date", "计划离职日期"), ("handover_employee", "离职交接人"), ("resignation_reason", "离职原因"), ("reason_description", "原因说明")))
		if getdate(data["planned_resignation_date"]) < getdate():
			frappe.throw(_("计划离职日期不能早于今天"))
	elif application_type == "handover":
		_required(data, (("resignation_application", "关联离职申请单"),))
		if not frappe.db.exists("Approval Instance", {
			"name": data["resignation_application"],
			"applicant_user": frappe.session.user,
			"application_type": "resignation",
			"status": ["in", ["进行中", "已通过"]],
		}):
			frappe.throw(_("关联离职申请不存在或不属于当前员工"), frappe.PermissionError)
		items = data.get("items") or []
		if not items:
			frappe.throw(_("交接清单不能为空"))
	return data


def _link_owned_files(doc, data: dict) -> None:
	urls: set[str] = set()
	def collect(value):
		if isinstance(value, dict):
			for v in value.values(): collect(v)
		elif isinstance(value, list):
			for v in value: collect(v)
		elif isinstance(value, str) and value.startswith(("/files/", "/private/files/")):
			urls.add(value)
	collect(data)
	for url in urls:
		file_name = frappe.db.get_value("File", {"file_url": url}, "name")
		if not file_name:
			frappe.throw(_("附件不存在或已被删除"))
		file_doc = frappe.get_doc("File", file_name)
		if file_doc.owner != frappe.session.user and "System Manager" not in frappe.get_roles():
			frappe.throw(_("附件不属于当前用户"), frappe.PermissionError)
		frappe.db.set_value("File", file_name, {"attached_to_doctype": "Approval Instance", "attached_to_name": doc.name}, update_modified=False)


@frappe.whitelist(methods=["POST"])
def save_application(application_type: str, payload: str | dict, instance_name: str | None = None, submit: int = 0) -> dict:
	"""Create/update a draft or submit it into the existing approval engine."""
	employee = _current_employee()
	if employee.status == "Left":
		frappe.throw(_("已离职员工不能发起申请"), frappe.PermissionError)
	data = _validate_application(application_type, _parse_payload(payload), submitting=bool(cint(submit)))
	form = _application_form(application_type)
	if instance_name:
		doc = _require_instance_owner(instance_name)
		if doc.status not in ("草稿", "已驳回", "已撤销"):
			frappe.throw(_("当前状态不能修改"))
		if doc.application_type != application_type:
			frappe.throw(_("申请类型不匹配"))
	else:
		doc = frappe.get_doc({
			"doctype": "Approval Instance",
			"application_no": make_autoname("EC-.YYYY.-.#####"),
			"application_type": application_type,
			"approval_form": form.name,
			"form_title": APPLICATION_TITLES[application_type],
			"applicant_user": frappe.session.user,
			"applicant_employee": employee.name,
			"status": "草稿",
		})
	data["employee_snapshot"] = _employee_snapshot(employee)
	doc.form_schema_json = form.form_schema_json
	doc.form_data_json = frappe.as_json(data)
	doc.process_snapshot_json = form.process_json
	doc.business_hook = form.business_hook
	doc.current_node_id = ""
	doc.current_node_label = "草稿" if not cint(submit) else ""
	if doc.is_new(): doc.insert(ignore_permissions=True)
	else: doc.save(ignore_permissions=True)
	_link_owned_files(doc, data)
	if cint(submit):
		if doc.status in ("已驳回", "已撤销"):
			frappe.db.set_value("Approval Task", {"instance": doc.name, "status": "待处理"}, "status", "已取消")
		doc.status = "进行中"
		doc.submitted_at = now_datetime()
		doc.finished_on = None
		doc.save(ignore_permissions=True)
		approval_engine_runtime._advance_from(doc, after_node_id=None)
		doc.reload()
	return {"name": doc.name, "application_no": doc.application_no, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def delete_draft(instance_name: str) -> None:
	doc = _require_instance_owner(instance_name)
	if doc.status != "草稿":
		frappe.throw(_("只能删除草稿"))
	doc.delete(ignore_permissions=True)
