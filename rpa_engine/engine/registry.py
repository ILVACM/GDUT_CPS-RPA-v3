"""
rpa_engine/engine/registry.py

内置操作函数查找接口（v3.1 定稿）。

薄再导出层（真转发，R6/F3-P3-3）：用户操作目录与查找函数的唯一定义在
ops/step_executor（BUILTIN_OPS/get_op_func/list_ops），本模块仅为 engine
包对外提供稳定接口，不再持有第二份实现（原双活副本已删除；
get_op_description 为本模块独有的展示辅助，保留）。
"""

from ops.step_executor import (  # noqa: F401
    BUILTIN_OPS,
    get_op_func,
    list_ops,
)


def get_op_description(op_name: str) -> str:
    """返回操作中文说明（GUI 目录展示用）；未知操作返回空串。"""
    entry = BUILTIN_OPS.get(op_name)
    return entry["description"] if entry else ""


__all__ = ["BUILTIN_OPS", "get_op_func", "list_ops", "get_op_description"]
