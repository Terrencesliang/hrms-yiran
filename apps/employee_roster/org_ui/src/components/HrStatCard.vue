<template>
	<a-card class="oc-stat-card" :class="{ 'is-alert': alert }" :bordered="false">
		<a-statistic :title="title" :value="value" :value-from="0" :show-group-separator="groupSeparator">
			<template v-if="suffix" #suffix>{{ suffix }}</template>
			<template v-if="extra" #extra><span class="oc-muted">{{ extra }}</span></template>
		</a-statistic>
	</a-card>
</template>

<script setup>
defineProps({
	title: { type: String, required: true },
	value: { type: [Number, String], default: 0 },
	extra: String,
	suffix: String,
	alert: Boolean,
	groupSeparator: { type: Boolean, default: false },
});
</script>
