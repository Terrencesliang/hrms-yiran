<template>
	<EmployeeDetailCard title="工作与组织" :icon="IconMindMapping">
		<template #action>
			<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'on_job')">
				编辑 <icon-right />
			</a-button>
		</template>
		<div class="arco-emp-info-grid">
			<EmployeeInfoItem label="合同公司" :value="state.company" />
			<EmployeeInfoItem label="部门" :value="state.department" />
			<EmployeeInfoItem label="岗位" :value="state.designation" />
			<EmployeeInfoItem label="职务" :value="state.hr_job_title" />
			<EmployeeInfoItem label="职级" :value="state.grade" />
			<EmployeeInfoItem label="岗位类别" :value="state.hr_position_category" />
			<EmployeeInfoItem label="工作地点" :value="state.hr_work_location || state.branch" />
			<EmployeeInfoItem label="工作性质" :value="state.employment_type_label" />
			<EmployeeInfoItem label="汇报上级" :value="state.reports_to" />
			<EmployeeInfoItem label="考勤编号" :value="state.attendance_device_id" />
			<EmployeeInfoItem label="OA编码" :value="state.hr_oa_code" />
		</div>
	</EmployeeDetailCard>
</template>

<script setup>
import { IconMindMapping, IconRight } from "@arco-design/web-vue/es/icon";
import EmployeeDetailCard from "./EmployeeDetailCard.vue";
import EmployeeInfoItem from "./EmployeeInfoItem.vue";

defineProps({ state: { type: Object, required: true } });
defineEmits(["navigate"]);
</script>
