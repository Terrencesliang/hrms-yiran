# Copyright (c) 2026 stillgroup
# License: MIT
import csv
import io
import os
import re
import zipfile
from pathlib import PurePosixPath

import frappe
from frappe import _

ALLOWED_ARCHIVE_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx"}
MAX_ARCHIVE_FILES = 1000
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 500 * 1024 * 1024


def _require_archive_permission(permission_type: str = "read") -> None:
	if "System Manager" in frappe.get_roles():
		return
	if not frappe.has_permission("Employee Archive Document", permission_type):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

DEFAULT_DOCUMENT_TYPES = [
	{"document_type": "id_card", "document_name": "身份证原件", "sort_order": 1},
	{"document_type": "education_cert", "document_name": "学历证书", "sort_order": 2},
	{"document_type": "onboarding_form", "document_name": "入职登记表", "sort_order": 3},
	{"document_type": "labor_contract", "document_name": "劳动合同", "sort_order": 4},
	{"document_type": "resignation_cert", "document_name": "离职证明", "sort_order": 5},
]


def seed_document_types():
	for row in DEFAULT_DOCUMENT_TYPES:
		if frappe.db.exists("Archive Document Type", row["document_type"]):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Archive Document Type",
				"document_type": row["document_type"],
				"document_name": row["document_name"],
				"sort_order": row["sort_order"],
				"is_required": 1,
				"is_active": 1,
			}
		)
		doc.insert(ignore_permissions=True)


def get_active_document_types():
	seed_document_types()
	return frappe.get_all(
		"Archive Document Type",
		filters={"is_active": 1},
		fields=["name", "document_type", "document_name", "is_required", "sort_order"],
		order_by="sort_order asc, document_name asc",
	)


def _employee_filters(department=None, status=None):
	filters = {}
	if department:
		filters["department"] = department
	if status:
		filters["status"] = status
	return filters


def _get_employees(department=None, status=None):
	return frappe.get_all(
		"Employee",
		filters=_employee_filters(department, status),
		fields=["name", "employee_name", "employee_number", "department", "status"],
		order_by="employee_number asc",
	)


def _uploaded_map(employee_names):
	if not employee_names:
		return {}
	rows = frappe.get_all(
		"Employee Archive Document",
		filters={"employee": ("in", employee_names), "file": ("!=", "")},
		fields=["employee", "document_type", "file", "name", "uploaded_on", "status"],
	)
	result = {}
	for row in rows:
		result.setdefault(row.employee, {})[row.document_type] = row
	return result


def _file_size_bytes(file_url):
	if not file_url:
		return 0
	return frappe.db.get_value("File", {"file_url": file_url}, "file_size") or 0


def _completeness_score(employee_name):
	emp = frappe.db.get_value(
		"Employee",
		employee_name,
		[
			"employee_name",
			"employee_number",
			"department",
			"designation",
			"date_of_joining",
			"cell_number",
			"person_to_be_contacted",
			"emergency_phone_number",
			"relation",
		],
		as_dict=True,
	)
	if not emp:
		return 0, 0

	checks = [
		bool(emp.employee_name),
		bool(emp.employee_number),
		bool(emp.department),
		bool(emp.designation),
		bool(emp.date_of_joining),
		bool(emp.cell_number),
		bool(emp.person_to_be_contacted and emp.emergency_phone_number and emp.relation),
	]
	education_count = frappe.db.count("Employee Education", {"parent": employee_name})
	checks.append(education_count > 0)

	filled = sum(1 for item in checks if item)
	return filled, len(checks)


def _group_stats(employees, doc_types, uploads):
	required_types = [d.name for d in doc_types if d.is_required]
	total = len(employees)
	archived = 0
	material_count = 0
	storage_bytes = 0
	completeness_total = 0

	for emp in employees:
		emp_uploads = uploads.get(emp.name, {})
		uploaded_required = sum(1 for dt in required_types if emp_uploads.get(dt))
		if required_types and uploaded_required == len(required_types):
			archived += 1
		for row in emp_uploads.values():
			if row.file:
				material_count += 1
				storage_bytes += _file_size_bytes(row.file)
		filled, total_fields = _completeness_score(emp.name)
		if total_fields:
			completeness_total += filled / total_fields

	archive_rate = round(archived / total * 100) if total else 0
	info_rate = round(completeness_total / total * 100) if total else 0
	return {
		"total": total,
		"archived_count": archived,
		"material_count": material_count,
		"storage_bytes": storage_bytes,
		"archive_rate": archive_rate,
		"info_completeness_rate": info_rate,
	}


