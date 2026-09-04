<template>
	<li class="od-tree-item" :class="`is-level-${level}`">
		<OrgDepartmentNode
			ref="card"
			:unit="unit"
			:level="level"
			:expanded="expanded"
			:expandable="hasChildren"
			@toggle="onToggle"
			@open-detail="tree.openDetail(unit)"
		/>
		<ul v-if="expanded && hasChildren" class="od-tree-children">
			<OrgTreeNode v-for="child in unit.children" :key="child.name" :unit="child" :level="level + 1" />
			<li v-if="unit.members?.length" class="od-tree-item is-members">
				<OrgMemberList
					:members="unit.members"
					:title="unit.children?.length ? '直属成员' : '成员'"
					@open-member="tree.openMember"
				/>
			</li>
		</ul>
	</li>
</template>

<script setup>
import { computed, inject, nextTick, ref } from "vue";
import OrgDepartmentNode from "./OrgDepartmentNode.vue";
import OrgMemberList from "./OrgMemberList.vue";

const props = defineProps({
	unit: { type: Object, required: true },
	level: { type: Number, default: 1 },
});

const tree = inject("odTree");
const card = ref(null);

const hasChildren = computed(
	() => (props.unit.children || []).length > 0 || (props.unit.members || []).length > 0
);
const expanded = computed(() => tree.isExpanded(props.unit.name));

function onToggle() {
	const opening = !expanded.value;
	tree.toggle(props.unit.name);
	if (!opening) return;
	// 展开后子树会把父节点推开，把当前卡片重新拉回视野
	nextTick(() => card.value?.$el?.scrollIntoView?.({ inline: "center", block: "nearest", behavior: "smooth" }));
}
</script>
