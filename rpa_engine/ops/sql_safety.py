"""
rpa_engine/ops/sql_safety.py

Layer 0 — SQL 安全工具模块。

提供标识符安全引用、多条件 WHERE 构建、表存在性守卫和事务上下文管理器，
是所有拼 SQL 的功能函数的统一地基（防止注入与语法错误）。

依赖库：sqlite3（内置）
"""

import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Tuple

from loguru import logger

# 支持的操作符白名单（大写归一后匹配）
SUPPORTED_OPERATORS = {
    "=": "=",
    "!=": "!=",
    "<>": "<>",
    ">": ">",
    "<": "<",
    ">=": ">=",
    "<=": "<=",
    "LIKE": "LIKE",
    "NOT LIKE": "NOT LIKE",
    "IN": "IN",
    "NOT IN": "NOT IN",
    "IS NULL": "IS NULL",
    "IS NOT NULL": "IS NOT NULL",
}

# 禁止出现在标识符中的字符（双引号会破坏引用闭合；控制字符无法安全使用）
_FORBIDDEN_IDENT_CHARS = ('"', "\x00", "\n", "\r", "\t")


def quote_ident(name: str) -> str:
    """安全引用 SQL 标识符（表名/列名），返回双引号包裹形式。

    SQLite 双引号标识符原生支持中文、空格、横线等任意字符，
    因此不再对用户输入做任何改名清洗（所见即所得，D10 决策），
    仅拒绝会破坏 SQL 结构的字符。

    Args:
        name: 原始表名或列名。

    Returns:
        str: 形如 "\"电费 金额\"" 的安全引用。

    Raises:
        ValueError: 名称为空或包含禁止字符。
    """
    if not name or not isinstance(name, str) or not name.strip():
        raise ValueError("quote_ident: 标识符不能为空")

    for ch in _FORBIDDEN_IDENT_CHARS:
        if ch in name:
            raise ValueError(
                f"quote_ident: 标识符包含禁止字符 {repr(ch)}: {name!r}"
            )

    # 双引号内的字面双引号按 SQL 标准转义为两个双引号（防御性，正常已被上面拦截）
    escaped = name.replace('"', '""')
    return f'"{escaped}"'


def quote_ident_list(names: List[str]) -> str:
    """批量引用标识符列表，返回逗号连接的 SQL 片段。"""
    return ", ".join(quote_ident(n) for n in names)


def build_where(
    conditions: List[Dict[str, Any]],
    logic: str = "AND",
) -> Tuple[str, Tuple[Any, ...]]:
    """将条件字典列表构建为参数化 WHERE 子句。

    支持多条件组合（AND/OR），操作符走白名单校验，
    值全部经参数占位符传递，防止 SQL 注入。

    Args:
        conditions: 条件列表，每项 {"column": str, "op": str, "value": any}。
            value 仅在 IN/NOT IN 时要求为非空列表；IS NULL/IS NOT NULL 时忽略。
        logic: 条件间连接词，"AND" 或 "OR"。

    Returns:
        Tuple[str, Tuple[Any, ...]]: (where_sql, params)。
            conditions 为空时返回 ("1=1", ())，便于无条件场景统一拼接。

    Raises:
        ValueError: 条件格式不合法、操作符不支持或 logic 非法。
    """
    if logic not in ("AND", "OR"):
        raise ValueError(f"build_where: logic 必须为 'AND' 或 'OR'，当前值: {logic}")

    if not conditions:
        return "1=1", ()

    if not isinstance(conditions, list):
        raise ValueError(
            f"build_where: conditions 必须为列表类型，当前类型: {type(conditions)}"
        )

    clauses: List[str] = []
    params: List[Any] = []

    for cond in conditions:
        if not isinstance(cond, dict):
            raise ValueError(f"build_where: 每个条件必须为字典，当前: {cond!r}")

        column = cond.get("column", "")
        op = str(cond.get("op", "")).strip().upper()
        value = cond.get("value")

        if not column:
            raise ValueError("build_where: condition.column 不能为空")
        if not op:
            raise ValueError("build_where: condition.op 不能为空")

        if op not in SUPPORTED_OPERATORS:
            raise ValueError(
                f"build_where: 不支持的操作符 '{op}'，"
                f"支持的操作符: {sorted(SUPPORTED_OPERATORS.keys())}"
            )

        sql_op = SUPPORTED_OPERATORS[op]
        col_ref = quote_ident(column)

        # IS NULL / IS NOT NULL 无参数
        if op in ("IS NULL", "IS NOT NULL"):
            clauses.append(f"{col_ref} {sql_op}")
            continue

        # IN / NOT IN 要求非空列表值（R11/B-14：标量误用时给中文提示，不改写）
        if op in ("IN", "NOT IN"):
            if not isinstance(value, (list, tuple)):
                raise ValueError(
                    f"build_where: '{op}' 需要多个值，请用逗号分隔，列: {column}"
                )
            if len(value) == 0:
                raise ValueError(
                    f"build_where: '{op}' 需要多个值，请用逗号分隔（不能为空），"
                    f"列: {column}"
                )
            placeholders = ", ".join(["?"] * len(value))
            clauses.append(f"{col_ref} {sql_op} ({placeholders})")
            params.extend(value)
            continue

        # 标准比较操作符（R6/F6-P3-13：LIKE 值转义 %/_ 通配符，按字面匹配）
        if op in ("LIKE", "NOT LIKE") and isinstance(value, str):
            escaped = (value.replace("\\", "\\\\")
                            .replace("%", "\\%")
                            .replace("_", "\\_"))
            clauses.append(f"{col_ref} {sql_op} ? ESCAPE '\\'")
            params.append(escaped)
            continue
        clauses.append(f"{col_ref} {sql_op} ?")
        params.append(value)

    return f" {logic} ".join(clauses), tuple(params)


