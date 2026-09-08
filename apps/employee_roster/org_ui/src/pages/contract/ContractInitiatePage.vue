<template>
	<div class="arco-org-ui contract-initiate">
		<a-card :bordered="false" class="ci-steps-card">
			<a-steps :current="currentStep" label-placement="horizontal">
				<a-step :title="templateLocked ? '选择员工' : '选择模板'" />
				<a-step title="确认合同内容" />
				<a-step title="预览合同发起签署" />
			</a-steps>
		</a-card>

		<!-- Step 1: 选择员工（模板已由上游确定） -->
		<div v-show="currentStep === 1" class="ci-step-body">
			<a-card :bordered="false" class="ci-section-card">
				<div class="ci-section-title">选择员工</div>
				<div class="ci-employee-row">
					<a-button type="outline" @click="openPicker">
						<template #icon><icon-user-add /></template>
						选择员工
					</a-button>
					<div v-if="selectedEmployees.length" class="ci-employee-tags">
						<a-tag
							v-for="emp in selectedEmployees"
							:key="emp.id"
							closable
							color="green"
							@close="removeEmployee(emp.id)"
						>
							{{ emp.name }}
						</a-tag>
					</div>
					<span v-else class="ci-hint">请选择需要签署合同的员工</span>
				</div>
			</a-card>

			<a-card :bordered="false" class="ci-section-card">
				<div class="ci-section-title">合同模板</div>
				<div v-if="selectedTemplate" class="ci-template-grid">
					<div class="ci-template-card is-active is-locked">
						<span class="ci-template-thumb">
							<span class="ci-template-thumb-title">{{ selectedTemplate.shortName }}</span>
							<span class="ci-template-thumb-sub">合同模板</span>
						</span>
						<span class="ci-template-meta">
							<span class="ci-template-name">{{ selectedTemplate.name }}</span>
							<span class="ci-template-desc">{{ selectedTemplate.desc || "已从模板库选定，发起签署时不可更换" }}</span>
						</span>
						<span class="ci-template-check">
							<icon-check-circle-fill />
						</span>
					</div>
				</div>
				<a-empty v-else description="未指定合同模板">
					<a-button type="primary" @click="goPickTemplate">去选择模板</a-button>
				</a-empty>
			</a-card>
		</div>

		<!-- Step 2: 确认合同内容 = 左侧预览 + 右侧变量表单 -->
		<div v-show="currentStep === 2" class="ci-step-body ci-confirm-layout">
			<div class="ci-doc-pane">
				<ContractDocPaper
					:form="contractForm"
					:title="selectedTemplate?.name || ''"
					:watermark-text="watermarkText"
					:start-date="previewStart"
					:end-date="previewEnd"
				/>
			</div>

			<aside class="ci-form-pane">
				<div class="ci-form-title">填充合同表单信息</div>
				<a-spin :loading="employeeDetailLoading" class="ci-form-spin">
					<a-form :model="contractForm" layout="vertical" class="ci-var-form" auto-label-width>
						<a-form-item label="员工姓名">
							<a-input :model-value="contractForm.employeeName" readonly />
						</a-form-item>
						<a-form-item label="证件号码">
							<a-input :model-value="contractForm.idNumber" readonly />
						</a-form-item>
						<a-form-item label="性别">
							<a-input :model-value="contractForm.gender" readonly />
						</a-form-item>
						<a-form-item label="岗位">
							<a-input :model-value="contractForm.designation" readonly />
						</a-form-item>
						<a-form-item label="试用期">
							<a-input :model-value="contractForm.probation" readonly />
						</a-form-item>
						<a-form-item label="手机号码">
							<a-input :model-value="contractForm.mobile" readonly />
						</a-form-item>
						<a-form-item label="现居住地">
							<a-input :model-value="contractForm.address" readonly />
						</a-form-item>

						<a-divider class="ci-form-divider" />

						<a-form-item label="现合同开始日期" required>
							<a-date-picker
								v-model="contractForm.contractStart"
								style="width: 100%"
								value-format="YYYY-MM-DD"
								placeholder="选择日期"
							/>
						</a-form-item>
						<a-form-item label="现合同结束日期" required>
							<a-date-picker
								v-model="contractForm.contractEnd"
								style="width: 100%"
								value-format="YYYY-MM-DD"
								placeholder="选择日期"
							/>
						</a-form-item>
						<a-form-item label="签署时间" required>
							<a-input
								v-model="contractForm.signTime"
								placeholder="请输入..."
								allow-clear
							/>
						</a-form-item>
						<a-form-item label="职级薪资" required>
							<a-input
								v-model="contractForm.salary"
								placeholder="请输入..."
								allow-clear
							/>
						</a-form-item>
						<a-form-item label="数字">
							<a-input
								v-model="contractForm.numberText"
								placeholder="请输入..."
								allow-clear
							/>
						</a-form-item>
						<a-form-item label="依然入职时间" required>
							<a-input
								v-model="contractForm.joinDateText"
								placeholder="请输入..."
								allow-clear
							/>
						</a-form-item>
					</a-form>
				</a-spin>
			</aside>
		</div>

		<!-- Step 3: 整份合同预览并发起签署 -->
		<div v-show="currentStep === 3" class="ci-step-body ci-final-layout">
			<a-alert :type="previewUrl ? 'success' : 'warning'" show-icon class="ci-final-alert">
				{{
					previewUrl
						? "已获取腾讯电子签正式预览，请核对后发起签署。"
						: previewError || "腾讯电子签未配置，暂时无法生成正式合同预览。"
				}}
			</a-alert>
			<div class="ci-doc-pane ci-doc-pane--final">
				<a-spin :loading="previewLoading" class="ci-real-preview-spin">
					<div v-if="previewUrl" class="ci-real-preview">
						<iframe
							:src="previewUrl"
							title="腾讯电子签合同预览"
							class="ci-real-preview-frame"
							referrerpolicy="no-referrer"
						/>
						<a-link :href="previewUrl" target="_blank" rel="noopener noreferrer">
							在新窗口打开正式预览
						</a-link>
					</div>
					<a-empty v-else :description="previewLoading ? '正在生成正式预览' : '未配置或预览失败'" />
				</a-spin>
			</div>
		</div>

		<div class="ci-footer" :class="{ 'is-spread': currentStep >= 2 }">
			<a-button v-if="currentStep > 1" @click="currentStep -= 1">上一步</a-button>
			<a-button v-else @click="onCancel">取消</a-button>
			<a-button
				v-if="currentStep === 1"
				type="primary"
				:disabled="!canNext"
				@click="goNext"
			>
				下一步
			</a-button>
			<a-button
				v-else-if="currentStep === 2"
				type="primary"
				:disabled="!canGenerate"
				:loading="previewLoading"
				@click="onGenerateContract"
			>
				生成合同
			</a-button>
			<a-button
				v-else
				type="primary"
				:disabled="!canNext || !previewUrl"
				:loading="submitting"
				@click="onSubmit"
			>
				发起签署
			</a-button>
		</div>

		<!-- 选择人员弹窗（modal-class 挂到 body，样式不依赖 .contract-initiate） -->
		<a-modal
			v-model:visible="pickerVisible"
			modal-class="ci-picker-modal"
			title="选择人员"
			:width="560"
			:body-style="{ padding: '0' }"
			unmount-on-close
			@ok="confirmPicker"
			@cancel="closePicker"
		>
			<a-tabs v-model:active-key="pickerTab" class="ci-picker-tabs" @change="onPickerTabChange">
				<a-tab-pane key="people" title="人员" />
				<a-tab-pane key="recent" title="最近选择" />
			</a-tabs>

			<div class="ci-picker-body">
				<a-input
					v-model="pickerKeyword"
					class="ci-picker-search"
					allow-clear
					placeholder="搜索人员或部门"
					@input="onSearchInput"
					@clear="onSearchClear"
				>
					<template #prefix><icon-search /></template>
				</a-input>

				<template v-if="pickerTab === 'people'">
					<div class="ci-picker-crumb">
						<button
							v-for="(crumb, idx) in breadcrumb"
							:key="crumb.id"
							type="button"
							class="ci-picker-crumb-item"
							:class="{ 'is-link': idx < breadcrumb.length - 1 }"
							@click="goCrumb(idx)"
						>
							<span v-if="idx > 0" class="ci-picker-crumb-sep-inline"><icon-right /></span>
							{{ crumb.title }}
						</button>
					</div>

					<a-spin :loading="orgLoading || searchLoading" class="ci-picker-spin">
						<div class="ci-picker-list">
							<!-- 远程搜索人员 -->
							<template v-if="pickerKeyword.trim()">
								<a-empty
									v-if="!searchLoading && !searchPeople.length && !searchDepts.length"
									description="未找到匹配人员或部门"
								/>
								<button
									v-for="dept in searchDepts"
									:key="`s-${dept.id}`"
									type="button"
									class="ci-picker-row is-dept"
									@click="enterDept(dept)"
								>
									<span class="ci-picker-dept-icon"><icon-apps /></span>
									<span class="ci-picker-row-main">
										<span class="ci-picker-row-title">{{ dept.name }}</span>
										<span class="ci-picker-row-sub">{{ dept.count }} 人</span>
									</span>
									<icon-right class="ci-picker-arrow" />
								</button>
								<label
									v-for="person in searchPeople"
									:key="person.id"
									class="ci-picker-row is-person"
									:class="{ 'is-checked': draftSelectedIds.includes(person.id) }"
								>
									<a-checkbox
										:model-value="draftSelectedIds.includes(person.id)"
										@change="(checked) => togglePerson(person, checked)"
									/>
									<span class="ci-picker-avatar">{{ avatarText(person.name) }}</span>
									<span class="ci-picker-row-main">
										<span class="ci-picker-row-title">{{ person.name }}</span>
										<span class="ci-picker-row-sub">
											{{ [person.dept, person.title].filter(Boolean).join(" · ") || "员工" }}
										</span>
									</span>
								</label>
							</template>

							<!-- 组织浏览 -->
							<template v-else>
								<a-empty v-if="!orgLoading && !currentDepts.length && !currentPeople.length" description="暂无组织或人员" />
								<button
									v-for="dept in currentDepts"
									:key="dept.id"
									type="button"
									class="ci-picker-row is-dept"
									:class="{ 'is-empty': !dept.count && !dept.hasChildren }"
									@click="enterDept(dept)"
								>
									<span class="ci-picker-dept-icon"><icon-apps /></span>
									<span class="ci-picker-row-main">
										<span class="ci-picker-row-title">{{ dept.name }}</span>
										<span class="ci-picker-row-sub">{{ dept.count }} 人</span>
									</span>
									<icon-right class="ci-picker-arrow" />
								</button>
								<label
									v-for="person in currentPeople"
									:key="person.id"
									class="ci-picker-row is-person"
									:class="{ 'is-checked': draftSelectedIds.includes(person.id) }"
								>
									<a-checkbox
										:model-value="draftSelectedIds.includes(person.id)"
										@change="(checked) => togglePerson(person, checked)"
									/>
									<span class="ci-picker-avatar">{{ avatarText(person.name) }}</span>
									<span class="ci-picker-row-main">
										<span class="ci-picker-row-title">{{ person.name }}</span>
										<span class="ci-picker-row-sub">{{ person.title || "员工" }}</span>
									</span>
								</label>
							</template>
						</div>
					</a-spin>
				</template>

				<div v-else class="ci-picker-list">
					<a-empty v-if="!recentEmployees.length" description="暂无最近选择" />
					<label
						v-for="person in recentEmployees"
						:key="person.id"
						class="ci-picker-row is-person"
						:class="{ 'is-checked': draftSelectedIds.includes(person.id) }"
					>
						<a-checkbox
							:model-value="draftSelectedIds.includes(person.id)"
							@change="(checked) => togglePerson(person, checked)"
						/>
						<span class="ci-picker-avatar">{{ avatarText(person.name) }}</span>
						<span class="ci-picker-row-main">
							<span class="ci-picker-row-title">{{ person.name }}</span>
							<span class="ci-picker-row-sub">
								{{ [person.dept, person.title].filter(Boolean).join(" · ") || "员工" }}
							</span>
						</span>
					</label>
				</div>

				<div v-if="draftSelectedIds.length" class="ci-picker-selected">
					<span class="ci-picker-selected-label">已选 {{ draftSelectedIds.length }} 人</span>
					<div class="ci-picker-selected-tags">
						<a-tag
							v-for="id in draftSelectedIds"
							:key="id"
							closable
							color="green"
							size="small"
							@close="removeDraft(id)"
						>
							{{ draftPeopleMap[id]?.name || id }}
						</a-tag>
					</div>
				</div>
			</div>

			<template #footer>
				<a-button @click="closePicker">取消</a-button>
				<a-button type="primary" :disabled="!draftSelectedIds.length" @click="confirmPicker">
					确认
				</a-button>
			</template>
		</a-modal>	</div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { Message, Modal } from "@arco-design/web-vue";
