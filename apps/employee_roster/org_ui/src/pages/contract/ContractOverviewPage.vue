<template>
	<div class="arco-org-ui contract-overview">
		<div class="co-toolbar">
			<a-input
				v-model="keyword"
				class="co-search"
				size="large"
				allow-clear
				placeholder="搜索合同名称"
				@press-enter="onSearch"
			>
				<template #suffix>
					<button type="button" class="co-search-btn" aria-label="搜索" @click="onSearch">
						<icon-search />
					</button>
				</template>
			</a-input>
			<a-button type="primary" size="large" class="co-quick-sign" @click="onQuickSign">
				<template #icon><icon-edit /></template>
				快速签署
			</a-button>
		</div>

		<a-card :bordered="false" class="co-summary-card">
			<a-row :gutter="0" class="co-summary-row">
				<a-col :xs="24" :lg="12" class="co-summary-pane">
					<div class="co-summary-title">签署中合同</div>
					<div class="co-stat-grid">
						<button
							v-for="item in signingStats"
							:key="item.key"
							type="button"
							class="co-stat"
							@click="goSigning(item.key)"
						>
							<div class="co-stat-label">{{ item.label }}</div>
							<div class="co-stat-value" :class="{ 'is-alert': item.alert && item.value > 0 }">
								{{ item.value }}
							</div>
						</button>
					</div>
				</a-col>
				<a-col :xs="24" :lg="12" class="co-summary-pane co-summary-pane--right">
					<div class="co-summary-title">合同到期提醒</div>
					<div class="co-stat-grid">
						<button
							v-for="item in expiryStats"
							:key="item.key"
							type="button"
							class="co-stat"
							@click="goArchive(item.key)"
						>
							<div class="co-stat-label">{{ item.label }}</div>
							<div class="co-stat-value" :class="{ 'is-alert': item.alert && item.value > 0 }">
								{{ item.value }}
							</div>
						</button>
					</div>
				</a-col>
			</a-row>
		</a-card>

		<a-row :gutter="16" class="co-main">
			<a-col :xs="24" :lg="12">
				<a-card :bordered="false" class="co-panel">
					<template #title>
						<span class="co-panel-mark">//</span>
						签署动态
					</template>
					<a-timeline v-if="activities.length" class="co-timeline">
						<a-timeline-item v-for="item in activities" :key="item.id" :dot-color="item.color">
							<div class="co-activity-title">{{ item.title }}</div>
							<div class="co-activity-desc">{{ item.desc }}</div>
							<div class="co-activity-meta">{{ item.time }}</div>
						</a-timeline-item>
					</a-timeline>
					<a-empty v-else description="暂无签署动态" />
				</a-card>
			</a-col>

			<a-col :xs="24" :lg="12">
				<a-card :bordered="false" class="co-panel">
					<template #title>常用模板</template>
					<template #extra>
						<a-dropdown trigger="click">
							<a-button type="text" size="mini">
								<template #icon><icon-more /></template>
							</a-button>
							<template #content>
								<a-doption @click="goTemplates">管理全部模板</a-doption>
							</template>
						</a-dropdown>
					</template>

					<div class="co-template-grid">
						<button
							v-for="tpl in templates"
							:key="tpl.id"
							type="button"
							class="co-template-card"
							@click="useTemplate(tpl)"
						>
							<span class="co-template-icon" :style="{ background: tpl.bg }">
								<component :is="tpl.icon" />
							</span>
							<span class="co-template-body">
								<span class="co-template-name">{{ tpl.name }}</span>
								<span class="co-template-desc">{{ tpl.desc }}</span>
							</span>
						</button>

						<button type="button" class="co-template-add" @click="addTemplate">
							<icon-plus />
							<span>添加常用模板</span>
						</button>
					</div>
				</a-card>
			</a-col>
		</a-row>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { Message } from "@arco-design/web-vue";
import {
	IconEdit,
	IconFile,
	IconMore,
	IconPlus,
	IconSearch,
	IconUser,
} from "@arco-design/web-vue/es/icon";

const keyword = ref("");

const signingStats = ref([
	{ key: "my-seal", label: "待我用印的", value: 0, alert: false },
	{ key: "all-seal", label: "全部待用印的", value: 13, alert: false },
	{ key: "employee-sign", label: "待员工签字的", value: 13, alert: false },
]);

const expiryStats = ref([
	{ key: "d60", label: "60天内到期的", value: 21, alert: false },
	{ key: "d30", label: "30天内到期的", value: 4, alert: true },
	{ key: "today", label: "今天到期的", value: 1, alert: true },
]);

const activities = ref([
	{
		id: 1,
		title: "《劳动合同》已发送给张三签署",
		desc: "人事部 · 待员工签字",
		time: "今天 09:42",
		color: "#00b386",
	},
	{
		id: 2,
		title: "李四完成《保密协议》签字",
		desc: "法务组 · 进入用印环节",
		time: "今天 09:18",
		color: "#00b386",
	},
	{
		id: 3,
		title: "王五《实习协议》待企业用印",
		desc: "招聘组 · 全部待用印",
		time: "昨天 17:05",
		color: "#86909c",
	},
	{
		id: 4,
		title: "赵六《离职证明》已作废",
		desc: "原因：信息填写有误，已重新发起",
		time: "昨天 15:20",
		color: "#86909c",
	},
	{
		id: 5,
		title: "《劳务协议》模板已更新",
		desc: "适用于签订非劳动关系的人员",
		time: "昨天 11:06",
		color: "#86909c",
	},
]);

const templates = ref([
	{
		id: "labor-service",
		name: "劳务协议",
		desc: "适用于签订非劳动关系的人员合作场景",
		icon: IconUser,
		bg: "rgba(0, 179, 134, 0.12)",
	},
	{
		id: "termination",
		name: "解除劳动合同协议",
		desc: "适用于用人单位与劳动者协商解除关系",
		icon: IconFile,
		bg: "rgba(22, 93, 255, 0.10)",
	},
]);

function go(routeParts) {
	try {
		window.frappe?.set_route?.(...routeParts);
	} catch (e) {
		console.warn("[contract-overview] navigate failed", e);
	}
}

function onSearch() {
	const q = String(keyword.value || "").trim();
	if (!q) {
		Message.info("请输入合同名称后搜索");
		return;
	}
	Message.success(`已搜索：${q}`);
	go(["contract-signing-pending"]);
}

function onQuickSign() {
	go(["contract-templates"]);
}

function goSigning() {
	go(["contract-signing-pending"]);
}

function goArchive() {
	go(["contract-archive"]);
}

function goTemplates() {
	go(["contract-templates"]);
}

function useTemplate(tpl) {
	try {
		if (window.frappe) {
			window.frappe.route_options = {
				templateId: tpl.id,
				templateName: tpl.name,
				openPicker: true,
			};
		}
	} catch (e) {
		/* ignore */
	}
	go(["contract-initiate"]);
}

function addTemplate() {
	go(["contract-templates"]);
}
</script>
