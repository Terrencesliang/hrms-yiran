import { createApp, h, reactive } from "vue";
import ArcoVue from "@arco-design/web-vue";
import ArcoVueIcon from "@arco-design/web-vue/es/icon";
import { ConfigProvider, Message } from "@arco-design/web-vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import "@arco-design/web-vue/dist/arco.css";
import "./styles.css";
import "./styles/hr-foundation.css";
import OrgChartPage from "./pages/orgchart/OrgChartPage.vue";
import OrgDiagramPage from "./pages/orgdiagram/OrgDiagramPage.vue";
import SidebarApp from "./pages/sidebar/SidebarApp.vue";
import NavbarApp from "./pages/navbar/NavbarApp.vue";
import EmployeeFormChrome from "./components/EmployeeFormChrome.vue";
import EmployeeArchivePanels from "./components/employee-detail/EmployeeArchivePanels.vue";
import EmployeeListOverview from "./components/EmployeeListOverview.vue";
import EmployeeRosterTable from "./components/EmployeeRosterTable.vue";
import ApprovalsApp from "./pages/approvals/ApprovalsApp.vue";
import ApprovalDesignerApp from "./pages/approvals/designer/ApprovalDesignerApp.vue";
import ApprovalsWorkspace from "./pages/approvals/workspace/ApprovalsWorkspace.vue";
import HrHomePage from "./pages/home/HrHomePage.vue";
import HrDashboardPage from "./pages/dashboard/HrDashboardPage.vue";
import ContractOverviewPage from "./pages/contract/ContractOverviewPage.vue";
import ContractTemplatesPage from "./pages/contract/ContractTemplatesPage.vue";
import ContractSigningListPage from "./pages/contract/ContractSigningListPage.vue";
import ContractInitiatePage from "./pages/contract/ContractInitiatePage.vue";
import ContractSealsPage from "./pages/contract/ContractSealsPage.vue";
import ContractPackagesPage from "./pages/contract/ContractPackagesPage.vue";
import ContractArchivePage from "./pages/contract/ContractArchivePage.vue";
import EmployeeListDeskHeader from "./pages/employee_list/EmployeeListDeskHeader.vue";
import EmployeeFormDeskHeader from "./pages/employee_form/EmployeeFormDeskHeader.vue";
import EmployeeArchiveDeskHeader from "./pages/employee_archive/EmployeeArchiveDeskHeader.vue";
import EmployeeCheckinDeskHeader from "./pages/employee_checkin/EmployeeCheckinDeskHeader.vue";
import EmployeeCheckinOverview from "./components/EmployeeCheckinOverview.vue";
import EmployeeCheckinTable from "./components/EmployeeCheckinTable.vue";
import AttendanceRulesPage from "./pages/attendance_rules/AttendanceRulesPage.vue";
import AttendanceRulesDeskHeader from "./pages/attendance_rules/AttendanceRulesDeskHeader.vue";
import EmployeeCenterPage from "./pages/employee_center/EmployeeCenterPage.vue";
import PermissionManagementPage from "./pages/permission_management/PermissionManagementPage.vue";
import RoleAssignmentPage from "./pages/role_assignment/RoleAssignmentPage.vue";
import PersonalCenterPage from "./pages/personal_center/PersonalCenterPage.vue";

/** Keep Arco / Desk dark mode in sync when OrgUI mounts after a Desk route change. */
function syncArcoTheme() {
	try {
		const stored = localStorage.getItem("arco-theme");
		const current =
			stored ||
			document.body.getAttribute("arco-theme") ||
			document.body.getAttribute("data-theme") ||
			"light";
		const theme = current === "dark" ? "dark" : "light";
		document.body.setAttribute("data-theme", theme);
		document.body.setAttribute("arco-theme", theme);
		document.documentElement.setAttribute("data-theme", theme);
		document.documentElement.setAttribute("arco-theme", theme);
	} catch (e) {
		/* ignore */
	}
}

function boot(app) {
	syncArcoTheme();
	app.use(ArcoVue);
	app.use(ArcoVueIcon);
	return app;
}

export function notify({ type = "info", content = "" } = {}) {
	const method = ["success", "warning", "error", "info"].includes(type) ? type : "info";
	Message[method](String(content || ""));
}

