<template>
	<div class="arco-org-ui contract-templates">
		<ContractSectionNav group="settings" active-key="contract-templates" />

		<ContractActionToolbar title="合同模板" description="维护合同类型、签署方与默认印章配置">
			<a-input
				v-model="keyword"
				class="ct-search"
				allow-clear
				placeholder="搜索合同类型"
				@press-enter="applyFilter"
				@clear="applyFilter"
			>
				<template #prefix><icon-search /></template>
			</a-input>

			<div class="ct-toolbar-actions">
				<a-link class="ct-help" @click="onHelp">如何使用电子合同？使用帮助戳这里</a-link>
				<a-button type="outline" status="success" @click="onSeedTest">
					<template #icon><icon-thunderbolt /></template>
					生成测试模板
				</a-button>
				<a-button type="primary" @click="onAddType">
					<template #icon><icon-plus /></template>
					新增合同类型
				</a-button>
				<a-button @click="onEditGroups">编辑分组</a-button>
			</div>
		</ContractActionToolbar>

		<a-alert
			v-if="testBannerVisible"
			class="ct-test-alert"
			type="success"
			closable
			title="已准备测试模板"
			@close="testBannerVisible = false"
		>
			可在列表顶部找到「【测试】入职劳动合同」，点击「发起签署」或「设置 → 编辑模板」体验流程（当前为示意数据）。
		</a-alert>

		<a-card :bordered="false" class="ct-card">
			<div class="ct-group-head">
				<div class="ct-group-title">
					<span class="ct-group-bar" />
					<span>合同/协议</span>
					<span class="ct-group-count">({{ filteredRows.length }})</span>
				</div>
				<div class="ct-group-ops">
					<a-dropdown trigger="click" @select="onSort">
						<a-button type="text" size="small">
							排序
							<template #icon><icon-swap /></template>
						</a-button>
						<template #content>
							<a-doption value="name">按名称</a-doption>
							<a-doption value="seal">按印章</a-doption>
						</template>
					</a-dropdown>
					<a-button type="text" size="small" @click="collapsed = !collapsed">
						{{ collapsed ? "展开" : "收起" }}
						<template #icon>
							<icon-up v-if="!collapsed" />
							<icon-down v-else />
						</template>
					</a-button>
				</div>
			</div>

			<div v-show="!collapsed" class="ct-table-wrap">
				<a-table
					:columns="columns"
					:data="filteredRows"
					:pagination="false"
					:bordered="false"
					row-key="id"
					:scroll="{ x: 980 }"
				>
					<template #typeName="{ record }">
						<div class="ct-type">
							<div class="ct-type-name">
								{{ record.name }}
								<a-tag v-if="record.isTest" color="green" size="small" class="ct-test-tag">测试</a-tag>
							</div>
							<div class="ct-type-desc">{{ record.desc }}</div>
						</div>
					</template>

					<template #seal="{ record }">
						<span :class="['ct-seal', { 'is-empty': !record.seal || record.seal === '无' }]">
							{{ record.seal || "无" }}
						</span>
					</template>

					<template #party="{ record }">
						<span class="ct-party">{{ record.party }}</span>
					</template>

					<template #ops="{ record }">
						<div class="ct-row-ops">
							<a-link @click="onStartSign(record, 'single')">发起签署</a-link>
							<a-dropdown trigger="click" @select="(key) => onStartSign(record, key)">
								<a-link>
									更多
									<icon-down />
								</a-link>
								<template #content>
									<a-doption value="single">单人签署</a-doption>
									<a-doption value="batch">批量签署</a-doption>
								</template>
							</a-dropdown>
							<a-dropdown trigger="click" @select="(key) => onSettings(record, key)">
								<a-link>
									设置
									<icon-down />
								</a-link>
								<template #content>
									<a-doption value="edit">编辑模板</a-doption>
									<a-doption value="seal">配置印章</a-doption>
									<a-doption value="party">签署方设置</a-doption>
								</template>
							</a-dropdown>
							<a-dropdown trigger="click" @select="(key) => onMore(record, key)">
								<a-button type="text" size="mini" class="ct-more-btn">
									<template #icon><icon-more /></template>
								</a-button>
								<template #content>
									<a-doption value="copy">复制</a-doption>
									<a-doption value="disable">停用</a-doption>
									<a-doption value="delete" class="ct-danger">删除</a-doption>
								</template>
							</a-dropdown>
						</div>
					</template>
				</a-table>
			</div>
		</a-card>

		<a-drawer
			v-model:visible="previewVisible"
			:width="560"
			unmount-on-close
			:title="preview?.name || '模板预览'"
		>
			<template v-if="preview">
				<a-descriptions :column="1" size="large" bordered class="ct-preview-meta">
					<a-descriptions-item label="加盖印章">{{ preview.seal || "无" }}</a-descriptions-item>
					<a-descriptions-item label="盖章方">{{ preview.party }}</a-descriptions-item>
					<a-descriptions-item label="说明">{{ preview.desc }}</a-descriptions-item>
				</a-descriptions>

				<div class="ct-preview-title">正文预览（示意）</div>
				<div class="ct-preview-body" v-html="previewBodyHtml" />

				<div class="ct-preview-actions">
					<a-space>
						<a-button type="primary" @click="onStartSign(preview, 'single')">单人签署</a-button>
						<a-button @click="onStartSign(preview, 'batch')">批量签署</a-button>
						<a-button type="outline" @click="previewVisible = false">关闭</a-button>
					</a-space>
				</div>
			</template>
		</a-drawer>

		<a-modal
			v-model:visible="createVisible"
			title="新增合同类型"
			ok-text="创建"
			unmount-on-close
			@ok="submitCreate"
		>
			<a-form :model="createForm" layout="vertical">
				<a-form-item label="类型名称" required>
					<a-input v-model="createForm.name" placeholder="如：依然集团-劳动合同" />
				</a-form-item>
				<a-form-item label="说明">
					<a-textarea v-model="createForm.desc" :auto-size="{ minRows: 2, maxRows: 4 }" />
				</a-form-item>
				<a-form-item label="加盖印章">
					<a-input v-model="createForm.seal" placeholder="无 / 公章名称" />
				</a-form-item>
				<a-form-item label="盖章方">
					<a-select
						v-model="createForm.party"
						:options="[
							{ label: '企业-员工双方签署', value: '企业-员工双方签署' },
							{ label: '员工单方签署', value: '员工单方签署' },
							{ label: '企业单方签署', value: '企业单方签署' },
						]"
					/>
				</a-form-item>
			</a-form>
		</a-modal>
	</div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import {
	IconDown,
	IconMore,
	IconPlus,
	IconSearch,
	IconSwap,
	IconThunderbolt,
	IconUp,
} from "@arco-design/web-vue/es/icon";
import ContractActionToolbar from "./ContractActionToolbar.vue";
import ContractSectionNav from "./ContractSectionNav.vue";