def require_table(conn: sqlite3.Connection, table_name: str) -> None:
    """表存在性守卫：不存在时抛出带可用表清单的 ValueError。

    Args:
        conn: 共享 SQLite 连接。
        table_name: 目标表名。

    Raises:
        ValueError: 表名为空或表不存在。
    """
    if not table_name or not table_name.strip():
        raise ValueError("require_table: 表名不能为空")

    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    if cursor.fetchone() is None:
        # R6/B1（P0-2）：内部物理表名清单只进日志（排查用），异常文本
        # 人话化（GUI 出口再经 error_messages 翻译层）
        logger.warning(
            f"[sql_safety] 表不存在: {table_name}，"
            f"当前可用表: {list_tables(conn)}")
        raise ValueError("步骤使用的数据表不存在")


# R6/D6（P2-10）：建索引行数门槛——超过才为匹配/分组/分区列建索引
# （小表建索引反而多花一步；会话库即用即抛，索引无清理负担）。
# 测试可经 sql_safety.INDEX_ROW_THRESHOLD 临时调整（模块属性引用）。
INDEX_ROW_THRESHOLD = 50_000


def ensure_index(conn: sqlite3.Connection, table_name: str, columns) -> None:
    """为指定表的指定列条件性建立普通索引（行数 > INDEX_ROW_THRESHOLD）。

    JOIN/GROUP BY/PARTITION BY 重负载路径无索引即全表扫（评估 P2-10）。
    幂等：IF NOT EXISTS＋固定索引名 idx_{table}_{col}；标识符一律
    quote_ident。表不存在/查询失败时静默返回（不干扰主流程）。
    """
    if not columns:
        return
    try:
        n = conn.execute(
            f"SELECT COUNT(*) FROM {quote_ident(table_name)}").fetchone()[0]
    except sqlite3.Error:
        return
    if n <= INDEX_ROW_THRESHOLD:
        return
    for col in columns:
        idx = f"idx_{table_name}_{col}"
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS {quote_ident(idx)} "
            f"ON {quote_ident(table_name)}({quote_ident(col)})")


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """检查表是否存在于数据库中（conn 版本）。"""
    if not table_name or not table_name.strip():
        raise ValueError("table_exists: 表名不能为空")

    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def list_tables(conn: sqlite3.Connection) -> List[str]:
    """列出数据库中所有用户表（排除 sqlite_ 系统表）。"""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [row[0] for row in cursor.fetchall()]


def get_table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    """获取表的列名列表（conn 版本）。

    Raises:
        ValueError: 表名非字符串、为空，或表不存在。
    """
    if not isinstance(table_name, str) or not table_name or not table_name.strip():
        raise ValueError("get_table_columns: 表名不能为空")

    cursor = conn.execute(f"PRAGMA table_info({quote_ident(table_name)})")
    col_info = cursor.fetchall()
    if not col_info:
        # PRAGMA 对不存在的表返回空，与"列名为空"区分报错
        raise ValueError(f"get_table_columns: 表不存在: {table_name}")
    return [info[1] for info in col_info]


@contextmanager
def txn(conn: sqlite3.Connection) -> Generator[sqlite3.Connection, None, None]:
    """写操作事务上下文管理器：正常退出 commit，异常回滚。

    用法：
        with txn(conn) as c:
            c.execute("INSERT ...", params)

    说明：
    - sqlite3 默认隔离级别下 execute 即隐式开事务，此处显式收口
      commit/rollback，满足 dev-spec §1.1 条 6"写操作必须包裹在事务中"。
    - 回滚后异常继续向上抛出，由调用方决定异常策略（stop/skip/retry）。
    """
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        logger.warning("[sql_safety] 事务回滚")
        raise
