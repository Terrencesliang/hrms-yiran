#!/usr/bin/env bash
# 共享配置与工具函数
set -euo pipefail

NATIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${NATIVE_DIR}/../.." && pwd)"
ENV_FILE="${NATIVE_DIR}/.env"

if [ -f "${ENV_FILE}" ]; then
	set -a
	# shellcheck disable=SC1090
	source "${ENV_FILE}"
	set +a
fi

BENCH_DIR="${BENCH_DIR:-${HOME}/frappe-bench}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-develop}"
ERPNEXT_BRANCH="${ERPNEXT_BRANCH:-develop}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"
DB_ROOT_USERNAME="${DB_ROOT_USERNAME:-postgres}"
REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/1}"
LANGUAGE="${LANGUAGE:-zh}"

PROD_SITE="${PROD_SITE:-hrms.localhost}"
PROD_DB_NAME="${PROD_DB_NAME:-yiran_customs}"
PROD_ADMIN_PASSWORD="${PROD_ADMIN_PASSWORD:-admin}"
PROD_HOST_NAME="${PROD_HOST_NAME:-http://127.0.0.1:8000}"

TEST_SITE="${TEST_SITE:-hrms-test.localhost}"
TEST_DB_NAME="${TEST_DB_NAME:-yiran_customs_test}"
TEST_ADMIN_PASSWORD="${TEST_ADMIN_PASSWORD:-admin}"
TEST_HOST_NAME="${TEST_HOST_NAME:-http://127.0.0.1:8001}"

