# Copyright (c) 2026 stillgroup
# License: MIT
"""员工档案详情：读取 / 分板块保存 API。"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, getdate, today

from employee_roster.hr_roster.employee_detail_schema import (
	CHILD_TABLE_MAP,
	REQUIRED_MATERIAL_KEYS,
	SECTION_FIELD_MAP,
)


def _can_read_employee(name: str) -> bool:
	return bool(frappe.has_permission("Employee", "read", doc=name))


def _can_write_employee(name: str) -> bool:
	return bool(frappe.has_permission("Employee", "write", doc=name))


def _years_between(start, end=None) -> float | None:
	if not start:
		return None
	try:
		start_d = getdate(start)
		end_d = getdate(end or today())
		days = (end_d - start_d).days
		if days < 0:
			return 0.0
		return round(days / 365.25, 1)
	except Exception:
		return None


def _age_years(birth) -> int | None:
	if not birth:
		return None
	try:
		b = getdate(birth)
		t = getdate(today())
		age = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
		return max(0, age)
	except Exception:
		return None


def _birthday_mmdd(birth) -> str:
	if not birth:
		return ""
	try:
		b = getdate(birth)
		return f"{b.month:02d}-{b.day:02d}"
	except Exception:
		return ""


def _mask_id(value: str, allow: bool) -> str:
	raw = str(value or "").strip()
	if not raw or allow:
		return raw
	if len(raw) <= 8:
		return raw[:2] + "*" * max(0, len(raw) - 2)
	return raw[:3] + "*" * (len(raw) - 7) + raw[-4:]


def _mask_phone(value: str, allow: bool) -> str:
	raw = str(value or "").strip()
	if not raw or allow:
		return raw
	if len(raw) <= 7:
		return raw[:2] + "****"
	return raw[:3] + "****" + raw[-4:]


def _mask_bank(value: str, allow: bool) -> str:
	raw = str(value or "").strip()
	if not raw or allow:
		return raw
	if len(raw) <= 8:
		return "****" + raw[-4:]
	return raw[:4] + " **** **** " + raw[-4:]


def _mask_money(value, allow: bool):
	if value in (None, ""):
		return value
	if allow:
		return value
	return "****"


def _child_rows(doc, fieldname: str) -> list[dict]:
	try:
		rows = doc.get(fieldname) or []
	except Exception:
		return []
	out = []
	for row in rows:
		item = row.as_dict() if hasattr(row, "as_dict") else dict(row)
		item.pop("parent", None)
		item.pop("parenttype", None)
		item.pop("parentfield", None)
		item.pop("doctype", None)
		out.append(item)
	return out


def _contract_status(start, end, fallback="") -> str:
	if fallback:
		return fallback
	try:
		t = getdate(today())
		s = getdate(start) if start else None
		e = getdate(end) if end else None
		if s and t < s:
			return "未生效"
		if e and t > e:
			return "已到期"
		if s:
			return "履行中"
	except Exception:
		pass
	return fallback or ""


def _material_groups(doc) -> list[dict]:
	groups = [
		{
			"key": "basic",
			"title": "员工基本资料",
			"items": [
				{"key": "hr_attach_id_front", "label": "身份证原件照片（人像面）", "required": True},
				{"key": "hr_attach_id_back", "label": "身份证复印件（国徽面）", "required": True},
				{"key": "hr_attach_diploma", "label": "学历证明", "required": True},
				{"key": "hr_attach_photo", "label": "个人证件照", "required": True},
				{"key": "hr_attach_degree", "label": "学位证书", "required": False},
				{"key": "hr_attach_bank_card", "label": "银行卡", "required": False},
				{"key": "hr_attach_others", "label": "其他材料", "required": False},
			],
		},
		{
			"key": "archive",
			"title": "员工档案资料",
			"items": [
				{"key": "hr_attach_resume", "label": "入职简历", "required": True},
				{"key": "hr_attach_medical_report", "label": "入职体检单", "required": False},
				{"key": "contract_file", "label": "劳动合同", "required": False, "from_contracts": True},
			],
		},
		{
			"key": "exit",
			"title": "员工离职资料",
			"items": [
				{"key": "hr_attach_resignation_proof", "label": "离职证明", "required": False},
			],
		},
	]
	for group in groups:
		for item in group["items"]:
			if item.get("from_contracts"):
				files = [r.get("attachment") for r in _child_rows(doc, "hr_contracts") if r.get("attachment")]
				item["files"] = [{"url": f, "name": f.split("/")[-1]} for f in files]
				item["file"] = files[0] if files else ""
			else:
				file_url = doc.get(item["key"]) or ""
				item["file"] = file_url
				item["files"] = [{"url": file_url, "name": file_url.split("/")[-1]}] if file_url else []
			item["missing"] = item.get("required") and not item["file"]
	return groups


def _archive_rate(doc) -> dict:
	required = REQUIRED_MATERIAL_KEYS[:]
	# 合同附件：若存在合同记录则计为必需之一
	contracts = _child_rows(doc, "hr_contracts")
	has_contract_file = any(r.get("attachment") for r in contracts)
	total = len(required) + (1 if contracts else 0)
	done = sum(1 for k in required if doc.get(k))
	if contracts:
		done += 1 if has_contract_file else 0
	rate = round(done / total * 100) if total else 0
	return {"rate": rate, "done": done, "total": total}


def _serialize_employee(doc, *, reveal_sensitive: bool) -> dict:
	allow = reveal_sensitive
	data = {
		"name": doc.name,
		"employee_name": doc.employee_name or doc.first_name or "",
		"first_name": doc.first_name or "",
		"employee_number": doc.employee_number or "",
		"status": doc.status or "",
		"department": doc.department or "",
		"designation": doc.designation or "",
		"company": doc.company or "",
		"branch": doc.get("branch") or "",
		"group_name": doc.get("group_name") or "",
		"employment_type": doc.employment_type or "",
		"grade": doc.grade or "",
		"reports_to": doc.reports_to or "",
		"image": doc.image or "",
		"gender": doc.gender or "",
		"date_of_birth": str(doc.date_of_birth or "")[:10],
		"birthday": _birthday_mmdd(doc.date_of_birth),
		"age": _age_years(doc.date_of_birth),
		"date_of_joining": str(doc.date_of_joining or "")[:10],
		"marital_status": doc.marital_status or "",
		"blood_group": doc.blood_group or "",
		"health_details": doc.health_details or "",
		"cell_number": _mask_phone(doc.cell_number, allow),
		"cell_number_raw": (doc.cell_number or "") if allow else "",
		"personal_email": doc.personal_email or "",
		"company_email": doc.company_email or "",
		"current_address": doc.current_address or "",
		"permanent_address": doc.permanent_address or "",
		"bank_name": doc.bank_name or "",
		"bank_ac_no": _mask_bank(doc.bank_ac_no, allow),
		"bank_ac_no_raw": (doc.bank_ac_no or "") if allow else "",
		"salary_mode": doc.salary_mode or "",
		"iban": doc.get("iban") or "",
		"ctc": _mask_money(doc.get("ctc"), allow),
		"salary_currency": doc.get("salary_currency") or "",
		"scheduled_confirmation_date": str(doc.scheduled_confirmation_date or "")[:10],
		"final_confirmation_date": str(doc.final_confirmation_date or "")[:10],
		"relieving_date": str(doc.relieving_date or "")[:10],
		"resignation_letter_date": str(doc.resignation_letter_date or "")[:10],
		"reason_for_leaving": doc.reason_for_leaving or "",
		"new_workplace": doc.new_workplace or "",
		"date_of_retirement": str(doc.date_of_retirement or "")[:10],
		"attendance_device_id": doc.get("attendance_device_id") or "",
		"holiday_list": doc.get("holiday_list") or "",
		"leave_approver": doc.get("leave_approver") or "",
		"expense_approver": doc.get("expense_approver") or "",
		"shift_request_approver": doc.get("shift_request_approver") or "",
		"bio": doc.get("bio") or "",
		"can_edit": _can_write_employee(doc.name),
		"can_view_sensitive": allow,
	}

	# 自定义 hr_ 字段
	meta = frappe.get_meta("Employee")
	for df in meta.fields:
		fn = df.fieldname
		if not fn.startswith("hr_") and fn not in (
			"person_to_be_contacted",
			"emergency_phone_number",
			"relation",
		):
			continue
		if df.fieldtype in ("Table", "Section Break", "Column Break", "Tab Break", "HTML", "Button"):
			continue
		val = doc.get(fn)
		if df.fieldtype == "Date":
			val = str(val or "")[:10]
		elif df.fieldtype == "Check":
			val = cint(val)
		data[fn] = val if val is not None else ""

	# 敏感字段覆盖
	data["hr_id_number"] = _mask_id(doc.get("hr_id_number"), allow)
	data["hr_id_number_raw"] = (doc.get("hr_id_number") or "") if allow else ""
	for money_key in (
		"hr_base_salary",
		"hr_position_salary",
		"hr_performance_salary",
		"hr_allowance",
		"hr_social_security_base",
		"hr_housing_fund_base",
	):
		data[money_key] = _mask_money(doc.get(money_key), allow)

	# 计算字段
	tenure_start = doc.get("hr_company_tenure_start") or doc.date_of_joining
	data["company_tenure_years"] = _years_between(tenure_start)
	data["total_work_years"] = _years_between(doc.get("hr_work_start_date"))
	data["hr_total_work_years"] = data["total_work_years"]

	# 子表
	for key, fieldname in CHILD_TABLE_MAP.items():
		rows = _child_rows(doc, fieldname)
		if key == "emergency_contacts" and not rows:
			# 兼容旧单字段紧急联系人
			if doc.person_to_be_contacted or doc.emergency_phone_number:
				rows = [
					{
						"name": "legacy",
						"contact_name": doc.person_to_be_contacted or "",
						"relationship": doc.relation or "",
						"mobile": _mask_phone(doc.emergency_phone_number, allow),
						"workplace": "",
						"address": "",
						"_legacy": 1,
					}
				]
		if key == "contracts":
			for row in rows:
				row["computed_status"] = _contract_status(
					row.get("start_date"), row.get("end_date"), row.get("contract_status") or ""
				)
		if key == "salary_history" and not allow:
			for row in rows:
				for mk in ("base_salary", "position_salary", "performance_salary", "allowance"):
					row[mk] = _mask_money(row.get(mk), False)
		if key in ("emergency_contacts", "family_members") and not allow:
			for row in rows:
				if row.get("mobile"):
					row["mobile"] = _mask_phone(row.get("mobile"), False)
		data[key] = rows

	# 若合同子表为空，回退展示当前主表合同字段为一条
	if not data["contracts"] and (
		doc.get("hr_contract_type") or doc.get("hr_contract_effective_from") or doc.get("hr_contract_expire_date")
	):
		data["contracts"] = [
			{
				"name": "current",
				"contract_type": doc.get("hr_contract_type") or "",
				"contract_no": "",
				"contract_company": doc.company or "",
				"start_date": str(doc.get("hr_contract_effective_from") or "")[:10],
				"end_date": str(doc.get("hr_contract_expire_date") or "")[:10],
				"signed_date": str(doc.get("hr_contract_signed_date") or "")[:10],
				"probation_months": doc.get("hr_probation_months") or "",
				"contract_status": _contract_status(
					doc.get("hr_contract_effective_from"),
					doc.get("hr_contract_expire_date"),
					doc.get("hr_contract_status") or "",
				),
				"computed_status": _contract_status(
					doc.get("hr_contract_effective_from"),
					doc.get("hr_contract_expire_date"),
					doc.get("hr_contract_status") or "",
				),
				"renewal_status": "",
				"attachment": "",
				"remarks": doc.get("hr_contract_remarks") or "",
				"_from_main": 1,
			}
		]

	data["materials"] = _material_groups(doc)
	data["archive_rate"] = _archive_rate(doc)
	return data


@frappe.whitelist()
def get_employee_archive(employee: str):
	"""返回员工档案完整预览数据。"""
	if not employee:
		frappe.throw(_("缺少员工编号"))
	if not _can_read_employee(employee):
		frappe.throw(_("无权查看该员工"), frappe.PermissionError)

	doc = frappe.get_doc("Employee", employee)
	reveal = _can_write_employee(employee) or "System Manager" in frappe.get_roles()
	return _serialize_employee(doc, reveal_sensitive=reveal)


def _parse_data(data):
	if isinstance(data, str):
		return frappe.parse_json(data) or {}
	return data or {}


def _validate_cn_id_number(id_number: str, *, date_of_birth: str | None = None) -> str | None:
	"""中国居民身份证 GB 11643：18 位、出生日期合法、校验位正确。"""
	import re
	from calendar import monthrange

	raw = str(id_number or "").strip().upper()
	if not raw:
		return "请填写身份证号码"
	if not re.fullmatch(r"\d{17}[\dX]", raw):
		return "身份证号码须为 18 位（17 位数字 + 校验位数字或 X）"

	try:
		y = int(raw[6:10])
		m = int(raw[10:12])
		d = int(raw[12:14])
		if m < 1 or m > 12 or d < 1 or d > monthrange(y, m)[1]:
			raise ValueError
		birth = getdate(f"{y:04d}-{m:02d}-{d:02d}")
	except Exception:
		return "身份证号码中的出生日期无效"

	if birth > getdate(today()):
		return "身份证号码中的出生日期不能晚于今天"

	weights = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
	check_map = "10X98765432"
	total = sum(int(raw[i]) * weights[i] for i in range(17))
	if check_map[total % 11] != raw[17]:
		return "身份证号码校验位不正确，请按国家标准核对"

	dob = str(date_of_birth or "").strip()[:10]
	if dob and dob.replace("-", "") != raw[6:14]:
		return "出生日期与身份证号码不一致"

	return None


def _validate_section(section: str, values: dict, doc) -> list[str]:
	errors = []

	def require(field, label):
		if not str(values.get(field) or "").strip():
			errors.append(f"{label}不能为空")

	if section == "employment_basic":
		for field, label in [
			("employee_number", "工号"),
			("department", "部门"),
			("designation", "岗位"),
			("hr_job_title", "职务"),
			("grade", "职级"),
			("company", "合同公司"),
			("reports_to", "汇报上级"),
			("hr_work_location", "工作地点"),
		]:
			# 兼容旧数据：空值时不强制阻断已有员工，仅当本次提交带了该字段且为空时提示
			if field in values:
				require(field, label)
	elif section == "employment_status":
		for field, label in [
			("employment_type", "工作性质"),
			("status", "员工状态"),
			("date_of_joining", "入职日期"),
			("hr_probation_months", "试用期"),
		]:
			if field in values:
				require(field, label)
	elif section == "personal_basic":
		for field, label in [
			("employee_name", "姓名"),
			("hr_id_type", "证件类型"),
			("hr_id_number", "证件号码"),
			("gender", "性别"),
			("date_of_birth", "出生日期"),
			("hr_country_region", "国家/地区"),
		]:
			if field in values:
				require(field, label)
		birth = str(values.get("date_of_birth") or "").strip()
		if birth and birth > str(today()):
			errors.append("出生日期不能晚于今天")
		id_number = str(values.get("hr_id_number") or "").strip()
		id_type = str(values.get("hr_id_type") or doc.get("hr_id_type") or "身份证").strip()
		if id_type == "身份证" and id_number:
			msg = _validate_cn_id_number(id_number, date_of_birth=birth or doc.get("date_of_birth"))
			if msg:
				errors.append(msg)
	elif section == "contact_basic":
		if "cell_number" in values:
			require("cell_number", "手机号码")
	elif section == "overview_basic":
		for field, label in [
			("employee_name", "员工姓名"),
			("hr_id_number", "证件号码"),
			("gender", "性别"),
			("designation", "岗位"),
			("cell_number", "手机号码"),
			("current_address", "现居住地"),
			("status", "员工状态"),
			("employee_number", "工号"),
			("date_of_joining", "入职时间"),
		]:
			if field in values:
				require(field, label)
		id_number = str(values.get("hr_id_number") or "").strip()
		id_type = str(values.get("hr_id_type") or doc.get("hr_id_type") or "身份证").strip()
		if id_type == "身份证" and id_number:
			msg = _validate_cn_id_number(
				id_number, date_of_birth=str(values.get("date_of_birth") or doc.get("date_of_birth") or "")
			)
			if msg:
				errors.append(msg)
		phone = str(values.get("cell_number") or "").strip()
		if phone:
			import re

			if not re.fullmatch(r"\+?[0-9\s()\-]{6,24}", phone):
				errors.append("手机号格式不正确")
	elif section == "overview_org":
		for field, label in [
			("company", "所属公司"),
			("department", "所属部门"),
			("designation", "岗位"),
			("reports_to", "汇报上级"),
			("employment_type", "工作性质"),
		]:
			if field in values:
				require(field, label)
	elif section == "salary_ss":
		ss_status = values.get("hr_ss_status", doc.get("hr_ss_status"))
		if ss_status == "已参保":
			for field, label in [
				("hr_social_security_city", "参保城市"),
				("hr_ss_start_date", "社保开始日期"),
				("hr_social_security_base", "社保基数"),
			]:
				if field in values:
					require(field, label)
		hf_status = values.get("hr_hf_status", doc.get("hr_hf_status"))
		if hf_status == "已缴纳":
			for field, label in [
				("hr_hf_city", "公积金缴纳城市"),
				("hr_hf_start_date", "公积金开始日期"),
				("hr_housing_fund_base", "公积金基数"),
			]:
				if field in values:
					require(field, label)
	elif section == "contract_row":
		for field, label in [
			("contract_type", "合同类型"),
			("contract_no", "合同编号"),
			("contract_company", "合同公司"),
			("start_date", "合同开始日期"),
			("signed_date", "签订日期"),
		]:
			require(field, label)
		if values.get("contract_type") == "固定期限劳动合同":
			require("end_date", "合同结束日期")
	elif section == "emergency_row":
		for field, label in [
			("contact_name", "姓名"),
			("relationship", "关系"),
			("mobile", "手机号码"),
		]:
			require(field, label)

	return errors


@frappe.whitelist()
def save_employee_section(employee: str, section: str, data: dict | str | None = None):
	"""按板块保存员工主表字段。"""
	if not employee:
		frappe.throw(_("缺少员工编号"))
	if not _can_write_employee(employee):
		frappe.throw(_("无权编辑该员工"), frappe.PermissionError)

	values = _parse_data(data)
	allowed = set(SECTION_FIELD_MAP.get(section) or [])
	if not allowed:
		frappe.throw(_("未知板块：{0}").format(section))

	doc = frappe.get_doc("Employee", employee)
	errors = _validate_section(section, values, doc)
	if errors:
		frappe.throw("<br>".join(errors), title=_("请检查必填项"))

	# 薪资调整：若修改了薪资字段，追加历史
	if section == "salary_pay" and doc.meta.has_field("hr_salary_history"):
		changed = any(
			str(values.get(k) or "") != str(doc.get(k) or "")
			for k in ("hr_base_salary", "hr_position_salary", "hr_performance_salary", "hr_allowance", "hr_salary_type")
			if k in values
		)
		if changed:
			doc.append(
				"hr_salary_history",
				{
					"effective_date": values.get("hr_salary_effective_date") or today(),
					"salary_type": values.get("hr_salary_type", doc.get("hr_salary_type")),
					"base_salary": values.get("hr_base_salary", doc.get("hr_base_salary")),
					"position_salary": values.get("hr_position_salary", doc.get("hr_position_salary")),
					"performance_salary": values.get("hr_performance_salary", doc.get("hr_performance_salary")),
					"allowance": values.get("hr_allowance", doc.get("hr_allowance")),
					"remarks": values.get("hr_salary_remarks", doc.get("hr_salary_remarks")),
				},
			)

	if section == "salary_ss" and doc.meta.has_field("hr_ss_history"):
		changed = any(
			str(values.get(k) or "") != str(doc.get(k) or "")
			for k in (
				"hr_ss_status",
				"hr_social_security_city",
				"hr_social_security_base",
				"hr_hf_status",
				"hr_hf_city",
				"hr_housing_fund_base",
			)
			if k in values
		)
		if changed:
			doc.append(
				"hr_ss_history",
				{
					"record_date": today(),
					"ss_status": values.get("hr_ss_status", doc.get("hr_ss_status")),
					"ss_city": values.get("hr_social_security_city", doc.get("hr_social_security_city")),
					"ss_base": values.get("hr_social_security_base", doc.get("hr_social_security_base")),
					"hf_status": values.get("hr_hf_status", doc.get("hr_hf_status")),
					"hf_city": values.get("hr_hf_city", doc.get("hr_hf_city")),
					"hf_base": values.get("hr_housing_fund_base", doc.get("hr_housing_fund_base")),
				},
			)

	for key, val in values.items():
		if key not in allowed:
			continue
		# 只读计算字段禁止写入
		if key in ("hr_total_work_years", "age", "birthday", "company_tenure_years"):
			continue
		if not doc.meta.has_field(key):
			continue
		df = doc.meta.get_field(key)
		if val == "" or val is None:
			if df and df.fieldtype in (
				"Int",
				"Float",
				"Currency",
				"Percent",
				"Date",
				"Datetime",
				"Time",
				"Link",
				"Dynamic Link",
				"Data",
				"Select",
				"Small Text",
				"Text",
				"Long Text",
				"Text Editor",
			):
				# 空字符串写入 Date/Float/Link 会触发底层异常；统一落成 None
				if df.fieldtype in ("Int", "Float", "Currency", "Percent", "Date", "Datetime", "Time", "Link", "Dynamic Link"):
					val = None
				else:
					val = ""
		doc.set(key, val)

	# 姓名同步 first_name
	if "employee_name" in values and values.get("employee_name"):
		doc.first_name = values["employee_name"]
		doc.employee_name = values["employee_name"]

	# 别名与曾用名合并：只保留曾用名
	if section == "personal_basic" and doc.meta.has_field("hr_alias"):
		alias = str(doc.get("hr_alias") or "").strip()
		former = str(doc.get("hr_former_name") or "").strip()
		if not former and alias:
			doc.hr_former_name = alias
		doc.hr_alias = None

	# 板块局部保存：已做板块校验，不因其他页签空必填/空链接阻断
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_links = True
	doc.save()
	reveal = True
	return _serialize_employee(frappe.get_doc("Employee", employee), reveal_sensitive=reveal)


@frappe.whitelist()
def save_employee_child_row(
	employee: str, table_key: str, row: dict | str | None = None, delete: int = 0
):
	"""新增/更新/删除一对多子表记录。"""
	if not employee:
		frappe.throw(_("缺少员工编号"))
	if not _can_write_employee(employee):
		frappe.throw(_("无权编辑该员工"), frappe.PermissionError)

	fieldname = CHILD_TABLE_MAP.get(table_key)
	if not fieldname:
		frappe.throw(_("未知子表：{0}").format(table_key))

	payload = _parse_data(row)
	doc = frappe.get_doc("Employee", employee)
	if not doc.meta.has_field(fieldname):
		frappe.throw(_("系统尚未启用该档案子表，请先执行数据库迁移"))

	# 校验
	if not cint(delete):
		section = {
			"contracts": "contract_row",
			"emergency_contacts": "emergency_row",
		}.get(table_key)
		if section:
			errors = _validate_section(section, payload, doc)
			if errors:
				frappe.throw("<br>".join(errors), title=_("请检查必填项"))

	row_name = payload.get("name")
	if cint(delete):
		if not row_name:
			frappe.throw(_("缺少行标识"))
		doc.set(fieldname, [r for r in (doc.get(fieldname) or []) if r.name != row_name])
	else:
		# 清理内部标记
		for k in list(payload.keys()):
			if k.startswith("_") or k in ("parent", "parenttype", "parentfield", "doctype", "idx"):
				payload.pop(k, None)
		if row_name and row_name not in ("legacy", "current"):
			found = False
			for r in doc.get(fieldname) or []:
				if r.name == row_name:
					for k, v in payload.items():
						if k == "name":
							continue
						r.set(k, v)
					found = True
					break
			if not found:
				frappe.throw(_("记录不存在或已删除"))
		else:
			payload.pop("name", None)
			doc.append(fieldname, payload)

		# 同步旧紧急联系人字段（取第一条）
		if table_key == "emergency_contacts":
			rows = doc.get("hr_emergency_contacts") or []
			if rows:
				first = rows[0]
				doc.person_to_be_contacted = first.contact_name
				doc.relation = first.relationship
				doc.emergency_phone_number = first.mobile

		# 同步主表合同摘要（取最新一条）
		if table_key == "contracts":
			rows = doc.get("hr_contracts") or []
			if rows:
				latest = sorted(rows, key=lambda r: str(r.start_date or ""), reverse=True)[0]
				doc.hr_contract_type = latest.contract_type
				doc.hr_contract_status = latest.contract_status or _contract_status(
					latest.start_date, latest.end_date
				)
				doc.hr_contract_effective_from = latest.start_date
				doc.hr_contract_expire_date = latest.end_date
				doc.hr_contract_signed_date = latest.signed_date
				doc.hr_contract_times = len(rows)
				if latest.contract_company:
					doc.company = latest.contract_company

	doc.flags.ignore_mandatory = True
	doc.save()
	return _serialize_employee(frappe.get_doc("Employee", employee), reveal_sensitive=True)


@frappe.whitelist()
def save_employee_material(employee: str, fieldname: str, file_url: str = ""):
	"""更新材料附件字段。"""
	if not employee:
		frappe.throw(_("缺少员工编号"))
	if not _can_write_employee(employee):
		frappe.throw(_("无权编辑该员工"), frappe.PermissionError)
	allowed = set(SECTION_FIELD_MAP.get("materials") or [])
	if fieldname not in allowed:
		frappe.throw(_("非法附件字段"))
	doc = frappe.get_doc("Employee", employee)
	if not doc.meta.has_field(fieldname):
		frappe.throw(_("附件字段尚未就绪，请先执行数据库迁移"))
	doc.set(fieldname, file_url or None)
	doc.flags.ignore_mandatory = True
	doc.save()
	return _serialize_employee(frappe.get_doc("Employee", employee), reveal_sensitive=True)


def _month_bounds():
	t = getdate(today())
	start = t.replace(day=1)
	return str(start), str(t)


def _attendance_summary(employee: str) -> dict:
	"""本月真实考勤：出勤天数 / 请假小时 / 迟到次数 / 加班小时。"""
	month_start, month_end = _month_bounds()
	result = {
		"month": month_start[:7],
		"attendance_days": 0,
		"leave_hours": 0,
		"late_count": 0,
		"overtime_hours": 0,
		"error": None,
	}
	try:
		if frappe.db.exists("DocType", "Attendance"):
			result["attendance_days"] = frappe.db.count(
				"Attendance",
				{
					"employee": employee,
					"attendance_date": ["between", [month_start, month_end]],
					"status": ["in", ["Present", "Work From Home"]],
					"docstatus": 1,
				},
			)
			result["late_count"] = frappe.db.count(
				"Attendance",
				{
					"employee": employee,
					"attendance_date": ["between", [month_start, month_end]],
					"late_entry": 1,
					"docstatus": 1,
				},
			)
			# 出勤记录上的加班时长
			ot_rows = frappe.get_all(
				"Attendance",
				filters={
					"employee": employee,
					"attendance_date": ["between", [month_start, month_end]],
					"docstatus": 1,
				},
				fields=["actual_overtime_duration"],
			)
			ot_sum = 0.0
			for row in ot_rows:
				val = row.get("actual_overtime_duration")
				if val is not None:
					try:
						ot_sum += float(val)
					except (TypeError, ValueError):
						pass
			result["overtime_hours"] = round(ot_sum, 1)

			# 请假：本月 Leave Application（已批准）按天 * 8 小时
			leave_hours = 0.0
			if frappe.db.exists("DocType", "Leave Application"):
				leaves = frappe.get_all(
					"Leave Application",
					filters={
						"employee": employee,
						"status": "Approved",
						"docstatus": 1,
						"from_date": ["<=", month_end],
						"to_date": [">=", month_start],
					},
					fields=["from_date", "to_date", "total_leave_days", "half_day"],
				)
				ms = getdate(month_start)
				me = getdate(month_end)
				for leave in leaves:
					try:
						lf = getdate(leave.from_date)
						lt = getdate(leave.to_date)
						overlap_start = max(lf, ms)
						overlap_end = min(lt, me)
						days = (overlap_end - overlap_start).days + 1
						if days < 0:
							continue
						# 半日假按 0.5 天
						if cint(leave.get("half_day")) and days == 1:
							days = 0.5
						elif leave.total_leave_days is not None and lf >= ms and lt <= me:
							days = float(leave.total_leave_days)
						leave_hours += float(days) * 8.0
					except Exception:
						continue
			# On Leave 出勤也计入
			on_leave_days = frappe.db.count(
				"Attendance",
				{
					"employee": employee,
					"attendance_date": ["between", [month_start, month_end]],
					"status": "On Leave",
					"docstatus": 1,
				},
			)
			if on_leave_days and leave_hours <= 0:
				leave_hours = float(on_leave_days) * 8.0
			result["leave_hours"] = round(leave_hours, 1)
	except Exception as e:
		result["error"] = str(e)[:200]
	return result


def _profile_checklist(doc) -> dict:
	"""档案完整度：基于真实员工字段/附件/紧急联系人。"""
	email = doc.company_email or doc.personal_email or ""
	has_id = bool(doc.get("hr_id_number") or doc.get("passport_number"))
	has_id_attach = bool(doc.get("hr_attach_id_front") or doc.get("hr_attach_id_back"))
	emergency_rows = _child_rows(doc, "hr_emergency_contacts")
	has_emergency = bool(emergency_rows) or bool(doc.person_to_be_contacted and doc.emergency_phone_number)

	items = [
		{
			"key": "cell_number",
			"label": "手机号",
			"action_label": "补充手机号",
			"done": bool(doc.cell_number),
			"target": "contact",
		},
		{
			"key": "email",
			"label": "邮箱",
			"action_label": "补充邮箱",
			"done": bool(email),
			"target": "contact",
		},
		{
			"key": "id",
			"label": "身份证",
			"action_label": "上传身份证",
			"done": has_id and has_id_attach if doc.meta.has_field("hr_attach_id_front") else has_id,
			"target": "materials",
		},
		{
			"key": "emergency",
			"label": "紧急联系人",
			"action_label": "补充紧急联系人",
			"done": has_emergency,
			"target": "emergency",
		},
	]
	done = sum(1 for i in items if i["done"])
	total = len(items)
	return {
		"rate": round(done / total * 100) if total else 0,
		"done": done,
		"total": total,
		"items": items,
	}


def _growth_timeline(doc) -> list[dict]:
	"""真实成长记录：入职/转正/任职变动/培训/奖惩等。"""
	events = []

	if doc.date_of_joining:
		join_desc = f"加入{doc.company}" if doc.company else (doc.designation or doc.department or "")
		events.append(
			{
				"key": f"join-{doc.date_of_joining}",
				"date": str(doc.date_of_joining)[:10],
				"title": "入职",
				"description": join_desc,
				"type": "join",
				"target": "on_job",
			}
		)

	if doc.final_confirmation_date:
		events.append(
			{
				"key": f"confirm-{doc.final_confirmation_date}",
				"date": str(doc.final_confirmation_date)[:10],
				"title": "转正",
				"description": "通过试用期考核，正式转正",
				"type": "confirm",
				"target": "on_job",
			}
		)

	for row in _child_rows(doc, "internal_work_history"):
		date = str(row.get("from_date") or "")[:10]
		if not date:
			continue
		title_parts = [x for x in [row.get("designation"), row.get("department")] if x]
		events.append(
			{
				"key": f"internal-{row.get('name') or date}",
				"date": date,
				"title": "岗位变动",
				"description": " · ".join(title_parts) if title_parts else "",
				"type": "transfer",
				"target": "internal_work_history",
			}
		)

	for row in _child_rows(doc, "hr_trainings"):
		date = str(row.get("start_date") or row.get("end_date") or "")[:10]
		if not date and not row.get("training_name"):
			continue
		events.append(
			{
				"key": f"train-{row.get('name') or date}",
				"date": date or "",
				"title": "培训记录",
				"description": row.get("training_name") or row.get("organizer") or "",
				"type": "training",
				"target": "trainings",
			}
		)

	for row in _child_rows(doc, "hr_rewards"):
		date = str(row.get("occur_date") or "")[:10]
		record_type = row.get("record_type") or ""
		title = "获得荣誉" if record_type == "奖励" else (record_type or "奖惩")
		events.append(
			{
				"key": f"reward-{row.get('name') or date}",
				"date": date,
				"title": title,
				"description": row.get("title") or "",
				"type": "reward",
				"target": "rewards",
			}
		)

	# Employee Transfer / Promotion（若有权限可读）
	for doctype, title, date_field in (
		("Employee Transfer", "人事调动", "transfer_date"),
		("Employee Promotion", "晋升", "promotion_date"),
	):
		if not frappe.db.exists("DocType", doctype):
			continue
		try:
			rows = frappe.get_all(
				doctype,
				filters={"employee": doc.name, "docstatus": ["<", 2]},
				fields=["name", date_field],
				order_by=f"{date_field} desc",
				limit=20,
			)
		except Exception:
			continue
		for row in rows:
			date = str(row.get(date_field) or "")[:10]
			if not date:
				continue
			events.append(
				{
					"key": f"{doctype}-{row.name}",
					"date": date,
					"title": title,
					"description": "",
					"type": "movement",
					"target": "on_job",
				}
			)

	# 去重：同日同标题保留一条
	seen = set()
	unique = []
	for ev in events:
		sig = (ev.get("date"), ev.get("title"), ev.get("description"))
		if sig in seen:
			continue
		seen.add(sig)
		unique.append(ev)

	unique.sort(key=lambda x: x.get("date") or "", reverse=True)
	return unique


@frappe.whitelist()
def get_employee_overview(employee: str):
	"""概况页专用：员工摘要 + 考勤 + 档案完整度 + 成长时间线。"""
	if not employee:
		frappe.throw(_("缺少员工编号"))
	if not _can_read_employee(employee):
		frappe.throw(_("无权查看该员工"), frappe.PermissionError)

	doc = frappe.get_doc("Employee", employee)
	reveal = _can_write_employee(employee) or "System Manager" in frappe.get_roles()

	employment_labels = {
		"Full-time": "全职",
		"Part-time": "兼职",
		"Intern": "实习",
		"Probation": "试用期",
		"Contract": "合同工",
	}

	attendance = _attendance_summary(employee)
	checklist = _profile_checklist(doc)
	timeline = _growth_timeline(doc)

	return {
		"name": doc.name,
		"employee_name": doc.employee_name or doc.first_name or "",
		"employee_number": doc.employee_number or "",
		"status": doc.status or "",
		"gender": doc.gender or "",
		"designation": doc.designation or "",
		"department": doc.department or "",
		"company": doc.company or "",
		"branch": doc.branch or "",
		"group_name": doc.get("group_name") or "",
		"grade": doc.grade or "",
		"reports_to": doc.reports_to or "",
		"employment_type": doc.employment_type or "",
		"employment_type_label": employment_labels.get(doc.employment_type, doc.employment_type or ""),
		"date_of_joining": str(doc.date_of_joining or "")[:10],
		"current_address": doc.current_address or "",
		"cell_number": _mask_phone(doc.cell_number, reveal),
		"cell_number_raw": (doc.cell_number or "") if reveal else "",
		"hr_id_number": _mask_id(doc.get("hr_id_number"), reveal),
		"hr_id_number_raw": (doc.get("hr_id_number") or "") if reveal else "",
		"hr_work_location": doc.get("hr_work_location") or doc.branch or "",
		"hr_work_city": doc.get("hr_work_city") or "",
		"image": doc.image or "",
		"can_edit": _can_write_employee(doc.name),
		"can_view_sensitive": reveal,
		"attendance": attendance,
		"profile_checklist": checklist,
		"profile_completion": checklist["rate"],
		"growth_timeline": timeline,
	}
