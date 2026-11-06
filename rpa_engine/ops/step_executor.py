"""
rpa_engine/ops/step_executor.py

Layer 3 — 步骤执行集成层。

职责：
- BUILTIN_OPS：用户操作目录注册表（仅暴露文员可理解的业务操作，
  D3 决策全量进目录；L1 行级 CRUD 属引擎内部能力，不进用户目录）
- execute_step()：单步执行入口，完成 table_id → sqlite 表名 翻译、
  参数白名单过滤、输出表自动命名（D6：t_s{步骤序号}；GUI 链路经
  params.output_table 固化为 t_{uid}（M5-a），t_s{n} 仅外部手写 JSON 缺省回退）

与 engine/executor.py 的职责边界（修复首轮断链 #2/#4）：
- engine/executor.py：工作流编排器（连接管理、数据源加载、步骤循环、
  异常策略、资源清理），唯一调用本模块的 execute_step
- 本模块：单步翻译与分发，不感知工作流全局状态

依赖库：sqlite3（内置）
"""

import copy
import sqlite3
import time
from typing import Any, Callable, Dict, List, Optional, Set

import psutil
from loguru import logger

from ops.filter_dedup import filter_table, dedup_table
from ops.mapping_matcher import match_tables
from ops.aggregator import aggregate_table
from ops.exporter import export_table
from ops.supervision_report import build_supervision_report
from ops.table_lifecycle import copy_table, merge_tables
from ops.table_schema import rename_columns, convert_dtype


# ---------------------------------------------------------------------------
# 用户操作目录（D3：全量进目录；项数见 gui.models.STEP_COUNT）
# 每项声明（R15 定稿字段集）：
#   func            操作函数
#   description     中文说明（GUI 目录展示）
#   output          是否产出输出表（True 时缺省自动命名 t_s{n}；GUI 链路经
#                   params.output_table 固化为 t_{uid}（M5-a），t_s{n} 仅外部
#                   手写 JSON 缺省回退）
#   param_keys      参数白名单（防 **params 混入保留键，如 conn）
#   params_schema   参数契约（**唯一源**，R15/B-64）：逐键声明
#                   key/type/required/default；GUI default_params() 与
#                   execute_step 的缺省回退**均派生于此**（R15/B-69/B-41）
#   extra_input_min 除目标表外的最小额外输入表数（R15/B-63）
#   overwritable    可否覆盖原表（R15/B-65；表单「结果保存方式」挂载依据）
#   deprecated      功能级弃用（R15/B-53；engine/validator 拒绝已弃用 type）
# 注（R15/B-62）：原 target_param／match_param 两休眠字段（零消费者、grep
# 证实）已按人工裁定**删除**——"启用为字段驱动"会与既裁 P2-2「不改 9 分支
# 结构」冲突；语义信息保留于各分支 call_args 组装处（见 execute_step）。
# ---------------------------------------------------------------------------

# GUI 注入参数键（前端表单不填、用户不可见；由 gui.models.to_dict 固化为
# 物理表名 t_{uid} 或经 output_table 参数传入引擎，R15/B-59 判据之一）
GUI_INJECTED_PARAM_KEYS: Set[str] = {"output_table"}

