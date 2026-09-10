import { call, uploadFile } from "./frappe.js";

export function getEmployeeArchive(employee) {
	return call("employee_roster.hr_roster.employee_detail.get_employee_archive", { employee });
}

export function getEmployeeOverview(employee) {
	return call("employee_roster.hr_roster.employee_detail.get_employee_overview", { employee });
}

export function saveEmployeeSection(employee, section, data) {
	return call("employee_roster.hr_roster.employee_detail.save_employee_section", {
		employee,
		section,
		data,
	});
}

export function saveEmployeeChildRow(employee, table_key, row, deleteFlag = 0) {
	return call("employee_roster.hr_roster.employee_detail.save_employee_child_row", {
		employee,
		table_key,
		row,
		delete: deleteFlag,
	});
}

export function saveEmployeeMaterial(employee, fieldname, file_url = "") {
	return call("employee_roster.hr_roster.employee_detail.save_employee_material", {
		employee,
		fieldname,
		file_url,
	});
}

export { uploadFile };
