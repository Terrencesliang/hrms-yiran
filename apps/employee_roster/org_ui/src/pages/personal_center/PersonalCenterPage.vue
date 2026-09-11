<template>
	<HrPage :breadcrumbs="[{ label: '个人中心' }]" class="personal-center-shell">
		<a-spin :loading="loading" style="width: 100%">
			<div v-if="context" class="pc-layout">
				<header class="pc-heading">
					<div>
						<h1>个人中心</h1>
						<p>查看本人资料，管理登录账号与密码</p>
					</div>
					<a-tag color="green" bordered>{{ context.account.enabled ? "账号正常" : "账号已停用" }}</a-tag>
				</header>

				<a-alert
					v-if="context.account.must_change_password"
					type="warning"
					show-icon
					class="pc-security-alert"
					title="当前使用的是初始密码，请尽快修改"
					content="新密码至少 8 位，并同时包含字母和数字。修改后其他设备上的登录会失效。"
				/>

				<section class="pc-grid">
					<a-card :bordered="false" class="pc-profile-card">
						<div class="pc-person">
							<a-avatar :size="72" class="pc-avatar">
								<img v-if="avatar" :src="avatar" alt="个人头像" />
								<span v-else>{{ avatarText }}</span>
							</a-avatar>
							<div class="pc-person-copy">
								<div class="pc-name-row">
									<h2>{{ displayName }}</h2>
									<a-tag v-if="employee" :color="employee.status === 'Active' ? 'green' : 'gray'" size="small">
										{{ employee.status === "Active" ? "在职" : "已离职" }}
									</a-tag>
								</div>
								<p>{{ employee?.designation || "暂未设置岗位" }}</p>
								<span>{{ organizationLine }}</span>
							</div>
						</div>
						<a-divider />
						<div class="pc-account-summary">
							<div><span>登录账号</span><strong>{{ context.account.username }}</strong></div>
							<div><span>员工工号</span><strong>{{ employee?.employee_number || "—" }}</strong></div>
							<div><span>企业微信</span><strong :class="employee?.wecom_bound ? 'is-bound' : ''">{{ employee?.wecom_bound ? "已绑定" : "未绑定" }}</strong></div>
						</div>
					</a-card>

					<a-card :bordered="false" class="pc-security-card">
						<div class="pc-card-title">
							<span class="pc-title-icon"><icon-lock /></span>
							<div><h2>账号安全</h2><p>定期修改密码可以更好地保护账号</p></div>
						</div>
						<a-form ref="passwordFormRef" :model="passwordForm" layout="vertical" @submit-success="submitPassword">
							<a-form-item field="current_password" label="当前密码" :rules="[{ required: true, message: '请输入当前密码' }]">
								<a-input-password v-model="passwordForm.current_password" allow-clear placeholder="请输入当前使用的密码" />
							</a-form-item>
							<a-form-item field="new_password" label="新密码" :rules="newPasswordRules">
								<a-input-password v-model="passwordForm.new_password" allow-clear placeholder="至少 8 位，包含字母和数字" />
							</a-form-item>
							<a-form-item field="confirm_password" label="确认新密码" :rules="confirmPasswordRules">
								<a-input-password v-model="passwordForm.confirm_password" allow-clear placeholder="请再次输入新密码" />
							</a-form-item>
							<div class="pc-password-meta">
								<span>上次修改：{{ context.account.last_password_reset_date }}</span>
								<a-button html-type="submit" type="primary" :loading="savingPassword">修改密码</a-button>
							</div>
						</a-form>
					</a-card>
				</section>

				<a-card :bordered="false" class="pc-details-card">
					<a-tabs v-model:active-key="activeTab">
						<a-tab-pane key="work" title="任职信息">
							<dl class="pc-info-grid"><div v-for="item in workItems" :key="item.label" class="pc-info-item"><dt>{{ item.label }}</dt><dd>{{ item.value }}</dd></div></dl>
						</a-tab-pane>
						<a-tab-pane key="personal" title="个人信息">
							<dl class="pc-info-grid"><div v-for="item in personalItems" :key="item.label" class="pc-info-item"><dt>{{ item.label }}</dt><dd>{{ item.value }}</dd></div></dl>
						</a-tab-pane>
						<a-tab-pane key="contact" title="联系信息">
							<dl class="pc-info-grid"><div v-for="item in contactItems" :key="item.label" class="pc-info-item"><dt>{{ item.label }}</dt><dd>{{ item.value }}</dd></div></dl>
						</a-tab-pane>
					</a-tabs>
					<a-empty v-if="!employee" description="当前账号尚未关联员工档案，请联系管理员处理" />
				</a-card>
			</div>
			<a-result v-else-if="errorMessage" status="error" title="个人中心加载失败" :subtitle="errorMessage">
				<template #extra><a-button type="primary" @click="loadContext">重新加载</a-button></template>
			</a-result>
		</a-spin>
	</HrPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { Message, Modal } from "@arco-design/web-vue";
