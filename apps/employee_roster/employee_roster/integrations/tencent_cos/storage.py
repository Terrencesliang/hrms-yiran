import base64
import mimetypes
import os
import re
import unicodedata
import uuid
from datetime import datetime
from functools import lru_cache
from urllib.parse import parse_qs, urlencode, urlparse

import frappe
from frappe import _

from employee_roster.integrations.tencent_cos.config import get_settings, is_enabled

DOWNLOAD_METHOD = "employee_roster.integrations.tencent_cos.storage.download_file"
COS_FILE_MARKER = f"/api/method/{DOWNLOAD_METHOD}"
AVATAR_FIELDS = {"avatar", "image", "user_image"}
HR_MODULES = {"HR", "Payroll", "hr_roster"}
HR_CORE_DOCTYPES = {"Employee"}


def _safe_segment(value: str | None, fallback: str) -> str:
	value = unicodedata.normalize("NFKC", str(value or "")).strip()
	value = re.sub(r"[^\w.-]+", "-", value, flags=re.UNICODE).strip("-._")
	return (value or fallback)[:100]


def _safe_filename(filename: str | None) -> str:
	filename = os.path.basename(str(filename or "attachment"))
	stem, extension = os.path.splitext(filename)
	stem = _safe_segment(stem, "attachment")[:60]
	extension = re.sub(r"[^A-Za-z0-9.]", "", extension.lower())[:16]
	return f"{stem}{extension}"


def _category_location(file_doc, settings) -> str:
	doctype = file_doc.get("attached_to_doctype") or ""
	fieldname = file_doc.get("attached_to_field") or ""
	if doctype in {"User", "Employee"} and fieldname in AVATAR_FIELDS:
		return settings.avatar_location
	if doctype == "Employee Archive Document":
		return settings.employee_archive_location
	if doctype == "Expense Claim":
		return settings.expense_claim_location
	return settings.files_location


def should_store_in_cos(file_doc) -> bool:
	"""Limit COS storage to HR business files; other Frappe files stay on the filesystem."""
	if not is_enabled():
		return False
	if is_cos_file_url(file_doc.get("file_url")):
		return True
	doctype = file_doc.get("attached_to_doctype") or ""
	fieldname = file_doc.get("attached_to_field") or ""
	if not doctype:
		return False
	if doctype == "User":
		return fieldname in AVATAR_FIELDS
	if doctype in HR_CORE_DOCTYPES:
		return True
	try:
		return frappe.get_meta(doctype).module in HR_MODULES
	except frappe.DoesNotExistError:
		return False


def build_object_key(file_doc, *, now: datetime | None = None) -> str:
	settings = get_settings()
	now = now or datetime.now()
	doctype = _safe_segment(file_doc.get("attached_to_doctype"), "unattached")
	docname = _safe_segment(file_doc.get("attached_to_name"), "unattached")
	filename = _safe_filename(file_doc.get("file_name"))
	unique_name = f"{uuid.uuid4().hex}-{filename}"
	return "/".join(
		[
			_category_location(file_doc, settings).strip("/"),
			doctype,
			docname,
			f"{now.year:04d}",
			f"{now.month:02d}",
			unique_name,
		]
	)


def _encode_key(key: str) -> str:
	return base64.urlsafe_b64encode(key.encode()).decode().rstrip("=")


def _decode_key(value: str) -> str:
	padding = "=" * (-len(value) % 4)
	try:
		return base64.urlsafe_b64decode(value + padding).decode()
	except (ValueError, UnicodeDecodeError) as exc:
		frappe.throw(_("Invalid COS object reference"), frappe.ValidationError)
		raise exc


def build_file_url(key: str) -> str:
	return f"{COS_FILE_MARKER}?{urlencode({'key': _encode_key(key)})}"


def is_cos_file_url(file_url: str | None) -> bool:
	return bool(file_url and file_url.startswith(f"{COS_FILE_MARKER}?"))


def object_key_from_url(file_url: str) -> str:
	if not is_cos_file_url(file_url):
		frappe.throw(_("This file is not stored in Tencent COS"), frappe.ValidationError)
	query = parse_qs(urlparse(file_url).query)
	encoded_key = query.get("key", [""])[0]
	if not encoded_key:
		frappe.throw(_("COS object reference is missing"), frappe.ValidationError)
	return _decode_key(encoded_key)


@lru_cache(maxsize=1)
def get_client():
	try:
		from qcloud_cos import CosConfig, CosS3Client
	except ImportError:
		frappe.throw(_("Tencent COS SDK is not installed. Install cos-python-sdk-v5."))
	settings = get_settings()
	config = CosConfig(
		Region=settings.region,
		SecretId=settings.secret_id,
		SecretKey=settings.secret_key,
		Scheme=settings.scheme,
		Timeout=(10, 60),
	)
	return CosS3Client(config)


