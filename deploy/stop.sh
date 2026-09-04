#!/usr/bin/env bash
# Stop HRMS Docker services on macOS/Linux.
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${DEPLOY_DIR}/compose.sh" down
echo "HRMS Docker services stopped. Persistent data volumes were kept."
