<template>
	<div class="arco-emp-archive-tab" v-if="doc">
		<a-spin :loading="loading" style="width: 100%">
			<div class="arco-emp-archive-stack">
				<!-- 基础任职信息 -->
				<EmployeeEditableSection
					title="基础任职信息"
					section-key="employment_basic"
					:can-edit="canEdit"
					:reset-token="resetToken"
					@edit="startEdit('employment_basic')"
					@cancel="cancelEdit('employment_basic')"
					@save="(ctl) => saveSection('employment_basic', ctl)"
				>
					<template #view>
						<EmployeePreviewGrid :items="basicViewItems" />
					</template>
					<template #edit>
						<a-form :model="forms.employment_basic" layout="vertical" class="arco-emp-archive-form">
							<a-row :gutter="16">
								<a-col :span="8">
									<a-form-item label="工号" required>
										<a-input v-model="forms.employment_basic.employee_number" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="部门" required>
										<a-input v-model="forms.employment_basic.department" placeholder="部门名称" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="兼任">
										<a-input v-model="forms.employment_basic.hr_concurrent_post" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="职务" required>
										<a-input v-model="forms.employment_basic.hr_job_title" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="岗位" required>
										<a-input v-model="forms.employment_basic.designation" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="岗位类别">
										<a-select
											v-model="forms.employment_basic.hr_position_category"
											allow-clear
											:options="positionCategoryOptions"
										/>
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="职级" required>
										<a-input v-model="forms.employment_basic.grade" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="职等">
										<a-input v-model="forms.employment_basic.hr_job_grade_level" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="合同公司" required>
										<a-input v-model="forms.employment_basic.company" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="身份">
										<a-select
											v-model="forms.employment_basic.hr_employee_identity"
											allow-clear
											:options="identityOptions"
										/>
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="汇报上级" required>
										<a-input v-model="forms.employment_basic.reports_to" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="工作地点" required>
										<a-input v-model="forms.employment_basic.hr_work_location" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="工作城市">
										<a-input v-model="forms.employment_basic.hr_work_city" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="工时制度">
										<a-select
											v-model="forms.employment_basic.hr_work_hours_system"
											allow-clear
											:options="workHoursOptions"
										/>
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="招聘渠道">
										<a-input v-model="forms.employment_basic.hr_recruitment_channel" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="考勤编号">
										<a-input v-model="forms.employment_basic.attendance_device_id" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="OA编码">
										<a-input v-model="forms.employment_basic.hr_oa_code" />
									</a-form-item>
								</a-col>
								<a-col :span="24">
									<a-form-item label="详细工作地址">
										<a-textarea v-model="forms.employment_basic.hr_work_address" :auto-size="{ minRows: 2 }" />
									</a-form-item>
								</a-col>
							</a-row>
						</a-form>
					</template>
				</EmployeeEditableSection>

				<!-- 员工状态 -->
				<EmployeeEditableSection
					title="员工状态"
					section-key="employment_status"
					:can-edit="canEdit"
					:reset-token="resetToken"
					@edit="startEdit('employment_status')"
					@cancel="cancelEdit('employment_status')"
					@save="(ctl) => saveSection('employment_status', ctl)"
				>
					<template #view>
						<EmployeePreviewGrid :items="statusViewItems" />
					</template>
					<template #edit>
						<a-form :model="forms.employment_status" layout="vertical" class="arco-emp-archive-form">
							<a-row :gutter="16">
								<a-col :span="8">
									<a-form-item label="工作性质" required>
										<a-select v-model="forms.employment_status.employment_type" :options="EMPLOYMENT_TYPE_OPTIONS" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="员工状态" required>
										<a-select v-model="forms.employment_status.status" :options="STATUS_OPTIONS" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="入职日期" required>
										<a-date-picker
											v-model="forms.employment_status.date_of_joining"
											style="width: 100%"
											value-format="YYYY-MM-DD"
										/>
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="试用期" required>
										<a-select v-model="forms.employment_status.hr_probation_months" :options="PROBATION_OPTIONS" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="转正日期">
										<a-date-picker
											v-model="forms.employment_status.final_confirmation_date"
											style="width: 100%"
											value-format="YYYY-MM-DD"
										/>
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="预计转正日期">
										<a-date-picker
											v-model="forms.employment_status.scheduled_confirmation_date"
											style="width: 100%"
											value-format="YYYY-MM-DD"
										/>
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="司龄开始日期">
										<a-date-picker
											v-model="forms.employment_status.hr_company_tenure_start"
											style="width: 100%"
											value-format="YYYY-MM-DD"
										/>
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="司龄">
										<a-input :model-value="yearsLabel(doc.company_tenure_years)" disabled />
									</a-form-item>
								</a-col>
							</a-row>
						</a-form>
					</template>
				</EmployeeEditableSection>

				<!-- 离职信息 -->
				<EmployeeEditableSection
					title="离职信息"
					section-key="employment_exit"
					:can-edit="canEdit"
					:reset-token="resetToken"
					@edit="startEdit('employment_exit')"
					@cancel="cancelEdit('employment_exit')"
					@save="(ctl) => saveSection('employment_exit', ctl)"
				>
					<template #view>
						<EmployeePreviewGrid :items="exitViewItems" />
					</template>
					<template #edit>
						<a-form :model="forms.employment_exit" layout="vertical" class="arco-emp-archive-form">
							<a-row :gutter="16">
								<a-col :span="8">
									<a-form-item label="离职申请日期">
										<a-date-picker v-model="forms.employment_exit.hr_leave_apply_date" style="width: 100%" value-format="YYYY-MM-DD" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="最后工作日">
										<a-date-picker v-model="forms.employment_exit.hr_last_working_day" style="width: 100%" value-format="YYYY-MM-DD" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="离职日期">
										<a-date-picker v-model="forms.employment_exit.relieving_date" style="width: 100%" value-format="YYYY-MM-DD" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="离职类型">
										<a-select v-model="forms.employment_exit.hr_leave_type" allow-clear :options="leaveTypeOptions" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="离职原因">
										<a-input v-model="forms.employment_exit.reason_for_leaving" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="离职去向">
										<a-input v-model="forms.employment_exit.hr_leave_destination" />
									</a-form-item>
								</a-col>
								<a-col :span="24">
									<a-form-item label="离职备注">
										<a-textarea v-model="forms.employment_exit.hr_leave_remarks" :auto-size="{ minRows: 2 }" />
									</a-form-item>
								</a-col>
							</a-row>
						</a-form>
					</template>
				</EmployeeEditableSection>

				<!-- 任职记录 -->
				<EmployeeRecordList
						title="任职记录"
						section-key="internal_work_history"
						:records="doc.internal_work_history || []"
						:can-edit="canEdit"
						empty-text="暂无任职记录"
						@add="openHistoryModal()"
						@edit="openHistoryModal"
						@remove="removeChild('internal_work_history', $event)"
					>
						<template #item="{ row }">
							<div class="arco-emp-record-title">{{ blank(row.designation) }}</div>
							<div class="arco-emp-record-sub">
								{{ blank(row.department) }} · {{ dateRange(row.from_date, row.to_date) }}
							</div>
						</template>
					</EmployeeRecordList>

				<!-- 奖惩记录 -->
				<EmployeeRecordList
						title="奖惩记录"
						section-key="rewards"
						:records="doc.rewards || []"
						:can-edit="canEdit"
						empty-text="暂无奖惩记录"
						@add="openRewardModal()"
						@edit="openRewardModal"
						@remove="removeChild('rewards', $event)"
					>
						<template #item="{ row }">
							<div class="arco-emp-record-title">
								<a-tag :color="row.record_type === '惩罚' ? 'red' : 'green'" size="small">{{ blank(row.record_type) }}</a-tag>
								{{ blank(row.title) }}
							</div>
							<div class="arco-emp-record-sub">{{ blank(formatDate(row.occur_date)) }}</div>
						</template>
					</EmployeeRecordList>

				<!-- 考察期 / 退休 -->
				<EmployeeEditableSection
					title="考察期信息"
					section-key="employment_exam"
					:can-edit="canEdit"
					:reset-token="resetToken"
					@edit="startEdit('employment_exam')"
					@cancel="cancelEdit('employment_exam')"
					@save="(ctl) => saveSection('employment_exam', ctl)"
				>
					<template #view>
						<EmployeePreviewGrid :items="examViewItems" />
					</template>
					<template #edit>
						<a-form :model="forms.employment_exam" layout="vertical" class="arco-emp-archive-form">
							<a-row :gutter="16">
								<a-col :span="8">
									<a-form-item label="考察期开始">
										<a-date-picker v-model="forms.employment_exam.hr_exam_start" style="width: 100%" value-format="YYYY-MM-DD" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="考察期结束">
										<a-date-picker v-model="forms.employment_exam.hr_exam_end" style="width: 100%" value-format="YYYY-MM-DD" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="考察结果">
										<a-input v-model="forms.employment_exam.hr_exam_result" />
									</a-form-item>
								</a-col>
								<a-col :span="24">
									<a-form-item label="考察备注">
										<a-textarea v-model="forms.employment_exam.hr_exam_remarks" :auto-size="{ minRows: 2 }" />
									</a-form-item>
								</a-col>
							</a-row>
						</a-form>
					</template>
				</EmployeeEditableSection>

				<EmployeeEditableSection
					title="退休信息"
					section-key="employment_retire"
					:can-edit="canEdit"
					:reset-token="resetToken"
					@edit="startEdit('employment_retire')"
					@cancel="cancelEdit('employment_retire')"
					@save="(ctl) => saveSection('employment_retire', ctl)"
				>
					<template #view>
						<EmployeePreviewGrid :items="retireViewItems" />
					</template>
					<template #edit>
						<a-form :model="forms.employment_retire" layout="vertical" class="arco-emp-archive-form">
							<a-form-item label="退休日期">
								<a-date-picker v-model="forms.employment_retire.date_of_retirement" style="width: 240px" value-format="YYYY-MM-DD" />
							</a-form-item>
						</a-form>
					</template>
				</EmployeeEditableSection>
			</div>
		</a-spin>

		<a-modal
			v-model:visible="historyModal.visible"
			:title="historyModal.row?.name ? '编辑任职记录' : '新增任职记录'"
			:ok-loading="historyModal.saving"
			unmount-on-close
			@ok="submitHistory"
		>
			<a-form :model="historyModal.form" layout="vertical">
				<a-form-item label="部门" required>
					<a-input v-model="historyModal.form.department" />
				</a-form-item>
				<a-form-item label="岗位" required>
					<a-input v-model="historyModal.form.designation" />
				</a-form-item>
				<a-form-item label="开始日期">
					<a-date-picker v-model="historyModal.form.from_date" style="width: 100%" value-format="YYYY-MM-DD" />
				</a-form-item>
				<a-form-item label="结束日期">
					<a-date-picker v-model="historyModal.form.to_date" style="width: 100%" value-format="YYYY-MM-DD" />
				</a-form-item>
			</a-form>
		</a-modal>

		<a-modal
			v-model:visible="rewardModal.visible"
			:title="rewardModal.row?.name ? '编辑奖惩记录' : '新增奖惩记录'"
			:ok-loading="rewardModal.saving"
			unmount-on-close
			@ok="submitReward"
		>
			<a-form :model="rewardModal.form" layout="vertical">
				<a-form-item label="类型" required>
					<a-select v-model="rewardModal.form.record_type" :options="[{label:'奖励',value:'奖励'},{label:'惩罚',value:'惩罚'}]" />
				</a-form-item>
				<a-form-item label="事项" required>
					<a-input v-model="rewardModal.form.title" />
				</a-form-item>
				<a-form-item label="发生日期">
					<a-date-picker v-model="rewardModal.form.occur_date" style="width: 100%" value-format="YYYY-MM-DD" />
				</a-form-item>
				<a-form-item label="说明">
					<a-textarea v-model="rewardModal.form.remarks" :auto-size="{ minRows: 2 }" />
				</a-form-item>
			</a-form>
		</a-modal>
	</div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { Message, Modal } from "@arco-design/web-vue";
