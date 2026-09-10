// Copyright (c) 2026 stillgroup
// License: MIT
/**
 * Employee List View — Arco Design 员工名录工作区：
 * 轻量状态导航 + 组合搜索 + 表格懒加载。
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
			set_lazy_page_size(listview);
			enhance_list_shell(listview);
			enable_automatic_refresh(listview);
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
			refresh_stat_board(listview);
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
				listview.$hr_desk_header_app = window.OrgUI.mountEmployeeListDeskHeader(
					$header.get(0),
					{ canCreate: !!frappe.model?.can_create?.(DOCTYPE) },
					{ onCreate: () => frappe.new_doc(DOCTYPE) },
				);
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
		}
		listview.$hr_emp_table = $list.closest(".hr-emp-table-card");
		listview.$hr_emp_table.find(".hr-emp-table-toolbar").remove();
		$list.addClass("hr-employee-native-list");
		mount_employee_table(listview, $list);
	}

	function set_default_sort(listview) {
		if (listview._hr_employee_sort_initialized) return;
		listview._hr_employee_sort_initialized = true;
		listview.sort_by = "employee_number";
		listview.sort_order = "asc";
		listview.sort_selector?.set_value?.("employee_number", "asc");
	}

	function set_lazy_page_size(listview) {
		if (listview._hr_employee_lazy_size_initialized) return;
		listview._hr_employee_lazy_size_initialized = true;
		listview.start = 0;
		listview.page_length = 2500;
	}

	function enable_automatic_refresh(listview) {
		if (listview._hr_employee_auto_refresh_initialized) return;
		listview._hr_employee_auto_refresh_initialized = true;

		const refreshWhenVisible = () => {
			if (window.cur_list !== listview || listview.doctype !== DOCTYPE) return;
			window.clearTimeout(listview._hr_employee_auto_refresh_timer);
			listview._hr_employee_auto_refresh_timer = window.setTimeout(() => {
				listview.start = 0;
				listview.refresh?.();
			}, 250);
		};

		frappe.realtime?.on?.("list_update", (event) => {
			if (event?.doctype === DOCTYPE) refreshWhenVisible();
		});
		frappe.router?.on?.("change", () => {
			const route = frappe.get_route?.() || [];
			if (route[0] === "List" && route[1] === DOCTYPE) refreshWhenVisible();
		});
	}

	function mount_employee_table(listview, $list) {
		const $card = $list.closest(".hr-emp-table-card");
		if (!$card.length || $card.find(".hr-employee-arco-table-host").length) return;

		const $host = $('<div class="hr-employee-arco-table-host"></div>');
		$card.prepend($host);
		if (!window.OrgUI?.mountEmployeeRosterTable) return;

		listview.$hr_employee_table_app = window.OrgUI.mountEmployeeRosterTable(
			$host.get(0),
			{},
			{
				onCreate() {
					frappe.new_doc(DOCTYPE);
				},
				onFilterOpen() {
					const $button = listview.$page.find(".page-form .filter-button").first();
					if ($button.length) $button.trigger("click");
				},
				onStatusFilter: async (item) => {
					const current = get_filter_value(listview, item.field);
					const currentOp = get_filter_operator(listview, item.field);
					if (current === item.valueKey && currentOp === (item.operator || "=")) {
						await remove_filter(listview, item.field);
					} else {
						await clear_status_filters(listview);
						await set_filter(listview, item.field, item.valueKey, item.operator || "=");
					}
					queue_employee_table_sync(listview);
				},
				onClearStatus: async () => {
					await clear_status_filters(listview);
					queue_employee_table_sync(listview);
				},
				onOpen(record) {
					if (record?.name) frappe.set_route("Form", DOCTYPE, record.name);
				},
				onSort(field, order) {
					const nextField = field === "date_of_joining" ? "date_of_joining" : "employee_number";
					const nextOrder = order === "desc" ? "desc" : "asc";
					listview.sort_by = nextField;
					listview.sort_order = nextOrder;
					listview.sort_selector?.set_value?.(nextField, nextOrder);
					// 先同步前端状态，立刻按数值重排，避免等列表刷新时倒序被字符串序打乱
					window.OrgUI?.updateEmployeeRosterTable?.({
						sortBy: nextField,
						sortOrder: nextOrder,
					});
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
		const sortBy = ["employee_number", "date_of_joining"].includes(listview.sort_by)
			? listview.sort_by
			: "employee_number";
		window.OrgUI.updateEmployeeRosterTable({
			rows: listview.data || [],
			loading: false,
			canCreate: !!frappe.model?.can_create?.(DOCTYPE),
			canDelete: !!frappe.model?.can_delete?.(DOCTYPE),
			filters: current_filters(listview),
			activeFilterCount: current_filters(listview).length,
			sortBy,
			sortOrder: listview.sort_order === "desc" ? "desc" : "asc",
		});
	}

	function queue_employee_table_sync(listview) {
		window.clearTimeout(listview._hr_employee_table_sync_timer);
		window.clearTimeout(listview._hr_employee_table_count_timer);
		listview._hr_employee_table_sync_timer = window.setTimeout(() => {
			sync_employee_table(listview);
		}, 0);
		listview._hr_employee_table_count_timer = window.setTimeout(() => {
			sync_employee_table(listview);
		}, 600);
	}

	function refresh_stat_board(listview) {
		const company = get_filter_value(listview, "company") || "";

		frappe.call({
			method: "employee_roster.hr_roster.page.roster.roster.get_employee_stats",
			args: { company },
			callback(r) {
				if (!r.message) return;
				window.OrgUI?.updateEmployeeRosterTable?.({
					total: r.message.total || 0,
					active: r.message.active || 0,
					left: r.message.left || 0,
					employmentCounts: r.message.employment_counts || {},
					filters: current_filters(listview),
					activeFilterCount: current_filters(listview).length,
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

	async function clear_status_filters(listview) {
		for (const fieldname of ["status", "designation", "employment_type"]) {
			if (get_filter_value(listview, fieldname)) await remove_filter(listview, fieldname);
		}
	}
})();
