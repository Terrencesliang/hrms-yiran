# Copyright (c) 2026 stillgroup
# License: MIT
"""Process JSON normalize / validate / summarize."""

from __future__ import annotations

import copy
import uuid
from typing import Any

import frappe
from frappe import _

from employee_roster.hr_roster.approval_engine.schema import parse_json

NODE_TYPES = {"start", "end", "approver", "cc", "condition", "parallel"}

DEFAULT_PROCESS = {
	"nodes": [
		{
			"id": "start",
			"type": "start",
			"label": "发起人",
			"props": {},
		},
		{
			"id": "approver_reports_to",
			"type": "approver",
			"label": "直属上级",
			"props": {
				"assignee_type": "reports_to",
				"mode": "or",
				"field_perms": {},
			},
		},
		{
			"id": "approver_hr",
			"type": "approver",
			"label": "HR",
			"props": {
				"assignee_type": "role",
				"role": "HR Manager",
				"mode": "or",
				"field_perms": {},
			},
		},
		{
			"id": "cc_hr",
			"type": "cc",
			"label": "抄送 HR",
			"props": {
				"assignee_type": "role",
				"role": "HR Manager",
			},
		},
		{
			"id": "end",
			"type": "end",
			"label": "结束",
			"props": {},
		},
	]
}


def _new_id(prefix: str) -> str:
	return f"{prefix}_{uuid.uuid4().hex[:8]}"


def empty_process() -> dict:
	return copy.deepcopy(DEFAULT_PROCESS)


def normalize_process(process: Any) -> dict:
	data = parse_json(process, empty_process())
	if not isinstance(data, dict):
		frappe.throw(_("流程 JSON 必须是对象"))
	nodes = data.get("nodes")
	if not isinstance(nodes, list) or not nodes:
		frappe.throw(_("流程至少需要一个节点"))

	normalized = []
	seen = set()
	for idx, raw in enumerate(nodes):
		if not isinstance(raw, dict):
			frappe.throw(_("第 {0} 个节点无效").format(idx + 1))
		ntype = (raw.get("type") or "").strip()
		if ntype not in NODE_TYPES:
			frappe.throw(_("不支持的节点类型：{0}").format(ntype or "(空)"))
		nid = (raw.get("id") or "").strip() or _new_id(ntype)
		if nid in seen:
			nid = _new_id(ntype)
		seen.add(nid)
		props = raw.get("props") if isinstance(raw.get("props"), dict) else {}
		node = {
			"id": nid,
			"type": ntype,
			"label": (raw.get("label") or ntype).strip(),
			"props": props,
		}
		if ntype == "condition":
			branches = props.get("branches") or raw.get("branches") or []
			node["props"]["branches"] = _normalize_branches(branches)
		if ntype == "parallel":
			branches = props.get("branches") or raw.get("branches") or []
			node["props"]["branches"] = _normalize_branches(branches, require_expr=False)
		normalized.append(node)

	if normalized[0]["type"] != "start":
		normalized.insert(0, {"id": "start", "type": "start", "label": "发起人", "props": {}})
	if normalized[-1]["type"] != "end":
		normalized.append({"id": "end", "type": "end", "label": "结束", "props": {}})

	return {"nodes": normalized}


def _normalize_branches(branches: Any, require_expr: bool = True) -> list:
	if not isinstance(branches, list):
		return []
	out = []
	for b in branches:
		if not isinstance(b, dict):
			continue
		nodes = normalize_process({"nodes": b.get("nodes") or []})["nodes"]
		# strip outer start/end injected by normalize for nested branches
		inner = [n for n in nodes if n["type"] not in ("start", "end")]
		item = {
			"id": b.get("id") or _new_id("branch"),
			"label": b.get("label") or "分支",
			"expression": b.get("expression") or "",
			"nodes": inner,
		}
		if require_expr and not item["expression"] and not b.get("is_default"):
			item["is_default"] = 0
		else:
			item["is_default"] = 1 if b.get("is_default") else 0
		out.append(item)
	return out


def summarize_process(process: Any) -> str:
	data = normalize_process(process)
	parts = []
	for node in data["nodes"]:
		if node["type"] in ("start", "end"):
			continue
		if node["type"] == "approver":
			parts.append(node["label"] or "审批人")
		elif node["type"] == "cc":
			parts.append(f"抄送：{node['label'] or '抄送'}")
		elif node["type"] == "condition":
			parts.append(f"条件：{node['label'] or '分支'}")
		elif node["type"] == "parallel":
			parts.append(f"并行：{node['label'] or '并行'}")
	return " → ".join(parts) if parts else "未配置流程"


def flatten_linear_nodes(process: dict) -> list[dict]:
	"""Return top-level linear nodes (condition/parallel kept as single steps)."""
	return list(normalize_process(process)["nodes"])
