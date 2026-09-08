<template>
	<EmployeeDetailCard title="档案完整度" :icon="IconSafe">
		<div class="arco-emp-completeness-body">
			<a-progress type="circle" :percent="completionRate / 100" :width="88" :stroke-width="6">
				<template #text>
					<strong class="arco-emp-completeness-percent">{{ completionRate }}<small>%</small></strong>
				</template>
			</a-progress>
			<div class="arco-emp-completeness-side">
				<p class="arco-emp-completion-tip">建议完善以下信息</p>
				<div v-if="missingItems.length" class="arco-emp-missing-list is-compact">
					<button
						v-for="item in missingItems"
						:key="item.label"
						type="button"
						@click="$emit('navigate', item.target)"
					>
						<span><icon-check-circle />{{ item.label }}</span>
					</button>
				</div>
				<div v-else class="arco-emp-complete-state"><icon-safe /> 档案资料已完善</div>
			</div>
		</div>
	</EmployeeDetailCard>
</template>

<script setup>
import { computed } from "vue";
import { IconCheckCircle, IconSafe } from "@arco-design/web-vue/es/icon";
import EmployeeDetailCard from "./EmployeeDetailCard.vue";

const props = defineProps({ state: { type: Object, required: true } });
defineEmits(["navigate"]);

const completionRate = computed(() => {
	const value = Number(props.state.profile_completion);
	return Number.isFinite(value) ? Math.min(100, Math.max(0, Math.round(value))) : 0;
});

const missingItems = computed(() => (props.state.profile_missing || []).slice(0, 4));
</script>
