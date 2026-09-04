// Copyright (c) 2026 stillgroup
// License: MIT
/**
 * Employee Checkin List View 增强（Arco Design Pro 风格）：
 * 1) onload 默认 time=["Timespan","today"]
 * 2) 顶部 data-panel：出勤 / 上下班打卡 / 迟到 / 缺卡（后端聚合，可下钻）
 * 3) 表格四列：日出勤结果 / 日出勤时长 / 最早上班 / 最晚下班
 *
 * 出勤 = 有打卡的人（含迟到、缺卡）；上下班打卡 = 打齐 IN+OUT。
 * 表格日出勤结果仍互斥（缺卡/迟到/出勤）。口径见 employee_checkin_dashboard.py
 */
(function () {
	const DOCTYPE = "Employee Checkin";
	const DASHBOARD_METHOD =
		"employee_roster.hr_roster.api.employee_checkin_dashboard.get_checkin_dashboard";

	const ICONS = {
		present:
			'<svg width="20" height="20" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M24 44c11.046 0 20-8.954 20-20S35.046 4 24 4 4 12.954 4 24s8.954 20 20 20Z" stroke="currentColor" stroke-width="3"/><path d="m15 24 6 6 12-12" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
		both_punches:
			'<svg width="20" height="20" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M24 14v10l6 4" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M24 44c11.046 0 20-8.954 20-20S35.046 4 24 4 4 12.954 4 24s8.954 20 20 20Z" stroke="currentColor" stroke-width="3"/></svg>',
		late:
			'<svg width="20" height="20" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M24 12v14h10" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M24 44c11.046 0 20-8.954 20-20S35.046 4 24 4 4 12.954 4 24s8.954 20 20 20Z" stroke="currentColor" stroke-width="3"/><path d="M36 6 42 12M12 6 6 12" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
		missing:
			'<svg width="20" height="20" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M24 44c11.046 0 20-8.954 20-20S35.046 4 24 4 4 12.954 4 24s8.954 20 20 20Z" stroke="currentColor" stroke-width="3"/><path d="M24 14v14M24 34h.02" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
		home:
			'<svg width="16" height="16" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M9 18 24 6l15 12v22a2 2 0 0 1-2 2H11a2 2 0 0 1-2-2V18Z" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/><path d="M19 42V26h10v16" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/></svg>',
	};

	const prev = frappe.listview_settings[DOCTYPE] || {};
	const prev_onload = prev.onload;
	const prev_before_render = prev.before_render;
	const prev_refresh = prev.refresh;
	const prev_formatters = prev.formatters || {};

	frappe.listview_settings[DOCTYPE] = Object.assign({}, prev, {
		add_fields: Array.from(
			new Set([...(prev.add_fields || []), "employee", "time", "log_type", "shift", "shift_start"]),
		),

		onload(listview) {
			if (typeof prev_onload === "function") {
				prev_onload(listview);
			}
			listview._checkin_day_map = listview._checkin_day_map || {};
			listview._checkin_dashboard = listview._checkin_dashboard || null;
			listview._checkin_result_filter = listview._checkin_result_filter || null;

			init_default_today_filter(listview);
			enhance_list_shell(listview);
			inject_stat_board(listview);
			bind_stat_board(listview);
			ensure_day_columns(listview);
			refresh_dashboard(listview);
		},

		refresh(listview) {
			if (typeof prev_refresh === "function") {
				prev_refresh(listview);
			}
			enhance_list_shell(listview);
			if (!listview.$hr_checkin_stats || !listview.$hr_checkin_stats.length) {
				inject_stat_board(listview);
				bind_stat_board(listview);
			}
			refresh_dashboard(listview);
			sync_list_toolbar(listview);
		},

		before_render() {
			if (typeof prev_before_render === "function") {
				prev_before_render();
			}
			const listview = cur_list;
			if (listview && listview.doctype === DOCTYPE) {
				apply_summary_to_rows(listview);
			}
		},

		formatters: Object.assign({}, prev_formatters, {
			log_type(value) {
				return render_log_type_tag(value);
			},
			day_attendance_result(value, df, doc) {
				const summary = lookup_summary(cur_list, doc);
				const result = (summary && summary.result) || value || "";
				return render_result_tag(result);
			},
			day_work_hours(value, df, doc) {
				const summary = lookup_summary(cur_list, doc);
				const hours = summary ? summary.work_hours : value;
				if (hours === null || hours === undefined || hours === "") {
					return "";
				}
				return `<span class="hr-ck-hours">${frappe.utils.escape_html(String(hours))} ${__("小时")}</span>`;
			},
			day_first_in(value, df, doc) {
				const summary = lookup_summary(cur_list, doc);
				const text = (summary && summary.first_in) || value || "";
				return text ? `<span class="hr-ck-time">${frappe.utils.escape_html(text)}</span>` : "";
			},
			day_last_out(value, df, doc) {
				const summary = lookup_summary(cur_list, doc);
				const text = (summary && summary.last_out) || value || "";
				return text ? `<span class="hr-ck-time">${frappe.utils.escape_html(text)}</span>` : "";
			},
		}),
	});

	function init_default_today_filter(listview) {
		if (listview._hr_checkin_default_applied) {
			return;
		}
		listview._hr_checkin_default_applied = true;

		const filters = (listview.filter_area && listview.filter_area.get()) || [];
		const has_time = filters.some((f) => f[1] === "time");
		if (has_time) {
			return;
		}

		listview.filter_area.add([[DOCTYPE, "time", "Timespan", "today"]]);
	}

	function ensure_day_columns(listview) {
		if (listview._hr_checkin_cols_injected) {
			return;
		}
		listview._hr_checkin_cols_injected = true;
		const defs = [
			{ fieldname: "day_attendance_result", label: __("日出勤结果"), fieldtype: "Data" },
			{ fieldname: "day_work_hours", label: __("日出勤时长"), fieldtype: "Data" },
			{ fieldname: "day_first_in", label: __("最早上班时间"), fieldtype: "Data" },
			{ fieldname: "day_last_out", label: __("最晚下班时间"), fieldtype: "Data" },
		];
		const setup = listview.setup_columns.bind(listview);
		listview.setup_columns = function () {
			setup();
			defs.forEach((df) => {
				if (this.columns.some((c) => c.df && c.df.fieldname === df.fieldname)) {
					return;
				}
				this.columns.push({
					type: "Field",
					df: Object.assign({ in_list_view: 1 }, df),
				});
			});
		};
		if (listview.columns && listview.columns.length) {
			listview.setup_columns();
		}
	}

	function get_time_args(listview) {
		const filters = (listview.filter_area && listview.filter_area.get()) || [];
		const time_filter = filters.find((f) => f[1] === "time");
		if (!time_filter) {
			return {};
		}
		const op = time_filter[2];
		const val = time_filter[3];
		if (op === "Timespan") {
			return { timespan: val };
		}
		if (op === "Between" && Array.isArray(val)) {
			return { from_date: val[0], to_date: val[1] };
		}
		if (op === "=" && val) {
			return { from_date: val, to_date: val };
		}
		if (op === ">" || op === ">=") {
			return { from_date: val, to_date: frappe.datetime.get_today() };
		}
		return {};
	}

	function refresh_dashboard(listview) {
		if (!listview || listview.doctype !== DOCTYPE) {
			return;
		}
		const args = get_time_args(listview);
		const token = JSON.stringify(args);
		if (listview._hr_checkin_dash_token === token && listview._checkin_dashboard) {
			render_stat_board(listview);
			apply_summary_to_rows(listview);
			return;
		}
		listview._hr_checkin_dash_token = token;
		set_loading(listview, true);

		if (listview._hr_checkin_dash_req) {
			listview._hr_checkin_dash_req.abort && listview._hr_checkin_dash_req.abort();
		}

		listview._hr_checkin_dash_req = frappe.call({
			method: DASHBOARD_METHOD,
			args,
			callback(r) {
				listview._hr_checkin_dash_req = null;
				set_loading(listview, false);
				if (!r.message) {
					return;
				}
				listview._checkin_dashboard = r.message;
				listview._checkin_day_map = r.message.summaries || {};
				apply_summary_to_rows(listview);
				render_stat_board(listview);
				if (listview.data && listview.data.length && listview.render_list && !listview._hr_checkin_rendering) {
					listview._hr_checkin_rendering = true;
					try {
						listview.render_list();
					} finally {
						listview._hr_checkin_rendering = false;
					}
				}
			},
			error() {
				listview._hr_checkin_dash_req = null;
				set_loading(listview, false);
			},
		});
	}

	function set_loading(listview, on) {
		const $wrap = listview.$hr_checkin_stats;
		if (!$wrap || !$wrap.length) {
			return;
		}
		$wrap.toggleClass("is-loading", !!on);
	}

	function lookup_summary(listview, doc) {
		if (!listview || !doc || !doc.employee || !doc.time) {
			return null;
		}
		const day = String(doc.time).slice(0, 10);
		const key = `${doc.employee}|${day}`;
		const map = listview._checkin_day_map || {};
		return map[key] || null;
	}

	function apply_summary_to_rows(listview) {
		if (!listview || !listview.data) {
			return;
		}
		listview.data.forEach((row) => {
			const summary = lookup_summary(listview, row);
			if (!summary) {
				return;
			}
			row.day_attendance_result = summary.result;
			row.day_work_hours = summary.work_hours;
			row.day_first_in = summary.first_in;
			row.day_last_out = summary.last_out;
		});
	}

	function render_result_tag(result) {
		if (!result) {
			return "";
		}
		let cls = "tag-default";
		if (result === "出勤") {
			cls = "tag-present";
		} else if (result === "迟到") {
			cls = "tag-late";
		} else if (result === "缺卡") {
			cls = "tag-missing";
		}
		return `<span class="hr-checkin-result-tag ${cls}">${frappe.utils.escape_html(result)}</span>`;
	}

	function render_log_type_tag(value) {
		if (!value) {
			return "";
		}
		const raw = String(value).toUpperCase();
		let cls = "tag-default";
		let label = value;
		if (raw === "IN" || value === "签到") {
			cls = "tag-in";
			label = __("签到");
		} else if (raw === "OUT" || value === "签退") {
			cls = "tag-out";
			label = __("签退");
		}
		return `<span class="hr-checkin-log-tag ${cls}">${frappe.utils.escape_html(label)}</span>`;
	}

	/** 筛选区 + 列表区套上 Arco Pro search-table 卡片壳 */
	function enhance_list_shell(listview) {
		const $section = listview.$page.find(".layout-main-section");
		if (!$section.length) {
			return;
		}
		$section.addClass("hr-checkin-list-page");

		const $form = $section.find(".page-form").first();
		if ($form.length) {
			$form.addClass("hr-ck-filter-card");
		}

		const $list = $section.find(".frappe-list").first();
		if (!$list.length) {
			return;
		}

		if (!$list.parent().hasClass("hr-ck-table-card")) {
			$list.wrap('<div class="hr-ck-table-card"></div>');
			$list.before(`
				<div class="hr-ck-table-toolbar">
					<div class="hr-ck-table-toolbar-left">
						<span class="hr-ck-table-title">${__("打卡明细")}</span>
						<span class="hr-ck-table-count"></span>
					</div>
				</div>
			`);
		}
		listview.$hr_checkin_table = $list.closest(".hr-ck-table-card");
		sync_list_toolbar(listview);
	}

	function sync_list_toolbar(listview) {
		const $card = listview.$hr_checkin_table;
		if (!$card || !$card.length) {
			return;
		}
		const total =
			(listview.total_count != null && listview.total_count) ||
			(listview.data && listview.data.length) ||
			0;
		$card.find(".hr-ck-table-count").text(`${__("共")} ${total} ${__("条")}`);
	}

	function inject_stat_board(listview) {
		const $section = listview.$page.find(".layout-main-section");
		if (!$section.length) {
			return;
		}
		$section.addClass("hr-checkin-list-page");
		enhance_list_shell(listview);
		$section.find(".hr-checkin-list-stats").remove();

		const $board = $(`
			<div class="hr-roster-page hr-checkin-list-stats is-loading">
				<div class="hr-ck-panel">
					<div class="hr-ck-panel-meta">
						<h3 class="hr-ck-panel-title">${ICONS.home}<span>${__("考勤概览")}</span></h3>
						<span class="hr-ck-panel-range"></span>
					</div>
					<div class="hr-stat-board hr-checkin-stat-board"></div>
					<div class="hr-ck-hint">${__("点击指标可按人员下钻筛选，再次点击取消")}</div>
				</div>
			</div>
		`);
		const $page_form = $section.find(".page-form").first();
		if ($page_form.length) {
			$page_form.after($board);
		} else {
			$section.prepend($board);
		}
		listview.$hr_checkin_stats = $board;
	}

	function bind_stat_board(listview) {
		const $board = listview.$hr_checkin_stats;
		if (!$board || !$board.length) {
			return;
		}
		$board.off("click.hr-checkin-stat").on("click.hr-checkin-stat", ".hr-stat-cell[data-result]", async function () {
			const result_key = $(this).attr("data-result");
			if (!result_key) {
				return;
			}
			const current = listview._checkin_result_filter;
			if (current === result_key) {
				listview._checkin_result_filter = null;
				await clear_employee_in_filter(listview);
			} else {
				listview._checkin_result_filter = result_key;
				await apply_result_drilldown(listview, result_key);
			}
			sync_stat_active(listview);
		});
	}

	async function apply_result_drilldown(listview, result_key) {
		const dash = listview._checkin_dashboard;
		if (!dash || !dash.employees_by_result) {
			return;
		}
		const map = {
			present: "出勤",
			both_punches: "both_punches",
			late: "迟到",
			missing: "缺卡",
		};
		const bucket = map[result_key] || result_key;
		const employees = dash.employees_by_result[bucket] || [];
		await clear_employee_in_filter(listview);
		if (!employees.length) {
			await listview.filter_area.add([[DOCTYPE, "employee", "=", "__none__"]]);
			return;
		}
		await listview.filter_area.add([[DOCTYPE, "employee", "in", employees]]);
	}

	async function clear_employee_in_filter(listview) {
		const filters = (listview.filter_area && listview.filter_area.get()) || [];
		const emp = filters.find((f) => f[1] === "employee" && (f[2] === "in" || f[3] === "__none__"));
		if (emp && listview.filter_area.remove) {
			await listview.filter_area.remove("employee");
		}
	}

	function format_range_label(dash) {
		if (!dash || !dash.range) {
			return "";
		}
		const { from: from_dt, to: to_dt, timespan } = dash.range;
		if (timespan) {
			const labels = {
				today: __("今天"),
				yesterday: __("昨天"),
				"this week": __("本周"),
				"this month": __("本月"),
				"this year": __("今年"),
				"last week": __("上周"),
				"last month": __("上月"),
			};
			return labels[timespan] || timespan;
		}
		if (from_dt && to_dt) {
			const a = String(from_dt).slice(0, 10);
			const b = String(to_dt).slice(0, 10);
			return a === b ? a : `${a} ~ ${b}`;
		}
		return __("全部时间");
	}

	function render_stat_board(listview) {
		const $wrap = listview.$hr_checkin_stats;
		if (!$wrap || !$wrap.length) {
			return;
		}
		const dash = listview._checkin_dashboard || {};
		const stats = dash.stats || {
			present: 0,
			both_punches: 0,
			late: 0,
			missing: 0,
		};

		$wrap.find(".hr-ck-panel-range").text(format_range_label(dash));
		$wrap.find(".hr-checkin-stat-board").html(`
			<div class="hr-stat-card">${stat_cell(__("出勤"), stats.present || 0, "present", " is-green")}</div>
			<div class="hr-stat-card">${stat_cell(__("上下班打卡"), stats.both_punches || 0, "both_punches", " is-blue")}</div>
			<div class="hr-stat-card">${stat_cell(__("迟到"), stats.late || 0, "late", " is-warn")}</div>
			<div class="hr-stat-card">${stat_cell(__("缺卡"), stats.missing || 0, "missing", " is-danger")}</div>
		`);
		sync_stat_active(listview);
	}

	function sync_stat_active(listview) {
		const $wrap = listview.$hr_checkin_stats;
		if (!$wrap) {
			return;
		}
		$wrap.find(".hr-stat-cell").removeClass("is-active");
		const key = listview._checkin_result_filter;
		if (key) {
			$wrap.find(`.hr-stat-cell[data-result="${key}"]`).addClass("is-active");
			const labels = {
				present: __("出勤"),
				both_punches: __("上下班打卡"),
				late: __("迟到"),
				missing: __("缺卡"),
			};
			$wrap.find(".hr-ck-hint").html(
				`${__("当前筛选")}：<strong>${frappe.utils.escape_html(labels[key] || key)}</strong> · ${__(
					"再次点击取消",
				)}`,
			);
		} else {
			$wrap.find(".hr-ck-hint").text(__("点击指标可按人员下钻筛选，再次点击取消"));
		}
	}

	function escape_attr(value) {
		return frappe.utils.escape_html(String(value || ""));
	}

	function stat_cell(label, value, resultKey, extraClass) {
		const icon = ICONS[resultKey] || ICONS.present;
		return `<button type="button" class="hr-stat-cell${extraClass || ""}" data-result="${escape_attr(
			resultKey,
		)}">
			<span class="hr-stat-avatar">${icon}</span>
			<span class="hr-stat-body">
				<span class="hr-stat-label">${label}</span>
				<span class="hr-stat-num">${value}<span class="hr-stat-unit">${__("人")}</span></span>
			</span>
		</button>`;
	}
})();
