#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR="/home/frappe/frappe-bench"
MARKER="${BENCH_DIR}/.hrms-yiran-installed"
SOURCE_DIR="/workspace/source"
SITE_NAME="${SITE_NAME:-hrms.localhost}"
SITE_DB_NAME="${SITE_DB_NAME:-}"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD is required}"
DB_ROOT_USERNAME="${DB_ROOT_USERNAME:-postgres}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-develop}"
ERPNEXT_BRANCH="${ERPNEXT_BRANCH:-develop}"
LANGUAGE="${LANGUAGE:-zh}"
HTTP_PORT="${HTTP_PORT:-8080}"
REDIS_URL="${REDIS_URL:-redis://redis:6379}"
SYNC_LOCAL_DATA="${SYNC_LOCAL_DATA:-false}"
BACKUP_DIR="${SOURCE_DIR}/deploy/data/incoming"

log() {
	printf '\n[hrms-deploy] %s\n' "$*"
}

wait_for_service() {
	local host="$1"
	local port="$2"
	local label="$3"
	log "等待 ${label} (${host}:${port})..."
	until python3 - <<PY
import socket
socket.create_connection(("${host}", ${port}), timeout=2).close()
PY
	do
		sleep 2
	done
}

redis_endpoint() {
	python3 - <<PY
from urllib.parse import urlparse
url = "${REDIS_URL}"
parsed = urlparse(url)
host = parsed.hostname or "redis"
port = parsed.port or 6379
print(host)
print(port)
PY
}

configure_bench_hosts() {
	cd "${BENCH_DIR}"
	bench set-redis-cache-host "${REDIS_URL}"
	bench set-redis-queue-host "${REDIS_URL}"
	bench set-redis-socketio-host "${REDIS_URL}"
	bench set-config -g serve_default_site true
	bench set-config -g default_site "${SITE_NAME}"
}

apply_site_config() {
	cd "${BENCH_DIR}"
	bench --site "${SITE_NAME}" set-config developer_mode 0
	bench --site "${SITE_NAME}" set-config language "${LANGUAGE}"
	bench --site "${SITE_NAME}" set-config host_name "http://localhost:${HTTP_PORT}"
	bench --site "${SITE_NAME}" enable-scheduler
	bench --site "${SITE_NAME}" clear-cache
	bench use "${SITE_NAME}"
}

has_local_backup() {
	[ -d "${BACKUP_DIR}" ] && ls "${BACKUP_DIR}"/*-database.sql.gz >/dev/null 2>&1
}

restore_local_backup() {
	if [ "${SYNC_LOCAL_DATA}" != "true" ]; then
		return 1
	fi
	if ! has_local_backup; then
		log "SYNC_LOCAL_DATA=true 但未找到备份，将执行全新安装"
		return 1
	fi

	log "检测到本机备份，开始恢复数据..."
	bash "${SOURCE_DIR}/deploy/scripts/restore_backup.sh"
	return 0
}

trim_procfile() {
	cd "${BENCH_DIR}"
	sed -i '/^redis/d' ./Procfile || true
	sed -i '/^watch/d' ./Procfile || true
}

install_apps() {
	cd "${BENCH_DIR}"

	if [ ! -d "apps/erpnext" ]; then
		log "安装 ERPNext (${ERPNEXT_BRANCH})..."
		bench get-app --branch "${ERPNEXT_BRANCH}" erpnext
	fi

	if [ ! -d "apps/payments" ]; then
		log "安装 Payments..."
		bench get-app --branch "${ERPNEXT_BRANCH}" payments || bench get-app payments
	fi

	if [ ! -d "apps/hrms" ]; then
		log "安装 HRMS（本地定制版）..."
		bench get-app hrms "${SOURCE_DIR}"
	fi

	if [ ! -d "apps/employee_roster" ]; then
		log "安装员工花名册扩展..."
		bench get-app employee_roster "${SOURCE_DIR}/apps/employee_roster"
	fi
}

create_and_setup_site() {
	cd "${BENCH_DIR}"

	if [ -d "sites/${SITE_NAME}" ]; then
		log "站点 ${SITE_NAME} 已存在，跳过创建"
		bench use "${SITE_NAME}" || true
		return
	fi

	log "创建站点 ${SITE_NAME}（PostgreSQL，首次约 10-20 分钟）..."
	local site_args=(
		--force
		--db-type postgres
		--db-host "${DB_HOST}"
		--db-port "${DB_PORT}"
		--db-root-username "${DB_ROOT_USERNAME}"
		--db-root-password "${DB_PASSWORD}"
		--admin-password "${ADMIN_PASSWORD}"
	)
	if [ -n "${SITE_DB_NAME}" ]; then
		site_args+=(--db-name "${SITE_DB_NAME}")
	fi
	bench new-site "${SITE_NAME}" "${site_args[@]}"

	log "安装应用..."
	bench --site "${SITE_NAME}" install-app erpnext
	bench --site "${SITE_NAME}" install-app hrms
	bench --site "${SITE_NAME}" install-app employee_roster

	log "配置站点..."
	apply_site_config
}

build_assets() {
	cd "${BENCH_DIR}"
	log "构建前端资源..."
	bench build --app hrms --app employee_roster
}

first_time_install() {
	export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}"

	wait_for_service "${DB_HOST}" "${DB_PORT}" "PostgreSQL"
	mapfile -t redis_parts < <(redis_endpoint)
	wait_for_service "${redis_parts[0]}" "${redis_parts[1]}" "Redis"
	log "数据库: ${DB_HOST}:${DB_PORT} (用户: ${DB_ROOT_USERNAME})"
	log "Redis: ${REDIS_URL}"

	if [ ! -d "${BENCH_DIR}/apps/frappe" ]; then
		log "初始化 Frappe Bench (${FRAPPE_BRANCH})..."
		bench init \
			--skip-redis-config-generation \
			--frappe-branch "${FRAPPE_BRANCH}" \
			frappe-bench
	fi

	configure_bench_hosts
	trim_procfile
	install_apps
	if restore_local_backup; then
		log "本机数据已恢复"
	else
		create_and_setup_site
	fi
	build_assets

	touch "${MARKER}"
	log "首次安装完成"
}

start_bench() {
	cd "${BENCH_DIR}"
	log "启动 HRMS 服务..."
	exec bench start
}

if [ -f "${MARKER}" ] && [ -d "${BENCH_DIR}/apps/frappe" ]; then
	start_bench
elif [ -d "${BENCH_DIR}/apps/frappe" ]; then
	log "检测到未完成的安装，继续执行..."
	first_time_install
	start_bench
else
	first_time_install
	start_bench
fi
