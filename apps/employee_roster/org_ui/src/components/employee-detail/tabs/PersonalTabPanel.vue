<template>
	<div class="arco-emp-archive-tab" v-if="doc">
		<a-spin :loading="loading" style="width: 100%">
			<div class="arco-emp-archive-stack">
				<EmployeeEditableSection
					title="基本信息"
					section-key="personal_basic"
					:can-edit="canEdit"
					:reset-token="resetToken"
					@edit="startEdit"
					@cancel="cancelEdit"
					@save="saveBasic"
				>
					<template #view>
						<EmployeePreviewGrid :items="basicViewItems" />
					</template>
					<template #edit>
						<a-form :model="form" layout="vertical" class="arco-emp-archive-form">
							<div class="arco-emp-archive-form-group">
								<div class="arco-emp-archive-form-group-title">身份信息</div>
								<a-row :gutter="[16, 4]">
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="姓名" required>
											<a-input v-model="form.employee_name" placeholder="请输入姓名" allow-clear />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="曾用名">
											<a-input v-model="form.hr_former_name" placeholder="如无曾用名可留空" allow-clear />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="国家/地区" required>
											<a-input v-model="form.hr_country_region" placeholder="中国" allow-clear />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="证件类型" required>
											<a-select v-model="form.hr_id_type" :options="ID_TYPE_OPTIONS" placeholder="请选择" />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="证件号码" required>
											<a-input
												v-model="form.hr_id_number"
												:max-length="form.hr_id_type === '身份证' ? 18 : 64"
												:placeholder="form.hr_id_type === '身份证' ? '18 位身份证号码' : '请输入证件号码'"
												allow-clear
												@blur="onIdBlur"
											/>
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="证件有效期">
											<a-date-picker
												v-model="form.hr_id_valid_until"
												style="width:100%"
												value-format="YYYY-MM-DD"
												placeholder="请选择"
											/>
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="性别" required>
											<a-select v-model="form.gender" :options="genderSelectOptions" placeholder="请选择" />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="出生日期" required>
											<a-date-picker
												v-model="form.date_of_birth"
												style="width:100%"
												value-format="YYYY-MM-DD"
												placeholder="请选择"
											/>
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="生日 / 年龄">
											<a-input :model-value="birthdayAgeLabel" disabled />
										</a-form-item>
									</a-col>
								</a-row>
							</div>

							<div class="arco-emp-archive-form-group">
								<div class="arco-emp-archive-form-group-title">家庭与户籍</div>
								<a-row :gutter="[16, 4]">
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="婚姻状况">
											<a-select v-model="form.marital_status" allow-clear :options="maritalOptions" placeholder="请选择" />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="是否已育">
											<a-select v-model="form.hr_has_children" allow-clear :options="yesNo" placeholder="请选择" />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="民族">
											<a-input v-model="form.hr_ethnicity" placeholder="如：汉族" allow-clear />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="政治面貌">
											<a-select v-model="form.hr_political_status" allow-clear :options="politicalOptions" placeholder="请选择" />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="籍贯">
											<a-input v-model="form.hr_native_place" placeholder="省 / 市" allow-clear />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="户籍城市">
											<a-input v-model="form.hr_household_city" placeholder="请输入户籍城市" allow-clear />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="户口性质">
											<a-select v-model="form.hr_household_type" allow-clear :options="householdOptions" placeholder="请选择" />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="社保户籍">
											<a-input v-model="form.hr_social_security_household" placeholder="请输入社保户籍" allow-clear />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="24" :md="16">
										<a-form-item label="户籍地址">
											<a-textarea
												v-model="form.hr_household_address"
												:auto-size="{ minRows: 2, maxRows: 4 }"
												placeholder="请输入详细户籍地址"
												allow-clear
											/>
										</a-form-item>
									</a-col>
								</a-row>
							</div>

							<div class="arco-emp-archive-form-group">
								<div class="arco-emp-archive-form-group-title">工作与身体信息</div>
								<a-row :gutter="[16, 4]">
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="参加工作时间">
											<a-date-picker
												v-model="form.hr_work_start_date"
												style="width:100%"
												value-format="YYYY-MM-DD"
												placeholder="请选择"
											/>
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="工龄">
											<a-input :model-value="yearsLabel(doc.total_work_years)" disabled />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="身高 (cm)">
											<a-input v-model="form.hr_height" placeholder="如：170" allow-clear />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="体重 (kg)">
											<a-input v-model="form.hr_weight" placeholder="如：60" allow-clear />
										</a-form-item>
									</a-col>
									<a-col :xs="24" :sm="12" :md="8">
										<a-form-item label="血型">
											<a-input v-model="form.blood_group" placeholder="如：A / B / O / AB" allow-clear />
										</a-form-item>
									</a-col>
									<a-col :xs="24">
										<a-form-item label="健康状况">
											<a-textarea
												v-model="form.health_details"
												:auto-size="{ minRows: 2, maxRows: 4 }"
												placeholder="可填写健康说明，无则留空"
												allow-clear
											/>
										</a-form-item>
									</a-col>
								</a-row>
							</div>
						</a-form>
					</template>
				</EmployeeEditableSection>

				<EmployeeRecordList
					v-for="block in recordBlocks"
					:key="block.key"
					:title="block.title"
					:section-key="block.key"
					:records="doc[block.key] || []"
					:can-edit="canEdit"
					:empty-text="block.empty"
					@add="openRecord(block.key)"
					@edit="(row) => openRecord(block.key, row)"
					@remove="(row) => removeRecord(block.key, row)"
				>
					<template #item="{ row }">
						<div class="arco-emp-record-title">{{ block.titleOf(row) }}</div>
						<div class="arco-emp-record-sub">{{ block.subOf(row) }}</div>
					</template>
				</EmployeeRecordList>
			</div>
		</a-spin>

		<a-modal
			v-model:visible="modal.visible"
			:title="modal.title"
			:ok-loading="modal.saving"
			unmount-on-close
			width="560px"
			@ok="submitRecord"
		>
			<a-form :model="modal.form" layout="vertical">
				<template v-if="modal.key === 'education'">
					<a-form-item label="学校/院校" required><a-input v-model="modal.form.school_univ" /></a-form-item>
					<a-form-item label="学历/资格"><a-input v-model="modal.form.qualification" /></a-form-item>
					<a-form-item label="学历层次"><a-input v-model="modal.form.level" /></a-form-item>
					<a-form-item label="专业"><a-input v-model="modal.form.maj_opt_subj" /></a-form-item>
					<a-form-item label="毕业年份"><a-input-number v-model="modal.form.year_of_passing" style="width:100%" /></a-form-item>
				</template>
				<template v-else-if="modal.key === 'external_work_history'">
					<a-form-item label="公司名称" required><a-input v-model="modal.form.company_name" /></a-form-item>
					<a-form-item label="岗位"><a-input v-model="modal.form.designation" /></a-form-item>
					<a-form-item label="工作年限"><a-input v-model="modal.form.total_experience" /></a-form-item>
				</template>
				<template v-else-if="modal.key === 'languages'">
					<a-form-item label="语言" required><a-input v-model="modal.form.language" /></a-form-item>
					<a-form-item label="听"><a-input v-model="modal.form.listening" /></a-form-item>
					<a-form-item label="说"><a-input v-model="modal.form.speaking" /></a-form-item>
					<a-form-item label="读"><a-input v-model="modal.form.reading" /></a-form-item>
					<a-form-item label="写"><a-input v-model="modal.form.writing" /></a-form-item>
				</template>
				<template v-else-if="modal.key === 'skills'">
					<a-form-item label="技能" required><a-input v-model="modal.form.skill_name" /></a-form-item>
					<a-form-item label="熟练度"><a-input v-model="modal.form.level" /></a-form-item>
					<a-form-item label="年限"><a-input-number v-model="modal.form.years" style="width:100%" /></a-form-item>
				</template>
				<template v-else-if="modal.key === 'titles'">
					<a-form-item label="职称" required><a-input v-model="modal.form.title_name" /></a-form-item>
					<a-form-item label="级别"><a-input v-model="modal.form.level" /></a-form-item>
					<a-form-item label="获得日期"><a-date-picker v-model="modal.form.issue_date" style="width:100%" value-format="YYYY-MM-DD" /></a-form-item>
					<a-form-item label="发证单位"><a-input v-model="modal.form.issuer" /></a-form-item>
				</template>
				<template v-else-if="modal.key === 'certificates'">
					<a-form-item label="证书名称" required><a-input v-model="modal.form.certificate_name" /></a-form-item>
					<a-form-item label="证书编号"><a-input v-model="modal.form.certificate_no" /></a-form-item>
					<a-form-item label="发证日期"><a-date-picker v-model="modal.form.issue_date" style="width:100%" value-format="YYYY-MM-DD" /></a-form-item>
					<a-form-item label="有效期至"><a-date-picker v-model="modal.form.expire_date" style="width:100%" value-format="YYYY-MM-DD" /></a-form-item>
				</template>
				<template v-else-if="modal.key === 'trainings'">
					<a-form-item label="培训名称" required><a-input v-model="modal.form.training_name" /></a-form-item>
					<a-form-item label="主办方"><a-input v-model="modal.form.organizer" /></a-form-item>
					<a-form-item label="开始日期"><a-date-picker v-model="modal.form.start_date" style="width:100%" value-format="YYYY-MM-DD" /></a-form-item>
					<a-form-item label="结束日期"><a-date-picker v-model="modal.form.end_date" style="width:100%" value-format="YYYY-MM-DD" /></a-form-item>
					<a-form-item label="结果"><a-input v-model="modal.form.result" /></a-form-item>
				</template>
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
	errMessage,
	formatDate,
	genderLabel,
	ID_TYPE_OPTIONS,
	validateChineseIdNumber,
	yearsLabel,
} from "../../../utils/employeeArchive";

