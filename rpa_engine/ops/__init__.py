"""
rpa_engine/ops/__init__.py

操作层（ops）模块 — L0 基础设施 + L1 表操作 + L2 业务操作 + L3 集成。

Layer 0（基础设施层）：
  - sql_safety: SQL 安全工具（标识符引用、条件构建、事务、表守卫）
  - session_db: 会话数据库管理器（唯一连接创建点，WAL）
  - excel_preprocessor: Excel 预处理（复制、格式转换、扫描、表头行读取）
  - sqlite_manager: SQLite 数据交换（DataFrame 导入导出、只读 SQL）

Layer 1（表操作层，引擎内部复用，不进用户操作目录）：
  - table_importer: Excel → SQLite 导入
  - table_lifecycle: 表生命周期（创建、删除、复制、合并）
  - table_schema: 表结构（列重命名、类型转换、列信息）
  - table_content: 表内容（行级增删改查）

Layer 2（业务操作层 = 用户操作目录）：
  - filter_dedup: 条件筛选 + 条件去重
  - mapping_matcher: 跨表映射匹配（SQL JOIN）
  - aggregator: 条件统计（GROUP BY 聚合）
  - exporter: 结果导出（流式 xlsx）

Layer 3（集成层）：
  - step_executor: BUILTIN_OPS 用户操作目录 + execute_step 单步执行
    （table_id 翻译、参数白名单、输出表自动命名）

所有函数均为纯函数式操作（接收共享 conn），不自行创建连接。
"""

from ops.sql_safety import (
    SUPPORTED_OPERATORS,
    build_where,
    get_table_columns,
    list_tables,
    quote_ident,
    quote_ident_list,
    require_table,
    table_exists,
    txn,
)
from ops.session_db import SessionDB
from ops.excel_preprocessor import (
    clean_alias_name,
    ensure_xlsx,
    read_excel_sheet,
    scan_sheets,
    validate_and_copy,
)
from ops.sqlite_manager import (
    import_dataframe,
    table_row_count,
)
from ops.table_importer import import_excel_table
from ops.table_lifecycle import (
    copy_table,
    delete_table,
    merge_tables,
)
from ops.table_schema import (
    ALLOWED_TYPE_CONVERSIONS,
    convert_dtype,
    rename_columns,
)
from ops.filter_dedup import dedup_table, filter_table
from ops.mapping_matcher import JOIN_MODES, match_tables
from ops.aggregator import AGG_FUNCTIONS, aggregate_table
from ops.exporter import export_table
from ops.step_executor import BUILTIN_OPS, execute_step, get_op_func, list_ops

__all__ = [
    # L0 sql_safety
    "SUPPORTED_OPERATORS",
    "build_where",
    "get_table_columns",
    "list_tables",
    "quote_ident",
    "quote_ident_list",
    "require_table",
    "table_exists",
    "txn",
    # L0 session_db
    "SessionDB",
    # L0 excel_preprocessor
    "clean_alias_name",
    "ensure_xlsx",
    "read_excel_sheet",
    "scan_sheets",
    "validate_and_copy",
    # L0 sqlite_manager
    # R6/F2（P3-2）：cleanup_files / execute_sql / fetch_dataframe 已从公共
    # 出口除名（execute_sql 为内部工具，非工作流操作，禁止接入 JSON 参数）。
    "import_dataframe",
    "table_row_count",
    # L1 table_importer
    "import_excel_table",
    # L1 table_lifecycle
    # R6/F2：create_table 已除名（引擎内部经 table_lifecycle 直连使用）。
    "copy_table",
    "delete_table",
    "merge_tables",
    # L1 table_schema
    # R6/F2：get_column_info 已除名。
    "ALLOWED_TYPE_CONVERSIONS",
    "convert_dtype",
    "rename_columns",
    # L1 table_content
    # R6/F2：delete_rows / insert_rows / query_rows / update_rows 已除名
    # （行级 CRUD 为死 API，BUILTIN_OPS 未登记；生产写入唯一通道＝
    # table_importer / sqlite_manager.import_dataframe）。
    # L2 业务操作
    "dedup_table",
    "filter_table",
    "JOIN_MODES",
    "match_tables",
    "AGG_FUNCTIONS",
    "aggregate_table",
    "export_table",
    # L3 集成
    "BUILTIN_OPS",
    "execute_step",
    "get_op_func",
    "list_ops",
]
