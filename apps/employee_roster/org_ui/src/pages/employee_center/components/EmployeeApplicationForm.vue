<template>
	<div class="ec-business-form">
		<a-card :bordered="false" class="ec-steps-card">
			<a-steps :current="currentStep" small>
				<a-step v-for="step in steps" :key="step" :title="step" />
			</a-steps>
		</a-card>

		<a-alert v-if="applicationType === 'subsidy'" type="info" title="补贴规则说明">
			餐补 25 元/次；22 点前车补不超过 30 元/次；22 点后实报实销，100 元封顶，并需上传打车单截图。
		</a-alert>

		<a-card :bordered="false" class="ec-form-card">
			<h2>基本信息</h2>
			<a-descriptions :column="4" bordered size="large">
				<a-descriptions-item label="申请人">{{ setup.employee.applicant }}</a-descriptions-item>
				<a-descriptions-item label="工号">{{ setup.employee.employee_number || '—' }}</a-descriptions-item>
				<a-descriptions-item label="部门">{{ setup.employee.department || '—' }}</a-descriptions-item>
				<a-descriptions-item label="岗位">{{ setup.employee.designation || '—' }}</a-descriptions-item>
			</a-descriptions>
		</a-card>

		<a-form ref="formRef" :model="formData" layout="vertical" @submit-success="submitApplication">
			<template v-if="applicationType === 'subsidy'">
				<SubsidyDetails v-model="formData.details" :employees="setup.options.employees" />
			</template>
			<template v-else-if="applicationType === 'handover'">
				<a-card :bordered="false" class="ec-form-card">
					<h2>关联离职申请</h2>
					<a-form-item field="resignation_application" label="关联离职申请单" required>
						<a-select v-model="formData.resignation_application" allow-search placeholder="请选择已提交的离职申请">
							<a-option v-for="item in setup.resignation_applications || []" :key="item.name" :value="item.name">{{ item.application_no }} · {{ item.status }}</a-option>
						</a-select>
					</a-form-item>
				</a-card>
				<HandoverChecklist v-model="formData.items" :employees="setup.options.employees" />
			</template>
			<template v-else>
				<a-card v-for="section in displayedSections" :key="section.title" :bordered="false" class="ec-form-card">
					<div class="ec-section-title"><div><h2>{{ section.title }}</h2><p v-if="section.description">{{ section.description }}</p></div></div>
					<div class="ec-form-grid">
						<a-form-item v-for="field in section.fields" :key="field.key" :field="field.key" :label="field.label" :required="field.required" :rules="field.required ? [{ required: true, message: `请填写${field.label}` }] : []" :class="{ 'is-wide': field.type === 'textarea' || field.type === 'upload' || field.type === 'checkbox' }">
							<a-input v-if="field.type === 'text'" v-model="formData[field.key]" allow-clear :placeholder="field.placeholder || `请输入${field.label}`" />
							<a-textarea v-else-if="field.type === 'textarea'" v-model="formData[field.key]" :max-length="500" show-word-limit auto-size :placeholder="field.placeholder || `请输入${field.label}`" />
							<a-input-number v-else-if="field.type === 'number'" v-model="formData[field.key]" :min="0" hide-button style="width:100%" />
							<a-date-picker v-else-if="field.type === 'date'" v-model="formData[field.key]" value-format="YYYY-MM-DD" style="width:100%" />
							<a-select v-else-if="field.type === 'select'" v-model="formData[field.key]" allow-clear :placeholder="`请选择${field.label}`">
								<a-option v-for="option in field.options || []" :key="option" :value="option">{{ option }}</a-option>
							</a-select>
							<a-select v-else-if="field.type === 'department'" v-model="formData[field.key]" allow-search allow-clear :placeholder="`请选择${field.label}`">
								<a-option v-for="option in setup.options.departments" :key="option" :value="option">{{ option }}</a-option>
							</a-select>
							<a-select v-else-if="field.type === 'designation'" v-model="formData[field.key]" allow-search allow-clear :placeholder="`请选择${field.label}`">
								<a-option v-for="option in setup.options.designations" :key="option" :value="option">{{ option }}</a-option>
							</a-select>
							<a-select v-else-if="field.type === 'employee'" v-model="formData[field.key]" allow-search allow-clear :placeholder="`请选择${field.label}`">
								<a-option v-for="option in setup.options.employees" :key="option.name" :value="option.name">{{ option.employee_name }}（{{ option.employee_number || option.name }}）</a-option>
							</a-select>
							<a-checkbox v-else-if="field.type === 'checkbox'" v-model="formData[field.key]">{{ field.label }}</a-checkbox>
							<AttachmentUploader v-else-if="field.type === 'upload'" v-model="formData[field.key]" />
						</a-form-item>
					</div>
				</a-card>
			</template>

			<a-card v-if="showApprovalPreview" :bordered="false" class="ec-form-card ec-approval-preview">
				<div class="ec-section-title"><div><h2>审批流程</h2><p>审批节点来自系统现有流程配置，员工不可修改</p></div></div>
				<div class="ec-flow-list">
					<div class="ec-flow-person"><a-avatar>{{ setup.employee.applicant?.slice(0,1) }}</a-avatar><span><strong>发起人</strong><small>{{ setup.employee.applicant }}</small></span></div>
					<template v-for="node in setup.process_preview || []" :key="node.id">
						<icon-right class="ec-flow-arrow" />
						<div class="ec-flow-person" :class="{ 'is-empty': node.empty }"><a-avatar><icon-user /></a-avatar><span><strong>{{ node.label }}</strong><small>{{ node.people?.map((p:any) => p.full_name).join('、') || '待配置' }}</small></span></div>
					</template>
				</div>
			</a-card>
		</a-form>

		<div class="ec-form-actions">
			<a-button @click="$emit('cancel')">取消</a-button>
			<a-button v-if="isOnboarding && currentStep > 1" @click="previousStep">上一步</a-button>
			<a-button :loading="saving" @click="saveDraft">保存草稿</a-button>
			<a-button v-if="isOnboarding && currentStep < steps.length" type="primary" @click="nextStep">下一步</a-button>
			<a-button v-else type="primary" :loading="submitting" @click="validateAndSubmit">提交申请</a-button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import { IconRight, IconUser } from "@arco-design/web-vue/es/icon";
