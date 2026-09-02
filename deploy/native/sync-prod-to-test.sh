#!/usr/bin/env bash
# 正式库 (PostgreSQL) → 测试库 (PostgreSQL) 一键同步
set -euo pipefail

NATIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${NATIVE_DIR}/common.sh"

FORCE="${FORCE:-false}"

while [ $# -gt 0 ]; do
	case "$1" in
	--force) FORCE=true ;;
	-h | --help) exit 0 ;;
	*) die "未知参数: $1" ;;
	esac
	shift
done

require_bench

if [ "${FORCE}" != "true" ]; then
	show_pg_sync_plan "${PROD_SITE}" "${TEST_SITE}"
	echo ""
	echo "警告: 即将用正式 PostgreSQL 库覆盖测试 PostgreSQL 库！"
	read -r -p "输入 YES 继续: " confirm
	[ "${confirm}" = "YES" ] || die "已取消"
fi

sync_sites "${PROD_SITE}" "${TEST_SITE}" "${TEST_HOST_NAME}" "${TEST_ADMIN_PASSWORD}"

log "完成: 正式 PG 库已同步到测试 PG 库"