def _document_progress(employees, doc_types, uploads):
	total = len(employees)
	progress = []
	for doc in doc_types:
		uploaded = 0
		for emp in employees:
			if uploads.get(emp.name, {}).get(doc.name):
				uploaded += 1
		rate = round(uploaded / total * 100) if total else 0
		progress.append(
			{
				"document_type": doc.name,
				"document_name": doc.document_name,
				"uploaded": uploaded,
				"total": total,
				"rate": rate,
			}
		)
	return progress


@frappe.whitelist()
def get_departments() -> list[str]:
	_require_archive_permission()
	return frappe.get_all("Department", fields=["name"], order_by="name asc", pluck="name")


@frappe.whitelist()
def get_archive_options() -> dict:
	_require_archive_permission()
	from frappe.utils.file_manager import get_max_file_size

	return {
		"departments": frappe.get_all("Department", fields=["name"], order_by="name asc", pluck="name"),
		"document_types": get_active_document_types(),
		"max_upload_size": get_max_file_size(),
	}


@frappe.whitelist()
def get_archive_overview(department: str | None = None) -> dict:
	_require_archive_permission()
	doc_types = get_active_document_types()
	active_employees = _get_employees(department=department, status="Active")
	left_employees = _get_employees(department=department, status="Left")
	all_names = [e.name for e in active_employees + left_employees]
	uploads = _uploaded_map(all_names)

	return {
		"document_types": doc_types,
		"active": {
			**_group_stats(active_employees, doc_types, uploads),
			"progress": _document_progress(active_employees, doc_types, uploads),
		},
		"left": {
			**_group_stats(left_employees, doc_types, uploads),
			"progress": _document_progress(left_employees, doc_types, uploads),
		},
	}


@frappe.whitelist()
def list_archive_documents(
	department: str | None = None,
	status: str | None = None,
	document_type: str | None = None,
	missing_only: int | str = 0,
) -> list[dict]:
	_require_archive_permission()
	doc_types = get_active_document_types()
	employees = _get_employees(department=department, status=status or None)
	uploads = _uploaded_map([e.name for e in employees])
	rows = []

	for emp in employees:
		for doc in doc_types:
			if document_type and doc.name != document_type:
				continue
			uploaded = uploads.get(emp.name, {}).get(doc.name)
			if int(missing_only or 0) and uploaded:
				continue
			rows.append(
				{
					"name": uploaded.name if uploaded else "",
					"employee": emp.name,
					"employee_name": emp.employee_name,
					"employee_number": emp.employee_number,
					"department": emp.department,
					"employee_status": emp.status,
					"document_type": doc.name,
					"document_name": doc.document_name,
					"status": uploaded.status if uploaded else "Pending",
					"file": uploaded.file if uploaded else "",
					"uploaded_on": uploaded.uploaded_on if uploaded else "",
					"has_file": bool(uploaded and uploaded.file),
				}
			)

	return rows


def _get_uploaded_zip(file_url: str):
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not file_name:
		frappe.throw(_("The uploaded ZIP file could not be found"), frappe.ValidationError)
	file_doc = frappe.get_doc("File", file_name)
	file_doc.check_permission("read")
	if os.path.splitext(file_doc.file_name or "")[1].lower() != ".zip":
		frappe.throw(_("Only ZIP archives are supported"), frappe.ValidationError)
	content = file_doc.get_content()
	if isinstance(content, str):
		content = content.encode()
	return file_doc, content


