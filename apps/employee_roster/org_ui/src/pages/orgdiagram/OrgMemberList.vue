<template>
	<a-card class="od-member-list" :bordered="true">
		<div class="od-member-list__head">
			<span class="od-node-icon is-member"><icon-user /></span>
			<strong>{{ title }}</strong>
			<a-typography-text type="secondary">{{ members.length }} 人</a-typography-text>
		</div>
		<ul class="od-member-list__body">
			<li v-for="member in members" :key="member.name">
				<a-avatar :size="24" class="od-member-avatar">{{ initial(member) }}</a-avatar>
				<div class="od-member-list__text">
					<a-link class="od-member-name" @click.stop="$emit('open-member', member)">{{ member.title }}</a-link>
					<span class="od-member-role" :title="member.designation">{{ member.designation || "岗位未设置" }}</span>
				</div>
				<a-tag v-if="isPartTime(member)" size="small" color="gray">非全职</a-tag>
			</li>
		</ul>
	</a-card>
</template>

<script setup>
defineProps({
	members: { type: Array, default: () => [] },
	title: { type: String, default: "成员" },
});

defineEmits(["open-member"]);

const NON_FULLTIME = new Set(["Part-time", "Intern", "Contract"]);

function initial(member) {
	return String(member.title || "").trim().slice(0, 1) || "?";
}

function isPartTime(member) {
	return NON_FULLTIME.has(member.employment_type);
}
</script>
