<template>
	<HrPage title="人员角色分配" subtitle="按组织架构为企业人员配置业务角色" class="role-assignment-page">
		<template #actions>
			<a-select v-model="company" class="ra-company-select" :disabled="!context?.is_platform_admin" @change="loadContext">
				<a-option v-for="item in context?.companies || []" :key="item" :value="item">{{ item }}</a-option>
			</a-select>
		</template>

		<a-spin :loading="loading" class="ra-loading">
			<div v-if="context" class="ra-workspace">
				<aside class="ra-org-panel">
					<header class="ra-panel-head">
						<div><strong>组织架构</strong><span>{{ context.organization_count }} 个组织</span></div>
						<a-input v-model="orgKeyword" allow-clear placeholder="搜索部门或组别">
							<template #prefix><icon-search /></template>
						</a-input>
					</header>
					<div v-if="filteredOrgTree.length" class="ra-org-scroll">
						<ul class="ra-org-tree">
							<OrgHierarchyNode
								v-for="node in filteredOrgTree"
								:key="node.key"
								:node="node"
								:selected-key="selectedOrgKey"
								:expanded-keys="expandedKeys"
								@select="selectOrganization"
								@toggle="toggleOrganization"
							/>
						</ul>
					</div>
					<a-empty v-else description="没有匹配的组织" class="ra-empty" />
				</aside>

				<section class="ra-member-panel">
					<header class="ra-member-head">
						<div><strong>{{ selectedOrganization?.title || "请选择组织" }}</strong><span>{{ members.length }} 名成员</span></div>
						<a-input v-model="memberKeyword" allow-clear placeholder="搜索成员" class="ra-member-search">
							<template #prefix><icon-search /></template>
						</a-input>
					</header>
					<div v-if="members.length" class="ra-member-tools">
						<a-checkbox :model-value="allVisibleChecked" :indeterminate="partVisibleChecked" @change="toggleAllVisible(Boolean($event))">
							已选择 {{ checkedUsers.size }} 人
						</a-checkbox>
						<a-button v-if="checkedUsers.size" type="primary" size="small" @click="startBulk">批量分配</a-button>
					</div>
					<div v-if="members.length" class="ra-member-list">
						<button
							v-for="member in filteredMembers"
							:key="member.employee"
							type="button"
							class="ra-member-row"
							:class="{ active: !bulkMode && member.employee === selectedEmployeeId, disabled: !member.user_id }"
							@click="selectMember(member)"
						>
							<a-checkbox
								:model-value="Boolean(member.user_id && checkedUsers.has(member.user_id))"
								:disabled="!member.user_id"
								@click.stop
								@change="toggleMember(member, Boolean($event))"
							/>
							<a-avatar :size="36" :style="{ backgroundColor: avatarColor(member.title) }">{{ avatarText(member.title) }}</a-avatar>
							<span class="ra-member-main"><strong>{{ member.title }}</strong><small>{{ member.employee_number || member.employee }}</small></span>
							<span class="ra-member-job">{{ member.designation || "未填写岗位" }}</span>
							<span class="ra-member-roles">
								<a-tag v-if="!member.user_id" color="gray" size="small">未绑定账号</a-tag>
								<template v-else-if="member.assigned_roles?.length">
									<a-tag v-for="role in member.assigned_roles.slice(0, 1)" :key="role" color="arcoblue" size="small">{{ roleTitle(role) }}</a-tag>
									<small v-if="member.assigned_roles.length > 1">+{{ member.assigned_roles.length - 1 }}</small>
								</template>
								<a-tag v-else color="orange" size="small">未分配</a-tag>
							</span>
						</button>
						<a-empty v-if="!filteredMembers.length" description="没有匹配的成员" class="ra-empty" />
					</div>
					<a-empty v-else description="该组织暂无在职成员" class="ra-empty" />
					<footer class="ra-member-foot">已显示 {{ filteredMembers.length }} 名成员</footer>
				</section>

				<section class="ra-role-panel">
					<template v-if="activeTarget">
						<header class="ra-profile">
							<a-avatar :size="44" :style="{ backgroundColor: avatarColor(activeTarget.title) }">{{ bulkMode ? checkedUsers.size : avatarText(activeTarget.title) }}</a-avatar>
							<div>
								<strong>{{ bulkMode ? `批量分配（${checkedUsers.size} 人）` : activeTarget.title }}</strong>
								<span v-if="!bulkMode">{{ activeTarget.employee_number || activeTarget.employee }} <i></i> 在职</span>
								<small v-if="!bulkMode">{{ organizationPath }}<template v-if="activeTarget.designation"> · {{ activeTarget.designation }}</template></small>
								<small v-else>将为选中的员工设置相同角色</small>
							</div>
						</header>

						<div class="ra-role-content">
							<div class="ra-role-title"><strong>角色分配</strong><span>已选 {{ selectedRoles.size }} 个</span></div>
							<div v-if="selectedRoleItems.length" class="ra-selected-tags">
								<a-tag v-for="role in selectedRoleItems" :key="role.name" closable color="arcoblue" @close="toggleRole(role.name, false)">{{ role.role_title }}</a-tag>
							</div>
							<a-input v-model="roleKeyword" allow-clear placeholder="搜索角色名称">
								<template #prefix><icon-search /></template>
							</a-input>
							<a-radio-group v-model="roleCategory" type="button" size="small" class="ra-role-filter">
								<a-radio value="全部">全部</a-radio><a-radio value="系统角色">系统角色</a-radio><a-radio value="自定义角色">自定义角色</a-radio>
							</a-radio-group>
							<div class="ra-role-list">
								<label v-for="role in filteredRoles" :key="role.name" class="ra-role-row" :class="{ active: selectedRoles.has(role.name) }">
									<a-checkbox :model-value="selectedRoles.has(role.name)" @change="toggleRole(role.name, Boolean($event))" />
									<span><strong>{{ role.role_title }}</strong><small>{{ role.description || "自定义菜单访问角色" }}</small></span>
									<a-tag color="gray" size="small">{{ role.is_system_role ? "系统" : "自定义" }}</a-tag>
								</label>
								<a-empty v-if="!filteredRoles.length" description="没有匹配的角色" class="ra-empty" />
							</div>
							<p class="ra-role-note"><icon-info-circle />平台超级管理员不支持企业内分配</p>
						</div>

						<footer class="ra-actions">
							<span>角色修改后立即生效</span>
							<div><a-button :disabled="!dirty" @click="resetRoles">取消</a-button><a-button type="primary" :loading="saving" :disabled="!canSave" @click="saveRoles">保存</a-button></div>
						</footer>
					</template>
					<a-empty v-else description="请从左侧选择一名已绑定账号的员工" class="ra-empty" />
				</section>
			</div>
		</a-spin>
	</HrPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Message } from "@arco-design/web-vue";
