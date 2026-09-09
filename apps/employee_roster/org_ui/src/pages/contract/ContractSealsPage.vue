<template>
	<div class="arco-org-ui contract-seals">
		<ContractSectionNav group="settings" active-key="contract-seals" />

		<ContractActionToolbar title="企业印章" description="查看法大大企业印章及免验证签授权状态">
			<a-input
				v-model="keyword"
				class="cse-search"
				allow-clear
				placeholder="搜索公司主体 / 印章名称"
				@press-enter="applyFilter"
				@clear="applyFilter"
			>
				<template #prefix><icon-search /></template>
			</a-input>
			<a-button :loading="loading" @click="loadSeals">
				刷新
			</a-button>
		</ContractActionToolbar>

		<a-alert v-if="errorMessage" type="error" show-icon>{{ errorMessage }}</a-alert>
		<div class="cse-grid">
			<a-card v-for="seal in filteredSeals" :key="seal.sealId" :bordered="false" class="cse-card">
				<div class="cse-preview">
					<a-image
						v-if="seal.picFileUrl"
						:src="seal.picFileUrl"
						:alt="seal.sealName"
						fit="contain"
						class="cse-image"
					/>
					<div v-else class="cse-stamp">{{ seal.sealName.slice(0, 2) }}</div>
				</div>
				<div class="cse-body">
					<div class="cse-name-row">
						<div class="cse-name">{{ seal.sealName }}</div>
						<a-tag :color="sealStatusColor(seal.sealStatus)" size="small">
							{{ sealStatusText(seal.sealStatus) }}
						</a-tag>
					</div>
					<div class="cse-meta">印章 ID：{{ seal.sealId }}</div>
					<div class="cse-meta">类型：{{ categoryText(seal.categoryType) }} · 主体：{{ seal.entityId || "—" }}</div>
					<div class="cse-meta">免验证签：{{ freeSignSummary(seal.freeSignInfos) }}</div>
				</div>
				<div class="cse-ops">
					<a-link :loading="detailLoadingId === seal.sealId" @click="queryStatus(seal)">查询详情</a-link>
					<a-link @click="openAuthorization(seal)">免验证签授权</a-link>
				</div>
			</a-card>
		</div>
		<a-empty v-if="!loading && !errorMessage && !filteredSeals.length" description="暂无法大大印章" />

		<a-modal
			v-model:visible="modalVisible"
			title="免验证签授权"
			ok-text="获取授权链接"
			:ok-loading="authorizing"
			unmount-on-close
			@ok="submitAuthorization"
		>
			<a-alert type="info" show-icon class="cse-modal-alert">
				将为印章“{{ activeSeal?.sealName }}”申请法大大免验证签授权，授权完成后请返回并刷新状态。
			</a-alert>
			<a-form :model="form" layout="vertical">
				<a-form-item label="业务场景 ID（businessId）" required>
					<a-input v-model="form.businessId" placeholder="请输入法大大后台已申请的免验证签场景码" />
				</a-form-item>
			</a-form>
		</a-modal>

		<a-drawer v-model:visible="detailVisible" title="法大大印章详情" :width="480">
			<a-descriptions v-if="sealDetail" :column="1" bordered>
				<a-descriptions-item label="印章名称">{{ sealDetail.sealName || activeSeal?.sealName || "—" }}</a-descriptions-item>
				<a-descriptions-item label="印章 ID">{{ sealDetail.sealId || activeSeal?.sealId || "—" }}</a-descriptions-item>
				<a-descriptions-item label="印章状态">{{ sealStatusText(sealDetail.sealStatus ?? activeSeal?.sealStatus) }}</a-descriptions-item>
				<a-descriptions-item label="免验证签">{{ freeSignSummary(sealDetail.freeSignInfos ?? activeSeal?.freeSignInfos) }}</a-descriptions-item>
			</a-descriptions>
			<pre v-if="sealDetail" class="cse-detail-json">{{ JSON.stringify(sealDetail, null, 2) }}</pre>
		</a-drawer>
	</div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import { IconSearch } from "@arco-design/web-vue/es/icon";
import {
	getFadadaSealAuthorizationUrl,
	getFadadaSeals,
	getFadadaSealStatus,
} from "../../api/contract.js";
import ContractActionToolbar from "./ContractActionToolbar.vue";
import ContractSectionNav from "./ContractSectionNav.vue";

