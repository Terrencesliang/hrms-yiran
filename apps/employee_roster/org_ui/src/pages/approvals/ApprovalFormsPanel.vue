<template>
	<div class="ap-panel">
		<div class="ap-panel-header">
			<div>
				<h1 class="oc-page-title" style="margin-bottom: 4px">审批表单</h1>
				<p class="ap-hint">配置企业可用的审批表单、可见范围与流程摘要（一期管理端壳）</p>
			</div>
			<div class="ap-actions">
				<a-input-search
					v-model="keyword"
					allow-clear
					placeholder="搜索审批表单"
					style="width: 220px"
					@search="loadForms"
					@clear="loadForms"
					@press-enter="loadForms"
				/>
				<a-button @click="openGroupModal">编辑分组</a-button>
				<a-button type="primary" @click="openCreateForm">
					<template #icon><icon-plus /></template>
					新建审批表单
				</a-button>
			</div>
		</div>

		<a-card :bordered="false" class="oc-table-card">
			<a-tabs v-model:active-key="activeGroup" type="rounded" @change="loadForms">
				<a-tab-pane
					v-for="g in groups"
					:key="g.name"
					:title="`${g.group_name} (${g.form_count || 0})`"
				/>
			</a-tabs>

			<a-table
				:columns="columns"
				:data="forms"
				:loading="loading"
				:pagination="false"
				row-key="name"
			>
				<template #formName="{ record }">
					<div class="ap-form-name">
						<span class="ap-icon" :style="{ background: record.color || '#165DFF' }">
							{{ (record.form_name || "?").slice(0, 1) }}
						</span>
						<div>
							<div class="ap-form-title">
								{{ record.form_name }}
								<a-tag
									v-if="record.status === '使用中'"
									size="small"
									color="green"
									style="margin-left: 6px"
								>
									使用中
								</a-tag>
								<a-tag v-else size="small" color="gray" style="margin-left: 6px">已停用</a-tag>
							</div>
							<div class="ap-form-desc">{{ record.description || "—" }}</div>
						</div>
					</div>
				</template>
				<template #process="{ record }">
					<span class="ap-process">{{ record.process_summary || "未配置流程" }}</span>
				</template>
				<template #ops="{ record }">
					<a-space>
						<a-link @click="openEditForm(record)">设置</a-link>
						<a-dropdown>
							<a-link><icon-more /></a-link>
							<template #content>
								<a-doption @click="openEditForm(record)">编辑</a-doption>
								<a-doption @click="toggleStatus(record)">
									{{ record.status === "使用中" ? "停用" : "启用" }}
								</a-doption>
							</template>
						</a-dropdown>
					</a-space>
				</template>
			</a-table>
		</a-card>

		<a-modal
			v-model:visible="formModalVisible"
			:title="formModel.name ? '设置审批表单' : '新建审批表单'"
			:ok-loading="saving"
			unmount-on-close
			@ok="submitForm"
		>
			<a-form :model="formModel" layout="vertical">
				<a-form-item label="表单名称" required>
					<a-input v-model="formModel.form_name" placeholder="如：请假" />
				</a-form-item>
				<a-form-item label="分组" required>
					<a-select v-model="formModel.group" placeholder="选择分组">
						<a-option v-for="g in groups" :key="g.name" :value="g.name">
							{{ g.group_name }}
						</a-option>
					</a-select>
				</a-form-item>
				<a-form-item label="描述">
					<a-textarea v-model="formModel.description" :auto-size="{ minRows: 2 }" />
				</a-form-item>
				<a-form-item label="可见范围">
					<a-select v-model="formModel.visibility">
						<a-option value="全公司">全公司</a-option>
						<a-option value="自定义">自定义</a-option>
					</a-select>
				</a-form-item>
				<a-form-item label="状态">
					<a-select v-model="formModel.status">
						<a-option value="使用中">使用中</a-option>
						<a-option value="已停用">已停用</a-option>
					</a-select>
				</a-form-item>
				<a-form-item label="流程摘要">
					<a-input
						v-model="formModel.process_summary"
						placeholder="如：直属上级 → HR → 抄送：HR"
					/>
				</a-form-item>
				<a-form-item label="颜色">
					<a-input v-model="formModel.color" placeholder="#165DFF" />
				</a-form-item>
			</a-form>
		</a-modal>

		<a-modal
			v-model:visible="groupModalVisible"
			title="编辑分组"
			:footer="false"
			width="560px"
			unmount-on-close
		>
			<div class="ap-group-editor">
				<div v-for="g in allGroups" :key="g.name" class="ap-group-row">
					<a-input v-model="g.group_name" style="flex: 1" />
					<a-input-number v-model="g.sort_order" :min="0" style="width: 90px" />
					<a-button type="outline" size="small" @click="saveGroup(g)">保存</a-button>
					<a-button
						status="danger"
						size="small"
						:disabled="(g.form_count || 0) > 0"
						@click="removeGroup(g)"
					>
						删除
					</a-button>
				</div>
				<a-divider />
				<div class="ap-group-row">
					<a-input v-model="newGroup.group_name" placeholder="新分组名称" style="flex: 1" />
					<a-input-number v-model="newGroup.sort_order" :min="0" style="width: 90px" />
					<a-button type="primary" size="small" @click="createGroup">添加</a-button>
				</div>
			</div>
		</a-modal>
	</div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { Message, Modal } from "@arco-design/web-vue";
