"""W-03 DAG 可视化演示——伪后端（示例数据，可替换）。

用途：
    为前端 dag_viewer.py 提供纯标准库的数据访问接口，模拟真实重构输出
    （M0 后 graph/ 包）的数据形态；仅用于设计验证演示，不接引擎。

接口（契约见 ../plan.md §1.4，原 _agent/CONTRACTS.md v1.1 已并入；2026-09-16 动态化扩展）：
    get_meta() -> dict               # 流程元信息（含 total_steps）
    get_dag() -> dict                # tables/steps/statuses/fail_reasons/edges（深拷贝）
    get_node(key: str) -> dict|None  # 表/步骤详情（附 kind/status 等展示字段）
    set_status(key: str, status: str) -> bool  # 更新内存状态（不回写文件）
    -- 动态配置扩展（原 W-03_dynamic_dag_deep_test_PLAN §4.3，已并入 ../plan.md）--
    reset_state() -> None            # 重读 JSON 重建内存态（测试/场景驱动隔离用）
    recompute() -> None              # 全量重算：表集合/seq/is_end/config_state/edges
    add_step(op_type, anchor=None) -> str|None   # 按选中态插入新步骤（定案 1/5/6）
    remove_step(key) -> bool         # 删除步骤并级联（产表消失/下游悬空）
    update_params(key, params) -> (ok, config_state, missing)
    deprecate_table(key, flag) -> bool           # 显式弃用/恢复
    export_workflow() -> dict        # 导出当前 workflow（仅内存，不写文件）

边模型（2026-09-17 细节优化 ADR-3：边为后端单一事实源，前端只按 type 取样式）：
    get_dag()["edges"] = [edge, ...]，edge 字段见 _build_edges 文档字符串。

数据文件：
    data/workflow_demo.json —— 示例数据，可替换（接口不变）。
    模块级加载一次（UTF-8），之后内存持有；写接口仅改内存。
"""

import copy
import json
from pathlib import Path

from backend.func_registry import (default_params, get_op, is_end_op,
                                   op_name_cn, produce_label, produces_table)

# 数据文件路径：<项目根>/data/workflow_demo.json
_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "workflow_demo.json"

# 步骤状态合法值（W-02 F：无"未启动"档）
_VALID_STATUSES = ("pending", "running", "done", "failed")

# 起止标识虚拟 key（避开 _next_key/get_node 的 "T/S+纯数字" 命名空间）
START_KEY = "__start__"
END_KEY = "__end__"

_DATA: dict = {}
_TABLES: list = []
_STEPS: list = []
_STATUSES: dict = {}
_FAIL_REASONS: dict = {}
_STEP_KEYS: set = set()
_EDGES: list = []


def _load():
    """从 JSON 重建内存态（纯加载；派生字段由 recompute 补齐，见模块末尾初始化）。"""
    global _DATA, _TABLES, _STEPS, _STATUSES, _FAIL_REASONS, _STEP_KEYS, _EDGES
    _DATA = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    _TABLES = _DATA["tables"]
    _STEPS = _DATA["steps"]
    _STATUSES = dict(_DATA["initial_statuses"])
    _FAIL_REASONS = dict(_DATA.get("fail_reasons", {}))
    _STEP_KEYS = {step["key"] for step in _STEPS}
    _EDGES = []


_load()


def reset_state():
    """重读 JSON 重建内存态（丢弃全部动态修改；测试/场景驱动隔离用）。"""
    _load()
    recompute()


def _find_table(key):
    for t in _TABLES:
        if t["key"] == key:
            return t
    return None


def _find_step(key):
    for s in _STEPS:
        if s["key"] == key:
            return s
    return None


def _table_keys():
    return {t["key"] for t in _TABLES}


def _next_key(prefix, existing):
    nums = []
    for k in existing:
        if k.startswith(prefix) and k[len(prefix):].isdigit():
            nums.append(int(k[len(prefix):]))
    return "%s%d" % (prefix, (max(nums) + 1) if nums else 1)


