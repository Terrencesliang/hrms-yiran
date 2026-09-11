<template>
	<a-card :bordered="false" class="ec-form-card">
		<div class="ec-section-title"><div><h2>补贴明细</h2><p>金额将由后端按规则再次校验</p></div><a-button type="outline" @click="addRow"><template #icon><icon-plus /></template>新增一行</a-button></div>
		<a-table :columns="columns" :data="modelValue" :pagination="false" row-key="_key" :scroll="{ x: 1250 }">
			<template #index="{ rowIndex }">{{ rowIndex + 1 }}</template>
			<template #date="{ record }"><a-date-picker v-model="record.overtime_date" value-format="YYYY-MM-DD" style="width:140px" /></template>
			<template #time="{ record }"><a-time-picker v-model="record.clock_time" format="HH:mm" value-format="HH:mm" style="width:110px" /></template>
			<template #meal="{ record }"><a-input-number v-model="record.meal_amount" :min="0" :max="25" hide-button style="width:92px" /></template>
			<template #vehicle="{ record }"><a-input-number v-model="record.vehicle_amount" :min="0" :max="100" hide-button style="width:92px" /></template>
			<template #punch="{ record }"><AttachmentUploader v-model="record.punch_attachment" /></template>
			<template #taxi="{ record }"><AttachmentUploader v-model="record.taxi_attachment" /></template>
			<template #remark="{ record }"><a-input v-model="record.remark" allow-clear /></template>
			<template #operation="{ rowIndex }"><a-button type="text" status="danger" @click="removeRow(rowIndex)">删除</a-button></template>
		</a-table>
		<a-empty v-if="!modelValue.length" description="暂无补贴明细，请新增一行" />
		<div class="ec-subsidy-summary">
			<div><span>餐补合计</span><strong>{{ mealTotal.toFixed(2) }} 元</strong></div>
			<div><span>车补合计</span><strong>{{ vehicleTotal.toFixed(2) }} 元</strong></div>
			<div class="is-total"><span>总金额</span><strong>{{ total.toFixed(2) }} 元</strong></div>
		</div>
	</a-card>
</template>
<script setup lang="ts">
import { computed } from "vue";
import { IconPlus } from "@arco-design/web-vue/es/icon";
import AttachmentUploader from "./AttachmentUploader.vue";
const props = defineProps<{ modelValue: any[]; employees?: any[] }>();
const emit = defineEmits<{ "update:modelValue": [value: any[]] }>();
const columns = [
	{ title: "序号", slotName: "index", width: 60 }, { title: "加班日期", slotName: "date", width: 160 }, { title: "打卡时间", slotName: "time", width: 130 },
	{ title: "用餐金额", slotName: "meal", width: 112 }, { title: "用车金额", slotName: "vehicle", width: 112 }, { title: "打卡记录截图", slotName: "punch", width: 230 },
	{ title: "打车单截图（22点后）", slotName: "taxi", width: 250 }, { title: "备注", slotName: "remark", width: 180 }, { title: "操作", slotName: "operation", width: 70 },
];
const mealTotal = computed(() => props.modelValue.reduce((sum, row) => sum + Number(row.meal_amount || 0), 0));
const vehicleTotal = computed(() => props.modelValue.reduce((sum, row) => sum + Number(row.vehicle_amount || 0), 0));
const total = computed(() => mealTotal.value + vehicleTotal.value);
function addRow() { emit("update:modelValue", [...props.modelValue, { _key: `${Date.now()}-${Math.random()}`, meal_amount: 25, vehicle_amount: 30, remark: "" }]); }
function removeRow(index: number) { emit("update:modelValue", props.modelValue.filter((_, i) => i !== index)); }
</script>
