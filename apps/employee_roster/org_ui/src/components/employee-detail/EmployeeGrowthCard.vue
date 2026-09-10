<template>
	<a-card class="arco-emp-detail-card arco-emp-overview-card arco-emp-growth-card" :bordered="true">
		<template #title>
			<div class="arco-emp-detail-card-title">
				<span class="arco-emp-detail-card-icon"><icon-history /></span>
				<span>成长记录</span>
			</div>
		</template>
		<template #extra>
			<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'profile_tab')">
				查看全部 <icon-right />
			</a-button>
		</template>

		<a-empty v-if="!items.length" description="暂无成长记录" class="arco-emp-empty" />
		<div v-else class="arco-emp-growth-rail">
			<button
				v-for="(item, index) in items"
				:key="item.key"
				type="button"
				class="arco-emp-growth-node"
				@click="$emit('navigate', item.target || 'on_job')"
			>
				<small class="arco-emp-growth-date">{{ item.date || "-" }}</small>
				<span class="arco-emp-growth-track">
					<span class="arco-emp-growth-dot" :class="`is-${item.type || 'default'}`" />
					<span v-if="index < items.length - 1" class="arco-emp-growth-line" aria-hidden="true" />
				</span>
				<strong class="arco-emp-growth-title">{{ item.title }}</strong>
				<em v-if="item.description" class="arco-emp-growth-desc">{{ item.description }}</em>
			</button>
		</div>
	</a-card>
</template>

<script setup>
import { computed } from "vue";
import { IconHistory, IconRight } from "@arco-design/web-vue/es/icon";

const props = defineProps({
	timeline: { type: Array, default: () => [] },
});
defineEmits(["navigate"]);

const items = computed(() => props.timeline || []);
</script>