const TEST_TEMPLATE_ID = "test-onboarding-labor";

const keyword = ref("");
const collapsed = ref(false);
const sortBy = ref("name");
const testBannerVisible = ref(false);
const previewVisible = ref(false);
const preview = ref(null);
const createVisible = ref(false);

const createForm = reactive({
	name: "",
	desc: "",
	seal: "深圳市依然电商科技有限公司公章",
	party: "企业-员工双方签署",
});

const rows = ref([
	{
		id: "1",
		name: "依然集团-劳动合同",
		desc: "适用于全职员工签订固定期限劳动合同",
		seal: "深圳市依然电商科技有限公司公章",
		party: "企业-员工双方签署",
	},
	{
		id: "2",
		name: "依然杭州-劳动合同",
		desc: "适用于杭州分公司全职员工签订固定期限劳动合同",
		seal: "依然杭州公章",
		party: "企业-员工双方签署",
	},
	{
		id: "3",
		name: "依然集团-保密协议",
		desc: "适用于全职员工入职时签订保密义务",
		seal: "深圳市依然电商科技有限公司公章",
		party: "企业-员工双方签署",
	},
	{
		id: "4",
		name: "依然杭州分公司-保密协议",
		desc: "适用于杭州分公司员工入职签订保密义务",
		seal: "依然杭州公章",
		party: "企业-员工双方签署",
	},
	{
		id: "5",
		name: "依然集团-薪酬确认书",
		desc: "适用于员工薪酬调整或入职薪酬确认",
		seal: "无",
		party: "员工单方签署",
	},
	{
		id: "6",
		name: "依然集团-竞争性兼职禁止协议",
		desc: "适用于关键岗位员工兼职限制约定",
		seal: "深圳市依然电商科技有限公司公章",
		party: "企业-员工双方签署",
	},
	{
		id: "7",
		name: "依然集团-实习协议",
		desc: "适用于在校实习生签订实习约定",
		seal: "深圳市依然电商科技有限公司公章",
		party: "企业-员工双方签署",
	},
	{
		id: "8",
		name: "依然集团-离职证明",
		desc: "适用于员工离职后开具证明文件",
		seal: "深圳市依然电商科技有限公司公章",
		party: "企业单方签署",
	},
]);

const columns = [
	{ title: "类型名称", slotName: "typeName", width: 320 },
	{ title: "加盖印章", slotName: "seal", width: 260 },
	{ title: "盖章方", slotName: "party", width: 160 },
	{ title: "", slotName: "ops", width: 220, align: "right" },
];

const filteredRows = computed(() => {
	const q = keyword.value.trim().toLowerCase();
	let list = rows.value.slice();
	if (q) {
		list = list.filter(
			(row) =>
				row.name.toLowerCase().includes(q) ||
				row.desc.toLowerCase().includes(q) ||
				String(row.seal || "").toLowerCase().includes(q)
		);
	}
	if (sortBy.value === "seal") {
		list.sort((a, b) => String(a.seal || "").localeCompare(String(b.seal || ""), "zh"));
	} else {
		list.sort((a, b) => {
			if (a.isTest && !b.isTest) return -1;
			if (!a.isTest && b.isTest) return 1;
			return a.name.localeCompare(b.name, "zh");
		});
	}
	return list;
});

