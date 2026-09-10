<template>
	<a-card class="arco-emp-header-card" :bordered="true">
		<div class="arco-emp-header-v2">
			<div class="arco-emp-header-v2-top">
				<a-avatar :size="44" class="arco-emp-avatar">
					<img v-if="state.image" :src="state.image" :alt="state.employee_name || '员工头像'" />
					<span v-else>{{ initials }}</span>
				</a-avatar>
				<div class="arco-emp-header-v2-identity">
					<div class="arco-emp-header-title">
						<h1 class="arco-emp-name">
							{{ state.is_new ? "新增员工" : dash(state.employee_name || state.name) }}
						</h1>
						<EmployeeStatusTag :status="state.status" />
					</div>
					<p v-if="!state.is_new" class="arco-emp-header-subtitle">
						{{ subtitleLine }}
					</p>
				</div>
			</div>

			<div v-if="!state.is_new && factItems.length" class="arco-emp-header-strip">
				<div
					v-for="item in factItems"
					:key="item.key"
					class="arco-emp-header-strip-item"
					:class="{ 'is-wide': item.wide }"
				>
					<span class="arco-emp-header-strip-icon" :class="`is-${item.key}`">
						<component :is="item.icon" />
					</span>
					<div class="arco-emp-header-strip-copy" :class="{ 'is-wrap': item.wide }">
						<em>{{ item.label }}</em>
						<strong>{{ item.value }}</strong>
					</div>
				</div>
			</div>
		</div>
	</a-card>
</template>

<script setup>
import { computed } from "vue";
import {
	IconCalendar,
	IconHome,
	IconIdcard,
	IconLocation,
	IconSubscribed,
	IconUserGroup,
} from "@arco-design/web-vue/es/icon";
import { dash, departmentLine, workCityLine } from "../../utils/employeeDetail";
import EmployeeStatusTag from "./EmployeeStatusTag.vue";

const props = defineProps({
	state: { type: Object, required: true },
});

const initials = computed(() => String(props.state.employee_name || props.state.name || "?").trim().slice(0, 1));

const tenureText = computed(() => {
	const days = Number(props.state?.tenure_days);
	if (!Number.isFinite(days) || days < 0) return "-";
	return `入职第 ${days} 天`;
});

const subtitleLine = computed(() => {
	const parts = [dash(props.state.designation), departmentLine(props.state), workCityLine(props.state)].filter(
		(v) => v !== "-"
	);
	return parts.join(" · ") || "员工档案";
});

const factItems = computed(() =>
	[
		{ key: "employee_number", label: "工号", value: dash(props.state.employee_number), icon: IconIdcard },
		{ key: "designation", label: "岗位", value: dash(props.state.designation), icon: IconSubscribed },
		{ key: "department", label: "部门", value: departmentLine(props.state), icon: IconUserGroup, wide: true },
		{ key: "location", label: "地点", value: workCityLine(props.state), icon: IconLocation },
		{ key: "company", label: "所属公司", value: dash(props.state.company), icon: IconHome, wide: true },
		{ key: "tenure", label: "入职时间", value: tenureText.value, icon: IconCalendar },
	].filter((item) => item.value !== "-")
);
</script>
