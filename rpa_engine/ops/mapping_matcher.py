"""
rpa_engine/ops/mapping_matcher.py

Layer 2 — 跨表映射匹配模块（用户操作目录）。

提供基于 SQL JOIN 的两表匹配（inner/left/right/full 四模式），
替代 Pandas merge（规约红线：关联必须 SQL JOIN）。

修复要点：
- N3 重名列崩溃：右表列统一加 r_ 前缀别名（D9 决策）；若加前缀后
  仍与左表列撞名，则追加数字序号兜底。
- N2 标识符引用：表名/列名全部经 quote_ident。

SQLite 无原生 RIGHT/FULL JOIN：
- right_join = 右表视角 LEFT JOIN（FROM 右表 LEFT JOIN 左表）
- full_join  = 左视角 LEFT JOIN UNION 右视角 LEFT JOIN

依赖库：sqlite3（内置）
"""

import sqlite3
from typing import Dict, List

from loguru import logger

from ops.sql_safety import (
    ensure_index,
    get_table_columns,
    quote_ident,
    require_table,
    txn,
)
from ops.table_lifecycle import guard_overwrite_target

# JOIN 模式
JOIN_MODES = ("inner_join", "left_join", "right_join", "full_join")

# 右表列前缀（D9 决策）
RIGHT_PREFIX = "r_"


def _build_right_aliases(
    left_columns: List[str],
    right_columns: List[str],
) -> Dict[str, str]:
    """构建右表列别名映射 {右表列名: 输出列名}。

    规则：默认 r_{原列名}；若与已占用名（左表列或先前别名）撞名，
    追加数字序号兜底。
    """
    used = set(left_columns)
    aliases: Dict[str, str] = {}

    for col in right_columns:
        candidate = f"{RIGHT_PREFIX}{col}"
        if candidate in used:
            n = 2
            while f"{candidate}_{n}" in used:
                n += 1
            candidate = f"{candidate}_{n}"
        aliases[col] = candidate
        used.add(candidate)

    return aliases


def _left_view_select(
    left_table: str,
    left_columns: List[str],
    right_table: str,
    right_columns: List[str],
    right_aliases: Dict[str, str],
    match_columns: Dict[str, str],
) -> str:
    """构建左视角 SELECT（FROM 左表 LEFT JOIN 右表）。"""
    lq, rq = quote_ident(left_table), quote_ident(right_table)
    sel_l = ", ".join(
        f"{lq}.{quote_ident(c)} AS {quote_ident(c)}" for c in left_columns
    )
    sel_r = ", ".join(
        f"{rq}.{quote_ident(c)} AS {quote_ident(right_aliases[c])}"
        for c in right_columns
    )
    on = " AND ".join(
        f"{lq}.{quote_ident(lc)} = {rq}.{quote_ident(rc)}"
        for lc, rc in match_columns.items()
    )
    return f"SELECT {sel_l}, {sel_r} FROM {lq} LEFT JOIN {rq} ON {on}"


def _right_view_select(
    left_table: str,
    left_columns: List[str],
    right_table: str,
    right_columns: List[str],
    right_aliases: Dict[str, str],
    match_columns: Dict[str, str],
) -> str:
    """构建右视角 SELECT（FROM 右表 LEFT JOIN 左表），输出列序保持左列在前。"""
    lq, rq = quote_ident(left_table), quote_ident(right_table)
    # 列序与左视角一致（左列在前），保证 UNION 对齐
    sel_l = ", ".join(
        f"{lq}.{quote_ident(c)} AS {quote_ident(c)}" for c in left_columns
    )
    sel_r = ", ".join(
        f"{rq}.{quote_ident(c)} AS {quote_ident(right_aliases[c])}"
        for c in right_columns
    )
    # ON 条件与左视角完全一致（等值对称）
    on = " AND ".join(
        f"{lq}.{quote_ident(lc)} = {rq}.{quote_ident(rc)}"
        for lc, rc in match_columns.items()
    )
    return f"SELECT {sel_l}, {sel_r} FROM {rq} LEFT JOIN {lq} ON {on}"


