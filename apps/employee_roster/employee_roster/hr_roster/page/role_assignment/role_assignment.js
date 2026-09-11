// Copyright (c) 2026 stillgroup
// License: MIT

let roleAssignmentApp = null;

frappe.pages["role-assignment"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({ parent: wrapper, title: __("人员角色分配"), single_column: true });
	const $main = wrapper.page.main;
	$main.empty();
	const mountEl = document.createElement("div");
	mountEl.id = "role-assignment-arco-root";
	$main.append(mountEl);
	if (!window.OrgUI?.mountRoleAssignment) {
		mountEl.innerHTML = `<div class="oc-empty">${__("人员角色分配前端未加载，请刷新页面。")}</div>`;
		return;
	}
	roleAssignmentApp = window.OrgUI.mountRoleAssignment(mountEl);
};

frappe.pages["role-assignment"].on_page_leave = function () {
	try { roleAssignmentApp?.unmount?.(); } catch (error) { console.warn("[role-assignment] unmount failed", error); }
	roleAssignmentApp = null;
};