import {
	IconApps,
	IconCheckCircleFill,
	IconRight,
	IconSearch,
	IconUserAdd,
} from "@arco-design/web-vue/es/icon";
import { call, getOrgTree, searchEmployees } from "../../api";
import { createContractSigning, previewContract } from "../../api/contract.js";
import ContractDocPaper from "./ContractDocPaper.vue";

const RECENT_KEY = "contract-initiate-recent";

const props = defineProps({
	templateId: { type: String, default: "" },
	templateName: { type: String, default: "" },
	mode: { type: String, default: "single" },
	openPicker: { type: Boolean, default: true },
});

const currentStep = ref(1);
const pickerVisible = ref(false);
const pickerTab = ref("people");
const pickerKeyword = ref("");
const pathStack = ref([]);
const draftSelectedIds = ref([]);
const draftPeopleMap = ref({});
const selectedEmployees = ref([]);
const selectedTemplateId = ref("");
const templateLocked = ref(false);
const employeeDetailLoading = ref(false);
const previewLoading = ref(false);
const previewUrl = ref("");
const previewError = ref("");
const submitting = ref(false);
const submissionReference = ref("");

const contractForm = reactive({
	employeeName: "",
	idNumber: "",
	gender: "",
	designation: "",
	probation: "",
	mobile: "",
	address: "",
	contractStart: "",
	contractEnd: "",
	signTime: "",
	salary: "",
	numberText: "",
	joinDateText: "",
});

