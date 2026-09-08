<template>
	<HrPage :breadcrumbs="breadcrumbs" class="approval-admin hr-analysis">
		<main class="ap-main hr-desk-page-stack">
			<ApprovalFormsPanel v-if="activeNav === 'forms'" ref="formsPanel" />
			<ApprovalTemplatesPanel v-else @used="onTemplateUsed" />
		</main>
	</HrPage>
</template>

<script setup>
import { computed, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import HrPage from "../../components/HrPage.vue";
import { APPROVAL_MODULE_LABEL, hrPageBreadcrumbs } from "../../utils/hrBreadcrumbs.js";
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
const pageTitle = computed(() => (activeNav.value === "templates" ? "审批模板库" : "审批表单"));
const breadcrumbs = computed(() => hrPageBreadcrumbs(pageTitle.value, APPROVAL_MODULE_LABEL));

function onTemplateUsed(result) {
	Message.success(`已从模板创建「${result.form_name}」`);
	if (window.frappe?.set_route && result?.name) {
		window.frappe.set_route("approval-form-designer", result.name);
		return;
	}
	activeNav.value = "forms";
	setTimeout(() => formsPanel.value?.reload?.(), 50);
}
</script>
