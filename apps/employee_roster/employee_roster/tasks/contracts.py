"""电子合同对账、事件重放、归档重试与预览清理任务。"""
from __future__ import annotations

import json

import frappe
from frappe.utils import get_datetime, now_datetime


def _log_failure(title: str, name: str) -> None:
	frappe.log_error(
		title=title,
		message=f"{name}\n{frappe.get_traceback()}",
	)


def reconcile_contracts(limit: int = 100) -> None:
	from employee_roster.integrations.fadada import service

	names = frappe.get_all(
		"Contract Signing",
		filters={
			"provider": "Fadada",
			"sign_task_id": ["is", "set"],
			"status": ["in", ["Draft", "Pending", "Signing", "Error"]],
			"is_preview": 0,
		},
		pluck="name",
		order_by="last_synced_on asc",
		limit_page_length=limit,
	)
	for name in names:
		try:
			doc = frappe.get_doc("Contract Signing", name)
			if doc.next_retry_on and get_datetime(doc.next_retry_on) > now_datetime():
				continue
			service.sync_contract_status(doc)
		except Exception:
			_log_failure("法大大合同定时对账失败", name)


def replay_contract_events(limit: int = 100) -> None:
	from employee_roster.integrations.fadada.callback import _apply_event

	names = frappe.get_all(
		"Contract Signing Event",
		filters={"provider": "Fadada", "processed": 0},
		pluck="name",
		order_by="creation asc",
		limit_page_length=limit,
	)
	for name in names:
		try:
			event = frappe.get_doc("Contract Signing Event", name)
			_apply_event(event, json.loads(event.payload or "{}"))
		except Exception:
			_log_failure("法大大回调事件重放失败", name)


def retry_archives(limit: int = 50) -> None:
	from employee_roster.integrations.fadada.service import archive_signed_contract

	names = frappe.get_all(
		"Contract Signing",
		filters={
			"provider": "Fadada",
			"status": "Completed",
			"signed_file": ["is", "not set"],
			"archive_status": ["in", ["Pending", "Failed"]],
		},
		pluck="name",
		order_by="modified asc",
		limit_page_length=limit,
	)
	for name in names:
		try:
			doc = frappe.get_doc("Contract Signing", name)
			if doc.next_retry_on and get_datetime(doc.next_retry_on) > now_datetime():
				continue
			archive_signed_contract(name)
		except Exception:
			_log_failure("法大大合同归档重试失败", name)


def cleanup_preview_drafts(limit: int = 100) -> None:
	from employee_roster.integrations.fadada.client import FadadaClient

	names = frappe.get_all(
		"Contract Signing",
		filters={
			"provider": "Fadada",
			"is_preview": 1,
			"preview_expires_on": ["<", now_datetime()],
			"status": "Draft",
		},
		pluck="name",
		order_by="preview_expires_on asc",
		limit_page_length=limit,
	)
	client = None
	for name in names:
		try:
			doc = frappe.get_doc("Contract Signing", name)
			if doc.sign_task_id:
				client = client or FadadaClient()
				client.delete(doc.sign_task_id)
			frappe.delete_doc("Contract Signing", name, ignore_permissions=True)
		except Exception:
			_log_failure("法大大预览草稿清理失败", name)


def hourly() -> None:
	reconcile_contracts()
	replay_contract_events()
	retry_archives()


def cleanup() -> None:
	cleanup_preview_drafts()
