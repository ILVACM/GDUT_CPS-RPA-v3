# code.md — `supervision_report` 代码修改指令书

> **本文件性质**：跨执行者（换模型、换软件）的**确定性施工指令书**。任何执行者严格照做，产物逐字节一致。
> **上游依据**：`_temp/plan.md`（2026-11-02 定稿，全部裁定已落文）。本文件是 plan.md 的**实现级细化**，两者冲突处以本文件为准（冲突点已集中列于 §2 勘误表）。
> **目标**：新增用户操作 `supervision_report`（履职表单抽查报告）——输入 1~N 张同格式数据表，输出 1 个 xlsx（3 张统计 sheet）+ 1 个 txt（单行总结）。
> **基线**：仓库 `D:\cps-gpes_rpa-20250312`，工作目录 `v3/`，源码指纹 `SOURCE_HASH=9fc85bc09ac1376a`（FILES=56，改动后必变，exe 由人工重建）。

---

## 0. 执行约定（必读）

1. **执行顺序**：严格按 §3 批次顺序（0→10）。同一批次内按编号顺序。
2. **编辑语义**：每条修改给出【定位锚】（原文，精确匹配，全文唯一）与【改为】（替换后全文）。定位锚必须在文件中**恰好出现 1 次**；多于 1 次时停下来人工裁决，不得猜测。
3. **缩进**：所有代码块的缩进是**空格**（本仓库 Python 用 4 空格），不得转换为 Tab。
4. **行尾**：`AGENTS.md`/`README.md`/`docs/**` 用 CRLF；`rpa_engine/**/*.py` 跟随文件现状（现为 LF）。改完后不得引入混合行尾。
5. **禁止事项**：禁止 git 写操作（add/commit/push 等，提交由人工）；禁止改动本指令书未列出的文件；禁止"顺手优化"。
6. **每批次后验证**：批次 2 起，每完成一批执行 `python -m py_compile <改动的 .py>`（在 `rpa_engine/` 下），必须零报错再进下一批。
7. **编码**：新文件为 UTF-8、无 BOM（txt 输出文件除外，其 BOM 由 `utf-8-sig` 写出）。
8. **术语**：【新增】＝创建全新文件；【修改】＝按锚替换；`…` 表示锚内省略的原文（以文件现状为准）。

---

## 1. 产物总览

| 批次 | 文件 | 操作 | 影响指纹 |
|---|---|---|---|
| 0 | —（只读检查） | — | 否 |
| 1 | `rpa_engine/ops/supervision_report.py` | 【新增】全文 | 是 |
| 2 | `rpa_engine/ops/step_executor.py` | 【修改】3 处 | 是 |
| 3 | `RPA_Workflow_v3.spec` | 【修改】1 处 | 否（spec 不在指纹范围） |
| 4 | `rpa_engine/gui/models.py` | 【修改】5 处 | 是 |
| 5 | `rpa_engine/gui/forms.py` | 【修改】3 处 | 是 |
| 6 | `rpa_engine/gui/page_operation_config.py` | 【修改】2 处 | 是 |
| 7 | `rpa_engine/gui/main_window.py` | 【修改】1 处 | 是 |
| 8 | `rpa_engine/tests/test_supervision_report.py` | 【新增】全文 | 否（tests/ 不在指纹范围） |
| 9 | 文档 6 件 | 【修改】若干处 | 否 |
| 10 | 门禁复跑 | — | — |

---

## 2. plan.md 勘误表（执行前知悉；plan.md 已按此同步修正）

| # | plan.md 原文 | 更正为 | 理由 |
|---|---|---|---|
| C1 | `"extra_input_min": 1` | **`"extra_input_min": 0`** | 字段语义＝"除目标表外的最小**额外**输入表数"（`step_executor.py` L49 注释）；追加表是**可选**的。且 `tests/test_registry_single_source.py` L135 断言"除 mapping_match/merge_tables 外必须为 0"，设 1 会打破现有测试 |
| C2 | §3.3 函数签名参数名 `extra_table_ids` | 函数层参数名 **`extra_tables`**（值为 `_translate_table_id` 翻译后的**物理表名**） | JSON 键名仍为 `extra_table_ids`（逻辑表号 T2 等）；函数入参是物理名，命名须区分 |
| C3 | 批次 1.4 建议 `Workbook(write_only=True)` | **标准 `Workbook()`** | 输出表仅 ≤60 行，无内存风险；且需冻结首行/设列宽/加粗（write-only 模式支持不全） |
| C4 | §3A.3 "取文本前 10 位按格式匹配" | **先按空格截断取日期部分，再按格式匹配** | "前 10 位"会截断 `2026/9/5 10:00` 之类的值 |
| C5 | `BaseParamForm` 仅加 `source_dir` 可选参数 | 加 **3 个**可选参数：`source_dir`、`registry`、`target_table_id` | §9 参数 2 需按"目标表+追加表日期并集"显示期间提示、D2 需别名显示，均需 registry |

### 2.1 已知行为（设计取舍，非遗漏；独立验证员复核确认）

| # | 行为 | 判定 |
|---|---|---|
| K1 | `workday_count` 经 `int()` 转换，手写 JSON 传 `2.9` 会静默取整为 2 | 设计取舍：GUI 传整数；引擎校验范围 1~366 已足够 |
| K2 | `output_path` 后缀非 `.xlsx`（如 `.xls`）时按原样写入，不纠正 | 设计取舍：GUI 保存对话框过滤器限定 `*.xlsx`；`txt` 侧按 `Path.with_suffix('.txt')` 派生 |
| K3 | 多表合并的临时表（`_t_supervision_tmp`）在 `__normalize_meta` 无记录，日期列识别回落业务常量 `COL_DATE` | 可接受：真实数据日期列即该列名；单表路径优先走 `__normalize_meta` |
| K4 | 表3 括号内 N 张 = 人员计数 + 空检查人行（`blank`） | ✅ **已按 plan「该部门草稿+整改中总数」严格实现**（T-19 覆盖） |
| K5 | `probe_period` 由 T-12 覆盖（`found`/`date_min`/`date_max`/`natural_days`/`workday_default`） | ✅ 导出 API 已有用例 |

---

## 3. 批次 0：前置检查（只读，不改任何文件）

在 `v3/rpa_engine/` 下逐条确认（PowerShell）：

```powershell
Select-String -LiteralPath 'ops\step_executor.py' -Pattern 'GUI_INJECTED_PARAM_KEYS'      # 应命中 L59
Select-String -LiteralPath 'gui\models.py' -Pattern '^STEP_COUNT'                          # 应命中 L96
Select-String -LiteralPath 'gui\forms.py' -Pattern 'class ExportForm'                      # 应命中 L458
Select-String -LiteralPath 'gui\page_operation_config.py' -Pattern 'conn_columns=self\._conn_columns\(\), parent=w'  # 应命中 L384
Select-String -LiteralPath 'gui\main_window.py' -Pattern '"columns": columns,'             # 应命中 L404
Select-String -LiteralPath 'tests\test_registry_single_source.py' -Pattern 'extra_input_min 应为 0'  # 应命中 L135
```

全部命中后执行基线门禁，期望：

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python -m unittest discover -s tests     # Ran 234 tests ... OK
python tools/smoke/smoke_m1m3.py         # SMOKE_ALL_OK
python tools/smoke/smoke_mb.py           # SMOKE_ALL_OK
```

基线不绿则**停止**，不得继续。

---

## 4. 批次 1：【新增】`rpa_engine/ops/supervision_report.py`

创建文件，内容为下列全文（一字不改；注意缩进为空格、末尾换行）：

```python
"""
rpa_engine/ops/supervision_report.py

Layer 2 — 履职表单抽查报告（用户操作目录，supervision_report）。

一次生成 2 个文件：
- output_path（.xlsx）：3 张统计 sheet（项目部 / 专业 / 草稿整改中）
- 同主名 .txt：1 段总结文字（UTF-8 带 BOM，单行）

实现口径唯一依据：_temp/plan.md §2A / §2A.9 / §3A.3。

约束：
- 业务字面量集中在下方「业务适配层」常量区（tests T-16 静态检查依据）
- 禁用 pandas，全表流式读取（内存红线 AGENTS §2.1 条 5）
- 舍入：Decimal ROUND_HALF_UP，固定位数补零
"""

import sqlite3
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from ops.sql_safety import get_table_columns, quote_ident, require_table
from ops.table_lifecycle import delete_table, merge_tables

# ==========================================================================
# 监理部业务适配层（唯一允许业务字面量的区域；将来通用化时仅需换本段）
# ==========================================================================
COL_DEPT = "部门"
COL_PERSON = "检查人"
COL_DATE = "检查时间"
COL_PROF = "专业名称"
COL_BAD = "不合格项"
COL_STATUS = "工单状态"

STATUS_CLOSED = "已闭环"
STATUS_DRAFT = "草稿"
STATUS_FIXING = "整改中"

SHEET_DEPT = "各总监项目部填写情况统计表"
SHEET_PROF = "各专业表单填写情况统计表"
SHEET_TODO = "草稿、整改中履职表单情况统计表"

