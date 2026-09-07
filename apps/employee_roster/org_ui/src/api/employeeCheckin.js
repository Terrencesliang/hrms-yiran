import { call } from "./frappe.js";

export function getCheckinDashboard(args = {}) {
	return call("employee_roster.hr_roster.api.employee_checkin_dashboard.get_checkin_dashboard", args);
}
