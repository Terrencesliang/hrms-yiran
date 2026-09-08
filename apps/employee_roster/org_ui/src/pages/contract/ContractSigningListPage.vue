<template>
	<div class="arco-org-ui contract-signing">
		<ContractSectionNav group="signing" :active-key="`contract-signing-${status}`" />

		<ContractActionToolbar :title="toolbarTitle" :description="toolbarDescription">
			<template #filters>
				<a-input
					v-model="keyword"
					class="cs-search"
					allow-clear
					placeholder="搜索合同名称 / 员工"
					@press-enter="applyFilter"
					@clear="applyFilter"
				>
					<template #prefix><icon-search /></template>
				</a-input>
				<a-select
					v-model="department"
					class="cs-filter"
					allow-clear
					placeholder="部门"
					:options="deptOptions"
				/>
				<a-select
					v-model="contractType"
					class="cs-filter"
					allow-clear
					placeholder="合同类型"
					:options="typeOptions"
				/>
				<a-range-picker v-model="dateRange" class="cs-range" />
			</template>
			<template #actions>
				<a-button type="primary" @click="onStartSign">
					<template #icon><icon-plus /></template>
					发起签署
				</a-button>
			</template>
		</ContractActionToolbar>

		<a-card v-if="status === 'pending'" :bordered="false" class="cs-stats-card">
			<a-row :gutter="16">
				<a-col v-for="item in pendingStats" :key="item.key" :xs="24" :sm="8">
					<button
						type="button"
						class="cs-stat"
						:class="{ 'is-active': pendingFilter === item.key }"
						@click="pendingFilter = pendingFilter === item.key ? '' : item.key"
					>
						<div class="cs-stat-label">{{ item.label }}</div>
						<div class="cs-stat-value" :class="{ 'is-alert': item.alert }">{{ item.value }}</div>
					</button>
				</a-col>
			</a-row>
		</a-card>

		<a-card :bordered="false" class="cs-table-card">
			<template #title>{{ pageTitle }}</template>
			<a-table
				:columns="columns"
				:data="filteredRows"
				:pagination="{ pageSize: 10 }"
				:bordered="false"
				row-key="id"
				:scroll="{ x: 1100 }"
				@row-click="openDetail"
			>
				<template #name="{ record }">
					<div class="cs-name">{{ record.name }}</div>
					<div class="cs-sub">{{ record.type }}</div>
				</template>
				<template #progress="{ record }">
					<a-progress :percent="record.progress / 100" size="small" :show-text="true" />
				</template>
				<template #status="{ record }">
					<a-tag :color="statusTagColor">{{ record.node || statusLabel }}</a-tag>
				</template>
				<template #ops="{ record }">
					<div class="cs-ops" @click.stop>
						<a-link v-if="status === 'pending'" @click="onUrge(record)">催办</a-link>
						<a-link v-if="status === 'pending'" status="danger" @click="onWithdraw(record)">撤回</a-link>
						<a-link v-if="status === 'signed'" @click="onDownload(record)">下载</a-link>
						<a-link v-if="status === 'signed'" @click="onArchive(record)">归档</a-link>
						<a-link @click="openDetail(record)">查看</a-link>
					</div>
				</template>
			</a-table>
		</a-card>

		<a-drawer
			v-model:visible="drawerVisible"
			:width="420"
			unmount-on-close
			:title="active?.name || '签署详情'"
		>
			<template v-if="active">
				<a-descriptions :column="1" size="large" bordered>
					<a-descriptions-item label="合同类型">{{ active.type }}</a-descriptions-item>
					<a-descriptions-item label="员工">{{ active.employee }}</a-descriptions-item>
					<a-descriptions-item label="部门">{{ active.department }}</a-descriptions-item>
					<a-descriptions-item label="发起人">{{ active.initiator }}</a-descriptions-item>
					<a-descriptions-item label="发起时间">{{ active.createdAt }}</a-descriptions-item>
					<a-descriptions-item v-if="status === 'signed'" label="完成时间">
						{{ active.finishedAt }}
					</a-descriptions-item>
					<a-descriptions-item v-if="status === 'signed'" label="有效期">
						{{ active.validUntil }}
					</a-descriptions-item>
					<a-descriptions-item v-if="status === 'void'" label="作废时间">
						{{ active.voidAt }}
					</a-descriptions-item>
					<a-descriptions-item v-if="status === 'void'" label="作废原因">
						{{ active.voidReason }}
					</a-descriptions-item>
				</a-descriptions>

				<div class="cs-drawer-title">签署方进度</div>
				<a-timeline>
					<a-timeline-item
						v-for="step in active.timeline"
						:key="step.id"
						:dot-color="step.color"
					>
						<div class="cs-tl-title">{{ step.title }}</div>
						<div class="cs-tl-meta">{{ step.meta }}</div>
					</a-timeline-item>
				</a-timeline>
			</template>
		</a-drawer>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import { IconPlus, IconSearch } from "@arco-design/web-vue/es/icon";
