# Copyright (c) 2026 stillgroup
# License: MIT
"""Department 覆盖：允许不同上级下同名组织，仅禁止同级重名。

ERPNext 默认 autoname 为「{department_name} - {abbr}」，导致全公司名称唯一，
无法在「杭州分公司」与「渠道部」下同时存在「直播组」。
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.naming import append_number_if_name_exists
from frappe.utils.nestedset import get_root_of

from erpnext.setup.doctype.department.department import Department as ERPNextDepartment
from erpnext.setup.doctype.department.department import get_abbreviated_name


class Department(ERPNextDepartment):
	def autoname(self):
		if not self.company:
			self.name = self.department_name
			return

		parent_title = self._parent_title_for_name()
		if parent_title:
			abbr = frappe.get_cached_value("Company", self.company, "abbr") or ""
			candidate = f"{self.department_name} · {parent_title} - {abbr}".strip(" -")
		else:
			candidate = get_abbreviated_name(self.department_name, self.company)

		self.name = append_number_if_name_exists("Department", candidate)

	def validate(self):
		super().validate()
		self.validate_sibling_department_name()

	def before_rename(self, old, new, merge=False):
		abbr = frappe.get_cached_value("Company", self.company, "abbr") if self.company else None
		if abbr and abbr not in new:
			parent_title = self._parent_title_for_name()
			if parent_title:
				new = f"{new} · {parent_title} - {abbr}"
			else:
				new = get_abbreviated_name(new, self.company)
		return new

	def _parent_title_for_name(self) -> str:
		parent = (self.parent_department or "").strip()
		if not parent:
			return ""
		if parent == "All Departments" or parent.startswith("All Departments"):
			return ""

		title = frappe.db.get_value("Department", parent, "department_name")
		if not title or title == "All Departments":
			return ""
		return str(title).strip()

	def validate_sibling_department_name(self) -> None:
		"""同一上级 + 同一公司下，department_name 不能重复。"""
		title = (self.department_name or "").strip()
		if not title or not self.company:
			return

		parent = (self.parent_department or "").strip() or get_root_of("Department")
		rows = frappe.get_all(
			"Department",
			filters={
				"department_name": title,
				"parent_department": parent,
				"company": self.company,
			},
			pluck="name",
		)
		conflict = next((name for name in rows if name != self.name), None)
		if conflict:
			frappe.throw(
				_("同一上级下已存在同名组织「{0}」，不同上级下可以使用相同名称").format(title),
				title=_("组织名称重复"),
			)
