<template>
	<a-card class="od-company-node" :bordered="true">
		<div class="od-company-node__content">
			<span class="od-node-icon od-node-icon--company"><icon-home /></span>
			<div class="od-company-node__main">
				<strong>{{ companyName || "公司" }}</strong>
				<span v-if="manager.label" class="od-manager-line">
					总经理
					<a-avatar :size="22" :image-url="manager.image || undefined"><icon-user /></a-avatar>
					{{ manager.name || manager.label }}
				</span>
			</div>
			<a-typography-text class="od-company-node__count">
				<strong>{{ employeeCount }} 人</strong><i></i>{{ departmentCount }} 个一级部门
			</a-typography-text>
		</div>
	</a-card>
</template>

<script setup>
defineProps({
	companyName: String,
	manager: { type: Object, default: () => ({}) },
	employeeCount: { type: Number, default: 0 },
	departmentCount: { type: Number, default: 0 },
});
</script>
