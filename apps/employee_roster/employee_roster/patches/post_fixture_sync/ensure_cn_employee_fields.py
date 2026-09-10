# Copyright (c) 2026 stillgroup
# License: MIT
"""员工详情 — 中国 HR 字段与页签补齐。

页签：概览 / 在职信息 / 个人信息 / 联系信息 / 工资社保 / 合同信息 / 材料附件 /
背景调查 / 履历资料 / 考勤假期 / 离职办理 / 更多。
所有新增字段带 hr_ 前缀，不改动 erpnext / hrms 原生字段结构。
"""

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


TAB_LABELS = {
	"basic_details_tab": "概览",
	"employment_details": "在职信息",
	"personal_details": "个人信息",
	"contact_details": "联系信息",
	"salary_information": "工资社保",
	"hr_contract_tab": "合同信息",
	"hr_materials_tab": "材料附件",
	"hr_background_tab": "背景调查",
	"profile_tab": "履历资料",
	"attendance_and_leave_details": "考勤假期",
	"exit": "离职办理",
	"connections_tab": "更多",
}

FIELD_LABELS = {
	"naming_series": "编号规则",
	"first_name": "名",
	"middle_name": "中间名",
	"last_name": "姓",
	"employee_name": "员工姓名",
	"user_id": "关联用户",
	"create_user_permission": "创建用户权限",
	"salutation": "称谓",
	"image": "员工照片",
	"employee_number": "工号",
	"company": "合同公司",
	"department": "部门",
	"designation": "岗位",
	"grade": "职级",
	"reports_to": "汇报上级",
	"branch": "分支机构",
	"employment_type": "工作性质",
	"date_of_joining": "入职日期",
	"date_of_birth": "出生日期",
	"scheduled_confirmation_date": "预计转正日期",
	"final_confirmation_date": "转正日期",
	"contract_end_date": "合同到期日期",
	"notice_number_of_days": "离职通知期(天)",
	"date_of_retirement": "退休日期",
	"holiday_list": "节假日列表",
	"cell_number": "手机号",
	"company_email": "公司邮箱",
	"personal_email": "个人邮箱",
	"prefered_contact_email": "首选联系邮箱",
	"prefered_email": "首选邮箱",
	"person_to_be_contacted": "紧急联系人",
	"emergency_phone_number": "紧急联系电话",
	"relation": "与本人关系",
	"current_address": "居住地址",
	"permanent_address": "永久地址",
	"current_accommodation_type": "居住地址类型",
	"permanent_accommodation_type": "永久地址类型",
	"marital_status": "婚姻状况",
	"blood_group": "血型",
	"family_background": "家庭背景",
	"health_details": "健康状况",
	"passport_number": "护照号码",
	"date_of_issue": "签发日期",
	"valid_upto": "有效期至",
	"place_of_issue": "签发地点",
	"salary_mode": "工资发放方式",
	"bank_name": "开户银行",
	"bank_ac_no": "银行卡号",
	"salary_currency": "薪资币种",
	"ctc": "年度薪酬总额(CTC)",
	"health_insurance_provider": "商业保险供应商",
	"health_insurance_no": "商业保险单号",
	"attendance_device_id": "考勤编号",
	"default_shift": "默认班次",
	"education": "教育经历",
	"external_work_history": "外部工作经历",
	"internal_work_history": "公司内部履历",
	"bio": "个人简介",
	"status": "员工状态",
	"gender": "性别",
	"resignation_letter_date": "辞职信日期",
	"relieving_date": "离职日期",
	"reason_for_leaving": "离职原因",
	"held_on": "离职面谈日期",
	"new_workplace": "新工作单位",
	"feedback": "反馈",
}

CHILD_FIELD_LABELS = {
	"Employee Education": {
		"school_univ": "学校/院校",
		"qualification": "学历/资格",
		"level": "学历层次",
		"year_of_passing": "毕业年份",
		"class_per": "成绩/百分比",
		"maj_opt_subj": "专业/选修科目",
	},
	"Employee External Work History": {
		"company_name": "公司名称",
		"designation": "岗位",
		"salary": "薪资",
		"address": "公司地址",
		"contact": "证明人联系方式",
		"total_experience": "工作年限",
	},
	"Employee Internal Work History": {
		"department": "部门",
		"designation": "岗位",
		"from_date": "开始日期",
		"to_date": "结束日期",
	},
}


