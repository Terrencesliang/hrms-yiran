#!/usr/bin/env bash
# Prepare an already-running development container without rebuilding it.
set -euo pipefail

BENCH_DIR="/home/frappe/frappe-bench"
SOURCE_DIR="/workspace/source"
SITE_NAME="${SITE_NAME:-hrms.localhost}"
ALLOW_MIGRATE=false
FORCE_MIGRATE=false
LOCAL_DATABASE=false
PROGRESS_INTERVAL_SECONDS="${PROGRESS_INTERVAL_SECONDS:-15}"
progress_pid=""

stop_progress() {
	if [ -n "${progress_pid}" ]; then
		kill "${progress_pid}" 2>/dev/null || true
		wait "${progress_pid}" 2>/dev/null || true
		progress_pid=""
	fi
}

run_with_progress() {
	local label="$1"
	local started_at status elapsed
	shift

	started_at="${SECONDS}"
	printf '%s\n' "${label} This can take several minutes; progress will be reported every ${PROGRESS_INTERVAL_SECONDS}s."
	printf '%s\n' "If a DocType progress bar stays at 100%, hooks and cleanup may still be running."
	(
		while sleep "${PROGRESS_INTERVAL_SECONDS}"; do
			elapsed=$((SECONDS - started_at))
			printf '\n[migration] Still working... %ss elapsed.\n' "${elapsed}"
		done
	) &
	progress_pid="$!"

	if "$@"; then
		status=0
	else
		status="$?"
	fi
	stop_progress
	elapsed=$((SECONDS - started_at))
	if [ "${status}" -eq 0 ]; then
		printf '%s\n' "[migration] Completed after ${elapsed}s."
	else
		printf '%s\n' "[migration] Failed after ${elapsed}s (exit code ${status})." >&2
	fi
	return "${status}"
}

trap stop_progress EXIT

if ! [[ "${PROGRESS_INTERVAL_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
	echo "PROGRESS_INTERVAL_SECONDS must be a positive integer." >&2
	exit 2
fi

for arg in "$@"; do
	case "${arg}" in
		--migrate) ALLOW_MIGRATE=true ;;
		--force-migrate) ALLOW_MIGRATE=true; FORCE_MIGRATE=true ;;
		--local-database) LOCAL_DATABASE=true ;;
		*) echo "Unknown prepare_dev option: ${arg}" >&2; exit 2 ;;
	esac
done

cd "${BENCH_DIR}"

schema_signature() {
	python3 - <<'PY'
from hashlib import sha256
from pathlib import Path

roots = (
    Path("/workspace/source/hrms"),
    Path("/workspace/source/apps/employee_roster/employee_roster"),
)
names = {"hooks.py", "patches.txt"}
digest = sha256()

for root in roots:
    if not root.exists():
        continue
    files = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and (
            path.name in names
            or path.suffix == ".json"
            or "patches" in path.parts
        )
        and "node_modules" not in path.parts
        and "__pycache__" not in path.parts
    ]
    for path in sorted(files):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())

print(digest.hexdigest())
PY
}

installed_apps=""
for _attempt in $(seq 1 60); do
	if installed_apps="$(bench --site "${SITE_NAME}" execute frappe.get_installed_apps 2>/dev/null)"; then
		break
	fi
	sleep 1
done
if [ -z "${installed_apps}" ]; then
	echo "Site ${SITE_NAME} did not become ready within 60 seconds." >&2
	exit 4
fi
missing_apps=()
for app in hrms employee_roster; do
	if ! grep -q "\"${app}\"" <<<"${installed_apps}"; then
		missing_apps+=("${app}")
	fi
done

signature="$(schema_signature)"
marker="sites/${SITE_NAME}/.dev-schema-signature"
schema_changed=false
if [ -f "${marker}" ]; then
	[ "$(cat "${marker}")" = "${signature}" ] || schema_changed=true
elif [ "${LOCAL_DATABASE}" = true ] || [ "${ALLOW_MIGRATE}" = true ]; then
	schema_changed=true
elif [ "${#missing_apps[@]}" -eq 0 ]; then
	# Adopt an existing remote development database without migrating it on the
	# first run. Future metadata changes will still be detected.
	printf '%s\n' "${signature}" > "${marker}"
fi

needs_migrate=false
if [ "${FORCE_MIGRATE}" = true ] || [ "${schema_changed}" = true ] || [ "${#missing_apps[@]}" -gt 0 ]; then
	needs_migrate=true
fi

if [ "${needs_migrate}" = true ] && [ "${LOCAL_DATABASE}" != true ] && [ "${ALLOW_MIGRATE}" != true ]; then
	echo "The remote development database needs an HR schema update." >&2
	if [ "${#missing_apps[@]}" -gt 0 ]; then
		echo "Missing apps: ${missing_apps[*]}" >&2
	fi
	echo "Run the development command once with --migrate (Windows: -Migrate)." >&2
	exit 3
fi

if [ "${needs_migrate}" = true ]; then
	if [ "${#missing_apps[@]}" -gt 0 ]; then
		echo "Synchronizing the existing Frappe/ERPNext schema first..."
		run_with_progress "Preparing the base database schema." \
			bench --site "${SITE_NAME}" migrate --skip-search-index
	fi
	for app in "${missing_apps[@]}"; do
		echo "Installing ${app} on ${SITE_NAME}..."
		bench --site "${SITE_NAME}" install-app "${app}"
	done
	echo "Synchronizing database metadata for ${SITE_NAME}..."
	run_with_progress "Applying database metadata updates for ${SITE_NAME}." \
		bench --site "${SITE_NAME}" migrate --skip-search-index
	if [ "${ALLOW_MIGRATE}" = true ] && [ ! -f "${marker}" ]; then
		# Recover idempotent setup work when Frappe marked an app installed but
		# a previous after_install hook stopped part-way through.
		installed_apps="$(bench --site "${SITE_NAME}" execute frappe.get_installed_apps)"
		if grep -q '"hrms"' <<<"${installed_apps}"; then
			bench --site "${SITE_NAME}" execute hrms.install.after_install
		fi
		if grep -q '"employee_roster"' <<<"${installed_apps}"; then
			bench --site "${SITE_NAME}" execute employee_roster.install.after_install
		fi
	fi
	bench --site "${SITE_NAME}" clear-cache
	printf '%s\n' "${signature}" > "${marker}"
	printf '%s\n' "Database metadata is up to date."
else
	printf '%s\n' "Database metadata is unchanged."
fi
