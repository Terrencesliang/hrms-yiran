<template>
	<div class="arco-org-ui contract-initiate">
		<ContractSectionNav group="signing" active-key="contract-initiate" />
		<ContractActionToolbar
			title="基于模板发起签署"
			description="填写法大大模板控件，生成正式预览后发起签署任务"
		/>
		<a-alert v-if="props.mode === 'batch'" type="warning" show-icon>
			当前电子签流程暂不支持批量发起，已切换为单人签署；每次只能选择一名员工。
		</a-alert>

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
							<span class="ci-template-desc">印章 ID：{{ props.sealId || "未配置" }}</span>
							<span class="ci-template-desc">企业盖章：负责人在员工签署后进入法大大人工验证</span>
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

		<!-- Step 2: 确认模板控件映射与变量 -->
		<div v-show="currentStep === 2" class="ci-step-body ci-confirm-layout">
			<div class="ci-doc-pane">
				<div class="ci-preview-toolbar">
					<div>
						<div class="ci-section-title">整份合同预览</div>
						<div class="ci-preview-toolbar-hint">
							右侧字段会实时显示在合同对应位置，无需反复生成预览。
						</div>
					</div>
					<a-button
						type="outline"
						:disabled="!canGenerate"
						:loading="editorLoading"
						@click="loadEditorPreview(true)"
					>
						刷新模板底稿
					</a-button>
				</div>
				<a-spin :loading="editorLoading" class="ci-real-preview-spin">
					<div v-if="editorPages.length" class="ci-live-preview">
						<div
							v-for="page in editorPages"
							:key="page.number"
							class="ci-live-page"
							:style="{ aspectRatio: `${page.width} / ${page.height}` }"
						>
							<canvas :ref="(el) => setEditorCanvas(el, page.number)" />
							<span
								v-for="field in editorFieldsForPage(page.number)"
								:key="field.field_id"
								class="ci-live-field"
								:class="{ 'is-empty': !editorFieldValue(field) }"
								:style="editorFieldStyle(field)"
								:title="field.field_name"
							>
								{{ editorFieldValue(field) || `待填：${field.field_name}` }}
							</span>
						</div>
					</div>
					<a-card v-else :bordered="false" class="ci-template-mapping-card">
					<a-result status="info" title="合同底稿将在字段完整后自动加载">
						<template #subtitle>
							请完善右侧必填字段；加载后修改内容会立即显示在合同对应位置。
						</template>
					</a-result>
					<a-descriptions :column="1" bordered>
						<a-descriptions-item label="签署任务模板">{{ selectedTemplate?.name || "—" }}</a-descriptions-item>
						<a-descriptions-item label="法大大模板 ID">{{
							props.providerTemplateId || "—"
						}}</a-descriptions-item>
						<a-descriptions-item label="字段映射">
							contract_start、contract_end、sign_time、salary、number_text、join_date_text
						</a-descriptions-item>
					</a-descriptions>
					</a-card>
				</a-spin>
			</div>

			<aside class="ci-form-pane">
				<div class="ci-form-title">填充法大大模板控件</div>
				<a-alert type="info" class="ci-field-mapping-alert">
					员工档案已有值的字段保持只读；档案为空时可临时补填，仅用于本次合同。
				</a-alert>
				<a-spin :loading="employeeDetailLoading" class="ci-form-spin">
					<a-form :model="contractForm" layout="vertical" class="ci-var-form" auto-label-width>
						<a-form-item label="员工姓名">
							<a-input :model-value="contractForm.employeeName" readonly />
						</a-form-item>
						<a-form-item label="证件号码" required>
							<a-input
								v-model="contractForm.idNumber"
								:readonly="employeeFieldLocked.idNumber"
								placeholder="员工档案为空，可临时补填"
							/>
						</a-form-item>
						<a-form-item label="性别" required>
							<a-input
								v-model="contractForm.gender"
								:readonly="employeeFieldLocked.gender"
								placeholder="员工档案为空，可临时补填"
							/>
						</a-form-item>
						<a-form-item label="岗位" required>
							<a-input
								v-model="contractForm.designation"
								:readonly="employeeFieldLocked.designation"
								placeholder="员工档案为空，可临时补填"
							/>
						</a-form-item>
						<a-form-item label="试用期" required>
							<a-input
								v-model="contractForm.probation"
								:readonly="employeeFieldLocked.probation"
								placeholder="例如：3个月"
							/>
						</a-form-item>
						<a-form-item label="手机号码" required>
							<a-input
								v-model="contractForm.mobile"
								:readonly="employeeFieldLocked.mobile"
								placeholder="员工档案为空，可临时补填"
							/>
						</a-form-item>
						<a-form-item label="现居住地" required>
							<a-input
								v-model="contractForm.address"
								:readonly="employeeFieldLocked.address"
								placeholder="员工档案为空，可临时补填"
							/>
						</a-form-item>

						<a-divider class="ci-form-divider" />

						<a-form-item label="合同开始日期（contract_start）" required>
							<a-date-picker
								v-model="contractForm.contractStart"
								style="width: 100%"
								value-format="YYYY-MM-DD"
								placeholder="选择日期"
							/>
						</a-form-item>
						<a-form-item label="合同结束日期（contract_end）" required>
							<a-date-picker
								v-model="contractForm.contractEnd"
								style="width: 100%"
								value-format="YYYY-MM-DD"
								placeholder="选择日期"
							/>
						</a-form-item>
						<a-form-item label="签署时间（sign_time）" required>
							<a-input
								v-model="contractForm.signTime"
								placeholder="请输入..."
								allow-clear
							/>
						</a-form-item>
						<a-form-item label="职级薪资（salary）" required>
							<a-input
								v-model="contractForm.salary"
								placeholder="请输入..."
								allow-clear
							/>
						</a-form-item>
						<a-form-item label="数字文本（number_text）">
							<a-input
								v-model="contractForm.numberText"
								placeholder="请输入..."
								allow-clear
							/>
						</a-form-item>
						<a-form-item label="入职时间（join_date_text）" required>
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
						? "已获取法大大正式预览，请核对后发起签署。"
						: previewError || "尚未生成法大大正式合同预览。"
				}}
			</a-alert>
			<a-card :bordered="false" class="ci-flow-summary">
				<div class="ci-section-title">签署流程摘要</div>
				<a-steps :current="1" small>
					<a-step title="系统固化合同" description="预填字段生成法大大签署文件" />
					<a-step title="员工先签" description="员工核对合同并完成签署" />
					<a-step title="企业人工盖章" description="企业负责人进入法大大完成验证与盖章" />
				</a-steps>
				<a-descriptions :column="2" bordered>
					<a-descriptions-item label="模板印章 ID">{{ props.sealId || "未配置" }}</a-descriptions-item>
					<a-descriptions-item label="企业盖章方式">
						人工验证盖章
					</a-descriptions-item>
				</a-descriptions>
			</a-card>
			<div class="ci-doc-pane ci-doc-pane--final">
				<a-spin :loading="previewLoading" class="ci-real-preview-spin">
					<div v-if="previewUrl" class="ci-real-preview">
						<a-result
							v-if="externalPreviewUrl"
							status="success"
							title="法大大官方预览已生成"
							subtitle="法大大禁止跨域嵌入该页面，已在新窗口打开；也可点击下方按钮再次查看。"
						>
							<template #extra>
								<a-button type="primary" @click="openOfficialPreview">
									打开法大大官方预览
								</a-button>
							</template>
						</a-result>
						<iframe
							v-else
							:src="previewUrl"
							title="合同预览"
							class="ci-real-preview-frame"
							referrerpolicy="no-referrer"
							@error="previewFrameFailed = true"
						/>
						<a-alert v-if="previewFrameFailed" type="warning">
							浏览器无法内嵌该预览，请使用下方链接在新窗口打开。
						</a-alert>
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
				@click="onStep2Primary"
			>
				{{ step2PrimaryLabel }}
			</a-button>
			<a-button
				v-else
				type="primary"
				:disabled="!canNext || !previewUrl || previewStale"
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
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { Message, Modal } from "@arco-design/web-vue";
import * as pdfjsLib from "pdfjs-dist";
import pdfWorkerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import {
	IconApps,
	IconCheckCircleFill,
	IconRight,
	IconSearch,
	IconUserAdd,
} from "@arco-design/web-vue/es/icon";
import { call, getOrgTree, searchEmployees } from "../../api";
import {
	createContractSigning,
	getContractEditorPreview,
	previewContract,
} from "../../api/contract.js";
import ContractActionToolbar from "./ContractActionToolbar.vue";
import ContractSectionNav from "./ContractSectionNav.vue";

