<template>
	<section class="ec-applications">
		<div class="ec-applications-tabs">
			<a-tabs v-model:active-key="activeStatus" hide-content @change="reload">
				<a-tab-pane v-for="tab in tabs" :key="tab.key" :title="`${tab.label} ${tab.count}`" />
			</a-tabs>
			<a-input-search
				v-model="keyword"
				allow-clear
				placeholder="搜索申请标题或单号"
				class="ec-application-search"
				@search="reload"
				@clear="reload"
				@press-enter="reload"
			/>
			<a-popover trigger="click" position="br">
				<a-button><template #icon><icon-filter /></template>筛选<span v-if="filterCount">（{{ filterCount }}）</span></a-button>
				<template #content>
					<div class="ec-filter-popover">
						<label>申请类型</label>
						<a-select v-model="applicationType" allow-clear placeholder="全部类型">
							<a-option v-for="item in applicationTypes" :key="item.value" :value="item.value">{{ item.label }}</a-option>
						</a-select>
						<label>提交时间</label>
						<a-range-picker v-model="dateRange" value-format="YYYY-MM-DD" />
						<a-space><a-button @click="resetFilters">重置</a-button><a-button type="primary" @click="reload">应用筛选</a-button></a-space>
					</div>
				</template>
			</a-popover>
		</div>

		<a-spin :loading="loading && !rows.length" style="width: 100%">
			<a-empty v-if="!loading && !rows.length" description="暂无申请记录">
				<template #extra>
					<a-button type="primary" @click="$emit('go-home')">发起申请</a-button>
				</template>
			</a-empty>
			<div v-else class="ec-application-list">
				<button
					v-for="row in rows"
					:key="row.name"
					type="button"
					class="ec-application-row"
					@click="openDetail(row)"
				>
					<span class="ec-application-mark"><icon-file /></span>
					<span class="ec-application-copy">
						<strong>{{ row.form_title || "未命名申请" }}</strong>
						<small>{{ row.application_no }}</small>
					</span>
					<span class="ec-application-time">
					<small>{{ row.status === '草稿' ? '保存时间' : '提交时间' }}</small>
						{{ formatDateTime(row.submitted_at) }}
					</span>
					<span class="ec-application-node">
						<small>当前节点</small>
						{{ row.current_node_label || "—" }}
					</span>
					<ApplicationStatusTag :status="row.status" />
					<icon-right class="ec-row-arrow" />
				</button>
				<div ref="loadSentinel" class="ec-load-sentinel">
					<a-spin v-if="loading" />
					<a-button v-else-if="hasMore" type="text" @click="loadMore">加载更多</a-button>
					<span v-else-if="rows.length" class="ec-list-end">已加载全部申请</span>
				</div>
			</div>
		</a-spin>

		<a-drawer
			:visible="detailVisible"
			:width="720"
			:title="detail?.instance?.form_title || '申请详情'"
			unmount-on-close
			@cancel="detailVisible = false"
		>
			<a-spin :loading="detailLoading" style="width: 100%">
				<template v-if="detail?.instance">
					<div class="ec-detail-heading">
						<div>
							<span>申请单号</span>
							<strong>{{ detail.instance.application_no || detail.instance.name }}</strong>
						</div>
						<ApplicationStatusTag :status="detail.instance.status" />
					</div>
					<a-descriptions :column="2" bordered size="large">
						<a-descriptions-item :label="detail.instance.status === '草稿' ? '保存时间' : '提交时间'">{{ formatDateTime(detail.instance.submitted_at || detail.instance.creation) }}</a-descriptions-item>
						<a-descriptions-item label="当前节点">{{ detail.instance.current_node_label || "—" }}</a-descriptions-item>
					</a-descriptions>

					<h3 class="ec-detail-title">申请内容</h3>
					<a-descriptions :column="1" bordered>
						<a-descriptions-item v-for="item in detailFields" :key="item.key" :label="item.label">
							{{ formatValue(item.value) }}
						</a-descriptions-item>
					</a-descriptions>

					<h3 class="ec-detail-title">审批进度</h3>
					<a-timeline>
						<a-timeline-item v-for="task in detail.timeline || []" :key="task.name" :label="formatDateTime(task.acted_on || task.creation)">
							<strong>{{ task.node_label || "审批节点" }}</strong>
							<ApplicationStatusTag :status="task.status" />
							<p>{{ task.comment || task.assignee || "—" }}</p>
						</a-timeline-item>
					</a-timeline>
				</template>
			</a-spin>
			<template #footer>
				<a-space>
					<a-button @click="detailVisible = false">关闭</a-button>
					<a-button v-if="detail?.instance?.status === '草稿' || detail?.instance?.status === '已驳回' || detail?.instance?.status === '已撤销'" type="primary" @click="editCurrent">{{ detail?.instance?.status === '草稿' ? '继续填写' : '修改并重新提交' }}</a-button>
					<a-popconfirm
						v-if="detail?.can_cancel"
						content="确定撤回这条申请吗？"
						@ok="withdraw"
					>
						<a-button status="warning" :loading="withdrawing">撤回申请</a-button>
					</a-popconfirm>
				</a-space>
			</template>
		</a-drawer>
	</section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { Message } from "@arco-design/web-vue";
