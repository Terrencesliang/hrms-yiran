"""Loaded only when PYTHONPATH includes this directory. Safe if Werkzeug is absent."""

from __future__ import annotations

import sys
from pathlib import Path

_deploy_dir = str(Path(__file__).resolve().parent.parent)
if _deploy_dir not in sys.path:
	sys.path.insert(0, _deploy_dir)

try:
	from gzip_wsgi import patch_werkzeug_run_simple
except ModuleNotFoundError:
	patch_werkzeug_run_simple = None

if patch_werkzeug_run_simple is not None:
	try:
		patch_werkzeug_run_simple()
	except ModuleNotFoundError:
		pass