const props = defineProps({
	doc: { type: Object, required: true },
	loading: { type: Boolean, default: false },
	canEdit: { type: Boolean, default: false },
	resetToken: { type: Number, default: 0 },
});
const emit = defineEmits(["updated"]);

const KEYS = [
	"employee_name", "hr_former_name", "hr_id_type", "hr_id_number", "hr_id_valid_until",
	"gender", "date_of_birth", "marital_status", "hr_has_children", "hr_country_region", "hr_ethnicity",
	"hr_political_status", "hr_native_place", "hr_household_city", "hr_household_type", "hr_household_address",
	"hr_social_security_household", "hr_work_start_date", "hr_height", "hr_weight", "health_details", "blood_group",
];

const form = reactive({});
const yesNo = [{ label: "是", value: "是" }, { label: "否", value: "否" }];
const maritalOptions = ["已婚", "未婚", "离异", "丧偶"].map((v) => ({ label: v, value: v }));
const politicalOptions = ["群众", "共青团员", "中共党员", "民主党派", "其他"].map((v) => ({ label: v, value: v }));
const householdOptions = ["本地城镇", "本地农村", "外地城镇", "外地农村", "其他"].map((v) => ({ label: v, value: v }));
const genderSelectOptions = [
	{ label: "男", value: "男" },
	{ label: "女", value: "女" },
];

