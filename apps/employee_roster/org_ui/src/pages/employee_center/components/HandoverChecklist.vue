<template>
	<a-card :bordered="false" class="ec-form-card">
		<div class="ec-section-title"><div><h2>交接清单</h2><p>已完成 {{ completed }} / {{ modelValue.length }} 项</p></div><a-space><a-select v-model="batchEmployee" allow-search placeholder="选择交接人" style="width:160px"><a-option v-for="employee in employees" :key="employee.name" :value="employee.name">{{ employee.employee_name }}</a-option></a-select><a-button :disabled="!batchEmployee" @click="batchAssignee">应用到当前分类</a-button><a-button type="outline" @click="addCustom"><template #icon><icon-plus /></template>新增自定义项</a-button></a-space></div>
		<a-progress :percent="progress" :show-text="false" status="success" />
		<a-tabs v-model:active-key="activeCategory" class="ec-handover-tabs">
			<a-tab-pane v-for="category in categories" :key="category" :title="category">
				<a-table :columns="columns" :data="categoryRows" :pagination="false" row-key="_key" :scroll="{ x: 1000 }">
					<template #index="{ rowIndex }">{{ rowIndex + 1 }}</template>
					<template #content="{ record }"><a-input v-model="record.work_content" placeholder="填写具体交接内容" /></template>
					<template #remark="{ record }"><a-input v-model="record.remark" placeholder="备注" /></template>
					<template #employee="{ record }"><a-select v-model="record.handover_employee" allow-search style="width:160px"><a-option v-for="employee in employees" :key="employee.name" :value="employee.name">{{ employee.employee_name }}</a-option></a-select></template>
					<template #status="{ record }"><a-select v-model="record.handover_status" style="width:110px"><a-option v-for="status in statuses" :key="status" :value="status">{{ status }}</a-option></a-select></template>
					<template #operation="{ record }"><a-button v-if="record.is_custom" type="text" status="danger" @click="remove(record._key)">删除</a-button><span v-else>—</span></template>
				</a-table>
			</a-tab-pane>
		</a-tabs>
	</a-card>
</template>
<script setup lang="ts">
import { computed, ref } from "vue";
import { IconPlus } from "@arco-design/web-vue/es/icon";
import { handoverTemplates } from "../applicationFormConfig";
const props = defineProps<{ modelValue: any[]; employees: any[] }>();
const emit = defineEmits<{ "update:modelValue": [value: any[]] }>();
const categories = Object.keys(handoverTemplates);
const activeCategory = ref(categories[0]);
const batchEmployee = ref("");
const statuses = ["未开始", "进行中", "已完成"];
const columns = [{ title: "序号", slotName: "index", width: 60 }, { title: "事项", dataIndex: "item_name", width: 180 }, { title: "具体工作内容", slotName: "content", width: 280 }, { title: "备注", slotName: "remark", width: 180 }, { title: "交接人", slotName: "employee", width: 190 }, { title: "交接状态", slotName: "status", width: 140 }, { title: "操作", slotName: "operation", width: 70 }];
if (!props.modelValue.length) emit("update:modelValue", categories.flatMap(category => handoverTemplates[category].map((item_name, index) => ({ _key: `${category}-${index}`, category, item_name, work_content: "", remark: "", handover_employee: "", handover_status: "未开始", sort_order: index, is_custom: 0 }))));
const categoryRows = computed(() => props.modelValue.filter(row => row.category === activeCategory.value));
const completed = computed(() => props.modelValue.filter(row => row.handover_status === "已完成").length);
const progress = computed(() => props.modelValue.length ? completed.value / props.modelValue.length : 0);
function addCustom() { emit("update:modelValue", [...props.modelValue, { _key: `${Date.now()}`, category: activeCategory.value, item_name: "自定义交接项", work_content: "", remark: "", handover_employee: "", handover_status: "未开始", sort_order: categoryRows.value.length, is_custom: 1 }]); }
function remove(key: string) { emit("update:modelValue", props.modelValue.filter(row => row._key !== key)); }
function batchAssignee() {
	if (batchEmployee.value) props.modelValue.forEach(row => { if (row.category === activeCategory.value) row.handover_employee = batchEmployee.value; });
}
</script>
