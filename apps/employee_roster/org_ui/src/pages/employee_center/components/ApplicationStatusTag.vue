<template>
	<a-tag :color="meta.color" size="small" class="ec-status-tag">
		<span class="ec-status-dot" />{{ meta.label }}
	</a-tag>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ status?: string }>();

const meta = computed(() => {
	const status = props.status || "";
	if (status === "草稿") return { label: "草稿", color: "gray" };
	if (["进行中", "审批中"].includes(status)) return { label: "审批中", color: "arcoblue" };
	if (status === "已通过") return { label: "已通过", color: "green" };
	if (status === "已驳回") return { label: "已驳回", color: "red" };
	if (["已撤销", "已撤回"].includes(status)) return { label: "已撤回", color: "gray" };
	return { label: status || "未知", color: "gray" };
});
</script>

<style scoped>
.ec-status-tag {
	border: 0;
	border-radius: 12px;
	padding: 0 10px;
}

.ec-status-dot {
	display: inline-block;
	width: 6px;
	height: 6px;
	margin-right: 6px;
	border-radius: 50%;
	background: currentColor;
	vertical-align: 1px;
}
</style>
