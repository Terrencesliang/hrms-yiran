<template>
	<div class="arco-emp-overview arco-emp-pro">
		<a-spin :loading="loading && !overview.name" style="width: 100%">
			<div class="arco-emp-workspace-grid arco-emp-detail-grid arco-emp-overview-proto">
				<div class="arco-emp-detail-cell span-4">
					<EmployeeBasicInfoCard :data="merged" @navigate="$emit('navigate', $event)" />
				</div>
				<div class="arco-emp-detail-cell span-4">
					<EmployeeOrganizationCard :data="merged" @navigate="$emit('navigate', $event)" />
				</div>
				<div class="arco-emp-detail-cell span-4">
					<EmployeeAttendanceCard
						:attendance="overview.attendance || {}"
						:loading="loading"
						:error="attendanceError"
						@navigate="$emit('navigate', $event)"
						@retry="loadOverview"
					/>
				</div>
				<div class="arco-emp-detail-cell span-4">
					<EmployeeCompletenessCard
						:checklist="overview.profile_checklist || {}"
						@navigate="$emit('navigate', $event)"
					/>
				</div>
				<div class="arco-emp-detail-cell span-8">
					<EmployeeGrowthCard
						:timeline="overview.growth_timeline || []"
						@navigate="$emit('navigate', $event)"
					/>
				</div>
			</div>
		</a-spin>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { Message } from "@arco-design/web-vue";
import { getEmployeeOverview } from "../api/employeeDetail";
import { errMessage } from "../utils/employeeArchive";
import EmployeeAttendanceCard from "./employee-detail/EmployeeAttendanceCard.vue";
import EmployeeBasicInfoCard from "./employee-detail/EmployeeBasicInfoCard.vue";
import EmployeeCompletenessCard from "./employee-detail/EmployeeCompletenessCard.vue";
import EmployeeGrowthCard from "./employee-detail/EmployeeGrowthCard.vue";
import EmployeeOrganizationCard from "./employee-detail/EmployeeOrganizationCard.vue";

const props = defineProps({
	state: { type: Object, required: true },
	handlers: { type: Object, default: () => ({}) },
});
defineEmits(["navigate"]);

const loading = ref(false);
const overview = ref({});
const attendanceError = ref("");

const merged = computed(() => ({
	...props.state,
	...overview.value,
	name: overview.value.name || props.state.name,
}));

async function loadOverview() {
	const employee = props.state?.name;
	if (!employee || props.state?.is_new) {
		overview.value = {};
		return;
	}
	loading.value = true;
	attendanceError.value = "";
	try {
		const data = await getEmployeeOverview(employee);
		overview.value = data || {};
		if (data?.attendance?.error) {
			attendanceError.value = "考勤数据加载失败";
		}
	} catch (e) {
		Message.error(errMessage(e, "概况数据加载失败"));
		attendanceError.value = errMessage(e, "考勤数据加载失败");
	} finally {
		loading.value = false;
	}
}

watch(
	() => props.state?.name,
	() => {
		loadOverview();
	},
	{ immediate: true }
);

watch(
	() => props.state?.show_overview,
	(show) => {
		if (show) loadOverview();
	}
);
</script>
