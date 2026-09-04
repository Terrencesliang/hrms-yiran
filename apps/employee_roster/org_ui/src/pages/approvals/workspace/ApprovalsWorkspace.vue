<template>
	<div class="arco-org-ui ap-root ap-workspace">
		<header class="ap-panel-header">
			<div>
				<h1 class="oc-page-title" style="margin-bottom: 4px">{{ title }}</h1>
				<p class="ap-hint">发起审批、处理待办与查看抄送</p>
			</div>
			<div class="ap-actions">
				<a-input-search
					v-model="keyword"
					allow-clear
					placeholder="搜索"
					style="width: 220px"
					@search="reload"
					@clear="reload"
					@press-enter="reload"
				/>
				<a-button type="primary" @click="setView('start')">发起审批</a-button>
			</div>
		</header>

		<a-row :gutter="12" class="ap-stats">
			<a-col :span="6" v-for="s in statCards" :key="s.key">
				<a-card :bordered="false" class="ap-stat-card" :class="{ active: view === s.key }" @click="setView(s.key)">
					<a-statistic :title="s.title" :value="stats[s.stat] ?? 0" />
				</a-card>
			</a-col>
		</a-row>

		<a-card v-if="view === 'start'" :bordered="false" class="oc-table-card">
			<a-spin :loading="loading">
				<div class="ap-start-grid">
					<div
						v-for="f in startForms"
						:key="f.name"
						class="ap-start-card"
						@click="openStart(f)"
					>
						<span class="ap-icon" :style="{ background: f.color || '#165DFF' }">
							{{ (f.form_name || "?").slice(0, 1) }}
						</span>
						<div>
							<div class="ap-form-title">{{ f.form_name }}</div>
							<div class="ap-form-desc">{{ f.description || f.process_summary || "—" }}</div>
						</div>
					</div>
				</div>
			</a-spin>
		</a-card>

		<a-card v-else :bordered="false" class="oc-table-card">
			<a-table
				:columns="columns"
				:data="rows"
				:loading="loading"
				:pagination="false"
				row-key="name"
				@row-click="onRowClick"
			>
				<template #status="{ record }">
					<a-tag :color="statusColor(record)">{{ statusText(record) }}</a-tag>
				</template>
			</a-table>
		</a-card>

		<a-drawer
			:visible="detailVisible"
			:width="520"
			unmount-on-close
			:title="detail?.instance?.form_title || '详情'"
			@cancel="detailVisible = false"
		>
			<template v-if="detail">
				<a-descriptions :column="1" size="small" style="margin-bottom: 12px">
					<a-descriptions-item label="状态">{{ detail.instance.status }}</a-descriptions-item>
					<a-descriptions-item label="发起人">{{ detail.instance.applicant_user }}</a-descriptions-item>
					<a-descriptions-item label="当前节点">
						{{ detail.instance.current_node_label || "—" }}
					</a-descriptions-item>
				</a-descriptions>

				<FormRenderer
					v-model="detailForm"
					:schema="detail.instance.form_schema"
					:field-perms="detail.field_perms"
					:readonly="!canAct"
				/>

				<a-divider>流转</a-divider>
				<a-timeline>
					<a-timeline-item v-for="t in detail.timeline" :key="t.name">
						{{ t.node_label }} · {{ t.assignee }} · {{ t.status }}
						<div v-if="t.comment" class="ap-form-desc">{{ t.comment }}</div>
					</a-timeline-item>
				</a-timeline>

				<template v-if="canAct">
					<a-divider>处理</a-divider>
					<a-textarea v-model="comment" placeholder="审批意见" :auto-size="{ minRows: 2 }" />
					<a-space style="margin-top: 12px">
						<a-button type="primary" :loading="acting" @click="act('approve')">同意</a-button>
						<a-button status="danger" :loading="acting" @click="act('reject')">驳回</a-button>
						<a-button :loading="acting" @click="showTransfer = true">转交</a-button>
					</a-space>
				</template>
				<template v-else-if="detail.can_cancel">
					<a-divider />
					<a-button status="warning" :loading="acting" @click="cancelMine">撤销申请</a-button>
				</template>
			</template>
		</a-drawer>

		<a-modal v-model:visible="startVisible" :title="startMeta?.form_name || '发起审批'" :ok-loading="acting" @ok="submitStart">
			<p class="ap-hint" style="margin-bottom: 12px">{{ startMeta?.description || startMeta?.process_summary }}</p>
			<FormRenderer v-if="startMeta" v-model="startData" :schema="startMeta.form_schema" />
		</a-modal>

		<a-modal v-model:visible="showTransfer" title="转交" @ok="doTransfer">
			<a-input v-model="transferUser" placeholder="目标用户邮箱 / 用户名" />
		</a-modal>
	</div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { Message } from "@arco-design/web-vue";
import FormRenderer from "../shared/FormRenderer.vue";

const props = defineProps({
	view: { type: String, default: "todo" },
});

const view = ref(props.view || "todo");
const keyword = ref("");
const loading = ref(false);
const acting = ref(false);
const rows = ref([]);
const startForms = ref([]);
const stats = ref({ todo: 0, done: 0, mine: 0, cc: 0 });
const detailVisible = ref(false);
const detail = ref(null);
const detailForm = ref({});
const comment = ref("");
const startVisible = ref(false);
const startMeta = ref(null);
const startData = ref({});
const showTransfer = ref(false);
const transferUser = ref("");

