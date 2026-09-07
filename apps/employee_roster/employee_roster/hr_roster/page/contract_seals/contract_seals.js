// Copyright (c) 2026 stillgroup
// License: MIT

let contractSealsApp = null;

function ensureOrgUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["contract-seals"].on_page_load = function (wrapper) {
	ensureOrgUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("企业印章"),
		single_column: true,
	});

	$(wrapper).addClass("arco-contract-seals-wrapper");
	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();

	const mountEl = document.createElement("div");
	mountEl.id = "contract-seals-arco-root";
	$main.append(mountEl);

	if (!window.OrgUI?.mountContractSeals) {
		mountEl.innerHTML = `<div class="oc-empty">${__("企业印章前端未加载，请刷新页面或重新构建 org_ui。")}</div>`;
		return;
	}

	contractSealsApp = window.OrgUI.mountContractSeals(mountEl);
};

frappe.pages["contract-seals"].on_page_leave = function () {
	try {
		contractSealsApp?.unmount?.();
	} catch (e) {
		console.warn("[contract-seals] unmount failed", e);
	}
	contractSealsApp = null;
};
