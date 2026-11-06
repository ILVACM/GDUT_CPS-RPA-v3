# -*- coding: utf-8 -*-
"""tools/doc_verify.py — 文档体检脚本（批次 E/P1-11，doc-governance §4 脚本化）。

检查项：
  [1] 相对链接可达（AGENTS.md、README.md、docs/**、knowledge/**）
  [2] docs/INDEX.md 日期列 vs 各文档 frontmatter last-updated
  [3] AGENTS.md 容量三口径（含CR<=8000 / 余量>=200 建议 / LF归一化+行数）
      与行尾约束（必须 CRLF：loneCR/loneLF=0）

输出：退出码 0=全绿；markdown 报告写 _temp/verify-<YYYYMMDD-HHMM>.md（留痕）。
用法：python tools/doc_verify.py（仓库根执行，纯标准库）。
"""

import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_FENCE_RE = re.compile(r"^```.*?^```", re.S | re.M)
_CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SKIP_PREFIXES = ("http://", "https://", "mailto:", "ftp://")

CAPACITY_LIMIT = 8000
CAPACITY_MARGIN = 200


def _scan_targets():
    files = []
    for name in ("AGENTS.md", "README.md"):
        p = ROOT / name
        if p.exists():
            files.append(p)
    for sub in ("docs", "knowledge"):
        base = ROOT / sub
        if base.is_dir():
            files.extend(sorted(base.rglob("*.md")))
    return files


def check_links():
    """[1] 相对链接可达性。返回 (failures, checked_count)。"""
    failures = []
    checked = 0
    for f in _scan_targets():
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            failures.append(f"{f.relative_to(ROOT)}: 读取失败 {e}")
            continue
        # 代码块/行内代码内的 [x](y) 非链接（防误报，如 handlers[op](df)）
        text = _CODE_SPAN_RE.sub("", _FENCE_RE.sub("", text))
        for m in _LINK_RE.finditer(text):
            target = m.group(1)
            if target.startswith(_SKIP_PREFIXES) or target.startswith("#"):
                continue
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            checked += 1
            resolved = (f.parent / path_part).resolve()
            if not resolved.exists():
                failures.append(
                    f"{f.relative_to(ROOT)}: 链接不可达 -> {target}")
    return failures, checked


def _frontmatter_last_updated(doc: Path):
    try:
        lines = doc.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:40]:
        if line.strip() == "---":
            break
        if line.startswith("last-updated:"):
            return line.split(":", 1)[1].strip()
    return None


def check_index_dates():
    """[2] docs/INDEX.md 日期列 vs frontmatter last-updated。"""
    failures = []
    index = ROOT / "docs" / "INDEX.md"
    if not index.exists():
        return ["docs/INDEX.md 不存在"]
    for line in index.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        m = re.match(r"\[[^\]]+\]\((\./[^)]+\.md)\)", cells[0])
        if not m:
            continue
        doc_rel = m.group(1)
        doc = (index.parent / doc_rel).resolve()
        listed = cells[4].strip()
        if not _DATE_RE.match(listed):
            failures.append(f"INDEX 行日期列非日期格式: {doc_rel} -> {listed!r}")
            continue
        if not doc.exists():
            failures.append(f"INDEX 登记文档不存在: {doc_rel}")
            continue
        actual = _frontmatter_last_updated(doc)
        if actual is None:
            failures.append(f"{doc_rel}: 无 frontmatter last-updated")
        elif actual != listed:
            failures.append(
                f"{doc_rel}: INDEX 日期 {listed} != frontmatter {actual}")
    return failures


def check_agents_capacity():
    """[3] AGENTS.md 容量三口径＋行尾约束。返回 (failures, metrics_lines)。"""
    failures = []
    p = ROOT / "AGENTS.md"
    raw = p.read_bytes()
    text = raw.decode("utf-8")
    n_cr = len(text)                       # 口径1：含 CR 字符数
    text_lf = text.replace("\r\n", "\n")
    n_lf = len(text_lf)                    # 口径2：LF 归一化字符数
    n_lines = text_lf.count("\n") + (0 if text_lf.endswith("\n") else 1)
    lone_cr = sum(1 for i, ch in enumerate(text)
                  if ch == "\r" and not (i + 1 < len(text)
                                         and text[i + 1] == "\n"))
    lone_lf = sum(1 for i, ch in enumerate(text)
                  if ch == "\n" and not (i >= 1 and text[i - 1] == "\r"))
    margin = CAPACITY_LIMIT - n_cr
    metrics = [
        f"含CR字符数: {n_cr} / 上限 {CAPACITY_LIMIT}（余量 {margin}）",
        f"LF归一化字符数: {n_lf}",
        f"行数: {n_lines}",
        f"loneCR={lone_cr} loneLF={lone_lf}（要求均为 0＝纯 CRLF）",
    ]
    if n_cr > CAPACITY_LIMIT:
        failures.append(f"AGENTS.md 含CR字符数 {n_cr} 超上限 {CAPACITY_LIMIT}")
    elif margin < CAPACITY_MARGIN:
        metrics.append(
            f"[警告] 余量 {margin} < {CAPACITY_MARGIN}：新增内容前须先下沉细节")
    if lone_cr or lone_lf:
        failures.append(
            f"AGENTS.md 行尾非纯 CRLF（loneCR={lone_cr}, loneLF={lone_lf}）")
    return failures, metrics


def main() -> int:
    link_failures, checked = check_links()
    index_failures = check_index_dates()
    cap_failures, cap_metrics = check_agents_capacity()

    all_failures = ([f"[链接] {x}" for x in link_failures]
                    + [f"[INDEX日期] {x}" for x in index_failures]
                    + [f"[AGENTS容量] {x}" for x in cap_failures])

    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    report_dir = ROOT / "_temp"
    report_dir.mkdir(exist_ok=True)
    report_path = report_dir / f"verify-{stamp}.md"

    lines = [
        f"# 文档体检报告 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"- 结论: {'全绿 PASS' if not all_failures else f'FAIL（{len(all_failures)} 项）'}",
        f"- 链接检查数: {checked}",
        "",
        "## AGENTS.md 容量三口径",
        "",
    ]
    lines += [f"- {m}" for m in cap_metrics]
    lines += ["", "## 失败项", ""]
    if all_failures:
        lines += [f"- {x}" for x in all_failures]
    else:
        lines.append("- 无")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"doc_verify: {'PASS' if not all_failures else 'FAIL'} "
          f"(links={checked}, failures={len(all_failures)})")
    for x in all_failures:
        print(f"  - {x}")
    print(f"report: {report_path.relative_to(ROOT)}")
    return 0 if not all_failures else 1


if __name__ == "__main__":
    sys.exit(main())
