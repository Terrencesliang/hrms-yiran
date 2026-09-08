export const EMPLOYEE_STATUS_MAP = {
	Active: { label: "在职", color: "green" },
	Inactive: { label: "停用", color: "orangered" },
	Suspended: { label: "停职", color: "red" },
	Left: { label: "离职", color: "gray" },
};

export const EMPLOYMENT_TYPE_LABELS = {
	"Full-time": "全职",
	Intern: "实习",
	Probation: "试用期",
	Contract: "合同工",
	"Part-time": "兼职",
};

export function dash(value) {
	if (value === 0) return value;
	if (value == null || value === "") return "—";
	return value;
}

export function statusLabel(status) {
	return EMPLOYEE_STATUS_MAP[status]?.label || dash(status);
}

export function statusColor(status) {
	return EMPLOYEE_STATUS_MAP[status]?.color || "gray";
}

export function employmentTypeLabel(type) {
	return EMPLOYMENT_TYPE_LABELS[type] || dash(type);
}

export function probationStatusText(state) {
	if (state?.employment_type === "Probation") {
		const remain = Number(state.probation_days_remaining);
		if (Number.isFinite(remain) && remain > 0) {
			return `进行中（剩余 ${remain} 天）`;
		}
		return "进行中";
	}
	if (state?.employment_type === "Full-time" && state?.status === "Active") {
		return "已转正";
	}
	return "—";
}

export function joinDateLine(state) {
	const date = dash(state?.date_of_joining);
	const days = Number(state?.tenure_days);
	if (!Number.isFinite(days) || date === "—") return date;
	return `${date}（入职第 ${days} 天）`;
}

export function workCityLine(state) {
	return dash(state?.hr_work_city || state?.branch);
}

export function departmentLine(state) {
	const dept = state?.department;
	const company = state?.company;
	if (dept && company) return `${dept} - ${company}`;
	return dash(dept || company);
}

export function headerMetaLine(state) {
	const parts = [dash(state?.employee_number), dash(state?.designation), departmentLine(state)].filter(
		(v) => v !== "—"
	);
	return parts.length ? parts.join(" ｜ ") : "—";
}

export function headerCompanyLine(state) {
	const parts = [dash(state?.company), workCityLine(state)].filter((v) => v !== "—");
	return parts.length ? parts.join(" ｜ ") : "—";
}
