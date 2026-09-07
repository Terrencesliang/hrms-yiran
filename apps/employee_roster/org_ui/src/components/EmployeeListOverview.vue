<template>
	<HrDeskStatOverview :items="items" :handlers="overviewHandlers" grid-class="" />
</template>

<script setup>
import { computed } from "vue";
import {
	IconCheckCircle,
	IconClockCircle,
	IconCloseCircle,
	IconIdcard,
	IconSafe,
	IconUserGroup,
} from "@arco-design/web-vue/es/icon";
import HrDeskStatOverview from "./HrDeskStatOverview.vue";

const props = defineProps({
	state: { type: Object, required: true },
	handlers: { type: Object, default: () => ({}) },
});

function isActive(field, value, operator = "=") {
	if (!props.state.filters?.length) return field === "status" && value === "Active";
	return props.state.filters.some(
		(filter) => filter.field === field && filter.value === value && (filter.operator || "=") === operator,
	);
}

const items = computed(() => {
	const counts = props.state.employmentCounts || {};
	return [
		{ key: "active", label: "在职", value: props.state.active, field: "status", valueKey: "Active", tone: "success", icon: IconCheckCircle },
		{ key: "fulltime", label: "全职", value: counts["Full-time"] || 0, field: "designation", valueKey: "实习生", operator: "!=", tone: "primary", icon: IconIdcard },
		{ key: "intern", label: "实习生", value: counts.Intern || 0, field: "designation", valueKey: "实习生", tone: "purple", icon: IconUserGroup },
		{ key: "probation", label: "试用期", value: counts.Probation || 0, field: "employment_type", valueKey: "Probation", tone: "warning", icon: IconClockCircle },
		{ key: "inactive", label: "停用", value: props.state.inactive, field: "status", valueKey: "Inactive", tone: "neutral", icon: IconSafe },
		{ key: "left", label: "已离职", value: props.state.left, field: "status", valueKey: "Left", tone: "danger", icon: IconCloseCircle },
	].map((item) => ({
		...item,
		operator: item.operator || "=",
		active: isActive(item.field, item.valueKey, item.operator || "="),
		disabled: !item.field || !item.valueKey,
	}));
});

const overviewHandlers = computed(() => ({
	onSelect: (item) => props.handlers?.onFilter?.(item),
}));
</script>