import { call } from "../../api/frappe";

const loading = ref(false);
const saving = ref(false);
const keyword = ref("");
const groups = ref([]);
const forms = ref([]);
const activeGroup = ref("");

const formModalVisible = ref(false);
const formModel = reactive({
	name: "",
	form_name: "",
	group: "",
	description: "",
	visibility: "全公司",
	status: "使用中",
	process_summary: "直属上级 → HR → 抄送：HR",
	color: "#165DFF",
	sort_order: 0,
});

const groupModalVisible = ref(false);
const allGroups = ref([]);
const newGroup = reactive({ group_name: "", sort_order: 0 });

const columns = [
	{ title: "表单名称", slotName: "formName", width: 320 },
	{ title: "可见范围", dataIndex: "visibility", width: 120 },
	{ title: "审批流程", slotName: "process" },
	{ title: "操作", slotName: "ops", width: 120 },
];

async function loadGroups() {
	groups.value = (await call("employee_roster.hr_roster.approval_admin.list_approval_groups")) || [];
	if (!activeGroup.value && groups.value.length) {
		activeGroup.value = groups.value[0].name;
	}
}

async function loadForms() {
	loading.value = true;
	try {
		forms.value =
			(await call("employee_roster.hr_roster.approval_admin.list_approval_forms", {
				group: activeGroup.value || undefined,
				keyword: keyword.value || undefined,
			})) || [];
		// refresh counts on current groups
		await loadGroups();
	} catch (e) {
		Message.error("加载审批表单失败");
	} finally {
		loading.value = false;
	}
}

function resetFormModel(extra = {}) {
	Object.assign(formModel, {
		name: "",
		form_name: "",
		group: activeGroup.value || groups.value[0]?.name || "",
		description: "",
		visibility: "全公司",
		status: "使用中",
		process_summary: "直属上级 → HR → 抄送：HR",
		color: "#165DFF",
		sort_order: 0,
		...extra,
	});
}

function openCreateForm() {
	resetFormModel();
	formModalVisible.value = true;
}

function openEditForm(record) {
	resetFormModel({
		name: record.name,
		form_name: record.form_name,
		group: record.group,
		description: record.description || "",
		visibility: record.visibility || "全公司",
		status: record.status || "使用中",
		process_summary: record.process_summary || "",
		color: record.color || "#165DFF",
		sort_order: record.sort_order || 0,
	});
	formModalVisible.value = true;
}

async function submitForm() {
	if (!formModel.form_name?.trim() || !formModel.group) {
		Message.warning("请填写表单名称和分组");
		return false;
	}
	saving.value = true;
	try {
		await call("employee_roster.hr_roster.approval_admin.save_approval_form", {
			payload: { ...formModel },
		});
		Message.success("已保存");
		formModalVisible.value = false;
		await loadForms();
	} catch (e) {
		Message.error("保存失败");
		return false;
	} finally {
		saving.value = false;
	}
}

async function toggleStatus(record) {
	const next = record.status === "使用中" ? "已停用" : "使用中";
	await call("employee_roster.hr_roster.approval_admin.save_approval_form", {
		payload: {
			name: record.name,
			form_name: record.form_name,
			group: record.group,
			description: record.description,
			visibility: record.visibility,
			status: next,
			process_summary: record.process_summary,
			color: record.color,
			sort_order: record.sort_order,
		},
	});
	Message.success(next === "使用中" ? "已启用" : "已停用");
	await loadForms();
}

async function openGroupModal() {
	allGroups.value = JSON.parse(JSON.stringify(groups.value));
	newGroup.group_name = "";
	newGroup.sort_order = (groups.value.length + 1) * 10;
	groupModalVisible.value = true;
}

async function saveGroup(g) {
	await call("employee_roster.hr_roster.approval_admin.save_approval_group", {
		payload: {
			name: g.name,
			group_name: g.group_name,
			sort_order: g.sort_order,
			enabled: 1,
		},
	});
	Message.success("分组已保存");
	await loadGroups();
	allGroups.value = JSON.parse(JSON.stringify(groups.value));
	await loadForms();
}

async function createGroup() {
	if (!newGroup.group_name?.trim()) {
		Message.warning("请输入分组名称");
		return;
	}
	await call("employee_roster.hr_roster.approval_admin.save_approval_group", {
		payload: { ...newGroup, enabled: 1 },
	});
	Message.success("分组已添加");
	newGroup.group_name = "";
	await loadGroups();
	allGroups.value = JSON.parse(JSON.stringify(groups.value));
}

function removeGroup(g) {
	Modal.confirm({
		title: "删除分组",
		content: `确认删除「${g.group_name}」？`,
		onOk: async () => {
			await call("employee_roster.hr_roster.approval_admin.delete_approval_group", {
				name: g.name,
			});
			Message.success("已删除");
			if (activeGroup.value === g.name) activeGroup.value = "";
			await loadGroups();
			allGroups.value = JSON.parse(JSON.stringify(groups.value));
			await loadForms();
		},
	});
}

async function reload() {
	await loadGroups();
	await loadForms();
}

defineExpose({ reload });

onMounted(reload);
</script>
