<template>
	<div class="ec-home">
		<a-card :bordered="false" class="ec-profile-card">
			<div class="ec-profile-main">
				<a-avatar :size="64" class="ec-avatar">
					<img v-if="employee.image" :src="employee.image" :alt="employee.employee_name" />
					<span v-else>{{ employee.employee_name?.slice(0, 1) || "员" }}</span>
				</a-avatar>
				<div class="ec-profile-copy">
					<div class="ec-welcome">你好，{{ employee.employee_name || "同事" }}</div>
					<div class="ec-jobline">
						<span>{{ employee.employee_number || "未设置工号" }}</span>
						<i />
						<span>{{ employee.designation || "未设置岗位" }}</span>
						<i />
						<span>{{ employee.department || "未设置部门" }}</span>
					</div>
					<div class="ec-company">{{ employee.company || "未设置公司" }}</div>
				</div>
			</div>
			<div class="ec-profile-progress">
				<div class="ec-progress-head">
					<span>个人资料完整度</span>
					<strong>{{ profile.percent }}%</strong>
				</div>
				<a-progress :percent="profile.percent / 100" :show-text="false" />
				<a-link v-if="profile.missing?.length" @click="$emit('navigate', 'onboarding')">
					继续完善 {{ profile.missing.length }} 项资料
				</a-link>
				<span v-else class="ec-complete">资料已完善</span>
			</div>
		</a-card>

		<section class="ec-section">
			<div class="ec-section-head">
				<div><h2>常用服务</h2><p>办理与你相关的人事业务</p></div>
			</div>
			<div class="ec-module-grid">
				<EmployeeCenterModuleCard
					v-for="(item, index) in modules"
					:key="item.key"
					:title="item.title"
					:description="item.description"
					:tone="moduleMeta[index]?.tone || 'blue'"
					:icon="moduleMeta[index]?.icon || IconFile"
					@open="$emit('navigate', item.key)"
				/>
			</div>
		</section>

		<section class="ec-section ec-application-summary">
			<div class="ec-section-head">
				<div><h2>我的申请</h2><p>查看申请与审批进度</p></div>
				<a-link @click="$emit('navigate', 'applications')">查看全部 <icon-right /></a-link>
			</div>
			<div class="ec-stat-row">
				<button v-for="item in statItems" :key="item.key" type="button" @click="$emit('open-status', item.key)">
					<span :class="`is-${item.tone}`"><component :is="item.icon" /></span>
					<small>{{ item.label }}</small>
					<strong>{{ item.value }}</strong>
				</button>
			</div>
			<div v-if="recentApplications.length" class="ec-recent-list" style="margin-top:14px">
				<button v-for="item in recentApplications" :key="item.name" type="button" class="ec-recent-item" @click="$emit('navigate', 'applications')">
					<span><strong>{{ item.form_title }}</strong><small>{{ item.application_no }}</small></span>
					<span>{{ formatDate(item.submitted_at) }}</span>
					<ApplicationStatusTag :status="item.status" />
					<icon-right />
				</button>
			</div>
		</section>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
	IconApps,
	IconCheckCircle,
	IconClockCircle,
	IconFile,
	IconImport,
	IconRight,
	IconSchedule,
	IconSend,
	IconSettings,
	IconUser,
} from "@arco-design/web-vue/es/icon";
import { listMyApplications, type ApplicationRow, type EmployeeCenterModule, type EmployeeSummary } from "../../api/employeeCenter";
import EmployeeCenterModuleCard from "./components/EmployeeCenterModuleCard.vue";
import ApplicationStatusTag from "./components/ApplicationStatusTag.vue";

const props = defineProps<{
	employee: EmployeeSummary;
	profile: { completed: number; total: number; percent: number; missing: string[] };
	modules: EmployeeCenterModule[];
	stats: Record<string, number>;
}>();

defineEmits<{
	navigate: [view: string];
	"open-status": [status: string];
}>();

const moduleMeta = [
	{ icon: IconUser, tone: "blue" },
	{ icon: IconImport, tone: "orange" },
	{ icon: IconSettings, tone: "purple" },
	{ icon: IconSend, tone: "red" },
	{ icon: IconSchedule, tone: "green" },
];
const recentApplications = ref<ApplicationRow[]>([]);
function formatDate(value: string) { return value ? String(value).replace("T", " ").slice(0, 16) : "—"; }
onMounted(async () => {
	try { recentApplications.value = (await listMyApplications({ page_length: 3 })).rows || []; }
	catch { recentApplications.value = []; }
});

const statItems = computed(() => [
	{ key: "pending", label: "审批中", value: props.stats.pending || 0, tone: "blue", icon: IconClockCircle },
	{ key: "approved", label: "已通过", value: props.stats.approved || 0, tone: "green", icon: IconCheckCircle },
	{ key: "draft", label: "草稿", value: props.stats.draft || 0, tone: "gray", icon: IconFile },
	{ key: "all", label: "全部申请", value: props.stats.all || 0, tone: "purple", icon: IconApps },
]);
</script>
