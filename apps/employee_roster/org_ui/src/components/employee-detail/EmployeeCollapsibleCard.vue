<template>
	<div ref="rootRef" class="arco-emp-archive-section-host" :data-section-key="sectionKey || undefined">
		<a-card
			class="arco-emp-archive-section"
			:class="{ 'is-collapsed': !expanded, 'is-expanded': expanded }"
			:bordered="true"
		>
			<template #title>
				<div class="arco-emp-collapse-head" @click="toggle">
					<span class="arco-emp-archive-section-title">{{ title }}</span>
					<icon-down class="arco-emp-collapse-icon" :class="{ 'is-open': expanded }" />
				</div>
			</template>
			<template v-if="expanded && $slots.extra" #extra>
				<div @click.stop>
					<slot name="extra" />
				</div>
			</template>
			<div class="arco-emp-collapse-panel" :class="{ 'is-open': expanded }">
				<div class="arco-emp-collapse-panel-inner">
					<div v-if="expanded" class="arco-emp-archive-section-body">
						<slot />
					</div>
				</div>
			</div>
		</a-card>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { IconDown } from "@arco-design/web-vue/es/icon";
import { useSectionExpand } from "./useArchiveExpand";

const props = defineProps({
	title: { type: String, required: true },
	sectionKey: { type: String, default: "" },
	defaultExpanded: { type: Boolean, default: false },
});

const expanded = ref(!!props.defaultExpanded);
const rootRef = ref(null);
const sectionKeyRef = computed(() => props.sectionKey);

useSectionExpand(sectionKeyRef, expanded, rootRef);

function toggle() {
	expanded.value = !expanded.value;
}

defineExpose({
	expanded,
	expand: () => {
		expanded.value = true;
	},
	collapse: () => {
		expanded.value = false;
	},
});
</script>
