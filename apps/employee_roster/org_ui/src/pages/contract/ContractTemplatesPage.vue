<template>
	<div class="arco-org-ui contract-templates">
		<ContractSectionNav group="settings" active-key="contract-templates" />

		<ContractActionToolbar title="签署任务模板" description="查看法大大签署任务模板及其启用状态">
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
		</ContractActionToolbar>

		<a-alert
			v-if="errorMessage"
			class="ct-test-alert"
			type="warning"
			show-icon
			:title="configurationMissing ? '电子签服务尚未配置' : '签署任务模板加载失败'"
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
							<a-doption value="provider">按服务商</a-doption>
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
						<a-empty :description="errorMessage ? '模板暂不可用' : '尚未配置可用的签署任务模板'">
							<a-button type="primary" @click="loadTemplates">重新加载</a-button>
						</a-empty>
					</template>
					<template #typeName="{ record }">
						<div class="ct-type">
							<div class="ct-type-name">{{ record.name }}</div>
							<div class="ct-type-desc">{{ record.desc }}</div>
						</div>
					</template>

					<template #provider="{ record }">
						<a-tag color="arcoblue">{{ record.provider }}</a-tag>
					</template>

					<template #enabled="{ record }">
						<a-tag :color="record.enabled ? 'green' : 'gray'">
							{{ record.enabled ? "已启用" : "已停用" }}
						</a-tag>
					</template>

					<template #sealConfig="{ record }">
						<div class="ct-seal" :class="{ 'is-empty': !record.sealId }">
							<a-tag :color="record.sealConfigured ? 'green' : 'orange'">
								{{ record.sealConfigured ? "人工盖章已配置" : "人工盖章待配置" }}
							</a-tag>
							<div v-if="record.sealId">印章 ID：{{ record.sealId }}</div>
							<div v-if="record.businessId">授权场景：{{ record.businessId }}</div>
						</div>
					</template>

					<template #ops="{ record }">
						<div class="ct-row-ops">
							<a-link v-if="record.provider === 'Fadada'" @click="openConfigure(record)">配置印章</a-link>
							<a-link v-if="record.provider === 'Fadada'" @click="openFadadaTemplate(record)">设置签署顺序</a-link>
							<a-link :disabled="!record.enabled" @click="onStartSign(record, 'single')">发起签署</a-link>
						</div>
					</template>
				</a-table>
			</div>
		</a-card>
		<a-modal
			v-model:visible="configureVisible"
			title="配置模板自动盖章"
			ok-text="保存配置"
			:ok-loading="configuring"
			@ok="saveConfiguration"
		>
			<a-alert type="info" show-icon>
				员工签署后，企业负责人将通过法大大链接完成人工验证和盖章。
			</a-alert>
			<a-form :model="configureForm" layout="vertical">
				<a-form-item label="法大大印章 ID" required>
					<a-input v-model="configureForm.sealId" />
				</a-form-item>
				<a-form-item label="免验证签业务场景 ID（可选）">
					<a-input
						v-model="configureForm.businessId"
						:max-length="32"
						placeholder="填写法大大后台已申请的场景码"
					/>
				</a-form-item>
			</a-form>
		</a-modal>
	</div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import { IconDown, IconSearch, IconSwap, IconUp } from "@arco-design/web-vue/es/icon";
import {
	configureFadadaTemplate,
	getFadadaTemplateEditUrl,
	getTemplates,
} from "../../api/contract.js";
import ContractActionToolbar from "./ContractActionToolbar.vue";
import ContractSectionNav from "./ContractSectionNav.vue";

const keyword = ref("");
const collapsed = ref(false);
const sortBy = ref("name");
const loading = ref(false);
const errorMessage = ref("");
const configurationMissing = ref(false);
const rows = ref([]);
const configureVisible = ref(false);
const configuring = ref(false);
const configureTemplate = ref(null);
const configureForm = reactive({ sealId: "", businessId: "" });

const columns = [
	{ title: "类型名称", slotName: "typeName", width: 320 },
	{ title: "服务商", slotName: "provider", width: 140 },
	{ title: "模板 ID", dataIndex: "templateId", width: 240 },
	{ title: "印章配置", slotName: "sealConfig", width: 220 },
	{ title: "状态", slotName: "enabled", width: 110 },
	{ title: "", slotName: "ops", width: 260, align: "right" },
];