import { IconInfoCircle, IconSearch } from "@arco-design/web-vue/es/icon";
import HrPage from "../../components/HrPage.vue";
import OrgHierarchyNode from "../orgchart/OrgHierarchyNode.vue";
import { assignBusinessRoles, assignBusinessRolesBulk, getRoleAssignmentContext, type BusinessRole, type RoleAssignmentContext, type RoleAssignmentNode } from "../../api/permissionManagement";
import "./role-assignment.css";

const context = ref<RoleAssignmentContext | null>(null);
const company = ref("");
const loading = ref(false);
const saving = ref(false);
const orgKeyword = ref("");
const memberKeyword = ref("");
const roleKeyword = ref("");
const roleCategory = ref("全部");
const selectedOrgKey = ref("");
const selectedEmployeeId = ref("");
const expandedKeys = ref<string[]>([]);
const checkedUsers = ref(new Set<string>());
const bulkMode = ref(false);
const selectedRoles = ref(new Set<string>());
const savedRoles = ref(new Set<string>());

function withKeys(nodes: RoleAssignmentNode[]): RoleAssignmentNode[] { return nodes.map((node) => ({ ...node, key: node.name, children: withKeys(node.children || []) })); }
const roots = computed(() => withKeys(context.value?.roots || []));
function orgChildren(node: RoleAssignmentNode) { return (node.children || []).filter((child) => !child.is_employee); }
function employeeChildren(node?: RoleAssignmentNode | null, out: RoleAssignmentNode[] = []) { for (const child of node?.children || []) child.is_employee ? out.push(child) : employeeChildren(child, out); return out; }
function flattenOrg(nodes: RoleAssignmentNode[], out: RoleAssignmentNode[] = []) { for (const node of nodes) { if (!node.is_employee) out.push(node); flattenOrg(orgChildren(node), out); } return out; }
function filterOrganizations(nodes: RoleAssignmentNode[], keyword: string): RoleAssignmentNode[] {
	const query = keyword.trim().toLowerCase();
	if (!query) return nodes;
	const walk = (items: RoleAssignmentNode[]): RoleAssignmentNode[] => items.flatMap((node) => {
		const children = walk(orgChildren(node));
		return String(node.title || "").toLowerCase().includes(query) || children.length ? [{ ...node, children }] : [];
	});
	return walk(nodes);
}
const filteredOrgTree = computed(() => filterOrganizations(roots.value, orgKeyword.value));
const allOrganizations = computed(() => flattenOrg(roots.value));
const selectedOrganization = computed(() => allOrganizations.value.find((node) => node.key === selectedOrgKey.value));
const members = computed(() => employeeChildren(selectedOrganization.value));
const filteredMembers = computed(() => { const q = memberKeyword.value.trim().toLowerCase(); return !q ? members.value : members.value.filter((member) => [member.title, member.employee_number, member.employee, member.designation].some((v) => String(v || "").toLowerCase().includes(q))); });
const selectedMember = computed(() => members.value.find((member) => member.employee === selectedEmployeeId.value));
const activeTarget = computed(() => bulkMode.value ? ({ title: "批量分配" } as RoleAssignmentNode) : selectedMember.value);
const organizationPath = computed(() => selectedOrganization.value?.title || "");
const roles = computed(() => context.value?.roles || []);
const selectedRoleItems = computed(() => roles.value.filter((role) => selectedRoles.value.has(role.name)));
const filteredRoles = computed(() => { const q = roleKeyword.value.trim().toLowerCase(); return roles.value.filter((role) => (roleCategory.value === "全部" || role.role_category === roleCategory.value) && (!q || role.role_title.toLowerCase().includes(q))); });
const dirty = computed(() => selectedRoles.value.size !== savedRoles.value.size || [...selectedRoles.value].some((role) => !savedRoles.value.has(role)));
const canSave = computed(() => Boolean(activeTarget.value && dirty.value && (bulkMode.value ? checkedUsers.value.size : selectedMember.value?.user_id)));
const visibleUserIds = computed(() => filteredMembers.value.map((member) => member.user_id).filter(Boolean) as string[]);
const allVisibleChecked = computed(() => Boolean(visibleUserIds.value.length && visibleUserIds.value.every((user) => checkedUsers.value.has(user))));
const partVisibleChecked = computed(() => !allVisibleChecked.value && visibleUserIds.value.some((user) => checkedUsers.value.has(user)));

