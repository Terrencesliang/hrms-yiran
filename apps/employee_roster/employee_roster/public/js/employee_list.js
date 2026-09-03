// Copyright (c) 2026 stillgroup
// License: MIT
//
// Employee List View UI restyle only — keep Frappe ListView filters,
// sorting, selection, pagination, actions and routes intact.

frappe.listview_settings["Employee"] = {
	add_fields: ["employee_name", "image", "status", "employment_type", "designation"],

	onload(listview) {
		ensure_employee_list_styles();
		mark_employee_list_page(listview);
		enhance_page_head(listview);
		enhance_filter_toolbar(listview);
		inject_stat_board(listview);
		bind_stat_board(listview);
		refresh_stat_board(listview);
	},

	refresh(listview) {
		ensure_employee_list_styles();
		mark_employee_list_page(listview);
		enhance_page_head(listview);
		enhance_filter_toolbar(listview);

		if (!listview.$hr_stat_board || !listview.$hr_stat_board.length) {
			inject_stat_board(listview);
			bind_stat_board(listview);
		}
		refresh_stat_board(listview);
		enhance_row_avatars(listview);
		restyle_primary_button(listview);
	},

	formatters: {
		employment_type(value) {
			if (!value) return "";
			const labels = {
				"Full-time": __("正式"),
				Intern: __("实习生"),
				Probation: __("试用期"),
				"Part-time": __("兼职"),
				Contract: __("合同"),
			};
			const label = labels[value] || value;
			const cls = value === "Intern" ? "hr-emp-tag hr-emp-tag--intern" : "hr-emp-tag";
			return `<span class="${cls}">${frappe.utils.escape_html(label)}</span>`;
		},
	},
};

function mark_employee_list_page(listview) {
	listview.$page.addClass("hr-employee-list-shell");
	listview.$page.find(".layout-main-section").addClass("hr-employee-list-page");
	document.body.classList.add("hr-employee-list-route");
	if (!window.__hr_employee_list_route_bound) {
		window.__hr_employee_list_route_bound = true;
		frappe.router.on("change", () => {
			const route = frappe.get_route() || [];
			const on_employee_list = route[0] === "List" && route[1] === "Employee";
			document.body.classList.toggle("hr-employee-list-route", on_employee_list);
		});
	}
}

function ensure_employee_list_styles() {
	let style = document.getElementById("hr-employee-list-stat-style");
	if (!style) {
		style = document.createElement("style");
		style.id = "hr-employee-list-stat-style";
		document.head.appendChild(style);
	}
	style.textContent = HR_EMPLOYEE_LIST_CSS;
}

