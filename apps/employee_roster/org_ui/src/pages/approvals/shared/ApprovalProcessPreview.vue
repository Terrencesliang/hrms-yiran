<template>
	<div class="ap-process-preview">
		<div class="ap-process-preview__title">
			审批流程（已由管理员预设不可修改审批人）
		</div>
		<a-empty
			v-if="!steps?.length"
			description="暂无流程节点"
			class="ap-process-preview__empty"
		/>
		<div v-else class="ap-process-preview__timeline">
			<div
				v-for="(step, idx) in steps"
				:key="step.id || idx"
				class="ap-process-step"
				:class="[`is-${step.type || 'approver'}`, { 'is-last': idx === steps.length - 1 }]"
			>
				<div class="ap-process-step__rail">
					<span class="ap-process-step__dot">
						<icon-send v-if="step.type === 'cc'" />
						<icon-user v-else />
					</span>
					<span v-if="idx !== steps.length - 1" class="ap-process-step__line" />
				</div>
				<div class="ap-process-step__body">
					<div class="ap-process-step__label">{{ step.label }}</div>
					<div class="ap-process-people">
						<div
							v-for="person in step.people || []"
							:key="person.user"
							class="ap-process-person"
						>
							<a-avatar :size="28" :image-url="person.avatar || undefined">
								{{ avatarText(person.full_name || person.user) }}
							</a-avatar>
							<span class="ap-process-person__name">{{ person.full_name || person.user }}</span>
						</div>

						<div v-if="step.empty" class="ap-process-person is-empty">
							<a-avatar :size="28">
								<template #icon><icon-user /></template>
							</a-avatar>
							<span class="ap-process-person__name is-danger">审批人为空</span>
						</div>

						<button
							v-if="step.type === 'cc' && !step.locked"
							type="button"
							class="ap-process-add"
							aria-label="添加抄送人"
						>
							<icon-plus />
						</button>
					</div>
					<div v-if="step.auto_approve_hint" class="ap-process-hint">
						<icon-exclamation-circle-fill />
						<span>未找到审批人，将自动同意</span>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import {
	IconExclamationCircleFill,
	IconPlus,
	IconSend,
	IconUser,
} from "@arco-design/web-vue/es/icon";

defineProps({
	steps: {
		type: Array,
		default: () => [],
	},
});

function avatarText(name) {
	const s = String(name || "").trim();
	return s ? s.slice(0, 1) : "?";
}
</script>
