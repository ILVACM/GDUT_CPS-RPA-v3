"""
rpa_engine/engine/__init__.py

引擎核心模块（v3.1 定稿）。

导出：
- parse_workflow / ParserError      参数文件解析
- validate_workflow / ValidationError 全量校验
- execute_workflow / ExecutionError 工作流编排执行
- BUILTIN_OPS / get_op_func / list_ops 用户操作目录接口
"""

from engine.parser import (
    ParserError,
    StepDef,
    TableDef,
    WorkflowDef,
    parse_workflow,
)
from engine.validator import ValidationError, validate_workflow
from engine.executor import ExecutionError, execute_workflow
from engine.registry import (
    BUILTIN_OPS,
    get_op_description,
    get_op_func,
    list_ops,
)

__all__ = [
    "ParserError",
    "StepDef",
    "TableDef",
    "WorkflowDef",
    "parse_workflow",
    "ValidationError",
    "validate_workflow",
    "ExecutionError",
    "execute_workflow",
    "BUILTIN_OPS",
    "get_op_func",
    "get_op_description",
    "list_ops",
]
