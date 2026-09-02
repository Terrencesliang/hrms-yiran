#!/usr/bin/env bash
# 测试库 (PostgreSQL) → 正式库 (PostgreSQL) 一键同步
set -euo pipefail

NATIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${NATIVE_DIR}/common.sh"

FORCE="${FORCE:-false}"

usage() {
	cat <<EOF
用法: $0 [--force]

  PostgreSQL 测试库 → PostgreSQL 正式库
  站点: ${TEST_SITE} → ${PROD_SITE}
  模式: \${SYNC_MODE} (pg=库级直同步, bench=备份恢复)

选项:
  --force   跳过交互确认
EOF
}

while [ $# -gt 0 ]; do
	case "$1" in
	--force) FORCE=true ;;
	-h | --help)
		usage
		exit 0
		;;
	*) die "未知参数: $1" ;;
	esac
	shift
done

require_bench

if [ "${FORCE}" != "true" ]; then
	show_pg_sync_plan "${TEST_SITE}" "${PROD_SITE}"
	echo ""
	echo "警告: 即将用测试 PostgreSQL 库覆盖正式 PostgreSQL 库！"
	read -r -p "输入 YES 继续: " confirm
	[ "${confirm}" = "YES" ] || die "已取消"
fi

log "进入维护模式..."
bench_cmd --site "${PROD_SITE}" set-maintenance-mode on || true

sync_sites "${TEST_SITE}" "${PROD_SITE}" "${PROD_HOST_NAME}" "${PROD_ADMIN_PASSWORD}"

log "关闭维护模式..."
bench_cmd --site "${PROD_SITE}" set-maintenance-mode off || true

log "完成: 测试 PG 库已同步到正式 PG 库"
