"""企业微信通讯录同步和消息业务适配。"""
from __future__ import annotations

import re
import time
from importlib import import_module
from typing import Any
from urllib.parse import urlparse

import frappe
import requests
from frappe.utils import now, nowdate
from frappe.utils.nestedset import get_root_of

from .client import WeComClient, WeComConfig, WeComConfigurationError

ACTIVE_WECOM_STATUSES = {1, 4}


def normalize_employee_name(value: str) -> str:
	"""有中文时只保留汉字（去掉英文/韩文/emoji 等后缀）；纯非中文姓名保持不变。"""
	name = str(value or "").strip()
	chinese_parts = re.findall(r"[\u3400-\u9fff]+", name)
	if chinese_parts:
		return "".join(chinese_parts)
	return re.sub(r"\s+", " ", name).strip()


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
	parent_ids = {
		str(row.get("parentid"))
		for row in rows
		if row.get("parentid") is not None
	}
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
				if department_id in parent_ids and not int(doc.is_group or 0):
					doc.is_group = 1
					changed = True
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
	employee_name = str(user.get("name") or "").strip()
	if employee_name:
		rows = frappe.get_all(
			"Employee",
			filters={
				"employee_name": employee_name,
				"status": "Active",
			},
			fields=["name", "hr_wecom_id"],
			limit=2,
		)
		matches = [row.name for row in rows if not row.hr_wecom_id]
		if len(rows) == 1 and len(matches) == 1:
			return str(matches[0])
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
		"cell_number": "mobile",
		"company_email": "email",
	}
	if employee_name := normalize_employee_name(str(user.get("name") or "")):
		values["employee_name"] = employee_name
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
	name = normalize_employee_name(
		str(user.get("name") or user.get("userid") or "")
	)
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
	doc = frappe.get_doc(payload).insert(ignore_permissions=True)
	if userid := str(user.get("userid") or "").strip():
		doc.db_set("hr_wecom_id", userid, update_modified=False)
	return doc


def sync_users(
	*,
	client: WeComClient | None = None,
	create_missing: bool | None = None,
	commit_every: int = 0,
) -> dict[str, Any]:
	client = client or WeComClient()
	company = _company(client.config)
	create_missing = (
		client.config.create_missing_employees if create_missing is None else create_missing
	)
	created = updated = skipped = failed = 0
	errors: list[dict[str, str]] = []
	remote_users = client.list_user_ids()
	total = len(remote_users)
	for index, row in enumerate(remote_users, start=1):
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
			else:
				doc = frappe.get_doc("Employee", employee_name)
				values = _employee_values(user)
				for fieldname, value in values.items():
					setattr(doc, fieldname, value)
				doc.save(ignore_permissions=True)
				doc.db_set("hr_wecom_id", userid, update_modified=False)
				updated += 1
		except Exception as exc:
			failed += 1
			errors.append({"userid": userid, "error": str(exc)[:300]})
		if commit_every and index % commit_every == 0:
			frappe.db.commit()
			print(
				f"企微员工导入进度: {index}/{total}，"
				f"创建 {created}，更新 {updated}，跳过 {skipped}，失败 {failed}",
				flush=True,
			)
	if commit_every:
		frappe.db.commit()
		print(
			f"企微员工导入完成: {total}/{total}，"
			f"创建 {created}，更新 {updated}，跳过 {skipped}，失败 {failed}",
			flush=True,
		)
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


def import_missing_users() -> dict[str, Any]:
	"""管理命令入口：显式创建企微中尚未匹配的 Employee。"""
	previous = getattr(frappe.flags, "in_import", False)
	frappe.flags.in_import = True
	try:
		return sync_users(create_missing=True, commit_every=20)
	finally:
		frappe.flags.in_import = previous


