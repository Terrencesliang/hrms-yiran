<template>
	<div class="arco-emp-archive-tab" v-if="doc">
		<a-spin :loading="loading" style="width: 100%">
			<div class="arco-emp-archive-stack">
				<EmployeeEditableSection
					title="工资卡信息"
					section-key="salary_bank"
					:can-edit="canEdit"
					:reset-token="resetToken"
					@edit="() => pick('salary_bank')"
					@cancel="() => pick('salary_bank')"
					@save="(ctl) => save('salary_bank', ctl)"
				>
					<template #view>
						<EmployeePreviewGrid :items="bankItems" />
					</template>
					<template #edit>
						<a-form :model="forms.salary_bank" layout="vertical" class="arco-emp-archive-form">
							<a-row :gutter="16">
								<a-col :span="12"><a-form-item label="工资卡卡号"><a-input v-model="forms.salary_bank.bank_ac_no" /></a-form-item></a-col>
								<a-col :span="12"><a-form-item label="银行名称"><a-input v-model="forms.salary_bank.bank_name" /></a-form-item></a-col>
								<a-col :span="12"><a-form-item label="开户城市"><a-input v-model="forms.salary_bank.hr_bank_city" /></a-form-item></a-col>
								<a-col :span="12"><a-form-item label="开户行"><a-input v-model="forms.salary_bank.hr_bank_branch" /></a-form-item></a-col>
								<a-col :span="12"><a-form-item label="发放方式"><a-input v-model="forms.salary_bank.salary_mode" /></a-form-item></a-col>
							</a-row>
						</a-form>
					</template>
				</EmployeeEditableSection>

				<EmployeeEditableSection
					title="社保公积金信息"
					section-key="salary_ss"
					:can-edit="canEdit"
					:reset-token="resetToken"
					@edit="() => pick('salary_ss')"
					@cancel="() => pick('salary_ss')"
					@save="(ctl) => save('salary_ss', ctl)"
				>
					<template #view>
						<EmployeePreviewGrid :items="ssItems" />
					</template>
					<template #edit>
						<a-form :model="forms.salary_ss" layout="vertical" class="arco-emp-archive-form">
							<a-row :gutter="16">
								<a-col :span="8">
									<a-form-item label="社保参保状态">
										<a-select v-model="forms.salary_ss.hr_ss_status" allow-clear :options="ssStatus" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="参保城市" :required="forms.salary_ss.hr_ss_status === '已参保'">
										<a-input v-model="forms.salary_ss.hr_social_security_city" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="社保开始日期" :required="forms.salary_ss.hr_ss_status === '已参保'">
										<a-date-picker v-model="forms.salary_ss.hr_ss_start_date" style="width:100%" value-format="YYYY-MM-DD" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="社保基数" :required="forms.salary_ss.hr_ss_status === '已参保'">
										<a-input-number v-model="forms.salary_ss.hr_social_security_base" style="width:100%" :min="0" />
									</a-form-item>
								</a-col>
								<a-col :span="8"><a-form-item label="社保账号"><a-input v-model="forms.salary_ss.hr_social_security_no" /></a-form-item></a-col>
								<a-col :span="8">
									<a-form-item label="公积金缴纳状态">
										<a-select v-model="forms.salary_ss.hr_hf_status" allow-clear :options="hfStatus" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="公积金缴纳城市" :required="forms.salary_ss.hr_hf_status === '已缴纳'">
										<a-input v-model="forms.salary_ss.hr_hf_city" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="公积金开始日期" :required="forms.salary_ss.hr_hf_status === '已缴纳'">
										<a-date-picker v-model="forms.salary_ss.hr_hf_start_date" style="width:100%" value-format="YYYY-MM-DD" />
									</a-form-item>
								</a-col>
								<a-col :span="8">
									<a-form-item label="公积金基数" :required="forms.salary_ss.hr_hf_status === '已缴纳'">
										<a-input-number v-model="forms.salary_ss.hr_housing_fund_base" style="width:100%" :min="0" />
									</a-form-item>
								</a-col>
								<a-col :span="8"><a-form-item label="公积金账号"><a-input v-model="forms.salary_ss.hr_housing_fund_no" /></a-form-item></a-col>
							</a-row>
						</a-form>
					</template>
				</EmployeeEditableSection>

				<EmployeeEditableSection
					title="工资信息"
					section-key="salary_pay"
					:can-edit="canEdit"
					:reset-token="resetToken"
					@edit="() => pick('salary_pay')"
					@cancel="() => pick('salary_pay')"
					@save="(ctl) => save('salary_pay', ctl)"
				>
					<template #view>
						<EmployeePreviewGrid :items="payItems" />
					</template>
					<template #edit>
						<a-form :model="forms.salary_pay" layout="vertical" class="arco-emp-archive-form">
							<a-row :gutter="16">
								<a-col :span="8"><a-form-item label="薪资类型"><a-input v-model="forms.salary_pay.hr_salary_type" /></a-form-item></a-col>
								<a-col :span="8"><a-form-item label="基本工资"><a-input-number v-model="forms.salary_pay.hr_base_salary" style="width:100%" :min="0" /></a-form-item></a-col>
								<a-col :span="8"><a-form-item label="岗位工资"><a-input-number v-model="forms.salary_pay.hr_position_salary" style="width:100%" :min="0" /></a-form-item></a-col>
								<a-col :span="8"><a-form-item label="绩效工资"><a-input-number v-model="forms.salary_pay.hr_performance_salary" style="width:100%" :min="0" /></a-form-item></a-col>
								<a-col :span="8"><a-form-item label="津贴/补贴"><a-input-number v-model="forms.salary_pay.hr_allowance" style="width:100%" :min="0" /></a-form-item></a-col>
								<a-col :span="8"><a-form-item label="薪资生效日期"><a-date-picker v-model="forms.salary_pay.hr_salary_effective_date" style="width:100%" value-format="YYYY-MM-DD" /></a-form-item></a-col>
								<a-col :span="24"><a-form-item label="薪资备注"><a-textarea v-model="forms.salary_pay.hr_salary_remarks" :auto-size="{minRows:2}" /></a-form-item></a-col>
							</a-row>
						</a-form>
					</template>
				</EmployeeEditableSection>

				<EmployeeRecordList
						title="工资调整记录"
						section-key="salary_history"
						:records="doc.salary_history || []"
						:can-edit="false"
						empty-text="暂无工资调整记录"
					>
						<template #item="{ row }">
							<div class="arco-emp-record-title">{{ blank(formatDate(row.effective_date)) }} · {{ blank(row.salary_type) }}</div>
							<div class="arco-emp-record-sub">
								基本 {{ blank(row.base_salary) }} · 岗位 {{ blank(row.position_salary) }} · 绩效 {{ blank(row.performance_salary) }}
							</div>
						</template>
					</EmployeeRecordList>

				<EmployeeRecordList
						title="社保公积金记录"
						section-key="ss_history"
						:records="doc.ss_history || []"
						:can-edit="false"
						empty-text="暂无社保公积金记录"
					>
						<template #item="{ row }">
							<div class="arco-emp-record-title">{{ blank(formatDate(row.record_date)) }}</div>
							<div class="arco-emp-record-sub">
								社保 {{ blank(row.ss_status) }} / {{ blank(row.ss_city) }} · 公积金 {{ blank(row.hf_status) }} / {{ blank(row.hf_city) }}
							</div>
						</template>
					</EmployeeRecordList>
			</div>
		</a-spin>
	</div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { Message } from "@arco-design/web-vue";
