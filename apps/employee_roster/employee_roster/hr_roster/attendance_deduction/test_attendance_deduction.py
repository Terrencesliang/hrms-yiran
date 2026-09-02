# Copyright (c) 2026 stillgroup
# License: MIT
import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from employee_roster.hr_roster.attendance_deduction.engine import (
	AttendanceMetrics,
	_calc_item,
	_calc_per_minute,
	_calc_tiered,
	_match_tier,
)


class TestAttendanceDeductionEngine(IntegrationTestCase):
	def test_match_tier_minutes(self):
		tiers = [
			{
				"item_type": "Late Entry",
				"min_value": 1,
				"max_value": 5,
				"tier_unit": "Per Occurrence Minutes",
				"deduction_type": "Fixed Amount",
				"amount": 20,
			},
			{
				"item_type": "Late Entry",
				"min_value": 6,
				"max_value": 0,
				"tier_unit": "Per Occurrence Minutes",
				"deduction_type": "Fixed Amount",
				"amount": 50,
			},
		]
		amount, label = _match_tier(tiers, 3, "Per Occurrence Minutes")
		self.assertEqual(amount, 20)
		self.assertIn("1-5", label)
		amount, _ = _match_tier(tiers, 10, "Per Occurrence Minutes")
		self.assertEqual(amount, 50)

	def test_per_minute_calculation(self):
		item = frappe._dict(
			{"item_type": "Late Entry", "calc_mode": "Per Minute", "rate_per_minute": 2}
		)
		metrics = AttendanceMetrics(late_entries=[{"date": "2026-01-01", "minutes": 60}])
		lines, total = _calc_per_minute("Late Entry", item, metrics)
		self.assertEqual(total, 120)
		self.assertEqual(len(lines), 1)

	def test_tiered_monthly_missing_punch(self):
		if not frappe.db.exists("Attendance Deduction Rule", "企业默认考勤规则"):
			self.skipTest("Default rules not seeded")
		rule = frappe.get_doc("Attendance Deduction Rule", "企业默认考勤规则")
		metrics = AttendanceMetrics(
			missing_punches=[{"date": "2026-01-01"}, {"date": "2026-01-02"}]
		)
		lines, total = _calc_tiered("Missing Punch", rule, metrics)
		self.assertGreater(flt(total), 0)
		self.assertTrue(lines)

	def test_none_mode_returns_zero(self):
		item = frappe._dict({"item_type": "Missing Punch", "enabled": 1, "calc_mode": "None"})
		rule = frappe._dict({"rule_items": [item], "rule_tiers": []})
		metrics = AttendanceMetrics(missing_punches=[{"date": "2026-01-01"}])
		lines, total = _calc_item(item, rule, metrics, "HR-EMP-00001", "2026-01-31")
		self.assertEqual(total, 0)
