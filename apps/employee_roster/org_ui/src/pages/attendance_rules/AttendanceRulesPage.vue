<template>
	<div class="hr-attendance-rules-shell">
		<a-spin :loading="loading" style="width: 100%">
			<div class="hr-desk-page-stack">
				<HrDeskStatOverview
					v-if="activeTab === 'deduction'"
					:items="statItems"
					grid-class="hr-employee-overview-grid--three"
					meta-title="规则概览"
					:meta-icon="IconBook"
					meta-hint="扣款规则启用与覆盖情况"
				/>

				<a-card :bordered="false" class="hr-desk-toolbar-card">
					<div class="hr-attendance-rules-toolbar">
						<a-tabs v-model:active-key="activeTab" type="rounded" hide-content class="hr-attendance-rules-tabs">
							<a-tab-pane key="deduction" title="扣款规则" />
							<a-tab-pane key="allowance" title="补贴规则" />
							<a-tab-pane key="makeup" title="补卡规则" />
							<a-tab-pane key="overtime" title="加班规则" />
							<a-tab-pane key="travel" title="外出差旅规则" />
						</a-tabs>
						<div class="hr-attendance-rules-actions">
							<a-button :disabled="activeTab !== 'deduction'" @click="importRules">导入规则</a-button>
							<a-button type="primary" :disabled="activeTab !== 'deduction'" @click="addRule">
								<template #icon><IconPlus /></template>
								新增扣款规则
							</a-button>
						</div>
					</div>
				</a-card>

				<template v-if="activeTab === 'deduction'">
					<a-card :bordered="false" class="hr-desk-guide-card">
						<template #title>使用指南</template>
						<div class="hr-attendance-rules-guide-body">
							<p>1、考勤规则方案可以根据企业已启用的考勤项，包括迟到、早退、缺卡、旷工等，自定义扣款规则。</p>
							<p>
								2、{{ helpText }}
								<a-link @click="goGroups">考勤分组</a-link>
								／
								<a-link @click="goSettings">扣款设置</a-link>
							</p>
							<p>3、若有多个不同规则，请新增方案并设置后，到【考勤分组】关联方案及人员。</p>
						</div>
					</a-card>

					<a-card :bordered="false" class="hr-desk-table-card">
						<template #title>扣款规则列表</template>
						<template #extra>
							<span class="hr-attendance-rules-count">共 {{ rules.length }} 条</span>
						</template>
						<a-table
							:columns="columns"
							:data="rules"
							:pagination="false"
							row-key="name"
							:bordered="false"
							size="medium"
						>
							<template #rule_name="{ record }">
								<a-link @click="editRule(record.name)">{{ record.rule_name }}</a-link>
							</template>
							<template #actions="{ record }">
								<a-space>
									<a-link @click="editRule(record.name)">修改</a-link>
									<a-link status="danger" @click="confirmDelete(record)">删除</a-link>
								</a-space>
							</template>
							<template #empty>
								<a-empty description="暂无规则" />
							</template>
						</a-table>
					</a-card>
				</template>

				<a-card v-else :bordered="false" class="hr-desk-table-card">
					<a-empty description="该规则类型即将支持，当前请先配置扣款规则。" />
				</a-card>
			</div>
		</a-spin>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { IconBook, IconFolder, IconPlus, IconUserGroup } from "@arco-design/web-vue/es/icon";
import { Message, Modal } from "@arco-design/web-vue";
import HrDeskStatOverview from "../../components/HrDeskStatOverview.vue";
import { deleteDeductionRule, getRulesOverview } from "../../api/attendanceRules.js";

const loading = ref(false);
const activeTab = ref("deduction");
const helpText = ref("");
const stats = ref({});
const rules = ref([]);

const columns = [
	{ title: "规则名称", dataIndex: "rule_name", slotName: "rule_name", ellipsis: true },
	{ title: "迟到扣款", dataIndex: "late_mode", width: 140 },
	{ title: "早退扣款", dataIndex: "early_mode", width: 140 },
	{ title: "缺卡处理", dataIndex: "missing_mode", width: 140 },
	{ title: "旷工扣款", dataIndex: "absent_mode", width: 140 },
	{ title: "操作", slotName: "actions", width: 120, align: "center" },
];

const statItems = computed(() => {
	const s = stats.value || {};
	return [
		{ key: "enabled_rules", label: "已用扣款规则", value: s.enabled_rules ?? 0, suffix: "条", tone: "success", icon: IconBook, disabled: true },
		{ key: "linked_groups", label: "关联考勤分组", value: s.linked_groups ?? 0, suffix: "个", tone: "primary", icon: IconFolder, disabled: true },
		{ key: "covered_employees", label: "覆盖员工", value: s.covered_employees ?? 0, suffix: "人", tone: "purple", icon: IconUserGroup, disabled: true },
	];
});

async function reload() {
	loading.value = true;
	try {
		const data = await getRulesOverview();
		helpText.value = data?.help || "";
		stats.value = data?.stats || {};
		rules.value = data?.rules || [];
	} catch (error) {
		Message.error("加载考勤规则失败");
		console.error(error);
	} finally {
		loading.value = false;
	}
}

function addRule() {
	window.frappe?.new_doc?.("Attendance Deduction Rule");
}

function importRules() {
	window.frappe?.new_doc?.("Data Import", {
		reference_doctype: "Attendance Deduction Rule",
		import_type: "Insert New Records",
	});
}

function editRule(name) {
	if (name) window.frappe?.set_route?.("Form", "Attendance Deduction Rule", name);
}

function goGroups() {
	window.frappe?.set_route?.("List", "Attendance Group");
}

function goSettings() {
	window.frappe?.set_route?.("Form", "Attendance Deduction Settings");
}

function confirmDelete(record) {
	Modal.confirm({
		title: "确认删除",
		content: `确认删除规则「${record.rule_name || record.name}」？`,
		onOk: async () => {
			await deleteDeductionRule(record.name);
			Message.success("已删除");
			await reload();
		},
	});
}

onMounted(reload);

defineExpose({ reload });
</script>
