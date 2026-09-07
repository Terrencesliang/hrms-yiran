<template>
	<HrPage
		:title="title"
		:breadcrumbs="resolvedBreadcrumbs"
		:subtitle="subtitle"
		:class="pageClass"
	>
		<template v-if="$slots.actions" #actions>
			<slot name="actions" />
		</template>
	</HrPage>
</template>

<script setup>
import { computed } from "vue";
import HrPage from "./HrPage.vue";
import { hrPageBreadcrumbs, HR_MODULE_LABEL } from "../utils/hrBreadcrumbs.js";

const props = defineProps({
	title: { type: String, required: true },
	module: { type: String, default: HR_MODULE_LABEL },
	breadcrumbs: { type: Array, default: null },
	subtitle: { type: String, default: "" },
	moduleClass: { type: String, default: "" },
});

const resolvedBreadcrumbs = computed(
	() => props.breadcrumbs || hrPageBreadcrumbs(props.title, props.module),
);

const pageClass = computed(() => {
	const parts = ["hr-desk-page", "hr-desk-header-only"];
	if (props.moduleClass) parts.push(props.moduleClass);
	return parts.join(" ");
});
</script>
