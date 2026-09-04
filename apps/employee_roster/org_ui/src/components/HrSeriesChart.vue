<template>
	<div class="hr-series-chart">
		<div v-if="!labels.length" class="hr-bar-empty">暂无数据</div>
		<template v-else>
			<div class="hr-series-legend">
				<span v-for="s in series" :key="s.name" class="hr-series-legend-item">
					<i :style="{ background: s.color }" />
					{{ s.name }}
				</span>
			</div>
			<div class="hr-series-body">
				<div
					v-for="(label, idx) in labels"
					:key="label"
					class="hr-series-col"
					:title="tooltip(idx)"
				>
					<div class="hr-series-bars">
						<div
							v-for="s in series"
							:key="s.name"
							class="hr-series-bar"
							:style="{
								height: barHeight(s.data[idx]) + '%',
								background: s.color,
							}"
						/>
					</div>
					<div class="hr-series-label">{{ shortLabel(label) }}</div>
				</div>
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	labels: { type: Array, default: () => [] },
	series: { type: Array, default: () => [] },
});

const maxVal = computed(() => {
	let m = 1;
	for (const s of props.series) {
		for (const v of s.data || []) m = Math.max(m, Number(v) || 0);
	}
	return m;
});

function barHeight(v) {
	return Math.round(((Number(v) || 0) / maxVal.value) * 100);
}

function shortLabel(label) {
	const parts = String(label).split("-");
	return parts.length === 2 ? `${Number(parts[1])}月` : label;
}

function tooltip(idx) {
	const parts = props.series.map((s) => `${s.name}: ${s.data?.[idx] ?? 0}`);
	return `${props.labels[idx]}\n${parts.join("\n")}`;
}
</script>
