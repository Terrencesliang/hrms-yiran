// Copyright (c) 2026 stillgroup
// License: MIT

let designerApp = null;

function ensureOrgUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["approval-form-designer"].on_page_load = function (wrapper) {
	ensureOrgUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("表单设计器"),
		single_column: true,
	});

	$(wrapper).addClass("arco-approvals-wrapper");
	const $main = wrapper.page.main;
	$main.empty().addClass("approvals-page");

	const mountEl = document.createElement("div");
	mountEl.id = "approval-designer-arco-root";
	$main.append(mountEl);

	const route = frappe.get_route() || [];
	const formName = route[1] || "";

	if (!window.OrgUI?.mountApprovalDesigner) {
		mountEl.innerHTML = `<div class="oc-empty">${__("审批前端未加载，请刷新或重新构建 org_ui。")}</div>`;
		return;
	}
	designerApp = window.OrgUI.mountApprovalDesigner(mountEl, { formName });
};

frappe.pages["approval-form-designer"].on_page_show = function () {
	// remount when route form changes
};

frappe.pages["approval-form-designer"].on_page_leave = function () {
	try {
		designerApp?.unmount?.();
	} catch (e) {
		console.warn("[approval-form-designer] unmount failed", e);
	}
	designerApp = null;
};
