<template>
	<div ref="rootRef" class="arco-emp-archive-section-host" :data-section-key="sectionKey || undefined">
		<a-card
			class="arco-emp-archive-section arco-emp-record-section"
			:class="{ 'is-collapsed': !expanded, 'is-expanded': expanded }"
			:bordered="true"
		>
			<template #title>
				<div class="arco-emp-collapse-head" @click="toggle">
					<span class="arco-emp-archive-section-title">{{ title }}</span>
					<span v-if="countLabel" class="arco-emp-collapse-meta">{{ countLabel }}</span>
					<icon-down class="arco-emp-collapse-icon" :class="{ 'is-open': expanded }" />
				</div>
			</template>
			<template v-if="canEdit && expanded" #extra>
				<a-button type="outline" size="mini" @click.stop="$emit('add')">
					<template #icon><icon-plus /></template>
					新增
				</a-button>
			</template>

			<div class="arco-emp-collapse-panel" :class="{ 'is-open': expanded }">
				<div class="arco-emp-collapse-panel-inner">
					<div v-if="expanded" class="arco-emp-archive-section-body">
						<div v-if="!records?.length" class="arco-emp-empty-state">
							<icon-empty :size="48" />
							<p>{{ emptyText }}</p>
						</div>
						<div v-else class="arco-emp-record-cards">
							<div v-for="(row, idx) in records" :key="row.name || idx" class="arco-emp-record-card">
								<div class="arco-emp-record-main">
									<slot name="item" :row="row" :index="idx" />
								</div>
								<div v-if="canEdit" class="arco-emp-record-ops">
									<a-button type="text" size="mini" @click="$emit('edit', row)">编辑</a-button>
									<a-button type="text" size="mini" status="danger" @click="$emit('remove', row)">
										删除
									</a-button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</a-card>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { IconDown, IconEmpty, IconPlus } from "@arco-design/web-vue/es/icon";
import { useSectionExpand } from "./useArchiveExpand";

const props = defineProps({
	title: { type: String, required: true },
	sectionKey: { type: String, default: "" },
	records: { type: Array, default: () => [] },
	canEdit: { type: Boolean, default: false },
	emptyText: { type: String, default: "暂无记录" },
	defaultExpanded: { type: Boolean, default: false },
});

defineEmits(["add", "edit", "remove"]);

const expanded = ref(!!props.defaultExpanded);
const rootRef = ref(null);
const sectionKeyRef = computed(() => props.sectionKey);
const countLabel = computed(() => {
	const n = props.records?.length || 0;
	return n ? `${n} 条` : "";
});

useSectionExpand(sectionKeyRef, expanded, rootRef);

function toggle() {
	expanded.value = !expanded.value;
}
</script>
