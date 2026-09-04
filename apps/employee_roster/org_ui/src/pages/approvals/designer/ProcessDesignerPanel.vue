<template>
	<div class="apd-process">
		<div class="apd-process-toolbar">
			<a-space>
				<a-button size="small" @click="addNode('approver')">加审批节点</a-button>
				<a-button size="small" @click="addNode('cc')">加抄送节点</a-button>
				<a-button size="small" @click="addNode('condition')">加条件分支</a-button>
			</a-space>
		</div>
		<div class="apd-process-chain">
			<div v-for="(node, idx) in localNodes" :key="node.id" class="apd-node-wrap">
				<div
					class="apd-node"
					:class="[`apd-node--${node.type}`, { active: selectedId === node.id }]"
					@click="selectedId = node.id"
				>
					<div class="apd-node-title">{{ node.label || node.type }}</div>
					<div class="apd-node-meta">{{ nodeHint(node) }}</div>
					<a-space v-if="node.type !== 'start' && node.type !== 'end'" style="margin-top: 8px">
						<a-button size="mini" @click.stop="move(idx, -1)">上移</a-button>
						<a-button size="mini" @click.stop="move(idx, 1)">下移</a-button>
						<a-button size="mini" status="danger" @click.stop="remove(idx)">删除</a-button>
					</a-space>
				</div>
				<div v-if="idx < localNodes.length - 1" class="apd-node-arrow">↓</div>
			</div>
		</div>

		<a-drawer
			:visible="!!selected"
			:width="380"
			unmount-on-close
			@cancel="selectedId = ''"
			:footer="false"
			title="节点配置"
		>
			<template v-if="selected">
				<a-form layout="vertical" size="small">
					<a-form-item label="名称">
						<a-input v-model="selected.label" />
					</a-form-item>
					<template v-if="selected.type === 'approver' || selected.type === 'cc'">
						<a-form-item label="审批人类型">
							<a-select v-model="selected.props.assignee_type">
								<a-option value="reports_to">直属上级</a-option>
								<a-option value="role">角色</a-option>
								<a-option value="user">指定用户</a-option>
								<a-option value="employee">指定员工</a-option>
								<a-option value="department_head">部门负责人</a-option>
							</a-select>
						</a-form-item>
						<a-form-item v-if="selected.props.assignee_type === 'role'" label="角色">
							<a-input v-model="selected.props.role" placeholder="HR Manager" />
						</a-form-item>
						<a-form-item v-if="selected.props.assignee_type === 'user'" label="用户">
							<a-input v-model="selected.props.user" placeholder="user@example.com" />
						</a-form-item>
						<a-form-item v-if="selected.props.assignee_type === 'employee'" label="员工 ID">
							<a-input v-model="selected.props.employee" />
						</a-form-item>
						<a-form-item v-if="selected.type === 'approver'" label="会签模式">
							<a-select v-model="selected.props.mode">
								<a-option value="or">或签（一人即可）</a-option>
								<a-option value="and">会签（全部同意）</a-option>
							</a-select>
						</a-form-item>
					</template>
					<template v-if="selected.type === 'condition'">
						<a-form-item label="分支说明">
							<div class="apd-hint">配置表达式，如 days > 3；可设默认分支</div>
						</a-form-item>
						<div
							v-for="(b, bi) in selected.props.branches || []"
							:key="b.id"
							class="apd-branch"
						>
							<a-input v-model="b.label" placeholder="分支名" style="margin-bottom: 6px" />
							<a-input v-model="b.expression" placeholder="表达式 days > 3" style="margin-bottom: 6px" />
							<a-switch
								:model-value="!!b.is_default"
								@change="(v) => (b.is_default = v ? 1 : 0)"
							/>
							<span style="margin-left: 8px; font-size: 12px">默认分支</span>
							<a-button size="mini" status="danger" @click="removeBranch(bi)">删分支</a-button>
						</div>
						<a-button size="small" long style="margin-top: 8px" @click="addBranch">加分支</a-button>
					</template>
					<template v-if="selected.type === 'approver'">
						<a-divider>字段权限</a-divider>
						<div v-for="f in fields" :key="f.key" class="apd-perm-row">
							<span>{{ f.label }}</span>
							<a-select
								:model-value="(selected.props.field_perms || {})[f.key] || 'read'"
								size="mini"
								style="width: 110px"
								@change="(v) => setPerm(f.key, v)"
							>
								<a-option value="hide">隐藏</a-option>
								<a-option value="read">只读</a-option>
								<a-option value="write">可写</a-option>
							</a-select>
						</div>
					</template>
				</a-form>
			</template>
		</a-drawer>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
	nodes: { type: Array, default: () => [] },
	fields: { type: Array, default: () => [] },
});
const emit = defineEmits(["update:nodes"]);

