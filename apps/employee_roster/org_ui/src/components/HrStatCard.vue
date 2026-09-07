<template>
	<a-card
		class="oc-stat-card"
		:class="{ 'is-alert': alert, 'is-clickable': clickable }"
		:bordered="false"
		:hoverable="clickable"
		:role="clickable ? 'button' : undefined"
		:tabindex="clickable ? 0 : undefined"
		@click="onClick"
		@keyup.enter="onClick"
		@keyup.space.prevent="onClick"
	>
		<a-statistic :title="title" :value="value" :value-from="0" :show-group-separator="groupSeparator">
			<template v-if="suffix" #suffix><span class="hr-stat-suffix">{{ suffix }}</span></template>
			<template v-if="extra" #extra><span class="oc-muted">{{ extra }}</span></template>
		</a-statistic>
	</a-card>
</template>

<script setup>
const props = defineProps({
	title: { type: String, required: true },
	value: { type: [Number, String], default: 0 },
	extra: String,
	suffix: String,
	alert: Boolean,
	clickable: Boolean,
	groupSeparator: { type: Boolean, default: false },
});

const emit = defineEmits(["click"]);

function onClick() {
	if (props.clickable) emit("click");
}
</script>
