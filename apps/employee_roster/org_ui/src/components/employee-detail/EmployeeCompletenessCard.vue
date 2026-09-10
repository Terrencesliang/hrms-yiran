<template>
	<a-card class="arco-emp-detail-card arco-emp-overview-card" :bordered="true">
		<template #title>
			<div class="arco-emp-detail-card-title">
				<span class="arco-emp-detail-card-icon"><icon-safe /></span>
				<span>档案完整度</span>
			</div>
		</template>
		<template #extra>
			<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'materials')">
				查看详情 <icon-right />
			</a-button>
		</template>

		<div class="arco-emp-completeness-body">
			<a-progress type="circle" :percent="completionRate / 100" :width="92" :stroke-width="8" color="#165DFF">
				<template #text>
					<strong class="arco-emp-completeness-percent">{{ completionRate }}<small>%</small></strong>
				</template>
			</a-progress>
			<div class="arco-emp-completeness-side">
				<div v-if="items.length" class="arco-emp-checklist">
					<button
						v-for="item in items"
						:key="item.key"
						type="button"
						class="arco-emp-checklist-item"
						:class="{ 'is-done': item.done }"
						@click="$emit('navigate', item.target)"
					>
						<span class="arco-emp-checklist-mark">
							<icon-check-circle-fill v-if="item.done" />
							<span v-else class="arco-emp-checklist-empty" />
						</span>
						<span>{{ item.done ? item.label : item.action_label || item.label }}</span>
					</button>
				</div>
				<div v-else class="arco-emp-complete-state"><icon-safe /> 档案资料已完善</div>
			</div>
		</div>
	</a-card>
</template>

<script setup>
import { computed } from "vue";
import { IconCheckCircleFill, IconRight, IconSafe } from "@arco-design/web-vue/es/icon";

const props = defineProps({
	checklist: { type: Object, default: () => ({}) },
});
defineEmits(["navigate"]);

const completionRate = computed(() => {
	const value = Number(props.checklist?.rate);
	return Number.isFinite(value) ? Math.min(100, Math.max(0, Math.round(value))) : 0;
});

const items = computed(() => props.checklist?.items || []);
</script>
