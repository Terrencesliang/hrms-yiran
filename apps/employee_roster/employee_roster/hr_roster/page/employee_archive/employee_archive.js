// Copyright (c) 2026 stillgroup
// License: MIT

const ARCHIVE_API = "employee_roster.hr_roster.page.employee_archive.employee_archive";
const ARCHIVE_PAGE_SIZE = 50;

const ARCHIVE_TABS = [
	{ key: "overview", label: () => __("员工档案概况") },
	{ key: "education", label: () => __("教育经历") },
	{ key: "work", label: () => __("工作经历") },
	{ key: "documents", label: () => __("证书/证件") },
	{ key: "emergency", label: () => __("紧急联系人") },
	{ key: "skills", label: () => __("工作技能") },
];

const ARCHIVE_ASSET_VERSION = "20260912a";

const ARCHIVE_DOC_NAME_SLUGS = {
	身份证原件: "id_card",
	学历证书: "education_cert",
	入职登记表: "onboarding_form",
	劳动合同: "labor_contract",
	离职证明: "resignation_cert",
};

const ARCHIVE_DOC_VISUALS = {
	default: {
		tone: "default",
		label: __("材料"),
		svg: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M9 1.5H4.5A1.5 1.5 0 0 0 3 3v10a1.5 1.5 0 0 0 1.5 1.5h7A1.5 1.5 0 0 0 13 13V5.5L9 1.5Z" stroke="currentColor" stroke-width="1.35" stroke-linejoin="round"/><path d="M9 1.5V5.5H13" stroke="currentColor" stroke-width="1.35" stroke-linejoin="round"/></svg>`,
	},
	id_card: {
		tone: "id",
		label: __("身份证"),
		svg: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="2.5" y="3.5" width="11" height="9" rx="1.2" stroke="currentColor" stroke-width="1.3"/><circle cx="5.8" cy="7" r="1.2" stroke="currentColor" stroke-width="1.1"/><path d="M4.3 10.2c.5-1 1.2-1.5 2.5-1.5s2 .5 2.5 1.5" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/><path d="M9.2 6.3h2.1M9.2 8.2h2.1" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/></svg>`,
	},
	education_cert: {
		tone: "edu",
		label: __("学历"),
		svg: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M2.8 6.2 8 3.4l5.2 2.8L8 9 2.8 6.2Z" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/><path d="M4.5 7.4V10.2c0 .8 1.5 1.6 3.5 1.6s3.5-.8 3.5-1.6V7.4" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"/><path d="M12.8 6.5V10.8" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"/></svg>`,
	},
	onboarding_form: {
		tone: "form",
		label: __("登记表"),
		svg: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="3.5" y="2.5" width="9" height="11" rx="1.2" stroke="currentColor" stroke-width="1.25"/><path d="M5.8 5.5h4.4M5.8 7.8h4.4M5.8 10.1h2.8" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/><path d="M11.8 2.8v1.9c0 .6-.5 1-1 1h-1.8" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/></svg>`,
	},
	labor_contract: {
		tone: "contract",
		label: __("合同"),
		svg: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M4.5 1.8h4.3L12.5 5v8.7a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1V2.8a1 1 0 0 1 1-1Z" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/><path d="M8.8 1.8V5h3.7" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/><path d="M5.8 8.2c1 .8 2.1 1.2 3.4.2" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/><path d="M5.8 10.8h4.2" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/></svg>`,
	},
	resignation_cert: {
		tone: "exit",
		label: __("离职"),
		svg: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M5.2 2.5h3.1l2.8 2.8V12a1 1 0 0 1-1 1H5.2a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1Z" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/><path d="M8.3 2.5V5.3h2.8" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/><path d="M10.6 8.8H13M12.3 7.5l1.3 1.3-1.3 1.3" stroke="currentColor" stroke-width="1.15" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
	},
};

function resolve_archive_doc_visual(item) {
	const slugCandidates = [
		item?.document_slug,
		item?.document_type,
		ARCHIVE_DOC_NAME_SLUGS[item?.document_name],
	].filter(Boolean);
	for (const slug of slugCandidates) {
		const key = String(slug).toLowerCase();
		if (ARCHIVE_DOC_VISUALS[key]) return ARCHIVE_DOC_VISUALS[key];
	}
	return ARCHIVE_DOC_VISUALS.default;
}

