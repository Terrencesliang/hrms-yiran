<template>
	<div class="arco-org-ui contract-archive">
		<ContractActionToolbar title="合同档案库" description="查询与管理员工合同归档记录，支持到期预警与续签跟踪">
			<template #filters>
				<a-input
					v-model="keyword"
					class="ca-search"
					allow-clear
					placeholder="搜索员工 / 合同类型"
					@press-enter="applyFilter"
					@clear="applyFilter"
				>
					<template #prefix><icon-search /></template>
				</a-input>
				<a-select
					v-model="department"
					class="ca-filter"
					allow-clear
					placeholder="部门"
					:options="deptOptions"
				/>
				<a-select
					v-model="contractType"
					class="ca-filter"
					allow-clear
					placeholder="合同类型"
					:options="typeOptions"
				/>
				<a-select
					v-model="archiveStatus"
					class="ca-filter"
					allow-clear
					placeholder="归档状态"
					:options="statusOptions"
				/>
				<a-range-picker v-model="expireRange" class="ca-range" />
			</template>
		</ContractActionToolbar>

		<a-card :bordered="false" class="ca-stats-card">
			<a-row :gutter="16">
				<a-col v-for="item in stats" :key="item.key" :xs="12" :sm="6">
					<button
						type="button"
						class="ca-stat"
						:class="{ 'is-active': statusFilter === item.key }"
						@click="statusFilter = statusFilter === item.key ? '' : item.key"
					>
						<div class="ca-stat-label">{{ item.label }}</div>
						<div class="ca-stat-value" :class="{ 'is-alert': item.alert }">{{ item.value }}</div>
					</button>
				</a-col>
			</a-row>
		</a-card>

		<a-card :bordered="false" class="ca-table-card">
			<template #title>合同档案</template>
			<a-table
				:columns="columns"
				:data="filteredRows"
				:pagination="{ pageSize: 10 }"
				:bordered="false"
				row-key="id"
				:scroll="{ x: 1100 }"
				@row-click="openDetail"
			>
				<template #employee="{ record }">
					<div class="ca-emp">{{ record.employee }}</div>
					<div class="ca-sub">{{ record.employeeNo }}</div>
				</template>
				<template #period="{ record }">
					<div>{{ record.effectiveFrom }} ~ {{ record.expireAt }}</div>
				</template>
				<template #status="{ record }">
					<a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
				</template>
				<template #ops="{ record }">
					<div class="ca-ops" @click.stop>
						<a-link @click="openDetail(record)">预览</a-link>
						<a-link @click="onDownload(record)">下载</a-link>
						<a-link @click="onRenew(record)">续签</a-link>
					</div>
				</template>
			</a-table>
		</a-card>

		<a-drawer
			v-model:visible="drawerVisible"
			:width="440"
			unmount-on-close
			:title="active ? `${active.employee} · ${active.type}` : '合同详情'"
		>
			<template v-if="active">
				<a-descriptions :column="1" size="large" bordered>
					<a-descriptions-item label="工号">{{ active.employeeNo }}</a-descriptions-item>
					<a-descriptions-item label="部门">{{ active.department }}</a-descriptions-item>
					<a-descriptions-item label="合同类型">{{ active.type }}</a-descriptions-item>
					<a-descriptions-item label="签署完成日">{{ active.signedAt }}</a-descriptions-item>
					<a-descriptions-item label="生效 / 到期">
						{{ active.effectiveFrom }} ~ {{ active.expireAt }}
					</a-descriptions-item>
					<a-descriptions-item label="状态">{{ active.status }}</a-descriptions-item>
				</a-descriptions>

				<div class="ca-drawer-title">附件文件</div>
				<a-list :bordered="false" size="small">
					<a-list-item v-for="file in active.files" :key="file.id">
						<a-list-item-meta :title="file.name" :description="file.size" />
						<template #actions>
							<a-link @click="onPreviewFile(file)">预览</a-link>
						</template>
					</a-list-item>
				</a-list>
			</template>
		</a-drawer>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import { IconSearch } from "@arco-design/web-vue/es/icon";
import ContractActionToolbar from "./ContractActionToolbar.vue";

const keyword = ref("");
const department = ref("");
const contractType = ref("");
const archiveStatus = ref("");
const expireRange = ref([]);
const statusFilter = ref("");
const drawerVisible = ref(false);
const active = ref(null);

const deptOptions = [
	{ label: "人事行政部", value: "人事行政部" },
	{ label: "技术中心", value: "技术中心" },
	{ label: "电商运营部", value: "电商运营部" },
];

const typeOptions = [
	{ label: "劳动合同", value: "劳动合同" },
	{ label: "保密协议", value: "保密协议" },
	{ label: "实习协议", value: "实习协议" },
];

const statusOptions = [
	{ label: "在职有效", value: "在职有效" },
	{ label: "30天内到期", value: "30天内到期" },
	{ label: "已过期", value: "已过期" },
	{ label: "已归档", value: "已归档" },
];

