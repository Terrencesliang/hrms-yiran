# Copyright (c) 2026 stillgroup
# License: MIT
"""Ensure composite index on Approval Instance (approval_form, status)."""

import frappe


def execute():
	if not frappe.db.exists("DocType", "Approval Instance"):
		return
	# Idempotent: Frappe add_index skips / no-ops when already present in most versions;
	# wrap to keep migrate safe across MariaDB/Postgres.
	try:
		frappe.db.add_index("Approval Instance", ["approval_form", "status"])
	except Exception as exc:
		# Index may already exist with a slightly different name
		msg = str(exc).lower()
		if "already exists" in msg or "duplicate" in msg:
			return
		raise
