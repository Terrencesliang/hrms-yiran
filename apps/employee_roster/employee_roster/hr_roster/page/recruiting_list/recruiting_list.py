# Copyright (c) 2026 stillgroup
# License: MIT
import frappe


STATUS_LABELS = {
	"Accepted": "已入职",
	"Rejected": "已淘汰",
}


@frappe.whitelist()
def get_candidates(
	status: str,
	company: str | None = None,
	job_opening: str | None = None,
	keyword: str | None = None,
	sort_by: str = "modified desc",
	page: int = 1,
	page_size: int = 20,
):
	"""候选人卡片列表（已入职 / 已淘汰）。"""
	if status not in STATUS_LABELS:
		frappe.throw("Invalid status")

	page = max(int(page or 1), 1)
	page_size = min(max(int(page_size or 20), 1), 100)

	filters = [["status", "=", status]]
	if job_opening:
		filters.append(["job_title", "=", job_opening])
	elif company:
		openings = frappe.get_all("Job Opening", filters={"company": company}, pluck="name")
		filters.append(["job_title", "in", openings or ["__none__"]])

	order_by = _normalize_sort(sort_by)
	rows = frappe.get_all(
		"Job Applicant",
		filters=filters,
		fields=[
			"name",
			"applicant_name",
			"email_id",
			"phone_number",
			"job_title",
			"designation",
			"status",
			"source",
			"source_name",
			"applicant_rating",
			"creation",
			"modified",
		],
		order_by=order_by,
		limit_page_length=None,
	)

	if keyword:
		kw = keyword.strip().lower()
		rows = [
			r
			for r in rows
			if kw in (r.applicant_name or "").lower()
			or kw in (r.email_id or "").lower()
			or kw in (r.phone_number or "").lower()
		]

	total = len(rows)
	start = (page - 1) * page_size
	page_rows = rows[start : start + page_size]

	job_labels = _job_labels([r.job_title for r in page_rows if r.job_title])
	candidates = []
	for row in page_rows:
		candidates.append(
			{
				"name": row.name,
				"applicant_name": row.applicant_name,
				"email_id": row.email_id,
				"phone_number": row.phone_number,
				"job_title": row.job_title,
				"job_label": job_labels.get(row.job_title) or row.job_title or "-",
				"designation": row.designation,
				"status": row.status,
				"status_label": STATUS_LABELS.get(row.status, row.status),
				"source": row.source,
				"source_name": row.source_name,
				"applicant_rating": row.applicant_rating or 0,
				"creation": row.creation,
				"modified": row.modified,
			}
		)

	companies = frappe.get_all("Company", pluck="name", order_by="name asc")
	job_openings = frappe.get_all(
		"Job Opening",
		fields=["name", "job_title", "company"],
		order_by="modified desc",
		limit_page_length=200,
	)

	return {
		"candidates": candidates,
		"total": total,
		"page": page,
		"page_size": page_size,
		"page_count": max(1, (total + page_size - 1) // page_size) if total else 1,
		"companies": companies,
		"job_openings": job_openings,
	}


def _normalize_sort(sort_by: str) -> str:
	mapping = {
		"modified desc": "modified desc",
		"modified asc": "modified asc",
		"creation desc": "creation desc",
		"name asc": "applicant_name asc",
	}
	return mapping.get(sort_by or "modified desc", "modified desc")


def _job_labels(job_names):
	if not job_names:
		return {}
	rows = frappe.get_all(
		"Job Opening",
		filters={"name": ["in", list(set(job_names))]},
		fields=["name", "job_title"],
	)
	return {r.name: r.job_title or r.name for r in rows}
