import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
	plugins: [vue()],
	define: {
		"process.env.NODE_ENV": JSON.stringify("production"),
	},
	build: {
		lib: {
			entry: path.resolve(__dirname, "src/main.js"),
			name: "OrgUI",
			formats: ["iife"],
			fileName: () => "org_ui.js",
		},
		outDir: path.resolve(__dirname, "../employee_roster/public/org_ui"),
		emptyOutDir: true,
		cssCodeSplit: false,
		sourcemap: false,
		rollupOptions: {
			output: {
				inlineDynamicImports: true,
				assetFileNames: (assetInfo) => {
					if (assetInfo.name && assetInfo.name.endsWith(".css")) return "org_ui.css";
					return assetInfo.name || "asset";
				},
			},
		},
	},
});
