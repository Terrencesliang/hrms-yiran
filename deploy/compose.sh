#!/usr/bin/env bash
# 根据 .env 决定是否启动内置 PostgreSQL / Redis
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${DEPLOY_DIR}/.env"
args=()

if [ -f "${ENV_FILE}" ]; then
	if grep -qE '^USE_BUNDLED_POSTGRES=true' "${ENV_FILE}"; then
		args+=(--profile bundled-postgres)
	fi
	if grep -qE '^USE_BUNDLED_REDIS=true' "${ENV_FILE}"; then
		args+=(--profile bundled-redis)
	fi
fi

exec docker compose "${args[@]}" "$@"
