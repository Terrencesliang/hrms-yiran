import { call } from "./frappe.js";

export function getRulesOverview() {
	return call("employee_roster.hr_roster.page.attendance_rules.attendance_rules.get_rules_overview");
}

export function deleteDeductionRule(name) {
	return call("frappe.client.delete", {
		doctype: "Attendance Deduction Rule",
		name,
	});
}