import EmployeeEditableSection from "../EmployeeEditableSection.vue";
import EmployeePreviewGrid from "../EmployeePreviewGrid.vue";
import EmployeeRecordList from "../EmployeeRecordList.vue";
import { saveEmployeeSection } from "../../../api/employeeDetail";
import { blank, errMessage, formatDate } from "../../../utils/employeeArchive";

const props = defineProps({
	doc: { type: Object, required: true },
	loading: { type: Boolean, default: false },
	canEdit: { type: Boolean, default: false },
	resetToken: { type: Number, default: 0 },
});
const emit = defineEmits(["updated"]);

const MAP = {
	salary_bank: ["bank_ac_no", "bank_name", "hr_bank_city", "hr_bank_branch", "salary_mode", "iban"],
	salary_ss: [
		"hr_ss_status", "hr_social_security_city", "hr_ss_start_date", "hr_social_security_base", "hr_social_security_no",
		"hr_hf_status", "hr_hf_city", "hr_hf_start_date", "hr_housing_fund_base", "hr_housing_fund_no",
	],
	salary_pay: [
		"hr_salary_type", "hr_base_salary", "hr_position_salary", "hr_performance_salary", "hr_allowance",
		"hr_salary_effective_date", "hr_salary_remarks", "ctc", "salary_currency",
	],
};

