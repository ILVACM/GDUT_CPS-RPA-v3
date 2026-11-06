"""
rpa_engine/ops/exporter.py

Layer 2 — 数据导出模块（用户操作目录）。

基础导出：SQLite 表 → Excel 文件（无模板，需求 n：直接导出）。

设计要点：
- 修复 N10：全程不使用 pandas/pd.read_sql，改为 cursor 流式取数
  分批写入 openpyxl（每批 5000 行）。
- R15/B-03（原编号 F-05）：改用 openpyxl **write_only 模式**——工作簿不再
  常驻全部单元格对象，内存占用与表大小解耦，大表导出安全（原实现为普通
  `Workbook()`，内存随行数线性增长，与本注释不符；B-76 随本改动一并更正）。
- 显式列名查询（禁 SELECT *），标识符经 quote_ident 引用。

依赖库：openpyxl>=3.1
"""

import gc
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, List, Optional

from loguru import logger

from paths import get_engine_root
from ops.sql_safety import (
    get_table_columns,
    quote_ident,
    quote_ident_list,
    require_table,
)

# 流式写出批次大小（行）
BATCH_SIZE = 5000

# R11/A-06（H2）：ISO 8601 文本 → 真日期写回（导出侧）。仅匹配严格形态，
# 解析失败一律回落写原始字符串（裁定 G10：解析失败不得引入新失败）。
_DATE_OUT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_OUT_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
_FMT_DATE = "yyyy-mm-dd"
_FMT_DATETIME = "yyyy-mm-dd hh:mm:ss"

# R11/D3［P4-4］：**仅用于元数据标记为 datetime 的列**的宽松形态（无歧义限定，
# 非无限放宽）：`YYYY/M/D`／`YYYY.M.D`（→日期）与 `YYYY-MM-DDTHH:MM(:SS)`。
_LOOSE_DATE_RE = re.compile(r"^\d{4}[/.]\d{1,2}[/.]\d{1,2}$")
_LOOSE_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$")


def _iso_to_datetime(value):
    """把 ISO 8601 文本反解为 datetime 及其 Excel number_format；否则返回 None。"""
    if not isinstance(value, str):
        return None, None
    if _DATE_OUT_RE.match(value):
        try:
            return datetime.strptime(value, "%Y-%m-%d"), _FMT_DATE
        except ValueError:
            return None, None
    if _DATETIME_OUT_RE.match(value):
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S"), _FMT_DATETIME
        except ValueError:
            return None, None
    return None, None


def _parse_datetime_loose(value):
    """R11/D3［P4-4］：宽松形态解析（**仅供元数据标记为 datetime 的列**使用）。

    先走严格 ISO（与改动前一致）；未命中再试**无歧义**宽松形态：
    `YYYY/M/D`／`YYYY.M.D`（→ 日期）与 `YYYY-MM-DDTHH:MM(:SS)`（→ 日期时间）。
    **任何解析失败一律返回 (None, None)**——不得引入新失败（裁定 G10 精神）。
    """
    dt, fmt = _iso_to_datetime(value)
    if dt is not None:
        return dt, fmt
    if not isinstance(value, str):
        return None, None
    v = value.strip()
    if _LOOSE_DATE_RE.match(v):
        try:
            return datetime.strptime(v.replace("/", "-").replace(".", "-"),
                                     "%Y-%m-%d"), _FMT_DATE
        except ValueError:
            return None, None
    if _LOOSE_DATETIME_RE.match(v):
        try:
            return datetime.fromisoformat(v), _FMT_DATETIME
        except ValueError:
            return None, None
    return None, None


def _datetime_columns(conn: sqlite3.Connection, table_name: str) -> set:
    """R11/D3［P4-4］：取该表在 `__normalize_meta` 中被标记为 datetime 的列名集合。

    元数据表不存在（旧库／旧会话）或任何查询异常 → **返回空集**，
    使导出行为与改动前**逐格等价**（＝回落路径的保证）。
    只取列名集合（≤ 列数），不加载行数据（内存安全）。
    """
    try:
        rows = conn.execute(
            "SELECT column FROM __normalize_meta "
            "WHERE sqlite_table = ? AND original_type = 'datetime'",
            (str(table_name),),
        ).fetchall()
    except sqlite3.Error as e:
        logger.debug(f"[exporter] 元数据表不可用（回落值形态判定）: {e}")
        return set()
    return {str(r[0]) for r in rows if r and r[0] is not None}


