"""
rpa_engine/gui/models.py

GUI 纯数据层（v3.1 定稿）：用户操作目录、步骤/数据表模型与 JSON 互转。
仅依赖标准库（禁止 import Qt），是 GUI 生成 v3.1 JSON 参数文件的唯一数据载体。
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from loguru import logger

# 派生表号段起点（输入表 T1-99 / 派生表 T101+，2026-09-21 定稿 M2-T2）
_DERIVED_BASE = 101


def _new_uid() -> str:
    """稳定 ID 生成（uuid4 短码；前端键，to_dict 剔除，定稿 M2-T1/D-C2）。"""
    return uuid.uuid4().hex[:8]

# ---------------------------------------------------------------------------
# 用户操作目录（与 ops/step_executor.BUILTIN_OPS 对齐，D3；总数见 STEP_COUNT）
# 2026-09-21 定稿 D-B2/M3-T1：升级为 StepMeta 元数据（key 稳定铁律：
# 改名只动 display，持久化全以 key 为准）
# ---------------------------------------------------------------------------


@dataclass
class StepMeta:
    """功能函数元数据（注册表单一源，定稿 D-B2）。

    Attributes:
        key: 稳定标识（JSON steps[].type / BUILTIN_OPS / 表单注册全以 key 为准）。
        display: 中文显示名（可改名，不触碰持久化数据）。
        desc: 一句话业务说明（STEP_DESC 派生源，禁技术词）。
        category: 业务分类（筛选类/关联统计类/表结构类/输出类）。
        keywords: 搜索关键词/别名（弹层搜索过滤用）。
        order: 分组内排序权重（同时决定分类代表=主按钮）。
        deprecated: 功能级弃用标记（弹层置灰「（已停用）」）。
    """

    key: str
    display: str
    desc: str
    category: str
    keywords: Tuple[str, ...] = ()
    order: int = 0
    deprecated: bool = False

    def __getitem__(self, idx: int) -> str:
        """兼容层：0→display、1→desc（旧下标访问零改动，定稿 D-B2）。"""
        if idx == 0:
            return self.display
        if idx == 1:
            return self.desc
        raise KeyError(idx)

    def __iter__(self):
        """兼容层：tuple 解包 (display, desc)。"""
        return iter((self.display, self.desc))


_STEP_META_RAW: List[Tuple[str, str, str, str, Tuple[str, ...], int]] = [
    ("filter", "条件筛选", "按条件筛选数据表的行，结果存为新表",
     "筛选类", ("筛选", "条件", "filter"), 1),
    ("dedup", "条件去重", "按指定列去重，保留首次/末次出现的行",
     "筛选类", ("去重", "重复", "dedup"), 2),
    ("mapping_match", "跨表映射匹配", "两张数据表按匹配列关联（类似 Excel 的 VLOOKUP）",
     "关联统计类", ("vlookup", "匹配", "映射", "关联"), 3),
    ("aggregate", "条件统计", "按列分组计数/求和/平均等统计",
     "关联统计类", ("分组", "求和", "计数", "统计"), 4),
    ("merge_tables", "数据表合并", "将多张格式一致的数据表上下合并为一张",
     "关联统计类", ("合并", "merge", "拼接"), 5),
    ("copy_table", "数据表复制", "复制一张数据表的副本",
     "表结构类", ("复制", "副本", "分支"), 6),
    ("rename_columns", "表头名称修改", "修改数据表的列标题名称",
     "表结构类", ("改名", "表头", "列名"), 7),
    ("convert_dtype", "数据类型转换", "文本数字与可计算数值之间的无损转换",
     "表结构类", ("类型", "转换", "数值"), 8),
    ("export", "结果导出", "将数据表导出为 Excel 文件",
     "输出类", ("导出", "保存", "excel"), 9),
    ("supervision_report", "履职表单抽查报告", "一次生成多张统计表和一段总结文字",
     "输出类", ("报告", "履职", "抽查", "统计表", "一键", "月报"), 10),
]

STEP_CATALOG: Dict[str, StepMeta] = {
    k: StepMeta(key=k, display=d, desc=ds, category=c, keywords=kw, order=o)
    for k, d, ds, c, kw, o in _STEP_META_RAW
}

# 功能函数总数单一源（R15/B-67＋B-68，原编号 E3／A4）：门禁断言与文案
# 一律引用本常量（由目录长度派生），新增/删除功能函数时自动同步，
# 不再手改多处「9」等值断言与说明文案
STEP_COUNT: int = len(STEP_CATALOG)

# 前端键「结果保存方式」集中声明（R15/B-60，原编号 B8）：
# 生产代码一律引用本三常量，禁止散落字面量（编辑态保留/业务口径剔除见
# to_dict；键不在任何 param_keys 白名单内，属 GUI 专属前端键）
OUTPUT_MODE_KEY = "output_mode"
OUTPUT_MODE_NEW = "new_table"
OUTPUT_MODE_OVERWRITE = "overwrite_target"

# 步骤性质值域单一源（R15/B-55，原编号 B2）：STEP_KIND 的合法取值；
# 非法值不再静默回退 sequential，由 classify_step/reconcile 报错
STEP_KINDS: Tuple[str, ...] = ("end", "merge", "fork", "sequential")


def display_name(type_name: str) -> str:
    """操作中文显示名（兼容层，定稿 M3-T1）；未知类型回退 key。"""
    meta = STEP_CATALOG.get(type_name)
    return meta.display if meta is not None else type_name


def ordinal_map(steps: List["StepConfig"]) -> Dict[str, int]:
    """同类步骤实时位序 {step_id: 序数}（2026-09-21 审计 P8）。

    位序=同 type 步骤按列表序从 1 计数；删除中间步后自动收缩，
    消除 name 快照重号。纯函数，无副作用。
    """
    counters: Dict[str, int] = {}
    result: Dict[str, int] = {}
    for s in steps:
        counters[s.type] = counters.get(s.type, 0) + 1
        result[s.step_id] = counters[s.type]
    return result


def title_of(steps: List["StepConfig"], step_id: str) -> str:
    """步骤实时标题「显示名 位序」（配置态展示统一源，P8）。

    未命中回退 step_id 本身（与页面 _sname 回退语义一致）。
    """
    for s in steps:
        if s.step_id == step_id:
            return f"{display_name(s.type)} {ordinal_map(steps)[step_id]}"
    return step_id


def active_catalog_keys() -> List[str]:
    """非弃用操作键列表（＝排除 deprecated 后的 STEP_CATALOG 键集合，B-13）。

    供启动自检的按钮分组比对与按钮生成**共用**，消除"一侧过滤弃用、一侧
    未过滤"的双口径（否则任一功能标记 deprecated=True 即致启动自检失败）。
    """
    return [k for k, meta in STEP_CATALOG.items() if not meta.deprecated]


def main_buttons() -> List[str]:
    """主按钮组（定稿 M3-T2：category+order 派生，消除双源硬编码列表）。

    规则：每个业务分类取 order 最小者为主按钮（4 分类→4 主按钮），
    其余归「更多功能」下拉；分组展示序同 order。仅取非弃用操作
    （active_catalog_keys() 单一过滤口径，B-13）。
    """
    reps: Dict[str, str] = {}
    for key in active_catalog_keys():
        meta = STEP_CATALOG[key]
        cur = reps.get(meta.category)
        if cur is None or meta.order < STEP_CATALOG[cur].order:
            reps[meta.category] = key
    return [reps[c] for c in _category_order() if c in reps]


def more_buttons() -> List[str]:
    """「更多功能」下拉组（主按钮之外的非弃用操作，按 order 升序）。"""
    mains = set(main_buttons())
    return [k for k in sorted(active_catalog_keys(),
                              key=lambda k: m_order(STEP_CATALOG[k]))
            if k not in mains]


def _category_order() -> List[str]:
    """分类展示序（按分类内最小 order）。"""
    mins: Dict[str, int] = {}
    for meta in STEP_CATALOG.values():
        mins[meta.category] = min(mins.get(meta.category, 10**6), meta.order)
    return [c for c, _ in sorted(mins.items(), key=lambda kv: kv[1])]


def categories() -> List[str]:
    """业务分类展示序（弹层分组标题用，定稿 M3-T3）。"""
    return _category_order()


def category_ops(category: str) -> List[str]:
    """指定分类内操作 key 列表（按 order 升序，含弃用项由调用方过滤）。"""
    return [k for k, meta in sorted(STEP_CATALOG.items(),
                                    key=lambda kv: kv[1].order)
            if meta.category == category]


def m_order(meta: StepMeta) -> int:
    """排序权重访问器。"""
    return meta.order

# 需要产出新表的操作（节点图连线用）
OUTPUT_OPS = {"filter", "dedup", "mapping_match", "aggregate",
              "merge_tables", "copy_table"}

# 操作在流程图中的性质分类（节点图 DAG 渲染用）
# end:        终点（分支结束关闭）
# merge:      多输入合并（多条线汇聚为一条新线）
# fork:       单输入分叉（源线继续 + 新线分出）
# sequential: 原地操作（单输入无新表，源线继续）
STEP_KIND: Dict[str, str] = {
    "export":         "end",
    "supervision_report": "end",
    "mapping_match":  "merge",
    "merge_tables":   "merge",
    "filter":         "fork",
    "dedup":          "fork",
    "aggregate":      "fork",
    "copy_table":     "fork",
    "rename_columns": "sequential",
    "convert_dtype":  "sequential",
}


def classify_step(type_name: str) -> str:
    """返回操作在流程图中的性质分类（end/merge/fork/sequential）。

    未知类型回退为 sequential（单输入无新表的保守处理）；已知类型的
    **值域越界**（不在 STEP_KINDS 内）则报错，不再静默回退（R15/B-55）。

    Args:
        type_name: 操作类型名（STEP_CATALOG 键）。

    Returns:
        str: 操作性质分类。

    Raises:
        ValueError: STEP_KIND 中该类型的取值不在 STEP_KINDS 值域内。
    """
    kind = STEP_KIND.get(type_name, "sequential")
    if kind not in STEP_KINDS:
        raise ValueError(
            f"STEP_KIND 取值非法: {type_name} -> {kind!r}，"
            f"允许值: {list(STEP_KINDS)}")
    return kind


# ---------------------------------------------------------------------------
# 流程图元数据扩展（2026-09-18 M18，同源对齐 SampleCode/backend/func_registry.py）
# ---------------------------------------------------------------------------

# 数据产出边标签：copy_table 专用「复制新表」，其余产表操作「新表」，不产表操作 None
PRODUCE_LABEL: Dict[str, Optional[str]] = {
    "filter": "新表",
    "dedup": "新表",
    "mapping_match": "新表",
    "aggregate": "新表",
    "merge_tables": "新表",
    "copy_table": "复制新表",
    "rename_columns": None,
    "convert_dtype": None,
    "export": None,
    "supervision_report": None,
}

# 工具栏功能按钮分组（主按钮 4 项 +「更多功能」下拉 5 项；并集=STEP_CATALOG 键集且不相交）
# 按钮分组硬编码列表已删除（2026-09-21 定稿 M3-T2）：改由
# main_buttons()/more_buttons() 按 category+order 派生（消除双源）。

# 步骤卡片业务副标题（操作类型级静态描述，2026-09-20 M23/D-2=a）
# 由 STEP_CATALOG 的一句话说明派生——单一语义源，禁另立文案（同 M21 禁双源原则）
STEP_DESC: Dict[str, str] = {
    t: desc for t, (_cn, desc) in STEP_CATALOG.items()
}


def step_desc(type_name: str) -> str:
    """返回操作类型级业务描述（步骤卡片副标题用）；未知类型返回空串。

    Args:
        type_name: 操作类型名（STEP_CATALOG 键）。

    Returns:
        str: 业务描述文案（面向无技术背景用户）。
    """
    return STEP_DESC.get(type_name, "")


def produce_label(type_name: str) -> Optional[str]:
    """数据产出边的画布标签文案；未知操作或不产表操作返回 None。

    Args:
        type_name: 操作类型名（STEP_CATALOG 键）。

    Returns:
        Optional[str]: 产出边标签（「新表」/「复制新表」/None）。
    """
    return PRODUCE_LABEL.get(type_name)


def produces_table(type_name: str, params: Optional[Dict[str, Any]] = None) -> bool:
    """该步骤在当前参数下是否产出一张新的数据表（数据产出边判定）。

    判定＝产表类操作（OUTPUT_OPS）且未选择「覆盖原表」——覆盖模式为原地修改，
    不新增表节点（正本 §8.3、plan.md M16 规格第 5 条）。

    Args:
        type_name: 操作类型名（STEP_CATALOG 键）。
        params: 步骤参数（读取前端键 OUTPUT_MODE_KEY；可空）。

    Returns:
        bool: 产出新表返回 True。
    """
    if type_name not in OUTPUT_OPS:
        return False
    return (params or {}).get(OUTPUT_MODE_KEY) != OUTPUT_MODE_OVERWRITE


def is_end_op(type_name: str) -> bool:
    """该操作是否为流程结束类操作（STEP_KIND == "end"）。

    Args:
        type_name: 操作类型名（STEP_CATALOG 键）。

    Returns:
        bool: 结束类操作返回 True。
    """
    return STEP_KIND.get(type_name) == "end"


@dataclass
class TableEntry:
    """数据表条目（阶段 1 确认导入时由主窗口注册）。"""

    table_id: str = ""       # 显示编号（T1, T2, ...；reconcile 可重排投影）
    alias: str = ""          # 别名（用户可见）
    sqlite_table: str = ""   # SQLite 表名
    file_path: str = ""      # 临时区 xlsx 路径（复现信息）
    sheet_name: str = ""     # 源数据表名
    header_row: int = 1      # 表头行（1-based）
    source_path: str = ""    # 原始文件路径（复现信息；R11/A-10 落 last_config 用）
    uid: str = ""            # 稳定 ID（前端键，不入 v3.1 JSON，D-C2）


@dataclass
class StepConfig:
    """单个步骤配置。"""

    step_id: str = ""
    type: str = ""                 # STEP_CATALOG 操作名
    name: str = ""                 # 中文显示名
    target_table_id: str = ""      # 目标数据表编号
    output_table_id: str = ""      # 派生表编号（可空 = 自动分配）
    params: Dict[str, Any] = field(default_factory=dict)
    on_error: str = "stop"
    retry_count: int = 3
    uid: str = ""                  # 稳定 ID（前端键，不入 v3.1 JSON，D-C2）


class WorkflowModel:
    """工作流模型：维护数据表清单与步骤列表，负责 v3.1 JSON 互转。"""

    def __init__(self, workflow_name: str = "GUI 操作") -> None:
        self.workflow_name = workflow_name
        self.tables: List[TableEntry] = []
        self.steps: List[StepConfig] = []
        self._next_step_num = 1
        # 已弃用表编号（2026-09-20 M23/D-1=B）：前端编辑态，可逆、不入 v3.1 JSON
        self.deprecated_tables: Set[str] = set()
        # 表生命周期状态机投影（2026-09-21 定稿 M2-T3/§7.3）：
        # 6 记录态（declared/produced/referenced/overwritten/deprecated/
        # dangling，落 table_states）+1 隐式态（dropped＝表已不存在且号由
        # _alloc_table_id 回收，不落 table_states）
        self.table_states: Dict[str, str] = {}

    # ------------------------------------------------------------------ #
    # 数据表管理
    # ------------------------------------------------------------------ #

    def set_tables(self, entries: List[Dict[str, Any]]) -> None:
        """设置输入数据表清单（阶段 1 确认导入后调用）。

        Args:
            entries: [{table_id, alias, sqlite_table, file_path,
                      sheet_name, header_row}]
        """
        self.tables = [
            TableEntry(
                table_id=e["table_id"],
                alias=e.get("alias", e["table_id"]),
                sqlite_table=e.get("sqlite_table", e["table_id"].lower()),
                file_path=e.get("file_path", ""),
                sheet_name=e.get("sheet_name", ""),
                header_row=int(e.get("header_row", 1)),
                source_path=str(e.get("source_path", "") or ""),
                uid=str(e.get("uid", "") or _new_uid()),
            )
            for e in entries
        ]
        self.reconcile()

    def apply_registry(self, registry: List[Dict[str, Any]]) -> None:
        """仅刷新输入表 registry + reconcile，不动 steps/deprecated_tables。

        与 load_session（整会话载入，清空步骤）区分：确认导入时保留已恢复
        的步骤（2026-09-21 审计 P2 修复）。steps 引用号在新 registry 缺失时
        由 reconcile 自动 dangling 化（画布可视化+执行前 validator 拦截）。
        """
        self.set_tables(registry)

    def alias_of(self, table_id: str) -> str:
        """返回编号对应别名（含已声明派生表）；未知返回编号本身。"""
        for t in self.tables:
            if t.table_id == table_id:
                return t.alias
        for s in self.steps:
            if s.output_table_id == table_id:
                # 实时标题单一源（2026-09-21 审计 P8，替代 name 快照）
                return f"{title_of(self.steps, s.step_id)}·结果"
        return table_id

    def available_table_ids(self, upto_step: int = -1) -> List[str]:
        """返回可选表编号：输入表 + 前序步骤派生表。

        Args:
            upto_step: 截止步骤下标（不含）；-1 表示全部。
        """
        ids = [t.table_id for t in self.tables]
        end = len(self.steps) if upto_step < 0 else upto_step
        for s in self.steps[:end]:
            if s.output_table_id:
                ids.append(s.output_table_id)
        return ids

    # ------------------------------------------------------------------ #
    # 步骤管理
    # ------------------------------------------------------------------ #

    def insert_step(self, index: int, type_name: str) -> StepConfig:
        """在指定位置插入新步骤并立即重排 step_id（S1..Sn）。

        插入即重排，画布键随 refresh 重建（M5-b/K5）；与 add_step 旧行为
        （末尾追加+临时号）的差异属 C3 已裁定接受范围。
        """
        if type_name not in STEP_CATALOG:
            raise ValueError(f"未知操作类型: {type_name}")
        idx = max(0, min(index, len(self.steps)))   # clamp（插入时点，K5）

        n = sum(1 for s in self.steps if s.type == type_name) + 1
        step = StepConfig(
            step_id=f"step_{self._next_step_num:02d}",   # 临时号，下方 renumber 即覆盖
            type=type_name,
            name=f"{display_name(type_name)} {n}",
            target_table_id=self.tables[0].table_id if self.tables else "",
            output_table_id="",
            params=default_params(type_name),
            uid=_new_uid(),
        )
        # 产出表的操作自动分配派生表编号（T101+ 最小空号，定稿 M2-T2）
        # 产表列 = 该步骤的锚列（output_table 所在列）：产出边自步骤卡片顶边
        # 右锚点竖直向上连至该列表头（M19 显式约定，供 M7/M16 列定位语义使用）
        if type_name in OUTPUT_OPS:
            step.output_table_id = self._alloc_table_id()
        self.steps.insert(idx, step)
        self.renumber_steps()                       # 立即重排（K5/C3）
        self._next_step_num += 1
        self.reconcile()
        return step

    def add_step(self, type_name: str) -> StepConfig:
        """在末尾追加一个指定类型的新步骤。

        新步骤默认以第一张输入表为目标表（表清单非空时），
        避免新建即处于"缺目标表"的非法状态。
        ＝末尾插入委托（M5-b/K5），构造逻辑已整体迁移至 insert_step。
        """
        return self.insert_step(len(self.steps), type_name)

    def remove_step(self, index: int) -> None:
        """删除指定下标步骤（越界忽略）。

        级联 B（2026-09-21 定稿 D-C1/§7.4，矛盾调和记录：定稿 M2-T4  wording
        "置空"与 §7.4 dangling 视觉不可同时成立——置空后引用消失即无 dangling
        边；采"保留引用"解释使红虚线/缺输入角标/待配置橙边框/用户重指全链路
        自洽）：下游对已删步骤派生表的引用**保留编号** → missing_refs 判
        "表不存在" → dangling 边（画布红虚线短桩+⚠+「输入缺失」角标）+
        table_states[dangling] + 右面板待配置橙边框（_config_state_of 判
        target 不在列集即 incomplete）；用户在面板重指目标表即消除 dangling。
        弃用标记随表消失摘除、step_id 即时重排、状态机 reconcile。
        """
        if 0 <= index < len(self.steps):
            step = self.steps[index]
            out_id = step.output_table_id
            del self.steps[index]
            if out_id:
                self.deprecated_tables.discard(out_id)
            self.renumber_steps()
            self.reconcile()

    def reset(self) -> None:
        """原地清空数据表与步骤并重置状态。

        保持对象引用不变（页面与主窗口共享同一 model 实例，
        替换对象会导致二者脱钩）。
        """
        self.tables.clear()
        self.steps.clear()
        self.deprecated_tables.clear()
        self.table_states.clear()
        self._next_step_num = 1

    def reset_steps(self) -> None:
        """仅清步骤与弃用/状态投影，保留输入表 registry（定稿 M2-T3/§7.4）。"""
        self.steps.clear()
        self.deprecated_tables.clear()
        self._next_step_num = 1
        self.reconcile()

    # R6/F1（P3-1/H2）：move_step 已删除（2026-09-21 H2 裁定"调序 UI 不恢复、
    # 留下一清理轮"，本轮执行）。调序等效手段＝remove_step＋insert_step
    # （M5-b 三态锚点插入）；漂移免疫由 t_{uid} 物理名机制保证。

    def renumber_steps(self) -> None:
        """按当前顺序重编 step_id（S1, S2, ...）。

        step_id 即步骤行序，与产表列（add_step 分配的 output_table_id 所在列）
        共同决定画布几何：行 = row_cy(seq)，列 = col_cx(锚列)（M19 约定）。
        """
        for i, s in enumerate(self.steps, start=1):
            s.step_id = f"S{i}"

    # ------------------------------------------------------------------ #
    # 编号分配 / 生命周期状态机（2026-09-21 定稿 M2-T2/T3/T6）
    # ------------------------------------------------------------------ #

    def _alloc_table_id(self,
                        extra_used: Optional[Set[str]] = None) -> str:
        """派生表编号分配：T101+ 号段最小空号（输入∪产出已用集扫描）。

        无状态分配器：删除步骤回收的号可被复用，根治"单调递增导致跳号/
        重号"缺陷（定稿 §7.2 唯一性不变量 FF1）。

        Args:
            extra_used: 批量预分配时的额外排除集（尚未写回模型的号）。
        """
        used = {t.table_id for t in self.tables}
        used.update(s.output_table_id for s in self.steps
                    if s.output_table_id)
        used.update(extra_used or ())
        # dangling 引用号占用（2026-09-21 审计 P6）：防新步夺回悬空号使旧
        # 引用"复活"（前端绿灯/执行拦截口径分裂）；用户重指后经 reconcile
        # 释放复用
        used.update(k for k, v in self.table_states.items()
                    if v == "dangling")
        n = _DERIVED_BASE
        while f"T{n}" in used:
            n += 1
        return f"T{n}"

    def alloc_table_id(self,
                       extra_used: Optional[Set[str]] = None) -> str:
        """公共分配器入口（F7：消除跨层私有调用，委托 _alloc_table_id）。"""
        return self._alloc_table_id(extra_used)

    def deprecated_closure(self) -> Tuple[Set[str], Set[str]]:
        """公共弃用闭包入口（F7：委托 _deprecated_closure）。"""
        return self._deprecated_closure()

    def validate_table_ids_unique(self) -> List[str]:
        """配置期即时校验：返回重复的表编号列表（空＝通过，FF1）。"""
        seen: Set[str] = set()
        dups: List[str] = []
        ids = [t.table_id for t in self.tables]
        ids.extend(s.output_table_id for s in self.steps
                   if s.output_table_id)
        for tid in ids:
            if tid in seen and tid not in dups:
                dups.append(tid)
            seen.add(tid)
        return dups

    def reconcile(self) -> None:
        """表生命周期状态机投影（定稿 §7.3）：每次模型变更后统一调用。

        状态口径＝6 记录态（declared/produced/referenced/overwritten/
        deprecated/dangling，落 table_states）+1 隐式态（dropped＝表不存在
        且号由 _alloc_table_id 回收，不落 table_states）。
        记录态优先级：deprecated > overwritten > referenced > produced >
        declared；被引用但已不存在的表记 dangling；弃用集中已消失的表自动
        摘除。
        """
        produced_by = {s.output_table_id: s for s in self.steps
                       if s.output_table_id}
        referenced: Set[str] = set()
        for s in self.steps:
            if s.target_table_id:
                referenced.add(s.target_table_id)
            referenced.update(extra_input_ids(s))
        alive = alive_table_ids(self.tables, self.steps)
        # 弃用集摘除已消失表（"弃用未及时清理"根治，定稿 §7.4）
        for tid in list(self.deprecated_tables):
            if tid not in alive:
                self.deprecated_tables.discard(tid)
        states: Dict[str, str] = {}
        for tid in alive:
            if tid in self.deprecated_tables:
                states[tid] = "deprecated"
            elif (tid in produced_by
                    and produced_by[tid].params.get(OUTPUT_MODE_KEY)
                    == OUTPUT_MODE_OVERWRITE):
                states[tid] = "overwritten"
            elif tid in referenced:
                states[tid] = "referenced"
            elif tid in produced_by:
                states[tid] = "produced"
            else:
                states[tid] = "declared"
        for s in self.steps:
            refs = ([s.target_table_id] if s.target_table_id else [])
            refs.extend(extra_input_ids(s))
            for r in refs:
                if r and r not in states:
                    states[r] = "dangling"
        self.table_states = states

    def edge_state(self, table_id: str) -> str:
        """表在画布边派生口径下的单一状态访问器（B-21/G-13）。

        返回生命周期状态机的记录态（declared/produced/referenced/
        ``overwritten``/deprecated/dangling）；未登记（既非存活表、亦非悬空
        引用）返回空串。画布与边派生层统一经此读取状态，消除"画布各自演化、
        口径与模型账本分叉"。注意：读取前模型须已 ``reconcile``。

        Args:
            table_id: 数据表编号（输入表或派生表）。

        Returns:
            str: 该表的记录态；未登记返回空串。
        """
        if not table_id:
            return ""
        return self.table_states.get(table_id, "")

    def set_output_mode(self, step_id: str, mode: str) -> None:
        """收敛 output_mode 直写并触发状态机重算（定稿 M2-T3）。"""
        for s in self.steps:
            if s.step_id == step_id:
                s.params[OUTPUT_MODE_KEY] = mode
                self.reconcile()
                return

    # ------------------------------------------------------------------ #
    # 表弃用（2026-09-20 M23 / plan.md §4.2，D-1=B 前端翻译降级）
    # ------------------------------------------------------------------ #

    def deprecate_table(self, table_id: str, flag: bool = True) -> None:
        """标记/取消标记某张数据表为「已弃用」（可逆，仅本会话有效）。

        弃用属用户本轮编辑意图，不写入 v3.1 参数文件；执行侧的实现方式是
        导出时过滤弃用闭包（见 to_dict），内存释放由会话结束清理兜底。

        Args:
            table_id: 数据表编号（输入表或派生表）。
            flag: True＝弃用，False＝恢复使用。
        """
        if not table_id:
            return
        if flag:
            self.deprecated_tables.add(table_id)
        else:
            self.deprecated_tables.discard(table_id)
        self.reconcile()

    def _deprecated_closure(self) -> Tuple[Set[str], Set[str]]:
        """计算弃用传递闭包。

        规则（plan.md §4.2）：被弃用表为闭包根 → 产出该表的步骤入闭包 →
        凡 target/extra 引用闭包内表、或引用闭包内步骤产出表的步骤递归入闭包。
        仅向下游单向传播，有限集单调扩张，必然终止。

        Returns:
            Tuple[Set[str], Set[str]]: (闭包内步骤 step_id 集, 闭包内表编号集)。
        """
        dep_tables: Set[str] = {t for t in self.deprecated_tables if t}
        dep_steps: Set[str] = set()
        changed = True
        while changed:
            changed = False
            for s in self.steps:
                if s.step_id in dep_steps:
                    continue
                refs = ([s.target_table_id] if s.target_table_id else [])
                refs.extend(extra_input_ids(s))
                hit = any(r in dep_tables for r in refs) or (
                    bool(s.output_table_id) and s.output_table_id in dep_tables
                )
                if hit:
                    dep_steps.add(s.step_id)
                    if s.output_table_id:
                        dep_tables.add(s.output_table_id)
                    changed = True
        return dep_steps, dep_tables

    # ------------------------------------------------------------------ #
    # JSON 互转
    # ------------------------------------------------------------------ #

    def to_dict(self, include_deprecated: bool = False) -> Dict[str, Any]:
        """导出为 v3.1 JSON 字典（step_id 重编号后与落盘一致）。

        本方法是「GUI 配置 → 后端执行参数」的翻译层（plan.md §4）：
        弃用闭包过滤（§4.2）、覆盖模式两步链展开（§4.3）、前端键剔除。

        Args:
            include_deprecated: False（默认）＝业务/执行口径——过滤弃用闭包、
                pop output_mode（翻译为覆盖两步链）、展开 _cp 合成步
                （save_json 执行交接单与运行配置留档）；True＝编辑态口径——
                保留弃用闭包、**保留 params.output_mode、不展开 _cp**
                （last_config/阶段往返暂存/模板保存，无损往返，2026-09-21
                审计 P1 修复）。uid：业务口径剔除（D-C2 前端键）；编辑态
                口径作为步骤第 9 键持久化（M5-a t_{uid} 机制，R6/E1 修正
                原"双口径均剔除"矛盾表述）。

        Returns:
            Dict[str, Any]: v3.1 参数文件字典。
        """
        self.renumber_steps()

        if include_deprecated:
            drop_steps: Set[str] = set()
            drop_tables: Set[str] = set()
        else:
            drop_steps, drop_tables = self._deprecated_closure()

        # 逻辑编号 → SQLite 物理表名（覆盖模式两步链需写回目标表物理名）
        sqlite_of = {t.table_id: t.sqlite_table for t in self.tables}

        steps_out: List[Dict[str, Any]] = []
        if not include_deprecated:
            # uid 重复防御（M5-a/§3.4）：重复者就地重生成，保证物理名唯一
            _seen_uids: Set[str] = set()
            for _s in self.steps:
                if _s.uid in _seen_uids:
                    logger.warning(
                        f"uid 重复，现场重生成: step={_s.step_id} uid={_s.uid}")
                    _s.uid = _new_uid()
                _seen_uids.add(_s.uid)
        # 派生表号 → 物理名 t_{uid}（R6/A1-P0-1：覆盖写回目标为派生表时
        # 供 cp 步解析真名；仅业务口径消费，无条件构建无害。
        # 位置约束：必须在 uid 重复防御之后——使用修正后的 uid）
        derived_phys = {st.output_table_id: f"t_{st.uid}"
                        for st in self.steps if st.output_table_id}
        for s in self.steps:
            if s.step_id in drop_steps:
                continue
            params = dict(s.params)
            # 前端键 output_mode：业务口径 pop（不入 v3.1，翻译为两步链）；
            # 编辑态口径 get 保留（无损往返，P1 修复）
            # 键名引用集中常量（R15/B-60）
            mode = (params.get(OUTPUT_MODE_KEY) if include_deprecated
                    else params.pop(OUTPUT_MODE_KEY, None))
            # 派生表物理名：业务口径固化为 t_{uid}（M5-a/K2）；编辑态剥离；
            # 同时剔除旧文件遗留键（§4.3）
            if include_deprecated:
                params.pop("output_table", None)
            elif s.output_table_id:
                params["output_table"] = f"t_{s.uid}"
            else:
                params.pop("output_table", None)
            step_dict = {
                "step_id": s.step_id,
                "type": s.type,
                "name": s.name,
                "target_table_id": s.target_table_id,
                "output_table_id": s.output_table_id,
                "params": params,
                "on_error": s.on_error,
                "retry_count": s.retry_count,
            }
            if include_deprecated:
                step_dict["uid"] = s.uid   # 编辑态第 9 键，居末位（K1/M5a-T2）
            steps_out.append(step_dict)
            # 覆盖原表 → 两步链（§4.3）：本步产出中间表，再复制写回目标表物理名
            # （filter/dedup 实现为先 DROP 目标再 CREATE，同名覆盖会删掉源表，
            #   故必须经中间表中转；copy_table 允许目标已存在，零后端改动）
            if (mode == OUTPUT_MODE_OVERWRITE and s.output_table_id
                    and not include_deprecated):
                # 三级回退（R6/A1-P0-1/D1①）：输入表物理名 → 派生表物理名
                # → 逻辑号（前两级 miss 均不应发生于合法 GUI 配置）
                target_phys = (sqlite_of.get(s.target_table_id)
                               or derived_phys.get(s.target_table_id)
                               or s.target_table_id)
                steps_out.append({
                    "step_id": f"{s.step_id}_cp",
                    "type": "copy_table",
                    "name": f"{s.name}（写回原表）",
                    "target_table_id": s.output_table_id,
                    "output_table_id": "",
                    "params": {"output_table": target_phys},
                    "on_error": s.on_error,
                    "retry_count": s.retry_count,
                })

        return {
            "__meta": {
                "schema_version": "3.1",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "name": self.workflow_name,
            "global": {"keep_db": False},
            "tables": [
                {
                    "table_id": t.table_id,
                    "alias": t.alias,
                    "source": {
                        "file": (t.source_path or t.file_path),
                        "sheet": t.sheet_name,
                        "header_row": t.header_row,
                    },
                    "sqlite_table": t.sqlite_table,
                }
                for t in self.tables
                if t.table_id not in drop_tables
            ],
            "steps": steps_out,
        }

    def save_json(self, path: Path,
                  extra_meta: Optional[Dict[str, Any]] = None) -> None:
        """落盘 v3.1 JSON 参数文件。

        Args:
            path: 目标路径。
            extra_meta: 追加进 ``__meta`` 的键值（R6/F6 实例标识等；
                不得覆盖 schema_version/created 既有键）。
        """
        data = self.to_dict()
        if extra_meta:
            for k, v in extra_meta.items():
                if k not in data["__meta"]:
                    data["__meta"][k] = v
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _collapse_copy_steps(self, raw_steps: List[Dict[str, Any]],
                             raw_tables: List[Dict[str, Any]]
                             ) -> List[Dict[str, Any]]:
        """业务口径存量文件的 _cp 合成步折叠迁移（2026-09-21 审计 P1-b）。

        识别 (step_id 以 "_cp" 结尾 + type=="copy_table") 的合成步，三级优先
        定位父步（①前邻 step_id==去后缀 ②全表搜同 id ③output_table_id==本步
        target），命中则父步 params 补 output_mode="overwrite_target" 并删除
        合成步；未命中保留原样并 warning（不静默丢）。纯函数式：入参不改，
        返回浅拷贝新列表。时序安全：renumber 仅发生于 to_dict，载入时
        step_id 仍为原始 S{n}_cp。
        """
        phys_to_tid = {t.get("sqlite_table", ""): t.get("table_id", "")
                       for t in raw_tables if isinstance(t, dict)}
        steps = [dict(s) for s in raw_steps if isinstance(s, dict)]
        out: List[Dict[str, Any]] = []
        for i, s in enumerate(steps):
            sid = str(s.get("step_id", ""))
            if not (sid.endswith("_cp") and s.get("type") == "copy_table"):
                out.append(s)
                continue
            parent_id = sid[:-3]
            parent: Optional[Dict[str, Any]] = None
            if out and str(out[-1].get("step_id", "")) == parent_id:
                parent = out[-1]
            else:
                for cand in out:
                    if str(cand.get("step_id", "")) == parent_id:
                        parent = cand
                        break
            if parent is None:
                tgt = s.get("target_table_id", "")
                for cand in out:
                    if cand.get("output_table_id", "") == tgt and tgt:
                        parent = cand
                        break
            if parent is None:
                logger.warning(
                    f"[models] _cp 合成步无法识别父步骤，按普通复制步保留: {sid}")
                out.append(s)
                continue
            p_params = dict(parent.get("params", {}))
            p_params[OUTPUT_MODE_KEY] = OUTPUT_MODE_OVERWRITE
            parent["params"] = p_params
            phys = (s.get("params") or {}).get("output_table", "")
            mapped = phys_to_tid.get(phys, "")
            if mapped and mapped != parent.get("target_table_id", ""):
                logger.warning(
                    f"[models] _cp 步 {sid} 物理名 {phys}（{mapped}）与父步目标 "
                    f"{parent.get('target_table_id', '')} 不一致，以父步为准")
        return out

    def load_from_dict(self, data: Dict[str, Any]) -> None:
        """从 v3.1 JSON 字典载入（模板应用/回退恢复）。

        不还原弃用态：弃用是本轮会话的编辑意图、不写入参数文件，
        载入后需由用户重新标记（plan.md §4.2①）。
        兼容旧文件 params 中的遗留 output_table 键（不报错，由 to_dict 剔除）。
        存量业务口径文件的 _cp 合成步经 _collapse_copy_steps 折叠回
        父步 output_mode（P1-b 迁移）。
        """
        self.workflow_name = str(data.get("name", "GUI 操作"))
        self.deprecated_tables.clear()
        self.tables = [
            TableEntry(
                table_id=t.get("table_id", ""),
                alias=t.get("alias", ""),
                sqlite_table=t.get("sqlite_table", ""),
                file_path=t.get("source", {}).get("file", ""),
                sheet_name=t.get("source", {}).get("sheet", ""),
                header_row=int(t.get("source", {}).get("header_row", 1)),
                uid=_new_uid(),
            )
            for t in data.get("tables", [])
        ]
        raw_steps = self._collapse_copy_steps(
            data.get("steps", []), data.get("tables", []))
        self.steps = [
            StepConfig(
                step_id=s.get("step_id", ""),
                type=s.get("type", ""),
                name=s.get("name", s.get("type", "")),
                target_table_id=s.get("target_table_id", ""),
                output_table_id=s.get("output_table_id", ""),
                params=dict(s.get("params", {})),
                on_error=s.get("on_error", "stop"),
                retry_count=int(s.get("retry_count", 3)),
                uid=str(s.get("uid", "") or _new_uid()),
            )
            for s in raw_steps
        ]
        self._next_step_num = len(self.steps) + 1
        self.reconcile()

    def load_session(self, registry: List[Dict[str, Any]],
                     data: Dict[str, Any]) -> None:
        """会话载入单一入口（2026-09-21 定稿 M2-T5/§7.5）。

        registry（阶段 1 输入表注册表）为表清单权威源；data 的 tables 字段
        载入后被 registry 覆盖（禁止外部 tables 覆盖 registry，根治 H2）。
        模板/暂存的步骤编号位置映射由调用方（页面层）在传入前完成。

        Args:
            registry: set_tables 格式 entries 列表。
            data: v3.1 字典（取 steps/name；tables 忽略）。
        """
        self.load_from_dict(data)
        self.set_tables(registry)


def extra_input_ids(step: StepConfig) -> List[str]:
    """步骤除目标表外的额外输入表编号（数据层单一来源，2026-09-20 M16）。

    mapping_match 取单张匹配表；merge_tables 取多张合并表；其余操作为空。
    边派生（gui/graph_edges.py）与弃用闭包均复用本函数，避免多处各自推导。

    Args:
        step: 步骤配置。

    Returns:
        List[str]: 额外输入表编号列表（去空，保持参数中的顺序）。
    """
    if step.type == "mapping_match":
        mt = str(step.params.get("match_table_id", "") or "")
        return [mt] if mt else []
    if step.type == "merge_tables":
        return [str(x) for x in (step.params.get("match_table_ids") or []) if str(x)]
    if step.type == "supervision_report":
        return [str(x) for x in (step.params.get("extra_table_ids") or []) if str(x)]
    return []


def alive_table_ids(tables: Iterable[Any], steps: Iterable[Any]) -> Set[str]:
    """存活表编号单一源（与 ``reconcile`` 的 alive 同口径，B-21/G-13）。

    口径＝输入表编号 ∪ 全部步骤产出编号，**含覆盖模式**
    （``output_mode="overwrite_target"``）步骤的中间产出编号——该编号在画布
    上不产生表节点（``gui.graph_edges.specs_from_model`` 不收录），但在生命
    周期账本中仍存活，故下游步骤引用它**不应**判悬空（消除"假悬空告警"）。

    边派生层（``gui.graph_edges``）与状态机（``reconcile``）共用本函数，
    保证两本账同源、不再各自演化。兼容两类入参（duck-typing）：数据层
    ``TableEntry``/``StepConfig``（``table_id``/``output_table_id``）与边派生
    视图 ``TableSpec``/``StepSpec``（``key``/``output_table``）。

    Args:
        tables: 表清单（数据层条目或边派生视图）。
        steps: 步骤清单（数据层配置或边派生视图）。

    Returns:
        Set[str]: 存活表编号集合。
    """
    alive: Set[str] = set()
    for t in tables:
        tid = getattr(t, "table_id", "") or getattr(t, "key", "")
        if tid:
            alive.add(tid)
    for s in steps:
        oid = getattr(s, "output_table_id", "") or getattr(s, "output_table", "")
        if oid:
            alive.add(oid)
    return alive


def default_params(type_name: str) -> Dict[str, Any]:
    """各类操作的新步骤默认参数（表单回填起点）。

    R15/B-69（原编号 P2-1）：**不再手写清单**——一律派生自引擎单一源
    `ops/step_executor.BUILTIN_OPS[type_name]["params_schema"]` 的默认值，
    与 `execute_step` 的缺省回退同源（闭合 §7 B9 双源）。

    Args:
        type_name: 操作类型名（STEP_CATALOG 键）。

    Returns:
        Dict[str, Any]: 参数默认值字典（未知操作返回空字典）。
    """
    from ops.step_executor import param_defaults
    return param_defaults(type_name)


def _txt_sidecar(path: str) -> str:
    """同主名 .txt 派生（等价 Path.with_suffix 语义，不引 pathlib）。"""
    dot = path.rfind(".")
    sep = max(path.rfind("/"), path.rfind("\\"))
    return (path[:dot] if dot > sep else path) + ".txt"


def collect_file_stats(model: WorkflowModel, engine_root: Path) -> Dict[str, List[str]]:
    """收集本次执行的输入/输出文件清单（报告页统计用）。

    R18/D1+：凡 params 含 output_path 的步骤均收集（不按操作类型硬编码）；
    supervision_report 另收集同主名 .txt（报告页"输出文件数"真实为 2）。
    """
    input_files: List[str] = []
    for t in model.tables:
        if t.file_path and t.file_path not in input_files:
            input_files.append(t.file_path)

    output_files: List[str] = []
    for s in model.steps:
        p = str(s.params.get("output_path", "") or "").strip()
        if p and p not in output_files:
            output_files.append(p)
        if p and s.type == "supervision_report":
            t = _txt_sidecar(p)
            if t not in output_files:
                output_files.append(t)

    return {"input_files": input_files, "output_files": output_files}
