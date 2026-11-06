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
