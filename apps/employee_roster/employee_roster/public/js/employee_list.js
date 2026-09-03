// Copyright (c) 2026 stillgroup
// License: MIT

frappe.listview_settings["Employee"] = {
	onload(listview) {
		ensure_employee_list_styles();
		inject_stat_board(listview);
		bind_stat_board(listview);
		refresh_stat_board(listview);
	},

	refresh(listview) {
		if (!listview.$hr_stat_board || !listview.$hr_stat_board.length) {
			inject_stat_board(listview);
			bind_stat_board(listview);
		}
		refresh_stat_board(listview);
	},
};

function ensure_employee_list_styles() {
	if (document.getElementById("hr-employee-list-stat-style")) return;
	const style = document.createElement("style");
	style.id = "hr-employee-list-stat-style";
	style.textContent = `
		.layout-main-section.hr-employee-list-page {
			display: flex;
			flex-direction: column;
		}
		.layout-main-section.hr-employee-list-page > .page-form {
			margin-bottom: 0;
		}
		.hr-roster-page.hr-employee-list-stats {
			--hr-primary: #00b386;
			--hr-primary-hover: #00a077;
			--hr-border: #e5e6eb;
			--hr-bg: #fff;
			--hr-subtle: #f7f8fa;
			--hr-text: #1f2329;
			--hr-muted: #8f959e;
			/* Match .frappe-list horizontal inset so cards align with the roster below */
			margin: 12px 15px;
			flex-shrink: 0;
			font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
		}
		.hr-roster-page.hr-employee-list-stats .hr-stat-board {
			display: grid !important;
			grid-template-columns: 0.9fr 1.1fr 1.5fr 1.1fr;
			gap: 12px;
			margin: 0;
		}
		.hr-roster-page.hr-employee-list-stats .hr-stat-card {
			display: flex;
			flex-direction: row;
			align-items: stretch;
			background: var(--hr-bg);
			border: 1px solid var(--hr-border);
			border-radius: 8px;
			min-height: 88px;
			overflow: hidden;
			padding: 0;
			box-shadow: none;
			text-align: initial;
			cursor: default;
		}
		.hr-roster-page.hr-employee-list-stats .hr-stat-card.hr-stat-card--split2 .hr-stat-cell {
			flex: 1 1 50%;
		}
		.hr-roster-page.hr-employee-list-stats .hr-stat-card.hr-stat-card--split3 .hr-stat-cell {
			flex: 1 1 33.33%;
		}
		.hr-roster-page.hr-employee-list-stats .hr-stat-cell {
			appearance: none;
			flex: 1;
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			gap: 8px;
			padding: 14px 10px;
			border: none;
			background: transparent;
			cursor: pointer;
			text-align: center;
		}
		.hr-roster-page.hr-employee-list-stats .hr-stat-cell:not(:last-child) {
			border-right: 1px solid var(--hr-border);
		}
		.hr-roster-page.hr-employee-list-stats .hr-stat-cell:hover {
			background: var(--hr-subtle);
		}
		.hr-roster-page.hr-employee-list-stats .hr-stat-cell.is-active {
			background: #f0faf6;
		}
		.hr-roster-page.hr-employee-list-stats .hr-stat-label {
			font-size: 13px;
			color: var(--hr-muted);
			line-height: 1.2;
			margin: 0;
		}
		.hr-roster-page.hr-employee-list-stats .hr-stat-num {
			font-size: 20px;
			font-weight: 700;
			color: var(--hr-text);
			line-height: 1.2;
		}
		.hr-roster-page.hr-employee-list-stats .hr-stat-unit {
			font-size: 13px;
			font-weight: 400;
			margin-left: 2px;
		}
		.hr-roster-page.hr-employee-list-stats .hr-stat-cell.is-green .hr-stat-label,
		.hr-roster-page.hr-employee-list-stats .hr-stat-cell.is-green .hr-stat-num {
			color: var(--hr-primary);
		}
		@media (max-width: 1200px) {
			.hr-roster-page.hr-employee-list-stats .hr-stat-board {
				grid-template-columns: repeat(2, 1fr);
			}
		}
		@media (max-width: 768px) {
			.hr-roster-page.hr-employee-list-stats .hr-stat-board {
				grid-template-columns: 1fr;
			}
		}
	`;
	document.head.appendChild(style);
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

	$board.off("click.hr-stat").on("click.hr-stat", ".hr-stat-cell[data-filter-field]", async function () {
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
		},
	});
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
		<div class="hr-stat-num">${value}<span class="hr-stat-unit">${__("人")}</span></div>
	</button>`;
}

function render_stat_board($wrap, stats, listview) {
	const fulltime = get_employment_count(stats, "Full-time");
	const intern = get_employment_count(stats, "Intern");
	const probation = get_employment_count(stats, "Probation");

	$wrap.find(".hr-stat-board").html(`
		<div class="hr-stat-card">${stat_cell(__("在职"), stats.active || 0, "status", "Active", " is-green")}</div>
		<div class="hr-stat-card hr-stat-card--split2">
			${stat_cell(__("全职"), fulltime, "designation", "实习生", "", "!=")}
			${stat_cell(__("实习生"), intern, "designation", "实习生", "")}
		</div>
		<div class="hr-stat-card hr-stat-card--split3">
			${stat_cell(__("试用期"), probation, "employment_type", "Probation", "")}
			${stat_cell(__("停用"), stats.inactive || 0, "status", "Inactive", "")}
			${stat_cell(__("正式"), fulltime, "designation", "实习生", "", "!=")}
		</div>
		<div class="hr-stat-card hr-stat-card--split2">
			${stat_cell(__("待入职") + " ›", 0, "", "", "")}
			${stat_cell(__("已离职"), stats.left || 0, "status", "Left", "")}
		</div>
	`);

	sync_stat_active($wrap, listview);
}

function sync_stat_active($wrap, listview) {
	$wrap.find(".hr-stat-cell").removeClass("is-active");

	const status = get_filter_value(listview, "status");
	const designation = get_filter_value(listview, "designation");
	const designationOp = get_filter_operator(listview, "designation");
	const employment_type = get_filter_value(listview, "employment_type");

	if (status) {
		$wrap
			.find(`.hr-stat-cell[data-filter-field="status"][data-filter-value="${css_escape(status)}"]`)
			.addClass("is-active");
	}
	if (designation === "实习生") {
		const opSel =
			designationOp === "!="
				? '[data-filter-operator="!="]'
				: ':not([data-filter-operator])';
		$wrap
			.find(`.hr-stat-cell[data-filter-field="designation"][data-filter-value="实习生"]${opSel}`)
			.addClass("is-active");
	}
	if (employment_type) {
		$wrap
			.find(
				`.hr-stat-cell[data-filter-field="employment_type"][data-filter-value="${css_escape(employment_type)}"]`,
			)
			.addClass("is-active");
	}

	if (!status && !designation && !employment_type) {
		$wrap.find('.hr-stat-cell[data-filter-field="status"][data-filter-value="Active"]').addClass("is-active");
	}
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
