// Copyright (c) 2026 stillgroup
frappe.ui.form.on("Payroll Entry", {
	refresh(frm) {
		if (frm.doc.docstatus !== 0 || frm.is_new() || !(frm.doc.employees || []).length) {
			return;
		}
		frm.add_custom_button(__("Create Attendance Deductions"), () => {
			frappe.call({
				method: "employee_roster.hr_roster.attendance_deduction.payroll_integration.create_attendance_deduction_summaries",
				args: { payroll_entry: frm.doc.name },
				freeze: true,
				callback() {
					frm.reload_doc();
				},
			});
		}).addClass("btn-primary");
	},
});

frappe.ui.form.on("Attendance Deduction Summary", {
	refresh(frm) {
		if (frm.doc.docstatus !== 0 || frm.is_new()) return;
		frm.add_custom_button(__("Recalculate"), () => {
			frappe.call({
				method: "employee_roster.hr_roster.attendance_deduction.engine.preview_deduction",
				args: {
					employee: frm.doc.employee,
					start_date: frm.doc.start_date,
					end_date: frm.doc.end_date,
				},
				callback(r) {
					if (r.message) {
						frappe.msgprint({
							title: __("Preview"),
							message: `<pre>${JSON.stringify(r.message, null, 2)}</pre>`,
							indicator: "blue",
						});
					}
				},
			});
		});
	},
});
