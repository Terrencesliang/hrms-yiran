#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "${DEPLOY_DIR}/scripts/export_local_data.sh"
echo ""
echo "==> 恢复数据到 Docker 容器..."
bash "${DEPLOY_DIR}/compose.sh" exec -T backend bash /workspace/source/deploy/scripts/restore_backup.sh
bash "${DEPLOY_DIR}/compose.sh" exec -T backend bash -lc "cd /home/frappe/frappe-bench && bench build --app hrms --app employee_roster && bench --site \${SITE_NAME:-hrms.localhost} clear-cache"
echo "数据同步完成。"