const titleMap = {
	start: "发起审批",
	todo: "我的待办",
	done: "我的已办",
	mine: "我发起的",
	cc: "抄送我的",
};
const title = computed(() => titleMap[view.value] || "审批工作区");

const statCards = [
	{ key: "todo", title: "待办", stat: "todo" },
	{ key: "done", title: "已办", stat: "done" },
	{ key: "mine", title: "我发起的", stat: "mine" },
	{ key: "cc", title: "抄送我的", stat: "cc" },
];

const columns = computed(() => {
	if (view.value === "mine") {
		return [
			{ title: "标题", dataIndex: "form_title" },
			{ title: "状态", slotName: "status" },
			{ title: "当前节点", dataIndex: "current_node_label" },
			{ title: "更新时间", dataIndex: "modified" },
		];
	}
	return [
		{ title: "标题", dataIndex: "form_title" },
		{ title: "节点", dataIndex: "node_label" },
		{ title: "状态", slotName: "status" },
		{ title: "发起人", dataIndex: "applicant_user" },
		{ title: "时间", dataIndex: "modified" },
	];
});

const canAct = computed(
	() =>
		detail.value?.task?.task_type === "approve" &&
		detail.value?.task?.status === "待处理"
);

async function call(method, args = {}) {
	const r = await window.frappe.call({
		method: `employee_roster.hr_roster.approval_runtime.${method}`,
		args,
	});
	return r.message;
}

function setView(v) {
	if (v === "start") {
		view.value = "start";
	} else {
		view.value = v;
	}
	reload();
}

async function loadStats() {
	try {
		stats.value = await call("workspace_stats");
	} catch (_) {
		/* ignore */
	}
}

async function reload() {
	loading.value = true;
	try {
		await loadStats();
		if (view.value === "start") {
			startForms.value = await call("list_startable_forms", { keyword: keyword.value });
			rows.value = [];
		} else {
			rows.value = await call("list_workspace_items", {
				view: view.value,
				keyword: keyword.value,
			});
		}
	} catch (e) {
		Message.error(e.message || "加载失败");
	} finally {
		loading.value = false;
	}
}

async function openStart(f) {
	try {
		startMeta.value = await call("get_start_form", { name: f.name });
		startData.value = {};
		startVisible.value = true;
	} catch (e) {
		Message.error(e.message || "无法打开表单");
	}
}

async function submitStart() {
	acting.value = true;
	try {
		await call("start_approval", {
			form_name: startMeta.value.name,
			form_data: startData.value,
		});
		Message.success("已提交");
		startVisible.value = false;
		view.value = "mine";
		await reload();
	} catch (e) {
		Message.error(e.message || "提交失败");
		throw e;
	} finally {
		acting.value = false;
	}
}

async function onRowClick(record) {
	try {
		const args =
			record.item_type === "instance"
				? { instance_name: record.name }
				: { task_name: record.name };
		detail.value = await call("get_workspace_detail", args);
		detailForm.value = { ...(detail.value.instance.form_data || {}) };
		comment.value = "";
		detailVisible.value = true;
	} catch (e) {
		Message.error(e.message || "加载详情失败");
	}
}

async function act(action) {
	if (!detail.value?.task) return;
	acting.value = true;
	try {
		await call("complete_approval_task", {
			task_name: detail.value.task.name,
			action,
			comment: comment.value,
			form_data: detailForm.value,
		});
		Message.success(action === "approve" ? "已同意" : "已驳回");
		detailVisible.value = false;
		await reload();
	} catch (e) {
		Message.error(e.message || "操作失败");
	} finally {
		acting.value = false;
	}
}

async function doTransfer() {
	if (!transferUser.value) {
		Message.warning("请填写转交用户");
		return;
	}
	acting.value = true;
	try {
		await call("transfer_approval_task", {
			task_name: detail.value.task.name,
			to_user: transferUser.value,
			comment: comment.value,
		});
		Message.success("已转交");
		showTransfer.value = false;
		detailVisible.value = false;
		await reload();
	} catch (e) {
		Message.error(e.message || "转交失败");
	} finally {
		acting.value = false;
	}
}

async function cancelMine() {
	acting.value = true;
	try {
		await call("cancel_approval", {
			instance_name: detail.value.instance.name,
			comment: comment.value || "撤销",
		});
		Message.success("已撤销");
		detailVisible.value = false;
		await reload();
	} catch (e) {
		Message.error(e.message || "撤销失败");
	} finally {
		acting.value = false;
	}
}

function statusText(record) {
	return record.instance_status || record.status || "—";
}

function statusColor(record) {
	const s = statusText(record);
	if (s.includes("通过") || s.includes("同意")) return "green";
	if (s.includes("驳回")) return "red";
	if (s.includes("待")) return "orangered";
	if (s.includes("撤销") || s.includes("取消")) return "gray";
	return "arcoblue";
}

watch(
	() => props.view,
	(v) => {
		if (v) view.value = v;
	}
);

onMounted(reload);
</script>
