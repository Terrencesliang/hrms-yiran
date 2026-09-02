// Copyright (c) 2026 stillgroup
// License: MIT — shared helpers for 已入职 / 已淘汰 list pages

function ensure_recruiting_styles() {
	if (document.getElementById("recruiting-stylesheet")) return;
	const link = document.createElement("link");
	link.id = "recruiting-stylesheet";
	link.rel = "stylesheet";
	link.href = `/assets/employee_roster/css/recruiting.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

function init_recruiting_list_page(wrapper, cfg) {
	ensure_recruiting_styles();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: cfg.title,
		single_column: true,
	});

	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty().addClass("recruiting-page recruiting-list-page");
	$main.html(`
		<div class="recruiting-list-toolbar-top">
			<div class="recruiting-list-search-wrap">
				<input class="recruiting-search recruiting-list-search" type="text" placeholder="${__("搜索候选人/人才库")}">
				<button class="btn btn-default btn-sm recruiting-filter-toggle" type="button" title="${__("筛选")}">▾</button>
			</div>
			<button class="btn btn-primary btn-sm recruiting-add-btn" type="button">+ ${__("添加候选人")}</button>
		</div>
		<div class="recruiting-list-filters hidden">
			<select class="recruiting-company"></select>
			<select class="recruiting-job"></select>
		</div>
		<div class="recruiting-list-card">
			<div class="recruiting-list-toolbar">
				<div class="recruiting-list-toolbar-left">
					<div class="recruiting-pagination"></div>
					<label class="recruiting-select-all">
						<input type="checkbox" class="recruiting-check-all"> ${__("全选本页")}
					</label>
				</div>
				<div class="recruiting-list-toolbar-right">
					<button class="btn btn-link btn-sm recruiting-refresh" type="button">${__("刷新")}</button>
					<select class="recruiting-sort">
						<option value="modified desc">${__("按最近操作时间排序")}</option>
						<option value="creation desc">${__("按创建时间排序")}</option>
						<option value="name asc">${__("按姓名排序")}</option>
					</select>
					<button class="btn btn-default btn-sm recruiting-export" type="button">${__("导出")}</button>
				</div>
			</div>
			<div class="recruiting-card-list"></div>
		</div>
	`);

	const state = {
		status: cfg.status,
		company: "",
		job_opening: "",
		keyword: "",
		sort_by: "modified desc",
		page: 1,
		page_size: 20,
		timer: null,
		selected: new Set(),
		last_rows: [],
	};
	bind_list_events($main, state);
	load_list_data($main, state);
}

function bind_list_events($main, state) {
	$main.find(".recruiting-filter-toggle").on("click", () => {
		$main.find(".recruiting-list-filters").toggleClass("hidden");
	});
	$main.find(".recruiting-company").on("change", function () {
		state.company = $(this).val() || "";
		state.page = 1;
		load_list_data($main, state);
	});
	$main.find(".recruiting-job").on("change", function () {
		state.job_opening = $(this).val() || "";
		state.page = 1;
		load_list_data($main, state);
	});
	$main.find(".recruiting-list-search").on("input", function () {
		state.keyword = $(this).val() || "";
		state.page = 1;
		clearTimeout(state.timer);
		state.timer = setTimeout(() => load_list_data($main, state), 300);
	});
	$main.find(".recruiting-sort").on("change", function () {
		state.sort_by = $(this).val();
		state.page = 1;
		load_list_data($main, state);
	});
	$main.find(".recruiting-refresh").on("click", () => load_list_data($main, state));
	$main.find(".recruiting-add-btn").on("click", () => frappe.new_doc("Job Applicant", { status: "Open" }));
	$main.find(".recruiting-export").on("click", () => export_candidates(state.last_rows, state.status));
	$main.on("click", ".recruiting-page-btn", function () {
		const p = parseInt($(this).attr("data-page"), 10);
		if (!p || p === state.page) return;
		state.page = p;
		load_list_data($main, state);
	});
	$main.on("change", ".recruiting-check-all", function () {
		const checked = $(this).is(":checked");
		$main.find(".recruiting-card-check").prop("checked", checked);
		state.selected.clear();
		if (checked) state.last_rows.forEach((r) => state.selected.add(r.name));
	});
	$main.on("change", ".recruiting-card-check", function () {
		const name = $(this).closest(".recruiting-card").attr("data-name");
		if ($(this).is(":checked")) state.selected.add(name);
		else state.selected.delete(name);
		sync_select_all($main, state);
	});
	$main.on("click", ".recruiting-card-main", function (e) {
		if ($(e.target).closest("input,button,a").length) return;
		frappe.set_route("Form", "Job Applicant", $(this).closest(".recruiting-card").attr("data-name"));
	});
	$main.on("click", ".recruiting-card-view", function () {
		frappe.set_route("Form", "Job Applicant", $(this).closest(".recruiting-card").attr("data-name"));
	});
}

function load_list_data($main, state) {
	frappe.call({
		method: "employee_roster.hr_roster.page.recruiting_list.recruiting_list.get_candidates",
		args: {
			status: state.status,
			company: state.company || null,
			job_opening: state.job_opening || null,
			keyword: state.keyword || null,
			sort_by: state.sort_by,
			page: state.page,
			page_size: state.page_size,
		},
		callback(r) {
			if (!r.message) return;
			render_list_filters($main, r.message, state);
			state.last_rows = r.message.candidates || [];
			render_pagination($main, r.message, state);
			render_card_list($main, state.last_rows, r.message.total || 0);
			sync_select_all($main, state);
		},
	});
}

function render_list_filters($main, data, state) {
	const $company = $main.find(".recruiting-company");
	if (!$company.data("filled")) {
		$company.append(`<option value="">${__("不限公司")}</option>`);
		(data.companies || []).forEach((c) => $company.append(`<option value="${esc(c)}">${esc(c)}</option>`));
		$company.data("filled", true);
	}
	$company.val(state.company || "");

	const $job = $main.find(".recruiting-job");
	$job.empty().append(`<option value="">${__("不限职位")}</option>`);
	(data.job_openings || []).forEach((j) => {
		if (state.company && j.company !== state.company) return;
		const label = j.job_title || j.name;
		$job.append(`<option value="${esc(j.name)}">${esc(label)}</option>`);
	});
	$job.val(state.job_opening || "");
}

function render_pagination($main, data, state) {
	const page = data.page || 1;
	const pageCount = data.page_count || 1;
	const total = data.total || 0;
	let html = `<span class="recruiting-count">${__("共")} ${total} ${__("位")}</span>`;
	html += `<button class="btn btn-link btn-sm recruiting-page-btn" data-page="${page - 1}" ${page <= 1 ? "disabled" : ""}>&lt;</button>`;
	html += `<span class="recruiting-page-num">${page} / ${pageCount}</span>`;
	html += `<button class="btn btn-link btn-sm recruiting-page-btn" data-page="${page + 1}" ${page >= pageCount ? "disabled" : ""}>&gt;</button>`;
	$main.find(".recruiting-pagination").html(html);
}

function render_card_list($main, rows, total) {
	const $list = $main.find(".recruiting-card-list");
	if (!rows.length) {
		$list.html(`<div class="recruiting-empty"><div class="recruiting-empty-icon">📭</div>${__("暂无符合条件的候选人")}</div>`);
		return;
	}

	$list.html(
		rows
			.map((row) => {
				const initial = (row.applicant_name || "?").charAt(0);
				const tags = [
					row.job_label && `<span class="recruiting-tag recruiting-tag-job">${esc(row.job_label)}</span>`,
					row.source && `<span class="recruiting-tag">${esc(row.source)}</span>`,
					`<span class="recruiting-tag recruiting-tag-status">${esc(row.status_label || row.status)}</span>`,
				]
					.filter(Boolean)
					.join("");
				const sub = [row.email_id, row.phone_number].filter(Boolean).join(" · ") || "-";
				return `
				<div class="recruiting-card" data-name="${esc(row.name)}">
					<input type="checkbox" class="recruiting-card-check">
					<div class="recruiting-card-avatar">${esc(initial)}</div>
					<div class="recruiting-card-main">
						<div class="recruiting-card-name">${esc(row.applicant_name)}</div>
						<div class="recruiting-card-tags">${tags}</div>
						<div class="recruiting-card-sub">${esc(sub)}</div>
					</div>
					<button class="btn btn-default btn-sm recruiting-card-view" type="button">${__("查看")}</button>
				</div>`;
			})
			.join("")
	);
}

function sync_select_all($main, state) {
	const $checks = $main.find(".recruiting-card-check");
	const all = $checks.length && $checks.filter(":checked").length === $checks.length;
	$main.find(".recruiting-check-all").prop("checked", all);
}

function export_candidates(rows, status) {
	if (!rows.length) {
		frappe.show_alert({ message: __("暂无数据可导出"), indicator: "orange" });
		return;
	}
	const header = [__("姓名"), __("应聘职位"), __("岗位"), __("状态"), __("邮箱"), __("手机"), __("来源")];
	const lines = [header.join(",")];
	rows.forEach((r) => {
		lines.push(
			[r.applicant_name, r.job_label, r.designation, r.status_label, r.email_id, r.phone_number, r.source]
				.map(csv_cell)
				.join(",")
		);
	});
	const blob = new Blob(["\ufeff" + lines.join("\n")], { type: "text/csv;charset=utf-8;" });
	const a = document.createElement("a");
	a.href = URL.createObjectURL(blob);
	a.download = `${status === "Accepted" ? "hired" : "rejected"}_candidates.csv`;
	a.click();
}

function csv_cell(v) {
	const s = String(v == null ? "" : v);
	return s.includes(",") || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
}

function esc(s) {
	return String(s == null ? "" : s)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;");
}
