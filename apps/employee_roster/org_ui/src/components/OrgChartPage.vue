<template>
	<a-config-provider :locale="zhCN">
		<div class="arco-org-ui">
			<h1 class="oc-page-title">组织架构</h1>

			<div class="oc-stat-grid">
				<a-card class="oc-stat-card" :bordered="false">
					<a-statistic title="组织单元" :value="summary.units" :value-from="0" show-group-separator>
						<template #extra><span class="oc-muted">当前公司组织总数</span></template>
					</a-statistic>
				</a-card>
				<a-card class="oc-stat-card" :bordered="false">
					<a-statistic title="员工总数" :value="summary.employees" :value-from="0" show-group-separator>
						<template #extra><span class="oc-muted">在组织架构中的员工</span></template>
					</a-statistic>
				</a-card>
				<a-card class="oc-stat-card" :bordered="false">
					<a-statistic title="已设编制" :value="summary.quotaSet" :value-from="0">
						<template #suffix>/ {{ summary.units }}</template>
						<template #extra><span class="oc-muted">已维护编制的组织</span></template>
					</a-statistic>
				</a-card>
				<a-card class="oc-stat-card is-alert" :bordered="false">
					<a-statistic title="待补岗位" :value="summary.vacancies" :value-from="0">
						<template #extra><span class="oc-muted">根据已设置编制统计</span></template>
					</a-statistic>
				</a-card>
			</div>

			<a-card class="oc-toolbar-card" :bordered="false">
				<div class="oc-toolbar-row">
					<a-space wrap>
						<a-select
							v-model="company"
							:options="companyOptions"
							placeholder="切换公司"
							style="width: 220px"
							@change="onCompanyChange"
						/>
						<a-input-search
							v-model="keyword"
							placeholder="组织名称/员工姓名/工号"
							allow-clear
							style="width: 240px"
						/>
						<a-popover v-model:popup-visible="filterVisible" trigger="click" position="bl">
							<a-badge :count="filterCount" :dot="filterCount > 0">
								<a-button>
									<template #icon><icon-filter /></template>
									筛选
								</a-button>
							</a-badge>
							<template #content>
								<a-form :model="filters" layout="vertical" class="oc-filter-form">
									<a-form-item label="组织类型">
										<a-select v-model="filters.org_type" allow-clear placeholder="全部">
											<a-option value="公司">公司</a-option>
											<a-option value="部门">部门</a-option>
											<a-option value="组">组</a-option>
											<a-option value="员工">员工</a-option>
										</a-select>
									</a-form-item>
									<a-form-item label="人员编制">
										<a-select v-model="filters.quota" allow-clear placeholder="全部">
											<a-option value="set">已设置</a-option>
											<a-option value="unset">未设置</a-option>
										</a-select>
									</a-form-item>
									<a-form-item label="缺编/超编">
										<a-select v-model="filters.vacancy" allow-clear placeholder="全部">
											<a-option value="short">缺编</a-option>
											<a-option value="over">超编</a-option>
											<a-option value="full">满编</a-option>
										</a-select>
									</a-form-item>
									<a-space>
										<a-button @click="resetFilters">重置</a-button>
										<a-button type="primary" @click="filterVisible = false">确定</a-button>
									</a-space>
								</a-form>
							</template>
						</a-popover>
					</a-space>
					<a-space wrap>
						<a-button type="primary" @click="openDrawer()">
							<template #icon><icon-plus /></template>
							新增组织
						</a-button>
						<a-button @click="batchVisible = true">批量新增/更新</a-button>
						<a-dropdown :hide-on-select="false">
							<a-button>
								显示列
								<template #icon><icon-down /></template>
							</a-button>
							<template #content>
								<a-doption v-for="col in columnDefs" :key="col.key">
									<a-checkbox v-model="col.visible">{{ col.label }}</a-checkbox>
								</a-doption>
							</template>
						</a-dropdown>
						<a-dropdown>
							<a-button>
								更多功能
								<template #icon><icon-down /></template>
							</a-button>
							<template #content>
								<a-doption @click="expandAll">展开全部</a-doption>
								<a-doption @click="collapseAll">全部收起</a-doption>
								<a-doption @click="exportCsv">导出组织</a-doption>
								<a-doption @click="loadTree">刷新</a-doption>
							</template>
						</a-dropdown>
					</a-space>
				</div>
			</a-card>

			<a-card class="oc-table-card" :bordered="false">
				<div class="oc-table-caption">
					<div>
						<strong>组织明细</strong>
						<a-typography-text type="secondary">
							共 {{ orgCount }} 个组织 · {{ memberCount }} 名成员
						</a-typography-text>
					</div>
					<span>将鼠标移到组织行可快速新增下级</span>
				</div>
				<a-spin :loading="loading" style="width: 100%">
					<a-table
						row-key="key"
						:columns="visibleColumns"
						:data="displayTree"
						:pagination="false"
						:bordered="false"
						:hoverable="true"
						v-model:expanded-keys="expandedKeys"
						:scroll="{ x: 'max-content', y: 'calc(100dvh - 420px)' }"
						:row-class="rowClass"
					>
						<template #name="{ record }">
							<span class="oc-name-cell">
								<span class="oc-type-icon" :class="iconClass(record)">
									<icon-home v-if="iconClass(record) === 'is-company'" />
									<icon-user v-else-if="iconClass(record) === 'is-member'" />
									<icon-folder v-else-if="iconClass(record) === 'is-dept'" />
									<icon-user-group v-else />
								</span>
								<template v-if="record.is_employee">
									<a-link class="oc-title is-member" @click.stop="openEmployee(record)">{{ record.title }}</a-link>
									<a-typography-text v-if="record.designation" type="secondary">
										{{ record.designation }}
									</a-typography-text>
								</template>
								<template v-else>
									<span class="oc-title" :class="{ 'is-company': record.is_company }">{{ record.title }}</span>
									<span class="oc-row-actions" :class="{ 'is-company': record.is_company }">
										<a-link @click.stop="openDrawer(record)">新增下级</a-link>
										<a-link v-if="record.is_company" @click.stop="collapseAll">全部收起</a-link>
									</span>
								</template>
							</span>
						</template>
						<template #type="{ record }">
							<a-tag size="small" :color="typeColor(record)">{{ orgTypeOf(record) }}</a-tag>
						</template>
						<template #emp="{ record }">
							<template v-if="record.is_employee">
								<span class="oc-muted">--</span>
							</template>
							<template v-else>
								{{ Number(record.employee_count || 0) }}人
								<a-typography-text v-if="Number(record.parttime_count || 0) > 0" type="secondary">
									({{ record.parttime_count }}人非全职)
								</a-typography-text>
							</template>
						</template>
						<template #quota="{ record }">
							<template v-if="record.is_employee"><span class="oc-muted">--</span></template>
							<template v-else-if="Number(record.staff_quota || 0)">{{ record.staff_quota }}人</template>
							<a-tag v-else size="small">未设置</a-tag>
						</template>
						<template #vacancy="{ record }">
							<template v-if="record.is_employee"><span class="oc-muted">--</span></template>
							<template v-else>
								<a-tag v-if="vacancyState(record) === 'short'" color="orangered" size="small">
									缺编 {{ quotaGap(record) }}人
								</a-tag>
								<a-tag v-else-if="vacancyState(record) === 'over'" color="red" size="small">
									超编 {{ Math.abs(quotaGap(record)) }}人
								</a-tag>
								<a-tag v-else-if="vacancyState(record) === 'full'" color="green" size="small">满编</a-tag>
								<span v-else class="oc-muted">--</span>
							</template>
						</template>
						<template #head="{ record }">
							<span v-if="record.is_employee" class="oc-muted">{{ record.designation || "--" }}</span>
							<PersonCell v-else :record="record" role="head" :company="company" @saved="loadTree" />
						</template>
						<template #supervisor="{ record }">
							<span v-if="record.is_employee" class="oc-muted">--</span>
							<PersonCell v-else :record="record" role="supervisor" :company="company" @saved="loadTree" />
						</template>
					</a-table>
				</a-spin>
			</a-card>

			<OrgDrawer
				v-model:visible="drawerVisible"
				:company="company"
				:preset="drawerPreset"
				:roots="tree"
				@created="loadTree"
			/>

			<a-modal
				v-model:visible="batchVisible"
				title="批量新增/更新"
				:ok-loading="importing"
				ok-text="导入"
				unmount-on-close
				@ok="runImport"
			>
				<a-alert style="margin-bottom: 12px">
					请按模板填写组织名称、上级组织等信息，支持新增或按组织代码更新。
				</a-alert>
				<a-space direction="vertical" fill>
					<a-link @click="downloadTpl">下载 CSV 模板</a-link>
					<a-upload :auto-upload="false" accept=".csv" :limit="1" @change="onBatchFile">
						<template #upload-button>
							<a-button>选择 CSV 文件</a-button>
						</template>
					</a-upload>
				</a-space>
			</a-modal>
		</div>
	</a-config-provider>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { Message } from "@arco-design/web-vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import OrgDrawer from "./OrgDrawer.vue";