import ContractSectionNav from "./ContractSectionNav.vue";
import ContractActionToolbar from "./ContractActionToolbar.vue";

const props = defineProps({
	status: {
		type: String,
		default: "pending",
		validator: (v) => ["pending", "signed", "void"].includes(v),
	},
});

const keyword = ref("");
const department = ref("");
const contractType = ref("");
const dateRange = ref([]);
const pendingFilter = ref("");
const drawerVisible = ref(false);
const active = ref(null);

const deptOptions = [
	{ label: "人事行政部", value: "人事行政部" },
	{ label: "技术中心", value: "技术中心" },
	{ label: "电商运营部", value: "电商运营部" },
];

const typeOptions = [
	{ label: "劳动合同", value: "劳动合同" },
	{ label: "保密协议", value: "保密协议" },
	{ label: "实习协议", value: "实习协议" },
];

const pageTitle = computed(() => {
	if (props.status === "signed") return "已签署合同";
	if (props.status === "void") return "已作废合同";
	return "签署中合同";
});

const toolbarTitle = computed(() => pageTitle.value);

const toolbarDescription = computed(() => {
	if (props.status === "signed") return "检索已完成的签署记录，支持下载与归档";
	if (props.status === "void") return "查看已作废合同及作废原因";
	return "筛选签署任务，按部门、类型与日期跟踪进度";
});

const statusLabel = computed(() => {
	if (props.status === "signed") return "已签署";
	if (props.status === "void") return "已作废";
	return "签署中";
});

const statusTagColor = computed(() => {
	if (props.status === "signed") return "green";
	if (props.status === "void") return "red";
	return "arcoblue";
});

const pendingStats = [
	{ key: "mine", label: "待我签署", value: 2, alert: true },
	{ key: "peer", label: "待对方签署", value: 5, alert: false },
	{ key: "expiring", label: "即将超时", value: 1, alert: true },
];

const allRows = {
	pending: [
		{
			id: "p1",
			name: "依然集团-劳动合同",
			type: "劳动合同",
			employee: "张三",
			department: "技术中心",
			initiator: "李人事",
			createdAt: "2026-09-05 10:20",
			node: "待员工签署",
			progress: 50,
			remain: "2天",
			bucket: "peer",
			timeline: [
				{ id: 1, title: "发起签署", meta: "李人事 · 2026-09-05 10:20", color: "#00b386" },
				{ id: 2, title: "企业已盖章", meta: "公章 · 2026-09-05 11:00", color: "#00b386" },
				{ id: 3, title: "待员工签署", meta: "张三 · 进行中", color: "#165dff" },
			],
		},
		{
			id: "p2",
			name: "依然集团-保密协议",
			type: "保密协议",
			employee: "王五",
			department: "电商运营部",
			initiator: "李人事",
			createdAt: "2026-09-06 09:10",
			node: "待我盖章",
			progress: 30,
			remain: "1天",
			bucket: "mine",
			timeline: [
				{ id: 1, title: "发起签署", meta: "李人事 · 2026-09-06 09:10", color: "#00b386" },
				{ id: 2, title: "员工已签署", meta: "王五 · 2026-09-06 14:00", color: "#00b386" },
				{ id: 3, title: "待企业盖章", meta: "人事 · 进行中", color: "#165dff" },
			],
		},
		{
			id: "p3",
			name: "依然杭州-劳动合同",
			type: "劳动合同",
			employee: "赵六",
			department: "人事行政部",
			initiator: "周主管",
			createdAt: "2026-09-01 16:40",
			node: "待员工签署",
			progress: 40,
			remain: "6小时",
			bucket: "expiring",
			timeline: [
				{ id: 1, title: "发起签署", meta: "周主管 · 2026-09-01 16:40", color: "#00b386" },
				{ id: 2, title: "待员工签署", meta: "赵六 · 即将超时", color: "#f53f3f" },
			],
		},
	],
	signed: [
		{
			id: "s1",
			name: "依然集团-劳动合同",
			type: "劳动合同",
			employee: "陈七",
			department: "技术中心",
			initiator: "李人事",
			createdAt: "2026-08-10 11:00",
			finishedAt: "2026-08-12 15:30",
			validUntil: "2029-08-11",
			timeline: [
				{ id: 1, title: "发起签署", meta: "李人事 · 2026-08-10", color: "#00b386" },
				{ id: 2, title: "双方签署完成", meta: "2026-08-12 15:30", color: "#00b386" },
			],
		},
		{
			id: "s2",
			name: "依然集团-实习协议",
			type: "实习协议",
			employee: "孙八",
			department: "电商运营部",
			initiator: "周主管",
			createdAt: "2026-07-20 09:00",
			finishedAt: "2026-07-21 10:10",
			validUntil: "2026-12-31",
			timeline: [
				{ id: 1, title: "发起签署", meta: "周主管 · 2026-07-20", color: "#00b386" },
				{ id: 2, title: "双方签署完成", meta: "2026-07-21 10:10", color: "#00b386" },
			],
		},
	],
	void: [
		{
			id: "v1",
			name: "依然集团-保密协议",
			type: "保密协议",
			employee: "钱九",
			department: "人事行政部",
			initiator: "李人事",
			createdAt: "2026-06-01 14:00",
			voidAt: "2026-06-03 09:20",
			voidReason: "员工信息填写错误，重新发起",
			timeline: [
				{ id: 1, title: "发起签署", meta: "李人事 · 2026-06-01", color: "#86909c" },
				{ id: 2, title: "已作废", meta: "2026-06-03 09:20", color: "#f53f3f" },
			],
		},
	],
};