const RECENT_KEY = "contract-initiate-recent";
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

const props = defineProps({
	templateId: { type: String, default: "" },
	providerTemplateId: { type: String, default: "" },
	templateName: { type: String, default: "" },
	mode: { type: String, default: "single" },
	openPicker: { type: Boolean, default: true },
	sealId: { type: String, default: "" },
	businessId: { type: String, default: "" },
	employeeActorId: { type: String, default: "" },
	corpActorId: { type: String, default: "" },
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
const editorLoading = ref(false);
const editorBasePdfUrl = ref("");
const editorFields = ref([]);
const editorPages = ref([]);
const editorPageWidth = ref(793.76);
const editorPageHeight = ref(1122.56);
const previewLoading = ref(false);
const previewUrl = ref("");
const externalPreviewUrl = ref("");
const previewIsFilled = ref(false);
const previewError = ref("");
const previewFrameFailed = ref(false);
const previewFingerprint = ref("");
const previewTransReference = ref("");
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

const employeeFieldLocked = reactive({
	idNumber: false,
	gender: false,
	designation: false,
	probation: false,
	mobile: false,
	address: false,
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
let editorRenderToken = 0;
const editorCanvases = new Map();

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
			String(contractForm.idNumber || "").trim() &&
			String(contractForm.gender || "").trim() &&
			String(contractForm.designation || "").trim() &&
			String(contractForm.probation || "").trim() &&
			String(contractForm.mobile || "").trim() &&
			String(contractForm.address || "").trim() &&
			formatDate(contractForm.contractStart) &&
			formatDate(contractForm.contractEnd) &&
			String(contractForm.signTime || "").trim() &&
			String(contractForm.salary || "").trim() &&
			String(contractForm.numberText || "").trim() &&
			String(contractForm.joinDateText || "").trim()
	);
});

const currentPreviewFingerprint = computed(() =>
	JSON.stringify({
		employee: selectedEmployees.value[0]?.id || "",
		template: selectedTemplateId.value,
		fields: contractFields(),
	})
);

const previewStale = computed(
	() =>
		Boolean(previewUrl.value) &&
		previewFingerprint.value !== currentPreviewFingerprint.value
);

const step2PrimaryLabel = computed(() => {
	return previewLoading.value ? "正在生成预览" : "下一步预览";
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
	Object.keys(employeeFieldLocked).forEach((key) => {
		employeeFieldLocked[key] = false;
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
		const idNumber =
			doc.hr_id_number ||
			doc.custom_id_number ||
			doc.id_number ||
			doc.passport_number ||
			doc.uid ||
			"";
		const gender = doc.gender || "";
		const designation = doc.designation || "";
		const probation = doc.hr_probation_months
			? `${doc.hr_probation_months}个月`
			: doc.probation_period
			? `${doc.probation_period}个月`
			: doc.custom_probation || "";
		const mobile = doc.cell_number || doc.personal_mobile || "";
		const address =
			doc.current_address || doc.permanent_address || doc.person_to_be_contacted || "";
		Object.assign(contractForm, {
			idNumber,
			gender,
			designation,
			probation,
			mobile,
			address,
		});
		Object.assign(employeeFieldLocked, {
			idNumber: Boolean(idNumber),
			gender: Boolean(gender),
			designation: Boolean(designation),
			probation: Boolean(probation),
			mobile: Boolean(mobile),
			address: Boolean(address),
		});
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

watch(canGenerate, (ready) => {
	if (
		ready &&
		currentStep.value === 2 &&
		!editorBasePdfUrl.value &&
		!editorLoading.value
	) {
		loadEditorPreview();
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
		draftSelectedIds.value = [id];
		draftPeopleMap.value = { [id]: person };
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
	const selectedIds = draftSelectedIds.value.slice(0, 1);
	selectedEmployees.value = selectedIds.map((id) => {
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

async function goNext() {
	if (!canNext.value) {
		Message.warning("请先选择员工和合同模板");
		return;
	}
	const primary = selectedEmployees.value[0];
	currentStep.value = 2;
	await loadEmployeeDetail(primary?.id);
	if (canGenerate.value) await loadEditorPreview();
}

function contractFields() {
	return {
		id_number: String(contractForm.idNumber || "").trim(),
		gender: String(contractForm.gender || "").trim(),
		designation: String(contractForm.designation || "").trim(),
		probation: String(contractForm.probation || "").trim(),
		mobile: String(contractForm.mobile || "").trim(),
		address: String(contractForm.address || "").trim(),
		contract_start: formatDate(contractForm.contractStart),
		contract_end: formatDate(contractForm.contractEnd),
		sign_time: String(contractForm.signTime || "").trim(),
		salary: String(contractForm.salary || "").trim(),
		number_text: String(contractForm.numberText || "").trim(),
		join_date_text: String(contractForm.joinDateText || "").trim(),
	};
}

function setEditorCanvas(element, pageNumber) {
	if (element) editorCanvases.set(pageNumber, element);
	else editorCanvases.delete(pageNumber);
}

function editorFieldsForPage(pageNumber) {
	return editorFields.value.filter(
		(field) => Number(field?.position?.positionPageNo || 0) === pageNumber
	);
}

function displayEditorDate(value) {
	const match = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})/);
	return match ? `${match[1]}年${match[2]}月${match[3]}日` : value;
}

function editorFieldValue(field) {
	const source = String(field?.source || "");
	let value = "";
	if (source === "$employee.employee_name") {
		value = contractForm.employeeName;
	} else if (source.startsWith("$contract.")) {
		value = contractFields()[source.slice("$contract.".length)] || "";
	}
	return field?.field_type === "fill_date" ? displayEditorDate(value) : String(value || "");
}

function editorFieldStyle(field) {
	const position = field?.position || {};
	const width = Number(field.width || 160);
	const height = Number(field.height || 30);
	const alignment = String(field.alignment || "left");
	return {
		left: `${((Number(position.positionX || 0) - width / 2) / editorPageWidth.value) * 100}%`,
		top: `${((Number(position.positionY || 0) - height / 2) / editorPageHeight.value) * 100}%`,
		width: `${(width / editorPageWidth.value) * 100}%`,
		height: `${(height / editorPageHeight.value) * 100}%`,
		fontSize: `${Number(field.font_size || 16) / 7.9376}cqw`,
		justifyContent:
			alignment === "center" ? "center" : alignment === "right" ? "flex-end" : "flex-start",
	};
}

async function renderEditorPdf(url) {
	const token = ++editorRenderToken;
	const pdf = await pdfjsLib.getDocument({ url, withCredentials: true }).promise;
	const pages = [];
	for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
		const page = await pdf.getPage(pageNumber);
		const viewport = page.getViewport({ scale: 1 });
		pages.push({ number: pageNumber, width: viewport.width, height: viewport.height });
	}
	if (token !== editorRenderToken) return;
	editorPages.value = pages;
	await nextTick();
	for (const item of pages) {
		if (token !== editorRenderToken) return;
		const page = await pdf.getPage(item.number);
		const viewport = page.getViewport({ scale: 1.5 });
		const canvas = editorCanvases.get(item.number);
		if (!canvas) continue;
		canvas.width = viewport.width;
		canvas.height = viewport.height;
		await page.render({
			canvasContext: canvas.getContext("2d"),
			viewport,
		}).promise;
	}
}

async function loadEditorPreview(forceRefresh = false) {
	if (!canGenerate.value || editorLoading.value) return;
	editorLoading.value = true;
	try {
		const employee = selectedEmployees.value[0];
		const result = await getContractEditorPreview({
			template: selectedTemplateId.value,
			employee: employee.id,
			contract_fields: contractFields(),
			force_refresh: forceRefresh ? 1 : 0,
		});
		const payload = result?.data || result;
		editorPageWidth.value = Number(payload?.page_width || 793.76);
		editorPageHeight.value = Number(payload?.page_height || 1122.56);
		editorFields.value = Array.isArray(payload?.fields) ? payload.fields : [];
		editorBasePdfUrl.value = safeUrl(payload?.base_pdf_url);
		if (!editorBasePdfUrl.value) throw new Error("后端未返回合同模板底稿");
		await renderEditorPdf(editorBasePdfUrl.value);
	} catch (error) {
		console.warn("[contract-initiate] editor preview failed", error);
		editorPages.value = [];
		Message.error(backendError(error, "合同模板底稿加载失败"));
	} finally {
		editorLoading.value = false;
	}
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

function backendError(error, fallback) {
	return (
		error?.response?.data?.message ||
		error?.response?.data?.error ||
		error?.message ||
		fallback
	);
}

async function onGenerateContract() {
	if (!canGenerate.value) {
		Message.warning("请完善右侧必填合同变量后再生成");
		return;
	}
	const officialWindow = window.open("", "_blank");
	if (officialWindow) {
		officialWindow.opener = null;
		officialWindow.document.title = "正在生成法大大官方预览";
		officialWindow.document.body.textContent = "正在生成法大大官方合同预览，请稍候…";
	}
	previewLoading.value = true;
	previewError.value = "";
	previewFrameFailed.value = false;
	try {
		if (!submissionReference.value) {
			submissionReference.value =
				globalThis.crypto?.randomUUID?.() ||
				`${Date.now()}-${Math.random().toString(36).slice(2)}`;
		}
		const primaryEmployee = selectedEmployees.value[0];
		const fields = contractFields();
		const requestedFingerprint = currentPreviewFingerprint.value;
		const result = await previewContract({
			employee: primaryEmployee.id,
			template: selectedTemplateId.value,
			contract_fields: fields,
			trans_reference: `${submissionReference.value}-${primaryEmployee.id}`,
		});
		previewUrl.value = safeUrl(result);
		externalPreviewUrl.value = safeUrl(
			result?.external_preview_url || result?.data?.external_preview_url
		);
		previewIsFilled.value = Boolean(
			result?.preview_is_filled ?? result?.data?.preview_is_filled
		);
		if (officialWindow && externalPreviewUrl.value) {
			officialWindow.location.replace(externalPreviewUrl.value);
		}
		previewTransReference.value =
			result?.trans_reference || result?.data?.trans_reference || "";
		if (!previewUrl.value) {
			previewError.value = "后端未返回可用的法大大正式预览地址";
			return false;
		}
		previewFingerprint.value = requestedFingerprint;
		return true;
	} catch (error) {
		officialWindow?.close();
		console.warn("[contract-initiate] preview failed", error);
		previewUrl.value = "";
		externalPreviewUrl.value = "";
		previewIsFilled.value = false;
		previewTransReference.value = "";
		previewFingerprint.value = "";
		previewError.value = backendError(error, "法大大正式预览生成失败");
		Message.error(previewError.value);
		return false;
	} finally {
		if (officialWindow && !externalPreviewUrl.value) officialWindow.close();
		previewLoading.value = false;
	}
}

async function onStep2Primary() {
	if (!previewUrl.value || previewStale.value) {
		if (!(await onGenerateContract())) return;
	}
	currentStep.value = 3;
}

function openOfficialPreview() {
	if (!externalPreviewUrl.value) return;
	window.open(externalPreviewUrl.value, "_blank", "noopener,noreferrer");
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
	const employee = selectedEmployees.value[0];
	if (!employee || selectedEmployees.value.length !== 1) {
		Message.warning("请只选择一名员工后发起签署");
		return;
	}
	submitting.value = true;
	if (!submissionReference.value) {
		submissionReference.value =
			globalThis.crypto?.randomUUID?.() ||
			`${Date.now()}-${Math.random().toString(36).slice(2)}`;
	}
	let failure = "";
	try {
		const result = await createContractSigning({
			employee: employee.id,
			template: selectedTemplateId.value,
			contract_fields: contractFields(),
			trans_reference: previewTransReference.value || `${submissionReference.value}-${employee.id}`,
		});
		if (result?.ok === false) {
			throw new Error(result?.error?.message || result.error || result.message || "电子签合同发起失败");
		}
	} catch (error) {
		failure = backendError(error, "电子签合同发起失败");
	}
	submitting.value = false;
	if (failure) {
		Modal.error({ title: "签署发起失败", content: `${employee.name}：${failure}` });
		return;
	}
	Modal.success({
		title: "签署发起成功",
		content: `已为 ${employee.name} 创建合同并发送邮件邀请，无需再确认合同内容。`,
		okText: "查看待签合同",
		onOk: goPendingList,
	});
}
</script>
