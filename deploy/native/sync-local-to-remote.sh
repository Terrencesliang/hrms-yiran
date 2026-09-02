#!/usr/bin/env bash
# 将 WSL 本地 PostgreSQL 库同步到 192.168.1.114 远端 PG
set -euo pipefail

NATIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${NATIVE_DIR}/common.sh"

LOCAL_BENCH="${LOCAL_BENCH:-/home/dev/frappe-bench}"
LOCAL_SITE="${LOCAL_SITE:-hrms-test.localhost}"
LOCAL_DB_HOST="${LOCAL_DB_HOST:-127.0.0.1}"
LOCAL_DB_PORT="${LOCAL_DB_PORT:-5432}"
LOCAL_PG_ROOT="${LOCAL_PG_ROOT:-postgres}"
LOCAL_PG_PASSWORD="${LOCAL_PG_PASSWORD:-postgres_root_2026}"

REMOTE_DB_HOST="${REMOTE_DB_HOST:-${DB_HOST:-192.168.1.114}}"
REMOTE_DB_PORT="${REMOTE_DB_PORT:-${DB_PORT:-15432}}"
REMOTE_PG_ROOT="${REMOTE_PG_ROOT:-${DB_ROOT_USERNAME:-postgres}}"
REMOTE_PG_PASSWORD="${REMOTE_PG_PASSWORD:-${DB_PASSWORD:-}}"

TARGET_DB_NAME="${TARGET_DB_NAME:-${TEST_DB_NAME:-yiran_customs_test}}"
SYNC_FILES="${SYNC_FILES:-true}"

require_env REMOTE_PG_PASSWORD
command -v pg_dump >/dev/null 2>&1 || die "未找到 pg_dump"
command -v pg_restore >/dev/null 2>&1 || die "未找到 pg_restore"

site_cfg="${LOCAL_BENCH}/sites/${LOCAL_SITE}/site_config.json"
[ -f "${site_cfg}" ] || die "未找到本地站点: ${LOCAL_SITE}"

SRC_DB="$(python3 - <<PY
import json
print(json.load(open("${site_cfg}"))["db_name"])
PY
)"
SRC_DB_USER="$(python3 - <<PY
import json
cfg = json.load(open("${site_cfg}"))
print(cfg.get("db_user", cfg["db_name"]))
PY
)"

log "本地 → 远端 PostgreSQL 同步"
printf '  源:   %s @ %s:%s (site: %s)\n' "${SRC_DB}" "${LOCAL_DB_HOST}" "${LOCAL_DB_PORT}" "${LOCAL_SITE}"
printf '  目标: %s @ %s:%s\n' "${TARGET_DB_NAME}" "${REMOTE_DB_HOST}" "${REMOTE_DB_PORT}"

log "检查远端连接..."
PGPASSWORD="${REMOTE_PG_PASSWORD}" psql \
	-h "${REMOTE_DB_HOST}" -p "${REMOTE_DB_PORT}" -U "${REMOTE_PG_ROOT}" -d postgres \
	-c "SELECT 1" >/dev/null

if ! PGPASSWORD="${REMOTE_PG_PASSWORD}" psql \
	-h "${REMOTE_DB_HOST}" -p "${REMOTE_DB_PORT}" -U "${REMOTE_PG_ROOT}" -d postgres -tAc \
	"SELECT 1 FROM pg_database WHERE datname='${TARGET_DB_NAME}'" | grep -q 1; then
	log "远端库 ${TARGET_DB_NAME} 不存在，正在创建..."
	PGPASSWORD="${REMOTE_PG_PASSWORD}" psql \
		-h "${REMOTE_DB_HOST}" -p "${REMOTE_DB_PORT}" -U "${REMOTE_PG_ROOT}" -d postgres \
		-c "CREATE DATABASE \"${TARGET_DB_NAME}\" OWNER ${REMOTE_PG_ROOT};"
fi

DUMP_FILE="$(mktemp /tmp/hrms-local-remote-XXXXXX.dump)"
log "pg_dump 本地库 ${SRC_DB} ..."
PGPASSWORD="${LOCAL_PG_PASSWORD}" pg_dump \
	-h "${LOCAL_DB_HOST}" -p "${LOCAL_DB_PORT}" -U "${LOCAL_PG_ROOT}" \
	-Fc --no-owner --no-acl \
	-d "${SRC_DB}" -f "${DUMP_FILE}"