# 在职信息页签内容（field_order 重排后紧跟 employment_details Tab Break）
ON_JOB_TAB_FIELDS = [
	"hr_org_section",
	"employee_number",
	"company",
	"department",
	"group_name",
	"designation",
	"hr_job_title",
	"hr_position_category",
	"hr_concurrent_post",
	"hr_org_col",
	"reports_to",
	"hr_employee_identity",
	"grade",
	"hr_job_grade_level",
	"employment_type",
	"branch",
	"hr_workplace_section",
	"hr_work_city",
	"hr_work_location",
	"hr_work_address",
	"hr_workplace_col",
	"hr_work_hours_system",
	"hr_recruitment_channel",
	"hr_oa_code",
	"attendance_device_id",
	"hr_joining_section",
	"status",
	"date_of_joining",
	"hr_probation_months",
]

# 个人信息「基本信息」分区：把原生性别从概览挪进来
PERSONAL_BASIC_FIELDS = [
	"gender",
]


def execute():
	_ensure_custom_fields()
	_upgrade_org_select_fields()
	_ensure_gender_options()
	_ensure_labels()
	_ensure_child_labels()
	_hide_default_shift()
	_hide_employee_alias()
	_reorder_employee_fields()
	frappe.clear_cache(doctype="Employee")


def _hide_default_shift():
	"""考勤假期页不再展示「默认班次」。"""
	if not frappe.db.exists("DocField", {"parent": "Employee", "fieldname": "default_shift"}):
		return
	key = "Employee-default_shift-hidden"
	if frappe.db.exists("Property Setter", key):
		frappe.db.set_value("Property Setter", key, "value", "1")
	else:
		make_property_setter("Employee", "default_shift", "hidden", 1, "Check")


def _hide_employee_alias():
	"""别名与曾用名合并，Desk 表单隐藏「别名」。"""
	if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": "hr_alias"}):
		return
	key = "Employee-hr_alias-hidden"
	if frappe.db.exists("Property Setter", key):
		frappe.db.set_value("Property Setter", key, "value", "1")
	else:
		make_property_setter("Employee", "hr_alias", "hidden", 1, "Check")
	frappe.db.set_value("Custom Field", {"dt": "Employee", "fieldname": "hr_alias"}, "hidden", 1)

JOB_TITLE_OPTIONS = "\n总经理\n副总经理\n总监\n高级经理\n经理\n主管\n组长\n专员\n助理\n实习生\n其他"
JOB_GRADE_OPTIONS = "\n" + "\n".join(str(i) for i in range(1, 16))

ORG_SELECT_FIELD_UPGRADES = {
	"group_name": {"fieldtype": "Autocomplete", "options": ""},
	"hr_job_title": {"fieldtype": "Autocomplete", "options": JOB_TITLE_OPTIONS},
	"hr_job_grade_level": {"fieldtype": "Select", "options": JOB_GRADE_OPTIONS},
	"hr_concurrent_post": {"fieldtype": "Link", "options": "Designation"},
}


def _upgrade_org_select_fields():
	"""组织信息：自由文本改为下拉/联想选择。"""
	for fieldname, props in ORG_SELECT_FIELD_UPGRADES.items():
		name = f"Employee-{fieldname}"
		if not frappe.db.exists("Custom Field", name):
			continue
		cf = frappe.get_doc("Custom Field", name)
		changed = False
		for key, value in props.items():
			if cf.get(key) != value:
				cf.set(key, value)
				changed = True
		if changed:
			cf.flags.ignore_validate = True
			cf.save()