const modal = reactive({ visible: false, saving: false, key: "", title: "", form: {} });

const birthdayAgeLabel = computed(() => {
	const birthday = props.doc?.birthday || "-";
	const age = props.doc?.age != null ? `${props.doc.age} 岁` : "-";
	return `${birthday} ／ ${age}`;
});

function pick() {
	KEYS.forEach((k) => {
		form[k] = props.doc?.[k] ?? "";
	});
	// 别名并入曾用名（只保留曾用名）
	const former = String(form.hr_former_name || "").trim();
	const alias = String(props.doc?.hr_alias || "").trim();
	if (!former && alias) {
		form.hr_former_name = alias;
	}
	if (!String(form.hr_country_region || "").trim()) {
		form.hr_country_region = "中国";
	}
	if (props.doc?.can_view_sensitive && props.doc?.hr_id_number_raw) {
		form.hr_id_number = props.doc.hr_id_number_raw;
	}
}

function startEdit() { pick(); }
function cancelEdit() { pick(); }

function onIdBlur() {
	if (String(form.hr_id_type || "") !== "身份证") return;
	const result = validateChineseIdNumber(form.hr_id_number, {
		dateOfBirth: form.date_of_birth,
	});
	if (!result.ok) return;
	form.hr_id_number = result.normalized;
	if (!String(form.date_of_birth || "").trim() && result.birth) {
		form.date_of_birth = result.birth;
	}
	if (!String(form.gender || "").trim() && result.gender) {
		form.gender = result.gender;
	}
}

