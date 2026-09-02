#!/usr/bin/env bash
# 从本机 bench 站点导出备份到 deploy/data/incoming
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
INCOMING_DIR="${DEPLOY_DIR}/data/incoming"
BENCH_DIR="${LOCAL_BENCH_DIR:-/home/dev/frappe-bench}"
LOCAL_SITE="${LOCAL_SITE:-hrms-test.localhost}"

log() {
	printf '\n[hrms-export] %s\n' "$*"
}

if [ ! -d "${BENCH_DIR}/sites/${LOCAL_SITE}" ]; then
	if [ -d "${BENCH_DIR}/sites/hrms.localhost" ]; then
		LOCAL_SITE="hrms.localhost"
		log "改用站点: ${LOCAL_SITE}"
	else
		echo "未找到本地站点 hrms-pg.localhost 或 hrms.localhost" >&2
		exit 1
	fi
fi

mkdir -p "${INCOMING_DIR}"
rm -f "${INCOMING_DIR}"/*

log "导出站点 ${LOCAL_SITE} -> ${INCOMING_DIR}"
cd "${BENCH_DIR}"
bench --site "${LOCAL_SITE}" backup --with-files --backup-path "${INCOMING_DIR}"

log "导出完成:"
ls -lh "${INCOMING_DIR}"
