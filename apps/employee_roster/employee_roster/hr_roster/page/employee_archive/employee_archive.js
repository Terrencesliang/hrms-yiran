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
					<button type="button" class="btn btn-primary btn-sm hr-archive-batch-import-btn">${frappe.utils.icon("upload", "sm")}<span>${__("批量导入")}</span></button>
					<button type="button" class="btn btn-default btn-sm hr-archive-upload-btn">${frappe.utils.icon("attachment", "sm")}<span>${__("单份上传")}</span></button>
					<button type="button" class="btn btn-default btn-sm hr-archive-export-btn">${frappe.utils.icon("download", "sm")}<span>${__("导出档案")}</span></button>
					<button type="button" class="btn btn-default btn-sm hr-archive-refresh-btn">${__("刷新")}</button>
				</div>
			</div>
			<div class="hr-archive-panel"></div>
		</div>
	`);

	init_archive_page($main, state);
};

function init_archive_page($main, state) {
	load_archive_options($main, state);
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

function load_archive_options($main, state) {
	const $dept = $main.find(".hr-archive-dept");
	$dept.html(`<option value="">${__("全部")}</option>`);
	frappe.call({
		method: `${ARCHIVE_API}.get_archive_options`,
		callback: (r) => {
			const data = r.message || {};
			(data.departments || []).forEach((d) => $dept.append(`<option value="${escape_html(d)}">${escape_html(d)}</option>`));
			populate_doc_type_filter($main, state, data.document_types || []);
		},
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
	$main.find(".hr-archive-export-btn").on("click", () => open_export_dialog($main, state));
	$main.find(".hr-archive-batch-import-btn").on("click", () => open_batch_import_dialog($main, state));
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
	$main.find(".hr-archive-upload-btn").toggle(isDocuments);
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
			<span class="hr-archive-progress-icon">${frappe.utils.icon("file", "sm")}</span>
			<div class="hr-archive-progress-head">
				<span>${escape_html(item.document_name)}</span>
				<span>${item.rate || 0}%</span>
			</div>
			<div class="hr-archive-progress-bar"><i style="width:${item.rate || 0}%"></i></div>
			<span class="hr-archive-progress-value">${item.rate || 0}%</span>
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

function open_batch_import_dialog($main, state) {
	let preview = null;
	const dialog = new frappe.ui.Dialog({
		title: __("批量导入档案材料"),
		size: "extra-large",
		fields: [
			{
				fieldname: "guide",
				fieldtype: "HTML",
				options: `
					<div class="hr-archive-import-guide">
						<div class="hr-archive-import-guide__icon">${frappe.utils.icon("folder-open", "md")}</div>
						<div><strong>${__("按“员工编号-材料类型”命名文件")}</strong><p>${__("示例：HR-EMP-00001-学历证书.pdf。支持 PDF、图片和 Office 文档，请将文件统一打包为 ZIP。")}</p></div>
					</div>`,
			},
			{ fieldname: "zip_file", label: __("ZIP 压缩包"), fieldtype: "Attach", reqd: 1 },
			{ fieldname: "overwrite_existing", label: __("覆盖已存在的同类型材料"), fieldtype: "Check", default: 0 },
			{ fieldname: "preview", fieldtype: "HTML", options: render_import_empty_state() },
		],
		primary_action_label: __("开始校验"),
		primary_action(values) {
			if (!values.zip_file || !/\.zip(?:\?.*)?$/i.test(values.zip_file)) {
				frappe.msgprint(__("请选择 ZIP 格式的压缩包"));
				return;
			}

			if (!preview) {
				dialog.get_primary_btn().prop("disabled", true).text(__("正在校验…"));
				frappe.call({
					method: `${ARCHIVE_API}.preview_archive_import`,
					args: { file_url: values.zip_file, overwrite_existing: values.overwrite_existing ? 1 : 0 },
					callback: (r) => {
						preview = r.message || {};
						dialog.fields_dict.preview.$wrapper.html(render_import_preview(preview));
						dialog.get_primary_btn().prop("disabled", !(preview.ready_count > 0)).text(__("确认导入 {0} 份", [preview.ready_count || 0]));
					},
					error: () => dialog.get_primary_btn().prop("disabled", false).text(__("重新校验")),
				});
				return;
			}

			dialog.get_primary_btn().prop("disabled", true).text(__("正在导入…"));
			frappe.call({
				method: `${ARCHIVE_API}.import_archive_zip`,
				args: { file_url: values.zip_file, overwrite_existing: values.overwrite_existing ? 1 : 0 },
				freeze: true,
				freeze_message: __("正在导入档案材料，请稍候…"),
				callback: (r) => {
					const result = r.message || {};
					frappe.show_alert({ message: __("导入完成：成功 {0} 份，跳过 {1} 份", [result.imported || 0, result.skipped || 0]), indicator: "green" }, 7);
					dialog.hide();
					reload_archive($main, state);
				},
				error: () => dialog.get_primary_btn().prop("disabled", false).text(__("重新导入")),
			});
		},
	});
	dialog.show();
	dialog.$wrapper.addClass("hr-archive-import-dialog");
	const reset_preview = () => {
		preview = null;
		dialog.fields_dict.preview.$wrapper.html(render_import_empty_state());
		dialog.get_primary_btn().prop("disabled", false).text(__("开始校验"));
	};
	dialog.fields_dict.zip_file.df.onchange = reset_preview;
	dialog.fields_dict.overwrite_existing.df.onchange = reset_preview;
}

function render_import_empty_state() {
	return `<div class="hr-archive-import-empty"><span>${frappe.utils.icon("upload-cloud", "lg")}</span><strong>${__("上传后先校验，再确认导入")}</strong><small>${__("系统会匹配员工与材料类型，并列出无法识别或已存在的文件。")}</small></div>`;
}

function render_import_preview(data) {
	const rows = (data.items || []).slice(0, 100);
	const body = rows.length
		? rows.map((row) => `<tr>
			<td title="${escape_html(row.filename)}">${escape_html(row.filename)}</td>
			<td>${escape_html(row.employee_name || "-")}</td>
			<td>${escape_html(row.document_name || "-")}</td>
			<td><span class="hr-archive-import-state is-${escape_html(row.state)}">${escape_html(row.message)}</span></td>
		</tr>`).join("")
		: `<tr><td colspan="4" class="text-muted text-center">${__("压缩包中没有可导入文件")}</td></tr>`;
	return `
		<div class="hr-archive-import-summary">
			<div><strong>${data.total_files || 0}</strong><span>${__("文件总数")}</span></div>
			<div class="is-ready"><strong>${data.ready_count || 0}</strong><span>${__("可导入")}</span></div>
			<div class="is-skip"><strong>${data.skipped_count || 0}</strong><span>${__("将跳过")}</span></div>
			<div class="is-error"><strong>${data.error_count || 0}</strong><span>${__("无法识别")}</span></div>
		</div>
		<div class="hr-archive-import-table"><table class="table"><thead><tr><th>${__("文件名")}</th><th>${__("员工")}</th><th>${__("材料类型")}</th><th>${__("校验结果")}</th></tr></thead><tbody>${body}</tbody></table></div>
		${(data.items || []).length > 100 ? `<div class="text-muted small">${__("仅展示前 100 条，导入时会处理全部文件。")}</div>` : ""}`;
}

function open_export_dialog($main, state) {
	const departments = $main.find(".hr-archive-dept option").map((_, el) => ({ label: $(el).text(), value: $(el).val() })).get();
	const documentTypes = $main.find(".hr-archive-doc-type option").map((_, el) => ({ label: $(el).text(), value: $(el).val() })).get();
	const dialog = new frappe.ui.Dialog({
		title: __("导出员工档案"),
		fields: [
			{ fieldname: "export_type", label: __("导出内容"), fieldtype: "Select", options: [{ label: __("缺失材料清单"), value: "missing" }, { label: __("档案材料明细"), value: "detail" }], default: "missing", reqd: 1 },
			{ fieldname: "department", label: __("部门"), fieldtype: "Select", options: departments, default: state.department || "" },
			{ fieldname: "status", label: __("员工状态"), fieldtype: "Select", options: [{ label: __("全部"), value: "" }, { label: __("在职"), value: "Active" }, { label: __("离职"), value: "Left" }], default: state.doc_status || "" },
			{ fieldname: "document_type", label: __("材料类型"), fieldtype: "Select", options: documentTypes, default: state.document_type || "" },
			{ fieldname: "export_hint", fieldtype: "HTML", options: `<div class="hr-archive-export-hint">${frappe.utils.icon("info", "sm")}<span>${__("导出为 UTF-8 CSV，可直接使用 Excel 打开。导出结果仅包含您有权查看的档案数据。")}</span></div>` },
		],
		primary_action_label: __("生成并下载"),
		primary_action(values) {
			dialog.get_primary_btn().prop("disabled", true).text(__("正在生成…"));
			frappe.call({
				method: `${ARCHIVE_API}.get_archive_export`,
				args: values,
				callback: (r) => {
					const result = r.message || {};
					download_text_file(result.filename || "employee_archive.csv", result.content || "");
					frappe.show_alert({ message: __("已导出 {0} 条记录", [result.count || 0]), indicator: "green" });
					dialog.hide();
				},
				error: () => dialog.get_primary_btn().prop("disabled", false).text(__("重新生成")),
			});
		},
	});
	dialog.show();
	dialog.$wrapper.addClass("hr-archive-export-dialog");
}

function download_text_file(filename, content) {
	const url = URL.createObjectURL(new Blob([content], { type: "text/csv;charset=utf-8" }));
	const link = document.createElement("a");
	link.href = url;
	link.download = filename;
	document.body.appendChild(link);
	link.click();
	link.remove();
	URL.revokeObjectURL(url);
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
