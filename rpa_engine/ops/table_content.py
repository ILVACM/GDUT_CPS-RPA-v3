"""
rpa_engine/ops/table_content.py

Layer 1 — 表内容操作模块。

提供行级插入、条件更新、条件删除和条件查询。全部接收共享连接 conn（D8），
标识符经 quote_ident 引用，条件统一走 build_where（多条件+操作符白名单，
修复 N2/N4），写操作包裹事务（修复 N11），无裸 except。

依赖库：sqlite3（内置）
"""

import sqlite3
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

from ops.sql_safety import (
    build_where,
    get_table_columns,
    quote_ident,
    quote_ident_list,
    require_table,
    txn,
)


def insert_rows(
    conn: sqlite3.Connection,
    table_name: str,
    rows: List[Dict[str, Any]],
) -> int:
    """插入行（单事务批量），返回成功插入行数。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 目标表名。
        rows: 数据行列表，每项 {"列名": 值}；无效列的行跳过并告警。

    Returns:
        int: 成功插入的行数。

    Raises:
        ValueError: 表名为空、表不存在或 rows 为空。
        sqlite3.Error: 插入失败（事务回滚后向上抛出）。
    """
    if not table_name or not table_name.strip():
        raise ValueError("insert_rows: table_name 不能为空")

    require_table(conn, table_name)

    if not rows:
        raise ValueError("insert_rows: rows 不能为空列表")

    existing_columns = get_table_columns(conn, table_name)

    inserted = 0
    with txn(conn):
        # R6/D8（P3-6）：按列集分桶后 executemany 批量提交
        # （原逐行 prepare+execute；值参数化口径不变）
        buckets: Dict[tuple, List[tuple]] = {}
        for row in rows:
            valid_data = {k: v for k, v in row.items() if k in existing_columns}
            if not valid_data:
                logger.warning(f"[table_content] 插入行无可匹配列，跳过: {row}")
                continue
            cols = tuple(valid_data.keys())
            buckets.setdefault(cols, []).append(
                tuple(valid_data[c] for c in cols))
        for cols, data_rows in buckets.items():
            placeholders = ", ".join(["?"] * len(cols))
            sql = (
                f"INSERT INTO {quote_ident(table_name)} "
                f"({quote_ident_list(list(cols))}) VALUES ({placeholders})"
            )
            conn.executemany(sql, data_rows)
            inserted += len(data_rows)

    logger.info(f"[table_content] 插入完成: {table_name}, {inserted} 行")
    return inserted


def update_rows(
    conn: sqlite3.Connection,
    table_name: str,
    conditions: List[Dict[str, Any]],
    values: Dict[str, Any],
) -> int:
    """条件更新，返回影响行数。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 目标表名。
        conditions: 筛选条件列表（build_where 格式），空列表表示全表更新。
        values: 更新值 {"列名": 新值}。

    Returns:
        int: 受影响的行数。

    Raises:
        ValueError: 表名为空、表不存在、values 为空或含无效列。
    """
    if not table_name or not table_name.strip():
        raise ValueError("update_rows: table_name 不能为空")

    require_table(conn, table_name)

    if not values:
        raise ValueError("update_rows: values 不能为空字典")

    existing_columns = get_table_columns(conn, table_name)

    # SET 子句（值全部参数化）
    set_clauses = []
    set_values: List[Any] = []
    for col, val in values.items():
        if col not in existing_columns:
            raise ValueError(
                f"update_rows: 列不存在: {col}，可用列: {existing_columns}"
            )
        set_clauses.append(f"{quote_ident(col)} = ?")
        set_values.append(val)

    where_sql, where_params = build_where(conditions)

    sql = (
        f"UPDATE {quote_ident(table_name)} SET {', '.join(set_clauses)} "
        f"WHERE {where_sql}"
    )

    with txn(conn):
        cursor = conn.execute(sql, tuple(set_values) + where_params)
        affected = cursor.rowcount

    logger.info(f"[table_content] 更新完成: {table_name}, 影响 {affected} 行")
    return affected


def delete_rows(
    conn: sqlite3.Connection,
    table_name: str,
    conditions: List[Dict[str, Any]],
) -> int:
    """条件删除，返回影响行数。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 目标表名。
        conditions: 筛选条件列表（build_where 格式）。

    Returns:
        int: 受影响的行数。

    Raises:
        ValueError: 表名为空、表不存在或 conditions 为空（防止误删全表）。
    """
    if not table_name or not table_name.strip():
        raise ValueError("delete_rows: table_name 不能为空")

    require_table(conn, table_name)

    if not conditions:
        raise ValueError(
            "delete_rows: conditions 不能为空，防止误删全表。如确需清空，请使用 delete_table()"
        )

    where_sql, where_params = build_where(conditions)
    sql = f"DELETE FROM {quote_ident(table_name)} WHERE {where_sql}"

    with txn(conn):
        cursor = conn.execute(sql, where_params)
        affected = cursor.rowcount

    logger.info(f"[table_content] 删除完成: {table_name}, 影响 {affected} 行")
    return affected


def query_rows(
    conn: sqlite3.Connection,
    table_name: str,
    conditions: Optional[List[Dict[str, Any]]] = None,
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """条件查询，返回 DataFrame（显式列名，禁 SELECT *）。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 目标表名。
        conditions: 筛选条件列表；None/空 表示全表。
        columns: 指定列名列表；None 表示全部列（内部显式展开）。

    Returns:
        pd.DataFrame: 查询结果。

    Raises:
        ValueError: 表名为空、表不存在或指定列无效。
    """
    if not table_name or not table_name.strip():
        raise ValueError("query_rows: table_name 不能为空")

    require_table(conn, table_name)

    existing_columns = get_table_columns(conn, table_name)

    use_cols = columns if columns else existing_columns
    for c in use_cols:
        if c not in existing_columns:
            raise ValueError(
                f"query_rows: 列不存在: {c}，可用列: {existing_columns}"
            )

    where_sql, where_params = build_where(conditions or [])

    sql = (
        f"SELECT {quote_ident_list(use_cols)} "
        f"FROM {quote_ident(table_name)} WHERE {where_sql}"
    )
    cursor = conn.execute(sql, where_params)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=use_cols)

    logger.info(f"[table_content] 查询完成: {table_name}, 返回 {len(df)} 行")
    return df
