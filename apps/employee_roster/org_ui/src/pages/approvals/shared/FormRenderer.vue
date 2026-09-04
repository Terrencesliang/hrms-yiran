<template>
	<a-form layout="vertical">
		<template v-for="field in visibleFields" :key="field.key">
			<a-form-item :label="field.label" :required="!!field.required && !readonly">
				<template v-if="permOf(field.key) === 'read' || readonly">
					<div class="ap-readonly">{{ displayValue(field) }}</div>
				</template>
				<template v-else>
					<a-input
						v-if="field.type === 'text'"
						v-model="model[field.key]"
						:placeholder="field.placeholder || field.label"
					/>
					<a-textarea
						v-else-if="field.type === 'textarea'"
						v-model="model[field.key]"
						:placeholder="field.placeholder || field.label"
						:auto-size="{ minRows: 2 }"
					/>
					<a-input-number
						v-else-if="field.type === 'number'"
						v-model="model[field.key]"
						style="width: 100%"
					/>
					<a-date-picker
						v-else-if="field.type === 'date'"
						v-model="model[field.key]"
						style="width: 100%"
						value-format="YYYY-MM-DD"
					/>
					<a-select
						v-else-if="field.type === 'select'"
						v-model="model[field.key]"
						:placeholder="field.label"
						allow-clear
					>
						<a-option v-for="o in field.options || []" :key="o" :value="o">{{ o }}</a-option>
					</a-select>
					<a-select
						v-else-if="field.type === 'multiselect'"
						v-model="model[field.key]"
						multiple
						:placeholder="field.label"
						allow-clear
					>
						<a-option v-for="o in field.options || []" :key="o" :value="o">{{ o }}</a-option>
					</a-select>
					<a-input
						v-else-if="field.type === 'attachment'"
						v-model="model[field.key]"
						placeholder="附件 URL / 文件名"
					/>
					<a-input
						v-else-if="field.type === 'employee' || field.type === 'department'"
						v-model="model[field.key]"
						:placeholder="field.type === 'employee' ? '员工 ID' : '部门名称'"
					/>
					<a-input v-else v-model="model[field.key]" />
				</template>
			</a-form-item>
		</template>
	</a-form>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	schema: { type: Object, default: () => ({ fields: [] }) },
	modelValue: { type: Object, default: () => ({}) },
	fieldPerms: { type: Object, default: () => ({}) },
	readonly: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue"]);

const model = computed({
	get: () => props.modelValue,
	set: (v) => emit("update:modelValue", v),
});

function permOf(key) {
	if (props.readonly) return "read";
	return props.fieldPerms?.[key] || "write";
}

const visibleFields = computed(() =>
	(props.schema?.fields || []).filter((f) => permOf(f.key) !== "hide")
);

function displayValue(field) {
	const v = model.value?.[field.key];
	if (v == null || v === "") return "—";
	if (Array.isArray(v)) return v.join(", ");
	return String(v);
}
</script>
