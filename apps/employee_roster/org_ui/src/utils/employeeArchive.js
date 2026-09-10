/** 员工档案 / 概况预览空值统一显示为 "-"。 */
export function blank(value) {
	if (value === 0) return value;
	if (value == null || value === "") return "-";
	return value;
}

export function formatDate(value) {
	if (!value) return "";
	const raw = String(value).trim();
	const iso = raw.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
	if (iso) {
		return `${iso[1]}-${String(iso[2]).padStart(2, "0")}-${String(iso[3]).padStart(2, "0")}`;
	}
	return raw.slice(0, 10);
}

export function dateRange(from, to, ongoing = "至今") {
	const a = formatDate(from);
	const b = formatDate(to);
	if (!a && !b) return "-";
	if (a && !b) return `${a} ～ ${ongoing}`;
	if (!a && b) return `～ ${b}`;
	return `${a} ～ ${b}`;
}

export function yearsLabel(years) {
	if (years == null || years === "") return "-";
	const n = Number(years);
	if (!Number.isFinite(n)) return blank(years);
	return `${n} 年`;
}

export const GENDER_OPTIONS = [
	{ label: "男", value: "男" },
	{ label: "女", value: "女" },
	{ label: "Male", value: "Male" },
	{ label: "Female", value: "Female" },
];

export const STATUS_OPTIONS = [
	{ label: "在职", value: "Active" },
	{ label: "停用", value: "Inactive" },
	{ label: "停职", value: "Suspended" },
	{ label: "已离职", value: "Left" },
];

export const EMPLOYMENT_TYPE_OPTIONS = [
	{ label: "全职", value: "Full-time" },
	{ label: "兼职", value: "Part-time" },
	{ label: "实习", value: "Intern" },
	{ label: "试用期", value: "Probation" },
	{ label: "合同工", value: "Contract" },
];

export const ID_TYPE_OPTIONS = ["身份证", "护照", "港澳通行证", "台胞证", "其他"].map((v) => ({
	label: v,
	value: v,
}));

/** 中国居民身份证（GB 11643）：18 位、出生日期合法、校验位正确。 */
export function validateChineseIdNumber(raw, options = {}) {
	const id = String(raw || "")
		.trim()
		.toUpperCase();
	if (!id) return { ok: false, message: "请填写身份证号码" };
	if (!/^\d{17}[\dX]$/.test(id)) {
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

	const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2];
	const checkMap = "10X98765432";
	let sum = 0;
	for (let i = 0; i < 17; i += 1) sum += Number(id[i]) * weights[i];
	if (checkMap[sum % 11] !== id[17]) {
		return { ok: false, message: "身份证号码校验位不正确，请按国家标准核对" };
	}

	const dob = String(options.dateOfBirth || "").trim().slice(0, 10);
	if (dob && dob.replace(/-/g, "") !== id.slice(6, 14)) {
		return { ok: false, message: "出生日期与身份证号码不一致" };
	}

	const genderCode = Number(id[16]);
	const genderFromId = genderCode % 2 === 1 ? "男" : "女";
	return { ok: true, birth: birthIso, gender: genderFromId, normalized: id };
}

export const PROBATION_OPTIONS = ["无试用期", "1", "2", "3", "6"].map((v) => ({
	label: v === "无试用期" ? v : `${v} 个月`,
	value: v,
}));

export const CONTRACT_TYPE_OPTIONS = [
	"固定期限劳动合同",
	"无固定期限劳动合同",
	"实习协议",
	"劳务合同",
	"劳务派遣",
	"退休返聘",
	"其他",
].map((v) => ({ label: v, value: v }));

export function genderLabel(value) {
	if (!value) return "-";
	const map = { Male: "男", Female: "女", Other: "其他" };
	return map[value] || value;
}

export function statusLabel(value) {
	const map = { Active: "在职", Inactive: "停用", Suspended: "停职", Left: "已离职" };
	return map[value] || blank(value);
}

export function employmentTypeLabel(value) {
	const map = {
		"Full-time": "全职",
		"Part-time": "兼职",
		Intern: "实习",
		Probation: "试用期",
		Contract: "合同工",
	};
	return map[value] || blank(value);
}

export function errMessage(e, fallback = "操作失败") {
	const fromServer = parseFrappeServerMessages(e);
	let raw =
		fromServer ||
		e?.message ||
		(typeof e === "string" ? e : "") ||
		fallback;
	raw = String(raw)
		.replace(/<[^>]+>/g, " ")
		.replace(/&nbsp;/g, " ")
		.replace(/\\n/g, "\n")
		.replace(/\s+/g, " ")
		.trim();

	// 不要把整段 Traceback 甩给用户
	if (/Traceback \(most recent call last\)/i.test(raw)) {
		const lines = raw
			.split(/\n|(?=File ")/)
			.map((s) => s.trim())
			.filter(Boolean);
		const lastUseful =
			[...lines].reverse().find((line) => line && !/^File "/.test(line) && !/^Traceback/.test(line)) ||
			"";
		raw = lastUseful || fallback;
	}

	return (raw || fallback).slice(0, 240);
}

function parseFrappeServerMessages(e) {
	const raw = e?._server_messages || e?.responseJSON?._server_messages;
	if (!raw) return "";
	try {
		const list = typeof raw === "string" ? JSON.parse(raw) : raw;
		const parts = (Array.isArray(list) ? list : [list])
			.map((item) => {
				try {
					const obj = typeof item === "string" ? JSON.parse(item) : item;
					return obj?.message || obj?.title || "";
				} catch {
					return typeof item === "string" ? item : "";
				}
			})
			.filter(Boolean);
		return parts.join("；");
	} catch {
		return "";
	}
}
