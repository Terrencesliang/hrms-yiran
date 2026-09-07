<template>
	<div class="ci-doc-paper" :class="{ 'is-final': final }">
		<div class="ci-doc-watermark" aria-hidden="true">
			<span v-for="i in 24" :key="i">{{ watermarkText }}</span>
		</div>
		<div class="ci-doc-body">
			<h2>{{ title || "劳动合同" }}</h2>
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
			<h4>二、工作内容与工作地点</h4>
			<p>
				乙方同意从事
				<span class="ci-doc-var" :class="{ 'is-empty': !form.designation }">
					{{ form.designation || "（岗位）" }}
				</span>
				岗位工作，工作地点由甲方安排并可根据经营需要合理调整。
			</p>
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
			<h4>十、经济补偿</h4>
			<p>
				有下列情形之一的，甲方应向乙方支付经济补偿：……补偿标准按国家及深圳市有关规定执行。
			</p>
			<h4>十一、劳动合同的解除、终止</h4>
			<p>
				甲乙双方协商一致，可以解除劳动合同。乙方提前三十日以书面形式通知甲方，可以解除劳动合同。
			</p>
			<h4>十二、劳动争议处理</h4>
			<p>
				因履行本合同发生争议，双方可协商解决；协商不成的，可向深圳市依然电商科技有限公司所在地劳动争议仲裁委员会申请仲裁。
			</p>
			<h4>十三、其他约定事项</h4>
			<p>
				乙方入职时间为
				<span class="ci-doc-var" :class="{ 'is-empty': !form.joinDateText }">
					{{ form.joinDateText || "#依然入职时间#" }}
				</span>
				。本合同未尽事宜，按法律法规及甲方依法制定的规章制度执行。
			</p>
			<p>本合同一式两份，甲乙双方各执一份，具有同等法律效力。</p>
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
</template>

<script setup>
defineProps({
	form: { type: Object, required: true },
	title: { type: String, default: "" },
	watermarkText: { type: String, default: "合同预览" },
	startDate: { type: String, default: "" },
	endDate: { type: String, default: "" },
	final: { type: Boolean, default: false },
});
</script>
