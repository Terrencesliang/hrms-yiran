// Copyright (c) 2026 stillgroup
// License: MIT

let hrHomeApp = null;

function ensureOrgUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["hr-home"].on_page_load = function (wrapper) {
	ensureOrgUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("人事主页"),
		single_column: true,
	});

	$(wrapper).addClass("arco-hr-home-wrapper");
	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();

	const mountEl = document.createElement("div");
	mountEl.id = "hr-home-arco-root";
	$main.append(mountEl);

	if (!window.OrgUI?.mountHrHome) {
		mountEl.innerHTML = `<div class="oc-empty">${__("人事主页前端未加载，请刷新页面或重新构建 org_ui。")}</div>`;
		return;
	}

	hrHomeApp = window.OrgUI.mountHrHome(mountEl);
};

frappe.pages["hr-home"].on_page_leave = function () {
	try {
		hrHomeApp?.unmount?.();
	} catch (e) {
		console.warn("[hr-home] unmount failed", e);
	}
	hrHomeApp = null;
};
