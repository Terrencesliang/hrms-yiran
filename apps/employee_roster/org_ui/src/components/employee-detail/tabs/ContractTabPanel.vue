<template>
	<div class="arco-emp-archive-tab" v-if="doc">
		<a-spin :loading="loading" style="width: 100%">
			<div class="arco-emp-archive-stack">
				<EmployeeRecordList
						title="合同记录"
						section-key="contracts"
						:records="doc.contracts || []"
						:can-edit="canEdit"
						empty-text="暂无合同记录"
						@add="openModal()"
						@edit="openModal"
						@remove="removeRow"
					>
						<template #item="{ row }">
							<div class="arco-emp-record-title">
								{{ blank(row.contract_type) }}
								<a-tag size="small" style="margin-left: 8px" :color="statusColor(row)">
									{{ blank(row.computed_status || row.contract_status) }}
								</a-tag>
							</div>
							<div class="arco-emp-record-sub">
								{{ blank(row.contract_no) }} · {{ blank(row.contract_company) }} ·
								{{ dateRange(row.start_date, row.end_date) }}
							</div>
							<div v-if="row.attachment" class="arco-emp-record-sub">
								<a :href="row.attachment" target="_blank" rel="noopener">查看附件</a>
							</div>
						</template>
					</EmployeeRecordList>
			</div>
		</a-spin>

		<a-modal
			v-model:visible="modal.visible"
			:title="modal.form.name && modal.form.name !== 'current' ? '编辑合同' : '新增合同'"
			:ok-loading="modal.saving"
			unmount-on-close
			width="640px"
			@ok="submit"
		>
			<a-form :model="modal.form" layout="vertical">
				<a-row :gutter="16">
					<a-col :span="12">
						<a-form-item label="合同类型" required>
							<a-select v-model="modal.form.contract_type" :options="CONTRACT_TYPE_OPTIONS" />
						</a-form-item>
					</a-col>
					<a-col :span="12">
						<a-form-item label="合同编号" required>
							<a-input v-model="modal.form.contract_no" />
						</a-form-item>
					</a-col>
					<a-col :span="12">
						<a-form-item label="合同公司" required>
							<a-input v-model="modal.form.contract_company" />
						</a-form-item>
					</a-col>
					<a-col :span="12">
						<a-form-item label="签订日期" required>
							<a-date-picker v-model="modal.form.signed_date" style="width: 100%" value-format="YYYY-MM-DD" />
						</a-form-item>
					</a-col>
					<a-col :span="12">
						<a-form-item label="合同开始日期" required>
							<a-date-picker v-model="modal.form.start_date" style="width: 100%" value-format="YYYY-MM-DD" />
						</a-form-item>
					</a-col>
					<a-col :span="12">
						<a-form-item
							label="合同结束日期"
							:required="modal.form.contract_type === '固定期限劳动合同'"
						>
							<a-date-picker v-model="modal.form.end_date" style="width: 100%" value-format="YYYY-MM-DD" />
						</a-form-item>
					</a-col>
					<a-col :span="12">
						<a-form-item label="试用期">
							<a-input v-model="modal.form.probation_months" />
						</a-form-item>
					</a-col>
					<a-col :span="12">
						<a-form-item label="合同状态">
							<a-select
								v-model="modal.form.contract_status"
								allow-clear
								:options="statusOptions"
							/>
						</a-form-item>
					</a-col>
					<a-col :span="12">
						<a-form-item label="续签状态">
							<a-select
								v-model="modal.form.renewal_status"
								allow-clear
								:options="renewalOptions"
							/>
						</a-form-item>
					</a-col>
					<a-col :span="12">
						<a-form-item label="合同附件">
							<a-input v-model="modal.form.attachment" placeholder="文件 URL 或上传后填入" />
						</a-form-item>
					</a-col>
					<a-col :span="24">
						<a-form-item label="备注">
							<a-textarea v-model="modal.form.remarks" :auto-size="{ minRows: 2 }" />
						</a-form-item>
					</a-col>
				</a-row>
			</a-form>
		</a-modal>
	</div>
</template>

<script setup>
import { reactive } from "vue";
import { Message, Modal } from "@arco-design/web-vue";
import EmployeeRecordList from "../EmployeeRecordList.vue";
import { saveEmployeeChildRow } from "../../../api/employeeDetail";
import { blank, CONTRACT_TYPE_OPTIONS, dateRange, errMessage } from "../../../utils/employeeArchive";

const props = defineProps({
	doc: { type: Object, required: true },
	loading: { type: Boolean, default: false },
	canEdit: { type: Boolean, default: false },
	resetToken: { type: Number, default: 0 },
});
const emit = defineEmits(["updated"]);

const statusOptions = ["未签订", "履行中", "已到期", "已解除", "已终止"].map((v) => ({ label: v, value: v }));
const renewalOptions = ["未续签", "已续签", "不续签"].map((v) => ({ label: v, value: v }));

const modal = reactive({
	visible: false,
	saving: false,
	form: {},
});

function statusColor(row) {
	const s = row.computed_status || row.contract_status || "";
	if (s.includes("履行")) return "green";
	if (s.includes("到期") || s.includes("终止") || s.includes("解除")) return "orangered";
	return "gray";
}

function openModal(row = null) {
	const fromMain = row?._from_main || row?.name === "current";
	modal.form = {
		name: fromMain ? undefined : row?.name,
		contract_type: row?.contract_type || "",
		contract_no: row?.contract_no || "",
		contract_company: row?.contract_company || props.doc.company || "",
		start_date: row?.start_date || "",
		end_date: row?.end_date || "",
		signed_date: row?.signed_date || "",
		probation_months: row?.probation_months || "",
		contract_status: row?.contract_status || "",
		renewal_status: row?.renewal_status || "",
		attachment: row?.attachment || "",
		remarks: row?.remarks || "",
	};
	modal.visible = true;
}

async function submit() {
	modal.saving = true;
	try {
		const updated = await saveEmployeeChildRow(props.doc.name, "contracts", { ...modal.form });
		Message.success("合同已保存");
		emit("updated", updated);
		modal.visible = false;
	} catch (e) {
		Message.error(errMessage(e));
		return false;
	} finally {
		modal.saving = false;
	}
}

function removeRow(row) {
	if (!row?.name || row.name === "current" || row._from_main) {
		Message.warning("请先将主表合同迁移为正式记录后再删除");
		return;
	}
	Modal.confirm({
		title: "确认删除合同",
		content: "删除后不可恢复，确定继续吗？",
		okText: "删除",
		okButtonProps: { status: "danger" },
		async onOk() {
			const updated = await saveEmployeeChildRow(props.doc.name, "contracts", { name: row.name }, 1);
			Message.success("已删除");
			emit("updated", updated);
		},
	});
}
</script>
