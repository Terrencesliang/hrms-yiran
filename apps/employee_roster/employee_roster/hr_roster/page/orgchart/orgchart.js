// Copyright (c) 2026 stillgroup
// License: MIT

const ORG_API = "employee_roster.hr_roster.page.orgchart.orgchart";
const COL_STORAGE_KEY = "orgchart-hidden-cols";
const COLUMNS = [
	{ key: "type", label: "组织类型" },
	{ key: "emp", label: "员工数" },
	{ key: "quota", label: "人员编制" },
	{ key: "vacancy", label: "缺编/超编" },
	{ key: "head", label: "负责人" },
	{ key: "supervisor", label: "分管领导" },
];

const ICONS = {
	search: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3-3"/></svg>`,
	filter: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 5h16l-6 7.5V19l-4 2v-8.5L4 5z"/></svg>`,
	caret: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>`,
	close: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>`,
	edit: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 16l.8-3.2L15.5 6l2.5 2.5-6.7 6.7L8 16z"/></svg>`,
	calendar: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3v4M16 3v4M4 10h16"/></svg>`,
	picker: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3-3"/></svg>`,
	expand: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M7 10l5 5 5-5"/></svg>`,
};

function ensure_orgchart_styles() {
	if (document.querySelector("link[data-orgchart-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.href = `/assets/employee_roster/css/orgchart.css?v=${Date.now()}`;
	link.setAttribute("data-orgchart-css", "1");
	document.head.appendChild(link);
}

frappe.pages["orgchart"].on_page_load = function (wrapper) {
	ensure_orgchart_styles();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("组织架构"),
		single_column: true,
	});

	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();
	$main.addClass("orgchart-page");
	$main.html(page_markup());

	const state = create_state($main);
	bind_toolbar(state);
	bind_tree(state);
	load_tree(state);
};

frappe.pages["orgchart"].on_page_leave = function () {
	$(document).off(".orgchart");
	close_drawer();
	close_popovers();
};

function create_state($main) {
	return {
		$main,
		data: null,
		company: null,
		keyword: "",
		collapsed: new Set(),
		hiddenCols: load_hidden_cols(),
		filters: { org_type: "", quota: "", vacancy: "" },
		flat: [],
		searchTimer: null,
	};
}

function page_markup() {
	return `
		<div class="oc-shell">
			<div class="oc-toolbar">
				<div class="oc-toolbar-left">
					<div class="oc-company-wrap">
						<button type="button" class="oc-company-switch" aria-haspopup="listbox" aria-label="${__("切换公司")}">
							<span class="oc-company-switch-name"></span>
							${ICONS.caret}
						</button>
						<div class="oc-menu oc-company-menu" role="listbox"></div>
					</div>
					<div class="oc-search-box">
						<input type="search" class="oc-search-input" placeholder="${__("组织名称/组织代码")}" aria-label="${__("搜索组织")}">
						<span class="oc-search-icon">${ICONS.search}</span>
					</div>
					<div class="oc-filter-wrap">
						<button type="button" class="oc-icon-btn oc-filter-btn" aria-label="${__("筛选")}">${ICONS.filter}</button>
						<div class="oc-popover oc-filter-popover">
							<div class="oc-popover-title">${__("筛选")}</div>
							<label class="oc-filter-field">
								<span>${__("组织类型")}</span>
								<select class="oc-filter-type">
									<option value="">${__("全部")}</option>
									<option value="公司">${__("公司")}</option>
									<option value="部门">${__("部门")}</option>
									<option value="组">${__("组")}</option>
								</select>
							</label>
							<label class="oc-filter-field">
								<span>${__("人员编制")}</span>
								<select class="oc-filter-quota">
									<option value="">${__("全部")}</option>
									<option value="set">${__("已设置")}</option>
									<option value="unset">${__("未设置")}</option>
								</select>
							</label>
							<label class="oc-filter-field">
								<span>${__("缺编/超编")}</span>
								<select class="oc-filter-vacancy">
									<option value="">${__("全部")}</option>
									<option value="short">${__("缺编")}</option>
									<option value="over">${__("超编")}</option>
									<option value="full">${__("满编")}</option>
								</select>
							</label>
							<div class="oc-popover-actions">
								<button type="button" class="oc-btn oc-btn-ghost oc-filter-reset">${__("重置")}</button>
								<button type="button" class="oc-btn oc-btn-primary oc-filter-apply">${__("确定")}</button>
							</div>
						</div>
					</div>
				</div>
				<div class="oc-toolbar-right">
					<button type="button" class="oc-btn oc-btn-primary oc-add-btn">${__("新增组织")}</button>
					<button type="button" class="oc-btn oc-btn-outline oc-batch-btn">${__("批量新增/更新")}</button>
					<div class="oc-menu-wrap">
						<button type="button" class="oc-btn oc-btn-outline oc-cols-btn">${__("显示筛选")} ${ICONS.caret}</button>
						<div class="oc-menu oc-cols-menu"></div>
					</div>
					<div class="oc-menu-wrap">
						<button type="button" class="oc-btn oc-btn-outline oc-more-btn">${__("更多功能")} ${ICONS.caret}</button>
						<div class="oc-menu oc-more-menu">
							<button type="button" class="oc-menu-item" data-action="expand">${__("展开全部")}</button>
							<button type="button" class="oc-menu-item" data-action="collapse">${__("全部收起")}</button>
							<button type="button" class="oc-menu-item" data-action="export">${__("导出组织")}</button>
							<button type="button" class="oc-menu-item" data-action="refresh">${__("刷新")}</button>
						</div>
					</div>
				</div>
			</div>
			<div class="oc-table">
				<div class="orgchart-table-head"></div>
				<div class="orgchart-table-body"></div>
			</div>
		</div>
	`;
}

