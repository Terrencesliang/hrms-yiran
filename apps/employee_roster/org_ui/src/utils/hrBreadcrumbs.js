/** 与 unified_sidebar MODULE_TAB_LABELS["HR Setup"] 一致 */
export const HR_MODULE_LABEL = "人事";

/** 与 unified_sidebar MODULE_TAB_LABELS["Shift & Attendance"] 一致 */
export const ATTENDANCE_MODULE_LABEL = "考勤";

/** Arco Pro 风格 HR 页面包屑：{模块} / {页面} */
export function hrPageBreadcrumbs(pageLabel, moduleLabel = HR_MODULE_LABEL) {
	const items = [{ label: moduleLabel }];
	if (pageLabel) {
		items.push({ label: pageLabel });
	}
	return items;
}

export function navigateHrRoute(route) {
	if (!route || typeof window === "undefined") {
		return;
	}
	if (window.frappe?.set_route) {
		window.frappe.set_route(route);
	}
}
