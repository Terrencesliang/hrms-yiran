# Copyright (c) 2026 stillgroup
# License: MIT
"""Safe simple expression evaluator for condition branches."""

from __future__ import annotations

import ast
import operator
from typing import Any

import frappe
from frappe import _

_BIN_OPS = {
	ast.Eq: operator.eq,
	ast.NotEq: operator.ne,
	ast.Lt: operator.lt,
	ast.LtE: operator.le,
	ast.Gt: operator.gt,
	ast.GtE: operator.ge,
	ast.Add: operator.add,
	ast.Sub: operator.sub,
	ast.Mult: operator.mul,
	ast.Div: operator.truediv,
}

_BOOL_OPS = {
	ast.And: all,
	ast.Or: any,
}

_UNARY_OPS = {
	ast.Not: operator.not_,
	ast.USub: operator.neg,
}


def eval_expression(expression: str, context: dict[str, Any]) -> bool:
	expr = (expression or "").strip()
	if not expr:
		return False
	try:
		tree = ast.parse(expr, mode="eval")
	except SyntaxError:
		frappe.throw(_("条件表达式语法错误：{0}").format(expr))
	return bool(_eval_node(tree.body, context or {}))


def _eval_node(node: ast.AST, ctx: dict[str, Any]) -> Any:
	if isinstance(node, ast.Constant):
		return node.value
	if isinstance(node, ast.Name):
		if node.id not in ctx:
			return None
		return ctx[node.id]
	if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
		return _UNARY_OPS[type(node.op)](_eval_node(node.operand, ctx))
	if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
		left = _eval_node(node.left, ctx)
		right = _eval_node(node.right, ctx)
		if left is None or right is None:
			return False
		return _BIN_OPS[type(node.op)](left, right)
	if isinstance(node, ast.Compare):
		left = _eval_node(node.left, ctx)
		for op, comparator in zip(node.ops, node.comparators):
			right = _eval_node(comparator, ctx)
			op_type = type(op)
			if op_type not in _BIN_OPS:
				frappe.throw(_("不支持的比较运算"))
			if left is None or right is None:
				return False
			if not _BIN_OPS[op_type](left, right):
				return False
			left = right
		return True
	if isinstance(node, ast.BoolOp) and type(node.op) in _BOOL_OPS:
		values = [_eval_node(v, ctx) for v in node.values]
		return _BOOL_OPS[type(node.op)](bool(v) for v in values)
	frappe.throw(_("条件表达式包含不支持的语法"))