const columns = computed(() => {
	const base = [
		{ title: "合同", slotName: "name", width: 240 },
		{ title: "员工", dataIndex: "employee", width: 100 },
		{ title: "部门", dataIndex: "department", width: 120 },
		{ title: "发起人", dataIndex: "initiator", width: 100 },
		{ title: "发起时间", dataIndex: "createdAt", width: 160 },
	];
	if (props.status === "pending") {
		return [
			...base,
			{ title: "当前节点", slotName: "status", width: 120 },
			{ title: "进度", slotName: "progress", width: 140 },
			{ title: "剩余时效", dataIndex: "remain", width: 100 },
			{ title: "操作", slotName: "ops", width: 180, fixed: "right" },
		];
	}
	if (props.status === "signed") {
		return [
			...base,
			{ title: "完成时间", dataIndex: "finishedAt", width: 160 },
			{ title: "有效期至", dataIndex: "validUntil", width: 120 },
			{ title: "操作", slotName: "ops", width: 180, fixed: "right" },
		];
	}
	return [
		...base,
		{ title: "作废时间", dataIndex: "voidAt", width: 160 },
		{ title: "原因", dataIndex: "voidReason", width: 220 },
		{ title: "操作", slotName: "ops", width: 100, fixed: "right" },
	];
});

const filteredRows = computed(() => {
	let list = (allRows[props.status] || []).slice();
	const q = keyword.value.trim().toLowerCase();
	if (q) {
		list = list.filter(
			(row) =>
				row.name.toLowerCase().includes(q) ||
				row.employee.toLowerCase().includes(q) ||
				row.type.toLowerCase().includes(q)
		);
	}
	if (department.value) list = list.filter((row) => row.department === department.value);
	if (contractType.value) list = list.filter((row) => row.type === contractType.value);
	if (props.status === "pending" && pendingFilter.value) {
		list = list.filter((row) => row.bucket === pendingFilter.value);
	}
	return list;
});

function applyFilter() {
	/* computed */
}

function go(route) {
	try {
		window.frappe?.set_route?.(route);
	} catch (e) {
		console.warn("[contract-signing] navigate failed", e);
	}
}

function onStartSign() {
	try {
		window.frappe?.set_route?.("contract-templates");
	} catch (e) {
		console.warn("[contract-signing] navigate failed", e);
	}
}

function openDetail(record) {
	active.value = record;
	drawerVisible.value = true;
}

function onUrge(record) {
	Message.success(`已催办：${record.employee}`);
}

function onWithdraw(record) {
	Message.warning(`已撤回：${record.name}`);
}

function onDownload(record) {
	Message.info(`下载：${record.name}（示意）`);
}

function onArchive(record) {
	Message.success(`已归档：${record.name}`);
	go(["contract-archive"]);
}
</script>