def _job_fields():
	"""在职信息：插入 employment_details 页签既有字段之间。"""
	return [
		{
			"fieldname": "hr_org_section",
			"fieldtype": "Section Break",
			"label": "组织信息",
			"insert_after": "employment_details",
		},
		{"fieldname": "hr_org_col", "fieldtype": "Column Break", "insert_after": "hr_org_section"},
		{
			"fieldname": "hr_workplace_section",
			"fieldtype": "Section Break",
			"label": "工作地点与制度",
			"insert_after": "hr_org_col",
		},
		{"fieldname": "hr_workplace_col", "fieldtype": "Column Break", "insert_after": "hr_workplace_section"},
		{
			"fieldname": "hr_joining_section",
			"fieldtype": "Section Break",
			"label": "入职与转正",
			"insert_after": "hr_workplace_col",
		},
		{"fieldname": "hr_job_title", "fieldtype": "Autocomplete", "label": "职务", "insert_after": "designation", "options": JOB_TITLE_OPTIONS},
		{
			"fieldname": "hr_position_category",
			"fieldtype": "Select",
			"label": "岗位类别",
			"options": "\n管理类\n技术类\n客服类\n销售类\n职能类\n运营类\n其他",
			"insert_after": "hr_job_title",
		},
		{
			"fieldname": "hr_job_grade_level",
			"fieldtype": "Select",
			"label": "职等",
			"options": JOB_GRADE_OPTIONS,
			"insert_after": "grade",
		},
		{
			"fieldname": "hr_concurrent_post",
			"fieldtype": "Link",
			"label": "兼任",
			"options": "Designation",
			"insert_after": "hr_job_grade_level",
		},
		{
			"fieldname": "hr_employee_identity",
			"fieldtype": "Select",
			"label": "身份",
			"options": "\n普通成员\n部门负责人\n组织负责人",
			"insert_after": "reports_to",
		},
		{"fieldname": "hr_work_city", "fieldtype": "Data", "label": "工作城市", "insert_after": "branch"},
		{"fieldname": "hr_work_location", "fieldtype": "Data", "label": "工作地点", "insert_after": "hr_work_city"},
		{
			"fieldname": "hr_work_address",
			"fieldtype": "Small Text",
			"label": "详细工作地址",
			"insert_after": "hr_work_location",
		},
		{
			"fieldname": "hr_work_hours_system",
			"fieldtype": "Select",
			"label": "工时制度",
			"options": "\n标准工时\n综合工时\n不定时工时",
			"insert_after": "hr_work_address",
		},
		{
			"fieldname": "hr_recruitment_channel",
			"fieldtype": "Data",
			"label": "招聘渠道",
			"insert_after": "hr_work_hours_system",
		},
		{"fieldname": "hr_oa_code", "fieldtype": "Data", "label": "OA编码", "insert_after": "hr_recruitment_channel"},
		{
			"fieldname": "hr_probation_months",
			"fieldtype": "Select",
			"label": "试用期(月)",
			"options": "\n无试用期\n1\n2\n3\n6",
			"insert_after": "date_of_joining",
		},
	]


def _personal_fields():
	"""个人信息：置于 personal_details 页签顶部（基本信息分区）。"""
	return [
		{
			"fieldname": "hr_personal_basic_section",
			"fieldtype": "Section Break",
			"label": "基本信息",
			"insert_after": "personal_details",
		},
		{"fieldname": "hr_former_name", "fieldtype": "Data", "label": "曾用名", "insert_after": "hr_personal_basic_section"},
		{
			"fieldname": "hr_id_type",
			"fieldtype": "Select",
			"label": "证件类型",
			"options": "\n身份证\n护照\n港澳通行证\n台胞证\n其他",
			"default": "身份证",
			"insert_after": "hr_former_name",
		},
		{"fieldname": "hr_id_number", "fieldtype": "Data", "label": "证件号码", "insert_after": "hr_id_type"},
		{"fieldname": "hr_id_valid_until", "fieldtype": "Date", "label": "证件有效期", "insert_after": "hr_id_number"},
		{"fieldname": "hr_work_start_date", "fieldtype": "Date", "label": "参加工作时间", "insert_after": "hr_id_valid_until"},
		{"fieldname": "hr_total_work_years", "fieldtype": "Data", "label": "工龄", "insert_after": "hr_work_start_date"},
		{"fieldname": "hr_personal_col_1", "fieldtype": "Column Break", "insert_after": "hr_total_work_years"},
		{"fieldname": "hr_alias", "fieldtype": "Data", "label": "别名", "insert_after": "hr_personal_col_1", "hidden": 1},
		{
			"fieldname": "hr_has_children",
			"fieldtype": "Select",
			"label": "是否已育",
			"options": "\n是\n否",
			"insert_after": "hr_alias",
		},
		{
			"fieldname": "hr_country_region",
			"fieldtype": "Data",
			"label": "国家/地区",
			"default": "中国",
			"insert_after": "hr_has_children",
		},
		{"fieldname": "hr_ethnicity", "fieldtype": "Data", "label": "民族", "insert_after": "hr_country_region"},
		{
			"fieldname": "hr_political_status",
			"fieldtype": "Select",
			"label": "政治面貌",
			"options": "\n群众\n共青团员\n中共党员\n民主党派\n其他",
			"insert_after": "hr_ethnicity",
		},
		{
			"fieldname": "hr_household_section",
			"fieldtype": "Section Break",
			"label": "户籍与身体信息",
			"insert_after": "hr_political_status",
		},
		{"fieldname": "hr_native_place", "fieldtype": "Data", "label": "籍贯", "insert_after": "hr_household_section"},
		{"fieldname": "hr_household_city", "fieldtype": "Data", "label": "户籍城市", "insert_after": "hr_native_place"},
		{
			"fieldname": "hr_household_type",
			"fieldtype": "Select",
			"label": "户口性质",
			"options": "\n本地城镇\n本地农村\n外地城镇\n外地农村\n其他",
			"insert_after": "hr_household_city",
		},
		{
			"fieldname": "hr_household_address",
			"fieldtype": "Small Text",
			"label": "户籍地址",
			"insert_after": "hr_household_type",
		},
		{"fieldname": "hr_personal_col_2", "fieldtype": "Column Break", "insert_after": "hr_household_address"},
		{
			"fieldname": "hr_social_security_household",
			"fieldtype": "Data",
			"label": "社保户籍",
			"insert_after": "hr_personal_col_2",
		},
		{"fieldname": "hr_height", "fieldtype": "Data", "label": "身高(cm)", "insert_after": "hr_social_security_household"},
		{"fieldname": "hr_weight", "fieldtype": "Data", "label": "体重(kg)", "insert_after": "hr_height"},
	]


