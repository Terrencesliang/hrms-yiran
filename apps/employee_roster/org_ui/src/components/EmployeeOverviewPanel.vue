<template>
	<div class="arco-emp-overview arco-emp-pro">
		<div class="arco-emp-workspace-grid">
			<EmployeeSectionCard title="任职信息" subtitle="当前组织归属与岗位信息" :icon="IconUser" :span="6" variant="featured">
				<div class="arco-emp-role-card-body">
					<a-descriptions :column="2" layout="horizontal" size="small" class="arco-emp-role-descriptions">
						<a-descriptions-item v-for="item in roleItems" :key="item.label" :label="item.label">
							{{ item.value }}
						</a-descriptions-item>
					</a-descriptions>
					<div class="arco-emp-role-watermark" aria-hidden="true"><icon-home /></div>
				</div>
			</EmployeeSectionCard>

			<EmployeeSectionCard title="联系方式" subtitle="工作与紧急联系" :icon="IconPhone" :span="3">
				<template #action>
					<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'contact')">
						编辑 <icon-right />
					</a-button>
				</template>
				<div class="arco-emp-contact-list">
					<div v-for="item in contactItems" :key="item.label">
						<span>{{ item.label }}</span><strong>{{ item.value }}</strong>
					</div>
				</div>
			</EmployeeSectionCard>

			<EmployeeSectionCard title="档案完整度" subtitle="完善资料，提升档案可用性" :icon="IconSafe" :span="3" variant="completion">
				<div class="arco-emp-completion-summary">
					<strong>{{ completionRate }}<small>%</small></strong>
					<a-progress :percent="completionRate / 100" :show-text="false" :stroke-width="6" />
				</div>
				<p class="arco-emp-completion-tip">建议完善以下信息</p>
				<div v-if="missingItems.length" class="arco-emp-missing-list">
					<button v-for="item in missingItems" :key="item.label" type="button" @click="$emit('navigate', item.target)">
						<span><icon-safe />{{ item.label }}</span><em>去完善</em>
					</button>
				</div>
				<div v-else class="arco-emp-complete-state"><icon-safe /> 档案信息已完善</div>
			</EmployeeSectionCard>

			<EmployeeSectionCard title="员工经历" subtitle="入职、教育与工作履历" :icon="IconCommon" :span="8" variant="journey">
				<div class="arco-emp-journey">
					<button v-for="(item, index) in journeyItems" :key="item.key" type="button" class="arco-emp-journey-item" @click="$emit('navigate', item.target)">
						<span class="arco-emp-journey-node" :class="`is-${item.tone}`"><component :is="item.icon" /></span>
						<span class="arco-emp-journey-copy">
							<strong>{{ item.title }}</strong>
							<small>{{ item.meta }}</small>
							<em>{{ item.description }}</em>
						</span>
						<span v-if="index < journeyItems.length - 1" class="arco-emp-journey-line" aria-hidden="true" />
					</button>
				</div>
			</EmployeeSectionCard>

			<EmployeeSectionCard title="个人资料" subtitle="部分信息已加密保护" :icon="IconSafe" :span="4" variant="private">
				<template #action>
					<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'personal')">
						编辑 <icon-right />
					</a-button>
				</template>
				<a-descriptions :column="2" layout="vertical" size="small" class="arco-emp-descriptions arco-emp-private-descriptions">
					<a-descriptions-item v-for="item in personalItems" :key="item.label" :label="item.label">
						{{ item.value }}
					</a-descriptions-item>
				</a-descriptions>
			</EmployeeSectionCard>

			<EmployeeSectionCard title="简历 / 求职信" subtitle="个人简介与职业概述" :icon="IconFile" :span="12" :empty="!bioPreview" empty-text="暂无简历内容">
				<template #action>
					<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'bio')">
						查看完整简历 <icon-right />
					</a-button>
				</template>
				<p class="arco-emp-bio-text">{{ bioPreview }}</p>
			</EmployeeSectionCard>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { IconBook, IconCommon, IconFile, IconHome, IconPhone, IconSafe, IconSchedule, IconUser } from "@arco-design/web-vue/es/icon";
import EmployeeSectionCard from "./EmployeeSectionCard.vue";

const props = defineProps({ state: { type: Object, required: true } });
defineEmits(["navigate"]);

function dash(value) {
	return value === 0 || value ? value : "—";
}

const maritalMap = { Single: "未婚", Married: "已婚", Divorced: "离异", Widowed: "丧偶" };
const maritalLabel = computed(() => maritalMap[props.state.marital_status] || props.state.marital_status || "—");
const maskPassport = computed(() => {
	const raw = String(props.state.passport_number || "").trim();
	if (!raw) return "—";
	if (raw.length <= 4) return "****";
	return `${"*".repeat(Math.max(4, raw.length - 4))}${raw.slice(-4)}`;
});
const bioPreview = computed(() => {
	const raw = String(props.state.bio_text || "").trim();
	return raw ? (raw.length > 320 ? `${raw.slice(0, 320)}…` : raw) : "";
});
const completionRate = computed(() => {
	const value = Number(props.state.profile_completion);
	return Number.isFinite(value) ? Math.min(100, Math.max(0, Math.round(value))) : 0;
});

const roleItems = computed(() => [
	{ label: "公司", value: dash(props.state.company) },
	{ label: "部门", value: dash(props.state.department) },
	{ label: "职位", value: dash(props.state.designation) },
	{ label: "分支机构", value: dash(props.state.branch) },
	{ label: "上级主管", value: dash(props.state.reports_to) },
	{ label: "雇佣类型", value: dash(props.state.employment_type_label || props.state.employment_type) },
]);
const contactItems = computed(() => [
	{ label: "手机号", value: dash(props.state.cell_number) },
	{ label: "公司邮箱", value: dash(props.state.company_email) },
	{ label: "个人邮箱", value: dash(props.state.personal_email) },
	{ label: "紧急联系人", value: dash(props.state.person_to_be_contacted) },
	{ label: "紧急电话", value: dash(props.state.emergency_phone_number) },
	{ label: "关系", value: dash(props.state.relation) },
]);
const personalItems = computed(() => [
	{ label: "婚姻状况", value: maritalLabel.value },
	{ label: "血型", value: dash(props.state.blood_group) },
	{ label: "护照号码", value: maskPassport.value },
	{ label: "健康保险", value: dash(props.state.health_insurance_provider) },
]);
const missingItems = computed(() => (props.state.profile_missing || []).slice(0, 3));
const journeyItems = computed(() => [
	{
		key: "join",
		title: "入职记录",
		meta: props.state.date_of_joining || "尚未填写日期",
		description: props.state.date_of_joining ? "已入职" : "待完善",
		target: "employment_details",
		icon: IconSchedule,
		tone: "primary",
	},
	{
		key: "education",
		title: "教育培训",
		meta: props.state.education?.length ? `${props.state.education.length} 条记录` : "暂无教育培训记录",
		description: props.state.education?.[0]?.school_univ || "学历、专业与培训",
		target: "education",
		icon: IconBook,
		tone: "green",
	},
	{
		key: "work",
		title: "工作经历",
		meta: `${(props.state.external_work_history?.length || 0) + (props.state.internal_work_history?.length || 0)} 条记录`,
		description: props.state.external_work_history?.[0]?.company_name || props.state.internal_work_history?.[0]?.department || "外部与内部任职履历",
		target: "external_work_history",
		icon: IconCommon,
		tone: "purple",
	},
]);
</script>
