# Copyright (c) 2026 stillgroup
# License: MIT
"""组织架构：同级不可重名，不同上级可同名。"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from employee_roster.hr_roster.page.orgchart.orgchart import create_org_unit


class TestDepartmentSiblingNames(FrappeTestCase):
	def setUp(self):
		self.company = frappe.db.get_single_value("Global Defaults", "default_company")
		if not self.company:
			self.company = frappe.db.get_value("Company", {}, "name")
		self.assertTrue(self.company, "需要至少一个公司才能跑组织架构测试")
		self._created = []

	def tearDown(self):
		for name in reversed(self._created):
			if frappe.db.exists("Department", name):
				frappe.delete_doc("Department", name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _create(self, title: str, parent: str | None = None, org_type: str = "组") -> dict:
		result = create_org_unit(
			title=title,
			company=self.company,
			parent=parent,
			org_type=org_type,
		)
		self._created.append(result["name"])
		return result

	def test_same_title_under_different_parents_allowed(self):
		branch = self._create("测试杭州分公司", org_type="分公司")
		channel = self._create("测试渠道部", org_type="部门")

		g1 = self._create("直播组", parent=branch["name"], org_type="组")
		g2 = self._create("直播组", parent=channel["name"], org_type="组")

		self.assertNotEqual(g1["name"], g2["name"])
		self.assertEqual(g1["title"], "直播组")
		self.assertEqual(g2["title"], "直播组")
		self.assertEqual(
			frappe.db.get_value("Department", g1["name"], "parent_department"),
			branch["name"],
		)
		self.assertEqual(
			frappe.db.get_value("Department", g2["name"], "parent_department"),
			channel["name"],
		)

	def test_same_title_under_same_parent_rejected(self):
		parent = self._create("测试同级父部门", org_type="部门")
		self._create("直播组", parent=parent["name"], org_type="组")

		with self.assertRaises(frappe.ValidationError):
			self._create("直播组", parent=parent["name"], org_type="组")