const HR_EMPLOYEE_LIST_CSS = `
body.hr-employee-list-route .page-container[data-page-container="List/Employee"],
body.hr-employee-list-route .page-container:has(.hr-employee-list-page) {
	background: #f5f6f8;
}
.hr-employee-list-shell .page-head {
	background: transparent;
	border-bottom: none;
	margin-bottom: 0;
	padding-bottom: 4px;
}
.hr-employee-list-shell .page-head .page-title h3,
.hr-employee-list-shell .page-head .page-title .title-text {
	font-size: 22px;
	font-weight: 700;
	color: #1f2329;
	letter-spacing: -0.01em;
}
.hr-employee-list-shell .hr-page-count {
	margin-left: 10px;
	font-size: 13px;
	font-weight: 400;
	color: #8f959e;
	vertical-align: middle;
}
.hr-employee-list-shell .page-actions .btn-primary,
.hr-employee-list-shell .btn-primary.primary-action {
	background: #2d8a62 !important;
	border-color: #2d8a62 !important;
	color: #fff !important;
	border-radius: 8px;
	font-weight: 600;
	box-shadow: none;
}
.hr-employee-list-shell .page-actions .btn-primary:hover,
.hr-employee-list-shell .btn-primary.primary-action:hover {
	background: #267553 !important;
	border-color: #267553 !important;
}
.hr-employee-list-shell .page-actions .btn-default,
.hr-employee-list-shell .page-icon-group .btn {
	border-radius: 8px;
	border-color: #e5e6eb;
	background: #fff;
	color: #4e5969;
}
.layout-main-section.hr-employee-list-page {
	display: flex;
	flex-direction: column;
	gap: 12px;
	background: transparent;
	padding-top: 4px;
	/* Keep page scroll on .main-section; do not clip list height. */
	overflow: visible !important;
	min-height: 0;
	height: auto;
}
.layout-main-section.hr-employee-list-page > .page-form {
	margin-bottom: 0;
}
.hr-employee-list-page .page-form.list-page-form,
.hr-employee-list-page .hr-list-page-form {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	gap: 10px;
	padding: 12px 14px;
	background: #fff;
	border: 1px solid #e5e6eb;
	border-radius: 10px;
	box-shadow: none;
}
.hr-employee-list-page .hr-list-page-form .standard-filter-section {
	display: flex;
	flex: 1 1 240px;
	flex-wrap: wrap;
	align-items: flex-end;
	gap: 10px;
	min-width: 0;
}
.hr-employee-list-page .hr-list-page-form:not(.hr-filters-open) .standard-filter-section > .frappe-control:not(.hr-main-search) {
	display: none !important;
}
.hr-employee-list-page .hr-list-page-form .standard-filter-section > .hr-main-search {
	flex: 1 1 260px;
	margin: 0;
	max-width: none !important;
	min-width: 200px;
}
.hr-employee-list-page .hr-list-page-form .standard-filter-section > .hr-main-search .form-group {
	margin: 0;
}
.hr-employee-list-page .hr-list-page-form .standard-filter-section > .hr-main-search .clearfix {
	display: none;
}
.hr-employee-list-page .hr-list-page-form .standard-filter-section > .hr-main-search input.input-with-feedback,
.hr-employee-list-page .hr-list-page-form .standard-filter-section > .hr-main-search input.form-control {
	height: 36px;
	border: 1px solid #e5e6eb;
	border-radius: 8px;
	padding-left: 36px;
	background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%238f959e' stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-3-3'/%3E%3C/svg%3E") 12px center / 14px no-repeat;
	font-size: 13px;
	color: #1f2329;
	box-shadow: none;
}
.hr-employee-list-page .hr-list-page-form .standard-filter-section > .hr-main-search input:focus {
	border-color: #2d8a62;
	box-shadow: 0 0 0 2px rgba(45, 138, 98, 0.15);
}
.hr-employee-list-page .hr-list-page-form.hr-filters-open .standard-filter-section > .frappe-control:not(.hr-main-search) {
	display: block !important;
	min-width: 160px;
	margin: 0;
}
.hr-employee-list-page .hr-list-page-form.hr-filters-open .standard-filter-section > .frappe-control:not(.hr-main-search) .clearfix {
	font-size: 12px;
	color: #8f959e;
	margin-bottom: 4px;
}
.hr-employee-list-page .hr-list-page-form .filter-section {
	display: flex;
	align-items: center;
	gap: 8px;
	margin: 0;
	flex: 0 0 auto;
}
.hr-employee-list-page .hr-filter-panel-btn {
	height: 36px;
	border: 1px solid #e5e6eb;
	background: #fff;
	color: #2d8a62;
	border-radius: 8px;
	font-size: 13px;
	font-weight: 500;
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 0 12px;
}
.hr-employee-list-page .hr-filter-panel-btn::before {
	content: "";
	width: 14px;
	height: 14px;
	background: center / contain no-repeat url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232d8a62' stroke-width='2'%3E%3Cpath d='M4 5h16l-6 7v5l-4 2v-7L4 5z'/%3E%3C/svg%3E");
}
.hr-employee-list-page .hr-filter-panel-btn.is-open,
.hr-employee-list-page .hr-filter-panel-btn.has-filter {
	background: #f0faf6;
	border-color: #b7e0cc;
}
.hr-employee-list-page .hr-filter-panel-btn .filter-count {
	color: #2d8a62;
	font-weight: 700;
}
.hr-employee-list-page .hr-list-page-form .filter-selector .btn,
.hr-employee-list-page .hr-list-page-form .sort-selector .btn {
	height: 36px;
	border-radius: 8px;
	border-color: #e5e6eb;
	background: #fff;
	color: #4e5969;
	font-size: 13px;
}
.hr-employee-list-stats {
	--hr-primary: #2d8a62;
	--hr-border: #e5e6eb;
	--hr-bg: #fff;
	--hr-subtle: #f7f8fa;
	--hr-text: #1f2329;
	--hr-muted: #8f959e;
	margin: 0;
	flex-shrink: 0;
	font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}
.hr-employee-list-stats .hr-stat-board {
	display: flex !important;
	align-items: stretch;
	gap: 0;
	margin: 0;
	background: var(--hr-bg);
	border: 1px solid var(--hr-border);
	border-radius: 10px;
	overflow: hidden;
	min-height: 72px;
}
.hr-employee-list-stats .hr-stat-primary {
	appearance: none;
	border: none;
	background: #f0faf6;
	min-width: 160px;
	padding: 14px 20px;
	display: flex;
	flex-direction: column;
	justify-content: center;
	gap: 4px;
	cursor: pointer;
	text-align: left;
	border-right: 1px solid var(--hr-border);
}
.hr-employee-list-stats .hr-stat-primary .hr-stat-label {
	font-size: 13px;
	color: var(--hr-primary);
}
.hr-employee-list-stats .hr-stat-primary .hr-stat-num {
	font-size: 22px;
	font-weight: 700;
	color: var(--hr-primary);
	line-height: 1.2;
}
.hr-employee-list-stats .hr-stat-primary.is-active {
	background: #e6f6ef;
}
.hr-employee-list-stats .hr-stat-rest {
	display: flex;
	flex: 1;
	align-items: stretch;
	min-width: 0;
	overflow-x: auto;
}
.hr-employee-list-stats .hr-stat-cell {
	appearance: none;
	flex: 1 1 0;
	min-width: 88px;
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	justify-content: center;
	gap: 4px;
	padding: 14px 16px;
	border: none;
	background: transparent;
	cursor: pointer;
	text-align: left;
}
.hr-employee-list-stats .hr-stat-cell:not(:last-child) {
	border-right: 1px solid var(--hr-border);
}
.hr-employee-list-stats .hr-stat-cell:hover {
	background: var(--hr-subtle);
}
.hr-employee-list-stats .hr-stat-cell.is-active {
	background: #f0faf6;
}
.hr-employee-list-stats .hr-stat-cell .hr-stat-label {
	font-size: 12px;
	color: var(--hr-muted);
	line-height: 1.2;
	margin: 0;
}
.hr-employee-list-stats .hr-stat-cell .hr-stat-num {
	font-size: 18px;
	font-weight: 700;
	color: var(--hr-text);
	line-height: 1.2;
}
.hr-employee-list-stats .hr-stat-unit {
	font-size: 12px;
	font-weight: 400;
	margin-left: 2px;
	color: inherit;
}
.hr-employee-list-page .frappe-list {
	background: #fff;
	border: 1px solid #e5e6eb;
	border-radius: 10px;
	/* Critical: never overflow:hidden here — it blocks ListView scroll
	   (page scroll and/or .result-container virtualization). */
	overflow: visible;
	flex: 0 0 auto;
	min-height: 0;
}
.hr-employee-list-page .result-container {
	background: transparent;
	border: none;
	border-radius: 0;
	overflow-x: auto;
	overflow-y: auto;
	-webkit-overflow-scrolling: touch;
}
.hr-employee-list-page .result {
	background: transparent;
	border: none;
	border-radius: 0;
	overflow: visible;
}
.hr-employee-list-page .frappe-list .result {
	border: none;
	border-radius: 0;
}
/* Ensure desk main area remains the scrollport under unified sidebar. */
body.hr-employee-list-route.hr-unified-sidebar-active .main-section {
	overflow: auto !important;
	overflow-x: hidden !important;
	overscroll-behavior: contain;
}
.hr-employee-list-page .list-row-head,
.hr-employee-list-page .list-row {
	padding: 10px 16px;
	border-color: #eef0f3 !important;
	min-height: 52px;
}
.hr-employee-list-page .list-row-head {
	background: #fafbfc;
	color: #8f959e;
	font-size: 12px;
	font-weight: 500;
}
.hr-employee-list-page .list-row:hover {
	background: #fafbfc;
}
.hr-employee-list-page .list-subject {
	align-items: center;
	gap: 10px;
}
.hr-employee-list-page .hr-emp-avatar {
	flex: 0 0 32px;
	width: 32px;
	height: 32px;
	border-radius: 50%;
	background: #e8f5ef;
	color: #2d8a62;
	font-size: 12px;
	font-weight: 700;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	letter-spacing: 0;
	line-height: 1;
}
.hr-employee-list-page .list-subject a {
	font-weight: 600;
	color: #1f2329 !important;
	font-size: 13px;
}
.hr-employee-list-page .list-row .level-item {
	color: #4e5969;
	font-size: 13px;
}
.hr-employee-list-page .hr-emp-tag {
	display: inline-block;
	padding: 2px 8px;
	border-radius: 4px;
	font-size: 12px;
	color: #4e5969;
	background: #f2f3f5;
}
.hr-employee-list-page .hr-emp-tag--intern {
	background: #eef2f6;
	color: #5b6b7c;
}
.hr-employee-list-page .list-paging-area {
	border-top: 1px solid #eef0f3;
	background: #fff;
	padding: 10px 16px;
}
@media (max-width: 900px) {
	.hr-employee-list-stats .hr-stat-board {
		flex-direction: column;
	}
	.hr-employee-list-stats .hr-stat-primary {
		border-right: none;
		border-bottom: 1px solid var(--hr-border);
	}
}
`;

