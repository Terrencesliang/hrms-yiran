// Copyright (c) 2026 stillgroup
// License: MIT

let contractInitiateApp = null;

function ensureOrgUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

function readInitiateOptions() {
	const opts = window.frappe?.route_options || {};
	const route = window.frappe?.get_route?.() || [];
	const params = new URLSearchParams(window.location.search || "");
	const templateId =
		opts.templateId || opts.template_id || params.get("templateId") || route[1] || "";
	const templateName =
		opts.templateName || opts.template_name || params.get("templateName") || "";
	const modeRaw = opts.mode || params.get("mode") || "single";
	const mode = modeRaw === "batch" ? "batch" : "single";
	const openRaw = opts.openPicker ?? opts.open_picker ?? params.get("openPicker");
	const openPicker = openRaw === undefined || openRaw === null || openRaw === ""
		? true
		: !(openRaw === false || openRaw === "0" || openRaw === "false");
	try {
		if (window.frappe) window.frappe.route_options = null;
	} catch (e) {
		/* ignore */
	}
	return { templateId, templateName, mode, openPicker };
}

function ensureMountEl(wrapper) {
	const $main = wrapper.page.main;
	let mountEl = document.getElementById("contract-initiate-arco-root");
	if (!mountEl) {
		$main.empty();
		mountEl = document.createElement("div");
		mountEl.id = "contract-initiate-arco-root";
		$main.append(mountEl);
	}
	return mountEl;
}

function mountInitiate(wrapper) {
	const mountEl = ensureMountEl(wrapper);
	if (!window.OrgUI?.mountContractInitiate) {
		mountEl.innerHTML = `<div class="oc-empty">${__("发起签署前端未加载，请刷新页面或重新构建 org_ui。")}</div>`;
		return;
	}
	try {
		contractInitiateApp?.unmount?.();
	} catch (e) {
		/* ignore */
	}
	contractInitiateApp = window.OrgUI.mountContractInitiate(mountEl, readInitiateOptions());
}

frappe.pages["contract-initiate"].on_page_load = function (wrapper) {
	ensureOrgUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("发起签署"),
		single_column: true,
	});

	$(wrapper).addClass("arco-contract-initiate-wrapper");
	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	ensureMountEl(wrapper);
	wrapper.__ci_shell_ready = true;
};

frappe.pages["contract-initiate"].on_page_show = function (wrapper) {
	if (!wrapper?.__ci_shell_ready) return;
	mountInitiate(wrapper);
};

frappe.pages["contract-initiate"].on_page_leave = function () {
	try {
		contractInitiateApp?.unmount?.();
	} catch (e) {
		console.warn("[contract-initiate] unmount failed", e);
	}
	contractInitiateApp = null;
};
