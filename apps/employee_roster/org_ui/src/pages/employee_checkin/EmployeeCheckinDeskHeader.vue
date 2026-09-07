<template>
	<HrDeskPageHeader title="打卡记录" :module="ATTENDANCE_MODULE_LABEL" module-class="hr-checkin-list-desk" />
</template>

<script setup>
import HrDeskPageHeader from "../../components/HrDeskPageHeader.vue";
import { ATTENDANCE_MODULE_LABEL } from "../../utils/hrBreadcrumbs.js";
</script>
