<template>
	<div ref="pagesEl" class="ci-doc-pages" :class="{ 'is-final': final }">
		<!-- 隐藏的完整正文用于按当前纸张宽度测量并自动分页 -->
		<div ref="sourceEl" class="ci-doc-body ci-doc-source" aria-hidden="true">
			<div class="ci-doc-flow-block">
				<h2>{{ title || "劳动合同" }}</h2>
			</div>
			<div class="ci-doc-flow-block">
			<p>
				<strong>甲方（用人单位）：</strong>深圳市依然电商科技有限公司
			</p>
			<p>
				<strong>乙方（劳动者）：</strong>
				<span class="ci-doc-var" :class="{ 'is-empty': !form.employeeName }">
					{{ form.employeeName || "（员工姓名）" }}
				</span>
			</p>
			<p>
				证件号码：
				<span class="ci-doc-var" :class="{ 'is-empty': !form.idNumber }">
					{{ form.idNumber || "（证件号码）" }}
				</span>
				；性别：
				<span class="ci-doc-var" :class="{ 'is-empty': !form.gender }">
					{{ form.gender || "（性别）" }}
				</span>
				；岗位：
				<span class="ci-doc-var" :class="{ 'is-empty': !form.designation }">
					{{ form.designation || "（岗位）" }}
				</span>
			</p>
			<p>
				手机号码：
				<span class="ci-doc-var" :class="{ 'is-empty': !form.mobile }">
					{{ form.mobile || "（手机号码）" }}
				</span>
				；现居住地：
				<span class="ci-doc-var" :class="{ 'is-empty': !form.address }">
					{{ form.address || "（现居住地）" }}
				</span>
			</p>
			<p>
				根据《中华人民共和国劳动法》《中华人民共和国劳动合同法》等法律法规，甲乙双方在平等自愿、协商一致的基础上，订立本合同。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>一、合同期限</h4>
			<p>
				本合同期限自
				<span class="ci-doc-var" :class="{ 'is-empty': !startDate }">
					{{ startDate || "#现合同开始日期#" }}
				</span>
				起至
				<span class="ci-doc-var" :class="{ 'is-empty': !endDate }">
					{{ endDate || "#现合同结束日期#" }}
				</span>
				止。签署时间为
				<span class="ci-doc-var" :class="{ 'is-empty': !form.signTime }">
					{{ form.signTime || "#签署时间#" }}
				</span>
				。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>二、工作内容与工作地点</h4>
			<p>
				乙方同意从事
				<span class="ci-doc-var" :class="{ 'is-empty': !form.designation }">
					{{ form.designation || "（岗位）" }}
				</span>
				岗位工作，工作地点由甲方安排并可根据经营需要合理调整。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>三、劳动报酬</h4>
			<p>
				乙方职级薪资为
				<span class="ci-doc-var" :class="{ 'is-empty': !form.salary }">
					{{ form.salary || "#职级薪资#" }}
				</span>
				元/月（税前）
				<template v-if="form.numberText">
					（大写/备注：
					<span class="ci-doc-var">{{ form.numberText }}</span>
					）
				</template>
				。试用期为
				<span class="ci-doc-var" :class="{ 'is-empty': !form.probation }">
					{{ form.probation || "#试用期#" }}
				</span>
				，试用期工资及其他待遇按公司制度执行。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>四、工作时间和休息休假</h4>
			<p>
				甲方依法实行标准工时、综合计算工时或不定时工作制。乙方享有法定节假日、年休假、婚假、产假等休息休假权利，具体按照国家规定及甲方依法制定的制度执行。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>五、社会保险和福利待遇</h4>
			<p>
				甲乙双方依法参加社会保险并缴纳社会保险费。乙方依法享受社会保险待遇，甲方按照公司制度为乙方提供相应福利。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>六、劳动保护、劳动条件和职业危害防护</h4>
			<p>
				甲方为乙方提供符合国家规定的劳动条件、必要的劳动防护用品和安全生产教育。对可能产生职业危害的岗位，甲方依法履行告知、防护和健康检查义务。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>七、规章制度和劳动纪律</h4>
			<p>
				乙方应遵守国家法律法规以及甲方依法制定并公示的规章制度、操作规程和劳动纪律，忠实履行岗位职责，保守甲方商业秘密。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>八、合同的变更</h4>
			<p>
				甲乙双方经协商一致，可以书面变更本合同。因法律法规、客观情况或甲方经营需要发生变化时，双方应依法协商处理。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>九、违约责任</h4>
			<p>
				任何一方违反本合同约定，给对方造成损失的，应依法承担相应责任。涉及培训服务期、竞业限制及保密义务的，按照双方另行签订的协议执行。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>十、经济补偿</h4>
			<p>
				有下列情形之一的，甲方应向乙方支付经济补偿：……补偿标准按国家及深圳市有关规定执行。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>十一、劳动合同的解除、终止</h4>
			<p>
				甲乙双方协商一致，可以解除劳动合同。乙方提前三十日以书面形式通知甲方，可以解除劳动合同。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>十二、劳动争议处理</h4>
			<p>
				因履行本合同发生争议，双方可协商解决；协商不成的，可向深圳市依然电商科技有限公司所在地劳动争议仲裁委员会申请仲裁。
			</p>
			</div>
			<div class="ci-doc-flow-block">
			<h4>十三、其他约定事项</h4>
			<p>
				乙方入职时间为
				<span class="ci-doc-var" :class="{ 'is-empty': !form.joinDateText }">
					{{ form.joinDateText || "#依然入职时间#" }}
				</span>
				。本合同未尽事宜，按法律法规及甲方依法制定的规章制度执行。
			</p>
			<p>本合同一式两份，甲乙双方各执一份，具有同等法律效力。</p>
			</div>
			<div v-if="final" class="ci-doc-flow-block">
			<div v-if="final" class="ci-doc-sign-block">
				<div>
					<p>甲方（盖章）：深圳市依然电商科技有限公司</p>
					<p>日期：______________</p>
				</div>
				<div>
					<p>乙方（签字）：{{ form.employeeName || "______________" }}</p>
					<p>日期：______________</p>
				</div>
			</div>
			</div>
		</div>

		<article v-for="(pageHtml, index) in pages" :key="index" class="ci-doc-paper">
			<div class="ci-doc-watermark" aria-hidden="true">
				<span v-for="i in 24" :key="i">{{ watermarkText }}</span>
			</div>
			<div class="ci-doc-body" v-html="pageHtml" />
			<div class="ci-doc-page-no">第 {{ index + 1 }} 页 / 共 {{ pages.length }} 页</div>
		</article>
	</div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
	form: { type: Object, required: true },
	title: { type: String, default: "" },
	watermarkText: { type: String, default: "合同预览" },
	startDate: { type: String, default: "" },
	endDate: { type: String, default: "" },
	final: { type: Boolean, default: false },
});

