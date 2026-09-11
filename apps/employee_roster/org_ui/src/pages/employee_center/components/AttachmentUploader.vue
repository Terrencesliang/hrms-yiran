<template>
	<div class="ec-attachment">
		<a-upload :custom-request="upload" :show-file-list="false" :limit="1">
			<template #upload-button><a-button><template #icon><icon-upload /></template>{{ modelValue ? "重新上传" : "上传文件" }}</a-button></template>
		</a-upload>
		<a-link v-if="modelValue" :href="modelValue" target="_blank"><icon-file /> 查看附件</a-link>
		<a-button v-if="modelValue" type="text" status="danger" size="small" @click="$emit('update:modelValue', '')">删除</a-button>
	</div>
</template>
<script setup lang="ts">
import { Message } from "@arco-design/web-vue";
import { IconFile, IconUpload } from "@arco-design/web-vue/es/icon";
import { uploadFile } from "../../../api/employeeCenter";
defineProps<{ modelValue?: string }>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();
function upload(option: any) {
	let aborted = false;
	void (async () => {
		try {
			const result = await uploadFile(option.fileItem?.file || option.fileItem);
			if (aborted) return;
			emit("update:modelValue", result.file_url);
			option.onSuccess?.(result);
		} catch (error) { if (!aborted) { option.onError?.(error); Message.error("附件上传失败"); } }
	})();
	return { abort() { aborted = true; } };
}
</script>