const orgLoading = ref(false);
const searchLoading = ref(false);
const companyTitle = ref("公司");
const orgById = ref({});
const rootChildren = ref([]);
const searchPeople = ref([]);
const searchDepts = ref([]);
const recentEmployees = ref([]);

let searchTimer = null;

const selectedTemplate = computed(() => {
	if (!selectedTemplateId.value) return null;
	const name = props.templateName || selectedTemplateId.value;
	return {
		id: selectedTemplateId.value,
		name,
		shortName: name.length > 14 ? `${name.slice(0, 12)}…` : name,
		desc: "已从模板库选定，发起签署时不可更换",
	};
});

const modeLabel = computed(() => (props.mode === "batch" ? "批量签署" : "单人签署"));

const watermarkText = computed(() => {
	const name = contractForm.employeeName || "合同预览";
	const tail = String(contractForm.idNumber || "").slice(-4);
	return tail ? `${name} ${tail}` : name;
});

const previewStart = computed(() => formatDate(contractForm.contractStart));
const previewEnd = computed(() => formatDate(contractForm.contractEnd));

const breadcrumb = computed(() => [
	{ id: "__root__", title: companyTitle.value },
	...pathStack.value.map((p) => ({ id: p.id, title: p.name })),
]);

const currentNode = computed(() => {
	if (!pathStack.value.length) return null;
	const tip = pathStack.value[pathStack.value.length - 1];
	return orgById.value[tip.id] || null;
});

