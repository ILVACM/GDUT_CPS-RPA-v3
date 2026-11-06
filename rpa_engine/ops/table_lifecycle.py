"""
rpa_engine/ops/table_lifecycle.py

Layer 1 — 表生命周期管理模块。

提供数据表的创建、删除、复制、合并功能。全部接收共享连接 conn（D8），
标识符经 quote_ident 安全引用（修复 N2），写操作包裹事务（修复 N11），
列名原样保留不做清洗（D10）。

依赖库：sqlite3（内置）
"""

import sqlite3
from typing import List

from loguru import logger

from ops.sql_safety import (
    get_table_columns,
    quote_ident,
    quote_ident_list,
    require_table,
    table_exists,
    txn,
)

# 兼容再导出（旧调用方 import list_tables 从本模块）
from ops.sql_safety import list_tables  # noqa: F401


def guard_overwrite_target(conn: sqlite3.Connection, output_table: str) -> None:
    """R11/A-15（G-5①）：目标表为「存在且非空」的活表时拒绝覆盖。

    因 legacy 隔离级别下 DDL 自动提交、不可回滚，"先 DROP 后重建"会把用户既有
    数据永久抹掉。故凡"产表/合并/去重/统计/匹配"落点，若目标表已存在且行数>0，
    一律拒绝并要求改用新表名（同源守卫，不得各写一套判据）。

    Args:
        conn: 共享 SQLite 连接。
        output_table: 目标物理表名。

    Raises:
        ValueError: 目标表已存在且行数 > 0。
    """
    if not output_table or not str(output_table).strip():
        raise ValueError("guard_overwrite_target: output_table 不能为空")

    if not table_exists(conn, output_table):
        return
    n = conn.execute(
        f"SELECT COUNT(*) FROM {quote_ident(output_table)}").fetchone()[0]
    if n > 0:
        raise ValueError(
            f"目标数据表 [{output_table}] 已存在且含 {n} 行数据，"
            f"为避免覆盖请改用新的表名")


def create_table(
    conn: sqlite3.Connection,
    table_name: str,
    columns: List[str],
) -> None:
    """新建空白表（若表已存在则先删除后重建）。

    所有列默认 TEXT 类型；列名原样保留（D10）。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 新表名。
        columns: 列名列表。

    Raises:
        ValueError: 表名为空、列名列表为空或列名重复。
    """
    if not table_name or not table_name.strip():
        raise ValueError("create_table: table_name 不能为空")

    if not columns:
        raise ValueError("create_table: columns 不能为空列表")

    # 列名重复会导致建表歧义，前置拦截
    if len(set(columns)) != len(columns):
        dup = [c for c in columns if columns.count(c) > 1]
        raise ValueError(f"create_table: 列名重复: {sorted(set(dup))}")

    cols_def = ", ".join(f"{quote_ident(c)} TEXT" for c in columns)

    with txn(conn):
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(table_name)}")
        conn.execute(f"CREATE TABLE {quote_ident(table_name)} ({cols_def})")

    logger.info(f"[table_lifecycle] 表创建完成: {table_name}, {len(columns)} 列")


def delete_table(conn: sqlite3.Connection, table_name: str) -> bool:
    """删除表，返回是否实际删除。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 目标表名。

    Returns:
        bool: 表存在并删除返回 True；表不存在返回 False。

    Raises:
        ValueError: 表名为空。
    """
    if not table_name or not table_name.strip():
        raise ValueError("delete_table: table_name 不能为空")

    if not table_exists(conn, table_name):
        logger.warning(f"[table_lifecycle] 表不存在，无需删除: {table_name}")
        return False

    with txn(conn):
        conn.execute(f"DROP TABLE {quote_ident(table_name)}")

    logger.info(f"[table_lifecycle] 表删除完成: {table_name}")
    return True


