<template>
	<EmployeeDetailCard title="考勤统计" :icon="IconSchedule">
		<template #action>
			<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'attendance')">
				查看详情 <icon-right />
			</a-button>
		</template>
		<div class="arco-emp-attendance-stats-row">
			<div v-for="item in stats" :key="item.key" class="arco-emp-attendance-stat">
				<span class="arco-emp-attendance-stat-icon" :class="`is-${item.key}`"><component :is="item.icon" /></span>
				<div class="arco-emp-attendance-stat-copy">
					<span>{{ item.title }}</span>
					<strong>{{ item.display }}</strong>
				</div>
			</div>
		</div>
	</EmployeeDetailCard>
</template>

<script setup>
import { computed } from "vue";
import { IconClockCircle, IconRight, IconSchedule, IconSun, IconThunderbolt } from "@arco-design/web-vue/es/icon";
import EmployeeDetailCard from "./EmployeeDetailCard.vue";

const props = defineProps({ state: { type: Object, required: true } });
defineEmits(["navigate"]);

function formatStat(value, suffix = "") {
	if (value == null || value === "") return "—";
	if (typeof value === "number" && Number.isFinite(value)) {
		return `${value}${suffix}`;
	}
	return String(value);
}

const stats = computed(() => [
	{
		key: "attendance",
		title: "本月出勤",
		display: formatStat(props.state.attendance_month, " 天"),
		icon: IconSchedule,
	},
	{
		key: "leave",
		title: "请假",
		display: formatStat(props.state.leave_balance, " 天"),
		icon: IconSun,
	},
	{
		key: "late",
		title: "迟到",
		display: formatStat(props.state.late_count, " 次"),
		icon: IconClockCircle,
	},
	{
		key: "overtime",
		title: "加班",
		display: formatStat(props.state.overtime_hours, " 小时"),
		icon: IconThunderbolt,
	},
]);
</script>