def _safe_zip_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
	members = []
	total_bytes = 0
	for member in archive.infolist():
		path = PurePosixPath(member.filename)
		if member.is_dir() or member.filename.startswith("__MACOSX/") or path.name.startswith("."):
			continue
		if path.is_absolute() or ".." in path.parts:
			frappe.throw(_("The ZIP archive contains an unsafe file path"), frappe.ValidationError)
		members.append(member)
		total_bytes += member.file_size
		if len(members) > MAX_ARCHIVE_FILES:
			frappe.throw(_("A maximum of {0} files can be imported at once").format(MAX_ARCHIVE_FILES), frappe.ValidationError)
		if total_bytes > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
			frappe.throw(_("The extracted archive is too large"), frappe.ValidationError)
	return members


def _decoded_zip_filename(member: zipfile.ZipInfo) -> str:
	if member.flag_bits & 0x800:
		return member.filename
	try:
		raw_name = member.filename.encode("cp437")
	except UnicodeEncodeError:
		return member.filename
	for encoding in ("utf-8", "gb18030"):
		try:
			return raw_name.decode(encoding)
		except UnicodeDecodeError:
			continue
	return member.filename


def _normalized_match_value(value) -> str:
	return re.sub(r"\s+", "", str(value or "")).casefold()


def _build_import_indexes():
	employees = _get_employees()
	doc_types = get_active_document_types()
	employee_index = {}
	for employee in employees:
		for value in (employee.name, employee.employee_number, employee.employee_name):
			key = _normalized_match_value(value)
			if key:
				employee_index.setdefault(key, []).append(employee)
	doc_suffixes = []
	for doc_type in doc_types:
		for value in (doc_type.document_name, doc_type.document_type, doc_type.name):
			key = _normalized_match_value(value)
			if key:
				doc_suffixes.append((key, doc_type))
	doc_suffixes.sort(key=lambda item: len(item[0]), reverse=True)
	return employee_index, doc_suffixes


def _match_import_member(filename: str, employee_index: dict, doc_suffixes: list) -> dict:
	basename = PurePosixPath(filename).name
	stem, extension = os.path.splitext(basename)
	if extension.lower() not in ALLOWED_ARCHIVE_EXTENSIONS:
		return {"filename": basename, "state": "error", "message": _("Unsupported file type")}
	normalized_stem = _normalized_match_value(stem)
	doc_type = None
	employee_token = ""
	for suffix, candidate in doc_suffixes:
		for separator in ("-", "_", "—", "–"):
			marker = f"{separator}{suffix}"
			if normalized_stem.endswith(marker):
				doc_type = candidate
				employee_token = normalized_stem[: -len(marker)]
				break
		if doc_type:
			break
	if not doc_type:
		return {"filename": basename, "state": "error", "message": _("Document type was not recognized")}
	matches = employee_index.get(employee_token, [])
	if not matches:
		return {"filename": basename, "state": "error", "message": _("Employee was not found"), "document_name": doc_type.document_name}
	unique_matches = {employee.name: employee for employee in matches}
	if len(unique_matches) != 1:
		return {"filename": basename, "state": "error", "message": _("Employee name is ambiguous; use the employee number"), "document_name": doc_type.document_name}
	employee = next(iter(unique_matches.values()))
	return {
		"filename": basename,
		"state": "ready",
		"message": _("Ready to import"),
		"employee": employee.name,
		"employee_name": employee.employee_name,
		"employee_number": employee.employee_number,
		"document_type": doc_type.name,
		"document_name": doc_type.document_name,
	}


def _build_import_preview(file_url: str, overwrite_existing: int | str = 0):
	from frappe.utils.file_manager import get_max_file_size

	_, content = _get_uploaded_zip(file_url)
	try:
		archive = zipfile.ZipFile(io.BytesIO(content))
	except zipfile.BadZipFile:
		frappe.throw(_("The uploaded file is not a valid ZIP archive"), frappe.ValidationError)
	with archive:
		members = _safe_zip_members(archive)
		employee_index, doc_suffixes = _build_import_indexes()
		items = []
		seen_pairs = set()
		for member in members:
			item = _match_import_member(_decoded_zip_filename(member), employee_index, doc_suffixes)
			item["member_name"] = member.filename
			if member.file_size > get_max_file_size():
				item.update(state="error", message=_("File exceeds the server upload size limit"))
			if item["state"] == "ready":
				pair = (item["employee"], item["document_type"])
				if pair in seen_pairs:
					item.update(state="error", message=_("Duplicate employee and document type in ZIP"))
				else:
					seen_pairs.add(pair)
					existing = frappe.db.get_value(
						"Employee Archive Document",
						{"employee": item["employee"], "document_type": item["document_type"], "file": ("!=", "")},
						"name",
					)
					if existing and not int(overwrite_existing or 0):
						item.update(state="skip", message=_("Already exists"))
			items.append(item)
	return content, items