async function saveBasic(ctl) {
	try {
		const missing = [
			["employee_name", "姓名"],
			["hr_id_type", "证件类型"],
			["hr_id_number", "证件号码"],
			["gender", "性别"],
			["date_of_birth", "出生日期"],
			["hr_country_region", "国家/地区"],
		].filter(([k]) => !String(form[k] || "").trim());
		if (missing.length) {
			Message.warning(`请填写：${missing.map((x) => x[1]).join("、")}`);
			ctl.fail();
			return;
		}
		const today = new Date().toISOString().slice(0, 10);
		if (String(form.date_of_birth || "") > today) {
			Message.warning("出生日期不能晚于今天");
			ctl.fail();
			return;
		}
		if (String(form.hr_id_type || "") === "身份证") {
			const result = validateChineseIdNumber(form.hr_id_number, {
				today,
				dateOfBirth: form.date_of_birth,
			});
			if (!result.ok) {
				Message.warning(result.message);
				ctl.fail();
				return;
			}
			form.hr_id_number = result.normalized;
		}
		const payload = { ...form, hr_alias: "" };
		const updated = await saveEmployeeSection(props.doc.name, "personal_basic", payload);
		Message.success("保存成功");
		emit("updated", updated);
		ctl.done(true);
	} catch (e) {
		Message.error(errMessage(e));
		ctl.fail();
	}
}

const basicViewItems = computed(() => [
	{ key: "employee_name", label: "姓名", value: props.doc.employee_name, required: true },
	{
		key: "hr_former_name",
		label: "曾用名",
		value: props.doc.hr_former_name || props.doc.hr_alias,
	},
	{ key: "hr_id_type", label: "证件类型", value: props.doc.hr_id_type, required: true },
	{ key: "hr_id_number", label: "证件号码", value: props.doc.hr_id_number, required: true },
	{ key: "hr_id_valid_until", label: "证件有效期", value: formatDate(props.doc.hr_id_valid_until) },
	{ key: "gender", label: "性别", value: genderLabel(props.doc.gender), required: true },
	{ key: "date_of_birth", label: "出生日期", value: formatDate(props.doc.date_of_birth), required: true },
	{ key: "birthday", label: "生日", value: props.doc.birthday },
	{ key: "age", label: "年龄", value: props.doc.age },
	{ key: "marital_status", label: "婚姻状况", value: props.doc.marital_status },
	{ key: "hr_has_children", label: "是否已育", value: props.doc.hr_has_children },
	{ key: "hr_country_region", label: "国家/地区", value: props.doc.hr_country_region, required: true },
	{ key: "hr_ethnicity", label: "民族", value: props.doc.hr_ethnicity },
	{ key: "hr_political_status", label: "政治面貌", value: props.doc.hr_political_status },
	{ key: "hr_native_place", label: "籍贯", value: props.doc.hr_native_place },
	{ key: "hr_household_city", label: "户籍城市", value: props.doc.hr_household_city },
	{ key: "hr_household_type", label: "户口性质", value: props.doc.hr_household_type },
	{ key: "hr_household_address", label: "户籍地址", value: props.doc.hr_household_address },
	{ key: "hr_social_security_household", label: "社保户籍", value: props.doc.hr_social_security_household },
	{ key: "hr_work_start_date", label: "参加工作时间", value: formatDate(props.doc.hr_work_start_date) },
	{ key: "total_work_years", label: "工龄", value: yearsLabel(props.doc.total_work_years) },
	{ key: "hr_height", label: "身高(cm)", value: props.doc.hr_height },
	{ key: "hr_weight", label: "体重(kg)", value: props.doc.hr_weight },
	{ key: "health_details", label: "健康状况", value: props.doc.health_details },
]);

