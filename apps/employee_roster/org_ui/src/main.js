import { createApp, h, reactive } from "vue";
import ArcoVue from "@arco-design/web-vue";
import ArcoVueIcon from "@arco-design/web-vue/es/icon";
import { ConfigProvider } from "@arco-design/web-vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import "@arco-design/web-vue/dist/arco.css";
import "./styles.css";
import OrgChartPage from "./pages/orgchart/OrgChartPage.vue";
import OrgDiagramPage from "./pages/orgdiagram/OrgDiagramPage.vue";
import SidebarApp from "./pages/sidebar/SidebarApp.vue";
import NavbarApp from "./pages/navbar/NavbarApp.vue";
import EmployeeFormChrome from "./components/EmployeeFormChrome.vue";
import ApprovalsApp from "./pages/approvals/ApprovalsApp.vue";
import ApprovalDesignerApp from "./pages/approvals/designer/ApprovalDesignerApp.vue";
import ApprovalsWorkspace from "./pages/approvals/workspace/ApprovalsWorkspace.vue";
import HrHomePage from "./pages/home/HrHomePage.vue";
import HrDashboardPage from "./pages/dashboard/HrDashboardPage.vue";

function boot(app) {
	app.use(ArcoVue);
	app.use(ArcoVueIcon);
	return app;
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
	status: "",
	department: "",
	designation: "",
	company: "",
	branch: "",
	employment_type: "",
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
	education: [],
	external_work_history: [],
	internal_work_history: [],
	tenure_days: null,
	leave_balance: null,
	attendance_month: null,
	related_count: 0,
	show_overview: true,
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

export function updateEmployeeForm(payload) {
	Object.assign(employeeFormState, payload || {});
}

export function setEmployeeFormHandlers(handlers = {}) {
	Object.assign(employeeFormHandlers, handlers || {});
}