log "断开远端库连接 ${TARGET_DB_NAME} ..."
PGPASSWORD="${REMOTE_PG_PASSWORD}" psql \
	-h "${REMOTE_DB_HOST}" -p "${REMOTE_DB_PORT}" -U "${REMOTE_PG_ROOT}" -d postgres \
	-c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${TARGET_DB_NAME}' AND pid <> pg_backend_pid();" \
	>/dev/null || true

log "pg_restore → 远端库 ${TARGET_DB_NAME} ..."
PGPASSWORD="${REMOTE_PG_PASSWORD}" pg_restore \
	-h "${REMOTE_DB_HOST}" -p "${REMOTE_DB_PORT}" -U "${REMOTE_PG_ROOT}" \
	-d "${TARGET_DB_NAME}" --clean --if-exists --no-owner --no-acl "${DUMP_FILE}"
rm -f "${DUMP_FILE}"

log "修正远端表归属 → ${TARGET_DB_NAME} ..."
PGPASSWORD="${REMOTE_PG_PASSWORD}" psql \
	-h "${REMOTE_DB_HOST}" -p "${REMOTE_DB_PORT}" -U "${REMOTE_PG_ROOT}" -d "${TARGET_DB_NAME}" <<SQL || true
DO \$\$
DECLARE r record;
BEGIN
  FOR r IN SELECT rolname FROM pg_roles WHERE rolname = '${SRC_DB_USER}'
  LOOP
    EXECUTE format('REASSIGN OWNED BY %I TO ${REMOTE_PG_ROOT}', r.rolname);
  END LOOP;
END\$\$;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${REMOTE_PG_ROOT};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${REMOTE_PG_ROOT};
GRANT ALL PRIVILEGES ON SCHEMA public TO ${REMOTE_PG_ROOT};
SQL

if [ "${SYNC_FILES}" = "true" ]; then
	log "同步附件到远端 (rsync → ${REMOTE_DB_HOST})..."
	REMOTE_SITE="${REMOTE_SITE:-${TEST_SITE:-hrms-test.localhost}}"
	REMOTE_BENCH="${REMOTE_BENCH:-${BENCH_DIR:-/data/yiran/frappe-bench}}"
	rsync -avz --delete \
		"${LOCAL_BENCH}/sites/${LOCAL_SITE}/public/files/" \
		"yr@${REMOTE_DB_HOST}:${REMOTE_BENCH}/sites/${REMOTE_SITE}/public/files/" 2>/dev/null || \
		log "附件 public/files 同步跳过（需 SSH 免密或手动同步）"
	rsync -avz --delete \
		"${LOCAL_BENCH}/sites/${LOCAL_SITE}/private/files/" \
		"yr@${REMOTE_DB_HOST}:${REMOTE_BENCH}/sites/${REMOTE_SITE}/private/files/" 2>/dev/null || \
		log "附件 private/files 同步跳过（需 SSH 免密或手动同步）"
fi

log "验证远端数据..."
EMP_COUNT="$(PGPASSWORD="${REMOTE_PG_PASSWORD}" psql \
	-h "${REMOTE_DB_HOST}" -p "${REMOTE_DB_PORT}" -U "${REMOTE_PG_ROOT}" -d "${TARGET_DB_NAME}" \
	-tAc 'SELECT count(*) FROM "tabEmployee";' 2>/dev/null || echo "?")"
DB_SIZE="$(PGPASSWORD="${REMOTE_PG_PASSWORD}" psql \
	-h "${REMOTE_DB_HOST}" -p "${REMOTE_DB_PORT}" -U "${REMOTE_PG_ROOT}" -d "${TARGET_DB_NAME}" \
	-tAc "SELECT pg_size_pretty(pg_database_size('${TARGET_DB_NAME}'));" 2>/dev/null || echo "?")"

printf '  远端库大小: %s\n' "${DB_SIZE}"
printf '  员工数:     %s\n' "${EMP_COUNT}"
log "完成: 本地 ${SRC_DB} → 远端 ${TARGET_DB_NAME}@${REMOTE_DB_HOST}:${REMOTE_DB_PORT}"
log "请在远端 bench 执行: bench --site ${TEST_SITE:-hrms-test.localhost} migrate && bench --site ${TEST_SITE:-hrms-test.localhost} clear-cache"
