// Copyright (c) 2026 stillgroup
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

	const $main = wrapper.page.main;
	$main.addClass("attendance-rules-page");
	$main.html(`
		<div class="ar-help"></div>
		<div class="ar-toolbar">
			<button class="btn btn-primary btn-sm ar-add-rule" type="button">+ ${__("新增扣款规则")}</button>
			<button class="btn btn-default btn-sm ar-open-groups" type="button">${__("考勤分组")}</button>
			<button class="btn btn-default btn-sm ar-open-settings" type="button">${__("扣款设置")}</button>
		</div>
		<div class="ar-rule-list"></div>
	`);

	$main.find(".ar-add-rule").on("click", () => frappe.new_doc("Attendance Deduction Rule"));
	$main.find(".ar-open-groups").on("click", () => frappe.set_route("List", "Attendance Group"));
	$main.find(".ar-open-settings").on("click", () => frappe.set_route("Form", "Attendance Deduction Settings"));

	load_rules($main);
};

function load_rules($main) {
	frappe.call({
		method: "employee_roster.hr_roster.page.attendance_rules.attendance_rules.get_rules_overview",
		callback(r) {
			if (!r.message) return;
			$main.find(".ar-help").html(`<p>${esc(r.message.help || "")}</p>`);
			const cards = (r.message.rules || [])
				.map((rule) => {
					const tags = (rule.items || [])
						.map((it) => `<span class="ar-tag"><b>${esc(it.label)}</b> ${esc(it.mode)}</span>`)
						.join("");
					return `
					<div class="ar-card" data-name="${esc(rule.name)}">
						<div class="ar-card-head">
							<h4>${esc(rule.rule_name)}</h4>
							<span class="ar-groups">${__("关联分组")}: ${rule.group_count || 0}</span>
						</div>
						<p class="ar-desc">${esc(rule.description || "")}</p>
						<div class="ar-tags">${tags || __("未启用扣款项")}</div>
						<button class="btn btn-default btn-sm ar-edit" type="button">${__("编辑")}</button>
					</div>`;
				})
				.join("");
			$main.find(".ar-rule-list").html(cards || `<div class="ar-empty">${__("暂无规则")}</div>`);
			$main.find(".ar-edit").on("click", function () {
				frappe.set_route("Form", "Attendance Deduction Rule", $(this).closest(".ar-card").attr("data-name"));
			});
		},
	});
}

function esc(s) {
	return String(s == null ? "" : s)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;");
}