import EmployeeEditableSection from "../EmployeeEditableSection.vue";
import EmployeePreviewGrid from "../EmployeePreviewGrid.vue";
import EmployeeRecordList from "../EmployeeRecordList.vue";
import { saveEmployeeChildRow, saveEmployeeSection } from "../../../api/employeeDetail";
import {
	blank,
	dateRange,
	EMPLOYMENT_TYPE_OPTIONS,
	employmentTypeLabel,
	errMessage,
	formatDate,
	PROBATION_OPTIONS,
	STATUS_OPTIONS,
	statusLabel,
	yearsLabel,
} from "../../../utils/employeeArchive";

const props = defineProps({
	doc: { type: Object, required: true },
	loading: { type: Boolean, default: false },
	canEdit: { type: Boolean, default: false },
	resetToken: { type: Number, default: 0 },
});

const emit = defineEmits(["updated"]);

const SECTION_KEYS = {
	employment_basic: [
		"employee_number",
		"department",
		"hr_concurrent_post",
		"hr_job_title",
		"designation",
		"hr_position_category",
		"grade",
		"hr_job_grade_level",
		"company",
		"hr_employee_identity",
		"reports_to",
		"hr_work_location",
		"hr_work_city",
		"hr_work_address",
		"hr_work_hours_system",
		"hr_recruitment_channel",
		"attendance_device_id",
		"hr_oa_code",
		"branch",
		"group_name",
	],
	employment_status: [
		"employment_type",
		"status",
		"date_of_joining",
		"hr_probation_months",
		"hr_probation_end",
		"scheduled_confirmation_date",
		"final_confirmation_date",
		"hr_company_tenure_start",
	],
	employment_exit: [
		"hr_leave_apply_date",
		"hr_last_working_day",
		"relieving_date",
		"hr_leave_type",
		"reason_for_leaving",
		"hr_leave_destination",
		"hr_leave_remarks",
		"new_workplace",
	],
	employment_exam: ["hr_exam_start", "hr_exam_end", "hr_exam_result", "hr_exam_remarks"],
	employment_retire: ["date_of_retirement"],
};

