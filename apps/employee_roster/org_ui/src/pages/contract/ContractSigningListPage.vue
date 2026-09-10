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
					<a-tag :color="tagColor(record.stage)">{{ record.stageLabel }}</a-tag>
				</template>
				<template #actorStatus="{ record }">
					<div class="cs-actor-status">
						<span>员工：填充 {{ record.employeeFillStatus }} / 签署 {{ record.employeeSignStatus }}</span>
						<span>企业：填充 {{ record.corpFillStatus }} / 签署 {{ record.corpSignStatus }}</span>
					</div>
				</template>
				<template #archiveStatus="{ record }">
					<a-tag :color="archiveColor(record.archiveStatus)">{{ archiveText(record.archiveStatus) }}</a-tag>
				</template>
				<template #ops="{ record }">
					<div class="cs-ops" @click.stop>
						<a-link v-if="record.employeePending" @click="onSign(record)">签署链接</a-link>
						<a-link v-if="record.companyAction" @click="onCompanySign(record)">
							{{ record.companyAction }}
						</a-link>
						<a-link v-if="status === 'pending'" @click="onUrge(record)">催办</a-link>
						<a-link v-if="status === 'pending'" status="danger" @click="onWithdraw(record)">撤销</a-link>
						<a-link v-if="status === 'signed'" @click="onDownload(record)">下载</a-link>
						<a-link v-if="record.retryable" status="danger" @click="onRetry(record)">重试</a-link>
						<a-link @click="onSync(record)">同步</a-link>
						<a-link @click="onView(record)">查看</a-link>
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
					<a-descriptions-item label="签署任务 ID">{{ active.signTaskId || "—" }}</a-descriptions-item>
					<a-descriptions-item label="状态">{{ active.statusLabel || "—" }}</a-descriptions-item>
					<a-descriptions-item label="当前节点">{{ active.stageLabel || "—" }}</a-descriptions-item>
					<a-descriptions-item label="员工状态">填充 {{ active.employeeFillStatus }} / 签署 {{ active.employeeSignStatus }}</a-descriptions-item>
					<a-descriptions-item label="企业状态">填充 {{ active.corpFillStatus }} / 签署 {{ active.corpSignStatus }}</a-descriptions-item>
					<a-descriptions-item label="归档状态">{{ archiveText(active.archiveStatus) }}</a-descriptions-item>
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
	getCompanySignUrl,
	getSignUrl,
	listContractSignings,
	retryContract,
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
			{ title: "参与方状态", slotName: "actorStatus", width: 210 },
			{ title: "进度", slotName: "progress", width: 140 },
			{ title: "归档", slotName: "archiveStatus", width: 100 },
			{ title: "剩余时效", dataIndex: "remain", width: 100 },
			{ title: "操作", slotName: "ops", width: 220, fixed: "right", align: "left" },
		];
	}
	if (props.status === "signed") {
		return [
			...base,
			{ title: "完成时间", dataIndex: "finishedAt", width: 160 },
			{ title: "参与方状态", slotName: "actorStatus", width: 210 },
			{ title: "归档", slotName: "archiveStatus", width: 100 },
			{ title: "有效期至", dataIndex: "validUntil", width: 120 },
			{ title: "操作", slotName: "ops", width: 180, fixed: "right", align: "left" },
		];
	}
	return [
		...base,
		{ title: "作废时间", dataIndex: "voidAt", width: 160 },
		{ title: "原因", dataIndex: "voidReason", width: 220 },
		{ title: "操作", slotName: "ops", width: 100, fixed: "right", align: "left" },
	];
});

