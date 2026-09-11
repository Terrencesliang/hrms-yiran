#!/usr/bin/env python3
"""Start gunicorn against deploy.wsgi with the current Frappe site forced."""

from __future__ import annotations

import os
import sys
from pathlib import Path

BENCH_DIR = Path("/home/frappe/frappe-bench")
SITES_DIR = BENCH_DIR / "sites"
DEPLOY_DIR = Path("/workspace/source/deploy")


def main() -> None:
	os.chdir(SITES_DIR)
	os.environ.setdefault(
		"FRAPPE_SITE",
		(SITES_DIR / "currentsite.txt").read_text(encoding="utf-8").strip(),
	)
	if str(DEPLOY_DIR) not in sys.path:
		sys.path.insert(0, str(DEPLOY_DIR))

	workers = int(os.environ.get("GUNICORN_WORKERS", "3"))
	timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
	bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

	from gunicorn.app.wsgiapp import run

	sys.argv = [
		"gunicorn",
		"--bind",
		bind,
		"--workers",
		str(workers),
		"--threads",
		os.environ.get("GUNICORN_THREADS", "2"),
		"--timeout",
		str(timeout),
		"--keep-alive",
		"5",
		"--max-requests",
		"2000",
		"--max-requests-jitter",
		"200",
		"--access-logfile",
		"-",
		"--error-logfile",
		"-",
		"--pythonpath",
		str(DEPLOY_DIR),
		"wsgi:application",
	]
	run()


if __name__ == "__main__":
	main()
