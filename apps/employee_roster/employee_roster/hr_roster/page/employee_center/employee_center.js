// Copyright (c) 2026 stillgroup
// License: MIT

let employeeCenterApp = null;

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
	const allowed = ["home", "onboarding", "subsidy", "job-change", "resignation", "handover", "applications"];
	return allowed.includes(route[1]) ? route[1] : "home";
}

function resolveInstanceName() {
	const route = frappe.get_route() || [];
	return route[2] || "";
}

function mountEmployeeCenter(wrapper) {
	const $main = wrapper.page.main;
	$main.empty().addClass("employee-center-page");
	const mountEl = document.createElement("div");
	mountEl.id = "employee-center-arco-root";
	$main.append(mountEl);

	if (!window.OrgUI?.mountEmployeeCenter) {
		mountEl.innerHTML = `<div class="oc-empty">${__("员工中心前端未加载，请刷新或重新构建 org_ui。")}</div>`;
		return;
	}
	try {
		employeeCenterApp?.unmount?.();
	} catch (_) {
		/* ignore */
	}
		employeeCenterApp = window.OrgUI.mountEmployeeCenter(mountEl, { view: resolveView(), instanceName: resolveInstanceName() });
}

frappe.pages["employee-center"].on_page_load = function (wrapper) {
	ensureOrgUiCss();
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("员工中心"),
		single_column: true,
	});
	$(wrapper).addClass("arco-employee-center-wrapper");
	mountEmployeeCenter(wrapper);
};

frappe.pages["employee-center"].on_page_show = function (wrapper) {
	if (wrapper?.page?.main) mountEmployeeCenter(wrapper);
};

frappe.pages["employee-center"].on_page_leave = function () {
	try {
		employeeCenterApp?.unmount?.();
	} catch (error) {
		console.warn("[employee-center] unmount failed", error);
	}
	employeeCenterApp = null;
};
