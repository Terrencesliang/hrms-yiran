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
					:accordion="useAccordion"
					:collapsed="!!state.compact"
					:selected-keys="state.activeKey ? [state.activeKey] : []"
					:open-keys="state.compact ? [] : openKeys"
					@update:open-keys="onOpenKeysChange"
					@menu-item-click="onMenuClick"
				>
					<template v-for="group in state.groups" :key="group.key || group.label">
							<!-- 模块直属入口，例如合同模块的概览、签署和设置页面。 -->
						<a-menu-item v-if="group.type === 'item'" :key="group.key || group.label">
							<template #icon>
								<component :is="itemIcon(group)" />
							</template>
							{{ group.label }}
						</a-menu-item>

						<a-sub-menu v-else :key="group.key || group.label">
							<template #icon>
								<component :is="groupIcon(group)" />
							</template>
							<template #title>{{ group.label }}</template>
							<template v-for="item in group.items" :key="item.key">
								<a-sub-menu v-if="item.children?.length" :key="item.key">
									<template #icon>
										<component :is="itemIcon(item)" />
									</template>
									<template #title>{{ item.label }}</template>
									<a-menu-item v-for="child in item.children" :key="child.key">
										{{ child.label }}
									</a-menu-item>
								</a-sub-menu>
								<a-menu-item v-else :key="item.key">
									<template v-if="item.icon" #icon>
										<component :is="itemIcon(item)" />
									</template>
									{{ item.label }}
								</a-menu-item>
							</template>
						</a-sub-menu>
					</template>
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
import { computed, inject, ref, watch } from "vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import {
	IconBook,
	IconBookmark,
	IconCalendar,
	IconCalendarClock,
	IconCheckCircle,
	IconCommon,
	IconDashboard,
	IconDesktop,
	IconFile,
	IconFolder,
	IconMenuFold,
	IconMenuUnfold,
	IconSearch,
	IconSettings,
	IconStorage,
	IconTrophy,
	IconUser,
	IconUserAdd,
	IconUserGroup,
} from "@arco-design/web-vue/es/icon";

const state = inject("sidebarState");
const handlers = inject("sidebarHandlers");
const openKeys = ref([]);

/** 顶层模块使用手风琴展开，模块内页面保持统一的二级导航。 */
const useAccordion = computed(() =>
	(state.groups || []).every((group) => String(group?.key || "").startsWith("mod:"))
);
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

const ITEM_ICONS = {
	desktop: IconDesktop,
	file: IconFile,
	archive: IconStorage,
	folder: IconFolder,
	setting: IconSettings,
	settings: IconSettings,
};

watch(
	() => [state.groups, state.activeKey, state.compact],
	() => {
		if (state.compact) return;
		const groups = state.groups || [];
		const keys = [];

		for (const group of groups) {
			if (group.type === "item") continue;
			const groupKey = group.key || group.label;
			let groupHasActive = false;

				// 模块下的直属页面入口。
			const directActive = (group.items || []).some((item) => item.key === state.activeKey);
			if (directActive) {
				keys.push(groupKey);
				groupHasActive = true;
			}

			for (const item of group.items || []) {
				if (item.children?.length) {
					const childActive = item.children.some((child) => child.key === state.activeKey);
					if (childActive) {
						keys.push(groupKey, item.key);
						groupHasActive = true;
					} else if (item.open) {
						keys.push(item.key);
					}
				} else if (item.key === state.activeKey) {
					keys.push(groupKey);
					groupHasActive = true;
				}
			}
			if (!groupHasActive && group.open === true) {
				keys.push(groupKey);
			}
		}

		openKeys.value = [
			...new Set(keys.length ? keys : groups.filter((g) => g.open && g.type !== "item").map((g) => g.key || g.label)),
		];
	},
	{ immediate: true }
);

function groupIcon(group) {
	if (group?.icon) return itemIcon(group);
	const mod = String(group?.key || "").replace(/^mod:/, "");
	return MODULE_ICONS[mod] || IconDashboard;
}

function itemIcon(item) {
	return ITEM_ICONS[item?.icon] || IconFile;
}

function onOpenKeysChange(keys) {
	if (state.compact) return;
	openKeys.value = keys;
}

function flattenMenuItems(groups) {
	const out = [];
	for (const group of groups || []) {
		if (group.type === "item") {
			out.push(group);
			continue;
		}
		for (const item of group.items || []) {
			if (item.children?.length) {
				out.push(...item.children);
			} else {
				out.push(item);
			}
		}
	}
	return out;
}

function onMenuClick(key) {
	const item = flattenMenuItems(state.groups).find((entry) => entry.key === key);
	if (!item) return;
	if (item.openInNewTab) {
		window.open(item.path, "_blank", "noopener");
		return;
	}
	handlers.onNavigate?.(item);
}
</script>
