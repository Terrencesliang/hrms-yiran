import { call } from "./frappe.js";

const METHOD_PREFIX = "employee_roster.hr_roster.api.contract";

function contractCall(method, args = {}, type = "POST") {
	return call(`${METHOD_PREFIX}.${method}`, args, { type });
}

export function getTemplates() {
	return contractCall("get_templates", {}, "GET");
}

export function previewContract(args) {
	return contractCall("preview_contract", args);
}

export function createContractSigning(args) {
	return contractCall("create_contract_signing", args);
}

export function listContractSignings(status) {
	return contractCall("list_contract_signings", { status }, "GET");
}

export function getContractSigning(signing) {
	return contractCall("get_contract_signing", { name: signing }, "GET");
}

export function getSignUrl(signing) {
	return contractCall("get_sign_url", { name: signing });
}

export function urgeContract(signing) {
	return contractCall("urge_contract", { name: signing });
}

export function cancelContract(signing) {
	return contractCall("cancel_contract", { name: signing });
}

export function downloadSignedContract(signing) {
	return contractCall("download_signed_contract", { name: signing });
}

export function syncContractStatus(signing) {
	return contractCall("sync_contract_status", { name: signing });
}
