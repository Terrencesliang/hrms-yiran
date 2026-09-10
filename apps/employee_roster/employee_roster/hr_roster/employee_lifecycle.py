# Copyright (c) 2026 stillgroup
# License: MIT
"""员工生命周期规则。"""

import frappe
from frappe import _


def ensure_left_before_delete(doc, method=None):
	"""只允许删除已经完成离职的员工。"""
	if doc.status != "Left":
		frappe.throw(
			_("员工 {0} 当前不是已离职状态，请先办理离职并保存后再删除。")
			.format(doc.employee_name or doc.name),
			title=_("不能删除员工"),
		)
