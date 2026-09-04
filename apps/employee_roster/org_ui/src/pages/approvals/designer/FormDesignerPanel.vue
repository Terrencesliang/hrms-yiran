<template>
	<div class="apd-layout">
		<aside class="apd-palette">
			<div class="apd-section-title">组件库</div>
			<div
				v-for="item in palette"
				:key="item.type"
				class="apd-palette-item"
				draggable="true"
				@dragstart="onDragStart($event, item)"
				@click="addField(item)"
			>
				{{ item.label }}
			</div>
		</aside>

		<section
			class="apd-canvas"
			@dragover.prevent
			@drop="onDrop"
		>
			<div class="apd-section-title">画布</div>
			<div v-if="!localFields.length" class="apd-empty">从左侧拖入或点击组件添加字段</div>
			<div
				v-for="(field, idx) in localFields"
				:key="field.key"
				class="apd-field-card"
				:class="{ active: field.key === selectedKey }"
				@click="selectedKey = field.key"
			>
				<div class="apd-field-card-head">
					<span>{{ field.label }} <small>({{ field.type }})</small></span>
					<a-space>
						<a-button size="mini" @click.stop="move(idx, -1)">上移</a-button>
						<a-button size="mini" @click.stop="move(idx, 1)">下移</a-button>
						<a-button size="mini" status="danger" @click.stop="remove(idx)">删除</a-button>
					</a-space>
				</div>
				<a-input
					v-if="field.type === 'text'"
					:placeholder="field.placeholder || field.label"
					disabled
				/>
				<a-textarea
					v-else-if="field.type === 'textarea'"
					:placeholder="field.placeholder || field.label"
					disabled
					:auto-size="{ minRows: 2 }"
				/>
				<a-input-number v-else-if="field.type === 'number'" disabled style="width: 100%" />
				<a-date-picker v-else-if="field.type === 'date'" disabled style="width: 100%" />
				<a-select v-else-if="field.type === 'select'" disabled :placeholder="field.label">
					<a-option v-for="o in field.options || []" :key="o" :value="o">{{ o }}</a-option>
				</a-select>
				<a-select
					v-else-if="field.type === 'multiselect'"
					disabled
					multiple
					:placeholder="field.label"
				/>
				<a-input v-else disabled :placeholder="typeLabel(field.type)" />
			</div>
		</section>

		<aside class="apd-props">
			<div class="apd-section-title">字段属性</div>
			<template v-if="current">
				<a-form layout="vertical" size="small">
					<a-form-item label="标签">
						<a-input v-model="current.label" />
					</a-form-item>
					<a-form-item label="字段 Key">
						<a-input v-model="current.key" />
					</a-form-item>
					<a-form-item label="占位提示">
						<a-input v-model="current.placeholder" />
					</a-form-item>
					<a-form-item label="必填">
						<a-switch v-model="current.required" :checked-value="1" :unchecked-value="0" />
					</a-form-item>
					<a-form-item
						v-if="current.type === 'select' || current.type === 'multiselect'"
						label="选项（每行一个）"
					>
						<a-textarea
							:model-value="(current.options || []).join('\n')"
							:auto-size="{ minRows: 4 }"
							@update:model-value="onOptionsChange"
						/>
					</a-form-item>
				</a-form>
			</template>
			<div v-else class="apd-empty">选中字段后编辑属性</div>
		</aside>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	fields: { type: Array, default: () => [] },
	selectedKey: { type: String, default: "" },
});
const emit = defineEmits(["update:fields", "update:selectedKey"]);

const palette = [
	{ type: "text", label: "单行文本" },
	{ type: "textarea", label: "多行文本" },
	{ type: "number", label: "数字" },
	{ type: "date", label: "日期" },
	{ type: "select", label: "单选" },
	{ type: "multiselect", label: "多选" },
	{ type: "attachment", label: "附件" },
	{ type: "employee", label: "员工" },
	{ type: "department", label: "部门" },
];

const localFields = computed({
	get: () => props.fields,
	set: (v) => emit("update:fields", v),
});
const selectedKey = computed({
	get: () => props.selectedKey,
	set: (v) => emit("update:selectedKey", v),
});
const current = computed(() => localFields.value.find((f) => f.key === selectedKey.value));

function typeLabel(t) {
	return palette.find((p) => p.type === t)?.label || t;
}

function uid(type) {
	return `${type}_${Math.random().toString(36).slice(2, 8)}`;
}

function addField(item) {
	const key = uid(item.type);
	const next = [
		...localFields.value,
		{
			key,
			label: item.label,
			type: item.type,
			required: 0,
			placeholder: "",
			options: item.type === "select" || item.type === "multiselect" ? ["选项1", "选项2"] : [],
		},
	];
	localFields.value = next;
	selectedKey.value = key;
}

function onDragStart(e, item) {
	e.dataTransfer.setData("text/plain", item.type);
}

function onDrop(e) {
	const type = e.dataTransfer.getData("text/plain");
	const item = palette.find((p) => p.type === type);
	if (item) addField(item);
}

function remove(idx) {
	const key = localFields.value[idx]?.key;
	const next = localFields.value.filter((_, i) => i !== idx);
	localFields.value = next;
	if (selectedKey.value === key) selectedKey.value = next[0]?.key || "";
}

function move(idx, delta) {
	const to = idx + delta;
	if (to < 0 || to >= localFields.value.length) return;
	const next = [...localFields.value];
	const tmp = next[idx];
	next[idx] = next[to];
	next[to] = tmp;
	localFields.value = next;
}

function onOptionsChange(val) {
	if (!current.value) return;
	current.value.options = String(val || "")
		.split("\n")
		.map((s) => s.trim())
		.filter(Boolean);
}
</script>
