"""tools/make_fingerprint.py — 构建源码指纹（R6/C1-P0-3，D5 裁定：双指纹）。

输出 KEY=VALUE 行到 stdout（build.bat 解析 SOURCE_HASH/GIT_REV）：
    SOURCE_HASH=<rpa_engine/**/*.py 按相对路径排序，逐文件 sha256
                 （路径+内容）串联后再 sha256，取前 16 位>
    FILES=<参与哈希的 .py 文件数>
    GIT_REV=<git rev-parse HEAD；git 不可用/非仓库/超时 → N/A>

用法：python tools/make_fingerprint.py（仓库根执行，纯标准库）。
判据（build-guide §1.10 第 4 条）：交付包 BUILD_INFO 的 SOURCE_HASH
与当前源码重算值一致 → 包与源码同版；不一致 → 包失效需重建。
"""

import hashlib
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    files = sorted((root / "rpa_engine").rglob("*.py"))
    h = hashlib.sha256()
    for f in files:
        rel = str(f.relative_to(root)).replace("\\", "/")
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(hashlib.sha256(f.read_bytes()).digest())
    print(f"SOURCE_HASH={h.hexdigest()[:16]}")
    print(f"FILES={len(files)}")

    rev = "N/A"
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            rev = out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    print(f"GIT_REV={rev}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
