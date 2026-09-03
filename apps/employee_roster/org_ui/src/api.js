const ORG_API = "employee_roster.hr_roster.page.orgchart.orgchart";

export function call(method, args = {}, extra = {}) {
	return new Promise((resolve, reject) => {
		window.frappe.call({
			method,
			args,
			...extra,
			callback(r) {
				resolve(r.message);
			},
			error(err) {
				reject(err);
			},
		});
	});
}

export function getOrgTree(company) {
	return call(`${ORG_API}.get_org_tree`, { company: company || undefined });
}

export function searchEmployees(txt, company) {
	return call(`${ORG_API}.search_employees`, { txt, company });
}

export function createOrgUnit(args) {
	return call(`${ORG_API}.create_org_unit`, args, {
		freeze: true,
		freeze_message: "正在保存...",
	});
}

export function updateOrgPerson(orgName, role, employee) {
	return call(`${ORG_API}.update_org_person`, {
		org_name: orgName,
		role,
		employee: employee || "",
	});
}

export function getImportTemplate() {
	return call(`${ORG_API}.get_org_import_template`);
}

export function importOrgUnits(fileUrl, company) {
	return call(
		`${ORG_API}.import_org_units`,
		{ file_url: fileUrl, company },
		{ freeze: true, freeze_message: "正在导入组织..." }
	);
}

export async function uploadFile(file) {
	const fd = new FormData();
	fd.append("file", file, file.name);
	fd.append("is_private", "1");
	fd.append("folder", "Home");
	const res = await fetch("/api/method/upload_file", {
		method: "POST",
		headers: { "X-Frappe-CSRF-Token": window.frappe.csrf_token },
		body: fd,
	});
	const data = await res.json();
	if (data.exc || data._server_messages) {
		throw new Error("文件上传失败");
	}
	return data.message;
}

export function toTableTree(nodes) {
	return (nodes || []).map((n) => {
		const row = { ...n, key: n.name };
		if (n.children && n.children.length) {
			row.children = toTableTree(n.children);
		}
		return row;
	});
}

export function collectExpandKeys(nodes, out = []) {
	for (const n of nodes || []) {
		if (n.children?.length) {
			out.push(n.key);
			collectExpandKeys(n.children, out);
		}
	}
	return out;
}

export function flattenTree(nodes, parentKey = null, depth = 0, out = []) {
	for (const n of nodes || []) {
		out.push({ node: n, parentKey, depth });
		if (n.children?.length) flattenTree(n.children, n.key || n.name, depth + 1, out);
	}
	return out;
}

export function vacancyState(node) {
	const quota = Number(node.staff_quota || 0);
	if (!quota) return "";
	const diff = quota - Number(node.employee_count || 0);
	if (diff > 0) return "short";
	if (diff < 0) return "over";
	return "full";
}

export function orgTypeOf(node) {
	if (node.is_employee) return "员工";
	return node.org_type || (node.is_company ? "公司" : "部门");
}

export function filterTree(nodes, pred) {
	const walk = (list) => {
		const out = [];
		for (const n of list || []) {
			const kids = n.children ? walk(n.children) : [];
			if (pred(n) || kids.length) {
				out.push({
					...n,
					children: kids.length ? kids : undefined,
				});
			}
		}
		return out;
	};
	return walk(nodes);
}

export function downloadText(filename, content, mime = "text/csv;charset=utf-8") {
	const blob = new Blob(["\ufeff" + content], { type: mime });
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = filename;
	a.click();
	URL.revokeObjectURL(url);
}
