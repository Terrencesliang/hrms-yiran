#!/usr/bin/env bash
# Validate deploy/.env for Docker Desktop (shared by install/start/dev on macOS/Linux).
# Mirrors deploy/install.ps1 / deploy/dev.ps1 checks on Windows.
set -euo pipefail

ENV_FILE="${1:-}"
if [ -z "${ENV_FILE}" ] || [ ! -f "${ENV_FILE}" ]; then
	echo "Missing deploy/.env. Copy deploy/.env.example to deploy/.env first." >&2
	exit 1
fi

env_value() {
	local key="$1"
	local default="${2:-}"
	local value
	value="$(grep -E "^${key}=" "${ENV_FILE}" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '\r' | sed 's/^["'\'']//;s/["'\'']$//' || true)"
	printf '%s' "${value:-$default}"
}

db_host="$(env_value DB_HOST "")"
redis_url="$(env_value REDIS_URL "")"
use_bundled_pg="$(env_value USE_BUNDLED_POSTGRES false | tr '[:upper:]' '[:lower:]')"
site_name="$(env_value SITE_NAME hrms.localhost)"

echo "Using env file: ${ENV_FILE}"
echo "  SITE_NAME=${site_name}"
echo "  DB_HOST=${db_host}"
echo "  REDIS_URL=${redis_url}"
echo "  USE_BUNDLED_POSTGRES=${use_bundled_pg}"

if [ "${use_bundled_pg}" = "true" ]; then
	if [ -n "${db_host}" ] && [ "${db_host}" != "postgres" ]; then
		echo "WARNING: USE_BUNDLED_POSTGRES=true but DB_HOST=${db_host} (expected postgres)." >&2
	fi
	exit 0
fi

# Containers cannot reach the Docker host via loopback.
case "${db_host}" in
127.0.0.1 | localhost)
	echo "" >&2
	echo "Invalid DB_HOST for Docker: ${db_host}" >&2
	echo "Use host.docker.internal when PostgreSQL runs on the same machine as Docker." >&2
	echo "  Edit deploy/.env:" >&2
	echo "    DB_HOST=host.docker.internal" >&2
	echo "When PostgreSQL is on another LAN machine, use that machine IP (e.g. 192.168.1.114)." >&2
	exit 1
	;;
esac

if [ -z "${db_host}" ]; then
	echo "DB_HOST is empty while USE_BUNDLED_POSTGRES=false." >&2
	exit 1
fi
