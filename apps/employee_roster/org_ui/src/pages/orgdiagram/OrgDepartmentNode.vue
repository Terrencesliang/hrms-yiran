<template>
	<a-card
		class="od-unit-node"
		:class="[`is-level-${level}`, { 'is-expanded': expanded, 'is-expandable': expandable }]"
		:bordered="true"
		@click="expandable && $emit('toggle')"
	>
		<div class="od-unit-node__top">
			<span class="od-node-icon" :class="{ 'is-group': level > 1 }">
				<icon-user-group v-if="level === 1" />
				<icon-branch v-else />
			</span>
			<strong :title="unit.title">{{ unit.title }}</strong>
			<a-popover trigger="click" position="rt" :content-class="'od-department-popover'">
				<a-button type="text" shape="circle" size="mini" aria-label="查看组织信息" @click.stop>
					<icon-info-circle />
				</a-button>
				<template #content>
					<div class="od-detail-card">
						<div class="od-detail-card__title">
							<span class="od-node-icon"><icon-user-group /></span>
							<strong>{{ unit.title }}</strong>
							<a-tag size="small">{{ unit.org_type || "部门" }}</a-tag>
						</div>
						<div class="od-detail-card__manager">
							<span>负责人</span>
							<a-avatar :size="24" :image-url="unit.manager_info?.image || undefined"><icon-user /></a-avatar>
							<strong>{{ managerName || "未设置" }}</strong>
						</div>
						<div class="od-detail-card__stats">
							<div><span>在岗</span><strong>{{ unit.employee_count || 0 }} 人</strong></div>
							<div><span>编制</span><strong>{{ unit.staff_quota || "--" }} 人</strong></div>
							<div><span>缺编</span><strong :class="{ 'is-danger': quotaGap > 0 }">{{ quotaLabel }}</strong></div>
						</div>
						<a-button type="text" long @click="$emit('open-detail')">
							查看组织详情 <icon-right />
						</a-button>
					</div>
				</template>
			</a-popover>
		</div>
		<div class="od-unit-node__manager">
			<a-avatar :size="20" :image-url="unit.manager_info?.image || undefined"><icon-user /></a-avatar>
			<span :title="managerName">{{ managerName || "负责人未设置" }}</span>
		</div>
		<div class="od-unit-node__foot">
			<strong>{{ Number(unit.employee_count || 0) }} 人</strong>
			<a-typography-text v-if="subCount" type="secondary">{{ subCount }} 个组</a-typography-text>
			<a-button
				v-if="expandable"
				type="text"
				shape="circle"
				size="mini"
				:aria-label="expanded ? '收起' : '展开'"
				@click.stop="$emit('toggle')"
			>
				<icon-down :class="{ 'is-open': expanded }" />
			</a-button>
		</div>
	</a-card>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	unit: { type: Object, required: true },
	level: { type: Number, default: 1 },
	expanded: Boolean,
	expandable: Boolean,
});

defineEmits(["toggle", "open-detail"]);

const managerName = computed(
	() =>
		props.unit.manager_info?.name ||
		props.unit.head_name ||
		String(props.unit.manager || "").replace(/^.*?(经理|主管|负责人)\s*/, "")
);

const subCount = computed(() => (props.unit.children || []).length);

const quotaGap = computed(() => {
	const quota = Number(props.unit.staff_quota || 0);
	return quota ? quota - Number(props.unit.employee_count || 0) : 0;
});

const quotaLabel = computed(() => {
	if (!Number(props.unit.staff_quota || 0)) return "--";
	if (quotaGap.value > 0) return `${quotaGap.value} 人`;
	if (quotaGap.value < 0) return `超 ${Math.abs(quotaGap.value)} 人`;
	return "0 人";
});
</script>
