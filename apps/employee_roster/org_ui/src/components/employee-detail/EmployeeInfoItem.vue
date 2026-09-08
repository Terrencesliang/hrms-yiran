<template>
	<div class="arco-emp-info-item">
		<span class="arco-emp-info-label">{{ label }}</span>
		<span class="arco-emp-info-value">
			<slot>{{ displayValue }}</slot>
		</span>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { dash } from "../../utils/employeeDetail";

const props = defineProps({
	label: { type: String, required: true },
	value: { type: [String, Number], default: "" },
});

const displayValue = computed(() => dash(props.value));
</script>
