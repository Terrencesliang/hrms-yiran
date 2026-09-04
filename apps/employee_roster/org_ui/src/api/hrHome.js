import { call } from "./frappe.js";

export function getHrWorkplace(company) {
	return call("employee_roster.hr_roster.api.hr_home.get_hr_workplace", {
		company: company || undefined,
	});
}

export function getHrDashboard(company) {
	return call("employee_roster.hr_roster.api.hr_home.get_hr_dashboard", {
		company: company || undefined,
	});
}