BUILTIN_OPS: Dict[str, Dict[str, Any]] = {
    # L2 业务操作（查的范畴）
    "filter": {
        "func": filter_table, "description": "条件筛选",
        "output": True,
        "param_keys": {"conditions", "logic", "output_table"},
        "params_schema": [
            {"key": "conditions", "type": "list", "required": False,
             "default": []},
            {"key": "logic", "type": "enum", "required": False,
             "default": "AND"},
        ],
        "extra_input_min": 0,
        "overwritable": True,
        "deprecated": False,
    },
    "dedup": {
        "func": dedup_table, "description": "条件去重",
        "output": True,
        "param_keys": {"key_columns", "keep", "output_table"},
        "params_schema": [
            {"key": "key_columns", "type": "list", "required": False,
             "default": []},
            {"key": "keep", "type": "enum", "required": False,
             "default": "first"},
        ],
        "extra_input_min": 0,
        "overwritable": True,
        "deprecated": False,
    },
    "mapping_match": {
        "func": match_tables, "description": "跨表映射匹配",
        "output": True,
        "param_keys": {"match_table_id", "match_columns", "mode",
                       "output_table"},
        "params_schema": [
            # R15/B-41：缺省由 inner_join 改为 left_join——原值会**静默丢弃**
            # 主表未匹配行（"界面说成功、数据变少"类高危），且与界面默认
            # 及文档记录表相反；现与 GUI 同源
            {"key": "match_table_id", "type": "text", "required": True,
             "default": ""},
            {"key": "match_columns", "type": "dict", "required": False,
             "default": {}},
            {"key": "mode", "type": "enum", "required": False,
             "default": "left_join"},
        ],
        "extra_input_min": 2,
        "overwritable": False,
        "deprecated": False,
    },
    "aggregate": {
        "func": aggregate_table, "description": "条件统计",
        "output": True,
        "param_keys": {"group_by", "metrics", "conditions", "output_table"},
        "params_schema": [
            {"key": "group_by", "type": "list", "required": False,
             "default": []},
            {"key": "metrics", "type": "list", "required": False,
             "default": []},
            {"key": "conditions", "type": "list", "required": False,
             "default": []},
        ],
        "extra_input_min": 0,
        "overwritable": False,
        "deprecated": False,
    },
    "export": {
        "func": export_table, "description": "结果导出",
        "output": False,
        "param_keys": {"output_path", "sheet_name"},
        "params_schema": [
            {"key": "output_path", "type": "text", "required": True,
             "default": ""},
            {"key": "sheet_name", "type": "text", "required": False,
             "default": "数据"},
        ],
        "extra_input_min": 0,
        "overwritable": False,
        "deprecated": False,
    },
    "supervision_report": {
        "func": build_supervision_report, "description": "履职表单抽查报告",
        "output": False,
        "param_keys": {"output_path", "workday_count", "extra_table_ids"},
        "params_schema": [
            {"key": "output_path", "type": "text", "required": True,
             "default": ""},
            {"key": "workday_count", "type": "integer", "required": False,
             "default": 0},
            {"key": "extra_table_ids", "type": "list", "required": False,
             "default": []},
        ],
        "extra_input_min": 0,
        "overwritable": False,
        "deprecated": False,
    },
    # 表级直观操作（D3 追加 4 项）
    "merge_tables": {
        "func": merge_tables, "description": "数据表合并",
        "output": True,
        "param_keys": {"match_table_ids", "output_table"},
        "params_schema": [
            {"key": "match_table_ids", "type": "list", "required": True,
             "default": []},
        ],
        "extra_input_min": 2,
        "overwritable": False,
        "deprecated": False,
    },
    "copy_table": {
        "func": copy_table, "description": "数据表复制",
        "output": True,
        "param_keys": {"output_table"},
        "params_schema": [],
        "extra_input_min": 0,
        "overwritable": False,
        "deprecated": False,
    },
    "rename_columns": {
        "func": rename_columns, "description": "表头名称修改",
        "output": False,
        "param_keys": {"mapping"},
        "params_schema": [
            {"key": "mapping", "type": "dict", "required": True,
             "default": {}},
        ],
        "extra_input_min": 0,
        "overwritable": False,
        "deprecated": False,
    },
    "convert_dtype": {
        "func": convert_dtype, "description": "数据类型转换",
        "output": False,
        "param_keys": {"column", "from_type", "to_type"},
        "params_schema": [
            {"key": "column", "type": "text", "required": True,
             "default": ""},
            # R15/B-41：原回退为空串会使 convert_dtype **必然报错**
            # （空串不在 ALLOWED_TYPE_CONVERSIONS 内），现与 GUI 同源
            {"key": "from_type", "type": "enum", "required": True,
             "default": "TEXT"},
            {"key": "to_type", "type": "enum", "required": True,
             "default": "INTEGER"},
        ],
        "extra_input_min": 0,
        "overwritable": False,
        "deprecated": False,
    },
}


def param_schema(op_type: str) -> List[Dict[str, Any]]:
    """该操作的参数契约（R15/B-64 单一源）；未知操作返回空列表。"""
    return BUILTIN_OPS.get(op_type, {}).get("params_schema", [])


def param_default(op_type: str, key: str) -> Any:
    """该操作某参数键的默认值（R15/B-41／B-69：GUI 与引擎的唯一来源）。

    返回**深拷贝**：调用方就地修改（如 append）时不会污染共享默认对象。
    """
    for p in param_schema(op_type):
        if p["key"] == key:
            return copy.deepcopy(p["default"])
    return None


def param_defaults(op_type: str) -> Dict[str, Any]:
    """该操作全部参数的默认值字典（供 gui.models.default_params 派生）。"""
    return {p["key"]: copy.deepcopy(p["default"]) for p in param_schema(op_type)}


def list_ops() -> List[str]:
    """返回用户操作目录全部操作名。"""
    return sorted(BUILTIN_OPS.keys())