function bind_toolbar(state) {
	const $main = state.$main;

	$main.find(".oc-search-input").on("input", function () {
		clearTimeout(state.searchTimer);
		state.searchTimer = setTimeout(() => {
			state.keyword = String(this.value || "").trim();
			rebuild_tree(state);
		}, 180);
	});

	$main.find(".oc-add-btn").on("click", () => open_org_drawer(state));
	$main.find(".oc-batch-btn").on("click", () => open_batch_dialog(state));
	$main.find(".oc-company-switch").on("click", (e) => {
		e.stopPropagation();
		toggle_menu($main.find(".oc-company-menu"));
	});
	$main.find(".oc-cols-btn").on("click", (e) => {
		e.stopPropagation();
		render_cols_menu(state);
		toggle_menu($main.find(".oc-cols-menu"));
	});
	$main.find(".oc-more-btn").on("click", (e) => {
		e.stopPropagation();
		toggle_menu($main.find(".oc-more-menu"));
	});
	$main.find(".oc-filter-btn").on("click", (e) => {
		e.stopPropagation();
		close_popovers($main.find(".oc-filter-popover")[0]);
		$main.find(".oc-filter-popover").toggleClass("open");
	});

	$main.find(".oc-filter-apply").on("click", () => {
		state.filters.org_type = $main.find(".oc-filter-type").val() || "";
		state.filters.quota = $main.find(".oc-filter-quota").val() || "";
		state.filters.vacancy = $main.find(".oc-filter-vacancy").val() || "";
		$main.find(".oc-filter-btn").toggleClass("has-filter", has_filters(state));
		$main.find(".oc-filter-popover").removeClass("open");
		rebuild_tree(state);
	});
	$main.find(".oc-filter-reset").on("click", () => {
		state.filters = { org_type: "", quota: "", vacancy: "" };
		$main.find(".oc-filter-type, .oc-filter-quota, .oc-filter-vacancy").val("");
		$main.find(".oc-filter-btn").removeClass("has-filter");
		rebuild_tree(state);
	});

	$main.find(".oc-more-menu").on("click", ".oc-menu-item", function () {
		const action = this.getAttribute("data-action");
		close_popovers();
		if (action === "expand") {
			state.collapsed.clear();
			rebuild_tree(state);
		} else if (action === "collapse") {
			collapse_all(state);
			rebuild_tree(state);
		} else if (action === "export") {
			export_tree(state);
		} else if (action === "refresh") {
			load_tree(state);
		}
	});

	$main.find(".oc-company-menu").on("click", ".oc-menu-item", function () {
		const company = this.getAttribute("data-company");
		close_popovers();
		if (company && company !== state.company) {
			state.company = company;
			load_tree(state);
		}
	});

	$main.find(".oc-cols-menu").on("change", "input[type=checkbox]", function () {
		const key = this.getAttribute("data-col");
		if (this.checked) state.hiddenCols.delete(key);
		else state.hiddenCols.add(key);
		save_hidden_cols(state.hiddenCols);
		rebuild_tree(state);
	});

	$main.find(".oc-filter-popover, .oc-menu").on("click", (e) => e.stopPropagation());
	$(document).on("click.orgchart", () => close_popovers());
	$(document).on("keydown.orgchart", (e) => {
		if (e.key === "Escape") {
			close_drawer();
			close_popovers();
		}
	});
}

