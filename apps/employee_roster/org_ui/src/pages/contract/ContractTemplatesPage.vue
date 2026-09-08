<template>
	<div class="arco-org-ui contract-templates">
		<div class="ct-toolbar">
			<a-input
				v-model="keyword"
				class="ct-search"
				allow-clear
				placeholder="搜索合同类型"
			>
				<template #prefix><icon-search /></template>
			</a-input>

			<div class="ct-toolbar-actions">
				<a-button :loading="loading" @click="loadTemplates">刷新</a-button>
			</div>
		</div>

		<a-alert
			v-if="errorMessage"
			class="ct-test-alert"
			type="warning"
			show-icon
			:title="configurationMissing ? '腾讯电子签尚未配置' : '腾讯电子签模板加载失败'"
		>
			{{ errorMessage }}
		</a-alert>

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
					:loading="loading"
					:pagination="false"
					:bordered="false"
					row-key="id"
					:scroll="{ x: 980 }"
				>
					<template #empty>
						<a-empty :description="errorMessage ? '模板暂不可用' : '尚未配置可用的腾讯电子签模板'">
							<a-button type="primary" @click="loadTemplates">重新加载</a-button>
						</a-empty>
					</template>
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
							<a-link @click="onStartSign(record, 'single')">发起签署</a-link>
							<a-dropdown trigger="click" @select="(key) => onStartSign(record, key)">
								<a-link>
									更多
									<icon-down />
								</a-link>
								<template #content>
									<a-doption value="single">单人签署</a-doption>
									<a-doption value="batch">批量签署</a-doption>
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
import { computed, onMounted, ref } from "vue";
import { IconDown, IconSearch, IconSwap, IconUp } from "@arco-design/web-vue/es/icon";
import { getTemplates } from "../../api/contract.js";

const keyword = ref("");
const collapsed = ref(false);
const sortBy = ref("name");
const loading = ref(false);
const errorMessage = ref("");
const configurationMissing = ref(false);
const rows = ref([]);

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

function normalizeTemplate(row, index) {
	return {
		id: String(row?.id || row?.template_id || row?.name || index),
		name: row?.template_name || row?.title || row?.name || `未命名模板 ${index + 1}`,
		desc: row?.description || row?.desc || "",
		seal: row?.seal_name || row?.seal || (row?.seal_id ? "已配置企业印章" : "无"),
		party: row?.signing_party || row?.party || "未配置",
	};
}

async function loadTemplates() {
	loading.value = true;
	errorMessage.value = "";
	configurationMissing.value = false;
	try {
		const result = await getTemplates();
		const list = Array.isArray(result) ? result : result?.templates || result?.data || [];
		rows.value = Array.isArray(list) ? list.map(normalizeTemplate) : [];
		if (result?.configuration?.configured === false) {
			configurationMissing.value = true;
			errorMessage.value = result.configuration.message || "请先完成腾讯电子签服务端配置";
		}
	} catch (error) {
		console.warn("[contract-templates] load failed", error);
		rows.value = [];
		errorMessage.value = "无法从后端获取模板";
	} finally {
		loading.value = false;
	}
}

function onSort(key) {
	sortBy.value = key;
}

function onStartSign(record, mode) {
	const payload = {
		templateId: record?.id || "",
		templateName: record?.name || "",
		mode: mode === "batch" ? "batch" : "single",
		openPicker: true,
	};
	try {
		if (window.frappe) {
			window.frappe.route_options = payload;
		}
		const go = window.frappe?.set_route;
		if (typeof go === "function") {
			go("contract-initiate");
			return;
		}
	} catch (e) {
		console.warn("[contract-templates] set_route failed", e);
	}
	// fallback when Desk route unavailable
	window.location.assign(
		`/desk/contract-initiate?templateId=${encodeURIComponent(payload.templateId)}&templateName=${encodeURIComponent(
			payload.templateName
		)}&mode=${payload.mode}&openPicker=1`
	);
}

onMounted(loadTemplates);
</script>
