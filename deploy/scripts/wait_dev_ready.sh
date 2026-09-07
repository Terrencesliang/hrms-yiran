#!/usr/bin/env bash
# Wait for Frappe without making the host wrapper platform-specific.
set -euo pipefail

timeout_seconds="${1:-55}"
if ! [[ "${timeout_seconds}" =~ ^[0-9]+$ ]] || [ "${timeout_seconds}" -lt 1 ]; then
	echo "Invalid readiness timeout: ${timeout_seconds}" >&2
	exit 2
fi

deadline=$((SECONDS + timeout_seconds))
while [ "${SECONDS}" -lt "${deadline}" ]; do
	if python - <<'PY' >/dev/null 2>&1
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:8000/api/method/ping", timeout=2) as response:
    if response.status != 200:
        raise SystemExit(1)
PY
	then
		echo "Development server is ready."
		exit 0
	fi
	sleep 1
done

echo "Timed out waiting for Frappe after ${timeout_seconds}s." >&2
echo "A first-time site installation can take longer; inspect with: docker compose logs backend" >&2
exit 1
