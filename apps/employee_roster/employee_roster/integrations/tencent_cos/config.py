import os
from dataclasses import dataclass

import frappe
from frappe import _


def _setting(name: str, default: str = "") -> str:
	value = os.environ.get(name)
	if value is None:
		value = frappe.conf.get(name.lower(), default)
	return str(value or default).strip()


def _as_bool(value: str) -> bool:
	return value.lower() in {"1", "true", "yes", "on"}


def is_enabled() -> bool:
	return _as_bool(_setting("USE_TENCENT_COS", "false"))


@dataclass(frozen=True)
class COSSettings:
	bucket: str
	region: str
	secret_id: str
	secret_key: str
	scheme: str
	location: str
	files_location: str
	avatar_location: str
	employee_archive_location: str
	expense_claim_location: str
	signed_url_expires: int


def get_settings() -> COSSettings:
	location = _setting("TENCENT_COS_LOCATION", "hrms/prod").strip("/")
	settings = COSSettings(
		bucket=_setting("TENCENT_COS_BUCKET"),
		region=_setting("TENCENT_COS_REGION"),
		secret_id=_setting("TENCENT_COS_SECRET_ID"),
		secret_key=_setting("TENCENT_COS_SECRET_KEY"),
		scheme=_setting("TENCENT_COS_SCHEME", "https"),
		location=location,
		files_location=_setting("TENCENT_COS_FILES_LOCATION", f"{location}/files").strip("/"),
		avatar_location=_setting("TENCENT_COS_AVATAR_LOCATION", f"{location}/avatars").strip("/"),
		employee_archive_location=_setting(
			"TENCENT_COS_EMPLOYEE_ARCHIVE_LOCATION", f"{location}/employee-archive"
		).strip("/"),
		expense_claim_location=_setting(
			"TENCENT_COS_EXPENSE_CLAIM_LOCATION", f"{location}/expense-claims"
		).strip("/"),
		signed_url_expires=int(_setting("TENCENT_COS_SIGNED_URL_EXPIRES", "600")),
	)
	missing = [
		name
		for name, value in {
			"TENCENT_COS_BUCKET": settings.bucket,
			"TENCENT_COS_REGION": settings.region,
			"TENCENT_COS_SECRET_ID": settings.secret_id,
			"TENCENT_COS_SECRET_KEY": settings.secret_key,
		}.items()
		if not value
	]
	if missing:
		frappe.throw(_("Tencent COS configuration is incomplete: {0}").format(", ".join(missing)))
	if settings.scheme not in {"http", "https"}:
		frappe.throw(_("TENCENT_COS_SCHEME must be http or https"))
	if not 60 <= settings.signed_url_expires <= 3600:
		frappe.throw(_("TENCENT_COS_SIGNED_URL_EXPIRES must be between 60 and 3600 seconds"))
	return settings
