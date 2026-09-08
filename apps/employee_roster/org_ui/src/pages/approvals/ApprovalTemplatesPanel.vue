<template>
	<div class="ap-panel">
		<a-card :bordered="false" class="hr-desk-toolbar-card ap-toolbar-card">
			<div class="ap-panel-toolbar">
				<a-input-search
					v-model="keyword"
					allow-clear
					placeholder="搜索模板"
					class="ap-search"
					@search="load"
					@clear="load"
					@press-enter="load"
				/>
				<span class="ap-toolbar-hint">选择模板可快速创建标准审批表单</span>
			</div>
		</a-card>

		<a-card :bordered="false" class="hr-desk-table-card ap-content-card">
			<template #title>审批模板列表</template>
			<template #extra><span class="ap-list-count">共 {{ rows.length }} 个模板</span></template>
			<a-tabs v-model:active-key="category" type="rounded" class="ap-category-tabs" @change="load">
				<a-tab-pane v-for="c in categories" :key="c" :title="c" />
			</a-tabs>

			<a-table
				:columns="columns"
				:data="rows"
				:loading="loading"
				:pagination="false"
				row-key="name"
				:bordered="false"
				size="medium"
			>
				<template #name="{ record }">
					<div class="ap-form-name">
						<span class="ap-icon" :style="{ background: record.color || '#165DFF' }">
							{{ (record.template_name || "?").slice(0, 1) }}
						</span>
						<div class="ap-form-title">{{ record.template_name }}</div>
					</div>
				</template>
				<template #ops="{ record }">
					<a-link @click="useTemplate(record)">
						{{ using === record.name ? "创建中…" : "使用" }}
					</a-link>
				</template>
				<template #empty><a-empty description="当前分类暂无审批模板" /></template>
			</a-table>
		</a-card>
	</div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import { call } from "../../api/frappe";

const emit = defineEmits(["used"]);

const categories = ["全部", "人事", "考勤", "薪资", "行政", "其他"];
const category = ref("全部");
const keyword = ref("");
const loading = ref(false);
const using = ref("");
const rows = ref([]);

const columns = [
	{ title: "审批模板名称", slotName: "name", width: 240 },
	{ title: "模板说明", dataIndex: "description" },
	{ title: "操作", slotName: "ops", width: 100 },
];

async function load() {
	loading.value = true;
	try {
		rows.value =
			(await call("employee_roster.hr_roster.approval_admin.list_approval_templates", {
				category: category.value,
				keyword: keyword.value || undefined,
			})) || [];
	} catch (e) {
		Message.error("加载模板失败");
	} finally {
		loading.value = false;
	}
}

async function useTemplate(record) {
	using.value = record.name;
	try {
		const result = await call("employee_roster.hr_roster.approval_admin.use_approval_template", {
			template_name: record.name,
		});
		emit("used", result);
	} catch (e) {
		Message.error("使用模板失败");
	} finally {
		using.value = "";
	}
}

onMounted(load);
</script>