def export_table(
    conn: sqlite3.Connection,
    table_name: str,
    output_path: str,
    sheet_name: str = "数据",
    cancel_check: Optional[Callable[[], bool]] = None,
) -> int:
    """基础导出：SQLite 表 → xlsx 文件（流式写出），返回导出行数。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 源表名。
        output_path: 输出 xlsx 路径（目录不存在时自动创建）。
        sheet_name: 输出工作表名（默认"数据"）。

    Returns:
        int: 导出的数据行数（不含表头）。

    Raises:
        ValueError: 表名为空、表不存在或输出路径为空。
        OSError: 输出文件写入失败。
    """
    if not table_name or not table_name.strip():
        raise ValueError("export_table: table_name 不能为空")
    if not output_path or not output_path.strip():
        raise ValueError("export_table: output_path 不能为空")

    require_table(conn, table_name)

    # 输出目录自动创建（修复旧版"目录不存在直接报错"的体验问题）
    # R15/B-49：后缀不再静默改写（"报表.csv" 曾被改成 "报表.xlsx" 且界面零提示）——
    # 改为中文报错，与 D10「所见即所得」一致
    out = Path(output_path)
    if out.suffix.lower() != ".xlsx":
        raise ValueError(
            f"export_table: 导出文件必须为 .xlsx，当前为 "
            f"{out.suffix or '（无后缀）'}，请修改导出路径后重试")
    # R6/D7（P2-13）：导出路径不得指向程序导入副本区（防覆盖输入副本）
    _copy_area = (Path(get_engine_root()) / "temp" / "input_selection").resolve()
    _out_res = out.resolve()
    if _out_res == _copy_area or _copy_area in _out_res.parents:
        raise ValueError("export_table: 导出路径不得指向程序导入副本区")
    out.parent.mkdir(parents=True, exist_ok=True)

    columns = get_table_columns(conn, table_name)

    # R11/D3［P4-4］：元数据优先——被标记为 datetime 的列按宽松形态解析
    # （无元数据表则返回空集 → 全部回落严格值形态判定，行为与改动前一致）
    dt_cols = _datetime_columns(conn, table_name)

    # 显式列名查询（禁 SELECT *）
    sql = f"SELECT {quote_ident_list(columns)} FROM {quote_ident(table_name)}"

    from openpyxl import Workbook
    from openpyxl.cell import WriteOnlyCell

    # R15/B-03：write_only 模式（内存与表大小解耦）；write_only 下无默认工作表，
    # 须 create_sheet；日期格式经 WriteOnlyCell.number_format 保留（与改动前等价）
    wb = Workbook(write_only=True)
    ws = wb.create_sheet(title=str(sheet_name)[:31])  # sheet 名上限 31 字符

    # 写表头（原样，D10：所见即所得）
    ws.append(list(columns))

    exported = 0
    cursor = conn.execute(sql)
    while True:
        # R6/D1（P1-4）：长导出循环内取消检查（每批 5000 行一查）
        if cancel_check is not None and cancel_check():
            raise RuntimeError("步骤已取消：收到终止请求")
        rows = cursor.fetchmany(BATCH_SIZE)
        if not rows:
            break
        for row in rows:
            # R11/A-06：ISO 8601 文本 → 真日期写回（number_format）；其余原样写
            out_row: List[Any] = []
            for c_i, v in enumerate(row, start=1):
                # R11/D3［P4-4］：元数据标记列 → 宽松形态解析；未标记列 → 严格值形态（现状）
                is_dt_col = str(columns[c_i - 1]) in dt_cols
                dt, fmt = (_parse_datetime_loose(v) if is_dt_col
                           else _iso_to_datetime(v))
                if dt is not None:
                    cell = WriteOnlyCell(ws)
                    cell.value = dt
                    cell.number_format = fmt
                    out_row.append(cell)
                else:
                    out_row.append(v)
            ws.append(out_row)
        exported += len(rows)

    wb.save(str(out))
    wb.close()
    gc.collect()

    logger.info(
        f"[exporter] 导出完成: {table_name} -> {out.name}, "
        f"{exported} 行 × {len(columns)} 列（流式写出）"
    )
    return exported
