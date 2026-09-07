<template>
	<div class="arco-org-ui ap-root ap-workspace">
		<!-- 页头 -->
		<div class="apw-header">
			<div class="apw-header-text">
				<h1 class="oc-page-title">审批中心</h1>
				<p class="ap-hint">发起申请、处理待办，并跟踪我发起与抄送的单据</p>
			</div>
			<a-space>
				<a-button type="primary" @click="setView('start')">
					<template #icon><icon-plus /></template>
					发起审批
				</a-button>
			</a-space>
		</div>

		<!-- 顶部分段导航（PC 主入口，不依赖窄侧栏） -->
		<a-card :bordered="false" class="apw-nav-card">
			<a-radio-group v-model="view" type="button" size="large" @change="onViewChange">
				<a-radio value="start">发起审批</a-radio>
				<a-radio value="todo">我的待办{{ stats.todo ? ` (${stats.todo})` : "" }}</a-radio>
				<a-radio value="done">我的已办</a-radio>
				<a-radio value="mine">我发起的</a-radio>
				<a-radio value="cc">抄送我的</a-radio>
			</a-radio-group>
		</a-card>

		<!-- 统计 -->
		<a-row v-if="view !== 'start'" :gutter="16" class="apw-stats">
			<a-col :xs="12" :sm="6" v-for="s in statCards" :key="s.key">
				<a-card
					:bordered="false"
					class="apw-stat"
					:class="{ 'apw-stat--active': view === s.key }"
					@click="setView(s.key)"
				>
					<a-statistic :title="s.title" :value="stats[s.stat] ?? 0">
						<template #prefix>
							<span class="apw-stat-dot" :style="{ background: s.color }" />
						</template>
					</a-statistic>
				</a-card>
			</a-col>
		</a-row>

		<!-- 筛选 -->
		<a-card :bordered="false" class="apw-filter-card">
			<a-form :model="filters" layout="inline" class="apw-filter-form">
				<a-form-item label="关键词">
					<a-input-search
						v-model="keyword"
						allow-clear
						:placeholder="view === 'start' ? '搜索可发起的审批表单' : '搜索标题 / 发起人 / 节点'"
						style="width: 280px"
						@search="reload"
						@clear="reload"
						@press-enter="reload"
					/>
				</a-form-item>
				<a-form-item v-if="view === 'mine'" label="状态">
					<a-select
						v-model="filters.status"
						allow-clear
						placeholder="全部状态"
						style="width: 140px"
						@change="reload"
					>
						<a-option value="进行中">进行中</a-option>
						<a-option value="已通过">已通过</a-option>
						<a-option value="已驳回">已驳回</a-option>
						<a-option value="已撤销">已撤销</a-option>
					</a-select>
				</a-form-item>
				<a-form-item>
					<a-space>
						<a-button type="primary" @click="reload">查询</a-button>
						<a-button @click="resetFilters">重置</a-button>
					</a-space>
				</a-form-item>
			</a-form>
		</a-card>

		<!-- 发起：表单目录 -->
		<a-card v-if="view === 'start'" :bordered="false" class="oc-table-card apw-content-card">
			<template #title>
				<span>可发起的审批</span>
				<span class="apw-card-sub">共 {{ startForms.length }} 个表单</span>
			</template>
			<a-spin :loading="loading" style="width: 100%">
				<a-empty v-if="!loading && !startForms.length" description="暂无可发起的审批表单" />
				<div v-else class="apw-start-grid">
					<div
						v-for="f in startForms"
						:key="f.name"
						class="apw-start-item"
						@click="openStart(f)"
					>
						<span class="ap-icon apw-start-icon" :style="{ background: f.color || '#00b386' }">
							{{ (f.form_name || "?").slice(0, 1) }}
						</span>
						<div class="apw-start-body">
							<div class="ap-form-title">{{ f.form_name }}</div>
							<div class="ap-form-desc">{{ f.description || "暂无说明" }}</div>
							<div class="apw-start-meta">
								<a-tag size="small" color="arcoblue">{{ f.group || "未分组" }}</a-tag>
								<span>{{ f.process_summary || "流程未配置" }}</span>
							</div>
						</div>
						<a-button type="outline" size="small" class="apw-start-btn">发起</a-button>
					</div>
				</div>
			</a-spin>
		</a-card>

		<!-- 列表 -->
		<a-card v-else :bordered="false" class="oc-table-card apw-content-card">
			<template #title>
				<span>{{ title }}</span>
				<span class="apw-card-sub">共 {{ filteredRows.length }} 条</span>
			</template>
			<a-table
				:columns="columns"
				:data="filteredRows"
				:loading="loading"
				:pagination="pagination"
				row-key="name"
				:bordered="false"
				stripe
			>
				<template #titleCol="{ record }">
					<div class="apw-title-cell" @click="onRowClick(record)">
						<div class="ap-form-title">{{ record.form_title || "—" }}</div>
						<div class="ap-form-desc">
							{{ record.node_label || record.current_node_label || "—" }}
							· {{ record.name }}
						</div>
					</div>
				</template>
				<template #status="{ record }">
					<a-tag :color="statusColor(record)">{{ statusText(record) }}</a-tag>
				</template>
				<template #ops="{ record }">
					<a-space>
						<a-link @click="onRowClick(record)">查看</a-link>
						<a-link
							v-if="view === 'todo'"
							@click="onRowClick(record)"
						>
							处理
						</a-link>
					</a-space>
				</template>
			</a-table>
		</a-card>

		<!-- 详情：宽抽屉，PC 双栏 -->
		<a-drawer
			:visible="detailVisible"
			:width="760"
			unmount-on-close
			:title="detail?.instance?.form_title || '审批详情'"
			@cancel="detailVisible = false"
		>
			<template v-if="detail">
				<div class="apw-detail">
					<a-alert
						v-if="canAct"
						type="warning"
						banner
						style="margin-bottom: 16px"
					>
						当前待你处理：{{ detail.task?.node_label || "审批节点" }}
					</a-alert>

					<a-descriptions :column="2" size="large" bordered class="apw-desc">
						<a-descriptions-item label="单据状态">
							<a-tag :color="statusColor({ status: detail.instance.status })">
								{{ detail.instance.status }}
							</a-tag>
						</a-descriptions-item>
						<a-descriptions-item label="当前节点">
							{{ detail.instance.current_node_label || "—" }}
						</a-descriptions-item>
						<a-descriptions-item label="发起人">
							{{ detail.instance.applicant_user }}
						</a-descriptions-item>
						<a-descriptions-item label="发起时间">
							{{ detail.instance.creation || "—" }}
						</a-descriptions-item>
					</a-descriptions>

					<a-row :gutter="20" style="margin-top: 20px">
						<a-col :span="14">
							<div class="apw-section-title">表单内容</div>
							<a-card :bordered="true" class="apw-form-card">
								<FormRenderer
									v-model="detailForm"
									:schema="detail.instance.form_schema"
									:field-perms="detail.field_perms"
									:readonly="!canAct"
								/>
							</a-card>
						</a-col>
						<a-col :span="10">
							<div class="apw-section-title">审批流转</div>
							<a-card :bordered="true" class="apw-form-card">
								<a-timeline>
									<a-timeline-item
										v-for="t in detail.timeline"
										:key="t.name"
										:label="t.acted_on || t.creation"
									>
										<div class="apw-tl-title">
											{{ t.node_label }}
											<a-tag size="small" style="margin-left: 6px">{{ t.status }}</a-tag>
										</div>
										<div class="ap-form-desc">{{ t.assignee }}</div>
										<div v-if="t.comment" class="apw-tl-comment">{{ t.comment }}</div>
									</a-timeline-item>
								</a-timeline>
							</a-card>
						</a-col>
					</a-row>

					<template v-if="canAct">
						<div class="apw-section-title" style="margin-top: 20px">审批处理</div>
						<a-card :bordered="true" class="apw-form-card">
							<a-textarea
								v-model="comment"
								placeholder="请输入审批意见（可选）"
								:auto-size="{ minRows: 3 }"
							/>
							<a-space style="margin-top: 14px">
								<a-button type="primary" :loading="acting" @click="act('approve')">
									同意
								</a-button>
								<a-button status="danger" :loading="acting" @click="act('reject')">
									驳回
								</a-button>
								<a-button :loading="acting" @click="showTransfer = true">转交</a-button>
							</a-space>
						</a-card>
					</template>
					<template v-else-if="detail.can_cancel">
						<div style="margin-top: 20px">
							<a-button status="warning" :loading="acting" @click="cancelMine">
								撤销申请
							</a-button>
						</div>
					</template>
				</div>
			</template>
		</a-drawer>

		<!-- 发起弹窗：更宽 -->
		<a-modal
			v-model:visible="startVisible"
			:title="startMeta?.form_name || '发起审批'"
			:ok-loading="acting"
			:width="640"
			ok-text="提交申请"
			unmount-on-close
			@ok="submitStart"
		>
			<a-alert
				v-if="startMeta?.process_summary"
				type="info"
				:content="`审批流程：${startMeta.process_summary}`"
				style="margin-bottom: 16px"
			/>
			<p v-if="startMeta?.description" class="ap-hint" style="margin-bottom: 12px">
				{{ startMeta.description }}
			</p>
			<FormRenderer v-if="startMeta" v-model="startData" :schema="startMeta.form_schema" />
		</a-modal>

		<a-modal v-model:visible="showTransfer" title="转交待办" :width="420" @ok="doTransfer">
			<a-form layout="vertical">
				<a-form-item label="转交给" required>
					<a-input v-model="transferUser" placeholder="目标用户邮箱 / 用户名" />
				</a-form-item>
				<a-form-item label="备注">
					<a-textarea v-model="comment" :auto-size="{ minRows: 2 }" />
				</a-form-item>
			</a-form>
		</a-modal>
	</div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
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
const filters = reactive({ status: undefined });

