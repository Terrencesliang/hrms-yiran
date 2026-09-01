// Copyright (c) 2026 stillgroup
// License: MIT

const HR_STATUS_LABELS = {
	Active: __("在职"),
	Left: __("已离职"),
	Inactive: __("停用"),
	Suspended: __("暂停"),
};

const HR_STATUS_CLASS = {
	Active: "status-active",
	Left: "status-left",
	Inactive: "status-inactive",
	Suspended: "status-suspended",
};

const HR_EMPLOYMENT_LABELS = {
	"Full-time": __("全职"),
	"Part-time": __("兼职"),
	Intern: __("实习生"),
	Contract: __("合同"),
	Probation: __("试用期"),
};

function ensure_roster_styles() {
	if (document.getElementById("hr-roster-stylesheet")) return;
	const link = document.createElement("link");
	link.id = "hr-roster-stylesheet";
	link.rel = "stylesheet";
	link.href = `/assets/employee_roster/css/roster.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["roster"].on_page_load = function (wrapper) {
	ensure_roster_styles();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("员工花名册"),
		single_column: true,
	});

	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const page = wrapper.page;
	const $main = page.main;

	$main.empty();
	$main.addClass("hr-roster-page");

	$main.html(`
		<div class="hr-page-shell">
			<div class="hr-filter-bar">
				<div class="hr-filter-left">
					<div class="hr-search-box">
						<input type="text" class="hr-search-input" placeholder="${__("姓名/手机号/工号")}">
					</div>
					<div class="hr-dept-wrap">
						<span class="hr-dept-label">${__("部门")}:</span>
						<select class="hr-dept-filter"></select>
					</div>
					<button class="btn btn-default btn-sm hr-filter-btn" type="button">
						<span class="hr-filter-text">${__("筛选")}</span><span class="hr-filter-count"></span>
					</button>
					<div class="hr-filter-popover">
						<div class="hr-filter-popover-title">${__("更多筛选")}</div>
						<label class="hr-filter-field">
							<span>${__("状态")}</span>
							<select class="hr-status-filter"></select>
						</label>
						<div class="hr-filter-popover-actions">
							<button class="btn btn-default btn-sm hr-filter-reset" type="button">${__("重置")}</button>
							<button class="btn btn-primary btn-sm hr-filter-apply" type="button">${__("确定")}</button>
						</div>
					</div>
				</div>
				<div class="hr-filter-right">
					<button class="btn btn-primary btn-sm hr-add-btn" type="button">+ ${__("添加员工")}</button>
					<button class="btn btn-default btn-sm hr-import-btn" type="button">${__("导入")}</button>
					<button class="btn btn-default btn-sm hr-export-btn" type="button">${__("导出")}</button>
					<button class="btn btn-default btn-sm hr-more-btn" type="button">${__("更多功能")} ▾</button>
				</div>
			</div>
			<div class="hr-stat-board"></div>
			<div class="hr-table-card">
				<div class="hr-table-toolbar">
					<div class="hr-table-toolbar-left">
						<span class="hr-table-count"></span>
						<span class="hr-sort-rule">${__("排序规则")}：${__("工号升序")}</span>
					</div>
					<button class="btn btn-link btn-sm hr-refresh-btn" type="button">${__("刷新")}</button>
				</div>
				<div class="hr-table-scroll">
					<table class="hr-roster-table">
						<thead></thead>
						<tbody></tbody>
					</table>
				</div>
				<div class="hr-table-hint">${__("双击「手机号 / 组别 / 状态」单元格可直接编辑")}</div>
			</div>
		</div>
		<datalist id="hr-group-options"></datalist>
	`);

	const state = {
		rows: [],
		groups: [],
		stats: {},
		keyword: "",
		department: "",
		status: "",
		search_timer: null,
		selected: new Set(),
		column_defs: [
			{ key: "_select", label: "", width: "44px", type: "checkbox", sticky: false },
			{ key: "employee_name", label: __("姓名"), width: "130px" },
			{ key: "employee_number", label: __("工号"), width: "80px" },
			{ key: "department", label: __("部门"), minWidth: "160px" },
			{ key: "designation", label: __("岗位"), width: "120px" },
			{ key: "employment_type", label: __("工作性质"), width: "96px" },
			{ key: "date_of_joining", label: __("入职日期"), width: "110px" },
			{ key: "branch", label: __("上班地点"), width: "96px" },
			{ key: "group_name", label: __("组别"), width: "96px", editable: true, inputType: "datalist", datalist: "hr-group-options" },
			{ key: "cell_number", label: __("手机号码"), width: "120px", editable: true, inputType: "text", validate: "mobile" },
			{ key: "status", label: __("状态"), width: "88px", editable: true, inputType: "select", options: ["Active", "Inactive", "Suspended", "Left"] },
			{ key: "_actions", label: __("操作"), width: "88px", type: "actions", sticky: true },
		],
	};

	init_toolbar($main, state);
	load_home_data($main, state);
};

frappe.pages["roster"].on_page_leave = function () {
	$(document).off("click.hr-roster-filter");
};


function init_toolbar($main, state) {
	const $kw = $main.find(".hr-search-input");
	const $dept = $main.find(".hr-dept-filter");
	const $status = $main.find(".hr-status-filter");

	$dept.html(`<option value="">${__("全部")}</option>`);
	$status.html(`<option value="">${__("全部状态")}</option><option value="Active">${__("在职")}</option><option value="Left">${__("已离职")}</option><option value="Inactive">${__("停用")}</option><option value="Suspended">${__("暂停")}</option>`);

	frappe.call({
		method: "employee_roster.hr_roster.page.roster.roster.get_departments",
		callback: (r) => (r.message || []).forEach((d) => $dept.append(`<option value="${escape_html(d)}">${escape_html(d)}</option>`)),
	});

	frappe.call({
		method: "employee_roster.hr_roster.page.roster.roster.get_groups",
		callback: (r) => {
			state.groups = r.message || [];
			const $dl = $("#hr-group-options");
			$dl.empty();
			state.groups.forEach((g) => $dl.append(`<option value="${escape_html(g)}">`));
		},
	});

	$kw.on("input", function () {
		clearTimeout(state.search_timer);
		state.search_timer = setTimeout(() => {
			state.keyword = $(this).val().trim();
			update_filter_badge($main, state);
			do_search($main, state);
		}, 300);
	});

	$dept.on("change", function () {
		state.department = $(this).val();
		update_filter_badge($main, state);
		do_search($main, state);
	});

	$status.on("change", function () {
		state.status = $(this).val();
		update_filter_badge($main, state);
		sync_stat_active($main, state.status);
	});

	$main.find(".hr-filter-btn").on("click", function (e) {
		e.stopPropagation();
		$main.find(".hr-filter-popover").toggle();
		$(this).toggleClass("is-active");
	});

	$main.find(".hr-filter-apply").on("click", function () {
		state.status = $status.val();
		update_filter_badge($main, state);
		sync_stat_active($main, state.status);
		$main.find(".hr-filter-popover").hide();
		$main.find(".hr-filter-btn").removeClass("is-active");
		do_search($main, state);
	});

	$main.find(".hr-filter-reset").on("click", function () {
		$kw.val("");
		$dept.val("");
		$status.val("");
		state.keyword = "";
		state.department = "";
		state.status = "";
		update_filter_badge($main, state);
		sync_stat_active($main, "");
		$main.find(".hr-filter-popover").hide();
		$main.find(".hr-filter-btn").removeClass("is-active");
		load_home_data($main, state);
	});

	$(document).on("click.hr-roster-filter", function (e) {
		if (!$(e.target).closest(".hr-filter-left").length) {
			$main.find(".hr-filter-popover").hide();
			$main.find(".hr-filter-btn").removeClass("is-active");
		}
	});

	$main.find(".hr-refresh-btn").on("click", () => load_home_data($main, state));
	$main.find(".hr-add-btn").on("click", () => frappe.new_doc("Employee"));
	$main.find(".hr-import-btn").on("click", () => frappe.set_route("import", "Employee"));
	$main.find(".hr-export-btn").on("click", () => export_csv($main, state));
	$main.find(".hr-more-btn").on("click", () => show_more_menu($main, state));
	update_filter_badge($main, state);
}

function update_filter_badge($main, state) {
	let count = 0;
	if (state.keyword) count += 1;
	if (state.department) count += 1;
	if (state.status) count += 1;
	$main.find(".hr-filter-count").text(count ? ` (${count})` : "");
	$main.find(".hr-filter-btn").toggleClass("has-filter", count > 0);
}

function sync_stat_active($main, status) {
	$main.find(".hr-stat-cell").removeClass("is-active");
	if (status) {
		$main.find(`.hr-stat-cell[data-status="${status}"]`).addClass("is-active");
	} else {
		$main.find('.hr-stat-cell[data-status="Active"]').addClass("is-active");
	}
}

function load_home_data($main, state) {
	frappe.call({
		method: "employee_roster.hr_roster.page.roster.roster.get_roster_data",
		callback: (r) => {
			if (!r.message) return;
			state.rows = r.message.tables || [];
			state.stats = r.message.stats || {};
			state.selected.clear();
			render_stat_board($main, state.stats, state);
			bind_stat_filter($main, state);
			render_table($main, state);
		},
		error: (err) => frappe.msgprint(__("加载员工数据失败：") + ((err && err.message) || err)),
	});
}

function do_search($main, state) {
	frappe.call({
		method: "employee_roster.hr_roster.page.roster.roster.search_employees",
		args: { keyword: state.keyword, department: state.department, status: state.status },
		callback: (r) => {
			state.rows = r.message || [];
			state.selected.clear();
			update_table_count($main, state.rows.length, state.stats);
			render_table($main, state);
		},
		error: (err) => frappe.msgprint(__("查询失败：") + ((err && err.message) || err)),
	});
}

function get_employment_count(stats, key) {
	return (stats.employment_counts && stats.employment_counts[key]) || 0;
}

function stat_cell(label, value, status, extraClass) {
	return `<button type="button" class="hr-stat-cell${extraClass || ""}" data-status="${status || ""}">
		<div class="hr-stat-label">${label}</div>
		<div class="hr-stat-num">${value}<span class="hr-stat-unit">${__("人")}</span></div>
	</button>`;
}

function render_stat_board($main, stats, state) {
	const fulltime = get_employment_count(stats, "Full-time");
	const intern = get_employment_count(stats, "Intern");
	const probation = get_employment_count(stats, "Probation");

	$main.find(".hr-stat-board").html(`
		<div class="hr-stat-card">${stat_cell(__("在职"), stats.active || 0, "Active", " is-green")}</div>
		<div class="hr-stat-card hr-stat-card--split2">
			${stat_cell(__("全职"), fulltime, "", "")}
			${stat_cell(__("实习生"), intern, "", "")}
		</div>
		<div class="hr-stat-card hr-stat-card--split3">
			${stat_cell(__("试用期"), probation, "", "")}
			${stat_cell(__("停用"), stats.inactive || 0, "Inactive", "")}
			${stat_cell(__("正式"), fulltime, "", "")}
		</div>
		<div class="hr-stat-card hr-stat-card--split2">
			${stat_cell(__("待入职") + " ›", 0, "", "")}
			${stat_cell(__("已离职"), stats.left || 0, "Left", "")}
		</div>
	`);
	update_table_count($main, stats.total || 0, stats);
	sync_stat_active($main, (state && state.status) || "");
}

function update_table_count($main, count, stats) {
	const total = (stats && stats.total) || count;
	const text = count !== total ? __("共 {0} / {1} 条", [count, total]) : __("共 {0} 条", [count]);
	$main.find(".hr-table-count").text(text);
}

function bind_stat_filter($main, state) {
	$main.find(".hr-stat-board").off("click").on("click", ".hr-stat-cell[data-status]", function () {
		const st = $(this).attr("data-status");
		if (!st) return;
		state.status = state.status === st ? "" : st;
		$main.find(".hr-status-filter").val(state.status);
		update_filter_badge($main, state);
		sync_stat_active($main, state.status);
		do_search($main, state);
	});
}

function avatar_color(name) {
	let hash = 0;
	for (let i = 0; i < (name || "").length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
	return ["#00b386", "#3b82f6", "#8b5cf6", "#f59e0b", "#ef4444", "#06b6d4"][Math.abs(hash) % 6];
}

function format_cell_value(col, row) {
	const value = row[col.key];
	if (col.type === "checkbox") {
		const checked = row._selected ? "checked" : "";
		return `<input type="checkbox" class="hr-row-check" data-name="${escape_html(row.name)}" ${checked}>`;
	}
	if (col.type === "actions") {
		return `<button type="button" class="hr-quick-edit" data-name="${escape_html(row.name)}">${__("快速编辑")}</button>`;
	}
	if (col.key === "employee_name") {
		const initial = (value || "?").slice(0, 1);
		return `<div class="hr-name-cell"><span class="hr-avatar" style="background:${avatar_color(value)}">${escape_html(initial)}</span><span class="hr-name-text">${escape_html(value || "")}</span></div>`;
	}
	if (value == null || value === "") return '<span class="hr-cell-empty">-</span>';
	if (col.key === "date_of_joining") return escape_html(frappe.datetime.str_to_user(value) || value);
	if (col.key === "employment_type") return escape_html(HR_EMPLOYMENT_LABELS[value] || value);
	if (col.key === "status") {
		const label = HR_STATUS_LABELS[value] || value;
		return `<span class="hr-status-pill ${HR_STATUS_CLASS[value] || "status-left"}">${escape_html(label)}</span>`;
	}
	return escape_html(value);
}

function render_table($main, state) {
	const defs = state.column_defs;
	const $thead = $main.find("thead").empty();
	const headTr = $("<tr></tr>");
	defs.forEach((col) => {
		const sticky = col.sticky ? " hr-col-sticky" : "";
		const style = col.width ? `width:${col.width}` : col.minWidth ? `min-width:${col.minWidth}` : "";
		if (col.type === "checkbox") {
			headTr.append(`<th class="hr-col-check${sticky}" style="${style}"><input type="checkbox" class="hr-check-all"></th>`);
			return;
		}
		const editMark = col.editable ? `<span class="hr-edit-ico" title="${__("可双击编辑")}">✎</span>` : "";
		headTr.append(`<th class="${sticky.trim()}" style="${style}">${col.label}${editMark}</th>`);
	});
	$thead.append(headTr);

	const $tbody = $main.find("tbody").empty();
	if (!state.rows.length) {
		$tbody.append(`<tr><td colspan="${defs.length}" class="hr-empty-row">${__("暂无符合条件的员工")}</td></tr>`);
		bind_table_events($main, state);
		return;
	}
	state.rows.forEach((row) => {
		row._selected = state.selected.has(row.name);
		const tr = $("<tr></tr>").attr("data-name", row.name || "");
		defs.forEach((col) => {
			const cls = [
				col.editable ? "hr-cell-editable" : "hr-cell-readonly",
				col.type === "checkbox" ? "hr-col-check" : "",
				col.type === "actions" ? "hr-col-actions hr-col-sticky" : "",
				col.sticky ? "hr-col-sticky" : "",
			].filter(Boolean).join(" ");
			const style = col.width ? `width:${col.width}` : col.minWidth ? `min-width:${col.minWidth}` : "";
			tr.append(`<td class="${cls}" data-key="${col.key}" data-name="${escape_html(row.name || "")}" style="${style}">${format_cell_value(col, row)}</td>`);
		});
		$tbody.append(tr);
	});
	bind_table_events($main, state);
}

function bind_table_events($main, state) {
	$main.find(".hr-check-all").off("change").on("change", function () {
		const checked = $(this).is(":checked");
		state.selected.clear();
		if (checked) state.rows.forEach((r) => state.selected.add(r.name));
		render_table($main, state);
	});
	$main.find(".hr-row-check").off("change").on("change", function () {
		const name = $(this).attr("data-name");
		if ($(this).is(":checked")) state.selected.add(name);
		else state.selected.delete(name);
	});
	$main.find(".hr-quick-edit").off("click").on("click", function () {
		const name = $(this).attr("data-name");
		if (name) frappe.set_route("Form", "Employee", name);
	});
	$main.find("tbody").off("dblclick").on("dblclick", ".hr-cell-editable", function () {
		const $td = $(this);
		const col = state.column_defs.find((c) => c.key === $td.attr("data-key"));
		start_edit($main, state, $td, $td.attr("data-name"), col);
	});
}

function get_cell_raw_value($td, col) {
	if (col.key === "status") {
		const text = $td.find(".hr-status-pill").text().trim();
		return Object.keys(HR_STATUS_LABELS).find((k) => HR_STATUS_LABELS[k] === text) || text;
	}
	return $td.text().trim().replace(/^-$/, "");
}

function start_edit($main, state, $td, name, col) {
	if (!col || !name) return;
	const cur = get_cell_raw_value($td, col);
	let editor;
	if (col.inputType === "select") {
		editor = $("<select class='hr-cell-input'></select>");
		(col.options || []).forEach((o) => editor.append(`<option value="${o}" ${o === cur ? "selected" : ""}>${HR_STATUS_LABELS[o] || o}</option>`));
	} else if (col.inputType === "datalist") {
		editor = $(`<input type="text" class="hr-cell-input" list="${col.datalist}">`).val(cur);
	} else {
		editor = $("<input type='text' class='hr-cell-input'>").val(cur);
	}
	$td.empty().append(editor);
	const finish = (save) => {
		const val = (editor.val() || "").toString().trim();
		if (!save || val === cur) {
			const row = state.rows.find((x) => x.name === name);
			$td.html(format_cell_value(col, row || {}));
			return;
		}
		const err = validate_value(col, val);
		if (err) {
			editor.addClass("has-error");
			frappe.show_alert({ message: err, indicator: "red" });
			return editor.focus();
		}
		save_edit($main, state, name, col.key, val);
	};
	editor.on("blur", () => finish(true));
	editor.on("keydown", (e) => {
		if (e.key === "Enter") { e.preventDefault(); finish(true); }
		else if (e.key === "Escape") finish(false);
	});
	editor.focus();
	if (editor.is("input")) editor.select();
}

function validate_value(col, val) {
	if (col.validate === "mobile" && val && !/^1[3-9]\d{9}$/.test(val)) {
		return __("手机号格式不正确，应为 1 开头的 11 位数字");
	}
	return null;
}

function save_edit($main, state, name, field, value) {
	frappe.call({
		method: "employee_roster.hr_roster.page.roster.roster.update_employee_fields",
		args: { employee: name, field, value },
		callback: (r) => {
			if (!r.message?.ok) return;
			frappe.show_alert({ message: __("已保存"), indicator: "green" });
			const row = state.rows.find((x) => x.name === name);
			if (row) row[field] = value;
			const col = state.column_defs.find((c) => c.key === field);
			$main.find(`tbody td[data-name="${name}"][data-key="${field}"]`).html(format_cell_value(col, row));
			if (field === "group_name" && value && !state.groups.includes(value)) {
				state.groups.push(value);
				state.groups.sort();
				$("#hr-group-options").append(`<option value="${escape_html(value)}">`);
			}
		},
		error: () => refresh_row($main, state, name),
	});
}

function refresh_row($main, state, name) {
	const row = state.rows.find((x) => x.name === name);
	if (!row) return;
	state.column_defs.forEach((col) => {
		if (!col.key.startsWith("_")) {
			$main.find(`tbody td[data-name="${name}"][data-key="${col.key}"]`).html(format_cell_value(col, row));
		}
	});
}

function export_csv($main, state) {
	const defs = state.column_defs.filter((c) => !c.key.startsWith("_"));
	let csv = "\uFEFF" + defs.map((c) => c.label).join(",") + "\n";
	state.rows.forEach((row) => {
		csv += defs.map((c) => {
			let v = row[c.key] || "";
			if (c.key === "status") v = HR_STATUS_LABELS[v] || v;
			if (c.key === "employment_type") v = HR_EMPLOYMENT_LABELS[v] || v;
			return `"${String(v).replace(/"/g, '""')}"`;
		}).join(",") + "\n";
	});
	const link = document.createElement("a");
	link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" }));
	link.download = "员工花名册.csv";
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
}

function show_more_menu($main, state) {
	$main.find(".hr-more-menu").remove();
	const items = [
		{ label: __("刷新数据"), action: () => load_home_data($main, state) },
		{ label: __("打开员工列表"), action: () => frappe.set_route("List", "Employee") },
	];
	const dropdown = $("<div class='hr-more-menu'></div>");
	items.forEach((it) => dropdown.append(`<button type='button' class='hr-more-item'>${it.label}</button>`));
	$main.find(".hr-more-btn").parent().append(dropdown);
	dropdown.on("click", ".hr-more-item", function () {
		items[$(this).index()].action();
		dropdown.remove();
	});
	setTimeout(() => $(document).one("click", () => dropdown.remove()), 0);
}

function escape_html(s) {
	return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
