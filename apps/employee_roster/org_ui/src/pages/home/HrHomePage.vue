<template>
	<div class="arco-org-ui hr-workplace hr-wp-pro">
		<a-spin :loading="loading" style="width: 100%">
			<div class="hr-wp-stack">
				<section class="hr-wp-hero">
					<div class="hr-wp-hero-bg" aria-hidden="true" />
					<div class="hr-wp-hero-inner">
						<div class="hr-wp-hero-main">
							<h1 class="hr-wp-hero-title">
								{{ greeting }}，{{ data?.user?.full_name || "同事" }}
								<span class="hr-wp-wave">👋</span>
							</h1>
							<p class="hr-wp-hero-sub">
								用数据洞察人才，让组织更有活力。今天也是高效工作的一天！
							</p>
							<div class="hr-wp-hero-tagline">AI 就是未来 / AI IS THE FUTURE</div>
						</div>
						<div class="hr-wp-hero-side">
							<a-select
								v-if="(data?.companies || []).length > 1"
								v-model="company"
								allow-clear
								placeholder="全部公司"
								class="hr-wp-company"
								@change="reload"
							>
								<a-option v-for="c in data.companies" :key="c" :value="c">{{ c }}</a-option>
							</a-select>
							<div class="hr-wp-date-card">
								<div class="hr-wp-date">{{ data?.hero?.date_label }} {{ data?.hero?.weekday }}</div>
								<div class="hr-wp-quote">“{{ data?.hero?.quote }}”</div>
							</div>
						</div>
					</div>
				</section>

				<div class="hr-wp-kpis">
					<a-card
						v-for="card in metricCards"
						:key="card.key"
						:bordered="false"
						class="hr-wp-kpi-card"
						:class="{ 'is-clickable': !!card.route }"
						@click="card.route && go(card.route)"
					>
						<div class="hr-wp-kpi-head">
							<div
								class="hr-wp-kpi-icon"
								:style="{ background: card.color + '18', color: card.color }"
							>
								<component :is="kpiIconMap[card.icon] || IconApps" />
							</div>
							<div class="hr-wp-kpi-body">
								<div class="hr-wp-kpi-title">{{ card.title }}</div>
								<div class="hr-wp-kpi-value">
									{{ formatNum(card.value) }}
									<span class="hr-wp-kpi-unit">{{ card.suffix }}</span>
								</div>
								<div class="hr-wp-kpi-meta">
									<span class="hr-wp-kpi-delta-label">{{ card.delta_label }}</span>
									<span
										class="hr-wp-kpi-delta-abs"
										:class="card.delta_abs >= 0 ? 'is-up' : 'is-down'"
									>
										{{ card.delta_abs >= 0 ? "+" : "" }}{{ card.delta_abs }}
									</span>
									<span
										class="hr-wp-kpi-delta-pct"
										:class="card.delta_pct >= 0 ? 'is-up' : 'is-down'"
									>
										{{ card.delta_pct >= 0 ? "↑" : "↓" }}
										{{ card.delta_pct >= 0 ? "+" : "" }}{{ card.delta_pct }}%
									</span>
								</div>
							</div>
							<div class="hr-wp-kpi-chart">
								<HrEchart :option="sparkOption(card)" height="56px" />
							</div>
						</div>
					</a-card>
				</div>

				<div class="hr-wp-content">
					<a-card :bordered="false" class="hr-wp-panel hr-wp-dept-card hr-wp-cell-dept">
						<template #title>部门人员分布</template>
						<template #extra>
							<a-select v-model="deptFilter" size="small" style="width: 120px">
								<a-option value="">全部部门</a-option>
								<a-option v-for="d in deptOptions" :key="d" :value="d">{{ shortDept(d) }}</a-option>
							</a-select>
						</template>
						<div class="hr-wp-dept-charts">
							<div class="hr-wp-dept-bar">
								<HrEchart :option="deptBarOption" height="320px" />
							</div>
							<div class="hr-wp-dept-pie">
								<div class="hr-wp-dept-pie-layout">
									<div class="hr-wp-dept-pie-chart">
										<HrEchart :option="deptPieOption" height="260px" />
									</div>
									<ul v-if="deptPieLegend.length" class="hr-wp-dept-pie-legend">
										<li v-for="item in deptPieLegend" :key="item.name">
											<i :style="{ background: item.color }" aria-hidden="true" />
											<span class="hr-wp-dept-pie-legend-name">{{ item.label }}</span>
											<span class="hr-wp-dept-pie-legend-pct">{{ item.pct }}%</span>
										</li>
									</ul>
								</div>
							</div>
						</div>
					</a-card>

					<a-card :bordered="false" class="hr-wp-panel hr-wp-cell-quick">
						<template #title>快捷入口</template>
						<div class="hr-wp-quick-grid">
							<button
								v-for="link in data?.quick_links || []"
								:key="link.label"
								type="button"
								class="hr-wp-quick"
								@click="go(link.route)"
							>
								<span class="hr-wp-quick-icon">
									<component :is="iconMap[link.icon] || IconApps" />
								</span>
								<span class="hr-wp-quick-label">{{ link.label }}</span>
								<span class="hr-wp-quick-desc">{{ link.desc }}</span>
							</button>
						</div>
					</a-card>

					<a-card :bordered="false" class="hr-wp-panel hr-wp-cell-joiners">
						<template #title>近期入职员工</template>
						<template #extra>
							<a-link @click="go(['List', 'Employee'])">查看全部员工 &gt;</a-link>
						</template>
						<a-table
							class="hr-wp-join-table"
							:columns="joinerColumns"
							:data="data?.recent_joiners || []"
							:pagination="false"
							row-key="name"
							:bordered="false"
							size="medium"
						>
							<template #name="{ record }">
								<a-space>
									<a-avatar :size="32" :style="{ background: avatarColor(record.employee_name) }">
										<img v-if="record.image" :src="record.image" alt="" />
										<span v-else>{{ (record.employee_name || "?").slice(0, 1) }}</span>
									</a-avatar>
									<span>{{ record.employee_name }}</span>
								</a-space>
							</template>
							<template #department="{ record }">
								{{ record.department || "—" }}
							</template>
							<template #actions="{ record }">
								<a-dropdown trigger="click">
									<a-button type="text" size="mini">
										<icon-more />
									</a-button>
									<template #content>
										<a-doption @click="go(['Form', 'Employee', record.name])">查看员工</a-doption>
									</template>
								</a-dropdown>
							</template>
						</a-table>
					</a-card>

					<a-card :bordered="false" class="hr-wp-panel hr-wp-rank-card hr-wp-cell-rank">
						<template #title>部门人数榜</template>
						<template #extra>
							<a-link @click="go(['hr-dashboard'])">数据看板</a-link>
						</template>
						<a-table
							class="hr-rank-table hr-wp-rank-table hr-wp-rank-table--fill"
							:style="{ '--rank-rows': Math.max(deptRanking.length, 1) }"
							:columns="rankColumns"
							:data="deptRanking"
							:pagination="false"
							:bordered="false"
							row-key="rank"
							size="small"
						>
							<template #rank="{ record }">
								<span class="hr-rank" :class="'r' + Math.min(record.rank, 3)">{{ record.rank }}</span>
							</template>
							<template #name="{ record }">
								<span class="hr-wp-rank-name">{{ shortDept(record.name) }}</span>
							</template>
							<template #headcount="{ record }">
								<span class="hr-num">{{ record.headcount }}</span>
							</template>
							<template #roles="{ record }">
								<span class="hr-num">{{ record.roles }}</span>
							</template>
						</a-table>
					</a-card>
				</div>
			</div>
		</a-spin>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import {
	IconUserGroup,
	IconMindMapping,
	IconDashboard,
	IconFolder,
	IconApps,
	IconCalendar,
	IconUserAdd,
	IconExport,
	IconMore,
} from "@arco-design/web-vue/es/icon";
import HrEchart from "../../components/HrEchart.vue";
import { getHrWorkplace } from "../../api/hrHome.js";
import { hrChartTheme, useHrTheme } from "../../utils/useHrTheme.js";

