#!/usr/bin/env bash
# Stop HRMS Docker services on macOS/Linux while keeping containers reusable.
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
remove_containers=false

for arg in "$@"; do
	case "${arg}" in
		--down) remove_containers=true ;;
		-h | --help)
			echo "Usage: bash deploy/stop.sh [--down]"
			echo "  --down  Remove containers and network; persistent volumes are kept."
			exit 0
			;;
		*) echo "Unknown option: ${arg}" >&2; exit 2 ;;
	esac
done

if [ "${remove_containers}" = true ]; then
	bash "${DEPLOY_DIR}/compose.sh" down
	echo "HRMS Docker containers and network removed. Persistent data volumes were kept."
else
	bash "${DEPLOY_DIR}/compose.sh" stop
	echo "HRMS Docker services stopped and kept for a faster next start."
fi
