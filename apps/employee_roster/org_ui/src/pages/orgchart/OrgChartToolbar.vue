<template>
	<a-card class="oc-toolbar-card" :bordered="false">
		<div class="oc-toolbar-row">
			<a-space wrap>
				<a-select
					:model-value="company"
					:options="companyOptions"
					placeholder="切换公司"
					style="width: 220px"
					@update:model-value="$emit('update:company', $event)"
					@change="$emit('company-change')"
				/>
				<a-input-search
					:model-value="keyword"
					placeholder="组织名称/员工姓名/工号"
					allow-clear
					style="width: 240px"
					@update:model-value="$emit('update:keyword', $event)"
				/>
				<a-popover :popup-visible="filterVisible" trigger="click" position="bl" @update:popup-visible="$emit('update:filterVisible', $event)">
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
								<a-button @click="$emit('reset-filters')">重置</a-button>
								<a-button type="primary" @click="$emit('update:filterVisible', false)">确定</a-button>
							</a-space>
						</a-form>
					</template>
				</a-popover>
			</a-space>
			<a-space wrap>
				<a-button type="primary" @click="$emit('create')">
					<template #icon><icon-plus /></template>
					新增组织
				</a-button>
				<a-button @click="$emit('batch')">批量新增/更新</a-button>
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
						<a-doption @click="$emit('expand-all')">展开全部</a-doption>
						<a-doption @click="$emit('collapse-all')">全部收起</a-doption>
						<a-doption @click="$emit('export')">导出组织</a-doption>
						<a-doption @click="$emit('refresh')">刷新</a-doption>
					</template>
				</a-dropdown>
			</a-space>
		</div>
	</a-card>
</template>

<script setup>
defineProps({
	company: String,
	companyOptions: { type: Array, default: () => [] },
	keyword: String,
	filters: { type: Object, required: true },
	filterVisible: Boolean,
	filterCount: { type: Number, default: 0 },
	columnDefs: { type: Array, required: true },
});

defineEmits([
	"update:company",
	"update:keyword",
	"update:filterVisible",
	"company-change",
	"reset-filters",
	"create",
	"batch",
	"expand-all",
	"collapse-all",
	"export",
	"refresh",
]);
</script>