function avatarText(name?: string) { return String(name || "员").slice(-1); }
function avatarColor(name?: string) { const colors = ["#165dff", "#14c9c9", "#722ed1", "#ff7d00", "#00b42a"]; let value = 0; for (const char of String(name || "")) value += char.charCodeAt(0); return colors[value % colors.length]; }
function roleTitle(name: string) { return roles.value.find((role) => role.name === name)?.role_title || "未知角色"; }
function setRoles(values: string[]) { selectedRoles.value = new Set(values); savedRoles.value = new Set(values); }
function selectOrganization(key: string) { selectedOrgKey.value = key; checkedUsers.value = new Set(); bulkMode.value = false; }
function toggleOrganization(key: string) { const next = new Set(expandedKeys.value); next.has(key) ? next.delete(key) : next.add(key); expandedKeys.value = [...next]; }
function selectMember(member: RoleAssignmentNode) { if (!member.user_id) { Message.warning("该员工尚未绑定登录账号"); return; } bulkMode.value = false; selectedEmployeeId.value = member.employee || ""; setRoles(member.assigned_roles || []); }
function toggleMember(member: RoleAssignmentNode, checked: boolean) { if (!member.user_id) return; const next = new Set(checkedUsers.value); checked ? next.add(member.user_id) : next.delete(member.user_id); checkedUsers.value = next; }
function toggleAllVisible(checked: boolean) { const next = new Set(checkedUsers.value); visibleUserIds.value.forEach((user) => checked ? next.add(user) : next.delete(user)); checkedUsers.value = next; }
function startBulk() { if (!checkedUsers.value.size) return; bulkMode.value = true; setRoles([]); }
function toggleRole(role: string, checked: boolean) { const next = new Set(selectedRoles.value); checked ? next.add(role) : next.delete(role); selectedRoles.value = next; }
function resetRoles() { selectedRoles.value = new Set(savedRoles.value); }

async function loadContext() {
	loading.value = true;
	try {
		const data = await getRoleAssignmentContext(company.value || undefined);
		context.value = data; company.value = data.company;
		const orgs = flattenOrg(withKeys(data.roots || []));
		if (!orgs.some((node) => node.key === selectedOrgKey.value)) selectedOrgKey.value = orgs.find((node) => !node.is_company)?.key || orgs[0]?.key || "";
		expandedKeys.value = orgs.filter((node) => orgChildren(node).length).map((node) => node.name);
	} catch (error: any) { Message.error(error?.message || "人员角色数据加载失败"); }
	finally { loading.value = false; }
}

async function saveRoles() {
	if (!context.value || !canSave.value) return;
	saving.value = true;
	try {
		const roleNames = [...selectedRoles.value];
		const result = bulkMode.value
			? await assignBusinessRolesBulk([...checkedUsers.value], company.value, roleNames)
			: await assignBusinessRoles(selectedMember.value!.user_id!, company.value, roleNames);
		Message.success(result.message || "角色已保存");
		window.dispatchEvent(new CustomEvent("hr-menu-permissions-changed"));
		const employeeId = selectedEmployeeId.value;
		await loadContext();
		selectedEmployeeId.value = employeeId;
		checkedUsers.value = new Set(); bulkMode.value = false;
		const refreshed = members.value.find((member) => member.employee === employeeId);
		if (refreshed) setRoles(refreshed.assigned_roles || []);
	} catch (error: any) { Message.error(error?.message || "角色保存失败"); }
	finally { saving.value = false; }
}

watch(members, (list) => { if (!list.some((member) => member.employee === selectedEmployeeId.value && member.user_id)) { const first = list.find((member) => member.user_id); selectedEmployeeId.value = first?.employee || ""; setRoles(first?.assigned_roles || []); } }, { immediate: true });
onMounted(loadContext);
</script>
