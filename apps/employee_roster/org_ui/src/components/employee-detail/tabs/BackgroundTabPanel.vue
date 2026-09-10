<template>
	<div class="arco-emp-archive-tab" v-if="doc">
		<a-spin :loading="loading" style="width: 100%">
			<div class="arco-emp-archive-stack">
				<EmployeeEditableSection
					title="背景调查"
					section-key="background_basic"
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
									<a-form-item label="背调状态">
										<a-select v-model="form.hr_background_status" allow-clear :options="statusOptions" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="背调机构">
										<a-input v-model="form.hr_background_agency" allow-clear />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="背调完成日期">
										<a-date-picker v-model="form.hr_background_date" style="width:100%" value-format="YYYY-MM-DD" />
									</a-form-item>
								</a-col>
								<a-col :span="24">
									<a-form-item label="背调报告">
										<a-input v-model="form.hr_background_report" allow-clear placeholder="文件链接或说明" />
									</a-form-item>
								</a-col>
								<a-col :span="24">
									<a-form-item label="背调备注">
										<a-textarea v-model="form.hr_background_remarks" :auto-size="{ minRows: 3 }" allow-clear />
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
	"hr_background_status",
	"hr_background_agency",
	"hr_background_date",
	"hr_background_report",
	"hr_background_remarks",
];
const form = reactive({});
const statusOptions = ["未开始", "进行中", "已完成", "异常", "免背调"].map((v) => ({ label: v, value: v }));

function pick() {
	KEYS.forEach((k) => {
		form[k] = props.doc?.[k] ?? "";
	});
}
function startEdit() { pick(); }
function cancelEdit() { pick(); }

async function saveBasic(ctl) {
	try {
		const updated = await saveEmployeeSection(props.doc.name, "background_basic", { ...form });
		Message.success("保存成功");
		emit("updated", updated);
		ctl.done(true);
	} catch (e) {
		Message.error(errMessage(e));
		ctl.fail();
	}
}

const viewItems = computed(() => [
	{ key: "hr_background_status", label: "背调状态", value: props.doc.hr_background_status },
	{ key: "hr_background_agency", label: "背调机构", value: props.doc.hr_background_agency },
	{ key: "hr_background_date", label: "背调完成日期", value: formatDate(props.doc.hr_background_date) },
	{ key: "hr_background_report", label: "背调报告", value: props.doc.hr_background_report },
	{ key: "hr_background_remarks", label: "背调备注", value: props.doc.hr_background_remarks },
]);

watch(() => props.doc?.name, pick, { immediate: true });
</script>
