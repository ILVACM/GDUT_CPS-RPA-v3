"""
rpa_engine/ops/aggregator.py

Layer 2 — 条件统计模块（用户操作目录）。

提供基于 SQL GROUP BY 的多指标聚合统计。全部接收共享连接 conn（D8），
条件走 build_where（修复 N5：旧版无条件过滤且仅单列单函数），
标识符经 quote_ident 引用（修复 N2）。

依赖库：sqlite3（内置）
"""

import sqlite3
from typing import Any, Dict, List, Optional

from loguru import logger

from ops.sql_safety import (
    build_where,
    ensure_index,
    get_table_columns,
    quote_ident,
    require_table,
    txn,
)
from ops.table_lifecycle import guard_overwrite_target

# 支持的聚合函数映射：用户可读名 -> SQL 聚合函数
AGG_FUNCTIONS = {
    "count": "COUNT",
    "sum": "SUM",
    "mean": "AVG",
    "max": "MAX",
    "min": "MIN",
}


def aggregate_table(
    conn: sqlite3.Connection,
    table_name: str,
    group_by: Optional[List[str]],
    metrics: List[Dict[str, str]],
    output_table: str,
    conditions: Optional[List[Dict[str, Any]]] = None,
) -> int:
    """条件统计：分组聚合结果写入输出表，返回输出行数。

    灵活形态：
    - group_by 为空 + metrics 仅 count → 整表计数（单行结果）
    - group_by 为空 + 多指标 → 整表汇总（单行结果）
    - group_by 非空 → 分组统计（每组一行）
    - conditions 非空 → 统计前先过滤（条件统计）

    Args:
        conn: 共享 SQLite 连接。
        table_name: 源表名。
        group_by: 分组列列表；None/空 表示整表统计。
        metrics: 聚合指标列表，每项 {"column": 列名, "func": 聚合函数,
            "alias": 输出列名}；count 可用 "*" 表示 COUNT(*)。
        output_table: 输出表名（replace 语义）。
        conditions: 筛选条件列表（build_where 格式）；None/空 表示不过滤。

    Returns:
        int: 输出表行数。

    Raises:
        ValueError: 参数不合法、表/列不存在或聚合函数不支持。
    """
    if not table_name or not table_name.strip():
        raise ValueError("aggregate_table: table_name 不能为空")
    if not output_table or not output_table.strip():
        raise ValueError("aggregate_table: output_table 不能为空")
    if not metrics:
        raise ValueError("aggregate_table: metrics 不能为空列表")

    require_table(conn, table_name)

    existing_columns = get_table_columns(conn, table_name)
    group_by = group_by or []

    for col in group_by:
        if col not in existing_columns:
            raise ValueError(
                f"aggregate_table: 分组列不存在: {col}，可用列: {existing_columns}"
            )

    # 校验指标并构建聚合表达式
    agg_exprs: List[str] = []
    used_aliases = set(group_by)
    for m in metrics:
        func = str(m.get("func", "")).lower().strip()
        column = m.get("column", "")
        if func not in AGG_FUNCTIONS:
            raise ValueError(
                f"aggregate_table: 不支持的聚合函数 '{func}'，"
                f"支持: {list(AGG_FUNCTIONS.keys())}"
            )

        # count 允许 "*"（COUNT(*)）；其余函数要求有效列
        if column != "*":
            if column not in existing_columns:
                raise ValueError(
                    f"aggregate_table: 聚合列不存在: {column}，"
                    f"可用列: {existing_columns}"
                )
            col_ref = quote_ident(column)
        else:
            if func != "count":
                raise ValueError(
                    f"aggregate_table: 仅 count 允许 column='*'，当前 func={func}"
                )
            col_ref = "*"

        alias = m.get("alias") or f"{column}_{func}"
        if alias in used_aliases:
            raise ValueError(f"aggregate_table: 输出列名重复: {alias}")
        used_aliases.add(alias)

        agg_exprs.append(
            f"{AGG_FUNCTIONS[func]}({col_ref}) AS {quote_ident(alias)}"
        )

    # R6/D6（P2-10）：GROUP BY 列条件性建索引（大表才建，幂等）
    ensure_index(conn, table_name, list(group_by or []))

    # SELECT 组装：分组列在前 + 聚合表达式
    select_parts = [quote_ident(c) for c in group_by] + agg_exprs
    where_sql, where_params = build_where(conditions or [])

    sql = (
        f"SELECT {', '.join(select_parts)} "
        f"FROM {quote_ident(table_name)} WHERE {where_sql}"
    )
    if group_by:
        sql += f" GROUP BY {', '.join(quote_ident(c) for c in group_by)}"

    # R11/A-15（G-5①）：拒绝覆盖"存在且非空"的活表
    guard_overwrite_target(conn, output_table)

    with txn(conn):
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(output_table)}")
        conn.execute(f"CREATE TABLE {quote_ident(output_table)} AS {sql}", where_params)

    from ops.sqlite_manager import table_row_count
    row_count = table_row_count(output_table, conn)
    logger.info(
        f"[aggregator] 统计完成: {table_name} -> {output_table}, "
        f"{row_count} 行（分组: {group_by or '整表'}, "
        f"指标: {[m.get('func') for m in metrics]}, "
        f"条件: {len(conditions or [])} 个）"
    )
    return row_count
