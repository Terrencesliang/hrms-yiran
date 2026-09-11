import { call } from "./frappe";
export { uploadFile } from "./frappe";

export type EmployeeCenterView =
	| "home"
	| "onboarding"
	| "subsidy"
	| "job-change"
	| "resignation"
	| "handover"
	| "applications";

export interface EmployeeSummary {
	name: string;
	employee_name: string;
	employee_number: string;
	status: string;
	department: string;
	designation: string;
	company: string;
	branch: string;
	employment_type: string;
	date_of_joining: string;
	image: string;
	reports_to: string;
	reports_to_name: string;
}

export interface EmployeeCenterModule {
	key: Exclude<EmployeeCenterView, "home" | "applications">;
	title: string;
	description: string;
	available: boolean;
	approval_form: string;
	approval_form_name: string;
}

export interface ApplicationRow {
	name: string;
	application_no: string;
	approval_form: string;
	form_title: string;
	status: string;
	status_key: string;
	current_node_label: string;
	creation: string;
	modified: string;
	finished_on: string;
	submitted_at: string;
}

export interface EmployeeCenterContext {
	employee: EmployeeSummary | null;
	profile: { completed: number; total: number; percent: number; missing: string[] };
	application_stats: Record<string, number>;
	modules: EmployeeCenterModule[];
	capabilities: {
		can_use_employee_center: boolean;
		can_submit: boolean;
		can_manage_hr: boolean;
		can_approve: boolean;
	};
}

const API_ROOT = "employee_roster.hr_roster.api.employee_center";
const APPROVAL_ROOT = "employee_roster.hr_roster.approval_runtime";

export function getEmployeeCenterContext() {
	return call(`${API_ROOT}.get_context`) as Promise<EmployeeCenterContext>;
}

export function listMyApplications(args: {
	status?: string;
	application_type?: string;
	date_from?: string;
	date_to?: string;
	keyword?: string;
	limit_start?: number;
	page_length?: number;
}) {
	return call(`${API_ROOT}.list_my_applications`, args) as Promise<{
		rows: ApplicationRow[];
		has_more: boolean;
		next_start: number;
	}>;
}

export function getApplicationDetail(instanceName: string) {
	return call(`${APPROVAL_ROOT}.get_workspace_detail`, {
		instance_name: instanceName,
	}) as Promise<any>;
}

export function cancelApplication(instanceName: string, comment = "员工本人撤回") {
	return call(`${APPROVAL_ROOT}.cancel_approval`, {
		instance_name: instanceName,
		comment,
	});
}

export function getApplicationSetup(applicationType: string, instanceName?: string) {
	return call(`${API_ROOT}.get_application_setup`, {
		application_type: applicationType,
		instance_name: instanceName,
	}) as Promise<any>;
}

export function saveEmployeeApplication(
	applicationType: string,
	payload: Record<string, unknown>,
	options: { instanceName?: string; submit?: boolean } = {},
) {
	return call(`${API_ROOT}.save_application`, {
		application_type: applicationType,
		payload,
		instance_name: options.instanceName,
		submit: options.submit ? 1 : 0,
	}) as Promise<{ name: string; application_no: string; status: string }>;
}

export function deleteApplicationDraft(instanceName: string) {
	return call(`${API_ROOT}.delete_draft`, { instance_name: instanceName });
}
