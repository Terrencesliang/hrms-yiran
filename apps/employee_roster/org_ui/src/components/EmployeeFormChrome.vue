<template>
	<a-config-provider :locale="zhCN">
		<template v-if="state.show_overview">
			<div class="arco-emp-form-chrome arco-emp-pro">
				<a-card class="arco-emp-hero" :bordered="false">
					<div class="arco-emp-hero-row">
						<div class="arco-emp-hero-left">
							<a-avatar :size="56" class="arco-emp-avatar">
								<img v-if="state.image" :src="state.image" alt="" />
								<span v-else>{{ initials }}</span>
							</a-avatar>
							<div class="arco-emp-hero-meta">
								<div class="arco-emp-hero-title-row">
									<h1 class="arco-emp-name">{{ state.employee_name || state.name || "—" }}</h1>
									<a-tag :color="statusColor" size="small" class="arco-emp-status-tag">
										{{ statusLabel }}
									</a-tag>
								</div>
								<div class="arco-emp-sub">
									<span class="arco-emp-id">{{ state.name }}</span>
									<span class="arco-emp-dot">·</span>
									<span>{{ state.designation || "未设置职位" }}</span>
									<span class="arco-emp-dot">·</span>
									<span>{{ state.department || "未设置部门" }}</span>
								</div>
							</div>
						</div>
						<div class="arco-emp-hero-right">
							<a-space wrap :size="8">
								<a-tag v-if="state.company" bordered class="arco-emp-pill">{{ state.company }}</a-tag>
								<a-tag v-if="state.branch" bordered class="arco-emp-pill">{{ state.branch }}</a-tag>
								<a-tag v-if="state.employment_type" bordered class="arco-emp-pill">
									{{ employmentTypeLabel }}
								</a-tag>
							</a-space>
						</div>
					</div>

					<div class="arco-emp-kv-grid">
						<div v-for="item in kvItems" :key="item.label" class="arco-emp-kv-item">
							<div class="arco-emp-kv-label">{{ item.label }}</div>
							<div class="arco-emp-kv-value">{{ item.value }}</div>
						</div>
					</div>
				</a-card>

				<div class="arco-emp-stat-grid">
					<a-card v-for="item in stats" :key="item.key" class="arco-emp-stat-card" :bordered="false">
						<div class="arco-emp-stat-inner">
							<div class="arco-emp-stat-icon" :class="`is-${item.key}`">
								<component :is="item.icon" />
							</div>
							<div class="arco-emp-stat-meta">
								<div class="arco-emp-stat-title">{{ item.title }}</div>
								<div class="arco-emp-stat-value">
									<template v-if="item.isText">{{ item.value }}</template>
									<template v-else>
										{{ item.value }}
										<span v-if="item.suffix" class="arco-emp-stat-suffix">{{ item.suffix }}</span>
									</template>
								</div>
							</div>
						</div>
					</a-card>
				</div>
			</div>

			<Teleport v-if="overviewReady" to="#employee-arco-overview-root">
				<EmployeeOverviewPanel :state="state" @navigate="onNavigate" />
			</Teleport>
		</template>
	</a-config-provider>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import {
	IconCalendar,
	IconFile,
	IconSchedule,
	IconStorage,
} from "@arco-design/web-vue/es/icon";
import EmployeeOverviewPanel from "./EmployeeOverviewPanel.vue";

const props = defineProps({
	state: {
		type: Object,
		required: true,
	},
	handlers: {
		type: Object,
		default: () => ({}),
	},
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

onUnmounted(() => {
	observer?.disconnect?.();
});

const initials = computed(() => {
	const name = String(props.state.employee_name || props.state.name || "?").trim();
	return name.slice(0, 1);
});

const statusMap = {
	Active: { label: "在职", color: "green" },
	Inactive: { label: "停用", color: "orangered" },
	Suspended: { label: "停职", color: "red" },
	Left: { label: "离职", color: "gray" },
};

const statusLabel = computed(() => statusMap[props.state.status]?.label || props.state.status || "—");
const statusColor = computed(() => statusMap[props.state.status]?.color || "gray");

const employmentTypeMap = {
	"Full-time": "全职",
	Intern: "实习",
	Probation: "试用期",
	Contract: "合同工",
	"Part-time": "兼职",
};

const employmentTypeLabel = computed(
	() => employmentTypeMap[props.state.employment_type] || props.state.employment_type || ""
);

const genderMap = {
	Male: "男",
	Female: "女",
	Other: "其他",
};

const genderLabel = computed(() => {
	const g = props.state.gender || "";
	return genderMap[g] || g || "—";
});

function dash(v) {
	return v === 0 || v ? v : "—";
}

const kvItems = computed(() => [
	{ label: "入职日期", value: dash(props.state.date_of_joining) },
	{ label: "手机号", value: dash(props.state.cell_number) },
	{ label: "公司邮箱", value: dash(props.state.company_email) },
	{ label: "上级主管", value: dash(props.state.reports_to) },
	{ label: "雇佣类型", value: employmentTypeLabel.value || "—" },
	{ label: "分支机构", value: dash(props.state.branch) },
	{ label: "员工等级", value: dash(props.state.grade) },
	{ label: "性别", value: genderLabel.value },
]);

function asStatNumber(v) {
	if (v == null || v === "" || v === "—") {
		return null;
	}
	const n = Number(v);
	return Number.isFinite(n) ? n : null;
}

const stats = computed(() => {
	const tenure = asStatNumber(props.state.tenure_days);
	const leave = asStatNumber(props.state.leave_balance);
	const attendance = asStatNumber(props.state.attendance_month);
	const related = asStatNumber(props.state.related_count) ?? 0;
	return [
		{
			key: "tenure",
			title: "在职天数",
			value: tenure == null ? "—" : tenure,
			suffix: tenure == null ? "" : "天",
			isText: tenure == null,
			icon: IconCalendar,
		},
		{
			key: "leave",
			title: "请假余额",
			value: leave == null ? "—" : leave,
			suffix: leave == null ? "" : "天",
			isText: leave == null,
			icon: IconFile,
		},
		{
			key: "attendance",
			title: "本月出勤",
			value: attendance == null ? "—" : attendance,
			suffix: attendance == null ? "" : "天",
			isText: attendance == null,
			icon: IconSchedule,
		},
		{
			key: "related",
			title: "关联单据",
			value: related,
			suffix: "",
			isText: false,
			icon: IconStorage,
		},
	];
});

function onNavigate(target) {
	props.handlers?.onNavigate?.(target);
}
</script>
