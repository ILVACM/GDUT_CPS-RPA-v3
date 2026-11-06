"""
rpa_engine/ops/excel_normalizer.py

Layer 0 — Excel 数据表规范化预处理模块（需求 R1~R7 与 H1~H10 的集中实现）。

职责：把指定 sheet 规范化为"表头在第 1 行、所有单元格独立且内容为纯值"的标准
数据表，并产出元数据、处理报告与用户可见告警。本模块只处理**内存中的 DataFrame**，
不写回临时区文件（文件生命周期由 excel_preprocessor 管理）。

**职责边界**（plan.md Part 4）：
- 负责：单元格/表级规范化、元数据产出、处理报告产出。
- 不负责：Excel 读取（复用 `excel_preprocessor.read_excel_sheet`）、SQLite 建表与
  写入（交 `sqlite_manager`）、异常话术翻译（交 `gui/error_messages`）、重试与取消
  策略（交 `engine/executor`）。
- 本模块是 Layer 0 基础设施，**不**进 JSON `steps[]`、**不**出现在 DAG 节点，故
  **不登记** `BUILTIN_OPS`；但须在 `RPA_Workflow_v3.spec` 的 hiddenimports 登记。

**本批（P3）已实现的规则**：R3（合并格拆分）、R4（公式兜底）、R5（超链接展开）。
**本批（P4）已实现的规则**：H4 错误值、R7 清洗、A-08 空值策略、A-04 类型推断（含
REQ-H3 布尔→1/0、A-06 日期→ISO 8601）。管线顺序规范（plan.md L2330/L2365，不得颠倒）：
公式兜底(R4) → 错误值(H4) → 超链接(R5) → 清洗(R7) → 空值策略(A-08) → 类型推断(A-04)。
**本批（P5）已实现的规则**：H1（重复/空列名归一，插在读取后最先）、H5（全空列保留并
标记／尾部空行裁剪，插在类型推断之后）、H6（非单元格内容探测告知，插在全量开簿内）、
H7（超长数字精度提示，只提示不改数据，插在读取后）、H9（处理报告／元数据表／失败清单
落盘函数）、H10（temp/normalized/ 会话内幂等缓存）。

**内存说明**（16GB 目标机，红线 §2.1 条 5）：本模块**不**复制第二份全量 DataFrame
（所有改写一律 `iat` 就地写回；逐列规范化仅产出单列副本后立即写回）。合并区与超链接
元数据**无法在只读模式下读取**（openpyxl 的 `ReadOnlyWorksheet` 既无 `merged_cells`
也不填充 `cell.hyperlink`，见 R11/P3 第 0 步实测），故须全量开簿——以 `FULL_LOAD_MAX_ROWS`
作内存护栏，超限时跳过 R3/R5 并如实告警（不静默）。

依赖库：pandas>=2.0, openpyxl>=3.1, re（标准库）, datetime（标准库）
"""

import gc
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd
from loguru import logger

from ops.excel_preprocessor import read_excel_sheet, scan_sheets

NORMALIZE_RULES_VERSION = "v1"      # 规则版本；规则变更须递增（使 H10 缓存失效）
MERGED_SPLIT_LIMIT = 10_000         # 单表合并区上限（超过则只告警不拆分）
FULL_LOAD_MAX_ROWS = 100_000        # 全量开簿护栏：超此行数则跳过 R3/R5（见模块 docstring）

# 处理报告中"处理方式"的取值（供 REQ-H9 报告与后续批次复用）
WAY_SPLIT = "拆分合并格"
WAY_FORMULA_FALLBACK = "保留公式原文（缓存为空）"
WAY_HYPERLINK = "替换为链接地址"
WAY_NOT_DONE = "未处理"
WAY_ERROR_NULL = "错误值转空值"
WAY_CLEAN = "清洗文本"
WAY_DATETIME = "日期规范化"
WAY_BOOL = "布尔转 1/0"
WAY_INFER = "类型推断"
WAY_DEDUP = "重复列名去重"          # H1
WAY_TRIM = "裁剪尾部空行"            # H5
WAY_PRECISION = "超长数字提示"       # H7（仅提示，不改数据）
WAY_NONCELL = "非单元格内容告知"     # H6（仅告知，不导入）

# H10：会话内幂等缓存开关（降级时可置 False，H10 记为"仅目录管理已落地"）
NORMALIZE_CACHE_ENABLED = True

# H5／H1：pandas 对空表头格的填充名形态（如 "Unnamed: 1"）
_UNNAMED_COL_RE = re.compile(r"^Unnamed:\s*\d+$")
# H1：pandas 对重复列名自动追加的 ".N" 后缀
_DUP_SUFFIX_RE = re.compile(r"^(.*)\.(\d+)$")

# H4：Excel 错误值形态（整格完全匹配，避免误伤普通文本，如 "编号#N/A-01"）
ERROR_VALUE_PATTERN = r"^#(N/A|DIV/0!|VALUE!|REF!|NAME\?|NUM!|NULL!|GETTING_DATA)$"

_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^(-?\d*)\.(\d+)$")
_DATE_RE = re.compile(r"^-?\d{4}[-/]\d{1,2}[-/]\d{1,2}$")
_DATETIME_RE = re.compile(
    r"^-?\d{4}[-/]\d{1,2}[-/]\d{1,2}[ T]\d{1,2}:\d{2}(:\d{2})?$")
_BOOL_LITERALS = {"TRUE", "FALSE"}

# A-08：policy="pandas" 时沿用的 pandas 默认缺失值字面集合（懒惰取得）
_PANDAS_NA_CACHE: Optional[set] = None


def _pandas_na_values() -> set:
    """取得 pandas 默认缺失值字面集合（STR_NA_VALUES）。取不到时回落空集。"""
    global _PANDAS_NA_CACHE
    if _PANDAS_NA_CACHE is None:
        try:
            from pandas._libs.parsers import STR_NA_VALUES
            _PANDAS_NA_CACHE = set(STR_NA_VALUES)
        except Exception as e:  # noqa: BLE001 内部 API 变动时安全回落
            logger.warning(f"[excel_normalizer] 取 pandas 默认缺失值集合失败: {e}")
            _PANDAS_NA_CACHE = set()
    return _PANDAS_NA_CACHE


@dataclass
class NormalizeResult:
    """规范化结果（表的唯一输出载体）。"""
    dataframe: Any                    # pd.DataFrame：表头在第 1 行、单元格为纯值
    meta: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # 逐列元数据：col -> {original_type, was_formula, was_hyperlink,
    #                    was_merged, all_empty, normalized, cleaned}
    report_entries: List[Dict[str, Any]] = field(default_factory=list)
    # 处理报告条目：(sheet, 位置, 原始内容, 处理方式, 结果)
    warnings: List[str] = field(default_factory=list)
    # 用户可见告警（人话；禁技术词）


def _set_meta_flag(meta: Dict[str, Dict[str, Any]], col: Any, key: str) -> None:
    """在 meta 中把某列的某个标记位置为 True（逐列元数据的统一写入口）。"""
    entry = meta.setdefault(str(col), {})
    entry[key] = True


def _warn(out: List[str], text: str) -> None:
    """追加人话告警（去重，避免同一告警刷屏）。"""
    if text not in out:
        out.append(text)