BLANK_LABEL = "（未填写）"
TOTAL_LABEL = "合计"
EMPTY_CELL = "/"
PERSON_JOIN = "、"
PERSON_TALLY_FMT = "{name}（{n}张）"
DEPT_TALLY_FMT = "{label}（{n}张）"
DEPT_SUFFIXES = ("总监项目部", "监理项目部")

HEAD1 = ("项目部", "人数", "工作日平均每人每日表单数", "自然日平均每人每日表单数")
HEAD2 = ("专业名称", "履职表单数", "占比")
HEAD3 = ("项目部", "草稿状态人员", "整改中人员")

SUMMARY_TEMPLATE = (
    "{period}各总监项目部共填写履职表单{total}张，"
    "自然日平均每人每日填写表单{nat_avg}张，"
    "工作日平均每人每日填写表单{work_avg}张。"
    "有发现问题表单{problem}张（占比{problem_pct}%），"
    "已闭环{closed}张（占比{closed_pct}%）。"
    "其余有{draft}张草稿、{rectifying}张整改中。"
)
DIRTY_SUFFIX = "（另有 {n} 行日期无法识别）"

OUTPUT_NAME_PREFIX = "履职表单报告统计"
OUTPUT_TIME_FMT = "%Y%m%d%H%M"

ERR_OUTPUT_PATH = "未指定保存位置"
ERR_DATE_COL = "这份数据里找不到检查日期，请确认导入的是履职表单"
ERR_EMPTY_DATA = "这份数据里没有内容，请重新导入"
ERR_WORKDAY_RANGE = "实际工作日天数须在 1~366 之间"
ERR_WRITE_FAIL = "这个位置存不进去，请换一个文件夹（比如桌面）"
ERR_MISSING_COLUMN = "数据里缺少「{col}」列"
WARN_WORKDAY_MISMATCH = (
    "你填的工作日天数（{user}）与系统统计口径（周一至周五 {default} 天）不一致，"
    "工作日平均会偏高。不确定就保持默认值。"
)
# ==========================================================================

_TMP_TABLE = "_t_supervision_tmp"
_CN_DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9}
_BIZ_COLS = (COL_DEPT, COL_PERSON, COL_PROF, COL_BAD, COL_STATUS)


def _parse_date(value: Any) -> Optional[date]:
    """解析日期值；仅接受 3 种格式，其余返回 None（视为脏日期）。"""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.split(" ", 1)[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _round_str(value: float, ndigits: int) -> str:
    """四舍五入到固定小数位（Decimal ROUND_HALF_UP，补零）。"""
    q = Decimal(1).scaleb(-ndigits)
    d = Decimal(repr(float(value))).quantize(q, rounding=ROUND_HALF_UP)
    return f"{d:.{ndigits}f}"


def _avg(count: int, people: int, days: int) -> float:
    """人均日填；people=0 或 days<=0 时返回 0.0（不抛错）。"""
    if people <= 0 or days <= 0:
        return 0.0
    return count / people / days


def _dept_short(dept: str) -> str:
    """去掉名称后缀（见 DEPT_SUFFIXES）；空值返回 BLANK_LABEL。"""
    if not dept:
        return BLANK_LABEL
    for suf in DEPT_SUFFIXES:
        if dept.endswith(suf):
            return dept[: -len(suf)]
    return dept


def _dept_number(short_label: str) -> Optional[int]:
    """「第+中文数字（一至九十九）」→ 数值；其余返回 None。"""
    if not short_label.startswith("第"):
        return None
    s = short_label[1:]
    if s == "十":
        return 10
    if s.startswith("十"):
        tail = s[1:]
        return 10 + _CN_DIGITS[tail] if len(tail) == 1 and tail in _CN_DIGITS else None
    if "十" in s:
        a, _, b = s.partition("十")
        if a in _CN_DIGITS and (b == "" or (len(b) == 1 and b in _CN_DIGITS)):
            return _CN_DIGITS[a] * 10 + (_CN_DIGITS[b] if b else 0)
        return None
    return _CN_DIGITS.get(s)


def _period_label(dmin: date, dmax: date) -> str:
    """期间标签：9月 / 3月-7月 / 2025年12月-2026年2月 / 9月15日。"""
    if dmin == dmax:
        return f"{dmin.month}月{dmin.day}日"
    if dmin.year == dmax.year:
        if dmin.month == dmax.month:
            return f"{dmin.month}月"
        return f"{dmin.month}月-{dmax.month}月"
    return f"{dmin.year}年{dmin.month}月-{dmax.year}年{dmax.month}月"


def _person_cell(counter: Dict[str, int]) -> str:
    """人员串：姓名（N张）、……；张数降序→姓名码点升序；空→EMPTY_CELL。"""
    if not counter:
        return EMPTY_CELL
    items = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    return PERSON_JOIN.join(PERSON_TALLY_FMT.format(name=n, n=c)
                            for n, c in items)


def _date_column(conn: sqlite3.Connection, table_name: str) -> Optional[str]:
    """日期列识别：__normalize_meta datetime 第一列 → 回落 COL_DATE → None。"""
    try:
        rows = conn.execute(
            "SELECT column FROM __normalize_meta WHERE sqlite_table = ? "
            "AND original_type = 'datetime'", (str(table_name),)).fetchall()
        cols = [str(r[0]) for r in rows if r and r[0]]
    except sqlite3.Error:
        cols = []
    if cols:
        return cols[0]
    try:
        if COL_DATE in get_table_columns(conn, table_name):
            return COL_DATE
    except ValueError:
        return None
    return None


def _count_workdays(dmin: date, dmax: date) -> int:
    n = 0
    cur = dmin
    while cur <= dmax:
        if cur.weekday() < 5:
            n += 1
        cur += timedelta(days=1)
    return n


def _analyze(conn: sqlite3.Connection, table_name: str) -> Dict[str, Any]:
    """单遍流式统计（只取 6 列，不整表载入 DataFrame）。"""
    require_table(conn, table_name)
    date_col = _date_column(conn, table_name)
    if date_col is None:
        raise ValueError(ERR_DATE_COL)
    existing = set(get_table_columns(conn, table_name))
    for c in _BIZ_COLS:
        if c not in existing:
            raise ValueError(ERR_MISSING_COLUMN.format(col=c))
    cols = [COL_DEPT, COL_PERSON, date_col, COL_PROF, COL_BAD, COL_STATUS]
    sql = ("SELECT " + ", ".join(quote_ident(c) for c in cols)
           + " FROM " + quote_ident(table_name))
    total = 0
    dirty = 0
    persons_all: set = set()
    persons_wd: set = set()
    wd_rows = 0
    bad_cnt = 0
    closed_cnt = 0
    draft_cnt = 0
    fixing_cnt = 0
    dmin: Optional[date] = None
    dmax: Optional[date] = None
    dept_stat: Dict[str, Dict[str, Any]] = {}
    prof_cnt: Dict[str, int] = {}
    todo: Dict[str, Dict[str, Dict[str, int]]] = {}
    for dept, person, dval, prof, bad, status in conn.execute(sql):
        total += 1
        d_key = dept or ""
        p_key = person or ""
        pr_key = prof or ""
        if p_key:
            persons_all.add(p_key)
        dt = _parse_date(dval)
        is_wd = False
        if dt is None:
            dirty += 1
        else:
            if dmin is None or dt < dmin:
                dmin = dt
            if dmax is None or dt > dmax:
                dmax = dt
            if dt.weekday() < 5:
                is_wd = True
                wd_rows += 1
                if p_key:
                    persons_wd.add(p_key)
        is_bad = (isinstance(bad, (int, float))
                  and not isinstance(bad, bool) and bad > 0)
        if is_bad:
            bad_cnt += 1
            if status == STATUS_CLOSED:
                closed_cnt += 1
        if status == STATUS_DRAFT:
            draft_cnt += 1
        elif status == STATUS_FIXING:
            fixing_cnt += 1
        ds = dept_stat.setdefault(d_key, {"n": 0, "persons": set(),
                                          "wd_n": 0, "wd_p": set()})
        ds["n"] += 1
        if p_key:
            ds["persons"].add(p_key)
        if is_wd:
            ds["wd_n"] += 1
            if p_key:
                ds["wd_p"].add(p_key)
        prof_cnt[pr_key] = prof_cnt.get(pr_key, 0) + 1
        if status in (STATUS_DRAFT, STATUS_FIXING):
            bucket = todo.setdefault(
                d_key, {"draft": {}, "fix": {}, "blank": 0})
            which = "draft" if status == STATUS_DRAFT else "fix"
            if p_key:
                bucket[which][p_key] = bucket[which].get(p_key, 0) + 1
            else:
                bucket["blank"] += 1
    if total == 0:
        raise ValueError(ERR_EMPTY_DATA)
    if dmin is None or dmax is None:
        raise ValueError(ERR_DATE_COL)
    return {"total": total, "dirty": dirty, "dmin": dmin, "dmax": dmax,
            "natural_days": (dmax - dmin).days + 1,
            "workday_default": _count_workdays(dmin, dmax),
            "persons_all": persons_all, "persons_wd": persons_wd,
            "wd_rows": wd_rows, "bad": bad_cnt, "closed": closed_cnt,
            "draft": draft_cnt, "fixing": fixing_cnt,
            "dept": dept_stat, "prof": prof_cnt, "todo": todo}


def _eff_wd(st: Dict[str, Any], workday_count: int) -> int:
    """生效工作日天数：>0 用用户值；0 用 workday_default；默认为 0 时取 1。"""
    if workday_count > 0:
        return workday_count
    return st["workday_default"] if st["workday_default"] > 0 else 1


def _summary_text(st: Dict[str, Any], workday_count: int) -> str:
    eff = _eff_wd(st, workday_count)
    total = st["total"]
    nat_avg = _avg(total, len(st["persons_all"]), st["natural_days"])
    work_avg = _avg(st["wd_rows"], len(st["persons_wd"]), eff)
    text = SUMMARY_TEMPLATE.format(
        period=_period_label(st["dmin"], st["dmax"]),
        total=total,
        nat_avg=_round_str(nat_avg, 2),
        work_avg=_round_str(work_avg, 2),
        problem=st["bad"],
        problem_pct=_round_str(st["bad"] / total * 100, 2) if total else "0.00",
        closed=st["closed"],
        closed_pct=(_round_str(st["closed"] / st["bad"] * 100, 2)
                    if st["bad"] else "0.00"),
        draft=st["draft"],
        rectifying=st["fixing"],
    )
    if st["dirty"]:
        text += DIRTY_SUFFIX.format(n=st["dirty"])
    return text


def _build_tables(st: Dict[str, Any], workday_count: int):
    eff = _eff_wd(st, workday_count)
    nat = st["natural_days"]
    total = st["total"]
    rows1_src = []
    for dept, d in st["dept"].items():
        label = _dept_short(dept)
        work = _avg(d["wd_n"], len(d["wd_p"]), eff)
        rows1_src.append((label, len(d["persons"]), work,
                          _avg(d["n"], len(d["persons"]), nat), d["n"]))
    rows1_src.sort(key=lambda r: (-r[2], -r[1], r[0]))
    rows1 = [[r[0], r[1], _round_str(r[2], 1), _round_str(r[3], 1)]
             for r in rows1_src]
    rows1.append([TOTAL_LABEL, len(st["persons_all"]),
                  _round_str(_avg(st["wd_rows"], len(st["persons_wd"]), eff), 1),
                  _round_str(_avg(total, len(st["persons_all"]), nat), 1)])
    prof_sorted = sorted(st["prof"].items(), key=lambda kv: (-kv[1], kv[0]))
    rows2 = [[(BLANK_LABEL if not k else k), v,
              _round_str(v / total * 100, 1) + "%"] for k, v in prof_sorted]
    rows2.append([TOTAL_LABEL, total, "100%"])

    def order3(dept: str):
        num = _dept_number(_dept_short(dept))
        if num is not None:
            return (0, num, "")
        return (1, -st["dept"][dept]["n"], _dept_short(dept))
    rows3 = []
    for dept in sorted(st["dept"].keys(), key=order3):
        bucket = st["todo"].get(dept, {})
        draft_c = bucket.get("draft", {})
        fix_c = bucket.get("fix", {})
        n = (sum(draft_c.values()) + sum(fix_c.values())
             + bucket.get("blank", 0))
        rows3.append([DEPT_TALLY_FMT.format(label=_dept_short(dept), n=n),
                      _person_cell(draft_c), _person_cell(fix_c)])
    return rows1, rows2, rows3


def _resolve_outputs(output_path: str) -> Tuple[Path, Path]:
    """目标冲突时 xlsx/txt 同批加 -2、-3… 后缀（任一存在即整体加）。"""
    base = Path(output_path)
    if not base.suffix:
        base = base.with_suffix(".xlsx")
    txt = base.with_suffix(".txt")
    if not base.exists() and not txt.exists():
        return base, txt
    n = 2
    while True:
        cand = base.with_name(base.stem + f"-{n}" + base.suffix)
        cand_txt = cand.with_suffix(".txt")
        if not cand.exists() and not cand_txt.exists():
            return cand, cand_txt
        n += 1


def _fill_sheet(wb, title: str, headers, rows, bold: Font) -> None:
    ws = wb.create_sheet(title=title[:31])
    ws.freeze_panes = "A2"
    ws.append(list(headers))
    for cell in ws[1]:
        cell.font = bold
    for row in rows:
        ws.append(list(row))
        if row and str(row[0]) == TOTAL_LABEL:
            for cell in ws[ws.max_row]:
                cell.font = bold
    for ci in range(1, len(headers) + 1):
        mx = len(str(headers[ci - 1]))
        for row in rows:
            if ci - 1 < len(row):
                mx = max(mx, len(str(row[ci - 1])))
        ws.column_dimensions[get_column_letter(ci)].width = min(60, max(10, mx + 4))


def _write_report(xlsx_path: Path, txt_path: Path,
                  rows1, rows2, rows3, text: str) -> None:
    bold = Font(bold=True)
    wb = Workbook()
    wb.remove(wb.active)
    _fill_sheet(wb, SHEET_DEPT, HEAD1, rows1, bold)
    _fill_sheet(wb, SHEET_PROF, HEAD2, rows2, bold)
    _fill_sheet(wb, SHEET_TODO, HEAD3, rows3, bold)
    try:
        xlsx_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(xlsx_path))
        txt_path.write_text(text, encoding="utf-8-sig")
    except OSError as e:
        raise ValueError(ERR_WRITE_FAIL) from e


