<template>
	<div class="arco-org-ui contract-templates">
		<div class="ct-toolbar">
			<a-input
				v-model="keyword"
				class="ct-search"
				allow-clear
				placeholder="搜索合同类型"
				@press-enter="applyFilter"
				@clear="applyFilter"
			>
				<template #prefix><icon-search /></template>
			</a-input>

			<div class="ct-toolbar-actions">
				<a-link class="ct-help" @click="onHelp">如何使用电子合同？使用帮助戳这里</a-link>
				<a-button type="primary" @click="onAddType">
					<template #icon><icon-plus /></template>
					新增合同类型
				</a-button>
				<a-button @click="onEditGroups">编辑分组</a-button>
			</div>
		</div>

		<a-card :bordered="false" class="ct-card">
			<div class="ct-group-head">
				<div class="ct-group-title">
					<span class="ct-group-bar" />
					<span>合同/协议</span>
					<span class="ct-group-count">({{ filteredRows.length }})</span>
				</div>
				<div class="ct-group-ops">
					<a-dropdown trigger="click" @select="onSort">
						<a-button type="text" size="small">
							排序
							<template #icon><icon-swap /></template>
						</a-button>
						<template #content>
							<a-doption value="name">按名称</a-doption>
							<a-doption value="seal">按印章</a-doption>
						</template>
					</a-dropdown>
					<a-button type="text" size="small" @click="collapsed = !collapsed">
						{{ collapsed ? "展开" : "收起" }}
						<template #icon>
							<icon-up v-if="!collapsed" />
							<icon-down v-else />
						</template>
					</a-button>
				</div>
			</div>

			<div v-show="!collapsed" class="ct-table-wrap">
				<a-table
					:columns="columns"
					:data="filteredRows"
					:pagination="false"
					:bordered="false"
					row-key="id"
					:scroll="{ x: 980 }"
				>
					<template #typeName="{ record }">
						<div class="ct-type">
							<div class="ct-type-name">{{ record.name }}</div>
							<div class="ct-type-desc">{{ record.desc }}</div>
						</div>
					</template>

					<template #seal="{ record }">
						<span :class="['ct-seal', { 'is-empty': !record.seal || record.seal === '无' }]">
							{{ record.seal || "无" }}
						</span>
					</template>

					<template #party="{ record }">
						<span class="ct-party">{{ record.party }}</span>
					</template>

					<template #ops="{ record }">
						<div class="ct-row-ops">
							<a-dropdown trigger="click" @select="(key) => onStartSign(record, key)">
								<a-link>
									发起签署
									<icon-down />
								</a-link>
								<template #content>
									<a-doption value="single">单人签署</a-doption>
									<a-doption value="batch">批量签署</a-doption>
								</template>
							</a-dropdown>
							<a-dropdown trigger="click" @select="(key) => onSettings(record, key)">
								<a-link>
									设置
									<icon-down />
								</a-link>
								<template #content>
									<a-doption value="edit">编辑模板</a-doption>
									<a-doption value="seal">配置印章</a-doption>
									<a-doption value="party">签署方设置</a-doption>
								</template>
							</a-dropdown>
							<a-dropdown trigger="click" @select="(key) => onMore(record, key)">
								<a-button type="text" size="mini" class="ct-more-btn">
									<template #icon><icon-more /></template>
								</a-button>
								<template #content>
									<a-doption value="copy">复制</a-doption>
									<a-doption value="disable">停用</a-doption>
									<a-doption value="delete" class="ct-danger">删除</a-doption>
								</template>
							</a-dropdown>
						</div>
					</template>
				</a-table>
			</div>
		</a-card>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import {
	IconDown,
	IconMore,
	IconPlus,
	IconSearch,
	IconSwap,
	IconUp,
} from "@arco-design/web-vue/es/icon";

const keyword = ref("");
const collapsed = ref(false);
const sortBy = ref("name");

const rows = ref([
	{
		id: "1",
		name: "依然集团-劳动合同",
		desc: "适用于全职员工签订固定期限劳动合同",
		seal: "深圳市依然电商科技有限公司公章",
		party: "企业-员工双方签署",
	},
	{
		id: "2",
		name: "依然杭州-劳动合同",
		desc: "适用于杭州分公司全职员工签订固定期限劳动合同",
		seal: "依然杭州公章",
		party: "企业-员工双方签署",
	},
	{
		id: "3",
		name: "依然集团-保密协议",
		desc: "适用于全职员工入职时签订保密义务",
		seal: "深圳市依然电商科技有限公司公章",
		party: "企业-员工双方签署",
	},
	{
		id: "4",
		name: "依然杭州分公司-保密协议",
		desc: "适用于杭州分公司员工入职签订保密义务",
		seal: "依然杭州公章",
		party: "企业-员工双方签署",
	},
	{
		id: "5",
		name: "依然集团-薪酬确认书",
		desc: "适用于员工薪酬调整或入职薪酬确认",
		seal: "无",
		party: "员工单方签署",
	},
	{
		id: "6",
		name: "依然集团-竞争性兼职禁止协议",
		desc: "适用于关键岗位员工兼职限制约定",
		seal: "深圳市依然电商科技有限公司公章",
		party: "企业-员工双方签署",
	},
	{
		id: "7",
		name: "依然集团-实习协议",
		desc: "适用于在校实习生签订实习约定",
		seal: "深圳市依然电商科技有限公司公章",
		party: "企业-员工双方签署",
	},
	{
		id: "8",
		name: "依然集团-离职证明",
		desc: "适用于员工离职后开具证明文件",
		seal: "深圳市依然电商科技有限公司公章",
		party: "企业单方签署",
	},
]);

const columns = [
	{ title: "类型名称", slotName: "typeName", width: 320 },
	{ title: "加盖印章", slotName: "seal", width: 260 },
	{ title: "盖章方", slotName: "party", width: 160 },
	{ title: "", slotName: "ops", width: 220, align: "right" },
];

const filteredRows = computed(() => {
	const q = keyword.value.trim().toLowerCase();
	let list = rows.value.slice();
	if (q) {
		list = list.filter(
			(row) =>
				row.name.toLowerCase().includes(q) ||
				row.desc.toLowerCase().includes(q) ||
				String(row.seal || "").toLowerCase().includes(q)
		);
	}
	if (sortBy.value === "seal") {
		list.sort((a, b) => String(a.seal || "").localeCompare(String(b.seal || ""), "zh"));
	} else {
		list.sort((a, b) => a.name.localeCompare(b.name, "zh"));
	}
	return list;
});

function applyFilter() {
	/* computed reacts to keyword */
}

function onHelp() {
	Message.info("电子合同使用帮助即将开放");
}

function onAddType() {
	Message.success("新增合同类型（示意）");
}

function onEditGroups() {
	Message.info("编辑分组（示意）");
}

function onSort(key) {
	sortBy.value = key;
}

function onStartSign(record, mode) {
	Message.success(`${record.name} · ${mode === "batch" ? "批量签署" : "单人签署"}`);
	try {
		window.frappe?.set_route?.("contract-signing-pending");
	} catch (e) {
		/* ignore */
	}
}

function onSettings(record, key) {
	const map = { edit: "编辑模板", seal: "配置印章", party: "签署方设置" };
	Message.info(`${record.name} · ${map[key] || key}`);
}

function onMore(record, key) {
	if (key === "copy") {
		Message.success(`已复制：${record.name}`);
		return;
	}
	if (key === "disable") {
		Message.warning(`已停用：${record.name}`);
		return;
	}
	if (key === "delete") {
		Message.error(`删除：${record.name}（示意）`);
	}
}
</script>
