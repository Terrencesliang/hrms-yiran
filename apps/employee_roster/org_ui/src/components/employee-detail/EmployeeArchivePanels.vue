<template>
	<a-config-provider :locale="zhCN">
		<div class="arco-emp-archive-panels arco-emp-pro">
			<EmploymentTabPanel
				v-if="activeTab === 'employment_details'"
				:doc="doc"
				:loading="loading"
				:can-edit="canEdit"
				:reset-token="resetToken"
				@updated="onUpdated"
			/>
			<PersonalTabPanel
				v-else-if="activeTab === 'personal_details'"
				:doc="doc"
				:loading="loading"
				:can-edit="canEdit"
				:reset-token="resetToken"
				@updated="onUpdated"
			/>
			<ContactTabPanel
				v-else-if="activeTab === 'contact_details'"
				:doc="doc"
				:loading="loading"
				:can-edit="canEdit"
				:reset-token="resetToken"
				@updated="onUpdated"
			/>
			<SalaryTabPanel
				v-else-if="activeTab === 'salary_information'"
				:doc="doc"
				:loading="loading"
				:can-edit="canEdit"
				:reset-token="resetToken"
				@updated="onUpdated"
			/>
			<ContractTabPanel
				v-else-if="activeTab === 'hr_contract_tab'"
				:doc="doc"
				:loading="loading"
				:can-edit="canEdit"
				:reset-token="resetToken"
				@updated="onUpdated"
			/>
			<MaterialsTabPanel
				v-else-if="activeTab === 'hr_materials_tab'"
				:doc="doc"
				:loading="loading"
				:can-edit="canEdit"
				:reset-token="resetToken"
				@updated="onUpdated"
			/>
			<AttendanceTabPanel
				v-else-if="activeTab === 'attendance_and_leave_details'"
				:doc="doc"
				:loading="loading"
				:can-edit="canEdit"
				:reset-token="resetToken"
				@updated="onUpdated"
			/>
			<ProfileTabPanel
				v-else-if="activeTab === 'profile_tab'"
				:doc="doc"
				:loading="loading"
				:can-edit="canEdit"
				:reset-token="resetToken"
				@updated="onUpdated"
			/>
			<BackgroundTabPanel
				v-else-if="activeTab === 'hr_background_tab'"
				:doc="doc"
				:loading="loading"
				:can-edit="canEdit"
				:reset-token="resetToken"
				@updated="onUpdated"
			/>
			<ExitTabPanel
				v-else-if="activeTab === 'exit'"
				:doc="doc"
				:loading="loading"
				:can-edit="canEdit"
				:reset-token="resetToken"
				@updated="onUpdated"
			/>
		</div>
	</a-config-provider>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import zhCN from "@arco-design/web-vue/es/locale/lang/zh-cn";
import EmploymentTabPanel from "./tabs/EmploymentTabPanel.vue";
import PersonalTabPanel from "./tabs/PersonalTabPanel.vue";
import ContactTabPanel from "./tabs/ContactTabPanel.vue";
import SalaryTabPanel from "./tabs/SalaryTabPanel.vue";
import ContractTabPanel from "./tabs/ContractTabPanel.vue";
import MaterialsTabPanel from "./tabs/MaterialsTabPanel.vue";
import AttendanceTabPanel from "./tabs/AttendanceTabPanel.vue";
import ProfileTabPanel from "./tabs/ProfileTabPanel.vue";
import BackgroundTabPanel from "./tabs/BackgroundTabPanel.vue";
import ExitTabPanel from "./tabs/ExitTabPanel.vue";
import { provideArchiveExpand } from "./useArchiveExpand";

const props = defineProps({
	state: { type: Object, required: true },
	handlers: { type: Object, default: () => ({}) },
});

const doc = computed(() => props.state.doc || {});
const loading = computed(() => !!props.state.loading);
const activeTab = computed(() => props.state.activeTab || "");
const resetToken = computed(() => props.state.resetToken || 0);
const canEdit = computed(() => !!(props.state.doc?.can_edit || props.state.can_edit));

const expandSection = ref(props.state.expandSection || "");
const expandNonce = ref(props.state.expandNonce || 0);
provideArchiveExpand({ expandSection, expandNonce });

watch(
	() => [props.state.expandSection, props.state.expandNonce],
	([section, nonce]) => {
		expandSection.value = section || "";
		expandNonce.value = nonce || 0;
	}
);

function onUpdated(payload) {
	props.handlers?.onUpdated?.(payload);
}
</script>
