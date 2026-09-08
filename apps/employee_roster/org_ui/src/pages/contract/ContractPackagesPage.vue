<template>
	<div class="arco-org-ui contract-packages">
		<ContractSectionNav group="settings" active-key="contract-packages" />

		<ContractActionToolbar title="合同包" description="按业务场景组合多份合同并统一发起签署">
			<a-input
				v-model="keyword"
				class="cpk-search"
				allow-clear
				placeholder="搜索合同包名称 / 场景"
				@press-enter="applyFilter"
				@clear="applyFilter"
			>
				<template #prefix><icon-search /></template>
			</a-input>
			<a-button type="primary" @click="openCreate">
				<template #icon><icon-plus /></template>
				新建合同包
			</a-button>
		</ContractActionToolbar>

		<a-card :bordered="false" class="cpk-card">
			<a-table
				:columns="columns"
				:data="filteredRows"
				:pagination="false"
				:bordered="false"
				row-key="id"
				:scroll="{ x: 980 }"
			>
				<template #name="{ record }">
					<div class="cpk-name">{{ record.name }}</div>
					<div class="cpk-desc">{{ record.desc }}</div>
				</template>
				<template #templates="{ record }">
					<a-space wrap>
						<a-tag v-for="t in record.templates" :key="t" size="small">{{ t }}</a-tag>
					</a-space>
				</template>
				<template #status="{ record }">
					<a-tag :color="record.enabled ? 'green' : 'gray'">
						{{ record.enabled ? "启用" : "停用" }}
					</a-tag>
				</template>
				<template #ops="{ record }">
					<div class="cpk-ops">
						<a-link @click="openEdit(record)">编辑</a-link>
						<a-link @click="onStart(record)">发起打包签署</a-link>
						<a-link :status="record.enabled ? 'danger' : 'success'" @click="onToggle(record)">
							{{ record.enabled ? "停用" : "启用" }}
						</a-link>
					</div>
				</template>
			</a-table>
		</a-card>

		<a-drawer
			v-model:visible="drawerVisible"
			:width="480"
			unmount-on-close
			:title="editing ? '编辑合同包' : '新建合同包'"
		>
			<a-form :model="form" layout="vertical">
				<a-form-item label="合同包名称" required>
					<a-input v-model="form.name" placeholder="如：全职入职合同包" />
				</a-form-item>
				<a-form-item label="适用场景" required>
					<a-select
						v-model="form.scene"
						:options="[
							{ label: '入职', value: '入职' },
							{ label: '转正', value: '转正' },
							{ label: '调岗', value: '调岗' },
							{ label: '离职', value: '离职' },
						]"
					/>
				</a-form-item>
				<a-form-item label="默认印章">
					<a-select
						v-model="form.seal"
						:options="sealOptions"
						allow-clear
						placeholder="选择印章"
					/>
				</a-form-item>
				<a-form-item label="包含模板（有序）" required>
					<a-checkbox-group v-model="form.templates" direction="vertical" :options="templateOptions" />
				</a-form-item>
				<a-form-item label="说明">
					<a-textarea v-model="form.desc" :auto-size="{ minRows: 2, maxRows: 4 }" />
				</a-form-item>
			</a-form>
			<template #footer>
				<a-space>
					<a-button @click="drawerVisible = false">取消</a-button>
					<a-button type="primary" @click="onSave">保存</a-button>
				</a-space>
			</template>
		</a-drawer>
	</div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import { IconPlus, IconSearch } from "@arco-design/web-vue/es/icon";
import ContractActionToolbar from "./ContractActionToolbar.vue";
import ContractSectionNav from "./ContractSectionNav.vue";

const keyword = ref("");
const drawerVisible = ref(false);
const editing = ref(null);

const templateOptions = [
	{ label: "劳动合同", value: "劳动合同" },
	{ label: "保密协议", value: "保密协议" },
	{ label: "薪酬确认书", value: "薪酬确认书" },
	{ label: "实习协议", value: "实习协议" },
	{ label: "离职证明", value: "离职证明" },
];

const sealOptions = [
	{ label: "深圳市依然电商科技有限公司公章", value: "深圳市依然电商科技有限公司公章" },
	{ label: "依然杭州公章", value: "依然杭州公章" },
];

const rows = ref([
	{
		id: "1",
		name: "全职入职合同包",
		desc: "适用于全职员工入职一次性发起多份签署",
		scene: "入职",
		templates: ["劳动合同", "保密协议", "薪酬确认书"],
		seal: "深圳市依然电商科技有限公司公章",
		enabled: true,
	},
	{
		id: "2",
		name: "实习生入职包",
		desc: "适用于在校实习生入职",
		scene: "入职",
		templates: ["实习协议", "保密协议"],
		seal: "深圳市依然电商科技有限公司公章",
		enabled: true,
	},
	{
		id: "3",
		name: "离职证明包",
		desc: "离职手续完成后开具证明",
		scene: "离职",
		templates: ["离职证明"],
		seal: "深圳市依然电商科技有限公司公章",
		enabled: false,
	},
]);

const form = reactive({
	name: "",
	scene: "入职",
	seal: "",
	templates: [],
	desc: "",
});

const columns = [
	{ title: "合同包", slotName: "name", width: 260 },
	{ title: "适用场景", dataIndex: "scene", width: 100 },
	{ title: "含模板", slotName: "templates", width: 280 },
	{ title: "默认印章", dataIndex: "seal", width: 220 },
	{ title: "状态", slotName: "status", width: 90 },
	{ title: "操作", slotName: "ops", width: 220, fixed: "right" },
];

const filteredRows = computed(() => {
	const q = keyword.value.trim().toLowerCase();
	if (!q) return rows.value;
	return rows.value.filter(
		(row) =>
			row.name.toLowerCase().includes(q) ||
			row.scene.toLowerCase().includes(q) ||
			row.desc.toLowerCase().includes(q)
	);
});

function applyFilter() {
	/* computed */
}

function resetForm() {
	form.name = "";
	form.scene = "入职";
	form.seal = sealOptions[0]?.value || "";
	form.templates = [];
	form.desc = "";
}

function openCreate() {
	editing.value = null;
	resetForm();
	drawerVisible.value = true;
}

function openEdit(record) {
	editing.value = record;
	form.name = record.name;
	form.scene = record.scene;
	form.seal = record.seal;
	form.templates = record.templates.slice();
	form.desc = record.desc;
	drawerVisible.value = true;
}

function onSave() {
	if (!form.name.trim() || !form.templates.length) {
		Message.warning("请填写名称并至少选择一个模板");
		return false;
	}
	const payload = {
		name: form.name.trim(),
		scene: form.scene,
		seal: form.seal,
		templates: form.templates.slice(),
		desc: form.desc,
	};
	if (editing.value) {
		Object.assign(editing.value, payload);
		Message.success("已更新合同包（示意）");
	} else {
		rows.value.unshift({
			id: String(Date.now()),
			enabled: true,
			...payload,
		});
		Message.success("已新建合同包（示意）");
	}
	drawerVisible.value = false;
}

function onStart(record) {
	try {
		if (window.frappe) {
			window.frappe.route_options = {
				templateId: record.id,
				templateName: record.name,
				mode: "batch",
				openPicker: true,
			};
		}
		window.frappe?.set_route?.(["contract-initiate"]);
	} catch (e) {
		/* ignore */
	}
}

function onToggle(record) {
	record.enabled = !record.enabled;
	Message.info(record.enabled ? `已启用：${record.name}` : `已停用：${record.name}`);
}
</script>
