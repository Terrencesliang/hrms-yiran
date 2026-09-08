<template>
	<div class="arco-org-ui contract-seals">
		<ContractSectionNav group="settings" active-key="contract-seals" />

		<ContractActionToolbar title="企业印章" description="管理各公司主体用于电子合同的印章">
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
			<a-button type="primary" @click="openCreate">
				<template #icon><icon-plus /></template>
				新增印章
			</a-button>
		</ContractActionToolbar>

		<div class="cse-grid">
			<a-card v-for="seal in filteredSeals" :key="seal.id" :bordered="false" class="cse-card">
				<div class="cse-preview" :class="{ 'is-disabled': !seal.enabled }">
					<div class="cse-stamp">{{ seal.shortName }}</div>
				</div>
				<div class="cse-body">
					<div class="cse-name-row">
						<div class="cse-name">{{ seal.name }}</div>
						<a-tag v-if="seal.isDefault" color="green" size="small">默认</a-tag>
						<a-tag v-if="!seal.enabled" color="gray" size="small">停用</a-tag>
					</div>
					<div class="cse-meta">{{ seal.entity }}</div>
					<div class="cse-meta">类型：{{ seal.type }} · 最近使用 {{ seal.lastUsed }}</div>
				</div>
				<div class="cse-ops">
					<a-link @click="onEdit(seal)">编辑</a-link>
					<a-link v-if="seal.enabled && !seal.isDefault" @click="onSetDefault(seal)">设为默认</a-link>
					<a-link :status="seal.enabled ? 'danger' : 'success'" @click="onToggle(seal)">
						{{ seal.enabled ? "停用" : "启用" }}
					</a-link>
				</div>
			</a-card>
		</div>

		<a-modal
			v-model:visible="modalVisible"
			:title="editing ? '编辑印章' : '新增印章'"
			ok-text="保存"
			unmount-on-close
			@ok="onSave"
		>
			<a-form :model="form" layout="vertical">
				<a-form-item label="印章名称" required>
					<a-input v-model="form.name" placeholder="如：依然集团公章" />
				</a-form-item>
				<a-form-item label="公司主体" required>
					<a-input v-model="form.entity" placeholder="如：深圳市依然电商科技有限公司" />
				</a-form-item>
				<a-form-item label="印章类型" required>
					<a-select
						v-model="form.type"
						:options="[
							{ label: '公章', value: '公章' },
							{ label: '合同章', value: '合同章' },
							{ label: '人事章', value: '人事章' },
						]"
					/>
				</a-form-item>
				<a-form-item label="印章图片">
					<a-upload :auto-upload="false" :limit="1" accept="image/*" tip="示意上传，本阶段不落库" />
				</a-form-item>
				<a-form-item label="备注">
					<a-textarea v-model="form.remark" :auto-size="{ minRows: 2, maxRows: 4 }" />
				</a-form-item>
			</a-form>
		</a-modal>
	</div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import { IconPlus, IconSearch } from "@arco-design/web-vue/es/icon";
import ContractActionToolbar from "./ContractActionToolbar.vue";
import ContractSectionNav from "./ContractSectionNav.vue";

const keyword = ref("");
const modalVisible = ref(false);
const editing = ref(null);

const seals = ref([
	{
		id: "1",
		name: "依然集团公章",
		shortName: "公章",
		entity: "深圳市依然电商科技有限公司",
		type: "公章",
		enabled: true,
		isDefault: true,
		lastUsed: "2026-09-06",
		remark: "",
	},
	{
		id: "2",
		name: "依然杭州公章",
		shortName: "杭州",
		entity: "依然杭州分公司",
		type: "公章",
		enabled: true,
		isDefault: false,
		lastUsed: "2026-09-01",
		remark: "",
	},
	{
		id: "3",
		name: "依然集团合同章",
		shortName: "合同",
		entity: "深圳市依然电商科技有限公司",
		type: "合同章",
		enabled: true,
		isDefault: false,
		lastUsed: "2026-08-28",
		remark: "",
	},
	{
		id: "4",
		name: "旧版人事章",
		shortName: "人事",
		entity: "深圳市依然电商科技有限公司",
		type: "人事章",
		enabled: false,
		isDefault: false,
		lastUsed: "2025-12-01",
		remark: "已停用",
	},
]);

const form = reactive({
	name: "",
	entity: "",
	type: "公章",
	remark: "",
});

const filteredSeals = computed(() => {
	const q = keyword.value.trim().toLowerCase();
	if (!q) return seals.value;
	return seals.value.filter(
		(s) =>
			s.name.toLowerCase().includes(q) ||
			s.entity.toLowerCase().includes(q) ||
			s.type.toLowerCase().includes(q)
	);
});

function applyFilter() {
	/* computed */
}

function resetForm() {
	form.name = "";
	form.entity = "";
	form.type = "公章";
	form.remark = "";
}

function openCreate() {
	editing.value = null;
	resetForm();
	modalVisible.value = true;
}

function onEdit(seal) {
	editing.value = seal;
	form.name = seal.name;
	form.entity = seal.entity;
	form.type = seal.type;
	form.remark = seal.remark || "";
	modalVisible.value = true;
}

function onSave() {
	if (!form.name.trim() || !form.entity.trim()) {
		Message.warning("请填写印章名称与公司主体");
		return false;
	}
	if (editing.value) {
		Object.assign(editing.value, {
			name: form.name.trim(),
			entity: form.entity.trim(),
			type: form.type,
			remark: form.remark,
			shortName: form.type.slice(0, 2),
		});
		Message.success("已更新印章（示意）");
	} else {
		seals.value.unshift({
			id: String(Date.now()),
			name: form.name.trim(),
			shortName: form.type.slice(0, 2),
			entity: form.entity.trim(),
			type: form.type,
			enabled: true,
			isDefault: false,
			lastUsed: "—",
			remark: form.remark,
		});
		Message.success("已新增印章（示意）");
	}
	modalVisible.value = false;
}

function onSetDefault(seal) {
	seals.value.forEach((s) => {
		s.isDefault = s.id === seal.id;
	});
	Message.success(`已设为默认：${seal.name}`);
}

function onToggle(seal) {
	seal.enabled = !seal.enabled;
	if (!seal.enabled) seal.isDefault = false;
	Message.info(seal.enabled ? `已启用：${seal.name}` : `已停用：${seal.name}`);
}
</script>
