<template>
	<a-card class="arco-emp-detail-card arco-emp-overview-card" :bordered="true">
		<template #title>
			<div class="arco-emp-detail-card-title">
				<span class="arco-emp-detail-card-icon"><icon-mind-mapping /></span>
				<span>工作与组织</span>
			</div>
		</template>
		<template #extra>
			<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'on_job')">
				查看详情 <icon-right />
			</a-button>
		</template>

		<div class="arco-emp-info-grid arco-emp-overview-org-grid is-fill">
			<EmployeeInfoItem label="所属公司" :value="blank(data.company)" :span="2" />
			<EmployeeInfoItem label="所属部门" :value="blank(departmentDisplay)" />
			<EmployeeInfoItem label="岗位" :value="blank(data.designation)" />
			<EmployeeInfoItem label="职级" :value="blank(data.grade)" />
			<EmployeeInfoItem label="工作地点" :value="blank(data.hr_work_location || data.hr_work_city)" />
			<EmployeeInfoItem label="汇报上级" :value="blank(data.reports_to)" />
			<EmployeeInfoItem
				label="工作性质"
				:value="blank(data.employment_type_label || employmentTypeLabel(data.employment_type))"
			/>
		</div>
	</a-card>
</template>

<script setup>
import { computed } from "vue";
import { IconMindMapping, IconRight } from "@arco-design/web-vue/es/icon";
import { blank, employmentTypeLabel } from "../../utils/employeeArchive";
import EmployeeInfoItem from "./EmployeeInfoItem.vue";

const props = defineProps({
	data: { type: Object, required: true },
});
defineEmits(["navigate"]);

const departmentDisplay = computed(() => {
	const dept = props.data?.department || "";
	const group = props.data?.group_name || "";
	if (dept && group) return `${dept} · ${group}`;
	return dept || group;
});
</script>
