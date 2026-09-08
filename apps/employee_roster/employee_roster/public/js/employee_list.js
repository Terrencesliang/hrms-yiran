// Copyright (c) 2026 stillgroup
// License: MIT
/**
 * Employee List View — Arco Design Pro 风格：
 * 人员概览 data-panel + 筛选卡片 + 列表卡片 + 状态/雇佣类型 Tag
 */
(function () {
	const DOCTYPE = "Employee";

	const prev = frappe.listview_settings[DOCTYPE] || {};
	const prev_onload = prev.onload;
	const prev_refresh = prev.refresh;
	const prev_before_render = prev.before_render;
	const prev_formatters = prev.formatters || {};

	frappe.listview_settings[DOCTYPE] = Object.assign({}, prev, {
		add_fields: Array.from(
			new Set([
				...(prev.add_fields || []),
				"employee_name",
				"image",
				"status",
				"employment_type",
				"designation",
				"department",
				"group_name",
				"branch",
				"date_of_joining",
				"cell_number",
				"company_email",
			]),
		),

		onload(listview) {
			if (typeof prev_onload === "function") {
				prev_onload(listview);
			}
			set_default_sort(listview);
			enhance_list_shell(listview);
			inject_stat_board(listview);
			refresh_stat_board(listview);
			queue_employee_table_sync(listview);
		},

		before_render() {
			if (typeof prev_before_render === "function") {
				prev_before_render();
			}
			const listview = cur_list;
			if (listview && listview.doctype === DOCTYPE) {
				queue_employee_table_sync(listview);
			}
		},

		refresh(listview) {
			if (typeof prev_refresh === "function") {
				prev_refresh(listview);
			}
			enhance_list_shell(listview);
			if (
				!listview.$hr_stat_board ||
				!listview.$hr_stat_board.length ||
				!document.documentElement.contains(listview.$hr_stat_board.get(0))
			) {
				inject_stat_board(listview);
			}
			refresh_stat_board(listview);
			sync_list_toolbar(listview);
			queue_employee_table_sync(listview);
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
		const $page = listview.$page;
		$page.addClass("arco-hr-employee-list-wrapper");

		const $section = listview.$page.find(".layout-main-section");
		if (!$section.length) {
			return;
		}
		$section.addClass("hr-employee-list-page hr-desk-content-stack");

		const $layoutMain = listview.$page.find(".layout-main").first();
		if ($layoutMain.length) {
			$layoutMain.addClass("row");
		}
		listview.$page.find(".layout-side-section").hide();
		listview.$page
			.find(".layout-main-section-wrapper")
			.addClass("col-md-12")
			.css({ flex: "1 1 100%", maxWidth: "100%", width: "100%" });

		$section.find("#hr-employee-list-header-root").remove();

		if (!$section.find("#hr-employee-list-header-root").length) {
			const $header = $('<div id="hr-employee-list-header-root" class="hr-desk-header-host"></div>');
			$section.prepend($header);
			if (window.OrgUI?.mountEmployeeListDeskHeader) {
				try {
					listview.$hr_desk_header_app?.unmount?.();
				} catch (error) {
					console.warn("[employee-list] desk header unmount failed", error);
				}
				listview.$hr_desk_header_app = window.OrgUI.mountEmployeeListDeskHeader($header.get(0));
			}
		}

		const $form = $section.find(".page-form").first();
		if ($form.length) {
			$form.addClass("hr-emp-filter-card");
			$form
				.find('[aria-label="Clear all filters"], [title="Clear all filters"]')
				.attr({ "aria-label": __("清除全部筛选"), title: __("清除全部筛选") });
			$form
				.find('[data-fieldname="employee_name"] input')
				.attr({ placeholder: __("姓名"), "aria-label": __("姓名") });
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
		$list.addClass("hr-employee-native-list");
		mount_employee_table(listview, $list);
		sync_list_toolbar(listview);
	}

	function set_default_sort(listview) {
		if (listview._hr_employee_sort_initialized) return;
		listview._hr_employee_sort_initialized = true;
		listview.sort_by = "employee_name";
		listview.sort_order = "asc";
		listview.sort_selector?.set_value?.("employee_name", "asc");
	}

	function mount_employee_table(listview, $list) {
		const $card = $list.closest(".hr-emp-table-card");
		if (!$card.length || $card.find(".hr-employee-arco-table-host").length) return;

		const $host = $('<div class="hr-employee-arco-table-host"></div>');
		$card.find(".hr-emp-table-toolbar").after($host);
		if (!window.OrgUI?.mountEmployeeRosterTable) return;

		listview.$hr_employee_table_app = window.OrgUI.mountEmployeeRosterTable(
			$host.get(0),
			{},
			{
				onOpen(record) {
					if (record?.name) frappe.set_route("Form", DOCTYPE, record.name);
				},
				onSort(field, order) {
					const nextField = field === "date_of_joining" ? "date_of_joining" : "employee_name";
					const nextOrder = order === "desc" ? "desc" : "asc";
					listview.sort_by = nextField;
					listview.sort_order = nextOrder;
					listview.sort_selector?.set_value?.(nextField, nextOrder);
					if (typeof listview.on_sort_change === "function") {
						listview.on_sort_change(nextField, nextOrder);
					} else {
						listview.refresh?.();
					}
				},
			},
		);
	}

	function sync_employee_table(listview) {
		if (!window.OrgUI?.updateEmployeeRosterTable) return;
		const sortBy = ["employee_name", "date_of_joining"].includes(listview.sort_by)
			? listview.sort_by
			: "employee_name";
		window.OrgUI.updateEmployeeRosterTable({
			rows: listview.data || [],
			total: listview.total_count ?? (listview.data || []).length,
			loading: false,
			sortBy,
			sortOrder: listview.sort_order === "desc" ? "desc" : "asc",
		});
	}

	function queue_employee_table_sync(listview) {
		window.clearTimeout(listview._hr_employee_table_sync_timer);
		window.clearTimeout(listview._hr_employee_table_count_timer);
		listview._hr_employee_table_sync_timer = window.setTimeout(() => {
			sync_employee_table(listview);
			sync_list_toolbar(listview);
		}, 0);
		listview._hr_employee_table_count_timer = window.setTimeout(() => {
			sync_employee_table(listview);
			sync_list_toolbar(listview);
			localize_paging_controls(listview);
		}, 600);
	}

	function localize_paging_controls(listview) {
		const $card = listview.$hr_emp_table;
		if (!$card?.length) return;
		$card
			.find('.list-paging-area [role="radiogroup"]')
			.attr("aria-label", __("每页条数"));
	}

	function sync_list_toolbar(listview) {
		const $card = listview.$hr_emp_table;
		if (!$card || !$card.length) {
			return;
		}
		const total = listview.total_count ?? (listview.data && listview.data.length) ?? 0;
		$card.find(".hr-emp-table-count").text(`${__("共")} ${total} ${__("人")}`);
	}

	function inject_stat_board(listview) {
		const $section = listview.$page.find(".layout-main-section");
		if (!$section.length) {
			return;
		}

		$section.addClass("hr-employee-list-page");
		enhance_list_shell(listview);
		const $existing = $section.find(".hr-employee-list-stats").first();
		if ($existing.length) {
			listview.$hr_stat_board = $existing;
			return;
		}
		try {
			listview.$hr_employee_overview_app?.unmount?.();
		} catch (error) {
			console.warn("[employee-list] overview unmount failed", error);
		}

		const $board = $(`
			<div class="hr-roster-page hr-employee-list-stats">
				<div class="hr-employee-list-overview-root"></div>
			</div>
		`);

		const $page_form = $section.find(".page-form").first();
		if ($page_form.length) {
			$page_form.after($board);
		} else {
			$section.prepend($board);
		}

		listview.$hr_stat_board = $board;
		const mountEl = $board.find(".hr-employee-list-overview-root").get(0);
		if (!mountEl || !window.OrgUI?.mountEmployeeListOverview) return;
		listview.$hr_employee_overview_app = window.OrgUI.mountEmployeeListOverview(mountEl, {}, {
			onFilter: async (item) => {
				const current = get_filter_value(listview, item.field);
				const currentOp = get_filter_operator(listview, item.field);
				if (current === item.valueKey && currentOp === item.operator) {
					await remove_filter(listview, item.field);
				} else {
					await set_filter(listview, item.field, item.valueKey, item.operator);
				}
				sync_stat_active(listview.$hr_stat_board, listview);
			},
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
				window.OrgUI?.updateEmployeeListOverview?.({
					total: r.message.total || 0,
					active: r.message.active || 0,
					inactive: r.message.inactive || 0,
					left: r.message.left || 0,
					employmentCounts: r.message.employment_counts || {},
					filters: current_filters(listview),
				});
			},
		});
	}

	function current_filters(listview) {
		return ((listview.filter_area && listview.filter_area.get()) || []).map((filter) => ({
			field: filter[1],
			operator: filter[2],
			value: filter[3],
		}));
	}

	function sync_stat_active($wrap, listview) {
		window.OrgUI?.updateEmployeeListOverview?.({ filters: current_filters(listview) });
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
