<template>
	<li class="oc-tree-item">
		<div class="oc-tree-row" :class="{ 'is-selected': selectedKey === node.key }" role="button" tabindex="0"
			@click="$emit('select', node.key)" @keydown.enter="$emit('select', node.key)" @keydown.space.prevent="$emit('select', node.key)">
			<a-button type="text" size="mini" class="oc-tree-toggle" :class="{ 'is-placeholder': !hasChildren }"
				:aria-label="expanded ? '收起下级组织' : '展开下级组织'" @click.stop="hasChildren && $emit('toggle', node.key)">
				<template #icon><icon-down v-if="hasChildren && expanded" /><icon-right v-else-if="hasChildren" /></template>
			</a-button>
			<icon-home v-if="node.is_company" class="oc-tree-icon" />
			<icon-folder v-else class="oc-tree-icon" />
			<span class="oc-tree-title" :title="node.title">{{ node.title }}</span>
			<span v-if="showCount" class="oc-tree-count">{{ Number(node.employee_count || 0) }} 人</span>
		</div>
		<ul v-if="expanded && hasChildren" class="oc-tree-children">
			<OrgHierarchyNode v-for="child in orgChildren" :key="child.key" :node="child" :selected-key="selectedKey"
				:expanded-keys="expandedKeys" @select="$emit('select', $event)" @toggle="$emit('toggle', $event)" />
		</ul>
	</li>
</template>

<script setup>
import { computed } from "vue";
const props = defineProps({ node: { type: Object, required: true }, selectedKey: { type: String, default: "" },
	expandedKeys: { type: Array, default: () => [] } });
defineEmits(["select", "toggle"]);
const orgChildren = computed(() => (props.node.children || []).filter((child) => !child.is_employee));
const hasChildren = computed(() => orgChildren.value.length > 0);
const expanded = computed(() => props.expandedKeys.includes(props.node.key));
const isGroup = computed(() => props.node.org_type === "组" || String(props.node.title || "").trim().endsWith("组"));
const showCount = computed(() => props.node.is_company || !isGroup.value);
</script>

<style scoped>
.oc-tree-item, .oc-tree-children { margin: 0; padding: 0; list-style: none; }
.oc-tree-row { display: flex; height: 38px; align-items: center; gap: 7px; padding: 0 10px 0 2px; border-radius: 6px;
	color: var(--color-text-1); cursor: pointer; transition: background-color .15s ease; }
.oc-tree-row:hover { background: var(--color-fill-1); }
.oc-tree-row.is-selected { background: rgb(var(--arcoblue-1)); color: rgb(var(--arcoblue-6)); }
.oc-tree-row:focus-visible { outline: 2px solid rgb(var(--arcoblue-4)); outline-offset: -2px; }
.oc-tree-toggle { width: 24px; height: 24px; min-width: 24px; padding: 0; color: var(--color-text-3); }
.oc-tree-toggle.is-placeholder { pointer-events: none; visibility: hidden; }
.oc-tree-icon { flex: 0 0 auto; color: currentColor; font-size: 16px; }
.oc-tree-title { min-width: 0; flex: 1; overflow: hidden; font-size: 14px; font-weight: 500; text-overflow: ellipsis; white-space: nowrap; }
.oc-tree-count { flex: 0 0 auto; color: var(--color-text-3); font-size: 12px; font-variant-numeric: tabular-nums; }
.oc-tree-children { position: relative; margin-left: 14px; padding-left: 14px; }
.oc-tree-children::before { position: absolute; top: 0; bottom: 12px; left: 0; width: 1px; background: var(--color-border-2); content: ""; }
</style>