const forms = reactive({
	employment_basic: {},
	employment_status: {},
	employment_exit: {},
	employment_exam: {},
	employment_retire: {},
});

const positionCategoryOptions = ["管理类", "技术类", "客服类", "销售类", "职能类", "运营类", "其他"].map((v) => ({
	label: v,
	value: v,
}));
const identityOptions = ["普通成员", "部门负责人", "组织负责人"].map((v) => ({ label: v, value: v }));
const workHoursOptions = ["标准工时", "综合工时", "不定时工时"].map((v) => ({ label: v, value: v }));
const leaveTypeOptions = ["主动离职", "协商解除", "公司辞退", "合同到期", "其他"].map((v) => ({ label: v, value: v }));

const historyModal = reactive({
	visible: false,
	saving: false,
	row: null,
	form: { department: "", designation: "", from_date: "", to_date: "" },
});

const rewardModal = reactive({
	visible: false,
	saving: false,
	row: null,
	form: { record_type: "奖励", title: "", occur_date: "", remarks: "" },
});

function pick(keys) {
	const out = {};
	keys.forEach((k) => {
		out[k] = props.doc?.[k] ?? "";
	});
	return out;
}

function startEdit(section) {
	forms[section] = pick(SECTION_KEYS[section]);
}

function cancelEdit(section) {
	forms[section] = pick(SECTION_KEYS[section]);
}

