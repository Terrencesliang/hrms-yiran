(function () {
	const CONFIG_METHOD = "employee_roster.integrations.wecom.api.get_web_login_config";
	const WW_LOGIN_SCRIPT =
		"https://rescdn.qqmail.com/node/ww/wwopenmng/js/sso/wwLogin-1.2.7.js";

	function nextPathFromLocation() {
		const params = new URLSearchParams(window.location.search || "");
		return params.get("redirect-to") || params.get("redirect_to") || "/desk/hr-home";
	}

	function showMessage(el, text, isError) {
		if (!el) return;
		el.textContent = text || "";
		el.hidden = !text;
		el.classList.toggle("is-error", !!isError);
	}

	function callGet(method, args) {
		const params = new URLSearchParams();
		Object.keys(args || {}).forEach((key) => {
			if (args[key] != null && args[key] !== "") params.set(key, args[key]);
		});
		const qs = params.toString();
		return fetch("/api/method/" + method + (qs ? "?" + qs : ""), {
			method: "GET",
			credentials: "same-origin",
			headers: { Accept: "application/json" },
		}).then(async (response) => {
			const payload = await response.json().catch(() => ({}));
			if (!response.ok || payload.exc_type || payload.exception) {
				const message =
					payload.message || payload.exc || "请求失败 " + response.status;
				throw new Error(String(message).slice(0, 300));
			}
			return payload.message ?? payload;
		});
	}

	function loadScript(src) {
		return new Promise((resolve, reject) => {
			if (window.WwLogin) {
				resolve();
				return;
			}
			const existing = document.querySelector('script[data-wecom-wwlogin="1"]');
			if (existing) {
				existing.addEventListener("load", () => resolve());
				existing.addEventListener("error", () => reject(new Error("load failed")));
				return;
			}
			const script = document.createElement("script");
			script.src = src;
			script.async = true;
			script.dataset.wecomWwlogin = "1";
			script.onload = () => resolve();
			script.onerror = () => reject(new Error("企微扫码脚本加载失败"));
			document.head.appendChild(script);
		});
	}

	function mountFallback(root, config, statusEl) {
		root.innerHTML = "";
		const link = document.createElement("a");
		link.className = "es-button w-full arco-login-btn btn-login-option wecom-qr-fallback";
		link.href = config.web_login_url;
		link.textContent = "企业微信扫码登录";
		root.appendChild(link);
		showMessage(statusEl, "点击后将打开企业微信扫码页", false);
	}

	function mountWwLogin(root, config, statusEl) {
		const panel = config.panel || {};
		root.innerHTML = "";
		const frameHost = document.createElement("div");
		frameHost.id = "wecom_qr_frame";
		root.appendChild(frameHost);
		// eslint-disable-next-line no-new
		new window.WwLogin({
			id: "wecom_qr_frame",
			appid: panel.appid,
			agentid: panel.agentid,
			redirect_uri: encodeURIComponent(panel.redirect_uri || config.callback_url),
			state: panel.state || "",
			href: "",
		});
		showMessage(statusEl, "请使用企业微信扫一扫", false);
	}

	function initWeComLogin() {
		const root = document.getElementById("wecom-qr-login");
		if (!root || root.dataset.ready === "1") return;
		root.dataset.ready = "1";
		const statusEl = document.getElementById("wecom-qr-status");
		const wrap = root.closest(".wecom-qr-wrap");

		callGet(CONFIG_METHOD, { next_path: nextPathFromLocation() })
			.then((config) => {
				if (!config || !config.configured) {
					if (wrap) wrap.hidden = true;
					return null;
				}
				if (wrap) wrap.hidden = false;
				return loadScript(WW_LOGIN_SCRIPT)
					.then(() => {
						if (typeof window.WwLogin !== "function") {
							mountFallback(root, config, statusEl);
							return;
						}
						mountWwLogin(root, config, statusEl);
					})
					.catch(() => mountFallback(root, config, statusEl));
			})
			.catch(() => {
				if (wrap) wrap.hidden = true;
			});
	}

	function boot() {
		initWeComLogin();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", boot);
	} else {
		boot();
	}
})();
