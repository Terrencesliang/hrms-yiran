<template>
	<HrDeskPageHeader :breadcrumbs="breadcrumbs" module-class="hr-employee-form-desk" />
</template>

<script setup>
import { computed } from "vue";
import HrDeskPageHeader from "../../components/HrDeskPageHeader.vue";
import { HR_MODULE_LABEL } from "../../utils/hrBreadcrumbs.js";

const props = defineProps({
	employeeName: { type: String, default: "" },
});

const breadcrumbs = computed(() => [
	{ label: HR_MODULE_LABEL },
	{ label: "员工花名册", route: "List/Employee" },
	{ label: props.employeeName || "员工详情" },
]);
</script>
