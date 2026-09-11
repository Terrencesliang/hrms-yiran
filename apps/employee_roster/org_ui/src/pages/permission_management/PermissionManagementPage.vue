<template>
	<HrPage title="权限管理" subtitle="配置角色可访问的菜单" class="permission-management-page">
		<template #actions>
			<a-space>
				<a-select v-model="company" class="pm-company-select" :disabled="!context?.is_platform_admin" @change="loadContext()">
					<a-option v-for="item in context?.companies || []" :key="item" :value="item">{{ item }}</a-option>
				</a-select>
				<a-button type="primary" @click="showCreate = true"><template #icon><icon-plus /></template>新增角色</a-button>
			</a-space>
		</template>

		<a-spin :loading="loading" style="width:100%">
			<div v-if="context" class="pm-shell">
				<aside class="pm-roles">
					<a-alert type="info" class="pm-admin-note">平台超级管理员拥有全部菜单权限，不参与配置。</a-alert>
					<template v-for="category in ['系统角色', '自定义角色']" :key="category">
						<div class="pm-role-group-title">{{ category }}</div>
						<button
							v-for="role in rolesByCategory(category)"
							:key="role.name"
							type="button"
							class="pm-role-item"
							:class="{ active: role.name === selectedRoleName }"
							@click="selectRole(role.name)"
						>
							<span class="pm-role-icon"><icon-user /></span>
							<span><strong>{{ role.role_title }}</strong><small>已分配 {{ role.assigned_count }} 人</small></span>
						</button>
						<div v-if="!rolesByCategory(category).length" class="pm-role-empty">暂无自定义角色</div>
					</template>
					<a-button type="text" long class="pm-add-role" @click="showCreate = true"><template #icon><icon-plus /></template>新增角色</a-button>
				</aside>

				<section class="pm-menu-panel">
					<header class="pm-menu-head">
						<div><h2>{{ selectedRole?.role_title || '角色' }}的菜单权限</h2><p>开启后，该角色可以在左侧导航栏中访问对应菜单</p></div>
						<span>{{ enabledChildCount }} 个页面已开放</span>
					</header>
					<div class="pm-menu-list">
						<div v-for="group in context.menu_catalog" :key="group.key" class="pm-menu-group">
							<div class="pm-menu-parent">
								<button type="button" class="pm-expand" :disabled="!group.children.length" @click="toggleExpanded(group.key)">
									<icon-down v-if="expanded.has(group.key)" /><icon-right v-else />
								</button>
								<span class="pm-menu-icon"><component :is="menuIcon(group.icon)" /></span>
								<strong>{{ group.label }}</strong>
								<small>{{ enabledChildren(group) }}/{{ group.children.length }} 个二级菜单</small>
								<a-switch :model-value="selectedKeys.has(group.key)" @change="toggleParent(group, Boolean($event))" />
							</div>
							<div v-if="expanded.has(group.key) && group.children.length" class="pm-menu-children">
								<label v-for="child in group.children" :key="child.key" class="pm-child-item">
									<a-checkbox :model-value="selectedKeys.has(child.key)" :disabled="!selectedKeys.has(group.key)" @change="toggleChild(group, child.key, Boolean($event))" />
									<span>{{ child.label }}</span>
								</label>
							</div>
						</div>
					</div>
					<footer class="pm-actions"><a-button :disabled="!dirty" @click="resetSelection">取消修改</a-button><a-button type="primary" :loading="saving" :disabled="!selectedRoleName || !dirty" @click="save">保存并生效</a-button></footer>
				</section>
			</div>
		</a-spin>

		<a-modal v-model:visible="showCreate" title="新增角色" :ok-loading="creating" ok-text="创建角色" cancel-text="取消" @ok="createRole">
			<a-form :model="newRole" layout="vertical">
				<a-form-item label="角色名称" required><a-input v-model="newRole.title" :max-length="30" placeholder="例如：招聘专员" /></a-form-item>
				<a-form-item label="角色说明"><a-textarea v-model="newRole.description" :max-length="100" placeholder="简要说明该角色负责的业务" /></a-form-item>
				<a-form-item label="复制菜单权限">
					<a-select v-model="newRole.copyFrom" allow-clear placeholder="不复制，创建空白角色">
						<a-option v-for="role in context?.roles || []" :key="role.name" :value="role.name">{{ role.role_title }}</a-option>
					</a-select>
				</a-form-item>
			</a-form>
		</a-modal>
	</HrPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import { IconBook, IconCalendar, IconCheckCircle, IconDown, IconFile, IconPlus, IconRight, IconSettings, IconUser, IconUserAdd, IconUserGroup } from "@arco-design/web-vue/es/icon";
