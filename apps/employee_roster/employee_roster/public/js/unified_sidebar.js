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
	const BODY_CLASS = "hr-unified-sidebar-active";

	const MODULE_TAB_LABELS = {
		"HR Setup": __("人事"),
		Tenure: __("在职"),
		Recruitment: __("招聘"),
		"Shift & Attendance": __("考勤"),
		Leaves: __("假期"),
		Expenses: __("费用"),
		Performance: __("绩效"),
		Payroll: __("薪酬"),
		"Tax & Benefits": __("个税"),
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
	]);

	const SKIP_LINK_LABELS = new Set(["Home", "Dashboard"]);

	const SECTION_LABEL_MAP = {
		Reports: __("报表"),
		Setup: __("设置"),
		Planning: __("计划"),
		Overtime: __("日常操作"),
	};

	const MODULE_FLOW_LABELS = {
		"HR Setup": __("业务主功能"),
		Tenure: __("业务主功能"),
		Recruitment: __("招聘流程"),
		"Shift & Attendance": __("日常操作"),
		Leaves: __("业务主功能"),
		Expenses: __("业务主功能"),
		Performance: __("业务主功能"),
		Payroll: __("业务主功能"),
		"Tax & Benefits": __("业务主功能"),
	};

	const controller = {
		initialized: false,
		menuModule: null,
		$root: null,
		vueApp: null,

		init() {
			if (this.initialized || !frappe.boot.setup_complete) return;
			this.initialized = true;

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

				// Never call frappe.get_route_str() — it does current_route.join
				// and throws when current_route is still null during boot.
				const route = this.getRouteStrSafe();
				if (!route) return false;

				const hrPrefixes = [
					"List/Employee",
					"Form/Employee",
					"recruiting-",
					"org-diagram",
					"orgchart",
					"roster",
					"employee-archive",
					"attendance-rules",
				];
				return hrPrefixes.some((prefix) => route.startsWith(prefix));
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
					this.deactivate();
					return;
				}

				document.body.classList.add(BODY_CLASS);
				this.ensureRoot();
				this.hideStandardChrome();
				if (window.OrgUI?.mountSidebar) {
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
			try {
				this.vueApp?.unmount?.();
			} catch (e) {
				/* ignore */
			}
			this.vueApp = null;
			this.$root?.remove();
			this.$root = null;
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

		mountArcoSidebar() {
			const root = document.getElementById(ROOT_ID);
			if (!root || this.vueApp) return;
			root.classList.add("arco-hr-sidebar-host");
			this.vueApp = window.OrgUI.mountSidebar(root, {
				onWorkspace: (ws) => {
					if (ws?.module) {
						frappe.app.sidebar.open_module(ws.module);
					} else if (ws?.route) {
						frappe.set_route(ws.route);
					}
				},
				onCollapse: () => frappe.app?.sidebar?.close?.(),
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
					if (frappe.is_mobile()) {
						frappe.app.sidebar.close();
					}
					const path = item?.path || "#";
					if (!path || path === "#") return;
					if (path.startsWith("http")) {
						window.location.href = path;
						return;
					}
					const url = new URL(path, window.location.origin);
					const hash = (url.hash || "").replace(/^#\/?/, "");
					const clean = decodeURIComponent(url.pathname.replace(/^\/(desk|app)\/?/, "")).replace(/\/$/, "");
					const route = hash || clean;
					if (route) frappe.set_route(route.split("/").filter(Boolean));
				},
			});
		},

		pushArcoState() {
			if (!window.OrgUI?.updateSidebar) return;

			const moduleKey = this.getMenuModuleKey();
			const sidebarData = frappe.boot.module_sidebars?.[moduleKey];
			const groups = sidebarData?.items?.length
				? this.buildGroups(sidebarData.items, moduleKey).map((group) => ({
						label: group.label,
						collapsible: !!group.collapsible,
						open: group.open !== false,
						items: group.items.map((item) => ({
							key: `${frappe.ui.sidebar_item.get_route(item) || "#"}::${item.label}`,
							label: __(item.label),
							path: frappe.ui.sidebar_item.get_route(item) || "#",
							iconHtml: frappe.utils.icon(item.icon || "list", "sm", "", "", "", true),
							openInNewTab: item.link_type === "URL" && item.open_in_new_tab,
						})),
					}))
				: [];

			const pathname = decodeURIComponent((window.location.pathname || "").replace(/\/$/, ""));
			let activeKey = "";
			let matchedLength = 0;
			groups.forEach((group) => {
				group.items.forEach((item) => {
					const href = decodeURIComponent((item.path || "").split("?")[0].split("#")[0].replace(/\/$/, ""));
					if (!href || href === "#") return;
					if ((pathname === href || pathname.startsWith(href + "/")) && href.length >= matchedLength) {
						activeKey = item.key;
						matchedLength = href.length;
					}
				});
			});

			window.OrgUI.updateSidebar({
				title: MODULE_TAB_LABELS[moduleKey] || this.getWorkspaceTitle(),
				tabs: this.getTabModules(),
				activeTab: moduleKey || this.getTabModules()[0]?.key || "",
				activeKey,
				groups,
				workspaces: this.getDockEntries().map((entry) => ({
					key: entry.module || entry.route,
					label: __(entry.title || entry.module),
					module: entry.module,
					route: entry.route,
				})),
				searchShortcut: /Mac|iPhone|iPad|iPod/i.test(navigator.platform || "") ? "⌘K" : "Ctrl+K",
			});
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
			const data = current ? frappe.boot.module_sidebars?.[current] : null;
			return __(data?.title || data?.name || "HR Setup");
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

			for (const entry of entries) {
				const key = entry.module;
				if (!key || seen.has(key)) continue;
				if (!frappe.boot.module_sidebars?.[key]?.items?.length) continue;
				seen.add(key);
				modules.push({
					key,
					label: MODULE_TAB_LABELS[key] || __(entry.title || key),
				});
			}

			return modules.length ? modules : FALLBACK_TAB_MODULES;
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
				frappe.utils.icon(icon, "sm", "", "", "text-green-600", true)
			);
			header.find(".hr-unified-workspace-title").text(title);
		},

		openWorkspaceMenu(anchor) {
			const entries = this.getDockEntries();
			if (!entries.length) return;

			const items = entries.map((entry) => ({
				label: __(entry.title || entry.module),
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
			const current = frappe.app?.sidebar?.current_module;

			if (current && tabKeys.includes(current)) {
				this.menuModule = current;
				return current;
			}

			if (this.menuModule && tabKeys.includes(this.menuModule)) {
				return this.menuModule;
			}

			const inferred = this.inferModuleFromRoute();
			if (inferred && tabKeys.includes(inferred)) {
				return inferred;
			}

			return current && tabKeys.includes(current) ? current : null;
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
			return SECTION_LABEL_MAP[label] || __(label);
		},

		renderMenuItem(item) {
			const path = frappe.ui.sidebar_item.get_route(item) || "#";
			const icon = item.icon || "list";
			const hasArrow = !!item.show_arrow;
			const target =
				item.link_type === "URL" && item.open_in_new_tab ? ' target="_blank" rel="noopener"' : "";

			return $(`
				<a href="${path}" class="hr-unified-item" data-label="${frappe.utils.escape_html(item.label)}"${target}>
					<span class="hr-unified-item-icon">${frappe.utils.icon(icon, "sm", "", "", "", true)}</span>
					<span class="hr-unified-item-label">${__(item.label)}</span>
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
			let btn = document.querySelector(".hr-unified-expand-btn");
			if (!btn) {
				btn = document.createElement("button");
				btn.type = "button";
				btn.className = "hr-unified-expand-btn";
				btn.setAttribute("aria-label", __("展开侧边栏"));
				btn.title = __("展开侧边栏");
				btn.innerHTML = frappe.utils.icon("chevron-right", "sm");
				btn.addEventListener("click", (event) => {
					event.preventDefault();
					event.stopPropagation();
					frappe.app?.sidebar?.open?.();
				});
				document.body.appendChild(btn);
			}
			this.syncCollapseControls();
		},

		syncCollapseControls() {
			const collapsed = document.body.classList.contains("sidebar-collapsed");
			const btn = document.querySelector(".hr-unified-expand-btn");
			if (btn) {
				btn.hidden = !document.body.classList.contains(BODY_CLASS) || !collapsed;
			}
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
