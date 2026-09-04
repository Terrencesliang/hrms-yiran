frappe.provide("employee_roster.unified_sidebar");

(function () {
	// Harden Frappe helper: current_route may be null before first resolve.
	if (typeof frappe.get_route_str === "function") {
		const _orig_get_route_str = frappe.get_route_str;
		frappe.get_route_str = function () {
			try {
				const parts = frappe.router?.current_route;
				if (!Array.isArray(parts)) return "";
				return parts.filter(Boolean).join("/");
			} catch (e) {
				try {
					return _orig_get_route_str();
				} catch (err) {
					return "";
				}
			}
		};
	}

	const ROOT_ID = "hr-unified-sidebar-root";
	const NAVBAR_ROOT_ID = "hr-arco-navbar-root";
	const BODY_CLASS = "hr-unified-sidebar-active";

	const MODULE_TAB_LABELS = {
		"HR Setup": __("人事"),
		Tenure: __("在职"),
		Recruitment: __("招聘"),
		"Shift & Attendance": __("考勤"),
		Leaves: __("假期"),
		Expenses: __("费用"),
		Performance: __("绩效"),
		Payroll: __("薪资"),
		"Tax & Benefits": __("个税"),
		hr_roster: __("审批"),
		Contract: __("合同"),
	};

	/** Preferred module order; unlisted modules keep their relative default order after these. */
	const MODULE_ORDER = [
		"HR Setup",
		"Shift & Attendance",
		"hr_roster",
		"Contract",
		"Recruitment",
		"Payroll",
	];

	/** Modules injected into the Arco menu when no Dock/Sidebar entry exists yet. */
	const SYNTHETIC_MODULES = {
		Contract: {
			items: [
				{
					label: __("合同台账"),
					path: "/app/employee-archive",
				},
				{
					label: __("劳动合同"),
					path: "/app/employee-archive",
				},
			],
		},
	};

	const FALLBACK_TAB_MODULES = Object.entries(MODULE_TAB_LABELS).map(([key, label]) => ({
		key,
		label,
	}));

	const HR_CONTEXT_MODULES = new Set([
		"HR Setup",
		"Recruitment",
		"Shift & Attendance",
		"Payroll",
		"Tax & Benefits",
		"Tenure",
		"Leaves",
		"Expenses",
		"Performance",
		"hr_roster",
		"Contract",
	]);

	const SKIP_LINK_LABELS = new Set([]);

	const SIDEBAR_LABEL_MAP = {
		// Common
		Home: "主页",
		Dashboard: "数据面板",
		Reports: "报表",
		Setup: "设置",
		Settings: "设置",
		Planning: "计划",
		Overtime: "日常操作",
		Travel: "差旅",
		// HR Setup
		Company: "公司",
		Branch: "分支机构",
		Department: "部门",
		Designation: "职位",
		"Employee Group": "员工组",
		"Employee Grade": "员工职级",
		"HR Settings": "人事设置",
		// Tenure
		"Employee Onboarding": "员工入职",
		"Employee Separation": "员工离职",
		"Employee Grievance": "员工申诉",
		"Employee Exits": "离职报表",
		"Employee Birthday": "员工生日",
		"Employee Information": "员工信息",
		"Employee Analytics": "员工分析",
		"Employee Skill Map": "员工技能图",
		"Grievance Type": "申诉类型",
		"Training Program": "培训项目",
		"Training Event": "培训活动",
		"Training Feedback": "培训反馈",
		"Training Result": "培训结果",
		// Recruitment
		"Hiring Pipeline": "招聘流程",
		"Job Opening": "职位开放",
		"Job Applicant": "应聘者",
		Interview: "面试",
		"Job Offer": "录用通知",
		"Appointment Letter": "录用函",
		"Job Requisition": "用人申请",
		"Staffing Plan": "编制计划",
		"Employee Referral": "内部推荐",
		"Recruitment Analytics": "招聘分析",
		"Interview Type": "面试类型",
		"Job Opening Template": "职位模板",
		"Appointment Letter Template": "录用函模板",
		"Job Offer Term Template": "录用条款模板",
		"Job Portal": "招聘门户",
		// Attendance
		Roster: "排班表",
		"Employee Attendance Tool": "考勤工具",
		"Employee Checkin": "打卡记录",
		"Shift Request": "班次申请",
		"Attendance Request": "考勤申请",
		"Overtime Type": "加班类型",
		"Overtime Slip": "加班单",
		"Monthly Attendance Sheet": "月度考勤表",
		"Shift Attendance": "班次考勤",
		"Employee Hours Utilization": "工时利用率",
		"Project Profitability": "项目盈利分析",
		"Shift Type": "班次类型",
		"Shift Location": "打卡地点",
		"Shift Schedule": "排班计划",
		"Activity Type": "活动类型",
		Timesheet: "工时表",
		"Attendance Rules": "考勤规则",
		"Attendance Deduction Rule": "考勤扣款规则",
		"Attendance Group": "考勤组",
		// Leaves
		"Leave Application": "请假申请",
		"Leave Encashment": "假期折现",
		"Leave Control Panel": "假期控制台",
		"Leave Policy Assignment": "假期政策分配",
		"Leave Allocation": "假期配额",
		"Leave Balance": "假期余额",
		"Leave Balance Summary": "假期余额汇总",
		"Employees Working on a Holiday": "节假日在岗员工",
		"Holiday List": "节假日列表",
		"Holiday List Assignment": "节假日分配",
		"Leave Period": "假期周期",
		"Leave Policy": "假期政策",
		"Leave Block List": "假期黑名单",
		"Leave Type": "假期类型",
		// Expenses
		"Employee Advance": "员工预支",
		"Expense Claim": "费用报销",
		"Purpose of Travel": "出差事由",
		"Travel Request": "出差申请",
		"Vehicle Log": "用车记录",
		"Accounting Entries": "会计分录",
		"Payment Entry": "付款凭证",
		"Journal Entry": "记账凭证",
		"Unpaid Expense Claim": "未付报销",
		"Vehicle Expenses": "车辆费用",
		"Accounts Receivable": "应收账款",
		"Accounts Payable": "应付账款",
		"General Ledger": "总账",
		"Expense Claim Type": "报销类型",
		Driver: "驾驶员",
		Vehicle: "车辆",
		// Performance
		Goal: "目标",
		"Appraisal Cycle": "考核周期",
		Appraisal: "绩效考核",
		"Employee Performance Feedback": "绩效反馈",
		"Employee Promotion": "员工晋升",
		"Appraisal Overview": "考核概览",
		"Appraisal Template": "考核模板",
		KRA: "关键结果领域",
		"Employee Feedback Criteria": "反馈评价标准",
		// Payroll
		"Payroll Entry": "薪资发放",
		"Salary Structure Assignment": "薪资结构分配",
		"Salary Slip": "工资条",
		"Additional Salary": "额外薪资",
		"Salary Withholding": "薪资暂扣",
		"Employee CTC Break-up": "员工成本明细",
		"Salary Register": "薪资登记表",
		"Income Tax Deductions": "个税扣缴",
		"Professional Tax Deductions": "职业税扣缴",
		"Salary Component": "薪资项目",
		"Salary Structure": "薪资结构",
		// Tax & Benefits
		"Exemption Declaration": "免税申报",
		"Exemption Submission Proof": "免税证明提交",
		"Benefit Application": "福利申请",
		"Benefit Claim": "福利报销",
		"Income Tax Computation": "个税计算",
		"Accrued Earnings Report": "应计收入报表",
		"Income Tax Slab": "个税税率表",
		"Exemption Category": "免税类别",
		// Approval / Contract
		"Approval Form": "审批表单",
		"Approval Forms": "审批表单",
		"Approval Template": "审批模板",
		"Approval Templates": "审批模板库",
		"Approval Template Library": "审批模板库",
	};

	const SECTION_LABEL_MAP = {
		Reports: "报表",
		Setup: "设置",
		Planning: "计划",
		Overtime: "日常操作",
		Travel: "差旅",
		"Accounting Entries": "会计分录",
	};

	const MODULE_FLOW_LABELS = {
		"HR Setup": "业务主功能",
		Tenure: "业务主功能",
		Recruitment: "招聘流程",
		"Shift & Attendance": "日常操作",
		Leaves: "业务主功能",
		Expenses: "业务主功能",
		Performance: "业务主功能",
		Payroll: "业务主功能",
		"Tax & Benefits": "业务主功能",
		hr_roster: "业务主功能",
		Contract: "业务主功能",
	};

	function translateSidebarLabel(label) {
		if (!label) return "";
		if (SIDEBAR_LABEL_MAP[label]) return SIDEBAR_LABEL_MAP[label];
		if (SECTION_LABEL_MAP[label]) return SECTION_LABEL_MAP[label];
		if (MODULE_TAB_LABELS[label]) return MODULE_TAB_LABELS[label];
		const translated = __(label);
		return translated && translated !== label ? translated : label;
	}

	const controller = {
		initialized: false,
		menuModule: null,
		$root: null,
		vueApp: null,
		navbarApp: null,
		compact: false,

		init() {
			if (this.initialized || !frappe.boot.setup_complete) return;
			this.initialized = true;
			this.compact = window.localStorage.getItem("hr_sidebar_compact") === "1";

			$(document).on("sidebar_setup", (_event, data) => {
				this.onSidebarSetup(data?.sidebar);
			});

			frappe.router.on("change", () => {
				window.requestAnimationFrame(() => this.refresh());
			});

			$(document).on("sidebar-expand.hr-unified", () => {
				this.syncCollapseControls();
			});

			this.waitForSidebar(() => this.refresh());
		},

		waitForSidebar(callback, attempts = 40) {
			if (frappe.app?.sidebar?.wrapper) {
				callback();
				return;
			}
			if (attempts <= 0) return;
			setTimeout(() => this.waitForSidebar(callback, attempts - 1), 150);
		},

		getHrmsApp() {
			return (frappe.boot.apps_data?.apps || []).find((app) => app.name === "hrms");
		},

		getRouteStrSafe() {
			try {
				const parts = frappe.router?.current_route;
				if (!Array.isArray(parts)) return "";
				return parts.filter(Boolean).join("/");
			} catch (e) {
				return "";
			}
		},

		isHrContext() {
			try {
				const current = frappe.app?.sidebar?.current_module;
				if (current && HR_CONTEXT_MODULES.has(current)) return true;
				// Keep sidebar mounted while navigating between items under the last HR module.
				if (this.menuModule && HR_CONTEXT_MODULES.has(this.menuModule)) return true;

				// Never call frappe.get_route_str() — it does current_route.join
				// and throws when current_route is still null during boot.
				const route = this.getRouteStrSafe();
				if (!route) return false;

				const hrPrefixes = [
					"List/Employee",
					"Form/Employee",
					"employee",
					"recruiting-",
					"org-diagram",
					"orgchart",
					"roster",
					"employee-archive",
					"attendance-rules",
					"approvals",
					"approval-templates",
					"approval-workspace",
					"approval-form-designer",
					"Company",
					"Branch",
					"Department",
					"Designation",
					"Employee Group",
					"Employee Grade",
					"HR Settings",
					"hr-settings",
					"List/Company",
					"List/Branch",
					"List/Department",
					"List/Designation",
				];
				return hrPrefixes.some(
					(prefix) => route === prefix || route.startsWith(prefix + "/") || route.startsWith(prefix)
				);
			} catch (e) {
				return false;
			}
		},

		shouldActivate() {
			try {
				return !!this.getHrmsApp() && this.isHrContext();
			} catch (e) {
				return false;
			}
		},

		onSidebarSetup(sidebar) {
			if (!sidebar) return;
			this.refresh();
		},

		refresh() {
			try {
				if (!this.shouldActivate()) {
					// Debounce teardown so brief route transitions don't remount the sidebar.
					clearTimeout(this._deactivateTimer);
					this._deactivateTimer = setTimeout(() => {
						if (!this.shouldActivate()) this.deactivate();
					}, 120);
					return;
				}

				clearTimeout(this._deactivateTimer);
				this._deactivateTimer = null;

				document.body.classList.add(BODY_CLASS);
				if (!frappe.is_mobile()) document.body.classList.remove("sidebar-collapsed");
				document.body.classList.toggle("hr-sidebar-compact", this.compact);
				this.ensureNavbar();
				this.ensureRoot();
				this.hideStandardChrome();
				if (window.OrgUI?.mountSidebar) {
					this.mountArcoNavbar();
					this.mountArcoSidebar();
					this.pushArcoState();
				} else {
					this.renderHeader();
					this.renderTabs();
					this.renderMenu();
				}
				this.enhanceUserFooter();
				this.ensureCollapseControls();
			} catch (e) {
				console.warn("[hr-unified-sidebar] refresh skipped:", e);
			}
		},

		deactivate() {
			document.body.classList.remove(BODY_CLASS);
			document.body.classList.remove("hr-sidebar-compact");
			try {
				this.vueApp?.unmount?.();
			} catch (e) {
				/* ignore */
			}
			try {
				this.navbarApp?.unmount?.();
			} catch (e) {
				/* ignore */
			}
			this.vueApp = null;
			this.navbarApp = null;
			this.$root?.remove();
			this.$root = null;
			document.getElementById(NAVBAR_ROOT_ID)?.remove();
			document.querySelector(".hr-unified-expand-btn")?.remove();
			this.restoreStandardChrome();
		},

		ensureRoot() {
			const sidebar = document.querySelector(".body-sidebar");
			if (!sidebar) return;

			let root = document.getElementById(ROOT_ID);
			if (!root) {
				root = document.createElement("div");
				root.id = ROOT_ID;
				root.className = "hr-unified-sidebar arco-hr-sidebar-host";
				sidebar.insertBefore(root, sidebar.firstChild);
			}
			this.$root = $(root);
		},


		ensureNavbar() {
			let root = document.getElementById(NAVBAR_ROOT_ID);
			if (!root) {
				root = document.createElement("div");
				root.id = NAVBAR_ROOT_ID;
				root.className = "arco-hr-navbar-host";
				document.body.insertBefore(root, document.body.firstChild);
			}
		},

		mountArcoNavbar() {
			const root = document.getElementById(NAVBAR_ROOT_ID);
			if (!root || this.navbarApp || !window.OrgUI?.mountNavbar) return;

			this.navbarApp = window.OrgUI.mountNavbar(root, {
				onSearch: () => {
					$(".navbar-modal-search-mobile").first().trigger("click");
				},
				onNotifications: () => {
					const trigger =
						document.querySelector(".dropdown-notifications .nav-link") ||
						document.querySelector(".notifications-icon") ||
						document.querySelector(".dropdown-notifications > a") ||
						document.querySelector('[data-toggle="dropdown"].notifications');
					if (trigger) {
						trigger.click();
						return;
					}
					frappe.show_alert?.({ message: __("暂无通知入口"), indicator: "orange" });
				},
				onSettings: () => {
					frappe.set_route("Form", "User", frappe.session.user);
				},
				onProfile: () => {
					frappe.set_route("Form", "User", frappe.session.user);
				},
				onLogout: () => {
					frappe.app?.logout?.();
				},
			});
		},

		pushNavbarState() {
			if (!window.OrgUI?.updateNavbar) return;
			const user = frappe.session?.user || "";
			const fullName = frappe.boot?.user?.full_name || frappe.user?.full_name?.() || user;

			let notificationCount = 0;
			try {
				const el = document.querySelector(
					".notifications-icon .notifications-seen, .dropdown-notifications .badge, .notification-indicator"
				);
				const raw = el?.textContent?.trim?.() || "";
				const n = parseInt(raw, 10);
				if (!Number.isNaN(n)) notificationCount = n;
				else if (document.querySelector(".notifications-icon .notifications-seen")?.classList?.contains?.("unseen")) {
					notificationCount = 1;
				}
			} catch (e) {
				/* ignore */
			}

			window.OrgUI.updateNavbar({
				title: "HR Pro",
				user,
				fullName,
				avatar: frappe.boot?.user?.user_image || "",
				notificationCount,
			});
		},

		mountArcoSidebar() {
			const root = document.getElementById(ROOT_ID);
			if (!root || this.vueApp) return;
			root.classList.add("arco-hr-sidebar-host");
			this.vueApp = window.OrgUI.mountSidebar(root, {
				onWorkspace: (ws) => {
					if (ws?.module) {
						this.menuModule = HR_CONTEXT_MODULES.has(ws.module) ? ws.module : null;
						frappe.app.sidebar.open_module(ws.module);
					} else if (ws?.route) {
						this.menuModule = null;
						frappe.set_route(ws.route);
					}
				},
				onCollapse: () => frappe.app?.sidebar?.close?.(),
				onToggleCompact: () => this.toggleCompact(),
				onSearch: () => {
					$(".navbar-modal-search-mobile").first().trigger("click");
				},
				onTabChange: (moduleKey) => {
					if (!moduleKey) return;
					this.menuModule = moduleKey;
					if (frappe.app?.sidebar?.current_module !== moduleKey) {
						frappe.app.sidebar.open_module(moduleKey);
					}
					this.pushArcoState();
				},
				onNavigate: (item) => {
					if (item?.module) {
						this.menuModule = item.module;
					}
					if (frappe.is_mobile()) {
						frappe.app.sidebar.close();
					}
					this.navigateSidebarItem(item);
				},
			});
		},

		navigateSidebarItem(item) {
			if (!item) return;
			if (item.openInNewTab && item.path) {
				window.open(item.path, "_blank", "noopener");
				return;
			}

			// Prefer typed routes to avoid /app/employee → List/Employee redirect flicker.
			const type = item.link_type;
			const linkTo = item.link_to;
			try {
				if (type === "DocType" && linkTo) {
					frappe.set_route("List", linkTo);
					return;
				}
				if (type === "Page" && linkTo) {
					frappe.set_route(linkTo);
					return;
				}
				if (type === "Workspace" && linkTo) {
					frappe.set_route(linkTo);
					return;
				}
				if (type === "Dashboard" && linkTo) {
					frappe.set_route("dashboard-view", linkTo);
					return;
				}
				if (type === "URL" && item.path) {
					if (item.path.startsWith("http")) {
						window.location.href = item.path;
						return;
					}
				}
			} catch (e) {
				console.warn("[hr-unified-sidebar] typed navigate failed:", e);
			}

			const path = item.path || "#";
			if (!path || path === "#") return;
			if (path.startsWith("http")) {
				window.location.href = path;
				return;
			}

			try {
				const url = new URL(path, window.location.origin);
				let parts = url.pathname.replace(/^\/+/, "").split("/").filter(Boolean);
				if (parts[0] === "desk" || parts[0] === "app") parts = parts.slice(1);

				const hash = (url.hash || "").replace(/^#\/?/, "");
				if (hash && !parts.length) {
					frappe.set_route(...hash.split("/").filter(Boolean));
					return;
				}

				// Single-segment DocType shortcuts → List/<Doctype>
				if (parts.length === 1 && frappe.boot?.user?.can_read?.includes?.(parts[0])) {
					frappe.set_route("List", parts[0]);
					return;
				}

				if (parts.length) frappe.set_route(...parts);
			} catch (e) {
				window.location.href = path;
			}
		},

		pushArcoState() {
			if (!window.OrgUI?.updateSidebar) return;

			this.pushNavbarState();

			const menuEl = document.querySelector(".arco-hr-menu-wrap .arco-menu, .arco-hr-sidebar .arco-menu");
			const scrollTop = menuEl?.scrollTop || 0;

			const activeModule = this.getMenuModuleKey();
			const modules = this.getTabModules();
			const pathname = decodeURIComponent((window.location.pathname || "").replace(/\/$/, ""));
			const routeStr = this.getRouteStrSafe();

			const groups = [];
			let activeKey = "";
			let matchedLength = 0;

			const markActive = (key, path) => {
				const href = decodeURIComponent((path || "").split("?")[0].split("#")[0].replace(/\/$/, ""));
				const candidates = [href, href.replace(/^\/(desk|app)/, "")].filter(Boolean);
				for (const candidate of candidates) {
					const clean = candidate.replace(/\/$/, "");
					if (!clean || clean === "#") continue;
					const pathMatch =
						pathname === clean ||
						pathname.endsWith(clean) ||
						pathname.startsWith(clean + "/") ||
						pathname.endsWith("/" + clean.replace(/^\//, ""));
					const routeMatch =
						routeStr &&
						(routeStr === clean.replace(/^\//, "") ||
							routeStr.startsWith(clean.replace(/^\//, "") + "/") ||
							("List/" + clean.replace(/^\//, "") === routeStr) ||
							routeStr.endsWith("/" + clean.replace(/^\//, "")));
					const score = clean.length;
					if ((pathMatch || routeMatch) && score >= matchedLength) {
						activeKey = key;
						matchedLength = score;
					}
				}
			};

			modules.forEach((mod) => {
				const sidebarData = frappe.boot.module_sidebars?.[mod.key];
				const items = [];

				if (sidebarData?.items?.length) {
					const built = this.buildGroups(sidebarData.items, mod.key);
					built.forEach((group) => {
						(group.items || []).forEach((item) => {
							const path = frappe.ui.sidebar_item.get_route(item) || "#";
							const key = `${mod.key}::${path}::${item.label}`;
							items.push({
								key,
								label: translateSidebarLabel(item.label),
								path,
								module: mod.key,
								link_type: item.link_type,
								link_to: item.link_to,
								openInNewTab: item.link_type === "URL" && item.open_in_new_tab,
							});
							markActive(key, path);
							if (item.link_type === "DocType" && item.link_to) {
								markActive(key, `/app/List/${item.link_to}`);
								markActive(key, `/app/${item.link_to}`);
							}
						});
					});
				} else if (SYNTHETIC_MODULES[mod.key]) {
					SYNTHETIC_MODULES[mod.key].items.forEach((item) => {
						const path = item.path || "#";
						const key = `${mod.key}::${path}::${item.label}`;
						items.push({
							key,
							label: item.label,
							path,
							module: mod.key,
							link_type: item.link_type || "Page",
							link_to: item.link_to,
							openInNewTab: false,
						});
						markActive(key, path);
					});
				}

				if (!items.length) return;

				groups.push({
					key: `mod:${mod.key}`,
					label: mod.label,
					collapsible: true,
					// Hint only — Vue keeps user-expanded keys to avoid collapse jump.
					open: mod.key === activeModule || (!activeModule && mod.key === modules[0]?.key),
					items,
				});
			});

			window.OrgUI.updateSidebar({
				title: this.getWorkspaceTitle(),
				tabs: [],
				activeTab: "",
				activeKey,
				groups,
				workspaces: this.getDockEntries().map((entry) => ({
					key: entry.module || entry.route,
					label: MODULE_TAB_LABELS[entry.module] || translateSidebarLabel(entry.title || entry.module),
					module: entry.module,
					route: entry.route,
				})),
				searchShortcut: /Mac|iPhone|iPad|iPod/i.test(navigator.platform || "") ? "⌘K" : "Ctrl+K",
				compact: this.compact,
			});

			requestAnimationFrame(() => {
				const el = document.querySelector(".arco-hr-menu-wrap .arco-menu, .arco-hr-sidebar .arco-menu");
				if (el) el.scrollTop = scrollTop;
			});
		},

		toggleCompact() {
			if (frappe.is_mobile()) {
				frappe.app?.sidebar?.close?.();
				return;
			}
			this.compact = !this.compact;
			document.body.classList.toggle("hr-sidebar-compact", this.compact);
			window.localStorage.setItem("hr_sidebar_compact", this.compact ? "1" : "0");
			this.pushArcoState();
		},

		hideStandardChrome() {
			const sidebar = document.querySelector(".body-sidebar");
			if (!sidebar) return;

			sidebar.classList.add("hr-unified-host");
			sidebar.querySelector(".sidebar-header")?.classList.add("hr-unified-hidden");
			sidebar.querySelector(".standard-items-band")?.classList.add("hr-unified-hidden");
			sidebar.querySelector(".sidebar-items")?.classList.add("hr-unified-hidden");
			sidebar.querySelector(".body-sidebar-cards")?.classList.add("hr-unified-hidden");
			sidebar.querySelector(".promotional-banners")?.classList.add("hr-unified-hidden");
		},

		restoreStandardChrome() {
			const sidebar = document.querySelector(".body-sidebar");
			if (!sidebar) return;

			sidebar.classList.remove("hr-unified-host");
			sidebar.querySelectorAll(".hr-unified-hidden").forEach((el) => {
				el.classList.remove("hr-unified-hidden");
			});
		},

		getWorkspaceTitle() {
			const sidebar = frappe.app?.sidebar;
			const current = sidebar?.current_module;
			if (current && MODULE_TAB_LABELS[current]) {
				return MODULE_TAB_LABELS[current];
			}
			const data = current ? frappe.boot.module_sidebars?.[current] : null;
			return MODULE_TAB_LABELS[current] || translateSidebarLabel(data?.title || data?.name || "HR Setup");
		},

		getDockEntries() {
			const sidebar = frappe.app?.sidebar;
			const app = this.getHrmsApp();
			if (!sidebar || !app) return [];
			return sidebar.collect_dock_entries(app) || [];
		},

		getTabModules() {
			const entries = this.getDockEntries();
			const modules = [];
			const seen = new Set();

			const pushModule = (key, label) => {
				if (!key || seen.has(key)) return;
				const hasSidebar = !!frappe.boot.module_sidebars?.[key]?.items?.length;
				const synthetic = !!SYNTHETIC_MODULES[key];
				if (!hasSidebar && !synthetic) return;
				seen.add(key);
				modules.push({
					key,
					label: MODULE_TAB_LABELS[key] || label || __(key),
					synthetic: !hasSidebar && synthetic,
				});
			};

			for (const entry of entries) {
				pushModule(entry.module, MODULE_TAB_LABELS[entry.module] || translateSidebarLabel(entry.title || entry.module));
			}

			// Ensure preferred modules (incl. 审批 / 合同) always appear when available.
			for (const key of MODULE_ORDER) {
				pushModule(key, MODULE_TAB_LABELS[key]);
			}

			if (!modules.length) {
				return FALLBACK_TAB_MODULES;
			}

			const ordered = [];
			const used = new Set();
			for (const key of MODULE_ORDER) {
				const hit = modules.find((m) => m.key === key);
				if (!hit) continue;
				ordered.push(hit);
				used.add(key);
			}
			for (const mod of modules) {
				if (!used.has(mod.key)) ordered.push(mod);
			}
			return ordered;
		},

		getTabModuleKeys() {
			return this.getTabModules().map((item) => item.key);
		},

		renderHeader() {
			if (!this.$root) return;

			const title = this.getWorkspaceTitle();
			const icon = frappe.boot.module_sidebars?.[frappe.app.sidebar.current_module]?.header_icon || "briefcase-business";
			const shortcut =
				/Mac|iPhone|iPad|iPod/i.test(navigator.platform || "") ? "⌘K" : "Ctrl+K";

			let header = this.$root.find(".hr-unified-header");
			if (!header.length) {
				header = $(`
					<div class="hr-unified-header">
						<div class="hr-unified-header-row">
							<button type="button" class="hr-unified-workspace-btn">
								<span class="hr-unified-workspace-icon"></span>
								<span class="hr-unified-workspace-title"></span>
								<span class="hr-unified-workspace-chevron">${frappe.utils.icon("chevron-down", "xs")}</span>
							</button>
							<button type="button" class="hr-unified-collapse-btn" aria-label="${__("收起侧边栏")}" title="${__("收起侧边栏")}">
								${frappe.utils.icon("chevron-left", "sm")}
							</button>
						</div>
						<div class="hr-unified-search">
							<span class="hr-unified-search-icon">${frappe.utils.icon("search", "sm")}</span>
							<input type="text" class="hr-unified-search-input navbar-modal-search-mobile" readonly placeholder="${__("搜索功能")}" aria-label="${__("搜索功能")}">
							<span class="hr-unified-search-kbd">${shortcut}</span>
						</div>
					</div>
				`);
				this.$root.prepend(header);

				header.find(".hr-unified-workspace-btn").on("click", (event) => {
					event.preventDefault();
					event.stopPropagation();
					this.openWorkspaceMenu(event.currentTarget);
				});

				header.find(".hr-unified-collapse-btn").on("click", (event) => {
					event.preventDefault();
					event.stopPropagation();
					frappe.app?.sidebar?.close?.();
				});

				header.find(".hr-unified-search-input").on("click", (event) => {
					event.preventDefault();
					$(".navbar-modal-search-mobile").first().trigger("click");
				});
			}

			header.find(".hr-unified-workspace-icon").html(
				frappe.utils.icon(icon, "sm", "", "", "text-blue-600", true)
			);
			header.find(".hr-unified-workspace-title").text(title);
		},

		openWorkspaceMenu(anchor) {
			const entries = this.getDockEntries();
			if (!entries.length) return;

			const items = entries.map((entry) => ({
				label: MODULE_TAB_LABELS[entry.module] || translateSidebarLabel(entry.title || entry.module),
				onClick: () => {
					if (entry.module) {
						frappe.app.sidebar.open_module(entry.module);
					} else if (entry.route) {
						frappe.set_route(entry.route);
					}
				},
			}));

			frappe.ui.menu({
				parent: anchor,
				menu_items: items,
			});
		},

		getMenuModuleKey() {
			const tabKeys = this.getTabModuleKeys();

			// Prefer route inference so stale Frappe current_module (e.g. HR Setup)
			// does not keep reopening 人事 after navigating into 审批 / other modules.
			const inferred = this.inferModuleFromRoute();
			if (inferred && tabKeys.includes(inferred)) {
				this.menuModule = inferred;
				return inferred;
			}

			if (this.menuModule && tabKeys.includes(this.menuModule)) {
				return this.menuModule;
			}

			const current = frappe.app?.sidebar?.current_module;
			if (current && tabKeys.includes(current)) {
				this.menuModule = current;
				return current;
			}

			return null;
		},

		inferModuleFromRoute() {
			const route = this.getRouteStrSafe();
			const pathname = (window.location.pathname || "").replace(/\/$/, "");

			if (currentHrSetupRoute(route, pathname)) {
				return "HR Setup";
			}

			for (const tab of this.getTabModules()) {
				const items = frappe.boot.module_sidebars?.[tab.key]?.items || [];
				for (const item of items) {
					if (item.type !== "Link") continue;
					const path = frappe.ui.sidebar_item.get_route(item);
					if (!path || path.startsWith("http")) continue;
					const clean = decodeURIComponent(path.split("?")[0].split("#")[0]).replace(/\/$/, "");
					if (
						clean &&
						(pathname === clean ||
							pathname.startsWith(clean + "/") ||
							route.startsWith(item.link_to))
					) {
						return tab.key;
					}
				}
			}

			return null;
		},

		renderTabs() {
			if (!this.$root) return;

			const activeModule = this.getMenuModuleKey();
			let tabs = this.$root.find(".hr-unified-tabs");
			if (!tabs.length) {
				tabs = $('<div class="hr-unified-tabs"></div>');
				this.$root.find(".hr-unified-header").after(tabs);

				tabs.on("click", ".hr-unified-tab", (event) => {
					const moduleKey = event.currentTarget.dataset.module;
					if (!moduleKey) return;
					this.menuModule = moduleKey;
					this.renderTabs();
					this.renderMenu();

					if (frappe.app?.sidebar?.current_module !== moduleKey) {
						frappe.app.sidebar.open_module(moduleKey);
					}
				});
			}

			tabs.empty();
			this.getTabModules().forEach((tab) => {
				const isActive = tab.key === activeModule;
				tabs.append(
					`<button type="button" class="hr-unified-tab${isActive ? " is-active" : ""}" data-module="${frappe.utils.escape_html(tab.key)}" title="${frappe.utils.escape_html(tab.label)}">${tab.label}</button>`
				);
			});
		},

		renderMenu() {
			if (!this.$root) return;

			const tabKeys = this.getTabModuleKeys();
			let moduleKey = this.getMenuModuleKey();

			if (!moduleKey) {
				const current = frappe.app?.sidebar?.current_module;
				moduleKey =
					(current && tabKeys.includes(current) && current) ||
					this.getTabModules()[0]?.key ||
					"HR Setup";
			}

			const sidebarData = frappe.boot.module_sidebars?.[moduleKey];
			let menu = this.$root.find(".hr-unified-menu");
			if (!menu.length) {
				menu = $('<nav class="hr-unified-menu" aria-label="HR navigation"></nav>');
				this.$root.find(".hr-unified-tabs").after(menu);
			}

			if (!sidebarData?.items?.length) {
				menu.html(`<div class="hr-unified-empty">${__("暂无菜单项")}</div>`);
				return;
			}

			const groups = this.buildGroups(sidebarData.items, moduleKey);
			menu.empty();

			groups.forEach((group, index) => {
				if (index > 0) {
					menu.append('<div class="hr-unified-divider"></div>');
				}

				const groupEl = $(`
					<section class="hr-unified-group${group.collapsible ? " is-collapsible" : ""}${group.open ? " is-open" : ""}">
						<div class="hr-unified-group-head">
							<span class="hr-unified-group-title">${frappe.utils.escape_html(group.label)}</span>
							${group.collapsible ? `<span class="hr-unified-group-arrow">${frappe.utils.icon("chevron-right", "xs")}</span>` : ""}
						</div>
						<div class="hr-unified-group-body"></div>
					</section>
				`);

				const body = groupEl.find(".hr-unified-group-body");
				group.items.forEach((item) => {
					body.append(this.renderMenuItem(item));
				});

				if (group.collapsible) {
					groupEl.find(".hr-unified-group-head").on("click", () => {
						groupEl.toggleClass("is-open");
					});
				}

				menu.append(groupEl);
			});

			this.markActiveItem(menu);
		},

		buildGroups(items, moduleKey) {
			const prepared = this.prepareItems(items);
			const groups = [];
			let current = null;
			let sectionChildMode = false;

			const pushCurrent = () => {
				if (current?.items?.length) {
					groups.push(current);
				}
				current = null;
				sectionChildMode = false;
			};

			const ensureGroup = (label, collapsible = false, open = true) => {
				if (!current || current.label !== label) {
					pushCurrent();
					current = { label, items: [], collapsible, open };
				}
			};

			for (const item of prepared) {
				if (item.type === "Section Break") {
					pushCurrent();
					current = {
						label: this.translateSectionLabel(item.label),
						items: [],
						collapsible: !!item.keep_closed,
						open: !item.keep_closed,
					};
					sectionChildMode = true;
					continue;
				}

				if (item.type !== "Link" || item.hidden) continue;
				if (SKIP_LINK_LABELS.has(item.label)) continue;

				if (item.child && current && sectionChildMode) {
					current.items.push(item);
					continue;
				}

				if (!current) {
					current = {
						label: MODULE_FLOW_LABELS[moduleKey] || __("业务主功能"),
						items: [],
						collapsible: false,
						open: true,
					};
				} else if (sectionChildMode) {
					pushCurrent();
					current = {
						label: MODULE_FLOW_LABELS[moduleKey] || __("业务主功能"),
						items: [],
						collapsible: false,
						open: true,
					};
					sectionChildMode = false;
				}

				current.items.push(item);
			}

			pushCurrent();
			return groups;
		},

		prepareItems(items) {
			const cloned = (items || []).map((item) => ({ ...item, nested_items: [] }));
			let currentSection = null;

			cloned.forEach((item) => {
				if (item.type === "Section Break") {
					currentSection = item;
				} else if (currentSection && item.child) {
					item.parent = currentSection;
					currentSection.nested_items.push(item);
				}
			});

			return cloned;
		},

		translateSectionLabel(label) {
			return translateSidebarLabel(label);
		},

		renderMenuItem(item) {
			const path = frappe.ui.sidebar_item.get_route(item) || "#";
			const icon = item.icon || "list";
			const hasArrow = !!item.show_arrow;
			const target =
				item.link_type === "URL" && item.open_in_new_tab ? ' target="_blank" rel="noopener"' : "";
			const label = translateSidebarLabel(item.label);

			return $(`
				<a href="${path}" class="hr-unified-item" data-label="${frappe.utils.escape_html(label)}"${target}>
					<span class="hr-unified-item-icon">${frappe.utils.icon(icon, "sm", "", "", "", true)}</span>
					<span class="hr-unified-item-label">${frappe.utils.escape_html(label)}</span>
					${hasArrow ? `<span class="hr-unified-item-arrow">${frappe.utils.icon("chevron-right", "xs")}</span>` : ""}
				</a>
			`).on("click", () => {
				if (frappe.is_mobile()) {
					frappe.app.sidebar.close();
				}
			});
		},

		markActiveItem(menu) {
			const pathname = decodeURIComponent(window.location.pathname.replace(/\/$/, ""));
			let matched = null;
			let matchedLength = 0;

			menu.find(".hr-unified-item").each((_idx, el) => {
				const href = decodeURIComponent((el.getAttribute("href") || "").split("?")[0].split("#")[0].replace(/\/$/, ""));
				if (!href || href === "#") return;
				const isActive = pathname === href || pathname.startsWith(href + "/");
				if (isActive && href.length >= matchedLength) {
					matched = el;
					matchedLength = href.length;
				}
			});

			menu.find(".hr-unified-item.is-active").removeClass("is-active");
			if (matched) {
				$(matched).addClass("is-active");
				$(matched).closest(".hr-unified-group.is-collapsible").addClass("is-open");
			}
		},

		getUserRoleLabel() {
			if (frappe.user.has_role("System Manager")) return __("管理员");
			if (frappe.user.has_role("HR Manager")) return __("HR 经理");
			if (frappe.user.has_role("HR User")) return __("HR 用户");
			const roles = frappe.user_roles || [];
			return roles.length ? __(roles[0]) : __("用户");
		},

		ensureCollapseControls() {
			document.querySelector(".hr-unified-expand-btn")?.remove();
		},

		syncCollapseControls() {
			document.querySelector(".hr-unified-expand-btn")?.remove();
		},

		enhanceUserFooter() {
			const bottom = document.querySelector(".body-sidebar-bottom");
			if (!bottom) return;

			bottom.classList.add("hr-unified-footer");
			const emailEl = bottom.querySelector(".avatar-name-email span.text-secondary");
			if (emailEl) {
				emailEl.textContent = this.getUserRoleLabel();
				emailEl.classList.add("hr-unified-user-role");
			}

			let moreBtn = bottom.querySelector(".hr-unified-user-more");
			if (!moreBtn) {
				moreBtn = document.createElement("button");
				moreBtn.type = "button";
				moreBtn.className = "hr-unified-user-more btn-reset";
				moreBtn.setAttribute("aria-label", __("更多操作"));
				moreBtn.innerHTML = frappe.utils.icon("ellipsis", "sm");
				bottom.querySelector(".sidebar-user-button")?.appendChild(moreBtn);

				moreBtn.addEventListener("click", (event) => {
					event.preventDefault();
					event.stopPropagation();
					bottom.querySelector(".sidebar-user-button")?.click();
				});
			}
		},
	};

	function currentHrSetupRoute(route, pathname) {
		const hrSetupRoutes = ["roster", "orgchart", "org-diagram", "employee-archive"];
		return hrSetupRoutes.some((name) => route.startsWith(name) || pathname.includes(name));
	}

	employee_roster.unified_sidebar = controller;

	$(document).ready(() => controller.init());
})();
