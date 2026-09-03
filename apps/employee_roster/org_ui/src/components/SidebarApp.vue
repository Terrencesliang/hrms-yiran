<template>
	<a-config-provider :locale="zhCN">
		<div class="arco-hr-sidebar">
			<div class="arco-hr-header">
				<a-dropdown trigger="click" position="bl">
					<a-button type="text" long>
						<icon-apps />
						<span class="arco-hr-title">{{ state.title || "HR Setup" }}</span>
						<icon-down />
					</a-button>
					<template #content>
						<a-doption v-for="ws in state.workspaces" :key="ws.key" @click="handlers.onWorkspace?.(ws)">
							{{ ws.label }}
						</a-doption>
					</template>
				</a-dropdown>
				<a-button type="text" size="small" title="收起侧边栏" @click="handlers.onCollapse?.()">
					<icon-menu-fold />
				</a-button>
			</div>

			<a-input
				class="arco-hr-search"
				readonly
				placeholder="搜索功能"
				:title="state.searchShortcut"
				@click="handlers.onSearch?.()"
			>
				<template #prefix><icon-search /></template>
				<template #suffix>
					<a-typography-text type="secondary" style="font-size: 11px">
						{{ state.searchShortcut }}
					</a-typography-text>
				</template>
			</a-input>

			<div class="arco-hr-tabs">
				<a-button
					v-for="tab in state.tabs"
					:key="tab.key"
					size="small"
					:type="tab.key === state.activeTab ? 'primary' : 'secondary'"
					@click="handlers.onTabChange?.(tab.key)"
				>
					{{ tab.label }}
				</a-button>
			</div>

			<a-menu
				v-if="state.groups?.length"
				:selected-keys="state.activeKey ? [state.activeKey] : []"
				:open-keys="openKeys"
				auto-open
				@update:open-keys="(keys) => (openKeys = keys)"
				@menu-item-click="onMenuClick"
			>
				<template v-for="group in state.groups" :key="group.label">
					<a-sub-menu v-if="group.collapsible" :key="group.label">
						<template #title>{{ group.label }}</template>
						<a-menu-item v-for="item in group.items" :key="item.key">
							<template #icon>
								<component :is="menuIcon(item)" />
							</template>
							{{ item.label }}
						</a-menu-item>
					</a-sub-menu>
					<template v-else>
						<a-typography-text type="secondary" style="display: block; padding: 8px 12px 4px; font-size: 11px">
							{{ group.label }}
						</a-typography-text>
						<a-menu-item v-for="item in group.items" :key="item.key">
							<template #icon>
								<component :is="menuIcon(item)" />
							</template>
							{{ item.label }}
						</a-menu-item>
					</template>
				</template>
			</a-menu>
			<a-empty v-else description="暂无菜单项" />
		</div>
	</a-config-provider>
</template>

<script setup>
import { inject, ref, watch } from "vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import {
	IconDashboard,
	IconFolder,
	IconHome,
	IconList,
	IconMindMapping,
	IconSettings,
	IconShareAlt,
	IconUserGroup,
} from "@arco-design/web-vue/es/icon";

const state = inject("sidebarState");
const handlers = inject("sidebarHandlers");
const openKeys = ref([]);

watch(
	() => state.groups,
	(groups) => {
		openKeys.value = (groups || []).filter((g) => g.open !== false).map((g) => g.label);
	},
	{ immediate: true }
);

function menuIcon(item) {
	const hay = `${item.path || ""} ${item.label || ""}`.toLowerCase();
	if (hay.includes("orgchart") || hay.includes("组织架构")) return IconMindMapping;
	if (hay.includes("org-diagram") || hay.includes("org_diagram") || hay.includes("架构图")) return IconShareAlt;
	if (hay.includes("roster") || hay.includes("花名册")) return IconUserGroup;
	if (hay.includes("archive") || hay.includes("档案")) return IconFolder;
	if (hay.includes("home") || hay.includes("主页")) return IconHome;
	if (hay.includes("dashboard") || hay.includes("数据面板")) return IconDashboard;
	if (hay.includes("setting") || hay.includes("设置")) return IconSettings;
	return IconList;
}

function onMenuClick(key) {
	const item = (state.groups || []).flatMap((g) => g.items || []).find((it) => it.key === key);
	if (!item) return;
	if (item.openInNewTab) {
		window.open(item.path, "_blank", "noopener");
		return;
	}
	handlers.onNavigate?.(item);
}
</script>
