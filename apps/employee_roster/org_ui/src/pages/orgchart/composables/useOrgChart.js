import { computed, onMounted, reactive, ref, watch } from "vue";
import { Message } from "@arco-design/web-vue";
import {
	collectExpandKeys,
	downloadText,
	filterTree,
	flattenTree,
	getImportTemplate,
	getOrgTree,
	importOrgUnits,
	orgTypeOf,
	toTableTree,
	uploadFile,
	vacancyState,
} from "../../../api";

const COL_STORAGE_KEY = "orgchart-hidden-cols";

function loadColumnDefs() {
	let hidden = [];
	try {
		hidden = JSON.parse(localStorage.getItem(COL_STORAGE_KEY) || "[]");
	} catch (e) {
		hidden = [];
	}
	const hiddenSet = new Set(Array.isArray(hidden) ? hidden : []);
	return [
		{ key: "type", label: "组织类型", visible: !hiddenSet.has("type") },
		{ key: "emp", label: "员工数", visible: !hiddenSet.has("emp") },
		{ key: "quota", label: "人员编制", visible: !hiddenSet.has("quota") },
		{ key: "vacancy", label: "缺编/超编", visible: !hiddenSet.has("vacancy") },
		{ key: "head", label: "负责人", visible: !hiddenSet.has("head") },
		{ key: "supervisor", label: "分管领导", visible: !hiddenSet.has("supervisor") },
	];
}

