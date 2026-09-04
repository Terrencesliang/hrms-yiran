#!/usr/bin/env python3
"""Poll the host-mounted source tree and mirror changes into the running Bench.

Polling is intentional: Docker Desktop file-system events behave differently on
Windows and macOS, while stat-based polling is predictable on both platforms.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


SOURCE_ROOT = Path("/workspace/source")
BENCH_ROOT = Path("/home/frappe/frappe-bench")
POLL_INTERVAL = max(float(os.environ.get("DEV_SYNC_INTERVAL", "0.5")), 0.2)

IGNORED_DIRECTORIES = {
	".codegraph",
	".git",
	".idea",
	".mypy_cache",
	".pytest_cache",
	".ruff_cache",
	".venv",
	"__pycache__",
	"node_modules",
	"other",
}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".swp", ".tmp"}
ROOT_EXCLUDED_DIRECTORIES = {"apps", "deploy"}


@dataclass(frozen=True)
class SyncMapping:
	source: Path
	destination: Path
	excluded_top_level: frozenset[str] = frozenset()


MAPPINGS = (
	SyncMapping(SOURCE_ROOT, BENCH_ROOT / "apps" / "hrms", frozenset(ROOT_EXCLUDED_DIRECTORIES)),
	SyncMapping(SOURCE_ROOT / "apps" / "employee_roster", BENCH_ROOT / "apps" / "employee_roster"),
)


running = True


def stop(*_args) -> None:
	global running
	running = False


def should_ignore(relative_path: Path, mapping: SyncMapping) -> bool:
	if not relative_path.parts:
		return False
	if relative_path.parts[0] in mapping.excluded_top_level:
		return True
	if any(part in IGNORED_DIRECTORIES for part in relative_path.parts):
		return True
	return relative_path.suffix.lower() in IGNORED_SUFFIXES or relative_path.name == ".DS_Store"


def source_files(mapping: SyncMapping):
	if not mapping.source.exists():
		return
	for root, directories, filenames in os.walk(mapping.source):
		root_path = Path(root)
		relative_root = root_path.relative_to(mapping.source)
		directories[:] = [
			name
			for name in directories
			if not should_ignore(relative_root / name, mapping)
		]
		for filename in filenames:
			relative_path = relative_root / filename
			if not should_ignore(relative_path, mapping):
				yield relative_path, root_path / filename


def signature(path: Path) -> tuple[int, int]:
	stat = path.stat()
	return stat.st_mtime_ns, stat.st_size


def copy_file(source_path: Path, destination_path: Path) -> None:
	"""Replace through a sibling temp file so host-owned legacy files are writable."""
	destination_path.parent.mkdir(parents=True, exist_ok=True)
	file_descriptor, temporary_name = tempfile.mkstemp(
		dir=destination_path.parent,
		prefix=f".{destination_path.name}.dev-sync-",
	)
	os.close(file_descriptor)
	temporary_path = Path(temporary_name)
	try:
		shutil.copy2(source_path, temporary_path)
		os.replace(temporary_path, destination_path)
	finally:
		if temporary_path.exists():
			temporary_path.unlink()


def sync_mapping(mapping: SyncMapping, previous: dict[Path, tuple[int, int]]) -> tuple[dict[Path, tuple[int, int]], int, int]:
	current: dict[Path, tuple[int, int]] = {}
	copied = 0
	removed = 0
	for relative_path, source_path in source_files(mapping) or ():
		file_signature = signature(source_path)
		current[relative_path] = file_signature
		if previous.get(relative_path) == file_signature:
			continue
		destination_path = mapping.destination / relative_path
		if destination_path.is_file() and signature(destination_path) == file_signature:
			continue
		copy_file(source_path, destination_path)
		copied += 1

	for relative_path in previous.keys() - current.keys():
		destination_path = mapping.destination / relative_path
		if destination_path.is_file() or destination_path.is_symlink():
			destination_path.unlink()
			removed += 1

	return current, copied, removed


def main() -> None:
	parser = argparse.ArgumentParser(description="Sync mounted development sources into the Bench apps directory.")
	parser.add_argument("--once", action="store_true", help="Run one synchronization pass and exit.")
	args = parser.parse_args()

	signal.signal(signal.SIGTERM, stop)
	signal.signal(signal.SIGINT, stop)
	snapshots: dict[Path, dict[Path, tuple[int, int]]] = {mapping.source: {} for mapping in MAPPINGS}
	if args.once:
		print(f"[dev-sync] synchronizing {SOURCE_ROOT}", flush=True)
	else:
		print(f"[dev-sync] watching {SOURCE_ROOT} every {POLL_INTERVAL:.1f}s", flush=True)

	while running:
		for mapping in MAPPINGS:
			try:
				updated, copied, removed = sync_mapping(mapping, snapshots[mapping.source])
				snapshots[mapping.source] = updated
				if copied or removed:
					print(
						f"[dev-sync] {mapping.source.name or 'hrms'}: "
						f"{copied} copied, {removed} removed",
						flush=True,
					)
			except Exception as exc:
				print(f"[dev-sync] sync failed for {mapping.source}: {exc}", flush=True)
		if args.once:
			break
		time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
	main()
