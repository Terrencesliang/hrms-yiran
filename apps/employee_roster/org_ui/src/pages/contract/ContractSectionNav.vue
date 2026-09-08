<template>
	<a-card :bordered="false" class="hr-desk-toolbar-card contract-section-nav-card">
		<div class="contract-section-nav">
			<a-tabs
				:active-key="activeKey"
				type="rounded"
				hide-content
				class="contract-section-tabs"
				@change="navigate"
			>
				<a-tab-pane v-for="item in items" :key="item.route" :title="item.label" />
			</a-tabs>
			<span class="contract-section-hint">{{ hint }}</span>
		</div>
	</a-card>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	group: {
		type: String,
		required: true,
		validator: (value) => ["signing", "settings"].includes(value),
	},
	activeKey: {
		type: String,
		required: true,
	},
});

const groups = {
	signing: {
		hint: "按签署状态快速切换合同",
		items: [
			{ label: "签署中", route: "contract-signing-pending" },
			{ label: "已签署", route: "contract-signing-signed" },
			{ label: "已作废", route: "contract-signing-void" },
		],
	},
	settings: {
		hint: "统一管理合同印章、模板与合同包",
		items: [
			{ label: "企业印章", route: "contract-seals" },
			{ label: "合同模板", route: "contract-templates" },
			{ label: "合同包", route: "contract-packages" },
		],
	},
};

const items = computed(() => groups[props.group]?.items || []);
const hint = computed(() => groups[props.group]?.hint || "");

function navigate(route) {
	if (!route || route === props.activeKey) return;
	if (window.frappe?.set_route) {
		window.frappe.set_route(route);
		return;
	}
	window.location.assign(`/app/${route}`);
}
</script>