function enhance_page_head(listview) {
	const $title = listview.$page.find(".page-head .page-title").first();
	if (!$title.length) return;

	if (!$title.find(".hr-page-count").length) {
		$title.append(`<span class="hr-page-count"></span>`);
	}
	restyle_primary_button(listview);
}

function restyle_primary_button(listview) {
	const $btn = listview.page.btn_primary;
	if (!$btn || !$btn.length) return;
	const label = "+ " + __("添加员工");
	if ($btn.text().trim() !== label) {
		$btn.text(label);
	}
	$btn.addClass("hr-add-employee-btn");
}

function enhance_filter_toolbar(listview) {
	const $form = listview.page.page_form;
	if (!$form || !$form.length || $form.data("hr-enhanced")) return;

	$form.data("hr-enhanced", 1);
	$form.addClass("hr-list-page-form");

	const $std = $form.find(".standard-filter-section").first();
	let $mainControl = $std.find('[data-fieldname="employee_name"]').first();
	if (!$mainControl.length) {
		$mainControl = $std.find('[data-fieldname="name"]').first();
	}
	if ($mainControl.length) {
		$mainControl.addClass("hr-main-search");
		const $input = $mainControl.find("input").first();
		if ($input.length) {
			$input.attr("placeholder", __("搜索姓名、编号、部门或职位"));
		}
	}

	const $filterSection = $form.find(".filter-section").first();
	const $btn = $(`
		<button type="button" class="btn btn-sm hr-filter-panel-btn" aria-expanded="false">
			<span class="hr-filter-panel-label">${__("筛选条件")}</span>
			<span class="filter-count"></span>
		</button>
	`);

	if ($filterSection.length) {
		$filterSection.prepend($btn);
	} else {
		$form.append($btn);
	}

	$btn.on("click.hr-filter-panel", () => {
		const open = !$form.hasClass("hr-filters-open");
		$form.toggleClass("hr-filters-open", open);
		$btn.toggleClass("is-open", open);
		$btn.attr("aria-expanded", String(open));
	});

	listview.$hr_filter_panel_btn = $btn;
	update_filter_panel_badge(listview);
}