const forms = reactive({ salary_bank: {}, salary_ss: {}, salary_pay: {} });
const ssStatus = ["未参保", "已参保", "停保"].map((v) => ({ label: v, value: v }));
const hfStatus = ["未缴纳", "已缴纳", "停缴"].map((v) => ({ label: v, value: v }));

function pick(section) {
	const out = {};
	MAP[section].forEach((k) => { out[k] = props.doc?.[k] ?? ""; });
	if (section === "salary_bank" && props.doc?.can_view_sensitive && props.doc?.bank_ac_no_raw) {
		out.bank_ac_no = props.doc.bank_ac_no_raw;
	}
	forms[section] = out;
}

async function save(section, ctl) {
	try {
		const updated = await saveEmployeeSection(props.doc.name, section, { ...forms[section] });
		Message.success("保存成功");
		emit("updated", updated);
		ctl.done(true);
	} catch (e) {
		Message.error(errMessage(e));
		ctl.fail();
	}
}

const bankItems = computed(() => [
	{ key: "bank_ac_no", label: "工资卡卡号", value: props.doc.bank_ac_no },
	{ key: "bank_name", label: "银行名称", value: props.doc.bank_name },
	{ key: "hr_bank_city", label: "开户城市", value: props.doc.hr_bank_city },
	{ key: "hr_bank_branch", label: "开户行", value: props.doc.hr_bank_branch },
]);

const ssItems = computed(() => [
	{ key: "hr_ss_status", label: "社保参保状态", value: props.doc.hr_ss_status },
	{ key: "hr_social_security_city", label: "参保城市", value: props.doc.hr_social_security_city },
	{ key: "hr_ss_start_date", label: "社保开始日期", value: formatDate(props.doc.hr_ss_start_date) },
	{ key: "hr_social_security_base", label: "社保基数", value: props.doc.hr_social_security_base },
	{ key: "hr_social_security_no", label: "社保账号", value: props.doc.hr_social_security_no },
	{ key: "hr_hf_status", label: "公积金缴纳状态", value: props.doc.hr_hf_status },
	{ key: "hr_hf_city", label: "公积金缴纳城市", value: props.doc.hr_hf_city },
	{ key: "hr_hf_start_date", label: "公积金开始日期", value: formatDate(props.doc.hr_hf_start_date) },
	{ key: "hr_housing_fund_base", label: "公积金基数", value: props.doc.hr_housing_fund_base },
	{ key: "hr_housing_fund_no", label: "公积金账号", value: props.doc.hr_housing_fund_no },
]);

const payItems = computed(() => [
	{ key: "hr_salary_type", label: "薪资类型", value: props.doc.hr_salary_type },
	{ key: "hr_base_salary", label: "基本工资", value: props.doc.hr_base_salary },
	{ key: "hr_position_salary", label: "岗位工资", value: props.doc.hr_position_salary },
	{ key: "hr_performance_salary", label: "绩效工资", value: props.doc.hr_performance_salary },
	{ key: "hr_allowance", label: "津贴/补贴", value: props.doc.hr_allowance },
	{ key: "hr_salary_effective_date", label: "薪资生效日期", value: formatDate(props.doc.hr_salary_effective_date) },
	{ key: "hr_salary_remarks", label: "薪资备注", value: props.doc.hr_salary_remarks },
]);

watch(
	() => props.doc?.name,
	() => {
		Object.keys(MAP).forEach(pick);
	},
	{ immediate: true }
);
</script>
