<template>
	<div class="oc-toolbar-card">
		<div class="oc-tree-toolbar">
			<a-select v-if="companyOptions.length > 1" :model-value="company" :options="companyOptions" placeholder="切换公司" class="oc-company-select"
				@update:model-value="$emit('update:company', $event)" @change="$emit('company-change')" />
			<a-input-search :model-value="keyword" placeholder="搜索组织或员工" allow-clear class="oc-search"
					@update:model-value="$emit('update:keyword', $event)" />
			<a-popover :popup-visible="filterVisible" trigger="click" position="bl"
					@update:popup-visible="$emit('update:filterVisible', $event)">
				<a-badge :count="filterCount" :dot="filterCount > 0">
					<a-button aria-label="筛选" title="筛选"><template #icon><icon-filter /></template></a-button>
				</a-badge>
					<template #content>
						<a-form :model="filters" layout="vertical" class="oc-filter-form">
							<a-form-item label="组织类型">
								<a-select v-model="filters.org_type" allow-clear placeholder="全部">
									<a-option value="公司">公司</a-option><a-option value="部门">部门</a-option>
									<a-option value="组">组</a-option><a-option value="员工">员工</a-option>
								</a-select>
							</a-form-item>
							<a-form-item label="人员编制">
								<a-select v-model="filters.quota" allow-clear placeholder="全部">
									<a-option value="set">已设置</a-option><a-option value="unset">未设置</a-option>
								</a-select>
							</a-form-item>
							<a-form-item label="缺编/超编">
								<a-select v-model="filters.vacancy" allow-clear placeholder="全部">
									<a-option value="short">缺编</a-option><a-option value="over">超编</a-option><a-option value="full">满编</a-option>
								</a-select>
							</a-form-item>
							<a-space><a-button @click="$emit('reset-filters')">重置</a-button><a-button type="primary" @click="$emit('update:filterVisible', false)">确定</a-button></a-space>
						</a-form>
					</template>
			</a-popover>
		</div>
	</div>
</template>

<script setup>
defineProps({ company: String, companyOptions: { type: Array, default: () => [] }, keyword: String,
	filters: { type: Object, required: true }, filterVisible: Boolean, filterCount: { type: Number, default: 0 } });
defineEmits(["update:company", "update:keyword", "update:filterVisible", "company-change", "reset-filters"]);
</script>

<style scoped>
.oc-toolbar-card, .oc-tree-toolbar { min-width: 0; }
.oc-tree-toolbar { display: flex; align-items: center; gap: 8px; }
.oc-company-select { width: 150px; flex: 0 0 auto; }
.oc-search { min-width: 0; flex: 1 1 auto; }
@media (max-width: 900px) {
	.oc-company-select { width: 120px; }
}
</style>
