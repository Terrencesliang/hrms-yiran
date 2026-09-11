<template>
	<section class="hr-roster-workspace" aria-label="员工名录">
		<header class="hr-roster-workspace__header">
			<div class="hr-roster-workspace__title">
				<h2>员工名录</h2>
				<span>共 {{ formatNumber(state.total) }} 人</span>
			</div>
			<a-button v-if="state.canCreate" type="primary" @click="handlers?.onCreate?.()">
				<template #icon><icon-plus /></template>
				新增员工
			</a-button>
		</header>

		<div class="hr-roster-workspace__controls">
			<div class="hr-roster-status-tabs" role="tablist" aria-label="员工状态筛选">
				<button
					v-for="item in statusItems"
					:key="item.key"
					type="button"
					class="hr-roster-status-tab"
					:class="[{ 'is-active': item.active }, `is-${item.tone}`]"
					:aria-selected="item.active"
					role="tab"
					@click="selectStatus(item)"
				>
					<span v-if="item.dot" class="hr-roster-status-tab__dot" />
					<span>{{ item.label }}</span>
					<strong>{{ formatNumber(item.value) }}</strong>
				</button>
			</div>

			<div class="hr-roster-query">
				<a-input-search
					v-model="keyword"
					allow-clear
					placeholder="搜索姓名、工号、部门"
					aria-label="搜索员工"
					@input="resetVisibleRows"
				/>
				<a-button class="hr-roster-filter-button" @click="handlers?.onFilterOpen?.()">
					<template #icon><icon-filter /></template>
					筛选
					<span v-if="state.activeFilterCount" class="hr-roster-filter-count">
						{{ state.activeFilterCount }}
					</span>
				</a-button>
			</div>
		</div>

		<a-table
			class="hr-roster-arco-table"
			:columns="columns"
			:data="visibleRows"
			:pagination="false"
			:loading="state.loading"
			:scroll="{ x: 1160 }"
			:bordered="false"
			row-key="name"
			@sorter-change="changeSort"
		>
			<template #employee="{ record }">
				<div class="hr-roster-employee">
					<a-avatar :size="36" :image-url="record.image || undefined" :style="avatarStyle(record)">
						{{ employeeInitial(record) }}
					</a-avatar>
					<div class="hr-roster-copy">
						<strong
							class="hr-roster-employee-name"
							role="link"
							tabindex="0"
							@click.stop="openRow(record)"
							@keydown.enter.prevent="openRow(record)"
						>
							{{ record.employee_name || "未命名员工" }}
						</strong>
						<span>工号 {{ record.employee_number || "—" }}</span>
					</div>
				</div>
			</template>

			<template #position="{ record }">
				<div class="hr-roster-copy">
					<strong>{{ localizePosition(record.designation) }}</strong>
					<span>{{ localizeOrganization(record.department) || "未分配部门" }}</span>
				</div>
			</template>

			<template #group="{ record }">
				<span class="hr-roster-primary-text">{{ localizeOrganization(record.group_name) || "—" }}</span>
			</template>

			<template #branch="{ record }">
				<span class="hr-roster-primary-text">{{ record.branch || "—" }}</span>
			</template>

			<template #employmentType="{ record }">
				<a-tag :color="employmentTypeColor(displayEmploymentType(record))" size="small">
					{{ employmentTypeLabel(displayEmploymentType(record)) }}
				</a-tag>
			</template>

			<template #joiningDate="{ record }">
				<span class="hr-roster-date">{{ formatDate(record.date_of_joining) }}</span>
			</template>

			<template #contact="{ record }">
				<div class="hr-roster-copy hr-roster-contact">
					<strong>{{ maskPhone(record.cell_number) }}</strong>
					<span>{{ record.company_email || "未填写公司邮箱" }}</span>
				</div>
			</template>

			<template #empty>
				<a-empty description="当前筛选条件下暂无员工记录" />
			</template>
		</a-table>

		<div ref="loadSentinel" class="hr-roster-lazy-status" aria-live="polite">
			<template v-if="hasMoreRows">
				<a-spin :size="18" />
				<span>正在加载更多员工...</span>
			</template>
			<span v-else-if="filteredRows.length">已加载全部 {{ formatNumber(filteredRows.length) }} 名员工</span>
		</div>
	</section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
	state: { type: Object, required: true },
	handlers: { type: Object, default: () => ({}) },
});

