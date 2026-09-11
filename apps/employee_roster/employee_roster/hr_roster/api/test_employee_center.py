# Copyright (c) 2026 stillgroup
# License: MIT

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from employee_roster.hr_roster.api import employee_center
from employee_roster.hr_roster.approval_engine import runtime


class TestEmployeeCenterFlow(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.company = frappe.db.get_value("Company", {}, "name")
		existing = frappe.db.get_value("Employee", {"user_id": "Administrator"}, "name")
		self.created_employee = not bool(existing)
		self.employee = frappe.get_doc("Employee", existing) if existing else frappe.get_doc({
			"doctype": "Employee", "first_name": "员工中心测试", "gender": "Female",
			"date_of_birth": "1995-01-01", "date_of_joining": nowdate(),
			"company": self.company, "status": "Active", "user_id": "Administrator",
		}).insert(ignore_permissions=True)
		self.instances = []
		self.files = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for name in self.instances:
			frappe.db.delete("Approval Task", {"instance": name})
			frappe.db.delete("Approval Instance", {"name": name})
		for name in self.files:
			if frappe.db.exists("File", name):
				frappe.delete_doc("File", name, force=True, ignore_permissions=True)
		if self.created_employee and frappe.db.exists("Employee", self.employee.name):
			frappe.db.set_value("Employee", self.employee.name, "status", "Left")
			frappe.delete_doc("Employee", self.employee.name, force=True, ignore_permissions=True)
		frappe.db.rollback()

	def _save(self, kind, data, submit=False, instance_name=None):
		result = employee_center.save_application(kind, data, instance_name, 1 if submit else 0)
		if result["name"] not in self.instances:
			self.instances.append(result["name"])
		return result

	def _approve(self, instance_name):
		task = frappe.db.get_value("Approval Task", {"instance": instance_name, "status": "待处理"}, "name")
		self.assertTrue(task)
		return runtime.complete_task(task, "approve", "自动化测试通过")

	def test_current_employee_draft_reentry_and_data_isolation(self):
		context = employee_center.get_context()
		self.assertEqual(context["employee"]["name"], self.employee.name)
		draft = self._save("onboarding", {"cell_number": "13800138000"})
		self.assertEqual(draft["status"], "草稿")
		setup = employee_center.get_application_setup("onboarding", draft["name"])
		self.assertEqual(setup["draft"]["data"]["cell_number"], "13800138000")
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			employee_center.get_application_setup("onboarding", draft["name"])

	def test_all_five_modules_submit_approve_and_run_business_hooks(self):
		onboarding = self._save("onboarding", {
			"gender": "女", "date_of_birth": "1995-01-01", "cell_number": "13800138000",
			"personal_email": "employee-center@example.com", "id_number": "440300199501010000",
			"truth_confirmed": True, "signature": "员工中心测试",
		}, True)
		self.assertEqual(self._approve(onboarding["name"])["status"], "已通过")

		subsidy = self._save("subsidy", {"details": [{
			"overtime_date": nowdate(), "clock_time": "21:30", "meal_amount": 25,
			"vehicle_amount": 30, "punch_attachment": "not-a-file-url",
		}]}, True)
		self.assertEqual(self._approve(subsidy["name"])["status"], "已通过")
		self.assertEqual(frappe.parse_json(frappe.db.get_value("Approval Instance", subsidy["name"], "form_data_json"))["total_amount"], 55)

		change = self._save("job-change", {"change_type": "调薪", "current_salary": 8000, "new_salary": 9000, "effective_date": add_days(nowdate(), 1), "reason": "年度调整"}, True)
		self.assertEqual(self._approve(change["name"])["status"], "已通过")

		resignation = self._save("resignation", {"planned_resignation_date": add_days(nowdate(), 30), "handover_employee": self.employee.name, "resignation_reason": "个人发展", "reason_description": "测试离职审批"}, True)
		self.assertEqual(self._approve(resignation["name"])["status"], "已通过")
		self.assertEqual(frappe.db.get_value("Employee", self.employee.name, "status"), "Active")

		handover = self._save("handover", {"resignation_application": resignation["name"], "items": [{"category": "工作内容", "item_name": "待办", "handover_status": "已完成", "handover_employee": self.employee.name}]}, True)
		self.assertEqual(self._approve(handover["name"])["status"], "已通过")
		result = frappe.parse_json(frappe.db.get_value("Approval Instance", handover["name"], "hook_result_json"))
		self.assertEqual((result["completed"], result["total"]), (1, 1))

	def test_subsidy_server_rules(self):
		with self.assertRaises(frappe.ValidationError):
			self._save("subsidy", {"details": [{"overtime_date": nowdate(), "clock_time": "21:00", "meal_amount": 26, "vehicle_amount": 31, "punch_attachment": "x"}]}, True)

	def test_attachment_is_linked_and_foreign_owner_is_rejected(self):
		draft = self._save("onboarding", {"cell_number": "13800138000"})
		doc = frappe.get_doc("Approval Instance", draft["name"])
		owned = frappe.get_doc({"doctype": "File", "file_name": "employee-center-owned.txt", "content": b"owned", "is_private": 1}).insert(ignore_permissions=True)
		self.files.append(owned.name)
		employee_center._link_owned_files(doc, {"attachment": owned.file_url})
		self.assertEqual(frappe.db.get_value("File", owned.name, "attached_to_name"), doc.name)
		foreign = frappe.get_doc({"doctype": "File", "file_name": "employee-center-foreign.txt", "content": b"foreign", "is_private": 1}).insert(ignore_permissions=True)
		self.files.append(foreign.name)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			employee_center._link_owned_files(doc, {"attachment": foreign.file_url})
		frappe.set_user("Administrator")
