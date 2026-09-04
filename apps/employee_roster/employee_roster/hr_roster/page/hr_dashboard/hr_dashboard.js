// Copyright (c) 2026 stillgroup
// License: MIT

let hrDashboardApp = null;

function ensureOrgUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["hr-dashboard"].on_page_load = function (wrapper) {
	ensureOrgUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("数据面板"),
		single_column: true,
	});

	$(wrapper).addClass("arco-hr-dashboard-wrapper");
	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();

	const mountEl = document.createElement("div");
	mountEl.id = "hr-dashboard-arco-root";
	$main.append(mountEl);

	if (!window.OrgUI?.mountHrDashboard) {
		mountEl.innerHTML = `<div class="oc-empty">${__("数据面板前端未加载，请刷新页面或重新构建 org_ui。")}</div>`;
		return;
	}

	hrDashboardApp = window.OrgUI.mountHrDashboard(mountEl);
};

frappe.pages["hr-dashboard"].on_page_leave = function () {
	try {
		hrDashboardApp?.unmount?.();
	} catch (e) {
		console.warn("[hr-dashboard] unmount failed", e);
	}
	hrDashboardApp = null;
};
