// Copyright (c) 2026 stillgroup
// License: MIT

let orgDiagramApp = null;

function ensureOrgDiagramUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["org-diagram"].on_page_load = function (wrapper) {
	ensureOrgDiagramUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("架构图"),
		single_column: true,
	});

	$(wrapper).addClass("arco-orgchart-wrapper arco-orgdiagram-wrapper");
	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();
	$main.addClass("orgchart-page org-diagram-page");

	const mountEl = document.createElement("div");
	mountEl.id = "orgdiagram-arco-root";
	$main.append(mountEl);

	if (!window.OrgUI?.mountOrgDiagram) {
		mountEl.innerHTML = `<div class="oc-empty">${__("架构图前端未加载，请刷新页面或重新构建 org_ui。")}</div>`;
		return;
	}

	orgDiagramApp = window.OrgUI.mountOrgDiagram(mountEl);
};

frappe.pages["org-diagram"].on_page_leave = function () {
	try {
		orgDiagramApp?.unmount?.();
	} catch (error) {
		console.warn("[org-diagram] unmount failed", error);
	}
	orgDiagramApp = null;
};
