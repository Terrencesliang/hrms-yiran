<template>
	<HrDeskPageHeader title="考勤规则" :module="ATTENDANCE_MODULE_LABEL" module-class="hr-attendance-rules-desk" />
</template>

<script setup>
import HrDeskPageHeader from "../../components/HrDeskPageHeader.vue";
import { ATTENDANCE_MODULE_LABEL } from "../../utils/hrBreadcrumbs.js";
</script>
