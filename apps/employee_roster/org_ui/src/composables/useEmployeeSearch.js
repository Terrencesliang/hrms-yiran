import { computed, ref } from "vue";
import { searchEmployees } from "../api";

export function useEmployeeSearch(getCompany) {
	const rows = ref([]);
	const loading = ref(false);

	async function search(txt = "") {
		loading.value = true;
		try {
			rows.value = (await searchEmployees(txt, getCompany?.() || "")) || [];
		} finally {
			loading.value = false;
		}
	}

	const selectOptions = computed(() =>
		rows.value.map((row) => ({
			value: row.name,
			label: `${row.employee_name}${row.designation ? " · " + row.designation : ""}`,
		}))
	);

	return { rows, selectOptions, loading, search };
}
