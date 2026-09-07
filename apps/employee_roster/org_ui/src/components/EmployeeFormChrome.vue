<template>
	<a-config-provider :locale="zhCN">
		<div class="arco-emp-form-chrome arco-emp-pro" :class="{ 'is-compact': !state.show_overview }">
			<a-card class="arco-emp-dossier-cover" :bordered="false">
				<div class="arco-emp-cover-main">
					<section class="arco-emp-identity" aria-label="员工身份信息">
						<a-avatar :size="state.show_overview ? 82 : 48" class="arco-emp-avatar">
							<img v-if="state.image" :src="state.image" :alt="state.employee_name || '员工头像'" />
							<span v-else>{{ initials }}</span>
						</a-avatar>
						<div class="arco-emp-identity-copy">
							<div class="arco-emp-hero-title-row">
								<h1 class="arco-emp-name">{{ state.employee_name || state.name || "—" }}</h1>
								<a-tag :color="statusColor" size="small" class="arco-emp-status-tag">
									<span class="arco-emp-status-dot" />{{ statusLabel }}
								</a-tag>
							</div>
							<div class="arco-emp-id"><icon-idcard />{{ state.name }}</div>
							<div class="arco-emp-role-line">
								<strong>{{ state.designation || "未设置职位" }}</strong>
								<span>{{ state.department || "未设置部门" }}</span>
							</div>
							<div v-if="state.show_overview" class="arco-emp-company-line">
								<span v-if="state.company"><icon-home />{{ state.company }}</span>
								<span v-if="state.branch"><icon-location />{{ state.branch }}</span>
							</div>
						</div>
					</section>

					<transition name="emp-expand">
						<section v-if="state.show_overview" class="arco-emp-lifecycle" aria-label="员工入职进度">
							<div class="arco-emp-join-summary">
								<div>
									<span>入职日期</span>
									<strong>{{ state.date_of_joining || "—" }}</strong>
								</div>
								<div class="arco-emp-tenure">
									<span>入职第</span>
									<strong>{{ tenureValue }}</strong>
									<small v-if="tenureValue !== '—'">天</small>
								</div>
							</div>
							<a-steps :current="lifecycleCurrent" size="small" class="arco-emp-lifecycle-steps">
								<a-step title="已入职" />
								<a-step title="试用期" />
								<a-step title="待转正" />
							</a-steps>
						</section>
					</transition>

					<div v-if="state.show_overview" class="arco-emp-cover-emblem" aria-hidden="true">
						<icon-idcard />
					</div>
				</div>

				<transition name="emp-expand">
					<div v-if="state.show_overview" class="arco-emp-metric-strip" aria-label="员工关键数据">
						<div v-for="item in metrics" :key="item.key" class="arco-emp-metric-item">
							<span class="arco-emp-metric-icon" :class="`is-${item.key}`"><component :is="item.icon" /></span>
							<div>
								<span>{{ item.title }}</span>
								<strong>{{ item.value }}<small v-if="item.suffix">{{ item.suffix }}</small></strong>
							</div>
						</div>
						<div class="arco-emp-metric-item is-completion">
							<a-progress type="circle" :percent="completionPercent" :width="42" :stroke-width="6" :show-text="false" />
							<div>
								<span>档案完整度</span>
								<strong>{{ completionRate }}<small>%</small></strong>
							</div>
						</div>
					</div>
				</transition>
			</a-card>
		</div>

		<Teleport v-if="overviewReady" to="#employee-arco-overview-root">
			<transition name="emp-overview" appear>
				<EmployeeOverviewPanel v-if="state.show_overview" :state="state" @navigate="onNavigate" />
			</transition>
		</Teleport>
	</a-config-provider>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import { IconFile, IconHome, IconIdcard, IconLocation, IconSchedule } from "@arco-design/web-vue/es/icon";
import EmployeeOverviewPanel from "./EmployeeOverviewPanel.vue";

const props = defineProps({
	state: { type: Object, required: true },
	handlers: { type: Object, default: () => ({}) },
});

const overviewReady = ref(false);
let observer = null;

function refreshOverviewTarget() {
	overviewReady.value = !!document.querySelector("#employee-arco-overview-root");
}

onMounted(() => {
	refreshOverviewTarget();
	observer = new MutationObserver(refreshOverviewTarget);
	observer.observe(document.body, { childList: true, subtree: true });
});

onUnmounted(() => observer?.disconnect?.());

const initials = computed(() => String(props.state.employee_name || props.state.name || "?").trim().slice(0, 1));
const statusMap = {
	Active: { label: "在职", color: "green" },
	Inactive: { label: "停用", color: "orangered" },
	Suspended: { label: "停职", color: "red" },
	Left: { label: "离职", color: "gray" },
};
const statusLabel = computed(() => statusMap[props.state.status]?.label || props.state.status || "—");
const statusColor = computed(() => statusMap[props.state.status]?.color || "gray");
const tenureValue = computed(() => {
	const value = Number(props.state.tenure_days);
	return Number.isFinite(value) ? value : "—";
});
const completionRate = computed(() => {
	const value = Number(props.state.profile_completion);
	return Number.isFinite(value) ? Math.min(100, Math.max(0, Math.round(value))) : 0;
});
const completionPercent = computed(() => completionRate.value / 100);
const lifecycleCurrent = computed(() => {
	if (props.state.status === "Left") return 3;
	if (props.state.employment_type === "Probation") return 2;
	if (props.state.employment_type === "Full-time" && tenureValue.value !== "—" && tenureValue.value > 180) return 3;
	return 1;
});

function asStatNumber(value) {
	if (value == null || value === "" || value === "—") return null;
	const number = Number(value);
	return Number.isFinite(number) ? number : null;
}

const metrics = computed(() => {
	const leave = asStatNumber(props.state.leave_balance);
	const attendance = asStatNumber(props.state.attendance_month);
	return [
		{ key: "attendance", title: "本月出勤", value: attendance ?? "—", suffix: attendance == null ? "" : "天", icon: IconSchedule },
		{ key: "leave", title: "请假余额", value: leave ?? "—", suffix: leave == null ? "" : "天", icon: IconFile },
		{ key: "related", title: "关联单据", value: asStatNumber(props.state.related_count) ?? 0, suffix: "", icon: IconIdcard },
	];
});

function onNavigate(target) {
	props.handlers?.onNavigate?.(target);
}
</script>