async function saveSection(section, ctl) {
	try {
		const data = { ...forms[section] };
		if (section === "employment_basic") {
			const missing = [
				["employee_number", "工号"],
				["department", "部门"],
				["designation", "岗位"],
				["hr_job_title", "职务"],
				["grade", "职级"],
				["company", "合同公司"],
				["reports_to", "汇报上级"],
				["hr_work_location", "工作地点"],
			].filter(([k]) => !String(data[k] || "").trim());
			if (missing.length) {
				Message.warning(`请填写：${missing.map((x) => x[1]).join("、")}`);
				ctl.fail();
				return;
			}
		}
		if (section === "employment_status") {
			const missing = [
				["employment_type", "工作性质"],
				["status", "员工状态"],
				["date_of_joining", "入职日期"],
				["hr_probation_months", "试用期"],
			].filter(([k]) => !String(data[k] || "").trim());
			if (missing.length) {
				Message.warning(`请填写：${missing.map((x) => x[1]).join("、")}`);
				ctl.fail();
				return;
			}
		}
		const updated = await saveEmployeeSection(props.doc.name, section, data);
		Message.success("保存成功");
		emit("updated", updated);
		ctl.done(true);
	} catch (e) {
		Message.error(errMessage(e, "保存失败"));
		ctl.fail();
	}
}

