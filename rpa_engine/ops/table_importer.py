"""
rpa_engine/ops/table_importer.py

Layer 1 — Excel 导入 SQLite 模块（需求 c：数据表导入）。

将临时区 xlsx 的指定 sheet 按表头行设置导入为 SQLite 数据表。
读取仍走 excel_preprocessor（read_excel_sheet），规范化（清洗/空值/日期/布尔/
类型推断）走 excel_normalizer.normalize_sheet（R11/A-04 接入），落库走
sqlite_manager.import_dataframe_atomic（R11/A-15 原子导入）。

内存说明：Excel 单 sheet 物理行数上限约 104.8 万行（1,048,576），
在 16GB 目标机上单次加载可行；超过警戒行数时记录 WARNING 提示。

依赖库：pandas>=2.0, openpyxl>=3.1
"""

import gc
import sqlite3
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from ops.excel_preprocessor import read_header_row, scan_sheets
from ops.excel_normalizer import NormalizeResult, normalize_sheet
from ops.sqlite_manager import import_dataframe_atomic, table_row_count

# 内存警戒行数（超过时记录 WARNING，仍可执行：受 Excel 物理行数上限保护）
MEMORY_WARN_ROWS = 500_000

# R11/P6（REQ-H9 接线）：import_excel_table 的返回值结构不可改（plan §0.2 条 2），
# 而报告/元数据表落盘需要 NormalizeResult。GUI 导入为单线程逐表串行调用，故以
# "最近一次结果"桥接调用侧：导入后经 take_last_normalize_result 取用，取走即清空。
_LAST_NORMALIZE_RESULT: Optional[NormalizeResult] = None


def take_last_normalize_result() -> Optional[NormalizeResult]:
    """取出并清空"最近一次 import_excel_table 产出的规范化结果"。

    供调用侧（GUI）在不改 import_excel_table 签名的前提下拿到 NormalizeResult，
    用于 REQ-H9 的报告/元数据表落盘；未成功产出（未导入或导入失败）时返回 None。
    """
    global _LAST_NORMALIZE_RESULT
    r = _LAST_NORMALIZE_RESULT
    _LAST_NORMALIZE_RESULT = None
    return r


def import_excel_table(
    conn: sqlite3.Connection,
    xlsx_path: str,
    sheet_name: str,
    header_row: int,
    table_name: str,
    sheet_info: Optional[List[Dict[str, Any]]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> int:
    """将 xlsx 指定 sheet 导入 SQLite 表（replace 语义），返回导入行数。

    Args:
        conn: 共享 SQLite 连接。
        xlsx_path: 临时区 xlsx 文件路径。
        sheet_name: 源数据表（sheet）名称。
        header_row: 表头所在行号（1 起始；skiprows 物化删前 N-1 行，D5）。
        table_name: 目标 SQLite 表名（已存在则替换）。

    Returns:
        int: 导入的数据行数（不含表头）。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: sheet 不存在、header_row 非法或目标表名为空。
        sqlite3.Error: 写入失败（事务回滚后向上抛出）。
    """
    global _LAST_NORMALIZE_RESULT
    # R11/P6：重置桥接槽（避免上一次残留被误取）
    _LAST_NORMALIZE_RESULT = None

    if not table_name or not table_name.strip():
        raise ValueError("import_excel_table: table_name 不能为空")

    # 预扫元信息：行数超警戒值提示（不阻断，受 Excel 行数物理上限保护）
    # R6/D8（P3-6）：扫描结果一次取得，传参复用给 read_excel_sheet 校验，
    # 消除同文件重复开簿（3 次→2 次；pd.read_excel 的读取开簿不可并入扫描）
    if sheet_info is None:
        sheet_info = scan_sheets(xlsx_path)
    for meta in sheet_info:
        if meta["sheet_name"] == sheet_name and meta["rows"] > MEMORY_WARN_ROWS:
            logger.warning(
                f"[table_importer] 源数据表行数较大（{meta['rows']} 行），"
                f"导入期间内存占用将升高，请注意"
            )

    # R6/D1（P1-4）：导入起点取消检查（导入无行级循环，中断粒度＝表间，
    # 粒度说明记 REPORT §5）
    if cancel_check is not None and cancel_check():
        raise RuntimeError("步骤已取消：收到终止请求")

    # R11/REQ-R2：表头行全空则拒绝并提示（原防护只覆盖"整表无内容"；
    # 用户选中夹在报表中的空行作表头时，表头语义会静默丢失）
    header_vals = read_header_row(xlsx_path, sheet_name, int(header_row))
    if header_vals is not None and all(
            str(v or "").strip() == "" for v in header_vals):
        raise ValueError(
            f"数据表 [{sheet_name}] 的第 {header_row} 行为空，不能作为表头。"
            f"请在界面中重新选择表头行后重试"
        )

    # 读取 ＋ 规范化（R11/A-04）：读取仍在 excel_preprocessor（read_excel_sheet，
    # 表头行物化在内完成），规范化管线（R3/R4/R5/H4/R7/A-08/A-06/H3/A-04）
    # 由 excel_normalizer.normalize_sheet 完成。返回结构 NormalizeResult 不变。
    result = normalize_sheet(xlsx_path, sheet_name, header_row,
                             sheet_info=sheet_info)
    df = result.dataframe

    if df.empty:
        raise ValueError(
            f"import_excel_table: 源数据表 [{sheet_name}] 表头后无数据行，无法导入"
        )

    # R11/A-03：表头禁字符预检——把失败前移到导入入口并给人话定位。
    # 复用 sql_safety 的同源禁字符集合（不另写字面量表）；SQLite 的双引号
    # 标识符本身支持中文/空格/括号，仅这 5 个字符会被 quote_ident 拒绝。
    # 空列名**不在此拒绝**（交由 REQ-H1 归一，见 plan.md §0.7.4 [ADJUSTED-10]）。
    from ops.sql_safety import _FORBIDDEN_IDENT_CHARS
    for _idx, _col in enumerate(df.columns):
        _name = str(_col)
        if not _name.strip():
            continue
        for _ch in _FORBIDDEN_IDENT_CHARS:
            if _ch in _name:
                raise ValueError(
                    f"数据表 [{sheet_name}] 的第 {_idx + 1} 列表头包含不可用字符"
                    f" {repr(_ch)}（常见于表头里的换行或制表符），"
                    f"请先在 Excel 中清理该表头后重试"
                )

    # R11/REQ-H1：重复/空列名归一已由 normalize_sheet 前置完成（结果列为
    # 唯一来源），此处仅作防御：若仍残留重复表头则记录告警便于排查。
    if len(set(map(str, df.columns))) != len(df.columns):
        logger.warning(
            f"[table_importer] 源数据表仍存在重复表头（异常残留）: "
            f"{list(df.columns)}"
        )

    # R11/A-15：改调原子导入（临时表 → 校验行数 → DROP 旧表 → RENAME），
    # 保证落库中途失败不留空壳表（legacy 隔离级别下 DDL 自动提交、不可回滚）。
    import_dataframe_atomic(df, table_name, conn, if_exists="replace")

    row_count = table_row_count(table_name, conn)
    logger.info(
        f"[table_importer] 导入完成: {sheet_name} -> {table_name}, "
        f"{row_count} 行 × {len(df.columns)} 列"
    )

    del df
    gc.collect()
    # R11/P6：导入成功后把规范化结果交给桥接槽，供调用侧落盘 REQ-H9 报告/元数据表
    _LAST_NORMALIZE_RESULT = result
    return row_count
