#!/usr/bin/env bash
# 将 deploy/data/incoming 中的 bench 备份恢复到当前站点
set -euo pipefail

BENCH_DIR="${BENCH_DIR:-/home/frappe/frappe-bench}"
SOURCE_DIR="${SOURCE_DIR:-/workspace/source}"
BACKUP_DIR="${BACKUP_DIR:-${SOURCE_DIR}/deploy/data/incoming}"
SITE_NAME="${SITE_NAME:-hrms.localhost}"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD is required}"
DB_ROOT_USERNAME="${DB_ROOT_USERNAME:-postgres}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}"
LANGUAGE="${LANGUAGE:-zh}"
HTTP_PORT="${HTTP_PORT:-8080}"

log() {
	printf '\n[hrms-restore] %s\n' "$*"
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

ensure_site_exists() {
	cd "${BENCH_DIR}"
	if [ -d "sites/${SITE_NAME}" ]; then
		return 0
	fi

	log "创建空站点 ${SITE_NAME}..."
	bench new-site "${SITE_NAME}" \
		--force \
		--db-type postgres \
		--db-host "${DB_HOST}" \
		--db-port "${DB_PORT}" \
		--db-root-username "${DB_ROOT_USERNAME}" \
		--db-root-password "${DB_PASSWORD}" \
		--admin-password "${ADMIN_PASSWORD}"
}

restore_latest_backup() {
	local db_file base files_tar private_tar

	if [ ! -d "${BACKUP_DIR}" ]; then
		log "备份目录不存在: ${BACKUP_DIR}"
		return 1
	fi

	db_file="$(ls -t "${BACKUP_DIR}"/*-database.sql.gz 2>/dev/null | head -1 || true)"
	if [ -z "${db_file}" ]; then
		log "未找到 *-database.sql.gz 备份文件"
		return 1
	fi

	base="${db_file%-database.sql.gz}"
	files_tar="${base}-files.tar"
	private_tar="${base}-private-files.tar"

	cd "${BENCH_DIR}"
	ensure_site_exists

	log "恢复备份: $(basename "${db_file}")"
	if [ -f "${files_tar}" ] && [ -f "${private_tar}" ]; then
		bench --site "${SITE_NAME}" restore "${db_file}" \
			--with-public-files "${files_tar}" \
			--with-private-files "${private_tar}"
	elif [ -f "${files_tar}" ]; then
		bench --site "${SITE_NAME}" restore "${db_file}" --with-public-files "${files_tar}"
	else
		bench --site "${SITE_NAME}" restore "${db_file}"
	fi

	log "执行 migrate..."
	bench --site "${SITE_NAME}" migrate
	apply_site_config
	log "数据恢复完成"
}

restore_latest_backup
