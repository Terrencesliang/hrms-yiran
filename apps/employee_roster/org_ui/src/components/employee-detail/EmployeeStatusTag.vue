<template>
	<a-tag :color="color" size="small" class="arco-emp-status-tag">
		<span class="arco-emp-status-dot" />{{ label }}
	</a-tag>
</template>

<script setup>
import { computed } from "vue";
import { statusColor, statusLabel } from "../../utils/employeeDetail";

const props = defineProps({
	status: { type: String, default: "" },
});

const label = computed(() => statusLabel(props.status));
const color = computed(() => statusColor(props.status));
</script>