def write_file(file_doc):
	"""Frappe write_file hook: persist HR business files in COS."""
	if not should_store_in_cos(file_doc):
		return file_doc.save_file_on_filesystem()

	file_doc.is_private = 1
	existing_key = object_key_from_url(file_doc.file_url) if is_cos_file_url(file_doc.file_url) else None
	key = existing_key or build_object_key(file_doc)
	content = file_doc._content.encode() if isinstance(file_doc._content, str) else file_doc._content
	content_type = file_doc.content_type or mimetypes.guess_type(file_doc.file_name)[0] or "application/octet-stream"
	settings = get_settings()
	get_client().put_object(
		Bucket=settings.bucket,
		Key=key,
		Body=content,
		ContentLength=str(len(content)),
		ContentType=content_type,
		ACL="private",
	)
	file_doc.file_name = _safe_filename(file_doc.file_name)
	file_doc.file_url = build_file_url(key)
	return {"file_name": file_doc.file_name, "file_url": file_doc.file_url}


def delete_file_data_content(file_doc, only_thumbnail: bool = False):
	"""Frappe deletion hook: remove COS data only after the last File reference is deleted."""
	from frappe.utils.file_manager import delete_file

	if only_thumbnail:
		delete_file(file_doc.thumbnail_url)
		return
	if not is_cos_file_url(file_doc.file_url):
		delete_file(file_doc.file_url)
		delete_file(file_doc.thumbnail_url)
		return
	settings = get_settings()
	get_client().delete_object(Bucket=settings.bucket, Key=object_key_from_url(file_doc.file_url))
	delete_file(file_doc.thumbnail_url)


def get_object_content(file_url: str) -> bytes:
	settings = get_settings()
	response = get_client().get_object(Bucket=settings.bucket, Key=object_key_from_url(file_url))
	return response["Body"].get_raw_stream().read()


def attach_and_organize_file(file_url: str, doctype: str, docname: str, fieldname: str | None = None) -> str:
	"""Attach an already uploaded file and move it from the unattached prefix to its business folder."""
	file_id = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not file_id:
		return file_url
	file_doc = frappe.get_doc("File", file_id)
	file_doc.check_permission("write")
	old_file_url = file_doc.file_url
	file_doc.attached_to_doctype = doctype
	file_doc.attached_to_name = docname
	file_doc.attached_to_field = fieldname
	if not is_cos_file_url(file_doc.file_url):
		if not should_store_in_cos(file_doc):
			file_doc.save(ignore_permissions=True)
			return file_doc.file_url
		content = file_doc.get_content()
		content = content.encode() if isinstance(content, str) else content
		settings = get_settings()
		new_key = build_object_key(file_doc)
		content_type = mimetypes.guess_type(file_doc.file_name)[0] or "application/octet-stream"
		get_client().put_object(
			Bucket=settings.bucket,
			Key=new_key,
			Body=content,
			ContentLength=str(len(content)),
			ContentType=content_type,
			ACL="private",
		)
		new_url = build_file_url(new_key)
		try:
			file_doc.file_url = new_url
			file_doc.is_private = 1
			file_doc.save(ignore_permissions=True)
		except Exception:
			get_client().delete_object(Bucket=settings.bucket, Key=new_key)
			raise
		from frappe.utils.file_manager import delete_file

		delete_file(old_file_url)
		return new_url

	settings = get_settings()
	old_key = object_key_from_url(file_doc.file_url)
	new_key = build_object_key(file_doc)
	response = get_client().get_object(Bucket=settings.bucket, Key=old_key)
	content = response["Body"].get_raw_stream().read()
	content_type = response.get("Content-Type") or mimetypes.guess_type(file_doc.file_name)[0] or "application/octet-stream"
	get_client().put_object(
		Bucket=settings.bucket,
		Key=new_key,
		Body=content,
		ContentLength=str(len(content)),
		ContentType=content_type,
		ACL="private",
	)
	new_url = build_file_url(new_key)
	try:
		file_doc.file_url = new_url
		file_doc.save(ignore_permissions=True)
	except Exception:
		get_client().delete_object(Bucket=settings.bucket, Key=new_key)
		raise
	get_client().delete_object(Bucket=settings.bucket, Key=old_key)
	return new_url


def object_exists(file_url: str) -> bool:
	from qcloud_cos.cos_exception import CosServiceError

	settings = get_settings()
	try:
		get_client().head_object(Bucket=settings.bucket, Key=object_key_from_url(file_url))
		return True
	except CosServiceError as exc:
		if exc.get_status_code() == 404:
			return False
		raise


@frappe.whitelist()
def download_file(key: str):
	"""Authorize through Frappe, then redirect to a short-lived private COS URL."""
	from frappe.core.doctype.file.utils import find_file_by_url

	expected_url = build_file_url(_decode_key(key))
	file_doc = find_file_by_url(expected_url)
	if not is_enabled() or not file_doc:
		frappe.throw(_("You do not have permission to access this file"), frappe.PermissionError)
	settings = get_settings()
	location = get_client().get_presigned_url(
		Method="GET",
		Bucket=settings.bucket,
		Key=object_key_from_url(file_doc.file_url),
		Expired=settings.signed_url_expires,
	)
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = location
