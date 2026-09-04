<template>
	<a-config-provider :locale="zhCN">
		<div class="arco-hr-sidebar" :class="{ 'is-compact': state.compact }" @keydown.esc="closePanel">
			<div class="arco-hr-compact-shell" @mouseleave="scheduleClose">
				<aside class="arco-hr-rail" aria-label="HR 主导航">
					<a-dropdown trigger="click" position="rt">
						<button class="arco-hr-rail-button arco-hr-brand-button" type="button" :aria-label="state.title || '人事'" :title="state.title || '人事'">
							<icon-apps />
						</button>
						<template #content>
							<a-doption v-for="ws in state.workspaces" :key="ws.key" @click="handlers.onWorkspace?.(ws)">
								{{ ws.label }}
							</a-doption>
						</template>
					</a-dropdown>

					<button type="button" class="arco-hr-rail-button" aria-label="搜索功能" :title="`搜索功能（${state.searchShortcut}）`" @click="handlers.onSearch?.()">
						<icon-search />
					</button>

					<nav class="arco-hr-rail-menu" aria-label="HR 业务模块">
						<button
							v-for="group in state.groups"
							:key="group.key || group.label"
							type="button"
							class="arco-hr-rail-button"
							:class="{ 'is-active': isCurrentGroup(group), 'is-open': panelKey === group.key }"
							:aria-label="group.label"
							:aria-expanded="panelKey === group.key"
							:title="group.label"
							@mouseenter="openPanel(group)"
							@focus="openPanel(group)"
							@click="openPanel(group)"
						>
							<component :is="groupIcon(group)" />
						</button>
					</nav>

					<button type="button" class="arco-hr-rail-button arco-hr-rail-collapse" aria-label="展开侧边栏" title="展开侧边栏" @click="handlers.onToggleCompact?.()">
						<icon-menu-unfold />
					</button>
				</aside>

				<transition name="arco-hr-panel">
					<section
						v-if="panelGroup"
						class="arco-hr-flyout"
						:style="{ top: flyoutTop }"
						:aria-label="`${panelGroup.label}菜单`"
						@mouseenter="cancelClose"
						@mouseleave="scheduleClose"
					>
						<div class="arco-hr-flyout-menu">
							<button
								v-for="item in panelGroup.items"
								:key="item.key"
								type="button"
								class="arco-hr-flyout-item"
								:class="{ 'is-active': item.key === state.activeKey }"
								:title="item.label"
								@click="onItemClick(item)"
							>
								<span>{{ item.label }}</span>
								<icon-launch v-if="item.openInNewTab" />
							</button>
						</div>
					</section>
				</transition>
			</div>

			<div class="arco-hr-expanded-shell">
				<div class="arco-hr-logo">
					<span class="arco-hr-logo-mark"><icon-apps /></span>
					<a-dropdown trigger="click" position="bl">
						<a-button type="text" class="arco-hr-logo-title">
							<span>{{ state.title || "人事" }}</span>
							<icon-down />
						</a-button>
						<template #content>
							<a-doption v-for="ws in state.workspaces" :key="ws.key" @click="handlers.onWorkspace?.(ws)">{{ ws.label }}</a-doption>
						</template>
					</a-dropdown>
				</div>
				<div class="arco-hr-search-wrap">
					<a-input readonly size="small" placeholder="搜索功能" :title="state.searchShortcut" @click="handlers.onSearch?.()">
						<template #prefix><icon-search /></template>
						<template #suffix><span class="arco-hr-kbd">{{ state.searchShortcut }}</span></template>
					</a-input>
				</div>
				<div class="arco-hr-menu-wrap">
					<a-menu
						v-if="state.groups?.length"
						accordion
						:selected-keys="state.activeKey ? [state.activeKey] : []"
						:open-keys="openKeys"
						@update:open-keys="(keys) => (openKeys = keys)"
						@menu-item-click="onMenuClick"
					>
						<a-sub-menu v-for="group in state.groups" :key="group.key || group.label">
							<template #icon><component :is="groupIcon(group)" /></template>
							<template #title>{{ group.label }}</template>
							<a-menu-item v-for="item in group.items" :key="item.key">{{ item.label }}</a-menu-item>
						</a-sub-menu>
					</a-menu>
					<a-empty v-else description="暂无菜单项" />
				</div>
				<div class="arco-hr-expanded-footer">
					<a-button type="text" size="small" aria-label="收起侧边栏" title="收起侧边栏" @click="handlers.onToggleCompact?.()">
						<icon-menu-fold />
						<span>收起侧边栏</span>
					</a-button>
				</div>
			</div>
		</div>
	</a-config-provider>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import {
	IconApps,
	IconBook,
	IconBookmark,
	IconCalendar,
	IconCalendarClock,
	IconCheckCircle,
	IconCommon,
	IconDashboard,
	IconDown,
	IconFile,
	IconLaunch,
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
const panelKey = ref("");
const panelIndex = ref(0);
let closeTimer = 0;

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

const panelGroup = computed(() => (state.groups || []).find((group) => group.key === panelKey.value));
const flyoutTop = computed(() => {
	const viewportHeight = typeof window === "undefined" ? 900 : window.innerHeight;
	const preferredTop = 94 + panelIndex.value * 42;
	return `${Math.max(68, Math.min(preferredTop, viewportHeight - 348))}px`;
});

watch(
	() => [state.groups, state.activeKey],
	() => {
		const groups = state.groups || [];
		const validKeys = new Set(groups.map((group) => group.key || group.label));
		const activeParent = groups.find((group) =>
			(group.items || []).some((item) => item.key === state.activeKey)
		);
		if (activeParent) {
			openKeys.value = [activeParent.key || activeParent.label];
		} else {
			openKeys.value = groups
				.filter((group) => group.open === true)
				.map((group) => group.key || group.label);
		}
		if (panelKey.value && !validKeys.has(panelKey.value)) panelKey.value = "";
	},
	{ immediate: true }
);

function groupIcon(group) {
	const mod = String(group?.key || "").replace(/^mod:/, "");
	return MODULE_ICONS[mod] || IconDashboard;
}

function isCurrentGroup(group) {
	return group?.open === true || (group?.items || []).some((item) => item.key === state.activeKey);
}

function openPanel(group) {
	cancelClose();
	panelKey.value = group?.key || "";
	panelIndex.value = Math.max(0, (state.groups || []).findIndex((entry) => entry.key === group?.key));
}

function scheduleClose() {
	cancelClose();
	closeTimer = window.setTimeout(closePanel, 180);
}

function cancelClose() {
	if (closeTimer) window.clearTimeout(closeTimer);
	closeTimer = 0;
}

function closePanel() {
	cancelClose();
	panelKey.value = "";
}

function onItemClick(item) {
	if (!item) return;
	if (item.openInNewTab) window.open(item.path, "_blank", "noopener");
	else handlers.onNavigate?.(item);
	closePanel();
}

function onMenuClick(key) {
	const item = (state.groups || []).flatMap((group) => group.items || []).find((entry) => entry.key === key);
	onItemClick(item);
}
</script>
