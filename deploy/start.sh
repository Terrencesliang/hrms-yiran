#!/usr/bin/env bash
# Start the stable HRMS Docker service on macOS/Linux.
# Behavior aligned with deploy/start.ps1 on Windows.
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/common.sh
source "${DEPLOY_DIR}/scripts/common.sh"
ENV_FILE="${DEPLOY_DIR}/.env"
show_logs=false

for arg in "$@"; do
	case "${arg}" in
		--logs) show_logs=true ;;
		-h | --help)
			echo "Usage: bash deploy/start.sh [--logs]"
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
	echo "Missing deploy/.env. Run bash deploy/install.sh first." >&2
	exit 1
fi

bash "${DEPLOY_DIR}/scripts/validate_env.sh" "${ENV_FILE}"

cd "${DEPLOY_DIR}"
echo "Starting HRMS stable mode..."
bash "${DEPLOY_DIR}/compose.sh" up -d backend nginx

compose_args=()
if grep -qE '^USE_BUNDLED_POSTGRES=true' "${ENV_FILE}"; then
	compose_args+=(--profile bundled-postgres)
fi
if grep -qE '^USE_BUNDLED_REDIS=true' "${ENV_FILE}"; then
	compose_args+=(--profile bundled-redis)
fi
deploy_wait_backend_running "${compose_args[@]}"

admin="$(deploy_env_value "${ENV_FILE}" ADMIN_PASSWORD admin)"
port="$(deploy_env_value "${ENV_FILE}" HTTP_PORT 8080)"

cat <<EOF

========================================
 HRMS Docker started
========================================
URL:      http://localhost:${port}
User:     Administrator
Password: ${admin}

Logs:  deploy/logs.sh
Stop:  deploy/stop.sh
========================================
EOF

if [ "${show_logs}" = true ]; then
	bash "${DEPLOY_DIR}/compose.sh" logs -f backend
fi
