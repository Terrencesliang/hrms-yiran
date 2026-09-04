<template>
	<div class="arco-emp-overview arco-emp-pro">
		<section class="arco-emp-section-card">
			<div class="arco-emp-section-head">
				<h3 class="arco-emp-section-title">基本信息</h3>
			</div>
			<div class="arco-emp-section-body">
				<div class="arco-emp-info-grid cols-3">
					<div v-for="item in basicItems" :key="item.label" class="arco-emp-info-item">
						<div class="arco-emp-info-label">{{ item.label }}</div>
						<div class="arco-emp-info-value">
							<a-tag v-if="item.tag" :color="item.tagColor" size="small">{{ item.value }}</a-tag>
							<template v-else>{{ item.value }}</template>
						</div>
					</div>
				</div>
			</div>
		</section>

		<section class="arco-emp-section-card">
			<div class="arco-emp-section-head">
				<h3 class="arco-emp-section-title">联系方式摘要</h3>
			</div>
			<div class="arco-emp-section-body">
				<div class="arco-emp-info-grid cols-3">
					<div v-for="item in contactItems" :key="item.label" class="arco-emp-info-item">
						<div class="arco-emp-info-label">{{ item.label }}</div>
						<div class="arco-emp-info-value">{{ item.value }}</div>
					</div>
				</div>
			</div>
		</section>

		<section class="arco-emp-section-card">
			<div class="arco-emp-section-head">
				<h3 class="arco-emp-section-title">简历 / 求职信</h3>
				<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'bio')">
					查看完整简历
				</a-button>
			</div>
			<div class="arco-emp-section-body">
				<p v-if="bioPreview" class="arco-emp-bio-text">{{ bioPreview }}</p>
				<div v-else class="arco-emp-mini-empty">暂无简历内容</div>
			</div>
		</section>

		<section class="arco-emp-section-card">
			<div class="arco-emp-section-head">
				<h3 class="arco-emp-section-title">教育培训</h3>
				<a-button type="text" size="mini" class="arco-emp-link-btn" @click="$emit('navigate', 'education')">
					去编辑
				</a-button>
			</div>
			<div class="arco-emp-section-body">
				<a-table
					v-if="educationRows.length"
					class="arco-emp-compact-table"
					:columns="educationColumns"
					:data="educationRows"
					:pagination="false"
					:bordered="false"
					size="small"
					row-key="_idx"
				/>
				<div v-else class="arco-emp-mini-empty">暂无教育培训记录</div>
			</div>
		</section>

		<section class="arco-emp-section-card">
			<div class="arco-emp-section-head">
				<h3 class="arco-emp-section-title">工作经历</h3>
				<a-button
					type="text"
					size="mini"
					class="arco-emp-link-btn"
					@click="$emit('navigate', 'external_work_history')"
				>
					去编辑
				</a-button>
			</div>
			<div class="arco-emp-section-body">
				<div class="arco-emp-work-block">
					<div class="arco-emp-work-label">外部就职经历</div>
					<a-table
						v-if="externalRows.length"
						class="arco-emp-compact-table"
						:columns="externalColumns"
						:data="externalRows"
						:pagination="false"
						:bordered="false"
						size="small"
						row-key="_idx"
					/>
					<div v-else class="arco-emp-mini-empty">暂无外部经历</div>
				</div>
				<div class="arco-emp-work-block">
					<div class="arco-emp-work-label">内部工作经历</div>
					<a-table
						v-if="internalRows.length"
						class="arco-emp-compact-table"
						:columns="internalColumns"
						:data="internalRows"
						:pagination="false"
						:bordered="false"
						size="small"
						row-key="_idx"
					/>
					<div v-else class="arco-emp-mini-empty">暂无内部经历</div>
				</div>
			</div>
		</section>

		<section class="arco-emp-section-card">
			<div class="arco-emp-section-head">
				<h3 class="arco-emp-section-title">个人资料摘要</h3>
			</div>
			<div class="arco-emp-section-body">
				<div class="arco-emp-info-grid cols-4">
					<div v-for="item in personalItems" :key="item.label" class="arco-emp-info-item">
						<div class="arco-emp-info-label">{{ item.label }}</div>
						<div class="arco-emp-info-value">{{ item.value }}</div>
					</div>
				</div>
			</div>
		</section>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	state: {
		type: Object,
		required: true,
	},
});

defineEmits(["navigate"]);

function dash(v) {
	return v === 0 || v ? v : "—";
}

const statusMap = {
	Active: { label: "在职", color: "green" },
	Inactive: { label: "停用", color: "orangered" },
	Suspended: { label: "停职", color: "red" },
	Left: { label: "离职", color: "gray" },
};

const statusLabel = computed(() => statusMap[props.state.status]?.label || props.state.status || "—");
const statusColor = computed(() => statusMap[props.state.status]?.color || "gray");

const maritalMap = {
	Single: "未婚",
	Married: "已婚",
	Divorced: "离异",
	Widowed: "丧偶",
};

const maritalLabel = computed(
	() => maritalMap[props.state.marital_status] || props.state.marital_status || "—"
);

const maskPassport = computed(() => {
	const raw = String(props.state.passport_number || "").trim();
	if (!raw) return "—";
	if (raw.length <= 4) return "****";
	return `${"*".repeat(Math.max(4, raw.length - 4))}${raw.slice(-4)}`;
});

const bioPreview = computed(() => {
	const raw = String(props.state.bio_text || "").trim();
	if (!raw) return "";
	return raw.length > 220 ? `${raw.slice(0, 220)}…` : raw;
});

const basicItems = computed(() => [
	{ label: "全名", value: dash(props.state.employee_name) },
	{ label: "入职日期", value: dash(props.state.date_of_joining) },
	{ label: "状态", value: statusLabel.value, tag: true, tagColor: statusColor.value },
	{ label: "公司", value: dash(props.state.company) },
	{ label: "部门", value: dash(props.state.department) },
	{ label: "职位", value: dash(props.state.designation) },
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

const educationColumns = [
	{ title: "学校", dataIndex: "school_univ", ellipsis: true },
	{ title: "专业/资格", dataIndex: "qualification" },
	{ title: "学历", dataIndex: "level", width: 100 },
	{ title: "毕业年份", dataIndex: "year_of_passing", width: 100 },
];

const educationRows = computed(() =>
	(props.state.education || []).map((row, i) => ({
		_idx: row.name || i,
		school_univ: row.school_univ || "—",
		qualification: row.qualification || row.maj_opt_subj || "—",
		level: row.level || "—",
		year_of_passing: row.year_of_passing || "—",
	}))
);

const externalColumns = [
	{ title: "公司", dataIndex: "company_name", ellipsis: true },
	{ title: "职位", dataIndex: "designation" },
	{ title: "时长", dataIndex: "total_experience", width: 120 },
];

const externalRows = computed(() =>
	(props.state.external_work_history || []).map((row, i) => ({
		_idx: row.name || i,
		company_name: row.company_name || "—",
		designation: row.designation || "—",
		total_experience: row.total_experience || "—",
	}))
);

const internalColumns = [
	{ title: "部门", dataIndex: "department", ellipsis: true },
	{ title: "职位", dataIndex: "designation" },
	{ title: "开始", dataIndex: "from_date", width: 110 },
	{ title: "结束", dataIndex: "to_date", width: 110 },
];

const internalRows = computed(() =>
	(props.state.internal_work_history || []).map((row, i) => ({
		_idx: row.name || i,
		department: row.department || "—",
		designation: row.designation || "—",
		from_date: row.from_date || "—",
		to_date: row.to_date || "—",
	}))
);
</script>
