#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Terrencesliang/hrms-yiran.git}"
BRANCH="${BRANCH:-yiran-custom}"
DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${DEPLOY_DIR}/.." && pwd)"
SKIP_LOCAL_DATA="${SKIP_LOCAL_DATA:-false}"

log() {
	printf '\n==> %s\n' "$*"
}

require_docker() {
	if ! command -v docker >/dev/null 2>&1; then
		echo "未检测到 Docker，请先安装: https://docs.docker.com/engine/install/"
		exit 1
	fi
	if ! docker info >/dev/null 2>&1; then
		echo "Docker 未运行，请先启动 Docker 服务。"
		exit 1
	fi
}

ensure_env() {
	if [ ! -f "${DEPLOY_DIR}/.env" ]; then
		cp "${DEPLOY_DIR}/.env.example" "${DEPLOY_DIR}/.env"
		log "已生成 deploy/.env"
	fi
}

ensure_repo() {
	if [ -d "${REPO_ROOT}/.git" ]; then
		log "使用当前目录代码: ${REPO_ROOT}"
		return
	fi
	echo "请先将项目克隆到本地，再运行本脚本："
	echo "  git clone --branch ${BRANCH} ${REPO_URL}"
	exit 1
}

env_flag() {
	local key="$1"
	local default="${2:-false}"
	local value
	value="$(grep "^${key}=" "${DEPLOY_DIR}/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)"
	case "${value:-$default}" in
	true | TRUE | 1 | yes | YES) return 0 ;;
	*) return 1 ;;
	esac
}

export_local_data_if_needed() {
	if [ "${SKIP_LOCAL_DATA}" = "true" ]; then
		log "已跳过本机数据导出 (SKIP_LOCAL_DATA=true)"
		return
	fi
	if ! env_flag SYNC_LOCAL_DATA false; then
		log "SYNC_LOCAL_DATA=false，跳过本机数据导出"
		return
	fi
	log "导出本机数据到 deploy/data/incoming"
	bash "${DEPLOY_DIR}/scripts/export_local_data.sh"
}

show_info() {
	local admin port
	admin="$(grep '^ADMIN_PASSWORD=' "${DEPLOY_DIR}/.env" | cut -d= -f2- | tr -d '"')"
	port="$(grep '^HTTP_PORT=' "${DEPLOY_DIR}/.env" | cut -d= -f2-)"
	admin="${admin:-admin}"
	port="${port:-8080}"

	cat <<EOF

========================================
 部署已启动（首次安装需等待 15-30 分钟）
========================================
访问地址: http://localhost:${port}
用户名:   Administrator
密码:     ${admin}

查看日志: ${DEPLOY_DIR}/logs.sh
重新同步: ${DEPLOY_DIR}/sync-data.sh
停止服务: ${DEPLOY_DIR}/stop.sh
========================================
EOF
}

log "检查 Docker 环境"
require_docker
ensure_repo
ensure_env
export_local_data_if_needed

cd "${DEPLOY_DIR}"
log "启动 Docker 容器"
bash "${DEPLOY_DIR}/compose.sh" up -d
show_info
