<template>
	<a-card class="arco-emp-header-card" :bordered="true">
		<div class="arco-emp-header">
			<div class="arco-emp-header-main">
				<a-avatar :size="56" class="arco-emp-avatar">
					<img v-if="state.image" :src="state.image" :alt="state.employee_name || '员工头像'" />
					<span v-else>{{ initials }}</span>
				</a-avatar>
				<div class="arco-emp-header-copy">
					<div class="arco-emp-header-title">
						<h1 class="arco-emp-name">{{ dash(state.employee_name || state.name) }}</h1>
						<EmployeeStatusTag :status="state.status" />
					</div>
					<p class="arco-emp-header-meta">{{ headerMetaLine(state) }}</p>
					<p class="arco-emp-header-meta is-muted">
						<span v-if="state.company"><icon-home />{{ dash(state.company) }}</span>
						<span v-if="workCityLine(state) !== '—'"><icon-location />{{ workCityLine(state) }}</span>
					</p>
				</div>
			</div>
			<EmployeeActions
				:can-edit="!!state.can_edit"
				:can-create-transfer="!!state.can_create_transfer"
				:more-actions="moreActions"
				@edit="$emit('edit')"
				@compare="$emit('compare')"
				@transfer="$emit('transfer')"
				@more="$emit('more', $event)"
			/>
		</div>
	</a-card>
</template>

<script setup>
import { computed } from "vue";
import { IconHome, IconLocation } from "@arco-design/web-vue/es/icon";
import { dash, headerMetaLine, workCityLine } from "../../utils/employeeDetail";
import EmployeeActions from "./EmployeeActions.vue";
import EmployeeStatusTag from "./EmployeeStatusTag.vue";

const props = defineProps({
	state: { type: Object, required: true },
	moreActions: { type: Array, default: () => [] },
});

defineEmits(["edit", "compare", "transfer", "more"]);

const initials = computed(() => String(props.state.employee_name || props.state.name || "?").trim().slice(0, 1));
</script>
