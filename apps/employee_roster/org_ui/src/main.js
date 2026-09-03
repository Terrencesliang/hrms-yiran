import { createApp, h, reactive } from "vue";
import ArcoVue from "@arco-design/web-vue";
import ArcoVueIcon from "@arco-design/web-vue/es/icon";
import { ConfigProvider } from "@arco-design/web-vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import "@arco-design/web-vue/dist/arco.css";
import "./styles.css";
import OrgChartPage from "./components/OrgChartPage.vue";
import SidebarApp from "./components/SidebarApp.vue";

function boot(app) {
	app.use(ArcoVue);
	app.use(ArcoVueIcon);
	return app;
}

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

const sidebarState = reactive({
	title: "",
	tabs: [],
	activeTab: "",
	activeKey: "",
	groups: [],
	workspaces: [],
	searchShortcut: "Ctrl+K",
});

const sidebarHandlers = {
	onWorkspace: null,
	onCollapse: null,
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
