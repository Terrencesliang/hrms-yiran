#!/usr/bin/env bash
# Start the Docker development environment with source sync and asset watching.
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${DEPLOY_DIR}/.env"
compose_args=(-f docker-compose.yml -f docker-compose.dev.yml)

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
docker compose "${compose_args[@]}" up -d --force-recreate backend

port="$(sed -n 's/^HTTP_PORT=//p' "${ENV_FILE}" | tail -1 | tr -d '"\r')"
port="${port:-8080}"
echo
echo "Development mode is ready: http://localhost:${port}"
echo "Source sync: enabled (Windows/macOS polling)"
echo "Frontend watch: enabled"
echo "Python reload: enabled"
echo
echo "Follow logs: bash deploy/dev.sh --logs"

if [ "${1:-}" = "--logs" ]; then
	docker compose "${compose_args[@]}" logs -f backend
fi
