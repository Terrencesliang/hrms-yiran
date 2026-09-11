#!/usr/bin/env bash
# Shared helpers for deploy/*.sh (parity with Windows *.ps1).
# Compatible with bash 3.2 (macOS /bin/bash).
# shellcheck shell=bash

deploy_env_value() {
	local env_file="$1"
	local key="$2"
	local default="${3:-}"
	local value
	value="$(grep -E "^${key}=" "${env_file}" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '\r' | sed 's/^["'\'']//;s/["'\'']$//' || true)"
	printf '%s' "${value:-$default}"
}

# Prints compose profile args as words (may be empty).
deploy_compose_profile_args() {
	local env_file="$1"
	if grep -qE '^USE_BUNDLED_POSTGRES=true' "${env_file}"; then
		printf '%s\n' --profile bundled-postgres
	fi
	if grep -qE '^USE_BUNDLED_REDIS=true' "${env_file}"; then
		printf '%s\n' --profile bundled-redis
	fi
}

deploy_wait_backend_running() {
	# Mirror Windows: do not exec into a crash-looping container.
	local i=1
	local status
	while [ "${i}" -le 45 ]; do
		status="$(docker compose "$@" ps --status running --format '{{.Name}}' 2>/dev/null | grep -E 'backend' || true)"
		if [ -n "${status}" ]; then
			return 0
		fi
		if docker compose "$@" ps -a --format '{{.Name}} {{.Status}}' 2>/dev/null | grep -qi 'backend.*Restarting'; then
			printf 'Backend is restarting (attempt %s/45)...\n' "${i}"
		else
			printf 'Waiting for backend container (attempt %s/45)...\n' "${i}"
		fi
		i=$((i + 1))
		sleep 2
	done
	echo "Backend container did not become ready. Recent logs:" >&2
	docker compose "$@" logs --tail 50 backend >&2 || true
	echo "" >&2
	echo "Common cause: site db_host=postgres while USE_BUNDLED_POSTGRES=false." >&2
	echo "Check deploy/.env DB_HOST / SITE_NAME, then recreate backend." >&2
	return 1
}
