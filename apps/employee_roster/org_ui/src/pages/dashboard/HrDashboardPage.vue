<template>
	<div class="arco-org-ui hr-dashboard hr-analysis">
		<a-spin :loading="loading" style="width: 100%">
			<!-- Arco Spin 不包 .arco-spin-children，内容直接挂在 .arco-spin 下，间距必须落在本层 -->
			<div class="hr-analysis-stack">
				<div class="hr-analysis-toolbar">
					<a-breadcrumb>
						<a-breadcrumb-item>人事</a-breadcrumb-item>
						<a-breadcrumb-item>数据面板</a-breadcrumb-item>
					</a-breadcrumb>
					<a-select
						v-if="(data?.companies || []).length > 1"
						v-model="company"
						allow-clear
						placeholder="全部公司"
						style="width: 180px"
						@change="reload"
					>
						<a-option v-for="c in data.companies" :key="c" :value="c">{{ c }}</a-option>
					</a-select>
				</div>

				<div class="hr-analysis-kpis">
					<a-card v-for="card in metricCards" :key="card.key" :bordered="false" class="hr-kpi-card">
						<div class="hr-kpi-head">
							<div>
								<div class="hr-kpi-title">{{ card.title }}</div>
								<div class="hr-kpi-value">{{ formatNum(card.value) }}</div>
								<div class="hr-kpi-delta" :class="card.delta >= 0 ? 'is-up' : 'is-down'">
									{{ card.delta_label }} {{ Math.abs(card.delta) }}%
									<span>{{ card.delta >= 0 ? "↑" : "↓" }}</span>
								</div>
							</div>
							<div class="hr-kpi-chart">
								<HrEchart :option="sparkOption(card)" height="70px" />
							</div>
						</div>
					</a-card>
				</div>

				<div class="hr-analysis-mid">
					<a-card :bordered="false" class="hr-panel-card hr-panel-card--fill">
						<template #title>部门人员分布</template>
						<template #extra>
							<a-link @click="goEmployee">查看花名册</a-link>
						</template>
						<div class="hr-panel-body">
							<HrEchart :option="deptBarOption" height="340px" />
						</div>
					</a-card>
					<a-card :bordered="false" class="hr-panel-card hr-panel-card--fill">
						<template #title>部门人数榜</template>
						<template #extra>
							<a-link @click="goOrg">组织架构</a-link>
						</template>
						<div class="hr-panel-body hr-rank-wrap">
							<a-table
								class="hr-rank-table"
								:columns="rankColumns"
								:data="deptRanking"
								:pagination="false"
								:bordered="false"
								row-key="rank"
								size="medium"
							>
								<template #rank="{ record }">
									<span class="hr-rank" :class="'r' + Math.min(record.rank, 3)">{{ record.rank }}</span>
								</template>
								<template #name="{ record }">
									{{ shortDept(record.name) }}
								</template>
								<template #headcount="{ record }">
									<span class="hr-num">{{ record.headcount }}</span>
								</template>
								<template #roles="{ record }">
									<span class="hr-num">{{ record.roles }}</span>
								</template>
							</a-table>
						</div>
					</a-card>
				</div>

				<a-card :bordered="false" class="hr-panel-card" title="近 12 个月入职 / 离职">
					<HrEchart :option="periodOption" height="320px" />
				</a-card>
			</div>
		</a-spin>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import HrEchart from "../../components/HrEchart.vue";
import { getHrDashboard } from "../../api/hrHome.js";

const loading = ref(false);
const company = ref("");
const data = ref(null);

const metricCards = computed(() => data.value?.metric_cards || []);
const deptRanking = computed(() => data.value?.dept_ranking || []);

const rankColumns = [
	{ title: "排名", dataIndex: "rank", slotName: "rank", width: 56, align: "center" },
	{ title: "部门", dataIndex: "name", slotName: "name", ellipsis: true },
	{ title: "人数", dataIndex: "headcount", slotName: "headcount", width: 72, align: "right" },
	{ title: "岗位数", dataIndex: "roles", slotName: "roles", width: 72, align: "right" },
];

function formatNum(n) {
	return Number(n || 0).toLocaleString("zh-CN");
}

function shortDept(name) {
	const s = String(name || "");
	const i = s.indexOf(" - ");
	return i > 0 ? s.slice(0, i) : s;
}

