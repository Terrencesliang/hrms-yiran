<template>
	<a-config-provider :locale="zhCN">
	<HrPage :breadcrumbs="breadcrumbs" class="hr-orgchart hr-analysis">
		<div class="hr-analysis-stack">
			<div class="hr-analysis-kpis">
				<a-card v-for="card in summaryCards" :key="card.key" :bordered="false" class="hr-kpi-card">
					<a-statistic
						:title="card.title"
						:value="card.value"
						:suffix="card.suffix"
						:extra="card.extra"
						:value-from="0"
						show-group-separator
					/>
				</a-card>
			</div>

			<OrgChartToolbar
					:company="company"
					:company-options="companyOptions"
					:keyword="keyword"
					:filters="filters"
					:filter-visible="filterVisible"
					:filter-count="filterCount"
					:column-defs="columnDefs"
					@update:company="company = $event"
					@update:keyword="keyword = $event"
					@update:filter-visible="filterVisible = $event"
					@company-change="onCompanyChange"
					@reset-filters="resetFilters"
					@create="openDrawer()"
					@batch="batchVisible = true"
					@expand-all="expandAll"
					@collapse-all="collapseAll"
					@export="exportCsv"
					@refresh="loadTree"
			/>

			<a-card :bordered="false" class="hr-panel-card hr-panel-card--fill">
				<template #title>组织明细</template>
				<template #extra>
					<a-typography-text type="secondary">
						共 {{ orgCount }} 个组织 · {{ memberCount }} 名成员
					</a-typography-text>
				</template>
				<div class="hr-panel-body hr-rank-wrap">
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
				</div>
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
import { computed } from "vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import HrPage from "../../components/HrPage.vue";
import { hrPageBreadcrumbs } from "../../utils/hrBreadcrumbs.js";
import PersonCell from "../../components/PersonCell.vue";
import OrgChartBatchModal from "./OrgChartBatchModal.vue";
import OrgChartToolbar from "./OrgChartToolbar.vue";
import OrgDrawer from "./OrgDrawer.vue";
import { useOrgChart } from "./composables/useOrgChart";

const breadcrumbs = hrPageBreadcrumbs("组织架构");

const {
	loading,
	company,
	tree,
	keyword,
	expandedKeys,
	filterVisible,
	drawerVisible,
	drawerPreset,
	batchVisible,
	importing,
	filters,
	columnDefs,
	companyOptions,
	filterCount,
	summary,
	displayTree,
	orgCount,
	memberCount,
	visibleColumns,
	orgTypeOf,
	vacancyState,
	rowClass,
	iconClass,
	typeColor,
	quotaGap,
	expandAll,
	collapseAll,
	resetFilters,
	openDrawer,
	openEmployee,
	onCompanyChange,
	loadTree,
	exportCsv,
	downloadTpl,
	onBatchFile,
	runImport,
} = useOrgChart();

const summaryCards = computed(() => [
	{ key: "units", title: "组织单元", value: summary.value?.units || 0, suffix: "", extra: "当前公司组织总数" },
	{ key: "employees", title: "员工总数", value: summary.value?.employees || 0, suffix: "", extra: "在组织架构中的员工" },
	{
		key: "quota",
		title: "已设编制",
		value: summary.value?.quotaSet || 0,
		suffix: `/ ${summary.value?.units || 0}`,
		extra: "已维护编制的组织",
	},
	{ key: "vacancies", title: "待补岗位", value: summary.value?.vacancies || 0, suffix: "", extra: "根据已设置编制统计" },
]);
</script>