CREATE_TEST_SITE="${CREATE_TEST_SITE:-true}"
SYNC_INCLUDE_FILES="${SYNC_INCLUDE_FILES:-true}"
# pg = PostgreSQL 库级直同步（推荐）；bench = bench backup/restore
SYNC_MODE="${SYNC_MODE:-pg}"
BACKUP_INCOMING="${BACKUP_INCOMING:-${NATIVE_DIR}/data/incoming}"
if [[ "${BACKUP_INCOMING}" != /* ]]; then
	BACKUP_INCOMING="${REPO_ROOT}/${BACKUP_INCOMING}"
fi

log() {
	printf '\n[native] %s\n' "$*"
}

die() {
	printf '\n[native] 错误: %s\n' "$*" >&2
	exit 1
}

require_env() {
	local key="$1"
	if [ -z "${!key:-}" ]; then
		die "缺少环境变量 ${key}，请配置 ${ENV_FILE}"
	fi
}

require_bench() {
	[ -d "${BENCH_DIR}/apps/frappe" ] || die "未找到 bench: ${BENCH_DIR}，请先运行 install.sh"
	command -v bench >/dev/null 2>&1 || die "未找到 bench 命令"
}

bench_cmd() {
	(
		cd "${BENCH_DIR}"
		bench "$@"
	)
}

redis_host_port() {
	python3 - <<PY
from urllib.parse import urlparse
parsed = urlparse("${REDIS_URL}")
print(parsed.hostname or "127.0.0.1")
print(parsed.port or 6379)
PY
}

wait_for_tcp() {
	local host="$1" port="$2" label="$3"
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
	bench_cmd set-redis-cache-host "${REDIS_URL}"
	bench_cmd set-redis-queue-host "${REDIS_URL}"
	bench_cmd set-redis-socketio-host "${REDIS_URL}"
	bench_cmd set-config -g serve_default_site true
}

apply_site_config() {
	local site="$1"
	local host_name="$2"
	bench_cmd --site "${site}" set-config developer_mode 0
	bench_cmd --site "${site}" set-config language "${LANGUAGE}"
	bench_cmd --site "${site}" set-config host_name "${host_name}"
	bench_cmd --site "${site}" enable-scheduler
	bench_cmd --site "${site}" clear-cache
}

install_apps() {
	if [ ! -d "${BENCH_DIR}/apps/erpnext" ]; then
		log "安装 ERPNext (${ERPNEXT_BRANCH})..."
		bench_cmd get-app --branch "${ERPNEXT_BRANCH}" erpnext
	fi
	if [ ! -d "${BENCH_DIR}/apps/payments" ]; then
		log "安装 Payments..."
		bench_cmd get-app --branch "${ERPNEXT_BRANCH}" payments || bench_cmd get-app payments
	fi
	if [ ! -d "${BENCH_DIR}/apps/hrms" ]; then
		log "安装 HRMS（本地定制版）..."
		bench_cmd get-app hrms "${REPO_ROOT}"
	fi
	if [ ! -d "${BENCH_DIR}/apps/employee_roster" ]; then
		log "安装 employee_roster..."
		bench_cmd get-app employee_roster "${REPO_ROOT}/apps/employee_roster"
	fi
}

create_postgres_site() {
	local site="$1"
	local admin_password="$2"
	local db_name="${3:-}"
	if [ -d "${BENCH_DIR}/sites/${site}" ]; then
		log "站点已存在，跳过创建: ${site}"
		return 0
	fi
	require_env DB_PASSWORD
	if [ -n "${db_name}" ]; then
		log "创建站点 ${site}（PostgreSQL 库: ${db_name}）..."
	else
		log "创建站点 ${site} ..."
	fi
	local args=(
		--force
		--db-type postgres
		--db-host "${DB_HOST}"
		--db-port "${DB_PORT}"
		--db-root-username "${DB_ROOT_USERNAME}"
		--db-root-password "${DB_PASSWORD}"
		--admin-password "${admin_password}"
	)
	if [ -n "${db_name}" ]; then
		args+=(--db-name "${db_name}")
	fi
	bench_cmd new-site "${site}" "${args[@]}"
}

site_db_name_for_site() {
	local site="$1"
	if [ "${site}" = "${PROD_SITE}" ]; then
		echo "${PROD_DB_NAME}"
	elif [ "${site}" = "${TEST_SITE}" ]; then
		echo "${TEST_DB_NAME}"
	else
		echo ""
	fi
}

install_fresh_site() {
	local site="$1"
	local admin_password="$2"
	local db_name="${3:-$(site_db_name_for_site "${site}")}"
	create_postgres_site "${site}" "${admin_password}" "${db_name}"
	bench_cmd --site "${site}" install-app erpnext
	bench_cmd --site "${site}" install-app hrms
	bench_cmd --site "${site}" install-app employee_roster
}

restore_site_from_dir() {
	local site="$1"
	local backup_dir="$2"
	local admin_password="${3:-${PROD_ADMIN_PASSWORD}}"
	local db_file base files_tar private_tar

	db_file="$(ls -t "${backup_dir}"/*-database.sql.gz 2>/dev/null | head -1 || true)"
	[ -n "${db_file}" ] || return 1

	base="${db_file%-database.sql.gz}"
	files_tar="${base}-files.tar"
	private_tar="${base}-private-files.tar"

	local db_name
	db_name="$(site_db_name_for_site "${site}")"
	create_postgres_site "${site}" "${admin_password}" "${db_name}"
	log "恢复备份到 ${site}: $(basename "${db_file}")"

	if [ -f "${files_tar}" ] && [ -f "${private_tar}" ]; then
		bench_cmd --site "${site}" restore "${db_file}" \
			--with-public-files "${files_tar}" \
			--with-private-files "${private_tar}"
	elif [ -f "${files_tar}" ]; then
		bench_cmd --site "${site}" restore "${db_file}" --with-public-files "${files_tar}"
	else
		bench_cmd --site "${site}" restore "${db_file}"
	fi

	bench_cmd --site "${site}" migrate
}

has_incoming_backup() {
	[ -d "${BACKUP_INCOMING}" ] && ls "${BACKUP_INCOMING}"/*-database.sql.gz >/dev/null 2>&1
}

pg_run() {
	PGPASSWORD="${DB_PASSWORD}" psql \
		-h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_ROOT_USERNAME}" \
		-v ON_ERROR_STOP=1 "$@"
}

site_pg_db_name() {
	local site="$1"
	python3 - <<PY
import json
from pathlib import Path
cfg = json.loads(Path("${BENCH_DIR}/sites/${site}/site_config.json").read_text())
db_type = cfg.get("db_type", "mariadb")
if db_type != "postgres":
    raise SystemExit(f"站点 ${site} 不是 PostgreSQL (db_type={db_type})")
print(cfg["db_name"])
PY
}

site_pg_host() {
	local site="$1"
	python3 - <<PY
import json
from pathlib import Path
cfg = json.loads(Path("${BENCH_DIR}/sites/${site}/site_config.json").read_text())
print(cfg.get("db_host", "${DB_HOST}"))
PY
}

verify_postgres_sites() {
	local s
	for s in "$@"; do
		[ -d "${BENCH_DIR}/sites/${s}" ] || die "站点不存在: ${s}"
		site_pg_db_name "${s}" >/dev/null
	done
}

show_pg_sync_plan() {
	local src_site="$1" dst_site="$2"
	local src_db dst_db src_host dst_host
	src_db="$(site_pg_db_name "${src_site}")"
	dst_db="$(site_pg_db_name "${dst_site}")"
	src_host="$(site_pg_host "${src_site}")"
	dst_host="$(site_pg_host "${dst_site}")"
	log "PostgreSQL 同步计划"
	printf '  源站点: %s\n' "${src_site}"
	printf '  源库:   %s @ %s:%s\n' "${src_db}" "${src_host}" "${DB_PORT}"
	printf '  目标站点: %s\n' "${dst_site}"
	printf '  目标库:   %s @ %s:%s\n' "${dst_db}" "${dst_host}" "${DB_PORT}"
	printf '  配置库名: 正式=%s  测试=%s\n' "${PROD_DB_NAME}" "${TEST_DB_NAME}"
	printf '  模式:   %s\n' "${SYNC_MODE}"
}

sync_site_files() {
	local src_site="$1" dst_site="$2"
	local src_public dst_public src_private dst_private

	if [ "${SYNC_INCLUDE_FILES}" != "true" ]; then
		log "SYNC_INCLUDE_FILES=false，跳过附件同步"
		return
	fi

	src_public="${BENCH_DIR}/sites/${src_site}/public/files"
	dst_public="${BENCH_DIR}/sites/${dst_site}/public/files"
	src_private="${BENCH_DIR}/sites/${src_site}/private/files"
	dst_private="${BENCH_DIR}/sites/${dst_site}/private/files"

	log "同步附件文件..."
	mkdir -p "${dst_public}" "${dst_private}"
	if [ -d "${src_public}" ]; then
		rsync -a --delete "${src_public}/" "${dst_public}/"
	fi
	if [ -d "${src_private}" ]; then
		rsync -a --delete "${src_private}/" "${dst_private}/"
	fi
}

sync_pg_between_sites() {
	local src_site="$1" dst_site="$2"
	local src_db dst_db dump_file
	src_db="$(site_pg_db_name "${src_site}")"
	dst_db="$(site_pg_db_name "${dst_site}")"
	dump_file="$(mktemp /tmp/hrms-pg-XXXXXX.dump)"

	log "pg_dump: ${src_db} → ${dump_file}"
	PGPASSWORD="${DB_PASSWORD}" pg_dump \
		-h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_ROOT_USERNAME}" \
		-Fc --no-owner --no-acl \
		-d "${src_db}" -f "${dump_file}"

	log "断开目标库连接: ${dst_db}"
	pg_run -d postgres -c \
		"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${dst_db}' AND pid <> pg_backend_pid();" \
		>/dev/null || true

	log "pg_restore: ${dump_file} → ${dst_db}"
	PGPASSWORD="${DB_PASSWORD}" pg_restore \
		-h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_ROOT_USERNAME}" \
		-d "${dst_db}" --clean --if-exists --no-owner --no-acl "${dump_file}"

	rm -f "${dump_file}"
}

sync_bench_backup_between_sites() {
	local src_site="$1" dst_site="$2" dst_admin_password="$3"
	local sync_dir
	sync_dir="$(mktemp -d /tmp/hrms-bench-sync-XXXXXX)"

	if [ "${SYNC_INCLUDE_FILES}" = "true" ]; then
		bench_cmd --site "${src_site}" backup --with-files --backup-path "${sync_dir}"
	else
		bench_cmd --site "${src_site}" backup --backup-path "${sync_dir}"
	fi

	restore_site_from_dir "${dst_site}" "${sync_dir}" "${dst_admin_password}"
	rm -rf "${sync_dir}"
}

sync_sites() {
	local src_site="$1" dst_site="$2" dst_host_name="$3" dst_admin_password="$4"

	require_env DB_PASSWORD
	command -v pg_dump >/dev/null 2>&1 || die "未找到 pg_dump，请安装 postgresql-client"
	command -v pg_restore >/dev/null 2>&1 || die "未找到 pg_restore，请安装 postgresql-client"

	verify_postgres_sites "${src_site}" "${dst_site}"
	show_pg_sync_plan "${src_site}" "${dst_site}"

	if [ "${SYNC_MODE}" = "pg" ]; then
		sync_pg_between_sites "${src_site}" "${dst_site}"
		sync_site_files "${src_site}" "${dst_site}"
	else
		sync_bench_backup_between_sites "${src_site}" "${dst_site}" "${dst_admin_password}"
	fi

	bench_cmd --site "${dst_site}" migrate
	apply_site_config "${dst_site}" "${dst_host_name}"
	bench_cmd build --app hrms --app employee_roster
	bench_cmd --site "${dst_site}" clear-cache

	log "同步完成: ${src_site} → ${dst_site}"
}
