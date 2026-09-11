"""Gzip Werkzeug/Frappe responses so public tunnels do not ship raw JS/CSS/JSON."""

from __future__ import annotations

import gzip

COMPRESSIBLE_PREFIXES = (
	"text/",
	"application/javascript",
	"application/json",
	"application/xml",
	"application/xhtml+xml",
	"image/svg+xml",
)
SKIP_PATH_PREFIXES = ("/files/", "/private/files/", "/assets/frappe/css/fonts/")
MIN_SIZE = 512
MAX_SIZE = 8 * 1024 * 1024


def _header_map(headers: list[tuple[str, str]]) -> dict[str, str]:
	return {name.lower(): value for name, value in headers}


def _compressible(content_type: str) -> bool:
	ctype = (content_type or "").split(";", 1)[0].strip().lower()
	if not ctype:
		return False
	return any(ctype == prefix or ctype.startswith(prefix) for prefix in COMPRESSIBLE_PREFIXES)


def _apply_gzip_headers(headers: list[tuple[str, str]], body_len: int) -> list[tuple[str, str]]:
	header_map = _header_map(headers)
	next_headers = [
		(name, value)
		for name, value in headers
		if name.lower() not in {"content-length", "content-encoding"}
	]
	next_headers.append(("Content-Encoding", "gzip"))
	next_headers.append(("Content-Length", str(body_len)))
	vary = header_map.get("vary", "")
	if "accept-encoding" not in vary.lower():
		next_headers = [(name, value) for name, value in next_headers if name.lower() != "vary"]
		next_headers.append(("Vary", f"{vary}, Accept-Encoding".strip(", ")))
	return next_headers


class GzipMiddleware:
	def __init__(self, app):
		self.app = app

	def __call__(self, environ, start_response):
		path = environ.get("PATH_INFO") or ""
		accepts_gzip = "gzip" in (environ.get("HTTP_ACCEPT_ENCODING") or "").lower()
		if not accepts_gzip or path.startswith(SKIP_PATH_PREFIXES):
			return self.app(environ, start_response)

		captured: dict = {}
		chunks: list[bytes] = []

		def inner_start(status, headers, exc_info=None):
			captured["status"] = status
			captured["headers"] = list(headers)
			captured["exc_info"] = exc_info

		result = self.app(environ, inner_start)
		close = getattr(result, "close", None)
		streamed = False
		try:
			for chunk in result:
				if isinstance(chunk, str):
					chunk = chunk.encode("utf-8")
				chunks.append(chunk or b"")
				if sum(len(part) for part in chunks) > MAX_SIZE:
					streamed = True
					start_response(
						captured.get("status") or "200 OK",
						captured.get("headers") or [],
						captured.get("exc_info"),
					)
					return _stream(chunks, result, close)
		except Exception:
			if close:
				close()
			raise

		if not streamed and close:
			close()

		body = b"".join(chunks)
		status = str(captured.get("status") or "500 INTERNAL SERVER ERROR")
		headers = list(captured.get("headers") or [])
		header_map = _header_map(headers)
		if (
			status.startswith("200")
			and not header_map.get("content-encoding")
			and MIN_SIZE <= len(body) <= MAX_SIZE
			and _compressible(header_map.get("content-type") or "")
		):
			body = gzip.compress(body, compresslevel=5)
			headers = _apply_gzip_headers(headers, len(body))

		start_response(status, headers, captured.get("exc_info"))
		return [body]


def _stream(chunks, result, close):
	def iterator():
		try:
			yield from chunks
			yield from result
		finally:
			if close:
				close()

	return iterator()


def patch_werkzeug_run_simple() -> None:
	from werkzeug.serving import run_simple as original_run_simple
	import werkzeug.serving as serving

	def run_simple(hostname, port, application, *args, **kwargs):
		return original_run_simple(hostname, port, GzipMiddleware(application), *args, **kwargs)

	serving.run_simple = run_simple
