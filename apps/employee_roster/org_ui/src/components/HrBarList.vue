<template>
	<div class="hr-bar-list">
		<div v-if="!items.length" class="hr-bar-empty">暂无数据</div>
		<div v-for="item in normalized" :key="item.name" class="hr-bar-row">
			<div class="hr-bar-meta">
				<span class="hr-bar-name" :title="item.name">{{ item.name }}</span>
				<span class="hr-bar-count">{{ item.count }}</span>
			</div>
			<div class="hr-bar-track">
				<div class="hr-bar-fill" :style="{ width: item.pct + '%', background: color }" />
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	items: { type: Array, default: () => [] },
	color: { type: String, default: "rgb(var(--primary-6))" },
});

const normalized = computed(() => {
	const max = Math.max(1, ...props.items.map((i) => Number(i.count) || 0));
	return props.items.map((i) => ({
		name: i.name,
		count: Number(i.count) || 0,
		pct: Math.round(((Number(i.count) || 0) / max) * 100),
	}));
});
</script>
