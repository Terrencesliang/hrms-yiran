<template>
	<a-card class="arco-emp-detail-card arco-emp-overview-card" :bordered="true">
		<template #title>
			<div class="arco-emp-detail-card-title">
				<span class="arco-emp-detail-card-icon"><icon-schedule /></span>
				<span>考勤统计</span>
			</div>
		</template>
		<template #extra>
			<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'attendance')">
				查看详情 <icon-right />
			</a-button>
		</template>

		<a-spin :loading="loading" class="arco-emp-attendance-spin">
			<a-alert
				v-if="error"
				type="error"
				class="arco-emp-overview-alert"
				:title="error"
			>
				<template #action>
					<a-button size="mini" type="text" @click="$emit('retry')">重新加载</a-button>
				</template>
			</a-alert>
			<div v-else class="arco-emp-attendance-fill">
				<div v-if="monthLabel" class="arco-emp-attendance-month">{{ monthLabel }}</div>
				<div class="arco-emp-attendance-pills">
					<div
						v-for="item in stats"
						:key="item.key"
						class="arco-emp-attendance-pill"
						:class="`is-${item.key}`"
					>
						<span class="arco-emp-attendance-pill-icon">
							<component :is="item.icon" />
						</span>
						<span class="arco-emp-attendance-pill-label">{{ item.title }}</span>
						<strong class="arco-emp-attendance-pill-value">{{ item.display }}</strong>
					</div>
				</div>
			</div>
		</a-spin>
	</a-card>
</template>

<script setup>
import { computed } from "vue";
import { IconClockCircle, IconRight, IconSchedule, IconSun, IconThunderbolt } from "@arco-design/web-vue/es/icon";

const props = defineProps({
	attendance: { type: Object, default: () => ({}) },
	loading: { type: Boolean, default: false },
	error: { type: String, default: "" },
});
defineEmits(["navigate", "retry"]);

function formatStat(value, suffix = "") {
	if (value == null || value === "") return "0" + suffix;
	if (typeof value === "number" && Number.isFinite(value)) {
		return `${value}${suffix}`;
	}
	return String(value);
}

const monthLabel = computed(() => {
	const m = props.attendance?.month;
	if (!m) return "";
	const parts = String(m).split("-");
	if (parts.length >= 2) {
		return `本月（${parts[0]}年${Number(parts[1])}月）`;
	}
	return `本月（${m}）`;
});

const stats = computed(() => {
	const a = props.attendance || {};
	return [
		{
			key: "attendance",
			title: "出勤天数",
			display: formatStat(a.attendance_days, " 天"),
			icon: IconSchedule,
		},
		{
			key: "leave",
			title: "请假",
			display: formatStat(a.leave_hours, " 小时"),
			icon: IconSun,
		},
		{
			key: "late",
			title: "迟到",
			display: formatStat(a.late_count, " 次"),
			icon: IconClockCircle,
		},
		{
			key: "overtime",
			title: "加班",
			display: formatStat(a.overtime_hours, " 小时"),
			icon: IconThunderbolt,
		},
	];
});
</script>
