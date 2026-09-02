# Copyright (c) 2026 stillgroup
# License: MIT
import frappe
from frappe import _
from frappe.model.document import Document


class AttendanceGroup(Document):
	def validate(self):
		seen = set()
		for row in self.members:
			if row.employee in seen:
				frappe.throw(_("Duplicate employee in group: {0}").format(row.employee))
			seen.add(row.employee)
			self._validate_employee_not_in_other_group(row.employee)

	def _validate_employee_not_in_other_group(self, employee: str) -> None:
		filters = {"employee": employee, "parenttype": "Attendance Group"}
		if self.name:
			filters["parent"] = ("!=", self.name)
		others = frappe.get_all("Attendance Group Member", filters=filters, pluck="parent")
		if others:
			frappe.throw(
				_("Employee {0} already belongs to group {1}").format(employee, others[0])
			)


def get_employee_deduction_rule(employee: str) -> str | None:
	rows = frappe.get_all(
		"Attendance Group Member",
		filters={"employee": employee, "parenttype": "Attendance Group"},
		fields=["parent"],
		limit=1,
	)
	if not rows:
		return None
	group = frappe.db.get_value("Attendance Group", rows[0].parent, ["deduction_rule", "is_active"], as_dict=True)
	if not group or not group.is_active:
		return None
	return group.deduction_rule