/** Register a new HR page here: mountXxx(el) → boot(createApp(Page)). */
export function mountOrgChart(el) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(OrgChartPage));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountOrgDiagram(el) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(OrgDiagramPage));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountApprovals(el, options = {}) {
	const tab = options.tab === "templates" ? "templates" : "forms";
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(ApprovalsApp, { tab }));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountApprovalDesigner(el, options = {}) {
	const formName = options.formName || "";
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () =>
					h(ApprovalDesignerApp, { formName })
				);
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountApprovalsWorkspace(el, options = {}) {
	const view = options.view || "todo";
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () =>
					h(ApprovalsWorkspace, { view })
				);
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountHrHome(el) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(HrHomePage));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountHrDashboard(el) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(HrDashboardPage));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountEmployeeCenter(el, options = {}) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () =>
					h(EmployeeCenterPage, {
						view: options.view || "home",
						instanceName: options.instanceName || "",
					})
				);
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountPersonalCenter(el) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(PersonalCenterPage));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountPermissionManagement(el) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(PermissionManagementPage));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountRoleAssignment(el) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(RoleAssignmentPage));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountContractOverview(el) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(ContractOverviewPage));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountContractTemplates(el) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(ContractTemplatesPage));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountContractSigning(el, options = {}) {
	const status = options.status || "pending";
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () =>
					h(ContractSigningListPage, { status })
				);
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountContractInitiate(el, options = {}) {
	const templateId = options.templateId || "";
	const providerTemplateId = options.providerTemplateId || "";
	const templateName = options.templateName || "";
	const mode = options.mode === "batch" ? "batch" : "single";
	const openPicker = options.openPicker !== false;
	const sealId = options.sealId || "";
	const businessId = options.businessId || "";
	const employeeActorId = options.employeeActorId || "";
	const corpActorId = options.corpActorId || "";
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () =>
					h(ContractInitiatePage, {
						templateId,
						providerTemplateId,
						templateName,
						mode,
						openPicker,
						sealId,
						businessId,
						employeeActorId,
						corpActorId,
					})
				);
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountContractSeals(el) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(ContractSealsPage));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountContractPackages(el) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(ContractPackagesPage));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountContractArchive(el) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(ContractArchivePage));
			},
		})
	);
	app.mount(el);
	return app;
}

const sidebarState = reactive({
	title: "",
	tabs: [],
	activeTab: "",
	activeKey: "",
	groups: [],
	workspaces: [],
	searchShortcut: "Ctrl+K",
	compact: false,
});

const sidebarHandlers = {
	onWorkspace: null,
	onCollapse: null,
	onToggleCompact: null,
	onSearch: null,
	onTabChange: null,
	onNavigate: null,
};

export function mountSidebar(el, handlers = {}) {
	Object.assign(sidebarHandlers, handlers);
	const app = boot(createApp(SidebarApp));
	app.provide("sidebarState", sidebarState);
	app.provide("sidebarHandlers", sidebarHandlers);
	app.mount(el);
	return app;
}

export function updateSidebar(payload) {
	Object.assign(sidebarState, payload || {});
}

const navbarState = reactive({
	title: "HR Pro",
	user: "",
	fullName: "",
	avatar: "",
	notificationCount: 0,
});

const navbarHandlers = {
	onSearch: null,
	onNotifications: null,
	onSettings: null,
	onProfile: null,
	onLogout: null,
	onThemeChange: null,
};

export function mountNavbar(el, handlers = {}) {
	Object.assign(navbarHandlers, handlers);
	const app = boot(createApp(NavbarApp));
	app.provide("navbarState", navbarState);
	app.provide("navbarHandlers", navbarHandlers);
	app.mount(el);
	return app;
}

export function updateNavbar(payload) {
	Object.assign(navbarState, payload || {});
}