function render_archive_doc_icon(item) {
	const visual = resolve_archive_doc_visual(item);
	return `<span class="hr-archive-progress-icon hr-archive-progress-icon--${visual.tone}" title="${escape_html(visual.label)}" aria-hidden="true">${visual.svg}</span>`;
}

function archive_toolbar_icon(type) {
	const icons = {
		upload: `<svg class="hr-archive-btn-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M7 1.75v6.5M4.55 4.9 7 2.45 9.45 4.9" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/><path d="M2.8 9.1v1.4c0 .61.49 1.1 1.1 1.1h6.2c.61 0 1.1-.49 1.1-1.1V9.1" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"/></svg>`,
		attachment: `<svg class="hr-archive-btn-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M8.05 3.2 5.45 7.05c-.78 1.04-.58 2.52.45 3.25 1.02.72 2.43.42 3.1-.65l2.85-4.2c.95-1.4.58-3.3-.82-4.25-1.4-.95-3.3-.58-4.25.82L3.15 6.95c-1.35 1.98-.82 4.65 1.16 6 1.98 1.35 4.65.82 6-1.16l.55-.8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
		download: `<svg class="hr-archive-btn-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M7 8.25V1.75M4.55 5.6 7 8.05l2.45-2.45" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/><path d="M2.8 9.1v1.4c0 .61.49 1.1 1.1 1.1h6.2c.61 0 1.1-.49 1.1-1.1V9.1" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"/></svg>`,
	};
	return icons[type] || "";
}

function ensure_archive_critical_styles() {
	let style = document.getElementById("hr-archive-critical-styles");
	if (!style) {
		style = document.createElement("style");
		style.id = "hr-archive-critical-styles";
		document.head.appendChild(style);
	}
	style.textContent = `
		.hr-archive-progress-row { display: grid !important; grid-template-columns: 34px minmax(120px, auto) minmax(100px, 1fr) 36px 58px !important; align-items: center !important; column-gap: 10px !important; }
		.hr-archive-progress-icon { display: inline-flex !important; align-items: center !important; justify-content: center !important; width: 30px !important; height: 30px !important; min-width: 30px !important; min-height: 30px !important; border-radius: 8px !important; box-sizing: border-box !important; overflow: visible !important; border: 1px solid transparent !important; }
		.hr-archive-progress-icon svg { display: block !important; width: 16px !important; height: 16px !important; opacity: 1 !important; visibility: visible !important; }
		.hr-archive-progress-row .hr-archive-progress-icon { grid-column: 1 !important; }
	`;
	document.head.appendChild(style);
}

function ensure_archive_styles() {
	ensure_archive_critical_styles();
	const href = `/assets/employee_roster/css/archive.css?v=${ARCHIVE_ASSET_VERSION}`;
	let link = document.getElementById("hr-archive-stylesheet");
	if (!link) {
		link = document.createElement("link");
		link.id = "hr-archive-stylesheet";
		link.rel = "stylesheet";
		document.head.appendChild(link);
	}
	if (link.getAttribute("href") !== href) {
		link.href = href;
	}
}

function fix_archive_page_layout(wrapper) {
	const $wrapper = $(wrapper);
	const navHeight =
		getComputedStyle(document.documentElement).getPropertyValue("--hr-arco-navbar-height").trim() || "60px";
	$wrapper.css({
		minHeight: `calc(100dvh - ${navHeight})`,
		height: "auto",
	});
	const $mainSection = $wrapper.closest(".main-section");
	if ($mainSection.length) {
		$mainSection.css({ background: "" });
	}
	$wrapper.find(".page-body, .page-wrapper, .page-content, .layout-main, .layout-main-section-wrapper, .layout-main-section").css({
		minHeight: 0,
		height: "auto",
		background: "transparent",
	});
	$wrapper.find(".page-content").css({ background: "" });
}

