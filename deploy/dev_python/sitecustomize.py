"""Development-only Python startup hooks for the Docker Bench process."""

try:
	from werkzeug.middleware.shared_data import SharedDataMiddleware
except ModuleNotFoundError:
	# The outer Bench launcher uses the system interpreter; the actual web
	# process loads this module again inside Bench's virtual environment.
	SharedDataMiddleware = None


if SharedDataMiddleware is not None:
	_shared_data_init = SharedDataMiddleware.__init__
	_shared_data_call = SharedDataMiddleware.__call__

	def _disable_static_cache(self, *args, **kwargs):
		kwargs["cache"] = False
		return _shared_data_init(self, *args, **kwargs)

	def _send_no_cache_headers(self, environ, start_response):
		def patch_start_response(status, headers, exc_info=None):
			headers = [
				(name, value)
				for name, value in headers
				if name.lower() not in {"cache-control", "expires", "etag"}
			]
			headers.append(("Cache-Control", "no-store,no-cache,must-revalidate,max-age=0"))
			return start_response(status, headers, exc_info)

		return _shared_data_call(self, environ, patch_start_response)

	SharedDataMiddleware.__init__ = _disable_static_cache
	SharedDataMiddleware.__call__ = _send_no_cache_headers
