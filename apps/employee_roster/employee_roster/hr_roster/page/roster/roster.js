// Copyright (c) 2026 stillgroup
// License: MIT

// 兼容历史收藏与外部链接；员工主数据统一由 List/Employee 承担。
frappe.pages["roster"].on_page_load = function () {
	frappe.set_route("List", "Employee");
};