const PAGE_SIZE = 30;
const keyword = ref("");
const visibleCount = ref(PAGE_SIZE);
const loadSentinel = ref(null);
let observer;

const columns = computed(() => [
	{
		title: "员工信息",
		dataIndex: "employee_number",
		slotName: "employee",
		width: 210,
		// 不再 fixed：避免固定列/排序列灰底与其它列不一致
		sortable: {
			sortDirections: ["ascend", "descend"],
			sorter: true,
			sortOrder: columnSortOrder("employee_number"),
		},
	},
	{ title: "任职信息", dataIndex: "designation", slotName: "position", width: 250 },
	{ title: "组别", dataIndex: "group_name", slotName: "group", width: 130 },
	{ title: "分支机构", dataIndex: "branch", slotName: "branch", width: 120 },
	{ title: "雇佣类型", dataIndex: "employment_type", slotName: "employmentType", width: 112 },
	{
		title: "入职日期",
		dataIndex: "date_of_joining",
		slotName: "joiningDate",
		width: 150,
		sortable: {
			sortDirections: ["ascend", "descend"],
			sorter: true,
			sortOrder: columnSortOrder("date_of_joining"),
		},
	},
	{ title: "联系方式", dataIndex: "cell_number", slotName: "contact", width: 205 },
]);

const statusItems = computed(() => {
	const counts = props.state.employmentCounts || {};
	return [
		{ key: "all", label: "全部", value: props.state.total, tone: "primary" },
		{ key: "active", label: "在职", value: props.state.active, field: "status", valueKey: "Active", tone: "success", dot: true },
		{ key: "fulltime", label: "全职", value: counts["Full-time"] || 0, field: "designation", valueKey: "实习生", operator: "!=", tone: "primary", dot: true },
		{ key: "intern", label: "实习生", value: counts.Intern || 0, field: "designation", valueKey: "实习生", tone: "purple", dot: true },
		{ key: "probation", label: "试用期", value: counts.Probation || 0, field: "employment_type", valueKey: "Probation", tone: "warning", dot: true },
		{ key: "left", label: "已离职", value: props.state.left, field: "status", valueKey: "Left", tone: "danger", dot: true },
	].map((item) => ({ ...item, active: isStatusActive(item) }));
});

const sortedRows = computed(() => {
	const field = props.state.sortBy || "employee_number";
	const desc = props.state.sortOrder === "desc";
	return [...(props.state.rows || [])].sort((left, right) => {
		if (field === "employee_number") {
			const emptyA = !String(left?.employee_number ?? "").trim();
			const emptyB = !String(right?.employee_number ?? "").trim();
			if (emptyA !== emptyB) return emptyA ? 1 : -1; // 空工号始终沉底
			const result = compareEmployeeNumber(left, right);
			return desc ? -result : result;
		}
		const emptyA = !String(left?.date_of_joining || "").trim();
		const emptyB = !String(right?.date_of_joining || "").trim();
		if (emptyA !== emptyB) return emptyA ? 1 : -1;
		const result = compareJoiningDate(left, right);
		if (result !== 0) return desc ? -result : result;
		const tie = compareEmployeeNumber(left, right);
		return desc ? -tie : tie;
	});
});