const currentDepts = computed(() => {
	const children = currentNode.value
		? currentNode.value.children || []
		: rootChildren.value;
	return children
		.filter((n) => !n.is_employee)
		.map(mapDept);
});

const currentPeople = computed(() => {
	const children = currentNode.value
		? currentNode.value.children || []
		: rootChildren.value;
	const deptName = currentNode.value?.title || companyTitle.value;
	return children.filter((n) => n.is_employee).map((n) => mapPerson(n, deptName));
});

const canNext = computed(() => {
	if (currentStep.value === 1) {
		return selectedEmployees.value.length > 0 && !!selectedTemplateId.value;
	}
	return selectedEmployees.value.length > 0 && !!selectedTemplateId.value;
});

const canGenerate = computed(() => {
	return Boolean(
		contractForm.employeeName &&
			formatDate(contractForm.contractStart) &&
			formatDate(contractForm.contractEnd) &&
			String(contractForm.signTime || "").trim() &&
			String(contractForm.salary || "").trim() &&
			String(contractForm.joinDateText || "").trim()
	);
});

function formatDate(value) {
	if (!value) return "";
	if (typeof value === "string") return value.slice(0, 10);
	try {
		const d = value instanceof Date ? value : new Date(value);
		if (Number.isNaN(d.getTime())) return "";
		const y = d.getFullYear();
		const m = String(d.getMonth() + 1).padStart(2, "0");
		const day = String(d.getDate()).padStart(2, "0");
		return `${y}-${m}-${day}`;
	} catch (e) {
		return "";
	}
}

