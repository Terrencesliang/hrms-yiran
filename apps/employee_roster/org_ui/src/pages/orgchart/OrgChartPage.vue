<template>
	<a-config-provider :locale="zhCN">
		<HrPage :breadcrumbs="breadcrumbs" class="hr-orgchart hr-analysis">
			<div class="oc-page-stack">
				<a-card :bordered="false" class="oc-workspace-card">
					<a-spin :loading="loading" class="oc-workspace-spin">
						<div class="oc-workspace">
							<aside class="oc-hierarchy-panel">
								<div class="oc-panel-heading">
									<OrgChartToolbar
										:company="company"
										:company-options="companyOptions"
										:keyword="keyword"
										:filters="filters"
										:filter-visible="filterVisible"
										:filter-count="filterCount"
										@update:company="company = $event"
										@update:keyword="keyword = $event"
										@update:filter-visible="filterVisible = $event"
										@company-change="onCompanyChange"
										@reset-filters="resetFilters"
									/>
									<a-typography-text type="secondary">{{ orgCount }} 个组织</a-typography-text>
								</div>
								<div v-if="organizationTree.length" class="oc-hierarchy-scroll">
									<ul class="oc-hierarchy-tree">
										<OrgHierarchyNode
											v-for="node in organizationTree"
											:key="node.key"
											:node="node"
											:selected-key="selectedKey"
											:expanded-keys="expandedKeys"
											@select="selectedKey = $event"
											@toggle="toggleNode"
										/>
									</ul>
								</div>
								<a-empty v-else description="没有匹配的组织" class="oc-hierarchy-empty" />
							</aside>

							<OrgUnitDetail
								:unit="selectedUnit"
								:members="selectedMembers"
								:company="company"
								@create-child="openDrawer"
								@create-root="openDrawer()"
								@batch="batchVisible = true"
								@expand-all="expandAll"
								@collapse-all="collapseAll"
								@export="exportCsv"
								@refresh="loadTree"
								@open-employee="openEmployee"
								@edit-unit="openUnitRecord"
								@reload="loadTree"
							/>
						</div>
					</a-spin>
				</a-card>
			</div>

			<OrgDrawer
				v-model:visible="drawerVisible"
				:company="company"
				:preset="drawerPreset"
				:roots="tree"
				@created="loadTree"
			/>

			<OrgChartBatchModal
				v-model:visible="batchVisible"
				:importing="importing"
				@import="runImport"
				@download-template="downloadTpl"
				@file-change="onBatchFile"
			/>
		</HrPage>
	</a-config-provider>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import HrPage from "../../components/HrPage.vue";
import { flattenTree } from "../../api";
import { hrPageBreadcrumbs } from "../../utils/hrBreadcrumbs.js";
import OrgChartBatchModal from "./OrgChartBatchModal.vue";
import OrgChartToolbar from "./OrgChartToolbar.vue";
import OrgDrawer from "./OrgDrawer.vue";
import OrgHierarchyNode from "./OrgHierarchyNode.vue";
import OrgUnitDetail from "./OrgUnitDetail.vue";
import { useOrgChart } from "./composables/useOrgChart";

const breadcrumbs = hrPageBreadcrumbs("组织架构");
const selectedKey = ref("");

const {
	loading, company, tree, keyword, expandedKeys, filterVisible, drawerVisible, drawerPreset,
	batchVisible, importing, filters, companyOptions, filterCount, displayTree, orgCount,
	expandAll, collapseAll, resetFilters, openDrawer, openEmployee, onCompanyChange, loadTree,
	exportCsv, downloadTpl, onBatchFile, runImport,
} = useOrgChart();

function withoutEmployees(nodes) {
	return (nodes || []).filter((node) => !node.is_employee).map((node) => ({
		...node,
		children: withoutEmployees(node.children),
	}));
}

function memberDescendants(node, out = []) {
	for (const child of node?.children || []) {
		if (child.is_employee) out.push(child);
		else memberDescendants(child, out);
	}
	return out;
}

const organizationTree = computed(() => withoutEmployees(displayTree.value));
const allOrganizationRows = computed(() =>
	flattenTree(tree.value).map((item) => item.node).filter((node) => !node.is_employee)
);
const selectedUnit = computed(
	() => allOrganizationRows.value.find((node) => node.key === selectedKey.value) || null
);
const selectedMembers = computed(() => {
	const rows = memberDescendants(selectedUnit.value);
	const search = keyword.value.trim().toLowerCase();
	if (!search) return rows;
	if (String(selectedUnit.value?.title || "").toLowerCase().includes(search)) return rows;
	return rows.filter((member) =>
		[member.title, member.employee_number, member.designation, member.reports_to_name]
			.some((value) => String(value || "").toLowerCase().includes(search))
	);
});

watch(tree, () => {
	const rows = allOrganizationRows.value;
	if (!rows.some((node) => node.key === selectedKey.value)) {
		selectedKey.value = rows.find((node) => !node.is_company)?.key || rows[0]?.key || "";
	}
}, { immediate: true });

function toggleNode(key) {
	const next = new Set(expandedKeys.value);
	if (next.has(key)) next.delete(key);
	else next.add(key);
	expandedKeys.value = [...next];
}

function openUnitRecord(unit) {
	if (!unit?.name || unit.is_company || !window.frappe?.set_route) return;
	frappe.set_route("Form", "Department", unit.name);
}
</script>

<style scoped>
.oc-page-stack { min-width: 0; }
.oc-workspace-card { height: calc(100dvh - 125px); min-height: 420px; overflow: hidden; border: 1px solid var(--color-border-2); border-radius: 8px; box-shadow: none; }
.oc-workspace-card :deep(.arco-card-body) { display: flex; height: 100%; min-height: 0; flex-direction: column; padding: 0; }
.oc-workspace-spin { display: block; width: 100%; min-height: 0; flex: 1 1 auto; }
.oc-workspace-spin :deep(.arco-spin-children) { display: block; width: 100%; height: 100%; min-height: 0; }
.oc-workspace { display: grid; grid-template-columns: minmax(280px, 36%) minmax(0, 1fr); height: 100%; min-height: 0; overflow: hidden; }
.oc-hierarchy-panel { display: flex; min-width: 0; min-height: 0; flex-direction: column; overflow: hidden; border-right: 1px solid var(--color-border-2); }
.oc-panel-heading { display: flex; min-height: 64px; align-items: center; gap: 10px; padding: 0 16px; border-bottom: 1px solid var(--color-border-2); }
.oc-panel-heading :deep(.oc-tree-toolbar) { min-width: 0; flex: 1 1 auto; }
.oc-panel-heading > :deep(.arco-typography) { flex: 0 0 auto; white-space: nowrap; }
.oc-hierarchy-scroll { min-height: 0; flex: 1 1 auto; overflow-x: hidden; overflow-y: auto; overscroll-behavior: contain; padding: 10px 12px 20px; scrollbar-gutter: stable; }
.oc-hierarchy-tree { margin: 0; padding: 0; list-style: none; }
.oc-hierarchy-empty { margin: auto; }
@media (max-width: 1100px) { .oc-workspace { grid-template-columns: minmax(260px, 32%) minmax(0, 1fr); } }
@media (max-width: 820px) {
	.oc-workspace-card { height: auto; max-height: none; }
	.oc-workspace { grid-template-columns: 1fr; height: auto; overflow: visible; }
	.oc-hierarchy-panel { max-height: 360px; border-right: 0; border-bottom: 1px solid var(--color-border-2); }
}
</style>