@frappe.whitelist()
def preview_archive_import(file_url: str, overwrite_existing: int | str = 0) -> dict:
	_require_archive_permission("create")
	_, items = _build_import_preview(file_url, overwrite_existing)
	return {
		"total_files": len(items),
		"ready_count": sum(1 for item in items if item["state"] == "ready"),
		"skipped_count": sum(1 for item in items if item["state"] == "skip"),
		"error_count": sum(1 for item in items if item["state"] == "error"),
		"items": [{key: value for key, value in item.items() if key != "member_name"} for item in items],
	}


def _save_imported_document(item: dict, content: bytes, overwrite_existing: bool) -> None:
	existing_name = frappe.db.get_value(
		"Employee Archive Document",
		{"employee": item["employee"], "document_type": item["document_type"]},
		"name",
	)
	if existing_name:
		if not overwrite_existing:
			return
		_require_archive_permission("write")
		doc = frappe.get_doc("Employee Archive Document", existing_name)
		old_file_url = doc.file
	else:
		_require_archive_permission("create")
		doc = frappe.get_doc(
			{
				"doctype": "Employee Archive Document",
				"employee": item["employee"],
				"document_type": item["document_type"],
				"remarks": _("Imported from ZIP"),
			}
		)
		doc.insert(ignore_permissions=True)
		old_file_url = None

	file_doc = None
	try:
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": item["filename"],
				"content": content,
				"is_private": 1,
				"attached_to_doctype": doc.doctype,
				"attached_to_name": doc.name,
				"attached_to_field": "file",
			}
		)
		file_doc.insert(ignore_permissions=True)
		doc.file = file_doc.file_url
		doc.save(ignore_permissions=True)
	except Exception:
		if file_doc and file_doc.file_url != old_file_url:
			frappe.delete_doc("File", file_doc.name, ignore_permissions=True)
		if not existing_name and doc.name:
			frappe.delete_doc(doc.doctype, doc.name, ignore_permissions=True)
		raise

	if old_file_url and old_file_url != file_doc.file_url:
		old_file_name = frappe.db.get_value("File", {"file_url": old_file_url}, "name")
		if old_file_name:
			frappe.delete_doc("File", old_file_name, ignore_permissions=True)


@frappe.whitelist()
def import_archive_zip(file_url: str, overwrite_existing: int | str = 0) -> dict:
	_require_archive_permission("create")
	content, items = _build_import_preview(file_url, overwrite_existing)
	overwrite = bool(int(overwrite_existing or 0))
	imported = 0
	skipped = 0
	with zipfile.ZipFile(io.BytesIO(content)) as archive:
		for item in items:
			if item["state"] != "ready":
				skipped += 1
				continue
			_save_imported_document(item, archive.read(item["member_name"]), overwrite)
			imported += 1
	return {"imported": imported, "skipped": skipped, "total": len(items)}


