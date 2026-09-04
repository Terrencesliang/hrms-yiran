const VISIBLE_APPS = new Set(["frappe", "hrms"]);

function hide_erpnext_from_apps_screen() {
	const boot = window.frappe?.boot;
	if (!boot) return;

	if (Array.isArray(boot.apps_data?.apps)) {
		boot.apps_data.apps = boot.apps_data.apps.filter((app) => VISIBLE_APPS.has(app.name));
	}
	if (Array.isArray(boot.app_data)) {
		boot.app_data = boot.app_data.filter((app) => VISIBLE_APPS.has(app.app_name));
	}
}

// app_include_js runs after boot data is available and before the initial Desk
// route is rendered. Running again on frappe.ready also covers cached boot flows.
hide_erpnext_from_apps_screen();
frappe.ready(hide_erpnext_from_apps_screen);
