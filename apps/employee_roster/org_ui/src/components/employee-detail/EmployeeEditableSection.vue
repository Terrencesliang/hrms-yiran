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
			<template v-if="canEdit && (expanded || mode === 'edit')" #extra>
				<a-space :size="8" @click.stop>
					<template v-if="mode === 'edit'">
						<a-button size="mini" :disabled="saving" @click="onCancel">取消</a-button>
						<a-button type="primary" size="mini" :loading="saving" @click="onSave">保存</a-button>
					</template>
					<a-button v-else type="text" size="mini" class="arco-emp-link-btn" @click="onEdit">
						编辑
					</a-button>
				</a-space>
			</template>
			<template v-else-if="expanded && $slots.extra" #extra>
				<div @click.stop>
					<slot name="extra" />
				</div>
			</template>

			<div class="arco-emp-collapse-panel" :class="{ 'is-open': expanded }">
				<div class="arco-emp-collapse-panel-inner">
					<template v-if="expanded">
						<div v-if="mode === 'view'" class="arco-emp-archive-section-body">
							<slot name="view" />
						</div>
						<div v-else class="arco-emp-archive-section-body is-edit">
							<slot name="edit" />
						</div>
					</template>
				</div>
			</div>
		</a-card>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { IconDown } from "@arco-design/web-vue/es/icon";
import { useSectionExpand } from "./useArchiveExpand";

const props = defineProps({
	title: { type: String, required: true },
	sectionKey: { type: String, default: "" },
	canEdit: { type: Boolean, default: false },
	showFooterActions: { type: Boolean, default: false },
	resetToken: { type: [Number, String], default: 0 },
	defaultExpanded: { type: Boolean, default: false },
});

const emit = defineEmits(["edit", "cancel", "save"]);

const mode = ref("view");
const saving = ref(false);
const expanded = ref(!!props.defaultExpanded);
const rootRef = ref(null);
const sectionKeyRef = computed(() => props.sectionKey);

useSectionExpand(sectionKeyRef, expanded, rootRef);

watch(
	() => props.resetToken,
	() => {
		mode.value = "view";
		saving.value = false;
	}
);

function toggle() {
	expanded.value = !expanded.value;
}

function onEdit() {
	if (!props.canEdit) return;
	expanded.value = true;
	mode.value = "edit";
	emit("edit");
}

function onCancel() {
	if (saving.value) return;
	mode.value = "view";
	emit("cancel");
}

async function onSave() {
	if (saving.value) return;
	saving.value = true;
	try {
		const ok = await new Promise((resolve) => {
			emit("save", {
				done: (success) => resolve(success !== false),
				fail: () => resolve(false),
			});
		});
		if (ok) mode.value = "view";
	} finally {
		saving.value = false;
	}
}

defineExpose({
	mode,
	saving,
	expanded,
	setView: () => {
		mode.value = "view";
	},
	expand: () => {
		expanded.value = true;
	},
	collapse: () => {
		expanded.value = false;
	},
});
</script>
