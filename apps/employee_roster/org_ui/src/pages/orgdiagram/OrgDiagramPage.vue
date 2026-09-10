<template>
	<HrPage :breadcrumbs="breadcrumbs" class="hr-orgdiagram hr-analysis">
		<div class="hr-analysis-stack">
			<OrgDiagramToolbar
				:company="company"
				:company-options="companyOptions"
				:keyword="keyword"
				:depth="depth"
				@update:company="company = $event"
				@update:keyword="keyword = $event"
				@update:depth="depth = $event"
				@company-change="loadDiagram"
				@export="exportDiagram"
			/>

			<a-spin :loading="loading" class="od-loading">
				<a-empty v-if="!loading && !departments.length" description="暂无组织架构数据" />
				<OrgDiagramCanvas
					v-else
					ref="diagramCanvas"
					:data="data"
					:departments="departments"
					:is-expanded="isExpanded"
					:zoom="zoom"
					@toggle="toggleNode"
					@open-detail="openUnitDetail"
					@open-member="openMember"
					@zoom-out="setZoom(zoom - 10)"
					@zoom-in="setZoom(zoom + 10)"
					@fit="() => fitDiagram('smooth', 'contain')"
				/>
			</a-spin>
		</div>
	</HrPage>
</template>

<script setup>
import { nextTick, ref, watch } from "vue";
import HrPage from "../../components/HrPage.vue";
import { hrPageBreadcrumbs } from "../../utils/hrBreadcrumbs.js";
import OrgDiagramCanvas from "./OrgDiagramCanvas.vue";
import OrgDiagramToolbar from "./OrgDiagramToolbar.vue";
import { useOrgDiagram } from "./composables/useOrgDiagram";

const breadcrumbs = hrPageBreadcrumbs("架构图");

const diagramCanvas = ref(null);
const {
	loading,
	company,
	data,
	keyword,
	depth,
	zoom,
	companyOptions,
	departments,
	isExpanded,
	toggleNode,
	loadDiagram,
	setZoom,
	exportDiagram,
	openUnitDetail,
	openMember,
} = useOrgDiagram();

function fitDiagram(behavior = "smooth", mode = "auto") {
	if (behavior && typeof behavior === "object") {
		behavior = "smooth";
		mode = "contain";
	}
	const nextZoom = diagramCanvas.value?.fit?.(mode) || 100;
	setZoom(nextZoom);
	nextTick(() => {
		requestAnimationFrame(() => {
			diagramCanvas.value?.centerTree?.(behavior);
		});
	});
}

function scheduleFit(behavior = "auto") {
	nextTick(() => {
		requestAnimationFrame(() => {
			requestAnimationFrame(() => fitDiagram(behavior, "auto"));
		});
	});
}

watch(loading, (isLoading, wasLoading) => {
	if (!isLoading && wasLoading) {
		scheduleFit("auto");
	}
});

watch(depth, () => {
	if (!loading.value) {
		scheduleFit("auto");
	}
});
</script>
