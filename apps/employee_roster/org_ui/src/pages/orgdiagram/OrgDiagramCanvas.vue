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

/** 返回让整棵树横向放进视口的缩放百分比。 */
function fit() {
	const tree = canvas.value?.querySelector(".od-tree");
	const host = viewport.value;
	if (!tree || !host) return 100;
	const naturalWidth = tree.getBoundingClientRect().width / (props.zoom / 100);
	const available = host.clientWidth - 48;
	return Math.max(50, Math.min(100, Math.floor((available / naturalWidth) * 100)));
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

defineExpose({ fit, centerRoot });
</script>