function resetContractForm() {
	Object.assign(contractForm, {
		employeeName: "",
		idNumber: "",
		gender: "",
		designation: "",
		probation: "",
		mobile: "",
		address: "",
		contractStart: "",
		contractEnd: "",
		signTime: "",
		salary: "",
		numberText: "",
		joinDateText: "",
	});
}

async function loadEmployeeDetail(employeeId) {
	if (!employeeId) {
		resetContractForm();
		return;
	}
	employeeDetailLoading.value = true;
	try {
		const doc = await call("frappe.client.get", {
			doctype: "Employee",
			name: employeeId,
		});
		const join = formatDate(doc.date_of_joining);
		contractForm.employeeName = doc.employee_name || doc.name || "";
		contractForm.idNumber =
			doc.custom_id_number ||
			doc.id_number ||
			doc.passport_number ||
			doc.uid ||
			"";
		contractForm.gender = doc.gender || "";
		contractForm.designation = doc.designation || "";
		contractForm.probation = doc.probation_period
			? `${doc.probation_period}个月`
			: doc.custom_probation || "3个月";
		contractForm.mobile = doc.cell_number || doc.personal_mobile || "";
		contractForm.address =
			doc.current_address || doc.permanent_address || doc.person_to_be_contacted || "";
		contractForm.joinDateText = join;
		if (!contractForm.contractStart && join) {
			contractForm.contractStart = join;
		}
		if (!contractForm.signTime && join) {
			contractForm.signTime = join;
		}
	} catch (e) {
		console.warn("[contract-initiate] load employee failed", e);
		const fallback = selectedEmployees.value.find((x) => x.id === employeeId);
		contractForm.employeeName = fallback?.name || employeeId;
		contractForm.designation = fallback?.title || "";
		Message.warning("部分员工信息未能加载，请手工核对表单");
	} finally {
		employeeDetailLoading.value = false;
	}
}

onMounted(() => {
	if (props.templateId) {
		selectedTemplateId.value = props.templateId;
		templateLocked.value = true;
	} else {
		// 未指定模板：先回模板库选择，避免在发起页再挑一遍
		goPickTemplate();
		return;
	}
	loadRecent();
	loadOrgTree().finally(() => {
		if (props.openPicker) openPicker();
	});
});

onUnmounted(() => {
	if (searchTimer) clearTimeout(searchTimer);
});

watch(pickerKeyword, (val) => {
	if (!pickerVisible.value || pickerTab.value !== "people") return;
	onSearchInput();
	if (!String(val || "").trim()) {
		searchPeople.value = [];
		searchDepts.value = [];
	}
});

function avatarText(name) {
	return String(name || "?").trim().slice(0, 1);
}

function mapDept(node) {
	const childOrgs = (node.children || []).filter((c) => !c.is_employee);
	return {
		id: node.name,
		name: node.title || node.name,
		count: Number(node.employee_count || 0),
		hasChildren: childOrgs.length > 0,
		raw: node,
	};
}

function mapPerson(node, deptName) {
	return {
		id: node.employee || String(node.name || "").replace(/^__emp__/, ""),
		name: node.title || node.employee_name || node.employee || "",
		title: node.designation || node.head_name || "",
		dept: deptName || "",
	};
}

function indexOrg(node, map = {}) {
	if (!node?.name) return map;
	map[node.name] = node;
	for (const child of node.children || []) {
		if (!child.is_employee) indexOrg(child, map);
	}
	return map;
}

async function loadOrgTree() {
	orgLoading.value = true;
	try {
		const data = await getOrgTree();
		const root = (data?.roots || [])[0] || null;
		companyTitle.value = data?.company_name || root?.title || "公司";
		rootChildren.value = root?.children || [];
		orgById.value = root ? indexOrg(root, {}) : {};
	} catch (e) {
		console.warn("[contract-initiate] load org failed", e);
		Message.error("加载花名册组织失败");
		companyTitle.value = "公司";
		rootChildren.value = [];
		orgById.value = {};
	} finally {
		orgLoading.value = false;
	}
}

