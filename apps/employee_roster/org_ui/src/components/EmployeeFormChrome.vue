<template>
	<a-config-provider :locale="zhCN">
		<div class="arco-emp-form-chrome arco-emp-pro" :class="{ 'is-compact': !state.show_overview }">
			<EmployeeHeader :state="state" />
		</div>

			<Teleport v-if="overviewReady" to="#employee-arco-overview-root">
				<transition name="emp-overview" appear>
					<EmployeeOverviewPanel
						v-if="state.show_overview"
						:state="state"
						:handlers="handlers"
						@navigate="onNavigate"
					/>
				</transition>
			</Teleport>
	</a-config-provider>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import EmployeeHeader from "./employee-detail/EmployeeHeader.vue";
import EmployeeOverviewPanel from "./EmployeeOverviewPanel.vue";

const props = defineProps({
	state: { type: Object, required: true },
	handlers: { type: Object, default: () => ({}) },
});

const overviewReady = ref(false);
let observer = null;

function refreshOverviewTarget() {
	overviewReady.value = !!document.querySelector("#employee-arco-overview-root");
}

onMounted(() => {
	refreshOverviewTarget();
	observer = new MutationObserver(refreshOverviewTarget);
	observer.observe(document.body, { childList: true, subtree: true });
});

onUnmounted(() => observer?.disconnect?.());

function onNavigate(target) {
	props.handlers?.onNavigate?.(target);
}
</script>