const filteredRows = computed(() => {
	const query = keyword.value.trim().toLowerCase();
	let list = rows.value;
	if (query) {
		list = list.filter((row) =>
			[row.name, row.type, row.employee, row.signTaskId]
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
		error: "异常",
	};
	return map[String(value || "").toLowerCase()] || value || "未知";
}

function parseActorStatus(value) {
	if (!value) return [];
	let parsed = value;
	if (typeof value === "string") {
		try {
			parsed = JSON.parse(value);
		} catch {
			return [];
		}
	}
	if (Array.isArray(parsed)) return parsed;
	if (Array.isArray(parsed?.actors)) return parsed.actors;
	if (typeof parsed === "object") {
		return Object.entries(parsed).map(([key, item]) =>
			typeof item === "object" ? { actorKey: key, ...item } : { actorKey: key, signStatus: item }
		);
	}
	return [];
}

function statusValue(actor, kind) {
	const keys = kind === "fill"
		? ["fillStatus", "fill_status", "fillTaskStatus", "fill_task_status"]
		: ["signStatus", "sign_status", "status", "signTaskStatus", "sign_task_status"];
	const sources = [
		actor,
		actor?.actor,
		actor?.fillConfigInfo,
		actor?.fill_config_info,
		actor?.signConfigInfo,
		actor?.sign_config_info,
	];
	for (const source of sources) {
		for (const key of keys) {
			if (source?.[key] !== undefined && source?.[key] !== null && source?.[key] !== "") return source[key];
		}
	}
	return "";
}

function actorRole(actor) {
	const text = [
		actor?.actorKey,
		actor?.actorType,
		actor?.actor_type,
		actor?.role,
		actor?.actorName,
		actor?.actor_name,
		actor?.actor?.actorType,
		actor?.actor?.actorName,
		actor?.actor?.actorId,
	].join(" ").toLowerCase();
	if (/corp|company|enterprise|企业|公司/.test(text)) return "corp";
	if (/employee|person|personal|员工|个人/.test(text)) return "employee";
	if (actor?.corpName || actor?.corp_name) return "corp";
	return "";
}

function displayActorStatus(value) {
	if (value === "" || value === null || value === undefined) return "—";
	const map = {
		pending: "待处理", waiting: "待处理", not_started: "未开始",
		wait_fill: "待填写", fill_progress: "填写中", filling: "填写中",
		fill_completed: "已填写", filled: "已填写", wait_sign: "待签署",
		sign_progress: "签署中", signing: "签署中", sign_completed: "已签署",
		signed: "已签署", completed: "已完成", failed: "失败",
	};
	return map[String(value).toLowerCase()] || String(value);
}

function actorSummary(value, employeeActorId = "") {
	const actors = parseActorStatus(value);
	const actorId = (actor) => String(actor?.actorId || actor?.actor_id || actor?.actor?.actorId || "");
	const employee =
		actors.find((actor) => employeeActorId && actorId(actor) === String(employeeActorId)) ||
		actors.find((actor) => actorRole(actor) === "employee") ||
		{};
	const corp =
		actors.find((actor) => actor !== employee && actorRole(actor) === "corp") ||
		actors.find((actor) => actor !== employee) ||
		{};
	const employeeSignRaw = statusValue(employee, "sign");
	const companySignRaw = statusValue(corp, "sign");
	const companyFillRaw = statusValue(corp, "fill");
	return {
		employeeFillStatus: displayActorStatus(statusValue(employee, "fill")),
		employeeSignStatus: displayActorStatus(employeeSignRaw),
		corpFillStatus: displayActorStatus(companyFillRaw),
		corpSignStatus: displayActorStatus(companySignRaw),
		employeePending: ["pending", "waiting", "signing", "unsigned", "待签署", "待处理"].includes(
			String(employeeSignRaw || "").toLowerCase()
		),
		companyPending: ["pending", "waiting", "signing", "unsigned", "wait_sign", "待签署", "待处理"].includes(
			String(companySignRaw || "").toLowerCase()
		),
		companyFillPending: ["pending", "waiting", "filling", "wait_fill", "待填写", "待处理"].includes(
			String(companyFillRaw || "").toLowerCase()
		),
	};
}

function stageText(value) {
	const map = {
		preparing: "准备中",
		ready: "待启动",
		employeesigning: "员工待签",
		companysigning: "企业待验证盖章",
		signing: "签署中",
		finishing: "收尾中",
		finished: "已完成",
		terminated: "已终止",
		unknown: "未知",
	};
	return map[String(value || "unknown").toLowerCase()] || "未知";
}

function stageProgress(value) {
	const map = { preparing: 10, ready: 25, employeesigning: 45, signing: 60, companysigning: 75, finishing: 85, finished: 100, terminated: 100, unknown: 0 };
	return map[String(value || "unknown").toLowerCase()] ?? 0;
}

function normalizeRow(row, index) {
	const rawStatus = row?.status || row?.sign_task_status || row?.flow_status || props.status;
	const stage = row?.stage || "Unknown";
	const actors = actorSummary(row?.actor_status, row?.provider_actor_id);
	if (row?.employee_sign_status) {
		actors.employeeSignStatus = displayActorStatus(row.employee_sign_status);
		actors.employeePending = ["wait_sign", "signing", "pending"].includes(
			String(row.employee_sign_status).toLowerCase()
		);
	}
	if (row?.company_sign_status) {
		actors.corpSignStatus = displayActorStatus(row.company_sign_status);
		actors.companyPending = ["wait_sign", "signing", "pending"].includes(
			String(row.company_sign_status).toLowerCase()
		);
	}
	if (row?.company_fill_status) {
		actors.corpFillStatus = displayActorStatus(row.company_fill_status);
		actors.companyFillPending = ["wait_fill", "filling", "pending"].includes(
			String(row.company_fill_status).toLowerCase()
		);
	}
	actors.companyPending = actors.companyPending && String(stage).toLowerCase() === "companysigning";
	actors.companyAction =
		String(stage).toLowerCase() === "companysigning" && actors.companyPending
			? "企业盖章"
			: String(stage).toLowerCase() === "preparing" && actors.companyFillPending
				? "确认合同内容"
				: "";
	const archiveStatus = row?.archive_status || "";
	const signTaskId = row?.sign_task_id || row?.signTaskId || row?.flow_id || row?.flowId || "";
	return {
		...row,
		...actors,
		id: String(row?.name || row?.id || row?.signing_id || signTaskId || index),
		name: row?.contract_name || row?.title || row?.template_name || "电子合同",
		type: row?.template_name || row?.contract_type || row?.template || "—",
		employee: row?.employee_name || row?.employee || "—",
		department: row?.department || "—",
		initiator: row?.requested_by || row?.initiator || "—",
		signTaskId,
		status: rawStatus,
		statusLabel: statusText(rawStatus),
		stage,
		stageLabel: stageText(stage),
		progress: stageProgress(stage),
		archiveStatus,
		retryable:
			String(rawStatus).toLowerCase() === "error" ||
			String(archiveStatus).toLowerCase() === "failed",
		remain: row?.remain || "—",
		createdAt: row?.requested_on || row?.creation || row?.created_at || row?.createdAt || "",
		finishedAt: row?.completed_on || row?.finishedAt || "",
		validUntil: row?.valid_until || row?.validUntil || "—",
		voidAt: row?.cancelled_on || row?.voidAt || "",
		voidReason: row?.error_status || row?.voidReason || "—",
		updatedAt: row?.modified || row?.updated_at || row?.updatedAt || "",
		signedFile: row?.signed_file || row?.signedFile || "",
		error: row?.error_status || row?.error || row?.error_message || row?.last_error || "",
	};
}

function signingKey(record) {
	return record.id;
}

function tagColor(status) {
	const value = String(status || "").toLowerCase();
	if (value === "finished") return "green";
	if (value === "terminated") return "red";
	return "arcoblue";
}

function archiveText(value) {
	const map = { pending: "待归档", processing: "归档中", archiving: "归档中", archived: "已归档", completed: "已归档", success: "已归档", failed: "失败" };
	return map[String(value || "").toLowerCase()] || value || "—";
}

function archiveColor(value) {
	const key = String(value || "").toLowerCase();
	if (["archived", "completed", "success"].includes(key)) return "green";
	if (key === "failed") return "red";
	return "gray";
}

function safeOpen(result, { preview = false } = {}) {
	const value =
		(typeof result === "string" ? result : "") ||
		result?.url ||
		result?.sign_url ||
		result?.download_url ||
		result?.preview_url ||
		result?.data?.url ||
		result?.data?.sign_url ||
		result?.data?.download_url ||
		result?.data?.preview_url ||
		"";
	if (!value) return false;
	try {
		let href = value;
		if (preview) {
			href = String(value).replace(
				"employee_roster.integrations.tencent_cos.storage.download_file",
				"employee_roster.integrations.tencent_cos.storage.preview_file"
			);
		}
		const url = new URL(href, window.location.origin);
		if (!["http:", "https:"].includes(url.protocol)) return false;
		window.open(url.href, "_blank", "noopener,noreferrer");
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
		errorMessage.value = error?.message || "无法加载电子签合同，请检查服务配置后重试。";
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
		Message.error(error?.message || "签署详情加载失败");
	} finally {
		detailLoading.value = false;
	}
}

async function onPreviewFile(record) {
	const localUrl = record.signedFile || record.signed_file || "";
	if (localUrl && safeOpen(localUrl, { preview: true })) return;
	try {
		const result = await downloadSignedContract(signingKey(record));
		if (!safeOpen(result, { preview: true })) Message.error("后端未返回可预览的合同文件地址");
	} catch (error) {
		console.warn("[contract-signing] preview failed", error);
		Message.error(error?.message || "打开合同预览失败");
	}
}

async function onView(record) {
	if (props.status === "signed" || record.signedFile || record.signed_file) {
		await onPreviewFile(record);
		return;
	}
	await openDetail(record);
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
		Message.error(error?.message || "操作失败，请稍后重试");
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
		Message.error(error?.message || "获取签署地址失败");
	}
}

async function onCompanySign(record) {
	try {
		const result = await getCompanySignUrl(signingKey(record));
		if (!safeOpen(result)) Message.error("后端未返回安全的企业盖章地址");
	} catch (error) {
		Message.error(error?.message || "获取企业盖章地址失败");
	}
}

async function onSync(record) {
	await runAction(record, syncContractStatus, "签署状态已同步");
}

async function onRetry(record) {
	await runAction(record, retryContract, "重试请求已提交");
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
