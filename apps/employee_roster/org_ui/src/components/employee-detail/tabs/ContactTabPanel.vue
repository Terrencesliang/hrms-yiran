<template>
	<div class="arco-emp-archive-tab" v-if="doc">
		<a-spin :loading="loading" style="width: 100%">
			<div class="arco-emp-archive-stack">
				<EmployeeEditableSection
					title="基础联系方式"
					section-key="contact_basic"
					:can-edit="canEdit"
					:reset-token="resetToken"
					@edit="startEdit"
					@cancel="cancelEdit"
					@save="saveBasic"
				>
					<template #view>
						<EmployeePreviewGrid :items="basicItems" />
					</template>
					<template #edit>
						<a-form :model="form" layout="vertical" class="arco-emp-archive-form">
							<a-row :gutter="16">
								<a-col :span="8"><a-form-item label="手机号码" required><a-input v-model="form.cell_number" /></a-form-item></a-col>
								<a-col :span="8"><a-form-item label="个人邮箱"><a-input v-model="form.personal_email" /></a-form-item></a-col>
								<a-col :span="8"><a-form-item label="工作电话"><a-input v-model="form.hr_work_phone" /></a-form-item></a-col>
								<a-col :span="8"><a-form-item label="工作邮箱"><a-input v-model="form.company_email" /></a-form-item></a-col>
								<a-col :span="8"><a-form-item label="企业微信账号"><a-input v-model="form.hr_wecom_id" /></a-form-item></a-col>
								<a-col :span="8"><a-form-item label="微信号"><a-input v-model="form.hr_wechat" /></a-form-item></a-col>
								<a-col :span="24"><a-form-item label="现居住地"><a-textarea v-model="form.current_address" :auto-size="{minRows:2}" /></a-form-item></a-col>
								<a-col :span="24"><a-form-item label="永久地址"><a-textarea v-model="form.permanent_address" :auto-size="{minRows:2}" /></a-form-item></a-col>
							</a-row>
						</a-form>
					</template>
				</EmployeeEditableSection>

				<EmployeeRecordList
						title="紧急联系人"
						section-key="emergency_contacts"
						:records="doc.emergency_contacts || []"
						:can-edit="canEdit"
						empty-text="暂无紧急联系人"
						@add="openEmergency()"
						@edit="openEmergency"
						@remove="removeChild('emergency_contacts', $event)"
					>
						<template #item="{ row }">
							<div class="arco-emp-record-title">{{ blank(row.contact_name) }} · {{ blank(row.relationship) }}</div>
							<div class="arco-emp-record-sub">{{ blank(row.mobile) }}{{ row.workplace ? ` · ${row.workplace}` : "" }}</div>
						</template>
					</EmployeeRecordList>

				<EmployeeRecordList
						title="家庭成员"
						section-key="family_members"
						:records="doc.family_members || []"
						:can-edit="canEdit"
						empty-text="暂无家庭成员"
						@add="openFamily()"
						@edit="openFamily"
						@remove="removeChild('family_members', $event)"
					>
						<template #item="{ row }">
							<div class="arco-emp-record-title">
								{{ blank(row.member_name) }} · {{ blank(row.relationship) }}
								<a-tag v-if="row.is_emergency_contact" size="small" color="arcoblue" style="margin-left: 6px">紧急联系人</a-tag>
							</div>
							<div class="arco-emp-record-sub">
								{{ blank(row.mobile) }}{{ row.workplace ? ` · ${row.workplace}` : "" }}
							</div>
						</template>
					</EmployeeRecordList>
			</div>
		</a-spin>

		<a-modal v-model:visible="em.visible" :title="em.form.name ? '编辑紧急联系人' : '新增紧急联系人'" :ok-loading="em.saving" unmount-on-close @ok="submitEmergency">
			<a-form :model="em.form" layout="vertical">
				<a-form-item label="姓名" required><a-input v-model="em.form.contact_name" /></a-form-item>
				<a-form-item label="与本人关系" required><a-input v-model="em.form.relationship" /></a-form-item>
				<a-form-item label="手机号码" required><a-input v-model="em.form.mobile" /></a-form-item>
				<a-form-item label="工作单位"><a-input v-model="em.form.workplace" /></a-form-item>
				<a-form-item label="联系地址"><a-textarea v-model="em.form.address" :auto-size="{minRows:2}" /></a-form-item>
			</a-form>
		</a-modal>

		<a-modal v-model:visible="fm.visible" :title="fm.form.name ? '编辑家庭成员' : '新增家庭成员'" :ok-loading="fm.saving" unmount-on-close @ok="submitFamily">
			<a-form :model="fm.form" layout="vertical">
				<a-form-item label="姓名" required><a-input v-model="fm.form.member_name" /></a-form-item>
				<a-form-item label="与本人关系" required><a-input v-model="fm.form.relationship" /></a-form-item>
				<a-form-item label="性别"><a-input v-model="fm.form.gender" /></a-form-item>
				<a-form-item label="出生日期"><a-date-picker v-model="fm.form.date_of_birth" style="width:100%" value-format="YYYY-MM-DD" /></a-form-item>
				<a-form-item label="手机号码"><a-input v-model="fm.form.mobile" /></a-form-item>
				<a-form-item label="工作单位"><a-input v-model="fm.form.workplace" /></a-form-item>
				<a-form-item label="是否紧急联系人"><a-switch v-model="fm.form.is_emergency_contact" :checked-value="1" :unchecked-value="0" /></a-form-item>
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
import { blank, errMessage } from "../../../utils/employeeArchive";