import PersonCell from "./PersonCell.vue";
import {
	collectExpandKeys,
	downloadText,
	filterTree,
	flattenTree,
	getImportTemplate,
	getOrgTree,
	importOrgUnits,
	orgTypeOf,
	toTableTree,
	uploadFile,
	vacancyState,
} from "../api";

const COL_STORAGE_KEY = "orgchart-hidden-cols";

const loading = ref(false);
const company = ref("");
const companies = ref([]);
const tree = ref([]);
const keyword = ref("");
const expandedKeys = ref([]);
const filterVisible = ref(false);
const drawerVisible = ref(false);
const drawerPreset = ref({});
const batchVisible = ref(false);
const batchFile = ref(null);
const importing = ref(false);

const filters = reactive({ org_type: "", quota: "", vacancy: "" });

const columnDefs = reactive(loadColumnDefs());

const companyOptions = computed(() =>
	companies.value.map((c) => ({
		value: c.name,
		label: c.company_name || c.abbr || c.name,
	}))
);

const filterCount = computed(
	() => [filters.org_type, filters.quota, filters.vacancy].filter(Boolean).length
);

const flat = computed(() => flattenTree(tree.value));

const summary = computed(() => {
	const units = flat.value.filter((it) => !it.node.is_company && !it.node.is_employee);
	const root = flat.value.find((it) => it.node.is_company)?.node;
	const employees = root
		? Number(root.employee_count || 0)
		: units.reduce((sum, it) => sum + Number(it.node.employee_count || 0), 0);
	const quotaUnits = units.filter((it) => Number(it.node.staff_quota || 0) > 0);
	const vacancies = quotaUnits.reduce(
		(sum, it) => sum + Math.max(Number(it.node.staff_quota || 0) - Number(it.node.employee_count || 0), 0),
		0
	);
	return { units: units.length, employees, quotaSet: quotaUnits.length, vacancies };
});

