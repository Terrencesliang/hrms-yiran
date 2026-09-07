<template>
	<a-card
		:bordered="false"
		class="arco-emp-section-card"
		:class="[`span-${span}`, variant ? `is-${variant}` : '']"
	>
		<template #title>
			<div class="arco-emp-section-heading">
				<span class="arco-emp-section-icon"><component :is="icon" /></span>
				<span>
					<strong>{{ title }}</strong>
					<small v-if="subtitle">{{ subtitle }}</small>
				</span>
			</div>
		</template>
		<template v-if="$slots.action" #extra><slot name="action" /></template>

		<a-empty v-if="empty" :description="emptyText" class="arco-emp-empty" />
		<slot v-else />
	</a-card>
</template>

<script setup>
defineProps({
	title: { type: String, required: true },
	subtitle: { type: String, default: "" },
	icon: { type: [Object, Function], required: true },
	span: { type: Number, default: 12 },
	variant: { type: String, default: "" },
	empty: Boolean,
	emptyText: { type: String, default: "暂无数据" },
});
</script>
