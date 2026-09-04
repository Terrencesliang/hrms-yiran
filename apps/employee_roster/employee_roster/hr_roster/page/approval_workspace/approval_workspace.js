// Copyright (c) 2026 stillgroup
// License: MIT

let workspaceApp = null;

function ensureOrgUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

function resolveView() {
	const route = frappe.get_route() || [];
	const v = route[1] || "todo";
	const allowed = ["todo", "done", "mine", "cc", "start"];
	return allowed.includes(v) ? v : "todo";
}

function mountWorkspace(wrapper) {
	const $main = wrapper.page.main;
	$main.empty().addClass("approvals-page");
	const mountEl = document.createElement("div");
	mountEl.id = "approval-workspace-arco-root";
	$main.append(mountEl);

	if (!window.OrgUI?.mountApprovalsWorkspace) {
		mountEl.innerHTML = `<div class="oc-empty">${__("审批前端未加载，请刷新或重新构建 org_ui。")}</div>`;
		return;
	}
	try {
		workspaceApp?.unmount?.();
	} catch (e) {
		/* ignore */
	}
	workspaceApp = window.OrgUI.mountApprovalsWorkspace(mountEl, { view: resolveView() });
}

frappe.pages["approval-workspace"].on_page_load = function (wrapper) {
	ensureOrgUiCss();
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("审批工作区"),
		single_column: true,
	});
	$(wrapper).addClass("arco-approvals-wrapper");
	mountWorkspace(wrapper);
};

frappe.pages["approval-workspace"].on_page_show = function (wrapper) {
	if (wrapper?.page?.main) {
		mountWorkspace(wrapper);
	}
};

frappe.pages["approval-workspace"].on_page_leave = function () {
	try {
		workspaceApp?.unmount?.();
	} catch (e) {
		console.warn("[approval-workspace] unmount failed", e);
	}
	workspaceApp = null;
};