const displayTree = computed(() => {
	const kw = keyword.value.trim().toLowerCase();
	return filterTree(tree.value, (node) => {
		if (kw) {
			const title = String(node.title || "").toLowerCase();
			const code = String(node.org_code || "").toLowerCase();
			const designation = String(node.designation || "").toLowerCase();
			if (!title.includes(kw) && !code.includes(kw) && !designation.includes(kw)) return false;
		}
		if (filters.org_type && orgTypeOf(node) !== filters.org_type) return false;
		if (node.is_employee) return true;
		const quota = Number(node.staff_quota || 0);
		if (filters.quota === "set" && !quota) return false;
		if (filters.quota === "unset" && quota) return false;
		if (filters.vacancy && vacancyState(node) !== filters.vacancy) return false;
		return true;
	});
});

const visibleRows = computed(() => flattenTree(displayTree.value));
const orgCount = computed(() => visibleRows.value.filter((it) => !it.node.is_employee).length);
const memberCount = computed(() => visibleRows.value.filter((it) => it.node.is_employee).length);

const visibleColumns = computed(() => {
	const cols = [
		{ title: "组织名称", dataIndex: "name", slotName: "name", width: 420, ellipsis: true, tooltip: true },
	];
	const extras = {
		type: { title: "组织类型", dataIndex: "type", slotName: "type", width: 110 },
		emp: { title: "员工数", dataIndex: "emp", slotName: "emp", width: 140 },
		quota: { title: "人员编制", dataIndex: "quota", slotName: "quota", width: 120 },
		vacancy: { title: "缺编/超编", dataIndex: "vacancy", slotName: "vacancy", width: 130 },
		head: { title: "负责人", dataIndex: "head", slotName: "head", width: 140 },
		supervisor: { title: "分管领导", dataIndex: "supervisor", slotName: "supervisor", width: 140 },
	};
	columnDefs.forEach((col) => {
		if (col.visible) cols.push(extras[col.key]);
	});
	return cols;
});

watch(
	columnDefs,
	() => {
		localStorage.setItem(
			COL_STORAGE_KEY,
			JSON.stringify(columnDefs.filter((c) => !c.visible).map((c) => c.key))
		);
	},
	{ deep: true }
);