@frappe.whitelist()
def upload_archive_document(
	employee: str,
	document_type: str,
	file_url: str,
	remarks: str | None = None,
) -> dict:
	from employee_roster.integrations.tencent_cos.storage import attach_and_organize_file

	existing = frappe.db.get_value(
		"Employee Archive Document",
		{"employee": employee, "document_type": document_type},
		"name",
	)
	permission_type = "write" if existing else "create"
	if not frappe.has_permission("Employee Archive Document", permission_type, doc=existing):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if existing:
		doc = frappe.get_doc("Employee Archive Document", existing)
		old_file_url = doc.file
		doc.file = file_url
		if remarks is not None:
			doc.remarks = remarks
		doc.save(ignore_permissions=True)
	else:
		old_file_url = None
		doc = frappe.get_doc(
			{
				"doctype": "Employee Archive Document",
				"employee": employee,
				"document_type": document_type,
				"file": file_url,
				"remarks": remarks or "",
			}
		)
		doc.insert(ignore_permissions=True)

	organized_url = attach_and_organize_file(
		file_url,
		"Employee Archive Document",
		doc.name,
		"file",
	)
	if organized_url != doc.file:
		doc.file = organized_url
		doc.save(ignore_permissions=True)

	if old_file_url and old_file_url != organized_url:
		old_file_id = frappe.db.get_value("File", {"file_url": old_file_url}, "name")
		if old_file_id:
			frappe.delete_doc("File", old_file_id, ignore_permissions=True)

	return {"name": doc.name, "status": doc.status, "file": doc.file}