function bind_tree(state) {
	const $body = state.$main.find(".orgchart-table-body");

	$body.on("click", ".oc-arrow[data-toggle]", function (e) {
		e.stopPropagation();
		const name = $(this).closest(".orgchart-row").attr("data-name");
		if (!name) return;
		if (state.collapsed.has(name)) state.collapsed.delete(name);
		else state.collapsed.add(name);
		rebuild_tree(state);
	});

	$body.on("click", ".oc-add-child", function (e) {
		e.stopPropagation();
		const $row = $(this).closest(".orgchart-row");
		open_org_drawer(state, {
			parent: $row.attr("data-name"),
			parentTitle: $row.attr("data-title"),
		});
	});

	$body.on("click", ".oc-collapse-all", function (e) {
		e.stopPropagation();
		collapse_all(state);
		rebuild_tree(state);
	});

	$body.on("click", ".oc-edit-person", function (e) {
		e.stopPropagation();
		open_person_popover(state, this);
	});
}

function load_tree(state) {
	const $body = state.$main.find(".orgchart-table-body");
	$body.html(`<div class="oc-empty">${__("加载中...")}</div>`);
	frappe.call({
		method: `${ORG_API}.get_org_tree`,
		args: { company: state.company || undefined },
		callback(r) {
			if (!r.message) return;
			state.data = r.message;
			state.company = r.message.company;
			render_company_switch(state);
			rebuild_tree(state);
		},
		error(err) {
			$body.html(`<div class="oc-empty oc-error">${__("加载组织架构失败：")}${esc((err && err.message) || err)}</div>`);
		},
	});
}

function render_company_switch(state) {
	const companies = state.data.companies || [];
	const current = companies.find((c) => c.name === state.company) || {};
	const label = current.abbr || current.company_name || state.data.company_name || __("公司");
	state.$main.find(".oc-company-switch-name").text(label);
	state.$main.find(".oc-company-menu").html(
		companies
			.map(
				(c) =>
					`<button type="button" class="oc-menu-item ${c.name === state.company ? "is-active" : ""}" data-company="${esc(c.name)}" role="option">${esc(c.company_name || c.name)}</button>`
			)
			.join("") || `<div class="oc-menu-empty">${__("暂无公司")}</div>`
	);
}

function flatten_tree(roots) {
	const flat = [];
	function walk(nodes, depth, parentKey) {
		(nodes || []).forEach((n) => {
			flat.push({ node: n, depth, parentKey });
			if (n.children && n.children.length) walk(n.children, depth + 1, n.name);
		});
	}
	walk(roots, 0, null);
	return flat;
}

function rebuild_tree(state) {
	const roots = (state.data && state.data.roots) || [];
	state.flat = flatten_tree(roots);
	render_header(state);
	render_rows(state);
}

function render_header(state) {
	const cols = [
		`<div class="oc-col oc-col-name">${__("组织名称")}</div>`,
		col_visible(state, "type") ? `<div class="oc-col oc-col-type">${__("组织类型")}</div>` : "",
		col_visible(state, "emp") ? `<div class="oc-col oc-col-emp">${__("员工数")}</div>` : "",
		col_visible(state, "quota") ? `<div class="oc-col oc-col-bianzhi">${__("人员编制")}</div>` : "",
		col_visible(state, "vacancy") ? `<div class="oc-col oc-col-qb">${__("缺编/超编")}</div>` : "",
		col_visible(state, "head") ? `<div class="oc-col oc-col-head">${__("负责人")}</div>` : "",
		col_visible(state, "supervisor") ? `<div class="oc-col oc-col-fg">${__("分管领导")}</div>` : "",
	];
	state.$main.find(".orgchart-table-head").html(cols.join(""));
}

