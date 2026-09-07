import { onBeforeUnmount, onMounted, ref } from "vue";

export function readHrDarkTheme() {
	if (typeof document === "undefined") return false;
	const root = document.documentElement;
	const body = document.body;
	return (
		root.getAttribute("data-theme") === "dark" ||
		root.getAttribute("arco-theme") === "dark" ||
		body.getAttribute("data-theme") === "dark" ||
		body.getAttribute("arco-theme") === "dark"
	);
}

export function useHrTheme() {
	const isDark = ref(readHrDarkTheme());
	let observer = null;

	function syncTheme() {
		isDark.value = readHrDarkTheme();
	}

	onMounted(() => {
		syncTheme();
		if (typeof MutationObserver === "undefined") return;
		observer = new MutationObserver(syncTheme);
		observer.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ["data-theme", "arco-theme"],
		});
		observer.observe(document.body, {
			attributes: true,
			attributeFilter: ["data-theme", "arco-theme"],
		});
	});

	onBeforeUnmount(() => {
		observer?.disconnect();
		observer = null;
	});

	return { isDark, syncTheme };
}

export function hrChartTheme(isDark) {
	return {
		surface: isDark ? "#232324" : "#ffffff",
		text1: isDark ? "rgba(255, 255, 255, 0.9)" : "#1D2129",
		text2: isDark ? "rgba(255, 255, 255, 0.68)" : "#4E5969",
		text3: isDark ? "rgba(255, 255, 255, 0.45)" : "#86909C",
		splitLine: isDark ? "rgba(255, 255, 255, 0.08)" : "#E5E6EB",
	};
}
