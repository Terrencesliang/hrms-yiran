<template>
	<div class="arco-org-ui hr-page">
		<div class="hr-page-body-stack">
			<header v-if="showHeader" class="hr-page-header">
				<div class="hr-page-heading">
					<nav v-if="breadcrumbItems.length" class="hr-page-breadcrumb" aria-label="页面路径">
						<a-breadcrumb>
							<a-breadcrumb-item v-for="(item, index) in breadcrumbItems" :key="`${item.label}-${index}`">
								<a
									v-if="item.route"
									href="#"
									class="hr-page-breadcrumb-link"
									@click.prevent="navigateHrRoute(item.route)"
								>
									{{ item.label }}
								</a>
								<span v-else>{{ item.label }}</span>
							</a-breadcrumb-item>
						</a-breadcrumb>
					</nav>
					<h1 v-if="showPageTitle" class="oc-page-title">{{ title }}</h1>
					<p v-if="showSubtitle" class="hr-page-subtitle">{{ subtitle }}</p>
				</div>
				<div v-if="$slots.actions" class="hr-page-actions">
					<slot name="actions" />
				</div>
			</header>
			<slot />
		</div>
	</div>
</template>

<script setup>
import { computed, useSlots } from "vue";
import { navigateHrRoute } from "../utils/hrBreadcrumbs.js";

const props = defineProps({
	title: String,
	subtitle: String,
	breadcrumbs: {
		type: Array,
		default: () => [],
	},
});

const slots = useSlots();
const breadcrumbItems = computed(() => props.breadcrumbs || []);
const showPageTitle = computed(() => props.title && !breadcrumbItems.value.length);
const showSubtitle = computed(() => props.subtitle && !breadcrumbItems.value.length);
const showHeader = computed(
	() =>
		showPageTitle.value ||
		showSubtitle.value ||
		breadcrumbItems.value.length ||
		!!slots.actions,
);
</script>