function update_filter_panel_badge(listview) {
	const $btn = listview.$hr_filter_panel_btn;
	if (!$btn || !$btn.length) return;

	const filters = (listview.filter_area && listview.filter_area.get()) || [];
	const mainField =
		listview.page.fields_dict.employee_name?.df?.fieldname ||
		listview.page.fields_dict.name?.df?.fieldname ||
		"";
	const extra = filters.filter((f) => f[1] !== mainField && f[3] !== "" && f[3] != null);
	const $count = $btn.find(".filter-count");
	if (extra.length) {
		$count.text(`(${extra.length})`);
		$btn.addClass("has-filter");
	} else {
		$count.text("");
		$btn.removeClass("has-filter");
	}
}

function inject_stat_board(listview) {
	const $section = listview.$page.find(".layout-main-section");
	if (!$section.length) return;

	$section.addClass("hr-employee-list-page");
	$section.find(".hr-employee-list-stats").remove();

	const $board = $(`
		<div class="hr-roster-page hr-employee-list-stats">
			<div class="hr-stat-board"></div>
		</div>
	`);

	const $page_form = $section.find(".page-form").first();
	if ($page_form.length) {
		$page_form.after($board);
	} else {
		$section.prepend($board);
	}

	listview.$hr_stat_board = $board;
}

