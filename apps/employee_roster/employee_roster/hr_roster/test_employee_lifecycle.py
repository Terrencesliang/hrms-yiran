# Copyright (c) 2026 stillgroup
# License: MIT

from types import SimpleNamespace
from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from employee_roster.hr_roster.employee_lifecycle import ensure_left_before_delete


class TestEmployeeLifecycle(FrappeTestCase):
	def test_active_employee_cannot_be_deleted(self):
		doc = SimpleNamespace(name="HR-EMP-00001", employee_name="测试员工", status="Active")
		with patch("employee_roster.hr_roster.employee_lifecycle.frappe.throw", side_effect=RuntimeError) as throw:
			with self.assertRaises(RuntimeError):
				ensure_left_before_delete(doc)
		throw.assert_called_once()

	def test_left_employee_can_be_deleted(self):
		doc = SimpleNamespace(name="HR-EMP-00001", employee_name="测试员工", status="Left")
		with patch("employee_roster.hr_roster.employee_lifecycle.frappe.throw") as throw:
			ensure_left_before_delete(doc)
		throw.assert_not_called()
