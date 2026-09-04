<template>
	<a-config-provider :locale="zhCN">
		<div class="arco-hr-navbar">
			<div class="arco-hr-navbar-left">
				<a-space :size="8">
					<span class="arco-hr-navbar-logo" aria-hidden="true">
						<icon-apps />
					</span>
					<a-typography-title :heading="5" class="arco-hr-navbar-title">
						{{ state.title || "HR Pro" }}
					</a-typography-title>
				</a-space>
			</div>

			<div class="arco-hr-navbar-center" />

			<ul class="arco-hr-navbar-right">
				<li>
					<a-tooltip content="搜索">
						<a-button class="nav-btn" type="outline" shape="circle" @click="handlers.onSearch?.()">
							<template #icon><icon-search /></template>
						</a-button>
					</a-tooltip>
				</li>
				<li>
					<a-tooltip :content="isDark ? '切换为亮色模式' : '切换为暗黑模式'">
						<a-button class="nav-btn" type="outline" shape="circle" @click="toggleTheme">
							<template #icon>
								<icon-moon-fill v-if="isDark" />
								<icon-sun-fill v-else />
							</template>
						</a-button>
					</a-tooltip>
				</li>
				<li>
					<a-tooltip content="通知">
						<a-badge :count="state.notificationCount || 0" :dot="!!state.notificationCount" :max-count="99">
							<a-button class="nav-btn" type="outline" shape="circle" @click="handlers.onNotifications?.()">
								<template #icon><icon-notification /></template>
							</a-button>
						</a-badge>
					</a-tooltip>
				</li>
				<li>
					<a-tooltip :content="isFullscreen ? '退出全屏' : '全屏'">
						<a-button class="nav-btn" type="outline" shape="circle" @click="toggleFullscreen">
							<template #icon>
								<icon-fullscreen-exit v-if="isFullscreen" />
								<icon-fullscreen v-else />
							</template>
						</a-button>
					</a-tooltip>
				</li>
				<li>
					<a-tooltip content="设置">
						<a-button class="nav-btn" type="outline" shape="circle" @click="handlers.onSettings?.()">
							<template #icon><icon-settings /></template>
						</a-button>
					</a-tooltip>
				</li>
				<li>
					<a-dropdown trigger="click" position="br">
						<a-avatar :size="32" class="arco-hr-navbar-avatar">
							<img v-if="state.avatar" :src="state.avatar" alt="avatar" />
							<span v-else>{{ avatarText }}</span>
						</a-avatar>
						<template #content>
							<a-doption @click="handlers.onProfile?.()">
								<a-space>
									<icon-user />
									<span>个人中心</span>
								</a-space>
							</a-doption>
							<a-doption @click="handlers.onSettings?.()">
								<a-space>
									<icon-settings />
									<span>账户设置</span>
								</a-space>
							</a-doption>
							<a-doption @click="handlers.onLogout?.()">
								<a-space>
									<icon-export />
									<span>退出登录</span>
								</a-space>
							</a-doption>
						</template>
					</a-dropdown>
				</li>
			</ul>
		</div>
	</a-config-provider>
</template>

<script setup>
import { computed, inject, onMounted, onUnmounted, ref } from "vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";

const state = inject("navbarState");
const handlers = inject("navbarHandlers");

const isDark = ref(false);
const isFullscreen = ref(false);

const avatarText = computed(() => {
	const name = String(state.fullName || state.user || "?").trim();
	return name.slice(0, 1).toUpperCase();
});

function readTheme() {
	const root = document.documentElement;
	const body = document.body;
	isDark.value =
		body.getAttribute("data-theme") === "dark" ||
		body.getAttribute("arco-theme") === "dark" ||
		root.getAttribute("data-theme") === "dark" ||
		root.getAttribute("arco-theme") === "dark";
}

function toggleTheme() {
	const next = !isDark.value;
	isDark.value = next;
	const theme = next ? "dark" : "light";
	document.body.setAttribute("data-theme", theme);
	document.body.setAttribute("arco-theme", theme);
	document.documentElement.setAttribute("data-theme", theme);
	document.documentElement.setAttribute("arco-theme", theme);
	try {
		localStorage.setItem("arco-theme", theme);
	} catch (e) {
		/* ignore */
	}
	handlers.onThemeChange?.(theme);
}

function syncFullscreen() {
	isFullscreen.value = !!document.fullscreenElement;
}

async function toggleFullscreen() {
	try {
		if (!document.fullscreenElement) {
			await document.documentElement.requestFullscreen();
		} else {
			await document.exitFullscreen();
		}
	} catch (e) {
		/* ignore browser restrictions */
	}
	syncFullscreen();
}

onMounted(() => {
	readTheme();
	syncFullscreen();
	document.addEventListener("fullscreenchange", syncFullscreen);
});

onUnmounted(() => {
	document.removeEventListener("fullscreenchange", syncFullscreen);
});
</script>
