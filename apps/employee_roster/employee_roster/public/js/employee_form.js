// Copyright (c) 2026 stillgroup
// License: MIT
/**
 * Employee Form — Arco Design：
 * 「概况」页签展示摘要仪表盘；
 * 在职/个人/联系/工资/合同/材料 页签默认预览，按板块编辑；
 * 新增员工仍使用原生表单。
 * cache: 20260913h
 */
(function () {
	let employeeFormApp = null;
	let employeeFormDeskHeaderApp = null;
	let employeeArchiveApp = null;
	let boundFrm = null;
	let lastEmployeeName = "";
	let lastActiveTab = "";
	let transitionTimer = null;
	let translationFrame = null;
	let isEditing = false;
	let isSaving = false;
	let isDeleting = false;
	let statsCacheKey = "";
	let statsRequestVersion = 0;
	let archiveRequestVersion = 0;
	let archiveResetToken = 0;
	let archiveExpandNonce = 0;
	let pendingExpand = null;
	const orgTreeRequests = new Map();

	const ARCHIVE_TABS = {
		employment_details: 1,
		personal_details: 1,
		contact_details: 1,
		salary_information: 1,
		hr_contract_tab: 1,
		hr_materials_tab: 1,
		attendance_and_leave_details: 1,
		profile_tab: 1,
		hr_background_tab: 1,
		exit: 1,
	};

	const NATIVE_COLLAPSE_TABS = {};

	/** 概况「查看详情」→ 页签 + 折叠卡片 */
	const OVERVIEW_NAV_MAP = {
		personal: { tab: "personal_details", section: "personal_basic" },
		on_job: { tab: "employment_details", section: "employment_basic" },
		contact: { tab: "contact_details", section: "contact_basic" },
		materials: { tab: "hr_materials_tab", section: "materials_rate" },
		attendance: { tab: "attendance_and_leave_details", section: "attendance_settings" },
		profile_tab: { tab: "profile_tab", section: "profile_bio" },
		background: { tab: "hr_background_tab", section: "background_basic" },
		contract: { tab: "hr_contract_tab", section: "contracts" },
		education: { tab: "personal_details", section: "education" },
		external_work_history: { tab: "personal_details", section: "external_work_history" },
		internal_work_history: { tab: "employment_details", section: "internal_work_history" },
		bio: { tab: "profile_tab", section: "profile_bio" },
		emergency: { tab: "contact_details", section: "emergency_contacts" },
		trainings: { tab: "personal_details", section: "trainings" },
		rewards: { tab: "employment_details", section: "rewards" },
	};

	const EMPLOYEE_ZH_TEXT = {
		Employee: "员工",
		Employees: "员工",
		"Employee List": "员工花名册",
		"New Employee": "新增员工",
		Details: "详情",
		"Employment Details": "在职信息",
		"Personal Details": "个人信息",
		"Contact Details": "联系信息",
		"Salary Information": "工资社保",
		"Attendance and Leave Details": "考勤假期",
		Profile: "履历资料",
		Exit: "离职办理",
		Dashboard: "数据面板",
		Connections: "关联记录",
		Activity: "动态",
		Timeline: "时间线",
		Attachments: "附件",
		Tags: "标签",
		Share: "分享",
		Follow: "关注",
		"Assign To": "分配给",
		"Add a comment": "添加评论",
		"No comments yet": "暂无评论",
		Email: "邮件",
		Print: "打印",
		Edit: "编辑",
		Save: "保存",
		Cancel: "取消",
		Delete: "删除",
		Duplicate: "复制",
		Rename: "重命名",
		Reload: "重新加载",
		Refresh: "刷新",
		Search: "搜索",
		Filter: "筛选",
		Sort: "排序",
		Clear: "清空",
		Close: "关闭",
		Confirm: "确认",
		Submit: "提交",
		"Add Row": "新增一行",
		"Add Multiple": "批量新增",
		"Select All": "全选",
		"Delete All": "全部删除",
		"Insert Above": "在上方插入",
		"Insert Below": "在下方插入",
		"Move To": "移动到",
		"No Data": "暂无数据",
		"No records found": "暂无记录",
		Loading: "加载中",
		Menu: "更多",
		Created: "创建时间",
		"Last Edited": "最近编辑",
		"Not Saved": "未保存",
		Submitted: "已提交",
		Draft: "草稿",
		Cancelled: "已取消",
		"Naming Series": "编号规则",
		"First Name": "名",
		"Middle Name": "中间名",
		"Last Name": "姓",
		"Employee Name": "员工姓名",
		Gender: "性别",
		"Date of Birth": "出生日期",
		"Date of Joining": "入职日期",
		Status: "员工状态",
		"User ID": "关联用户",
		Company: "合同公司",
		Department: "部门",
		Designation: "岗位",
		"Reports To": "汇报上级",
		Branch: "分支机构",
		Grade: "职级",
		"Employment Type": "工作性质",
		"Holiday List": "节假日列表",
		"Cell Number": "手机号",
		"Preferred Contact Email": "首选联系邮箱",
		"Prefered Contact Email": "首选联系邮箱",
		"Company Email": "公司邮箱",
		"Personal Email": "个人邮箱",
		Unsubscribed: "取消订阅",
		"Current Address": "居住地址",
		"Permanent Address": "永久地址",
		"Person to be Contacted": "紧急联系人",
		"Emergency Phone Number": "紧急联系电话",
		Relation: "与本人关系",
		"Salary Mode": "工资发放方式",
		"Bank Name": "开户银行",
		"Bank A/C No.": "银行卡号",
		IBAN: "国际银行账号",
		"Bank Details": "银行信息",
		"Emergency Contact": "紧急联系人",
		"Marital Status": "婚姻状况",
		"Family Background": "家庭背景",
		"Blood Group": "血型",
		"Health Details": "健康状况",
		"Passport Number": "护照号码",
		"Date of Issue": "签发日期",
		"Valid Upto": "有效期至",
		"Place of Issue": "签发地点",
		Bio: "个人简介",
		"Educational Qualification": "教育经历",
		"Previous Work Experience": "外部工作经历",
		"Internal Work History": "公司内部履历",
		"Date of Retirement": "退休日期",
		"Relieving Date": "离职日期",
		"Reason for Leaving": "离职原因",
		School: "学校/院校",
		"School/University": "学校/院校",
		Qualification: "学历/资格",
		Level: "学历层次",
		"Year of Passing": "毕业年份",
		"Class / Percentage": "成绩/百分比",
		"Major/Optional Subject": "专业/选修科目",
		"Company Name": "公司名称",
		"Total Experience": "工作年限",
		"From Date": "开始日期",
		"To Date": "结束日期",
		Active: "在职",
		Inactive: "停用",
		Suspended: "停职",
		Left: "已离职",
		"Full-time": "全职",
		"Part-time": "兼职",
		Intern: "实习生",
		Probation: "试用期",
		Contract: "合同工",
		Apprentice: "见习生",
		Male: "男",
		Female: "女",
		Other: "其他",
		Married: "已婚",
		Unmarried: "未婚",
		Divorced: "离异",
		Widowed: "丧偶",
		"A few seconds ago": "几秒前",
		"a few seconds ago": "几秒前",
		"A minute ago": "1 分钟前",
		"a minute ago": "1 分钟前",
		"An hour ago": "1 小时前",
		"an hour ago": "1 小时前",
		Yesterday: "昨天",
		yesterday: "昨天",
		"Create Assignments": "创建任务",
		"Begin typing for results.": "输入内容以搜索",
		"Default Shift": "默认班次",
		Approvers: "审批人",
		"Expense Approver": "费用审批人",
		"Leave Approver": "休假审批人",
		"Shift Request Approver": "排班申请审批人",
		"Employee Advance Account": "员工预支账户",
		"Payroll Cost Center": "薪资成本中心",
		"Health Insurance": "健康保险",
		"Job Applicant": "求职者",
		Attendance: "出勤",
		"Attendance Request": "出勤申请",
		"Employee Checkin": "员工签到",
		Leave: "休假",
		"Leave Application": "休假申请",
		"Leave Allocation": "休假额度",
		"Leave Policy Assignment": "休假政策分配",
		"Holiday List Assignment": "节假日列表分配",
		Lifecycle: "员工生命周期",
		"Employee Onboarding": "员工入职",
		"Employee Transfer": "员工调动",
		"Employee Promotion": "员工晋升",
		"Employee Grievance": "员工申诉",
		"Employee Exit": "员工离职",
		"Employee Separation": "员工离职办理",
		"Exit Interview": "离职面谈",
		"Salary Withholding": "薪资暂扣",
		"Shift Request": "排班申请",
		"Shift Assignment": "排班分配",
		"Travel Request": "出差申请",
		Benefit: "员工福利",
		"Employee Benefit Application": "员工福利申请",
		"Employee Benefit Claim": "员工福利申领",
		Payroll: "薪资核算",
		"Salary Structure Assignment": "薪资结构分配",
		"Salary Slip": "工资单",
		"Additional Salary": "附加薪资",
		"Employee Incentive": "员工激励",
		"Retention Bonus": "留任奖金",
		"Overtime Slip": "加班单",
		Arrear: "薪资补发",
		"Payroll Correction": "薪资更正",
		Training: "培训",
		"Training Event": "培训活动",
		"Training Result": "培训结果",
		"Training Feedback": "培训反馈",
		"Employee Skill Map": "员工技能图谱",
		Evaluation: "绩效评估",
		Appraisal: "绩效考核",
		"This is based on the attendance of this Employee": "以上数据基于该员工的出勤记录",
		Sun: "周日",
		Mon: "周一",
		Tue: "周二",
		Wed: "周三",
		Thu: "周四",
		Fri: "周五",
		Sat: "周六",
		Less: "少",
		More: "多",
		JAN: "一月",
		FEB: "二月",
		MAR: "三月",
		APR: "四月",
		MAY: "五月",
		JUN: "六月",
		JUL: "七月",
		AUG: "八月",
		SEP: "九月",
		OCT: "十月",
		NOV: "十一月",
		DEC: "十二月",
	};

	const EMPLOYEE_TAB_LABELS = {
		basic_details_tab: "概览",
		employment_details: "在职信息",
		personal_details: "个人信息",
		contact_details: "联系信息",
		salary_information: "工资社保",
		hr_contract_tab: "合同信息",
		hr_materials_tab: "材料附件",
		hr_background_tab: "背景调查",
		profile_tab: "履历资料",
		attendance_and_leave_details: "考勤假期",
		exit: "离职办理",
		connections_tab: "更多",
	};

	const EMPLOYEE_TAB_ORDER = [
		"basic_details_tab",
		"employment_details",
		"personal_details",
		"contact_details",
		"salary_information",
		"hr_contract_tab",
		"hr_materials_tab",
		"attendance_and_leave_details",
		"profile_tab",
		"hr_background_tab",
		"exit",
		"connections_tab",
	];

	function reorder_employee_tabs($page) {
		const $tabs = $page.find(".form-tabs .nav-item");
		if (!$tabs.length) {
			return;
		}
		const $container = $tabs.first().parent();
		const tabMap = {};
		$tabs.each(function () {
			const fieldname =
				this.querySelector(".nav-link")?.dataset?.fieldname ||
				$(this).find(".nav-link").data("fieldname") ||
				$(this).find(".nav-link").attr("data-fieldname") ||
				"";
			if (fieldname) {
				tabMap[fieldname] = this;
			}
		});
		EMPLOYEE_TAB_ORDER.forEach((fieldname) => {
			if (tabMap[fieldname]) {
				$container.append(tabMap[fieldname]);
			}
		});
	}

	function relabel_employee_tabs($page) {
		$page.find(".form-tabs .nav-link, .form-tabs button.nav-link").each(function () {
			const fieldname =
				this.dataset?.fieldname || $(this).data("fieldname") || $(this).attr("data-fieldname") || "";
			const label = EMPLOYEE_TAB_LABELS[fieldname];
			if (!label) {
				return;
			}
			const $label = $(this).find(".tab-label, span").first();
			if ($label.length) {
				$label.text(label);
			} else {
				$(this).text(label);
			}
		});
	}

	function translate_employee_text(value) {
		const text = String(value || "").trim();
		if (!text) {
			return null;
		}
		if (EMPLOYEE_ZH_TEXT[text]) {
			return EMPLOYEE_ZH_TEXT[text];
		}
		const activityDate = text.match(/^ON\s+([A-Z]{3})\s+(\d{4}),\s*(\d{1,2})$/);
		if (activityDate && EMPLOYEE_ZH_TEXT[activityDate[1]]) {
			return `${activityDate[2]}年${EMPLOYEE_ZH_TEXT[activityDate[1]]}${activityDate[3]}日`;
		}
		const relativeTime = text.match(/^(\d+)\s+(minute|hour|day|month|year)s?\s+ago$/i);
		if (relativeTime) {
			const units = { minute: "分钟", hour: "小时", day: "天", month: "个月", year: "年" };
			return `${relativeTime[1]} ${units[relativeTime[2].toLowerCase()]}前`;
		}
		const lastEdited = text.match(/^Last edited\s+(.+)$/i);
		if (lastEdited) {
			return `最近编辑：${translate_employee_text(lastEdited[1]) || lastEdited[1]}`;
		}
		const created = text.match(/^Created\s+(.+)$/i);
		if (created) {
			return `创建于 ${translate_employee_text(created[1]) || created[1]}`;
		}
		return null;
	}

	function localize_employee_page($page) {
		const root = $page?.get?.(0);
		if (!root) {
			return;
		}
		const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
		const nodes = [];
		let node = walker.nextNode();
		while (node) {
			nodes.push(node);
			node = walker.nextNode();
		}
		nodes.forEach((textNode) => {
			const raw = textNode.nodeValue || "";
			const translated = translate_employee_text(raw);
			if (translated) {
				textNode.nodeValue = raw.replace(raw.trim(), translated);
				return;
			}
			// 开发者模式会把字段名作为帮助文本显示；这不是面向用户的信息。
			if (/^[a-z][a-z0-9_]*$/.test(raw.trim()) && textNode.parentElement?.closest?.(".help-box")) {
				textNode.nodeValue = "";
			}
		});
		root.querySelectorAll("[title], [aria-label], [placeholder]").forEach((el) => {
			["title", "aria-label", "placeholder"].forEach((attr) => {
				const translated = translate_employee_text(el.getAttribute(attr));
				if (translated) {
					el.setAttribute(attr, translated);
				}
			});
		});
	}

	function schedule_localization($page) {
		cancelAnimationFrame(translationFrame);
		translationFrame = requestAnimationFrame(() => localize_employee_page($page));
	}

	function bind_localization_observer($page) {
		if (!$page?.length || $page.data("arco-emp-zh-mo")) {
			return;
		}
		const observer = new MutationObserver(() => schedule_localization($page));
		observer.observe($page.get(0), {
			childList: true,
			characterData: true,
			attributes: true,
			attributeFilter: ["title", "aria-label", "placeholder"],
			subtree: true,
		});
		$page.data("arco-emp-zh-mo", observer);
	}

	function fmt_date(v) {
		if (!v) {
			return "";
		}
		const raw = String(v).trim();
		const iso = raw.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
		if (iso) {
			return `${iso[1]}年${String(iso[2]).padStart(2, "0")}月${String(iso[3]).padStart(2, "0")}日`;
		}
		const userDate = raw.match(/^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$/);
		if (userDate) {
			return `${userDate[3]}年${String(userDate[2]).padStart(2, "0")}月${String(userDate[1]).padStart(2, "0")}日`;
		}
		try {
			const date = frappe.datetime.str_to_obj(v);
			if (date && !Number.isNaN(date.getTime())) {
				return `${date.getFullYear()}年${String(date.getMonth() + 1).padStart(2, "0")}月${String(date.getDate()).padStart(2, "0")}日`;
			}
			return raw;
		} catch (e) {
			return raw;
		}
	}

	function profile_summary(doc) {
		const checks = [
			{ value: doc.employee_name || doc.first_name, label: "补充员工姓名", target: "employee_name" },
			{ value: doc.date_of_joining, label: "补充入职日期", target: "date_of_joining" },
			{ value: doc.company, label: "补充合同公司", target: "company" },
			{ value: doc.department, label: "补充所属部门", target: "department" },
			{ value: doc.designation, label: "补充岗位", target: "designation" },
			{ value: doc.employee_number, label: "补充工号", target: "employee_number" },
			{ value: doc.cell_number, label: "补充手机号", target: "contact" },
			{ value: doc.company_email || doc.personal_email, label: "补充邮箱", target: "contact" },
			{
				value: doc.hr_id_number || doc.passport_number || doc.custom_id_number,
				label: "补充证件号码",
				target: "passport_number",
			},
			{ value: doc.hr_native_place, label: "补充籍贯", target: "hr_native_place" },
		];
		const complete = checks.filter((item) => !!item.value).length;
		return {
			profile_completion: Math.round((complete / checks.length) * 100),
			profile_missing: checks.filter((item) => !item.value).map(({ label, target }) => ({ label, target })),
		};
	}

	function get_form_permissions(frm) {
		try {
			const is_new = !!(frm?.is_new?.() || frm?.doc?.__islocal);
			const can_edit = !!(frm?.perm?.[0]?.write && !is_new);
			const can_save = !!(
				is_new ? frappe.model?.can_create?.(frm?.doctype || "Employee") : frm?.perm?.[0]?.write
			);
			const can_delete = !!(!is_new && frm?.perm?.[0]?.delete && frm?.doc?.status === "Left");
			const can_create_transfer =
				typeof frappe.model?.can_create === "function" ? frappe.model.can_create("Employee Transfer") : false;
			return { can_edit, can_save, can_delete, can_create_transfer, is_new };
		} catch (e) {
			return { can_edit: false, can_save: false, can_delete: false, can_create_transfer: false, is_new: false };
		}
	}

	function notify(type, content) {
		if (window.OrgUI?.notify) {
			window.OrgUI.notify({ type, content });
			return;
		}
		frappe.show_alert?.({ message: content, indicator: type === "error" ? "red" : "green" });
	}

	function confirm_action(message) {
		return new Promise((resolve) => {
			frappe.confirm(message, () => resolve(true), () => resolve(false));
		});
	}

	function validate_employee_before_save(frm) {
		const validateEmployee = window.EmployeeFormValidation?.validateEmployee;
		if (typeof validateEmployee !== "function") {
			return true;
		}
		const errors = validateEmployee(frm.doc || {}, { today: frappe.datetime.get_today() });
		if (!errors.length) {
			return true;
		}
		const items = errors.map((error) => `<li>${frappe.utils.escape_html(error.message)}</li>`).join("");
		frappe.msgprint({
			title: __("请检查员工信息"),
			indicator: "red",
			message: `<ul class="employee-validation-errors">${items}</ul>`,
		});
		navigate_from_overview(frm, errors[0].fieldname);
		return false;
	}

	function trigger_hr_transfer(frm) {
		if (!frm?.doc?.name) {
			return;
		}
		if (typeof frappe.model?.can_create === "function" && !frappe.model.can_create("Employee Transfer")) {
			frappe.msgprint(__("您没有创建人事异动的权限"));
			return;
		}
		frappe.new_doc("Employee Transfer", { employee: frm.doc.name });
	}

	function build_more_actions(frm) {
		const actions = [];
		if (frm?.doc?.name && !frm.doc.__islocal) {
			actions.push({ key: "create_user", label: __("创建用户") });
			actions.push({ key: "create_assignment", label: __("创建任务") });
		}
		return actions;
	}

	function handle_more_action(frm, key) {
		const $page = frm.$wrapper || frm.page?.wrapper || $();
		if (key === "create_user") {
			$page.find('[data-label="Create User"], .btn[data-label="Create User"]').first().get(0)?.click?.();
			return;
		}
		if (key === "create_assignment") {
			$page.find('[data-label="Create Assignments"], .btn[data-label="Create Assignments"]').first().get(0)?.click?.();
			return;
		}
	}

	function strip_html(html) {
		if (!html) {
			return "";
		}
		const tmp = document.createElement("div");
		tmp.innerHTML = html;
		return (tmp.textContent || tmp.innerText || "").replace(/\s+/g, " ").trim();
	}

	function calc_tenure_days(date_of_joining) {
		if (!date_of_joining) {
			return null;
		}
		try {
			const start = frappe.datetime.str_to_obj(date_of_joining);
			const today = frappe.datetime.str_to_obj(frappe.datetime.get_today());
			if (!start || !today) {
				return null;
			}
			const ms = today.getTime() - start.getTime();
			return Math.max(0, Math.floor(ms / 86400000));
		} catch (e) {
			return null;
		}
	}

	function map_child_rows(rows, fields) {
		return (rows || []).map((row) => {
			const out = { name: row.name || "" };
			fields.forEach((f) => {
				out[f] = row[f] ?? "";
			});
			return out;
		});
	}

	function payload_from_frm(frm, extras = {}) {
		const doc = (frm && frm.doc) || {};
		const profile = profile_summary(doc);
		const education = map_child_rows(doc.education, [
			"school_univ",
			"qualification",
			"level",
			"year_of_passing",
		]);
		const external_work_history = map_child_rows(doc.external_work_history, [
			"company_name",
			"designation",
			"total_experience",
		]);
		const internal_work_history = map_child_rows(doc.internal_work_history, [
			"department",
			"designation",
			"from_date",
			"to_date",
		]).map((row) => ({
			...row,
			from_date: fmt_date(row.from_date) || row.from_date,
			to_date: fmt_date(row.to_date) || row.to_date,
		}));

		const related_count =
			education.length +
			external_work_history.length +
			internal_work_history.length +
			(doc.bio ? 1 : 0) +
			(Number(extras.dashboard_links) || 0);

		return {
			...profile,
			...get_form_permissions(frm),
			name: doc.name || "",
			employee_name: doc.employee_name || doc.first_name || "",
			employee_number: doc.employee_number || "",
			status: doc.status || "",
			department: doc.department || "",
			designation: doc.designation || "",
			company: doc.company || "",
			branch: doc.branch || "",
			group_name: doc.group_name || "",
			employment_type: doc.employment_type || "",
			employment_type_label:
				({ "Full-time": "全职", Intern: "实习", Probation: "试用期", Contract: "合同工", "Part-time": "兼职" }[
					doc.employment_type
				] || doc.employment_type || ""),
			image: doc.image || "",
			date_of_joining: fmt_date(doc.date_of_joining),
			cell_number: doc.cell_number || "",
			company_email: doc.company_email || doc.prefered_email || "",
			personal_email: doc.personal_email || "",
			reports_to: doc.reports_to || "",
			grade: doc.grade || "",
			gender: doc.gender || "",
			marital_status: doc.marital_status || "",
			blood_group: doc.blood_group || "",
			passport_number: doc.passport_number || "",
			health_insurance_provider: doc.health_insurance_provider || "",
			health_insurance_no: doc.health_insurance_no || "",
			default_shift: doc.default_shift || "",
			person_to_be_contacted: doc.person_to_be_contacted || "",
			emergency_phone_number: doc.emergency_phone_number || "",
			relation: doc.relation || "",
			bio_text: strip_html(doc.bio),
			hr_job_title: doc.hr_job_title || "",
			hr_position_category: doc.hr_position_category || "",
			hr_job_grade_level: doc.hr_job_grade_level || "",
			hr_work_city: doc.hr_work_city || "",
			hr_work_location: doc.hr_work_location || "",
			hr_employee_identity: doc.hr_employee_identity || "",
			hr_oa_code: doc.hr_oa_code || "",
			hr_native_place: doc.hr_native_place || "",
			hr_id_number: doc.hr_id_number || "",
			hr_contract_type: doc.hr_contract_type || "",
			hr_contract_status: doc.hr_contract_status || "",
			hr_contract_expire_date: fmt_date(doc.hr_contract_expire_date),
			hr_background_status: doc.hr_background_status || "",
			attendance_device_id: doc.attendance_device_id || "",
			education_summary: education[0]?.qualification || education[0]?.level || "",
			probation_days_remaining: null,
			late_count: null,
			overtime_hours: null,
			education,
			external_work_history,
			internal_work_history,
			tenure_days: calc_tenure_days(doc.date_of_joining),
			leave_balance: extras.leave_balance ?? null,
			attendance_month: extras.attendance_month ?? null,
			related_count,
			show_overview: extras.show_overview !== false,
			is_editing: !!extras.is_editing,
			is_dirty: !!frm?.is_dirty?.(),
			is_saving: !!extras.is_saving,
			is_deleting: !!extras.is_deleting,
		};
	}

	function get_active_tab(frm) {
		const hash = String(location.hash || "").replace(/^#/, "");
		const known = {
			basic_details_tab: 1,
			contact_details: 1,
			attendance_and_leave_details: 1,
			salary_information: 1,
			personal_details: 1,
			profile_tab: 1,
			employment_details: 1,
			hr_contract_tab: 1,
			hr_materials_tab: 1,
			hr_background_tab: 1,
			exit: 1,
			connections_tab: 1,
		};
		if (hash && known[hash]) {
			return hash;
		}
		try {
			const tab = frm.get_active_tab?.();
			if (tab?.df?.fieldname) {
				return tab.df.fieldname;
			}
		} catch (e) {
			/* ignore */
		}
		const $active = (frm.$wrapper || $()).find(".form-tabs .nav-link.active").first();
		const fromDom = $active.data("fieldname") || $active.attr("data-fieldname") || "";
		return fromDom || "basic_details_tab";
	}

	function ensure_desk_header_root(frm) {
		const $page = frm.$wrapper || frm.page?.wrapper;
		if (!$page || !$page.length) {
			return null;
		}
		$page.addClass("arco-hr-employee-form-wrapper");
		$page.find(".layout-main-section").first().addClass("hr-desk-content-stack");
		let $root = $page.find("#hr-employee-form-header-root");
		if ($root.length) {
			return $root.get(0);
		}
		$root = $('<div id="hr-employee-form-header-root" class="hr-desk-header-host"></div>');
		const $section = $page.find(".layout-main-section").first();
		if ($section.length) {
			$section.prepend($root);
		} else {
			$page.find(".layout-main").first().prepend($root);
		}
		return $root.get(0);
	}

	function ensure_chrome_root(frm) {
		const $page = frm.$wrapper || frm.page?.wrapper;
		if (!$page || !$page.length) {
			return null;
		}
		$page.addClass("arco-employee-form-page");
		document.body.classList.add("arco-employee-form");

		let $root = $page.find("#employee-arco-chrome-root");
		if ($root.length) {
			return $root.get(0);
		}

		$root = $('<div id="employee-arco-chrome-root"></div>');
		const $tabs = $page.find(".form-tabs-list").first();
		const $layout = $page.find(".form-layout").first();
		if ($tabs.length) {
			$tabs.before($root);
		} else if ($layout.length) {
			$layout.prepend($root);
		} else {
			$page.find(".layout-main-section").first().prepend($root);
		}
		return $root.get(0);
	}

	function ensure_overview_root(frm) {
		const $page = frm.$wrapper || frm.page?.wrapper;
		if (!$page || !$page.length) {
			return null;
		}
		let $root = $page.find("#employee-arco-overview-root");
		if ($root.length) {
			return $root.get(0);
		}
		$root = $('<div id="employee-arco-overview-root"></div>');
		const $tabContent = $page.find(".form-tab-content, .tab-content").first();
		const $layout = $page.find(".form-layout").first();
		if ($tabContent.length) {
			$tabContent.prepend($root);
		} else if ($layout.length) {
			$layout.prepend($root);
		} else {
			$page.find(".layout-main-section").first().append($root);
		}
		return $root.get(0);
	}

	function ensure_archive_root(frm) {
		const $page = frm.$wrapper || frm.page?.wrapper;
		if (!$page || !$page.length) {
			return null;
		}
		let $root = $page.find("#employee-arco-archive-root");
		if ($root.length) {
			return $root.get(0);
		}
		$root = $('<div id="employee-arco-archive-root"></div>');
		const $overview = $page.find("#employee-arco-overview-root").first();
		const $tabContent = $page.find(".form-tab-content, .tab-content").first();
		if ($overview.length) {
			$overview.after($root);
		} else if ($tabContent.length) {
			$tabContent.prepend($root);
		} else {
			$page.find(".layout-main-section").first().append($root);
		}
		return $root.get(0);
	}

	function open_choice_dropdown(frm, fieldname) {
		const control = frm?.fields_dict?.[fieldname];
		const input = control?.$input?.get?.(0) || control?.input;
		if (!control || !input || input.disabled || input.readOnly) {
			return;
		}

		input.focus();
		if (control.df?.fieldtype === "Link" && typeof control.on_input === "function") {
			// 空搜索词加载完整候选项；不改 input.value，因此当前选择会原样保留。
			control.on_input({ target: { value: "" } });
			return;
		}

		if (control.df?.fieldtype === "Autocomplete" && control.awesomplete) {
			const showOptions = (items) => {
				const options = (items || []).filter((item) => item?.value || item?.label || item);
				if (!options.length || document.activeElement !== input) {
					return;
				}
				const autocomplete = control.awesomplete;
				const originalFilter = autocomplete.filter;
				try {
					// 展开时暂时不过滤当前文本，让用户直接看到并改选所有候选项。
					autocomplete.filter = () => true;
					autocomplete.list = options;
					autocomplete.evaluate?.();
				} finally {
					autocomplete.filter = originalFilter;
				}
			};

			const configured = control.get_data?.() || control._data || [];
			if (configured.length) {
				showOptions(configured);
				return;
			}

			if (fieldname === "group_name") {
				if (!frm.doc.department) {
					notify("warning", __("请先选择部门，再选择组别"));
					return;
				}
				load_org_group_values(frm)
					.then((values) => {
						control._arcoChoiceOptions = values.map((value) => ({ label: value, value }));
						if (!values.length) {
							notify("warning", __("当前部门在组织架构中尚未配置组别"));
							return;
						}
						showOptions(control._arcoChoiceOptions);
					})
					.catch((error) => console.warn("[employee-form] load org groups failed", error));
				return;
			}

			if (control._arcoChoiceOptions) {
				showOptions(control._arcoChoiceOptions);
				return;
			}

			// 未配置静态 options 的职务等字段，从现有员工档案中提取去重值作为可复用候选项。
			frappe.db
				.get_list("Employee", {
					fields: [fieldname],
					filters: [[fieldname, "is", "set"]],
					limit: 100,
					order_by: `${fieldname} asc`,
				})
				.then((rows) => {
					const values = [
						...new Set(
							(rows || [])
								.map((row) => String(row?.[fieldname] || "").trim())
								.filter(Boolean)
						),
					];
					control._arcoChoiceOptions = values.map((value) => ({ label: value, value }));
					showOptions(control._arcoChoiceOptions);
				})
				.catch((error) => console.warn(`[employee-form] load ${fieldname} options failed`, error));
		}
	}

	function enhance_choice_triggers(frm) {
		const $page = frm.$wrapper || frm.page?.wrapper;
		if (!$page?.length) {
			return;
		}

		$page
			.find('.frappe-control[data-fieldtype="Link"], .frappe-control[data-fieldtype="Autocomplete"]')
			.each(function () {
				const $control = $(this);
				const fieldname = $control.attr("data-fieldname");
				const $host =
					$control.attr("data-fieldtype") === "Link"
						? $control.find(".control-input .link-field").first()
						: $control.find(".control-input").first();
				if (!fieldname || !$host.length || $host.find(".arco-emp-choice-trigger").length) {
					return;
				}

				const label =
					frm.fields_dict?.[fieldname]?.df?.label ||
					$control.find(".control-label").first().text().trim() ||
					__("字段");
				const $trigger = $(
					`<button type="button" class="arco-emp-choice-trigger" aria-label="${frappe.utils.escape_html(
						__("展开{0}选项", [label])
					)}"><span aria-hidden="true"></span></button>`
				);
				$trigger.on("mousedown", (event) => event.preventDefault());
				$trigger.on("click", function (event) {
					event.preventDefault();
					event.stopPropagation();
					open_choice_dropdown(frm, fieldname);
				});
				$host.append($trigger);
			});
	}

	function polish_dom(frm) {
		const $page = frm.$wrapper || frm.page?.wrapper;
		if (!$page || !$page.length) {
			return;
		}
		$page.find(".form-tabs-list").addClass("arco-emp-tabs");
		$page.find(".form-layout").addClass("arco-emp-form-layout");
		$page.find(".form-dashboard").addClass("arco-emp-dashboard");
		$page.find(".form-section.card-section").addClass("arco-emp-section");
		$page.find(".form-grid-container, .form-grid").each(function () {
			$(this).closest(".frappe-control, .form-group").addClass("arco-emp-grid-wrap");
		});
		enhance_choice_triggers(frm);
		relabel_employee_tabs($page);
		reorder_employee_tabs($page);
		bind_localization_observer($page);
		schedule_localization($page);
	}

	function is_native_edit_context(frm) {
		const isNew = !!(frm?.is_new?.() || frm?.doc?.__islocal);
		return !!(isEditing || frm?.is_dirty?.() || isNew);
	}

	function is_archive_tab(tab) {
		return !!ARCHIVE_TABS[tab];
	}

	function sync_overview_visibility(frm) {
		const $page = frm.$wrapper || frm.page?.wrapper;
		if (!$page || !$page.length) {
			return false;
		}
		const active = get_active_tab(frm);
		const isNew = !!(frm?.is_new?.() || frm?.doc?.__islocal);
		const isOverview = !isNew && !isEditing && !frm?.is_dirty?.() && active === "basic_details_tab";
		const showArchive =
			!isNew && !isEditing && !frm?.is_dirty?.() && is_archive_tab(active) && !!frm?.doc?.name;

		$page.toggleClass("arco-emp-overview-active", isOverview);
		$page.toggleClass("arco-emp-archive-active", showArchive);
		$page.find("#employee-arco-chrome-root").show();
		$page.find("#employee-arco-overview-root").toggle(isOverview);
		$page.find("#employee-arco-archive-root").toggle(showArchive);

		// 概况：隐藏全部原生分区；档案页签：仅隐藏当前页签原生分区
		$page.find(".form-layout .form-section").toggleClass("arco-emp-native-hidden", isOverview || showArchive);

		if (lastActiveTab && lastActiveTab !== active) {
			$page.removeClass("arco-emp-tab-entering");
			void $page.get(0)?.offsetWidth;
			$page.addClass("arco-emp-tab-entering");
			clearTimeout(transitionTimer);
			transitionTimer = setTimeout(() => $page.removeClass("arco-emp-tab-entering"), 260);
			if (showArchive) {
				archiveResetToken += 1;
			}
		}
		lastActiveTab = active;
		schedule_localization($page);
		if (showArchive) {
			setTimeout(() => apply_pending_expand(frm), 80);
		}
		return isOverview;
	}

	function activate_employee_tab(frm, tabFieldname) {
		if (!tabFieldname) return;
		try {
			frm.set_active_tab?.(tabFieldname);
		} catch (e) {
			/* ignore */
		}
		const $page = frm.$wrapper || frm.page?.wrapper;
		if (!$page || !$page.length) return;
		const $link = $page.find(
			`.form-tabs .nav-link[data-fieldname="${tabFieldname}"], .form-tabs button.nav-link[data-fieldname="${tabFieldname}"]`
		);
		if ($link.length && !$link.hasClass("active")) {
			$link.trigger("click");
		}
	}

	function navigate_from_overview(frm, target) {
		const nav = OVERVIEW_NAV_MAP[target] || null;
		if (!nav?.tab) {
			console.warn("[employee-form] unknown overview navigate target", target);
			return;
		}

		pendingExpand = {
			tab: nav.tab,
			section: nav.section || "",
			field: nav.field || "",
		};

		activate_employee_tab(frm, nav.tab);

		// 页签切换后多次尝试展开，覆盖异步渲染
		[80, 200, 450, 800].forEach((ms) => {
			setTimeout(() => apply_pending_expand(frm), ms);
		});
	}

	function apply_pending_expand(frm) {
		if (!pendingExpand) return;
		const { tab, section } = pendingExpand;
		const active = get_active_tab(frm);

		if (tab && active !== tab) {
			return;
		}

		if (section && is_archive_tab(active)) {
			archiveExpandNonce += 1;
			window.OrgUI?.updateEmployeeArchivePanels?.({
				activeTab: active,
				expandSection: section,
				expandNonce: archiveExpandNonce,
			});
			pendingExpand = null;
			return;
		}

		pendingExpand = null;
	}

	function fetch_extra_stats(frm) {
		const doc = frm.doc || {};
		if (!doc.name || !doc.date_of_joining) {
			return;
		}

		const today = frappe.datetime.get_today();
		const month_start = today.slice(0, 8) + "01";
		const cacheKey = `${doc.name}:${month_start}:${today}`;
		if (statsCacheKey === cacheKey) {
			return;
		}
		statsCacheKey = cacheKey;
		const requestVersion = ++statsRequestVersion;

		Promise.all([
			frappe
				.db
				.count("Attendance", {
					filters: {
						employee: doc.name,
						attendance_date: ["between", [month_start, today]],
						status: ["in", ["Present", "Work From Home"]],
						docstatus: 1,
					},
				})
				.catch(() => null),
			frappe
				.call({
					method: "hrms.hr.doctype.leave_application.leave_application.get_leave_details",
					args: {
						employee: doc.name,
						date: today,
					},
				})
				.then((r) => r?.message || null)
				.catch(() => null),
		]).then(([attendance_month, leave_msg]) => {
			if (requestVersion !== statsRequestVersion || boundFrm !== frm) {
				return;
			}
			let leave_balance = null;
			try {
				const details = leave_msg?.leave_allocation;
				if (details && typeof details === "object") {
					const vals = Object.values(details)
						.map((x) => {
							if (!x || typeof x !== "object") {
								return NaN;
							}
							return Number(x.remaining_leaves);
						})
						.filter((n) => Number.isFinite(n));
					if (vals.length) {
						leave_balance = Math.round(vals.reduce((a, b) => a + b, 0) * 10) / 10;
					}
				}
			} catch (e) {
				leave_balance = null;
			}

			if (!window.OrgUI?.updateEmployeeForm) {
				return;
			}
			window.OrgUI.updateEmployeeForm({
				attendance_month: Number.isFinite(Number(attendance_month)) ? Number(attendance_month) : null,
				leave_balance: Number.isFinite(Number(leave_balance)) ? Number(leave_balance) : null,
			});
		});
	}

	function fetch_archive_data(frm, { force = false } = {}) {
		const doc = frm?.doc || {};
		const active = get_active_tab(frm);
		const isNew = !!(frm?.is_new?.() || doc.__islocal);
		if (isNew || !doc.name || !is_archive_tab(active)) {
			return;
		}
		if (!window.OrgUI?.updateEmployeeArchivePanels) {
			return;
		}

		const requestVersion = ++archiveRequestVersion;
		window.OrgUI.updateEmployeeArchivePanels({
			activeTab: active,
			loading: true,
			can_edit: !!get_form_permissions(frm).can_edit,
			resetToken: archiveResetToken,
		});

		frappe
			.call({
				method: "employee_roster.hr_roster.employee_detail.get_employee_archive",
				args: { employee: doc.name },
			})
			.then((r) => {
				if (requestVersion !== archiveRequestVersion || boundFrm !== frm) {
					return;
				}
				window.OrgUI.updateEmployeeArchivePanels({
					activeTab: get_active_tab(frm),
					loading: false,
					can_edit: !!get_form_permissions(frm).can_edit,
					resetToken: archiveResetToken,
					doc: r?.message || {},
				});
				setTimeout(() => apply_pending_expand(frm), 60);
			})
			.catch((error) => {
				if (requestVersion !== archiveRequestVersion || boundFrm !== frm) {
					return;
				}
				console.warn("[employee-form] load archive failed", error);
				window.OrgUI.updateEmployeeArchivePanels({ loading: false });
				notify("error", __("员工档案加载失败，请刷新后重试"));
			});
	}

	function bind_tab_events(frm) {
		const $page = frm.$wrapper || frm.page?.wrapper;
		if (!$page || !$page.length || $page.data("arco-emp-tab-bound")) {
			return;
		}
		$page.data("arco-emp-tab-bound", 1);

		const sync = function () {
			const show = sync_overview_visibility(frm);
			window.OrgUI?.updateEmployeeForm?.({
				show_overview: !!show,
				is_editing: is_native_edit_context(frm),
				is_dirty: !!frm?.is_dirty?.(),
			});
			fetch_archive_data(frm);
		};

		// Frappe 页签按钮常 stopPropagation，且用 history API 改 hash（无 hashchange）。
		// 用捕获阶段 + MutationObserver 才能稳定感知切换。
		const pageEl = $page.get(0);
		const onCaptureClick = function (e) {
			const link = e.target?.closest?.(".form-tabs .nav-link, .form-tabs button.nav-link");
			if (!link || !pageEl.contains(link)) {
				return;
			}
			setTimeout(sync, 0);
			setTimeout(sync, 50);
			setTimeout(sync, 200);
		};
		pageEl.addEventListener("click", onCaptureClick, true);
		$page.data("arco-emp-tab-capture", onCaptureClick);

		const tabsEl = $page.find(".form-tabs").get(0);
		if (tabsEl && typeof MutationObserver !== "undefined") {
			const mo = new MutationObserver(function () {
				sync();
			});
			mo.observe(tabsEl, {
				attributes: true,
				subtree: true,
				attributeFilter: ["class", "aria-selected"],
			});
			$page.data("arco-emp-tab-mo", mo);
		}

		$(window).on("hashchange.arcoEmpTab popstate.arcoEmpTab", function () {
			setTimeout(sync, 30);
		});
	}

	function mount_or_update(frm) {
		boundFrm = frm;
		const currentName = frm.doc?.name || "";
		if (lastEmployeeName !== currentName) {
			isEditing = !!(frm?.is_new?.() || frm?.doc?.__islocal);
			archiveResetToken += 1;
			archiveRequestVersion += 1;
		}
		const headerEl = ensure_desk_header_root(frm);
		const el = ensure_chrome_root(frm);
		ensure_overview_root(frm);
		const archiveEl = ensure_archive_root(frm);
		if (!el) {
			return;
		}
		polish_dom(frm);
		bind_tab_events(frm);
		const show_overview = sync_overview_visibility(frm);
		const payload = payload_from_frm(frm, {
			show_overview,
			is_editing: is_native_edit_context(frm),
			is_saving: isSaving,
			is_deleting: isDeleting,
		});

		if (headerEl && window.OrgUI?.mountEmployeeFormDeskHeader && !employeeFormDeskHeaderApp) {
			employeeFormDeskHeaderApp = window.OrgUI.mountEmployeeFormDeskHeader(headerEl);
		}
		window.OrgUI?.updateEmployeeFormDeskHeader?.({
			employeeName: payload.is_new ? __("新增员工") : payload.employee_name || payload.name || "",
		});

		if (!window.OrgUI?.mountEmployeeForm) {
			return;
		}

		const handlers = {
			onNavigate(target) {
				navigate_from_overview(frm, target);
			},
			onOverviewUpdated() {
				frm.reload_doc?.()
					.then(() => mount_or_update(frm))
					.catch((error) => console.warn("[employee-form] reload after overview save failed", error));
			},
			onEdit() {
				// 头部「编辑」：进入在职信息预览页，由板块内「编辑」完成修改
				isEditing = false;
				try {
					frm.set_active_tab?.("employment_details");
				} catch (e) {
					/* ignore */
				}
				mount_or_update(frm);
			},
			async onSave() {
				if (!get_form_permissions(frm).can_save || isSaving) return;
				if (!validate_employee_before_save(frm)) return;
				isSaving = true;
				mount_or_update(frm);
				try {
					await frm.save();
					isEditing = false;
					frm.set_active_tab?.("basic_details_tab");
					notify("success", __("员工信息已保存"));
				} catch (error) {
					console.warn("[employee-form] save failed", error);
					notify("error", __("保存失败，请检查必填项和字段格式后重试"));
				} finally {
					isSaving = false;
					mount_or_update(frm);
				}
			},
			async onCancel() {
				if (frm?.is_dirty?.()) {
					const confirmed = await confirm_action(__("当前修改尚未保存，确定放弃这些修改吗？"));
					if (!confirmed) return;
				}
				if (frm?.is_new?.() || frm?.doc?.__islocal) {
					if (frm.doc) frm.doc.__unsaved = 0;
					frappe.set_route("List", "Employee");
					return;
				}
				try {
					await frm.reload_doc();
					isEditing = false;
					frm.set_active_tab?.("basic_details_tab");
					notify("info", __("已放弃未保存的修改"));
				} catch (error) {
					console.warn("[employee-form] reload failed", error);
					notify("error", __("无法恢复员工信息，请刷新页面后重试"));
				}
				mount_or_update(frm);
			},
			onDelete() {
				if (frm.doc?.status !== "Left") {
					notify("warning", __("请先办理员工离职并保存后再删除"));
					return;
				}
				if (!get_form_permissions(frm).can_delete || !frm.doc?.name || isDeleting) return;
				isDeleting = true;
				mount_or_update(frm);
				frappe.call({
					method: "frappe.client.delete",
					args: { doctype: "Employee", name: frm.doc.name },
					freeze: true,
					freeze_message: __("正在删除员工…"),
					callback() {
						isDeleting = false;
						notify("success", __("员工已删除"));
						frappe.set_route("List", "Employee");
					},
					error() {
						isDeleting = false;
						notify("error", __("删除失败，该员工可能存在关联业务数据或当前用户权限不足"));
						mount_or_update(frm);
					},
				});
			},
			onTransfer() {
				trigger_hr_transfer(frm);
			},
			onMore(key) {
				handle_more_action(frm, key);
			},
			moreActions: build_more_actions(frm),
		};

		if (lastEmployeeName && currentName && lastEmployeeName !== currentName) {
			window.OrgUI.updateEmployeeForm?.({ name: "", show_overview: !!show_overview });
		}
		lastEmployeeName = currentName;

		if (!employeeFormApp) {
			employeeFormApp = window.OrgUI.mountEmployeeForm(el, payload, handlers);
		} else {
			window.OrgUI.setEmployeeFormHandlers?.(handlers);
			window.OrgUI.updateEmployeeForm(payload);
		}

		if (archiveEl && window.OrgUI?.mountEmployeeArchivePanels) {
			const archiveHandlers = {
				onUpdated(archiveDoc) {
					if (!archiveDoc) {
						fetch_archive_data(frm, { force: true });
						return;
					}
					window.OrgUI.updateEmployeeArchivePanels({
						doc: archiveDoc,
						loading: false,
						can_edit: !!get_form_permissions(frm).can_edit,
						activeTab: get_active_tab(frm),
						resetToken: archiveResetToken,
					});
					frm.reload_doc?.().catch((error) => {
						console.warn("[employee-form] reload after archive save failed", error);
					});
				},
			};
			if (!employeeArchiveApp) {
				employeeArchiveApp = window.OrgUI.mountEmployeeArchivePanels(
					archiveEl,
					{
						activeTab: get_active_tab(frm),
						loading: false,
						can_edit: !!get_form_permissions(frm).can_edit,
						resetToken: archiveResetToken,
						doc: {},
					},
					archiveHandlers
				);
			} else {
				window.OrgUI.setEmployeeArchiveHandlers?.(archiveHandlers);
			}
			fetch_archive_data(frm);
		}

		fetch_extra_stats(frm);
	}

	function teardown() {
		try {
			employeeFormApp?.unmount?.();
		} catch (e) {
			/* ignore */
		}
		try {
			employeeFormDeskHeaderApp?.unmount?.();
		} catch (e) {
			/* ignore */
		}
		try {
			employeeArchiveApp?.unmount?.();
		} catch (e) {
			/* ignore */
		}
		const $page = $(".arco-employee-form-page");
		const pageEl = $page.get(0);
		const capture = $page.data("arco-emp-tab-capture");
		if (pageEl && capture) {
			pageEl.removeEventListener("click", capture, true);
		}
		try {
			$page.data("arco-emp-tab-mo")?.disconnect?.();
		} catch (e) {
			/* ignore */
		}
		try {
			$page.data("arco-emp-zh-mo")?.disconnect?.();
		} catch (e) {
			/* ignore */
		}
		$page.removeData("arco-emp-tab-bound arco-emp-tab-capture arco-emp-tab-mo arco-emp-zh-mo");
		employeeFormApp = null;
		employeeFormDeskHeaderApp = null;
		employeeArchiveApp = null;
		boundFrm = null;
		lastEmployeeName = "";
		lastActiveTab = "";
		isEditing = false;
		isSaving = false;
		isDeleting = false;
		statsCacheKey = "";
		statsRequestVersion += 1;
		archiveRequestVersion += 1;
		archiveResetToken += 1;
		clearTimeout(transitionTimer);
		transitionTimer = null;
		cancelAnimationFrame(translationFrame);
		translationFrame = null;
		$(window).off("hashchange.arcoEmpTab popstate.arcoEmpTab");
		document.body.classList.remove("arco-employee-form");
		document.querySelector("#hr-employee-form-header-root")?.remove();
		document.querySelector("#employee-arco-chrome-root")?.remove();
		document.querySelector("#employee-arco-overview-root")?.remove();
		document.querySelector("#employee-arco-archive-root")?.remove();
	}

	const watch_fields = [
		"employee_name",
		"employee_number",
		"status",
		"department",
		"designation",
		"company",
		"branch",
		"group_name",
		"employment_type",
		"image",
		"date_of_joining",
		"cell_number",
		"company_email",
		"personal_email",
		"prefered_email",
		"reports_to",
		"grade",
		"gender",
		"marital_status",
		"blood_group",
		"passport_number",
		"health_insurance_provider",
		"health_insurance_no",
		"default_shift",
		"person_to_be_contacted",
		"emergency_phone_number",
		"relation",
		"bio",
		"attendance_device_id",
		"hr_job_title",
		"hr_position_category",
		"hr_job_grade_level",
		"hr_work_city",
		"hr_work_location",
		"hr_employee_identity",
		"hr_oa_code",
		"hr_native_place",
		"hr_id_number",
		"hr_contract_type",
		"hr_contract_status",
		"hr_contract_expire_date",
		"hr_background_status",
	];

	const ORG_AUTOCOMPLETE_DEFAULTS = {
		hr_job_title: [
			"总经理",
			"副总经理",
			"总监",
			"高级经理",
			"经理",
			"主管",
			"组长",
			"专员",
			"助理",
			"实习生",
			"其他",
		],
	};

	function load_org_tree(company) {
		const key = String(company || "");
		if (!orgTreeRequests.has(key)) {
			const request = frappe
				.call({
					method: "employee_roster.hr_roster.page.orgchart.orgchart.get_org_tree",
					args: { company: key || undefined },
				})
				.then((response) => response?.message || { roots: [] })
				.catch((error) => {
					orgTreeRequests.delete(key);
					throw error;
				});
			orgTreeRequests.set(key, request);
		}
		return orgTreeRequests.get(key);
	}

	function collect_department_groups(tree, department) {
		const groups = [];
		const visit = (node, insideDepartment) => {
			if (!node || node.is_employee) return;
			const isSelectedDepartment = node.name === department;
			const isInsideDepartment = insideDepartment || isSelectedDepartment;
			// 与架构图保持同一兼容规则：旧数据未标记 org_type 时，以“组”后缀识别。
			const isGroupNode = node.org_type === "组" || String(node.title || "").trim().endsWith("组");
			if (isInsideDepartment && isGroupNode && node.title) {
				groups.push(String(node.title).trim());
			}
			(node.children || []).forEach((child) => visit(child, isInsideDepartment));
		};
		(tree?.roots || []).forEach((root) => visit(root, false));
		return uniq_sorted(groups);
	}

	function load_org_group_values(frm) {
		if (!frm?.doc?.department) return Promise.resolve([]);
		return load_org_tree(frm.doc.company).then((tree) =>
			collect_department_groups(tree, frm.doc.department)
		);
	}

	function uniq_sorted(values) {
		return [...new Set((values || []).filter(Boolean))].sort((a, b) =>
			String(a).localeCompare(String(b), "zh")
		);
	}

	function set_autocomplete_options(frm, fieldname, values) {
		if (!frm?.fields_dict?.[fieldname]) return;
		const options = uniq_sorted(values).join("\n");
		frm.set_df_property(fieldname, "options", options);
		frm.refresh_field(fieldname);
	}

	function sync_org_group_options(frm, { clearInvalid = false } = {}) {
		const department = frm?.doc?.department || "";
		const company = frm?.doc?.company || "";
		const requestKey = `${company}::${department}`;
		frm._arcoOrgGroupRequestKey = requestKey;
		frm.toggle_enable("group_name", Boolean(department));

		if (!department) {
			set_autocomplete_options(frm, "group_name", []);
			return Promise.resolve([]);
		}

		return load_org_group_values(frm)
			.then((groups) => {
				if (frm._arcoOrgGroupRequestKey !== requestKey) return groups;
				const current = String(frm.doc.group_name || "").trim();
				set_autocomplete_options(frm, "group_name", groups);
				const control = frm.fields_dict?.group_name;
				if (control) {
					control._arcoChoiceOptions = groups.map((value) => ({ label: value, value }));
				}
				if (clearInvalid && current && !groups.includes(current)) {
					return frm.set_value("group_name", "").then(() => {
						notify("warning", __("部门已变更，请重新选择该部门下的组别"));
						return groups;
					});
				}
				return groups;
			})
			.catch((error) => {
				console.warn("[employee-form] sync org groups failed", error);
				return [];
			});
	}

	function setup_org_select_fields(frm) {
		if (!frm || frm.doctype !== "Employee") return;

		// 性别仅保留中国 HR 常用选项
		frm.set_query("gender", () => ({
			filters: { name: ["in", ["男", "女"]] },
		}));

		// 部门与组别共用架构图的 Department 树：部门选择器不允许选到“组”节点。
		frm.set_query("department", () => {
			const filters = {
				disabled: 0,
				org_type: ["!=", "组"],
				department_name: ["not like", "%组"],
			};
			if (frm.doc.company) filters.company = frm.doc.company;
			return { filters };
		});

		// 考勤假期：不展示「默认班次」
		if (frm.fields_dict?.default_shift) {
			frm.set_df_property("default_shift", "hidden", 1);
		}

		// 去掉 Link 字段悬停出现的「打开链接」跳转按钮（组织信息只要下拉选）
		const hide_open_fields = [
			"company",
			"department",
			"designation",
			"grade",
			"reports_to",
			"branch",
			"employment_type",
			"hr_concurrent_post",
		];
		hide_open_fields.forEach((fieldname) => {
			const control = frm.fields_dict?.[fieldname];
			const $open = control?.$link_open || control?.$input_area?.find(".btn-open");
			if ($open?.length) {
				$open.remove();
			}
		});

		sync_org_group_options(frm).then(() => enhance_choice_triggers(frm));

		const titleDefaults = ORG_AUTOCOMPLETE_DEFAULTS.hr_job_title.slice();
		if (frm.doc.hr_job_title) titleDefaults.push(frm.doc.hr_job_title);
		frappe.db
			.get_list("Employee", {
				fields: ["hr_job_title"],
				filters: [["hr_job_title", "is", "set"]],
				limit: 200,
			})
			.then((rows) => {
				const titles = titleDefaults.concat((rows || []).map((row) => row.hr_job_title));
				set_autocomplete_options(frm, "hr_job_title", titles);
			})
			.catch(() => set_autocomplete_options(frm, "hr_job_title", titleDefaults));
	}

	const handlers = {
		onload(frm) {
			setup_org_select_fields(frm);
			mount_or_update(frm);
		},
		refresh(frm) {
			statsCacheKey = "";
			setup_org_select_fields(frm);
			mount_or_update(frm);
		},
		validate(frm) {
			if (!validate_employee_before_save(frm)) {
				frappe.validated = false;
			}
		},
	};

	watch_fields.forEach((field) => {
		handlers[field] = function (frm) {
			mount_or_update(frm);
		};
	});

	handlers.department = function (frm) {
		sync_org_group_options(frm, { clearInvalid: true }).then(() => {
			enhance_choice_triggers(frm);
			mount_or_update(frm);
		});
	};

	handlers.company = function (frm) {
		orgTreeRequests.delete(String(frm.doc.company || ""));
		setup_org_select_fields(frm);
		mount_or_update(frm);
	};

	handlers.group_name = function (frm) {
		const selected = String(frm.doc.group_name || "").trim();
		if (!selected) {
			mount_or_update(frm);
			return;
		}
		load_org_group_values(frm).then((groups) => {
			if (String(frm.doc.group_name || "").trim() !== selected) return;
			if (!groups.includes(selected)) {
				frm.set_value("group_name", "").then(() =>
					notify("warning", __("组别必须从当前部门的组织架构中选择"))
				);
				return;
			}
			mount_or_update(frm);
		});
	};

	frappe.ui.form.on("Employee", handlers);

	$(document).on("page-change", function () {
		const route = frappe.get_route_str?.() || "";
		if (!String(route).startsWith("Form/Employee")) {
			teardown();
		}
	});
})();
