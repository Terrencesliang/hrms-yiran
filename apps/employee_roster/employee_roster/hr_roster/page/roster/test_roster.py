import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from employee_roster.hr_roster.page.roster import roster


class TestRosterPermissions(unittest.TestCase):
	def test_guest_cannot_read_employee_data(self):
		with patch.object(roster.frappe, "session", SimpleNamespace(user="Guest")):
			with patch.object(roster.frappe, "throw", side_effect=RuntimeError("permission denied")):
				with self.assertRaises(RuntimeError):
					roster.get_roster_data()

	def test_roster_query_uses_permission_aware_list(self):
		row = SimpleNamespace(
			name="HR-EMP-00001",
			employee_name="张三",
			employee_number="00001",
			department="人事部",
			designation="人事专员",
			employment_type="Full-time",
			date_of_joining="2026-01-01",
			branch="深圳",
			status="Active",
			group_name="招聘组",
			cell_number="13800000000",
		)
		with patch.object(roster.frappe, "session", SimpleNamespace(user="hr@example.com")):
			with patch.object(roster.frappe, "has_permission", return_value=True):
				with patch.object(roster.frappe, "get_list", return_value=[row]) as get_list:
					result = roster.get_roster_data()

		get_list.assert_called_once()
		self.assertEqual(result["tables"][0]["name"], row.name)

	def test_quick_edit_saves_employee_document(self):
		doc = Mock()
		with patch.object(roster.frappe, "session", SimpleNamespace(user="hr@example.com")):
			with patch.object(roster.frappe, "has_permission", return_value=True):
				with patch.object(roster.frappe, "get_doc", return_value=doc):
					result = roster.update_employee_fields("HR-EMP-00001", "cell_number", "13900000000")

		doc.set.assert_called_once_with("cell_number", "13900000000")
		doc.save.assert_called_once_with()
		self.assertTrue(result["ok"])

	def test_quick_edit_rejects_non_whitelisted_field(self):
		with patch.object(roster.frappe, "throw", side_effect=ValueError("not allowed")):
			with self.assertRaises(ValueError):
				roster.update_employee_fields("HR-EMP-00001", "salary", "100")


if __name__ == "__main__":
	unittest.main()