function sparkOption(card) {
	if (card.chart === "pie") {
		const pie = card.pie || [];
		return {
			color: ["#165DFF", "#14C9C9", "#F7BA1E", "#722ED1", "#FF7D00"],
			tooltip: { trigger: "item" },
			series: [
				{
					type: "pie",
					radius: ["48%", "72%"],
					center: ["58%", "50%"],
					label: { show: false },
					data: pie.map((p) => ({ name: p.name, value: p.count })),
				},
			],
		};
	}
	const series = card.series || [];
	const isBar = card.chart === "bar";
	return {
		grid: { left: 0, right: 0, top: 8, bottom: 0 },
		xAxis: { type: "category", show: false, data: series.map((_, i) => i) },
		yAxis: { type: "value", show: false },
		series: [
			{
				type: isBar ? "bar" : "line",
				data: series,
				smooth: true,
				symbol: "none",
				lineStyle: { width: 2, type: card.key === "exits_year" ? "dashed" : "solid" },
				itemStyle: { color: card.color || "#165DFF" },
				areaStyle: isBar
					? undefined
					: {
							color: {
								type: "linear",
								x: 0,
								y: 0,
								x2: 0,
								y2: 1,
								colorStops: [
									{ offset: 0, color: (card.color || "#165DFF") + "55" },
									{ offset: 1, color: (card.color || "#165DFF") + "00" },
								],
							},
					  },
				barWidth: 6,
			},
		],
	};
}

const deptBarOption = computed(() => {
	const items = [...(data.value?.by_department || [])].reverse();
	const names = items.map((i) => shortDept(i.name));
	const values = items.map((i) => i.count);
	return {
		color: ["#165DFF"],
		tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
		grid: { left: 96, right: 36, top: 16, bottom: 16 },
		xAxis: {
			type: "value",
			splitLine: { lineStyle: { type: "dashed" } },
		},
		yAxis: {
			type: "category",
			data: names,
			axisLabel: { width: 80, overflow: "truncate" },
		},
		series: [
			{
				name: "在职人数",
				type: "bar",
				data: values,
				barWidth: 14,
				itemStyle: {
					borderRadius: [0, 2, 2, 0],
					color: {
						type: "linear",
						x: 0,
						y: 0,
						x2: 1,
						y2: 0,
						colorStops: [
							{ offset: 0, color: "#94BFFF" },
							{ offset: 1, color: "#165DFF" },
						],
					},
				},
				label: { show: true, position: "right", color: "#4E5969" },
			},
		],
	};
});

const periodOption = computed(() => {
	const pa = data.value?.period_analysis || {};
	const hiring = pa.hiring || [];
	const attrition = pa.attrition || [];
	const net = pa.net || [];
	return {
		color: ["#165DFF", "#F77234", "#14C9C9"],
		tooltip: { trigger: "axis" },
		legend: { data: ["入职", "离职", "净增"], top: 0 },
		grid: { left: 48, right: 24, top: 40, bottom: 28 },
		xAxis: {
			type: "category",
			boundaryGap: false,
			data: pa.labels || [],
			axisLabel: { color: "#86909C" },
		},
		yAxis: {
			type: "value",
			minInterval: 1,
			splitLine: { lineStyle: { type: "dashed" } },
			axisLabel: { color: "#86909C" },
		},
		series: [
			{
				name: "入职",
				type: "line",
				smooth: true,
				showSymbol: true,
				symbolSize: 6,
				data: hiring,
				areaStyle: { opacity: 0.12 },
			},
			{
				name: "离职",
				type: "line",
				smooth: true,
				showSymbol: true,
				symbolSize: 6,
				data: attrition,
				areaStyle: { opacity: 0.08 },
			},
			{
				name: "净增",
				type: "line",
				smooth: true,
				showSymbol: true,
				symbolSize: 6,
				data: net,
			},
		],
	};
});

function goEmployee() {
	window.frappe?.set_route?.("List", "Employee");
}
function goOrg() {
	window.frappe?.set_route?.("orgchart");
}

async function reload() {
	loading.value = true;
	try {
		data.value = await getHrDashboard(company.value || undefined);
		await nextTick();
		window.dispatchEvent(new Event("resize"));
	} catch (e) {
		console.error(e);
		Message.error("加载数据面板失败");
	} finally {
		loading.value = false;
		await nextTick();
		window.dispatchEvent(new Event("resize"));
	}
}

onMounted(reload);
</script>
