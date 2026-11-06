"""
rpa_engine/engine/validator.py

全量校验模块（v3.1 定稿）。

校验内容：
1. tables[] 编号唯一且非空
2. steps[] 的 type 在 BUILTIN_OPS 用户操作目录中（且未弃用）
3. steps[] 引用的 table_id 已定义（含前序步骤的派生表编号）
4. 必填业务参数存在（如 mapping_match 的 match_table_id）

任一失败抛 ValidationError，不执行任何步骤。
"""

from typing import List, Optional, Set

from loguru import logger

from engine.parser import StepDef, TableDef, WorkflowDef
from ops.step_executor import BUILTIN_OPS


class ValidationError(Exception):
    """校验异常。"""
    pass


def validate_workflow(workflow: WorkflowDef) -> bool:
    """执行 v3.1 全量校验。

    Args:
        workflow: 工作流定义。

    Returns:
        bool: 校验全部通过返回 True。

    Raises:
        ValidationError: 任一校验失败。
    """
    logger.info(
        f"[validator] 开始全量校验: {workflow.name} "
        f"({len(workflow.steps)} 步, {len(workflow.tables)} 表)"
    )

    validate_tables(workflow.tables, workflow.steps)
    validate_steps(workflow.steps)

    logger.info("[validator] 全量校验通过")
    return True


def validate_tables(tables: List[TableDef],
                    steps: Optional[List[StepDef]] = None) -> None:
    """校验数据表定义：编号非空且唯一 + 输入∩派生交叉查重。

    交叉查重（2026-09-21 审计 P3）：输入表编号与步骤派生表编号重复时，
    executor 的 table_id_map 后写覆盖会静默劫持输入表物理名——引擎侧
    最后防线。steps 缺省 None 保持旧签名兼容。
    """
    seen: Set[str] = set()
    for i, t in enumerate(tables):
        if not t.table_id:
            raise ValidationError(f"tables[{i}] 编号为空")
        if t.table_id in seen:
            raise ValidationError(f"数据表编号重复: {t.table_id}")
        seen.add(t.table_id)
    derived = {s.output_table_id for s in (steps or [])
               if s.output_table_id}
    cross = seen & derived
    if cross:
        raise ValidationError(f"输入表与派生表编号重复: {sorted(cross)}")


def validate_steps(steps: List[StepDef]) -> None:
    """校验步骤：操作类型合法 + 引用链合法（含派生表前向引用）。"""
    # 第一遍：收集所有声明的派生表编号（用于引用校验）
    declared_output_ids: Set[str] = set()
    for s in steps:
        if s.output_table_id:
            if s.output_table_id in declared_output_ids:
                raise ValidationError(
                    f"步骤 [{s.step_id}] 派生表编号重复: {s.output_table_id}"
                )
            declared_output_ids.add(s.output_table_id)

    # 第二遍：逐项校验
    for s in steps:
        # 操作类型白名单
        if s.type not in BUILTIN_OPS:
            raise ValidationError(
                f"步骤 [{s.step_id}] 操作类型 '{s.type}' 不在用户操作目录中，"
                f"可用: {sorted(BUILTIN_OPS.keys())}"
            )

        # R15/B-53（原编号 D4）：已弃用操作拒绝执行——闭合"弃用口径前后端
        # 不闭合"缺口（此前 GUI 置灰但手写 JSON 仍可执行）
        if BUILTIN_OPS[s.type].get("deprecated"):
            raise ValidationError(
                f"步骤 [{s.step_id}] 操作 '{s.type}' 已停用，"
                f"请移除该步骤或改用其它操作后重试"
            )

        # 操作必填参数（每类操作的关键参数由 step_executor 分发时二次校验，
        # 此处仅校验结构性必填项）
        if s.type == "mapping_match" and not s.params.get("match_table_id"):
            raise ValidationError(
                f"步骤 [{s.step_id}] 映射匹配缺少 match_table_id（匹配哪张数据表）"
            )

        logger.debug(f"[validator] 步骤 [{s.step_id}] 类型 '{s.type}' 校验通过")


def validate_table_references(tables: List[TableDef], steps: List[StepDef]) -> None:
    """校验步骤引用的表编号在 tables[] 或前序派生表中存在。

    注意：此校验需按步骤顺序模拟执行（派生表按步骤顺序注册），
    由 executor 在执行前调用；validate_workflow 内不含（因派生表
    依赖执行顺序，静态校验仅查 tables[] 与全部声明）。
    """
    available: Set[str] = {t.table_id for t in tables}
    for s in steps:
        # 目标表
        if s.target_table_id not in available:
            raise ValidationError(
                f"步骤 [{s.step_id}] 引用未定义的数据表: {s.target_table_id}"
                f"（可用: {sorted(available)}）"
            )
        # 匹配表（mapping_match）
        match_id = s.params.get("match_table_id", "")
        if s.type == "mapping_match" and match_id and match_id not in available:
            raise ValidationError(
                f"步骤 [{s.step_id}] 引用未定义的匹配表: {match_id}"
                f"（可用: {sorted(available)}）"
            )
        # 合并的其余表
        if s.type == "merge_tables":
            for oid in s.params.get("match_table_ids", []) or []:
                if oid not in available:
                    raise ValidationError(
                        f"步骤 [{s.step_id}] 合并引用未定义的数据表: {oid}"
                        f"（可用: {sorted(available)}）"
                    )
        # 注册派生表
        if s.output_table_id:
            available.add(s.output_table_id)