const employeeFormState = reactive({
	name: "",
	employee_name: "",
	employee_number: "",
	status: "",
	department: "",
	designation: "",
	company: "",
	branch: "",
	group_name: "",
	employment_type: "",
	employment_type_label: "",
	image: "",
	date_of_joining: "",
	cell_number: "",
	company_email: "",
	personal_email: "",
	reports_to: "",
	grade: "",
	gender: "",
	marital_status: "",
	blood_group: "",
	passport_number: "",
	health_insurance_provider: "",
	health_insurance_no: "",
	default_shift: "",
	person_to_be_contacted: "",
	emergency_phone_number: "",
	relation: "",
	bio_text: "",
	hr_job_title: "",
	hr_position_category: "",
	hr_work_city: "",
	hr_work_location: "",
	hr_employee_identity: "",
	hr_oa_code: "",
	attendance_device_id: "",
	education_summary: "",
	probation_days_remaining: null,
	late_count: null,
	overtime_hours: null,
	education: [],
	external_work_history: [],
	internal_work_history: [],
	tenure_days: null,
	leave_balance: null,
	attendance_month: null,
	related_count: 0,
	profile_completion: 0,
	profile_missing: [],
	show_overview: true,
	can_edit: false,
	can_save: false,
	can_delete: false,
	can_create_transfer: false,
	is_new: false,
	is_editing: false,
	is_dirty: false,
	is_saving: false,
	is_deleting: false,
});

const employeeFormHandlers = {
	onNavigate: null,
};

export function mountEmployeeForm(el, payload = {}, handlers = {}) {
	Object.assign(employeeFormState, payload || {});
	Object.assign(employeeFormHandlers, handlers || {});
	const app = boot(
		createApp({
			render() {
				return h(EmployeeFormChrome, {
					state: employeeFormState,
					handlers: employeeFormHandlers,
				});
			},
		})
	);
	app.mount(el);
	return app;
}

const employeeFormDeskHeaderState = reactive({
	employeeName: "",
});

export function updateEmployeeForm(payload) {
	Object.assign(employeeFormState, payload || {});
	if ("employee_name" in (payload || {})) {
		employeeFormDeskHeaderState.employeeName = payload.employee_name || "";
	}
}

export function setEmployeeFormHandlers(handlers = {}) {
	Object.assign(employeeFormHandlers, handlers || {});
}

const employeeArchiveState = reactive({
	activeTab: "",
	loading: false,
	can_edit: false,
	resetToken: 0,
	expandSection: "",
	expandNonce: 0,
	doc: {},
});

const employeeArchiveHandlers = {
	onUpdated: null,
};

export function mountEmployeeArchivePanels(el, payload = {}, handlers = {}) {
	Object.assign(employeeArchiveState, payload || {});
	Object.assign(employeeArchiveHandlers, handlers || {});
	const app = boot(
		createApp({
			render() {
				return h(EmployeeArchivePanels, {
					state: employeeArchiveState,
					handlers: employeeArchiveHandlers,
				});
			},
		})
	);
	app.mount(el);
	return app;
}

export function updateEmployeeArchivePanels(payload = {}) {
	Object.assign(employeeArchiveState, payload || {});
}

export function setEmployeeArchiveHandlers(handlers = {}) {
	Object.assign(employeeArchiveHandlers, handlers || {});
}

const employeeListOverviewState = reactive({
	total: 0,
	active: 0,
	inactive: 0,
	left: 0,
	employmentCounts: {},
	filters: [],
});

const employeeListOverviewHandlers = {
	onFilter: null,
};

export function mountEmployeeListOverview(el, payload = {}, handlers = {}) {
	Object.assign(employeeListOverviewState, payload || {});
	Object.assign(employeeListOverviewHandlers, handlers || {});
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () =>
					h(EmployeeListOverview, {
						state: employeeListOverviewState,
						handlers: employeeListOverviewHandlers,
					})
				);
			},
		})
	);
	app.mount(el);
	return app;
}

export function updateEmployeeListOverview(payload = {}) {
	Object.assign(employeeListOverviewState, payload || {});
}

const employeeRosterTableState = reactive({
	rows: [],
	total: 0,
	active: 0,
	left: 0,
	employmentCounts: {},
	filters: [],
	activeFilterCount: 0,
	loading: false,
	sortBy: "employee_number",
	sortOrder: "asc",
	canCreate: false,
	canDelete: false,
});

const employeeRosterTableHandlers = {
	onOpen: null,
	onSort: null,
	onDelete: null,
	onCreate: null,
	onStatusFilter: null,
	onClearStatus: null,
	onFilterOpen: null,
};