def _ensure_object_col(df: pd.DataFrame, ci: int, value: Any) -> None:
    """确保第 ci 列能容纳待写入的 value。

    pandas 的 `iat` 赋值**不做 dtype 上溯**：把 str（如公式原文 / 链接地址）写入
    float64 列会抛错。此处仅在该列 dtype 不兼容时把**该列**转为 object
    （不复制整表，遵内存红线 §2.1 条 5）。数值写入数值列时不做无谓转换。
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return
    name = df.columns[ci]
    if df[name].dtype != object:
        df[name] = df[name].astype(object)


def split_merged_cells(ws: Any, df: pd.DataFrame,
                       header_rows: int = 1) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """R3：把所有合并单元格拆开，原内容复制到每一个被拆出的单元格。

    Args:
        ws: 已打开的 openpyxl **全量**工作表（只读模式不支持 merged_cells，
            见模块 docstring）。
        df: 已按表头行读入的 DataFrame（列名已上移）。
        header_rows: 表头占用的行数（默认 1）。

    Returns:
        (df, splits)：df 为**就地**填充后的同一对象；splits 逐条记
        {sheet, 首格, 行列数, 值, 方式}。超 MERGED_SPLIT_LIMIT 时不拆分，
        splits 内含一条 `方式="未处理"` 的记录（如实标注，不静默）。
    """
    splits: List[Dict[str, Any]] = []
    try:
        ranges = list(ws.merged_cells.ranges)
    except (AttributeError, TypeError) as e:  # 只读工作表无 merged_cells
        logger.warning(f"[excel_normalizer] 无法读取合并区（跳过 R3）: {e}")
        return df, splits

    if len(ranges) > MERGED_SPLIT_LIMIT:
        # 降级：只记录并在报告中告警，不做拆分（plan.md A-05 §6）
        splits.append({
            "sheet": ws.title,
            "位置": f"{len(ranges)} 处合并单元格",
            "原始内容": "",
            "处理方式": WAY_NOT_DONE,
            "结果": f"合并区数超过上限 {MERGED_SPLIT_LIMIT}，未拆分（避免超时）",
        })
        logger.warning(
            f"[excel_normalizer] 合并区数 {len(ranges)} 超过上限 "
            f"{MERGED_SPLIT_LIMIT}，未拆分")
        return df, splits

    n_rows, n_cols = df.shape
    for rng in ranges:
        try:
            value = ws.cell(row=rng.min_row, column=rng.min_col).value
            if value is None or (isinstance(value, str) and value.strip() == ""):
                continue
            filled = 0
            # rng 覆盖的单元格 → df 坐标：行＝min_row-1-header_rows，列＝min_col-1
            for r in range(rng.min_row, rng.max_row + 1):
                ri = r - 1 - header_rows
                if ri < 0 or ri >= n_rows:
                    continue
                for c in range(rng.min_col, rng.max_col + 1):
                    ci = c - 1
                    if ci < 0 or ci >= n_cols:
                        continue
                    if df.iat[ri, ci] is None or (
                            isinstance(df.iat[ri, ci], float) and pd.isna(df.iat[ri, ci])):
                        _ensure_object_col(df, ci, value)
                        df.iat[ri, ci] = value
                        filled += 1
            if filled:
                col_name = df.columns[rng.min_col - 1] if rng.min_col - 1 < n_cols else ""
                splits.append({
                    "sheet": ws.title,
                    "位置": f"{rng}",
                    "列名": col_name,
                    "原始内容": value,
                    "处理方式": WAY_SPLIT,
                    "结果": f"填充 {filled} 个单元格",
                })
        except Exception as e:  # noqa: BLE001 单区失败不影响整表（单元格级容错）
            logger.warning(f"[excel_normalizer] 合并区 {rng} 拆分失败（跳过）: {e}")
            continue
    return df, splits


def resolve_formula_cells(ws_tex: Any, ws_val: Any, df: pd.DataFrame,
                          offset_rows: int,
                          offset_cols: int = 0) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """R4（兜底路径）：对缓存值为空的单元格，读其公式原文并保留 + 告警。

    设计（人工裁定）：**不调用 Excel COM**（不引入 pywin32，遵"不引入新依赖"）。
    策略：优先用 openpyxl 缓存值；缓存为空且该格存在公式 → 写入公式原文并记入
    告警（**绝不静默填 NULL**）。

    Args:
        ws_tex: `data_only=False` 打开的工作表（读公式原文）。
        ws_val: `data_only=True` 打开的工作表（判缓存是否为空）。
        df: 已读入的 DataFrame（就地改写，不复制第二份全量表）。
        offset_rows: skiprows 偏移（＝ header_row - 1）。
        offset_cols: 列偏移（默认 0）。

    Returns:
        (df, formula_cells)：formula_cells 逐条记 (行, 列, 公式原文, "cached_empty")。
        无命中时**零开销**返回原 df（不建副本、不遍历整表）。
    """
    formula_cells: List[Dict[str, Any]] = []
    n_rows, n_cols = df.shape
    for ri in range(n_rows):
        for ci in range(n_cols):
            v = df.iat[ri, ci]
            is_blank = v is None or (isinstance(v, float) and pd.isna(v))
            if not is_blank:
                continue
            # 表头占据 offset_rows+1 行，故数据首行的 Excel 行号 = offset_rows+2
            xl_row = offset_rows + 2 + ri
            xl_col = offset_cols + 1 + ci
            try:
                cached = ws_val.cell(row=xl_row, column=xl_col).value
                if cached is not None:
                    continue          # 有缓存值（df 为空白属其它原因）→ 不改写
                formula = ws_tex.cell(row=xl_row, column=xl_col).value
            except Exception as e:  # noqa: BLE001 单格失败不影响整表
                logger.warning(
                    f"[excel_normalizer] 公式兜底失败（跳过）r{xl_row}c{xl_col}: {e}")
                continue
            if isinstance(formula, str) and formula.startswith("="):
                _ensure_object_col(df, ci, formula)
                df.iat[ri, ci] = formula           # 就地写回：保留公式原文
                formula_cells.append({
                    "行": ri + 1, "列": ci + 1,
                    "公式原文": formula, "原因": "cached_empty",
                    "单元格": f"{ws_tex.title}!{_coord(xl_row, xl_col)}",
                })
    return df, formula_cells


def expand_hyperlinks(ws: Any, df: pd.DataFrame,
                      offset_rows: int) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """R5：超链接单元格替换为链接地址文本（**不展开外部引用**）。

    Args:
        ws: `data_only=False` 打开的 openpyxl **全量**工作表（只读模式下
            `cell.hyperlink` 恒为 None，见模块 docstring）。
        df: 已读入的 DataFrame（就地改写）。
        offset_rows: skiprows 偏移（＝ header_row - 1）。

    Returns:
        (df, link_cells)：link_cells 逐条记 (行, 列, 显示文本, 目标地址)。
        未检测到任何超链接时**零开销**返回（先快速探测再遍历）。
    """
    link_cells: List[Dict[str, Any]] = []
    n_rows, n_cols = df.shape
    # 表头占据 offset_rows+1 行，故数据行的 Excel 行号区间 = [offset_rows+2, offset_rows+1+n_rows]
    first_row = offset_rows + 2
    last_row = offset_rows + 1 + n_rows
    try:
        # 快速探测：只要有一格带超链接才做逐格处理（省开销）
        has_link = False
        for r in range(first_row, last_row + 1):
            for c in range(1, n_cols + 1):
                if getattr(ws.cell(row=r, column=c), "hyperlink", None) is not None:
                    has_link = True
                    break
            if has_link:
                break
        if not has_link:
            return df, link_cells

        for r in range(first_row, last_row + 1):
            ri = r - first_row
            for c in range(1, n_cols + 1):
                cell = ws.cell(row=r, column=c)
                link = getattr(cell, "hyperlink", None)
                if link is None:
                    continue
                target = getattr(link, "target", None)
                if not target:
                    continue          # location 形式外链：只记 target，不展开
                ci = c - 1
                prev = df.iat[ri, ci]
                _ensure_object_col(df, ci, target)
                df.iat[ri, ci] = target
                link_cells.append({
                    "行": ri + 1, "列": ci + 1,
                    "显示文本": prev, "目标地址": target,
                })
    except Exception as e:  # noqa: BLE001 单元格级容错：不因单格失败放弃整表
        logger.warning(f"[excel_normalizer] 超链接展开中断（已处理部分保留）: {e}")
    return df, link_cells


def _coord(row: int, col: int) -> str:
    """把 (行, 列) 转成 Excel 风格坐标，如 (2, 1) -> 'A2'。"""
    letters = ""
    c = col
    while c > 0:
        c, rem = divmod(c - 1, 26)
        letters = chr(65 + rem) + letters
    return f"{letters}{row}"


# ---------------------------------------------------------------------------
# P4 管线：H4 错误值 → R7 清洗 → A-08 空值策略 → A-06/H3/A-04 类型规范化
# （顺序不得颠倒，见模块 docstring；均就地/逐列改写，不复制整表）
# ---------------------------------------------------------------------------

def _is_blank(v: Any) -> bool:
    """判定"真空"：None 或全空白字符串（不含字面 NA 语义）。"""
    if v is None:
        return True
    if isinstance(v, float) and pd.isna(v):
        return True
    return isinstance(v, str) and v.strip() == ""


def normalize_error_cells(
    df: pd.DataFrame, meta: Dict[str, Dict[str, Any]],
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """H4：Excel 错误值（#N/A／#DIV/0!／#VALUE!／#REF! 等）统一转 NULL ＋ 原文留痕。

    以**整格完全匹配**（fullmatch）判定，避免误伤 "编号#N/A-01" 之类普通文本。
    单格失败绝不影响整表（单元格级容错）。**须在 A-08 的字面 NA 保留策略之前**
    执行，否则 "#N/A" 会被"保留"策略放过（依赖管线顺序，不靠改策略）。

    Returns:
        (df, error_cells)：df 就地改写；error_cells 逐条记 (行, 列, 原文)。
    """
    error_cells: List[Dict[str, Any]] = []
    n_rows, n_cols = df.shape
    for ri in range(n_rows):
        for ci in range(n_cols):
            v = df.iat[ri, ci]
            if isinstance(v, str) and re.fullmatch(ERROR_VALUE_PATTERN, v):
                df.iat[ri, ci] = None
                _set_meta_flag(meta, df.columns[ci], "was_error")
                error_cells.append({"行": ri + 1, "列": ci + 1,
                                    "列名": df.columns[ci], "原文": v})
    return df, error_cells


def collect_workbook_errors(
    ws: Any, offset_rows: int, n_rows: int, n_cols: int,
) -> List[Dict[str, Any]]:
    """H4（补充）：从**全量工作表**收集错误值单元格原文。

    背景（R11/P4 实测）：openpyxl 把错误值存为 data_type='e'（值形如
    "#DIV/0!"），而 pandas.read_excel 会把错误单元格一并读成 NaN——故 DataFrame
    里已无原文可留痕。本函数直接从工作表读回错误原文（df 中该格已是 NULL，
    无需再改写），仅用于"原文留痕"，满足 REQ-H4 的元数据要求。

    Returns:
        逐条 {"行"(df 行号, 1 起始), "列"(1 起始), "原文"}；无错误值时零开销返回空表。
    """
    errs: List[Dict[str, Any]] = []
    first = offset_rows + 2      # 表头占 offset_rows+1 行
    for ri in range(n_rows):
        r = first + ri
        for ci in range(n_cols):
            try:
                v = ws.cell(row=r, column=ci + 1).value
            except Exception as e:  # noqa: BLE001 单格失败不影响整表
                logger.debug(f"[excel_normalizer] 错误值扫描失败（跳过）: {e}")
                continue
            if isinstance(v, str) and re.fullmatch(ERROR_VALUE_PATTERN, v):
                errs.append({"行": ri + 1, "列": ci + 1, "原文": v})
    return errs


def _clean_one(s: str) -> str:
    """R7 单格清洗：去除控制字符（\\x00／\\x0b／\\x0c）后 strip（含全角空格）。"""
    if "\x00" in s or "\x0b" in s or "\x0c" in s:
        s = s.replace("\x00", "").replace("\x0b", "").replace("\x0c", "")
    return s.strip()


def clean_cell_text(
    series: "pd.Series", meta: Dict[str, Dict[str, Any]], col: Any,
) -> "pd.Series":
    """R7：逐单元格去除首尾空格与 null 字符（仅对文本列生效）。

    仅对 str 单元格生效（数值/日期格不动）；清洗后为空的单元格**不在此转 NULL**，
    交 A-08 的空值策略统一处理（避免双口径）。meta[col]["cleaned"]=True 表示有变更。

    Returns:
        清洗后的 Series（dtype=object，就地值级复制单列）。
    """
    if not _is_text_col(series):
        return series
    changed = 0
    out: List[Any] = []
    for v in series:
        if isinstance(v, str):
            nv = _clean_one(v)
            if nv != v:
                changed += 1
            out.append(nv)
        else:
            out.append(v)
    if changed:
        meta.setdefault(str(col), {})["cleaned"] = True
    return pd.Series(out, dtype=object, index=series.index)


def apply_na_policy(
    df: pd.DataFrame, policy: str = "preserve",
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """A-08／R7：按策略决定"哪些字面文本算空值"。

    policy="preserve"（默认，裁定 G11）：仅真空／全空白算 NULL，字面
        NA／N/A／None／null／nan／#N/A 等**原样保留**；
    policy="pandas"：沿用 pandas 默认 STR_NA_VALUES（即改动前现状）。

    Returns:
        (df, nulled_cells)：df 就地改写（命中格置 None）；nulled_cells 记
        (行, 列, 原值) 供 REQ-H9 报告。
    """
    mode = (policy or "preserve").strip().lower()
    pandas_na = _pandas_na_values() if mode == "pandas" else set()
    nulled: List[Dict[str, Any]] = []
    n_rows, n_cols = df.shape
    for ri in range(n_rows):
        for ci in range(n_cols):
            v = df.iat[ri, ci]
            if _is_blank(v):
                if v is not None and not (isinstance(v, float) and pd.isna(v)):
                    df.iat[ri, ci] = None        # 空白字符串 → NULL（preserve 口径）
                continue
            if mode == "pandas" and isinstance(v, str) and v in pandas_na:
                df.iat[ri, ci] = None
                nulled.append({"行": ri + 1, "列": ci + 1,
                               "列名": df.columns[ci], "原值": v})
    return df, nulled


def _to_timestamp(v: Any) -> Optional["pd.Timestamp"]:
    """把日期对象或"日期形态"字符串尝试解析为 Timestamp；失败返回 None。

    仅接受 datetime/date 对象或严格日期形态字符串（YYYY-MM-DD／带时刻），
    以免把订单号等普通数字文本误判为日期（如 "12345"／"2026-001"）。
    """
    if isinstance(v, (datetime, date)):
        return pd.Timestamp(v)
    if isinstance(v, pd.Timestamp):
        return v
    if isinstance(v, str):
        s = v.strip()
        if _DATE_RE.match(s) or _DATETIME_RE.match(s):
            try:
                return pd.Timestamp(pd.to_datetime(s, errors="raise"))
            except (ValueError, TypeError):
                return None
    return None


def is_datetime_column(series: "pd.Series") -> bool:
    """判定列是否为日期列：datetime64，或含 ≥1 个日期值且非空白值均可解析。"""
    try:
        if pd.api.types.is_datetime64_any_dtype(series):
            return True
    except (TypeError, AttributeError):
        pass
    seen_date = False
    for v in series:
        if _is_blank(v):
            continue
        if isinstance(v, (datetime, date, pd.Timestamp)):
            seen_date = True
            continue
        if isinstance(v, str) and (_DATE_RE.match(v.strip())
                                   or _DATETIME_RE.match(v.strip())):
            seen_date = True
            continue
        return False        # 混有非日期文本 → 不是日期列
    return seen_date


def normalize_datetime_column(
    series: "pd.Series", meta: Dict[str, Dict[str, Any]], col: Any,
) -> "pd.Series":
    """A-06：日期/时间统一转为 ISO 8601 字符串（TEXT），并标记原始类型。

    "无时间部分时用 %Y-%m-%d"（整列所有日期均为 0 时刻时省略 00:00:00，
    使 `2026-02-20` 可被等值命中，见 A-07）；解析失败的格**原样保留**
    （不得抛错、不得静默填 NULL）。meta[col] 记 original_type="datetime"、
    normalized="iso8601"。
    """
    parsed = [_to_timestamp(v) for v in series]
    has_time = any(ts is not None and (ts.hour or ts.minute or ts.second)
                   for ts in parsed)
    if not any(ts is not None for ts in parsed):
        return series
    fmt = "%Y-%m-%d %H:%M:%S" if has_time else "%Y-%m-%d"
    out = [
        ts.strftime(fmt) if ts is not None else v
        for v, ts in zip(series, parsed)
    ]
    entry = meta.setdefault(str(col), {})
    entry.setdefault("original_type", "datetime")
    entry["normalized"] = "iso8601"
    return pd.Series(out, dtype=object, index=series.index)


def is_bool_column(series: "pd.Series") -> bool:
    """判定列是否"整列皆为布尔形态"（bool 对象或 TRUE/FALSE 文本）。

    REQ-H3 §6：须限定整列皆布尔形态才转，避免把恰好写着 TRUE 的普通文本列误转。
    """
    seen = False
    for v in series:
        if _is_blank(v):
            continue
        if isinstance(v, bool):
            seen = True
        elif isinstance(v, str) and v.strip().upper() in _BOOL_LITERALS:
            seen = True
        else:
            return False
    return seen


def _bool_to_int(v: Any) -> Optional[int]:
    """布尔值（bool 对象或 TRUE/FALSE 文本）→ 1/0；空白 → None。"""
    if _is_blank(v):
        return None
    if isinstance(v, bool):
        return 1 if v else 0
    return 1 if str(v).strip().upper() == "TRUE" else 0


def infer_cell_type(raw: Any, max_significant_digits: int = 5) -> Tuple[Any, str]:
    """A-04／R6：按阈值判定单元格目标类型。

    规则（逐条实现，见 plan.md A-04 §3）：
        ① 空值 → (None, "NULL")；
        ② 整数 `^-?\\d+$`：前导零编码（以 0 开头且长度 > 1）→ str；
           否则去负号后位数 ≤ 阈值 → int，超阈值 → str；
        ③ 浮点 `^-?\\d*\\.\\d+$`：整数部分位数 ≤ 阈值 → float，否则 → str；
        ④ 其余 → str（超长数字、身份证、订单号一律 str）。
    bool 对象在此处先行识别（bool 是 int 子类，若走整数分支会丢标记）。
    阈值走可配置项（默认 5，JSON global 可覆盖），不硬编码在业务分支。

    Returns:
        (value, target_type)  target_type ∈ {"NULL","int","float","str"}。
    """
    if _is_blank(raw):
        return None, "NULL"
    if isinstance(raw, bool):          # bool 是 int 子类，须先判
        return (1 if raw else 0), "int"
    if isinstance(raw, str):
        s = raw.strip()
        if _INT_RE.match(s):
            body = s[1:] if s.startswith("-") else s
            if len(body) > 1 and body.startswith("0"):
                return s, "str"        # 前导零编码，保留为文本
            if len(body) <= max_significant_digits:
                return int(s), "int"
            return s, "str"
        m = _FLOAT_RE.match(s)
        if m:
            int_part = m.group(1).lstrip("-")
            if len(int_part) <= max_significant_digits:
                return float(s), "float"
            return s, "str"
        return s, "str"
    return raw, "str"


def _is_text_col(series: "pd.Series") -> bool:
    """列是否为文本列（object 或 pandas 字符串扩展类型）。"""
    try:
        return (series.dtype == object
                or pd.api.types.is_string_dtype(series.dtype))
    except (TypeError, AttributeError):
        return False


def normalize_column_types(
    df: pd.DataFrame, meta: Dict[str, Dict[str, Any]],
    max_significant_digits: int = 5,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """A-06／REQ-H3／A-04：逐列类型规范化（日期→ISO／布尔→1/0／数字→int/float）。

    仅处理尚未被上游标记（iso8601／bool01）的列；逐列产出单列副本后立即写回，
    不复制整表。写回 dtype=object，使 `to_sql` 按值选择 SQLite 列类型
    （int 值 → INTEGER、float 值 → REAL、str 值 → TEXT）。

    Returns:
        (df, type_reports)：type_reports 逐列记 {列名, 方式, 结果}。
    """
    reports: List[Dict[str, Any]] = []
    for ci in range(df.shape[1]):
        col = df.columns[ci]
        series = df.iloc[:, ci]
        key = str(col)
        marker = meta.get(key, {}).get("normalized")
        if marker in ("iso8601", "bool01"):
            continue
        if is_datetime_column(series):
            new_series = normalize_datetime_column(series, meta, col)
            df[df.columns[ci]] = new_series
            reports.append({"列名": key, "方式": WAY_DATETIME,
                            "结果": "统一为 ISO 8601 文本"})
            continue
        if is_bool_column(series):
            vals = [_bool_to_int(v) for v in series]
            df[df.columns[ci]] = pd.Series(vals, dtype=object, index=df.index)
            entry = meta.setdefault(key, {})
            entry.setdefault("original_type", "bool")
            entry["normalized"] = "bool01"
            reports.append({"列名": key, "方式": WAY_BOOL, "结果": "1/0（整数）"})
            continue
        if _is_text_col(series):
            vals = [infer_cell_type(v, max_significant_digits)[0] for v in series]
            df[df.columns[ci]] = pd.Series(vals, dtype=object, index=df.index)
    return df, reports


# ---------------------------------------------------------------------------
# P5 管线：H1 列名规范化 · H7 超长数字提示 · H6 非单元格内容 · H5 空列/尾部空行
# ---------------------------------------------------------------------------

_COMMENT_SCAN_CELL_CAP = 200_000     # H6：批注扫描的单元格数上限（超过则跳过，避免超时）


def _is_unnamed_col(name: Any) -> bool:
    """列名是否属"空列名"（全空白，或 pandas 对空表头格的填充名 "Unnamed: N"）。"""
    s = str(name)
    return s.strip() == "" or bool(_UNNAMED_COL_RE.match(s))


def dedup_columns(columns: List[Any]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """H1：重复列名按 `原名`／`原名_2`／`原名_3` 归一（确定性命名）。

    输入为 pandas 读入后的列名列表——pandas 对重复表头已自动追加 ".1"／".2"
    后缀（R11/P5 实测），此处把该后缀还原为需求措辞的 `_2`／`_3` 形式；空表头格
    （pandas 填充为 "Unnamed: N" 或全空白文本）归一为 `未命名列_N`。仅当某原始名
    出现 ≥2 次时才归一，避免误伤"本就叫 X.1"的唯一列。

    Args:
        columns: 当前列名列表（任意类型，内部转 str）。

    Returns:
        (new_columns, renamed)：new_columns 为规范化后的列名（保序、等长）；
        renamed 逐条记 {"原始列名","新列名","出现次数"}，仅含发生变更的项。
    """
    cols = [str(c) for c in columns]

    def _base(name: str) -> str:
        m = _DUP_SUFFIX_RE.match(name)
        return m.group(1) if m else name

    base_counts: Dict[str, int] = {}
    for c in cols:
        if _is_unnamed_col(c):
            continue
        b = _base(c)
        base_counts[b] = base_counts.get(b, 0) + 1

    new_cols: List[str] = []
    renamed: List[Dict[str, Any]] = []
    occ: Dict[str, int] = {}
    unnamed_n = 0
    for raw in cols:
        if _is_unnamed_col(raw):
            unnamed_n += 1
            nn = f"未命名列_{unnamed_n}"
            new_cols.append(nn)
            renamed.append({"原始列名": raw, "新列名": nn, "出现次数": unnamed_n})
            continue
        b = _base(raw)
        if base_counts.get(b, 0) <= 1:
            new_cols.append(raw)          # 无重复，保留原名（含可能的 X.1）
            continue
        occ[b] = occ.get(b, 0) + 1
        nn = b if occ[b] == 1 else f"{b}_{occ[b]}"
        new_cols.append(nn)
        if nn != raw:
            renamed.append({"原始列名": raw, "新列名": nn, "出现次数": occ[b]})
    return new_cols, renamed


def detect_precision_loss(
    df: "pd.DataFrame", meta: Dict[str, Dict[str, Any]],
    threshold_digits: int = 15,
) -> List[Dict[str, Any]]:
    """H7：扫描阶段检测超长数字列并提示（源文件精度已丢失，**不可修复**）。

    **只提示，绝不改写数据**（源文件已损失精度，任何"补零/还原"都是编造）。
    判定口径：数字型值或纯数字文本的**整数部分位数 > threshold_digits**
    （默认 15，Excel 自身有效数字上限）。

    Args:
        df: 待检测 DataFrame（只读，不修改）。
        meta: 逐列元数据（保留参数位，便于将来扩展）。
        threshold_digits: 有效数字阈值（默认 15）。

    Returns:
        List[Dict[str, Any]]：逐列记 {"列名","样本值","位数"}；无命中时返回空表。
    """
    reports: List[Dict[str, Any]] = []
    for ci in range(df.shape[1]):
        col = str(df.columns[ci])
        sample: Optional[str] = None
        digits = 0
        for v in df.iloc[:, ci]:
            if v is None or (isinstance(v, float) and pd.isna(v)):
                continue
            if isinstance(v, bool):
                continue
            if isinstance(v, int):
                s = str(abs(v))
            elif isinstance(v, float):
                s = str(int(abs(v))) if v.is_integer() else ""
            elif isinstance(v, str):
                s = v.strip()
                if s.startswith("-"):
                    s = s[1:]
                s = s.split(".")[0]
                if not s.isdigit():
                    continue
            else:
                continue
            if len(s) > threshold_digits:
                sample = str(v)
                digits = len(s)
                break
        if sample is not None:
            reports.append({"列名": col, "样本值": sample, "位数": digits})
    return reports


def detect_non_cell_content(ws: Any) -> Dict[str, int]:
    """H6：探测非单元格内容（图片/图表/批注）数量，仅用于告知，不予导入。

    须在**全量开簿**的工作表上调用（只读模式下 `_images`／`_charts`／批注均不可
    用，R11/P5 实测）。任何属性不可用一律安全回落到 0（绝不中断导入）。

    Args:
        ws: openpyxl 工作表（`read_only=False`）。

    Returns:
        Dict[str, int]：{"images": n, "charts": n, "comments": n}。
    """
    result = {"images": 0, "charts": 0, "comments": 0}
    try:
        result["images"] = len(getattr(ws, "_images", None) or [])
    except Exception as e:  # noqa: BLE001 探测失败降级为 0
        logger.debug(f"[excel_normalizer] 图片探测失败（忽略）: {e}")
    try:
        result["charts"] = len(getattr(ws, "_charts", None) or [])
    except Exception as e:  # noqa: BLE001
        logger.debug(f"[excel_normalizer] 图表探测失败（忽略）: {e}")
    try:
        comments = getattr(ws, "_comments", None)
        if comments:
            result["comments"] = len(comments)
        else:
            # openpyxl 3.1 的 ws._comments 恒为空表（实测），批注挂在单元格上，
            # 故对较小表遍历单元格计数（超过上限则跳过，避免超时）
            rows = getattr(ws, "max_row", 0) or 0
            cols = getattr(ws, "max_column", 0) or 0
            if rows * cols <= _COMMENT_SCAN_CELL_CAP:
                n = 0
                for row in ws.iter_rows():
                    for c in row:
                        if getattr(c, "comment", None) is not None:
                            n += 1
                result["comments"] = n
    except Exception as e:  # noqa: BLE001
        logger.debug(f"[excel_normalizer] 批注探测失败（忽略）: {e}")
    return result


def handle_empty_cols_rows(
    df: "pd.DataFrame", meta: Dict[str, Dict[str, Any]],
) -> Tuple["pd.DataFrame", List[str], int]:
    """H5：全空列保留但标记；**尾部**连续全空行裁剪（中间空行保留为数据行）。

    Args:
        df: 待处理 DataFrame（就地标记列元数据；行裁剪仅改变视图范围）。
        meta: 逐列元数据（全空列置 all_empty=True）。

    Returns:
        (df_out, empty_cols, trimmed_rows)：df_out 为裁剪尾部空行后的表；
        empty_cols 为全空列名列表；trimmed_rows 为被裁剪的尾部空行数。
    """
    empty_cols: List[str] = []
    for ci in range(df.shape[1]):
        col = df.columns[ci]
        series = df.iloc[:, ci]
        if len(series) and all(_is_blank(v) for v in series):
            empty_cols.append(str(col))
            _set_meta_flag(meta, col, "all_empty")

    n_rows = df.shape[0]
    last = n_rows
    while last > 0:
        row = df.iloc[last - 1]
        if all(_is_blank(v) for v in row):
            last -= 1
        else:
            break
    trimmed_rows = n_rows - last
    if trimmed_rows:
        df = df.iloc[:last]             # 视图裁剪：不复制整表（内存红线 §2.1 条 5）
    return df, empty_cols, trimmed_rows


# ---------------------------------------------------------------------------
# H9 落盘：规范化处理报告（JSON＋人读）· 元数据表 · 失败清单
# ---------------------------------------------------------------------------

def _b(v: Any) -> int:
    """布尔 → 1/0（供元数据表 INTEGER 列）。"""
    return 1 if v else 0


def write_normalize_report(
    result: "NormalizeResult", out_dir: str, table_id: str, alias: str,
) -> Dict[str, str]:
    """H9／产物 3：把规范化过程写入可读报告（JSON ＋ 人读文本）。

    报告**禁用技术词**（SQL／表名／SQLite／物理名 → 用"数据表编号/标识名称"
    表述，遵 docs/architecture.md §8.4）。

    Args:
        result: 规范化结果。
        out_dir: 报告目录（如 workspace/normalize_report/<会话时间戳>/）。
        table_id: 数据表编号（如 "T1"）。
        alias: 标识名称（用户面名称）。

    Returns:
        Dict[str, str]：{"json": 路径, "text": 路径}。
    """
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    entries = list(result.report_entries)
    payload = {
        "数据表编号": table_id,
        "标识名称": alias,
        "规则版本": NORMALIZE_RULES_VERSION,
        "需留意": list(result.warnings),
        "处理明细": entries,
    }
    jp = d / f"{table_id}_normalize.json"
    jp.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                  encoding="utf-8")

    lines = [f"数据表编号：{table_id}", f"标识名称：{alias}", ""]
    if result.warnings:
        lines.append("【需留意】")
        lines += [f"  - {w}" for w in result.warnings]
        lines.append("")
    lines.append("【处理明细】")
    for e in entries:
        pos = e.get("位置", "")
        way = e.get("处理方式", "")
        res = e.get("结果", "")
        orig = e.get("原始内容", "")
        line = f"  - {pos}｜{way}｜{res}"
        if orig not in ("", None):
            line += f"（原文：{orig}）"
        lines.append(line)
    tp = d / f"{table_id}_normalize.txt"
    tp.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(jp), "text": str(tp)}


def write_meta_table(
    conn: Any, result: "NormalizeResult", sqlite_table: str, table_id: str,
) -> int:
    """H9／产物 2：把逐列原始 Excel 类型/公式/超链接/合并/空列标记写入元数据表。

    在同一会话库内建统一表 `__normalize_meta`（前缀 `__` 明示非业务表，仅供
    追溯）。**不创建连接**（用调用方传入的 conn，遵 AGENTS.md §2.2 条 4）。

    Args:
        conn: 共享 SQLite 连接。
        result: 规范化结果。
        sqlite_table: 目标物理表名（仅供追溯登记，不对用户展示）。
        table_id: 数据表编号。

    Returns:
        int: 写入行数（＝被导入表列数）。
    """
    conn.execute(
        "CREATE TABLE IF NOT EXISTS __normalize_meta ("
        "table_id TEXT, sqlite_table TEXT, column TEXT, "
        "original_type TEXT, was_formula INTEGER, was_hyperlink INTEGER, "
        "was_merged INTEGER, all_empty INTEGER, was_error INTEGER, "
        "normalized TEXT, cleaned INTEGER)"
    )
    rows = 0
    for col in result.dataframe.columns:
        m = result.meta.get(str(col), {})
        conn.execute(
            "INSERT INTO __normalize_meta VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (table_id, sqlite_table, str(col),
             m.get("original_type"),
             _b(m.get("was_formula")), _b(m.get("was_hyperlink")),
             _b(m.get("was_merged")), _b(m.get("all_empty")),
             _b(m.get("was_error")), m.get("normalized"),
             _b(m.get("cleaned"))),
        )
        rows += 1
    conn.commit()
    return rows


def write_failed_list(failed: List[Dict[str, str]], out_dir: str) -> str:
    """H9／产物 4：把未入库的数据表与原因写成失败清单。

    Args:
        failed: 逐条 {"alias","sheet","file","reason","stage"}。
        out_dir: 报告目录。

    Returns:
        str: 清单文件路径（JSON）。
    """
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    items = [{
        "标识名称": it.get("alias", ""),
        "工作表": it.get("sheet", ""),
        "文件": it.get("file", ""),
        "环节": it.get("stage", ""),
        "原因": it.get("reason", ""),
    } for it in failed]
    jp = d / "failed_list.json"
    jp.write_text(json.dumps(items, ensure_ascii=False, indent=2),
                  encoding="utf-8")
    lines = ["未能导入的数据表清单", ""]
    for it in items:
        lines.append(f"- {it['标识名称']}（工作表：{it['工作表']}）")
        lines.append(f"    原因：{it['原因']}")
    tp = d / "failed_list.txt"
    tp.write_text("\n".join(lines), encoding="utf-8")
    return str(jp)


# ---------------------------------------------------------------------------
# H10 幂等缓存：键（文件指纹＋sheet＋表头行＋规则版本）· 读 · 写
# ---------------------------------------------------------------------------

def normalized_cache_key(
    file_path: str, sheet_name: str, header_row: int, rules_version: str,
) -> str:
    """H10：规范化产物的幂等键（文件指纹 + sheet + 表头行 + 规则版本）。

    指纹含 路径 + 大小 + mtime，故文件内容变更或规则升级后缓存自动失效。
    """
    p = Path(file_path)
    try:
        st = p.stat()
        fingerprint = f"{p.resolve()}|{st.st_size}|{int(st.st_mtime)}"
    except OSError:
        fingerprint = f"{p}|0|0"
    raw = f"{fingerprint}|{sheet_name}|{int(header_row)}|{rules_version}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def load_normalized_cache(key: str) -> Optional[Dict[str, Any]]:
    """H10：命中缓存则返回其内容；未命中/不可读返回 None。

    缓存仅记录"该键已处理过"及其元数据（**不落盘 DataFrame**，因不引入
    pyarrow／pickle 新依赖；数据本身仍每次重新读取）。
    """
    try:
        from paths import get_normalized_dir
        p = get_normalized_dir() / f"{key}.json"
        if not p.is_file():
            return None
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        logger.debug(f"[excel_normalizer] 读取规范化缓存失败（忽略）: {e}")
        return None


def _save_normalized_cache(
    key: str, result: "NormalizeResult", stage_a_transforms: bool,
) -> None:
    """H10：写出缓存（失败一律忽略，绝不中断规范化）。"""
    try:
        from paths import get_normalized_dir
        p = get_normalized_dir() / f"{key}.json"
        payload = {
            "key": key,
            "rules_version": NORMALIZE_RULES_VERSION,
            "stage_a_transforms": bool(stage_a_transforms),
            "rows": int(result.dataframe.shape[0]),
            "cols": int(result.dataframe.shape[1]),
            "meta": result.meta,
            "warnings": result.warnings,
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        }
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except (OSError, TypeError, ValueError) as e:
        logger.debug(f"[excel_normalizer] 写入规范化缓存失败（忽略）: {e}")


def normalize_sheet(
    file_path: str,
    sheet_name: str,
    header_row: int,
    *,
    sheet_info: Optional[List[Dict[str, Any]]] = None,
    max_significant_digits: int = 5,
    na_policy: str = "preserve",
    enable_cache: bool = True,
    progress: Optional[Callable[[str], None]] = None,
) -> NormalizeResult:
    """把指定 sheet 规范化为标准数据表。

    Args:
        file_path: 临时区 xlsx 路径。
        sheet_name: 目标 sheet。
        header_row: 表头行号（1 起始）。
        sheet_info: 已扫描的 sheet 元信息（复用，避免重复开簿）。
        max_significant_digits: R6 阈值（默认 5，可由 JSON global 覆盖）。
        na_policy: "preserve"（默认）｜"pandas"（R7／A-08 的空值口径）。
        enable_cache: H10 幂等缓存开关——**本批仅保留签名**，由 P5 实现。
        progress: 可选进度回调（每阶段一次）。

    Returns:
        NormalizeResult。

    Raises:
        ValueError: 表头行为空（REQ-R2）／列名含禁止字符（A-03）／表不存在。
        FileNotFoundError: 文件不存在。
        RuntimeError: 取消（沿用导入链的取消语义）。
    """
    from openpyxl import load_workbook

    src = Path(file_path)
    if not src.is_file():
        raise FileNotFoundError(f"Excel 文件不存在: {file_path}")

    if sheet_info is None:
        sheet_info = scan_sheets(str(src))
    meta_row = next((m for m in sheet_info if m.get("sheet_name") == sheet_name), None)
    if meta_row is None:
        raise ValueError(
            f"数据表不存在: {sheet_name}，可用: {[m['sheet_name'] for m in sheet_info]}")

    def _tick(stage: str) -> None:
        if progress is not None:
            try:
                progress(stage)
            except Exception as e:  # noqa: BLE001 进度回调失败不影响规范化
                logger.debug(f"[excel_normalizer] 进度回调异常（忽略）: {e}")

    # ① 读取（表头行物化在 read_excel_sheet 内完成；复用 sheet_info 避免重复开簿）
    _tick("读取数据")
    df = read_excel_sheet(str(src), sheet_name, header_row, sheet_info=sheet_info)

    report_entries: List[Dict[str, Any]] = []
    warnings: List[str] = []
    meta: Dict[str, Dict[str, Any]] = {}

    # H1：重复列名/空列名归一（须在其它规范化阶段之前，使 NormalizeResult 的列名
    # 成为全流程唯一来源）。pandas 已对重复表头加 ".1" 后缀，此处还原为需求措辞
    # 的 `_2`／`_3`；空表头格（"Unnamed: N" 或全空白）归一为 `未命名列_N`。
    new_cols, renamed = dedup_columns(list(df.columns))
    if renamed:
        df.columns = new_cols          # 仅改列元数据，不复制数据（内存红线 §2.1 条 5）
        for rn in renamed:
            report_entries.append({
                "sheet": sheet_name, "位置": rn["新列名"],
                "原始内容": rn["原始列名"], "处理方式": WAY_DEDUP,
                "结果": f"重命名为 {rn['新列名']}",
            })
        _warn(warnings, f"数据表 [{sheet_name}] 中有 {len(renamed)} 个重复或空白的"
                        f"列名已自动规范命名，详见处理报告")

    # H7：超长数字精度提示（扫描期；**只提示，绝不改写数据**——源文件精度已丢失）
    precision_cols = detect_precision_loss(df, meta)
    for pc in precision_cols:
        report_entries.append({
            "sheet": sheet_name, "位置": pc["列名"], "原始内容": pc["样本值"],
            "处理方式": WAY_PRECISION,
            "结果": f"该列存在超长数字（{pc['位数']} 位），Excel 已将其精度限制为 "
                    f"15 位有效数字，请核对源数据",
        })
    if precision_cols:
        _warn(warnings, f"数据表 [{sheet_name}] 的 "
                        f"{'、'.join(pc['列名'] for pc in precision_cols)} 列存在"
                        f"超长数字（超过 15 位），Excel 已丢失其精度且无法恢复，"
                        f"请核对源数据")

    sheet_rows = int(meta_row.get("rows") or 0)
    wb_tex = None
    wb_val = None

    # H10：会话内幂等缓存（文件指纹 + sheet + 表头行 + 规则版本）。命中且缓存表明
    # 该表无合并格/公式/错误值/超链接时，跳过全量开簿（避免重复双开簿与公式扫描）。
    cache_key: Optional[str] = None
    cache_hit = False
    if enable_cache and NORMALIZE_CACHE_ENABLED:
        try:
            cache_key = normalized_cache_key(
                str(src), sheet_name, header_row, NORMALIZE_RULES_VERSION)
            _cached = load_normalized_cache(cache_key)
            if _cached and not _cached.get("stage_a_transforms", True):
                cache_hit = True
        except Exception as e:  # noqa: BLE001 缓存失败绝不影响规范化
            logger.debug(f"[excel_normalizer] 计算/读取缓存失败（忽略）: {e}")
    stage_a_transforms = False

    # 阶段 A：需全量开簿的四段（R3 → R4 → H4 → R5）。
    # 顺序＝管线规范（plan.md L2330/L2365，不得颠倒）：合并格 → 公式兜底 →
    # 错误值 → 超链接。开簿在 finally 内立即关闭，避免后续纯内存阶段占用。
    try:
        if cache_hit:
            _warn(warnings, f"数据表 [{sheet_name}] 命中缓存"
                            f"（同一会话内重复导入，未重复扫描公式/超链接）")
        elif sheet_rows > FULL_LOAD_MAX_ROWS:
            _warn(warnings, f"数据表 [{sheet_name}] 行数较多（{sheet_rows} 行），"
                            f"为控制内存未处理合并单元格与超链接")
            report_entries.append({
                "sheet": sheet_name, "位置": f"整表 {sheet_rows} 行", "原始内容": "",
                "处理方式": WAY_NOT_DONE,
                "结果": f"行数超过 {FULL_LOAD_MAX_ROWS}，未做合并格/超链接处理",
            })
        else:
            wb_tex = load_workbook(str(src), read_only=False, data_only=False)
            ws_tex = wb_tex[sheet_name]

            # H6 非单元格内容探测（图片/图表/批注）——须在全量开簿阶段做
            # （只读模式无 _images/_charts/批注，R11/P5 实测）；仅告知，不导入。
            _tick("探测非单元格内容")
            noncell = detect_non_cell_content(ws_tex)
            if noncell["images"] or noncell["charts"] or noncell["comments"]:
                report_entries.append({
                    "sheet": sheet_name, "位置": "整表", "原始内容": "",
                    "处理方式": WAY_NONCELL,
                    "结果": f"含 {noncell['charts']} 张图表、{noncell['images']} 张"
                            f"图片、{noncell['comments']} 处批注（不会被导入）",
                })
                _warn(warnings, f"数据表 [{sheet_name}] 含 {noncell['charts']} 张图表、"
                                f"{noncell['images']} 张图片、{noncell['comments']} 处"
                                f"批注，这些内容不会被导入")

            # R3 合并单元格拆分
            _tick("拆分合并单元格")
            df, splits = split_merged_cells(ws_tex, df, header_rows=1)
            report_entries.extend(splits)
            for s in splits:
                if s["处理方式"] == WAY_NOT_DONE:
                    _warn(warnings, f"数据表 [{sheet_name}] 的合并单元格过多，"
                                    f"本次未自动拆分（结果已按原样保留）")
                elif s["处理方式"] == WAY_SPLIT:
                    _set_meta_flag(meta, s.get("列名", ""), "was_merged")

            # R4 公式兜底（强制管线第 1 段）
            _tick("处理公式单元格")
            wb_val = load_workbook(str(src), read_only=True, data_only=True)
            df, formulas = resolve_formula_cells(
                ws_tex, wb_val[sheet_name], df,
                offset_rows=header_row - 1, offset_cols=0)
            for fc in formulas:
                report_entries.append({
                    "sheet": sheet_name,
                    "位置": fc["单元格"], "原始内容": "（空）",
                    "处理方式": WAY_FORMULA_FALLBACK,
                    "结果": fc["公式原文"],
                })
            if formulas:
                _warn(warnings, f"数据表 [{sheet_name}] 中有 {len(formulas)} 个公式"
                                f"单元格没有计算值，已保留公式原文"
                                f"（建议在 Excel 中打开并保存后重新导入）")

            # H4 错误值 → NULL（须早于 A-08 的字面 NA 保留策略，见 plan.md REQ-H4）
            _tick("处理错误值单元格")
            df, error_cells = normalize_error_cells(df, meta)
            # R11/P4 实测补充：openpyxl 把错误值存为 data_type='e'，pandas 会把它
            # 读成 NaN（df 中已无原文），故原文从工作表读回以完成留痕
            error_cells += collect_workbook_errors(
                ws_tex, header_row - 1, df.shape[0], df.shape[1])
            for ec in error_cells:
                report_entries.append({
                    "sheet": sheet_name,
                    "位置": f"{_coord(ec['行'] + header_row, ec['列'])}",
                    "原始内容": ec["原文"],
                    "处理方式": WAY_ERROR_NULL,
                    "结果": "NULL（错误值不进入数据，原文已记录）",
                })
            if error_cells:
                _warn(warnings, f"数据表 [{sheet_name}] 中有 {len(error_cells)} 个"
                                f"错误值单元格已转为空值（原文已记录）")

            # R5 超链接展开
            _tick("展开超链接")
            df, links = expand_hyperlinks(ws_tex, df, offset_rows=header_row - 1)
            for lk in links:
                report_entries.append({
                    "sheet": sheet_name,
                    "位置": f"{_coord(lk['行'] + header_row, lk['列'])}",
                    "原始内容": lk["显示文本"],
                    "处理方式": WAY_HYPERLINK,
                    "结果": lk["目标地址"],
                })
            if links:
                _warn(warnings, f"数据表 [{sheet_name}] 中有 {len(links)} 个超链接"
                                f"已替换为链接地址文本")

            # H10：本表是否发生阶段 A 变换（供缓存判定下次可否安全跳开全量开簿）
            stage_a_transforms = bool(splits or formulas or error_cells or links)
    finally:
        for _wb in (wb_val, wb_tex):
            if _wb is not None:
                try:
                    _wb.close()
                except Exception as e:  # noqa: BLE001 关闭失败不阻断
                    logger.debug(f"[excel_normalizer] 关簿异常（忽略）: {e}")
        gc.collect()

    # 阶段 B：纯内存规范化（R7 清洗 → A-08 空值策略 → A-06/H3/A-04 类型规范化）
    # R7 文本清洗（仅数据单元格；表头不清洗，遵 D10 边界 / A-03 拒绝口径）
    _tick("清洗文本")
    for ci in range(df.shape[1]):
        col = df.columns[ci]
        series = df.iloc[:, ci]
        if not _is_text_col(series):
            continue
        df[df.columns[ci]] = clean_cell_text(series, meta, col)
        if meta.get(str(col), {}).get("cleaned"):
            report_entries.append({
                "sheet": sheet_name, "位置": str(col), "原始内容": "",
                "处理方式": WAY_CLEAN,
                "结果": "去除首尾空格/控制字符（含全角空格）",
            })

    # A-08 空值策略（空白 → NULL；字面缺失值按策略）
    _tick("应用空值策略")
    df, nulled_cells = apply_na_policy(df, na_policy)
    if nulled_cells:
        report_entries.append({
            "sheet": sheet_name, "位置": f"{len(nulled_cells)} 个单元格",
            "原始内容": "", "处理方式": "空值归一",
            "结果": f"空白/字面缺失值按 [{na_policy}] 策略归一为 NULL",
        })

    # A-06 日期 → ISO 8601 ／ REQ-H3 布尔 → 1/0 ／ A-04 类型推断
    _tick("类型规范化")
    df, type_reports = normalize_column_types(
        df, meta, max_significant_digits)
    for tr in type_reports:
        report_entries.append({
            "sheet": sheet_name, "位置": tr["列名"], "原始内容": "",
            "处理方式": tr["方式"], "结果": tr["结果"],
        })

    # H5：全空列保留并标记；**尾部**连续全空行裁剪（中间空行保留为数据行）
    _tick("处理空列与尾部空行")
    df, empty_cols, trimmed_rows = handle_empty_cols_rows(df, meta)
    for ec in empty_cols:
        report_entries.append({
            "sheet": sheet_name, "位置": ec, "原始内容": "",
            "处理方式": "保留空列",
            "结果": "整列为空，已保留并在元数据中标记",
        })
    if trimmed_rows:
        report_entries.append({
            "sheet": sheet_name, "位置": "表尾", "原始内容": "",
            "处理方式": WAY_TRIM, "结果": f"裁剪 {trimmed_rows} 行尾部空白行",
        })
        _warn(warnings, f"数据表 [{sheet_name}] 尾部 {trimmed_rows} 行空白行已裁剪")

    _tick("完成")

    result = NormalizeResult(
        dataframe=df, meta=meta,
        report_entries=report_entries, warnings=warnings,
    )
    # H10：写出幂等缓存（失败一律忽略，绝不中断规范化）
    if cache_key is not None:
        _save_normalized_cache(cache_key, result, stage_a_transforms)

    logger.info(f"[excel_normalizer] 规范化完成: {sheet_name}，"
                f"{df.shape[0]} 行 × {df.shape[1]} 列，"
                f"报告 {len(report_entries)} 条，告警 {len(warnings)} 条")
    return result