frappe.pages["employee-archive"].on_page_load = function (wrapper) {
	ensure_archive_styles();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("员工档案库"),
		single_column: true,
	});

	$(wrapper).addClass("arco-employee-archive-wrapper");
	fix_archive_page_layout(wrapper);
	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const page = wrapper.page;
	const $main = page.main;
	$main.empty().addClass("hr-archive-page hr-desk-content-stack");

	const $headerHost = $('<div id="hr-archive-desk-header-root" class="hr-desk-header-host"></div>');
	$main.append($headerHost);
	if (window.OrgUI?.mountEmployeeArchiveDeskHeader) {
		page.$hr_archive_header_app = window.OrgUI.mountEmployeeArchiveDeskHeader($headerHost.get(0));
	}

	const state = {
		tab: "overview",
		department: "",
		doc_status: "",
		document_type: "",
		missing_only: false,
		overview: null,
		load_token: 0,
		list_page: 1,
		list_rows: [],
		list_total: 0,
		list_has_more: false,
		list_loading_more: false,
		list_observer: null,
	};

	const tab_html = ARCHIVE_TABS.map(
		(tab, idx) =>
			`<button type="button" class="hr-archive-tab${idx === 0 ? " is-active" : ""}" data-tab="${tab.key}">${tab.label()}</button>`
	).join("");

	$main.append(`
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
					<button type="button" class="hr-archive-btn hr-archive-btn--primary hr-archive-batch-import-btn">${archive_toolbar_icon("upload")}<span>${__("批量导入")}</span></button>
					<button type="button" class="hr-archive-btn hr-archive-btn--secondary hr-archive-upload-btn">${archive_toolbar_icon("attachment")}<span>${__("单份上传")}</span></button>
					<button type="button" class="hr-archive-btn hr-archive-btn--secondary hr-archive-export-btn">${archive_toolbar_icon("download")}<span>${__("导出档案")}</span></button>
					<button type="button" class="hr-archive-btn hr-archive-btn--secondary hr-archive-refresh-btn">${__("刷新")}</button>
				</div>
			</div>
			<div class="hr-archive-panel"></div>
		</div>
	`);

	init_archive_page($main, state);
	fix_archive_page_layout(wrapper);
};

function init_archive_page($main, state) {
	bind_archive_events($main, state);
	parse_route_filters(state);
	// The overview payload already contains departments and document types.  A
	// separate options request on the default route duplicated setup work.
	if (state.tab !== "overview") load_archive_options($main, state);
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
			populate_department_filter($main, data.departments || [], state.department);
			populate_doc_type_filter($main, state, data.document_types || []);
		},
	});
}

