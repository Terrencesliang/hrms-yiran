#!/usr/bin/env bash
# 从本机 WSL 导出数据到 deploy/native/data/incoming（在 Windows 上通过 WSL 运行）
set -euo pipefail

NATIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${NATIVE_DIR}/common.sh"

LOCAL_SITE="${LOCAL_SITE:-hrms-test.localhost}"
LOCAL_BENCH="${LOCAL_BENCH:-/home/dev/frappe-bench}"

if [ ! -d "${LOCAL_BENCH}/sites/${LOCAL_SITE}" ]; then
	if [ -d "${LOCAL_BENCH}/sites/hrms.localhost" ]; then
		LOCAL_SITE="hrms.localhost"
	else
		die "未找到本地站点 ${LOCAL_SITE}"
	fi
fi

mkdir -p "${BACKUP_INCOMING}"
rm -f "${BACKUP_INCOMING}"/*

log "导出 ${LOCAL_SITE} -> ${BACKUP_INCOMING}"
(
	cd "${LOCAL_BENCH}"
	bench --site "${LOCAL_SITE}" backup --with-files --backup-path "${BACKUP_INCOMING}"
)

ls -lh "${BACKUP_INCOMING}"
