import { call } from "./frappe.js";

const METHOD_PREFIX = "employee_roster.hr_roster.api.contract";

function errorMessage(value, fallback = "合同服务操作失败") {
	if (!value) return fallback;
	if (typeof value === "string") {
		try {
			return errorMessage(JSON.parse(value), value);
		} catch (error) {
			return value;
		}
	}
	const payload = value?.responseJSON || value?.response?.data || value;
	if (payload?._server_messages) {
		try {
			const messages = JSON.parse(payload._server_messages);
			const message = messages.map((item) => errorMessage(item, "")).filter(Boolean).join("；");
			if (message) return message;
		} catch (error) {
			/* Fall through to the regular response fields. */
		}
	}
	return (
		payload?.error?.message ||
		payload?.error ||
		payload?.message ||
		payload?.detail ||
		payload?.exc_type ||
		value?.message ||
		fallback
	);
}

function contractCall(method, args = {}, type = "POST") {
	return call(`${METHOD_PREFIX}.${method}`, args, { type })
		.then((result) => {
			if (result?.ok === false) {
				throw new Error(String(errorMessage(result)));
			}
			return result;
		})
		.catch((error) => {
			throw error instanceof Error ? error : new Error(String(errorMessage(error)));
		});
}

export function getTemplates() {
	return contractCall("get_templates", {}, "GET");
}

export function previewContract(args) {
	return contractCall("preview_contract", args);
}

export function getContractEditorPreview(args) {
	return contractCall("get_contract_editor_preview", args);
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

export function getCompanySignUrl(signing) {
	return contractCall("get_sign_url", { name: signing, actor_type: "company" });
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

export function retryContract(signing) {
	return contractCall("retry_contract", { name: signing });
}

export function getFadadaSeals() {
	return contractCall("get_fadada_seals", {}, "GET");
}

export function getFadadaSealStatus(sealId) {
	return contractCall("get_fadada_seal_status", { seal_id: sealId }, "GET");
}

export function getFadadaSealAuthorizationUrl(sealId, businessId, redirectUrl = "") {
	return contractCall("get_fadada_seal_authorization_url", {
		seal_id: sealId,
		business_id: businessId,
		redirect_url: redirectUrl,
	});
}

export function configureFadadaTemplate(template, sealId, businessId) {
	return contractCall("configure_fadada_template", {
		template,
		seal_id: sealId,
		business_id: businessId,
	});
}

export function getFadadaTemplateEditUrl(template) {
	return contractCall("get_fadada_template_edit_url", { template });
}