const filteredRows = computed(() => {
	const q = keyword.value.trim().toLowerCase();
	let list = rows.value.slice();
	if (q) {
		list = list.filter(
			(row) =>
				row.name.toLowerCase().includes(q) ||
				row.desc.toLowerCase().includes(q) ||
				row.templateId.toLowerCase().includes(q) ||
				row.provider.toLowerCase().includes(q)
		);
	}
	if (sortBy.value === "provider") {
		list.sort((a, b) => a.provider.localeCompare(b.provider, "zh"));
	} else {
		list.sort((a, b) => a.name.localeCompare(b.name, "zh"));
	}
	return list;
});

function normalizeTemplate(row, index) {
	const templateId = String(
		row?.provider_template_id ||
			row?.sign_task_template_id ||
			row?.task_template_id ||
			row?.template_id ||
			""
	);
	const localName = String(row?.name || templateId || index);
	const rawEnabled = row?.enabled ?? row?.is_enabled ?? row?.status;
	return {
		id: localName,
		templateId: templateId || "—",
		name: row?.template_name || row?.title || row?.name || `未命名模板 ${index + 1}`,
		desc: row?.description || row?.desc || "",
		provider: row?.provider_name || row?.provider || "法大大",
		sealId: String(row?.seal_id || ""),
		businessId: String(row?.business_id || ""),
		employeeActorId: String(row?.employee_actor_id || ""),
		corpActorId: String(row?.corp_actor_id || ""),
		sealConfigured: Boolean(
			row?.seal_id &&
				row?.employee_actor_id &&
				row?.corp_actor_id
		),
		enabled: ![false, 0, "0", "false", "disabled", "inactive", "停用", "已停用"].includes(
			typeof rawEnabled === "string" ? rawEnabled.toLowerCase() : rawEnabled
		),
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
			errorMessage.value = result.configuration.message || "请先完成电子签服务端配置";
		}
	} catch (error) {
		console.warn("[contract-templates] load failed", error);
		rows.value = [];
		errorMessage.value = error?.message || "无法从后端获取签署任务模板";
	} finally {
		loading.value = false;
	}
}

function onSort(key) {
	sortBy.value = key;
}

async function openFadadaTemplate(record) {
	try {
		const result = await getFadadaTemplateEditUrl(record.id);
		const data = result?.data || result || {};
		const value =
			data.templateEditUrl ||
			data.editUrl ||
			data.url ||
			data.templateEditShortUrl;
		if (!value || !["http:", "https:"].includes(new URL(value).protocol)) {
			throw new Error("后端未返回安全的模板编辑地址");
		}
		window.open(value, "_blank", "noopener,noreferrer");
	} catch (error) {
		Message.error(error?.message || "获取法大大模板编辑地址失败");
	}
}

function openConfigure(record) {
	configureTemplate.value = record;
	configureForm.sealId = record.sealId || "";
	configureForm.businessId = record.businessId || "";
	configureVisible.value = true;
}

async function saveConfiguration() {
	if (!configureForm.sealId.trim()) {
		Message.warning("请填写印章 ID");
		return false;
	}
	configuring.value = true;
	try {
		await configureFadadaTemplate(
			configureTemplate.value.id,
			configureForm.sealId.trim(),
			configureForm.businessId.trim()
		);
		Message.success("模板自动盖章配置已保存");
		configureVisible.value = false;
		await loadTemplates();
	} catch (error) {
		Message.error(error?.message || "模板配置保存失败");
		return false;
	} finally {
		configuring.value = false;
	}
}

function onStartSign(record) {
	if (!record?.enabled) return;
	const payload = {
		templateId: record?.id || "",
		providerTemplateId: record?.templateId || "",
		templateName: record?.name || "",
		mode: "single",
		sealId: record?.sealId || "",
		businessId: record?.businessId || "",
		employeeActorId: record?.employeeActorId || "",
		corpActorId: record?.corpActorId || "",
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
		)}&providerTemplateId=${encodeURIComponent(payload.providerTemplateId)}&mode=single&sealId=${encodeURIComponent(
			payload.sealId
		)}&businessId=${encodeURIComponent(payload.businessId)}&employeeActorId=${encodeURIComponent(
			payload.employeeActorId
		)}&corpActorId=${encodeURIComponent(payload.corpActorId)}&openPicker=1`
	);
}

onMounted(loadTemplates);
</script>
