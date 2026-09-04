// Copyright (c) 2026 stillgroup
// License: MIT
/**
 * Employee List View — Arco Design Pro 风格：
 * 人员概览 data-panel + 筛选卡片 + 列表卡片 + 状态/雇佣类型 Tag
 */
(function () {
	const DOCTYPE = "Employee";

	const ICONS = {
		users:
			'<svg width="16" height="16" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M24 22a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z" stroke="currentColor" stroke-width="3"/><path d="M42 40c0-7.18-6.268-13-14-13h-8c-7.732 0-14 5.82-14 13" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
		active:
			'<svg width="18" height="18" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M24 44c11.046 0 20-8.954 20-20S35.046 4 24 4 4 12.954 4 24s8.954 20 20 20Z" stroke="currentColor" stroke-width="3"/><path d="m15 24 6 6 12-12" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
		fulltime:
			'<svg width="18" height="18" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M8 14h32v26H8V14Z" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/><path d="M16 14V10a8 8 0 0 1 16 0v4" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
		intern:
			'<svg width="18" height="18" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M12 18 24 10l12 8v18a2 2 0 0 1-2 2H14a2 2 0 0 1-2-2V18Z" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/><path d="M24 22v8M20 26h8" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
		probation:
			'<svg width="18" height="18" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M24 14v10l6 4" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M24 44c11.046 0 20-8.954 20-20S35.046 4 24 4 4 12.954 4 24s8.954 20 20 20Z" stroke="currentColor" stroke-width="3"/></svg>',
		inactive:
			'<svg width="18" height="18" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M24 44c11.046 0 20-8.954 20-20S35.046 4 24 4 4 12.954 4 24s8.954 20 20 20Z" stroke="currentColor" stroke-width="3"/><path d="M16 24h16" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
		pending:
			'<svg width="18" height="18" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M24 44c11.046 0 20-8.954 20-20S35.046 4 24 4 4 12.954 4 24s8.954 20 20 20Z" stroke="currentColor" stroke-width="3"/><path d="M24 14v14M24 34h.02" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
		left:
			'<svg width="18" height="18" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M10 8h18v32H10V8Z" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/><path d="m28 24 10-8v16L28 24Z" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/></svg>',
	};

	const prev = frappe.listview_settings[DOCTYPE] || {};
	const prev_onload = prev.onload;
	const prev_refresh = prev.refresh;
	const prev_formatters = prev.formatters || {};

	frappe.listview_settings[DOCTYPE] = Object.assign({}, prev, {
		add_fields: Array.from(
			new Set([...(prev.add_fields || []), "status", "employment_type", "designation", "department"]),
		),

		onload(listview) {
			if (typeof prev_onload === "function") {
				prev_onload(listview);
			}
			enhance_list_shell(listview);
			inject_stat_board(listview);
			bind_stat_board(listview);
			refresh_stat_board(listview);
		},

		refresh(listview) {
			if (typeof prev_refresh === "function") {
				prev_refresh(listview);
			}
			enhance_list_shell(listview);
			if (!listview.$hr_stat_board || !listview.$hr_stat_board.length) {
				inject_stat_board(listview);
				bind_stat_board(listview);
			}
			refresh_stat_board(listview);
			sync_list_toolbar(listview);
		},

		formatters: Object.assign({}, prev_formatters, {
			status(value) {
				return render_status_tag(value);
			},
			employment_type(value) {
				return render_employment_type_tag(value);
			},
		}),
	});

	function enhance_list_shell(listview) {
		const $section = listview.$page.find(".layout-main-section");
		if (!$section.length) {
			return;
		}
		$section.addClass("hr-employee-list-page");

		const $form = $section.find(".page-form").first();
		if ($form.length) {
			$form.addClass("hr-emp-filter-card");
		}

		const $list = $section.find(".frappe-list").first();
		if (!$list.length) {
			return;
		}

		if (!$list.parent().hasClass("hr-emp-table-card")) {
			$list.wrap('<div class="hr-emp-table-card"></div>');
			$list.before(`
				<div class="hr-emp-table-toolbar">
					<div class="hr-emp-table-toolbar-left">
						<span class="hr-emp-table-title">${__("员工名录")}</span>
						<span class="hr-emp-table-count"></span>
					</div>
				</div>
			`);
		}
		listview.$hr_emp_table = $list.closest(".hr-emp-table-card");
		sync_list_toolbar(listview);
	}

	function sync_list_toolbar(listview) {
		const $card = listview.$hr_emp_table;
		if (!$card || !$card.length) {
			return;
		}
		const total =
			(listview.total_count != null && listview.total_count) ||
			(listview.data && listview.data.length) ||
			0;
		$card.find(".hr-emp-table-count").text(`${__("共")} ${total} ${__("人")}`);
	}

	function inject_stat_board(listview) {
		const $section = listview.$page.find(".layout-main-section");
		if (!$section.length) {
			return;
		}

		$section.addClass("hr-employee-list-page");
		enhance_list_shell(listview);
		$section.find(".hr-employee-list-stats").remove();

		const $board = $(`
			<div class="hr-roster-page hr-employee-list-stats">
				<div class="hr-emp-panel">
					<div class="hr-emp-panel-meta">
						<h3 class="hr-emp-panel-title">${ICONS.users}<span>${__("人员概览")}</span></h3>
						<span class="hr-emp-panel-hint">${__("点击指标筛选列表，再次点击取消")}</span>
					</div>
					<div class="hr-stat-board"></div>
				</div>
			</div>
		`);

		const $page_form = $section.find(".page-form").first();
		if ($page_form.length) {
			$page_form.after($board);
		} else {
			$section.prepend($board);
		}

		listview.$hr_stat_board = $board;
	}

	function bind_stat_board(listview) {
		const $board = listview.$hr_stat_board;
		if (!$board || !$board.length) {
			return;
		}

		$board.off("click.hr-stat").on("click.hr-stat", ".hr-stat-cell[data-filter-field]", async function () {
			const $cell = $(this);
			if ($cell.hasClass("is-disabled") || $cell.is(":disabled")) {
				return;
			}
			const field = $cell.attr("data-filter-field");
			const value = $cell.attr("data-filter-value") || "";
			const operator = $cell.attr("data-filter-operator") || "=";
			if (!field || !value) {
				return;
			}

			const current = get_filter_value(listview, field);
			const currentOp = get_filter_operator(listview, field);
			if (current === value && currentOp === operator) {
				await remove_filter(listview, field);
			} else {
				await set_filter(listview, field, value, operator);
			}
			sync_stat_active(listview.$hr_stat_board, listview);
		});
	}

	function refresh_stat_board(listview) {
		const $board = listview.$hr_stat_board;
		if (!$board || !$board.length) {
			return;
		}

		const company = get_filter_value(listview, "company") || "";

		frappe.call({
			method: "employee_roster.hr_roster.page.roster.roster.get_employee_stats",
			args: { company },
			callback(r) {
				if (!r.message || !listview.$hr_stat_board) {
					return;
				}
				render_stat_board(listview.$hr_stat_board, r.message, listview);
			},
		});
	}

	function get_employment_count(stats, key) {
		return (stats.employment_counts && stats.employment_counts[key]) || 0;
	}

	function escape_attr(value) {
		return frappe.utils.escape_html(String(value || ""));
	}

	function stat_cell(label, value, filterField, filterValue, extraClass, filterOperator, iconKey) {
		let attrs = "";
		const disabled = !filterField || !filterValue;
		if (filterField && filterValue) {
			attrs = ` data-filter-field="${escape_attr(filterField)}" data-filter-value="${escape_attr(filterValue)}"`;
			if (filterOperator && filterOperator !== "=") {
				attrs += ` data-filter-operator="${escape_attr(filterOperator)}"`;
			}
		}
		const icon = ICONS[iconKey] || ICONS.active;
		const disabledCls = disabled ? " is-disabled" : "";
		const disabledAttr = disabled ? " disabled" : "";
		return `<button type="button" class="hr-stat-cell${extraClass || ""}${disabledCls}"${attrs}${disabledAttr}>
			<span class="hr-stat-avatar">${icon}</span>
			<span class="hr-stat-body">
				<span class="hr-stat-label">${label}</span>
				<span class="hr-stat-num">${value}<span class="hr-stat-unit">${__("人")}</span></span>
			</span>
		</button>`;
	}

	function render_stat_board($wrap, stats, listview) {
		const fulltime = get_employment_count(stats, "Full-time");
		const intern = get_employment_count(stats, "Intern");
		const probation = get_employment_count(stats, "Probation");

		$wrap.find(".hr-stat-board").html(`
			<div class="hr-stat-card">${stat_cell(__("在职"), stats.active || 0, "status", "Active", " is-green", "=", "active")}</div>
			<div class="hr-stat-card hr-stat-card--split2">
				${stat_cell(__("全职"), fulltime, "designation", "实习生", " is-blue", "!=", "fulltime")}
				${stat_cell(__("实习生"), intern, "designation", "实习生", "", "=", "intern")}
			</div>
			<div class="hr-stat-card hr-stat-card--split3">
				${stat_cell(__("试用期"), probation, "employment_type", "Probation", " is-warn", "=", "probation")}
				${stat_cell(__("停用"), stats.inactive || 0, "status", "Inactive", " is-muted", "=", "inactive")}
				${stat_cell(__("正式"), fulltime, "designation", "实习生", " is-blue", "!=", "fulltime")}
			</div>
			<div class="hr-stat-card hr-stat-card--split2">
				${stat_cell(__("待入职"), 0, "", "", " is-muted", "=", "pending")}
				${stat_cell(__("已离职"), stats.left || 0, "status", "Left", " is-danger", "=", "left")}
			</div>
		`);

		sync_stat_active($wrap, listview);
	}

	function sync_stat_active($wrap, listview) {
		if (!$wrap || !$wrap.length) {
			return;
		}
		$wrap.find(".hr-stat-cell").removeClass("is-active");

		const status = get_filter_value(listview, "status");
		const designation = get_filter_value(listview, "designation");
		const designationOp = get_filter_operator(listview, "designation");
		const employment_type = get_filter_value(listview, "employment_type");

		if (status) {
			$wrap
				.find(`.hr-stat-cell[data-filter-field="status"][data-filter-value="${css_escape(status)}"]`)
				.addClass("is-active");
		}
		if (designation === "实习生") {
			const opSel =
				designationOp === "!=" ? '[data-filter-operator="!="]' : ':not([data-filter-operator])';
			$wrap
				.find(`.hr-stat-cell[data-filter-field="designation"][data-filter-value="实习生"]${opSel}`)
				.addClass("is-active");
		}
		if (employment_type) {
			$wrap
				.find(
					`.hr-stat-cell[data-filter-field="employment_type"][data-filter-value="${css_escape(employment_type)}"]`,
				)
				.addClass("is-active");
		}

		if (!status && !designation && !employment_type) {
			$wrap.find('.hr-stat-cell[data-filter-field="status"][data-filter-value="Active"]').addClass("is-active");
		}
	}

	function render_status_tag(value) {
		if (!value) {
			return "";
		}
		const map = {
			Active: { cls: "tag-active", label: __("在职") },
			Inactive: { cls: "tag-inactive", label: __("停用") },
			Suspended: { cls: "tag-suspended", label: __("停职") },
			Left: { cls: "tag-left", label: __("离职") },
		};
		const item = map[value] || { cls: "tag-default", label: __(value) };
		return `<span class="hr-emp-status-tag ${item.cls}">${frappe.utils.escape_html(item.label)}</span>`;
	}

	function render_employment_type_tag(value) {
		if (!value) {
			return "";
		}
		const map = {
			"Full-time": { cls: "tag-fulltime", label: __("全职") },
			Intern: { cls: "tag-intern", label: __("实习") },
			Probation: { cls: "tag-probation", label: __("试用期") },
			Contract: { cls: "tag-default", label: __("合同工") },
			"Part-time": { cls: "tag-default", label: __("兼职") },
		};
		const item = map[value] || { cls: "tag-default", label: __(value) };
		return `<span class="hr-emp-type-tag ${item.cls}">${frappe.utils.escape_html(item.label)}</span>`;
	}

	function css_escape(value) {
		if (window.CSS && CSS.escape) {
			return CSS.escape(value);
		}
		return String(value).replace(/"/g, '\\"');
	}

	function get_filter_value(listview, fieldname) {
		const filters = (listview.filter_area && listview.filter_area.get()) || [];
		const match = filters.find((f) => f[1] === fieldname);
		return match ? match[3] : "";
	}

	function get_filter_operator(listview, fieldname) {
		const filters = (listview.filter_area && listview.filter_area.get()) || [];
		const match = filters.find((f) => f[1] === fieldname);
		return match ? match[2] : "";
	}

	async function remove_filter(listview, fieldname) {
		if (listview.filter_area && listview.filter_area.remove) {
			await listview.filter_area.remove(fieldname);
		}
	}

	async function set_filter(listview, fieldname, value, operator) {
		await remove_filter(listview, fieldname);
		await listview.filter_area.add([[listview.doctype, fieldname, operator || "=", value]]);
	}
})();
