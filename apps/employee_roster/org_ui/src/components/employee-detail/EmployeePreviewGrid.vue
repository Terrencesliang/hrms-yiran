<template>
	<div class="arco-emp-preview-grid" :style="{ '--cols': cols }">
		<div v-for="item in items" :key="item.key || item.label" class="arco-emp-preview-item">
			<div class="arco-emp-preview-label">
				{{ item.label }}
				<span v-if="item.required" class="arco-emp-req">*</span>
			</div>
			<div class="arco-emp-preview-value">
				<slot :name="item.key" :item="item">{{ display(item) }}</slot>
			</div>
		</div>
	</div>
</template>

<script setup>
import { blank } from "../../utils/employeeArchive";

defineProps({
	items: { type: Array, required: true },
	cols: { type: Number, default: 3 },
});

function display(item) {
	if (item.render) return item.render(item.value);
	return blank(item.value);
}
</script>