def _missing_for(step, tkeys):
    """按注册表契约计算步骤缺失项（输入完整性校验，X6）。"""
    meta = get_op(step.get("op_type"))
    missing = []
    if meta is None:
        return ["未知操作类型"]
    tgt = step.get("target_table")
    if not tgt or tgt not in tkeys:
        missing.append("目标数据表")
    else:
        tt = _find_table(tgt)
        if tt and tt.get("deprecated"):
            missing.append("目标表已弃用")
    extras = [e for e in (step.get("extra_inputs") or [])]
    valid = [e for e in extras if e in tkeys]
    if len(valid) < meta["inputs"].get("extra_min", 0):
        missing.append("输入数据表不足")
    for e in extras:
        if e not in tkeys:
            missing.append("悬空输入表")
        else:
            te = _find_table(e)
            if te and te.get("deprecated"):
                missing.append("引用已弃用表")
    params = step.get("params") or {}
    for item in meta["params"]:
        key, label, _spec, req = item[0], item[1], item[2], item[3]
        if req and not str(params.get(key, "")).strip():
            missing.append(label)
    return missing


def _missing_refs(step, tkeys):
    """返回步骤引用了但已不存在的表 key 列表（悬空引用）。

    口径严格限定为"表不存在"：弃用表、缺参、输入不足等其它缺失原因由
    _missing_for 承载（供 config_state 与面板红字），避免 dangling 与
    deprecated 重复计数，也不改变画布角标「输入缺失」的既有触发条件。
    """
    refs = []
    tgt = step.get("target_table")
    if tgt:
        refs.append(tgt)
    for e in (step.get("extra_inputs") or []):
        if e:
            refs.append(e)
    return [r for r in refs if r not in tkeys]


def _normalize_end():
    """规范化 is_end：仅数组中最后一个结束类操作（注册表 kind=="end"）为结束步。

    对齐生产语义 is_end=(type=="export")（rpa_engine/gui/page_operation_config.py:525），
    保证结束标识唯一；无结束类操作时全部为 False（前端 fallback 到末步）。
    """
    last = -1
    for i, s in enumerate(_STEPS):
        s["is_end"] = False
        if is_end_op(s.get("op_type")):
            last = i
    if last >= 0:
        _STEPS[last]["is_end"] = True


def _end_step():
    """返回结束锚点步骤：is_end 步优先，否则末步（fallback）；空流程返回 None。"""
    if not _STEPS:
        return None
    for s in _STEPS:
        if s.get("is_end"):
            return s
    return _STEPS[-1]


def _uniq_edge_key(base, seen):
    """保证边 key 全集唯一（同一 (type,from,to,role) 重复时追加 #n 后缀）。"""
    if base not in seen:
        seen.add(base)
        return base
    n = 2
    while "%s#%d" % (base, n) in seen:
        n += 1
    key = "%s#%d" % (base, n)
    seen.add(key)
    return key


def _mk_edge(etype, src, dst, seen, role=None, label=None, missing=None):
    """构造一条边字典（字段契约见 _build_edges）。"""
    base = "%s:%s:%s" % (etype, src, dst)
    if role:
        base = "%s:%s" % (base, role)
    return {
        "key": _uniq_edge_key(base, seen),
        "type": etype,
        "from": src,
        "to": dst,
        "role": role,
        "label": label,
        "missing": missing,
    }


