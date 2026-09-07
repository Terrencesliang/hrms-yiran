<template>
	<div class="od-canvas-shell">
		<div ref="viewport" class="od-canvas-viewport">
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

		<div class="od-legend" aria-label="架构图图例">
			<span><i class="is-company"></i>公司</span>
			<span><i class="is-department"></i>部门</span>
			<span><i class="is-group"></i>组</span>
			<span><i class="is-member"></i>成员</span>
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

const emit = defineEmits(["toggle", "open-detail", "open-member"]);

const viewport = ref(null);
const canvas = ref(null);

provide("odTree", {
	isExpanded: (name) => props.isExpanded(name),
	toggle: (name) => emit("toggle", name),
	openDetail: (unit) => emit("open-detail", unit),
	openMember: (member) => emit("open-member", member),
});

/** 返回让整棵树放进视口的缩放百分比（宽高取较小比例，最大 100%）。 */
function fit() {
	const host = viewport.value;
	const content = canvas.value;
	if (!content || !host) return 100;

	const scale = props.zoom / 100;
	const naturalWidth = content.scrollWidth / scale;
	const naturalHeight = content.scrollHeight / scale;
	const padX = 48;
	const padY = 40;
	const availableW = Math.max(1, host.clientWidth - padX);
	const availableH = Math.max(1, host.clientHeight - padY);
	const scaleW = (availableW / naturalWidth) * 100;
	const scaleH = (availableH / naturalHeight) * 100;

	return Math.max(50, Math.min(100, Math.floor(Math.min(scaleW, scaleH))));
}

/** 将整棵树居中到视口内，便于一屏看到全部节点。 */
function centerTree(behavior = "auto") {
	const host = viewport.value;
	const content = canvas.value;
	if (!host || !content) return;

	const hostRect = host.getBoundingClientRect();
	const rect = content.getBoundingClientRect();
	const offsetX = rect.left + rect.width / 2 - (hostRect.left + hostRect.width / 2);
	const offsetY = rect.top + rect.height / 2 - (hostRect.top + hostRect.height / 2);
	host.scrollTo({
		left: host.scrollLeft + offsetX,
		top: host.scrollTop + offsetY,
		behavior,
	});
}

/** 树比视口宽时根节点在正中，需要把视口滚到公司节点下方。 */
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