def employee_import_status() -> dict[str, int]:
	samples = frappe.get_all(
		"Employee",
		fields=["hr_wecom_id"],
		order_by="creation desc",
		limit=5,
	)
	duplicate_counts = frappe.db.sql(
		"""
		select count(*)
		from `tabEmployee`
		group by employee_name
		having count(*) > 1
		"""
	)
	return {
		"employees": frappe.db.count("Employee"),
		"active": frappe.db.count("Employee", {"status": "Active"}),
		"wecom_bound": frappe.db.count("Employee", {"hr_wecom_id": ["is", "set"]}),
		"recent_with_wecom_id": sum(bool(row.hr_wecom_id) for row in samples),
		"duplicate_name_groups": len(duplicate_counts),
		"duplicate_extra_rows": sum(int(row[0]) - 1 for row in duplicate_counts),
	}


def name_cleanup_preview() -> dict[str, int]:
	rows = frappe.get_all(
		"Employee",
		fields=["name", "employee_name", "hr_wecom_id"],
	)
	groups: dict[str, list[Any]] = {}
	changed = 0
	for row in rows:
		normalized = normalize_employee_name(row.employee_name)
		if normalized and normalized != row.employee_name:
			changed += 1
		if normalized:
			groups.setdefault(normalized, []).append(row)
	duplicate_groups = [group for group in groups.values() if len(group) > 1]
	auto_mergeable = [
		group
		for group in duplicate_groups
		if len(group) == 2
		and sum(bool(row.hr_wecom_id) for row in group) == 1
	]
	return {
		"employees": len(rows),
		"names_to_normalize": changed,
		"duplicate_groups_after_normalize": len(duplicate_groups),
		"safe_merge_groups": len(auto_mergeable),
		"ambiguous_groups": len(duplicate_groups) - len(auto_mergeable),
	}


def cleanup_and_merge_employee_names() -> dict[str, Any]:
	"""合并“中文原档案 + 带英文企微档案”，保留原档案编号和所有关联。"""
	delete_doc_module = import_module("frappe.model.delete_doc")
	original_delete_for_document = delete_doc_module.delete_for_document
	original_clear_cache = frappe.clear_cache
	# 批量 merge 时逐条删除 __global_search 会与后台索引器互锁；
	# 逐人全站 clear-cache / 搜索重建也会把百人合并放大到数小时。
	delete_doc_module.delete_for_document = lambda _doc: None
	frappe.clear_cache = lambda *args, **kwargs: None
	rows = frappe.get_all(
		"Employee",
		fields=[
			"name",
			"employee_name",
			"first_name",
			"hr_wecom_id",
			"department",
			"cell_number",
			"company_email",
		],
	)
	groups: dict[str, list[Any]] = {}
	for row in rows:
		normalized = normalize_employee_name(row.employee_name)
		if normalized:
			groups.setdefault(normalized, []).append(row)

	merged = normalized_count = skipped = 0
	errors: list[dict[str, str]] = []
	for normalized, group in groups.items():
		if len(group) == 1:
			row = group[0]
			if normalized != row.employee_name:
				frappe.db.set_value(
					"Employee",
					row.name,
					{"employee_name": normalized, "first_name": normalized},
					update_modified=False,
				)
				normalized_count += 1
			continue
		bound = [row for row in group if row.hr_wecom_id]
		unbound = [row for row in group if not row.hr_wecom_id]
		if len(group) != 2 or len(bound) != 1 or len(unbound) != 1:
			skipped += 1
			continue
		source = bound[0]
		target = unbound[0]
		for attempt in range(3):
			try:
				updates = {
					"employee_name": normalized,
					"first_name": normalized,
					"hr_wecom_id": source.hr_wecom_id,
				}
				for fieldname in ("department", "cell_number", "company_email"):
					if not getattr(target, fieldname, None) and getattr(source, fieldname, None):
						updates[fieldname] = getattr(source, fieldname)
				frappe.db.set_value(
					"Employee", target.name, updates, update_modified=False
				)
				frappe.rename_doc(
					"Employee",
					source.name,
					target.name,
					merge=True,
					force=True,
					show_alert=False,
					rebuild_search=False,
				)
				frappe.db.set_value(
					"Employee",
					target.name,
					{
						"employee_name": normalized,
						"first_name": normalized,
						"hr_wecom_id": source.hr_wecom_id,
					},
					update_modified=False,
				)
				frappe.db.commit()
				merged += 1
				break
			except frappe.QueryDeadlockError as exc:
				frappe.db.rollback()
				if attempt < 2:
					time.sleep(0.5 * (attempt + 1))
					continue
				errors.append(
					{
						"source": source.name,
						"target": target.name,
						"error": str(exc)[:300],
					}
				)
			except Exception as exc:
				frappe.db.rollback()
				errors.append(
					{
						"source": source.name,
						"target": target.name,
						"error": str(exc)[:300],
					}
				)
				break
		if merged and merged % 10 == 0:
			print(f"姓名去重进度: 已合并 {merged}", flush=True)
	frappe.db.commit()
	delete_doc_module.delete_for_document = original_delete_for_document
	frappe.clear_cache = original_clear_cache
	frappe.clear_cache(doctype="Employee")
	return {
		"merged": merged,
		"normalized": normalized_count,
		"skipped": skipped,
		"failed": len(errors),
		"errors": errors,
	}