function loadColumnDefs() {
	let hidden = [];
	try {
		hidden = JSON.parse(localStorage.getItem(COL_STORAGE_KEY) || "[]");
	} catch (e) {
		hidden = [];
	}
	const hiddenSet = new Set(Array.isArray(hidden) ? hidden : []);
	return [
		{ key: "type", label: "组织类型", visible: !hiddenSet.has("type") },
		{ key: "emp", label: "员工数", visible: !hiddenSet.has("emp") },
		{ key: "quota", label: "人员编制", visible: !hiddenSet.has("quota") },
		{ key: "vacancy", label: "缺编/超编", visible: !hiddenSet.has("vacancy") },
		{ key: "head", label: "负责人", visible: !hiddenSet.has("head") },
		{ key: "supervisor", label: "分管领导", visible: !hiddenSet.has("supervisor") },
	];
}

function rowClass(record) {
	if (record.is_company) return "oc-row-company";
	if (record.is_employee) return "oc-row-member";
	return "";
}

function iconClass(record) {
	if (record.is_employee) return "is-member";
	const t = orgTypeOf(record);
	if (record.is_company || t === "公司") return "is-company";
	if (t === "组" || String(record.title || "").endsWith("组")) return "is-group";
	return "is-dept";
}

function typeColor(record) {
	const t = orgTypeOf(record);
	if (t === "公司") return "green";
	if (t === "组") return "gray";
	if (t === "员工") return "cyan";
	return "arcoblue";
}

function quotaGap(record) {
	return Number(record.staff_quota || 0) - Number(record.employee_count || 0);
}

function expandAll() {
	expandedKeys.value = collectExpandKeys(tree.value);
}

function collapseAll() {
	expandedKeys.value = [];
}

function resetFilters() {
	filters.org_type = "";
	filters.quota = "";
	filters.vacancy = "";
}

function openDrawer(record) {
	if (record?.is_employee) return;
	drawerPreset.value = record
		? { parent: record.name, parentTitle: record.title }
		: { parent: tree.value[0]?.name, parentTitle: tree.value[0]?.title };
	drawerVisible.value = true;
}

function openEmployee(record) {
	const id = record.employee || String(record.name || "").replace(/^__emp__/, "");
	if (!id || !window.frappe?.set_route) return;
	frappe.set_route("Form", "Employee", id);
}

let syncingCompany = false;

function onCompanyChange() {
	if (syncingCompany) return;
	loadTree();
}

async function loadTree() {
	loading.value = true;
	try {
		const data = await getOrgTree(company.value || undefined);
		syncingCompany = true;
		company.value = data.company;
		companies.value = data.companies || [];
		tree.value = toTableTree(data.roots || []);
		expandAll();
	} catch (err) {
		Message.error("加载组织架构失败");
	} finally {
		syncingCompany = false;
		loading.value = false;
	}
}

function exportCsv() {
	const rows = [["组织名称", "组织代码", "组织类型", "员工数", "非全职", "人员编制", "缺编/超编", "负责人", "分管领导", "上级组织"]];
	flattenTree(tree.value).forEach((it) => {
		const n = it.node;
		const parent = flattenTree(tree.value).find((x) => x.node.key === it.parentKey);
		const vs = vacancyState(n);
		const gap = quotaGap(n);
		const vacancyLabel = vs === "short" ? `缺编${gap}` : vs === "over" ? `超编${Math.abs(gap)}` : vs === "full" ? "满编" : "";
		rows.push([
			n.title || "",
			n.org_code || "",
			orgTypeOf(n),
			n.employee_count || 0,
			n.parttime_count || 0,
			n.staff_quota || "",
			vacancyLabel,
			n.head_name || "",
			n.supervisor_name || "",
			parent ? parent.node.title : "",
		]);
	});
	downloadText("orgchart.csv", rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n"));
}

async function downloadTpl() {
	const file = await getImportTemplate();
	downloadText(file.filename || "org_import_template.csv", file.content || "");
}

function onBatchFile(_, current) {
	batchFile.value = current?.[0]?.file || current?.[0]?.originFile || null;
}

async function runImport() {
	if (!batchFile.value) {
		Message.warning("请上传 CSV 文件");
		return false;
	}
	importing.value = true;
	try {
		const uploaded = await uploadFile(batchFile.value);
		const res = await importOrgUnits(uploaded.file_url, company.value);
		Message.success(`导入完成：新增 ${res.created || 0}，更新 ${res.updated || 0}，跳过 ${(res.skipped || []).length}`);
		batchVisible.value = false;
		batchFile.value = null;
		await loadTree();
	} finally {
		importing.value = false;
	}
}

watch(keyword, (val) => {
	if (val) expandedKeys.value = collectExpandKeys(displayTree.value);
});

onMounted(loadTree);
</script>
