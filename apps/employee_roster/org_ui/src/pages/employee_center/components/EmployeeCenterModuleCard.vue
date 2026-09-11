<template>
	<button type="button" class="ec-module-card" :class="`is-${tone}`" @click="$emit('open')">
		<span class="ec-module-icon"><component :is="icon" /></span>
		<span class="ec-module-copy">
			<strong>{{ title }}</strong>
			<small>{{ description }}</small>
		</span>
		<icon-right class="ec-module-arrow" />
	</button>
</template>

<script setup lang="ts">
import { IconRight } from "@arco-design/web-vue/es/icon";

defineProps<{
	title: string;
	description: string;
	tone: string;
	icon: object;
}>();

defineEmits<{ open: [] }>();
</script>

<style scoped>
.ec-module-card {
	display: flex;
	align-items: center;
	gap: 14px;
	width: 100%;
	min-height: 96px;
	padding: 18px;
	text-align: left;
	background: var(--color-bg-2);
	border: 1px solid var(--color-border-2);
	border-radius: 10px;
	cursor: pointer;
	transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.ec-module-card:hover {
	border-color: rgb(var(--primary-4));
	box-shadow: 0 8px 24px rgba(29, 78, 216, 0.08);
	transform: translateY(-1px);
}

.ec-module-icon {
	display: grid;
	place-items: center;
	width: 44px;
	height: 44px;
	flex: 0 0 44px;
	border-radius: 12px;
	font-size: 22px;
	color: rgb(var(--primary-6));
	background: rgb(var(--primary-1));
}

.is-green .ec-module-icon { color: rgb(var(--green-6)); background: rgb(var(--green-1)); }
.is-orange .ec-module-icon { color: rgb(var(--orange-6)); background: rgb(var(--orange-1)); }
.is-purple .ec-module-icon { color: rgb(var(--purple-6)); background: rgb(var(--purple-1)); }
.is-red .ec-module-icon { color: rgb(var(--red-6)); background: rgb(var(--red-1)); }

.ec-module-copy { min-width: 0; flex: 1; }
.ec-module-copy strong { display: block; color: var(--color-text-1); font-size: 15px; line-height: 22px; }
.ec-module-copy small { display: block; margin-top: 5px; color: var(--color-text-3); font-size: 13px; line-height: 19px; }
.ec-module-arrow { flex: 0 0 auto; color: var(--color-text-4); }
</style>