def _contact_fields():
	return [
		{"fieldname": "hr_wechat", "fieldtype": "Data", "label": "微信号", "insert_after": "cell_number"},
	]


def _social_insurance_fields():
	"""工资社保：社保公积金分区，插在 salary 页签 IBAN 之后。"""
	return [
		{
			"fieldname": "hr_social_insurance_section",
			"fieldtype": "Section Break",
			"label": "社保公积金",
			"insert_after": "iban",
		},
		{
			"fieldname": "hr_social_security_city",
			"fieldtype": "Data",
			"label": "参保城市",
			"insert_after": "hr_social_insurance_section",
		},
		{
			"fieldname": "hr_social_security_no",
			"fieldtype": "Data",
			"label": "社保电脑号",
			"insert_after": "hr_social_security_city",
		},
		{
			"fieldname": "hr_social_security_base",
			"fieldtype": "Currency",
			"label": "社保基数",
			"insert_after": "hr_social_security_no",
		},
		{"fieldname": "hr_ss_col_break", "fieldtype": "Column Break", "insert_after": "hr_social_security_base"},
		{"fieldname": "hr_housing_fund_no", "fieldtype": "Data", "label": "公积金账号", "insert_after": "hr_ss_col_break"},
		{
			"fieldname": "hr_housing_fund_base",
			"fieldtype": "Currency",
			"label": "公积金基数",
			"insert_after": "hr_housing_fund_no",
		},
	]


