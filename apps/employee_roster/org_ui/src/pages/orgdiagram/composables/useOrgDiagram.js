import { computed, onMounted, ref, watch } from "vue";
import { Message } from "@arco-design/web-vue";
import { downloadText, getOrgDiagram } from "../../../api";

const ZOOM_MIN = 50;
const ZOOM_MAX = 150;

function unitSelfMatches(unit, query) {
	return [unit.title, unit.head_name, unit.manager_info?.name, unit.manager]
		.filter(Boolean)
		.some((text) => String(text).toLowerCase().includes(query));
}

function memberMatches(member, query) {
	return [member.title, member.designation, member.employee]
		.filter(Boolean)
		.some((text) => String(text).toLowerCase().includes(query));
}

/** 保留命中的组织；组织本身未命中时只保留命中的下级/成员。 */
function filterUnit(unit, query) {
	if (unitSelfMatches(unit, query)) return unit;
	const children = (unit.children || []).map((child) => filterUnit(child, query)).filter(Boolean);
	const members = (unit.members || []).filter((member) => memberMatches(member, query));
	if (!children.length && !members.length) return null;
	return { ...unit, children, members };
}

function collectUnitKeys(units, predicate, level = 1, out = []) {
	for (const unit of units || []) {
		if (predicate(unit, level)) out.push(unit.name);
		collectUnitKeys(unit.children, predicate, level + 1, out);
	}
	return out;
}

export function useOrgDiagram() {
	const loading = ref(false);
	const company = ref("");
	const data = ref({ companies: [], departments: [] });
	const keyword = ref("");
	const viewMode = ref("diagram");
	const depth = ref(1);
	const zoom = ref(100);
	const expandedKeys = ref(new Set());

	const companyOptions = computed(() =>
		(data.value.companies || []).map((item) => ({
			value: item.name,
			label: item.company_name || item.abbr || item.name,
		}))
	);

	const departments = computed(() => {
		const query = keyword.value.trim().toLowerCase();
		const all = data.value.departments || [];
		if (!query) return all;
		return all.map((department) => filterUnit(department, query)).filter(Boolean);
	});

	function isExpanded(name) {
		return expandedKeys.value.has(name);
	}

	function toggleNode(name) {
		const next = new Set(expandedKeys.value);
		if (next.has(name)) next.delete(name);
		else next.add(name);
		expandedKeys.value = next;
	}

	/** depth=1 只看部门；2 展开部门显示组；3 连组内成员一起展开。 */
	function applyDepth(level) {
		expandedKeys.value = new Set(
			collectUnitKeys(data.value.departments, (_unit, unitLevel) => unitLevel < level)
		);
	}

	function expandForKeyword() {
		expandedKeys.value = new Set(collectUnitKeys(departments.value, () => true));
	}

	async function loadDiagram() {
		loading.value = true;
		try {
			const response = await getOrgDiagram(company.value || undefined);
			data.value = response || { companies: [], departments: [] };
			company.value = response?.company || company.value;
			applyDepth(depth.value);
		} catch (error) {
			Message.error("加载架构图失败");
		} finally {
			loading.value = false;
		}
	}

	function setZoom(value) {
		zoom.value = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(value)));
	}

	function exportDiagram() {
		const rows = [["部门", "组", "姓名", "岗位", "工号", "组织在岗人数", "组织编制"]];
		const walk = (unit, deptTitle, groupTitle) => {
			(unit.members || []).forEach((member) =>
				rows.push([
					deptTitle,
					groupTitle,
					member.title || "",
					member.designation || "",
					member.employee || "",
					unit.employee_count || 0,
					unit.staff_quota || "",
				])
			);
			if (!(unit.members || []).length && !(unit.children || []).length) {
				rows.push([deptTitle, groupTitle, "", "", "", unit.employee_count || 0, unit.staff_quota || ""]);
			}
			(unit.children || []).forEach((child) =>
				walk(child, deptTitle, groupTitle ? `${groupTitle}/${child.title}` : child.title)
			);
		};
		(data.value.departments || []).forEach((department) => walk(department, department.title || "", ""));
		downloadText(
			"组织架构.csv",
			rows.map((row) => row.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(",")).join("\n")
		);
	}

	function openUnitDetail(unit) {
		if (!unit?.name || !window.frappe?.set_route) return;
		frappe.set_route("Form", "Department", unit.name);
	}

	function openMember(member) {
		const id = member?.employee || String(member?.name || "").replace(/^__emp__/, "");
		if (!id || !window.frappe?.set_route) return;
		frappe.set_route("Form", "Employee", id);
	}

	watch(viewMode, (mode) => {
		if (mode === "list" && window.frappe?.set_route) frappe.set_route("orgchart");
	});

	watch(depth, applyDepth);

	watch(keyword, (value) => {
		if (value.trim()) expandForKeyword();
		else applyDepth(depth.value);
	});

	onMounted(loadDiagram);

	return {
		loading,
		company,
		data,
		keyword,
		viewMode,
		depth,
		zoom,
		companyOptions,
		departments,
		isExpanded,
		toggleNode,
		loadDiagram,
		setZoom,
		exportDiagram,
		openUnitDetail,
		openMember,
	};
}
