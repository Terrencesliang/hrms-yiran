// Copyright (c) 2026 stillgroup
// License: MIT
/**
 * Employee Form — Arco Design：
 * 仅「概况」页签（#basic_details_tab）展示摘要仪表盘；
 * 其它页签保持原生表单（可有轻量 Arco CSS）。
 * cache: 20260907l
 */
(function () {
	let employeeFormApp = null;
	let boundFrm = null;
	let lastActiveTab = "";
	let transitionTimer = null;
	let translationFrame = null;

	const EMPLOYEE_ZH_TEXT = {
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
		Mon: "周一",
		Wed: "周三",
		Fri: "周五",
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
		observer.observe($page.get(0), { childList: true, subtree: true });
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
			{ value: doc.date_of_joining, label: "补充入职日期", target: "employment_details" },
			{ value: doc.company, label: "补充所属公司", target: "company" },
			{ value: doc.department, label: "补充所属部门", target: "department" },
			{ value: doc.designation, label: "补充员工职位", target: "designation" },
			{ value: doc.branch, label: "补充分支机构", target: "branch" },
			{ value: doc.cell_number, label: "补充手机号", target: "contact" },
			{ value: doc.company_email || doc.personal_email, label: "补充邮箱", target: "contact" },
			{ value: doc.person_to_be_contacted && doc.emergency_phone_number, label: "完善紧急联系人", target: "contact" },
			{ value: doc.bio || (doc.education || []).length || (doc.external_work_history || []).length, label: "完善个人履历", target: "bio" },
		];
		const complete = checks.filter((item) => !!item.value).length;
		return {
			profile_completion: Math.round((complete / checks.length) * 100),
			profile_missing: checks.filter((item) => !item.value).map(({ label, target }) => ({ label, target })),
		};
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
			name: doc.name || "",
			employee_name: doc.employee_name || doc.first_name || "",
			status: doc.status || "",
			department: doc.department || "",
			designation: doc.designation || "",
			company: doc.company || "",
			branch: doc.branch || "",
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
			education,
			external_work_history,
			internal_work_history,
			tenure_days: calc_tenure_days(doc.date_of_joining),
			leave_balance: extras.leave_balance ?? null,
			attendance_month: extras.attendance_month ?? null,
			related_count,
			show_overview: extras.show_overview !== false,
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
		bind_localization_observer($page);
		schedule_localization($page);
	}

	function sync_overview_visibility(frm) {
		const $page = frm.$wrapper || frm.page?.wrapper;
		if (!$page || !$page.length) {
			return false;
		}
		const active = get_active_tab(frm);
		// 摘要仪表盘仅挂在「概况」页签，其它 hash 页签保持原生表单
		const isOverview = active === "basic_details_tab";
		$page.toggleClass("arco-emp-overview-active", isOverview);
		// 身份头始终保留，避免切换页签时页面基准突然上移；Vue 内部会平滑收起详情。
		$page.find("#employee-arco-chrome-root").show();
		$page.find("#employee-arco-overview-root").toggle(isOverview);
		$page.find(".form-layout .form-section").toggleClass("arco-emp-native-hidden", isOverview);

		if (lastActiveTab && lastActiveTab !== active) {
			$page.removeClass("arco-emp-tab-entering");
			void $page.get(0)?.offsetWidth;
			$page.addClass("arco-emp-tab-entering");
			clearTimeout(transitionTimer);
			transitionTimer = setTimeout(() => $page.removeClass("arco-emp-tab-entering"), 260);
		}
		lastActiveTab = active;
		schedule_localization($page);
		return isOverview;
	}

	function navigate_from_overview(frm, target) {
		const fieldMap = {
			bio: "bio",
			education: "education",
			external_work_history: "external_work_history",
			internal_work_history: "internal_work_history",
			contact: "cell_number",
			personal: "marital_status",
		};
		const fieldname = fieldMap[target] || target;
		try {
			if (["bio", "education", "external_work_history", "internal_work_history"].includes(fieldname)) {
				frm.set_active_tab?.("profile_tab");
			} else if (["cell_number", "company_email", "person_to_be_contacted"].includes(fieldname)) {
				frm.set_active_tab?.("contact_details");
			} else if (["marital_status", "blood_group", "passport_number"].includes(fieldname)) {
				frm.set_active_tab?.("personal_details");
			}
		} catch (e) {
			/* ignore */
		}
		setTimeout(() => {
			try {
				frm.scroll_to_field?.(fieldname);
			} catch (e) {
				/* ignore */
			}
		}, 80);
	}

	function fetch_extra_stats(frm) {
		const doc = frm.doc || {};
		if (!doc.name || !doc.date_of_joining) {
			return;
		}

		const today = frappe.datetime.get_today();
		const month_start = today.slice(0, 8) + "01";

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

	function bind_tab_events(frm) {
		const $page = frm.$wrapper || frm.page?.wrapper;
		if (!$page || !$page.length || $page.data("arco-emp-tab-bound")) {
			return;
		}
		$page.data("arco-emp-tab-bound", 1);

		const sync = function () {
			const show = sync_overview_visibility(frm);
			window.OrgUI?.updateEmployeeForm?.({ show_overview: !!show });
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
		const el = ensure_chrome_root(frm);
		ensure_overview_root(frm);
		if (!el) {
			return;
		}
		polish_dom(frm);
		bind_tab_events(frm);
		const show_overview = sync_overview_visibility(frm);
		const payload = payload_from_frm(frm, { show_overview });

		if (!window.OrgUI?.mountEmployeeForm) {
			return;
		}

		const handlers = {
			onNavigate(target) {
				navigate_from_overview(frm, target);
			},
		};

		if (!employeeFormApp) {
			employeeFormApp = window.OrgUI.mountEmployeeForm(el, payload, handlers);
		} else {
			window.OrgUI.setEmployeeFormHandlers?.(handlers);
			window.OrgUI.updateEmployeeForm(payload);
		}

		fetch_extra_stats(frm);
	}

	function teardown() {
		try {
			employeeFormApp?.unmount?.();
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
		boundFrm = null;
		lastActiveTab = "";
		clearTimeout(transitionTimer);
		transitionTimer = null;
		cancelAnimationFrame(translationFrame);
		translationFrame = null;
		$(window).off("hashchange.arcoEmpTab popstate.arcoEmpTab");
		document.body.classList.remove("arco-employee-form");
		document.querySelector("#employee-arco-chrome-root")?.remove();
		document.querySelector("#employee-arco-overview-root")?.remove();
	}

	const watch_fields = [
		"employee_name",
		"status",
		"department",
		"designation",
		"company",
		"branch",
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
	];

	const handlers = {
		onload(frm) {
			mount_or_update(frm);
		},
		refresh(frm) {
			mount_or_update(frm);
		},
	};

	watch_fields.forEach((field) => {
		handlers[field] = function (frm) {
			mount_or_update(frm);
		};
	});

	frappe.ui.form.on("Employee", handlers);

	$(document).on("page-change", function () {
		const route = frappe.get_route_str?.() || "";
		if (!String(route).startsWith("Form/Employee")) {
			teardown();
		}
	});
})();
