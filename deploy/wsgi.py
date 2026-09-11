"""WSGI entry for gunicorn: Frappe app + /assets + /files static middleware."""

from __future__ import annotations

import os
from pathlib import Path

BENCH_DIR = Path("/home/frappe/frappe-bench")
SITES_DIR = BENCH_DIR / "sites"

os.chdir(SITES_DIR)

site = (os.environ.get("SITE_NAME") or "").strip()
if not site:
	current = SITES_DIR / "currentsite.txt"
	if current.exists():
		site = current.read_text(encoding="utf-8").strip()

import frappe.app as frappe_app

if site:
	frappe_app._site = site
frappe_app._sites_path = "."

# bench serve wraps statics; bare gunicorn does not — without this, /assets 404
# and the WeCom QR login script never loads.
application = frappe_app.application_with_statics()