function render_rows(state) {
	const $tbody = state.$main.find(".orgchart-table-body");
	const keyword = state.keyword.toLowerCase();
	const matchSet = new Set();
	if (keyword) {
		state.flat.forEach((it) => {
			const title = String(it.node.title || "").toLowerCase();
			const code = String(it.node.org_code || "").toLowerCase();
			if (title.includes(keyword) || code.includes(keyword)) matchSet.add(it.node.name);
		});
		state.flat.forEach((it) => {
			if (!matchSet.has(it.node.name)) return;
			let cur = it.parentKey;
			let depth = it.depth;
			while (cur != null && depth > 0) {
				matchSet.add(cur);
				const parentEntry = state.flat.find((x) => x.node.name === cur && x.depth === depth - 1);
				cur = parentEntry ? parentEntry.parentKey : null;
				depth--;
			}
		});
	}

	const html = [];
	state.flat.forEach((it) => {
		if (!is_row_visible(state, it, matchSet, keyword)) return;
		html.push(render_row(state, it));
	});
	$tbody.html(html.join("") || `<div class="oc-empty">${__("没有匹配的组织")}</div>`);
}

function is_row_visible(state, it, matchSet, keyword) {
	if (keyword && !matchSet.has(it.node.name)) return false;
	if (!passes_filters(state, it.node)) return false;
	let cur = it.parentKey;
	let depth = it.depth;
	while (cur != null && depth > 0) {
		if (state.collapsed.has(cur)) return false;
		const parentEntry = state.flat.find((x) => x.node.name === cur && x.depth === depth - 1);
		cur = parentEntry ? parentEntry.parentKey : null;
		depth--;
	}
	return true;
}

function passes_filters(state, node) {
	const f = state.filters;
	if (f.org_type && (node.org_type || (node.is_company ? "公司" : "部门")) !== f.org_type) return false;
	const quota = Number(node.staff_quota || 0);
	if (f.quota === "set" && !quota) return false;
	if (f.quota === "unset" && quota) return false;
	const vacancy = vacancy_state(node);
	if (f.vacancy && vacancy !== f.vacancy) return false;
	return true;
}

function vacancy_state(node) {
	const quota = Number(node.staff_quota || 0);
	if (!quota) return "";
	const diff = quota - Number(node.employee_count || 0);
	if (diff > 0) return "short";
	if (diff < 0) return "over";
	return "full";
}

function render_row(state, it) {
	const node = it.node;
	const hasChildren = node.children && node.children.length > 0;
	const isCollapsed = state.collapsed.has(node.name);
	const arrow = hasChildren
		? `<button type="button" class="oc-arrow ${isCollapsed ? "" : "open"}" data-toggle aria-label="${isCollapsed ? __("展开") : __("收起")}">${isCollapsed ? "▸" : "▾"}</button>`
		: `<span class="oc-arrow oc-arrow-empty"></span>`;
	const indent = it.depth * 22;
	const nodeType = node.org_type || (node.is_company ? __("公司") : __("部门"));
	const rowClass = ["orgchart-row", node.is_company ? "is-company" : "", it.depth > 0 ? "is-child" : ""]
		.filter(Boolean)
		.join(" ");
	const actions = node.is_company
		? `<span class="oc-row-actions">
				<button type="button" class="oc-text-link oc-add-child">${__("新增下级")}</button>
				<button type="button" class="oc-text-link oc-collapse-all">${__("全部收起")}</button>
			</span>`
		: `<span class="oc-row-actions oc-row-actions-hover">
				<button type="button" class="oc-text-link oc-add-child">${__("新增下级")}</button>
			</span>`;

	return `
		<div class="${rowClass}" data-name="${esc(node.name)}" data-title="${esc(node.title)}" data-depth="${it.depth}">
			<div class="oc-col oc-col-name" style="padding-left:${indent + 12}px">
				${arrow}
				<span class="oc-node${node.is_company ? " oc-node-company" : ""}">${esc(node.title)}</span>
				${actions}
			</div>
			${col_visible(state, "type") ? `<div class="oc-col oc-col-type">${esc(nodeType)}</div>` : ""}
			${col_visible(state, "emp") ? `<div class="oc-col oc-col-emp">${format_emp(node)}</div>` : ""}
			${col_visible(state, "quota") ? `<div class="oc-col oc-col-bianzhi">${format_quota(node)}</div>` : ""}
			${col_visible(state, "vacancy") ? `<div class="oc-col oc-col-qb">${format_vacancy(node)}</div>` : ""}
			${col_visible(state, "head") ? person_cell(node, "head", node.head_name) : ""}
			${col_visible(state, "supervisor") ? person_cell(node, "supervisor", node.supervisor_name) : ""}
		</div>
	`;
}

function person_cell(node, role, name) {
	const label = name || "";
	return `<div class="oc-col oc-col-${role === "head" ? "head" : "fg"}">
		<span class="oc-person-cell">
			<span class="oc-person-name">${esc(label)}</span>
			<button type="button" class="oc-edit-person" data-role="${role}" data-name="${esc(node.name)}" aria-label="${__("编辑")}">${ICONS.edit}</button>
		</span>
	</div>`;
}

