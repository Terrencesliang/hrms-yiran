<template>
	<a-select
		:model-value="modelValue"
		allow-search
		allow-clear
		:filter-option="false"
		:options="options"
		:placeholder="placeholder"
		:loading="loading"
		@update:model-value="$emit('update:modelValue', $event)"
		@search="onSearch"
		@popup-visible-change="onPopup"
	/>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { call } from "../api/frappe";

const props = defineProps({
	modelValue: { type: String, default: "" },
	doctype: { type: String, default: "User" },
	placeholder: { type: String, default: "搜索并选择" },
	filters: { type: Object, default: null },
});

defineEmits(["update:modelValue"]);

const options = ref([]);
const loading = ref(false);
let timer = null;

async function search(txt = "") {
	loading.value = true;
	try {
		const rows =
			(await call("frappe.desk.search.search_link", {
				doctype: props.doctype,
				txt: txt || "",
				page_length: 20,
				filters: props.filters || undefined,
			})) || [];
		options.value = rows.map((row) => ({
			value: row.value,
			label: row.description ? `${row.value} · ${row.description}` : row.value,
		}));
		// Keep current value visible even if not in search results
		if (props.modelValue && !options.value.some((o) => o.value === props.modelValue)) {
			options.value.unshift({ value: props.modelValue, label: props.modelValue });
		}
	} finally {
		loading.value = false;
	}
}

function onSearch(txt) {
	clearTimeout(timer);
	timer = setTimeout(() => search(txt), 200);
}

function onPopup(visible) {
	if (visible && !options.value.length) search("");
}

onMounted(() => {
	if (props.modelValue) search(props.modelValue);
});
</script>