const titleMap = {
	start: "发起审批",
	todo: "我的待办",
	done: "我的已办",
	mine: "我发起的",
	cc: "抄送我的",
};
const title = computed(() => titleMap[view.value] || "审批工作区");

const statCards = [
	{ key: "todo", title: "待办", stat: "todo", color: "#F77234" },
	{ key: "done", title: "已办", stat: "done", color: "#00B42A" },
	{ key: "mine", title: "我发起的", stat: "mine", color: "#165DFF" },
	{ key: "cc", title: "抄送我的", stat: "cc", color: "#0FC6C2" },
];

const pagination = { pageSize: 10, showTotal: true, showPageSize: true };

const columns = computed(() => {
	const base = [
		{ title: "审批标题", slotName: "titleCol", width: 320 },
		{ title: "状态", slotName: "status", width: 110 },
	];
	if (view.value === "mine") {
		return [
			...base,
			{ title: "当前节点", dataIndex: "current_node_label", width: 140 },
			{ title: "更新时间", dataIndex: "modified", width: 180 },
			{ title: "操作", slotName: "ops", width: 120 },
		];
	}
	return [
		...base,
		{ title: "节点", dataIndex: "node_label", width: 140 },
		{ title: "发起人", dataIndex: "applicant_user", width: 160 },
		{ title: "时间", dataIndex: "modified", width: 180 },
		{ title: "操作", slotName: "ops", width: 120 },
	];
});

const filteredRows = computed(() => {
	if (view.value !== "mine" || !filters.status) return rows.value;
	return rows.value.filter((r) => (r.status || r.instance_status) === filters.status);
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
	view.value = v;
	reload();
	syncRoute(v);
}

function onViewChange(v) {
	reload();
	syncRoute(v);
}

function syncRoute(v) {
	if (window.frappe?.set_route) {
		try {
			window.frappe.set_route("approval-workspace", v);
		} catch (_) {
			/* ignore */
		}
	}
}

function resetFilters() {
	keyword.value = "";
	filters.status = undefined;
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
		const tasks = [loadStats()];
		if (view.value === "start") {
			tasks.push(
				call("list_startable_forms", { keyword: keyword.value }).then((r) => {
					startForms.value = r || [];
					rows.value = [];
				})
			);
		} else {
			tasks.push(
				call("list_workspace_items", {
					view: view.value,
					keyword: keyword.value,
				}).then((r) => {
					rows.value = r || [];
				})
			);
		}
		await Promise.all(tasks);
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
	if (s.includes("待") || s.includes("进行")) return "orangered";
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
