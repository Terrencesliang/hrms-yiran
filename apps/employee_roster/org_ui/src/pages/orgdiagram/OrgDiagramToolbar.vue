<template>
	<a-card class="od-toolbar hr-panel-card" :bordered="false">
		<div class="od-toolbar__row">
			<div class="od-toolbar__cluster od-toolbar__cluster--primary">
				<a-select
					v-if="companyOptions.length > 1"
					:model-value="company"
					:options="companyOptions"
					size="small"
					class="od-toolbar__company"
					placeholder="选择公司"
					@update:model-value="$emit('update:company', $event)"
					@change="$emit('company-change')"
				>
					<template #prefix><icon-home /></template>
				</a-select>

				<a-input-search
					:model-value="keyword"
					size="small"
					allow-clear
					class="od-toolbar__search"
					placeholder="搜索部门、岗位或姓名"
					@update:model-value="$emit('update:keyword', $event)"
				/>

				<a-select
					:model-value="depth"
					size="small"
					class="od-toolbar__depth"
					@update:model-value="$emit('update:depth', $event)"
				>
					<a-option :value="1">仅部门</a-option>
					<a-option :value="2">展开到组</a-option>
					<a-option :value="3">展开到成员</a-option>
				</a-select>
			</div>

			<a-button size="small" type="outline" class="od-toolbar__export" @click="$emit('export')">
				<template #icon><icon-download /></template>
				导出
			</a-button>
		</div>
	</a-card>
</template>

<script setup>
defineProps({
	company: String,
	companyOptions: { type: Array, default: () => [] },
	keyword: String,
	depth: { type: Number, default: 2 },
});

defineEmits([
	"update:company",
	"update:keyword",
	"update:depth",
	"company-change",
	"export",
]);
</script>
