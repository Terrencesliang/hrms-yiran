# Sidebar Design QA

## Visual target

- Expanded reference: `/var/folders/65/rpjxw3dj7ts4md354_n11sq40000gn/T/codex-clipboard-b2c5c23a-9d58-4af1-883f-216d9c88c2f3.png`
- Compact reference: `/var/folders/65/rpjxw3dj7ts4md354_n11sq40000gn/T/codex-clipboard-7f46b0af-8577-490d-86ed-797ec841ff8f.png`
- Implementation checked at: `http://localhost:8080/desk/employee`
- Viewport: 2388 × 1199 (Chrome)

## Result

Status: **Passed**

- Expanded state keeps the complete module tree, search control, active item styling, and a bottom collapse action.
- Compact state occupies 56 px, preserves one icon per business module, highlights the active module, and exposes its links in a small icon-anchored flyout.
- The bottom control switches both ways and the preference survives reloads.
- Frappe's two legacy `.sidebar-toggle-btn` controls stay hidden while the custom sidebar is active, leaving exactly one visible expand/collapse action in either state.
- The main content reflows in both states; no permanent overlay or duplicate Frappe expand control remains.
- Compact flyout is offset below the header area and constrained to the viewport height.
- The flyout owns a higher stacking layer than list/table controls; checkboxes and sticky table content no longer render through it.
- Large modules scroll inside a 336 px maximum-height menu instead of creating a page-height drawer.
- Mobile keeps the readable expanded menu and uses the existing Frappe close behavior.

## Verification

- `npm run build` — passed.
- `git diff --check` — passed.
- Browser interaction — expanded → compact → module flyout → expanded passed.
- Duplicate-control regression — expanded and compact each expose one custom control; visible legacy toggle count is zero.
- Reference and implementation captures were reviewed together at the same browser viewport.
