"""企业微信通讯录同步和消息业务适配。"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import frappe
import requests
from frappe.utils import now, nowdate
from frappe.utils.nestedset import get_root_of

from .client import WeComClient, WeComConfig, WeComConfigurationError

ACTIVE_WECOM_STATUSES = {1, 4}


def _company(config: WeComConfig) -> str:
	if config.default_company:
		if not frappe.db.exists("Company", config.default_company):
			raise WeComConfigurationError(
				f"企业微信 DEFAULT_COMPANY 不存在: {config.default_company}"
			)
		return config.default_company
	companies = frappe.get_all("Company", pluck="name", limit=2)
	if len(companies) != 1:
		raise WeComConfigurationError("存在多个公司时必须配置 WECOM_DEFAULT_COMPANY")
	return companies[0]


def sync_departments(*, client: WeComClient | None = None) -> dict[str, Any]:
	client = client or WeComClient()
	company = _company(client.config)
	rows = client.list_departments()
	by_id = {str(row.get("id")): row for row in rows if row.get("id") is not None}
	root_name = get_root_of("Department")
	mapped: dict[str, str] = {"1": root_name}
	created = updated = skipped = 0
	pending = {key for key in by_id if key != "1"}

	while pending:
		progress = False
		for department_id in list(pending):
			row = by_id[department_id]
			parent_id = str(row.get("parentid") or "1")
			if parent_id not in mapped:
				continue
			title = str(row.get("name") or "").strip()
			if not title or title == department_id:
				skipped += 1
				pending.remove(department_id)
				progress = True
				continue
			parent = mapped[parent_id]
			name = frappe.db.get_value(
				"Department", {"wecom_department_id": department_id}, "name"
			)
			if not name:
				name = frappe.db.get_value(
					"Department",
					{
						"department_name": title,
						"parent_department": parent,
						"company": company,
					},
					"name",
				)
			if name:
				doc = frappe.get_doc("Department", name)
				changed = False
				for fieldname, value in (
					("department_name", title),
					("parent_department", parent),
					("wecom_department_id", department_id),
					("wecom_last_synced_on", now()),
				):
					if getattr(doc, fieldname, None) != value:
						setattr(doc, fieldname, value)
						changed = True
				if changed:
					doc.save(ignore_permissions=True)
					updated += 1
			else:
				doc = frappe.get_doc(
					{
						"doctype": "Department",
						"department_name": title,
						"parent_department": parent,
						"company": company,
						"is_group": 1,
						"wecom_department_id": department_id,
						"wecom_last_synced_on": now(),
					}
				).insert(ignore_permissions=True)
				created += 1
			mapped[department_id] = doc.name
			pending.remove(department_id)
			progress = True
		if not progress:
			skipped += len(pending)
			break

	return {
		"remote": len(rows),
		"created": created,
		"updated": updated,
		"skipped": skipped,
		"unresolved_department_ids": sorted(pending),
	}


def _find_employee(user: dict[str, Any]) -> str:
	userid = str(user.get("userid") or "").strip()
	if userid and (
		name := frappe.db.get_value("Employee", {"hr_wecom_id": userid}, "name")
	):
		return str(name)
	mobile = str(user.get("mobile") or "").strip()
	if mobile and (
		name := frappe.db.get_value("Employee", {"cell_number": mobile}, "name")
	):
		return str(name)
	email = str(user.get("email") or "").strip().lower()
	if email and (
		name := frappe.db.get_value("Employee", {"company_email": email}, "name")
	):
		return str(name)
	return ""


def _primary_department(user: dict[str, Any]) -> str:
	department_ids = user.get("department") or []
	main_id = str(user.get("main_department") or (department_ids[0] if department_ids else ""))
	if not main_id or main_id == "1":
		return ""
	return str(
		frappe.db.get_value("Department", {"wecom_department_id": main_id}, "name") or ""
	)


def _employee_values(user: dict[str, Any]) -> dict[str, Any]:
	values: dict[str, Any] = {
		"hr_wecom_id": str(user.get("userid") or "").strip(),
		"wecom_last_synced_on": now(),
	}
	field_mapping = {
		"employee_name": "name",
		"cell_number": "mobile",
		"company_email": "email",
	}
	for target, source in field_mapping.items():
		if value := str(user.get(source) or "").strip():
			values[target] = value
	if department := _primary_department(user):
		values["department"] = department
	if position := str(user.get("position") or "").strip():
		if frappe.db.exists("Designation", position):
			values["designation"] = position
	if int(user.get("status") or 0) in ACTIVE_WECOM_STATUSES:
		values["status"] = "Active"
	return values


def _create_employee(user: dict[str, Any], company: str) -> Any:
	name = str(user.get("name") or user.get("userid") or "").strip()
	if not name:
		raise frappe.ValidationError("企微成员缺少姓名和 UserID")
	gender_map = {"1": "男", "2": "女"}
	gender = gender_map.get(str(user.get("gender") or ""), "")
	if gender and not frappe.db.exists("Gender", gender):
		gender = ""
	payload = {
		"doctype": "Employee",
		"first_name": name,
		"employee_name": name,
		"company": company,
		"date_of_joining": nowdate(),
		"status": "Active",
		**_employee_values(user),
	}
	if gender:
		payload["gender"] = gender
	return frappe.get_doc(payload).insert(ignore_permissions=True)


def sync_users(
	*,
	client: WeComClient | None = None,
	create_missing: bool | None = None,
) -> dict[str, Any]:
	client = client or WeComClient()
	company = _company(client.config)
	create_missing = (
		client.config.create_missing_employees if create_missing is None else create_missing
	)
	created = updated = skipped = failed = 0
	errors: list[dict[str, str]] = []
	for row in client.list_user_ids():
		userid = str(row.get("userid") or "").strip()
		if not userid:
			skipped += 1
			continue
		try:
			user = client.get_user(userid)
			employee_name = _find_employee(user)
			if not employee_name:
				if not create_missing:
					skipped += 1
					continue
				_create_employee(user, company)
				created += 1
				continue
			doc = frappe.get_doc("Employee", employee_name)
			values = _employee_values(user)
			for fieldname, value in values.items():
				setattr(doc, fieldname, value)
			doc.save(ignore_permissions=True)
			updated += 1
		except Exception as exc:
			failed += 1
			errors.append({"userid": userid, "error": str(exc)[:300]})
	return {
		"created": created,
		"updated": updated,
		"skipped": skipped,
		"failed": failed,
		"errors": errors[:50],
	}


def sync_contacts(*, create_missing: bool | None = None) -> dict[str, Any]:
	client = WeComClient()
	return {
		"departments": sync_departments(client=client),
		"employees": sync_users(client=client, create_missing=create_missing),
	}


def bind_employee_userids_by_mobile(*, limit: int = 100) -> dict[str, Any]:
	"""用已校验的中国大陆手机号绑定存量员工；有限额且失败不重试，规避封禁。"""
	client = WeComClient()
	limit = max(1, min(int(limit), 1000))
	rows = frappe.get_all(
		"Employee",
		filters={
			"status": "Active",
			"hr_wecom_id": ["is", "not set"],
			"cell_number": ["is", "set"],
		},
		fields=["name", "cell_number"],
		limit=limit,
	)
	bound = invalid = failed = 0
	errors: list[dict[str, str]] = []
	for row in rows:
		mobile = re.sub(r"[\s-]", "", str(row.cell_number or ""))
		if mobile.startswith("+86"):
			mobile = mobile[3:]
		if not re.fullmatch(r"1[3-9]\d{9}", mobile):
			invalid += 1
			continue
		try:
			userid = client.get_userid_by_mobile(mobile)
			if not userid:
				failed += 1
				continue
			frappe.db.set_value(
				"Employee",
				row.name,
				{"hr_wecom_id": userid, "wecom_last_synced_on": now()},
			)
			bound += 1
		except Exception as exc:
			failed += 1
			errors.append({"employee": row.name, "error": str(exc)[:300]})
	return {
		"attempted": len(rows) - invalid,
		"bound": bound,
		"invalid": invalid,
		"failed": failed,
		"errors": errors[:50],
	}


def send_text(userids: list[str] | str, content: str) -> dict[str, Any]:
	client = WeComClient()
	recipients = (
		"|".join(dict.fromkeys(item for item in userids if item))
		if isinstance(userids, list)
		else str(userids)
	)
	if not recipients:
		raise frappe.ValidationError("企业微信消息缺少接收人")
	return client.send_message(
		{
			"touser": recipients,
			"msgtype": "text",
			"agentid": client.config.agent_id,
			"text": {"content": str(content)[:2048]},
			"safe": 0,
			"enable_id_trans": 0,
			"enable_duplicate_check": 1,
			"duplicate_check_interval": 1800,
		}
	)


def send_robot_text(content: str) -> dict[str, Any]:
	webhook = WeComConfig.load().robot_webhook
	parsed = urlparse(webhook)
	if parsed.scheme != "https" or parsed.hostname != "qyapi.weixin.qq.com":
		raise WeComConfigurationError("WECOM_ROBOT_WEBHOOK 必须是企微官方 HTTPS 地址")
	response = requests.post(
		webhook,
		json={"msgtype": "text", "text": {"content": str(content)[:2048]}},
		timeout=(5, 30),
	)
	response.raise_for_status()
	body = response.json()
	if int(body.get("errcode") or 0):
		raise frappe.ValidationError(
			f"企业微信群机器人错误 {body.get('errcode')}: {body.get('errmsg')}"
		)
	return body


def notify_system_users(users: list[str] | None, *, subject: str, message: str) -> None:
	"""将 Frappe 用户映射为 Employee，再按企微 UserID 批量发送。失败不阻断主业务。"""
	if not users:
		return
	userids = frappe.get_all(
		"Employee",
		filters={
			"user_id": ["in", list(set(users))],
			"status": "Active",
			"hr_wecom_id": ["is", "set"],
		},
		pluck="hr_wecom_id",
	)
	if not userids:
		return
	try:
		send_text(userids, f"{subject}\n{message}")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "企业微信消息发送失败")
