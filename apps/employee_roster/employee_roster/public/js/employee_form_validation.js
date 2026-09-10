// Copyright (c) 2026 stillgroup
// License: MIT
/** Employee 表单的纯校验规则；保持无 Frappe 依赖，便于浏览器和 Node 测试复用。 */
(function (root, factory) {
	const api = factory();
	if (typeof module === "object" && module.exports) {
		module.exports = api;
	}
	root.EmployeeFormValidation = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
	const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	const PHONE_PATTERN = /^\+?[0-9\s()\-]{6,24}$/;
	const CN_ID_BODY_PATTERN = /^\d{17}[\dXx]$/;
	const CN_ID_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2];
	const CN_ID_CHECK_MAP = "10X98765432";

	function value(doc, fieldname) {
		return String(doc?.[fieldname] || "").trim();
	}

	function isAfter(left, right) {
		return Boolean(left && right && left > right);
	}

	function validateChineseIdNumber(raw, options = {}) {
		const id = String(raw || "")
			.trim()
			.toUpperCase();
		if (!id) return { ok: false, message: "请填写身份证号码" };
		if (!CN_ID_BODY_PATTERN.test(id)) {
			return { ok: false, message: "身份证号码须为 18 位（17 位数字 + 校验位数字或 X）" };
		}

		const y = Number(id.slice(6, 10));
		const m = Number(id.slice(10, 12));
		const d = Number(id.slice(12, 14));
		const birthIso = `${String(y).padStart(4, "0")}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
		const birthDate = new Date(`${birthIso}T00:00:00`);
		if (
			!Number.isFinite(y) ||
			m < 1 ||
			m > 12 ||
			d < 1 ||
			d > 31 ||
			Number.isNaN(birthDate.getTime()) ||
			birthDate.getFullYear() !== y ||
			birthDate.getMonth() + 1 !== m ||
			birthDate.getDate() !== d
		) {
			return { ok: false, message: "身份证号码中的出生日期无效" };
		}

		const today = options.today || new Date().toISOString().slice(0, 10);
		if (birthIso > today) {
			return { ok: false, message: "身份证号码中的出生日期不能晚于今天" };
		}

		let sum = 0;
		for (let i = 0; i < 17; i += 1) sum += Number(id[i]) * CN_ID_WEIGHTS[i];
		if (CN_ID_CHECK_MAP[sum % 11] !== id[17]) {
			return { ok: false, message: "身份证号码校验位不正确，请按国家标准核对" };
		}

		const dob = String(options.dateOfBirth || "").trim().slice(0, 10);
		if (dob && dob.replace(/-/g, "") !== id.slice(6, 14)) {
			return { ok: false, message: "出生日期与身份证号码不一致" };
		}

		return { ok: true, birth: birthIso, normalized: id };
	}

	function validateEmployee(doc, options = {}) {
		const errors = [];
		const add = (fieldname, message) => errors.push({ fieldname, message });
		const today = options.today || new Date().toISOString().slice(0, 10);
		const birthDate = value(doc, "date_of_birth");
		const joiningDate = value(doc, "date_of_joining");

		if (birthDate && isAfter(birthDate, today)) {
			add("date_of_birth", "出生日期不能晚于今天");
		}
		if (birthDate && joiningDate && isAfter(birthDate, joiningDate)) {
			add("date_of_joining", "入职日期不能早于出生日期");
		}

		[
			["scheduled_confirmation_date", "预计转正日期"],
			["final_confirmation_date", "转正日期"],
			["relieving_date", "离职日期"],
			["date_of_retirement", "退休日期"],
		].forEach(([fieldname, label]) => {
			const date = value(doc, fieldname);
			if (joiningDate && date && isAfter(joiningDate, date)) {
				add(fieldname, `${label}不能早于入职日期`);
			}
		});

		const workStartDate = value(doc, "hr_work_start_date");
		if (birthDate && workStartDate && isAfter(birthDate, workStartDate)) {
			add("hr_work_start_date", "参加工作时间不能早于出生日期");
		}

		const contractFrom = value(doc, "hr_contract_effective_from");
		const contractUntil = value(doc, "hr_contract_expire_date");
		if (contractFrom && contractUntil && isAfter(contractFrom, contractUntil)) {
			add("hr_contract_expire_date", "合同到期日期不能早于合同开始日期");
		}

		["company_email", "personal_email"].forEach((fieldname) => {
			const email = value(doc, fieldname);
			if (email && !EMAIL_PATTERN.test(email)) {
				add(fieldname, `${fieldname === "company_email" ? "公司邮箱" : "个人邮箱"}格式不正确`);
			}
		});

		[
			["cell_number", "手机号"],
			["emergency_phone_number", "紧急联系电话"],
		].forEach(([fieldname, label]) => {
			const phone = value(doc, fieldname);
			if (phone && !PHONE_PATTERN.test(phone)) {
				add(fieldname, `${label}格式不正确`);
			}
		});

		const idNumber = value(doc, "hr_id_number");
		if (value(doc, "hr_id_type") === "身份证" && idNumber) {
			const result = validateChineseIdNumber(idNumber, {
				today,
				dateOfBirth: birthDate,
			});
			if (!result.ok) {
				add("hr_id_number", result.message);
			}
		}

		return errors;
	}

	return { validateEmployee, validateChineseIdNumber };
});
