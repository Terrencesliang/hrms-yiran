<template>
	<EmployeeDetailCard title="成长记录" :icon="IconHistory">
		<template #action>
			<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'profile_tab')">
				查看全部 <icon-right />
			</a-button>
		</template>
		<div class="arco-emp-journey">
			<button
				v-for="(item, index) in journeyItems"
				:key="item.key"
				type="button"
				class="arco-emp-journey-item"
				@click="$emit('navigate', item.target)"
			>
				<span class="arco-emp-journey-node" :class="`is-${item.tone}`"><component :is="item.icon" /></span>
				<span class="arco-emp-journey-copy">
					<strong>{{ item.title }}</strong>
					<small>{{ item.meta }}</small>
					<em>{{ item.description }}</em>
				</span>
				<span v-if="index < journeyItems.length - 1" class="arco-emp-journey-line" aria-hidden="true" />
			</button>
		</div>
	</EmployeeDetailCard>
</template>

<script setup>
import { computed } from "vue";
import { IconBook, IconCommon, IconHistory, IconSchedule } from "@arco-design/web-vue/es/icon";
import { statusLabel } from "../../utils/employeeDetail";
import EmployeeDetailCard from "./EmployeeDetailCard.vue";

const props = defineProps({ state: { type: Object, required: true } });
defineEmits(["navigate"]);

const journeyItems = computed(() => [
	{
		key: "join",
		title: "入职",
		meta: props.state.date_of_joining || "尚未填写日期",
		description: props.state.employment_type_label || statusLabel(props.state.status),
		target: "date_of_joining",
		icon: IconSchedule,
		tone: "primary",
	},
	{
		key: "education",
		title: "教育经历",
		meta: props.state.education?.length ? `${props.state.education.length} 条记录` : "暂无记录",
		description: props.state.education?.[0]?.school_univ || props.state.education_summary || "学历、专业与培训",
		target: "education",
		icon: IconBook,
		tone: "green",
	},
	{
		key: "work",
		title: "工作经历",
		meta: `${(props.state.external_work_history?.length || 0) + (props.state.internal_work_history?.length || 0)} 条记录`,
		description:
			props.state.external_work_history?.[0]?.company_name ||
			props.state.internal_work_history?.[0]?.department ||
			"外部与内部任职履历",
		target: "external_work_history",
		icon: IconCommon,
		tone: "purple",
	},
]);
</script>
