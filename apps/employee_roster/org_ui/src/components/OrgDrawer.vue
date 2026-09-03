<template>
	<a-drawer
		:visible="visible"
		:width="480"
		unmount-on-close
		:mask-closable="true"
		@cancel="$emit('update:visible', false)"
		@ok="submit(false)"
	>
		<template #title>新增组织</template>
		<template #footer>
			<a-space>
				<a-button :loading="savingContinue" @click="submit(true)">保存并继续添加</a-button>
				<a-button type="primary" :loading="saving" @click="submit(false)">确认</a-button>
			</a-space>
		</template>

		<a-form ref="formRef" :model="form" :rules="rules" layout="horizontal" auto-label-width>
			<a-form-item field="title" label="组织名称" required>
				<a-input v-model="form.title" :max-length="140" placeholder="请输入组织名称" />
			</a-form-item>
			<a-form-item field="org_code" label="组织代码">
				<a-input v-model="form.org_code" placeholder="请输入..." />
			</a-form-item>
			<a-form-item field="org_abbr" label="组织简称">
				<a-input v-model="form.org_abbr" placeholder="请输入" />
			</a-form-item>
			<a-form-item field="org_type" label="组织类型">
				<a-space direction="vertical" fill>
					<a-select v-model="form.org_type">
						<a-option value="部门">部门</a-option>
						<a-option value="组">组</a-option>
						<a-option value="公司">公司</a-option>
					</a-select>
					<a-switch v-model="form.enable_cost_center" :checked-value="1" :unchecked-value="0">
						<template #checked>已启用费用中心类型</template>
						<template #unchecked>启用费用中心类型</template>
					</a-switch>
				</a-space>
			</a-form-item>
			<a-form-item field="parent" label="上级组织">
				<a-select v-model="form.parent" allow-search :options="parentOptions" placeholder="请选择上级组织" />
			</a-form-item>
			<a-form-item field="department_head" label="组织负责人">
				<a-select
					v-model="form.department_head"
					allow-search
					allow-clear
					:filter-option="false"
					:options="headOptions"
					placeholder="员工姓名/拼音"
					@search="(txt) => searchHead(txt)"
				/>
			</a-form-item>
			<a-form-item field="staff_quota" label="编制人数">
				<a-input-number v-model="form.staff_quota" :min="0" :precision="0" placeholder="请输入..." hide-button />
			</a-form-item>
			<a-form-item field="effective_date" label="启用日期" required>
				<a-date-picker v-model="form.effective_date" value-format="YYYY-MM-DD" style="width: 100%" />
			</a-form-item>

			<a-button type="text" @click="showExtra = !showExtra">
				{{ showExtra ? "收起信息" : "展开信息" }}
				<icon-down :style="{ transform: showExtra ? 'rotate(180deg)' : 'none' }" />
			</a-button>

			<template v-if="showExtra">
				<a-form-item field="supervisor" label="分管领导">
					<a-select
						v-model="form.supervisor"
						allow-search
						allow-clear
						:filter-option="false"
						:options="supervisorOptions"
						placeholder="员工姓名/拼音"
						@search="(txt) => searchSupervisor(txt)"
					/>
				</a-form-item>
				<a-form-item field="org_remark" label="备注">
					<a-textarea v-model="form.org_remark" :auto-size="{ minRows: 3 }" placeholder="请输入" />
				</a-form-item>
			</template>
		</a-form>
	</a-drawer>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { Message } from "@arco-design/web-vue";
import { createOrgUnit, flattenTree, searchEmployees } from "../api";

const props = defineProps({
	visible: Boolean,
	company: String,
	preset: { type: Object, default: () => ({}) },
	roots: { type: Array, default: () => [] },
});

const emit = defineEmits(["update:visible", "created"]);

const formRef = ref(null);
const showExtra = ref(false);
const saving = ref(false);
const savingContinue = ref(false);
const headOptions = ref([]);
const supervisorOptions = ref([]);

const form = reactive({
	title: "",
	org_code: "",
	org_abbr: "",
	org_type: "部门",
	parent: "",
	department_head: "",
	supervisor: "",
	staff_quota: undefined,
	effective_date: "",
	enable_cost_center: 0,
	org_remark: "",
});

const rules = {
	title: [{ required: true, message: "组织名称不能为空" }],
	effective_date: [{ required: true, message: "请选择启用日期" }],
};

const parentOptions = computed(() =>
	flattenTree(props.roots)
		.filter((it) => !it.node.is_employee)
		.map((it) => ({
			value: it.node.key || it.node.name,
			label: `${"　".repeat(it.depth)}${it.node.title}`,
		}))
);

function today() {
	return window.frappe?.datetime?.get_today?.() || new Date().toISOString().slice(0, 10);
}

function resetForm() {
	form.title = "";
	form.org_code = "";
	form.org_abbr = "";
	form.org_type = "部门";
	form.parent = props.preset.parent || props.roots?.[0]?.name || "";
	form.department_head = "";
	form.supervisor = "";
	form.staff_quota = undefined;
	form.effective_date = today();
	form.enable_cost_center = 0;
	form.org_remark = "";
	showExtra.value = false;
}

watch(
	() => props.visible,
	(open) => {
		if (open) resetForm();
	}
);

async function loadEmployees(txt, target) {
	const rows = await searchEmployees(txt, props.company);
	target.value = (rows || []).map((row) => ({
		value: row.name,
		label: `${row.employee_name}${row.designation ? " · " + row.designation : ""}`,
	}));
}

function searchHead(txt) {
	loadEmployees(txt, headOptions);
}
function searchSupervisor(txt) {
	loadEmployees(txt, supervisorOptions);
}

async function submit(continueAdd) {
	const err = await formRef.value?.validate();
	if (err) return;
	const flag = continueAdd ? savingContinue : saving;
	flag.value = true;
	try {
		await createOrgUnit({
			...form,
			staff_quota: form.staff_quota || 0,
			company: props.company,
		});
		Message.success("组织已创建");
		emit("created");
		if (continueAdd) {
			form.title = "";
			form.org_code = "";
			form.org_abbr = "";
			form.staff_quota = undefined;
			form.department_head = "";
			formRef.value?.clearValidate();
		} else {
			emit("update:visible", false);
		}
	} finally {
		flag.value = false;
	}
}
</script>