import { saveEmployeeApplication } from "../../../api/employeeCenter";
import { formSections, formSteps, type BusinessView } from "../applicationFormConfig";
import AttachmentUploader from "./AttachmentUploader.vue";
import SubsidyDetails from "./SubsidyDetails.vue";
import HandoverChecklist from "./HandoverChecklist.vue";

const props = defineProps<{ applicationType: BusinessView; setup: any }>();
const emit = defineEmits<{ cancel: []; saved: [result: any]; submitted: [result: any] }>();
const formRef = ref<any>();
const saving = ref(false);
const submitting = ref(false);
const instanceName = ref(props.setup.draft?.name || "");
const formData = reactive<Record<string, any>>({ ...(props.setup.profile_defaults || {}), ...(props.setup.draft?.data || {}) });
if (props.applicationType === "subsidy" && !formData.details) formData.details = [];
if (props.applicationType === "handover" && !formData.items) formData.items = [];
if (props.applicationType === "onboarding" && !formData.submitted_date) formData.submitted_date = new Date().toISOString().slice(0, 10);

const steps = computed(() => formSteps[props.applicationType]);
const currentStep = ref(1);
const isOnboarding = computed(() => props.applicationType === "onboarding");
const visibleSections = computed(() => formSections[props.applicationType].map(section => ({ ...section, fields: section.fields.filter(field => !field.show || field.show(formData)) })));
const displayedSections = computed(() => isOnboarding.value ? visibleSections.value.slice(currentStep.value - 1, currentStep.value) : visibleSections.value);
const showApprovalPreview = computed(() => !isOnboarding.value || currentStep.value === steps.value.length);

async function persist(submit: boolean) {
	const state = submit ? submitting : saving;
	if (state.value) return;
	state.value = true;
	try {
		const result = await saveEmployeeApplication(props.applicationType, { ...formData }, { instanceName: instanceName.value || undefined, submit });
		instanceName.value = result.name;
		Message.success(submit ? "申请已提交" : "草稿已保存");
		if (submit) emit("submitted", result);
		else emit("saved", result);
	} catch (error: any) {
		Message.error(error?.message || (submit ? "提交失败" : "保存失败"));
	} finally { state.value = false; }
}
function saveDraft() { persist(false); }
function submitApplication() { persist(true); }
function previousStep() {
	if (currentStep.value > 1) currentStep.value -= 1;
}
async function nextStep() {
	const errors = await formRef.value?.validate?.();
	if (!errors && currentStep.value < steps.value.length) currentStep.value += 1;
}
async function validateAndSubmit() {
	const errors = await formRef.value?.validate?.();
	if (!errors) submitApplication();
}
</script>
