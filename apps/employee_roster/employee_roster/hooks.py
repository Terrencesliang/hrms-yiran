app_name = "employee_roster"
app_title = "员工花名册"
app_publisher = "stillgroup"
app_description = "员工花名册 数据面板与员工列表合并页面"
app_email = "huangxianrun@stillgroup.net"
app_license = "mit"

after_install = "employee_roster.install.after_install"

# Send non-GET requests for this app's endpoints as native `application/json`
# bodies instead of form-encoded, per-key JSON-stringified values.
use_json_request_body = True

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "employee_roster",
# 		"logo": "/assets/employee_roster/logo.png",
# 		"title": "员工花名册",
# 		"route": "/employee_roster",
# 		"has_permission": "employee_roster.api.permission.has_app_permission",
# 	}
# ]

# The dock, the rail down the left of the desk, is a document rather than a hook. Author it in
# Manage Dock on a developer-mode site and press Export to App, and it is written to
# `employee_roster/dock/employee_roster/employee_roster.json` for git to carry. An app that ships none has no
# rail: its sidebar gets a switcher in the header instead.
#
# A companion app, one that extends a host app rather than standing on its own, says so with
# `mount_on` on that same record, and its entries are appended to the host's rail. Mounting keeps
# the companion off the apps screen, so it takes precedence over any add_to_apps_screen above.

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
	"/assets/employee_roster/css/roster.css",
	"/assets/employee_roster/css/orgchart.css",
	"/assets/employee_roster/css/recruiting.css",
	"/assets/employee_roster/css/attendance_rules.css",
	"/assets/employee_roster/css/attendance_deduction_rule_form.css?v=20260303b",
	"/assets/employee_roster/css/unified_sidebar.css?v=20260903c",
]
app_include_js = [
	"/assets/employee_roster/js/recruiting_candidates.js",
	"/assets/employee_roster/js/unified_sidebar.js?v=20260903c",
]

# include js, css files in header of web template
# web_include_css = "/assets/employee_roster/css/employee_roster.css"
# web_include_js = "/assets/employee_roster/js/employee_roster.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "employee_roster/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
page_js = {
	"recruiting-active": "public/js/recruiting_active.js",
	"recruiting-hired": "public/js/recruiting_hired.js",
	"recruiting-rejected": "public/js/recruiting_rejected.js",
	"attendance-rules": "public/js/attendance_rules_v3.js",
}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_list_js = {
	"Employee": "public/js/employee_list.js",
}
doctype_js = {
	"Payroll Entry": "public/js/attendance_deduction.js",
	"Attendance Deduction Summary": "public/js/attendance_deduction.js",
	"Attendance Deduction Rule": "public/js/attendance_deduction_rule_form.js",
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "employee_roster/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Setup Wizard
# ------------

# open a fresh site's setup in this app's own UI instead of the desk wizard.
# must be a non-desk route (not under /desk or /app); to customize setup within
# desk, use setup_wizard_stages / setup_wizard_complete instead.
# setup_wizard_url = "/employee_roster/setup"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "employee_roster.utils.jinja_methods",
# 	"filters": "employee_roster.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "employee_roster.install.before_install"
# after_install = "employee_roster.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "employee_roster.uninstall.before_uninstall"
# after_uninstall = "employee_roster.uninstall.after_uninstall"

# Disable / Enable
# ----------------
# Called when this app is logically disabled or re-enabled on a site,
# without uninstalling it. Use this to hide/restore fields this app adds
# to other apps' doctypes.

# before_disable = "employee_roster.uninstall.before_disable"
# after_disable = "employee_roster.uninstall.after_disable"
# before_enable = "employee_roster.install.before_enable"
# after_enable = "employee_roster.install.after_enable"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "employee_roster.utils.before_app_install"
# after_app_install = "employee_roster.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "employee_roster.utils.before_app_uninstall"
# after_app_uninstall = "employee_roster.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "employee_roster.build.after_build"

# To hook into the build process of other apps
# The list of apps being built is passed as an argument

# after_app_build = "employee_roster.build.after_app_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "employee_roster.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["employee_roster.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Salary Slip": {
		"validate": "employee_roster.hr_roster.attendance_deduction.payroll_integration.adjust_salary_slip_payment_days",
	},
	"Payroll Entry": {
		"on_submit": "employee_roster.hr_roster.attendance_deduction.payroll_integration.on_payroll_entry_submit",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"employee_roster.tasks.all"
# 	],
# 	"daily": [
# 		"employee_roster.tasks.daily"
# 	],
# 	"hourly": [
# 		"employee_roster.tasks.hourly"
# 	],
# 	"weekly": [
# 		"employee_roster.tasks.weekly"
# 	],
# 	"monthly": [
# 		"employee_roster.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "employee_roster.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "employee_roster.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "employee_roster.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "employee_roster.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["employee_roster.utils.before_request"]
# after_request = ["employee_roster.utils.after_request"]

# Job Events
# ----------
# before_job = ["employee_roster.utils.before_job"]
# after_job = ["employee_roster.utils.after_job"]

# after_file_upload = ["employee_roster.utils.after_file_upload"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"employee_roster.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

# Require all whitelisted methods to have type annotations
require_type_annotated_api_methods = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

