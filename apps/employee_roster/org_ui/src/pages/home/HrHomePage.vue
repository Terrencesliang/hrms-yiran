<template>
	<div class="arco-org-ui hr-workplace">
		<a-spin :loading="loading" style="width: 100%">
			<div class="hr-wp-banner">
				<div class="hr-wp-banner-text">
					<div class="hr-wp-greeting">{{ greeting }}，{{ data?.user?.full_name || "同事" }}</div>
					<p class="hr-wp-sub">人事工作台 · 掌握组织人员概况，快速进入常用功能</p>
				</div>
				<a-space>
					<a-select
						v-if="(data?.companies || []).length > 1"
						v-model="company"
						allow-clear
						placeholder="全部公司"
						style="width: 180px"
						@change="reload"
					>
						<a-option v-for="c in data.companies" :key="c" :value="c">{{ c }}</a-option>
					</a-select>
					<a-button type="outline" @click="reload">
						<template #icon><icon-refresh /></template>
						刷新
					</a-button>
				</a-space>
			</div>

			<a-row :gutter="16" class="hr-wp-stats">
				<a-col :xs="12" :sm="12" :md="6" v-for="card in statCards" :key="card.key">
					<a-card :bordered="false" class="hr-wp-stat-card" @click="card.onClick?.()">
						<a-statistic :title="card.title" :value="card.value" :value-from="0" show-group-separator>
							<template #suffix>
								<span class="hr-wp-stat-suffix">{{ card.suffix }}</span>
							</template>
						</a-statistic>
						<div class="hr-wp-stat-extra">{{ card.extra }}</div>
					</a-card>
				</a-col>
			</a-row>

			<a-row :gutter="16" class="hr-wp-main">
				<a-col :xs="24" :lg="16">
					<a-card :bordered="false" title="部门人员分布" class="hr-wp-panel">
						<template #extra>
							<a-link @click="go(['hr-dashboard'])">查看数据面板</a-link>
						</template>
						<HrBarList :items="data?.by_department || []" />
					</a-card>
				</a-col>
				<a-col :xs="24" :lg="8">
					<a-card :bordered="false" title="快捷入口" class="hr-wp-panel hr-wp-shortcuts">
						<div class="hr-wp-quick-grid">
							<button
								v-for="link in data?.quick_links || []"
								:key="link.label"
								type="button"
								class="hr-wp-quick"
								@click="go(link.route)"
							>
								<span class="hr-wp-quick-icon">
									<component :is="iconMap[link.icon] || 'icon-apps'" />
								</span>
								<span>{{ link.label }}</span>
							</button>
						</div>
					</a-card>
				</a-col>
			</a-row>

			<a-card :bordered="false" title="近期入职" class="hr-wp-panel">
				<template #extra>
					<a-link @click="go(['List', 'Employee'])">全部员工</a-link>
				</template>
				<a-table
					:columns="joinerColumns"
					:data="data?.recent_joiners || []"
					:pagination="false"
					row-key="name"
					:bordered="false"
					@row-click="(record) => go(['Form', 'Employee', record.name])"
				>
					<template #name="{ record }">
						<a-space>
							<a-avatar :size="28">
								<img v-if="record.image" :src="record.image" alt="" />
								<span v-else>{{ (record.employee_name || "?").slice(0, 1) }}</span>
							</a-avatar>
							<span>{{ record.employee_name }}</span>
						</a-space>
					</template>
				</a-table>
			</a-card>
		</a-spin>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import {
	IconUserGroup,
	IconMindMapping,
	IconDashboard,
	IconFolder,
	IconApps,
} from "@arco-design/web-vue/es/icon";
import HrBarList from "../../components/HrBarList.vue";
import { getHrWorkplace } from "../../api/hrHome.js";

const loading = ref(false);
const company = ref("");
const data = ref(null);

const iconMap = {
	IconUserGroup,
	IconMindMapping,
	IconDashboard,
	IconFolder,
	IconApps,
};

const joinerColumns = [
	{ title: "员工", dataIndex: "employee_name", slotName: "name" },
	{ title: "部门", dataIndex: "department" },
	{ title: "职位", dataIndex: "designation" },
	{ title: "入职日期", dataIndex: "date_of_joining", width: 120 },
];

const greeting = computed(() => {
	const h = new Date().getHours();
	if (h < 12) return "上午好";
	if (h < 18) return "下午好";
	return "晚上好";
});

const statCards = computed(() => {
	const s = data.value?.stats || {};
	return [
		{
			key: "active",
			title: "在职员工",
			value: s.active || 0,
			suffix: "人",
			extra: `共 ${s.total || 0} 人档案`,
			onClick: () => go(["List", "Employee"]),
		},
		{
			key: "join_q",
			title: "本季入职",
			value: s.joining_quarter || 0,
			suffix: "人",
			extra: "本自然季度",
		},
		{
			key: "leave_q",
			title: "本季离职",
			value: s.relieving_quarter || 0,
			suffix: "人",
			extra: "本自然季度",
		},
		{
			key: "hire_y",
			title: "本年入职",
			value: s.hires_year || 0,
			suffix: "人",
			extra: `本年离职 ${s.exits_year || 0} 人`,
			onClick: () => go(["hr-dashboard"]),
		},
	];
});

function go(route) {
	if (!route?.length || !window.frappe?.set_route) return;
	window.frappe.set_route(...route);
}

async function reload() {
	loading.value = true;
	try {
		data.value = await getHrWorkplace(company.value || undefined);
	} catch (e) {
		console.error(e);
		Message.error("加载人事主页失败");
	} finally {
		loading.value = false;
	}
}

onMounted(reload);
</script>
