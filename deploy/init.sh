#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR="/home/frappe/frappe-bench"
MARKER="${BENCH_DIR}/.hrms-yiran-installed"
SOURCE_DIR="/workspace/source"
SITE_NAME="${SITE_NAME:-hrms.localhost}"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD is required}"
DB_ROOT_USERNAME="${DB_ROOT_USERNAME:-postgres}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-develop}"
ERPNEXT_BRANCH="${ERPNEXT_BRANCH:-develop}"
LANGUAGE="${LANGUAGE:-zh}"
HTTP_PORT="${HTTP_PORT:-8080}"

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

configure_bench_hosts() {
	cd "${BENCH_DIR}"
	bench set-redis-cache-host redis://redis:6379
	bench set-redis-queue-host redis://redis:6379
	bench set-redis-socketio-host redis://redis:6379
	bench set-config -g serve_default_site true
	bench set-config -g default_site "${SITE_NAME}"
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
	bench new-site "${SITE_NAME}" \
		--force \
		--db-type postgres \
		--db-host "${DB_HOST}" \
		--db-port "${DB_PORT}" \
		--db-root-username "${DB_ROOT_USERNAME}" \
		--db-root-password "${DB_PASSWORD}" \
		--admin-password "${ADMIN_PASSWORD}"

	log "安装应用..."
	bench --site "${SITE_NAME}" install-app erpnext
	bench --site "${SITE_NAME}" install-app hrms
	bench --site "${SITE_NAME}" install-app employee_roster

	log "配置站点..."
	bench --site "${SITE_NAME}" set-config developer_mode 0
	bench --site "${SITE_NAME}" set-config language "${LANGUAGE}"
	bench --site "${SITE_NAME}" set-config host_name "http://localhost:${HTTP_PORT}"
	bench --site "${SITE_NAME}" enable-scheduler
	bench --site "${SITE_NAME}" clear-cache
	bench use "${SITE_NAME}"
}

build_assets() {
	cd "${BENCH_DIR}"
	log "构建前端资源..."
	bench build --app hrms --app employee_roster
}

first_time_install() {
	export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}"

	wait_for_service "${DB_HOST}" "${DB_PORT}" "PostgreSQL"
	wait_for_service redis 6379 "Redis"

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
	create_and_setup_site
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
