<template>
	<a-card
		class="hr-employee-overview-card"
		:class="{ 'hr-employee-overview-card--compact': compact }"
		:bordered="false"
		:loading="loading"
	>
		<div v-if="metaTitle || metaHint" class="hr-employee-overview-head">
			<div>
				<div v-if="metaTitle" class="hr-employee-overview-title">
					<component :is="metaIcon" v-if="metaIcon" />
					<span>{{ metaTitle }}</span>
				</div>
				<div v-if="metaHint" class="hr-employee-overview-hint">{{ metaHint }}</div>
			</div>
			<div v-if="metaExtra" class="hr-employee-overview-hint">{{ metaExtra }}</div>
		</div>
		<div class="hr-employee-overview-grid" :class="gridClass">
			<button
				v-for="item in items"
				:key="item.key"
				type="button"
				class="hr-employee-overview-item"
				:class="[`is-${item.tone}`, { 'is-active': item.active, 'is-disabled': item.disabled }]"
				:disabled="item.disabled"
				:aria-pressed="item.active"
				@click="select(item)"
			>
				<span class="hr-employee-overview-icon"><component :is="item.icon" /></span>
				<span class="hr-employee-overview-copy">
					<span class="hr-employee-overview-label">{{ item.label }}</span>
					<strong>{{ formatNumber(item.value) }}<small>{{ item.suffix || "人" }}</small></strong>
				</span>
			</button>
		</div>
	</a-card>
</template>

<script setup>
const props = defineProps({
	items: { type: Array, default: () => [] },
	loading: { type: Boolean, default: false },
	compact: { type: Boolean, default: true },
	gridClass: { type: String, default: "" },
	metaTitle: { type: String, default: "" },
	metaHint: { type: String, default: "" },
	metaExtra: { type: String, default: "" },
	metaIcon: { type: [Object, Function], default: null },
	handlers: { type: Object, default: () => ({}) },
});

function formatNumber(value) {
	return Number(value || 0).toLocaleString("zh-CN");
}

function select(item) {
	if (!item.disabled) props.handlers?.onSelect?.(item);
}
</script>
