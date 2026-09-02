// Copyright (c) 2026 stillgroup
// License: MIT

function ensure_recruiting_styles() {
	if (document.getElementById("recruiting-stylesheet")) return;
	const link = document.createElement("link");
	link.id = "recruiting-stylesheet";
	link.rel = "stylesheet";
	link.href = `/assets/employee_roster/css/recruiting.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["recruiting-active"].on_page_load = function (wrapper) {
	ensure_recruiting_styles();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("招聘中"),
		single_column: true,
	});

	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();
	$main.addClass("recruiting-page");
	$main.html(`
		<div class="recruiting-toolbar">
			<div class="recruiting-toolbar-left">
				<select class="recruiting-company"></select>
				<select class="recruiting-job"></select>
				<input class="recruiting-search" type="text" placeholder="${__("搜索候选人/人才库")}">
			</div>
			<div class="recruiting-toolbar-right">
				<button class="btn btn-primary btn-sm recruiting-add-btn" type="button">+ ${__("添加候选人")}</button>
			</div>
		</div>
		<div class="recruiting-pipeline"></div>
		<div class="recruiting-list-card">
			<div class="recruiting-list-toolbar">
				<span class="recruiting-count"></span>
				<button class="btn btn-link btn-sm recruiting-refresh" type="button">${__("刷新")}</button>
			</div>
			<div class="recruiting-table-scroll">
				<table class="recruiting-table">
					<thead></thead>
					<tbody></tbody>
				</table>
			</div>
		</div>
	`);

	const state = { company: "", job_opening: "", keyword: "", timer: null };
	bind_events($main, state);
	load_data($main, state);
};

function bind_events($main, state) {
	$main.find(".recruiting-company").on("change", function () {
		state.company = $(this).val() || "";
		load_data($main, state);
	});
	$main.find(".recruiting-job").on("change", function () {
		state.job_opening = $(this).val() || "";
		load_data($main, state);
	});
	$main.find(".recruiting-search").on("input", function () {
		state.keyword = $(this).val() || "";
		clearTimeout(state.timer);
		state.timer = setTimeout(() => load_data($main, state), 300);
	});
	$main.find(".recruiting-refresh").on("click", () => load_data($main, state));
	$main.find(".recruiting-add-btn").on("click", () => frappe.new_doc("Job Applicant", { status: "Open" }));
}

function load_data($main, state) {
	frappe.call({
		method: "employee_roster.hr_roster.page.recruiting_active.recruiting_active.get_recruiting_pipeline",
		args: {
			company: state.company || null,
			job_opening: state.job_opening || null,
			keyword: state.keyword || null,
		},
		callback(r) {
			if (!r.message) return;
			render_filters($main, r.message, state);
			render_pipeline($main, r.message.pipeline || {});
			render_table($main, r.message.candidates || [], r.message.total || 0);
		},
	});
}

function render_filters($main, data, state) {
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

function render_pipeline($main, pipeline) {
	const stages = ["screening", "interview", "offer"];
	const html = stages
		.map((key) => {
			const stage = pipeline[key];
			if (!stage) return "";
			const items = (stage.items || [])
				.map((it) => `<div class="recruiting-stage-item"><span>${esc(it.label)}</span><strong>${it.count || 0}</strong></div>`)
				.join("");
			return `<div class="recruiting-stage-card"><div class="recruiting-stage-title">${esc(stage.label)}</div><div class="recruiting-stage-items">${items}</div></div>`;
		})
		.join("");
	$main.find(".recruiting-pipeline").html(html);
}

function render_table($main, rows, total) {
	$main.find(".recruiting-count").text(`${__("共")} ${total} ${__("位候选人")}`);
	const head = `
		<tr>
			<th>${__("姓名")}</th>
			<th>${__("应聘职位")}</th>
			<th>${__("岗位")}</th>
			<th>${__("状态")}</th>
			<th>${__("邮箱")}</th>
			<th>${__("手机")}</th>
		</tr>`;
	const body = rows.length
		? rows
				.map(
					(row) => `
			<tr data-name="${esc(row.name)}" class="recruiting-row" style="cursor:pointer">
				<td>${esc(row.applicant_name)}</td>
				<td>${esc(row.job_title || "-")}</td>
				<td>${esc(row.designation || "-")}</td>
				<td><span class="recruiting-status">${esc(row.status_label || row.status)}</span></td>
				<td>${esc(row.email_id || "-")}</td>
				<td>${esc(row.phone_number || "-")}</td>
			</tr>`
				)
				.join("")
		: `<tr><td colspan="6"><div class="recruiting-empty"><div class="recruiting-empty-icon">📭</div>${__("暂无符合条件的候选人")}</div></td></tr>`;

	$main.find(".recruiting-table thead").html(head);
	$main.find(".recruiting-table tbody").html(body);
	$main.find(".recruiting-row").on("click", function () {
		frappe.set_route("Form", "Job Applicant", $(this).attr("data-name"));
	});
}

function esc(s) {
	return String(s == null ? "" : s)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;");
}
