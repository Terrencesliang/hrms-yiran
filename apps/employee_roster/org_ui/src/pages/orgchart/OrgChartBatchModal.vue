<template>
	<a-modal
		:visible="visible"
		title="批量新增/更新"
		:ok-loading="importing"
		ok-text="导入"
		unmount-on-close
		@update:visible="$emit('update:visible', $event)"
		@ok="$emit('import')"
	>
		<a-alert style="margin-bottom: 12px">
			请按模板填写组织名称、上级组织等信息，支持新增或按组织代码更新。
		</a-alert>
		<a-space direction="vertical" fill>
			<a-link @click="$emit('download-template')">下载 CSV 模板</a-link>
			<a-upload :auto-upload="false" accept=".csv" :limit="1" @change="onFile">
				<template #upload-button>
					<a-button>选择 CSV 文件</a-button>
				</template>
			</a-upload>
		</a-space>
	</a-modal>
</template>

<script setup>
defineProps({
	visible: Boolean,
	importing: Boolean,
});

const emit = defineEmits(["update:visible", "import", "download-template", "file-change"]);

function onFile(list, current) {
	emit("file-change", list, current);
}
</script>
