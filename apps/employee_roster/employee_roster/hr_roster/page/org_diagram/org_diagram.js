// Copyright (c) 2026 stillgroup
// License: MIT

const ORG_DIAGRAM_CSS = `
.org-diagram-page{font-family:"Microsoft YaHei","PingFang SC","Noto Sans SC",sans-serif;font-size:13px}
.orgchart-diagram{background-color:#f5f6f8;background-image:linear-gradient(90deg,rgba(0,0,0,.04) 1px,transparent 1px),linear-gradient(rgba(0,0,0,.04) 1px,transparent 1px);background-size:20px 20px;border:1px solid #d0d5dd;border-radius:8px;overflow:auto;min-height:560px;padding:32px 24px 40px}
.oc-diagram-canvas{min-width:max-content;margin:0 auto;padding-bottom:16px}
.oc-diagram-level{display:flex;flex-direction:column;align-items:center}
.oc-diagram-root-row{display:flex;align-items:center;justify-content:center;position:relative}
.oc-diagram-node{border-radius:4px;padding:10px 18px;font-size:13px;font-weight:600;text-align:center;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.08);line-height:1.4}
.oc-diagram-company{background:#2f6fed;color:#fff;min-width:300px}
.oc-diagram-gm-arm{display:flex;align-items:center;margin-left:8px}
.oc-diagram-gm{background:#fff;color:#e67e22;border:1px solid #f0c090;min-width:140px;font-weight:600}
.oc-diagram-dept{background:#0f9b8e;color:#fff;min-width:108px}
.oc-diagram-dept em{font-style:normal;font-weight:400;margin-left:2px}
.oc-diagram-manager{background:#fff;color:#e67e22;border:1px solid #f0c090;min-width:132px;font-weight:600}
.oc-diagram-line-v,.oc-diagram-line-h{background:#98a2b3;flex-shrink:0}
.oc-diagram-line-v{width:2px;height:24px;margin:0 auto}
.oc-diagram-line-h{height:2px;width:36px}
.oc-line-trunk{height:32px}
.oc-diagram-rail-wrap{position:relative;width:100%;display:flex;flex-direction:column;align-items:stretch}
.oc-diagram-rail-wrap>.oc-line-rail{position:absolute;top:0;left:60px;right:60px;height:2px;width:auto}
.oc-diagram-cols{display:flex;justify-content:flex-start;gap:16px;flex-wrap:nowrap;padding-top:0;min-width:max-content}
.oc-diagram-col{display:flex;flex-direction:column;align-items:center;flex:0 0 auto;min-width:108px;max-width:280px;position:relative}
.oc-diagram-col .oc-line-drop{height:32px}
.oc-diagram-roles{display:flex;flex-direction:row;flex-wrap:nowrap;justify-content:center;align-items:flex-end;gap:8px;padding-top:4px;max-width:280px;overflow-x:auto}
.oc-diagram-role{writing-mode:vertical-rl;text-orientation:upright;letter-spacing:1px;background:#fff;border:1px solid #d0d5dd;border-radius:4px;padding:12px 8px;font-size:12px;color:#344054;min-height:132px;display:inline-flex;flex-direction:row;align-items:center;justify-content:space-between;gap:10px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
.oc-role-title{writing-mode:vertical-rl;text-orientation:upright;font-size:12px;line-height:1.2;max-height:120px;overflow:hidden}
.oc-role-count{writing-mode:horizontal-tb;font-weight:700;font-size:12px;color:#667085;flex-shrink:0}
.oc-diagram-role-muted{writing-mode:horizontal-tb;min-height:auto;color:#667085;padding:8px 12px}
.oc-diagram-empty{text-align:center;color:#667085;padding:48px 0;width:100%}
.orgchart-diagram-toolbar{margin-bottom:12px}
.orgchart-title-bar{display:flex;align-items:center;gap:10px;padding:12px 16px;background:#f9fafb;border:1px solid #d0d5dd;border-radius:8px;font-size:14px;font-weight:600}
.orgchart-sub{font-size:12px;color:#667085;font-weight:400;margin-left:auto}
`;