const previewBodyHtml = computed(() => {
	if (!preview.value) return "";
	const name = preview.value.name;
	return `
		<p><strong>${name}</strong></p>
		<p>甲方（用人单位）：深圳市依然电商科技有限公司</p>
		<p>乙方（劳动者）：______________</p>
		<p>根据《中华人民共和国劳动合同法》及相关规定，甲乙双方协商一致，订立本合同。</p>
		<ol>
			<li>合同期限：自 ____ 年 __ 月 __ 日起至 ____ 年 __ 月 __ 日止。</li>
			<li>工作内容与地点：乙方同意从事 ________ 岗位工作，工作地点为 ________。</li>
			<li>工作时间与休息休假：按国家规定及公司制度执行。</li>
			<li>劳动报酬：月工资人民币 ________ 元（税前），按月支付。</li>
			<li>本合同一式两份，甲乙双方各执一份，经双方签署后生效。</li>
		</ol>
		<p class="ct-preview-sign">甲方（盖章）：____________　　乙方（签字）：____________</p>
		<p class="ct-preview-sign">日期：____年__月__日　　　　日期：____年__月__日</p>
	`;
});

function applyFilter() {
	/* computed */
}

function buildTestTemplate() {
	return {
		id: TEST_TEMPLATE_ID,
		name: "【测试】入职劳动合同",
		desc: "测试专用：固定期限劳动合同示意稿，可发起签署进入选人向导",
		seal: "深圳市依然电商科技有限公司公章",
		party: "企业-员工双方签署",
		isTest: true,
	};
}

function onSeedTest() {
	const existing = rows.value.find((row) => row.id === TEST_TEMPLATE_ID);
	if (existing) {
		rows.value = [existing, ...rows.value.filter((row) => row.id !== TEST_TEMPLATE_ID)];
		Message.success("测试模板已置顶，可直接发起签署");
	} else {
		rows.value.unshift(buildTestTemplate());
		Message.success("已生成测试模板：【测试】入职劳动合同");
	}
	testBannerVisible.value = true;
	keyword.value = "";
	preview.value = rows.value.find((row) => row.id === TEST_TEMPLATE_ID);
	previewVisible.value = true;
}

function onHelp() {
	Message.info("电子合同使用帮助即将开放");
}

function onAddType() {
	createForm.name = "";
	createForm.desc = "";
	createForm.seal = "深圳市依然电商科技有限公司公章";
	createForm.party = "企业-员工双方签署";
	createVisible.value = true;
}

function submitCreate() {
	if (!createForm.name.trim()) {
		Message.warning("请填写类型名称");
		return false;
	}
	rows.value.unshift({
		id: String(Date.now()),
		name: createForm.name.trim(),
		desc: createForm.desc.trim() || "自定义合同类型",
		seal: createForm.seal.trim() || "无",
		party: createForm.party,
	});
	Message.success("已新增合同类型");
	createVisible.value = false;
}

function onEditGroups() {
	Message.info("编辑分组（示意）");
}

function onSort(key) {
	sortBy.value = key;
}

function onStartSign(record, mode) {
	previewVisible.value = false;
	const payload = {
		templateId: record?.id || "",
		templateName: record?.name || "",
		mode: mode === "batch" ? "batch" : "single",
		openPicker: true,
	};
	try {
		if (window.frappe) {
			window.frappe.route_options = payload;
		}
		const go = window.frappe?.set_route;
		if (typeof go === "function") {
			go("contract-initiate");
			return;
		}
	} catch (e) {
		console.warn("[contract-templates] set_route failed", e);
	}
	// fallback when Desk route unavailable
	window.location.assign(
		`/desk/contract-initiate?templateId=${encodeURIComponent(payload.templateId)}&templateName=${encodeURIComponent(
			payload.templateName
		)}&mode=${payload.mode}&openPicker=1`
	);
}

function onSettings(record, key) {
	if (key === "edit") {
		preview.value = record;
		previewVisible.value = true;
		return;
	}
	const map = { seal: "配置印章", party: "签署方设置" };
	Message.info(`${record.name} · ${map[key] || key}`);
}

function onMore(record, key) {
	if (key === "copy") {
		rows.value.unshift({
			...record,
			id: String(Date.now()),
			name: `${record.name}-副本`,
			isTest: false,
		});
		Message.success(`已复制：${record.name}`);
		return;
	}
	if (key === "disable") {
		Message.warning(`已停用：${record.name}`);
		return;
	}
	if (key === "delete") {
		rows.value = rows.value.filter((row) => row.id !== record.id);
		Message.success(`已删除：${record.name}`);
	}
}

// 打开页面时自动准备一条测试模板，方便直接试
if (!rows.value.some((row) => row.id === TEST_TEMPLATE_ID)) {
	rows.value.unshift(buildTestTemplate());
	testBannerVisible.value = true;
}
</script>
