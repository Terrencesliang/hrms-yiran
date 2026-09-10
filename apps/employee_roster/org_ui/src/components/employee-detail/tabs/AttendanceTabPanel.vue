<template>
	<div class="arco-emp-archive-tab" v-if="doc">
		<a-spin :loading="loading" style="width: 100%">
			<div class="arco-emp-archive-stack">
				<EmployeeEditableSection
					title="考勤设置"
					section-key="attendance_settings"
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
									<a-form-item label="考勤编号">
										<a-input v-model="form.attendance_device_id" allow-clear />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="假期列表">
										<a-input v-model="form.holiday_list" allow-clear />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="请假审批人">
										<a-input v-model="form.leave_approver" allow-clear />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="报销审批人">
										<a-input v-model="form.expense_approver" allow-clear />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="班次申请审批人">
										<a-input v-model="form.shift_request_approver" allow-clear />
									</a-form-item>
								</a-col>
							</a-row>
						</a-form>
					</template>
				</EmployeeEditableSection>

				<EmployeeCollapsibleCard title="本月考勤摘要" section-key="attendance_summary">
					<div class="arco-emp-attendance-summary">
						<div class="arco-emp-attendance-summary-item">
							<span>出勤天数</span>
							<strong>{{ blank(doc.attendance_month ?? overviewAttendance.attendance_days) }}</strong>
						</div>
						<div class="arco-emp-attendance-summary-item">
							<span>请假小时</span>
							<strong>{{ blank(overviewAttendance.leave_hours) }}</strong>
						</div>
						<div class="arco-emp-attendance-summary-item">
							<span>迟到次数</span>
							<strong>{{ blank(overviewAttendance.late_count) }}</strong>
						</div>
						<div class="arco-emp-attendance-summary-item">
							<span>加班小时</span>
							<strong>{{ blank(overviewAttendance.overtime_hours) }}</strong>
						</div>
					</div>
					<div class="arco-emp-attendance-summary-actions">
						<a-button type="outline" size="mini" @click="openAttendanceList">查看考勤明细</a-button>
					</div>
				</EmployeeCollapsibleCard>
			</div>
		</a-spin>
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { Message } from "@arco-design/web-vue";
import EmployeeCollapsibleCard from "../EmployeeCollapsibleCard.vue";
import EmployeeEditableSection from "../EmployeeEditableSection.vue";
import EmployeePreviewGrid from "../EmployeePreviewGrid.vue";
import { getEmployeeOverview, saveEmployeeSection } from "../../../api/employeeDetail";
import { blank, errMessage } from "../../../utils/employeeArchive";

const props = defineProps({
	doc: { type: Object, required: true },
	loading: { type: Boolean, default: false },
	canEdit: { type: Boolean, default: false },
	resetToken: { type: [Number, String], default: 0 },
});
const emit = defineEmits(["updated"]);

const KEYS = [
	"attendance_device_id",
	"holiday_list",
	"leave_approver",
	"expense_approver",
	"shift_request_approver",
];
const form = reactive({});
const overviewAttendance = ref({});

function pick() {
	KEYS.forEach((k) => {
		form[k] = props.doc?.[k] ?? "";
	});
}

function startEdit() {
	pick();
}
function cancelEdit() {
	pick();
}

async function saveBasic(ctl) {
	try {
		const updated = await saveEmployeeSection(props.doc.name, "attendance_settings", { ...form });
		Message.success("保存成功");
		emit("updated", updated);
		ctl.done(true);
	} catch (e) {
		Message.error(errMessage(e));
		ctl.fail();
	}
}

const viewItems = computed(() => [
	{ key: "attendance_device_id", label: "考勤编号", value: props.doc.attendance_device_id },
	{ key: "holiday_list", label: "假期列表", value: props.doc.holiday_list },
	{ key: "leave_approver", label: "请假审批人", value: props.doc.leave_approver },
	{ key: "expense_approver", label: "报销审批人", value: props.doc.expense_approver },
	{ key: "shift_request_approver", label: "班次申请审批人", value: props.doc.shift_request_approver },
]);

function openAttendanceList() {
	if (!props.doc?.name || !window.frappe?.set_route) return;
	window.frappe.route_options = { employee: props.doc.name };
	window.frappe.set_route("List", "Attendance");
}

async function loadAttendance() {
	if (!props.doc?.name) return;
	try {
		const data = await getEmployeeOverview(props.doc.name);
		overviewAttendance.value = data?.attendance || {};
	} catch {
		overviewAttendance.value = {};
	}
}

watch(() => props.doc?.name, () => { pick(); loadAttendance(); }, { immediate: true });
</script>