def _build_edges():
    """生成显式边列表（单一事实源；前端只按 type 取样式，不再自行推导）。

    五类边（2026-09-17 细节优化 ADR-3/§5.1 词表）：
      flow       起止连接边：__start__→首步、结束步→__end__（steps 非空恒 2 条）
      reference  数据引用边：表→步骤（role=target|extra）
      deprecated 弃用引用边：reference 的样式变体（该表 deprecated=True）
      produce    数据产出边：步骤→操作表（label 取注册表 produce_label）
      dangling   悬空标记边：缺失表→步骤（missing=缺失 key）

    edge 字段：key（稳定唯一）/type/from/to/role/label/missing。
    顺序稳定：flow → reference|deprecated（按表列序→消费者序）→ produce（按步骤序）
    → dangling（按步骤序），保证两次 recompute 后同一逻辑边 key 不变。
    """
    edges = []
    seen = set()
    tkeys = _table_keys()

    # 1) flow：起止连接边
    if _STEPS:
        edges.append(_mk_edge("flow", START_KEY, _STEPS[0]["key"], seen))
        end = _end_step()
        if end is not None:
            edges.append(_mk_edge("flow", end["key"], END_KEY, seen))

    # 2) reference / deprecated：按表列序 → 消费者序（与前端泳道渲染序一致）
    for t in _TABLES:
        dep = bool(t.get("deprecated"))
        etype = "deprecated" if dep else "reference"
        for s in _STEPS:
            if s.get("target_table") == t["key"]:
                edges.append(_mk_edge(etype, t["key"], s["key"], seen, role="target"))
            for e in (s.get("extra_inputs") or []):
                if e == t["key"]:
                    edges.append(_mk_edge(etype, t["key"], s["key"], seen, role="extra"))

    # 3) produce：步骤→操作表（按步骤序）
    for s in _STEPS:
        ot = s.get("output_table")
        if ot and ot in tkeys:
            edges.append(_mk_edge("produce", s["key"], ot, seen,
                                  label=produce_label(s.get("op_type"))))

    # 4) dangling：缺失表→步骤（按步骤序）
    for s in _STEPS:
        for mk in (s.get("missing_refs") or []):
            edges.append(_mk_edge("dangling", mk, s["key"], seen, missing=mk))

    return edges


def recompute():
    """全量重算（就地更新 _TABLES/_STEPS/_EDGES）：

    1. seq 按数组序重排 1..n；
    2. 表集合 = 输入表 ∪ 产表步骤输出（produces_table 判定；新产出自动建表，
       不再产出的派生表若无其他 producer 则移除）；
    3. mapping_match 的 params.match_table 同步为 extra_inputs[0]（单一事实源）；
    4. is_end 规范化（仅最后一个结束类操作为结束步）；
    5. 每步 missing_refs（悬空引用）与 config_state = ok / incomplete；
    6. 重建显式边列表 _EDGES（五类边，见 _build_edges）。
    """
    global _EDGES
    for i, s in enumerate(_STEPS):
        s["seq"] = i + 1
    tkeys = _table_keys()

    for s in _STEPS:
        op = s.get("op_type")
        params = s.setdefault("params", {})
        if op == "mapping_match" and params.get("match_table"):
            s["extra_inputs"] = [params["match_table"]]
        if produces_table(op, params):
            ot = s.get("output_table")
            if not ot or ot not in tkeys:
                ot = _next_key("T", tkeys)
                _TABLES.append({
                    "key": ot,
                    "display": op_name_cn(op) + "结果",
                    "is_input": False,
                    "producer_step": s["key"],
                    "deprecated": False,
                    "business_desc": "由「%s」产生的操作表" % op_name_cn(op),
                })
                tkeys.add(ot)
            s["output_table"] = ot
            tt = _find_table(ot)
            if tt:
                tt["producer_step"] = s["key"]
                tt["is_input"] = False
        else:
            old = s.get("output_table")
            s["output_table"] = None
            if old and old in tkeys:
                other = [x for x in _STEPS
                         if x is not s and x.get("output_table") == old]
                tt = _find_table(old)
                if not other and tt and not tt.get("is_input"):
                    _TABLES.remove(tt)
                    tkeys.discard(old)

    # 4) is_end 规范化（结束标识唯一；无结束类操作时全 False）
    _normalize_end()

    # 5) 悬空引用与配置状态（missing_refs 口径仅"表不存在"，见 _missing_refs）
    tkeys_now = _table_keys()
    for s in _STEPS:
        s["missing_refs"] = _missing_refs(s, tkeys_now)
        s["config_state"] = "incomplete" if _missing_for(s, tkeys_now) else "ok"

    # 6) 重建显式边列表（单一事实源）
    _EDGES = _build_edges()