@frappe.whitelist()
def delete_archive_document(name: str) -> dict:
	if not frappe.has_permission("Employee Archive Document", "delete"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.delete_doc("Employee Archive Document", name, ignore_permissions=True)
	return {"ok": True}


@frappe.whitelist()
def export_missing_documents(department: str | None = None, status: str | None = None) -> None:
	rows = list_archive_documents(department=department, status=status, missing_only=1)
	output = io.StringIO()
	writer = csv.writer(output)
	writer.writerow(["employee", "employee_name", "employee_number", "department", "document_type", "document_name"])
	for row in rows:
		writer.writerow(
			[
				row["employee"],
				row["employee_name"],
				row["employee_number"],
				row["department"] or "",
				row["document_type"],
				row["document_name"],
			]
		)
	frappe.response["filename"] = "missing_archive_documents.csv"
	frappe.response["filecontent"] = output.getvalue()
	frappe.response["type"] = "csv"


@frappe.whitelist()
def get_archive_export(
	export_type: str = "missing",
	department: str | None = None,
	status: str | None = None,
	document_type: str | None = None,
) -> dict:
	_require_archive_permission("read")
	if export_type not in {"missing", "detail"}:
		frappe.throw(_("Unsupported export type"), frappe.ValidationError)
	rows = list_archive_documents(
		department=department,
		status=status,
		document_type=document_type,
		missing_only=1 if export_type == "missing" else 0,
	)
	output = io.StringIO()
	output.write("\ufeff")
	writer = csv.writer(output)
	if export_type == "missing":
		writer.writerow([_("Employee"), _("Employee Name"), _("Employee Number"), _("Department"), _("Employee Status"), _("Document Type"), _("Document Name")])
		for row in rows:
			writer.writerow([row["employee"], row["employee_name"], row["employee_number"], row["department"] or "", row["employee_status"], row["document_type"], row["document_name"]])
		filename = "employee_archive_missing.csv"
	else:
		writer.writerow([_("Employee"), _("Employee Name"), _("Employee Number"), _("Department"), _("Employee Status"), _("Document Type"), _("Document Name"), _("Archive Status"), _("File URL"), _("Uploaded On")])
		for row in rows:
			writer.writerow([row["employee"], row["employee_name"], row["employee_number"], row["department"] or "", row["employee_status"], row["document_type"], row["document_name"], row["status"], row["file"], row["uploaded_on"]])
		filename = "employee_archive_detail.csv"
	return {"filename": filename, "content": output.getvalue(), "count": len(rows)}


def _employees_index(department: str | None = None, status: str | None = None) -> dict:
	employees = _get_employees(department=department, status=status)
	return {row.name: row for row in employees}


@frappe.whitelist()
def list_education_records(department: str | None = None, status: str | None = None) -> list[dict]:
	_require_archive_permission()
	emp_map = _employees_index(department, status)
	if not emp_map:
		return []
	rows = frappe.get_all(
		"Employee Education",
		filters={"parent": ("in", list(emp_map.keys()))},
		fields=["parent", "school_univ", "qualification", "level", "year_of_passing", "class_per", "maj_opt_subj"],
		order_by="year_of_passing desc",
	)
	result = []
	for row in rows:
		emp = emp_map.get(row.parent)
		if not emp:
			continue
		result.append(
			{
				"employee": emp.name,
				"employee_name": emp.employee_name,
				"employee_number": emp.employee_number,
				"department": emp.department,
				"employee_status": emp.status,
				"school_univ": row.school_univ or "",
				"qualification": row.qualification or "",
				"level": row.level or "",
				"year_of_passing": row.year_of_passing or "",
				"class_per": row.class_per or "",
				"maj_opt_subj": row.maj_opt_subj or "",
			}
		)
	return result


@frappe.whitelist()
def list_work_history(department: str | None = None, status: str | None = None) -> list[dict]:
	_require_archive_permission()
	emp_map = _employees_index(department, status)
	if not emp_map:
		return []
	parents = list(emp_map.keys())
	rows = []

	for row in frappe.get_all(
		"Employee External Work History",
		filters={"parent": ("in", parents)},
		fields=["parent", "company_name", "designation", "salary", "address", "total_experience"],
		order_by="idx asc",
	):
		emp = emp_map[row.parent]
		rows.append(
			{
				"employee": emp.name,
				"employee_name": emp.employee_name,
				"employee_number": emp.employee_number,
				"department": emp.department,
				"history_type": __("外部"),
				"organization": row.company_name or "",
				"designation": row.designation or "",
				"period": row.total_experience or "",
				"detail": row.address or "",
			}
		)

	for row in frappe.get_all(
		"Employee Internal Work History",
		filters={"parent": ("in", parents)},
		fields=["parent", "branch", "department", "designation", "from_date", "to_date"],
		order_by="from_date desc",
	):
		emp = emp_map[row.parent]
		period = " - ".join(filter(None, [str(row.from_date or ""), str(row.to_date or "")]))
		rows.append(
			{
				"employee": emp.name,
				"employee_name": emp.employee_name,
				"employee_number": emp.employee_number,
				"department": emp.department,
				"history_type": __("内部"),
				"organization": row.branch or row.department or "",
				"designation": row.designation or "",
				"period": period,
				"detail": row.department or "",
			}
		)

	return rows


@frappe.whitelist()
def list_emergency_contacts(department: str | None = None, status: str | None = None) -> list[dict]:
	_require_archive_permission()
	employees = _get_employees(department=department, status=status)
	rows = []
	for emp in employees:
		contact_name = frappe.db.get_value(
			"Employee",
			emp.name,
			["person_to_be_contacted", "emergency_phone_number", "relation"],
			as_dict=True,
		)
		if not contact_name:
			continue
		rows.append(
			{
				"employee": emp.name,
				"employee_name": emp.employee_name,
				"employee_number": emp.employee_number,
				"department": emp.department,
				"employee_status": emp.status,
				"contact_name": contact_name.person_to_be_contacted or "",
				"contact_phone": contact_name.emergency_phone_number or "",
				"relation": contact_name.relation or "",
				"is_complete": bool(
					contact_name.person_to_be_contacted
					and contact_name.emergency_phone_number
					and contact_name.relation
				),
			}
		)
	return rows


@frappe.whitelist()
def list_skill_records(department: str | None = None, status: str | None = None) -> list[dict]:
	_require_archive_permission()
	emp_map = _employees_index(department, status)
	if not emp_map:
		return []
	skill_maps = frappe.get_all(
		"Employee Skill Map",
		filters={"employee": ("in", list(emp_map.keys()))},
		fields=["name", "employee"],
	)
	if not skill_maps:
		return []
	map_by_name = {row.name: row.employee for row in skill_maps}
	skill_rows = frappe.get_all(
		"Employee Skill",
		filters={"parent": ("in", list(map_by_name.keys()))},
		fields=["parent", "skill", "proficiency", "evaluation_date"],
		order_by="evaluation_date desc",
	)
	result = []
	for row in skill_rows:
		employee = map_by_name.get(row.parent)
		emp = emp_map.get(employee)
		if not emp:
			continue
		result.append(
			{
				"employee": emp.name,
				"employee_name": emp.employee_name,
				"employee_number": emp.employee_number,
				"department": emp.department,
				"skill": row.skill or "",
				"proficiency": row.proficiency or 0,
				"evaluation_date": row.evaluation_date or "",
			}
		)
	return result
