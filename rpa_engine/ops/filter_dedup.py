"""
rpa_engine/ops/filter_dedup.py

Layer 2 — 条件筛选与去重模块（用户操作目录）。

提供基于 SQL WHERE 的多条件筛选和基于 ROW_NUMBER 的条件去重。
全部接收共享连接 conn（D8），条件走 build_where（修复 N4 单条件限制），
标识符经 quote_ident 引用（修复 N2），写操作包裹事务（修复 N11）。

依赖库：sqlite3（内置）
"""

import sqlite3
from typing import Any, Dict, List

from loguru import logger

from ops.sql_safety import (
    build_where,
    ensure_index,
    get_table_columns,
    quote_ident,
    quote_ident_list,
    require_table,
    txn,
)
from ops.table_lifecycle import guard_overwrite_target

# 兼容再导出：操作符白名单统一定义于 sql_safety
from ops.sql_safety import SUPPORTED_OPERATORS  # noqa: F401


def filter_table(
    conn: sqlite3.Connection,
    table_name: str,
    conditions: List[Dict[str, Any]],
    output_table: str,
    logic: str = "AND",
) -> int:
    """条件筛选：源表按条件过滤后写入输出表，返回输出行数。

    支持多条件组合（AND/OR），结果为新表（replace 语义）。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 源表名。
        conditions: 条件列表（build_where 格式）。
        output_table: 输出表名。
        logic: 条件连接词 AND/OR。

    Returns:
        int: 输出表行数。

    Raises:
        ValueError: 参数不合法、源表不存在或条件列不存在。
    """
    if not table_name or not table_name.strip():
        raise ValueError("filter_table: table_name 不能为空")
    if not output_table or not output_table.strip():
        raise ValueError("filter_table: output_table 不能为空")
    if not conditions:
        raise ValueError("filter_table: conditions 不能为空列表（无条件筛选无意义）")

    require_table(conn, table_name)

    existing_columns = get_table_columns(conn, table_name)
    for cond in conditions:
        col = cond.get("column", "")
        if col not in existing_columns:
            raise ValueError(
                f"filter_table: 条件列不存在: {col}，可用列: {existing_columns}"
            )

    where_sql, where_params = build_where(conditions, logic)
    cols_str = quote_ident_list(existing_columns)

    sql = (
        f"SELECT {cols_str} FROM {quote_ident(table_name)} WHERE {where_sql}"
    )

    # R11/A-15（G-5①）：拒绝覆盖"存在且非空"的活表
    guard_overwrite_target(conn, output_table)

    with txn(conn):
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(output_table)}")
        conn.execute(
            f"CREATE TABLE {quote_ident(output_table)} AS {sql}",
            where_params,
        )

    from ops.sqlite_manager import table_row_count
    row_count = table_row_count(output_table, conn)
    logger.info(
        f"[filter_dedup] 条件筛选完成: {table_name} -> {output_table}, "
        f"{row_count} 行（{logic} 连接，{len(conditions)} 个条件）"
    )
    return row_count


def dedup_table(
    conn: sqlite3.Connection,
    table_name: str,
    key_columns: List[str],
    keep: str,
    output_table: str,
) -> int:
    """条件去重：按键列分组保留首次/末次出现，结果写入输出表。

    使用 ROW_NUMBER() 窗口函数（SQLite 3.25+）。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 源表名。
        key_columns: 去重键列列表。
        keep: 保留策略 first/last。
        output_table: 输出表名。

    Returns:
        int: 输出表行数。

    Raises:
        ValueError: 参数不合法、源表/键列不存在或 keep 非法。
    """
    if not table_name or not table_name.strip():
        raise ValueError("dedup_table: table_name 不能为空")
    if not output_table or not output_table.strip():
        raise ValueError("dedup_table: output_table 不能为空")
    if not key_columns:
        raise ValueError("dedup_table: key_columns 不能为空列表")
    if keep not in ("first", "last"):
        raise ValueError(f"dedup_table: keep 必须为 'first' 或 'last'，当前值: {keep}")

    require_table(conn, table_name)

    existing_columns = get_table_columns(conn, table_name)
    for col in key_columns:
        if col not in existing_columns:
            raise ValueError(
                f"dedup_table: 键列不存在: {col}，可用列: {existing_columns}"
            )

    # R6/D6（P2-10）：去重分区列条件性建索引（大表才建，幂等）
    ensure_index(conn, table_name, list(key_columns))

    partition_str = quote_ident_list(key_columns)
    order_direction = "ASC" if keep == "first" else "DESC"
    cols_str = quote_ident_list(existing_columns)

    # 内层窗口标记行号，外层取 __rn=1（显式列名，禁 SELECT *）
    sql = (
        f"SELECT {cols_str} FROM ("
        f"SELECT {cols_str}, ROW_NUMBER() OVER ("
        f"PARTITION BY {partition_str} ORDER BY rowid {order_direction}"
        f") AS __rn FROM {quote_ident(table_name)}"
        f") WHERE __rn = 1"
    )

    # R11/A-15（G-5①）：拒绝覆盖"存在且非空"的活表
    guard_overwrite_target(conn, output_table)

    with txn(conn):
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(output_table)}")
        conn.execute(f"CREATE TABLE {quote_ident(output_table)} AS {sql}")

    from ops.sqlite_manager import table_row_count
    row_count = table_row_count(output_table, conn)
    logger.info(
        f"[filter_dedup] 去重完成: {table_name} -> {output_table}, "
        f"{row_count} 行（键列: {key_columns}, 策略: {keep}）"
    )
    return row_count
