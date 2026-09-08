<template>
	<div class="arco-emp-overview arco-emp-pro">
		<div class="arco-emp-workspace-grid arco-emp-detail-grid">
			<div class="arco-emp-detail-cell span-5">
				<EmployeeBasicInfoCard :state="state" @navigate="$emit('navigate', $event)" />
			</div>
			<div class="arco-emp-detail-cell span-3 arco-emp-overview-middle">
				<EmployeeAttendanceCard :state="state" @navigate="$emit('navigate', $event)" />
				<EmployeeCompletenessCard :state="state" @navigate="$emit('navigate', $event)" />
			</div>
			<div class="arco-emp-detail-cell span-4">
				<EmployeeOrganizationCard :state="state" @navigate="$emit('navigate', $event)" />
			</div>
			<div class="arco-emp-detail-cell span-12">
				<EmployeeGrowthCard :state="state" @navigate="$emit('navigate', $event)" />
			</div>
		</div>
	</div>
</template>

<script setup>
import EmployeeAttendanceCard from "./employee-detail/EmployeeAttendanceCard.vue";
import EmployeeBasicInfoCard from "./employee-detail/EmployeeBasicInfoCard.vue";
import EmployeeCompletenessCard from "./employee-detail/EmployeeCompletenessCard.vue";
import EmployeeGrowthCard from "./employee-detail/EmployeeGrowthCard.vue";
import EmployeeOrganizationCard from "./employee-detail/EmployeeOrganizationCard.vue";

defineProps({ state: { type: Object, required: true } });
defineEmits(["navigate"]);
</script>
