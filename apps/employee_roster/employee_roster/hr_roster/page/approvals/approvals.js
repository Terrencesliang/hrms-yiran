// Copyright (c) 2026 stillgroup
// License: MIT

let approvalsApp = null;

function ensureOrgUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["approvals"].on_page_load = function (wrapper) {
	ensureOrgUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("审批表单"),
		single_column: true,
	});

	$(wrapper).addClass("arco-approvals-wrapper");
	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();
	$main.addClass("approvals-page");

	const mountEl = document.createElement("div");
	mountEl.id = "approvals-arco-root";
	$main.append(mountEl);

	if (!window.OrgUI?.mountApprovals) {
		mountEl.innerHTML = `<div class="oc-empty">${__("审批前端未加载，请刷新页面或重新构建 org_ui。")}</div>`;
		return;
	}

	approvalsApp = window.OrgUI.mountApprovals(mountEl, { tab: "forms" });
};

frappe.pages["approvals"].on_page_leave = function () {
	try {
		approvalsApp?.unmount?.();
	} catch (e) {
		console.warn("[approvals] unmount failed", e);
	}
	approvalsApp = null;
};
