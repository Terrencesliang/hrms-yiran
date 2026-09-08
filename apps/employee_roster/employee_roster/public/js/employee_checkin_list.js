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

	const prev = frappe.listview_settings[DOCTYPE] || {};
	const prev_onload = prev.onload;
	const prev_before_render = prev.before_render;
	const prev_refresh = prev.refresh;
	const prev_formatters = prev.formatters || {};

	frappe.listview_settings[DOCTYPE] = Object.assign({}, prev, {
		add_fields: Array.from(
			new Set([
				...(prev.add_fields || []),
				"employee",
				"employee_name",
				"time",
				"log_type",
				"checkin_type",
				"device_id",
				"latitude",
				"longitude",
				"shift",
				"shift_start",
			]),
		),

		onload(listview) {
			if (typeof prev_onload === "function") {
				prev_onload(listview);
			}
			listview._checkin_day_map = listview._checkin_day_map || {};
			listview._checkin_dashboard = listview._checkin_dashboard || null;
			listview._checkin_result_filter = listview._checkin_result_filter || null;
			listview.sort_by = "time";
			listview.sort_order = "desc";
			listview.sort_selector?.set_value?.("time", "desc");

			patch_empty_state(listview);
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
			patch_empty_state(listview);
			enhance_list_shell(listview);
			if (!listview.$hr_checkin_stats || !listview.$hr_checkin_stats.length) {
				inject_stat_board(listview);
				bind_stat_board(listview);
			}
			refresh_dashboard(listview);
			sync_arco_table(listview);
			sync_list_toolbar(listview);
			refresh_empty_state(listview);
		},

		before_render() {
			if (typeof prev_before_render === "function") {
				prev_before_render();
			}
			const listview = cur_list;
			if (listview && listview.doctype === DOCTYPE) {
				apply_summary_to_rows(listview);
				sync_arco_table(listview);
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

	function refresh_empty_state(listview) {
		if (!listview?.$no_result?.length || !listview.get_no_result_message) {
			return;
		}
		listview.$no_result.html(listview.get_no_result_message());
	}

	function patch_empty_state(listview) {
		if (listview._hr_checkin_empty_patched) {
			return;
		}
		listview._hr_checkin_empty_patched = true;
		listview.get_no_result_message = function get_checkin_no_result_message() {
			const filters = this.filter_area && this.filter_area.get();
			const has_filters_set = filters && filters.length;
			const title = has_filters_set ? __("未找到打卡记录") : __("暂无打卡记录");
			const description = has_filters_set
				? __("清除筛选条件以查看全部记录。")
				: __("当前还没有打卡数据。");
			const icon =
				this.meta?.icon && !String(this.meta.icon).startsWith("fa fa-")
					? this.meta.icon
					: "pointer";
			return frappe.ui.empty_state.html({
				icon,
				title,
				description,
				actions: [],
			});
		};
	}

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
		window.OrgUI?.updateEmployeeCheckinOverview?.({ loading: !!on });
		window.OrgUI?.updateEmployeeCheckinTable?.({ loading: !!on });
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
		const $page = listview.$page;
		$page.addClass("arco-hr-checkin-list-wrapper");

		const $section = listview.$page.find(".layout-main-section");
		if (!$section.length) {
			return;
		}
		$section.addClass("hr-checkin-list-page hr-desk-content-stack");

		const $layoutMain = listview.$page.find(".layout-main").first();
		if ($layoutMain.length) {
			$layoutMain.addClass("row");
		}
		listview.$page.find(".layout-side-section").hide();
		listview.$page
			.find(".layout-main-section-wrapper")
			.addClass("col-md-12")
			.css({ flex: "1 1 100%", maxWidth: "100%", width: "100%" });

		$section.find("#hr-checkin-list-header-root").remove();
		if (!$section.find("#hr-checkin-list-header-root").length) {
			const $header = $('<div id="hr-checkin-list-header-root" class="hr-desk-header-host"></div>');
			$section.prepend($header);
			if (window.OrgUI?.mountEmployeeCheckinDeskHeader) {
				try {
					listview.$hr_checkin_header_app?.unmount?.();
				} catch (error) {
					console.warn("[employee-checkin] desk header unmount failed", error);
				}
				listview.$hr_checkin_header_app = window.OrgUI.mountEmployeeCheckinDeskHeader($header.get(0));
			}
		}

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
						<span class="hr-emp-table-title">${__("打卡明细")}</span>
						<span class="hr-emp-table-count"></span>
					</div>
				</div>
			`);
		}
		listview.$hr_checkin_table = $list.closest(".hr-emp-table-card");
		mount_arco_table(listview, $list);
		sync_list_toolbar(listview);
	}

	function mount_arco_table(listview, $list) {
		const $card = $list.closest(".hr-emp-table-card");
		let $host = $card.find(".hr-checkin-arco-table-host").first();
		if (!$host.length) {
			$host = $('<div class="hr-checkin-arco-table-host"></div>');
			$list.before($host);
		}
		$list.addClass("hr-checkin-native-list");
		if (listview.$hr_checkin_table_app || !window.OrgUI?.mountEmployeeCheckinTable) {
			return;
		}
		listview.$hr_checkin_table_app = window.OrgUI.mountEmployeeCheckinTable(
			$host.get(0),
			{},
			{
				onOpen(row) {
					if (row?.name) frappe.set_route("Form", DOCTYPE, row.name);
				},
				onSort(order) {
					const nextOrder = order === "asc" ? "asc" : "desc";
					listview.sort_selector?.set_value?.("time", nextOrder);
					window.OrgUI?.updateEmployeeCheckinTable?.({ sortOrder: nextOrder });
					if (typeof listview.on_sort_change === "function") {
						listview.on_sort_change("time", nextOrder);
					} else {
						listview.sort_by = "time";
						listview.sort_order = nextOrder;
						listview.refresh();
					}
				},
			}
		);
		sync_arco_table(listview);
	}

	function sync_arco_table(listview) {
		if (!window.OrgUI?.updateEmployeeCheckinTable) return;
		window.OrgUI.updateEmployeeCheckinTable({
			rows: Array.isArray(listview?.data) ? listview.data.slice() : [],
			total: Number(listview?.total_count || listview?.data?.length || 0),
			loading: false,
			sortOrder: listview?.sort_order === "asc" ? "asc" : "desc",
		});
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
		$card.find(".hr-emp-table-count").text(`${__("共")} ${total} ${__("条")}`);
	}

	function inject_stat_board(listview) {
		const $section = listview.$page.find(".layout-main-section");
		if (!$section.length) {
			return;
		}
		$section.addClass("hr-checkin-list-page");
		enhance_list_shell(listview);
		const $existing = $section.find(".hr-checkin-list-stats").first();
		if ($existing.length) {
			listview.$hr_checkin_stats = $existing;
			return;
		}
		try {
			listview.$hr_checkin_overview_app?.unmount?.();
		} catch (error) {
			console.warn("[employee-checkin] overview unmount failed", error);
		}

		const $board = $(`
			<div class="hr-roster-page hr-checkin-list-stats">
				<div class="hr-checkin-overview-root"></div>
			</div>
		`);

		const $page_form = $section.find(".page-form").first();
		if ($page_form.length) {
			$page_form.after($board);
		} else {
			$section.prepend($board);
		}

		listview.$hr_checkin_stats = $board;
		const mountEl = $board.find(".hr-checkin-overview-root").get(0);
		if (!mountEl || !window.OrgUI?.mountEmployeeCheckinOverview) {
			return;
		}
		listview.$hr_checkin_overview_app = window.OrgUI.mountEmployeeCheckinOverview(mountEl, {}, {
			onFilter: async (resultKey) => {
				const current = listview._checkin_result_filter;
				if (current === resultKey) {
					listview._checkin_result_filter = null;
					await clear_employee_in_filter(listview);
				} else {
					listview._checkin_result_filter = resultKey;
					await apply_result_drilldown(listview, resultKey);
				}
				sync_stat_active(listview);
			},
		});
	}

	function bind_stat_board(listview) {
		/* Vue overview handles click via onFilter */
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
		const dash = listview._checkin_dashboard || {};
		const stats = dash.stats || {
			present: 0,
			both_punches: 0,
			late: 0,
			missing: 0,
		};
		window.OrgUI?.updateEmployeeCheckinOverview?.({
			stats,
			rangeLabel: format_range_label(dash),
			activeResult: listview._checkin_result_filter || null,
			loading: false,
		});
	}

	function sync_stat_active(listview) {
		window.OrgUI?.updateEmployeeCheckinOverview?.({
			activeResult: listview._checkin_result_filter || null,
		});
	}
})();
