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

		<a-alert v-if="errorMessage" type="error" show-icon class="cs-error-alert">
			{{ errorMessage }}
		</a-alert>

		<a-card :bordered="false" class="cs-table-card">
			<template #title>{{ pageTitle }}</template>
			<a-table
				:columns="columns"
				:data="filteredRows"
				:loading="loading"
				:pagination="{ pageSize: 10 }"
				:bordered="false"
				row-key="id"
				:scroll="{ x: 1080 }"
				@row-click="openDetail"
			>
				<template #empty>
					<a-empty :description="errorMessage ? '合同数据加载失败' : `暂无${pageTitle}`">
						<a-button v-if="errorMessage" @click="loadRows">重新加载</a-button>
					</a-empty>
				</template>
				<template #name="{ record }">
					<div class="cs-name">{{ record.name }}</div>
					<div class="cs-sub">{{ record.type }}</div>
				</template>
				<template #progress="{ record }">
					<a-progress :percent="record.progress / 100" size="small" :show-text="true" />
				</template>
				<template #status="{ record }">
					<a-tag :color="tagColor(record.status)">{{ record.statusLabel }}</a-tag>
				</template>
				<template #ops="{ record }">
					<div class="cs-ops" @click.stop>
						<a-link v-if="status === 'pending'" @click="onSign(record)">签署链接</a-link>
						<a-link v-if="status === 'pending'" @click="onUrge(record)">催办</a-link>
						<a-link v-if="status === 'pending'" status="danger" @click="onWithdraw(record)">撤销</a-link>
						<a-link v-if="status === 'signed'" @click="onDownload(record)">下载</a-link>
						<a-link @click="onSync(record)">同步</a-link>
						<a-link @click="openDetail(record)">查看</a-link>
					</div>
				</template>
			</a-table>
		</a-card>

		<a-drawer
			v-model:visible="drawerVisible"
			:width="460"
			unmount-on-close
			:title="active?.name || '签署详情'"
		>
			<a-spin :loading="detailLoading" class="cs-detail-spin">
				<a-descriptions v-if="active" :column="1" size="large" bordered>
					<a-descriptions-item label="Flow ID">{{ active.flowId || "—" }}</a-descriptions-item>
					<a-descriptions-item label="状态">{{ active.statusLabel || "—" }}</a-descriptions-item>
					<a-descriptions-item label="员工">{{ active.employee || "—" }}</a-descriptions-item>
					<a-descriptions-item label="合同模板">{{ active.type || "—" }}</a-descriptions-item>
					<a-descriptions-item label="发起时间">{{ active.createdAt || "—" }}</a-descriptions-item>
					<a-descriptions-item label="更新时间">{{ active.updatedAt || "—" }}</a-descriptions-item>
					<a-descriptions-item label="错误信息">
						<span :class="{ 'cs-error-text': active.error }">{{ active.error || "无" }}</span>
					</a-descriptions-item>
				</a-descriptions>
			</a-spin>
		</a-drawer>
	</div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { Message, Modal } from "@arco-design/web-vue";
import { IconPlus, IconSearch } from "@arco-design/web-vue/es/icon";
import {
	cancelContract,
	downloadSignedContract,
	getContractSigning,
	getSignUrl,
	listContractSignings,
	syncContractStatus,
	urgeContract,
} from "../../api/contract.js";
import ContractSectionNav from "./ContractSectionNav.vue";
import ContractActionToolbar from "./ContractActionToolbar.vue";

const props = defineProps({
	status: {
		type: String,
		default: "pending",
		validator: (value) => ["pending", "signed", "void"].includes(value),
	},
});

const keyword = ref("");
const department = ref("");
const contractType = ref("");
const dateRange = ref([]);
const rows = ref([]);
const loading = ref(false);
const errorMessage = ref("");
const drawerVisible = ref(false);
const detailLoading = ref(false);
const active = ref(null);
const actionIds = ref(new Set());

const pageTitle = computed(() => {
	if (props.status === "signed") return "已签署合同";
	if (props.status === "void") return "已作废合同";
	return "签署中合同";
});

const deptOptions = computed(() =>
	[...new Set(rows.value.map((row) => row.department).filter((value) => value && value !== "—"))].map(
		(value) => ({ label: value, value })
	)
);

const typeOptions = computed(() =>
	[...new Set(rows.value.map((row) => row.type).filter((value) => value && value !== "—"))].map(
		(value) => ({ label: value, value })
	)
);

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
	const query = keyword.value.trim().toLowerCase();
	let list = rows.value;
	if (query) {
		list = list.filter((row) =>
			[row.name, row.type, row.employee, row.flowId]
			.map((value) => String(value || "").toLowerCase())
			.some((value) => value.includes(query))
		);
	}
	if (department.value) list = list.filter((row) => row.department === department.value);
	if (contractType.value) list = list.filter((row) => row.type === contractType.value);
	if (dateRange.value?.length === 2) {
		const [start, end] = dateRange.value.map((value) => new Date(value).getTime());
		list = list.filter((row) => {
			const timestamp = new Date(row.createdAt).getTime();
			return Number.isFinite(timestamp) && timestamp >= start && timestamp <= end;
		});
	}
	return list;
});

function applyFilter() {
	/* Filters are computed from the current controls. */
}