const selectedId = ref("");
const localNodes = computed({
	get: () => props.nodes,
	set: (v) => emit("update:nodes", v),
});

const selected = computed(() => localNodes.value.find((n) => n.id === selectedId.value));

watch(
	localNodes,
	(list) => {
		list.forEach((n) => {
			if (!n.props) n.props = {};
			if ((n.type === "approver" || n.type === "cc") && !n.props.assignee_type) {
				n.props.assignee_type = "reports_to";
			}
			if (n.type === "approver" && !n.props.mode) n.props.mode = "or";
			if (n.type === "approver" && !n.props.field_perms) n.props.field_perms = {};
			if (n.type === "condition" && !n.props.branches) n.props.branches = [];
		});
	},
	{ deep: true, immediate: true }
);

function uid(prefix) {
	return `${prefix}_${Math.random().toString(36).slice(2, 8)}`;
}

function nodeHint(node) {
	const p = node.props || {};
	if (node.type === "approver" || node.type === "cc") {
		return p.assignee_type || "reports_to";
	}
	if (node.type === "condition") {
		return `${(p.branches || []).length} 个分支`;
	}
	return node.type;
}

function addNode(type) {
	const nodes = [...localNodes.value];
	const endIdx = nodes.findIndex((n) => n.type === "end");
	const insertAt = endIdx >= 0 ? endIdx : nodes.length;
	const node = {
		id: uid(type),
		type,
		label: type === "approver" ? "审批人" : type === "cc" ? "抄送" : "条件分支",
		props:
			type === "condition"
				? {
						branches: [
							{ id: uid("branch"), label: "条件1", expression: "", is_default: 0, nodes: [] },
							{ id: uid("branch"), label: "默认", expression: "", is_default: 1, nodes: [] },
						],
					}
				: {
						assignee_type: "reports_to",
						mode: "or",
						field_perms: {},
					},
	};
	nodes.splice(insertAt, 0, node);
	localNodes.value = nodes;
	selectedId.value = node.id;
}

function remove(idx) {
	const n = localNodes.value[idx];
	if (!n || n.type === "start" || n.type === "end") return;
	localNodes.value = localNodes.value.filter((_, i) => i !== idx);
	selectedId.value = "";
}

function move(idx, delta) {
	const n = localNodes.value[idx];
	if (!n || n.type === "start" || n.type === "end") return;
	const to = idx + delta;
	if (to <= 0 || to >= localNodes.value.length - 1) return;
	const next = [...localNodes.value];
	const tmp = next[idx];
	next[idx] = next[to];
	next[to] = tmp;
	localNodes.value = next;
}

function addBranch() {
	if (!selected.value) return;
	if (!selected.value.props.branches) selected.value.props.branches = [];
	selected.value.props.branches.push({
		id: uid("branch"),
		label: "新分支",
		expression: "",
		is_default: 0,
		nodes: [],
	});
}

function removeBranch(bi) {
	selected.value.props.branches.splice(bi, 1);
}

function setPerm(key, val) {
	if (!selected.value.props.field_perms) selected.value.props.field_perms = {};
	selected.value.props.field_perms[key] = val;
}
</script>