def _contract_tab_fields(anchor):
	"""合同信息页签（新建，链式追加在字段流末尾）。"""
	return [
		{"fieldname": "hr_contract_tab", "fieldtype": "Tab Break", "label": "合同信息", "insert_after": anchor},
		{
			"fieldname": "hr_contract_section",
			"fieldtype": "Section Break",
			"label": "劳动合同",
			"insert_after": "hr_contract_tab",
		},
		{
			"fieldname": "hr_contract_type",
			"fieldtype": "Select",
			"label": "合同类型",
			"options": "\n固定期限劳动合同\n无固定期限劳动合同\n实习协议\n劳务合同\n劳务派遣\n退休返聘\n其他",
			"insert_after": "hr_contract_section",
		},
		{
			"fieldname": "hr_contract_status",
			"fieldtype": "Select",
			"label": "合同状态",
			"options": "\n未签订\n履行中\n已到期\n已解除\n已终止",
			"insert_after": "hr_contract_type",
		},
		{
			"fieldname": "hr_contract_signed_date",
			"fieldtype": "Date",
			"label": "首次签订日期",
			"insert_after": "hr_contract_status",
		},
		{"fieldname": "hr_contract_col_1", "fieldtype": "Column Break", "insert_after": "hr_contract_signed_date"},
		{
			"fieldname": "hr_contract_effective_from",
			"fieldtype": "Date",
			"label": "合同开始日期",
			"insert_after": "hr_contract_col_1",
		},
		{
			"fieldname": "hr_contract_expire_date",
			"fieldtype": "Date",
			"label": "合同到期日期",
			"insert_after": "hr_contract_effective_from",
		},
		{"fieldname": "hr_contract_times", "fieldtype": "Int", "label": "签订次数", "insert_after": "hr_contract_expire_date"},
		{
			"fieldname": "hr_contract_remark_section",
			"fieldtype": "Section Break",
			"label": "备注",
			"insert_after": "hr_contract_times",
		},
		{
			"fieldname": "hr_contract_remarks",
			"fieldtype": "Small Text",
			"label": "合同备注",
			"insert_after": "hr_contract_remark_section",
		},
	]


def _materials_tab_fields():
	"""材料附件页签（新建）。"""
	return [
		{"fieldname": "hr_materials_tab", "fieldtype": "Tab Break", "label": "材料附件", "insert_after": "hr_contract_remarks"},
		{
			"fieldname": "hr_materials_id_section",
			"fieldtype": "Section Break",
			"label": "证件材料",
			"insert_after": "hr_materials_tab",
		},
		{
			"fieldname": "hr_attach_id_front",
			"fieldtype": "Attach Image",
			"label": "身份证(人像面)",
			"insert_after": "hr_materials_id_section",
		},
		{
			"fieldname": "hr_attach_id_back",
			"fieldtype": "Attach Image",
			"label": "身份证(国徽面)",
			"insert_after": "hr_attach_id_front",
		},
		{"fieldname": "hr_attach_photo", "fieldtype": "Attach Image", "label": "证件照", "insert_after": "hr_attach_id_back"},
		{"fieldname": "hr_materials_col_1", "fieldtype": "Column Break", "insert_after": "hr_attach_photo"},
		{"fieldname": "hr_attach_bank_card", "fieldtype": "Attach", "label": "银行卡", "insert_after": "hr_materials_col_1"},
		{
			"fieldname": "hr_attach_diploma",
			"fieldtype": "Attach",
			"label": "学历证书",
			"insert_after": "hr_attach_bank_card",
		},
		{"fieldname": "hr_attach_degree", "fieldtype": "Attach", "label": "学位证书", "insert_after": "hr_attach_diploma"},
		{
			"fieldname": "hr_materials_doc_section",
			"fieldtype": "Section Break",
			"label": "入职材料",
			"insert_after": "hr_attach_degree",
		},
		{
			"fieldname": "hr_attach_resume",
			"fieldtype": "Attach",
			"label": "个人简历",
			"insert_after": "hr_materials_doc_section",
		},
		{
			"fieldname": "hr_attach_resignation_proof",
			"fieldtype": "Attach",
			"label": "离职证明",
			"insert_after": "hr_attach_resume",
		},
		{"fieldname": "hr_materials_col_2", "fieldtype": "Column Break", "insert_after": "hr_attach_resignation_proof"},
		{
			"fieldname": "hr_attach_medical_report",
			"fieldtype": "Attach",
			"label": "体检报告",
			"insert_after": "hr_materials_col_2",
		},
		{"fieldname": "hr_attach_others", "fieldtype": "Attach", "label": "其他材料", "insert_after": "hr_attach_medical_report"},
	]


