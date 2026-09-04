# Copyright (c) 2026 stillgroup
# License: MIT
from employee_roster.hr_roster.approval_admin import seed_approval_admin_data
from employee_roster.install import sync_hr_roster_sidebar


def execute():
	seed_approval_admin_data()
	sync_hr_roster_sidebar()
