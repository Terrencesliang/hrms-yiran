# Copyright (c) 2026 stillgroup
# License: MIT
"""Ensure approval phase-2 DocTypes/pages and seed schemas."""

import frappe

from employee_roster.hr_roster.approval_admin import seed_approval_admin_data
from employee_roster.install import sync_hr_roster_sidebar


def execute():
	seed_approval_admin_data()
	sync_hr_roster_sidebar()
	frappe.clear_cache()
