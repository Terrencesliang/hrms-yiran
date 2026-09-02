#!/usr/bin/env bash
# 原生 Linux 部署：安装 bench + 正式库 + 可选测试库
set -euo pipefail

NATIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${NATIVE_DIR}/common.sh"

SKIP_DEPS="${SKIP_DEPS:-false}"
RESTORE_FROM_BACKUP="${RESTORE_FROM_BACKUP:-true}"

install_system_deps() {
	if [ "${SKIP_DEPS}" = "true" ]; then
		return
	fi
	if ! command -v apt-get >/dev/null 2>&1; then
		log "非 Debian/Ubuntu 系统，请手动安装: python3 git redis-tools libpq-dev"
		return
	fi
	log "安装系统依赖（需要 sudo）..."
	sudo apt-get update -qq
	sudo apt-get install -y -qq \
		git python3 python3-pip python3-dev python3-venv \
		redis-tools libpq-dev postgresql-client \
		curl wget cron rsync \
		>/dev/null
}

install_bench_cli() {
	if command -v bench >/dev/null 2>&1; then
		log "bench 已安装: $(bench --version 2>/dev/null || true)"
		return
	fi
	log "安装 frappe-bench..."
	pip3 install --user frappe-bench
	export PATH="${HOME}/.local/bin:${PATH}"
	command -v bench >/dev/null 2>&1 || die "bench 安装失败，请检查 PATH"
}

init_bench() {
	if [ -d "${BENCH_DIR}/apps/frappe" ]; then
		log "Bench 已存在: ${BENCH_DIR}"
		return
	fi

	log "初始化 bench (${FRAPPE_BRANCH})..."
	mkdir -p "$(dirname "${BENCH_DIR}")"
	bench init \
		--skip-redis-config-generation \
		--frappe-branch "${FRAPPE_BRANCH}" \
		"${BENCH_DIR}"
}

prepare_bench() {
	cd "${BENCH_DIR}"
	sed -i '/^redis/d' ./Procfile 2>/dev/null || true
	sed -i '/^watch/d' ./Procfile 2>/dev/null || true
	configure_bench_hosts
	install_apps
}

setup_prod_site() {
	if has_incoming_backup && [ "${RESTORE_FROM_BACKUP}" = "true" ]; then
		log "从备份恢复正式库 ${PROD_SITE} ..."
		restore_site_from_dir "${PROD_SITE}" "${BACKUP_INCOMING}"
		apply_site_config "${PROD_SITE}" "${PROD_HOST_NAME}"
		bench_cmd use "${PROD_SITE}"
		return
	fi

	if [ -d "${BENCH_DIR}/sites/${PROD_SITE}" ]; then
		log "正式库已存在: ${PROD_SITE}"
		bench_cmd use "${PROD_SITE}" || true
		return
	fi

	log "全新安装正式库 ${PROD_SITE}（PG: ${PROD_DB_NAME}）..."
	install_fresh_site "${PROD_SITE}" "${PROD_ADMIN_PASSWORD}" "${PROD_DB_NAME}"
	apply_site_config "${PROD_SITE}" "${PROD_HOST_NAME}"
	bench_cmd use "${PROD_SITE}"
}

setup_test_site() {
	if [ "${CREATE_TEST_SITE}" != "true" ]; then
		log "CREATE_TEST_SITE=false，跳过测试库"
		return
	fi

	if [ -d "${BENCH_DIR}/sites/${TEST_SITE}" ]; then
		log "测试库已存在: ${TEST_SITE}"
		return
	fi

	log "创建测试库 ${TEST_SITE}（PG: ${TEST_DB_NAME}）..."
	create_postgres_site "${TEST_SITE}" "${TEST_ADMIN_PASSWORD}" "${TEST_DB_NAME}"
	bench_cmd --site "${TEST_SITE}" install-app erpnext
	bench_cmd --site "${TEST_SITE}" install-app hrms
	bench_cmd --site "${TEST_SITE}" install-app employee_roster
	apply_site_config "${TEST_SITE}" "${TEST_HOST_NAME}"
}

build_assets() {
	log "构建前端资源..."
	bench_cmd build --app hrms --app employee_roster
}

main() {
	[ -f "${ENV_FILE}" ] || die "请先复制配置: cp deploy/native/.env.example deploy/native/.env"

	require_env DB_PASSWORD

	install_system_deps
	install_bench_cli
	export PATH="${HOME}/.local/bin:${PATH}"

	mapfile -t redis_parts < <(redis_host_port)
	wait_for_tcp "${DB_HOST}" "${DB_PORT}" "PostgreSQL"
	wait_for_tcp "${redis_parts[0]}" "${redis_parts[1]}" "Redis"

	init_bench
	prepare_bench
	setup_prod_site
	setup_test_site
	build_assets

	log "安装完成"
	cat <<EOF

========================================
 正式库: ${PROD_SITE}  →  PG: ${PROD_DB_NAME}
 测试库: ${TEST_SITE}  →  PG: ${TEST_DB_NAME}
 Bench:  ${BENCH_DIR}

 启动:   cd ${BENCH_DIR} && bench start
 同步:   bash deploy/native/sync-test-to-prod.sh
 克隆正式→测试: bash deploy/native/sync-prod-to-test.sh
========================================
EOF
}

main "$@"
