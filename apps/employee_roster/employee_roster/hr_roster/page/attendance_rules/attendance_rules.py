# Copyright (c) 2026 stillgroup
# License: MIT
import frappe


@frappe.whitelist()
def get_rules_overview() -> dict:
	rules = frappe.get_all(
		"Attendance Deduction Rule",
		filters={"is_active": 1},
		fields=["name", "rule_name", "description"],
		order_by="rule_name asc",
	)
	result = []
	for rule in rules:
		doc = frappe.get_doc("Attendance Deduction Rule", rule.name)
		items_summary = []
		for item in doc.rule_items:
			if not item.enabled:
				continue
			label = {
				"Late Entry": "迟到",
				"Early Exit": "早退",
				"Missing Punch": "缺卡",
				"Absent": "旷工",
			}.get(item.item_type, item.item_type)
			mode = {
				"Tiered": "阶梯/组合",
				"Per Minute": "按分钟",
				"None": "不扣款",
				"Salary Percent": "工资比例",
			}.get(item.calc_mode, item.calc_mode)
			items_summary.append({"label": label, "mode": mode, "item_type": item.item_type})
		group_count = frappe.db.count("Attendance Group", {"deduction_rule": rule.name, "is_active": 1})
		result.append(
			{
				"name": rule.name,
				"rule_name": rule.rule_name,
				"description": rule.description,
				"items": items_summary,
				"group_count": group_count,
			}
		)
	return {"rules": result, "help": "规则需关联考勤分组后才会对员工生效。发薪前通过 Payroll Entry 创建考勤扣款汇总。"}