const filteredRows = computed(() => {
	const query = keyword.value.trim().toLocaleLowerCase("zh-CN");
	if (!query) return sortedRows.value;
	return sortedRows.value.filter((record) =>
		[record.employee_name, record.name, record.employee_number, record.department, record.designation, record.group_name]
			.filter(Boolean)
			.some((value) => String(value).toLocaleLowerCase("zh-CN").includes(query)),
	);
});

const visibleRows = computed(() => filteredRows.value.slice(0, visibleCount.value));
const hasMoreRows = computed(() => visibleRows.value.length < filteredRows.value.length);

/** 工号按数值比较（调用方已处理空值沉底） */
function compareEmployeeNumber(left, right) {
	const rawA = String(left?.employee_number ?? "").trim();
	const rawB = String(right?.employee_number ?? "").trim();
	if (!rawA && !rawB) return 0;
	if (!rawA) return 1;
	if (!rawB) return -1;

	const a = Number.parseInt(rawA.replace(/[^\d-]/g, ""), 10);
	const b = Number.parseInt(rawB.replace(/[^\d-]/g, ""), 10);
	if (Number.isFinite(a) && Number.isFinite(b) && a !== b) return a - b;
	return rawA.localeCompare(rawB, "zh-CN", { numeric: true, sensitivity: "base" });
}

function compareJoiningDate(left, right) {
	const a = String(left?.date_of_joining || "").slice(0, 10);
	const b = String(right?.date_of_joining || "").slice(0, 10);
	if (!a && !b) return 0;
	if (!a) return 1;
	if (!b) return -1;
	return a.localeCompare(b);
}

function columnSortOrder(field) {
	if (props.state.sortBy !== field) return "";
	return props.state.sortOrder === "desc" ? "descend" : "ascend";
}

function isStatusActive(item) {
	const filters = props.state.filters || [];
	if (item.key === "all") return !filters.some((filter) => ["status", "designation", "employment_type"].includes(filter.field));
	return filters.some((filter) => filter.field === item.field && filter.value === item.valueKey && (filter.operator || "=") === (item.operator || "="));
}

function selectStatus(item) {
	if (item.key === "all") props.handlers?.onClearStatus?.();
	else props.handlers?.onStatusFilter?.(item);
}

function resetVisibleRows() {
	visibleCount.value = PAGE_SIZE;
}

function loadMoreRows() {
	if (hasMoreRows.value) visibleCount.value = Math.min(visibleCount.value + PAGE_SIZE, filteredRows.value.length);
}

function employeeInitial(record) {
	return String(record.employee_name || record.name || "员").slice(-1);
}

function avatarStyle(record) {
	if (record.image) return undefined;
	const palettes = [["#E8F3FF", "#165DFF"], ["#E8FFEA", "#00B42A"], ["#F5E8FF", "#722ED1"], ["#FFF7E8", "#FF7D00"]];
	const code = String(record.name || record.employee_name || "");
	const index = [...code].reduce((sum, char) => sum + char.charCodeAt(0), 0) % palettes.length;
	return { backgroundColor: palettes[index][0], color: palettes[index][1] };
}

function localizePosition(value) {
	if (!value) return "未设置职位";
	return String(value).replace(/HRBP/gi, "人力资源业务伙伴").replace(/ITBP/gi, "信息技术业务伙伴").replace(/FBP/gi, "财务业务伙伴").replace(/BP/gi, "业务伙伴").replace(/\bVP\b/gi, "副总裁").replace(/AI/gi, "人工智能");
}

function localizeOrganization(value) {
	if (!value) return "";
	return String(value).replace(/ITBP/gi, "信息技术业务伙伴").replace(/FBP/gi, "财务业务伙伴").replace(/HRBP/gi, "人力资源业务伙伴").replace(/KA/gi, "重点客户").replace(/AI/gi, "人工智能");
}

function employmentTypeLabel(value) {
	return { "Full-time": "全职", "Part-time": "兼职", Intern: "实习生", Probation: "试用期", Contract: "合同工", Apprentice: "见习生" }[value] || value || "未设置";
}

