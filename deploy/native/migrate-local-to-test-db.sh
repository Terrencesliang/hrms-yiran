#!/usr/bin/env bash
# 将本地 WSL 站点数据迁移到 PostgreSQL 库 yiran_customs_test
set -euo pipefail

BENCH_DIR="${BENCH_DIR:-/home/dev/frappe-bench}"
SOURCE_SITE="${SOURCE_SITE:-hrms-pg.localhost}"
TARGET_SITE="${TARGET_SITE:-hrms-test.localhost}"
TARGET_DB_NAME="${TARGET_DB_NAME:-yiran_customs_test}"
PG_ROOT_USER="${PG_ROOT_USER:-postgres}"
PG_ROOT_PASSWORD="${PG_ROOT_PASSWORD:-postgres_root_2026}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"

export PATH="${HOME}/.local/bin:${PATH}"
export PGPASSWORD="${PG_ROOT_PASSWORD}"

log() { printf '\n[local-migrate] %s\n' "$*"; }

site_db_name() {
	local site="$1"
	python3 - <<PY
import json
from pathlib import Path
cfg = json.loads(Path("${BENCH_DIR}/sites/${site}/site_config.json").read_text())
print(cfg["db_name"])
PY
}

site_db_user() {
	local site="$1"
	python3 - <<PY
import json
from pathlib import Path
cfg = json.loads(Path("${BENCH_DIR}/sites/${site}/site_config.json").read_text())
print(cfg.get("db_user", cfg["db_name"]))
PY
}

cd "${BENCH_DIR}"

if [ ! -d "sites/${SOURCE_SITE}" ]; then
	if [ -d "sites/hrms.localhost" ]; then
		SOURCE_SITE="hrms.localhost"
	else
		echo "未找到源站点 ${SOURCE_SITE}" >&2
		exit 1
	fi
fi

SRC_DB="$(site_db_name "${SOURCE_SITE}")"
SRC_DB_USER="$(site_db_user "${SOURCE_SITE}")"

if [ -d "sites/${TARGET_SITE}" ]; then
	log "删除旧目标站点 ${TARGET_SITE} ..."
	bench drop-site "${TARGET_SITE}" \
		--db-root-username "${PG_ROOT_USER}" \
		--db-root-password "${PG_ROOT_PASSWORD}" \
		--force || rm -rf "sites/${TARGET_SITE}"
fi

log "1/5 创建目标站点 ${TARGET_SITE}（PG 库: ${TARGET_DB_NAME}）..."
bench new-site "${TARGET_SITE}" \
	--force \
	--db-type postgres \
	--db-host "${DB_HOST}" \
	--db-port "${DB_PORT}" \
	--db-root-username "${PG_ROOT_USER}" \
	--db-root-password "${PG_ROOT_PASSWORD}" \
	--db-name "${TARGET_DB_NAME}" \
	--admin-password "${ADMIN_PASSWORD}"

DST_DB="$(site_db_name "${TARGET_SITE}")"
DST_DB_USER="$(site_db_user "${TARGET_SITE}")"

log "2/5 pg_dump ${SRC_DB} → pg_restore ${DST_DB} ..."
DUMP_FILE="$(mktemp /tmp/hrms-pg-XXXXXX.dump)"
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${PG_ROOT_USER}" \
	-Fc --no-owner --no-acl -d "${SRC_DB}" -f "${DUMP_FILE}"

psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${PG_ROOT_USER}" -d postgres -c \
	"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DST_DB}' AND pid <> pg_backend_pid();" \
	>/dev/null || true

pg_restore -h "${DB_HOST}" -p "${DB_PORT}" -U "${PG_ROOT_USER}" \
	-d "${DST_DB}" --clean --if-exists --no-owner --no-acl "${DUMP_FILE}"
rm -f "${DUMP_FILE}"

log "3/5 修正 PG 表归属 ${SRC_DB_USER} → ${DST_DB_USER} ..."
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${PG_ROOT_USER}" -d "${DST_DB}" <<SQL
REASSIGN OWNED BY ${SRC_DB_USER} TO ${DST_DB_USER};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${DST_DB_USER};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${DST_DB_USER};
GRANT ALL PRIVILEGES ON SCHEMA public TO ${DST_DB_USER};
SQL

log "4/5 同步附件 + migrate ..."
mkdir -p "sites/${TARGET_SITE}/public/files" "sites/${TARGET_SITE}/private/files"
rsync -a "sites/${SOURCE_SITE}/public/files/" "sites/${TARGET_SITE}/public/files/" 2>/dev/null || true
rsync -a "sites/${SOURCE_SITE}/private/files/" "sites/${TARGET_SITE}/private/files/" 2>/dev/null || true

bench --site "${TARGET_SITE}" migrate
bench --site "${TARGET_SITE}" set-config developer_mode 1
bench --site "${TARGET_SITE}" clear-cache
bench use "${TARGET_SITE}"
echo "${TARGET_SITE}" > sites/currentsite.txt

log "5/5 验证 ..."
python3 - <<PY
import json, os, subprocess
from pathlib import Path
cfg = json.loads(Path("${BENCH_DIR}/sites/${TARGET_SITE}/site_config.json").read_text())
env = os.environ.copy()
env["PGPASSWORD"] = "${PG_ROOT_PASSWORD}"
count = subprocess.check_output(
    ["psql", "-h", "${DB_HOST}", "-p", "${DB_PORT}", "-U", "${PG_ROOT_USER}",
     "-d", cfg["db_name"], "-t", "-A", "-c", 'SELECT count(*) FROM "tabEmployee";'],
    env=env,
    text=True,
).strip()
print("site:", "${TARGET_SITE}")
print("db_name:", cfg.get("db_name"))
print("db_type:", cfg.get("db_type"))
print("employees:", count)
PY

log "完成: 本地已切换到 ${TARGET_SITE} / PostgreSQL:${TARGET_DB_NAME}"