function bind_stat_board(listview) {
	const $board = listview.$hr_stat_board;
	if (!$board || !$board.length) return;

	$board.off("click.hr-stat").on("click.hr-stat", ".hr-stat-cell[data-filter-field], .hr-stat-primary[data-filter-field]", async function () {
		const $cell = $(this);
		const field = $cell.attr("data-filter-field");
		const value = $cell.attr("data-filter-value") || "";
		const operator = $cell.attr("data-filter-operator") || "=";
		if (!field || !value) return;

		const current = get_filter_value(listview, field);
		const currentOp = get_filter_operator(listview, field);
		if (current === value && currentOp === operator) {
			await remove_filter(listview, field);
		} else {
			await set_filter(listview, field, value, operator);
		}
		update_filter_panel_badge(listview);
	});
}

function refresh_stat_board(listview) {
	const $board = listview.$hr_stat_board;
	if (!$board || !$board.length) return;

	const company = get_filter_value(listview, "company") || "";

	frappe.call({
		method: "employee_roster.hr_roster.page.roster.roster.get_employee_stats",
		args: { company },
		callback(r) {
			if (!r.message || !listview.$hr_stat_board) return;
			render_stat_board(listview.$hr_stat_board, r.message, listview);
			update_page_count(listview, r.message);
			update_filter_panel_badge(listview);
		},
	});
}

function update_page_count(listview, stats) {
	const total = stats.total != null ? stats.total : stats.active || 0;
	const $count = listview.$page.find(".hr-page-count");
	if ($count.length) {
		$count.text(__("共 {0} 名员工", [total]));
	}
}

function get_employment_count(stats, key) {
	return (stats.employment_counts && stats.employment_counts[key]) || 0;
}

function escape_attr(value) {
	return frappe.utils.escape_html(String(value || ""));
}

function stat_cell(label, value, filterField, filterValue, extraClass, filterOperator) {
	let attrs = "";
	if (filterField && filterValue) {
		attrs = ` data-filter-field="${escape_attr(filterField)}" data-filter-value="${escape_attr(filterValue)}"`;
		if (filterOperator && filterOperator !== "=") {
			attrs += ` data-filter-operator="${escape_attr(filterOperator)}"`;
		}
	}
	return `<button type="button" class="hr-stat-cell${extraClass || ""}"${attrs}>
		<div class="hr-stat-label">${label}</div>
		<div class="hr-stat-num">${value}</div>
	</button>`;
}

