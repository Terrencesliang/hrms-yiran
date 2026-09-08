<template>
	<a-card :bordered="false" class="hr-desk-toolbar-card contract-action-toolbar-card">
		<div class="contract-action-toolbar" :class="{ 'is-stacked': hasFilters }">
			<div class="contract-action-toolbar-head">
				<div class="contract-action-toolbar-meta">
					<span class="contract-action-toolbar-icon" aria-hidden="true">
						<IconFile />
					</span>
					<div>
						<div class="contract-action-toolbar-title">{{ title }}</div>
						<div v-if="description" class="contract-action-toolbar-description">{{ description }}</div>
					</div>
				</div>
				<div v-if="hasActions" class="contract-action-toolbar-actions">
					<slot name="actions" />
					<slot v-if="!hasFilters" />
				</div>
			</div>
			<div v-if="hasFilters" class="contract-action-toolbar-filters">
				<slot name="filters" />
			</div>
		</div>
	</a-card>
</template>

<script setup>
import { computed, useSlots } from "vue";
import { IconFile } from "@arco-design/web-vue/es/icon";

defineProps({
	title: {
		type: String,
		required: true,
	},
	description: {
		type: String,
		default: "",
	},
});

const slots = useSlots();
const hasFilters = computed(() => Boolean(slots.filters));
const hasActions = computed(() => Boolean(slots.actions) || !hasFilters.value);
</script>
