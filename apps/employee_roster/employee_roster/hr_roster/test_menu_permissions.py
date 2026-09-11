# Copyright (c) 2026 stillgroup
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from employee_roster.hr_roster import menu_permissions


class TestMenuPermissions(FrappeTestCase):
	def test_catalog_contains_only_chinese_labels(self):
		catalog = menu_permissions.get_menu_catalog()
		self.assertTrue(catalog)
		for group in catalog:
			self.assertTrue(group["label"])
			self.assertFalse(group["label"].isascii(), group["label"])
			for child in group["children"]:
				self.assertTrue(child["label"])
				self.assertFalse(child["label"].isascii(), child["label"])

	def test_employee_default_only_contains_employee_center(self):
		catalog = menu_permissions.get_menu_catalog()
		keys = menu_permissions.default_menu_keys("employee", catalog)
		self.assertIn(menu_permissions.parent_key("Employee Center"), keys)
		self.assertNotIn(menu_permissions.parent_key("HR Setup"), keys)
		self.assertNotIn(menu_permissions.parent_key("System Management"), keys)
		self.assertTrue(all("Employee Center" in key for key in keys))

	def test_hr_default_excludes_system_management(self):
		keys = menu_permissions.default_menu_keys("hr_admin")
		self.assertIn(menu_permissions.parent_key("HR Setup"), keys)
		self.assertIn(menu_permissions.parent_key("Employee Center"), keys)
		self.assertNotIn(menu_permissions.parent_key("System Management"), keys)

	def test_system_management_contains_role_assignment(self):
		group = next(item for item in menu_permissions.get_menu_catalog() if item["module"] == "System Management")
		self.assertIn("role-assignment", [item["target"] for item in group["children"]])

	def test_role_assignment_context_uses_org_tree_and_hides_platform_role(self):
		company = frappe.db.get_value("Company", {}, "name")
		context = menu_permissions.get_role_assignment_context(company)
		self.assertEqual(context["company"], company)
		self.assertTrue(context["roots"])
		self.assertNotIn("平台超级管理员", [role["role_title"] for role in context["roles"]])

	def test_platform_admin_cannot_be_enterprise_assignment_target(self):
		company = frappe.db.get_value("Company", {}, "name")
		with self.assertRaises(frappe.ValidationError):
			menu_permissions.assign_business_roles("Administrator", company, [])

	def test_parent_removed_also_removes_children(self):
		company = frappe.db.get_value("Company", {}, "name")
		menu_permissions.ensure_system_roles(company)
		role = frappe.db.get_value("HR Business Role", {"company": company, "system_key": "employee"}, "name")
		original = [row.menu_key for row in frappe.get_doc("HR Business Role", role).menu_permissions]
		try:
			result = menu_permissions.save_role_menu_permissions(
				role,
				[menu_permissions.child_key("HR Setup", "Page", "hr-home")],
			)
			self.assertIn(menu_permissions.parent_key("HR Setup"), result["menu_keys"])
			result = menu_permissions.save_role_menu_permissions(role, [])
			self.assertEqual(result["menu_keys"], [])
		finally:
			menu_permissions.save_role_menu_permissions(role, original)
