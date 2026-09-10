<template>
	<div class="arco-emp-archive-tab" v-if="doc">
		<a-spin :loading="loading" style="width: 100%">
			<div class="arco-emp-archive-stack">
				<EmployeeEditableSection
					title="离职办理"
					section-key="employment_exit"
					:can-edit="canEdit"
					:reset-token="resetToken"
					@edit="startEdit"
					@cancel="cancelEdit"
					@save="saveBasic"
				>
					<template #view>
						<EmployeePreviewGrid :items="viewItems" />
					</template>
					<template #edit>
						<a-form :model="form" layout="vertical" class="arco-emp-archive-form">
							<a-row :gutter="16">
								<a-col :span="8">
									<a-form-item label="离职申请日期">
										<a-date-picker v-model="form.hr_leave_apply_date" style="width:100%" value-format="YYYY-MM-DD" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="最后工作日">
										<a-date-picker v-model="form.hr_last_working_day" style="width:100%" value-format="YYYY-MM-DD" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="离职日期">
										<a-date-picker v-model="form.relieving_date" style="width:100%" value-format="YYYY-MM-DD" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="离职类型">
										<a-select v-model="form.hr_leave_type" allow-clear :options="leaveTypeOptions" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="离职原因">
										<a-input v-model="form.reason_for_leaving" allow-clear />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="离职去向">
										<a-input v-model="form.hr_leave_destination" allow-clear />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="新工作单位">
										<a-input v-model="form.new_workplace" allow-clear />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="辞职信日期">
										<a-date-picker v-model="form.resignation_letter_date" style="width:100%" value-format="YYYY-MM-DD" />
									</a-form-item>
								</a-col>
								<a-col :span="24">
									<a-form-item label="离职备注">
										<a-textarea v-model="form.hr_leave_remarks" :auto-size="{ minRows: 2 }" allow-clear />
									</a-form-item>
								</a-col>
							</a-row>
						</a-form>
					</template>
				</EmployeeEditableSection>
			</div>
		</a-spin>
	</div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { Message } from "@arco-design/web-vue";
import EmployeeEditableSection from "../EmployeeEditableSection.vue";
import EmployeePreviewGrid from "../EmployeePreviewGrid.vue";
import { saveEmployeeSection } from "../../../api/employeeDetail";
import { errMessage, formatDate } from "../../../utils/employeeArchive";

const props = defineProps({
	doc: { type: Object, required: true },
	loading: { type: Boolean, default: false },
	canEdit: { type: Boolean, default: false },
	resetToken: { type: [Number, String], default: 0 },
});
const emit = defineEmits(["updated"]);

const KEYS = [
	"hr_leave_apply_date",
	"hr_last_working_day",
	"relieving_date",
	"hr_leave_type",
	"reason_for_leaving",
	"hr_leave_destination",
	"hr_leave_remarks",
	"new_workplace",
	"resignation_letter_date",
];
const form = reactive({});
const leaveTypeOptions = ["主动离职", "协商解除", "公司辞退", "合同到期", "其他"].map((v) => ({ label: v, value: v }));

function pick() {
	KEYS.forEach((k) => {
		form[k] = props.doc?.[k] ?? "";
	});
}
function startEdit() { pick(); }
function cancelEdit() { pick(); }

async function saveBasic(ctl) {
	try {
		const updated = await saveEmployeeSection(props.doc.name, "employment_exit", { ...form });
		Message.success("保存成功");
		emit("updated", updated);
		ctl.done(true);
	} catch (e) {
		Message.error(errMessage(e));
		ctl.fail();
	}
}

const viewItems = computed(() => [
	{ key: "hr_leave_apply_date", label: "离职申请日期", value: formatDate(props.doc.hr_leave_apply_date) },
	{ key: "hr_last_working_day", label: "最后工作日", value: formatDate(props.doc.hr_last_working_day) },
	{ key: "relieving_date", label: "离职日期", value: formatDate(props.doc.relieving_date) },
	{ key: "hr_leave_type", label: "离职类型", value: props.doc.hr_leave_type },
	{ key: "reason_for_leaving", label: "离职原因", value: props.doc.reason_for_leaving },
	{ key: "hr_leave_destination", label: "离职去向", value: props.doc.hr_leave_destination },
	{ key: "new_workplace", label: "新工作单位", value: props.doc.new_workplace },
	{ key: "resignation_letter_date", label: "辞职信日期", value: formatDate(props.doc.resignation_letter_date) },
	{ key: "hr_leave_remarks", label: "离职备注", value: props.doc.hr_leave_remarks },
]);

watch(() => props.doc?.name, pick, { immediate: true });
</script>