def probe_period(conn: sqlite3.Connection, table_name: str) -> Dict[str, Any]:
    """探测统计期间（GUI 提示用）；任何异常 → found=False，不抛错。"""
    empty = {"found": False, "date_min": None, "date_max": None,
             "natural_days": None, "workday_default": None, "dirty_count": 0}
    try:
        require_table(conn, table_name)
        col = _date_column(conn, table_name)
        if col is None:
            return dict(empty)
        dmin: Optional[date] = None
        dmax: Optional[date] = None
        dirty = 0
        for (v,) in conn.execute(
                "SELECT " + quote_ident(col) + " FROM " + quote_ident(table_name)):
            dt = _parse_date(v)
            if dt is None:
                dirty += 1
                continue
            if dmin is None or dt < dmin:
                dmin = dt
            if dmax is None or dt > dmax:
                dmax = dt
        if dmin is None or dmax is None:
            return dict(empty)
        return {"found": True, "date_min": dmin.isoformat(),
                "date_max": dmax.isoformat(),
                "natural_days": (dmax - dmin).days + 1,
                "workday_default": _count_workdays(dmin, dmax),
                "dirty_count": dirty}
    except Exception:  # noqa: BLE001 探测不抛错
        logger.debug(f"[supervision_report] probe_period 失败: {table_name}")
        return dict(empty)


def workday_hint(user_value: Optional[int],
                 default_value: Optional[int]) -> Optional[str]:
    """工作日天数口径提示文案；无不一致返回 None（GUI 就地提示用）。"""
    if user_value is None or default_value is None:
        return None
    if user_value == 0 or user_value == default_value:
        return None
    return WARN_WORKDAY_MISMATCH.format(user=user_value, default=default_value)


def build_supervision_report(
    conn: sqlite3.Connection,
    table_name: str,
    output_path: str,
    workday_count: int = 0,
    extra_tables: Optional[List[str]] = None,
) -> int:
    """生成履职表单抽查报告（xlsx 3 sheet + txt 单行总结）。

    Args:
        output_path: 报告 .xlsx 完整路径（GUI 预填）；为空抛 ERR_OUTPUT_PATH。
        workday_count: 实际工作日天数；0=回退期间内周一至周五天数；
            引擎侧校验 1~366（0 除外），越界抛 ERR_WORKDAY_RANGE。
        extra_tables: 追加的同格式物理表名（UNION ALL 合并后统计）。

    Returns:
        写入的文件数（恒为 2）。
    """
    try:
        wc = int(workday_count)
    except (TypeError, ValueError) as e:
        raise ValueError(ERR_WORKDAY_RANGE) from e
    if not 0 <= wc <= 366:
        raise ValueError(ERR_WORKDAY_RANGE)
    if not output_path or not str(output_path).strip():
        raise ValueError(ERR_OUTPUT_PATH)
    require_table(conn, table_name)
    extras = [str(x) for x in (extra_tables or []) if str(x)]
    tmp_table = None
    data_table = table_name
    if extras:
        tmp_table = _TMP_TABLE
        merge_tables(conn, [table_name] + extras, tmp_table)
        data_table = tmp_table
    try:
        stats = _analyze(conn, data_table)
        text = _summary_text(stats, wc)
        rows1, rows2, rows3 = _build_tables(stats, wc)
        xlsx_path, txt_path = _resolve_outputs(str(output_path).strip())
        _write_report(xlsx_path, txt_path, rows1, rows2, rows3, text)
        logger.info(f"[supervision_report] 报告已生成: {xlsx_path}")
        return 2
    finally:
        if tmp_table:
            try:
                delete_table(conn, tmp_table)
            except Exception:  # noqa: BLE001 临时表清理失败不掩盖主异常
                pass
