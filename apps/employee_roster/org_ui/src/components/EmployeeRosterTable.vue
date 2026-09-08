<template>
	<a-table
		class="hr-roster-arco-table"
		:columns="columns"
		:data="sortedRows"
		:pagination="false"
		:loading="state.loading"
		:scroll="{ x: 1260 }"
		:bordered="false"
		row-key="name"
		@row-click="openRow"
		@sorter-change="changeSort"
	>
		<template #employee="{ record }">
			<div class="hr-roster-employee">
				<a-avatar :size="36" :image-url="record.image || undefined" :style="avatarStyle(record)">
					{{ employeeInitial(record) }}
				</a-avatar>
				<div class="hr-roster-copy">
					<strong>{{ record.employee_name || "未命名员工" }}</strong>
					<span>{{ record.name || "—" }}</span>
				</div>
			</div>
		</template>

		<template #position="{ record }">
			<div class="hr-roster-copy">
				<strong>{{ localizePosition(record.designation) }}</strong>
				<span>{{ localizeOrganization(record.department) || "未分配部门" }}</span>
			</div>
		</template>

		<template #group="{ record }">
			<span class="hr-roster-primary-text">{{ localizeOrganization(record.group_name) || "—" }}</span>
		</template>

		<template #branch="{ record }">
			<span class="hr-roster-primary-text">{{ record.branch || "—" }}</span>
		</template>

		<template #employmentType="{ record }">
			<a-tag :color="employmentTypeColor(displayEmploymentType(record))" size="small">
				{{ employmentTypeLabel(displayEmploymentType(record)) }}
			</a-tag>
		</template>

		<template #joiningDate="{ record }">
			<span class="hr-roster-date">{{ formatDate(record.date_of_joining) }}</span>
		</template>

		<template #contact="{ record }">
			<div class="hr-roster-copy hr-roster-contact">
				<strong>{{ record.cell_number || "未填写手机号" }}</strong>
				<span>{{ record.company_email || "未填写公司邮箱" }}</span>
			</div>
		</template>

		<template #status="{ record }">
			<a-tag :color="statusColor(record.status)" size="small">
				<span class="hr-roster-status-dot" />
				{{ statusLabel(record.status) }}
			</a-tag>
		</template>

		<template #empty>
			<a-empty description="当前筛选条件下暂无员工记录" />
		</template>
	</a-table>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	state: { type: Object, required: true },
	handlers: { type: Object, default: () => ({}) },
});

const columns = [
	{
		title: "员工信息",
		dataIndex: "employee_name",
		slotName: "employee",
		width: 210,
		fixed: "left",
		sortable: { sortDirections: ["ascend", "descend"] },
		defaultSortOrder: "ascend",
	},
	{ title: "任职信息", dataIndex: "designation", slotName: "position", width: 260 },
	{ title: "组别", dataIndex: "group_name", slotName: "group", width: 130 },
	{ title: "分支机构", dataIndex: "branch", slotName: "branch", width: 130 },
	{ title: "雇佣类型", dataIndex: "employment_type", slotName: "employmentType", width: 112 },
	{
		title: "入职日期",
		dataIndex: "date_of_joining",
		slotName: "joiningDate",
		width: 150,
		sortable: { sortDirections: ["ascend", "descend"] },
	},
	{ title: "联系方式", dataIndex: "cell_number", slotName: "contact", width: 205 },
	{ title: "状态", dataIndex: "status", slotName: "status", width: 100, fixed: "right" },
];

const sortedRows = computed(() => {
	const field = props.state.sortBy || "employee_name";
	const direction = props.state.sortOrder === "desc" ? -1 : 1;
	return [...(props.state.rows || [])].sort((left, right) => {
		const a = String(left[field] || "");
		const b = String(right[field] || "");
		return a.localeCompare(b, "zh-CN", { numeric: true }) * direction;
	});
});

function employeeInitial(record) {
	return String(record.employee_name || record.name || "员").slice(-1);
}