def repair_userid_bindings() -> dict[str, int]:
	"""仅读取尚未绑定的远端成员，按唯一姓名修复 UserID。"""
	client = WeComClient()
	updated = ambiguous = missing = 0
	bound = set(
		frappe.get_all(
			"Employee",
			filters={"hr_wecom_id": ["is", "set"]},
			pluck="hr_wecom_id",
		)
	)
	userids = [
		str(row.get("userid"))
		for row in client.list_user_ids()
		if row.get("userid") and str(row.get("userid")) not in bound
	]
	for index, userid in enumerate(userids, start=1):
		user = client.get_user(userid)
		employee_name = str(user.get("name") or "").strip()
		if not employee_name:
			missing += 1
			continue
		rows = frappe.get_all(
			"Employee",
			filters={"employee_name": employee_name, "status": "Active"},
			fields=["name", "hr_wecom_id"],
			limit=3,
		)
		candidates = [row.name for row in rows if not row.hr_wecom_id]
		if len(candidates) != 1:
			ambiguous += 1
			continue
		frappe.db.set_value(
			"Employee", candidates[0], "hr_wecom_id", userid, update_modified=False
		)
		updated += 1
		if index % 10 == 0:
			frappe.db.commit()
	frappe.db.commit()
	return {"updated": updated, "ambiguous": ambiguous, "missing": missing}


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


def send_textcard(
	userids: list[str] | str,
	*,
	title: str,
	description: str,
	url: str,
	btntxt: str = "查看详情",
) -> dict[str, Any]:
	client = WeComClient()
	recipients = (
		"|".join(dict.fromkeys(item for item in userids if item))
		if isinstance(userids, list)
		else str(userids)
	)
	if not recipients:
		raise frappe.ValidationError("企业微信消息缺少接收人")
	if not str(url or "").strip():
		raise frappe.ValidationError("企业微信卡片消息缺少跳转链接")
	return client.send_message(
		{
			"touser": recipients,
			"msgtype": "textcard",
			"agentid": client.config.agent_id,
			"textcard": {
				"title": str(title)[:128],
				"description": str(description)[:512],
				"url": str(url).strip(),
				"btntxt": str(btntxt or "查看详情")[:16],
			},
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


def _approval_action_path(
	document_type: str | None = None,
	document_name: str | None = None,
) -> str:
	from urllib.parse import urlencode

	params: dict[str, str] = {}
	if document_name:
		if document_type == "Approval Instance":
			params["instance"] = document_name
		elif document_type == "Approval Task":
			params["task"] = document_name
	query = urlencode(params)
	return f"/app/approval-workspace{('?' + query) if query else ''}"


def notify_system_users(
	users: list[str] | None,
	*,
	subject: str,
	message: str,
	document_type: str | None = None,
	document_name: str | None = None,
	action_url: str | None = None,
) -> None:
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
	content = f"{subject}\n{message}"
	try:
		from .oauth import build_authorize_url

		card_url = action_url or build_authorize_url(
			next_path=_approval_action_path(document_type, document_name)
		)
		send_textcard(
			userids,
			title=subject,
			description=message,
			url=card_url,
			btntxt="打开处理",
		)
	except Exception:
		try:
			send_text(userids, content)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "企业微信消息发送失败")
