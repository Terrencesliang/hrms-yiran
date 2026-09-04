<template>
	<a-card class="od-toolbar" :bordered="false">
		<div class="od-toolbar__row">
			<a-space :size="12" wrap>
				<a-select
					:model-value="company"
					:options="companyOptions"
					style="width: 260px"
					placeholder="选择公司"
					@update:model-value="$emit('update:company', $event)"
					@change="$emit('company-change')"
				>
					<template #prefix><icon-home /></template>
				</a-select>
				<a-input-search
					:model-value="keyword"
					style="width: 244px"
					allow-clear
					placeholder="搜索部门、岗位或姓名"
					@update:model-value="$emit('update:keyword', $event)"
				/>
				<a-radio-group
					:model-value="viewMode"
					type="button"
					@update:model-value="$emit('update:viewMode', $event)"
				>
					<a-radio value="diagram"><icon-mind-mapping /> 架构图</a-radio>
					<a-radio value="list"><icon-list /> 列表</a-radio>
				</a-radio-group>
			</a-space>

			<a-space :size="8" wrap>
				<a-select
					:model-value="depth"
					style="width: 132px"
					@update:model-value="$emit('update:depth', $event)"
				>
					<a-option :value="1">仅显示部门</a-option>
					<a-option :value="2">展开到组</a-option>
					<a-option :value="3">展开到成员</a-option>
				</a-select>
				<a-button-group>
					<a-tooltip content="缩小">
						<a-button aria-label="缩小架构图" @click="$emit('zoom-out')"><icon-minus /></a-button>
					</a-tooltip>
					<a-button class="od-zoom-value" disabled>{{ zoom }}%</a-button>
					<a-tooltip content="放大">
						<a-button aria-label="放大架构图" @click="$emit('zoom-in')"><icon-plus /></a-button>
					</a-tooltip>
				</a-button-group>
				<a-button @click="$emit('fit')"><template #icon><icon-fullscreen /></template>适应视图</a-button>
				<a-button @click="$emit('export')"><template #icon><icon-download /></template>导出</a-button>
			</a-space>
		</div>
	</a-card>
</template>

<script setup>
defineProps({
	company: String,
	companyOptions: { type: Array, default: () => [] },
	keyword: String,
	viewMode: { type: String, default: "diagram" },
	depth: { type: Number, default: 2 },
	zoom: { type: Number, default: 100 },
});

defineEmits([
	"update:company",
	"update:keyword",
	"update:viewMode",
	"update:depth",
	"company-change",
	"zoom-out",
	"zoom-in",
	"fit",
	"export",
]);
</script>