function format_emp(node) {
	const total = Number(node.employee_count || 0);
	const part = Number(node.parttime_count || 0);
	if (part > 0) return `${total}${__("人")}(${part}${__("人非全职")})`;
	return `${total}${__("人")}`;
}

function format_quota(node) {
	const quota = Number(node.staff_quota || 0);
	return quota ? `${quota}` : __("未设置");
}

function format_vacancy(node) {
	const quota = Number(node.staff_quota || 0);
	if (!quota) return "--";
	const diff = quota - Number(node.employee_count || 0);
	if (diff > 0) return `<span class="oc-vacancy is-short">${__("缺编")} ${diff}${__("人")}</span>`;
	if (diff < 0) return `<span class="oc-vacancy is-over">${__("超编")} ${Math.abs(diff)}${__("人")}</span>`;
	return __("满编");
}

function collapse_all(state) {
	state.collapsed.clear();
	state.flat.forEach((it) => {
		if (it.node.children && it.node.children.length) state.collapsed.add(it.node.name);
	});
}

function col_visible(state, key) {
	return !state.hiddenCols.has(key);
}

function render_cols_menu(state) {
	state.$main.find(".oc-cols-menu").html(
		COLUMNS.map(
			(col) => `<label class="oc-menu-check">
				<input type="checkbox" data-col="${col.key}" ${col_visible(state, col.key) ? "checked" : ""}>
				<span>${__(col.label)}</span>
			</label>`
		).join("")
	);
}

function load_hidden_cols() {
	try {
		const raw = JSON.parse(localStorage.getItem(COL_STORAGE_KEY) || "[]");
		return new Set(Array.isArray(raw) ? raw : []);
	} catch (e) {
		return new Set();
	}
}

function save_hidden_cols(set) {
	localStorage.setItem(COL_STORAGE_KEY, JSON.stringify([...set]));
}

function has_filters(state) {
	return !!(state.filters.org_type || state.filters.quota || state.filters.vacancy);
}

function toggle_menu($menu) {
	const el = $menu.get(0);
	const wasOpen = $menu.hasClass("open");
	close_popovers();
	if (!wasOpen && el) $menu.addClass("open");
}

function close_popovers(except) {
	document.querySelectorAll(".oc-menu.open, .oc-popover.open, .oc-person-popover").forEach((el) => {
		if (el !== except) el.classList.remove("open");
		if (el.classList.contains("oc-person-popover") && el !== except) el.remove();
	});
}

function export_tree(state) {
	const rows = [["组织名称", "组织代码", "组织类型", "员工数", "非全职", "人员编制", "缺编/超编", "负责人", "分管领导", "上级组织"]];
	state.flat.forEach((it) => {
		const n = it.node;
		const parent = state.flat.find((x) => x.node.name === it.parentKey);
		rows.push([
			n.title || "",
			n.org_code || "",
			n.org_type || "",
			n.employee_count || 0,
			n.parttime_count || 0,
			n.staff_quota || "",
			format_vacancy(n).replace(/<[^>]+>/g, ""),
			n.head_name || "",
			n.supervisor_name || "",
			parent ? parent.node.title : "",
		]);
	});
	const csv = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
	const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = "orgchart.csv";
	a.click();
	URL.revokeObjectURL(url);
}

function open_batch_dialog(state) {
	const dialog = new frappe.ui.Dialog({
		title: __("批量新增/更新"),
		fields: [
			{
				fieldtype: "HTML",
				options: `<div class="oc-batch-guide">${__("请按模板填写组织名称、上级组织等信息，支持新增或按组织代码更新。")}<br>
					<button type="button" class="oc-text-link oc-download-tpl">${__("下载 CSV 模板")}</button></div>`,
			},
			{ fieldname: "file", label: __("CSV 文件"), fieldtype: "Attach", reqd: 1 },
		],
		primary_action_label: __("导入"),
		primary_action(values) {
			if (!values.file) {
				frappe.msgprint(__("请上传 CSV 文件"));
				return;
			}
			dialog.get_primary_btn().prop("disabled", true).text(__("导入中..."));
			frappe.call({
				method: `${ORG_API}.import_org_units`,
				args: { file_url: values.file, company: state.company },
				freeze: true,
				freeze_message: __("正在导入组织..."),
				callback(r) {
					const res = r.message || {};
					frappe.show_alert({
						message: __("导入完成：新增 {0}，更新 {1}，跳过 {2}", [res.created || 0, res.updated || 0, (res.skipped || []).length]),
						indicator: "green",
					}, 7);
					dialog.hide();
					load_tree(state);
				},
				error() {
					dialog.get_primary_btn().prop("disabled", false).text(__("导入"));
				},
			});
		},
	});
	dialog.show();
	dialog.$wrapper.on("click", ".oc-download-tpl", () => {
		frappe.call({
			method: `${ORG_API}.get_org_import_template`,
			callback(r) {
				const file = r.message || {};
				const blob = new Blob(["\ufeff" + (file.content || "")], { type: "text/csv;charset=utf-8" });
				const url = URL.createObjectURL(blob);
				const a = document.createElement("a");
				a.href = url;
				a.download = file.filename || "org_import_template.csv";
				a.click();
				URL.revokeObjectURL(url);
			},
		});
	});
}

