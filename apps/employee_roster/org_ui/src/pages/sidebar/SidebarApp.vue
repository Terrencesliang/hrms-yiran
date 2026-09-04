<template>
	<a-config-provider :locale="zhCN">
		<div class="arco-hr-sidebar" :class="{ 'is-compact': state.compact }">
			<div v-show="!state.compact" class="arco-hr-search-wrap">
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

			<button
				v-if="state.compact"
				type="button"
				class="arco-hr-compact-search"
				:title="`搜索功能（${state.searchShortcut}）`"
				@click="handlers.onSearch?.()"
			>
				<icon-search />
			</button>

			<div class="arco-hr-menu-wrap">
				<a-menu
					v-if="state.groups?.length"
					accordion
					:collapsed="!!state.compact"
					:selected-keys="state.activeKey ? [state.activeKey] : []"
					:open-keys="state.compact ? [] : openKeys"
					@update:open-keys="onOpenKeysChange"
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
				<a-empty v-else-if="!state.compact" description="暂无菜单项" />
			</div>

			<div class="arco-hr-collapse-bar">
				<a-button
					type="text"
					size="small"
					:title="state.compact ? '展开侧边栏' : '收起侧边栏'"
					@click="handlers.onToggleCompact?.()"
				>
					<icon-menu-unfold v-if="state.compact" />
					<template v-else>
						<icon-menu-fold />
						<span>收起侧边栏</span>
					</template>
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
	IconBookmark,
	IconCalendar,
	IconCalendarClock,
	IconCheckCircle,
	IconCommon,
	IconDashboard,
	IconFile,
	IconMenuFold,
	IconMenuUnfold,
	IconSearch,
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
	hr_roster: IconCheckCircle,
	Contract: IconBookmark,
};

watch(
	() => [state.groups, state.activeKey, state.compact],
	() => {
		if (state.compact) return;
		const groups = state.groups || [];
		const activeParent = groups.find((group) =>
			(group.items || []).some((item) => item.key === state.activeKey)
		);
		if (activeParent) {
			openKeys.value = [activeParent.key || activeParent.label];
			return;
		}
		openKeys.value = groups
			.filter((group) => group.open === true)
			.map((group) => group.key || group.label);
	},
	{ immediate: true }
);

function groupIcon(group) {
	const mod = String(group?.key || "").replace(/^mod:/, "");
	return MODULE_ICONS[mod] || IconDashboard;
}

function onOpenKeysChange(keys) {
	if (state.compact) return;
	openKeys.value = keys;
}

function onMenuClick(key) {
	const item = (state.groups || []).flatMap((group) => group.items || []).find((entry) => entry.key === key);
	if (!item) return;
	if (item.openInNewTab) {
		window.open(item.path, "_blank", "noopener");
		return;
	}
	handlers.onNavigate?.(item);
}
</script>