def get_op_func(op_name: str) -> Optional[Callable]:
    """按操作名查找函数；未找到返回 None。"""
    entry = BUILTIN_OPS.get(op_name)
    return entry["func"] if entry else None


def _translate_table_id(
    table_id: str,
    table_id_map: Dict[str, str],
    context: str,
) -> str:
    """将表编号 ID 翻译为 sqlite 表名；未注册的 ID 报错。"""
    if table_id not in table_id_map:
        raise ValueError(
            f"{context}: 数据表编号 '{table_id}' 未定义，"
            f"当前可用: {sorted(table_id_map.keys())}"
        )
    return table_id_map[table_id]


def execute_step(
    step_config: Dict[str, Any],
    conn: sqlite3.Connection,
    table_id_map: Dict[str, str],
    step_index: int,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """执行单个步骤：ID 翻译 → 参数白名单过滤 → 分发执行。

    Args:
        step_config: 步骤配置 {"step_id", "type", "name",
            "target_table_id", "params", ...}。
        conn: 共享 SQLite 连接（D8）。
        table_id_map: 表编号映射 {"T1": "t1", ...}（含已注册的派生表）。
        step_index: 步骤序号（1 起始），用于输出表自动命名 t_s{n}（D6）；
            GUI 链路经 params.output_table 优先并固化为 t_{uid}（M5-a）。

    Returns:
        Dict[str, Any]: {"success": bool, "message": str,
            "output_table": Optional[str], "output_table_id": Optional[str]}。
            output_table 为实际产出的 sqlite 表名（无输出操作为 None）；
            output_table_id 回显步骤声明的派生表编号（供引擎注册映射）。
    """
    step_id = step_config.get("step_id", "unknown")
    step_name = step_config.get("name", "")
    op_type = step_config.get("type", "")
    params = dict(step_config.get("params") or {})

    logger.info(
        f"[step_executor] 步骤 [{step_id}] {step_name} 开始（操作: {op_type}）"
    )

    def fail(msg: str) -> Dict[str, Any]:
        return {
            "success": False,
            "message": f"步骤 [{step_id}] {step_name}: {msg}",
            "output_table": None,
            "output_table_id": None,
        }

    entry = BUILTIN_OPS.get(op_type)
    if entry is None:
        return fail(
            f"操作类型 '{op_type}' 未定义，可用操作: {list_ops()}"
        )

    # ---- 1. ID 翻译 ----
    target_table_id = step_config.get("target_table_id", "")
    if not target_table_id:
        return fail("缺少 target_table_id（本步骤操作哪张数据表）")

    try:
        target_table = _translate_table_id(
            target_table_id, table_id_map, f"步骤 [{step_id}]"
        )
    except ValueError as e:
        return fail(str(e))

    # ---- 2. 参数白名单过滤（防混入 conn 等保留键）----
    clean_params = {k: v for k, v in params.items() if k in entry["param_keys"]}
    # R6/E3（P2-6）：丢弃键记日志（排查"参数怎么没生效"；此前静默丢弃）
    _dropped = set(params) - set(clean_params)
    if _dropped:
        logger.debug(
            f"[step_executor] [{step_id}] 丢弃非白名单参数键: {sorted(_dropped)}")

    # ---- 3. 输出表名确定（D6：t_s{步骤序号} 自动命名；GUI 链路经
    #       params.output_table 固化为 t_{uid}——M5-a，t_s{n} 仅缺省回退）----
    output_table = None
    if entry["output"]:
        output_table = clean_params.pop("output_table", None) or f"t_s{step_index}"

    # ---- 4. 按操作类型组装函数入参 ----
    # R15/B-41＋B-69：各分支的**缺省回退一律取自 params_schema**（唯一源），
    # 与 gui.models.default_params 同源——手写 JSON 省略参数键时行为与界面一致
    call_args: Dict[str, Any] = {"conn": conn}

    if op_type == "filter":
        call_args.update(
            table_name=target_table,
            conditions=(clean_params.get("conditions")
                        or param_default("filter", "conditions")),
            output_table=output_table,
            logic=clean_params.get("logic",
                                   param_default("filter", "logic")),
        )
    elif op_type == "dedup":
        call_args.update(
            table_name=target_table,
            key_columns=(clean_params.get("key_columns")
                         or param_default("dedup", "key_columns")),
            keep=clean_params.get("keep", param_default("dedup", "keep")),
            output_table=output_table,
        )
    elif op_type == "mapping_match":
        match_table_id = clean_params.get(
            "match_table_id", param_default("mapping_match", "match_table_id"))
        if not match_table_id:
            return fail("缺少 match_table_id（匹配哪张数据表）")
        try:
            right_table = _translate_table_id(
                match_table_id, table_id_map, f"步骤 [{step_id}]"
            )
        except ValueError as e:
            return fail(str(e))
        call_args.update(
            left_table=target_table,
            right_table=right_table,
            match_columns=(clean_params.get("match_columns")
                           or param_default("mapping_match", "match_columns")),
            mode=clean_params.get("mode",
                                  param_default("mapping_match", "mode")),
            output_table=output_table,
        )
    elif op_type == "aggregate":
        call_args.update(
            table_name=target_table,
            group_by=(clean_params.get("group_by")
                      or param_default("aggregate", "group_by")),
            metrics=(clean_params.get("metrics")
                     or param_default("aggregate", "metrics")),
            output_table=output_table,
            conditions=(clean_params.get("conditions")
                        or param_default("aggregate", "conditions")),
        )
    elif op_type == "export":
        output_path = clean_params.get("output_path",
                                       param_default("export", "output_path"))
        if not output_path:
            return fail("缺少 output_path（导出到哪里）")
        call_args.update(
            table_name=target_table,
            output_path=output_path,
            sheet_name=clean_params.get("sheet_name",
                                        param_default("export", "sheet_name")),
            # R6/D1（P1-4）：长导出循环内取消检查（仅此分支＋导入链传递，
            # 不改 9 分支结构——P2-2 属功能函数批排除）
            cancel_check=cancel_check,
        )
    elif op_type == "supervision_report":
        output_path = clean_params.get(
            "output_path", param_default("supervision_report", "output_path"))
        if not output_path:
            return fail("缺少 output_path（报告保存位置）")
        extra_ids = (clean_params.get("extra_table_ids")
                     or param_default("supervision_report", "extra_table_ids"))
        extra_tables = []
        for eid in extra_ids:
            try:
                extra_tables.append(
                    _translate_table_id(eid, table_id_map, f"步骤 [{step_id}]")
                )
            except ValueError as e:
                return fail(str(e))
        call_args.update(
            table_name=target_table,
            output_path=output_path,
            workday_count=(clean_params.get("workday_count")
                           or param_default("supervision_report", "workday_count")),
            extra_tables=extra_tables,
        )
    elif op_type == "merge_tables":
        # 主表在前，其余匹配表 ID 逐一翻译
        other_ids = (clean_params.get("match_table_ids")
                     or param_default("merge_tables", "match_table_ids"))
        other_tables = []
        for oid in other_ids:
            try:
                other_tables.append(
                    _translate_table_id(oid, table_id_map, f"步骤 [{step_id}]")
                )
            except ValueError as e:
                return fail(str(e))
        call_args.update(
            table_names=[target_table] + other_tables,
            dst_table=output_table,
        )
    elif op_type == "copy_table":
        call_args.update(
            src_table=target_table,
            dst_table=output_table,
        )
    elif op_type == "rename_columns":
        call_args.update(
            table_name=target_table,
            mapping=(clean_params.get("mapping")
                     or param_default("rename_columns", "mapping")),
        )
    elif op_type == "convert_dtype":
        call_args.update(
            table_name=target_table,
            column=clean_params.get("column",
                                    param_default("convert_dtype", "column")),
            from_type=clean_params.get(
                "from_type", param_default("convert_dtype", "from_type")),
            to_type=clean_params.get(
                "to_type", param_default("convert_dtype", "to_type")),
        )

    # ---- 5. 执行 ----
    try:
        t0 = time.time()
        entry["func"](**call_args)
        elapsed = time.time() - t0
        mem_mb = psutil.Process().memory_info().rss / 1024 / 1024
        logger.info(
            f"[step_executor] 步骤 [{step_id}] 完成, "
            f"耗时: {elapsed:.2f}s, 内存: {mem_mb:.1f}MB"
        )
        return {
            "success": True,
            "message": f"步骤 [{step_id}] {step_name} 执行成功",
            "output_table": output_table,
            "output_table_id": step_config.get("output_table_id") or None,
        }
    except (ValueError, sqlite3.Error) as e:
        logger.error(
            f"[step_executor] 步骤 [{step_id}] 失败: {type(e).__name__}: {e}"
        )
        return fail(f"{type(e).__name__}: {e}")
    except Exception as e:
        logger.error(
            f"[step_executor] 步骤 [{step_id}] 异常: {type(e).__name__}: {e}"
        )
        return fail(f"未预期异常 {type(e).__name__}: {e}")