function open_org_drawer(state, preset = {}) {
	close_drawer();
	const parentTitle = preset.parentTitle || (state.data && state.data.company_name) || "";
	const parent = preset.parent || (state.data && state.data.roots && state.data.roots[0] && state.data.roots[0].name) || "";
	const today = frappe.datetime.get_today();
	const parentOptions = flatten_tree((state.data && state.data.roots) || [])
		.map((it) => `<option value="${esc(it.node.name)}" ${it.node.name === parent ? "selected" : ""}>${"　".repeat(it.depth)}${esc(it.node.title)}</option>`)
		.join("");

	const drawer = document.createElement("div");
	drawer.className = "oc-drawer-root";
	drawer.innerHTML = `
		<div class="oc-drawer-mask" data-close="1"></div>
		<aside class="oc-drawer" role="dialog" aria-modal="true" aria-labelledby="oc-drawer-title">
			<header class="oc-drawer-header">
				<h2 id="oc-drawer-title">${__("新增组织")}</h2>
				<button type="button" class="oc-icon-btn" data-close="1" aria-label="${__("关闭")}">${ICONS.close}</button>
			</header>
			<div class="oc-drawer-body">
				<div class="oc-form-row is-required" data-field="title">
					<label>${__("组织名称")}</label>
					<div class="oc-form-control">
						<input type="text" name="title" maxlength="140" autocomplete="off">
						<div class="oc-field-error">${__("组织名称不能为空")}</div>
					</div>
				</div>
				<div class="oc-form-row" data-field="org_code">
					<label>${__("组织代码")}</label>
					<div class="oc-form-control"><input type="text" name="org_code" placeholder="${__("请输入...")}"></div>
				</div>
				<div class="oc-form-row" data-field="org_abbr">
					<label>${__("组织简称")}</label>
					<div class="oc-form-control"><input type="text" name="org_abbr" placeholder="${__("请输入")}"></div>
				</div>
				<div class="oc-form-row" data-field="org_type">
					<label>${__("组织类型")}</label>
					<div class="oc-form-control">
						<select name="org_type">
							<option value="部门" selected>${__("部门")}</option>
							<option value="组">${__("组")}</option>
							<option value="公司">${__("公司")}</option>
						</select>
						<button type="button" class="oc-cost-center-toggle">${__("启用费用中心类型")}</button>
						<input type="hidden" name="enable_cost_center" value="0">
					</div>
				</div>
				<div class="oc-form-row" data-field="parent">
					<label>${__("上级组织")}</label>
					<div class="oc-form-control oc-has-icon">
						<select name="parent">${parentOptions}</select>
						<span class="oc-input-icon">${ICONS.picker}</span>
					</div>
				</div>
				<div class="oc-form-row" data-field="department_head">
					<label>${__("组织负责人")}</label>
					<div class="oc-form-control oc-has-icon">
						<input type="text" name="department_head_label" placeholder="${__("员工姓名/拼音")}" autocomplete="off">
						<input type="hidden" name="department_head">
						<span class="oc-input-icon">${ICONS.picker}</span>
						<div class="oc-suggest oc-head-suggest"></div>
					</div>
				</div>
				<div class="oc-form-row" data-field="staff_quota">
					<label>${__("编制人数")}</label>
					<div class="oc-form-control"><input type="number" name="staff_quota" min="0" step="1" placeholder="${__("请输入...")}"></div>
				</div>
				<div class="oc-form-row is-required" data-field="effective_date">
					<label>${__("启用日期")}</label>
					<div class="oc-form-control oc-has-icon">
						<input type="date" name="effective_date" value="${esc(today)}">
						<span class="oc-input-icon">${ICONS.calendar}</span>
					</div>
				</div>
				<button type="button" class="oc-expand-info">${__("展开信息")} ${ICONS.expand}</button>
				<div class="oc-extra-fields hidden">
					<div class="oc-form-row" data-field="supervisor">
						<label>${__("分管领导")}</label>
						<div class="oc-form-control oc-has-icon">
							<input type="text" name="supervisor_label" placeholder="${__("员工姓名/拼音")}" autocomplete="off">
							<input type="hidden" name="supervisor">
							<span class="oc-input-icon">${ICONS.picker}</span>
							<div class="oc-suggest oc-supervisor-suggest"></div>
						</div>
					</div>
					<div class="oc-form-row" data-field="org_remark">
						<label>${__("备注")}</label>
						<div class="oc-form-control"><textarea name="org_remark" rows="3" placeholder="${__("请输入")}"></textarea></div>
					</div>
				</div>
			</div>
			<footer class="oc-drawer-footer">
				<button type="button" class="oc-btn oc-btn-outline oc-save-continue">${__("保存并继续添加")}</button>
				<button type="button" class="oc-btn oc-btn-primary oc-save-confirm">${__("确认")}</button>
			</footer>
		</aside>
	`;
	document.body.appendChild(drawer);
	requestAnimationFrame(() => drawer.classList.add("open"));

	const $drawer = $(drawer);
	$drawer.on("click", "[data-close]", close_drawer);
	$drawer.find(".oc-expand-info").on("click", function () {
		$drawer.find(".oc-extra-fields").toggleClass("hidden");
		this.classList.toggle("is-open");
	});
	$drawer.find(".oc-cost-center-toggle").on("click", function () {
		const $hidden = $drawer.find("[name=enable_cost_center]");
		const next = $hidden.val() === "1" ? "0" : "1";
		$hidden.val(next);
		this.classList.toggle("is-on", next === "1");
		this.textContent = next === "1" ? __("已启用费用中心类型") : __("启用费用中心类型");
	});
	$drawer.find("[name=title]").on("input", function () {
		$drawer.find('[data-field="title"]').removeClass("has-error");
	});
	bind_employee_suggest(state, $drawer, "department_head", ".oc-head-suggest");
	bind_employee_suggest(state, $drawer, "supervisor", ".oc-supervisor-suggest");

	const submit = (continueAdd) => {
		const values = read_drawer_values($drawer);
		if (!values.title) {
			$drawer.find('[data-field="title"]').addClass("has-error");
			$drawer.find("[name=title]").focus();
			return;
		}
		const $btn = continueAdd ? $drawer.find(".oc-save-continue") : $drawer.find(".oc-save-confirm");
		$btn.prop("disabled", true);
		frappe.call({
			method: `${ORG_API}.create_org_unit`,
			args: { ...values, company: state.company },
			freeze: true,
			freeze_message: __("正在保存..."),
			callback() {
				frappe.show_alert({ message: __("组织已创建"), indicator: "green" });
				load_tree(state);
				if (continueAdd) {
					$drawer.find("[name=title], [name=org_code], [name=org_abbr], [name=staff_quota], [name=department_head], [name=department_head_label]").val("");
					$drawer.find('[data-field="title"]').removeClass("has-error");
					$btn.prop("disabled", false);
					$drawer.find("[name=title]").focus();
				} else {
					close_drawer();
				}
			},
			error() {
				$btn.prop("disabled", false);
			},
		});
	};

	$drawer.find(".oc-save-confirm").on("click", () => submit(false));
	$drawer.find(".oc-save-continue").on("click", () => submit(true));
	$drawer.find("[name=title]").focus();
	$drawer.find("[name=parent]").val(parent);
	if (parentTitle && !$drawer.find("[name=parent]").val()) {
		$drawer.find("[name=parent]").prepend(`<option value="${esc(parent)}" selected>${esc(parentTitle)}</option>`);
	}
}

