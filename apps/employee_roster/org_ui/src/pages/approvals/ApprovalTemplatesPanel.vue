<template>
	<div class="ap-panel">
		<div class="ap-panel-header">
			<div>
				<h1 class="oc-page-title" style="margin-bottom: 4px">审批模板库</h1>
				<p class="ap-hint">从预置模板一键创建审批表单，可再在「审批表单」中设置</p>
			</div>
			<a-input-search
				v-model="keyword"
				allow-clear
				placeholder="搜索模板"
				style="width: 260px"
				@search="load"
				@clear="load"
				@press-enter="load"
			/>
		</div>

		<a-card :bordered="false" class="oc-table-card">
			<a-tabs v-model:active-key="category" type="rounded" @change="load">
				<a-tab-pane v-for="c in categories" :key="c" :title="c" />
			</a-tabs>

			<a-table
				:columns="columns"
				:data="rows"
				:loading="loading"
				:pagination="false"
				row-key="name"
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