def _background_tab_fields():
	"""背景调查页签（新建）。"""
	return [
		{"fieldname": "hr_background_tab", "fieldtype": "Tab Break", "label": "背景调查", "insert_after": "hr_attach_others"},
		{
			"fieldname": "hr_background_section",
			"fieldtype": "Section Break",
			"label": "背调信息",
			"insert_after": "hr_background_tab",
		},
		{
			"fieldname": "hr_background_status",
			"fieldtype": "Select",
			"label": "背调状态",
			"options": "\n未开始\n进行中\n已通过\n有风险\n未通过",
			"insert_after": "hr_background_section",
		},
		{"fieldname": "hr_background_agency", "fieldtype": "Data", "label": "背调机构", "insert_after": "hr_background_status"},
		{"fieldname": "hr_background_col_1", "fieldtype": "Column Break", "insert_after": "hr_background_agency"},
		{"fieldname": "hr_background_date", "fieldtype": "Date", "label": "背调完成日期", "insert_after": "hr_background_col_1"},
		{
			"fieldname": "hr_background_report",
			"fieldtype": "Attach",
			"label": "背调报告",
			"insert_after": "hr_background_date",
		},
		{
			"fieldname": "hr_background_remark_section",
			"fieldtype": "Section Break",
			"label": "备注",
			"insert_after": "hr_background_report",
		},
		{
			"fieldname": "hr_background_remarks",
			"fieldtype": "Small Text",
			"label": "背调备注",
			"insert_after": "hr_background_remark_section",
		},
	]


def _ensure_custom_fields():
	# 新页签挂在最后一个原生字段之后，避免把既有页签内容切走。
	# 锚点必须每次运行都取原生字段（不能取 hr_ 自定义字段），否则重跑时
	# Tab Break 会被重新锚到自己内容的末尾，导致页签变空被隐藏。
	meta = frappe.get_meta("Employee", cached=False)
	native_last = "connections_tab"
	for field in meta.fields:
		if not field.fieldname.startswith("hr_"):
			native_last = field.fieldname

	fields = (
		_job_fields()
		+ _personal_fields()
		+ _contact_fields()
		+ _social_insurance_fields()
		+ _contract_tab_fields(native_last)
		+ _materials_tab_fields()
		+ _background_tab_fields()
	)
	create_custom_fields({"Employee": fields}, ignore_validate=True)


def _ensure_labels():
	_ensure_doctype_labels("Employee", {**TAB_LABELS, **FIELD_LABELS})


def _ensure_child_labels():
	for doctype, labels in CHILD_FIELD_LABELS.items():
		_ensure_doctype_labels(doctype, labels)


def _ensure_doctype_labels(doctype, labels):
	for fieldname, label in labels.items():
		is_native = frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname})
		is_custom = frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname})
		if not is_native and not is_custom:
			continue
		if is_custom:
			frappe.db.set_value("Custom Field", {"dt": doctype, "fieldname": fieldname}, "label", label)
			continue
		key = f"{doctype}-{fieldname}-label"
		if frappe.db.exists("Property Setter", key):
			frappe.db.set_value("Property Setter", key, "value", label)
		else:
			make_property_setter(doctype, fieldname, "label", label, "Data")


def _ensure_gender_options():
	"""中国 HR 常用性别选项；复用原生 Gender 主数据，不另造字段。"""
	for name in ("男", "女"):
		if frappe.db.exists("Gender", name):
			continue
		doc = frappe.get_doc({"doctype": "Gender", "gender": name})
		doc.insert(ignore_permissions=True)


def _reorder_employee_fields():
	"""重排原生字段到中文页签分区。

	- 部门/岗位等 → 在职信息
	- 性别 → 个人信息「基本信息」
	"""
	key = "Employee-main-field_order"
	if frappe.db.exists("Property Setter", key):
		frappe.db.delete("Property Setter", {"name": key})
	frappe.clear_cache(doctype="Employee")

	meta = frappe.get_meta("Employee", cached=False)
	order = [df.fieldname for df in meta.fields]

	order = _move_fields_after(order, ON_JOB_TAB_FIELDS, "employment_details")
	# 紧跟「曾用名」之后，保证出现在基本信息卡片内
	anchor = "hr_former_name" if "hr_former_name" in order else "hr_personal_basic_section"
	order = _move_fields_after(order, PERSONAL_BASIC_FIELDS, anchor)

	make_property_setter("Employee", None, "field_order", json.dumps(order), "Small Text", for_doctype=True)


def _move_fields_after(order: list[str], fields: list[str], anchor: str) -> list[str]:
	if anchor not in order:
		return order
	movable = [f for f in fields if f in order]
	if not movable:
		return order
	rest = [f for f in order if f not in movable]
	idx = rest.index(anchor) + 1
	return rest[:idx] + movable + rest[idx:]


def _reorder_on_job_fields():
	"""兼容旧调用名。"""
	_reorder_employee_fields()