const { isDark } = useHrTheme();
const chartTheme = computed(() => hrChartTheme(isDark.value));

const loading = ref(false);
const company = ref("");
const deptFilter = ref("");
const data = ref(null);

const iconMap = {
	IconUserGroup,
	IconMindMapping,
	IconDashboard,
	IconFolder,
	IconCalendar,
	IconUserAdd,
};

const kpiIconMap = {
	"user-group": IconUserGroup,
	"user-add": IconUserAdd,
	export: IconExport,
	calendar: IconCalendar,
};

const joinerColumns = [
	{ title: "员工", dataIndex: "employee_name", slotName: "name", width: 180 },
	{ title: "部门", dataIndex: "department", slotName: "department", ellipsis: true },
	{ title: "职位", dataIndex: "designation", ellipsis: true },
	{ title: "入职日期", dataIndex: "date_of_joining", width: 120 },
	{ title: "", slotName: "actions", width: 48, align: "center" },
];

const greeting = computed(() => {
	const h = new Date().getHours();
	if (h < 12) return "上午好";
	if (h < 18) return "下午好";
	return "晚上好";
});

const metricCards = computed(() => data.value?.metric_cards || []);

const deptRanking = computed(() => data.value?.dept_ranking || []);

const rankColumns = [
	{ title: "排名", dataIndex: "rank", slotName: "rank", width: 44, align: "center" },
	{ title: "部门", dataIndex: "name", slotName: "name", ellipsis: true },
	{ title: "人数", dataIndex: "headcount", slotName: "headcount", width: 52, align: "right" },
	{ title: "岗位", dataIndex: "roles", slotName: "roles", width: 52, align: "right" },
];

const deptItems = computed(() => {
	const items = [...(data.value?.by_department || [])];
	if (!deptFilter.value) return items;
	return items.filter((i) => i.name === deptFilter.value);
});

const deptOptions = computed(() => (data.value?.by_department || []).map((i) => i.name));

