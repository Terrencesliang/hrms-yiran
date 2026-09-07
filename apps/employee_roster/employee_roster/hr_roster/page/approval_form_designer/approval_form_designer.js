// Copyright (c) 2026 stillgroup
// License: MIT

let designerApp = null;
const ORG_UI_ASSET_VER = "20260907i";

function ensureOrgUiCss() {
	const href = `/assets/employee_roster/org_ui/org_ui.css?v=${ORG_UI_ASSET_VER}`;
	let link = document.querySelector("link[data-org-ui-css]");
	if (!link) {
		link = document.createElement("link");
		link.rel = "stylesheet";
		link.setAttribute("data-org-ui-css", "1");
		document.head.appendChild(link);
	}
	if (link.getAttribute("href") !== href) {
		link.href = href;
	}
}

function loadOrgUiScript() {
	return new Promise((resolve, reject) => {
		const src = `/assets/employee_roster/org_ui/org_ui.js?v=${ORG_UI_ASSET_VER}`;
		const existing = document.querySelector("script[data-org-ui-js]");
		if (window.OrgUI?.mountApprovalDesigner && existing?.getAttribute("src") === src) {
			resolve();
			return;
		}
		// Drop stale OrgUI so remount uses the new bundle
		if (existing) existing.remove();
		const script = document.createElement("script");
		script.src = src;
		script.async = true;
		script.setAttribute("data-org-ui-js", "1");
		script.onload = () => resolve();
		script.onerror = () => reject(new Error("org_ui.js load failed"));
		document.head.appendChild(script);
	});
}

function mountDesigner(wrapper) {
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

	try {
		designerApp?.unmount?.();
	} catch (e) {
		/* ignore */
	}
	designerApp = window.OrgUI.mountApprovalDesigner(mountEl, { formName });
}

frappe.pages["approval-form-designer"].on_page_load = async function (wrapper) {
	ensureOrgUiCss();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("表单设计器"),
		single_column: true,
	});

	$(wrapper).addClass("arco-approvals-wrapper");

	try {
		await loadOrgUiScript();
		mountDesigner(wrapper);
	} catch (e) {
		console.error(e);
		wrapper.page.main.html(
			`<div class="oc-empty">${__("审批前端加载失败，请强制刷新页面（Ctrl+F5）。")}</div>`
		);
	}
};

frappe.pages["approval-form-designer"].on_page_show = async function (wrapper) {
	if (!wrapper?.page?.main) return;
	ensureOrgUiCss();
	try {
		await loadOrgUiScript();
		mountDesigner(wrapper);
	} catch (e) {
		console.warn("[approval-form-designer] remount failed", e);
	}
};

frappe.pages["approval-form-designer"].on_page_leave = function () {
	try {
		designerApp?.unmount?.();
	} catch (e) {
		console.warn("[approval-form-designer] unmount failed", e);
	}
	designerApp = null;
};
