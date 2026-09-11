import type { EmployeeCenterView } from "../../api/employeeCenter";

export type BusinessView = Exclude<EmployeeCenterView, "home" | "applications">;
export type FieldKind = "text" | "textarea" | "date" | "time" | "number" | "select" | "department" | "designation" | "employee" | "upload" | "checkbox";
export interface FormField { key: string; label: string; type: FieldKind; required?: boolean; options?: string[]; placeholder?: string; show?: (data: Record<string, any>) => boolean }
export interface FormSection { title: string; description?: string; fields: FormField[] }

export const formSteps: Record<BusinessView, string[]> = {
	"onboarding": ["基本信息", "联系方式", "证件信息", "学历信息", "紧急联系人", "银行卡信息", "附件材料", "确认提交"],
	"subsidy": ["补贴明细", "附件与汇总", "确认提交"],
	"job-change": ["申请信息", "调整信息", "审批信息", "确认提交"],
	"resignation": ["填写申请", "离职信息", "审批信息", "确认提交"],
	"handover": ["交接清单", "审批信息", "确认提交"],
};

export const formSections: Record<BusinessView, FormSection[]> = {
	onboarding: [
		{ title: "基本信息", fields: [
			{ key: "gender", label: "性别", type: "select", required: true, options: ["男", "女"] },
			{ key: "date_of_birth", label: "出生日期", type: "date", required: true },
			{ key: "nationality", label: "民族", type: "select", options: ["汉族", "壮族", "满族", "回族", "苗族", "其他"] },
			{ key: "marital_status", label: "婚姻状况", type: "select", options: ["未婚", "已婚", "离异", "丧偶"] },
		] },
		{ title: "联系方式", fields: [
			{ key: "cell_number", label: "手机号", type: "text", required: true }, { key: "personal_email", label: "个人邮箱", type: "text", required: true },
			{ key: "current_address", label: "现居地址", type: "textarea" }, { key: "permanent_address", label: "户籍地址", type: "textarea" },
		] },
		{ title: "证件信息", fields: [
			{ key: "id_number", label: "身份证号", type: "text", required: true }, { key: "id_validity", label: "身份证有效期", type: "date" },
			{ key: "id_front", label: "身份证正面", type: "upload" }, { key: "id_back", label: "身份证反面", type: "upload" },
		] },
		{ title: "学历信息", fields: [
			{ key: "education", label: "最高学历", type: "select", options: ["高中及以下", "大专", "本科", "硕士", "博士"] },
			{ key: "school", label: "毕业院校", type: "text" }, { key: "major", label: "专业", type: "text" }, { key: "graduation_date", label: "毕业时间", type: "date" },
			{ key: "education_certificate", label: "学历证明", type: "upload" },
		] },
		{ title: "紧急联系人", fields: [
			{ key: "emergency_contact_name", label: "姓名", type: "text" }, { key: "emergency_relation", label: "关系", type: "select", options: ["父母", "配偶", "子女", "亲属", "朋友", "其他"] }, { key: "emergency_phone", label: "联系电话", type: "text" },
		] },
		{ title: "银行卡信息", fields: [
			{ key: "account_holder", label: "开户名", type: "text" }, { key: "bank_name", label: "开户银行", type: "text" }, { key: "bank_ac_no", label: "银行卡号", type: "text" }, { key: "bank_certificate", label: "银行卡证明", type: "upload" },
		] },
		{ title: "附件材料", fields: [
			{ key: "resume", label: "简历", type: "upload" }, { key: "personal_photo", label: "个人照片", type: "upload" }, { key: "other_attachment", label: "其他附件", type: "upload" },
		] },
		{ title: "确认提交", fields: [
			{ key: "truth_confirmed", label: "本人确认以上信息真实、完整", type: "checkbox", required: true }, { key: "signature", label: "签名", type: "text", required: true }, { key: "submitted_date", label: "提交日期", type: "date" },
		] },
	],
	subsidy: [],
	"job-change": [{ title: "异动信息", description: "原任职信息已按提交时快照保存", fields: [
		{ key: "change_type", label: "异动类型", type: "select", required: true, options: ["调岗", "晋升", "降级", "调薪"] },
		{ key: "new_department", label: "调入部门", type: "department", required: true, show: d => d.change_type === "调岗" },
		{ key: "new_designation", label: "调整后岗位", type: "designation", required: true, show: d => ["调岗", "晋升", "降级"].includes(d.change_type) },
		{ key: "new_grade", label: "调整后职级", type: "text", required: true, show: d => ["晋升", "降级"].includes(d.change_type) },
		{ key: "current_salary", label: "原薪资", type: "number", required: true, show: d => d.change_type === "调薪" },
		{ key: "new_salary", label: "调整后薪资", type: "number", required: true, show: d => d.change_type === "调薪" },
		{ key: "effective_date", label: "生效日期", type: "date", required: true }, { key: "reason", label: "申请原因", type: "textarea", required: true },
		{ key: "additional_notes", label: "补充说明", type: "textarea" }, { key: "attachment", label: "附件", type: "upload" },
	]}],
	resignation: [{ title: "离职信息", fields: [
		{ key: "planned_resignation_date", label: "计划离职日期", type: "date", required: true }, { key: "handover_employee", label: "离职交接人", type: "employee", required: true },
		{ key: "resignation_reason", label: "离职原因", type: "select", required: true, options: ["个人发展", "家庭原因", "健康原因", "薪酬福利", "工作内容", "其他"] },
		{ key: "reason_description", label: "原因说明", type: "textarea", required: true }, { key: "attachment", label: "相关附件", type: "upload" },
	]}],
	handover: [],
};

export const handoverTemplates: Record<string, string[]> = {
	"工作内容": ["一张表子表", "总甘特图", "日常图", "待办", "企微文档", "企微微盘", "企微群", "微信群", "客户联系方式", "审批中单据", "新建单据流程"],
	"账号权限": ["金蝶账号及审批", "吉客云账号", "2号人事部审批", "企微审批", "工作邮箱"],
	"虚拟资产": ["店铺账号及实名", "工具账号", "手机号", "微信号"],
	"固定资产": ["手机", "电脑", "其他工作设备", "样品"],
	"财务交接": ["店铺保证金", "个人借款", "费用申请", "应付款", "应收款"],
	"行政交接": ["企业滴滴", "门禁账号", "抽屉桌面", "办公用品", "工位牌"],
};
