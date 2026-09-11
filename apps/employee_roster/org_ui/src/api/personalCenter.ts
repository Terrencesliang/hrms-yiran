import { call } from "./frappe";

export interface PersonalCenterAccount {
	user_id: string;
	username: string;
	full_name: string;
	avatar: string;
	enabled: boolean;
	last_login: string;
	last_password_reset_date: string;
	must_change_password: boolean;
	roles: string[];
}

export interface PersonalCenterEmployee {
	name: string;
	employee_name: string;
	employee_number: string;
	status: string;
	image: string;
	company: string;
	department: string;
	group_name: string;
	designation: string;
	branch: string;
	employment_type: string;
	date_of_joining: string;
	gender: string;
	date_of_birth: string;
	cell_number: string;
	personal_email: string;
	company_email: string;
	current_address: string;
	reports_to_name: string;
	wecom_bound: boolean;
}

export interface PersonalCenterContext {
	account: PersonalCenterAccount;
	employee: PersonalCenterEmployee | null;
}

const API_ROOT = "employee_roster.hr_roster.api.personal_center";

export function getPersonalCenterContext() {
	return call(`${API_ROOT}.get_context`) as Promise<PersonalCenterContext>;
}

export function changeMyPassword(payload: {
	current_password: string;
	new_password: string;
	confirm_password: string;
}) {
	return call(`${API_ROOT}.change_my_password`, payload) as Promise<{
		message: string;
		must_change_password: boolean;
	}>;
}
