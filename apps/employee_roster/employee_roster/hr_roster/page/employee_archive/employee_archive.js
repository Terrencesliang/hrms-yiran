// Copyright (c) 2026 stillgroup
// License: MIT

const ARCHIVE_API = "employee_roster.hr_roster.page.employee_archive.employee_archive";

const ARCHIVE_TABS = [
	{ key: "overview", label: () => __("员工档案概况") },
	{ key: "education", label: () => __("教育经历") },
	{ key: "work", label: () => __("工作经历") },
	{ key: "documents", label: () => __("证书/证件") },
	{ key: "emergency", label: () => __("紧急联系人") },
	{ key: "skills", label: () => __("工作技能") },
];

function ensure_archive_styles() {
	if (document.getElementById("hr-archive-stylesheet")) return;
	const link = document.createElement("link");
	link.id = "hr-archive-stylesheet";
	link.rel = "stylesheet";
	link.href = `/assets/employee_roster/css/archive.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["employee-archive"].on_page_load = function (wrapper) {
	ensure_archive_styles();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("员工档案库"),
		single_column: true,
	});

	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const page = wrapper.page;
	const $main = page.main;
	$main.empty().addClass("hr-archive-page");

	const state = {
		tab: "overview",
		department: "",
		doc_status: "",
		document_type: "",
		missing_only: false,
		overview: null,
	};

	const tab_html = ARCHIVE_TABS.map(
		(tab, idx) =>
			`<button type="button" class="hr-archive-tab${idx === 0 ? " is-active" : ""}" data-tab="${tab.key}">${tab.label()}</button>`
	).join("");

	$main.html(`
		<div class="hr-archive-shell">
			<div class="hr-archive-tabs">${tab_html}</div>
			<div class="hr-archive-toolbar">
				<div class="hr-archive-toolbar-left">
					<label class="hr-archive-filter">
						<span>${__("部门")}:</span>
						<select class="hr-archive-dept"></select>
					</label>
					<label class="hr-archive-filter hr-archive-filter--status">
						<span>${__("员工状态")}:</span>
						<select class="hr-archive-status">
							<option value="">${__("全部")}</option>
							<option value="Active">${__("在职")}</option>
							<option value="Left">${__("离职")}</option>
						</select>
					</label>
					<label class="hr-archive-filter hr-archive-filter--docs">
						<span>${__("材料类型")}:</span>
						<select class="hr-archive-doc-type"></select>
					</label>
					<label class="hr-archive-filter hr-archive-filter--docs">
						<input type="checkbox" class="hr-archive-missing-only">
						<span>${__("仅缺档")}</span>
					</label>
				</div>
				<div class="hr-archive-toolbar-right">
					<button type="button" class="btn btn-primary btn-sm hr-archive-upload-btn">${__("上传材料")}</button>
					<button type="button" class="btn btn-default btn-sm hr-archive-export-btn">${__("导出缺档")}</button>
					<button type="button" class="btn btn-default btn-sm hr-archive-refresh-btn">${__("刷新")}</button>
				</div>
			</div>
			<div class="hr-archive-panel"></div>
		</div>
	`);

	init_archive_page($main, state);
};

function init_archive_page($main, state) {
	load_departments($main);
	bind_archive_events($main, state);
	parse_route_filters(state);
	switch_archive_tab($main, state, state.tab);
}

function parse_route_filters(state) {
	const route = frappe.get_route();
	if (route.length > 1 && ARCHIVE_TABS.some((t) => t.key === route[1])) {
		state.tab = route[1];
	}
	const opts = frappe.utils.get_query_params();
	if (opts.document_type) state.document_type = opts.document_type;
	if (opts.missing_only) state.missing_only = true;
}

function load_departments($main) {
	const $dept = $main.find(".hr-archive-dept");
	$dept.html(`<option value="">${__("全部")}</option>`);
	frappe.call({
		method: `${ARCHIVE_API}.get_departments`,
		callback: (r) => (r.message || []).forEach((d) => $dept.append(`<option value="${escape_html(d)}">${escape_html(d)}</option>`)),
	});
}

function bind_archive_events($main, state) {
	$main.on("click", ".hr-archive-tab", function () {
		switch_archive_tab($main, state, $(this).data("tab"));
	});

	$main.find(".hr-archive-dept").on("change", function () {
		state.department = $(this).val();
		reload_archive($main, state);
	});

	$main.find(".hr-archive-status").on("change", function () {
		state.doc_status = $(this).val();
		reload_archive($main, state);
	});

	$main.find(".hr-archive-doc-type, .hr-archive-missing-only").on("change", function () {
		state.document_type = $main.find(".hr-archive-doc-type").val();
		state.missing_only = $main.find(".hr-archive-missing-only").is(":checked");
		if (state.tab === "documents") load_documents($main, state);
	});

	$main.find(".hr-archive-refresh-btn").on("click", () => reload_archive($main, state));
	$main.find(".hr-archive-export-btn").on("click", () => export_missing($main, state));
	$main.find(".hr-archive-upload-btn").on("click", () => open_upload_dialog($main, state));

	$main.on("click", ".hr-archive-go-upload", function () {
		state.document_type = $(this).data("document-type");
		switch_archive_tab($main, state, "documents");
		$main.find(".hr-archive-doc-type").val(state.document_type);
		load_documents($main, state);
	});

	$main.on("click", ".hr-archive-upload-row", function () {
		open_upload_dialog($main, state, {
			employee: $(this).data("employee"),
			document_type: $(this).data("document-type"),
		});
	});

	$main.on("click", ".hr-archive-open-employee", function () {
		frappe.set_route("Form", "Employee", $(this).data("employee"));
	});
}

function switch_archive_tab($main, state, tab) {
	state.tab = tab;
	$main.find(".hr-archive-tab").removeClass("is-active");
	$main.find(`.hr-archive-tab[data-tab="${tab}"]`).addClass("is-active");

	const isOverview = tab === "overview";
	const isDocuments = tab === "documents";
	$main.find(".hr-archive-filter--status").toggle(!isOverview);
	$main.find(".hr-archive-filter--docs").toggle(isDocuments);
	$main.find(".hr-archive-upload-btn, .hr-archive-export-btn").toggle(isDocuments);
	reload_archive($main, state);
}

function reload_archive($main, state) {
	const loaders = {
		overview: load_overview,
		education: load_education,
		work: load_work,
		documents: load_documents,
		emergency: load_emergency,
		skills: load_skills,
	};
	(loaders[state.tab] || load_overview)($main, state);
}

function archive_panel($main) {
	return $main.find(".hr-archive-panel");
}

function show_loading($panel) {
	$panel.html(`<div class="hr-archive-loading">${__("加载中…")}</div>`);
}

function show_error($panel, err) {
	const msg = (err && (err.message || err.exc || err.responseText)) || __("加载失败");
	$panel.html(`<div class="hr-archive-error">${escape_html(String(msg))}</div>`);
}

function render_table_card($panel, rows, columns, count_label) {
	const body = rows.length
		? rows
				.map((row) => `<tr>${columns.map((col) => `<td>${col.render(row)}</td>`).join("")}</tr>`)
				.join("")
		: `<tr><td colspan="${columns.length}" class="hr-archive-empty">${__("暂无数据")}</td></tr>`;

	$panel.html(`
		<div class="hr-archive-table-card">
			<div class="hr-archive-table-meta">${count_label || `${__("共")} ${rows.length} ${__("条")}`}</div>
			<div class="hr-archive-table-scroll">
				<table class="table table-bordered hr-archive-table">
					<thead><tr>${columns.map((col) => `<th>${col.label}</th>`).join("")}</tr></thead>
					<tbody>${body}</tbody>
				</table>
			</div>
		</div>
	`);
}

function employee_edit_col() {
	return {
		label: __("操作"),
		render: (row) =>
			`<button type="button" class="btn btn-link btn-sm hr-archive-open-employee" data-employee="${escape_html(row.employee)}">${__("编辑档案")}</button>`,
	};
}

function load_overview($main, state) {
	const $panel = archive_panel($main);
	show_loading($panel);
	frappe.call({
		method: `${ARCHIVE_API}.get_archive_overview`,
		args: { department: state.department || "" },
		callback: (r) => {
			state.overview = r.message;
			populate_doc_type_filter($main, state, r.message?.document_types || []);
			render_overview($panel, state.overview);
		},
		error: (err) => show_error($panel, err),
	});
}

function populate_doc_type_filter($main, state, types) {
	const $sel = $main.find(".hr-archive-doc-type");
	if ($sel.data("loaded")) return;
	$sel.html(`<option value="">${__("全部")}</option>`);
	types.forEach((t) => $sel.append(`<option value="${escape_html(t.name)}">${escape_html(t.document_name)}</option>`));
	$sel.data("loaded", true);
	if (state.document_type) $sel.val(state.document_type);
}

function render_overview($panel, data) {
	if (!data) return;
	$panel.html(`
		<div class="hr-archive-overview-grid">
			${render_overview_column(__("在职员工"), data.active)}
			${render_overview_column(__("离职员工"), data.left)}
		</div>
	`);
}

function render_overview_column(title, block) {
	const storage = format_bytes(block.storage_bytes || 0);
	return `
		<div class="hr-archive-column">
			<div class="hr-archive-column-title">${title}</div>
			<div class="hr-archive-metrics">
				<div class="hr-archive-metric"><span>${__("人数")}</span><strong>${block.total || 0}</strong></div>
				<div class="hr-archive-metric"><span>${__("存档人数")}</span><strong>${block.archived_count || 0}</strong></div>
				<div class="hr-archive-metric"><span>${__("材料份数")}</span><strong>${block.material_count || 0}</strong></div>
				<div class="hr-archive-metric"><span>${__("占用空间")}</span><strong>${storage}</strong></div>
			</div>
			<div class="hr-archive-rates">
				<div class="hr-archive-rate-card">
					<div class="hr-archive-donut" style="--rate:${block.archive_rate || 0}"><span>${block.archive_rate || 0}%</span></div>
					<div class="hr-archive-rate-label">${__("存档率")}</div>
				</div>
				<div class="hr-archive-rate-card">
					<div class="hr-archive-donut hr-archive-donut--info" style="--rate:${block.info_completeness_rate || 0}"><span>${block.info_completeness_rate || 0}%</span></div>
					<div class="hr-archive-rate-label">${__("信息完整度")}</div>
				</div>
			</div>
			<div class="hr-archive-progress-list">
				${(block.progress || []).map((p) => render_progress_row(p)).join("")}
			</div>
		</div>`;
}

function render_progress_row(item) {
	return `
		<div class="hr-archive-progress-row">
			<div class="hr-archive-progress-head">
				<span>${escape_html(item.document_name)}</span>
				<span>${item.rate || 0}%</span>
			</div>
			<div class="hr-archive-progress-bar"><i style="width:${item.rate || 0}%"></i></div>
			<button type="button" class="btn btn-link btn-sm hr-archive-go-upload" data-document-type="${escape_html(item.document_type)}">${__("去上传")}</button>
		</div>`;
}

function list_args(state) {
	return {
		department: state.department || "",
		status: state.doc_status || "",
	};
}

function load_education($main, state) {
	const $panel = archive_panel($main);
	show_loading($panel);
	frappe.call({
		method: `${ARCHIVE_API}.list_education_records`,
		args: list_args(state),
		callback: (r) => {
			const rows = r.message || [];
			render_table_card($panel, rows, [
				{ label: __("姓名"), render: (row) => escape_html(row.employee_name) },
				{ label: __("工号"), render: (row) => escape_html(row.employee_number || "") },
				{ label: __("部门"), render: (row) => escape_html(row.department || "") },
				{ label: __("学校"), render: (row) => escape_html(row.school_univ || "") },
				{ label: __("学历"), render: (row) => escape_html(row.qualification || row.level || "") },
				{ label: __("毕业年份"), render: (row) => escape_html(row.year_of_passing || "") },
				{ label: __("专业"), render: (row) => escape_html(row.maj_opt_subj || "") },
				employee_edit_col(),
			]);
		},
		error: (err) => show_error($panel, err),
	});
}

function load_work($main, state) {
	const $panel = archive_panel($main);
	show_loading($panel);
	frappe.call({
		method: `${ARCHIVE_API}.list_work_history`,
		args: list_args(state),
		callback: (r) => {
			const rows = r.message || [];
			render_table_card($panel, rows, [
				{ label: __("姓名"), render: (row) => escape_html(row.employee_name) },
				{ label: __("类型"), render: (row) => escape_html(row.history_type || "") },
				{ label: __("公司/组织"), render: (row) => escape_html(row.organization || "") },
				{ label: __("岗位"), render: (row) => escape_html(row.designation || "") },
				{ label: __("期间"), render: (row) => escape_html(row.period || "") },
				employee_edit_col(),
			]);
		},
		error: (err) => show_error($panel, err),
	});
}

function load_emergency($main, state) {
	const $panel = archive_panel($main);
	show_loading($panel);
	frappe.call({
		method: `${ARCHIVE_API}.list_emergency_contacts`,
		args: list_args(state),
		callback: (r) => {
			const rows = r.message || [];
			render_table_card($panel, rows, [
				{ label: __("姓名"), render: (row) => escape_html(row.employee_name) },
				{ label: __("工号"), render: (row) => escape_html(row.employee_number || "") },
				{ label: __("部门"), render: (row) => escape_html(row.department || "") },
				{ label: __("联系人"), render: (row) => escape_html(row.contact_name || "") },
				{ label: __("电话"), render: (row) => escape_html(row.contact_phone || "") },
				{ label: __("关系"), render: (row) => escape_html(row.relation || "") },
				{
					label: __("状态"),
					render: (row) =>
						`<span class="hr-archive-status-pill ${row.is_complete ? "is-uploaded" : "is-pending"}">${row.is_complete ? __("已填写") : __("未填写")}</span>`,
				},
				employee_edit_col(),
			]);
		},
		error: (err) => show_error($panel, err),
	});
}

function load_skills($main, state) {
	const $panel = archive_panel($main);
	show_loading($panel);
	frappe.call({
		method: `${ARCHIVE_API}.list_skill_records`,
		args: list_args(state),
		callback: (r) => {
			const rows = r.message || [];
			render_table_card($panel, rows, [
				{ label: __("姓名"), render: (row) => escape_html(row.employee_name) },
				{ label: __("工号"), render: (row) => escape_html(row.employee_number || "") },
				{ label: __("部门"), render: (row) => escape_html(row.department || "") },
				{ label: __("技能"), render: (row) => escape_html(row.skill || "") },
				{ label: __("熟练度"), render: (row) => escape_html(row.proficiency || "") },
				{ label: __("评估日期"), render: (row) => escape_html(row.evaluation_date || "") },
				employee_edit_col(),
			]);
		},
		error: (err) => show_error($panel, err),
	});
}

function load_documents($main, state) {
	const $panel = archive_panel($main);
	show_loading($panel);
	frappe.call({
		method: `${ARCHIVE_API}.list_archive_documents`,
		args: {
			department: state.department || "",
			status: state.doc_status || "",
			document_type: state.document_type || "",
			missing_only: state.missing_only ? 1 : 0,
		},
		callback: (r) => {
			const rows = r.message || [];
			render_table_card($panel, rows, [
				{ label: __("姓名"), render: (row) => escape_html(row.employee_name) },
				{ label: __("工号"), render: (row) => escape_html(row.employee_number || "") },
				{ label: __("部门"), render: (row) => escape_html(row.department || "") },
				{ label: __("材料类型"), render: (row) => escape_html(row.document_name) },
				{
					label: __("状态"),
					render: (row) =>
						`<span class="hr-archive-status-pill ${row.has_file ? "is-uploaded" : "is-pending"}">${row.has_file ? __("已上传") : __("未上传")}</span>`,
				},
				{
					label: __("附件"),
					render: (row) => (row.file ? `<a href="${escape_html(row.file)}" target="_blank">${__("查看")}</a>` : "-"),
				},
				{
					label: __("上传时间"),
					render: (row) => (row.uploaded_on ? frappe.datetime.str_to_user(row.uploaded_on) : "-"),
				},
				{
					label: __("操作"),
					render: (row) =>
						`<button type="button" class="btn btn-link btn-sm hr-archive-upload-row" data-employee="${escape_html(row.employee)}" data-document-type="${escape_html(row.document_type)}">${row.has_file ? __("重新上传") : __("上传")}</button>`,
				},
			]);
		},
		error: (err) => show_error($panel, err),
	});
}

function open_upload_dialog($main, state, preset = {}) {
	const dialog = new frappe.ui.Dialog({
		title: __("上传档案材料"),
		fields: [
			{ fieldname: "employee", label: __("员工"), fieldtype: "Link", options: "Employee", reqd: 1, default: preset.employee || "" },
			{
				fieldname: "document_type",
				label: __("材料类型"),
				fieldtype: "Link",
				options: "Archive Document Type",
				reqd: 1,
				default: preset.document_type || state.document_type || "",
			},
			{ fieldname: "file", label: __("附件"), fieldtype: "Attach", reqd: 1 },
			{ fieldname: "remarks", label: __("备注"), fieldtype: "Small Text" },
		],
		primary_action_label: __("保存"),
		primary_action(values) {
			if (!values.file) {
				frappe.msgprint(__("请上传附件"));
				return;
			}
			frappe.call({
				method: `${ARCHIVE_API}.upload_archive_document`,
				args: {
					employee: values.employee,
					document_type: values.document_type,
					file_url: values.file,
					remarks: values.remarks || "",
				},
				callback: () => {
					frappe.show_alert({ message: __("上传成功"), indicator: "green" });
					dialog.hide();
					reload_archive($main, state);
				},
			});
		},
	});
	dialog.show();
}

function export_missing($main, state) {
	frappe.call({
		method: `${ARCHIVE_API}.list_archive_documents`,
		args: {
			department: state.department || "",
			status: state.doc_status || "",
			document_type: state.document_type || "",
			missing_only: 1,
		},
		callback: (r) => {
			const rows = r.message || [];
			const header = ["employee", "employee_name", "employee_number", "department", "document_type", "document_name"];
			const csv = [header.join(",")]
				.concat(
					rows.map((row) =>
						[row.employee, row.employee_name, row.employee_number, row.department || "", row.document_type, row.document_name]
							.map((v) => `"${String(v ?? "").replace(/"/g, '""')}"`)
							.join(",")
					)
				)
				.join("\n");
			const link = document.createElement("a");
			link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" }));
			link.download = "missing_archive_documents.csv";
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
		},
	});
}

function format_bytes(bytes) {
	if (!bytes) return "0 B";
	const units = ["B", "KB", "MB", "GB"];
	let value = bytes;
	let idx = 0;
	while (value >= 1024 && idx < units.length - 1) {
		value /= 1024;
		idx += 1;
	}
	return `${value.toFixed(idx === 0 ? 0 : 1)} ${units[idx]}`;
}

function escape_html(s) {
	return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