function read_drawer_values($drawer) {
	return {
		title: String($drawer.find("[name=title]").val() || "").trim(),
		org_code: String($drawer.find("[name=org_code]").val() || "").trim(),
		org_abbr: String($drawer.find("[name=org_abbr]").val() || "").trim(),
		org_type: $drawer.find("[name=org_type]").val() || "部门",
		parent: $drawer.find("[name=parent]").val() || "",
		department_head: $drawer.find("[name=department_head]").val() || "",
		supervisor: $drawer.find("[name=supervisor]").val() || "",
		staff_quota: $drawer.find("[name=staff_quota]").val() || 0,
		effective_date: $drawer.find("[name=effective_date]").val() || "",
		enable_cost_center: $drawer.find("[name=enable_cost_center]").val() || 0,
		org_remark: String($drawer.find("[name=org_remark]").val() || "").trim(),
	};
}

function bind_employee_suggest(state, $scope, field, suggestSel) {
	const $input = $scope.find(`[name=${field}_label]`);
	const $hidden = $scope.find(`[name=${field}]`);
	const $suggest = $scope.find(suggestSel);
	let timer = null;
	$input.on("input", function () {
		$hidden.val("");
		clearTimeout(timer);
		const txt = String(this.value || "").trim();
		timer = setTimeout(() => {
			frappe.call({
				method: `${ORG_API}.search_employees`,
				args: { txt, company: state.company },
				callback(r) {
					const rows = r.message || [];
					if (!rows.length) {
						$suggest.html(`<div class="oc-suggest-empty">${__("没有匹配的员工")}</div>`).addClass("open");
						return;
					}
					$suggest
						.html(
							rows
								.map(
									(row) =>
										`<button type="button" class="oc-suggest-item" data-id="${esc(row.name)}" data-label="${esc(row.employee_name)}">${esc(row.employee_name)}<small>${esc(row.designation || row.department || row.name)}</small></button>`
								)
								.join("")
						)
						.addClass("open");
				},
			});
		}, 180);
	});
	$suggest.on("click", ".oc-suggest-item", function () {
		$hidden.val(this.getAttribute("data-id"));
		$input.val(this.getAttribute("data-label"));
		$suggest.removeClass("open").empty();
	});
}

