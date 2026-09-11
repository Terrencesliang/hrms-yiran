#!/usr/bin/env bash
# Start the Docker development environment with source sync and asset watching.
# Behavior aligned with deploy/dev.ps1 on Windows.
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/common.sh
source "${DEPLOY_DIR}/scripts/common.sh"
ENV_FILE="${DEPLOY_DIR}/.env"
compose_args=(-f docker-compose.yml -f docker-compose.dev.yml)
show_logs=false
allow_migrate=false
force_migrate=false
force_recreate=false
start_timeout="${DEV_START_TIMEOUT:-55}"

for arg in "$@"; do
	case "${arg}" in
		--logs) show_logs=true ;;
		--migrate) allow_migrate=true ;;
		--force-migrate) allow_migrate=true; force_migrate=true ;;
		--recreate) force_recreate=true ;;
		--timeout=*) start_timeout="${arg#*=}" ;;
		-h|--help)
			echo "Usage: bash deploy/dev.sh [--logs] [--migrate] [--force-migrate] [--recreate] [--timeout=SECONDS]"
			echo "  --migrate        Run migration only when schema metadata changed."
			echo "  --force-migrate  Run a full migration even when metadata is unchanged."
			echo "  --timeout        Readiness timeout; defaults to 55 seconds."
			exit 0
			;;
		*) echo "Unknown option: ${arg}" >&2; exit 2 ;;
	esac
done

if ! [[ "${start_timeout}" =~ ^[0-9]+$ ]] || [ "${start_timeout}" -lt 10 ]; then
	echo "--timeout must be an integer of at least 10 seconds." >&2
	exit 2
fi

if ! command -v docker >/dev/null 2>&1; then
	echo "Docker not found. Install Docker Desktop first." >&2
	exit 1
fi
if ! docker info >/dev/null 2>&1; then
	echo "Docker is not running. Start Docker Desktop first." >&2
	exit 1
fi
if [ ! -f "${ENV_FILE}" ]; then
	echo "Missing deploy/.env. Run deploy/install.sh first." >&2
	exit 1
fi

bash "${DEPLOY_DIR}/scripts/validate_env.sh" "${ENV_FILE}"

if grep -qE '^USE_BUNDLED_POSTGRES=true' "${ENV_FILE}"; then
	compose_args+=(--profile bundled-postgres)
fi
if grep -qE '^USE_BUNDLED_REDIS=true' "${ENV_FILE}"; then
	compose_args+=(--profile bundled-redis)
fi

cd "${DEPLOY_DIR}"
started_at=${SECONDS}
echo "Starting HRMS development mode..."
up_args=(up -d backend nginx)
if [ "${force_recreate}" = true ]; then
	up_args=(up -d --force-recreate backend nginx)
fi
docker compose "${compose_args[@]}" "${up_args[@]}"

echo "Waiting for backend container..."
deploy_wait_backend_running "${compose_args[@]}"

echo "Synchronizing mounted source code..."
docker compose "${compose_args[@]}" exec -T backend \
	python /workspace/source/deploy/dev_sync.py --once

echo "Waiting for the development server (max ${start_timeout}s)..."
docker compose "${compose_args[@]}" exec -T backend \
	bash /workspace/source/deploy/scripts/wait_dev_ready.sh "${start_timeout}"

if [ "${allow_migrate}" = true ]; then
	prepare_args=()
	if grep -qE '^USE_BUNDLED_POSTGRES=true' "${ENV_FILE}"; then
		prepare_args+=(--local-database)
	fi
	if [ "${force_migrate}" = true ]; then
		prepare_args+=(--force-migrate)
	else
		prepare_args+=(--migrate)
	fi
	echo "Applying requested schema preparation (this may exceed the fast-start target)..."
	docker compose "${compose_args[@]}" exec -T backend \
		bash /workspace/source/deploy/scripts/prepare_dev.sh "${prepare_args[@]}"
fi

port="$(deploy_env_value "${ENV_FILE}" HTTP_PORT 8080)"
echo
echo "Development mode is ready in $((SECONDS - started_at))s: http://localhost:${port}"
echo "Source sync: enabled (Windows/macOS polling)"
echo "Frontend watch: enabled"
echo "Watched apps: hrms, employee_roster (ERPNext excluded)"
echo "Python reload: enabled"
echo "Arco org_ui watch: enabled"
echo
echo "Follow logs: bash deploy/dev.sh --logs"
echo "Stop: bash deploy/stop.sh"

if [ "${show_logs}" = true ]; then
	docker compose "${compose_args[@]}" logs -f backend
fi
