"""
rpa_engine/ops/table_schema.py

Layer 1 — 表结构管理模块。

提供列重命名、类型转换和列信息查询。全部接收共享连接 conn（D8），
标识符经 quote_ident 安全引用，类型转换白名单仅保留无损可逆对
（TEXT↔INTEGER、TEXT↔REAL），列名原样保留不做清洗（D10）。

依赖库：sqlite3（内置）
"""

import sqlite3
from typing import Dict, List

from loguru import logger

from ops.sql_safety import (
    get_table_columns,
    quote_ident,
    quote_ident_list,
    require_table,
    table_exists,
    txn,
)

# 允许的无损可逆类型转换路径（from_type -> 允许的 to_type 集合）
# 按需求收敛为：文本数字 ↔ 数值（可计算），排除 BLOB 等非常用路径
ALLOWED_TYPE_CONVERSIONS: Dict[str, List[str]] = {
    "TEXT": ["INTEGER", "REAL"],
    "INTEGER": ["TEXT", "REAL"],
    "REAL": ["TEXT", "INTEGER"],
}


def rename_columns(
    conn: sqlite3.Connection,
    table_name: str,
    mapping: Dict[str, str],
) -> bool:
    """批量改列名，返回是否全部成功。

    新列名原样使用（D10：所见即所得，不做空格/横线替换）；
    列不存在或新列名冲突的项跳过并记录，返回 False。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 目标表名。
        mapping: 列名映射 {"旧列名": "新列名"}。

    Returns:
        bool: 全部重命名成功返回 True，部分失败返回 False。

    Raises:
        ValueError: 表名为空、表不存在或映射为空。
    """
    if not table_name or not table_name.strip():
        raise ValueError("rename_columns: table_name 不能为空")

    require_table(conn, table_name)

    if not mapping:
        raise ValueError("rename_columns: mapping 不能为空字典")

    existing_columns = get_table_columns(conn, table_name)
    all_success = True

    # 预检：新列名不得与其他现有列冲突（重命名项自身除外）
    final_names = set(existing_columns)
    for old_name in mapping:
        final_names.discard(old_name)
    for new_name in mapping.values():
        if new_name in final_names:
            logger.warning(f"[table_schema] 目标列名已存在，跳过: {new_name}")
            all_success = False

    with txn(conn):
        for old_name, new_name in mapping.items():
            if old_name not in existing_columns:
                logger.warning(f"[table_schema] 列不存在，跳过: {old_name}")
                all_success = False
                continue
            if new_name in existing_columns and new_name != old_name:
                logger.warning(f"[table_schema] 目标列名已存在，跳过: {new_name}")
                all_success = False
                continue

            try:
                conn.execute(
                    f"ALTER TABLE {quote_ident(table_name)} "
                    f"RENAME COLUMN {quote_ident(old_name)} TO {quote_ident(new_name)}"
                )
                existing_columns.remove(old_name)
                existing_columns.append(new_name)
                logger.info(f"[table_schema] 列重命名: {old_name} -> {new_name}")
            except sqlite3.Error as e:
                logger.error(
                    f"[table_schema] 列重命名失败: {old_name} -> {new_name}, 错误: {e}"
                )
                all_success = False

    return all_success