import { IconLock } from "@arco-design/web-vue/es/icon";
import HrPage from "../../components/HrPage.vue";
import { changeMyPassword, getPersonalCenterContext, type PersonalCenterContext } from "../../api/personalCenter";
import "./personal-center.css";

const context = ref<PersonalCenterContext | null>(null);
const loading = ref(false);
const savingPassword = ref(false);
const errorMessage = ref("");
const activeTab = ref("work");
const passwordFormRef = ref();
const passwordForm = reactive({ current_password: "", new_password: "", confirm_password: "" });

const employee = computed(() => context.value?.employee || null);
const displayName = computed(() => employee.value?.employee_name || context.value?.account.full_name || "当前用户");
const avatar = computed(() => employee.value?.image || context.value?.account.avatar || "");
const avatarText = computed(() => displayName.value.slice(0, 1));
const organizationLine = computed(() => [employee.value?.department, employee.value?.group_name, employee.value?.company].filter(Boolean).join(" · ") || "暂未关联组织信息");
const value = (input?: string) => input || "—";
const workItems = computed(() => [
	{ label: "所属公司", value: value(employee.value?.company) },
	{ label: "部门", value: value(employee.value?.department) },
	{ label: "组别", value: value(employee.value?.group_name) },
	{ label: "岗位", value: value(employee.value?.designation) },
	{ label: "分支机构", value: value(employee.value?.branch) },
	{ label: "用工类型", value: value(employee.value?.employment_type) },
	{ label: "入职日期", value: value(employee.value?.date_of_joining) },
	{ label: "汇报上级", value: value(employee.value?.reports_to_name) },
]);
const personalItems = computed(() => [
	{ label: "姓名", value: value(employee.value?.employee_name) },
	{ label: "工号", value: value(employee.value?.employee_number) },
	{ label: "性别", value: value(employee.value?.gender) },
	{ label: "出生日期", value: value(employee.value?.date_of_birth) },
]);
const contactItems = computed(() => [
	{ label: "手机号", value: value(employee.value?.cell_number) },
	{ label: "企业邮箱", value: value(employee.value?.company_email) },
	{ label: "个人邮箱", value: value(employee.value?.personal_email) },
	{ label: "现居地址", value: value(employee.value?.current_address) },
]);

const newPasswordRules = [
	{ required: true, message: "请输入新密码" },
	{ minLength: 8, message: "新密码至少需要 8 位" },
	{ validator: (value: string, callback: (error?: string) => void) => /[A-Za-z]/.test(value) && /\d/.test(value) ? callback() : callback("新密码需要同时包含字母和数字") },
];
const confirmPasswordRules = [
	{ required: true, message: "请再次输入新密码" },
	{ validator: (value: string, callback: (error?: string) => void) => value === passwordForm.new_password ? callback() : callback("两次输入的新密码不一致") },
];

async function loadContext() {
	loading.value = true;
	errorMessage.value = "";
	try { context.value = await getPersonalCenterContext(); }
	catch (error: any) { errorMessage.value = error?.message || "无法获取当前用户信息"; }
	finally { loading.value = false; }
}

async function submitPassword() {
	Modal.confirm({
		title: "确认修改密码？",
		content: "修改后其他设备上的登录将失效，请使用新密码登录。",
		okText: "确认修改",
		cancelText: "取消",
		onOk: async () => {
			savingPassword.value = true;
			try {
				const result = await changeMyPassword(passwordForm);
				Message.success(result.message || "密码修改成功");
				passwordForm.current_password = passwordForm.new_password = passwordForm.confirm_password = "";
				passwordFormRef.value?.resetFields?.();
				if (context.value) context.value.account.must_change_password = false;
				await loadContext();
			} catch (error: any) {
				Message.error(error?.message || "密码修改失败");
				throw error;
			} finally { savingPassword.value = false; }
		},
	});
}

onMounted(loadContext);
</script>
