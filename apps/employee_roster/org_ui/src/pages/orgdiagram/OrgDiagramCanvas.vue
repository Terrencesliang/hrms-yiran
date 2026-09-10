<template>
	<div class="od-canvas-shell">
		<div ref="viewport" class="od-canvas-viewport">
			<div class="od-canvas-stage">
				<div ref="canvas" class="od-canvas" :style="{ zoom: zoom / 100 }">
					<ul class="od-tree">
						<li class="od-tree-item is-root">
							<OrgCompanyNode
								:company-name="data.company_name"
								:manager="data.general_manager_info || {}"
								:employee-count="Number(data.company_emp_count || 0)"
								:department-count="departments.length"
							/>
							<ul v-if="departments.length" class="od-tree-children">
								<OrgTreeNode
									v-for="department in departments"
									:key="department.name || department.title"
									:unit="department"
									:level="1"
								/>
							</ul>
						</li>
					</ul>
				</div>
			</div>
		</div>

		<div class="od-legend" aria-label="架构图图例">
			<span><i class="is-company"></i>公司</span>
			<span><i class="is-department"></i>部门</span>
			<span><i class="is-group"></i>组</span>
			<span><i class="is-member"></i>成员</span>
		</div>

		<div class="od-canvas-controls" role="toolbar" aria-label="视图控制">
			<a-tooltip content="缩小">
				<a-button type="text" size="mini" aria-label="缩小架构图" @click="$emit('zoom-out')">
					<template #icon><icon-minus /></template>
				</a-button>
			</a-tooltip>
			<span class="od-canvas-controls__zoom">{{ zoom }}%</span>
			<a-tooltip content="放大">
				<a-button type="text" size="mini" aria-label="放大架构图" @click="$emit('zoom-in')">
					<template #icon><icon-plus /></template>
				</a-button>
			</a-tooltip>
			<span class="od-canvas-controls__sep" aria-hidden="true" />
			<a-tooltip content="适应视图">
				<a-button type="text" size="mini" aria-label="适应视图" @click="$emit('fit')">
					<template #icon><icon-fullscreen /></template>
				</a-button>
			</a-tooltip>
		</div>
	</div>
</template>

<script setup>
import { provide, ref } from "vue";
import OrgCompanyNode from "./OrgCompanyNode.vue";
import OrgTreeNode from "./OrgTreeNode.vue";

const props = defineProps({
	data: { type: Object, required: true },
	departments: { type: Array, default: () => [] },
	isExpanded: { type: Function, required: true },
	zoom: { type: Number, default: 100 },
});

const emit = defineEmits(["toggle", "open-detail", "open-member", "zoom-out", "zoom-in", "fit"]);

const viewport = ref(null);
const canvas = ref(null);

provide("odTree", {
	isExpanded: (name) => props.isExpanded(name),
	toggle: (name) => emit("toggle", name),
	openDetail: (unit) => emit("open-detail", unit),
	openMember: (member) => emit("open-member", member),
});

/** 按画布/屏幕宽度适配默认缩放；contain 时同时考虑高度（适应视图）。 */
function fit(mode = "auto") {
	const host = viewport.value;
	const content = canvas.value;
	if (!content || !host) return 100;

	const ZOOM_MIN = 50;
	const ZOOM_MAX = 150;
	const scale = props.zoom / 100 || 1;
	const naturalWidth = content.scrollWidth / scale;
	const naturalHeight = content.scrollHeight / scale;
	const availableW = Math.max(1, host.clientWidth - 64);
	const availableH = Math.max(1, host.clientHeight - 56);
	const scaleW = (availableW / naturalWidth) * 100;
	const scaleH = (availableH / naturalHeight) * 100;

	const next = mode === "contain"
		? Math.min(scaleW, scaleH * 0.92)
		: scaleW;

	return Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, Math.round(next)));
}

/** 水平居中；垂直保持在顶部。 */
function centerTree(behavior = "auto") {
	const host = viewport.value;
	const content = canvas.value;
	if (!host || !content) return;

	const hostRect = host.getBoundingClientRect();
	const rect = content.getBoundingClientRect();
	const offsetX = rect.left + rect.width / 2 - (hostRect.left + hostRect.width / 2);
	host.scrollTo({
		left: host.scrollLeft + offsetX,
		top: 0,
		behavior,
	});
}

function centerRoot(behavior = "auto") {
	const host = viewport.value;
	const company = canvas.value?.querySelector(".od-company-node");
	if (!host || !company) return;
	const hostRect = host.getBoundingClientRect();
	const rect = company.getBoundingClientRect();
	const offset = rect.left + rect.width / 2 - (hostRect.left + hostRect.width / 2);
	host.scrollTo({ left: host.scrollLeft + offset, top: 0, behavior });
}

defineExpose({ fit, centerTree, centerRoot });
</script>
