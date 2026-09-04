#!/usr/bin/env bash
# Start the Docker development environment with source sync and asset watching.
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${DEPLOY_DIR}/.env"
compose_args=(-f docker-compose.yml -f docker-compose.dev.yml)
show_logs=false
force_migrate=false
force_recreate=false

for arg in "$@"; do
	case "${arg}" in
		--logs) show_logs=true ;;
		--migrate) force_migrate=true ;;
		--recreate) force_recreate=true ;;
		-h|--help)
			echo "Usage: bash deploy/dev.sh [--logs] [--migrate] [--recreate]"
			exit 0
			;;
		*) echo "Unknown option: ${arg}" >&2; exit 2 ;;
	esac
done

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

if grep -qE '^USE_BUNDLED_POSTGRES=true' "${ENV_FILE}"; then
	compose_args+=(--profile bundled-postgres)
fi
if grep -qE '^USE_BUNDLED_REDIS=true' "${ENV_FILE}"; then
	compose_args+=(--profile bundled-redis)
fi

cd "${DEPLOY_DIR}"
echo "Starting HRMS development mode..."
up_args=(up -d backend)
if [ "${force_recreate}" = true ]; then
	up_args=(up -d --force-recreate backend)
fi
docker compose "${compose_args[@]}" "${up_args[@]}"

echo "Synchronizing mounted source code..."
docker compose "${compose_args[@]}" exec -T backend \
	python /workspace/source/deploy/dev_sync.py --once

if grep -qE '^USE_BUNDLED_POSTGRES=true' "${ENV_FILE}"; then
	if [ "${force_migrate}" = true ]; then
		docker compose "${compose_args[@]}" exec -T backend \
			bash /workspace/source/deploy/scripts/prepare_dev.sh --local-database --migrate
	else
		docker compose "${compose_args[@]}" exec -T backend \
			bash /workspace/source/deploy/scripts/prepare_dev.sh --local-database
	fi
elif [ "${force_migrate}" = true ]; then
	docker compose "${compose_args[@]}" exec -T backend \
		bash /workspace/source/deploy/scripts/prepare_dev.sh --migrate
else
	docker compose "${compose_args[@]}" exec -T backend \
		bash /workspace/source/deploy/scripts/prepare_dev.sh
fi

port="$(sed -n 's/^HTTP_PORT=//p' "${ENV_FILE}" | tail -1 | tr -d '"\r')"
port="${port:-8080}"
echo
echo "Development mode is ready: http://localhost:${port}"
echo "Source sync: enabled (Windows/macOS polling)"
echo "Frontend watch: enabled"
echo "Python reload: enabled"
echo "Arco org_ui watch: enabled"
echo
echo "Follow logs: bash deploy/dev.sh --logs"

if [ "${show_logs}" = true ]; then
	docker compose "${compose_args[@]}" logs -f backend
fi
