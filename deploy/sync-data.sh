#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "${DEPLOY_DIR}/scripts/export_local_data.sh"
echo ""
echo "==> 恢复数据到 Docker 容器..."
bash "${DEPLOY_DIR}/compose.sh" exec -T backend bash /workspace/source/deploy/scripts/restore_backup.sh
site_name="$(grep -E '^SITE_NAME=' "${DEPLOY_DIR}/.env" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '\r"' || true)"
site_name="${site_name:-hrms.localhost}"
bash "${DEPLOY_DIR}/compose.sh" exec -T backend bash -lc \
	"cd /home/frappe/frappe-bench && bench build --app hrms --app employee_roster && bench --site '${site_name}' clear-cache"
echo "数据同步完成。"