const basicViewItems = computed(() => [
	{ key: "employee_number", label: "工号", value: props.doc.employee_number, required: true },
	{ key: "department", label: "部门", value: props.doc.department, required: true },
	{ key: "hr_concurrent_post", label: "兼任", value: props.doc.hr_concurrent_post },
	{ key: "hr_job_title", label: "职务", value: props.doc.hr_job_title, required: true },
	{ key: "designation", label: "岗位", value: props.doc.designation, required: true },
	{ key: "hr_position_category", label: "岗位类别", value: props.doc.hr_position_category },
	{ key: "grade", label: "职级", value: props.doc.grade, required: true },
	{ key: "hr_job_grade_level", label: "职等", value: props.doc.hr_job_grade_level },
	{ key: "company", label: "合同公司", value: props.doc.company, required: true },
	{ key: "hr_employee_identity", label: "身份", value: props.doc.hr_employee_identity },
	{ key: "reports_to", label: "汇报上级", value: props.doc.reports_to, required: true },
	{ key: "hr_work_location", label: "工作地点", value: props.doc.hr_work_location || props.doc.branch, required: true },
	{ key: "hr_work_city", label: "工作城市", value: props.doc.hr_work_city },
	{ key: "hr_work_address", label: "详细工作地址", value: props.doc.hr_work_address },
	{ key: "hr_work_hours_system", label: "工时制度", value: props.doc.hr_work_hours_system },
	{ key: "hr_recruitment_channel", label: "招聘渠道", value: props.doc.hr_recruitment_channel },
	{ key: "attendance_device_id", label: "考勤编号", value: props.doc.attendance_device_id },
	{ key: "hr_oa_code", label: "OA编码", value: props.doc.hr_oa_code },
]);

const statusViewItems = computed(() => [
	{ key: "employment_type", label: "工作性质", value: employmentTypeLabel(props.doc.employment_type), required: true },
	{ key: "status", label: "员工状态", value: statusLabel(props.doc.status), required: true },
	{ key: "date_of_joining", label: "入职日期", value: formatDate(props.doc.date_of_joining), required: true },
	{
		key: "hr_probation_months",
		label: "试用期",
		value: props.doc.hr_probation_months
			? props.doc.hr_probation_months === "无试用期"
				? "无试用期"
				: `${props.doc.hr_probation_months} 个月`
			: "",
		required: true,
	},
	{ key: "final_confirmation_date", label: "转正日期", value: formatDate(props.doc.final_confirmation_date) },
	{ key: "hr_company_tenure_start", label: "司龄开始日期", value: formatDate(props.doc.hr_company_tenure_start) },
	{ key: "company_tenure_years", label: "司龄", value: yearsLabel(props.doc.company_tenure_years) },
]);

