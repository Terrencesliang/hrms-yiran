// Copyright (c) 2026 stillgroup
// License: MIT

let contractSigningSignedApp = null;

function ensureOrgUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["contract-signing-signed"].on_page_load = function (wrapper) {
	ensureOrgUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("已签署"),
		single_column: true,
	});

	$(wrapper).addClass("arco-contract-signing-wrapper");
	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();

	const mountEl = document.createElement("div");
	mountEl.id = "contract-signing-signed-arco-root";
	$main.append(mountEl);

	if (!window.OrgUI?.mountContractSigning) {
		mountEl.innerHTML = `<div class="oc-empty">${__("合同签署前端未加载，请刷新页面或重新构建 org_ui。")}</div>`;
		return;
	}

	contractSigningSignedApp = window.OrgUI.mountContractSigning(mountEl, { status: "signed" });
};

frappe.pages["contract-signing-signed"].on_page_leave = function () {
	try {
		contractSigningSignedApp?.unmount?.();
	} catch (e) {
		console.warn("[contract-signing-signed] unmount failed", e);
	}
	contractSigningSignedApp = null;
};