const recordBlocks = [
	{
		key: "education",
		title: "教育经历",
		empty: "暂无教育经历",
		titleOf: (r) => blank(r.school_univ),
		subOf: (r) => [blank(r.qualification || r.level), blank(r.maj_opt_subj), r.year_of_passing || ""].filter(Boolean).join(" · "),
	},
	{
		key: "external_work_history",
		title: "工作经历",
		empty: "暂无工作经历",
		titleOf: (r) => blank(r.company_name),
		subOf: (r) => [blank(r.designation), blank(r.total_experience)].filter((x) => x !== "-").join(" · "),
	},
	{
		key: "languages",
		title: "语言能力",
		empty: "暂无语言能力",
		titleOf: (r) => blank(r.language),
		subOf: (r) => ["听 " + blank(r.listening), "说 " + blank(r.speaking)].join(" · "),
	},
	{
		key: "skills",
		title: "工作技能",
		empty: "暂无工作技能",
		titleOf: (r) => blank(r.skill_name),
		subOf: (r) => [blank(r.level), r.years != null ? `${r.years} 年` : ""].filter(Boolean).join(" · "),
	},
	{
		key: "titles",
		title: "职称",
		empty: "暂无职称",
		titleOf: (r) => blank(r.title_name),
		subOf: (r) => [blank(r.level), formatDate(r.issue_date)].filter((x) => x && x !== "-").join(" · "),
	},
	{
		key: "certificates",
		title: "证书/证件",
		empty: "暂无证书",
		titleOf: (r) => blank(r.certificate_name),
		subOf: (r) => [blank(r.certificate_no), formatDate(r.issue_date)].filter((x) => x && x !== "-").join(" · "),
	},
	{
		key: "trainings",
		title: "培训经历",
		empty: "暂无培训经历",
		titleOf: (r) => blank(r.training_name),
		subOf: (r) => [blank(r.organizer), dateRange(r.start_date, r.end_date)].filter((x) => x && x !== "-").join(" · "),
	},
];

const titles = {
	education: "教育经历",
	external_work_history: "工作经历",
	languages: "语言能力",
	skills: "工作技能",
	titles: "职称",
	certificates: "证书/证件",
	trainings: "培训经历",
};

function openRecord(key, row = null) {
	modal.key = key;
	modal.title = (row?.name ? "编辑" : "新增") + titles[key];
	modal.form = { ...(row || {}), name: row?.name };
	modal.visible = true;
}

async function submitRecord() {
	modal.saving = true;
	try {
		const updated = await saveEmployeeChildRow(props.doc.name, modal.key, { ...modal.form });
		Message.success("已保存");
		emit("updated", updated);
		modal.visible = false;
	} catch (e) {
		Message.error(errMessage(e));
		return false;
	} finally {
		modal.saving = false;
	}
}

function removeRecord(key, row) {
	if (!row?.name) return;
	Modal.confirm({
		title: "确认删除",
		content: "删除后不可恢复，确定继续吗？",
		okText: "删除",
		okButtonProps: { status: "danger" },
		async onOk() {
			const updated = await saveEmployeeChildRow(props.doc.name, key, { name: row.name }, 1);
			Message.success("已删除");
			emit("updated", updated);
		},
	});
}

watch(() => props.doc?.name, pick, { immediate: true });
</script>