def get_meta() -> dict:
    """返回流程元信息：JSON meta 三字段 + 计算字段 total_steps。"""
    meta = dict(_DATA["meta"])
    meta["total_steps"] = len(_STEPS)
    return meta


def get_dag() -> dict:
    """返回 DAG 全量数据：tables / steps / statuses / fail_reasons / edges（深拷贝）。

    edges 为显式边列表（2026-09-17 细节优化 ADR-3：边语义的单一事实源），
    前端只按 edge["type"] 取样式，不再自行推导连线与悬空。
    """
    return copy.deepcopy({
        "tables": _TABLES,
        "steps": _STEPS,
        "statuses": _STATUSES,
        "fail_reasons": _FAIL_REASONS,
        "edges": _EDGES,
    })


def get_node(key: str) -> dict | None:
    """返回指定表/步骤的详情字典；未知 key 返回 None。"""
    if not isinstance(key, str):
        return None
    if key.startswith("T"):
        table = _find_table(key)
        if table:
            node = copy.deepcopy(table)
            node["kind"] = "table"
            return node
        return None
    if key.startswith("S"):
        step = _find_step(key)
        if step:
            node = copy.deepcopy(step)
            node["kind"] = "step"
            node["status"] = _STATUSES.get(key)
            node["fail_reason"] = _FAIL_REASONS.get(key)
            return node
        return None
    return None


def set_status(key: str, status: str) -> bool:
    """更新指定步骤的内存状态；成功返回 True，失败返回 False。"""
    if not isinstance(key, str) or not isinstance(status, str):
        return False
    if status not in _VALID_STATUSES:
        return False
    if key not in _STEP_KEYS:
        return False
    _STATUSES[key] = status
    return True


# ---------------------------------------------------------------------------
# 动态配置扩展（2026-09-16）
# ---------------------------------------------------------------------------

def _resolve_insert_index(anchor):
    """按定案 1/5/6 解析插入位置索引。

    2026-09-17 细节优化：所有分支统一过 _tail_adjust —— 任何锚点都不得把新步骤
    插到结束步之后（原 ("step",k) 分支缺此保护，选中结束步时会插到其后）。
    """
    n = len(_STEPS)

    def _tail_adjust(idx):
        # 统一保护：不插到 is_end 步骤之后（定案 6 推广）。
        # 说明：该保护针对"追加到末尾"语义；若数据本身已损坏（is_end 步不在末位），
        # 锚点插到 is_end 之后的既有步骤后面时仍会落在结束步之后——属异常数据，
        # 不做静默重排（重排会改变用户流程顺序），由 _normalize_end 保证标识唯一。
        if idx >= n and n and _STEPS[-1].get("is_end"):
            return n - 1
        return idx

    if anchor is None:
        return _tail_adjust(n)
    kind, key = anchor
    if kind == "step":
        for i, s in enumerate(_STEPS):
            if s["key"] == key:
                return _tail_adjust(i + 1)
        return _tail_adjust(n)
    if kind == "table":
        t = _find_table(key)
        if not t:
            return _tail_adjust(n)
        if not t.get("is_input") and t.get("producer_step"):
            for i, s in enumerate(_STEPS):
                if s["key"] == t["producer_step"]:
                    return _tail_adjust(i + 1)
            return _tail_adjust(n)
        last = -1
        for i, s in enumerate(_STEPS):
            if s.get("target_table") == key or key in (s.get("extra_inputs") or []):
                last = i
        if last >= 0:
            return _tail_adjust(last + 1)
        return _tail_adjust(n)
    return _tail_adjust(n)


