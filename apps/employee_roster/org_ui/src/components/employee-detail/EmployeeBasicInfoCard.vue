<template>
	<a-card class="arco-emp-detail-card arco-emp-overview-card" :bordered="true">
		<template #title>
			<div class="arco-emp-detail-card-title">
				<span class="arco-emp-detail-card-icon"><icon-user /></span>
				<span>基本信息</span>
			</div>
		</template>
		<template #extra>
			<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'personal')">
				查看详情 <icon-right />
			</a-button>
		</template>

		<div class="arco-emp-info-grid arco-emp-overview-basic-grid">
			<EmployeeInfoItem label="员工姓名" :value="blank(data.employee_name)" />
			<EmployeeInfoItem label="证件号码" :value="blank(data.hr_id_number)" />
			<EmployeeInfoItem label="性别" :value="genderLabel(data.gender)" />
			<EmployeeInfoItem label="岗位" :value="blank(data.designation)" />
			<EmployeeInfoItem label="手机号码" :value="blank(data.cell_number)" />
			<EmployeeInfoItem label="员工状态">
				<EmployeeStatusTag :status="data.status" />
			</EmployeeInfoItem>
			<EmployeeInfoItem label="工号" :value="blank(data.employee_number)" />
			<EmployeeInfoItem label="入职时间" :value="blank(joinDisplay)" />
			<EmployeeInfoItem label="现居住地" :value="blank(data.current_address)" :span="2" />
		</div>
	</a-card>
</template>

<script setup>
import { computed } from "vue";
import { IconRight, IconUser } from "@arco-design/web-vue/es/icon";
import { blank, formatDate, genderLabel } from "../../utils/employeeArchive";
import EmployeeInfoItem from "./EmployeeInfoItem.vue";
import EmployeeStatusTag from "./EmployeeStatusTag.vue";

const props = defineProps({
	data: { type: Object, required: true },
});
defineEmits(["navigate"]);

const joinDisplay = computed(() => {
	const raw = formatDate(props.data?.date_of_joining);
	if (!raw) return "";
	const m = String(raw).match(/^(\d{4})-(\d{2})-(\d{2})$/);
	if (m) return `${m[1]}年${m[2]}月${m[3]}日`;
	return raw;
});
</script>
