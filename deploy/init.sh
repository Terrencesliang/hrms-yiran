#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR="/home/frappe/frappe-bench"
MARKER="${BENCH_DIR}/.hrms-yiran-installed"
SOURCE_DIR="/workspace/source"
SITE_NAME="${SITE_NAME:-hrms.localhost}"
SITE_DB_NAME="${SITE_DB_NAME:-}"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD is required}"
DB_ROOT_USERNAME="${DB_ROOT_USERNAME:-postgres}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-develop}"
ERPNEXT_BRANCH="${ERPNEXT_BRANCH:-develop}"
LANGUAGE="${LANGUAGE:-zh}"
HTTP_PORT="${HTTP_PORT:-8080}"
REDIS_URL="${REDIS_URL:-redis://redis:6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"
SYNC_LOCAL_DATA="${SYNC_LOCAL_DATA:-false}"
BACKUP_DIR="${SOURCE_DIR}/deploy/data/incoming"

redis_url_for_bench() {
	if [ -n "${REDIS_PASSWORD}" ] && [[ "${REDIS_URL}" != *"@"* ]]; then
		python3 - <<PY
from urllib.parse import urlparse, urlunparse
parsed = urlparse("${REDIS_URL}")
host = parsed.hostname or "127.0.0.1"
port = parsed.port or 6379
db = parsed.path or "/1"
print(f"redis://:{REDIS_PASSWORD}@{host}:{port}{db}")
PY
	else
		echo "${REDIS_URL}"
	fi
}

log() {
	printf '\n[hrms-deploy] %s\n' "$*"
}

configure_git_for_docker() {
	# Windows bind-mount: repo owner differs from container user (frappe)
	git config --global --add safe.directory '*' 2>/dev/null || true
}

app_is_present() {
	local name="$1"
	[ -d "${BENCH_DIR}/apps/${name}" ] && {
		[ -f "${BENCH_DIR}/apps/${name}/hooks.py" ] ||
			[ -f "${BENCH_DIR}/apps/${name}/${name}/hooks.py" ] ||
			[ -f "${BENCH_DIR}/apps/${name}/pyproject.toml" ]
	}
}

repair_apps_txt() {
	cd "${BENCH_DIR}"
	mkdir -p sites
	python3 <<'PY'
from pathlib import Path

path = Path("sites/apps.txt")
if not path.exists():
    path.write_text("frappe\n")
    raise SystemExit(0)

text = path.read_text()
text = text.replace("paymentshrms", "payments\nhrms")

lines = []
for raw in text.splitlines():
    line = raw.strip()
    if line:
        lines.append(line)

seen = set()
ordered = []
for line in lines:
    if line not in seen:
        seen.add(line)
        ordered.append(line)

path.write_text("\n".join(ordered) + "\n")
PY
}

ensure_app_in_apps_txt() {
	local name="$1"
	repair_apps_txt
	if ! grep -qx "${name}" sites/apps.txt; then
		printf '%s\n' "${name}" >> sites/apps.txt
	fi
}

install_local_app() {
	local name="$1"
	local src="$2"
	cd "${BENCH_DIR}"
	if app_is_present "${name}"; then
		ensure_app_in_apps_txt "${name}"
		return 0
	fi
	rm -rf "apps/${name}"
	log "安装本地应用 ${name}（从挂载目录复制）..."
	mkdir -p "apps/${name}"
	cp -a "${src}/." "apps/${name}/"
	ensure_app_in_apps_txt "${name}"
	if [ -x env/bin/pip ]; then
		env/bin/pip install -q -e "apps/${name}" || true
	fi
}

prepare_bench_dir() {
	mkdir -p "${BENCH_DIR}"
	if command -v sudo >/dev/null 2>&1; then
		sudo chown -R "$(id -u):$(id -g)" "${BENCH_DIR}" 2>/dev/null || true
	fi
}

wait_for_service() {
	local host="$1"
	local port="$2"
	local label="$3"
	log "等待 ${label} (${host}:${port})..."
	until python3 - <<PY
import socket
socket.create_connection(("${host}", ${port}), timeout=2).close()
PY
	do
		sleep 2
	done
}

redis_endpoint() {
	python3 - <<PY
from urllib.parse import urlparse
url = "${REDIS_URL}"
parsed = urlparse(url)
host = parsed.hostname or "redis"
port = parsed.port or 6379
print(host)
print(port)
PY
}

configure_bench_hosts() {
	local redis_url
	redis_url="$(redis_url_for_bench)"
	cd "${BENCH_DIR}"
	bench set-redis-cache-host "${redis_url}"
	bench set-redis-queue-host "${redis_url}"
	bench set-redis-socketio-host "${redis_url}"
	bench set-config -g serve_default_site true
	bench set-config -g default_site "${SITE_NAME}"
	bench create-rq-users 2>/dev/null || true
}