def match_tables(
    conn: sqlite3.Connection,
    left_table: str,
    right_table: str,
    match_columns: Dict[str, str],
    mode: str,
    output_table: str,
) -> int:
    """跨表映射匹配（SQL JOIN），结果写入输出表，返回输出行数。

    左表列保留原名，右表列加 r_ 前缀（防重名，D9）。

    Args:
        conn: 共享 SQLite 连接。
        left_table: 左表名（主表）。
        right_table: 右表名（匹配表）。
        match_columns: 匹配列映射 {"左表列": "右表列"}，至少一项。
        mode: inner_join / left_join / right_join / full_join。
        output_table: 输出表名（replace 语义）。

    Returns:
        int: 输出表行数。

    Raises:
        ValueError: 参数不合法、表/列不存在或模式不支持。
    """
    if not left_table or not left_table.strip():
        raise ValueError("match_tables: left_table 不能为空")
    if not right_table or not right_table.strip():
        raise ValueError("match_tables: right_table 不能为空")
    if left_table == right_table:
        raise ValueError("match_tables: 左右表不能为同一张表（请先复制副本再匹配）")
    if not match_columns:
        raise ValueError("match_tables: match_columns 不能为空字典")
    if mode not in JOIN_MODES:
        raise ValueError(
            f"match_tables: 不支持的 JOIN 模式 '{mode}'，支持的模式: {JOIN_MODES}"
        )
    if not output_table or not output_table.strip():
        raise ValueError("match_tables: output_table 不能为空")

    require_table(conn, left_table)
    require_table(conn, right_table)

    left_columns = get_table_columns(conn, left_table)
    right_columns = get_table_columns(conn, right_table)

    for lc, rc in match_columns.items():
        if lc not in left_columns:
            raise ValueError(
                f"match_tables: 左表列不存在: {lc}，可用列: {left_columns}"
            )
        if rc not in right_columns:
            raise ValueError(
                f"match_tables: 右表列不存在: {rc}，可用列: {right_columns}"
            )

    right_aliases = _build_right_aliases(left_columns, right_columns)
    lq, rq = quote_ident(left_table), quote_ident(right_table)

    # R6/D6（P2-10）：JOIN 前对匹配列条件性建索引（大表才建，幂等）
    ensure_index(conn, left_table, list(match_columns.keys()))
    ensure_index(conn, right_table, list(match_columns.values()))

    if mode == "inner_join":
        sel_l = ", ".join(
            f"{lq}.{quote_ident(c)} AS {quote_ident(c)}" for c in left_columns
        )
        sel_r = ", ".join(
            f"{rq}.{quote_ident(c)} AS {quote_ident(right_aliases[c])}"
            for c in right_columns
        )
        on = " AND ".join(
            f"{lq}.{quote_ident(lc)} = {rq}.{quote_ident(rc)}"
            for lc, rc in match_columns.items()
        )
        sql = f"SELECT {sel_l}, {sel_r} FROM {lq} INNER JOIN {rq} ON {on}"
    elif mode == "left_join":
        sql = _left_view_select(
            left_table, left_columns, right_table, right_columns,
            right_aliases, match_columns,
        )
    elif mode == "right_join":
        # 右视角 LEFT JOIN = RIGHT JOIN 语义
        sql = _right_view_select(
            left_table, left_columns, right_table, right_columns,
            right_aliases, match_columns,
        )
    else:  # full_join
        sql_fwd = _left_view_select(
            left_table, left_columns, right_table, right_columns,
            right_aliases, match_columns,
        )
        sql_rev = _right_view_select(
            left_table, left_columns, right_table, right_columns,
            right_aliases, match_columns,
        )
        # UNION 去重合并（交集行在两个视角各出现一次，UNION 去重后保留一份）
        sql = f"{sql_fwd} UNION {sql_rev}"

    # R11/A-15（G-5①）：拒绝覆盖"存在且非空"的活表
    guard_overwrite_target(conn, output_table)

    with txn(conn):
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(output_table)}")
        conn.execute(f"CREATE TABLE {quote_ident(output_table)} AS {sql}")

    from ops.sqlite_manager import table_row_count
    row_count = table_row_count(output_table, conn)
    logger.info(
        f"[mapping_matcher] 匹配完成（{mode}）: {left_table} & {right_table} "
        f"-> {output_table}, {row_count} 行"
    )
    return row_count
