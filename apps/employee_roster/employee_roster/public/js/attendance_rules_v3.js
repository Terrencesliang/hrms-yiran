// Copyright (c) 2026 stillgroup
// attendance-rules table UI (v3 — fixed column mapping)
frappe.pages["attendance-rules"].on_page_load = function (wrapper) {
	if (!document.getElementById("attendance-rules-css")) {
		const link = document.createElement("link");
		link.id = "attendance-rules-css";
		link.rel = "stylesheet";
		link.href = `/assets/employee_roster/css/attendance_rules.css?v=${Date.now()}`;
		document.head.appendChild(link);
	}

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("考勤规则"),
		single_column: true,
	});

	const page = wrapper.page;
	const $main = page.main;
	$main.addClass("attendance-rules-page");
	$(wrapper).addClass("ar-page-shell");

	$main.html(`
		<div class="ar-page-frame">
			<div class="ar-page-header">
				<div class="ar-page-header-text">
					<h1 class="ar-page-title">${__("考勤规则")}</h1>
					<p class="ar-page-subtitle">${__("管理考勤扣款、补贴、补卡、加班及外出差旅规则")}</p>
				</div>
				<div class="ar-page-actions">
					<button class="btn btn-default btn-sm ar-import-rule" type="button">${__("导入规则")}</button>
					<button class="btn btn-primary btn-sm ar-add-rule" type="button">＋ ${__("新增扣款规则")}</button>
				</div>
			</div>

			<nav class="ar-tabs" aria-label="${__("考勤规则导航")}">
				<button class="ar-tab is-active" type="button" data-ar-tab="deduction">${__("扣款规则")}</button>
				<button class="ar-tab" type="button" data-ar-tab="allowance">${__("补贴规则")}</button>
				<button class="ar-tab" type="button" data-ar-tab="makeup">${__("补卡规则")}</button>
				<button class="ar-tab" type="button" data-ar-tab="overtime">${__("加班规则")}</button>
				<button class="ar-tab" type="button" data-ar-tab="travel">${__("外出差旅规则")}</button>
			</nav>

			<section class="ar-guide" role="note">
				<b>${__("使用指南")}</b>
				<div class="ar-guide-body"></div>
			</section>

			<div class="ar-stats" hidden></div>

			<section class="ar-list-section" data-ar-panel="deduction">
				<div class="ar-table-wrap"></div>
				<div class="ar-footer-note ar-list-count"></div>
			</section>

			<section class="ar-placeholder-panel" data-ar-panel="other" hidden>
				<div class="ar-empty-panel">${__("该规则类型即将支持，当前请先配置扣款规则。")}</div>
			</section>
		</div>
	`);

	$main.find(".ar-add-rule").on("click", () => frappe.new_doc("Attendance Deduction Rule"));
	$main.find(".ar-import-rule").on("click", () => {
		frappe.new_doc("Data Import", {
			reference_doctype: "Attendance Deduction Rule",
			import_type: "Insert New Records",
		});
	});

	$main.find(".ar-tabs").on("click", ".ar-tab", function () {
		const tab = $(this).attr("data-ar-tab");
		$main.find(".ar-tab").removeClass("is-active");
		$(this).addClass("is-active");

		const is_deduction = tab === "deduction";
		$main.find('[data-ar-panel="deduction"]').toggle(is_deduction);
		$main.find('[data-ar-panel="other"]').toggle(!is_deduction);
		$main.find(".ar-stats").toggle(is_deduction);
		$main.find(".ar-add-rule, .ar-import-rule").prop("disabled", !is_deduction);
	});

	$main.on("click", ".ar-link-groups", (e) => {
		e.preventDefault();
		frappe.set_route("List", "Attendance Group");
	});
	$main.on("click", ".ar-link-settings", (e) => {
		e.preventDefault();
		frappe.set_route("Form", "Attendance Deduction Settings");
	});

	load_rules($main);
};

frappe.pages["attendance-rules"].on_page_show = function (wrapper) {
	const $main = wrapper?.page?.main;
	if ($main?.hasClass("attendance-rules-page")) {
		load_rules($main);
	}
};

function load_rules($main) {
	frappe.call({
		method: "employee_roster.hr_roster.page.attendance_rules.attendance_rules.get_rules_overview",
		callback(r) {
			if (!r.message) return;
			render_guide($main, r.message.help);
			render_stats($main, r.message.stats);
			render_rules($main, r.message.rules || []);
		},
	});
}

function render_guide($main, help) {
	const tip = help || __("规则需关联考勤分组后才会对员工生效；发薪前请通过 Payroll Entry 创建考勤扣款汇总。");
	$main.find(".ar-guide-body").html(`
		<p>1、${__("考勤规则方案可以根据企业已启用的考勤项，包括迟到、早退、缺卡、旷工等，自定义扣款规则。")}</p>
		<p>2、${esc(tip)}
			<a href="#" class="ar-link-groups">${__("考勤分组")}</a>
			／
			<a href="#" class="ar-link-settings">${__("扣款设置")}</a>
		</p>
		<p>3、${__("若有多个不同规则，请新增方案并设置后，到【考勤分组】关联方案及人员。")}</p>
	`);
}

function render_stats($main, stats) {
	const $stats = $main.find(".ar-stats");
	if (!stats || typeof stats !== "object") {
		$stats.attr("hidden", true).empty();
		return;
	}

	const cards = [];
	if (stats.enabled_rules != null) {
		cards.push(stat_card(__("已用扣款规则"), stats.enabled_rules, __("条"), true));
	}
	if (stats.linked_groups != null) {
		cards.push(stat_card(__("关联考勤分组"), stats.linked_groups, __("个"), false));
	}
	if (stats.covered_employees != null) {
		cards.push(stat_card(__("覆盖员工"), stats.covered_employees, __("人"), false));
	}

	if (!cards.length) {
		$stats.attr("hidden", true).empty();
		return;
	}

	$stats.removeAttr("hidden").html(cards.join(""));
}

