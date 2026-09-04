// Copyright (c) 2026 stillgroup
// License: MIT

let approvalTemplatesApp = null;

function ensureOrgUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["approval-templates"].on_page_load = function (wrapper) {
	ensureOrgUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("审批模板库"),
		single_column: true,
	});

	$(wrapper).addClass("arco-approvals-wrapper");
	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();
	$main.addClass("approvals-page");

	const mountEl = document.createElement("div");
	mountEl.id = "approval-templates-arco-root";
	$main.append(mountEl);

	if (!window.OrgUI?.mountApprovals) {
		mountEl.innerHTML = `<div class="oc-empty">${__("审批前端未加载，请刷新页面或重新构建 org_ui。")}</div>`;
		return;
	}

	approvalTemplatesApp = window.OrgUI.mountApprovals(mountEl, { tab: "templates" });
};

frappe.pages["approval-templates"].on_page_leave = function () {
	try {
		approvalTemplatesApp?.unmount?.();
	} catch (e) {
		console.warn("[approval-templates] unmount failed", e);
	}
	approvalTemplatesApp = null;
};