```

---

## 5. 批次 2：【修改】`rpa_engine/ops/step_executor.py`（3 处）

### 2.1 imports 追加

【定位锚】（L32）：

```python
from ops.exporter import export_table
```

【改为】：

```python
from ops.exporter import export_table
from ops.supervision_report import build_supervision_report
```

### 2.2 `BUILTIN_OPS` 增条目

【定位锚】（L127-140，export 条目全段）：

```python
    "export": {
        "func": export_table, "description": "结果导出",
        "output": False,
        "param_keys": {"output_path", "sheet_name"},
        "params_schema": [
            {"key": "output_path", "type": "text", "required": True,
             "default": ""},
            {"key": "sheet_name", "type": "text", "required": False,
             "default": "数据"},
        ],
        "extra_input_min": 0,
        "overwritable": False,
        "deprecated": False,
    },
```

【改为】（原条目后追加新条目）：

```python
    "export": {
        "func": export_table, "description": "结果导出",
        "output": False,
        "param_keys": {"output_path", "sheet_name"},
        "params_schema": [
            {"key": "output_path", "type": "text", "required": True,
             "default": ""},
            {"key": "sheet_name", "type": "text", "required": False,
             "default": "数据"},
        ],
        "extra_input_min": 0,
        "overwritable": False,
        "deprecated": False,
    },
    "supervision_report": {
        "func": build_supervision_report, "description": "履职表单抽查报告",
        "output": False,
        "param_keys": {"output_path", "workday_count", "extra_table_ids"},
        "params_schema": [
            {"key": "output_path", "type": "text", "required": True,
             "default": ""},
            {"key": "workday_count", "type": "integer", "required": False,
             "default": 0},
            {"key": "extra_table_ids", "type": "list", "required": False,
             "default": []},
        ],
        "extra_input_min": 0,
        "overwritable": False,
        "deprecated": False,
    },
```

> **注意 `extra_input_min: 0`**（勘误 C1）。

### 2.3 `execute_step` 增分发分支

【定位锚】（L377-381）：

```python
            cancel_check=cancel_check,
        )
    elif op_type == "merge_tables":
```

【改为】：

```python
            cancel_check=cancel_check,
        )
    elif op_type == "supervision_report":
        output_path = clean_params.get(
            "output_path", param_default("supervision_report", "output_path"))
        if not output_path:
            return fail("缺少 output_path（报告保存位置）")
        extra_ids = (clean_params.get("extra_table_ids")
                     or param_default("supervision_report", "extra_table_ids"))
        extra_tables = []
        for eid in extra_ids:
            try:
                extra_tables.append(
                    _translate_table_id(eid, table_id_map, f"步骤 [{step_id}]")
                )
            except ValueError as e:
                return fail(str(e))
        call_args.update(
            table_name=target_table,
            output_path=output_path,
            workday_count=(clean_params.get("workday_count")
                           or param_default("supervision_report", "workday_count")),
            extra_tables=extra_tables,
        )
    elif op_type == "merge_tables":
```

**批次 2 验证**：

```powershell
python -m py_compile ops\step_executor.py ops\supervision_report.py
```

---

## 6. 批次 3：【修改】`RPA_Workflow_v3.spec`（1 处）

【定位锚】：

```python
        'ops.exporter',
```

【改为】：

```python
        'ops.exporter',
        'ops.supervision_report',
```

> 必须改，否则 exe 场景 ImportError（`tests/test_dependency_contract.py` 亦校验声明完整性）。

---

## 7. 批次 4：【修改】`rpa_engine/gui/models.py`（5 处）

### 4.1 `_STEP_META_RAW` 增 1 行（6 元组，**不得填 7 个值**）

【定位锚】（L84-86）：

```python
    ("export", "结果导出", "将数据表导出为 Excel 文件",
     "输出类", ("导出", "保存", "excel"), 9),
]
```

【改为】：

```python
    ("export", "结果导出", "将数据表导出为 Excel 文件",
     "输出类", ("导出", "保存", "excel"), 9),
    ("supervision_report", "履职表单抽查报告", "一次生成多张统计表和一段总结文字",
     "输出类", ("报告", "履职", "抽查", "统计表", "一键", "月报"), 10),
]
```

### 4.2 `STEP_KIND` 增 1 项

【定位锚】（L208）：

```python
    "export":         "end",
```

【改为】：

```python
    "export":         "end",
    "supervision_report": "end",
```

### 4.3 `PRODUCE_LABEL` 增 1 项

【定位锚】（L257）：

```python
    "export": None,
}
```

【改为】：

```python
    "export": None,
    "supervision_report": None,
}
```

### 4.4 `extra_input_ids` 增分支（否则 DAG 边派生漏掉追加表）

【定位锚】（L962-967）：

```python
    if step.type == "merge_tables":
        return [str(x) for x in (step.params.get("match_table_ids") or []) if str(x)]
    return []
```

【改为】：

```python
    if step.type == "merge_tables":
        return [str(x) for x in (step.params.get("match_table_ids") or []) if str(x)]
    if step.type == "supervision_report":
        return [str(x) for x in (step.params.get("extra_table_ids") or []) if str(x)]
    return []
```

### 4.5 `collect_file_stats` 去 `export` 特判 + 同名 txt 收集

【定位锚】（L1019-1033，函数全段）：

```python
def collect_file_stats(model: WorkflowModel, engine_root: Path) -> Dict[str, List[str]]:
    """收集本次执行的输入/输出文件清单（报告页统计用）。"""
    input_files: List[str] = []
    for t in model.tables:
        if t.file_path and t.file_path not in input_files:
            input_files.append(t.file_path)

    output_files: List[str] = []
    for s in model.steps:
        if s.type == "export":
            p = str(s.params.get("output_path", ""))
            if p and p not in output_files:
                output_files.append(p)

    return {"input_files": input_files, "output_files": output_files}
```

【改为】：

```python
def _txt_sidecar(path: str) -> str:
    """同主名 .txt 派生（等价 Path.with_suffix 语义，不引 pathlib）。"""
    dot = path.rfind(".")
    sep = max(path.rfind("/"), path.rfind("\\"))
    return (path[:dot] if dot > sep else path) + ".txt"


def collect_file_stats(model: WorkflowModel, engine_root: Path) -> Dict[str, List[str]]:
    """收集本次执行的输入/输出文件清单（报告页统计用）。

    R18/D1+：凡 params 含 output_path 的步骤均收集（不按操作类型硬编码）；
    supervision_report 另收集同主名 .txt（报告页"输出文件数"真实为 2）。
    """
    input_files: List[str] = []
    for t in model.tables:
        if t.file_path and t.file_path not in input_files:
            input_files.append(t.file_path)

    output_files: List[str] = []
    for s in model.steps:
        p = str(s.params.get("output_path", "") or "").strip()
        if p and p not in output_files:
            output_files.append(p)
        if p and s.type == "supervision_report":
            t = _txt_sidecar(p)
            if t not in output_files:
                output_files.append(t)

    return {"input_files": input_files, "output_files": output_files}