const exitViewItems = computed(() => [
	{ key: "hr_leave_apply_date", label: "离职申请日期", value: formatDate(props.doc.hr_leave_apply_date) },
	{ key: "hr_last_working_day", label: "最后工作日", value: formatDate(props.doc.hr_last_working_day) },
	{ key: "relieving_date", label: "离职日期", value: formatDate(props.doc.relieving_date) },
	{ key: "hr_leave_type", label: "离职类型", value: props.doc.hr_leave_type },
	{ key: "reason_for_leaving", label: "离职原因", value: props.doc.reason_for_leaving },
	{ key: "hr_leave_destination", label: "离职去向", value: props.doc.hr_leave_destination },
	{ key: "hr_leave_remarks", label: "离职备注", value: props.doc.hr_leave_remarks },
]);

const examViewItems = computed(() => [
	{ key: "hr_exam_start", label: "考察期开始", value: formatDate(props.doc.hr_exam_start) },
	{ key: "hr_exam_end", label: "考察期结束", value: formatDate(props.doc.hr_exam_end) },
	{ key: "hr_exam_result", label: "考察结果", value: props.doc.hr_exam_result },
	{ key: "hr_exam_remarks", label: "考察备注", value: props.doc.hr_exam_remarks },
]);

const retireViewItems = computed(() => [
	{ key: "date_of_retirement", label: "退休日期", value: formatDate(props.doc.date_of_retirement) },
]);

function openHistoryModal(row = null) {
	historyModal.row = row;
	historyModal.form = {
		department: row?.department || "",
		designation: row?.designation || "",
		from_date: row?.from_date || "",
		to_date: row?.to_date || "",
		name: row?.name,
	};
	historyModal.visible = true;
}

async function submitHistory() {
	if (!historyModal.form.department || !historyModal.form.designation) {
		Message.warning("请填写部门和岗位");
		return false;
	}
	historyModal.saving = true;
	try {
		const updated = await saveEmployeeChildRow(props.doc.name, "internal_work_history", historyModal.form);
		Message.success("已保存任职记录");
		emit("updated", updated);
		historyModal.visible = false;
	} catch (e) {
		Message.error(errMessage(e));
		return false;
	} finally {
		historyModal.saving = false;
	}
}

function openRewardModal(row = null) {
	rewardModal.row = row;
	rewardModal.form = {
		record_type: row?.record_type || "奖励",
		title: row?.title || "",
		occur_date: row?.occur_date || "",
		remarks: row?.remarks || "",
		name: row?.name,
	};
	rewardModal.visible = true;
}

async function submitReward() {
	if (!rewardModal.form.title) {
		Message.warning("请填写事项");
		return false;
	}
	rewardModal.saving = true;
	try {
		const updated = await saveEmployeeChildRow(props.doc.name, "rewards", rewardModal.form);
		Message.success("已保存奖惩记录");
		emit("updated", updated);
		rewardModal.visible = false;
	} catch (e) {
		Message.error(errMessage(e));
		return false;
	} finally {
		rewardModal.saving = false;
	}
}

function removeChild(tableKey, row) {
	if (!row?.name || row.name === "legacy" || row.name === "current") {
		Message.warning("该记录无法删除");
		return;
	}
	Modal.confirm({
		title: "确认删除",
		content: "删除后不可恢复，确定继续吗？",
		okText: "删除",
		okButtonProps: { status: "danger" },
		async onOk() {
			const updated = await saveEmployeeChildRow(props.doc.name, tableKey, { name: row.name }, 1);
			Message.success("已删除");
			emit("updated", updated);
		},
	});
}

watch(
	() => props.doc?.name,
	() => {
		Object.keys(SECTION_KEYS).forEach((section) => {
			forms[section] = pick(SECTION_KEYS[section]);
		});
	},
	{ immediate: true }
);
</script>
