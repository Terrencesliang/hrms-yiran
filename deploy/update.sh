#!/usr/bin/env bash
# 一键拉取最新代码并更新本地 Docker 开发环境。
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${DEPLOY_DIR}/.." && pwd)"

log() {
	printf '\n[hrms-update] %s\n' "$*"
}

compose() {
	(
		cd "${DEPLOY_DIR}"
		bash "${DEPLOY_DIR}/compose.sh" "$@"
	)
}

log "拉取最新代码..."
git -C "${REPO_DIR}" pull --ff-only

log "启动 Docker 服务..."
compose up -d

log "同步应用代码并更新站点..."
compose exec -T backend bash -lc '
set -euo pipefail
cd /home/frappe/frappe-bench

cp -a /workspace/source/hrms/. apps/hrms/hrms/
cp -a /workspace/source/apps/employee_roster/. apps/employee_roster/
env/bin/pip install -q -e apps/employee_roster

site_name="${SITE_NAME:-hrms.localhost}"
bench --site "${site_name}" migrate
bench build --app hrms --app employee_roster
bench --site "${site_name}" clear-cache
'

log "重启后端服务..."
compose restart backend

log "更新完成。请在浏览器中强制刷新页面（Command + Shift + R）。"
