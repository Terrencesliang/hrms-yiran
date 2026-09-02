# Copyright (c) 2026 stillgroup
# License: MIT
import frappe
from frappe import _
from frappe.model.document import Document


class AttendanceDeductionRule(Document):
	def validate(self):
		item_types = set()
		for row in self.rule_items:
			if row.item_type in item_types:
				frappe.throw(_("Duplicate item type: {0}").format(row.item_type))
			item_types.add(row.item_type)

	def get_item_config(self, item_type: str) -> dict | None:
		for row in self.rule_items:
			if row.item_type == item_type:
				return row.as_dict()
		return None

	def get_tiers_for_item(self, item_type: str) -> list[dict]:
		return [t.as_dict() for t in self.rule_tiers if t.item_type == item_type]
