<template>
	<div class="arco-org-ui ap-root ap-designer">
		<header class="apd-header">
			<div class="apd-header-left">
				<a-button type="text" @click="goBack">
					<template #icon><icon-left /></template>
					返回
				</a-button>
				<div>
					<div class="apd-title">{{ meta.form_name || "表单设计" }}</div>
					<div class="apd-sub">设计表单字段与审批流程</div>
				</div>
			</div>
			<div class="apd-header-right">
				<a-radio-group v-model="tab" type="button" size="small">
					<a-radio value="form">表单设计</a-radio>
					<a-radio value="process">流程设计</a-radio>
					<a-radio value="settings">可见范围</a-radio>
				</a-radio-group>
				<a-button type="primary" :loading="saving" @click="save">保存</a-button>
			</div>
		</header>

		<a-spin :loading="loading" style="width: 100%">
			<FormDesignerPanel
				v-if="tab === 'form'"
				v-model:fields="fields"
				v-model:selected-key="selectedFieldKey"
			/>
			<ProcessDesignerPanel
				v-else-if="tab === 'process'"
				v-model:nodes="nodes"
				:fields="fields"
			/>
			<a-card v-else :bordered="false" class="apd-settings">
				<a-form layout="vertical" style="max-width: 480px">
					<a-form-item label="可见范围">
						<a-select v-model="visibility">
							<a-option value="全公司">全公司</a-option>
							<a-option value="自定义">自定义</a-option>
						</a-select>
					</a-form-item>
					<template v-if="visibility === '自定义'">
						<a-form-item label="允许角色（逗号分隔）">
							<a-input v-model="visibilityRoles" placeholder="如：HR Manager,Employee" />
						</a-form-item>
						<a-form-item label="允许部门（名称，逗号分隔）">
							<a-input v-model="visibilityDepts" placeholder="部门名称" />
						</a-form-item>
					</template>
					<a-form-item label="业务钩子">
						<a-select v-model="businessHook" allow-clear placeholder="无">
							<a-option value="leave_application">请假闭环</a-option>
							<a-option value="out_of_office">外出闭环</a-option>
						</a-select>
					</a-form-item>
				</a-form>
			</a-card>
		</a-spin>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import FormDesignerPanel from "./FormDesignerPanel.vue";
import ProcessDesignerPanel from "./ProcessDesignerPanel.vue";

const props = defineProps({
	formName: { type: String, default: "" },
});

const loading = ref(false);
const saving = ref(false);
const tab = ref("form");
const meta = ref({});
const fields = ref([]);
const nodes = ref([]);
const selectedFieldKey = ref("");
const visibility = ref("全公司");
const visibilityRoles = ref("");
const visibilityDepts = ref("");
const businessHook = ref("");

const formId = computed(() => {
	if (props.formName) return props.formName;
	const route = window.frappe?.get_route?.() || [];
	// ["approval-form-designer", formName]
	return route[1] || new URLSearchParams(location.search).get("form") || "";
});

async function call(method, args = {}) {
	const r = await window.frappe.call({
		method: `employee_roster.hr_roster.approval_runtime.${method}`,
		args,
	});
	return r.message;
}

async function load() {
	if (!formId.value) {
		Message.error("缺少表单参数");
		return;
	}
	loading.value = true;
	try {
		const data = await call("get_form_design", { name: formId.value });
		meta.value = data;
		fields.value = data.form_schema?.fields || [];
		nodes.value = data.process?.nodes || [];
		visibility.value = data.visibility || "全公司";
		businessHook.value = data.business_hook || "";
		const vj = data.visibility_json || {};
		visibilityRoles.value = (vj.roles || []).join(",");
		visibilityDepts.value = (vj.departments || []).join(",");
	} catch (e) {
		Message.error(e.message || "加载失败");
	} finally {
		loading.value = false;
	}
}

async function save() {
	saving.value = true;
	try {
		await call("save_form_design", {
			payload: {
				name: formId.value,
				form_schema: { fields: fields.value },
				process: { nodes: nodes.value },
				visibility: visibility.value,
				visibility_json: {
					roles: visibilityRoles.value
						.split(",")
						.map((s) => s.trim())
						.filter(Boolean),
					departments: visibilityDepts.value
						.split(",")
						.map((s) => s.trim())
						.filter(Boolean),
				},
				business_hook: businessHook.value || "",
			},
		});
		Message.success("已保存");
	} catch (e) {
		Message.error(e.message || "保存失败");
	} finally {
		saving.value = false;
	}
}

function goBack() {
	if (window.frappe?.set_route) {
		window.frappe.set_route("approvals");
	} else {
		history.back();
	}
}

onMounted(load);
</script>