function open_person_popover(state, btn) {
	close_popovers();
	const role = btn.getAttribute("data-role");
	const orgName = btn.getAttribute("data-name");
	const pop = document.createElement("div");
	pop.className = "oc-person-popover open";
	pop.innerHTML = `
		<input type="search" class="oc-person-search" placeholder="${__("员工姓名/拼音")}" aria-label="${__("搜索员工")}">
		<div class="oc-suggest open oc-person-results"><div class="oc-suggest-empty">${__("输入姓名搜索")}</div></div>
		<button type="button" class="oc-text-link oc-clear-person">${__("清除")}</button>
	`;
	document.body.appendChild(pop);
	position_popover(pop, btn);
	const $pop = $(pop);
	const run = (txt) => {
		frappe.call({
			method: `${ORG_API}.search_employees`,
			args: { txt, company: state.company },
			callback(r) {
				const rows = r.message || [];
				$pop.find(".oc-person-results").html(
					rows.length
						? rows
								.map(
									(row) =>
										`<button type="button" class="oc-suggest-item" data-id="${esc(row.name)}" data-label="${esc(row.employee_name)}">${esc(row.employee_name)}<small>${esc(row.designation || "")}</small></button>`
								)
								.join("")
						: `<div class="oc-suggest-empty">${__("没有匹配的员工")}</div>`
				);
			},
		});
	};
	$pop.find(".oc-person-search").on("input", function () {
		run(String(this.value || "").trim());
	}).trigger("focus");
	run("");
	$pop.on("click", ".oc-suggest-item", function () {
		save_person(state, orgName, role, this.getAttribute("data-id"));
	});
	$pop.on("click", ".oc-clear-person", () => save_person(state, orgName, role, ""));
	$pop.on("click", (e) => e.stopPropagation());
}

function save_person(state, orgName, role, employee) {
	frappe.call({
		method: `${ORG_API}.update_org_person`,
		args: { org_name: orgName, role, employee },
		callback() {
			frappe.show_alert({ message: __("已更新"), indicator: "green" });
			close_popovers();
			load_tree(state);
		},
	});
}

function position_popover(el, anchor) {
	const rect = anchor.getBoundingClientRect();
	el.style.top = `${rect.bottom + window.scrollY + 6}px`;
	el.style.left = `${Math.max(12, rect.left + window.scrollX - 80)}px`;
}

function close_drawer() {
	const root = document.querySelector(".oc-drawer-root");
	if (!root) return;
	root.classList.remove("open");
	setTimeout(() => root.remove(), 180);
}

function esc(s) {
	return String(s == null ? "" : s)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;");
}
