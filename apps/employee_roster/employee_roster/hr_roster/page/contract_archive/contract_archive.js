// Copyright (c) 2026 stillgroup
// License: MIT

let contractArchiveApp = null;

function ensureOrgUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["contract-archive"].on_page_load = function (wrapper) {
	ensureOrgUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("合同档案库"),
		single_column: true,
	});

	$(wrapper).addClass("arco-contract-archive-wrapper");
	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();

	const mountEl = document.createElement("div");
	mountEl.id = "contract-archive-arco-root";
	$main.append(mountEl);

	if (!window.OrgUI?.mountContractArchive) {
		mountEl.innerHTML = `<div class="oc-empty">${__("合同档案库前端未加载，请刷新页面或重新构建 org_ui。")}</div>`;
		return;
	}

	contractArchiveApp = window.OrgUI.mountContractArchive(mountEl);
};

frappe.pages["contract-archive"].on_page_leave = function () {
	try {
		contractArchiveApp?.unmount?.();
	} catch (e) {
		console.warn("[contract-archive] unmount failed", e);
	}
	contractArchiveApp = null;
};
