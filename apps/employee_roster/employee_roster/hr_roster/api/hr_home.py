# Copyright (c) 2026 stillgroup
# License: MIT
"""人事主页 / 数据面板聚合接口（供 OrgUI Arco 页面使用）。"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

import frappe
from frappe.utils import add_months, getdate


def _company_filters(company: str | None) -> list:
	if company:
		return [["company", "=", company]]
	return []


def _quarter_bounds(today: date | None = None) -> tuple[date, date]:
	today = today or getdate()
	q = (today.month - 1) // 3
	start_month = q * 3 + 1
	start = date(today.year, start_month, 1)
	end_month = start_month + 2
	if end_month == 12:
		end = date(today.year, 12, 31)
	else:
		end = date(today.year, end_month + 1, 1)
		end = date.fromordinal(end.toordinal() - 1)
	return start, end


def _year_bounds(today: date | None = None) -> tuple[date, date]:
	today = today or getdate()
	return date(today.year, 1, 1), date(today.year, 12, 31)


def _count_buckets(rows, field: str, *, active_only: bool = True, limit: int | None = 10) -> list[dict]:
	counts: dict[str, int] = defaultdict(int)
	for row in rows:
		if active_only and (row.status or "") != "Active":
			continue
		key = (getattr(row, field, None) or "").strip() or "未填写"
		counts[key] += 1
	items = [{"name": k, "count": v} for k, v in counts.items()]
	items.sort(key=lambda x: (-x["count"], x["name"]))
	if limit:
		items = items[:limit]
	return items


def _age_buckets(rows) -> list[dict]:
	today = getdate()
	buckets = [
		("25 岁以下", 0, 24),
		("25–34 岁", 25, 34),
		("35–44 岁", 35, 44),
		("45–54 岁", 45, 54),
		("55 岁及以上", 55, 200),
		("未填写", -1, -1),
	]
	counts = {label: 0 for label, _, _ in buckets}
	for row in rows:
		if (row.status or "") != "Active":
			continue
		dob = getattr(row, "date_of_birth", None)
		if not dob:
			counts["未填写"] += 1
			continue
		dob = getdate(dob)
		age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
		placed = False
		for label, lo, hi in buckets:
			if lo < 0:
				continue
			if lo <= age <= hi:
				counts[label] += 1
				placed = True
				break
		if not placed:
			counts["未填写"] += 1
	return [{"name": label, "count": counts[label]} for label, _, _ in buckets if counts[label] or label != "未填写"]


def _month_keys(months: int = 12) -> list[str]:
	today = getdate()
	keys = []
	cursor = date(today.year, today.month, 1)
	for _ in range(months):
		keys.append(cursor.strftime("%Y-%m"))
		cursor = add_months(cursor, -1)
	keys.reverse()
	return keys


def _hiring_attrition(rows, months: int = 12) -> dict:
	keys = _month_keys(months)
	hire = {k: 0 for k in keys}
	exit_ = {k: 0 for k in keys}
	for row in rows:
		if row.date_of_joining:
			k = getdate(row.date_of_joining).strftime("%Y-%m")
			if k in hire:
				hire[k] += 1
		rel = getattr(row, "relieving_date", None)
		if rel:
			k = getdate(rel).strftime("%Y-%m")
			if k in exit_:
				exit_[k] += 1
	return {
		"labels": keys,
		"hiring": [hire[k] for k in keys],
		"attrition": [exit_[k] for k in keys],
	}


def _load_employees(company: str | None = None):
	fields = [
		"name",
		"employee_name",
		"status",
		"department",
		"designation",
		"employment_type",
		"branch",
		"grade",
		"gender",
		"date_of_joining",
		"relieving_date",
		"date_of_birth",
		"image",
		"company",
	]
	return frappe.db.get_all(
		"Employee",
		fields=fields,
		filters=_company_filters(company),
		limit_page_length=None,
	)


def _stats(rows) -> dict:
	today = getdate()
	q_start, q_end = _quarter_bounds(today)
	y_start, y_end = _year_bounds(today)

	active = 0
	left = 0
	inactive = 0
	join_q = 0
	leave_q = 0
	hire_y = 0
	exit_y = 0

	for row in rows:
		status = row.status or ""
		if status == "Active":
			active += 1
		elif status == "Left":
			left += 1
		elif status == "Inactive":
			inactive += 1

		if row.date_of_joining:
			d = getdate(row.date_of_joining)
			if q_start <= d <= q_end:
				join_q += 1
			if y_start <= d <= y_end:
				hire_y += 1

		rel = getattr(row, "relieving_date", None)
		if rel:
			d = getdate(rel)
			if q_start <= d <= q_end:
				leave_q += 1
			if y_start <= d <= y_end:
				exit_y += 1

	return {
		"total": len(rows),
		"active": active,
		"left": left,
		"inactive": inactive,
		"joining_quarter": join_q,
		"relieving_quarter": leave_q,
		"hires_year": hire_y,
		"exits_year": exit_y,
	}


def _recent_joiners(rows, limit: int = 8) -> list[dict]:
	active = [r for r in rows if (r.status or "") == "Active" and r.date_of_joining]
	active.sort(key=lambda r: getdate(r.date_of_joining), reverse=True)
	out = []
	for r in active[:limit]:
		out.append(
			{
				"name": r.name,
				"employee_name": r.employee_name,
				"department": r.department or "",
				"designation": r.designation or "",
				"date_of_joining": str(getdate(r.date_of_joining)),
				"image": r.image or "",
			}
		)
	return out


def _companies() -> list[str]:
	return frappe.get_all("Company", pluck="name", order_by="name asc") or []


def _prev_month_bounds(today=None) -> tuple[date, date]:
	today = today or getdate()
	first_this = date(today.year, today.month, 1)
	last_prev = date.fromordinal(first_this.toordinal() - 1)
	first_prev = date(last_prev.year, last_prev.month, 1)
	return first_prev, last_prev


def _prev_year_ytd_bounds(today=None) -> tuple[date, date]:
	today = today or getdate()
	return date(today.year - 1, 1, 1), date(today.year - 1, today.month, today.day)


def _workplace_metric_cards(rows, ha: dict) -> list[dict]:
	"""人事主页 KPI：含环比绝对值 + 百分比 + sparkline。"""
	stats = _stats(rows)
	today = getdate()
	pq_start, pq_end = _prev_quarter_bounds(today)
	pm_start, pm_end = _prev_month_bounds(today)
	py_start, py_end = _prev_year_ytd_bounds(today)

	prev_join_q = 0
	prev_leave_q = 0
	join_lm = 0
	leave_lm = 0
	hire_ytd_prev = 0

	for row in rows:
		if row.date_of_joining:
			d = getdate(row.date_of_joining)
			if pq_start <= d <= pq_end:
				prev_join_q += 1
			if pm_start <= d <= pm_end:
				join_lm += 1
			if py_start <= d <= py_end:
				hire_ytd_prev += 1
		rel = getattr(row, "relieving_date", None)
		if rel:
			d = getdate(rel)
			if pq_start <= d <= pq_end:
				prev_leave_q += 1
			if pm_start <= d <= pm_end:
				leave_lm += 1

	hiring = ha.get("hiring") or []
	attrition = ha.get("attrition") or []
	net = [
		max(0, (hiring[i] if i < len(hiring) else 0) - (attrition[i] if i < len(attrition) else 0))
		for i in range(len(hiring))
	]
	running = []
	acc = max(stats["active"] - sum(net), 0)
	for n in net:
		acc += n
		running.append(acc)

	net_lm = join_lm - leave_lm
	prev_active = max(stats["active"] - net_lm, 0)

	return [
		{
			"key": "active",
			"title": "在职员工",
			"value": stats["active"],
			"suffix": "人",
			"delta_abs": net_lm,
			"delta_label": "较上月",
			"delta_pct": _pct_change(stats["active"], prev_active),
			"icon": "user-group",
			"color": "#165DFF",
			"chart": "line",
			"series": running or hiring,
			"route": ["List", "Employee"],
		},
		{
			"key": "join_q",
			"title": "本季入职",
			"value": stats["joining_quarter"],
			"suffix": "人",
			"delta_abs": stats["joining_quarter"] - prev_join_q,
			"delta_label": "较上季",
			"delta_pct": _pct_change(stats["joining_quarter"], prev_join_q),
			"icon": "user-add",
			"color": "#00B42A",
			"chart": "bar",
			"series": hiring,
		},
		{
			"key": "leave_q",
			"title": "本季离职",
			"value": stats["relieving_quarter"],
			"suffix": "人",
			"delta_abs": stats["relieving_quarter"] - prev_leave_q,
			"delta_label": "较上季",
			"delta_pct": _pct_change(stats["relieving_quarter"], prev_leave_q),
			"icon": "export",
			"color": "#722ED1",
			"chart": "line",
			"series": attrition,
		},
		{
			"key": "hire_y",
			"title": "本年入职",
			"value": stats["hires_year"],
			"suffix": "人",
			"delta_abs": stats["hires_year"] - hire_ytd_prev,
			"delta_label": "较去年",
			"delta_pct": _pct_change(stats["hires_year"], hire_ytd_prev),
			"icon": "calendar",
			"color": "#FF7D00",
			"chart": "line",
			"series": hiring,
			"route": ["hr-dashboard"],
		},
	]


@frappe.whitelist()
def get_hr_workplace(company: str | None = None) -> dict:
	"""人事主页（Arco Pro Workplace 风格）数据。"""
	rows = _load_employees(company)
	ha = _hiring_attrition(rows, months=12)
	user = frappe.session.user
	full_name = frappe.db.get_value("User", user, "full_name") or user
	today = getdate()
	weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
	return {
		"user": {"name": user, "full_name": full_name},
		"company": company or "",
		"companies": _companies(),
		"stats": _stats(rows),
		"metric_cards": _workplace_metric_cards(rows, ha),
		"by_department": _count_buckets(rows, "department", limit=12),
		"recent_joiners": _recent_joiners(rows, limit=6),
		"dept_ranking": _dept_ranking(rows, limit=8),
		"hero": {
			"date_label": today.strftime("%Y年%m月%d日"),
			"weekday": weekdays[today.weekday()],
			"quote": "优秀的组织，源于每一个人的成长。",
		},
		"quick_links": [
			{
				"label": "员工花名册",
				"desc": "查看和管理全员信息",
				"route": ["List", "Employee"],
				"icon": "IconUserGroup",
			},
			{
				"label": "组织架构",
				"desc": "树形查看部门与岗位",
				"route": ["orgchart"],
				"icon": "IconMindMapping",
			},
			{
				"label": "数据看板",
				"desc": "查看 HR 指标与趋势",
				"route": ["hr-dashboard"],
				"icon": "IconDashboard",
			},
			{
				"label": "员工档案库",
				"desc": "查阅合同与档案材料",
				"route": ["employee-archive"],
				"icon": "IconFolder",
			},
			{
				"label": "考勤管理",
				"desc": "排班打卡与异常处理",
				"route": ["List", "Employee Checkin"],
				"icon": "IconCalendar",
			},
			{
				"label": "招聘管理",
				"desc": "候选人流程与岗位管理",
				"route": ["List", "Job Applicant"],
				"icon": "IconUserAdd",
			},
		],
	}


def _pct_change(current: int, previous: int) -> float:
	if previous <= 0:
		return 100.0 if current > 0 else 0.0
	return round((current - previous) * 100.0 / previous, 2)


def _prev_quarter_bounds(today=None) -> tuple[date, date]:
	today = today or getdate()
	q_start, _ = _quarter_bounds(today)
	prev_end = date.fromordinal(q_start.toordinal() - 1)
	return _quarter_bounds(prev_end)


def _metric_cards(rows, ha: dict) -> list[dict]:
	"""Top KPI cards with sparkline + vs last quarter delta."""
	stats = _stats(rows)
	today = getdate()
	pq_start, pq_end = _prev_quarter_bounds(today)

	prev_join = 0
	prev_leave = 0
	for row in rows:
		if row.date_of_joining:
			d = getdate(row.date_of_joining)
			if pq_start <= d <= pq_end:
				prev_join += 1
		rel = getattr(row, "relieving_date", None)
		if rel:
			d = getdate(rel)
			if pq_start <= d <= pq_end:
				prev_leave += 1

	hiring = ha.get("hiring") or []
	attrition = ha.get("attrition") or []
	net = [max(0, (hiring[i] if i < len(hiring) else 0) - (attrition[i] if i < len(attrition) else 0)) for i in range(len(hiring))]
	# Approximate headcount sparkline: cumulative net from series (shifted positive)
	running = []
	acc = max(stats["active"] - sum(net), 0)
	for n in net:
		acc += n
		running.append(acc)

	gender = _count_buckets(rows, "gender", limit=6)
	return [
		{
			"key": "active",
			"title": "在职员工",
			"value": stats["active"],
			"delta": _pct_change(stats["joining_quarter"], prev_join),
			"delta_label": "较上季入职",
			"chart": "line",
			"color": "#165DFF",
			"series": running or hiring,
		},
		{
			"key": "hires_year",
			"title": "本年入职",
			"value": stats["hires_year"],
			"delta": _pct_change(stats["joining_quarter"], prev_join),
			"delta_label": "较上季",
			"chart": "bar",
			"color": "#14C9C9",
			"series": hiring,
		},
		{
			"key": "exits_year",
			"title": "本年离职",
			"value": stats["exits_year"],
			"delta": _pct_change(stats["relieving_quarter"], prev_leave),
			"delta_label": "较上季",
			"chart": "line",
			"color": "#722ED1",
			"series": attrition,
		},
		{
			"key": "structure",
			"title": "人员结构",
			"value": stats["active"],
			"delta": _pct_change(stats["joining_quarter"] - stats["relieving_quarter"], 1),
			"delta_label": "本季净增",
			"chart": "pie",
			"color": "#165DFF",
			"pie": gender,
		},
	]


def _dept_ranking(rows, limit: int = 8) -> list[dict]:
	depts = _count_buckets(rows, "department", limit=limit)
	# Approximate "clicks" as designation diversity * count for a second column feel
	desig_by_dept: dict[str, set] = defaultdict(set)
	for row in rows:
		if (row.status or "") != "Active":
			continue
		dept = (row.department or "").strip() or "未填写"
		desig_by_dept[dept].add((row.designation or "").strip() or "未填写")
	out = []
	for idx, item in enumerate(depts, start=1):
		out.append(
			{
				"rank": idx,
				"name": item["name"],
				"headcount": item["count"],
				"roles": len(desig_by_dept.get(item["name"]) or []),
			}
		)
	return out


def _month_short_labels(labels: list[str]) -> list[str]:
	out = []
	for lab in labels:
		parts = str(lab).split("-")
		out.append(f"{int(parts[1])}月" if len(parts) == 2 else lab)
	return out


@frappe.whitelist()
def get_hr_dashboard(company: str | None = None) -> dict:
	"""人事数据面板聚合（Arco Pro 分析页）。"""
	rows = _load_employees(company)
	ha = _hiring_attrition(rows, months=12)
	labels = ha.get("labels") or []
	hiring = ha.get("hiring") or []
	attrition = ha.get("attrition") or []
	net = [hiring[i] - attrition[i] for i in range(len(labels))]
	return {
		"company": company or "",
		"companies": _companies(),
		"stats": _stats(rows),
		"metric_cards": _metric_cards(rows, ha),
		"by_department": _count_buckets(rows, "department", limit=12),
		"by_gender": _count_buckets(rows, "gender", limit=8),
		"by_employment_type": _count_buckets(rows, "employment_type", limit=10),
		"by_grade": _count_buckets(rows, "grade", limit=10),
		"by_branch": _count_buckets(rows, "branch", limit=10),
		"by_designation": _count_buckets(rows, "designation", limit=10),
		"by_age": _age_buckets(rows),
		"hiring_attrition": ha,
		"dept_ranking": _dept_ranking(rows),
		"publish_ratio": {
			"labels": _month_short_labels(labels),
			"hiring": hiring,
			"attrition": attrition,
		},
		"period_analysis": {
			"labels": _month_short_labels(labels),
			"hiring": hiring,
			"attrition": attrition,
			"net": net,
		},
	}