export function mountEmployeeRosterTable(el, payload = {}, handlers = {}) {
	Object.assign(employeeRosterTableState, payload || {});
	Object.assign(employeeRosterTableHandlers, handlers || {});
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () =>
					h(EmployeeRosterTable, {
						state: employeeRosterTableState,
						handlers: employeeRosterTableHandlers,
					})
				);
			},
		})
	);
	app.mount(el);
	return app;
}

export function updateEmployeeRosterTable(payload = {}) {
	Object.assign(employeeRosterTableState, payload || {});
}

function mountDeskHeader(el, component, props = {}) {
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () => h(component, props));
			},
		})
	);
	app.mount(el);
	return app;
}

export function mountEmployeeListDeskHeader(el, payload = {}, handlers = {}) {
	return mountDeskHeader(el, EmployeeListDeskHeader, { state: payload, handlers });
}

export function mountEmployeeFormDeskHeader(el) {
	Object.assign(employeeFormDeskHeaderState, { employeeName: "" });
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () =>
					h(EmployeeFormDeskHeader, {
						employeeName: employeeFormDeskHeaderState.employeeName,
					})
				);
			},
		})
	);
	app.mount(el);
	return app;
}

export function updateEmployeeFormDeskHeader(payload = {}) {
	Object.assign(employeeFormDeskHeaderState, payload);
}

export function mountEmployeeArchiveDeskHeader(el) {
	return mountDeskHeader(el, EmployeeArchiveDeskHeader);
}

export function mountEmployeeCheckinDeskHeader(el) {
	return mountDeskHeader(el, EmployeeCheckinDeskHeader);
}

const employeeCheckinOverviewState = reactive({
	stats: {},
	rangeLabel: "",
	activeResult: null,
	loading: false,
});

const employeeCheckinOverviewHandlers = {
	onFilter: null,
};

export function mountEmployeeCheckinOverview(el, payload = {}, handlers = {}) {
	Object.assign(employeeCheckinOverviewState, payload || {});
	Object.assign(employeeCheckinOverviewHandlers, handlers || {});
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () =>
					h(EmployeeCheckinOverview, {
						state: employeeCheckinOverviewState,
						handlers: employeeCheckinOverviewHandlers,
					})
				);
			},
		})
	);
	app.mount(el);
	return app;
}

export function updateEmployeeCheckinOverview(payload = {}) {
	Object.assign(employeeCheckinOverviewState, payload || {});
}

const employeeCheckinTableState = reactive({
	rows: [],
	total: 0,
	loading: false,
	sortOrder: "desc",
});

const employeeCheckinTableHandlers = {
	onOpen: null,
	onSort: null,
};

export function mountEmployeeCheckinTable(el, payload = {}, handlers = {}) {
	Object.assign(employeeCheckinTableState, payload || {});
	Object.assign(employeeCheckinTableHandlers, handlers || {});
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () =>
					h(EmployeeCheckinTable, {
						state: employeeCheckinTableState,
						handlers: employeeCheckinTableHandlers,
					})
				);
			},
		})
	);
	app.mount(el);
	return app;
}

export function updateEmployeeCheckinTable(payload = {}) {
	Object.assign(employeeCheckinTableState, payload || {});
}

export function mountAttendanceRules(rootEl) {
	rootEl.classList.add("hr-attendance-rules-page", "hr-desk-content-stack");

	const headerHost = document.createElement("div");
	headerHost.className = "hr-desk-header-host";
	rootEl.appendChild(headerHost);
	mountDeskHeader(headerHost, AttendanceRulesDeskHeader);

	const bodyHost = document.createElement("div");
	bodyHost.className = "hr-attendance-rules-body";
	rootEl.appendChild(bodyHost);

	let reloadFn = null;
	const app = boot(
		createApp({
			render() {
				return h(ConfigProvider, { locale: zhCN }, () =>
					h(AttendanceRulesPage, {
						ref(instance) {
							reloadFn = () => instance?.reload?.();
						},
					})
				);
			},
		})
	);
	app.mount(bodyHost);
	app.reloadRules = () => reloadFn?.();
	return app;
}
