<template>
	<a-config-provider :locale="zhCN">
		<div class="arco-hr-sidebar">
			<div class="arco-hr-logo">
				<span class="arco-hr-logo-mark">
					<icon-apps />
				</span>
				<a-dropdown trigger="click" position="bl">
					<a-button type="text" class="arco-hr-logo-title">
						<span>{{ state.title || "HR" }}</span>
						<icon-down />
					</a-button>
					<template #content>
						<a-doption
							v-for="ws in state.workspaces"
							:key="ws.key"
							@click="handlers.onWorkspace?.(ws)"
						>
							{{ ws.label }}
						</a-doption>
					</template>
				</a-dropdown>
			</div>

			<div class="arco-hr-search-wrap">
				<a-input
					readonly
					size="small"
					placeholder="搜索功能"
					:title="state.searchShortcut"
					@click="handlers.onSearch?.()"
				>
					<template #prefix><icon-search /></template>
					<template #suffix>
						<span class="arco-hr-kbd">{{ state.searchShortcut }}</span>
					</template>
				</a-input>
			</div>

			<div class="arco-hr-menu-wrap">
				<a-menu
					v-if="state.groups?.length"
					:selected-keys="state.activeKey ? [state.activeKey] : []"
					:open-keys="openKeys"
					:style="{ width: '100%' }"
					@update:open-keys="(keys) => (openKeys = keys)"
					@menu-item-click="onMenuClick"
				>
					<a-sub-menu v-for="group in state.groups" :key="group.key || group.label">
						<template #icon>
							<component :is="groupIcon(group)" />
						</template>
						<template #title>{{ group.label }}</template>
						<a-menu-item v-for="item in group.items" :key="item.key">
							{{ item.label }}
						</a-menu-item>
					</a-sub-menu>
				</a-menu>
				<a-empty v-else description="暂无菜单项" />
			</div>

			<div class="arco-hr-collapse-bar">
				<a-button type="text" size="mini" title="收起侧边栏" @click="handlers.onCollapse?.()">
					<icon-menu-fold />
				</a-button>
			</div>
		</div>
	</a-config-provider>
</template>

<script setup>
import { inject, ref, watch } from "vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import {
	IconBook,
	IconCalendar,
	IconCalendarClock,
	IconCommon,
	IconDashboard,
	IconFile,
	IconTrophy,
	IconUser,
	IconUserAdd,
	IconUserGroup,
} from "@arco-design/web-vue/es/icon";

const state = inject("sidebarState");
const handlers = inject("sidebarHandlers");
const openKeys = ref([]);

const MODULE_ICONS = {
	"HR Setup": IconUserGroup,
	Tenure: IconUser,
	Recruitment: IconUserAdd,
	"Shift & Attendance": IconCalendar,
	Leaves: IconCalendarClock,
	Expenses: IconCommon,
	Performance: IconTrophy,
	Payroll: IconBook,
	"Tax & Benefits": IconFile,
};

watch(
	() => state.groups,
	(groups) => {
		openKeys.value = (groups || [])
			.filter((g) => g.open !== false)
			.map((g) => g.key || g.label);
	},
	{ immediate: true }
);

function groupIcon(group) {
	const mod = String(group.key || "").replace(/^mod:/, "");
	return MODULE_ICONS[mod] || IconDashboard;
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
