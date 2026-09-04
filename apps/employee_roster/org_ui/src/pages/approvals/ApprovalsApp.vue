<template>
	<div class="arco-org-ui ap-root ap-root--flat">
		<main class="ap-main">
			<ApprovalFormsPanel v-if="activeNav === 'forms'" ref="formsPanel" />
			<ApprovalTemplatesPanel v-else @used="onTemplateUsed" />
		</main>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { Message } from "@arco-design/web-vue";
import ApprovalFormsPanel from "./ApprovalFormsPanel.vue";
import ApprovalTemplatesPanel from "./ApprovalTemplatesPanel.vue";

const props = defineProps({
	tab: {
		type: String,
		default: "forms",
	},
});

const activeNav = ref(props.tab === "templates" ? "templates" : "forms");
const formsPanel = ref(null);

function onTemplateUsed(result) {
	Message.success(`已从模板创建「${result.form_name}」`);
	if (window.frappe?.set_route) {
		window.frappe.set_route("approvals");
		return;
	}
	activeNav.value = "forms";
	setTimeout(() => formsPanel.value?.reload?.(), 50);
}
</script>
