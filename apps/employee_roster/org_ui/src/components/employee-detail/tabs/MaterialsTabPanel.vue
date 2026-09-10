<template>
	<div class="arco-emp-archive-tab" v-if="doc">
		<a-spin :loading="loading" style="width: 100%">
			<div class="arco-emp-archive-stack">
				<EmployeeCollapsibleCard title="重要档案存档率" section-key="materials_rate">
					<div class="arco-emp-archive-rate">
						<a-progress
							type="circle"
							:percent="Number(doc.archive_rate?.rate || 0)"
							:width="88"
							:stroke-width="8"
							color="#165DFF"
						/>
						<div class="arco-emp-archive-rate-copy">
							<div class="arco-emp-archive-rate-value">{{ doc.archive_rate?.rate ?? 0 }}%</div>
							<div class="arco-emp-archive-rate-sub">
								已上传必需档案 {{ doc.archive_rate?.done ?? 0 }} / {{ doc.archive_rate?.total ?? 0 }}
							</div>
						</div>
					</div>
				</EmployeeCollapsibleCard>

				<EmployeeCollapsibleCard
					v-for="group in doc.materials || []"
					:key="group.key"
					:title="group.title"
					:section-key="'material_' + (group.key || group.title)"
				>
					<div class="arco-emp-material-list">
						<div v-for="item in group.items" :key="item.key" class="arco-emp-material-row">
							<div class="arco-emp-material-meta">
								<div class="arco-emp-material-name">
									{{ item.label }}
									<a-tag v-if="item.required" size="small" color="orangered" style="margin-left: 6px">必传</a-tag>
									<a-tag v-else size="small" style="margin-left: 6px">选传</a-tag>
								</div>
								<div class="arco-emp-material-status">
									<template v-if="item.file">
										<a :href="item.file" target="_blank" rel="noopener">{{ fileName(item.file) }}</a>
									</template>
									<span v-else class="is-missing">{{ item.required ? "缺失" : "-" }}</span>
								</div>
							</div>
							<a-space v-if="canEdit" :size="4">
								<a-upload
									:show-file-list="false"
									:custom-request="(opt) => onUpload(item, opt)"
									accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.zip"
								>
									<a-button size="mini" type="outline">上传</a-button>
								</a-upload>
								<a-button
									v-if="item.file && !item.from_contracts"
									size="mini"
									status="danger"
									type="text"
									@click="onRemove(item)"
								>
									删除
								</a-button>
								<a-button v-if="item.file" size="mini" type="text" @click="preview(item.file)">预览</a-button>
							</a-space>
						</div>
					</div>
				</EmployeeCollapsibleCard>
			</div>
		</a-spin>
	</div>
</template>

<script setup>
import { Message, Modal } from "@arco-design/web-vue";
import EmployeeCollapsibleCard from "../EmployeeCollapsibleCard.vue";
import { saveEmployeeMaterial, uploadFile } from "../../../api/employeeDetail";
import { errMessage } from "../../../utils/employeeArchive";

const props = defineProps({
	doc: { type: Object, required: true },
	loading: { type: Boolean, default: false },
	canEdit: { type: Boolean, default: false },
	resetToken: { type: Number, default: 0 },
});
const emit = defineEmits(["updated"]);

function fileName(url) {
	try {
		return decodeURIComponent(String(url).split("/").pop() || url);
	} catch (e) {
		return url;
	}
}

function preview(url) {
	window.open(url, "_blank", "noopener");
}

async function onUpload(item, option) {
	const file = option?.fileItem?.file || option?.file;
	if (!file) return;
	try {
		option?.onProgress?.(20);
		const uploaded = await uploadFile(file);
		const url = uploaded?.file_url || uploaded?.file_name || "";
		if (!url) throw new Error("上传失败");
		option?.onProgress?.(80);
		const updated = await saveEmployeeMaterial(props.doc.name, item.key, url);
		Message.success("上传成功");
		emit("updated", updated);
		option?.onSuccess?.(uploaded);
	} catch (e) {
		Message.error(errMessage(e, "上传失败"));
		option?.onError?.(e);
	}
}

function onRemove(item) {
	Modal.confirm({
		title: "删除附件",
		content: `确定删除「${item.label}」吗？`,
		okText: "删除",
		okButtonProps: { status: "danger" },
		async onOk() {
			const updated = await saveEmployeeMaterial(props.doc.name, item.key, "");
			Message.success("已删除");
			emit("updated", updated);
		},
	});
}
</script>