ensure_bench_initialized() {
	if [ -d "${BENCH_DIR}/apps/frappe" ] && [ -f "${BENCH_DIR}/sites/common_site_config.json" ]; then
		return 0
	fi

	log "初始化 Frappe Bench (${FRAPPE_BRANCH})..."
	prepare_bench_dir
	cd "${BENCH_DIR}"

	if [ "$(find . -mindepth 1 -maxdepth 1 | wc -l)" -gt 0 ]; then
		log "清理不完整的 bench 目录内容..."
		find . -mindepth 1 -maxdepth 1 -exec rm -rf {} +
	fi

	printf 'n\n' | bench init \
		--ignore-exist \
		--skip-redis-config-generation \
		--frappe-branch "${FRAPPE_BRANCH}" \
		.
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

has_local_backup() {
	[ -d "${BACKUP_DIR}" ] && ls "${BACKUP_DIR}"/*-database.sql.gz >/dev/null 2>&1
}

restore_local_backup() {
	if [ "${SYNC_LOCAL_DATA}" != "true" ]; then
		return 1
	fi
	if ! has_local_backup; then
		log "SYNC_LOCAL_DATA=true 但未找到备份，将执行全新安装"
		return 1
	fi

	log "检测到本机备份，开始恢复数据..."
	bash "${SOURCE_DIR}/deploy/scripts/restore_backup.sh"
	return 0
}

trim_procfile() {
	cd "${BENCH_DIR}"
	sed -i '/^redis/d' ./Procfile || true
	sed -i '/^watch/d' ./Procfile || true
}

install_apps() {
	cd "${BENCH_DIR}"
	configure_git_for_docker
	repair_apps_txt

	if [ ! -d "apps/erpnext" ]; then
		log "安装 ERPNext (${ERPNEXT_BRANCH})..."
		bench get-app --branch "${ERPNEXT_BRANCH}" erpnext
	fi

	if [ ! -d "apps/payments" ]; then
		log "安装 Payments..."
		bench get-app --branch "${ERPNEXT_BRANCH}" payments || bench get-app payments
	fi

	if ! app_is_present hrms; then
		log "安装 HRMS（本地定制版）..."
		install_local_app hrms "${SOURCE_DIR}"
	fi

	if ! app_is_present employee_roster; then
		log "安装员工花名册扩展..."
		install_local_app employee_roster "${SOURCE_DIR}/apps/employee_roster"
	fi
}

create_and_setup_site() {
	cd "${BENCH_DIR}"

	if [ -d "sites/${SITE_NAME}" ]; then
		log "站点 ${SITE_NAME} 已存在，跳过创建"
		bench use "${SITE_NAME}" || true
		return
	fi

	log "创建站点 ${SITE_NAME}（PostgreSQL，首次约 10-20 分钟）..."
	local site_args=(
		--force
		--db-type postgres
		--db-host "${DB_HOST}"
		--db-port "${DB_PORT}"
		--db-root-username "${DB_ROOT_USERNAME}"
		--db-root-password "${DB_PASSWORD}"
		--admin-password "${ADMIN_PASSWORD}"
	)
	if [ -n "${SITE_DB_NAME}" ]; then
		site_args+=(--db-name "${SITE_DB_NAME}")
	fi
	bench new-site "${SITE_NAME}" "${site_args[@]}"

	log "安装应用..."
	bench --site "${SITE_NAME}" install-app erpnext
	bench --site "${SITE_NAME}" install-app hrms
	bench --site "${SITE_NAME}" install-app employee_roster

	log "配置站点..."
	apply_site_config
}

build_assets() {
	cd "${BENCH_DIR}"
	log "构建前端资源..."
	bench build --app hrms --app employee_roster
}

first_time_install() {
	configure_git_for_docker
	prepare_bench_dir
	if [ -n "${NODE_VERSION_DEVELOP:-}" ] && [ -n "${NVM_DIR:-}" ]; then
		export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin:${PATH}"
	fi

	wait_for_service "${DB_HOST}" "${DB_PORT}" "PostgreSQL"
	mapfile -t redis_parts < <(redis_endpoint)
	wait_for_service "${redis_parts[0]}" "${redis_parts[1]}" "Redis"
	log "数据库: ${DB_HOST}:${DB_PORT} (用户: ${DB_ROOT_USERNAME})"
	log "Redis: $(redis_url_for_bench)"

	ensure_bench_initialized
	configure_bench_hosts
	trim_procfile
	install_apps
	if restore_local_backup; then
		log "本机数据已恢复"
	else
		create_and_setup_site
	fi
	build_assets

	touch "${MARKER}"
	log "首次安装完成"
}

start_bench() {
	cd "${BENCH_DIR}"
	repair_apps_txt
	log "启动 HRMS 服务..."
	exec bench start
}

if [ -f "${MARKER}" ] && [ -d "${BENCH_DIR}/apps/frappe" ]; then
	start_bench
elif [ -d "${BENCH_DIR}/apps/frappe" ]; then
	log "检测到未完成的安装，继续执行..."
	first_time_install
	start_bench
else
	first_time_install
	start_bench
fi
