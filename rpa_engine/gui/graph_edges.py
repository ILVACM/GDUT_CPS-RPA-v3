"""
rpa_engine/gui/graph_edges.py

DAG 边派生层（2026-09-20 M16）：五类边的**单一事实源**。

设计口径（`_temp/DAG-rebuild/plan.md` §1.4 契约 / §4 翻译契约 / M16 实现规格）：
- 边契约 7 字段：``key`` / ``type`` / ``from`` / ``to`` / ``role`` / ``label`` / ``missing``
  （``from`` 为 Python 关键字，属性名用 ``src``，``to_dict()`` 输出契约字段名）
- 五类 type：``flow``（起止连接）/ ``reference``（数据引用）/ ``deprecated``
  （弃用引用，reference 的样式变体）/ ``produce``（数据产出）/ ``dangling``（悬空标记）
- ``key`` = ``type:from:to[:role]``，全集冲突追加 ``#n``（n 从 2）→ 唯一且幂等
- 生成顺序稳定：flow → reference|deprecated（表列序 → 消费者序）→ produce（步骤序）
  → dangling（步骤序），保证两次派生同一逻辑边 key 不变
- **输入＝未过滤的 GUI 模型**：弃用态经 ``deprecated_ids`` 入参传入；弃用表在画布
  保留显示，仅 ``WorkflowModel.to_dict()`` 导出时才过滤闭包（渲染/导出互不污染）

仅依赖标准库 + gui.models（禁 import Qt）；蓝本为 SampleCode 伪后端
``_build_edges``（不 import 演示代码，逐函数对照移植）。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from gui.models import (WorkflowModel, alive_table_ids, extra_input_ids,
                        is_end_op, produce_label, produces_table)

# 起止虚拟端点 key（避开 T/S+数字 命名空间，不参与节点详情路由）
START_KEY: str = "__start__"
END_KEY: str = "__end__"

# 边类型枚举（画布按 type 取样式，不再自行推导）
EDGE_TYPES: Tuple[str, ...] = ("flow", "reference", "deprecated",
                               "produce", "dangling")

# 边字典字段契约（to_dict 输出恰为此 7 键，不多不少）
EDGE_FIELDS: Tuple[str, ...] = ("key", "type", "from", "to", "role",
                                "label", "missing")


@dataclass
class TableSpec:
    """边派生所需的数据表最小视图。

    Attributes:
        key: 表编号（T1/T101…），即边的 from/to 端点标识。
        display: 列头显示名（渲染用，边派生不消费）。
        is_input: True＝输入表（阶段 1 导入），False＝派生表（步骤产出）。
        producer_step: 派生表的产出步骤 key（输入表为 None）。
        deprecated: 是否已被用户标记弃用。
        sqlite_table: 输入表后端物理表名（2026-09-21 审计 P9c：表节点
            tooltip 展示；派生表留空——执行期才定名，经
            NodeGraphScene.set_output_tables 回写）。
    """

    key: str
    display: str = ""
    is_input: bool = True
    producer_step: Optional[str] = None
    deprecated: bool = False
    sqlite_table: str = ""


@dataclass
class StepSpec:
    """边派生所需的步骤最小视图。

    Attributes:
        key: 步骤 ID（S1/S2…），即边的 from/to 端点标识。
        seq: 步骤序号（1-based，数组序），决定 produce/dangling 生成顺序。
        name: 中文步骤名（渲染用）。
        op_type: 操作类型（STEP_CATALOG 键），供注册表查询。
        target_table: 目标表编号。
        extra_inputs: 额外输入表编号（mapping_match/merge_tables）。
        output_table: 派生表编号（可空）。
        is_end: 是否结束步（经 normalize_end 规范化后唯一）。
        params: 步骤参数（供 produces_table 判 output_mode）。
    """

    key: str
    seq: int = 0
    name: str = ""
    op_type: str = ""
    target_table: str = ""
    extra_inputs: List[str] = field(default_factory=list)
    output_table: str = ""
    is_end: bool = False
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EdgeSpec:
    """一条 DAG 边（字段契约见模块 docstring）。"""

    key: str
    type: str
    src: str
    dst: str
    role: Optional[str] = None
    label: Optional[str] = None
    missing: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """导出为契约字典（键集恰为 EDGE_FIELDS）。"""
        return {
            "key": self.key,
            "type": self.type,
            "from": self.src,
            "to": self.dst,
            "role": self.role,
            "label": self.label,
            "missing": self.missing,
        }


# --------------------------------------------------------------------------- #
# 派生辅助
# --------------------------------------------------------------------------- #

def missing_refs(step: StepSpec, table_keys: Set[str]) -> List[str]:
    """步骤引用了但已不存在的表编号（悬空引用）。

    口径严格限定「表不存在」：弃用表、缺参、输入不足等其它缺失原因不计入，
    避免 dangling 与 deprecated 重复计数（与蓝本一致）。

    Args:
        step: 步骤视图。
        table_keys: 当前存在的全部表编号集合。

    Returns:
        List[str]: 缺失表编号（保持引用顺序，去重）。
    """
    refs: List[str] = []
    if step.target_table:
        refs.append(step.target_table)
    refs.extend(step.extra_inputs)
    out: List[str] = []
    for r in refs:
        if r not in table_keys and r not in out:
            out.append(r)
    return out


def normalize_end(steps: List[StepSpec]) -> None:
    """规范化 is_end：仅最后一个结束类操作为结束步（原地修改）。

    对齐生产语义 is_end=(type=="export")，保证结束标识唯一；
    无结束类操作时全部为 False（由 end_step 回退到末步）。

    Args:
        steps: 步骤视图列表（按执行序）。
    """
    last = -1
    for i, s in enumerate(steps):
        s.is_end = False
        if is_end_op(s.op_type):
            last = i
    if last >= 0:
        steps[last].is_end = True


def end_step(steps: List[StepSpec]) -> Optional[StepSpec]:
    """结束锚点步骤：is_end 步优先，否则末步（回退）；空流程返回 None。"""
    if not steps:
        return None
    for s in steps:
        if s.is_end:
            return s
    return steps[-1]


def specs_from_model(
    model: WorkflowModel,
    id_to_display: Optional[Dict[str, str]] = None,
) -> Tuple[List[StepSpec], List[TableSpec]]:
    """由 GUI 模型构造边派生视图（输入＝未过滤模型）。

    派生表只收录**当前参数下确实产表**的步骤（``produces_table``）——覆盖原表
    模式为原地修改，不产生表节点（plan.md §4.3 / M16 规格第 5 条）。

    Args:
        model: 工作流模型（tables + steps + deprecated_tables）。
        id_to_display: 表编号 → 列头显示名（可空，空则用 ``编号 别名``）。

    Returns:
        Tuple[List[StepSpec], List[TableSpec]]: 步骤视图（已 normalize_end）与表视图。
    """
    id_to_display = dict(id_to_display or {})
    deprecated = set(model.deprecated_tables or ())

    step_specs: List[StepSpec] = []
    derived: List[TableSpec] = []
    for i, s in enumerate(model.steps, start=1):
        step_specs.append(StepSpec(
            key=s.step_id,
            seq=i,
            name=s.name,
            op_type=s.type,
            target_table=s.target_table_id,
            extra_inputs=extra_input_ids(s),
            output_table=s.output_table_id,
            params=dict(s.params or {}),
        ))
        if s.output_table_id and produces_table(s.type, s.params):
            derived.append(TableSpec(
                key=s.output_table_id,
                display=id_to_display.get(
                    s.output_table_id,
                    f"{s.output_table_id} {model.alias_of(s.output_table_id)}",
                ),
                is_input=False,
                producer_step=s.step_id,
                deprecated=s.output_table_id in deprecated,
            ))
    normalize_end(step_specs)

    table_specs: List[TableSpec] = [
        TableSpec(
            key=t.table_id,
            display=id_to_display.get(t.table_id, f"{t.table_id} {t.alias}"),
            is_input=True,
            producer_step=None,
            deprecated=t.table_id in deprecated,
            sqlite_table=t.sqlite_table,
        )
        for t in model.tables
    ]
    table_specs.extend(derived)
    return step_specs, table_specs


# --------------------------------------------------------------------------- #
# 边构造
# --------------------------------------------------------------------------- #

def _uniq_key(base: str, seen: Set[str]) -> str:
    """保证边 key 全集唯一（同一 base 重复时追加 #n 后缀，n 从 2）。"""
    if base not in seen:
        seen.add(base)
        return base
    n = 2
    while f"{base}#{n}" in seen:
        n += 1
    key = f"{base}#{n}"
    seen.add(key)
    return key


