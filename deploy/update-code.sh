#!/usr/bin/env bash
# ============================================================
# hrms-yiran 代码更新脚本
#
# 背景:容器实际运行的代码在 bench 数据卷(hrms-yiran_bench-data)内,
#       源码目录只是 :ro 挂载的"安装源"。git pull/reset 后必须把源码
#       重新同步进卷,并 migrate / build,再重启才生效。
#
# 用法(在 deploy 目录或任意位置):
#   bash deploy/update-code.sh          # 全量:同步 + migrate + build + 重启
#   bash deploy/update-code.sh --no-build   # 跳过前端构建(纯后端改动时更快)
# ============================================================
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${DEPLOY_DIR}")"
BENCH_VOLUME="hrms-yiran_bench-data"          # compose 项目名 + _bench-data
BACKEND_CONTAINER="hrms-yiran-backend-1"
IMAGE="frappe/bench:latest"
SITE_NAME="${SITE_NAME:-hrms.localhost}"

DO_BUILD=1
for arg in "$@"; do
	case "${arg}" in
		--no-build) DO_BUILD=0 ;;
		*) echo "未知参数: ${arg} (仅支持 --no-build)"; exit 1 ;;
	esac
done

log() { printf '\n[update-code] %s\n' "$*"; }

# compose.sh 依赖 cwd=deploy 目录(docker compose 默认找当前目录 yml)
run_compose() { ( cd "${DEPLOY_DIR}" && bash compose.sh "$@" ); }

# 确保内置依赖服务先起来(幂等)
log "1/6 启动内置 postgres / redis..."
run_compose up -d postgres redis >/dev/null 2>&1 || true

# 停 backend,避免运行中文件被替换
log "2/6 停止 backend(避免运行中替换代码)..."
run_compose stop backend >/dev/null 2>&1 || true

# 同步源码进 bench 卷(临时 root 容器;frappe/bench 镜像默认 USER=frappe,须 -u 0:0)
log "3/6 同步源码到 bench 卷 apps/hrms + apps/employee_roster ..."
docker run --rm -u 0:0 --entrypoint sh \
	-v "${BENCH_VOLUME}:/home/frappe/frappe-bench" \
	-v "${PROJECT_DIR}:/workspace/source:ro" \
	"${IMAGE}" -c '
set -e
cd /home/frappe/frappe-bench
rm -rf apps/hrms apps/employee_roster
cp -a /workspace/source/. apps/hrms/
cp -a /workspace/source/apps/employee_roster apps/employee_roster
chown -R 1000:1000 apps/hrms apps/employee_roster
echo "[sync] apps 已更新:"
(cd apps/hrms && git -c safe.directory=. log --oneline -1 2>/dev/null || true)
'
if [ $? -ne 0 ]; then
	echo "[update-code] 源码同步失败,已中止"; exit 1
fi

# 启动 backend(marker 存在则直接 start_bench)
log "4/6 启动 backend..."
run_compose up -d backend >/dev/null
for _ in $(seq 1 30); do
	st="$(docker inspect -f '{{.State.Running}}' "${BACKEND_CONTAINER}" 2>/dev/null || echo false)"
	[ "${st}" = "true" ] && break
	sleep 2
done
sleep 20   # 等 bench 各进程起来

# migrate
log "5/6 执行数据库迁移 bench --site ${SITE_NAME} migrate ..."
docker exec "${BACKEND_CONTAINER}" bash -c \
	"cd /home/frappe/frappe-bench && bench --site '${SITE_NAME}' migrate 2>&1 | tail -25"

# build
if [ "${DO_BUILD}" = "1" ]; then
	log "5.5/6 重建前端资源 bench build ..."
	docker exec "${BACKEND_CONTAINER}" bash -c \
		"cd /home/frappe/frappe-bench && bench build --app hrms --app employee_roster 2>&1 | tail -8"
fi

# 干净重启,确保所有进程加载新代码
log "6/6 重启 backend 完成加载..."
run_compose restart backend >/dev/null
sleep 15

log "完成!请访问 http://localhost:${HTTP_PORT:-8080} 验证;容器内版本:"
docker exec "${BACKEND_CONTAINER}" bash -c "cd /home/frappe/frappe-bench/apps/hrms && git log --oneline -1" 2>/dev/null || true
