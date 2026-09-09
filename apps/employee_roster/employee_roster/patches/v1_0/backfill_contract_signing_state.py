"""安全回填电子合同本地状态 (迁移期间不调用供应商 API)。"""
import json

import frappe


def execute() -> None:
	if not frappe.db.table_exists("Contract Signing"):
		return
	frappe.db.sql(
		"""
		update `tabContract Signing`
		set provider = coalesce(nullif(provider, ''), 'Tencent'),
			status = case
				when provider = 'Fadada' and vendor_status = 'task_finished' then 'Completed'
				when provider = 'Fadada' and vendor_status = 'sign_completed'
					and coalesce(signed_file, '') = '' then 'Pending'
				else coalesce(nullif(status, ''), 'Draft')
			end,
			archive_status = case
				when coalesce(signed_file, '') != '' then 'Archived'
				else coalesce(nullif(archive_status, ''), 'Pending')
			end,
			stage = case
				when vendor_status = 'task_finished' then 'Finished'
				when vendor_status = 'sign_completed' then 'Finishing'
				when vendor_status = 'sign_progress' then 'Signing'
				when vendor_status in ('fill_completed') then 'Ready'
				when vendor_status in ('task_created', 'fill_progress') then 'Preparing'
				else coalesce(nullif(stage, ''), 'Unknown')
			end
		"""
	)
	if frappe.db.table_exists("Contract Sign Template"):
		for row in frappe.get_all(
			"Contract Sign Template",
			filters={"provider": "Fadada"},
			fields=["name", "actor_config", "employee_actor_id", "corp_actor_id"],
		):
			try:
				config = json.loads(row.actor_config or "{}")
			except (TypeError, ValueError):
				continue
			employee_id = row.employee_actor_id or config.get("employee_actor_id") or ""
			corp_id = row.corp_actor_id or config.get("corp_actor_id") or ""
			for entry in config.get("actors") or []:
				actor = entry.get("actor") or entry
				if actor.get("actorType") == "person" and not employee_id:
					employee_id = actor.get("actorId") or ""
				if actor.get("actorType") == "corp" and not corp_id:
					corp_id = actor.get("actorId") or ""
			frappe.db.set_value(
				"Contract Sign Template",
				row.name,
				{
					"employee_actor_id": employee_id,
					"corp_actor_id": corp_id,
				},
				update_modified=False,
			)