function ensure_org_diagram_styles() {
	if (document.getElementById("org-diagram-inline-css")) return;
	const style = document.createElement("style");
	style.id = "org-diagram-inline-css";
	style.textContent = ORG_DIAGRAM_CSS;
	document.head.appendChild(style);
}

frappe.pages["org-diagram"].on_page_load = function (wrapper) {
	ensure_org_diagram_styles();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("架构图"),
		single_column: true,
	});

	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();
	$main.addClass("orgchart-page org-diagram-page");
	$main.html(`
		<div class="orgchart-diagram-toolbar"></div>
		<div class="orgchart-diagram"></div>
	`);

	frappe.require("/assets/employee_roster/css/orgchart.css").finally(() => {
		load_diagram($main);
	});
};

function load_diagram($main) {
	frappe.call({
		method: "employee_roster.hr_roster.page.orgchart.orgchart.get_org_diagram",
		callback: function (r) {
			if (!r.message) return;
			render_diagram_toolbar($main, r.message);
			render_diagram($main, r.message);
		},
		error: function (err) {
			frappe.msgprint(__("加载架构图失败：") + ((err && err.message) || err));
		},
	});
}

function render_diagram_toolbar($main, data) {
	const company = data.company_name || __("公司");
	const total = data.company_emp_count || 0;
	$main.find(".orgchart-diagram-toolbar").html(`
		<div class="orgchart-title-bar">
			<span class="orgchart-title">${esc(company)}</span>
			<span class="orgchart-sub">${total} 人 · ${(data.departments || []).length} 个一级部门</span>
		</div>
	`);
}

function render_diagram($main, data) {
	const $wrap = $main.find(".orgchart-diagram");
	const departments = data.departments || [];
	const gm = data.general_manager || "";
	const deptCols = departments.map((dept) => render_diagram_column(dept)).join("");

	$wrap.html(`
		<div class="oc-diagram-canvas">
			<div class="oc-diagram-level oc-level-root">
				<div class="oc-diagram-root-row">
					<div class="oc-diagram-node oc-diagram-company">${esc(data.company_name || "")}</div>
					${
						gm
							? `<div class="oc-diagram-gm-arm">
								<div class="oc-diagram-line-h"></div>
								<div class="oc-diagram-node oc-diagram-gm">${esc(gm)}</div>
							</div>`
							: ""
					}
				</div>
				<div class="oc-diagram-line-v oc-line-trunk"></div>
			</div>
			<div class="oc-diagram-level oc-level-depts">
				<div class="oc-diagram-rail-wrap">
					<div class="oc-diagram-line-h oc-line-rail"></div>
					<div class="oc-diagram-cols">${deptCols || `<div class="oc-diagram-empty">${__("暂无部门数据")}</div>`}</div>
				</div>
			</div>
		</div>
	`);
}

function render_diagram_column(dept) {
	const count = dept.employee_count || 0;
	const manager = dept.manager
		? `<div class="oc-diagram-line-v"></div>
		   <div class="oc-diagram-node oc-diagram-manager">${esc(dept.manager)}</div>`
		: "";

	const roles = (dept.roles || [])
		.map(
			(role) => `
			<div class="oc-diagram-role" title="${esc(role.title)}">
				<span class="oc-role-title">${esc(role.title)}</span>
				<span class="oc-role-count">${role.count}${__("人")}</span>
			</div>`
		)
		.join("");

	const rolesBlock =
		roles ||
		`<div class="oc-diagram-role oc-diagram-role-muted"><span class="oc-role-title">${__("暂无岗位")}</span></div>`;

	return `
		<div class="oc-diagram-col">
			<div class="oc-diagram-line-v oc-line-drop"></div>
			<div class="oc-diagram-node oc-diagram-dept">${esc(dept.title)}<em>(${count}${__("人")})</em></div>
			${manager}
			<div class="oc-diagram-line-v"></div>
			<div class="oc-diagram-roles">${rolesBlock}</div>
		</div>
	`;
}

function esc(s) {
	return String(s == null ? "" : s)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;");
}