def add_step(op_type, anchor=None):
    """插入新步骤（注册表驱动）；返回新步骤 key，未知操作返回 None。

    anchor：None=流程末尾（末步 export 则插其前）；("step",k)=k 之后；
    ("table",k)=操作表在其产出步骤后 / 输入表在其最后消费者后（定案 1）。
    新步骤参数取注册表默认值、config_state 由 recompute 判定（通常 incomplete）；
    is_end 由注册表 kind=="end" 派生（原硬编码 False 会让新增的结果导出步骤
    拿不到结束标识），唯一性由 recompute 的 _normalize_end 保证。
    """
    if get_op(op_type) is None:
        return None
    key = _next_key("S", _STEP_KEYS)
    step = {
        "key": key,
        "seq": 0,
        "name": op_name_cn(op_type),
        "op_type": op_type,
        "business_desc": "新添加的%s（待配置）" % op_name_cn(op_type),
        "target_table": None,
        "extra_inputs": [],
        "output_table": None,
        "is_end": is_end_op(op_type),
        "params": default_params(op_type),
        "config_state": "incomplete",
        "missing_refs": [],
    }
    idx = _resolve_insert_index(anchor)
    _STEPS.insert(idx, step)
    _STEP_KEYS.add(key)
    _STATUSES[key] = "pending"
    recompute()
    return key


def remove_step(key):
    """删除步骤并级联：其产出表若无其他 producer 则消失；重算下游悬空/incomplete。"""
    step = _find_step(key)
    if not step:
        return False
    out = step.get("output_table")
    _STEPS.remove(step)
    _STEP_KEYS.discard(key)
    _STATUSES.pop(key, None)
    _FAIL_REASONS.pop(key, None)
    if out:
        tt = _find_table(out)
        other = [x for x in _STEPS if x.get("output_table") == out]
        if tt and not tt.get("is_input") and not other:
            _TABLES.remove(tt)
    recompute()
    return True


def update_params(key, params):
    """写回步骤配置并重算；返回 (ok, config_state, missing)。

    fields 中保留键直接写字段：target_table→step.target_table、
    extra_inputs→step.extra_inputs（list 或单值）；其余键入 step.params
    （与注册表默认值合并）。
    """
    step = _find_step(key)
    if not step or not isinstance(params, dict):
        return (False, step.get("config_state") if step else "incomplete", [])
    merged = default_params(step.get("op_type"))
    merged.update(step.get("params") or {})
    for k, v in params.items():
        if k == "target_table":
            step["target_table"] = v or None
        elif k == "extra_inputs":
            step["extra_inputs"] = list(v) if isinstance(v, (list, tuple)) else ([v] if v else [])
        else:
            merged[k] = v
    step["params"] = merged
    recompute()
    missing = _missing_for(step, _table_keys())
    return (step["config_state"] == "ok", step["config_state"], missing)


def deprecate_table(key, flag):
    """显式弃用/恢复表（弃用表仍显示；消费者步骤经 recompute 判 incomplete）。"""
    t = _find_table(key)
    if not t:
        return False
    t["deprecated"] = bool(flag)
    recompute()
    return True


def export_workflow():
    """导出当前 workflow dict（仅内存，不写文件；定案 4）。

    missing_refs 属画布视图派生字段（非工作流参数），导出时剔除以保持契约干净；
    边列表同为派生物，不入导出结构。
    """
    steps = []
    for s in _STEPS:
        item = copy.deepcopy(s)
        item.pop("missing_refs", None)
        steps.append(item)
    return copy.deepcopy({
        "meta": _DATA["meta"],
        "tables": _TABLES,
        "steps": steps,
    })


# 模块加载后立即重算一次：补齐 is_end 规范化 / missing_refs / edges 等派生字段
# （_load() 为纯加载，不能在其内部调用 recompute —— 那时 recompute 尚未定义）
recompute()
