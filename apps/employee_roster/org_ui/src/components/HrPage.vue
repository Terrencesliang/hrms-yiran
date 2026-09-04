<template>
	<div class="arco-org-ui hr-page">
		<h1 v-if="title" class="oc-page-title">{{ title }}</h1>
		<slot />
	</div>
</template>

<script setup>
defineProps({
	title: String,
});
</script>
