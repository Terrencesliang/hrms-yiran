<template>
	<div class="arco-emp-header-actions">
		<a-space :size="8" wrap>
			<a-button size="small" @click="$emit('compare')">员工对比</a-button>
			<a-button v-if="canCreateTransfer" size="small" @click="$emit('transfer')">人事异动</a-button>
			<a-dropdown v-if="moreActions.length" trigger="click" @select="onMoreSelect">
				<a-button size="small">更多 <icon-down /></a-button>
				<template #content>
					<a-doption v-for="item in moreActions" :key="item.key" :value="item.key">{{ item.label }}</a-doption>
				</template>
			</a-dropdown>
			<a-button v-if="canEdit" type="primary" size="small" @click="$emit('edit')">
				<template #icon><icon-edit /></template>
				编辑
			</a-button>
		</a-space>
	</div>
</template>

<script setup>
import { IconDown, IconEdit } from "@arco-design/web-vue/es/icon";

defineProps({
	canEdit: { type: Boolean, default: false },
	canCreateTransfer: { type: Boolean, default: false },
	moreActions: { type: Array, default: () => [] },
});

const emit = defineEmits(["edit", "compare", "transfer", "more"]);

function onMoreSelect(key) {
	emit("more", key);
}
</script>
