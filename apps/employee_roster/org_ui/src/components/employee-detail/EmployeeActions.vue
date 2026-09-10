<template>
	<div class="arco-emp-header-actions">
		<a-space :size="8" wrap>
			<template v-if="isNew || isEditing">
				<a-button size="small" :disabled="isSaving" @click="$emit('cancel')">取消</a-button>
				<a-button
					type="primary"
					size="small"
					:loading="isSaving"
					:disabled="!canSave || (!isNew && !isDirty)"
					@click="$emit('save')"
				>
					保存
				</a-button>
			</template>
			<template v-else>
				<a-button v-if="canCreateTransfer" size="small" @click="$emit('transfer')">人事异动</a-button>
			</template>
			<a-dropdown v-if="!isNew && !isEditing && moreActions.length" trigger="click" @select="onMoreSelect">
				<a-button size="small">更多 <icon-down /></a-button>
				<template #content>
					<a-doption
						v-for="item in moreActions"
						:key="item.key"
						:value="item.key"
						:class="{ 'arco-emp-danger-option': item.danger }"
					>
						{{ item.label }}
					</a-doption>
				</template>
			</a-dropdown>
			<a-popconfirm
				v-if="!isNew && !isEditing && canDelete"
				content="该员工已离职。删除后无法恢复，确定继续吗？"
				type="warning"
				:ok-loading="isDeleting"
				@ok="$emit('delete')"
			>
				<a-button size="small" status="danger" :loading="isDeleting">删除</a-button>
			</a-popconfirm>
			<a-button v-if="!isNew && !isEditing && canEdit" type="primary" size="small" @click="$emit('edit')">
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
	canSave: { type: Boolean, default: false },
	canDelete: { type: Boolean, default: false },
	isNew: { type: Boolean, default: false },
	isEditing: { type: Boolean, default: false },
	isDirty: { type: Boolean, default: false },
	isSaving: { type: Boolean, default: false },
	isDeleting: { type: Boolean, default: false },
	moreActions: { type: Array, default: () => [] },
});

const emit = defineEmits(["edit", "transfer", "more", "save", "cancel", "delete"]);

function onMoreSelect(key) {
	emit("more", key);
}
</script>
