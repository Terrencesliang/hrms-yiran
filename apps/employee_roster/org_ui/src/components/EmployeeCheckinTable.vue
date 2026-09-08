<template>
	<a-table
		class="hr-checkin-arco-table"
		:columns="columns"
		:data="sortedRows"
		:pagination="false"
		:loading="state.loading"
		:scroll="{ x: 1180 }"
		:bordered="false"
		row-key="name"
		@row-click="openRow"
		@sorter-change="changeSort"
	>
		<template #employee="{ record }">
			<div class="hr-checkin-employee">
				<a-avatar :size="32" :style="avatarStyle(record)">
					{{ employeeInitial(record) }}
				</a-avatar>
				<div class="hr-checkin-employee-copy">
					<strong>{{ record.employee_name || "未命名员工" }}</strong>
					<span>{{ record.employee || "—" }}</span>
				</div>
			</div>
		</template>

		<template #date="{ record }">
			<div class="hr-checkin-date">
				<strong>{{ formatDate(record.time) }}</strong>
				<span>{{ formatWeekday(record.time) }}</span>
			</div>
		</template>

		<template #clock="{ record }">
			<span class="hr-checkin-clock">{{ formatClock(record.time) }}</span>
		</template>

		<template #action="{ record }">
			<a-tag :color="record.log_type === 'OUT' ? 'orangered' : 'green'" size="small">
				{{ logTypeLabel(record.log_type) }}
			</a-tag>
		</template>

		<template #checkinType="{ record }">
			<a-tag :color="checkinType(record) === '外勤打卡' ? 'arcoblue' : 'gray'" size="small">
				{{ checkinType(record) }}
			</a-tag>
		</template>

		<template #result="{ record }">
			<a-tag :color="resultColor(record.day_attendance_result)" size="small">
				{{ record.day_attendance_result || "待计算" }}
			</a-tag>
		</template>

		<template #workHours="{ record }">
			<span class="hr-checkin-muted">
				{{ formatHours(record.day_work_hours) }}
			</span>
		</template>

		<template #source="{ record }">
			<div class="hr-checkin-source">
				<span>{{ sourceLabel(record) }}</span>
				<small v-if="hasCoordinates(record)">已记录定位</small>
			</div>
		</template>

		<template #empty>
			<a-empty description="当前筛选条件下暂无打卡记录" />
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
	{ title: "员工", dataIndex: "employee", slotName: "employee", width: 190, fixed: "left" },
	{
		title: "打卡日期",
		dataIndex: "time",
		slotName: "date",
		width: 160,
		sortable: { sortDirections: ["ascend", "descend"] },
		defaultSortOrder: "descend",
	},
	{ title: "打卡时间", dataIndex: "time", slotName: "clock", width: 116 },
	{ title: "打卡动作", dataIndex: "log_type", slotName: "action", width: 120 },
	{ title: "打卡方式", dataIndex: "checkin_type", slotName: "checkinType", width: 120 },
	{ title: "日出勤结果", dataIndex: "day_attendance_result", slotName: "result", width: 120 },
	{ title: "日出勤时长", dataIndex: "day_work_hours", slotName: "workHours", width: 120 },
	{ title: "打卡来源", dataIndex: "device_id", slotName: "source", width: 180 },
];

const sortedRows = computed(() => {
	const direction = props.state.sortOrder === "asc" ? 1 : -1;
	return [...(props.state.rows || [])].sort((a, b) =>
		String(a.time || "").localeCompare(String(b.time || "")) * direction
	);
});

function parseDateTime(value) {
	const text = String(value || "");
	const [date = "", time = ""] = text.split(" ");
	return { date, time: time.slice(0, 8) };
}

function formatDate(value) {
	const { date } = parseDateTime(value);
	const [year, month, day] = date.split("-");
	return year && month && day ? `${year}年${month}月${day}日` : "—";
}

function formatWeekday(value) {
	const { date } = parseDateTime(value);
	if (!date) return "";
	const weekday = new Date(`${date}T00:00:00`).getDay();
	return ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"][weekday];
}

function formatClock(value) {
	return parseDateTime(value).time || "—";
}

function logTypeLabel(value) {
	if (String(value || "").toUpperCase() === "IN") return "上班打卡";
	if (String(value || "").toUpperCase() === "OUT") return "下班打卡";
	return value || "未设置";
}

function checkinType(record) {
	return record.checkin_type || "办公地点";
}

function resultColor(result) {
	return { 出勤: "green", 迟到: "orange", 缺卡: "red" }[result] || "gray";
}

function formatHours(value) {
	if (value === null || value === undefined || value === "") return "—";
	return `${Number(value).toFixed(2)} 小时`;
}

function hasCoordinates(record) {
	return Boolean(Number(record.latitude) || Number(record.longitude));
}

function sourceLabel(record) {
	if (record.device_id) return record.device_id;
	if (hasCoordinates(record)) return "移动端定位";
	return "手动录入";
}

function employeeInitial(record) {
	const name = String(record.employee_name || record.employee || "员");
	return name.slice(-1);
}

function avatarStyle(record) {
	const code = String(record.employee || "");
	const palettes = [
		["#E8F3FF", "#165DFF"],
		["#E8FFEA", "#00B42A"],
		["#F5E8FF", "#722ED1"],
		["#FFF7E8", "#FF7D00"],
	];
	const index = [...code].reduce((sum, char) => sum + char.charCodeAt(0), 0) % palettes.length;
	return { backgroundColor: palettes[index][0], color: palettes[index][1] };
}

function openRow(record) {
	props.handlers?.onOpen?.(record);
}

function changeSort(dataIndex, direction) {
	if (dataIndex !== "time") return;
	props.handlers?.onSort?.(direction === "ascend" ? "asc" : "desc");
}
</script>

<style scoped>
.hr-checkin-arco-table {
	width: 100%;
}

.hr-checkin-arco-table :deep(.arco-table-th) {
	height: 44px;
	background: var(--color-fill-1);
	color: var(--color-text-2);
	font-size: 13px;
	font-weight: 500;
}

.hr-checkin-arco-table :deep(.arco-table-td) {
	height: 64px;
	border-bottom-color: var(--color-border-1);
	font-size: 13px;
}

.hr-checkin-arco-table :deep(.arco-table-tr:not(.arco-table-tr-empty):hover .arco-table-td) {
	background: var(--color-fill-1);
	cursor: pointer;
}

.hr-checkin-employee,
.hr-checkin-employee-copy,
.hr-checkin-date,
.hr-checkin-source {
	display: flex;
}

.hr-checkin-employee {
	align-items: center;
	gap: 10px;
}

.hr-checkin-employee-copy,
.hr-checkin-date,
.hr-checkin-source {
	flex-direction: column;
	gap: 3px;
}

.hr-checkin-employee-copy strong,
.hr-checkin-date strong {
	color: var(--color-text-1);
	font-size: 13px;
	font-weight: 500;
}

.hr-checkin-employee-copy span,
.hr-checkin-date span,
.hr-checkin-source small,
.hr-checkin-muted {
	color: var(--color-text-3);
	font-size: 12px;
}

.hr-checkin-clock {
	color: rgb(var(--primary-6));
	font-variant-numeric: tabular-nums;
	font-weight: 600;
}

.hr-checkin-source > span {
	max-width: 170px;
	overflow: hidden;
	color: var(--color-text-2);
	text-overflow: ellipsis;
	white-space: nowrap;
}
</style>
