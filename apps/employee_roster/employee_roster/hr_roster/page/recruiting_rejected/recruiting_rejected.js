// Copyright (c) 2026 stillgroup
// License: MIT

frappe.pages["recruiting-rejected"].on_page_load = function (wrapper) {
	init_recruiting_list_page(wrapper, { title: __("已淘汰"), status: "Rejected" });
};
