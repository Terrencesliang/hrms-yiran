// Copyright (c) 2026 stillgroup
// License: MIT

let personalCenterApp = null;

function mountPersonalCenter(wrapper) {
	const $main = wrapper.page.main;
	$main.empty().addClass("personal-center-page");
	const mountEl = document.createElement("div");
	mountEl.id = "personal-center-arco-root";
	$main.append(mountEl);
	if (!window.OrgUI?.mountPersonalCenter) {
		mountEl.innerHTML = `<div class="oc-empty">${__("个人中心前端未加载，请刷新页面。")}</div>`;
		return;
	}
	try { personalCenterApp?.unmount?.(); } catch (_) { /* ignore */ }
	personalCenterApp = window.OrgUI.mountPersonalCenter(mountEl);
}

frappe.pages["personal-center"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({ parent: wrapper, title: __("个人中心"), single_column: true });
	$(wrapper).addClass("arco-personal-center-wrapper");
	mountPersonalCenter(wrapper);
};

frappe.pages["personal-center"].on_page_show = function (wrapper) {
	if (wrapper?.page?.main) mountPersonalCenter(wrapper);
};

frappe.pages["personal-center"].on_page_leave = function () {
	try { personalCenterApp?.unmount?.(); } catch (error) { console.warn("[personal-center] unmount failed", error); }
	personalCenterApp = null;
};
