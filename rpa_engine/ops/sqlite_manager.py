"""
rpa_engine/ops/sqlite_manager.py

Layer 0 — SQLite 数据交换模块。

职责（v3.1 修复后收窄）：
- DataFrame ⇄ SQLite 表的数据交换
- 只读 SQL 执行（SELECT/WITH 白名单）

连接生命周期已移交 SessionDB（ops/session_db.py），本模块全部函数
接收共享连接 conn，不再自建连接（修复 N1 红线违规）。

设计要点：
- 全程不使用 pd.read_sql（规约要求必须指定 dtype，而通用表读取无法
  预知列类型）；改为 cursor 取数后构建 DataFrame，既合规又省内存。
- 显式列名查询，禁止 SELECT *（dev-spec §1.1 条 3）。

依赖库：sqlite3（内置）, pandas>=2.0
"""

import gc
import sqlite3
import time
from typing import Any, List, Optional, Sequence, Tuple

import pandas as pd
from loguru import logger

from ops.sql_safety import (
    get_table_columns,
    quote_ident,
    quote_ident_list,
    table_exists,
    txn,
)


def execute_sql(
    sql: str,
    conn: sqlite3.Connection,
    params: Optional[Sequence[Any]] = None,
) -> List[Tuple]:
    """执行只读 SQL（仅 SELECT/WITH），返回结果行列表。

    内部工具，非工作流操作，禁止接入 JSON 参数（R6/F2 标注，2026-09-24）：
    仅供引擎/GUI 内部只读查询使用，未登记 BUILTIN_OPS，已从 ops 包出口除名。

    安全限制：仅允许 SELECT 和 WITH（CTE）查询，禁止任何数据修改语句。

    Args:
        sql: SQL 语句。
        conn: 共享 SQLite 连接。
        params: 参数化查询的参数（元组/列表）。

    Returns:
        List[Tuple]: 查询结果（每行一个 tuple）。

    Raises:
        ValueError: SQL 为空或包含非只读操作。
        sqlite3.Error: SQL 执行失败。
    """
    if not sql or not sql.strip():
        raise ValueError("execute_sql: SQL 语句不能为空")

    sql_upper = sql.strip().upper()
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        raise ValueError("execute_sql: 仅允许 SELECT/WITH 查询，禁止数据修改操作")

    if params:
        rows = conn.execute(sql, tuple(params)).fetchall()
    else:
        rows = conn.execute(sql).fetchall()

    logger.debug(f"[sqlite_manager] SQL 执行完成，返回 {len(rows)} 行")
    return rows


def fetch_dataframe(
    table_name: str,
    conn: sqlite3.Connection,
    columns: Optional[List[str]] = None,
    where_sql: str = "1=1",
    params: Tuple[Any, ...] = (),
) -> pd.DataFrame:
    """从 SQLite 表读取数据为 DataFrame（显式列名，禁 SELECT *）。

    不使用 pd.read_sql：cursor 取数后构建，规避 dtype 预知问题。

    Args:
        table_name: 源表名。
        conn: 共享 SQLite 连接。
        columns: 指定列名列表；None 表示全部列（内部仍显式展开列名）。
        where_sql: WHERE 子句片段（调用方经 build_where 生成），默认 "1=1"。
        params: WHERE 参数元组。

    Returns:
        pd.DataFrame: 查询结果（表为空时返回空 DataFrame）。

    Raises:
        ValueError: 表不存在。
    """
    # 表存在性守卫 + 全列展开（始终显式列名）
    cols = get_table_columns(conn, table_name)
    use_cols = columns if columns else cols

    # 校验指定列有效
    for c in use_cols:
        if c not in cols:
            raise ValueError(
                f"fetch_dataframe: 列不存在: {c}，可用列: {cols}"
            )

    sql = (
        f"SELECT {quote_ident_list(use_cols)} "
        f"FROM {quote_ident(table_name)} WHERE {where_sql}"
    )
    rows = conn.execute(sql, params).fetchall()
    df = pd.DataFrame(rows, columns=use_cols)

    logger.info(
        f"[sqlite_manager] 表读取: {table_name}, {len(df)} 行 × {len(use_cols)} 列"
    )
    return df


def import_dataframe(
    df: pd.DataFrame,
    table_name: str,
    conn: sqlite3.Connection,
    if_exists: str = "replace",
) -> None:
    """将 DataFrame 写入 SQLite 表。

    注意（R11/A-15 注释更正，受理定 G14）：python sqlite3 默认 legacy
    隔离级别下 **DDL 自动提交**，`txn` 的 rollback 无法撤销已执行的
    `DROP TABLE`／`CREATE TABLE`。故本函数的 `replace` 语义**不保证原子性**
    ——需要"要么完整、要么什么都没有"的落库请改用 `import_dataframe_atomic`。
    本函数保留供兼容（签名与行为不变）。

    Args:
        df: 待写入数据。
        table_name: 目标表名。
        conn: 共享 SQLite 连接。
        if_exists: replace（重建）/ append（追加）/ fail（已存在则报错）。

    Raises:
        ValueError: DataFrame 为空或表名为空。
        sqlite3.Error: 写入失败（legacy 隔离级别下 DDL 自动提交，可能残留空壳表）。
    """
    if df is None or df.empty:
        raise ValueError("import_dataframe: DataFrame 为空，无法导入")

    if not table_name or not table_name.strip():
        raise ValueError("import_dataframe: table_name 不能为空")

    with txn(conn):
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)

    logger.info(
        f"[sqlite_manager] DataFrame 导入完成: {table_name}, "
        f"{len(df)} 行 × {len(df.columns)} 列"
    )