function populate_department_filter($main, departments, selected = "") {
	const $dept = $main.find(".hr-archive-dept");
	if ($dept.data("loaded")) return;
	$dept.html(`<option value="">${__("全部")}</option>`);
	departments.forEach((d) => $dept.append(`<option value="${escape_html(d)}">${escape_html(d)}</option>`));
	$dept.data("loaded", true);
	if (selected) $dept.val(selected);
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
		if (state.tab === "documents") reload_archive($main, state);
	});

	$main.find(".hr-archive-refresh-btn").on("click", () => reload_archive($main, state));
	$main.find(".hr-archive-export-btn").on("click", () => open_export_dialog($main, state));
	$main.find(".hr-archive-batch-import-btn").on("click", () => open_batch_import_dialog($main, state));
	$main.find(".hr-archive-upload-btn").on("click", () => open_upload_dialog($main, state));

	$main.on("click", ".hr-archive-go-upload", function () {
		state.document_type = $(this).data("document-type");
		switch_archive_tab($main, state, "documents");
		$main.find(".hr-archive-doc-type").val(state.document_type);
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

	let scrollThrottle = null;
	$main.on("scroll", ".hr-archive-table-scroll", function () {
		if (scrollThrottle) return;
		scrollThrottle = setTimeout(() => {
			scrollThrottle = null;
			maybe_load_more_from_scroll($main, state, this);
		}, 120);
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
	teardown_infinite_scroll(state);
	state.list_page = 1;
	state.list_rows = [];
	state.list_total = 0;
	state.list_has_more = false;
	state.list_loading_more = false;

	const loaders = {
		overview: load_overview,
		education: load_education,
		work: load_work,
		documents: load_documents,
		emergency: load_emergency,
		skills: load_skills,
	};
	const token = ++state.load_token;
	(loaders[state.tab] || load_overview)($main, state, token);
}

function archive_panel($main) {
	return $main.find(".hr-archive-panel");
}

function show_loading($panel) {
	$panel.html(`
		<div class="hr-archive-table-card hr-archive-table-card--state">
			<div class="hr-archive-state">${__("加载中…")}</div>
		</div>
	`);
}

function show_error($panel, err) {
	const msg = (err && (err.message || err.exc || err.responseText)) || __("加载失败");
	$panel.html(`
		<div class="hr-archive-table-card hr-archive-table-card--state">
			<div class="hr-archive-state hr-archive-state--error">${escape_html(String(msg))}</div>
		</div>
	`);
}

function is_current_load(state, token, tab) {
	return token === state.load_token && state.tab === tab;
}

function normalize_list_response(message) {
	if (Array.isArray(message)) {
		return {
			rows: message,
			total: message.length,
			page: 1,
			page_size: message.length || ARCHIVE_PAGE_SIZE,
			has_more: false,
		};
	}
	return {
		rows: message?.rows || [],
		total: message?.total || 0,
		page: message?.page || 1,
		page_size: message?.page_size || ARCHIVE_PAGE_SIZE,
		has_more: !!message?.has_more,
	};
}

function render_table_rows(rows, columns) {
	return rows
		.map(
			(row) =>
				`<tr class="hr-archive-table__row">${columns.map((col) => `<td>${col.render(row)}</td>`).join("")}</tr>`
		)
		.join("");
}

function render_table_card($panel, rows, columns, meta = {}) {
	const colCount = columns.length;
	const total = meta.total != null ? meta.total : rows.length;
	const countLabel =
		meta.count_label ||
		(total ? `${__("共")} ${total} ${__("条")}，${__("已加载")} ${rows.length} ${__("条")}` : `${__("共")} 0 ${__("条")}`);
	const body = rows.length ? render_table_rows(rows, columns) : "";

	const emptyBody = `
		<tr class="hr-archive-table__row hr-archive-table__row--empty">
			<td colspan="${colCount}">
				<div class="hr-archive-table-empty">
					<span class="hr-archive-table-empty__icon">${frappe.utils.icon("inbox", "md")}</span>
					<span class="hr-archive-table-empty__text">${__("暂无数据")}</span>
				</div>
			</td>
		</tr>`;

	$panel.html(`
		<div class="hr-archive-table-card">
			<div class="hr-archive-table-card__head">
				<span class="hr-archive-table-card__count">${countLabel}</span>
			</div>
			<div class="hr-archive-table-scroll">
				<table class="hr-archive-table">
					<thead>
						<tr>${columns.map((col) => `<th scope="col">${col.label}</th>`).join("")}</tr>
					</thead>
					<tbody>${body || emptyBody}</tbody>
				</table>
			</div>
		</div>
	`);
	ensure_scroll_sentinel($panel, colCount);
}

function scroll_sentinel_row(colCount) {
	return `<tr class="hr-archive-scroll-sentinel" aria-hidden="true"><td colspan="${colCount}"></td></tr>`;
}

function ensure_scroll_sentinel($panel, colCount) {
	const $tbody = $panel.find(".hr-archive-table tbody");
	if (!$tbody.length) return null;
	$tbody.find(".hr-archive-scroll-sentinel").remove();
	$tbody.append(scroll_sentinel_row(colCount));
	return $tbody.find(".hr-archive-scroll-sentinel").get(0);
}

function append_table_rows($panel, rows, columns) {
	if (!rows.length) return;
	const $tbody = $panel.find(".hr-archive-table tbody");
	$tbody.find(".hr-archive-table__row--empty").remove();
	$tbody.find(".hr-archive-scroll-sentinel").remove();
	$tbody.append(render_table_rows(rows, columns));
	ensure_scroll_sentinel($panel, columns.length);
}

function set_table_loading_row($panel, colCount, loading) {
	const $tbody = $panel.find(".hr-archive-table tbody");
	$tbody.find(".hr-archive-table__row--loading").remove();
	if (loading && colCount) {
		$tbody.append(
			`<tr class="hr-archive-table__row hr-archive-table__row--loading"><td colspan="${colCount}"><div class="hr-archive-table-loading">${__("加载中…")}</div></td></tr>`
		);
	}
}

function update_table_card_meta($panel, state, colCount = 0) {
	const countLabel = state.list_total
		? `${__("共")} ${state.list_total} ${__("条")}，${__("已加载")} ${state.list_rows.length} ${__("条")}`
		: `${__("共")} 0 ${__("条")}`;
	$panel.find(".hr-archive-table-card__count").text(countLabel);
	set_table_loading_row($panel, colCount, state.list_loading_more);
}

function teardown_infinite_scroll(state) {
	if (state.list_observer) {
		state.list_observer.disconnect();
		state.list_observer = null;
	}
}

function get_table_scroll_root($main) {
	return archive_panel($main).find(".hr-archive-table-scroll").get(0);
}

function bind_infinite_scroll($main, state) {
	teardown_infinite_scroll(state);
	if (state.tab === "overview" || !state.list_has_more) return;
	if (typeof IntersectionObserver === "undefined") return;

	const scrollRoot = get_table_scroll_root($main);
	const sentinel = archive_panel($main).find(".hr-archive-scroll-sentinel").get(0);
	if (!scrollRoot || !sentinel) return;

	state.list_observer = new IntersectionObserver(
		(entries) => {
			if (!entries.some((entry) => entry.isIntersecting)) return;
			maybe_load_more_from_scroll($main, state, scrollRoot);
		},
		{
			root: scrollRoot,
			rootMargin: "120px 0px",
			threshold: 0,
		}
	);
	state.list_observer.observe(sentinel);
}

function maybe_load_more_from_scroll($main, state, scrollEl) {
	if (state.tab === "overview" || state.list_loading_more || !state.list_has_more) return;
	const el = scrollEl || get_table_scroll_root($main);
	if (!el) return;
	const threshold = 120;
	if (el.scrollTop + el.clientHeight < el.scrollHeight - threshold) return;
	load_more_archive_list($main, state);
}

function prefetch_until_scrollable($main, state) {
	requestAnimationFrame(() => {
		if (state.tab === "overview" || state.list_loading_more || !state.list_has_more) {
			bind_infinite_scroll($main, state);
			return;
		}

		const scrollRoot = get_table_scroll_root($main);
		if (scrollRoot && scrollRoot.scrollHeight <= scrollRoot.clientHeight + 8) {
			load_more_archive_list($main, state);
			return;
		}
		bind_infinite_scroll($main, state);
	});
}

function load_paginated_list($main, state, token, tab, method, columns, extraArgs = {}) {
	const $panel = archive_panel($main);
	const append = state.list_page > 1;
	if (!append) show_loading($panel);

	state.list_loading_more = append;
	if (append) update_table_card_meta($panel, state, columns.length);

	frappe.call({
		method,
		args: {
			...list_args(state),
			...extraArgs,
			page: state.list_page,
			page_size: ARCHIVE_PAGE_SIZE,
		},
		callback: (r) => {
			if (!is_current_load(state, token, tab)) return;
			const payload = normalize_list_response(r.message);
			state.list_total = payload.total;
			state.list_has_more = payload.has_more;
			state.list_loading_more = false;

			if (append) {
				state.list_rows = state.list_rows.concat(payload.rows);
				append_table_rows($panel, payload.rows, columns);
				update_table_card_meta($panel, state, columns.length);
				prefetch_until_scrollable($main, state);
				return;
			}

			state.list_rows = payload.rows;
			render_table_card($panel, state.list_rows, columns, {
				total: state.list_total,
				has_more: state.list_has_more,
			});
			prefetch_until_scrollable($main, state);
		},
		error: (err) => {
			state.list_loading_more = false;
			if (!is_current_load(state, token, tab)) return;
			if (append) {
				update_table_card_meta($panel, state, columns.length);
				frappe.show_alert({ message: __("加载失败"), indicator: "red" });
				return;
			}
			show_error($panel, err);
		},
	});
}

function load_more_archive_list($main, state) {
	if (state.list_loading_more || !state.list_has_more) return;
	teardown_infinite_scroll(state);
	state.list_page += 1;
	const token = state.load_token;
	const loaders = {
		education: () =>
			load_paginated_list($main, state, token, "education", `${ARCHIVE_API}.list_education_records`, education_columns()),
		work: () => load_paginated_list($main, state, token, "work", `${ARCHIVE_API}.list_work_history`, work_columns()),
		documents: () =>
			load_paginated_list($main, state, token, "documents", `${ARCHIVE_API}.list_archive_documents`, document_columns(), {
				document_type: state.document_type || "",
				missing_only: state.missing_only ? 1 : 0,
			}),
		emergency: () =>
			load_paginated_list($main, state, token, "emergency", `${ARCHIVE_API}.list_emergency_contacts`, emergency_columns()),
		skills: () => load_paginated_list($main, state, token, "skills", `${ARCHIVE_API}.list_skill_records`, skill_columns()),
	};
	(loaders[state.tab] || loaders.education)();
}

function employee_edit_col() {
	return {
		label: __("操作"),
		render: (row) =>
			`<button type="button" class="hr-archive-link-btn hr-archive-open-employee" data-employee="${escape_html(row.employee)}">${__("编辑档案")}</button>`,
	};
}

function load_overview($main, state, token) {
	const $panel = archive_panel($main);
	show_loading($panel);
	frappe.call({
		method: `${ARCHIVE_API}.get_archive_overview`,
		args: { department: state.department || "" },
		callback: (r) => {
			if (!is_current_load(state, token, "overview")) return;
			state.overview = r.message;
			populate_department_filter($main, r.message?.departments || [], state.department);
			populate_doc_type_filter($main, state, r.message?.document_types || []);
			render_overview($panel, state.overview);
			const pageRoot = $main.closest(".page-container")[0];
			if (pageRoot) fix_archive_page_layout(pageRoot);
		},
		error: (err) => {
			if (is_current_load(state, token, "overview")) show_error($panel, err);
		},
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
	const visual = resolve_archive_doc_visual(item);
	return `
		<div class="hr-archive-progress-row">
			${render_archive_doc_icon(item)}
			<div class="hr-archive-progress-head">
				<span>${escape_html(item.document_name)}</span>
				<span>${item.rate || 0}%</span>
			</div>
			<div class="hr-archive-progress-bar hr-archive-progress-bar--${visual.tone}"><i style="width:${item.rate || 0}%"></i></div>
			<span class="hr-archive-progress-value">${item.rate || 0}%</span>
			<button type="button" class="hr-archive-link-btn hr-archive-go-upload" data-document-type="${escape_html(item.document_type)}">${__("去上传")}</button>
		</div>`;
}

function list_args(state) {
	return {
		department: state.department || "",
		status: state.doc_status || "",
	};
}

function load_education($main, state, token) {
	load_paginated_list($main, state, token, "education", `${ARCHIVE_API}.list_education_records`, education_columns());
}

function education_columns() {
	return [
		{ label: __("姓名"), render: (row) => escape_html(row.employee_name) },
		{ label: __("工号"), render: (row) => escape_html(row.employee_number || "") },
		{ label: __("部门"), render: (row) => escape_html(row.department || "") },
		{ label: __("学校"), render: (row) => escape_html(row.school_univ || "") },
		{ label: __("学历"), render: (row) => escape_html(row.qualification || row.level || "") },
		{ label: __("毕业年份"), render: (row) => escape_html(row.year_of_passing || "") },
		{ label: __("专业"), render: (row) => escape_html(row.maj_opt_subj || "") },
		employee_edit_col(),
	];
}

function load_work($main, state, token) {
	load_paginated_list($main, state, token, "work", `${ARCHIVE_API}.list_work_history`, work_columns());
}

function work_columns() {
	return [
		{ label: __("姓名"), render: (row) => escape_html(row.employee_name) },
		{ label: __("类型"), render: (row) => escape_html(row.history_type || "") },
		{ label: __("公司/组织"), render: (row) => escape_html(row.organization || "") },
		{ label: __("岗位"), render: (row) => escape_html(row.designation || "") },
		{ label: __("期间"), render: (row) => escape_html(row.period || "") },
		employee_edit_col(),
	];
}

function load_emergency($main, state, token) {
	load_paginated_list($main, state, token, "emergency", `${ARCHIVE_API}.list_emergency_contacts`, emergency_columns());
}

function emergency_columns() {
	return [
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
	];
}

function load_skills($main, state, token) {
	load_paginated_list($main, state, token, "skills", `${ARCHIVE_API}.list_skill_records`, skill_columns());
}

function skill_columns() {
	return [
		{ label: __("姓名"), render: (row) => escape_html(row.employee_name) },
		{ label: __("工号"), render: (row) => escape_html(row.employee_number || "") },
		{ label: __("部门"), render: (row) => escape_html(row.department || "") },
		{ label: __("技能"), render: (row) => escape_html(row.skill || "") },
		{ label: __("熟练度"), render: (row) => escape_html(row.proficiency || "") },
		{ label: __("评估日期"), render: (row) => escape_html(row.evaluation_date || "") },
		employee_edit_col(),
	];
}

function load_documents($main, state, token) {
	load_paginated_list($main, state, token, "documents", `${ARCHIVE_API}.list_archive_documents`, document_columns(), {
		document_type: state.document_type || "",
		missing_only: state.missing_only ? 1 : 0,
	});
}

function document_columns() {
	return [
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
				`<button type="button" class="hr-archive-link-btn hr-archive-upload-row" data-employee="${escape_html(row.employee)}" data-document-type="${escape_html(row.document_type)}">${row.has_file ? __("重新上传") : __("上传")}</button>`,
		},
	];
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