function displayEmploymentType(record) {
	if (record.employment_type) return record.employment_type;
	if (record.designation === "实习生") return "Intern";
	if (record.status === "Active") return "Full-time";
	return "";
}

function employmentTypeColor(value) {
	return { "Full-time": "arcoblue", "Part-time": "purple", Intern: "purple", Probation: "orange", Contract: "cyan", Apprentice: "green" }[value] || "gray";
}

function formatDate(value) {
	const [year, month, day] = String(value || "").slice(0, 10).split("-");
	return year && month && day ? `${year}年${month}月${day}日` : "—";
}

function formatNumber(value) {
	return Number(value || 0).toLocaleString("zh-CN");
}

function maskPhone(value) {
	const phone = String(value || "").trim();
	if (!phone) return "未填写手机号";
	if (phone.length < 7) return phone;
	return `${phone.slice(0, 3)}****${phone.slice(-4)}`;
}

function openRow(record) {
	props.handlers?.onOpen?.(record);
}

function changeSort(dataIndex, direction) {
	if (!["employee_number", "date_of_joining"].includes(dataIndex)) return;
	// 再次点击同一方向时 Arco 可能传空字符串，视为切换正倒序
	let next = direction === "ascend" ? "asc" : direction === "descend" ? "desc" : "";
	if (!next) {
		const sameField = props.state.sortBy === dataIndex;
		next = sameField && props.state.sortOrder === "asc" ? "desc" : "asc";
	}
	props.handlers?.onSort?.(dataIndex, next);
}

watch(() => props.state.rows, resetVisibleRows);

onMounted(async () => {
	await nextTick();
	observer = new IntersectionObserver((entries) => {
		if (entries.some((entry) => entry.isIntersecting)) loadMoreRows();
	}, { rootMargin: "160px 0px" });
	if (loadSentinel.value) observer.observe(loadSentinel.value);
});

onBeforeUnmount(() => observer?.disconnect());
</script>

