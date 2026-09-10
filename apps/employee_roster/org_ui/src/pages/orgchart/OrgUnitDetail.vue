<template>
	<section class="oc-detail-panel">
		<template v-if="unit">
			<header class="oc-detail-header">
				<div class="oc-detail-title-wrap">
					<div class="oc-detail-title"><h2>{{ unit.title }}</h2><a-tag size="small" color="arcoblue">{{ unitType }}</a-tag></div>
					<div class="oc-detail-meta">
						<span>{{ members.length }} 名成员</span><span v-if="Number(unit.staff_quota || 0)">编制 {{ unit.staff_quota }}</span>
					</div>
				</div>
				<div class="oc-detail-actions">
					<a-popover trigger="click" position="br">
						<a-button aria-label="负责人设置" title="负责人设置"><template #icon><icon-user-group /></template></a-button>
						<template #content>
							<div class="oc-owner-pop">
								<div><span>负责人</span><PersonCell :record="unit" role="head" :company="company" @saved="$emit('reload')" /></div>
								<div><span>分管领导</span><PersonCell :record="unit" role="supervisor" :company="company" @saved="$emit('reload')" /></div>
							</div>
						</template>
					</a-popover>
					<a-dropdown position="br">
						<a-button type="primary"><template #icon><icon-plus /></template>新增<icon-down /></a-button>
						<template #content>
							<a-doption @click="$emit('create-child', unit)">新增当前下级</a-doption>
							<a-doption @click="$emit('create-root')">新增一级组织</a-doption>
						</template>
					</a-dropdown>
					<a-dropdown position="br">
						<a-button aria-label="更多" title="更多"><template #icon><icon-more /></template></a-button>
						<template #content>
							<a-doption v-if="!unit.is_company" @click="$emit('edit-unit', unit)">编辑当前组织</a-doption>
							<a-doption @click="$emit('batch')">批量新增/更新</a-doption>
							<a-doption @click="$emit('expand-all')">展开全部</a-doption>
							<a-doption @click="$emit('collapse-all')">全部收起</a-doption>
							<a-doption @click="$emit('export')">导出组织</a-doption>
							<a-doption @click="$emit('refresh')">刷新</a-doption>
						</template>
					</a-dropdown>
				</div>
			</header>
			<div class="oc-member-section">
				<div class="oc-member-caption"><strong>成员</strong><a-typography-text type="secondary">共 {{ members.length }} 人</a-typography-text></div>
				<div class="oc-member-table-scroll">
					<a-table row-key="key" :columns="columns" :data="members" :pagination="false" :bordered="false" :hoverable="true"
						class="oc-member-table">
						<template #employee="{ record }"><a-link class="oc-member-name" @click="$emit('open-employee', record)">{{ record.title }}</a-link></template>
						<template #reportsTo="{ record }">{{ record.reports_to_name || record.reports_to || "—" }}</template>
						<template #status><span class="oc-status"><i></i>在职</span></template>
						<template #empty><a-empty description="该组织暂无成员" /></template>
					</a-table>
				</div>
			</div>
		</template>
		<a-empty v-else description="请选择一个组织查看详情" class="oc-detail-empty" />
	</section>
</template>

<script setup>
import { computed } from "vue";
import PersonCell from "../../components/PersonCell.vue";
const props = defineProps({ unit: { type: Object, default: null }, members: { type: Array, default: () => [] }, company: String });
defineEmits(["create-child", "create-root", "open-employee", "edit-unit", "reload", "batch", "expand-all", "collapse-all", "export", "refresh"]);
const unitType = computed(() => {
	if (props.unit?.is_company) return "公司";
	if (props.unit?.org_type === "组" || String(props.unit?.title || "").trim().endsWith("组")) return "组";
	return props.unit?.org_type || "部门";
});
const columns = [
	{ title: "员工", dataIndex: "title", slotName: "employee", ellipsis: true, tooltip: true },
	{ title: "岗位", dataIndex: "designation", ellipsis: true, tooltip: true },
	{ title: "汇报上级", dataIndex: "reports_to", slotName: "reportsTo", ellipsis: true, tooltip: true },
	{ title: "状态", dataIndex: "status", slotName: "status", width: 100 },
];
</script>

<style scoped>
.oc-detail-panel { display: flex; min-width: 0; min-height: 0; flex-direction: column; overflow: hidden; background: var(--color-bg-2); }
.oc-detail-header { display: flex; min-height: 64px; align-items: center; justify-content: space-between; gap: 16px; padding: 10px 20px;
	border-bottom: 1px solid var(--color-border-2); }
.oc-detail-title-wrap { display: flex; min-width: 0; align-items: center; gap: 16px; }
.oc-detail-title { display: flex; flex: 0 1 auto; align-items: center; gap: 8px; }
.oc-detail-title h2 { overflow: hidden; margin: 0; font-size: 18px; font-weight: 600; line-height: 28px; text-overflow: ellipsis; white-space: nowrap; }
.oc-detail-meta { display: flex; min-width: 0; flex-wrap: nowrap; align-items: center; color: var(--color-text-3); font-size: 13px; white-space: nowrap; }
.oc-detail-meta > span + span::before { content: "·"; margin: 0 10px; color: var(--color-text-4); }
.oc-detail-meta :deep(.oc-person-cell) { color: var(--color-text-2); }
.oc-detail-actions { display: flex; flex: 0 0 auto; align-items: center; gap: 8px; }
.oc-owner-pop { display: grid; min-width: 190px; gap: 10px; }
.oc-owner-pop > div { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.oc-member-section { display: flex; min-height: 0; flex: 1 1 auto; flex-direction: column; padding: 0 20px 16px; }
.oc-member-caption { display: flex; min-height: 54px; align-items: center; gap: 8px; padding: 0 24px; }
.oc-member-caption strong { font-size: 14px; font-weight: 600; }
.oc-member-table-scroll { min-height: 0; flex: 1 1 auto; overflow-x: hidden; overflow-y: auto; overscroll-behavior: contain; border: 1px solid var(--color-border-2); border-radius: 6px; scrollbar-gutter: stable; }
.oc-member-table { min-height: 100%; }
.oc-member-table :deep(.arco-table-th) { height: 44px; background: var(--color-fill-1); color: var(--color-text-3); font-weight: 500; }
.oc-member-table :deep(.arco-table-th) { position: sticky; z-index: 1; top: 0; }
.oc-member-table :deep(.arco-table-td) { height: 52px; }
.oc-member-name { font-weight: 500; }
.oc-status { display: inline-flex; align-items: center; gap: 7px; }
.oc-status i { display: block; width: 7px; height: 7px; border-radius: 50%; background: rgb(var(--green-6)); }
.oc-detail-empty { margin: auto; }
@media (max-width: 1250px) {
	.oc-detail-meta span:nth-child(2), .oc-detail-meta span:nth-child(4) { display: none; }
}
@media (max-width: 1000px) {
	.oc-detail-header { min-height: 96px; align-items: stretch; flex-direction: column; }
	.oc-detail-title-wrap { flex-wrap: wrap; gap: 6px 12px; }
}
</style>
