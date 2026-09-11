"""为穿透/开发服务器提供可缓存的 OrgUI gzip 静态资源。"""
from __future__ import annotations

import gzip
from functools import lru_cache
from pathlib import Path

import frappe
from werkzeug.wrappers import Response


def _asset_path(filename: str) -> Path:
	return (
		Path(frappe.get_app_path("employee_roster"))
		/ "public"
		/ "org_ui"
		/ filename
	)


@lru_cache(maxsize=8)
def _asset_bytes(filename: str, compressed: bool, mtime_ns: int, size: int) -> bytes:
	# mtime/size 参与 key，避免同步新产物后仍吐旧 gzip 缓存。
	content = _asset_path(filename).read_bytes()
	return gzip.compress(content, compresslevel=6) if compressed else content


def _response(filename: str, mimetype: str) -> Response:
	accepts_gzip = "gzip" in str(
		frappe.get_request_header("Accept-Encoding") or ""
	).lower()
	path = _asset_path(filename)
	stat = path.stat()
	response = Response(
		_asset_bytes(filename, accepts_gzip, stat.st_mtime_ns, stat.st_size),
		mimetype=mimetype,
	)
	if accepts_gzip:
		response.headers["Content-Encoding"] = "gzip"
	response.headers["Cache-Control"] = "public, max-age=43200, immutable"
	response.headers["Vary"] = "Accept-Encoding"
	return response


@frappe.whitelist(allow_guest=True)
def org_ui_js() -> Response:
	return _response("org_ui.js", "application/javascript")


@frappe.whitelist(allow_guest=True)
def org_ui_css() -> Response:
	return _response("org_ui.css", "text/css")
