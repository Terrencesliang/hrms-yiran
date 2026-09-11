#!/usr/bin/env python3
"""Start Frappe's development server with gzip enabled on compressible responses."""

from __future__ import annotations

import os
import sys

BENCH_DIR = "/home/frappe/frappe-bench"
SITES_DIR = os.path.join(BENCH_DIR, "sites")
DEPLOY_DIR = "/workspace/source/deploy"

os.chdir(SITES_DIR)
os.environ.setdefault("FRAPPE_BIND_ADDR", "0.0.0.0")
if DEPLOY_DIR not in sys.path:
	sys.path.insert(0, DEPLOY_DIR)

from pathlib import Path

from gzip_wsgi import patch_werkzeug_run_simple

patch_werkzeug_run_simple()

from frappe.app import serve

site = (os.environ.get("SITE_NAME") or "").strip()
current = Path("currentsite.txt")
if not site and current.exists():
	site = current.read_text(encoding="utf-8").strip()

serve(
	port=int(os.environ.get("FRAPPE_PORT", "8000")),
	no_reload=True,
	sites_path=".",
	site=site or None,
	bind_addr=os.environ.get("FRAPPE_BIND_ADDR", "0.0.0.0"),
)
