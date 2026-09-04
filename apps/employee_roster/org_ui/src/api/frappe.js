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

export function downloadText(filename, content, mime = "text/csv;charset=utf-8") {
	const blob = new Blob(["\ufeff" + content], { type: mime });
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = filename;
	a.click();
	URL.revokeObjectURL(url);
}
