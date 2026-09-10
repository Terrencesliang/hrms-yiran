import { inject, onMounted, provide, ref, watch, nextTick } from "vue";

export const ARCHIVE_EXPAND_KEY = Symbol("employeeArchiveExpand");

export function provideArchiveExpand(state) {
	provide(ARCHIVE_EXPAND_KEY, state);
}

export function createArchiveExpandState() {
	return {
		expandSection: ref(""),
		expandNonce: ref(0),
	};
}

/** 监听外部 expandSection，匹配时展开并滚入视野 */
export function useSectionExpand(sectionKeyRef, expandedRef, rootElRef) {
	const ctx = inject(ARCHIVE_EXPAND_KEY, null);
	if (!ctx) return;

	async function tryExpand() {
		const key = sectionKeyRef?.value ?? sectionKeyRef;
		const section = ctx.expandSection.value;
		if (!key || !section || key !== section) return;
		expandedRef.value = true;
		await nextTick();
		await new Promise((r) => setTimeout(r, 50));
		const node = rootElRef?.value;
		if (node?.scrollIntoView) {
			node.scrollIntoView({ behavior: "smooth", block: "start" });
		}
	}

	watch(
		[() => ctx.expandSection.value, () => ctx.expandNonce.value],
		() => {
			tryExpand();
		},
		{ flush: "post" }
	);

	onMounted(() => {
		tryExpand();
	});
}

export function useArchiveExpandContext() {
	return inject(ARCHIVE_EXPAND_KEY, null);
}
