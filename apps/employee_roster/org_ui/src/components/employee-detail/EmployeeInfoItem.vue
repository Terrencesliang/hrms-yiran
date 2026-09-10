<template>
	<div class="arco-emp-info-item" :class="{ 'is-span-2': span === 2 }">
		<span class="arco-emp-info-label">
			{{ label }}<i v-if="required" class="arco-emp-req">*</i>
		</span>
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
	span: { type: Number, default: 1 },
	required: { type: Boolean, default: false },
});

const displayValue = computed(() => dash(props.value));
</script>