def copy_table(
    conn: sqlite3.Connection,
    src_table: str,
    dst_table: str,
) -> None:
    """复制表结构和数据（保留列类型，显式列名，禁 SELECT *）。

    修复要点：旧实现 CREATE TABLE AS SELECT * 既违反 SELECT * 红线，
    又丢失列类型声明；改为 PRAGMA 读类型 → 显式建表 → 显式列复制。

    Args:
        conn: 共享 SQLite 连接。
        src_table: 源表名。
        dst_table: 目标表名（已存在则先删除重建）。

    Raises:
        ValueError: 表名为空或源表不存在。
    """
    if not src_table or not src_table.strip():
        raise ValueError("copy_table: src_table 不能为空")
    if not dst_table or not dst_table.strip():
        raise ValueError("copy_table: dst_table 不能为空")
    if src_table == dst_table:
        raise ValueError("copy_table: 源表与目标表不能同名")

    require_table(conn, src_table)

    # 读取源表列名+类型（PRAGMA table_info: cid, name, type, notnull, dflt, pk）
    info = conn.execute(f"PRAGMA table_info({quote_ident(src_table)})").fetchall()
    cols = [r[1] for r in info]
    types = [r[2] or "TEXT" for r in info]

    cols_def = ", ".join(
        f"{quote_ident(c)} {t}" for c, t in zip(cols, types)
    )
    cols_str = quote_ident_list(cols)

    with txn(conn):
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(dst_table)}")
        conn.execute(f"CREATE TABLE {quote_ident(dst_table)} ({cols_def})")
        conn.execute(
            f"INSERT INTO {quote_ident(dst_table)} ({cols_str}) "
            f"SELECT {cols_str} FROM {quote_ident(src_table)}"
        )

    logger.info(f"[table_lifecycle] 表复制完成: {src_table} -> {dst_table}")


def merge_tables(
    conn: sqlite3.Connection,
    table_names: List[str],
    dst_table: str,
) -> None:
    """合并多表（列集合一致性校验 + UNION ALL 语义追加）。

    支持同时合并 2 张以上；要求所有源表列名集合完全一致，
    不一致时报错并给出差异列（增强自旧实现的报错信息）。

    Args:
        conn: 共享 SQLite 连接。
        table_names: 源表名列表（≥2 张）。
        dst_table: 目标表名（已存在则先删除重建）。

    Raises:
        ValueError: 源表少于 2 张、表名为空、源表不存在或列集合不一致。
    """
    if not table_names or len(table_names) < 2:
        raise ValueError(f"merge_tables: 至少需要 2 张源表，当前 {len(table_names) if table_names else 0} 张")

    if not dst_table or not dst_table.strip():
        raise ValueError("merge_tables: dst_table 不能为空")

    # 校验所有源表存在并获取列集合
    columns_list = []
    for name in table_names:
        require_table(conn, name)
        columns_list.append(get_table_columns(conn, name))

    # 列集合一致性校验（顺序无关，集合比较）
    first_set = set(columns_list[0])
    for i, cols in enumerate(columns_list[1:], start=1):
        cur_set = set(cols)
        if cur_set != first_set:
            missing = sorted(first_set - cur_set)
            extra = sorted(cur_set - first_set)
            raise ValueError(
                f"merge_tables: 第 {i + 1} 张表 [{table_names[i]}] 列不一致。"
                f"缺少列: {missing}，多出列: {extra}"
            )

    # 按第一张表的列顺序展开（显式列名）
    cols = columns_list[0]
    cols_str = quote_ident_list(cols)

    # 读取第一张表列类型用于建表（保持类型）
    info = conn.execute(f"PRAGMA table_info({quote_ident(table_names[0])})").fetchall()
    type_map = {r[1]: (r[2] or "TEXT") for r in info}
    cols_def = ", ".join(
        f"{quote_ident(c)} {type_map.get(c, 'TEXT')}" for c in cols
    )

    # R11/A-15（G-5①）：拒绝覆盖"存在且非空"的活表（DDL 自动提交不可回滚）
    guard_overwrite_target(conn, dst_table)

    with txn(conn):
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(dst_table)}")
        conn.execute(f"CREATE TABLE {quote_ident(dst_table)} ({cols_def})")
        for name in table_names:
            conn.execute(
                f"INSERT INTO {quote_ident(dst_table)} ({cols_str}) "
                f"SELECT {cols_str} FROM {quote_ident(name)}"
            )

    total = conn.execute(
        f"SELECT COUNT(*) FROM {quote_ident(dst_table)}"
    ).fetchone()[0]
    logger.info(
        f"[table_lifecycle] 表合并完成: {len(table_names)} 张 -> {dst_table}, "
        f"共 {total} 行"
    )
