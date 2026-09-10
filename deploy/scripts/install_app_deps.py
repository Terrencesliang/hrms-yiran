#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同步 employee_roster 的 Python 依赖(供 update-code.sh 调用)。

背景:update-code.sh 只同步代码 + migrate + build,不会安装 pyproject.toml
      里新增的依赖 → 运行期报 "No module named 'xxx'"(如 reportlab、
      腾讯云 COS/电子签 SDK)。

说明:
- 动态读取 apps/employee_roster/pyproject.toml 的 dependencies;
- **跳过 cryptography**:上游声明 `>=43,<47`,而 bench 环境为 50.x,
  按 -e 安装会强制降级,可能影响 base 环境,故在此排除
  (如确需按上游约束降级,可去掉 SKIP_PREFIXES 中的该项)。
用法(在 backend 容器内,bench 根目录执行):
    env/bin/python /workspace/source/deploy/scripts/install_app_deps.py
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

APP = "apps/employee_roster"
SKIP_PREFIXES = ("cryptography",)  # 见文件头说明


def read_dependencies(pyproject: pathlib.Path) -> list[str]:
    src = pyproject.read_text(encoding="utf-8")
    match = re.search(r"^dependencies\s*=\s*\[(.*?)\]", src, re.S | re.M)
    if not match:
        return []
    block = match.group(1)
    deps: list[str] = []
    for raw in block.splitlines():
        line = raw.split("#")[0].strip().rstrip(",").strip()
        line = line.strip('"').strip("'")
        if line:
            deps.append(line)
    return deps


def main() -> int:
    pyproject = pathlib.Path(APP, "pyproject.toml")
    if not pyproject.exists():
        print(f"[deps] 未找到 {pyproject},跳过")
        return 0

    deps = read_dependencies(pyproject)
    install: list[str] = []
    for dep in deps:
        name = re.split(r"[<>=!~\[]", dep, maxsplit=1)[0].strip().lower()
        if any(name.startswith(p) for p in SKIP_PREFIXES):
            print(f"[deps] 跳过 {dep}(避免与 bench 环境冲突)")
            continue
        install.append(dep)

    if not install:
        print("[deps] 无需要安装的依赖")
        return 0

    print("[deps] 安装/校验:", ", ".join(install))
    cmd = [sys.executable, "-m", "pip", "install", "-q"] + install
    rc = subprocess.call(cmd)
    if rc != 0:
        print(f"[deps] pip 安装失败(exit {rc})")
        return rc
    print("[deps] 完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
