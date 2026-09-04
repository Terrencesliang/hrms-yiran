<template>
	<span class="oc-person-cell">
		<span>{{ label }}</span>
		<a-popover
			v-model:popup-visible="visible"
			trigger="click"
			position="br"
			@popup-visible-change="onVisible"
		>
			<a-button type="text" size="mini">
				<template #icon><icon-edit /></template>
			</a-button>
			<template #content>
				<div class="oc-person-pop">
					<a-input-search
						v-model="keyword"
						placeholder="员工姓名/拼音"
						@search="search"
						@input="search(keyword)"
					/>
					<a-spin :loading="loading" style="width: 100%; margin-top: 8px">
						<a-list :data="options" size="small" :bordered="false" :max-height="220">
							<template #item="{ item }">
								<a-list-item style="cursor: pointer" @click="save(item.name)">
									{{ item.employee_name }}
									<template #actions>
										<a-typography-text type="secondary">{{ item.designation || "" }}</a-typography-text>
									</template>
								</a-list-item>
							</template>
							<template #empty>
								<a-empty description="没有匹配的员工" />
							</template>
						</a-list>
					</a-spin>
					<a-button type="text" size="small" @click="save('')">清除</a-button>
				</div>
			</template>
		</a-popover>
	</span>
</template>

<script setup>
import { computed, ref } from "vue";
import { Message } from "@arco-design/web-vue";
import { searchEmployees, updateOrgPerson } from "../api";

const props = defineProps({
	record: { type: Object, required: true },
	role: { type: String, required: true },
	company: String,
});
const emit = defineEmits(["saved"]);

const visible = ref(false);
const keyword = ref("");
const options = ref([]);
const loading = ref(false);

const label = computed(() =>
	props.role === "head" ? props.record.head_name || "" : props.record.supervisor_name || ""
);

function onVisible(open) {
	if (open) search("");
}

async function search(txt) {
	loading.value = true;
	try {
		options.value = (await searchEmployees(txt, props.company)) || [];
	} finally {
		loading.value = false;
	}
}

async function save(employee) {
	await updateOrgPerson(props.record.name, props.role, employee);
	Message.success("已更新");
	visible.value = false;
	emit("saved");
}
</script>
