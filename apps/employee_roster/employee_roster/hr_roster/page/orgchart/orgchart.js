// Copyright (c) 2026 stillgroup
// License: MIT

frappe.pages["orgchart"].on_page_load = function (wrapper) {
	if (!document.querySelector('link[data-orgchart-css]')) {
		const link = document.createElement("link");
		link.rel = "stylesheet";
		link.href = "/assets/employee_roster/css/orgchart.css";
		link.setAttribute("data-orgchart-css", "1");
		document.head.appendChild(link);
	}

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("组织架构"),
		single_column: true,
	});

	$(wrapper).find(".layout-main").addClass("row");
	$(wrapper).find(".layout-main-section-wrapper").addClass("col-md-12");

	const $main = wrapper.page.main;
	$main.empty();
	$main.addClass("orgchart-page");
	$main.html('<div class="orgchart-toolbar"></div><div class="orgchart-tree"></div>');

	load_tree($main);
};

function load_tree($main) {
	frappe.call({
		method: "employee_roster.hr_roster.page.orgchart.orgchart.get_org_tree",
		callback: function (r) {
			if (!r.message) return;
			render_toolbar($main, r.message);
			render_tree($main, r.message.roots || []);
		},
		error: function (err) {
			frappe.msgprint(__("加载组织架构失败：") + ((err && err.message) || err));
		},
	});
}

function render_toolbar($main, data) {
	const total = data.total || 0;
	const company = data.company_name || __("公司");
	$main.find(".orgchart-toolbar").html(`
		<div class="orgchart-title-bar">
			<span class="orgchart-title">${esc(company)}</span>
			<span class="orgchart-sub">${total} 个组织单元</span>
		</div>
	`);
}

function render_tree($main, roots) {
	const header = `
		<div class="orgchart-table-head">
			<div class="oc-col oc-col-name">组织名称</div>
			<div class="oc-col oc-col-type">组织类型</div>
			<div class="oc-col oc-col-emp">员工数</div>
			<div class="oc-col oc-col-bianzhi">人员编制</div>
			<div class="oc-col oc-col-qb">缺编超编</div>
			<div class="oc-col oc-col-head">负责人</div>
			<div class="oc-col oc-col-fg">分管领导</div>
		</div>
	`;
	$main.find(".orgchart-tree").html(header + '<div class="orgchart-table-body"></div>');
	const $tbody = $main.find(".orgchart-table-body");
	$tbody.empty();

	const flat = [];
	function walk(nodes, depth, parentKey) {
		nodes.forEach((n) => {
			flat.push({ node: n, depth, parentKey });
			if (n.children && n.children.length) {
				walk(n.children, depth + 1, n.name);
			}
		});
	}
	walk(roots, 0, null);

	const collapsed = new Set();

	function visibleKeys() {
		flat.forEach((it) => {
			let ok = true;
			let cur = it.parentKey;
			let depth = it.depth;
			while (cur != null && depth > 0) {
				if (collapsed.has(cur)) {
					ok = false;
					break;
				}
				const parentEntry = flat.find((x) => x.node.name === cur && x.depth === depth - 1);
				cur = parentEntry ? parentEntry.parentKey : null;
				depth--;
			}
			it.visible = ok;
		});
	}

	function rebuild() {
		visibleKeys();
		$tbody.empty();
		flat.forEach((it) => {
			if (!it.visible) return;
			const tr = document.createElement("div");
			tr.className = "orgchart-row";
			tr.setAttribute("data-name", it.node.name || "");
			tr.setAttribute("data-depth", it.depth);

			const hasChildren = it.node.children && it.node.children.length > 0;
			const isCollapsed = collapsed.has(it.node.name);
			const arrow = hasChildren
				? `<span class="oc-arrow ${isCollapsed ? "" : "open"}" data-toggle>${isCollapsed ? "▸" : "▾"}</span>`
				: `<span class="oc-arrow oc-arrow-empty"></span>`;

			const indent = it.depth * 26;
			const emp = it.node.employee_count == null ? 0 : it.node.employee_count;
			const head = it.node.head_name || "-";
			const nodeType = it.node.is_company ? __("公司") : __("部门");

			tr.innerHTML = `
				<div class="oc-col oc-col-name" style="padding-left:${indent + 8}px">
					${arrow}
					<span class="oc-node${it.node.is_company ? " oc-node-company" : ""}" style="cursor:${hasChildren ? "pointer" : "default"}">${esc(it.node.title)}</span>
				</div>
				<div class="oc-col oc-col-type">${nodeType}</div>
				<div class="oc-col oc-col-emp">${emp}</div>
				<div class="oc-col oc-col-bianzhi">-</div>
				<div class="oc-col oc-col-qb">-</div>
				<div class="oc-col oc-col-head">${esc(head)}</div>
				<div class="oc-col oc-col-fg">-</div>
			`;
			$tbody.append(tr);
		});
	}

	rebuild();

	$tbody.off("click").on("click", ".oc-arrow[data-toggle]", function () {
		const $row = $(this).closest(".orgchart-row");
		const name = $row.attr("data-name");
		const entry = flat.find((x) => x.node.name === name);
		const hasChildren = entry && entry.node.children && entry.node.children.length;
		if (!hasChildren) return;
		if (collapsed.has(name)) {
			collapsed.delete(name);
		} else {
			collapsed.add(name);
		}
		rebuild();
	});
}

function esc(s) {
	return String(s == null ? "" : s)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;");
}