function statusText(value) {
	const map = {
		pending: "签署中",
		signing: "签署中",
		completed: "已签署",
		signed: "已签署",
		cancelled: "已撤销",
		canceled: "已撤销",
		void: "已作废",
		failed: "失败",
	};
	return map[String(value || "").toLowerCase()] || value || "未知";
}

function normalizeRow(row, index) {
	const rawStatus = row?.status || row?.flow_status || props.status;
	return {
		...row,
		id: String(row?.name || row?.id || row?.signing_id || row?.flow_id || index),
		name: row?.contract_name || row?.title || row?.template_name || "电子合同",
		type: row?.template_name || row?.contract_type || row?.template || "—",
		employee: row?.employee_name || row?.employee || "—",
		department: row?.department || "—",
		initiator: row?.requested_by || row?.initiator || "—",
		flowId: row?.flow_id || row?.flowId || "",
		status: rawStatus,
		statusLabel: statusText(rawStatus),
		progress: ["completed", "signed"].includes(String(rawStatus).toLowerCase()) ? 100 : 50,
		remain: row?.remain || "—",
		createdAt: row?.requested_on || row?.creation || row?.created_at || row?.createdAt || "",
		finishedAt: row?.completed_on || row?.finishedAt || "",
		validUntil: row?.valid_until || row?.validUntil || "—",
		voidAt: row?.cancelled_on || row?.voidAt || "",
		voidReason: row?.error_status || row?.voidReason || "—",
		updatedAt: row?.modified || row?.updated_at || row?.updatedAt || "",
		error: row?.error_status || row?.error || row?.error_message || row?.last_error || "",
	};
}

function signingKey(record) {
	return record.id;
}

function tagColor(status) {
	const value = String(status || "").toLowerCase();
	if (["completed", "signed"].includes(value)) return "green";
	if (["failed", "cancelled", "canceled", "void"].includes(value)) return "red";
	return "arcoblue";
}

function safeOpen(result) {
	const value =
		(typeof result === "string" ? result : "") ||
		result?.url ||
		result?.sign_url ||
		result?.download_url ||
		result?.data?.url ||
		result?.data?.sign_url ||
		result?.data?.download_url ||
		"";
	if (!value) return false;
	try {
		const url = new URL(value, window.location.origin);
		if (!["http:", "https:"].includes(url.protocol)) return false;
		const link = document.createElement("a");
		link.href = url.href;
		link.target = "_blank";
		link.rel = "noopener noreferrer";
		link.click();
		return true;
	} catch (error) {
		return false;
	}
}

async function loadRows() {
	loading.value = true;
	errorMessage.value = "";
	try {
		const result = await listContractSignings(props.status);
		const list = Array.isArray(result) ? result : result?.rows || result?.signings || result?.data || [];
		rows.value = Array.isArray(list) ? list.map(normalizeRow) : [];
	} catch (error) {
		console.warn("[contract-signing] list failed", error);
		rows.value = [];
		errorMessage.value = "无法加载腾讯电子签合同，请检查接口配置后重试。";
	} finally {
		loading.value = false;
	}
}

async function openDetail(record) {
	active.value = record;
	drawerVisible.value = true;
	detailLoading.value = true;
	try {
		const result = await getContractSigning(signingKey(record));
		const detail = result?.signing || result?.data || result;
		if (detail) active.value = normalizeRow({ ...record, ...detail }, 0);
	} catch (error) {
		console.warn("[contract-signing] detail failed", error);
		Message.error("签署详情加载失败");
	} finally {
		detailLoading.value = false;
	}
}

async function runAction(record, action, successMessage) {
	const key = signingKey(record);
	if (actionIds.value.has(key)) return null;
	actionIds.value = new Set([...actionIds.value, key]);
	try {
		const result = await action(key);
		Message.success(successMessage);
		await loadRows();
		return result;
	} catch (error) {
		console.warn("[contract-signing] action failed", error);
		Message.error("操作失败，请稍后重试");
		return null;
	} finally {
		const next = new Set(actionIds.value);
		next.delete(key);
		actionIds.value = next;
	}
}

async function onUrge(record) {
	await runAction(record, urgeContract, `已催办：${record.employee}`);
}

function onWithdraw(record) {
	Modal.warning({
		title: "确认撤销合同",
		content: `撤销后签署流程将终止，确认撤销“${record.name}”吗？`,
		hideCancel: false,
		okText: "确认撤销",
		onOk: () => runAction(record, cancelContract, "合同已撤销"),
	});
}

async function onDownload(record) {
	const result = await runAction(record, downloadSignedContract, "下载地址已生成");
	if (result && !safeOpen(result)) Message.error("后端未返回安全的下载地址");
}

async function onSign(record) {
	try {
		const result = await getSignUrl(signingKey(record));
		if (!safeOpen(result)) Message.error("后端未返回安全的签署地址");
	} catch (error) {
		Message.error("获取签署地址失败");
	}
}

async function onSync(record) {
	await runAction(record, syncContractStatus, "签署状态已同步");
}

function onStartSign() {
	try {
		const go = window.frappe?.set_route;
		if (typeof go === "function") {
			go("contract-templates");
			return;
		}
	} catch (error) {
		console.warn("[contract-signing] navigate failed", error);
	}
	window.location.assign("/desk/contract-templates");
}

watch(() => props.status, loadRows);
onMounted(loadRows);
</script>