function avatarStyle(record) {
	if (record.image) return undefined;
	const palettes = [
		["#E8F3FF", "#165DFF"],
		["#E8FFEA", "#00B42A"],
		["#F5E8FF", "#722ED1"],
		["#FFF7E8", "#FF7D00"],
	];
	const code = String(record.name || record.employee_name || "");
	const index = [...code].reduce((sum, char) => sum + char.charCodeAt(0), 0) % palettes.length;
	return { backgroundColor: palettes[index][0], color: palettes[index][1] };
}

function localizePosition(value) {
	if (!value) return "未设置职位";
	return String(value)
		.replace(/HRBP/gi, "人力资源业务伙伴")
		.replace(/ITBP/gi, "信息技术业务伙伴")
		.replace(/FBP/gi, "财务业务伙伴")
		.replace(/BP/gi, "业务伙伴")
		.replace(/\bVP\b/gi, "副总裁")
		.replace(/AI/gi, "人工智能");
}

function localizeOrganization(value) {
	if (!value) return "";
	return String(value)
		.replace(/ITBP/gi, "信息技术业务伙伴")
		.replace(/FBP/gi, "财务业务伙伴")
		.replace(/HRBP/gi, "人力资源业务伙伴")
		.replace(/KA/gi, "重点客户")
		.replace(/AI/gi, "人工智能");
}

function statusLabel(value) {
	return {
		Active: "在职",
		Inactive: "停用",
		Suspended: "停职",
		Left: "已离职",
	}[value] || value || "未设置";
}

function statusColor(value) {
	return { Active: "green", Inactive: "gray", Suspended: "orange", Left: "red" }[value] || "gray";
}

function employmentTypeLabel(value) {
	return {
		"Full-time": "全职",
		"Part-time": "兼职",
		Intern: "实习生",
		Probation: "试用期",
		Contract: "合同工",
		Apprentice: "见习生",
	}[value] || value || "未设置";
}

function displayEmploymentType(record) {
	if (record.employment_type) return record.employment_type;
	if (record.designation === "实习生") return "Intern";
	if (record.status === "Active") return "Full-time";
	return "";
}

function employmentTypeColor(value) {
	return {
		"Full-time": "arcoblue",
		"Part-time": "purple",
		Intern: "purple",
		Probation: "orange",
		Contract: "cyan",
		Apprentice: "green",
	}[value] || "gray";
}

function formatDate(value) {
	const [year, month, day] = String(value || "").slice(0, 10).split("-");
	return year && month && day ? `${year}年${month}月${day}日` : "—";
}

function openRow(record) {
	props.handlers?.onOpen?.(record);
}

function changeSort(dataIndex, direction) {
	if (!direction || !["employee_name", "date_of_joining"].includes(dataIndex)) return;
	props.handlers?.onSort?.(dataIndex, direction === "ascend" ? "asc" : "desc");
}
</script>

<style scoped>
.hr-roster-arco-table {
	width: 100%;
}

.hr-roster-arco-table :deep(.arco-table-th) {
	height: 44px;
	background: var(--color-fill-1);
	color: var(--color-text-2);
	font-size: 13px;
	font-weight: 500;
}

.hr-roster-arco-table :deep(.arco-table-td) {
	height: 66px;
	border-bottom-color: var(--color-border-1);
	font-size: 13px;
}

.hr-roster-arco-table :deep(.arco-table-tr:not(.arco-table-tr-empty):hover .arco-table-td) {
	background: var(--color-fill-1);
	cursor: pointer;
}

.hr-roster-employee,
.hr-roster-copy {
	display: flex;
}

.hr-roster-employee {
	align-items: center;
	gap: 12px;
}

.hr-roster-copy {
	min-width: 0;
	flex-direction: column;
	gap: 4px;
}

.hr-roster-copy strong,
.hr-roster-primary-text,
.hr-roster-date {
	color: var(--color-text-1);
	font-size: 13px;
	font-weight: 500;
}

.hr-roster-copy span {
	max-width: 235px;
	overflow: hidden;
	color: var(--color-text-3);
	font-size: 12px;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.hr-roster-contact strong {
	font-weight: 400;
}

.hr-roster-date {
	font-variant-numeric: tabular-nums;
	white-space: nowrap;
}

.hr-roster-status-dot {
	display: inline-block;
	width: 6px;
	height: 6px;
	margin-right: 3px;
	border-radius: 50%;
	background: currentColor;
}
</style>
