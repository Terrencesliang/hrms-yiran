<template>
	<div class="arco-emp-archive-tab" v-if="doc">
		<a-spin :loading="loading" style="width: 100%">
			<div class="arco-emp-archive-stack">
				<EmployeeEditableSection
					title="个人简介"
					section-key="profile_bio"
					:can-edit="canEdit"
					:reset-token="resetToken"
					@edit="startEdit"
					@cancel="cancelEdit"
					@save="saveBasic"
				>
					<template #view>
						<div v-if="doc.bio" class="arco-emp-bio-text">{{ doc.bio }}</div>
						<div v-else class="arco-emp-empty-state">
							<p>暂无个人简介</p>
						</div>
					</template>
					<template #edit>
						<a-form :model="form" layout="vertical" class="arco-emp-archive-form">
							<a-form-item label="个人简介">
								<a-textarea v-model="form.bio" :auto-size="{ minRows: 4, maxRows: 10 }" allow-clear />
							</a-form-item>
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
					<a-form-item label="专业"><a-input v-model="modal.form.maj_opt_subj" /></a-form-item>
					<a-form-item label="毕业年份"><a-input-number v-model="modal.form.year_of_passing" style="width:100%" /></a-form-item>
				</template>
				<template v-else-if="modal.key === 'external_work_history'">
					<a-form-item label="公司名称" required><a-input v-model="modal.form.company_name" /></a-form-item>
					<a-form-item label="岗位"><a-input v-model="modal.form.designation" /></a-form-item>
					<a-form-item label="工作年限"><a-input v-model="modal.form.total_experience" /></a-form-item>
				</template>
				<template v-else-if="modal.key === 'internal_work_history'">
					<a-form-item label="岗位" required><a-input v-model="modal.form.designation" /></a-form-item>
					<a-form-item label="部门"><a-input v-model="modal.form.department" /></a-form-item>
					<a-form-item label="开始日期"><a-date-picker v-model="modal.form.from_date" style="width:100%" value-format="YYYY-MM-DD" /></a-form-item>
					<a-form-item label="结束日期"><a-date-picker v-model="modal.form.to_date" style="width:100%" value-format="YYYY-MM-DD" /></a-form-item>
				</template>
			</a-form>
		</a-modal>
	</div>
</template>

<script setup>
import { reactive, watch } from "vue";
import { Message, Modal } from "@arco-design/web-vue";
import EmployeeEditableSection from "../EmployeeEditableSection.vue";
import EmployeeRecordList from "../EmployeeRecordList.vue";
import { saveEmployeeChildRow, saveEmployeeSection } from "../../../api/employeeDetail";
import { blank, dateRange, errMessage, formatDate } from "../../../utils/employeeArchive";

const props = defineProps({
	doc: { type: Object, required: true },
	loading: { type: Boolean, default: false },
	canEdit: { type: Boolean, default: false },
	resetToken: { type: [Number, String], default: 0 },
});
const emit = defineEmits(["updated"]);

const form = reactive({ bio: "" });
const modal = reactive({ visible: false, saving: false, key: "", title: "", form: {} });

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
		title: "外部工作经历",
		empty: "暂无外部工作经历",
		titleOf: (r) => blank(r.company_name),
		subOf: (r) => [blank(r.designation), blank(r.total_experience)].filter((x) => x !== "-").join(" · "),
	},
	{
		key: "internal_work_history",
		title: "内部任职记录",
		empty: "暂无内部任职记录",
		titleOf: (r) => blank(r.designation),
		subOf: (r) => [blank(r.department), dateRange(r.from_date, r.to_date)].filter((x) => x && x !== "-").join(" · "),
	},
];

function pick() {
	form.bio = props.doc?.bio || "";
}
function startEdit() { pick(); }
function cancelEdit() { pick(); }

async function saveBasic(ctl) {
	try {
		const updated = await saveEmployeeSection(props.doc.name, "profile_bio", { bio: form.bio });
		Message.success("保存成功");
		emit("updated", updated);
		ctl.done(true);
	} catch (e) {
		Message.error(errMessage(e));
		ctl.fail();
	}
}

const titles = {
	education: "教育经历",
	external_work_history: "外部工作经历",
	internal_work_history: "内部任职记录",
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