const deptTotal = computed(() =>
	deptItems.value.reduce((sum, item) => sum + (item.count || 0), 0)
);

function formatNum(n) {
	return Number(n || 0).toLocaleString("zh-CN");
}

function shortDept(name) {
	const s = String(name || "");
	const i = s.indexOf(" - ");
	return i > 0 ? s.slice(0, i) : s;
}

function avatarColor(name) {
	const palette = ["#165DFF", "#14C9C9", "#722ED1", "#FF7D00", "#00B42A"];
	let hash = 0;
	for (const ch of String(name || "")) hash = (hash + ch.charCodeAt(0)) % palette.length;
	return palette[hash];
}

function sparkOption(card) {
	const series = card.series || [];
	const isBar = card.chart === "bar";
	return {
		grid: { left: 0, right: 0, top: 4, bottom: 0 },
		xAxis: { type: "category", show: false, data: series.map((_, i) => i) },
		yAxis: { type: "value", show: false },
		series: [
			{
				type: isBar ? "bar" : "line",
				data: series,
				smooth: true,
				symbol: "none",
				lineStyle: { width: 2 },
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
									{ offset: 0, color: (card.color || "#165DFF") + "44" },
									{ offset: 1, color: (card.color || "#165DFF") + "00" },
								],
							},
					  },
				barWidth: 4,
			},
		],
	};
}

const deptBarOption = computed(() => {
	const theme = chartTheme.value;
	const items = [...deptItems.value].reverse();
	const names = items.map((i) => shortDept(i.name));
	const values = items.map((i) => i.count);
	return {
		backgroundColor: "transparent",
		color: ["#165DFF"],
		tooltip: {
			trigger: "axis",
			axisPointer: { type: "shadow" },
			textStyle: { fontSize: 12, color: theme.text1 },
			padding: [6, 10],
		},
		grid: { left: 88, right: 36, top: 8, bottom: 8 },
		xAxis: {
			type: "value",
			splitLine: { lineStyle: { type: "dashed", color: theme.splitLine } },
			axisLabel: { color: theme.text3 },
		},
		yAxis: {
			type: "category",
			data: names,
			axisLabel: { width: 72, overflow: "truncate", color: theme.text2 },
			axisLine: { lineStyle: { color: theme.splitLine } },
		},
		series: [
			{
				name: "人数",
				type: "bar",
				data: values,
				barWidth: 12,
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
				label: { show: true, position: "right", color: theme.text2 },
			},
		],
	};
});

const DEPT_PIE_COLORS = [
	"#165DFF",
	"#4080FF",
	"#6AA1FF",
	"#14C9C9",
	"#33D1C9",
	"#722ED1",
	"#A871E3",
	"#FF9A2E",
];

const deptPieLegend = computed(() => {
	const items = deptItems.value;
	const total = deptTotal.value || 0;
	return items.map((item, index) => ({
		name: item.name,
		label: shortDept(item.name),
		pct: total ? ((item.count / total) * 100).toFixed(1) : "0.0",
		color: DEPT_PIE_COLORS[index % DEPT_PIE_COLORS.length],
	}));
});

const deptPieOption = computed(() => {
	const theme = chartTheme.value;
	const items = deptItems.value;
	const total = deptTotal.value || 0;
	if (!items.length) {
		return {
			backgroundColor: "transparent",
			graphic: {
				type: "text",
				left: "center",
				top: "middle",
				style: { text: "暂无数据", fill: theme.text3, fontSize: 13 },
			},
		};
	}
	return {
		backgroundColor: "transparent",
		color: DEPT_PIE_COLORS,
		tooltip: {
			trigger: "item",
			formatter: "{b}: {c} ({d}%)",
			textStyle: { fontSize: 12, color: theme.text1 },
			padding: [6, 10],
		},
		series: [
			{
				type: "pie",
				radius: ["48%", "70%"],
				center: ["50%", "50%"],
				itemStyle: {
					borderRadius: 4,
					borderColor: theme.surface,
					borderWidth: 2,
				},
				label: {
					show: true,
					position: "center",
					formatter: `{v|${total}}\n{t|在职员工}`,
					rich: {
						v: { fontSize: 22, fontWeight: 600, color: theme.text1, lineHeight: 28 },
						t: { fontSize: 12, color: theme.text3, lineHeight: 18 },
					},
				},
				labelLine: { show: false },
				data: items.map((i) => ({ name: shortDept(i.name), value: i.count })),
			},
		],
	};
});

function go(route) {
	if (!route?.length || !window.frappe?.set_route) return;
	window.frappe.set_route(...route);
}

async function reload() {
	loading.value = true;
	try {
		data.value = await getHrWorkplace(company.value || undefined);
		deptFilter.value = "";
		await nextTick();
		window.dispatchEvent(new Event("resize"));
	} catch (e) {
		console.error(e);
		Message.error("加载人事主页失败");
	} finally {
		loading.value = false;
		await nextTick();
		window.dispatchEvent(new Event("resize"));
	}
}

onMounted(reload);
</script>