function loadRecent() {
	try {
		const raw = localStorage.getItem(RECENT_KEY);
		const list = raw ? JSON.parse(raw) : [];
		recentEmployees.value = Array.isArray(list) ? list.slice(0, 20) : [];
	} catch (e) {
		recentEmployees.value = [];
	}
}

function saveRecent(people) {
	try {
		const map = new Map();
		for (const p of [...people, ...recentEmployees.value]) {
			if (p?.id && !map.has(p.id)) map.set(p.id, p);
		}
		const next = [...map.values()].slice(0, 20);
		recentEmployees.value = next;
		localStorage.setItem(RECENT_KEY, JSON.stringify(next));
	} catch (e) {
		/* ignore */
	}
}

function openPicker() {
	draftSelectedIds.value = selectedEmployees.value.map((e) => e.id);
	draftPeopleMap.value = Object.fromEntries(selectedEmployees.value.map((e) => [e.id, e]));
	pickerKeyword.value = "";
	pathStack.value = [];
	searchPeople.value = [];
	searchDepts.value = [];
	pickerTab.value = "people";
	pickerVisible.value = true;
	if (!rootChildren.value.length && !orgLoading.value) {
		loadOrgTree();
	}
}

function closePicker() {
	pickerVisible.value = false;
}

function onPickerTabChange() {
	pickerKeyword.value = "";
	pathStack.value = [];
	searchPeople.value = [];
	searchDepts.value = [];
}

function enterDept(dept) {
	pickerKeyword.value = "";
	searchPeople.value = [];
	searchDepts.value = [];
	pathStack.value = [...pathStack.value, { id: dept.id, name: dept.name }];
}

function goCrumb(idx) {
	if (idx >= breadcrumb.value.length - 1) return;
	if (idx <= 0) {
		pathStack.value = [];
		return;
	}
	pathStack.value = pathStack.value.slice(0, idx);
}

function onSearchClear() {
	searchPeople.value = [];
	searchDepts.value = [];
}

function onSearchInput() {
	if (searchTimer) clearTimeout(searchTimer);
	const q = pickerKeyword.value.trim();
	if (!q) {
		searchPeople.value = [];
		searchDepts.value = [];
		searchLoading.value = false;
		return;
	}
	searchTimer = setTimeout(() => runSearch(q), 280);
}

async function runSearch(q) {
	searchLoading.value = true;
	try {
		const qLower = q.toLowerCase();
		const depts = [];
		const walk = (nodes) => {
			for (const n of nodes || []) {
				if (n.is_employee) continue;
				if (String(n.title || "").toLowerCase().includes(qLower)) {
					depts.push(mapDept(n));
				}
				walk(n.children);
			}
		};
		walk(rootChildren.value);
		searchDepts.value = depts.slice(0, 20);

		const rows = (await searchEmployees(q)) || [];
		searchPeople.value = rows.map((row) => ({
			id: row.name,
			name: row.employee_name || row.name,
			title: row.designation || "",
			dept: row.department || "",
		}));
	} catch (e) {
		console.warn("[contract-initiate] search failed", e);
		searchPeople.value = [];
	} finally {
		searchLoading.value = false;
	}
}

function togglePerson(person, checked) {
	const id = person.id;
	if (checked) {
		if (props.mode !== "batch") {
			draftSelectedIds.value = [id];
			draftPeopleMap.value = { [id]: person };
			return;
		}
		if (!draftSelectedIds.value.includes(id)) {
			draftSelectedIds.value = [...draftSelectedIds.value, id];
		}
		draftPeopleMap.value = { ...draftPeopleMap.value, [id]: person };
	} else {
		draftSelectedIds.value = draftSelectedIds.value.filter((x) => x !== id);
		const next = { ...draftPeopleMap.value };
		delete next[id];
		draftPeopleMap.value = next;
	}
}

function removeDraft(id) {
	draftSelectedIds.value = draftSelectedIds.value.filter((x) => x !== id);
	const next = { ...draftPeopleMap.value };
	delete next[id];
	draftPeopleMap.value = next;
}

function confirmPicker() {
	selectedEmployees.value = draftSelectedIds.value.map((id) => {
		const p = draftPeopleMap.value[id] || recentEmployees.value.find((r) => r.id === id);
		return {
			id,
			name: p?.name || id,
			title: p?.title || "",
			dept: p?.dept || "",
		};
	});
	saveRecent(selectedEmployees.value);
	pickerVisible.value = false;
	if (selectedEmployees.value.length) {
		Message.success(`已选择 ${selectedEmployees.value.length} 人`);
	}
}

