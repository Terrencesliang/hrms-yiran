<template>
	<HrPage title="架构图" class="od-page">
		<OrgDiagramToolbar
			:company="company"
			:company-options="companyOptions"
			:keyword="keyword"
			:view-mode="viewMode"
			:depth="depth"
			:zoom="zoom"
			@update:company="company = $event"
			@update:keyword="keyword = $event"
			@update:view-mode="viewMode = $event"
			@update:depth="depth = $event"
			@company-change="loadDiagram"
			@zoom-out="setZoom(zoom - 10)"
			@zoom-in="setZoom(zoom + 10)"
			@fit="fitDiagram"
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
			/>
		</a-spin>
	</HrPage>
</template>

<script setup>
import { nextTick, ref, watch } from "vue";
import HrPage from "../../components/HrPage.vue";
import OrgDiagramCanvas from "./OrgDiagramCanvas.vue";
import OrgDiagramToolbar from "./OrgDiagramToolbar.vue";
import { useOrgDiagram } from "./composables/useOrgDiagram";

const diagramCanvas = ref(null);
const {
	loading,
	company,
	data,
	keyword,
	viewMode,
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

function fitDiagram() {
	setZoom(diagramCanvas.value?.fit?.() || 100);
	nextTick(() => diagramCanvas.value?.centerRoot?.("smooth"));
}

watch([loading, depth], ([isLoading]) => {
	if (!isLoading) nextTick(() => diagramCanvas.value?.centerRoot?.());
});
</script>
