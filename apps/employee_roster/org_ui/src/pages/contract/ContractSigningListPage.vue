<template>
	<div class="arco-org-ui contract-signing">
		<div class="cs-toolbar">
			<a-input v-model="keyword" class="cs-search" allow-clear placeholder="搜索合同名称 / 员工">
				<template #prefix><icon-search /></template>
			</a-input>
			<a-button :loading="loading" @click="loadRows">
				<template #icon><icon-refresh /></template>
				刷新列表
			</a-button>
			<a-button type="primary" @click="onStartSign">
				<template #icon><icon-plus /></template>
				发起签署
			</a-button>
		</div>

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
import { IconPlus, IconRefresh, IconSearch } from "@arco-design/web-vue/es/icon";
import {
	cancelContract,
	downloadSignedContract,
	getContractSigning,
	getSignUrl,
	listContractSignings,
	syncContractStatus,
	urgeContract,
} from "../../api/contract.js";

const props = defineProps({
	status: {
		type: String,
		default: "pending",
		validator: (value) => ["pending", "signed", "void"].includes(value),
	},
});

const keyword = ref("");
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

const columns = computed(() => [
	{ title: "合同", slotName: "name", width: 240 },
	{ title: "员工", dataIndex: "employee", width: 120 },
	{ title: "部门", dataIndex: "department", width: 140 },
	{ title: "Flow ID", dataIndex: "flowId", width: 180 },
	{ title: "状态", slotName: "status", width: 120 },
	{ title: "发起时间", dataIndex: "createdAt", width: 160 },
	{ title: "操作", slotName: "ops", width: 260, fixed: "right" },
]);

const filteredRows = computed(() => {
	const query = keyword.value.trim().toLowerCase();
	if (!query) return rows.value;
	return rows.value.filter((row) =>
		[row.name, row.type, row.employee, row.flowId]
			.map((value) => String(value || "").toLowerCase())
			.some((value) => value.includes(query))
	);
});

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
		flowId: row?.flow_id || row?.flowId || "",
		status: rawStatus,
		statusLabel: statusText(rawStatus),
		createdAt: row?.requested_on || row?.creation || row?.created_at || row?.createdAt || "",
		updatedAt: row?.modified || row?.updated_at || row?.updatedAt || "",
		error: row?.error || row?.error_message || row?.last_error || "",
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