<style scoped>
.hr-roster-workspace { width: 100%; min-height: calc(100vh - 172px); background: var(--color-bg-2, #fff); border: 1px solid var(--color-border-2, #e5e6eb); border-radius: 10px; overflow: hidden; }
.hr-roster-workspace__header, .hr-roster-workspace__controls { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 16px 20px; border-bottom: 1px solid var(--color-border-2, #e5e6eb); }
.hr-roster-workspace__title { display: flex; align-items: baseline; gap: 12px; }
.hr-roster-workspace__title h2 { margin: 0; color: var(--color-text-1); font-size: 20px; font-weight: 600; line-height: 1.4; }
.hr-roster-workspace__title span { color: var(--color-text-3); font-size: 13px; }
.hr-roster-workspace__controls { padding-top: 10px; padding-bottom: 10px; }
.hr-roster-status-tabs { display: flex; align-items: center; min-width: 0; overflow-x: auto; scrollbar-width: none; }
.hr-roster-status-tabs::-webkit-scrollbar { display: none; }
.hr-roster-status-tab { position: relative; display: inline-flex; align-items: center; gap: 7px; height: 42px; padding: 0 14px; border: 0; background: transparent; color: var(--color-text-2); font-size: 13px; white-space: nowrap; cursor: pointer; }
.hr-roster-status-tab::after { position: absolute; right: 12px; bottom: -11px; left: 12px; height: 2px; border-radius: 2px; background: transparent; content: ""; }
.hr-roster-status-tab:hover, .hr-roster-status-tab.is-active { color: rgb(var(--arcoblue-6, 22, 93, 255)); }
.hr-roster-status-tab.is-active::after { background: rgb(var(--arcoblue-6, 22, 93, 255)); }
.hr-roster-status-tab strong { font-size: 14px; font-variant-numeric: tabular-nums; }
.hr-roster-status-tab__dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.hr-roster-status-tab.is-success .hr-roster-status-tab__dot { color: rgb(var(--green-6)); }
.hr-roster-status-tab.is-purple .hr-roster-status-tab__dot { color: rgb(var(--purple-6)); }
.hr-roster-status-tab.is-warning .hr-roster-status-tab__dot { color: rgb(var(--orange-6)); }
.hr-roster-status-tab.is-danger .hr-roster-status-tab__dot { color: rgb(var(--red-6)); }
.hr-roster-query { display: flex; align-items: center; gap: 10px; flex: 0 0 auto; }
.hr-roster-query :deep(.arco-input-search) { width: clamp(300px, 27vw, 400px); }
.hr-roster-filter-button { flex: 0 0 auto; }
.hr-roster-filter-count { display: inline-flex; align-items: center; justify-content: center; min-width: 18px; height: 18px; margin-left: 4px; padding: 0 5px; border-radius: 9px; background: rgb(var(--arcoblue-6, 22, 93, 255)); color: #fff; font-size: 11px; }
.hr-roster-arco-table { width: 100%; }
.hr-roster-arco-table :deep(.arco-table-th) {
	height: 44px;
	background: var(--color-fill-1) !important;
	color: var(--color-text-2);
	font-size: 13px;
	font-weight: 500;
}
.hr-roster-arco-table :deep(.arco-table-td),
.hr-roster-arco-table :deep(.arco-table-td.arco-table-col-sorted) {
	height: 66px;
	background: #fff;
	border-bottom-color: var(--color-border-1);
	font-size: 13px;
}
.hr-roster-arco-table :deep(.arco-table-th.arco-table-col-sorted) {
	background: var(--color-fill-1) !important;
}
/* .arco-table-hover 在表格根节点上，不能写成后代选择器 */
.hr-roster-arco-table :deep(tbody .arco-table-tr:not(.arco-table-tr-empty):not(.arco-table-tr-summary):hover > .arco-table-td),
.hr-roster-arco-table :deep(tbody .arco-table-tr:not(.arco-table-tr-empty):not(.arco-table-tr-summary):hover > .arco-table-td.arco-table-col-sorted) {
	background-color: #e8f3ff !important;
}
.hr-roster-employee, .hr-roster-copy { display: flex; }
.hr-roster-employee { align-items: center; gap: 12px; }
.hr-roster-copy { min-width: 0; flex-direction: column; gap: 4px; }
.hr-roster-copy strong, .hr-roster-primary-text, .hr-roster-date { color: var(--color-text-1); font-size: 13px; font-weight: 500; }
.hr-roster-employee-name {
	width: fit-content;
	color: var(--color-text-1);
	font-size: 13px;
	font-weight: 500;
	cursor: pointer;
	text-decoration: none !important;
}

.hr-roster-employee-name:hover {
	color: #165dff;
	text-decoration: none !important;
}
.hr-roster-copy span { max-width: 235px; overflow: hidden; color: var(--color-text-3); font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.hr-roster-contact strong { font-weight: 400; }
.hr-roster-date { font-variant-numeric: tabular-nums; white-space: nowrap; }
.hr-roster-lazy-status { display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 46px; color: var(--color-text-3); font-size: 12px; }
:global(.hr-roster-danger-option) { color: rgb(var(--red-6)); }
@media (max-width: 1180px) {
	.hr-roster-workspace__controls { align-items: stretch; flex-direction: column; gap: 8px; }
	.hr-roster-status-tab::after { bottom: -1px; }
	.hr-roster-query :deep(.arco-input-search) { width: min(100%, 520px); }
}
@media (max-width: 640px) {
	.hr-roster-workspace__header { align-items: flex-start; padding: 14px 12px; }
	.hr-roster-workspace__controls { padding: 8px 12px; }
	.hr-roster-query { width: 100%; }
	.hr-roster-query :deep(.arco-input-search) { flex: 1; width: auto; }
}
</style>
