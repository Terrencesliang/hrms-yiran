<template>
	<div ref="el" class="hr-echart" :style="{ height, width: '100%' }" />
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts/core";
import { BarChart, LineChart, PieChart } from "echarts/charts";
import {
	GridComponent,
	LegendComponent,
	TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
	BarChart,
	LineChart,
	PieChart,
	GridComponent,
	LegendComponent,
	TooltipComponent,
	CanvasRenderer,
]);

const props = defineProps({
	option: { type: Object, default: () => ({}) },
	height: { type: String, default: "220px" },
});

const el = ref(null);
let chart = null;
let ro = null;

function render() {
	if (!el.value) return;
	if (!chart) chart = echarts.init(el.value);
	chart.setOption(props.option || {}, true);
	nextTick(() => chart?.resize());
}

function onResize() {
	chart?.resize();
}

onMounted(() => {
	render();
	window.addEventListener("resize", onResize);
	if (typeof ResizeObserver !== "undefined" && el.value) {
		ro = new ResizeObserver(() => chart?.resize());
		ro.observe(el.value);
	}
});

onBeforeUnmount(() => {
	window.removeEventListener("resize", onResize);
	ro?.disconnect();
	ro = null;
	chart?.dispose();
	chart = null;
});

watch(
	() => props.option,
	() => render(),
	{ deep: true }
);

watch(
	() => props.height,
	() => nextTick(() => chart?.resize())
);
</script>
