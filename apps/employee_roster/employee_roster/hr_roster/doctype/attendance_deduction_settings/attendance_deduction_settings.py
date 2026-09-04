# Copyright (c) 2026 stillgroup
# License: MIT
import frappe
from frappe.model.document import Document


class AttendanceDeductionSettings(Document):
	pass


def get_attendance_deduction_settings() -> dict:
	return frappe.get_cached_doc("Attendance Deduction Settings").as_dict()
