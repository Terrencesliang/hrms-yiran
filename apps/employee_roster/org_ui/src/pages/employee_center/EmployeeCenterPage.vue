<template>
	<HrPage :breadcrumbs="breadcrumbs" class="employee-center-shell">
		<a-spin :loading="loading" style="width: 100%">
			<div v-if="context" class="ec-page-stack">
				<header class="ec-page-heading">
					<div>
						<a-button v-if="view !== 'home'" type="text" class="ec-back" @click="navigate('home')">
							<template #icon><icon-left /></template>返回员工中心
						</a-button>
						<h1>{{ pageTitle }}</h1>
						<p>{{ pageSubtitle }}</p>
					</div>
					<a-button v-if="view === 'home'" @click="navigate('applications')">我的申请</a-button>
					<a-button v-else-if="view === 'applications' && context.employee" type="primary" @click="navigate('home')">
						<template #icon><icon-plus /></template>新建申请
					</a-button>
				</header>

				<a-card v-if="view === 'home' && !context.employee" :bordered="false" class="ec-module-stage">
					<a-result
						status="warning"
						title="当前账号未关联员工档案"
						subtitle="员工中心只展示当前登录人的资料。请先由 HR 在员工档案中设置对应的系统用户。"
					>
						<template #extra>
							<a-space>
								<a-button @click="navigate('applications')">查看我的申请</a-button>
								<a-button v-if="context.capabilities.can_manage_hr" type="primary" @click="openEmployeeList">前往员工花名册</a-button>
							</a-space>
						</template>
					</a-result>
				</a-card>
				<EmployeeCenterHome
					v-else-if="view === 'home' && context.employee"
					:employee="context.employee"
					:profile="context.profile"
					:modules="context.modules"
					:stats="context.application_stats"
					@navigate="navigate"
					@open-status="openStatus"
				/>
				<MyApplications
					v-else-if="view === 'applications'"
					:initial-status="applicationStatus"
					:stats="context.application_stats"
					@go-home="navigate('home')"
					@changed="reloadContext"
					@edit="editApplication"
				/>
				<a-spin v-else-if="applicationLoading" loading style="width:100%;min-height:420px" />
				<EmployeeApplicationForm
					v-else-if="applicationSetup && context.employee"
					:key="`${view}-${editInstance}`"
					:application-type="view as any"
					:setup="applicationSetup"
					@cancel="navigate('home')"
					@saved="reloadContext"
					@submitted="afterSubmitted"
				/>
				<a-result v-else status="warning" title="无法发起申请" :subtitle="applicationError || '请检查员工档案与审批流程配置'" />
			</div>
			<a-result v-else-if="errorMessage" status="error" title="员工中心加载失败" :subtitle="errorMessage">
				<template #extra><a-button type="primary" @click="reloadContext">重新加载</a-button></template>
			</a-result>
		</a-spin>
	</HrPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Message } from "@arco-design/web-vue";
import { IconLeft, IconPlus } from "@arco-design/web-vue/es/icon";
import HrPage from "../../components/HrPage.vue";
import { getApplicationSetup, getEmployeeCenterContext, type EmployeeCenterContext, type EmployeeCenterView } from "../../api/employeeCenter";
import EmployeeCenterHome from "./EmployeeCenterHome.vue";
import MyApplications from "./MyApplications.vue";
import EmployeeApplicationForm from "./components/EmployeeApplicationForm.vue";
import "./employee-center.css";

const props = defineProps<{ view?: EmployeeCenterView; instanceName?: string }>();
const view = ref<EmployeeCenterView>(props.view || "home");
const context = ref<EmployeeCenterContext | null>(null);
const loading = ref(false);
const errorMessage = ref("");
const applicationStatus = ref("all");
const applicationSetup = ref<any>(null);
const applicationLoading = ref(false);
const applicationError = ref("");
const editInstance = ref(props.instanceName || "");

const breadcrumbs = computed(() => [
	{ label: "员工中心", route: ["employee-center", "home"] },
	...(view.value === "home" ? [] : [{ label: pageTitle.value }]),
]);

const currentModule = computed(() => context.value?.modules.find((item) => item.key === view.value));
const pageTitle = computed(() => {
	if (view.value === "home") return "员工中心";
	if (view.value === "applications") return "我的申请 / 审批记录";
	return currentModule.value?.title || "员工中心";
});
const pageSubtitle = computed(() => {
	if (view.value === "home") return "个人资料与人事服务";
	if (view.value === "applications") return "查看本人发起的申请及当前审批进度";
	return currentModule.value?.description || "办理个人相关人事业务";
});

function syncRoute(nextView: string) {
	if (!window.frappe?.set_route) return;
	window.frappe.set_route("employee-center", nextView);
}

function navigate(nextView: string) {
	editInstance.value = "";
	view.value = nextView as EmployeeCenterView;
	syncRoute(nextView);
}

function openStatus(status: string) {
	applicationStatus.value = status;
	navigate("applications");
}

function openEmployeeList() {
	window.frappe?.set_route?.("List", "Employee");
}

async function loadApplicationSetup() {
	if (["home", "applications"].includes(view.value)) { applicationSetup.value = null; return; }
	applicationLoading.value = true;
	applicationError.value = "";
	try { applicationSetup.value = await getApplicationSetup(view.value, editInstance.value || undefined); }
	catch (error: any) { applicationSetup.value = null; applicationError.value = error?.message || "申请配置加载失败"; }
	finally { applicationLoading.value = false; }
}

function editApplication(type: string, name: string) {
	editInstance.value = name;
	view.value = type as EmployeeCenterView;
	window.frappe?.set_route?.("employee-center", type, name);
}

async function afterSubmitted() {
	await reloadContext();
	navigate("applications");
}

async function reloadContext() {
	loading.value = true;
	errorMessage.value = "";
	try {
		context.value = await getEmployeeCenterContext();
	} catch (error: any) {
		errorMessage.value = error?.message || "无法获取当前员工信息";
		Message.error(errorMessage.value);
	} finally {
		loading.value = false;
	}
}

watch(() => props.view, (value) => { if (value) view.value = value; });
watch(() => props.instanceName, (value) => { editInstance.value = value || ""; });
watch(view, loadApplicationSetup);
watch(editInstance, loadApplicationSetup);
onMounted(async () => { await reloadContext(); await loadApplicationSetup(); });
</script>
