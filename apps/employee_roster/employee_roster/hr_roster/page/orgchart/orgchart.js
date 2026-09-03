// Copyright (c) 2026 stillgroup
// License: MIT

let orgChartApp = null;

function ensureOrgUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["orgchart"].on_page_load = function (wrapper) {
	ensureOrgUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("组织架构"),
		single_column: true,
	});

	$(wrapper).addClass("arco-orgchart-wrapper");
	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();
	$main.addClass("orgchart-page");

	const mountEl = document.createElement("div");
	mountEl.id = "orgchart-arco-root";
	$main.append(mountEl);

	if (!window.OrgUI?.mountOrgChart) {
		mountEl.innerHTML = `<div class="oc-empty">${__("组织架构前端未加载，请刷新页面或重新构建 org_ui。")}</div>`;
		return;
	}

	orgChartApp = window.OrgUI.mountOrgChart(mountEl);
};

frappe.pages["orgchart"].on_page_leave = function () {
	try {
		orgChartApp?.unmount?.();
	} catch (e) {
		console.warn("[orgchart] unmount failed", e);
	}
	orgChartApp = null;
	document.querySelector(".oc-drawer-root")?.remove();
};
