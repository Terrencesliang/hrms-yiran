import { call } from "./frappe";

export interface MenuChild {
	key: string;
	label: string;
	link_type: string;
	target: string;
}

export interface MenuGroup {
	key: string;
	module: string;
	label: string;
	icon: string;
	children: MenuChild[];
}

export interface BusinessRole {
	name: string;
	role_title: string;
	role_category: "系统角色" | "自定义角色";
	is_system_role: number;
	description: string;
	assigned_count: number;
}

export interface PermissionContext {
	company: string;
	companies: string[];
	roles: BusinessRole[];
	selected_role: string;
	selected_menu_keys: string[];
	menu_catalog: MenuGroup[];
	is_platform_admin: boolean;
}

export interface RoleAssignmentNode {
	key?: string;
	name: string;
	title: string;
	is_company?: boolean;
	is_employee?: boolean;
	org_type?: string;
	employee?: string;
	employee_number?: string;
	designation?: string;
	employee_count?: number;
	status?: string;
	user_id?: string;
	image?: string;
	assigned_roles?: string[];
	children?: RoleAssignmentNode[];
}

export interface RoleAssignmentContext {
	company: string;
	companies: string[];
	is_platform_admin: boolean;
	roles: BusinessRole[];
	roots: RoleAssignmentNode[];
	organization_count: number;
}

const ROOT = "employee_roster.hr_roster.menu_permissions";

export function getPermissionManagementContext(company?: string, role?: string) {
	return call(`${ROOT}.get_permission_management_context`, { company, role }) as Promise<PermissionContext>;
}

export function saveRoleMenuPermissions(role: string, menuKeys: string[]) {
	return call(`${ROOT}.save_role_menu_permissions`, { role, menu_keys: menuKeys }) as Promise<{ message: string; menu_keys: string[] }>;
}

export function createBusinessRole(args: { company: string; role_title: string; description?: string; copy_from?: string }) {
	return call(`${ROOT}.create_business_role`, args) as Promise<{ name: string; role_title: string; message: string }>;
}

export function getRoleAssignmentContext(company?: string) {
	return call(`${ROOT}.get_role_assignment_context`, { company }) as Promise<RoleAssignmentContext>;
}

export function assignBusinessRoles(user: string, company: string, roles: string[]) {
	return call(`${ROOT}.assign_business_roles`, { user, company, roles }) as Promise<{ message: string; roles: string[] }>;
}

export function assignBusinessRolesBulk(users: string[], company: string, roles: string[]) {
	return call(`${ROOT}.assign_business_roles_bulk`, { users, company, roles }) as Promise<{ message: string; count: number; roles: string[] }>;
}
