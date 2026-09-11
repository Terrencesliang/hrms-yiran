# Copyright (c) 2026 stillgroup
# License: MIT
"""Business hooks after approval approved."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import getdate, nowdate


HOOKS: dict[str, str] = {
	# key stored on Approval Form.business_hook → dotted path
	"leave_application": "employee_roster.hr_roster.approval_engine.hooks_registry.create_leave_stub",
	"out_of_office": "employee_roster.hr_roster.approval_engine.hooks_registry.create_out_stub",
	"employee_center_onboarding": "employee_roster.hr_roster.approval_engine.hooks_registry.complete_employee_onboarding",
	"employee_center_subsidy": "employee_roster.hr_roster.approval_engine.hooks_registry.complete_employee_subsidy",
	"employee_center_job_change": "employee_roster.hr_roster.approval_engine.hooks_registry.complete_employee_job_change",
	"employee_center_resignation": "employee_roster.hr_roster.approval_engine.hooks_registry.complete_employee_resignation",
	"employee_center_handover": "employee_roster.hr_roster.approval_engine.hooks_registry.complete_employee_handover",
}


def run_business_hook(instance) -> Any:
	hook_key = (instance.business_hook or "").strip()
	if not hook_key:
		# infer from form title for seeded samples
		title = (instance.form_title or "").strip()
		if title == "请假":
			hook_key = "leave_application"
		elif title == "外出":
			hook_key = "out_of_office"
	path = HOOKS.get(hook_key)
	if not path:
		return None
	fn = frappe.get_attr(path)
	return fn(instance)


def _form_data(instance) -> dict:
	raw = instance.form_data_json
	if isinstance(raw, dict):
		return raw
	try:
		return json.loads(raw or "{}")
	except (TypeError, ValueError):
		return {}


def create_leave_stub(instance) -> dict:
	"""Record leave approval outcome on instance; optional Leave Application if DocType exists."""
	data = _form_data(instance)
	note = {
		"hook": "leave_application",
		"from_date": data.get("from_date"),
		"to_date": data.get("to_date"),
		"leave_type": data.get("leave_type"),
		"days": data.get("days"),
		"reason": data.get("reason"),
	}
	frappe.db.set_value(
		"Approval Instance",
		instance.name,
		"hook_result_json",
		json.dumps(note, ensure_ascii=False),
		update_modified=False,
	)
	if frappe.db.exists("DocType", "Leave Application") and instance.applicant_employee:
		# Best-effort create draft leave application
		try:
			if data.get("from_date") and data.get("to_date"):
				la = frappe.get_doc(
					{
						"doctype": "Leave Application",
						"employee": instance.applicant_employee,
						"from_date": data.get("from_date"),
						"to_date": data.get("to_date"),
						"description": data.get("reason") or instance.form_title,
						"leave_type": data.get("leave_type")
						or frappe.db.get_value("Leave Type", {}, "name"),
					}
				)
				# some sites require status/docstatus handling
				la.insert(ignore_permissions=True)
				note["leave_application"] = la.name
				frappe.db.set_value(
					"Approval Instance",
					instance.name,
					"hook_result_json",
					json.dumps(note, ensure_ascii=False),
					update_modified=False,
				)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Leave Application hook")
	return note


def create_out_stub(instance) -> dict:
	data = _form_data(instance)
	note = {
		"hook": "out_of_office",
		"out_date": data.get("out_date"),
		"destination": data.get("destination"),
		"reason": data.get("reason"),
	}
	frappe.db.set_value(
		"Approval Instance",
		instance.name,
		"hook_result_json",
		json.dumps(note, ensure_ascii=False),
		update_modified=False,
	)
	return note


def _save_hook_result(instance, result: dict) -> dict:
	frappe.db.set_value(
		"Approval Instance",
		instance.name,
		"hook_result_json",
		json.dumps(result, ensure_ascii=False),
		update_modified=False,
	)
	return result


def _set_employee_fields(employee_name: str, values: dict) -> list[str]:
	meta = frappe.get_meta("Employee")
	allowed = {field.fieldname for field in meta.fields}
	clean = {key: value for key, value in values.items() if key in allowed and value not in (None, "")}
	if clean:
		frappe.db.set_value("Employee", employee_name, clean)
	return sorted(clean)


def complete_employee_onboarding(instance) -> dict:
	data = _form_data(instance)
	updated = _set_employee_fields(instance.applicant_employee, {
		"gender": {"男": "Male", "女": "Female"}.get(data.get("gender"), data.get("gender")), "date_of_birth": data.get("date_of_birth"),
		"cell_number": data.get("cell_number"), "personal_email": data.get("personal_email"),
		"current_address": data.get("current_address"), "permanent_address": data.get("permanent_address"),
		"hr_id_number": data.get("id_number"), "education": data.get("education"),
		"bank_name": data.get("bank_name"), "bank_ac_no": data.get("bank_ac_no"),
		"person_to_be_contacted": data.get("emergency_contact_name"),
		"emergency_phone_number": data.get("emergency_phone"),
		"hr_attach_id_front": data.get("id_front"), "hr_attach_id_back": data.get("id_back"),
		"hr_attach_photo": data.get("personal_photo"), "hr_attach_resume": data.get("resume"),
	})
	return _save_hook_result(instance, {"hook": "employee_center_onboarding", "employee": instance.applicant_employee, "updated_fields": updated})


def complete_employee_subsidy(instance) -> dict:
	data = _form_data(instance)
	return _save_hook_result(instance, {"hook": "employee_center_subsidy", "total_amount": data.get("total_amount", 0), "detail_count": len(data.get("details") or []), "saved_in": "Approval Instance"})


def complete_employee_job_change(instance) -> dict:
	data = _form_data(instance)
	values = {}
	if data.get("new_department"): values["department"] = data["new_department"]
	if data.get("new_designation"): values["designation"] = data["new_designation"]
	if data.get("new_grade"): values["grade"] = data["new_grade"]
	if data.get("new_salary"): values["ctc"] = data["new_salary"]
	due = not data.get("effective_date") or getdate(data.get("effective_date")) <= getdate(nowdate())
	updated = _set_employee_fields(instance.applicant_employee, values) if due else []
	return _save_hook_result(instance, {"hook": "employee_center_job_change", "employee": instance.applicant_employee, "effective_date": data.get("effective_date"), "business_status": "已生效" if due else "待生效", "updated_fields": updated, "pending_values": {} if due else values, "original_snapshot": data.get("employee_snapshot") or {}})


def apply_due_employee_changes() -> None:
	"""Apply approved future-dated employee changes on their effective date."""
	rows = frappe.get_all(
		"Approval Instance",
		filters={"application_type": "job-change", "status": "已通过"},
		fields=["name", "applicant_employee", "hook_result_json"],
		limit_page_length=1000,
	)
	for row in rows:
		result = frappe.parse_json(row.hook_result_json or "{}")
		if result.get("business_status") != "待生效" or not result.get("effective_date"):
			continue
		if getdate(result["effective_date"]) > getdate(nowdate()):
			continue
		result["updated_fields"] = _set_employee_fields(row.applicant_employee, result.get("pending_values") or {})
		result["pending_values"] = {}
		result["business_status"] = "已生效"
		frappe.db.set_value("Approval Instance", row.name, "hook_result_json", json.dumps(result, ensure_ascii=False), update_modified=False)


def complete_employee_resignation(instance) -> dict:
	data = _form_data(instance)
	# Approval records the planned exit without deleting the employee or marking them Left.
	updated = _set_employee_fields(instance.applicant_employee, {"relieving_date": data.get("planned_resignation_date")})
	return _save_hook_result(instance, {"hook": "employee_center_resignation", "employee": instance.applicant_employee, "business_status": "待离职", "updated_fields": updated})


def complete_employee_handover(instance) -> dict:
	data = _form_data(instance)
	items = data.get("items") or []
	completed = len([row for row in items if row.get("handover_status") == "已完成"])
	return _save_hook_result(instance, {"hook": "employee_center_handover", "completed": completed, "total": len(items), "saved_in": "Approval Instance"})
