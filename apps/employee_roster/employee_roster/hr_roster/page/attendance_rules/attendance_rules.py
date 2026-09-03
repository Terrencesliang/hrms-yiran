# Copyright (c) 2026 stillgroup
# License: MIT
import frappe


@frappe.whitelist()
def get_rules_overview() -> dict:
	rules = frappe.get_all(
		"Attendance Deduction Rule",
		filters={"is_active": 1},
		fields=["name", "rule_name", "description", "modified"],
		order_by="rule_name asc",
	)
	result = []
	rule_names = []
	for rule in rules:
		doc = frappe.get_doc("Attendance Deduction Rule", rule.name)
		items_summary = []
		mode_by_type = {}
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
				"Tiered": "阶梯·组合",
				"Per Minute": "按分钟",
				"None": "不扣款",
				"Salary Percent": "工资比例",
			}.get(item.calc_mode, item.calc_mode)
			items_summary.append({"label": label, "mode": mode, "item_type": item.item_type})
			mode_by_type[item.item_type] = mode
		group_count = frappe.db.count("Attendance Group", {"deduction_rule": rule.name, "is_active": 1})
		rule_names.append(rule.name)
		result.append(
			{
				"name": rule.name,
				"rule_name": rule.rule_name,
				"description": rule.description,
				"items": items_summary,
				"group_count": group_count,
				"modified": rule.modified,
				# Fixed columns for table UI (one value per column)
				"late_mode": mode_by_type.get("Late Entry", "—"),
				"early_mode": mode_by_type.get("Early Exit", "—"),
				"missing_mode": mode_by_type.get("Missing Punch", "—"),
				"absent_mode": mode_by_type.get("Absent", "—"),
			}
		)

	linked_groups = 0
	covered_employees = 0
	if rule_names:
		group_names = frappe.get_all(
			"Attendance Group",
			filters={"is_active": 1, "deduction_rule": ["in", rule_names]},
			pluck="name",
		)
		linked_groups = len(group_names)
		if group_names:
			covered_employees = frappe.db.count(
				"Attendance Group Member",
				{"parenttype": "Attendance Group", "parent": ["in", group_names]},
			)

	return {
		"rules": result,
		"help": "规则需关联考勤分组后才会对员工生效；发薪前请通过 Payroll Entry 创建考勤扣款汇总。",
		"stats": {
			"enabled_rules": len(result),
			"linked_groups": linked_groups,
			"covered_employees": covered_employees,
		},
	}
