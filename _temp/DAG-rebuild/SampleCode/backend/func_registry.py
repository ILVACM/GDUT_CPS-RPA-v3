"""W-03 动态 DAG 演示——功能元数据注册表（单一事实源）。

语义同源生产 `rpa_engine/gui/models.py` 的 STEP_CATALOG / OUTPUT_OPS / STEP_KIND
（只读对齐，不 import 生产代码）：
- kind：end / merge / fork / sequential（流程图性质分类）
- produces_table：是否产生新操作表（filter/dedup 受 output_mode 参数影响）
- produce_label：数据产出边的画布标签文案（2026-09-17 细节优化 ADR-4；
  不产表操作为 None；「数据表复制」专用"复制新表"以区分普通产表）
- inputs：target 必填 + extra_min 最少额外输入表数
- params：参数 schema 元组 (key, 中文标签, 类型, 必填[, 默认值])
  类型：text→QLineEdit；table→QComboBox(当前表)；enum:a|b→QComboBox

演示前端（按钮/参数面板/边标签）与伪后端（recompute/校验/边生成）共用本注册表，
杜绝硬编码。
"""

FUNC_REGISTRY = {
    "filter": dict(
        name_cn="条件筛选", kind="fork", produces_table=True, produce_label="新表",
        inputs=dict(target=True, extra_min=0),
        params=[("conditions", "筛选条件", "text", True),
                ("output_mode", "结果保存方式", "enum:new_table|overwrite_target", False, "new_table")]),
    "dedup": dict(
        name_cn="条件去重", kind="fork", produces_table=True, produce_label="新表",
        inputs=dict(target=True, extra_min=0),
        params=[("columns", "去重列", "text", True),
                ("keep", "保留", "enum:first|last", False, "first"),
                ("output_mode", "结果保存方式", "enum:new_table|overwrite_target", False, "new_table")]),
    "mapping_match": dict(
        name_cn="跨表映射匹配", kind="merge", produces_table=True, produce_label="新表",
        inputs=dict(target=True, extra_min=1),
        params=[("match_table", "匹配表", "table", True),
                ("match_columns", "匹配列", "text", True),
                ("join_mode", "连接方式", "enum:left|inner|outer", False, "left")]),
    "aggregate": dict(
        name_cn="条件统计", kind="fork", produces_table=True, produce_label="新表",
        inputs=dict(target=True, extra_min=0),
        params=[("group_by", "分组列", "text", True),
                ("metrics", "统计列", "text", True),
                ("agg_func", "统计方式", "enum:count|sum|avg|max|min", False, "sum")]),
    "copy_table": dict(
        name_cn="数据表复制", kind="fork", produces_table=True, produce_label="复制新表",
        inputs=dict(target=True, extra_min=0),
        params=[]),
    "merge_tables": dict(
        name_cn="数据表合并", kind="merge", produces_table=True, produce_label="新表",
        inputs=dict(target=True, extra_min=1),
        params=[]),
    "rename_columns": dict(
        name_cn="表头名称修改", kind="sequential", produces_table=False, produce_label=None,
        inputs=dict(target=True, extra_min=0),
        params=[("mapping", "改名对照", "text", True)]),
    "convert_dtype": dict(
        name_cn="数据类型转换", kind="sequential", produces_table=False, produce_label=None,
        inputs=dict(target=True, extra_min=0),
        params=[("columns", "转换列", "text", True)]),
    "export": dict(
        name_cn="结果导出", kind="end", produces_table=False, produce_label=None,
        inputs=dict(target=True, extra_min=0),
        params=[("file_name", "导出文件名", "text", True)]),
}

# 工具栏主按钮（定案 5）；其余收纳「更多功能 ▾」下拉
MAIN_BUTTONS = ["filter", "mapping_match", "aggregate", "copy_table"]
MORE_BUTTONS = ["dedup", "merge_tables", "rename_columns", "convert_dtype", "export"]

# output_mode 可切换"覆盖原表"的操作（X3）
_OVERWRITABLE = ("filter", "dedup")


def get_op(op_type):
    """返回操作元数据 dict；未知操作返回 None。"""
    return FUNC_REGISTRY.get(op_type)


def op_name_cn(op_type):
    """操作中文显示名；未知操作返回操作名本身。"""
    meta = FUNC_REGISTRY.get(op_type)
    return meta["name_cn"] if meta else str(op_type)


def default_params(op_type):
    """按 schema 生成默认参数字典（必填项为空串，可选项取默认值）。"""
    meta = FUNC_REGISTRY.get(op_type)
    if not meta:
        return {}
    out = {}
    for item in meta["params"]:
        key = item[0]
        out[key] = item[4] if len(item) > 4 else ""
    return out


def required_param_keys(op_type):
    """必填参数 key 列表。"""
    meta = FUNC_REGISTRY.get(op_type)
    if not meta:
        return []
    return [item[0] for item in meta["params"] if item[3]]


def produces_table(op_type, params=None):
    """该操作在当前参数下是否产生新操作表。

    filter/dedup 且 output_mode=overwrite_target 时不产新表（X3）。
    """
    meta = FUNC_REGISTRY.get(op_type)
    if not meta:
        return False
    if not meta["produces_table"]:
        return False
    if op_type in _OVERWRITABLE and (params or {}).get("output_mode") == "overwrite_target":
        return False
    return True


def is_end_op(op_type):
    """该操作是否为流程结束类操作（注册表 kind=="end"，对齐生产 is_end 语义）。"""
    meta = FUNC_REGISTRY.get(op_type)
    return bool(meta and meta.get("kind") == "end")


def produce_label(op_type):
    """数据产出边的画布标签文案；不产表/未知操作返回 None。"""
    meta = FUNC_REGISTRY.get(op_type)
    if not meta:
        return None
    return meta.get("produce_label")
