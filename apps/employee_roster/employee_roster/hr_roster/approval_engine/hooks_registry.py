# Copyright (c) 2026 stillgroup
# License: MIT
"""Business hooks after approval approved."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _


HOOKS: dict[str, str] = {
	# key stored on Approval Form.business_hook → dotted path
	"leave_application": "employee_roster.hr_roster.approval_engine.hooks_registry.create_leave_stub",
	"out_of_office": "employee_roster.hr_roster.approval_engine.hooks_registry.create_out_stub",
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