const PAGE_CONTENT_HEIGHT = 918;
const pagesEl = ref(null);
const sourceEl = ref(null);
const pages = ref([]);
let resizeObserver = null;
let frameId = 0;

function paginate() {
	const source = sourceEl.value;
	const root = pagesEl.value;
	if (!source || !root) return;

	const paperWidth = Math.min(820, root.clientWidth || 820);
	source.style.width = `${Math.max(320, paperWidth - 116)}px`;

	const nextPages = [];
	let currentBlocks = [];
	let currentHeight = 0;
	for (const block of Array.from(source.children)) {
		const height = Math.ceil(block.getBoundingClientRect().height);
		if (currentBlocks.length && currentHeight + height > PAGE_CONTENT_HEIGHT) {
			nextPages.push(currentBlocks.map((item) => item.outerHTML).join(""));
			currentBlocks = [];
			currentHeight = 0;
		}
		currentBlocks.push(block);
		currentHeight += height;
	}
	if (currentBlocks.length) {
		nextPages.push(currentBlocks.map((item) => item.outerHTML).join(""));
	}
	pages.value = nextPages;
}

function schedulePaginate() {
	cancelAnimationFrame(frameId);
	nextTick(() => {
		frameId = requestAnimationFrame(paginate);
	});
}

watch(
	() => [props.form, props.title, props.startDate, props.endDate, props.final],
	schedulePaginate,
	{ deep: true, immediate: true }
);

onMounted(() => {
	resizeObserver = new ResizeObserver(schedulePaginate);
	if (pagesEl.value) resizeObserver.observe(pagesEl.value);
	if (sourceEl.value) resizeObserver.observe(sourceEl.value);
	schedulePaginate();
});

onBeforeUnmount(() => {
	cancelAnimationFrame(frameId);
	resizeObserver?.disconnect();
});
</script>
