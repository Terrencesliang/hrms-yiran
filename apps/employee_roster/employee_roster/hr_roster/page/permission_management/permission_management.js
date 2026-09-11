// Copyright (c) 2026 stillgroup
// License: MIT

let permissionManagementApp = null;

frappe.pages["permission-management"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({ parent: wrapper, title: __("权限管理"), single_column: true });
	const $main = wrapper.page.main;
	$main.empty();
	const mountEl = document.createElement("div");
	mountEl.id = "permission-management-arco-root";
	$main.append(mountEl);
	if (!window.OrgUI?.mountPermissionManagement) {
		mountEl.innerHTML = `<div class="oc-empty">${__("权限管理前端未加载，请刷新页面。")}</div>`;
		return;
	}
	permissionManagementApp = window.OrgUI.mountPermissionManagement(mountEl);
};

frappe.pages["permission-management"].on_page_leave = function () {
	try { permissionManagementApp?.unmount?.(); } catch (error) { console.warn("[permission-management] unmount failed", error); }
	permissionManagementApp = null;
};