const keyword = ref("");
const modalVisible = ref(false);
const detailVisible = ref(false);
const loading = ref(false);
const authorizing = ref(false);
const detailLoadingId = ref("");
const errorMessage = ref("");
const seals = ref([]);
const activeSeal = ref(null);
const sealDetail = ref(null);
const form = reactive({ businessId: "" });

const filteredSeals = computed(() => {
	const q = keyword.value.trim().toLowerCase();
	if (!q) return seals.value;
	return seals.value.filter(
		(s) =>
			String(s.sealName || "").toLowerCase().includes(q) ||
			String(s.entityId || "").toLowerCase().includes(q) ||
			String(s.sealId || "").toLowerCase().includes(q)
	);
});

function applyFilter() {
	/* computed */
}

function unwrapData(result) {
	return result?.data ?? result;
}

function safeOpen(result) {
	const data = unwrapData(result);
	const payload = data?.data || data;
	const value = typeof payload === "string"
		? payload
		: payload?.freeSignUrl ||
			payload?.freeSignShortUrl ||
			payload?.url ||
			payload?.authUrl ||
			payload?.authorizationUrl ||
			payload?.sealFreeSignUrl;
	if (!value) return false;
	try {
		const url = new URL(value, window.location.origin);
		if (!["http:", "https:"].includes(url.protocol)) return false;
		window.open(url.href, "_blank", "noopener,noreferrer");
		return true;
	} catch {
		return false;
	}
}

function sealStatusText(value) {
	const map = { 0: "未启用", 1: "正常", 2: "停用", 3: "注销", enabled: "正常", disabled: "停用" };
	return map[String(value ?? "").toLowerCase()] || String(value ?? "未知");
}

function sealStatusColor(value) {
	return ["1", "enabled", "normal", "active"].includes(String(value ?? "").toLowerCase()) ? "green" : "orange";
}

function categoryText(value) {
	const map = { 1: "企业公章", 2: "财务专用章", 3: "合同专用章", 4: "法定代表人章" };
	return map[value] || value || "—";
}

function freeSignSummary(value) {
	if (!value || (Array.isArray(value) && !value.length)) return "未授权";
	if (Array.isArray(value)) {
		return value.map((item) => item?.businessId || item?.businessName || item?.status || "已授权").join("、");
	}
	return typeof value === "object" ? value.businessId || value.status || "已授权" : String(value);
}

async function loadSeals() {
	loading.value = true;
	errorMessage.value = "";
	try {
		const result = await getFadadaSeals();
		const data = unwrapData(result) || {};
		const list = data?.sealInfos || data?.data?.sealInfos || [];
		seals.value = Array.isArray(list) ? list : [];
	} catch (error) {
		seals.value = [];
		errorMessage.value = error?.message || "法大大印章加载失败";
	} finally {
		loading.value = false;
	}
}

function openAuthorization(seal) {
	activeSeal.value = seal;
	form.businessId = "";
	modalVisible.value = true;
}

async function submitAuthorization() {
	if (!form.businessId.trim()) {
		Message.warning("请输入业务场景 ID");
		return false;
	}
	authorizing.value = true;
	try {
		const result = await getFadadaSealAuthorizationUrl(
			String(activeSeal.value.sealId),
			form.businessId.trim(),
			window.location.href
		);
		if (!safeOpen(result)) throw new Error("后端未返回安全的授权地址");
		modalVisible.value = false;
		Message.success("授权页面已打开，完成后请刷新印章状态");
	} catch (error) {
		Message.error(error?.message || "获取授权链接失败");
		return false;
	} finally {
		authorizing.value = false;
	}
}

async function queryStatus(seal) {
	activeSeal.value = seal;
	detailLoadingId.value = seal.sealId;
	try {
		const result = await getFadadaSealStatus(String(seal.sealId));
		const detail = unwrapData(result) || {};
		sealDetail.value = detail.sealInfo || detail.data?.sealInfo || detail;
		detailVisible.value = true;
	} catch (error) {
		Message.error(error?.message || "印章详情查询失败");
	} finally {
		detailLoadingId.value = "";
	}
}

onMounted(loadSeals);
</script>
