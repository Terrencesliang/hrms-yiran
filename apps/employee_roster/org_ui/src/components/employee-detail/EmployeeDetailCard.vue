<template>
	<a-card class="arco-emp-detail-card" :bordered="true">
		<template #title>
			<div class="arco-emp-detail-card-title">
				<span v-if="icon" class="arco-emp-detail-card-icon"><component :is="icon" /></span>
				<span>{{ title }}</span>
			</div>
		</template>
		<template v-if="$slots.action" #extra><slot name="action" /></template>
		<slot />
	</a-card>
</template>

<script setup>
defineProps({
	title: { type: String, required: true },
	icon: { type: [Object, Function], default: null },
});
</script>
