// Copyright (c) 2026 stillgroup
// License: MIT — thin Desk bridge; UI lives in org_ui

let attendanceRulesApp = null;

function ensureOrgUiCss() {
	if (document.querySelector("link[data-org-ui-css]")) return;
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.setAttribute("data-org-ui-css", "1");
	link.href = `/assets/employee_roster/org_ui/org_ui.css?v=${Date.now()}`;
	document.head.appendChild(link);
}

frappe.pages["attendance-rules"].on_page_load = function (wrapper) {
	ensureOrgUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("考勤规则"),
		single_column: true,
	});

	$(wrapper).addClass("arco-hr-attendance-rules-wrapper");
	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-side-section").hide();
	$(wrapper)
		.find(".layout-main-section-wrapper")
		.addClass("col-md-12")
		.css({ flex: "1 1 100%", maxWidth: "100%", width: "100%" });

	const $main = wrapper.page.main;
	$main.empty();

	const mountEl = document.createElement("div");
	mountEl.id = "hr-attendance-rules-arco-root";
	$main.append(mountEl);

	if (!window.OrgUI?.mountAttendanceRules) {
		mountEl.innerHTML = `<div class="oc-empty">${__("考勤规则前端未加载，请刷新页面或重新构建 org_ui。")}</div>`;
		return;
	}

	attendanceRulesApp = window.OrgUI.mountAttendanceRules(mountEl);
};

frappe.pages["attendance-rules"].on_page_show = function () {
	attendanceRulesApp?.reloadRules?.();
};

frappe.pages["attendance-rules"].on_page_leave = function () {
	try {
		attendanceRulesApp?.unmount?.();
	} catch (e) {
		console.warn("[attendance-rules] unmount failed", e);
	}
	attendanceRulesApp = null;
};
