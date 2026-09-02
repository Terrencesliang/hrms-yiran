#!/usr/bin/env bash
# 查看正式库 / 测试库对应的 PostgreSQL 数据库名
set -euo pipefail

NATIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${NATIVE_DIR}/common.sh"

require_bench

printf '%-6s %-28s %-36s %-22s\n' "角色" "Frappe 站点" "PostgreSQL 库名" "数据库地址"
printf '%s\n' "--------------------------------------------------------------------------------------------"

show_row() {
	local role="$1" site="$2" expected_db="$3"
	if [ ! -d "${BENCH_DIR}/sites/${site}" ]; then
		printf '%-6s %-28s %-36s %-22s\n' "${role}" "${site}" "${expected_db} (未创建)" "-"
		return
	fi
	local db_name db_host
	db_name="$(site_pg_db_name "${site}")"
	db_host="$(site_pg_host "${site}")"
	printf '%-6s %-28s %-36s %s:%s\n' "${role}" "${site}" "${db_name}" "${db_host}" "${DB_PORT}"
}

show_row "正式" "${PROD_SITE}" "${PROD_DB_NAME}"
show_row "测试" "${TEST_SITE}" "${TEST_DB_NAME}"

echo ""
echo "同步命令:"
echo "  测试 → 正式: bash deploy/native/sync-test-to-prod.sh"
echo "  正式 → 测试: bash deploy/native/sync-prod-to-test.sh"
echo "  同步模式:   SYNC_MODE=${SYNC_MODE} (pg=PostgreSQL直同步)"
