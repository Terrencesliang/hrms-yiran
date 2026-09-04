#!/usr/bin/env bash
# Start the stable HRMS Docker service on macOS/Linux.
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

cd "${DEPLOY_DIR}"
echo "Starting HRMS stable mode..."
bash "${DEPLOY_DIR}/compose.sh" up -d backend

port="$(sed -n 's/^HTTP_PORT=//p' "${ENV_FILE}" | tail -1 | tr -d '"\r')"
port="${port:-8080}"
echo "HRMS is ready: http://localhost:${port}"
echo "Stop: bash deploy/stop.sh"

if [ "${show_logs}" = true ]; then
	bash "${DEPLOY_DIR}/compose.sh" logs -f backend
fi