export function useOrgChart() {
	const loading = ref(false);
	const company = ref("");
	const companies = ref([]);
	const tree = ref([]);
	const keyword = ref("");
	const expandedKeys = ref([]);
	const filterVisible = ref(false);
	const drawerVisible = ref(false);
	const drawerPreset = ref({});
	const batchVisible = ref(false);
	const batchFile = ref(null);
	const importing = ref(false);

	const filters = reactive({ org_type: "", quota: "", vacancy: "" });
	const columnDefs = reactive(loadColumnDefs());

	const companyOptions = computed(() =>
		companies.value.map((c) => ({
			value: c.name,
			label: c.company_name || c.abbr || c.name,
		}))
	);

	const filterCount = computed(
		() => [filters.org_type, filters.quota, filters.vacancy].filter(Boolean).length
	);

	const flat = computed(() => flattenTree(tree.value));

	const summary = computed(() => {
		const units = flat.value.filter((it) => !it.node.is_company && !it.node.is_employee);
		const root = flat.value.find((it) => it.node.is_company)?.node;
		const employees = root
			? Number(root.employee_count || 0)
			: units.reduce((sum, it) => sum + Number(it.node.employee_count || 0), 0);
		const quotaUnits = units.filter((it) => Number(it.node.staff_quota || 0) > 0);
		const vacancies = quotaUnits.reduce(
			(sum, it) => sum + Math.max(Number(it.node.staff_quota || 0) - Number(it.node.employee_count || 0), 0),
			0
		);
		return { units: units.length, employees, quotaSet: quotaUnits.length, vacancies };
	});

	const displayTree = computed(() => {
		const kw = keyword.value.trim().toLowerCase();
		return filterTree(tree.value, (node) => {
			if (kw) {
				const title = String(node.title || "").toLowerCase();
				const code = String(node.org_code || "").toLowerCase();
				const designation = String(node.designation || "").toLowerCase();
				if (!title.includes(kw) && !code.includes(kw) && !designation.includes(kw)) return false;
			}
			if (filters.org_type && orgTypeOf(node) !== filters.org_type) return false;
			if (node.is_employee) return true;
			const quota = Number(node.staff_quota || 0);
			if (filters.quota === "set" && !quota) return false;
			if (filters.quota === "unset" && quota) return false;
			if (filters.vacancy && vacancyState(node) !== filters.vacancy) return false;
			return true;
		});
	});

	const visibleRows = computed(() => flattenTree(displayTree.value));
	const orgCount = computed(() => visibleRows.value.filter((it) => !it.node.is_employee).length);
	const memberCount = computed(() => visibleRows.value.filter((it) => it.node.is_employee).length);

	const visibleColumns = computed(() => {
		const cols = [
			{ title: "组织名称", dataIndex: "name", slotName: "name", width: 420, ellipsis: true, tooltip: true },
		];
		const extras = {
			type: { title: "组织类型", dataIndex: "type", slotName: "type", width: 110 },
			emp: { title: "员工数", dataIndex: "emp", slotName: "emp", width: 140 },
			quota: { title: "人员编制", dataIndex: "quota", slotName: "quota", width: 120 },
			vacancy: { title: "缺编/超编", dataIndex: "vacancy", slotName: "vacancy", width: 130 },
			head: { title: "负责人", dataIndex: "head", slotName: "head", width: 140 },
			supervisor: { title: "分管领导", dataIndex: "supervisor", slotName: "supervisor", width: 140 },
		};
		columnDefs.forEach((col) => {
			if (col.visible) cols.push(extras[col.key]);
		});
		return cols;
	});

	watch(
		columnDefs,
		() => {
			localStorage.setItem(
				COL_STORAGE_KEY,
				JSON.stringify(columnDefs.filter((c) => !c.visible).map((c) => c.key))
			);
		},
		{ deep: true }
	);

	function rowClass(record) {
		if (record.is_company) return "oc-row-company";
		if (record.is_employee) return "oc-row-member";
		return "";
	}

	function iconClass(record) {
		if (record.is_employee) return "is-member";
		const t = orgTypeOf(record);
		if (record.is_company || t === "公司") return "is-company";
		if (t === "组" || String(record.title || "").endsWith("组")) return "is-group";
		return "is-dept";
	}

	function typeColor(record) {
		const t = orgTypeOf(record);
		if (t === "公司") return "green";
		if (t === "组") return "gray";
		if (t === "员工") return "cyan";
		return "arcoblue";
	}

	function quotaGap(record) {
		return Number(record.staff_quota || 0) - Number(record.employee_count || 0);
	}

	function expandAll() {
		expandedKeys.value = collectExpandKeys(tree.value);
	}

	function collapseAll() {
		expandedKeys.value = [];
	}

	function resetFilters() {
		filters.org_type = "";
		filters.quota = "";
		filters.vacancy = "";
	}

	function openDrawer(record) {
		if (record?.is_employee) return;
		drawerPreset.value = record
			? { parent: record.name, parentTitle: record.title }
			: { parent: tree.value[0]?.name, parentTitle: tree.value[0]?.title };
		drawerVisible.value = true;
	}

	function openEmployee(record) {
		const id = record.employee || String(record.name || "").replace(/^__emp__/, "");
		if (!id || !window.frappe?.set_route) return;
		frappe.set_route("Form", "Employee", id);
	}

	let syncingCompany = false;

	function onCompanyChange() {
		if (syncingCompany) return;
		loadTree();
	}

	async function loadTree() {
		loading.value = true;
		try {
			const data = await getOrgTree(company.value || undefined);
			syncingCompany = true;
			company.value = data.company;
			companies.value = data.companies || [];
			tree.value = toTableTree(data.roots || []);
			expandAll();
		} catch (err) {
			Message.error("加载组织架构失败");
		} finally {
			syncingCompany = false;
			loading.value = false;
		}
	}

	function exportCsv() {
		const rows = [["组织名称", "组织代码", "组织类型", "员工数", "非全职", "人员编制", "缺编/超编", "负责人", "分管领导", "上级组织"]];
		flattenTree(tree.value).forEach((it) => {
			const n = it.node;
			const parent = flattenTree(tree.value).find((x) => x.node.key === it.parentKey);
			const vs = vacancyState(n);
			const gap = quotaGap(n);
			const vacancyLabel = vs === "short" ? `缺编${gap}` : vs === "over" ? `超编${Math.abs(gap)}` : vs === "full" ? "满编" : "";
			rows.push([
				n.title || "",
				n.org_code || "",
				orgTypeOf(n),
				n.employee_count || 0,
				n.parttime_count || 0,
				n.staff_quota || "",
				vacancyLabel,
				n.head_name || "",
				n.supervisor_name || "",
				parent ? parent.node.title : "",
			]);
		});
		downloadText("orgchart.csv", rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n"));
	}

	async function downloadTpl() {
		const file = await getImportTemplate();
		downloadText(file.filename || "org_import_template.csv", file.content || "");
	}

	function onBatchFile(_, current) {
		batchFile.value = current?.[0]?.file || current?.[0]?.originFile || null;
	}

	async function runImport() {
		if (!batchFile.value) {
			Message.warning("请上传 CSV 文件");
			return false;
		}
		importing.value = true;
		try {
			const uploaded = await uploadFile(batchFile.value);
			const res = await importOrgUnits(uploaded.file_url, company.value);
			Message.success(`导入完成：新增 ${res.created || 0}，更新 ${res.updated || 0}，跳过 ${(res.skipped || []).length}`);
			batchVisible.value = false;
			batchFile.value = null;
			await loadTree();
		} finally {
			importing.value = false;
		}
	}

	watch(keyword, (val) => {
		if (val) expandedKeys.value = collectExpandKeys(displayTree.value);
	});

	onMounted(loadTree);

	return {
		loading,
		company,
		tree,
		keyword,
		expandedKeys,
		filterVisible,
		drawerVisible,
		drawerPreset,
		batchVisible,
		importing,
		filters,
		columnDefs,
		companyOptions,
		filterCount,
		summary,
		displayTree,
		orgCount,
		memberCount,
		visibleColumns,
		orgTypeOf,
		vacancyState,
		rowClass,
		iconClass,
		typeColor,
		quotaGap,
		expandAll,
		collapseAll,
		resetFilters,
		openDrawer,
		openEmployee,
		onCompanyChange,
		loadTree,
		exportCsv,
		downloadTpl,
		onBatchFile,
		runImport,
	};
}
