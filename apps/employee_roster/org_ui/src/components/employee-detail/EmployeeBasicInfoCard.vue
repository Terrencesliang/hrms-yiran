<template>
	<EmployeeDetailCard title="基本信息" :icon="IconUser">
		<template #action>
			<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'personal')">
				编辑 <icon-right />
			</a-button>
		</template>
		<div class="arco-emp-info-grid">
			<EmployeeInfoItem label="姓名" :value="state.employee_name || state.name" />
			<EmployeeInfoItem label="员工状态">
				<EmployeeStatusTag :status="state.status" />
			</EmployeeInfoItem>
			<EmployeeInfoItem label="工号" :value="state.employee_number" />
			<EmployeeInfoItem label="入职日期" :value="joinDateLine(state)" />
			<EmployeeInfoItem label="部门" :value="state.department" />
			<EmployeeInfoItem label="工作城市" :value="workCityLine(state)" />
			<EmployeeInfoItem label="岗位" :value="state.designation" />
			<EmployeeInfoItem label="员工类别" :value="state.hr_employee_identity || state.group_name" />
			<EmployeeInfoItem label="职级" :value="state.grade" />
			<EmployeeInfoItem label="用工形式" :value="state.employment_type_label" />
			<EmployeeInfoItem label="汇报上级" :value="state.reports_to" />
			<EmployeeInfoItem label="试用期" :value="probationStatusText(state)" />
		</div>
	</EmployeeDetailCard>
</template>

<script setup>
import { IconRight, IconUser } from "@arco-design/web-vue/es/icon";
import { joinDateLine, probationStatusText, workCityLine } from "../../utils/employeeDetail";
import EmployeeDetailCard from "./EmployeeDetailCard.vue";
import EmployeeInfoItem from "./EmployeeInfoItem.vue";
import EmployeeStatusTag from "./EmployeeStatusTag.vue";

defineProps({ state: { type: Object, required: true } });
defineEmits(["navigate"]);
</script>