def import_dataframe_atomic(
    df: pd.DataFrame,
    table_name: str,
    conn: sqlite3.Connection,
    if_exists: str = "replace",
    tmp_suffix: str = "__tmp_import",
) -> int:
    """R11/A-15（G-5②）：原子导入 = 建临时表 → INSERT → 校验行数 → DROP → RENAME。

    流程（任一步失败都不留半成品）：
        ① 临时表名 = f"{table_name}{tmp_suffix}_{int(time.time()*1000)}"（唯一后缀防撞名）；
        ② `df.to_sql(临时表, ..., if_exists="replace", index=False)`；
        ③ 校验 `table_row_count(临时表) == len(df)`，不符即抛 ValueError；
        ④ 在 `with txn(conn)` 内 `DROP TABLE IF EXISTS <目标表>` 后
           `ALTER TABLE <临时表> RENAME TO <目标表>`；
        ⑤ `except` 分支内 `DROP TABLE IF EXISTS <临时表>`。
    因 legacy 隔离级别下 DDL 自动提交不可回滚，改名前的 DROP 已属"最终提交"，故
    只在临时表**已完整且校验通过**后才执行——失败时旧表毫发无损。

    Args:
        df: 待写入数据。
        table_name: 目标表名。
        conn: 共享 SQLite 连接。
        if_exists: 仅支持 "replace"（原子重建）与 "fail"（目标已存在则报错）。
        tmp_suffix: 临时表名后缀（供测试/定制）。

    Returns:
        int: 写入的数据行数（＝ len(df)）。

    Raises:
        ValueError: 表名为空／DataFrame 为空／if_exists 非法／行数校验不符／
            "fail" 且目标表已存在。
        sqlite3.Error: 任一 SQL 失败（调用方按策略处理）。
    """
    if df is None or df.empty:
        raise ValueError("import_dataframe_atomic: DataFrame 为空，无法导入")
    if not table_name or not table_name.strip():
        raise ValueError("import_dataframe_atomic: table_name 不能为空")
    if if_exists not in ("replace", "fail"):
        raise ValueError(
            f"import_dataframe_atomic: 不支持的 if_exists={if_exists!r}"
            f"（仅支持 'replace'/'fail'；追加语义请用 import_dataframe）")
    if if_exists == "fail" and table_exists(conn, table_name):
        raise ValueError(f"import_dataframe_atomic: 表已存在: {table_name}")

    tmp_name = f"{table_name}{tmp_suffix}_{int(time.time() * 1000)}"
    try:
        with txn(conn):
            df.to_sql(tmp_name, conn, if_exists="replace", index=False)
        n = table_row_count(tmp_name, conn)
        if n != len(df):
            raise ValueError(
                f"import_dataframe_atomic: 行数校验不符，期望 {len(df)}，实际 {n}")
        with txn(conn):
            conn.execute(f"DROP TABLE IF EXISTS {quote_ident(table_name)}")
            conn.execute(
                f"ALTER TABLE {quote_ident(tmp_name)} "
                f"RENAME TO {quote_ident(table_name)}")
    except Exception:
        # 任一步失败都不留半成品（临时表清理失败不掩盖原始异常）
        try:
            with txn(conn):
                conn.execute(f"DROP TABLE IF EXISTS {quote_ident(tmp_name)}")
        except sqlite3.Error as ce:
            logger.warning(
                f"[sqlite_manager] 原子导入失败后清理临时表失败（忽略）: {ce}")
        raise

    logger.info(
        f"[sqlite_manager] 原子导入完成: {table_name}, "
        f"{n} 行 × {len(df.columns)} 列（临时表→改名）"
    )
    return n


def table_row_count(table_name: str, conn: sqlite3.Connection) -> int:
    """获取表行数（COUNT 显式聚合，在 SQL 内完成）。

    Raises:
        ValueError: 表不存在。
    """
    # 表存在性守卫（get_table_columns 会抛出表不存在的明确报错）
    get_table_columns(conn, table_name)
    cursor = conn.execute(
        f"SELECT COUNT(*) FROM {quote_ident(table_name)}"
    )
    return cursor.fetchone()[0]


def cleanup_files(db_path: str) -> None:
    """清理数据库相关文件（.db/.db-wal/.db-shm）——供无 SessionDB 场景兜底。

    会话场景应优先使用 SessionDB.close(keep_db=False)。

    Args:
        db_path: 主数据库文件路径。
    """
    from pathlib import Path

    removed = 0
    for suffix in ("", "-wal", "-shm"):
        file_path = Path(db_path + suffix)
        if file_path.is_file():
            try:
                file_path.unlink()
                removed += 1
            except OSError as e:
                logger.warning(f"[sqlite_manager] 清理失败 {file_path}: {e}")
    if removed:
        logger.info(f"[sqlite_manager] 已清理 {removed} 个数据库相关文件")
    gc.collect()