import { IconFile, IconFilter, IconRight } from "@arco-design/web-vue/es/icon";
import {
	cancelApplication,
	getApplicationDetail,
	listMyApplications,
	type ApplicationRow,
} from "../../api/employeeCenter";
import ApplicationStatusTag from "./components/ApplicationStatusTag.vue";

const props = defineProps<{ initialStatus?: string; stats: Record<string, number> }>();
const emit = defineEmits<{ "go-home": []; changed: []; edit: [type: string, name: string] }>();

const activeStatus = ref(props.initialStatus || "all");
const keyword = ref("");
const applicationType = ref("");
const dateRange = ref<string[]>([]);
const rows = ref<ApplicationRow[]>([]);
const loading = ref(false);
const hasMore = ref(false);
const nextStart = ref(0);
const loadSentinel = ref<HTMLElement | null>(null);
const detailVisible = ref(false);
const detailLoading = ref(false);
const withdrawing = ref(false);
const detail = ref<any>(null);
let observer: IntersectionObserver | null = null;

const tabs = computed(() => [
	{ key: "all", label: "全部", count: props.stats.all || 0 },
	{ key: "draft", label: "草稿", count: props.stats.draft || 0 },
	{ key: "pending", label: "审批中", count: props.stats.pending || 0 },
	{ key: "approved", label: "已通过", count: props.stats.approved || 0 },
	{ key: "rejected", label: "已驳回", count: props.stats.rejected || 0 },
	{ key: "withdrawn", label: "已撤回", count: props.stats.withdrawn || 0 },
]);
const applicationTypes = [
	{ value: "onboarding", label: "入职资料填写" }, { value: "subsidy", label: "申请补贴" },
	{ value: "job-change", label: "调岗调薪" }, { value: "resignation", label: "离职申请表" }, { value: "handover", label: "离职交接表" },
];
const filterCount = computed(() => Number(Boolean(applicationType.value)) + Number(dateRange.value.length === 2));

const detailFields = computed(() => {
	const schemaFields = detail.value?.instance?.form_schema?.fields || [];
	const data = detail.value?.instance?.form_data || {};
	if (schemaFields.length) {
		return schemaFields
			.filter((field: any) => field?.key || field?.fieldname)
			.map((field: any) => {
				const key = field.key || field.fieldname;
				return { key, label: field.label || key, value: data[key] };
			});
	}
	return Object.entries(data).map(([key, value]) => ({ key, label: key, value }));
});

function formatDateTime(value?: string) {
	if (!value) return "—";
	return String(value).replace("T", " ").slice(0, 16);
}

function formatValue(value: unknown) {
	if (value === null || value === undefined || value === "") return "—";
	if (Array.isArray(value)) return value.join("、") || "—";
	if (typeof value === "object") return JSON.stringify(value);
	return String(value);
}

async function reload() {
	rows.value = [];
	nextStart.value = 0;
	hasMore.value = false;
	await loadMore();
}

async function loadMore() {
	if (loading.value || (rows.value.length && !hasMore.value)) return;
	loading.value = true;
	try {
		const result = await listMyApplications({
			status: activeStatus.value === "all" ? undefined : activeStatus.value,
			keyword: keyword.value,
			application_type: applicationType.value || undefined,
			date_from: dateRange.value[0] || undefined,
			date_to: dateRange.value[1] || undefined,
			limit_start: nextStart.value,
			page_length: 20,
		});
		rows.value.push(...(result.rows || []));
		hasMore.value = Boolean(result.has_more);
		nextStart.value = result.next_start || rows.value.length;
	} catch (error: any) {
		Message.error(error?.message || "申请记录加载失败");
	} finally {
		loading.value = false;
	}
}

function resetFilters() { applicationType.value = ""; dateRange.value = []; void reload(); }

async function openDetail(row: ApplicationRow) {
	detailVisible.value = true;
	detailLoading.value = true;
	detail.value = null;
	try {
		detail.value = await getApplicationDetail(row.name);
	} catch (error: any) {
		Message.error(error?.message || "申请详情加载失败");
		detailVisible.value = false;
	} finally {
		detailLoading.value = false;
	}
}

async function withdraw() {
	if (!detail.value?.instance?.name) return;
	withdrawing.value = true;
	try {
		await cancelApplication(detail.value.instance.name);
		Message.success("申请已撤回");
		detailVisible.value = false;
		emit("changed");
		await reload();
	} catch (error: any) {
		Message.error(error?.message || "撤回失败");
	} finally {
		withdrawing.value = false;
	}
}

function editCurrent() {
	const type = detail.value?.instance?.application_type;
	if (!type) { Message.error("该历史申请缺少业务类型，无法编辑"); return; }
	detailVisible.value = false;
	emit("edit", type, detail.value.instance.name);
}

function setupObserver() {
	observer?.disconnect();
	if (!loadSentinel.value || typeof IntersectionObserver === "undefined") return;
	observer = new IntersectionObserver((entries) => {
		if (entries[0]?.isIntersecting && hasMore.value) loadMore();
	}, { rootMargin: "160px" });
	observer.observe(loadSentinel.value);
}

watch(() => props.initialStatus, (value) => {
	activeStatus.value = value || "all";
	reload();
});
watch(loadSentinel, () => nextTick(setupObserver));
onMounted(async () => { await reload(); await nextTick(); setupObserver(); });
onBeforeUnmount(() => observer?.disconnect());
</script>