```

**批次 4 验证**：`python -m py_compile gui\models.py`。

---

## 8. 批次 5：【修改】`rpa_engine/gui/forms.py`（3 处）

### 5.0 imports 追加

【定位锚】（L20-24）：

```python
from PyQt5.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton,
    QVBoxLayout, QWidget,
)
```

【改为】：

```python
from PyQt5.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QSpinBox,
    QVBoxLayout, QWidget,
)
```

### 5.1 `BaseParamForm.__init__` 增 3 个可选参数（现有 9 表单零改动）

【定位锚】（L87-101）：

```python
    def __init__(
        self,
        params: Dict[str, Any],
        table_ids: Optional[List[str]] = None,
        conn_columns: Optional[Dict[str, List[str]]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._init_params = dict(params)
        self._table_ids = table_ids or []
        self._conn_columns = conn_columns or {}
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._form = QFormLayout()
        self._layout.addLayout(self._form)
```

【改为】：

```python
    def __init__(
        self,
        params: Dict[str, Any],
        table_ids: Optional[List[str]] = None,
        conn_columns: Optional[Dict[str, List[str]]] = None,
        parent: Optional[QWidget] = None,
        source_dir: str = "",
        registry: Optional[List[Dict[str, Any]]] = None,
        target_table_id: str = "",
    ) -> None:
        super().__init__(parent)
        self._init_params = dict(params)
        self._table_ids = table_ids or []
        self._conn_columns = conn_columns or {}
        self._source_dir = source_dir
        self._registry = registry or []
        self._target_table_id = target_table_id
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._form = QFormLayout()
        self._layout.addLayout(self._form)
```

> 三个新参数均带默认值 → 现有 9 个子类与调用点零改动。

### 5.2 【新增】`SupervisionReportForm` 类

【定位锚】（L598-600）：

```python
# ---------------------------------------------------------------------------
# 表单注册表（2026-09-20 M21：键集单一源 = gui.models.STEP_CATALOG）
# ---------------------------------------------------------------------------
```

【改为】（在其**前面**插入新类）：

```python
class SupervisionReportForm(BaseParamForm):
    """supervision_report：履职表单抽查报告（3 张统计表 + 1 段总结）。

    三参数：保存到（GUI 预填）/ 实际工作日天数（1~366）/ 追加数据表（多选）。
    默认路径与期间提示随目标表/追加表联动（refresh_context）。
    """

    def __init__(self, params, table_ids=None, conn_columns=None, parent=None,
                 source_dir="", registry=None, target_table_id=""):
        super().__init__(params, table_ids, conn_columns, parent,
                         source_dir=source_dir, registry=registry,
                         target_table_id=target_table_id)
        self.setWindowTitle("履职表单抽查报告参数")
        self._auto_path = ""
        # 0. 先建「追加数据表」控件——期间提示与工作日默认值都要读它的勾选态，
        #    故必须先于下方第 2 段创建（否则 AttributeError: _list）
        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.MultiSelection)
        # 1. 保存到（范式抄 ExportForm：文本框 + 浏览…）
        row = QHBoxLayout()
        self._auto_path = self._build_default_path()
        cur = str(params.get("output_path", "")).strip()
        self._path = QLineEdit(cur or self._auto_path)
        browse = QPushButton("浏览…")
        browse.clicked.connect(self._browse)
        row.addWidget(self._path)
        row.addWidget(browse)
        self._form.addRow("保存到", row)
        # 2. 期间提示 + 实际工作日天数
        self._wd_default = self._union_workday_default()
        self._hint = QLabel(self._period_text())
        self._form.addRow("数据期间", self._hint)
        self._spin = QSpinBox()
        self._spin.setRange(1, 366)
        self._spin.setValue(self._wd_default if self._wd_default else 1)
        self._spin.valueChanged.connect(self._refresh_warn)
        self._form.addRow("实际工作日天数", self._spin)
        self._warn = QLabel("")
        self._warn.setWordWrap(True)
        self._form.addRow("", self._warn)
        self._refresh_warn()
        # 3. 追加数据表（显示 别名（编号），D2；控件已在第 0 段创建）
        self._list.itemSelectionChanged.connect(self._refresh_context_view)
        self._rebuild_list()
        self._form.addRow("追加数据表", self._list)

    # ---- 上下文与派生 ----
    def _meta(self, tid: str) -> Dict[str, Any]:
        for e in self._registry:
            if e.get("table_id") == tid:
                return e
        return {}

    def _selected_ids(self) -> List[str]:
        ids = [i.data(256) for i in self._list.selectedItems()]
        return [str(x) for x in ids if str(x)]

    def _union_range(self):
        tids = ([self._target_table_id] if self._target_table_id else [])
        tids += self._selected_ids()
        mins, maxs = [], []
        for tid in tids:
            dr = (self._meta(tid) or {}).get("date_range") or {}
            if dr.get("min") and dr.get("max"):
                mins.append(str(dr["min"]))
                maxs.append(str(dr["max"]))
        if not mins:
            return None
        return min(mins), max(maxs)

    def _union_workday_default(self) -> Optional[int]:
        rng = self._union_range()
        if rng is None:
            return None
        from datetime import datetime as _dt, timedelta as _td
        d0 = _dt.strptime(rng[0], "%Y-%m-%d").date()
        d1 = _dt.strptime(rng[1], "%Y-%m-%d").date()
        n, cur = 0, d0
        while cur <= d1:
            if cur.weekday() < 5:
                n += 1
            cur += _td(days=1)
        return n

    def _period_text(self) -> str:
        rng = self._union_range()
        if rng is None:
            return "未能识别日期范围"
        n = self._union_workday_default() or 0
        return (f"数据涉及时间段：{rng[0]} ~ {rng[1]}，"
                f"其中周一至周五 {n} 天（未扣除法定节假日）")

    def _build_default_path(self) -> str:
        import os
        from datetime import datetime as _dt
        from paths import get_engine_root
        from ops.supervision_report import OUTPUT_NAME_PREFIX, OUTPUT_TIME_FMT
        base_dir = self._source_dir
        if not base_dir:
            src = ""
            if self._target_table_id:
                m = self._meta(self._target_table_id)
                src = str(m.get("source_path") or m.get("file_path") or "")
            if src:
                base_dir = os.path.dirname(src)
        if not base_dir:
            base_dir = str(get_engine_root())
        name = (OUTPUT_NAME_PREFIX + "-"
                + _dt.now().strftime(OUTPUT_TIME_FMT) + ".xlsx")
        return os.path.join(base_dir, name)

    def _rebuild_list(self) -> None:
        selected = set(self._selected_ids())
        self._list.clear()
        for tid in self._table_ids:
            if tid == self._target_table_id:
                continue
            alias = (self._meta(tid) or {}).get("alias") or tid
            item = QListWidgetItem(f"{alias}（{tid}）")
            item.setData(256, tid)  # UserRole
            self._list.addItem(item)
            if tid in selected:
                item.setSelected(True)

    def _refresh_context_view(self) -> None:
        self._hint.setText(self._period_text())
        self._refresh_warn()

    def _refresh_warn(self) -> None:
        msg = None
        try:
            from ops.supervision_report import workday_hint
            msg = workday_hint(int(self._spin.value()),
                               self._union_workday_default())
        except Exception:  # noqa: BLE001 提示失败不阻断
            msg = None
        self._warn.setText(msg or "")

    def refresh_context(self, source_dir="", registry=None,
                        target_table_id="") -> None:
        """目标表/数据表变更后刷新默认路径与期间提示（D1-B 联动）。"""
        if source_dir:
            self._source_dir = source_dir
        if registry is not None:
            self._registry = registry
        if target_table_id:
            self._target_table_id = target_table_id
        if self._path.text().strip() in ("", self._auto_path):
            self._auto_path = self._build_default_path()
            self._path.setText(self._auto_path)
        old_default = self._wd_default
        self._wd_default = self._union_workday_default()
        if self._spin.value() == (old_default if old_default else 1):
            self._spin.setValue(self._wd_default if self._wd_default else 1)
        self._rebuild_list()
        self._refresh_context_view()

    # ---- 参数收拢 ----
    def _browse(self) -> None:
        import os
        cur = self._path.text().strip()
        start = os.path.dirname(cur) if cur else ""
        if not start or not os.path.isdir(start):
            from paths import get_engine_root
            start = str(get_engine_root())
        path, _ = QFileDialog.getSaveFileName(
            self, "选择报告保存位置", start, "Excel 文件 (*.xlsx)")
        if path:
            self._path.setText(path)

    def get_params(self):
        wc = int(self._spin.value())
        return {
            "output_path": self._path.text().strip(),
            "workday_count": 0 if wc == self._wd_default else wc,
            "extra_table_ids": self._selected_ids(),
        }

    def validate_params(self, params):
        if not params.get("output_path"):
            return "请先选择报告要保存到哪里"
        return None


# ---------------------------------------------------------------------------
# 表单注册表（2026-09-20 M21：键集单一源 = gui.models.STEP_CATALOG）
# ---------------------------------------------------------------------------
```

> 说明：`get_params` 中 `workday_count=0` 表示"未改动默认值"（引擎回退口径）；`self._wd_default` 为 None 时任何值都原样传（口径提示为空）。

### 5.3 `_FORM_CLASSES` 增 1 项

【定位锚】（L608-613）：

```python
    "export": ExportForm,
```

【改为】：

```python
    "export": ExportForm,
    "supervision_report": SupervisionReportForm,
```

**批次 5 验证**：`python -m py_compile gui\forms.py`。

---

## 9. 批次 6：【修改】`rpa_engine/gui/page_operation_config.py`（2 处）

### 6.1 表单构造传 3 个新上下文参数

【定位锚】（L381-384）：

```python
        if form_cls is not None:
            self._inline_form = form_cls(
                step.params, table_ids=available,
                conn_columns=self._conn_columns(), parent=w)
```

【改为】：

```python
        if form_cls is not None:
            self._inline_form = form_cls(
                step.params, table_ids=available,
                conn_columns=self._conn_columns(), parent=w,
                source_dir=self._source_dir_for(step.target_table_id),
                registry=self._table_entries,
                target_table_id=step.target_table_id or "")
```

### 6.2 新增辅助方法 + 目标表变更联动

【定位锚】（L698-705）：

```python
    def _on_target_changed(self, step_index: int, combo_index: int) -> None:
        """目标表下拉变更 → 更新模型 + 状态机重算 + 刷新图（F4）。"""
        if 0 <= step_index < len(self.model.steps) and self._target_combo:
            tid = self._target_combo.itemData(combo_index)
            if tid:
                self.model.steps[step_index].target_table_id = tid
                self.model.reconcile()
                self._schedule_graph_refresh()
```

【改为】：

```python
    def _source_dir_for(self, table_id: str) -> str:
        """目标表源文件父目录（SupervisionReportForm 默认路径用）。"""
        from pathlib import Path
        for e in self._table_entries:
            if e.get("table_id") == table_id:
                p = str(e.get("source_path") or e.get("file_path") or "")
                return str(Path(p).parent) if p else ""
        return ""

    def _refresh_form_context(self, step_index: int) -> None:
        """目标表变更后刷新内联表单上下文（默认路径与期间提示联动，M7）。"""
        if (step_index == self._selected_step_index
                and self._inline_form is not None
                and hasattr(self._inline_form, "refresh_context")):
            step = self.model.steps[step_index]
            self._inline_form.refresh_context(
                source_dir=self._source_dir_for(step.target_table_id),
                registry=self._table_entries,
                target_table_id=step.target_table_id or "")

    def _on_target_changed(self, step_index: int, combo_index: int) -> None:
        """目标表下拉变更 → 更新模型 + 状态机重算 + 刷新图（F4）。"""
        if 0 <= step_index < len(self.model.steps) and self._target_combo:
            tid = self._target_combo.itemData(combo_index)
            if tid:
                self.model.steps[step_index].target_table_id = tid
                self.model.reconcile()
                self._schedule_graph_refresh()
                self._refresh_form_context(step_index)
```

**批次 6 验证**：`python -m py_compile gui\page_operation_config.py`。

---

## 10. 批次 7：【修改】`rpa_engine/gui/main_window.py`（1 处）

【定位锚】（L395-405）：

```python
                registry.append({
                    "table_id": table_id,
                    "alias": e["alias"],
                    "sqlite_table": sqlite_table,
                    "file_path": e["file_path"],
                    # R11/A-10：贯通原始文件路径（副本路径跨会话必变）
                    "source_path": e.get("source_path") or e["file_path"],
                    "sheet_name": e["sheet_name"],
                    "header_row": int(e["header_row"]),
                    "columns": columns,
                })
```

【改为】：

```python
                # R18：统计期间探测（supervision_report GUI 提示用，§3A.3）
                try:
                    from ops.supervision_report import probe_period
                    _probe = probe_period(conn, sqlite_table)
                except Exception as probe_err:  # noqa: BLE001
                    logger.debug(f"[main_window] 期间探测失败（忽略）: {probe_err}")
                    _probe = {}
                registry.append({
                    "table_id": table_id,
                    "alias": e["alias"],
                    "sqlite_table": sqlite_table,
                    "file_path": e["file_path"],
                    # R11/A-10：贯通原始文件路径（副本路径跨会话必变）
                    "source_path": e.get("source_path") or e["file_path"],
                    "sheet_name": e["sheet_name"],
                    "header_row": int(e["header_row"]),
                    "columns": columns,
                    "date_range": {"min": _probe.get("date_min"),
                                   "max": _probe.get("date_max")},
                    "workday_default": _probe.get("workday_default"),
                })
```

**批次 7 验证**：`python -m py_compile gui\main_window.py`。

---

## 11. 批次 8：【新增】`rpa_engine/tests/test_supervision_report.py`

创建文件，内容为下列全文（注意 `T-16` 读取被测源文件做静态检查；测试自身可含业务字面量）：

```python
"""
rpa_engine/tests/test_supervision_report.py

supervision_report 专属单测（plan.md §6.1，共 26 条）。
纯标准库 unittest + openpyxl；执行：

  cd rpa_engine
  python -m unittest tests.test_supervision_report -v
"""

import re
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from ops.supervision_report import (
    BLANK_LABEL, EMPTY_CELL, OUTPUT_NAME_PREFIX, OUTPUT_TIME_FMT,
    SHEET_DEPT, SHEET_PROF, SHEET_TODO, TOTAL_LABEL,
    ERR_DATE_COL, ERR_EMPTY_DATA, ERR_MISSING_COLUMN, ERR_OUTPUT_PATH,
    ERR_WORKDAY_RANGE, ERR_WRITE_FAIL,
    build_supervision_report, probe_period, workday_hint,
)

DDL_FULL = ("CREATE TABLE {t} (部门 TEXT, 检查人 TEXT, 检查时间 TEXT, "
            "专业名称 TEXT, 不合格项 INTEGER, 工单状态 TEXT)")


def _conn(ddl=DDL_FULL, table="t1"):
    conn = sqlite3.connect(":memory:")
    conn.execute(ddl.format(t=table))
    return conn


def _add(conn, rows, table="t1"):
    marks = ",".join(["?"] * len(rows[0]))
    conn.executemany(f"INSERT INTO {table} VALUES ({marks})", rows)
    conn.commit()


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig")


def _read_sheets(p: Path):
    import openpyxl
    wb = openpyxl.load_workbook(str(p))
    out = {}
    for name in wb.sheetnames:
        out[name] = [[c.value for c in row] for row in wb[name].iter_rows()]
    return wb.sheetnames, out


class SupervisionReportTest(unittest.TestCase):
    def _run(self, rows, table="t1", wc=0, extras=None, ddl=DDL_FULL):
        conn = _conn(ddl, table)
        _add(conn, rows, table)
        td = tempfile.mkdtemp()
        out = Path(td) / "out.xlsx"
        n = build_supervision_report(conn, table, str(out),
                                     workday_count=wc,
                                     extra_tables=extras or [])
        return out, out.with_suffix(".txt"), n

    # T-01 总表单数
    def test_t01_total(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")] * 3
        _, txt, n = self._run(rows)
        self.assertEqual(n, 2)
        self.assertIn("共填写履职表单3张", _read_text(txt))

    # T-02 不重复人数（表1 合计行）
    def test_t02_distinct_persons(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("B", "李四", "2026-09-01", "配网专业", 0, "已闭环")]
        xlsx, _, _ = self._run(rows)
        _, sheets = _read_sheets(xlsx)
        self.assertEqual(sheets[SHEET_DEPT][-1][0], TOTAL_LABEL)
        self.assertEqual(sheets[SHEET_DEPT][-1][1], 2)

    # T-03 自然日人均（2 位 HALF_UP：2.125 → 2.13；银行家舍入会错算 2.12）
    def test_t03_nat_avg_half_up(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")] * 32
        rows += [("A", "张三", "2026-09-16", "配网专业", 0, "已闭环")] * 2
        # 34 行 / 1 人 / 16 天 = 2.125
        _, txt, _ = self._run(rows)
        self.assertIn("自然日平均每人每日填写表单2.13张", _read_text(txt))

    # T-04 工作日人均（分子固定，分母=workday_count）
    def test_t04_workday_avg(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "李四", "2026-09-01", "配网专业", 0, "已闭环")]
        _, txt, _ = self._run(rows, wc=1)   # 2/2/1 = 1.00
        self.assertIn("工作日平均每人每日填写表单1.00张", _read_text(txt))

    # T-05 有问题表单边界（>0 才计）
    def test_t05_bad_boundaries(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", None, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", -1, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", 1, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", 3, "已闭环")]
        _, txt, _ = self._run(rows)
        self.assertIn("有发现问题表单2张", _read_text(txt))

    # T-06 已闭环＝交集口径
    def test_t06_closed_intersection(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 1, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", 1, "草稿")]
        _, txt, _ = self._run(rows)
        self.assertIn("已闭环1张", _read_text(txt))

    # T-07 草稿/整改中＝全表口径（非"问题表单剩余"）
    def test_t07_draft_fixing_full_table(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "草稿"),
                ("A", "张三", "2026-09-01", "配网专业", 0, "整改中"),
                ("A", "张三", "2026-09-01", "配网专业", 5, "草稿")]
        _, txt, _ = self._run(rows)
        self.assertIn("其余有2张草稿、1张整改中", _read_text(txt))

    # T-08 部门数动态（构造 3 个 → 表1 3 行 + 合计）
    def test_t08_dept_dynamic(self):
        rows = [("一部门", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("二部门", "李四", "2026-09-01", "配网专业", 0, "已闭环"),
                ("三部门", "王五", "2026-09-01", "配网专业", 0, "已闭环")]
        xlsx, _, _ = self._run(rows)
        _, sheets = _read_sheets(xlsx)
        self.assertEqual(len(sheets[SHEET_DEPT]), 1 + 3 + 1)

    # T-09 专业占比
    def test_t09_prof_pct(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")] * 3
        rows += [("A", "李四", "2026-09-01", "线路专业", 0, "已闭环")]
        xlsx, _, _ = self._run(rows)
        _, sheets = _read_sheets(xlsx)
        body = sheets[SHEET_PROF][1:-1]
        self.assertEqual([r[2] for r in body], ["75.0%", "25.0%"])
        self.assertEqual(sheets[SHEET_PROF][-1], [TOTAL_LABEL, 4, "100%"])

    # T-10 Excel 3 张 sheet（名称与顺序）
    def test_t10_three_sheets(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")]
        xlsx, _, _ = self._run(rows)
        names, _ = _read_sheets(xlsx)
        self.assertEqual(names, [SHEET_DEPT, SHEET_PROF, SHEET_TODO])

    # T-10b txt 单行 + BOM + 数值一致
    def test_t10b_txt(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")]
        _, txt, _ = self._run(rows)
        raw = txt.read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        text = _read_text(txt)
        self.assertNotIn("\n", text)
        self.assertIn("共填写履职表单1张", text)

    # T-10c 多表合并（UNION ALL：行数相加）
    def test_t10c_merge(self):
        conn = _conn()
        _add(conn, [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")] * 2)
        conn.execute(DDL_FULL.format(t="t2"))
        _add(conn, [("B", "李四", "2026-09-01", "配网专业", 0, "已闭环")] * 3,
             table="t2")
        td = tempfile.mkdtemp()
        out = Path(td) / "out.xlsx"
        build_supervision_report(conn, "t1", str(out), extra_tables=["t2"])
        self.assertIn("共填写履职表单5张", _read_text(out.with_suffix(".txt")))

    # T-10d output_path 为空
    def test_t10d_empty_output_path(self):
        conn = _conn()
        _add(conn, [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")])
        with self.assertRaises(ValueError) as cm:
            build_supervision_report(conn, "t1", "")
        self.assertIn(ERR_OUTPUT_PATH, str(cm.exception))

    # T-10e 默认文件名格式（命名常量）
    def test_t10e_name_format(self):
        name = (OUTPUT_NAME_PREFIX + "-"
                + datetime.now().strftime(OUTPUT_TIME_FMT) + ".xlsx")
        self.assertRegex(name, r"^履职表单报告统计-\d{12}\.xlsx$")

    # T-11 模板渲染无残留占位符
    def test_t11_no_placeholder_left(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 1, "已闭环")]
        _, txt, _ = self._run(rows)
        text = _read_text(txt)
        self.assertNotIn("{", text)
        self.assertNotIn("}", text)

    # T-12 期间识别与标签（单月 / 跨月）
    def test_t12_period(self):
        conn = _conn()
        _add(conn, [("A", "张三", "2026-09-10", "配网专业", 0, "已闭环"),
                    ("A", "张三", "2026-09-20", "配网专业", 0, "已闭环")])
        probe = probe_period(conn, "t1")
        self.assertTrue(probe["found"])
        self.assertEqual(probe["date_min"], "2026-09-10")
        self.assertEqual(probe["date_max"], "2026-09-20")
        self.assertEqual(probe["natural_days"], 11)
        self.assertEqual(probe["workday_default"], 7)
        td = tempfile.mkdtemp()
        out = Path(td) / "out.xlsx"
        build_supervision_report(conn, "t1", str(out))
        self.assertTrue(
            _read_text(out.with_suffix(".txt")).startswith("9月"))
        conn2 = _conn()
        _add(conn2, [("A", "张三", "2026-03-05", "配网专业", 0, "已闭环"),
                     ("A", "张三", "2026-07-01", "配网专业", 0, "已闭环")])
        td2 = tempfile.mkdtemp()
        out2 = Path(td2) / "out.xlsx"
        build_supervision_report(conn2, "t1", str(out2))
        self.assertTrue(
            _read_text(out2.with_suffix(".txt")).startswith("3月-7月"))

    # T-12b 脏日期：计入总数、不参与期间、txt 行尾提示
    def test_t12b_dirty_date(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "张三", "乱码", "配网专业", 0, "已闭环")]
        _, txt, _ = self._run(rows)
        text = _read_text(txt)
        self.assertIn("共填写履职表单2张", text)
        self.assertTrue(text.endswith("（另有 1 行日期无法识别）"))

    # T-12c 口径告警文案
    def test_t12c_workday_hint(self):
        self.assertIn("16", workday_hint(16, 22) or "")
        self.assertIn("22", workday_hint(16, 22) or "")
        self.assertIsNone(workday_hint(22, 22))
        self.assertIsNone(workday_hint(0, 22))
        self.assertIsNone(workday_hint(5, None))

    # T-13 缺列报中文可读错误
    def test_t13_missing_column(self):
        ddl = ("CREATE TABLE {t} (部门 TEXT, 检查人 TEXT, 检查时间 TEXT, "
               "专业名称 TEXT, 工单状态 TEXT)")
        conn = _conn(ddl)
        _add(conn, [("A", "张三", "2026-09-01", "配网专业", "已闭环")])
        with self.assertRaises(ValueError) as cm:
            build_supervision_report(conn, "t1", str(Path(tempfile.mkdtemp()) / "o.xlsx"))
        self.assertIn(ERR_MISSING_COLUMN.format(col="不合格项"), str(cm.exception))

    # T-14 空表 / 全脏日期
    def test_t14_empty_and_all_dirty(self):
        conn = _conn()
        with self.assertRaises(ValueError) as cm:
            build_supervision_report(conn, "t1", str(Path(tempfile.mkdtemp()) / "o.xlsx"))
        self.assertIn(ERR_EMPTY_DATA, str(cm.exception))
        conn2 = _conn()
        _add(conn2, [("A", "张三", "x", "配网专业", 0, "已闭环")])
        with self.assertRaises(ValueError) as cm2:
            build_supervision_report(conn2, "t1", str(Path(tempfile.mkdtemp()) / "o.xlsx"))
        self.assertIn(ERR_DATE_COL, str(cm2.exception))

    # T-15 输出不可写
    def test_t15_unwritable(self):
        conn = _conn()
        _add(conn, [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")])
        td = tempfile.mkdtemp()
        blocker = Path(td) / "blocker"
        blocker.write_text("x", encoding="utf-8")
        with self.assertRaises(ValueError) as cm:
            build_supervision_report(conn, "t1", str(blocker / "o.xlsx"))
        self.assertIn(ERR_WRITE_FAIL, str(cm.exception))

    # T-16 常量区唯一性（静态检查）
    def test_t16_constants_only(self):
        import ops.supervision_report as _sup_mod
        text = Path(_sup_mod.__file__).read_text(encoding="utf-8")
        first_def = text.index("\ndef ")
        tail = text[first_def:]
        literals = ["部门", "检查人", "检查时间", "专业名称", "不合格项",
                    "工单状态", "已闭环", "草稿", "整改中",
                    SHEET_DEPT, SHEET_PROF, SHEET_TODO, OUTPUT_NAME_PREFIX,
                    BLANK_LABEL, TOTAL_LABEL]
        for lit in literals:
            self.assertNotIn(lit, tail, f"业务字面量 {lit!r} 泄漏进函数体")

    # T-17 合计行人数＝全表去重（一人跨两部门 ≠ 相加）
    def test_t17_total_persons_distinct(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("B", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "李四", "2026-09-01", "配网专业", 0, "已闭环")]
        xlsx, _, _ = self._run(rows)
        _, sheets = _read_sheets(xlsx)
        self.assertEqual(sheets[SHEET_DEPT][-1][1], 2)

    # T-18 合计行人均＝全表重算（≠ 部门均值的平均）
    def test_t18_total_avg_full_recompute(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "张三", "2026-09-02", "配网专业", 0, "已闭环"),
                ("B", "李四", "2026-09-01", "配网专业", 0, "已闭环"),
                ("B", "王五", "2026-09-01", "配网专业", 0, "已闭环"),
                ("B", "赵六", "2026-09-02", "配网专业", 0, "已闭环")]
        xlsx, _, _ = self._run(rows)
        _, sheets = _read_sheets(xlsx)
        # A: 2/1/2=1.0；B: 3/3/2=0.5；部门均值平均=0.75→"0.8"（错误算法）
        # 合计：5 行/4 人/2 天=0.625→"0.6"（正确算法，两者不同即为本用例目的）
        self.assertEqual(sheets[SHEET_DEPT][-1][3], "0.6")

    # T-19 表3 全部门 + 编号自然序
    def test_t19_all_depts_and_order(self):
        rows = [("第一总监项目部", "张三", "2026-09-01", "配网专业", 0, "草稿"),
                ("第一总监项目部", "", "2026-09-01", "配网专业", 0, "草稿"),
                ("第三总监项目部", "李四", "2026-09-01", "配网专业", 0, "已闭环"),
                ("藏粤直流总监项目部", "王五", "2026-09-01", "配网专业", 0, "整改中")]
        xlsx, _, _ = self._run(rows)
        _, sheets = _read_sheets(xlsx)
        body = sheets[SHEET_TODO][1:]
        labels = [r[0] for r in body]
        self.assertIn("第三（0张）", labels)
        third = body[labels.index("第三（0张）")]
        self.assertEqual(third[1], EMPTY_CELL)
        self.assertEqual(third[2], EMPTY_CELL)
        # 空检查人的行计入 N 张（2＝张三 1 + 空 1），但不生成人员条目
        self.assertEqual(body[labels.index("第一（2张）")][1], "张三（1张）")
        self.assertLess(labels.index("第一（2张）"),
                        labels.index("藏粤直流（1张）"))

    # T-20 文件冲突：同批 -2 后缀，不覆盖原文件
    def test_t20_conflict_suffix(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")]
        conn = _conn()
        _add(conn, rows)
        td = tempfile.mkdtemp()
        out = Path(td) / "out.xlsx"
        out.write_text("old-xlsx", encoding="utf-8")
        out.with_suffix(".txt").write_text("old-txt", encoding="utf-8")
        build_supervision_report(conn, "t1", str(out))
        self.assertEqual(out.read_text(encoding="utf-8"), "old-xlsx")
        self.assertEqual(out.with_suffix(".txt").read_text(encoding="utf-8"),
                         "old-txt")
        self.assertTrue((Path(td) / "out-2.xlsx").exists())
        self.assertTrue((Path(td) / "out-2.txt").exists())


if __name__ == "__main__":
    unittest.main()
```

**批次 8 验证**：

```powershell
python -m unittest tests.test_supervision_report -v   # 26 tests ... OK
```

> 若 T-18 断言失败，先核对：合计行第 4 列（索引 3）是自然日人均的 1 位小数字符串；本例精确值 0.5。

---

## 12. 批次 9：文档同步（不影响指纹；改完跑 `doc_verify` 必须 PASS）

### 9.1 `docs/function-spec-rules.md`

【修改 a】标题：

- 锚：`### 3.2 文档版功能函数记录表（9 项，取值核对日期 2026-10-19）`
- 改为：`### 3.2 文档版功能函数记录表（10 项，取值核对日期 2026-11-02）`

【修改 b】记录表增行（锚＝ export 行 L113 全行）：

- 锚：

```markdown
| `export` | 结果导出 | 输出类 | 单表（终点，`STEP_KIND=end`） | 无新表（写 Excel 文件） | `output_path`,`sheet_name` ／ `output_path=""`,`sheet_name="数据"` | 否 | 否 | `ExportForm` |
```

- 改为：原行**原样保留**，其后新增一行：

```markdown
| `supervision_report` | 履职表单抽查报告 | 输出类 | 1～N 张同格式表（`extra_table_ids` 可选） | 无新表（写 xlsx 3 sheet ＋ txt） | `output_path`,`workday_count`,`extra_table_ids` ／ `output_path=""`,`workday_count=0`,`extra_table_ids=[]` | 否 | 否 | `SupervisionReportForm` |
```

【修改 c】§5.5 项 3：`现状 9 分支` → `现状 10 分支`。

【修改 d】frontmatter：`last-updated: 2026-10-24` → `last-updated: 2026-11-02`。

### 9.2 `docs/architecture.md`

【修改 a】§6 表增行（锚＝ export 行 L273 全行，原行保留、其后加）。

【定位锚】（L273）：

```markdown
| `export` | L2 业务 | 结果导出（SQLite → xlsx 流式直出，无模板；模板化输出**暂缓**，W-24 已裁定） | ❌ | output_path, sheet_name |
```

【改为】（原行保留，其后新增一行）：

```markdown
| `supervision_report` | L2 业务 | 履职表单抽查报告（3 张统计 sheet + 1 段总结 txt，写 2 文件） | ❌ | output_path, workday_count, extra_table_ids |
```

【修改 b】三处计数：`（D3 决策，9 项）` → `（D3 决策，10 项）`；`9 项；R15 字段集` → `10 项；R15 字段集`；`BUILTIN_OPS`（9 项）为**唯一** → `BUILTIN_OPS`（10 项）为**唯一**。

【修改 c】frontmatter：`last-updated: 2026-11-01` → `last-updated: 2026-11-02`。

### 9.3 `docs/INDEX.md`

- architecture.md 行（L22）：
  - 摘要锚（唯一）：`9 项用户操作清单（§6，2026-11-01 标注模板化输出暂缓）` → `10 项用户操作清单（§6，2026-11-02 增 supervision_report）`
  - 日期格锚（**行尾唯一片段**，避免行内重复歧义）：`| 架构、引擎、设计 | 2026-11-01 |` → `| 架构、引擎、设计 | 2026-11-02 |`
- function-spec-rules.md 行（L33）：
  - 摘要锚（唯一）：`记录表（9 项全字段）` → `记录表（10 项全字段）`
  - 日期格锚（行尾唯一片段）：`| 功能函数、三位一体、记录表、交互位置、变更顺序 | 2026-10-24 |` → `| 功能函数、三位一体、记录表、交互位置、变更顺序 | 2026-11-02 |`
- **规则**：INDEX 日期必须与对应文档 frontmatter `last-updated` 完全一致（`doc_verify` 强校验）。

### 9.4 根 `AGENTS.md`（4 处）

| 锚 | 改为 |
|---|---|
| `（BUILTIN_OPS 9 项 + L0-L3）` | `（BUILTIN_OPS 10 项 + L0-L3）` |
| `（9 项用户操作）承接` | `（10 项用户操作）承接` |
| `（BUILTIN_OPS 9 项）` | `（BUILTIN_OPS 10 项）` |
| `面向用户的 9 项操作（filter/dedup/…/convert_dtype）` | `面向用户的 10 项操作（filter/dedup/…/convert_dtype/supervision_report）` |

### 9.5 `v3/README.md`（L15 一处）

`9 项用户操作目录 \`BUILTIN_OPS\`（filter/dedup/mapping_match/aggregate/export/merge_tables/copy_table/rename_columns/convert_dtype，经` →
`10 项用户操作目录 \`BUILTIN_OPS\`（filter/dedup/mapping_match/aggregate/export/merge_tables/copy_table/rename_columns/convert_dtype/supervision_report，经`

### 9.6 `v3/rpa_engine/README.md`（L134 一处）

`BUILTIN_OPS 目录（9 项）` → `BUILTIN_OPS 目录（10 项）`

### 9.7 明确不动的文件

`v3/AGENTS.md`（§1 无「9 项」表述，无需改）、`docs/dev-spec.md`（§16 [37] 与本操作无涉）、`docs/INDEX.md` 其它行。

---

## 13. 批次 10：终检门禁（期望输出逐条对照）

```powershell
cd D:\cps-gpes_rpa-20250312\v3\rpa_engine
$env:QT_QPA_PLATFORM='offscreen'
python -m py_compile ops\supervision_report.py ops\step_executor.py gui\models.py gui\forms.py gui\page_operation_config.py gui\main_window.py
python -m unittest discover -s tests        # 期望：Ran 260 tests ... OK
python tools/smoke/smoke_m1m3.py            # 期望：SMOKE_ALL_OK
python tools/smoke/smoke_mb.py              # 期望：SMOKE_ALL_OK
python -c "import sys; sys.path.insert(0,'.'); from gui.app import run_self_check; r=run_self_check(); print(r.ok, len(r.items))"   # 期望：True 6
cd ..
python tools/doc_verify.py                  # 期望：PASS
python tools/make_fingerprint.py            # 期望：SOURCE_HASH 变化（≠ 9fc85bc09ac1376a），FILES=57
```

**逐条判定**：

| # | 检查 | 期望 |
|---|---|---|
| 1 | py_compile 6 文件 | 零输出（无 SyntaxError） |
| 2 | unittest discover | `Ran 260 tests` + `OK`（234 + 26） |
| 3 | smoke ×2 | `SMOKE_ALL_OK` |
| 4 | run_self_check | `True 6` |
| 5 | doc_verify | `PASS` |
| 6 | make_fingerprint | 新指纹 ≠ `9fc85bc09ac1376a`（exe 失效，**人工重建**） |
| 7 | `git status` | 仅列出本指令书 §1 产物表内的文件 + `_temp/` 无关变化；**不得**有其他源码改动 |

若任一不符：**停止**，逐条排查后重跑；禁止跳过。

---

## 附录 A：2026-09 样本验收期望（人工对照用）

对 `Test/zeng/履职表单20261017104155.xlsx` 的 sheet `0`（19,869 行）跑 `build_supervision_report`（`workday_count=22`）：

| 期望项 | 值 |
|---|---|
| 总表单数 | 19869 |
| 自然日人均（txt，2 位） | `2.17` |
| 工作日人均（txt，2 位，wc=22） | `2.52` |
| 有问题表单 | 3738（`18.81%`） |
| 已闭环 | 3710（`99.25%`） |
| 草稿 / 整改中 | 31 / 28 |
| 表1 行数 | 10 部门 + 合计 = 11 |
| 表1 合计人数 | 305 |
| 表1 合计自然日人均 | `2.2` |
| 表2 行数 | 8 专业 + 合计 = 9 |
| 表2 首行 | 配网专业 12090 `60.8%` |
| 表3 行数 | 10（含 `第四（0张）`、`藏粤直流（0张）`） |
| 表3 首行 | `第一（34张）` |
| txt 行数 | 1（末尾无换行） |
| 文件 | `<名>.xlsx` + `<名>.txt` 同目录同主名 |

## 附录 B：回归保护点（为什么现有 234 用例不会破）

| 现有断言 | 新增项影响 | 结论 |
|---|---|---|
| `test_registry_single_source` L135 `extra_input_min 应为 0` | 新操作取 **0**（勘误 C1） | ✅ 不破 |
| `test_param_keys_equals_schema_plus_gui_injected` | 新操作 `output=False` → `param_keys == schema_keys`（3 键一致） | ✅ 不破 |
| `test_overwritable_declared == {filter, dedup}` | 新操作 `overwritable=False` | ✅ 不破 |
| `test_deprecated_flag_present_and_false` | 新操作 `deprecated=False` | ✅ 不破 |
| `test_orders_unique` | 新操作 `order=10` 唯一 | ✅ 不破 |
| `test_step_catalog` `mains \| mores == active_catalog_keys()` | 按 category+order 派生，自动纳入 | ✅ 不破 |
| `test_dependency_contract` import 声明 | 新模块仅用 stdlib/requirements，且 spec 已登记 | ✅ 不破 |
| `STEP_COUNT` 自动派生 | 9→10 无需改断言 | ✅ 不破 |