const stats = [
	{ key: "active", label: "在职有效", value: 3, alert: false },
	{ key: "soon", label: "30天内到期", value: 1, alert: true },
	{ key: "expired", label: "已过期", value: 1, alert: true },
	{ key: "archived", label: "已归档", value: 1, alert: false },
];

const rows = ref([
	{
		id: "1",
		employee: "陈七",
		employeeNo: "YR10021",
		department: "技术中心",
		type: "劳动合同",
		signedAt: "2026-08-12",
		effectiveFrom: "2026-08-12",
		expireAt: "2029-08-11",
		status: "在职有效",
		bucket: "active",
		files: [
			{ id: "f1", name: "劳动合同.pdf", size: "1.2 MB" },
			{ id: "f2", name: "签署回执.pdf", size: "240 KB" },
		],
	},
	{
		id: "2",
		employee: "孙八",
		employeeNo: "YR10088",
		department: "电商运营部",
		type: "实习协议",
		signedAt: "2026-07-21",
		effectiveFrom: "2026-07-21",
		expireAt: "2026-09-30",
		status: "30天内到期",
		bucket: "soon",
		files: [{ id: "f1", name: "实习协议.pdf", size: "860 KB" }],
	},
	{
		id: "3",
		employee: "周十",
		employeeNo: "YR09011",
		department: "人事行政部",
		type: "劳动合同",
		signedAt: "2023-03-01",
		effectiveFrom: "2023-03-01",
		expireAt: "2026-02-28",
		status: "已过期",
		bucket: "expired",
		files: [{ id: "f1", name: "劳动合同.pdf", size: "1.1 MB" }],
	},
	{
		id: "4",
		employee: "吴十一",
		employeeNo: "YR08002",
		department: "技术中心",
		type: "保密协议",
		signedAt: "2024-01-10",
		effectiveFrom: "2024-01-10",
		expireAt: "2027-01-09",
		status: "已归档",
		bucket: "archived",
		files: [{ id: "f1", name: "保密协议.pdf", size: "520 KB" }],
	},
	{
		id: "5",
		employee: "郑十二",
		employeeNo: "YR10055",
		department: "电商运营部",
		type: "劳动合同",
		signedAt: "2025-05-08",
		effectiveFrom: "2025-05-08",
		expireAt: "2028-05-07",
		status: "在职有效",
		bucket: "active",
		files: [{ id: "f1", name: "劳动合同.pdf", size: "980 KB" }],
	},
	{
		id: "6",
		employee: "冯十三",
		employeeNo: "YR10060",
		department: "人事行政部",
		type: "保密协议",
		signedAt: "2025-11-02",
		effectiveFrom: "2025-11-02",
		expireAt: "2028-11-01",
		status: "在职有效",
		bucket: "active",
		files: [{ id: "f1", name: "保密协议.pdf", size: "410 KB" }],
	},
]);

const columns = [
	{ title: "员工", slotName: "employee", width: 140 },
	{ title: "部门", dataIndex: "department", width: 120 },
	{ title: "合同类型", dataIndex: "type", width: 120 },
	{ title: "签署完成日", dataIndex: "signedAt", width: 120 },
	{ title: "生效 / 到期", slotName: "period", width: 200 },
	{ title: "状态", slotName: "status", width: 110 },
	{ title: "附件", dataIndex: "fileCount", width: 80 },
	{ title: "操作", slotName: "ops", width: 180, fixed: "right" },
];

const tableRows = computed(() =>
	rows.value.map((row) => ({ ...row, fileCount: row.files?.length || 0 }))
);

const filteredRows = computed(() => {
	let list = tableRows.value.slice();
	const q = keyword.value.trim().toLowerCase();
	if (q) {
		list = list.filter(
			(row) =>
				row.employee.toLowerCase().includes(q) ||
				row.employeeNo.toLowerCase().includes(q) ||
				row.type.toLowerCase().includes(q)
		);
	}
	if (department.value) list = list.filter((row) => row.department === department.value);
	if (contractType.value) list = list.filter((row) => row.type === contractType.value);
	if (archiveStatus.value) list = list.filter((row) => row.status === archiveStatus.value);
	if (statusFilter.value) list = list.filter((row) => row.bucket === statusFilter.value);
	return list;
});

function applyFilter() {
	/* computed */
}

function statusColor(status) {
	if (status === "在职有效") return "green";
	if (status === "30天内到期") return "orangered";
	if (status === "已过期") return "red";
	return "gray";
}

function openDetail(record) {
	active.value = record;
	drawerVisible.value = true;
}

function onDownload(record) {
	Message.info(`下载：${record.employee} · ${record.type}（示意）`);
}

function onPreviewFile(file) {
	Message.info(`预览 ${file.name}`);
}

function onRenew(record) {
	Message.success(`续签：${record.employee}（示意）`);
	try {
		window.frappe?.set_route?.(["contract-templates"]);
	} catch (e) {
		/* ignore */
	}
}
</script>
