<template>
	<a-select
		:model-value="modelValue"
		allow-search
		allow-clear
		:filter-option="false"
		:options="selectOptions"
		:placeholder="placeholder"
		:loading="loading"
		@update:model-value="$emit('update:modelValue', $event)"
		@search="search"
	/>
</template>

<script setup>
import { useEmployeeSearch } from "../composables/useEmployeeSearch";

const props = defineProps({
	modelValue: [String, Number],
	company: String,
	placeholder: { type: String, default: "员工姓名/拼音" },
});

defineEmits(["update:modelValue"]);

const { selectOptions, loading, search } = useEmployeeSearch(() => props.company);
</script>
