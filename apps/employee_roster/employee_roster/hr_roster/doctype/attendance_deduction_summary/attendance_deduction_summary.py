# Copyright (c) 2026 stillgroup
# License: MIT
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_link_to_form

from employee_roster.hr_roster.attendance_deduction.metrics import SALARY_COMPONENT_NAME


class AttendanceDeductionSummary(Document):
	def validate(self):
		if self.start_date and self.end_date and self.start_date > self.end_date:
			frappe.throw(_("Start Date cannot be after End Date"))
		self._validate_overlap()

	def on_submit(self):
		self.create_additional_salary()

	def on_cancel(self):
		if self.additional_salary and frappe.db.exists("Additional Salary", self.additional_salary):
			add_sal = frappe.get_doc("Additional Salary", self.additional_salary)
			if add_sal.docstatus == 1:
				add_sal.cancel()

	def _validate_overlap(self):
		existing = frappe.get_all(
			"Attendance Deduction Summary",
			filters={
				"employee": self.employee,
				"docstatus": 1,
				"end_date": (">=", self.start_date),
				"start_date": ("<=", self.end_date),
				"name": ("!=", self.name),
			},
			pluck="name",
		)
		if existing:
			frappe.throw(
				_("Submitted summary already exists: {0}").format(get_link_to_form("Attendance Deduction Summary", existing[0]))
			)

	def create_additional_salary(self):
		if flt(self.total_deduction) <= 0:
			return
		if not frappe.db.exists("Salary Component", SALARY_COMPONENT_NAME):
			frappe.throw(_("Salary Component '{0}' not found. Run install/migrate.").format(SALARY_COMPONENT_NAME))

		if self.additional_salary and frappe.db.exists("Additional Salary", self.additional_salary):
			add_sal = frappe.get_doc("Additional Salary", self.additional_salary)
			if add_sal.docstatus == 1:
				add_sal.cancel()

		precision = frappe.db.get_single_value("System Settings", "currency_precision") or 2
		add_sal = frappe.get_doc(
			{
				"doctype": "Additional Salary",
				"company": self.company,
				"employee": self.employee,
				"salary_component": SALARY_COMPONENT_NAME,
				"amount": flt(self.total_deduction, precision),
				"payroll_date": self.end_date,
				"overwrite_salary_structure_amount": 0,
				"ref_doctype": "Attendance Deduction Summary",
				"ref_docname": self.name,
			}
		)
		add_sal.insert()
		add_sal.submit()
		self.db_set("additional_salary", add_sal.name)
