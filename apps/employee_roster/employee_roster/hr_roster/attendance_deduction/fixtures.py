# Copyright (c) 2026 stillgroup
# License: MIT
"""默认考勤扣款规则与示例分组 fixture 数据。"""

from copy import deepcopy

DEFAULT_RULES = [
	{
		"doctype": "Attendance Deduction Rule",
		"rule_name": "企业默认考勤规则",
		"is_active": 1,
		"description": "阶梯/组合扣款：迟到早退按次、缺卡按月累计、旷工按小时",
		"rule_items": [
			{"item_type": "Late Entry", "enabled": 1, "calc_mode": "Tiered"},
			{"item_type": "Early Exit", "enabled": 1, "calc_mode": "Tiered"},
			{"item_type": "Missing Punch", "enabled": 1, "calc_mode": "Tiered"},
			{"item_type": "Absent", "enabled": 1, "calc_mode": "Tiered"},
		],
		"rule_tiers": [
			{"item_type": "Late Entry", "min_value": 1, "max_value": 5, "tier_unit": "Per Occurrence Minutes", "deduction_type": "Fixed Amount", "amount": 20},
			{"item_type": "Late Entry", "min_value": 6, "max_value": 15, "tier_unit": "Per Occurrence Minutes", "deduction_type": "Fixed Amount", "amount": 50},
			{"item_type": "Late Entry", "min_value": 16, "max_value": 0, "tier_unit": "Per Occurrence Minutes", "deduction_type": "Fixed Amount", "amount": 100},
			{"item_type": "Early Exit", "min_value": 1, "max_value": 5, "tier_unit": "Per Occurrence Minutes", "deduction_type": "Fixed Amount", "amount": 20},
			{"item_type": "Early Exit", "min_value": 6, "max_value": 0, "tier_unit": "Per Occurrence Minutes", "deduction_type": "Fixed Amount", "amount": 50},
			{"item_type": "Missing Punch", "min_value": 1, "max_value": 1, "tier_unit": "Monthly Count", "deduction_type": "Fixed Amount", "amount": 30},
			{"item_type": "Missing Punch", "min_value": 2, "max_value": 3, "tier_unit": "Monthly Count", "deduction_type": "Fixed Amount", "amount": 80},
			{"item_type": "Missing Punch", "min_value": 4, "max_value": 0, "tier_unit": "Monthly Count", "deduction_type": "Fixed Amount", "amount": 150},
			{"item_type": "Absent", "min_value": 1, "max_value": 4, "tier_unit": "Occurrence Hours", "deduction_type": "Fixed Amount", "amount": 200},
			{"item_type": "Absent", "min_value": 4, "max_value": 0, "tier_unit": "Occurrence Hours", "deduction_type": "Fixed Amount", "amount": 500},
		],
	},
	{
		"doctype": "Attendance Deduction Rule",
		"rule_name": "扣款规则1",
		"is_active": 1,
		"description": "迟到早退按分钟线性；缺卡不扣；旷工按工资比例",
		"rule_items": [
			{"item_type": "Late Entry", "enabled": 1, "calc_mode": "Per Minute", "rate_per_minute": 2},
			{"item_type": "Early Exit", "enabled": 1, "calc_mode": "Per Minute", "rate_per_minute": 2},
			{"item_type": "Missing Punch", "enabled": 1, "calc_mode": "None"},
			{"item_type": "Absent", "enabled": 1, "calc_mode": "Salary Percent", "salary_percent": 10, "base_salary_component": "Basic"},
		],
		"rule_tiers": [],
	},
]


def seed_default_rules() -> None:
	import frappe

	for data in DEFAULT_RULES:
		if frappe.db.exists("Attendance Deduction Rule", data["rule_name"]):
			continue
		prepared = deepcopy(data)
		for item in prepared.get("rule_items", []):
			component = item.get("base_salary_component")
			if component and not frappe.db.exists("Salary Component", component):
				# A fresh/test site may not have completed the payroll setup wizard.
				# Leaving this optional link empty makes the calculation engine fall
				# back to the first earning component instead of failing app install.
				item.pop("base_salary_component", None)
		doc = frappe.get_doc(prepared)
		doc.insert(ignore_permissions=True)


def ensure_salary_component() -> None:
	import frappe

	name = "Attendance Deduction"
	if frappe.db.exists("Salary Component", name):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Salary Component",
			"salary_component": name,
			"salary_component_abbr": "ATTDED",
			"type": "Deduction",
			"depends_on_payment_days": 0,
			"is_tax_applicable": 0,
		}
	)
	doc.insert(ignore_permissions=True)


def ensure_settings() -> None:
	import frappe

	if frappe.db.exists("Attendance Deduction Settings", "Attendance Deduction Settings"):
		return
	doc = frappe.get_doc({"doctype": "Attendance Deduction Settings"})
	doc.insert(ignore_permissions=True)
