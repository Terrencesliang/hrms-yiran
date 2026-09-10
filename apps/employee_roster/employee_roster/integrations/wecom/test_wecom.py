# Copyright (c) 2026 stillgroup
# License: MIT
from datetime import date
from unittest import TestCase

from employee_roster.integrations.wecom.attendance import (
	_day_datetime,
	_log_type,
	_record_id,
)


class TestWeComAttendanceMapping(TestCase):
	def test_log_type_mapping(self):
		self.assertEqual(_log_type("上班打卡"), "IN")
		self.assertEqual(_log_type("下班打卡"), "OUT")
		self.assertEqual(_log_type("外出打卡"), "")

	def test_record_id_is_stable_and_sensitive_to_time(self):
		row = {
			"userid": "zhangsan",
			"checkin_time": 1789002000,
			"checkin_type": "上班打卡",
			"deviceid": "device-1",
			"groupid": 1,
		}
		self.assertEqual(_record_id(row), _record_id(dict(row)))
		changed = {**row, "checkin_time": row["checkin_time"] + 1}
		self.assertNotEqual(_record_id(row), _record_id(changed))

	def test_day_datetime_uses_seconds_from_midnight(self):
		value = _day_datetime(date(2026, 9, 10), 9 * 3600 + 30 * 60)
		self.assertEqual(value.isoformat(), "2026-09-10T09:30:00")