function stat_card(label, value, unit, highlight) {
	return `
		<div class="ar-stat-card${highlight ? " is-highlight" : ""}">
			<div class="ar-stat-label">${esc(label)}</div>
			<div class="ar-stat-value">
				<span class="ar-stat-num">${esc(value)}</span>
				<span class="ar-stat-unit">${esc(unit)}</span>
			</div>
		</div>
	`;
}

function cell_text(value) {
	const text = String(value == null || value === "" ? "—" : value);
	// Avoid "/" which historically broke HTML string assembly in this page.
	return text.replace(/\//g, "·");
}

function rule_columns(rule) {
	// Prefer backend-provided fixed fields; fall back to items mapping.
	if (rule.late_mode != null || rule.early_mode != null || rule.missing_mode != null || rule.absent_mode != null) {
		return [
			cell_text(rule.late_mode),
			cell_text(rule.early_mode),
			cell_text(rule.missing_mode),
			cell_text(rule.absent_mode),
		];
	}

	const by_type = Object.create(null);
	const by_label = Object.create(null);
	(rule.items || []).forEach((it) => {
		if (!it) return;
		const mode = cell_text(it.mode || it.calc_mode);
		if (it.item_type) by_type[String(it.item_type).trim()] = mode;
		if (it.label) by_label[String(it.label).trim()] = mode;
	});
	const pick = (...keys) => {
		for (const key of keys) {
			if (by_type[key] != null) return by_type[key];
			if (by_label[key] != null) return by_label[key];
		}
		return "—";
	};
	return [
		pick("Late Entry", "迟到"),
		pick("Early Exit", "早退"),
		pick("Missing Punch", "缺卡"),
		pick("Absent", "旷工"),
	];
}

function render_rules($main, rules) {
	const active_count = rules.length;
	$main
		.find(".ar-list-count")
		.text(active_count ? __("共 {0} 条规则", [active_count]) : __("暂无规则"));

	const $wrap = $main.find(".ar-table-wrap");
	$wrap.empty();

	const table = document.createElement("table");
	table.className = "ar-table";

	const colgroup = document.createElement("colgroup");
	["18%", "19%", "19%", "18%", "18%", "8%"].forEach((w) => {
		const col = document.createElement("col");
		col.style.width = w;
		colgroup.appendChild(col);
	});
	table.appendChild(colgroup);

	const thead = document.createElement("thead");
	const head_row = document.createElement("tr");
	[
		__("规则名称"),
		__("迟到扣款"),
		__("早退扣款"),
		__("缺卡处理"),
		__("旷工扣款"),
		__("操作"),
	].forEach((label) => {
		const th = document.createElement("th");
		th.textContent = label;
		head_row.appendChild(th);
	});
	thead.appendChild(head_row);
	table.appendChild(thead);

	const tbody = document.createElement("tbody");
	tbody.className = "ar-rule-list";

	if (!rules.length) {
		const tr = document.createElement("tr");
		const td = document.createElement("td");
		td.colSpan = 6;
		td.className = "ar-empty";
		td.textContent = __("暂无规则");
		tr.appendChild(td);
		tbody.appendChild(tr);
	} else {
		rules.forEach((rule) => {
			const tr = document.createElement("tr");
			tr.className = "ar-row";
			tr.setAttribute("data-name", rule.name || "");

			const name_td = document.createElement("td");
			name_td.className = "ar-name";
			name_td.title = rule.rule_name || "";
			name_td.textContent = rule.rule_name || "";
			tr.appendChild(name_td);

			rule_columns(rule).forEach((mode) => {
				const td = document.createElement("td");
				td.className = "ar-rule-cell";
				td.title = mode;
				td.textContent = mode;
				tr.appendChild(td);
			});

			const action_td = document.createElement("td");
			action_td.className = "ar-actions";

			const edit_btn = document.createElement("button");
			edit_btn.type = "button";
			edit_btn.className = "btn btn-link btn-sm ar-edit";
			edit_btn.textContent = __("修改");
			action_td.appendChild(edit_btn);

			const del_btn = document.createElement("button");
			del_btn.type = "button";
			del_btn.className = "btn btn-link btn-sm ar-delete";
			del_btn.textContent = __("删除");
			action_td.appendChild(del_btn);

			tr.appendChild(action_td);
			tbody.appendChild(tr);
		});
	}

	table.appendChild(tbody);
	$wrap[0].appendChild(table);

	$(tbody)
		.find(".ar-edit")
		.off("click.ar")
		.on("click.ar", function (e) {
			e.preventDefault();
			const name = $(this).closest(".ar-row").attr("data-name");
			if (name) {
				frappe.set_route("Form", "Attendance Deduction Rule", name);
			}
		});

	$(tbody)
		.find(".ar-delete")
		.off("click.ar")
		.on("click.ar", function (e) {
			e.preventDefault();
			const name = $(this).closest(".ar-row").attr("data-name");
			if (!name) return;
			frappe.confirm(__("确认删除规则 {0}？", [name]), () => {
				frappe.call({
					method: "frappe.client.delete",
					args: { doctype: "Attendance Deduction Rule", name },
					callback() {
						frappe.show_alert({ message: __("已删除"), indicator: "green" });
						load_rules($main);
					},
				});
			});
		});
}

function esc(s) {
	return String(s == null ? "" : s)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;");
}
