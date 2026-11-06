"""
rpa_engine/engine/parser.py

JSON 参数文件解析模块（v3.1 定稿）。

v3.1 schema（数据表驱动，自 v3 预设步骤架构迭代而来）：
{
  "__meta": {"schema_version": "3.1", "created": "..."},
  "name": "本轮操作",
  "global": {"keep_db": false},
  "tables": [                      # 阶段1确认导入的数据表（含复现信息）
    {"table_id": "T1", "alias": "电费表-sheet_1月",
     "source": {"file": "...xlsx", "sheet": "1月", "header_row": 1},
     "sqlite_table": "t1"}
  ],
  "steps": [                       # 阶段2配置的操作（每步必含目标表编号）
    {"step_id": "S1", "type": "filter", "name": "筛选大额",
     "target_table_id": "T1", "params": {...},
     "output_table_id": "T5",       # 可选：派生表编号（后续步骤可引用）
     "on_error": "stop", "retry_count": 3}
  ]
}

D4 决策：v3 旧格式（workflow{} 包裹）不再兼容执行，遇旧格式明确报错。
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

from loguru import logger


class ParserError(Exception):
    """参数文件解析异常。"""
    pass


@dataclass
class StepDef:
    """单个步骤定义。"""

    step_id: str = ""
    type: str = ""                 # BUILTIN_OPS 操作名
    name: str = ""
    target_table_id: str = ""      # 操作目标数据表编号
    output_table_id: str = ""      # 派生表编号（可选，供后续步骤引用）
    params: Dict[str, Any] = field(default_factory=dict)
    on_error: str = "stop"
    retry_count: int = 3


@dataclass
class TableDef:
    """数据表定义（阶段 1 确认导入时生成）。"""

    table_id: str = ""             # 编号（T1, T2, ...）
    alias: str = ""                # 别名（面向用户显示）
    source: Dict[str, Any] = field(default_factory=dict)  # file/sheet/header_row
    sqlite_table: str = ""         # SQLite 表名


# R6/E2（P1-3）：受支持的参数文件版本白名单（parse_workflow 版本门禁
# 消费；此前 schema_version 读入后全库零判定，未知版本静默按 3.1 执行）
_SUPPORTED_SCHEMA_VERSIONS = {"3.1"}


@dataclass
class WorkflowDef:
    """工作流定义。"""

    name: str = "未命名操作"
    schema_version: str = "3.1"
    global_config: Dict[str, Any] = field(default_factory=dict)
    tables: List[TableDef] = field(default_factory=list)
    steps: List[StepDef] = field(default_factory=list)


def parse_workflow(file_path: str) -> WorkflowDef:
    """解析 v3.1 JSON 参数文件。

    Args:
        file_path: JSON 参数文件路径。

    Returns:
        WorkflowDef: 解析后的工作流定义。

    Raises:
        ParserError: 文件不存在、JSON 格式错误、v3 旧格式或结构不符合 v3.1 规范。
    """
    import os

    if not os.path.isfile(file_path):
        raise ParserError(f"参数文件不存在: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ParserError(f"JSON 格式错误: {e}")
    except OSError as e:
        raise ParserError(f"文件读取失败: {e}")

    if not isinstance(data, dict):
        raise ParserError("参数文件根节点必须为对象")

    # D4：v3 旧格式明确拒绝
    if "workflow" in data and "tables" not in data:
        raise ParserError(
            "检测到 v3 旧格式参数文件（workflow 包裹结构）。"
            "v3.1 采用数据表驱动（tables + steps 结构），旧文件不再支持执行；"
            "请在 GUI 中重新配置（阶段 1 选择数据表 → 阶段 2 配置操作）。"
        )

    if "tables" not in data:
        raise ParserError("缺少 tables 字段（v3.1 参数文件必须声明数据表清单）")
    if "steps" not in data:
        raise ParserError("缺少 steps 字段（v3.1 参数文件必须声明操作步骤清单）")

    meta = data.get("__meta", {})
    # R6/E2（P1-3）：版本门禁——键缺失按缺省 "3.1" 放行（兼容现状）；
    # 显式给出的版本必须为字符串且落在白名单（数字型/空串/"3.10" 一律人话拒绝）
    if "schema_version" in meta:
        raw_version = meta.get("schema_version")
        if not isinstance(raw_version, str):
            raise ParserError(
                f"参数文件版本号格式非法（schema_version={raw_version!r}）；"
                '版本号必须写成字符串 "3.1"，不能写数字或其它类型。'
                "请在 GUI 中重新生成参数文件"
            )
        version = raw_version
    else:
        version = "3.1"
    if version not in _SUPPORTED_SCHEMA_VERSIONS:
        raise ParserError(
            f"不支持的文件版本（schema_version={version}；本程序支持 "
            f"{'/'.join(sorted(_SUPPORTED_SCHEMA_VERSIONS))}）。"
            "该文件由更新版本的程序生成，请升级程序后再打开"
        )

    workflow = WorkflowDef(
        name=str(data.get("name", "未命名操作")),
        schema_version=version,
        global_config=dict(data.get("global", {})),
    )

    # ---- tables 解析 ----
    raw_tables = data.get("tables", [])
    if not isinstance(raw_tables, list):
        raise ParserError("tables 必须为数组")

    for i, t in enumerate(raw_tables):
        if not isinstance(t, dict):
            raise ParserError(f"tables[{i}] 必须为对象")
        table_id = str(t.get("table_id", "")).strip()
        if not table_id:
            raise ParserError(f"tables[{i}] 缺少 table_id")
        workflow.tables.append(TableDef(
            table_id=table_id,
            alias=str(t.get("alias", table_id)),
            source=dict(t.get("source", {})),
            sqlite_table=str(t.get("sqlite_table", table_id.lower())),
        ))

    # ---- steps 解析 ----
    raw_steps = data.get("steps", [])
    if not isinstance(raw_steps, list):
        raise ParserError("steps 必须为数组")

    for i, s in enumerate(raw_steps):
        if not isinstance(s, dict):
            raise ParserError(f"steps[{i}] 必须为对象")
        step_id = str(s.get("step_id", "")).strip()
        op_type = str(s.get("type", "")).strip()
        target = str(s.get("target_table_id", "")).strip()
        if not step_id:
            raise ParserError(f"steps[{i}] 缺少 step_id")
        if not op_type:
            raise ParserError(f"steps[{i}] 缺少 type")
        if not target:
            raise ParserError(
                f"步骤 [{step_id}] 缺少 target_table_id（必须声明本步骤操作哪张数据表）"
            )
        on_error = str(s.get("on_error", "stop"))
        if on_error not in ("stop", "skip", "retry"):
            raise ParserError(
                f"步骤 [{step_id}] on_error 非法: {on_error}（允许 stop/skip/retry）"
            )
        workflow.steps.append(StepDef(
            step_id=step_id,
            type=op_type,
            name=str(s.get("name", op_type)),
            target_table_id=target,
            output_table_id=str(s.get("output_table_id", "")).strip(),
            params=dict(s.get("params", {})),
            on_error=on_error,
            retry_count=int(s.get("retry_count", 3)),
        ))

    logger.info(
        f"[parser] 解析完成: {workflow.name} "
        f"（{len(workflow.tables)} 表, {len(workflow.steps)} 步, schema {version}）"
    )
    return workflow