const props = defineProps({
	doc: { type: Object, required: true },
	loading: { type: Boolean, default: false },
	canEdit: { type: Boolean, default: false },
	resetToken: { type: Number, default: 0 },
});
const emit = defineEmits(["updated"]);

const KEYS = ["cell_number", "personal_email", "hr_work_phone", "company_email", "current_address", "hr_wecom_id", "hr_wechat", "permanent_address"];
const form = reactive({});
const em = reactive({ visible: false, saving: false, form: {} });
const fm = reactive({ visible: false, saving: false, form: {} });

function pick() {
	KEYS.forEach((k) => { form[k] = props.doc?.[k] ?? ""; });
	if (props.doc?.can_view_sensitive && props.doc?.cell_number_raw) form.cell_number = props.doc.cell_number_raw;
}
function startEdit() { pick(); }
function cancelEdit() { pick(); }

async function saveBasic(ctl) {
	try {
		if (!String(form.cell_number || "").trim()) {
			Message.warning("请填写手机号码");
			ctl.fail();
			return;
		}
		const updated = await saveEmployeeSection(props.doc.name, "contact_basic", { ...form });
		Message.success("保存成功");
		emit("updated", updated);
		ctl.done(true);
	} catch (e) {
		Message.error(errMessage(e));
		ctl.fail();
	}
}

const basicItems = computed(() => [
	{ key: "cell_number", label: "手机号码", value: props.doc.cell_number, required: true },
	{ key: "personal_email", label: "个人邮箱", value: props.doc.personal_email },
	{ key: "hr_work_phone", label: "工作电话", value: props.doc.hr_work_phone },
	{ key: "company_email", label: "工作邮箱", value: props.doc.company_email },
	{ key: "current_address", label: "现居住地", value: props.doc.current_address },
	{ key: "hr_wecom_id", label: "企业微信账号", value: props.doc.hr_wecom_id },
]);

function openEmergency(row = null) {
	em.form = {
		name: row?.name,
		contact_name: row?.contact_name || "",
		relationship: row?.relationship || "",
		mobile: row?.mobile || "",
		workplace: row?.workplace || "",
		address: row?.address || "",
	};
	em.visible = true;
}

async function submitEmergency() {
	em.saving = true;
	try {
		const updated = await saveEmployeeChildRow(props.doc.name, "emergency_contacts", { ...em.form });
		Message.success("已保存");
		emit("updated", updated);
		em.visible = false;
	} catch (e) {
		Message.error(errMessage(e));
		return false;
	} finally {
		em.saving = false;
	}
}

function openFamily(row = null) {
	fm.form = {
		name: row?.name,
		member_name: row?.member_name || "",
		relationship: row?.relationship || "",
		gender: row?.gender || "",
		date_of_birth: row?.date_of_birth || "",
		mobile: row?.mobile || "",
		workplace: row?.workplace || "",
		is_emergency_contact: row?.is_emergency_contact ? 1 : 0,
	};
	fm.visible = true;
}

async function submitFamily() {
	fm.saving = true;
	try {
		const updated = await saveEmployeeChildRow(props.doc.name, "family_members", { ...fm.form });
		Message.success("已保存");
		emit("updated", updated);
		fm.visible = false;
	} catch (e) {
		Message.error(errMessage(e));
		return false;
	} finally {
		fm.saving = false;
	}
}

function removeChild(key, row) {
	if (!row?.name || row.name === "legacy") {
		Message.warning("该记录无法删除");
		return;
	}
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
