<template>
	<HrDeskStatOverview
		:items="items"
		:loading="state.loading"
		:handlers="overviewHandlers"
		grid-class="hr-employee-overview-grid--four"
		meta-title="考勤概览"
		:meta-icon="IconHome"
		:meta-extra="hintText"
		:meta-hint="state.rangeLabel"
	/>
</template>

<script setup>
import { computed } from "vue";
import {
	IconCalendar,
	IconCheckCircle,
	IconClockCircle,
	IconExclamationCircle,
	IconHome,
} from "@arco-design/web-vue/es/icon";
import HrDeskStatOverview from "./HrDeskStatOverview.vue";

const props = defineProps({
	state: { type: Object, required: true },
	handlers: { type: Object, default: () => ({}) },
});

const items = computed(() => {
	const stats = props.state.stats || {};
	return [
		{ key: "present", label: "出勤", value: stats.present || 0, resultKey: "present", tone: "success", icon: IconCheckCircle },
		{ key: "both_punches", label: "上下班打卡", value: stats.both_punches || 0, resultKey: "both_punches", tone: "primary", icon: IconCalendar },
		{ key: "late", label: "迟到", value: stats.late || 0, resultKey: "late", tone: "warning", icon: IconClockCircle },
		{ key: "missing", label: "缺卡", value: stats.missing || 0, resultKey: "missing", tone: "danger", icon: IconExclamationCircle },
	].map((item) => ({
		...item,
		active: props.state.activeResult === item.resultKey,
		disabled: false,
	}));
});

const hintText = computed(() => {
	const key = props.state.activeResult;
	if (!key) return "点击指标可按人员下钻筛选，再次点击取消";
	const labels = {
		present: "出勤",
		both_punches: "上下班打卡",
		late: "迟到",
		missing: "缺卡",
	};
	return `当前筛选：${labels[key] || key} · 再次点击取消`;
});

const overviewHandlers = computed(() => ({
	onSelect: (item) => props.handlers?.onFilter?.(item.resultKey),
}));
</script>