function removeEmployee(id) {
	selectedEmployees.value = selectedEmployees.value.filter((e) => e.id !== id);
}

function goNext() {
	if (!canNext.value) {
		Message.warning("请先选择员工和合同模板");
		return;
	}
	const primary = selectedEmployees.value[0];
	loadEmployeeDetail(primary?.id);
	currentStep.value += 1;
}

function contractFields() {
	return {
		contract_start: formatDate(contractForm.contractStart),
		contract_end: formatDate(contractForm.contractEnd),
		sign_time: String(contractForm.signTime || "").trim(),
		salary: String(contractForm.salary || "").trim(),
		number_text: String(contractForm.numberText || "").trim(),
		join_date_text: String(contractForm.joinDateText || "").trim(),
	};
}

function safeUrl(result) {
	const value =
		(typeof result === "string" ? result : "") ||
		result?.preview_url ||
		result?.data?.preview_url ||
		result?.url ||
		result?.download_url ||
		"";
	if (!value) return "";
	try {
		const url = new URL(value, window.location.origin);
		if (!["http:", "https:"].includes(url.protocol)) return "";
		return url.href;
	} catch (error) {
		return "";
	}
}

async function onGenerateContract() {
	if (!canGenerate.value) {
		Message.warning("请完善右侧必填合同变量后再生成");
		return;
	}
	previewLoading.value = true;
	previewUrl.value = "";
	previewError.value = "";
	submissionReference.value = "";
	currentStep.value = 3;
	try {
		const result = await previewContract({
			employee: selectedEmployees.value[0].id,
			template: selectedTemplateId.value,
			contract_fields: contractFields(),
		});
		previewUrl.value = safeUrl(result);
		if (!previewUrl.value) {
			previewError.value = "后端未返回可用的腾讯电子签预览地址";
		}
	} catch (error) {
		console.warn("[contract-initiate] preview failed", error);
		previewError.value = "腾讯电子签未配置或正式预览生成失败";
	} finally {
		previewLoading.value = false;
	}
}

function onCancel() {
	try {
		window.frappe?.set_route?.("contract-templates");
	} catch (e) {
		/* ignore */
	}
}

function goPickTemplate() {
	try {
		window.frappe?.set_route?.("contract-templates");
	} catch (e) {
		window.location.assign("/desk/contract-templates");
	}
}

function goPendingList() {
	try {
		const go = window.frappe?.set_route;
		if (typeof go === "function") {
			go("contract-signing-pending");
			return;
		}
	} catch (error) {
		console.warn("[contract-initiate] navigate failed", error);
	}
	window.location.assign("/desk/contract-signing-pending");
}

async function onSubmit() {
	if (!previewUrl.value || submitting.value) return;
	submitting.value = true;
	if (!submissionReference.value) {
		submissionReference.value =
			globalThis.crypto?.randomUUID?.() ||
			`${Date.now()}-${Math.random().toString(36).slice(2)}`;
	}
	const fields = contractFields();
	const settled = await Promise.allSettled(
		selectedEmployees.value.map((employee) =>
			createContractSigning({
				employee: employee.id,
				template: selectedTemplateId.value,
				contract_fields: fields,
				trans_reference: `${submissionReference.value}-${employee.id}`,
			}).then((result) => {
				if (result?.ok === false) {
					throw new Error(result.error || "电子签合同发起失败");
				}
				return result;
			})
		)
	);
	submitting.value = false;

	const succeeded = [];
	const failed = [];
	settled.forEach((result, index) => {
		const employee = selectedEmployees.value[index];
		if (result.status === "fulfilled") succeeded.push(employee.name);
		else failed.push(employee.name);
	});

	const content = [
		`成功 ${succeeded.length} 人：${succeeded.join("、") || "无"}`,
		`失败 ${failed.length} 人：${failed.join("、") || "无"}`,
	].join("\n");
	const options = {
		title: failed.length ? "签署发起完成（部分失败）" : "签署发起成功",
		content,
		okText: succeeded.length ? "查看待签合同" : "关闭",
		onOk: succeeded.length ? goPendingList : undefined,
	};
	if (succeeded.length) Modal.success(options);
	else Modal.error(options);
}
</script>