def convert_dtype(
    conn: sqlite3.Connection,
    table_name: str,
    column: str,
    from_type: str,
    to_type: str,
) -> bool:
    """类型转换（仅允许无损可逆路径），返回是否成功。

    SQLite 修改列类型需重建表：建新表（目标列新类型）→ CAST 复制 →
    换名，全程包裹事务。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 目标表名。
        column: 要转换的列名。
        from_type: 源类型（TEXT/INTEGER/REAL）。
        to_type: 目标类型（TEXT/INTEGER/REAL）。

    Returns:
        bool: 转换成功返回 True。

    Raises:
        ValueError: 表/列不存在，或转换路径不在白名单。
    """
    if not table_name or not table_name.strip():
        raise ValueError("convert_dtype: table_name 不能为空")
    if not column or not column.strip():
        raise ValueError("convert_dtype: column 不能为空")

    require_table(conn, table_name)

    existing_columns = get_table_columns(conn, table_name)
    if column not in existing_columns:
        raise ValueError(f"convert_dtype: 列不存在: {column}，可用列: {existing_columns}")

    from_upper = str(from_type).upper().strip()
    to_upper = str(to_type).upper().strip()

    if from_upper not in ALLOWED_TYPE_CONVERSIONS:
        raise ValueError(
            f"convert_dtype: 不支持的源类型: {from_upper}，"
            f"允许的源类型: {list(ALLOWED_TYPE_CONVERSIONS.keys())}"
        )
    if to_upper not in ALLOWED_TYPE_CONVERSIONS[from_upper]:
        raise ValueError(
            f"convert_dtype: 不允许的类型转换: {from_upper} -> {to_upper}"
            f"（仅允许无损可逆转换），允许的目标类型: "
            f"{ALLOWED_TYPE_CONVERSIONS[from_upper]}"
        )

    # 读取完整列信息（名称+类型），目标列替换类型
    col_info = conn.execute(
        f"PRAGMA table_info({quote_ident(table_name)})"
    ).fetchall()

    # R6/F6（P3-13）：DDL 类型白名单——col_type 源自 PRAGMA 回读（正常来自
    # pandas to_sql，可信），白名单外类型一律回退 TEXT（纵深防御，告警不中断）；
    # 带长度后缀（VARCHAR(50) 等）取基名判定、保留原文。
    # 白名单＝施工图 9 类＋pandas 实际产出补充（FLOAT/TIMESTAMP/INT，偏差记 REPORT）
    _type_whitelist = {"TEXT", "INTEGER", "REAL", "BLOB", "NUMERIC",
                       "VARCHAR", "DATE", "DATETIME", "BOOLEAN",
                       "FLOAT", "TIMESTAMP", "INT"}
    new_cols_def = []
    for info in col_info:
        col_name = info[1]
        col_type = info[2].upper() if info[2] else "TEXT"
        if col_name == column:
            col_type = to_upper
        if col_type.split("(")[0].strip() not in _type_whitelist:
            logger.warning(
                f"[table_schema] 非白名单列类型回退 TEXT: "
                f"{col_name} 原类型 {col_type}")
            col_type = "TEXT"
        new_cols_def.append(f"{quote_ident(col_name)} {col_type}")

    cols_def = ", ".join(new_cols_def)
    col_names = [info[1] for info in col_info]
    cols_str = quote_ident_list(col_names)

    temp_table = f"__tmp_convert_{table_name}"

    with txn(conn):
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(temp_table)}")
        conn.execute(f"CREATE TABLE {quote_ident(temp_table)} ({cols_def})")
        conn.execute(
            f"INSERT INTO {quote_ident(temp_table)} ({cols_str}) "
            f"SELECT {cols_str} FROM {quote_ident(table_name)}"
        )
        conn.execute(f"DROP TABLE {quote_ident(table_name)}")
        conn.execute(
            f"ALTER TABLE {quote_ident(temp_table)} RENAME TO {quote_ident(table_name)}"
        )

    logger.info(
        f"[table_schema] 类型转换完成: {table_name}.{column} "
        f"{from_upper} -> {to_upper}"
    )
    return True


def get_column_info(
    conn: sqlite3.Connection,
    table_name: str,
) -> List[Dict]:
    """获取列信息 [{"name": str, "type": str}]。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 目标表名。

    Returns:
        List[Dict]: 每项含 "name" 与 "type" 键。

    Raises:
        ValueError: 表名为空或表不存在。
    """
    require_table(conn, table_name)

    col_info = conn.execute(
        f"PRAGMA table_info({quote_ident(table_name)})"
    ).fetchall()

    result = [
        {"name": info[1], "type": info[2] if info[2] else "TEXT"}
        for info in col_info
    ]
    logger.debug(f"[table_schema] 列信息: {table_name} -> {result}")
    return result