import HrPage from "../../components/HrPage.vue";
import { createBusinessRole, getPermissionManagementContext, saveRoleMenuPermissions, type MenuGroup, type PermissionContext } from "../../api/permissionManagement";
import "./permission-management.css";

const context = ref<PermissionContext | null>(null);
const company = ref("");
const selectedRoleName = ref("");
const selectedKeys = ref(new Set<string>());
const savedKeys = ref(new Set<string>());
const expanded = ref(new Set<string>(["module::HR Setup", "module::Employee Center"]));
const loading = ref(false);
const saving = ref(false);
const creating = ref(false);
const showCreate = ref(false);
const newRole = reactive({ title: "", description: "", copyFrom: "" });

const selectedRole = computed(() => context.value?.roles.find((item) => item.name === selectedRoleName.value));
const enabledChildCount = computed(() => context.value?.menu_catalog.reduce((total, group) => total + enabledChildren(group), 0) || 0);
const dirty = computed(() => selectedKeys.value.size !== savedKeys.value.size || [...selectedKeys.value].some((key) => !savedKeys.value.has(key)));

function rolesByCategory(category: string) { return context.value?.roles.filter((role) => role.role_category === category) || []; }
function menuIcon(icon: string) { return ({ calendar: IconCalendar, "check-circle": IconCheckCircle, file: IconFile, "user-add": IconUserAdd, book: IconBook, user: IconUser, settings: IconSettings, "user-group": IconUserGroup } as Record<string, object>)[icon] || IconFile; }
function enabledChildren(group: MenuGroup) { return group.children.filter((item) => selectedKeys.value.has(item.key)).length; }
function replaceKeys(next: Set<string>) { selectedKeys.value = new Set(next); }

function toggleExpanded(key: string) {
	const next = new Set(expanded.value);
	next.has(key) ? next.delete(key) : next.add(key);
	expanded.value = next;
}

function toggleParent(group: MenuGroup, checked: boolean) {
	const next = new Set(selectedKeys.value);
	if (checked) { next.add(group.key); if (group.children.length) { const open = new Set(expanded.value); open.add(group.key); expanded.value = open; } }
	else { next.delete(group.key); group.children.forEach((item) => next.delete(item.key)); }
	replaceKeys(next);
}

function toggleChild(group: MenuGroup, key: string, checked: boolean) {
	const next = new Set(selectedKeys.value);
	checked ? next.add(key) : next.delete(key);
	if (checked) next.add(group.key);
	replaceKeys(next);
}

async function loadContext(role?: string) {
	loading.value = true;
	try {
		const data = await getPermissionManagementContext(company.value || undefined, role);
		context.value = data;
		company.value = data.company;
		selectedRoleName.value = data.selected_role;
		selectedKeys.value = new Set(data.selected_menu_keys);
		savedKeys.value = new Set(data.selected_menu_keys);
	} catch (error: any) { Message.error(error?.message || "权限配置加载失败"); }
	finally { loading.value = false; }
}

async function selectRole(role: string) {
	if (dirty.value && !window.confirm("当前修改尚未保存，确定切换角色吗？")) return;
	await loadContext(role);
}

function resetSelection() { selectedKeys.value = new Set(savedKeys.value); }

async function save() {
	if (!selectedRoleName.value) return;
	saving.value = true;
	try {
		const result = await saveRoleMenuPermissions(selectedRoleName.value, [...selectedKeys.value]);
		selectedKeys.value = new Set(result.menu_keys);
		savedKeys.value = new Set(result.menu_keys);
		Message.success(result.message || "权限已保存并生效");
		window.dispatchEvent(new CustomEvent("hr-menu-permissions-changed"));
	} catch (error: any) { Message.error(error?.message || "权限保存失败"); }
	finally { saving.value = false; }
}

async function createRole() {
	if (!newRole.title.trim()) { Message.warning("请输入角色名称"); showCreate.value = true; return; }
	creating.value = true;
	try {
		const result = await createBusinessRole({ company: company.value, role_title: newRole.title.trim(), description: newRole.description.trim(), copy_from: newRole.copyFrom || undefined });
		Message.success(result.message || "角色创建成功");
		newRole.title = ""; newRole.description = ""; newRole.copyFrom = "";
		await loadContext(result.name);
	} catch (error: any) { Message.error(error?.message || "角色创建失败"); showCreate.value = true; }
	finally { creating.value = false; }
}

onMounted(() => loadContext());
</script>
