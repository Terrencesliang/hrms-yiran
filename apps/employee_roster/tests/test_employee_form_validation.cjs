const test = require("node:test");
const assert = require("node:assert/strict");

const {
	validateEmployee,
	validateChineseIdNumber,
} = require("../employee_roster/public/js/employee_form_validation.js");

test("accepts a valid employee document", () => {
	assert.deepEqual(
		validateEmployee(
			{
				date_of_birth: "1990-01-01",
				date_of_joining: "2020-01-01",
				company_email: "employee@example.com",
				cell_number: "+86 138-0000-0000",
				hr_id_type: "身份证",
				hr_id_number: "110101199001010015",
				hr_contract_effective_from: "2026-01-01",
				hr_contract_expire_date: "2028-01-01",
			},
			{ today: "2026-09-09" }
		),
		[]
	);
});

test("reports contact and date errors with their field names", () => {
	const errors = validateEmployee(
		{
			date_of_birth: "2030-01-01",
			date_of_joining: "2020-01-01",
			relieving_date: "2019-12-31",
			company_email: "invalid-email",
			cell_number: "123",
			hr_contract_effective_from: "2026-12-31",
			hr_contract_expire_date: "2026-01-01",
		},
		{ today: "2026-09-09" }
	);

	assert.deepEqual(
		errors.map((item) => item.fieldname),
		[
			"date_of_birth",
			"date_of_joining",
			"relieving_date",
			"hr_contract_expire_date",
			"company_email",
			"cell_number",
		]
	);
});

test("validates Chinese ID format only when ID type is 身份证", () => {
	assert.equal(validateEmployee({ hr_id_type: "身份证", hr_id_number: "123" }).length, 1);
	assert.equal(validateEmployee({ hr_id_type: "护照", hr_id_number: "P123" }).length, 0);
});

test("rejects invalid checksum and mismatched birth date", () => {
	assert.equal(validateChineseIdNumber("11010119900101001X").ok, false);
	assert.equal(validateChineseIdNumber("110101199001010015").ok, true);
	assert.equal(
		validateChineseIdNumber("110101199001010015", { dateOfBirth: "1991-01-01" }).ok,
		false
	);
	assert.match(
		validateChineseIdNumber("110101199013010015").message,
		/出生日期无效/
	);
});
