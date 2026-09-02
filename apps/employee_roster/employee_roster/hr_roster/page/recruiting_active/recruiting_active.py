# Copyright (c) 2026 stillgroup
# License: MIT
import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count


RECRUITING_STATUSES = ("Open", "Replied", "Shortlisted", "Hold")


@frappe.whitelist()
def get_recruiting_pipeline(
    company: str | None = None,
    job_opening: str | None = None,
    keyword: str | None = None,
):
    """招聘中候选人看板：初筛 / 面试 / 录用阶段统计 + 列表。"""
    filters = [["status", "in", list(RECRUITING_STATUSES)]]
    if job_opening:
        filters.append(["job_title", "=", job_opening])
    elif company:
        openings = frappe.get_all("Job Opening", filters={"company": company}, pluck="name")
        filters.append(["job_title", "in", openings or ["__none__"]])

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
            "applicant_rating",
            "creation",
        ],
        order_by="modified desc",
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

    applicant_names = [r.name for r in rows]
    interview_map = _interview_summary(applicant_names)
    offer_map = _offer_summary(applicant_names)

    pipeline = {
        "screening": {
            "label": "初筛",
            "items": [
                {"key": "pending", "label": "待初筛", "count": _count_status(rows, {"Open"})},
                {"key": "passed", "label": "初筛通过", "count": _count_status(rows, {"Replied"})},
            ],
        },
        "interview": {
            "label": "面试",
            "items": [
                {"key": "scheduled", "label": "已安排面试", "count": interview_map.get("Pending", 0)},
                {"key": "done", "label": "已面试", "count": interview_map.get("Under Review", 0)},
                {"key": "cleared", "label": "面试通过", "count": interview_map.get("Cleared", 0)},
            ],
        },
        "offer": {
            "label": "录用",
            "items": [
                {"key": "shortlisted", "label": "拟录用", "count": _count_status(rows, {"Shortlisted"})},
                {"key": "offered", "label": "已发 Offer", "count": offer_map.get("Awaiting Response", 0)},
                {"key": "pending_join", "label": "待入职", "count": offer_map.get("Accepted", 0)},
            ],
        },
    }

    candidates = []
    for row in rows:
        candidates.append(
            {
                "name": row.name,
                "applicant_name": row.applicant_name,
                "email_id": row.email_id,
                "phone_number": row.phone_number,
                "job_title": row.job_title,
                "designation": row.designation,
                "status": row.status,
                "status_label": _status_label(row.status),
                "applicant_rating": row.applicant_rating or 0,
                "creation": row.creation,
                "stage": _stage_for_status(row.status),
            }
        )

    companies = frappe.get_all("Company", pluck="name", order_by="name asc")
    job_openings = frappe.get_all(
        "Job Opening",
        filters={"status": "Open"},
        fields=["name", "job_title", "company"],
        order_by="modified desc",
        limit_page_length=200,
    )

    return {
        "pipeline": pipeline,
        "candidates": candidates,
        "total": len(candidates),
        "companies": companies,
        "job_openings": job_openings,
    }


def _count_status(rows, statuses):
    return sum(1 for r in rows if r.status in statuses)


def _status_label(status):
    return {
        "Open": "待初筛",
        "Replied": "初筛通过",
        "Shortlisted": "拟录用",
        "Hold": "暂缓",
    }.get(status, status)


def _stage_for_status(status):
    if status in ("Open", "Replied", "Hold"):
        return "screening"
    if status == "Shortlisted":
        return "offer"
    return "screening"


def _interview_summary(applicant_names):
    if not applicant_names:
        return {}
    Interview = DocType("Interview")
    rows = (
        frappe.qb.from_(Interview)
        .select(Interview.status, Count(Interview.name))
        .where(Interview.job_applicant.isin(applicant_names))
        .where(Interview.docstatus != 2)
        .groupby(Interview.status)
    ).run()
    return {status: count for status, count in rows}


def _offer_summary(applicant_names):
    if not applicant_names:
        return {}
    rows = frappe.get_all(
        "Job Offer",
        filters={"job_applicant": ["in", applicant_names], "docstatus": ["!=", 2]},
        fields=["status"],
        limit_page_length=None,
    )
    summary = {}
    for row in rows:
        summary[row.status] = summary.get(row.status, 0) + 1
    return summary