function render_stat_board($wrap, stats, listview) {
	const fulltime = get_employment_count(stats, "Full-time");
	const intern = get_employment_count(stats, "Intern");
	const probation = get_employment_count(stats, "Probation");

	$wrap.find(".hr-stat-board").html(`
		<button type="button" class="hr-stat-primary" data-filter-field="status" data-filter-value="Active">
			<div class="hr-stat-label">${__("在职员工")}</div>
			<div class="hr-stat-num">${stats.active || 0}<span class="hr-stat-unit">${__("人")}</span></div>
		</button>
		<div class="hr-stat-rest">
			${stat_cell(__("全职"), fulltime, "designation", "实习生", "", "!=")}
			${stat_cell(__("实习生"), intern, "designation", "实习生", "")}
			${stat_cell(__("试用期"), probation, "employment_type", "Probation", "")}
			${stat_cell(__("停用"), stats.inactive || 0, "status", "Inactive", "")}
			${stat_cell(__("待入职"), 0, "", "", "")}
			${stat_cell(__("已离职"), stats.left || 0, "status", "Left", "")}
		</div>
	`);

	sync_stat_active($wrap, listview);
}

function sync_stat_active($wrap, listview) {
	$wrap.find(".hr-stat-cell, .hr-stat-primary").removeClass("is-active");

	const status = get_filter_value(listview, "status");
	const designation = get_filter_value(listview, "designation");
	const designationOp = get_filter_operator(listview, "designation");
	const employment_type = get_filter_value(listview, "employment_type");

	if (status) {
		$wrap
			.find(`[data-filter-field="status"][data-filter-value="${css_escape(status)}"]`)
			.addClass("is-active");
	}
	if (designation === "实习生") {
		const opSel =
			designationOp === "!="
				? '[data-filter-operator="!="]'
				: ':not([data-filter-operator])';
		$wrap
			.find(`[data-filter-field="designation"][data-filter-value="实习生"]${opSel}`)
			.addClass("is-active");
	}
	if (employment_type) {
		$wrap
			.find(`[data-filter-field="employment_type"][data-filter-value="${css_escape(employment_type)}"]`)
			.addClass("is-active");
	}

	if (!status && !designation && !employment_type) {
		$wrap.find('[data-filter-field="status"][data-filter-value="Active"]').addClass("is-active");
	}
}

function enhance_row_avatars(listview) {
	if (!listview.$result || !listview.$result.length) return;

	listview.$result.find(".list-row-container").each(function () {
		const $row = $(this);
		if ($row.find(".hr-emp-avatar").length) return;

		const $link = $row.find(".list-subject a").first();
		if (!$link.length) return;

		const name = ($link.text() || "").trim();
		const initials = get_initials(name);
		$link.before(`<span class="hr-emp-avatar" aria-hidden="true">${frappe.utils.escape_html(initials)}</span>`);
	});
}

function get_initials(name) {
	const text = String(name || "").trim();
	if (!text) return "?";
	// Chinese names: last 2 chars; Latin: first letters of up to 2 words
	if (/[\u4e00-\u9fff]/.test(text)) {
		return text.slice(-2);
	}
	const parts = text.split(/\s+/).filter(Boolean);
	if (parts.length >= 2) {
		return (parts[0][0] + parts[1][0]).toUpperCase();
	}
	return text.slice(0, 2).toUpperCase();
}

function css_escape(value) {
	if (window.CSS && CSS.escape) return CSS.escape(value);
	return String(value).replace(/"/g, '\\"');
}

function get_filter_value(listview, fieldname) {
	const filters = listview.filter_area.get() || [];
	const match = filters.find((f) => f[1] === fieldname);
	return match ? match[3] : "";
}

function get_filter_operator(listview, fieldname) {
	const filters = listview.filter_area.get() || [];
	const match = filters.find((f) => f[1] === fieldname);
	return match ? match[2] : "";
}

async function remove_filter(listview, fieldname) {
	if (listview.filter_area.remove) {
		await listview.filter_area.remove(fieldname);
	}
}

async function set_filter(listview, fieldname, value, operator) {
	await remove_filter(listview, fieldname);
	await listview.filter_area.add([[listview.doctype, fieldname, operator || "=", value]]);
}