def _mk_edge(etype: str, src: str, dst: str, seen: Set[str],
             role: Optional[str] = None, label: Optional[str] = None,
             missing: Optional[str] = None) -> EdgeSpec:
    """构造一条边（key 由 type/from/to/role 派生并保证唯一）。"""
    base = f"{etype}:{src}:{dst}"
    if role:
        base = f"{base}:{role}"
    return EdgeSpec(key=_uniq_key(base, seen), type=etype, src=src, dst=dst,
                    role=role, label=label, missing=missing)


def build_edges(steps: List[StepSpec], tables: List[TableSpec],
                deprecated_ids: Optional[Set[str]] = None) -> List[EdgeSpec]:
    """派生五类边列表（单一事实源；渲染层只按 type 取样式，不自行推导）。

    Args:
        steps: 步骤视图（按执行序；建议先经 normalize_end）。
        tables: 表视图（按列序：输入表在前、派生表在后）。
        deprecated_ids: 已弃用表编号集合（与 TableSpec.deprecated 取并集）。

    Returns:
        List[EdgeSpec]: 顺序稳定的边列表（flow → reference|deprecated →
        produce → dangling）。
    """
    deprecated_ids = set(deprecated_ids or ())
    edges: List[EdgeSpec] = []
    seen: Set[str] = set()
    # 表节点集合（渲染节点用；覆盖模式不收录）与存活表集合（悬空判定用）——
    # 后者经 models.alive_table_ids 取**单一源**（与 reconcile 的 alive 同口径，
    # 含覆盖模式中间产出编号：不产生表节点但编号仍存活，故引用它不判悬空；
    # 消除 B-21/G-13「覆盖原表的派生表被判 dangling」假悬空告警）
    table_keys: Set[str] = {t.key for t in tables}
    alive_keys: Set[str] = alive_table_ids(tables, steps)

    # 1) flow：起止连接边（steps 非空恒 2 条，空流程 0 条）
    if steps:
        edges.append(_mk_edge("flow", START_KEY, steps[0].key, seen))
        end = end_step(steps)
        if end is not None:
            edges.append(_mk_edge("flow", end.key, END_KEY, seen))

    # 2) reference / deprecated：按表列序 → 消费者序（与泳道渲染序一致）
    for t in tables:
        etype = "deprecated" if (t.deprecated or t.key in deprecated_ids) \
            else "reference"
        for s in steps:
            if s.target_table == t.key:
                edges.append(_mk_edge(etype, t.key, s.key, seen, role="target"))
            for extra in s.extra_inputs:
                if extra == t.key:
                    edges.append(_mk_edge(etype, t.key, s.key, seen, role="extra"))

    # 3) produce：步骤 → 操作表（按步骤序；覆盖模式不产表故无边）
    for s in steps:
        if (s.output_table and s.output_table in table_keys
                and produces_table(s.op_type, s.params)):
            edges.append(_mk_edge("produce", s.key, s.output_table, seen,
                                  label=produce_label(s.op_type)))

    # 4) dangling：缺失表 → 步骤（按步骤序；判定基准＝存活表集合，
    #    非表节点集合——覆盖模式中间产出编号存活故不判悬空）
    for s in steps:
        for mk in missing_refs(s, alive_keys):
            edges.append(_mk_edge("dangling", mk, s.key, seen, missing=mk))

    return edges


def edges_to_dicts(edges: List[EdgeSpec]) -> List[Dict[str, Any]]:
    """边列表转契约字典列表（跨层传递用；均为新对象，不共享引用）。"""
    return [e.to_dict() for e in edges]


# R6/F5（P3-3）：detect_table_id_collisions 门面已删除（2026-09-24）。
# 撞号检测唯一生产入口＝WorkflowModel.validate_table_ids_unique()。

__all__ = [
    "START_KEY", "END_KEY", "EDGE_TYPES", "EDGE_FIELDS",
    "TableSpec", "StepSpec", "EdgeSpec",
    "missing_refs", "normalize_end", "end_step", "specs_from_model",
    "build_edges", "edges_to_dicts",
]
