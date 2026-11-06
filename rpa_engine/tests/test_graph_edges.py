"""五类边契约不变量测试（2026-09-20 M16/M-d）。

蓝本：SampleCode/tests/test_dynamic.py 的 EdgeModelTest（12 项不变量），
按生产实现（gui.graph_edges + gui.models）移植；不 import 演示代码。

契约依据：_temp/DAG-rebuild/plan.md §1.4（edges v1.1）与 M16 实现规格。
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gui.graph_edges import (EDGE_FIELDS, EDGE_TYPES, END_KEY, START_KEY,  # noqa: E402
                             build_edges, specs_from_model)
from gui.models import STEP_CATALOG, WorkflowModel, produce_label  # noqa: E402


def make_model() -> WorkflowModel:
    """构造 5 步 / 2 输入表 / 3 派生表的测试工作流。

    S1 数据类型转换(T1，无产表) → S2 条件筛选(T1→T3) →
    S3 跨表映射匹配(T3+T2→T4) → S4 条件统计(T2→T5) → S5 结果导出(T4，结束步)
    """
    m = WorkflowModel("边契约测试流程")
    m.set_tables([
        {"table_id": "T1", "alias": "电费明细", "sqlite_table": "t1",
         "file_path": "a.xlsx", "sheet_name": "Sheet1", "header_row": 1},
        {"table_id": "T2", "alias": "用户台账", "sqlite_table": "t2",
         "file_path": "b.xlsx", "sheet_name": "Sheet1", "header_row": 1},
    ])
    s1 = m.add_step("convert_dtype")
    s1.target_table_id = "T1"
    s1.params = {"column": "amt", "from_type": "TEXT", "to_type": "REAL"}

    s2 = m.add_step("filter")
    s2.target_table_id = "T1"
    s2.params = {"conditions": [{"column": "amt", "op": ">", "value": "100"}],
                 "logic": "AND"}

    s3 = m.add_step("mapping_match")
    s3.target_table_id = s2.output_table_id
    s3.params = {"match_table_id": "T2",
                 "match_columns": {"户号": "户号"},
                 "mode": "left_join"}

    s4 = m.add_step("aggregate")
    s4.target_table_id = "T2"
    s4.params = {"group_by": ["区域"],
                 "metrics": [{"column": "*", "func": "count", "alias": "计数"}],
                 "conditions": []}

    s5 = m.add_step("export")
    s5.target_table_id = s3.output_table_id
    s5.params = {"output_path": "out.xlsx", "sheet_name": "数据"}

    m.renumber_steps()
    return m


def build(model: WorkflowModel):
    """按生产装配路径派生边（返回 (step_specs, table_specs, edges)）。"""
    step_specs, table_specs = specs_from_model(model)
    return step_specs, table_specs, build_edges(
        step_specs, table_specs, model.deprecated_tables)


def by_type(edges, etype):
    return [e for e in edges if e.type == etype]


class EdgeModelTest(unittest.TestCase):
    """五类边 12 项不变量（与蓝本一一对应）。"""

    def setUp(self) -> None:
        self.model = make_model()
        self.steps, self.tables, self.edges = build(self.model)

    # 1) 字段契约与类型枚举
    def test_edge_schema_and_type_enum(self):
        self.assertTrue(self.edges)
        for e in self.edges:
            d = e.to_dict()
            self.assertEqual(set(d.keys()), set(EDGE_FIELDS))
            self.assertIn(e.type, EDGE_TYPES)

    # 2) reference 计数 = 有效引用数
    def test_reference_count(self):
        refs = by_type(self.edges, "reference")
        expect = 0
        tkeys = {t.key for t in self.tables}
        for s in self.steps:
            for r in [s.target_table] + list(s.extra_inputs):
                if r and r in tkeys:
                    expect += 1
        self.assertEqual(len(refs), expect)
        # T1→S1、T1→S2、T3→S3(target)、T2→S3(extra)、T2→S4、T4→S5
        self.assertEqual(expect, 6)

    # 3) reference 角色记录（target/extra）
    def test_reference_role_recorded(self):
        roles = {e.role for e in by_type(self.edges, "reference")}
        self.assertEqual(roles, {"target", "extra"})

    # 4) produce 计数与标签
    def test_produce_count_and_label(self):
        prod = by_type(self.edges, "produce")
        self.assertEqual(len(prod), 3)          # T3(filter)/T4(mapping)/T5(aggregate)
        for e in prod:
            step = next(s for s in self.steps if s.key == e.src)
            self.assertEqual(e.label, produce_label(step.op_type))
            self.assertEqual(e.dst, step.output_table)

    # 5) flow 边：起止各一条
    def test_flow_edges(self):
        flow = by_type(self.edges, "flow")
        self.assertEqual(len(flow), 2)
        self.assertEqual(flow[0].src, START_KEY)
        self.assertEqual(flow[0].dst, self.steps[0].key)
        self.assertEqual(flow[1].dst, END_KEY)
        end = next(s for s in self.steps if s.is_end)
        self.assertEqual(flow[1].src, end.key)
        self.assertEqual(end.op_type, "export")

    # 6) 空流程 flow 为 0
    def test_flow_zero_when_empty(self):
        edges = build_edges([], [], set())
        self.assertEqual(edges, [])

    # 7) dangling 计数 = 缺失引用数
    def test_dangling_count(self):
        self.assertEqual(by_type(self.edges, "dangling"), [])
        self.model.steps[2].params["match_table_id"] = "T9"   # 不存在的表
        _steps, _tables, edges = build(self.model)
        dang = by_type(edges, "dangling")
        self.assertEqual(len(dang), 1)
        self.assertEqual(dang[0].src, "T9")
        self.assertEqual(dang[0].missing, "T9")
        self.assertEqual(dang[0].dst, self.model.steps[2].step_id)

    # 8) missing 作用域：仅"表不存在"，弃用/缺参不计入
    def test_missing_refs_scope(self):
        self.model.deprecate_table("T2", True)
        _steps, _tables, edges = build(self.model)
        self.assertEqual(by_type(edges, "dangling"), [])   # 弃用不算悬空
        # 缺参（conditions 为空）同样不计入 dangling
        self.model.steps[1].params["conditions"] = []
        _s, _t, edges2 = build(self.model)
        self.assertEqual(by_type(edges2, "dangling"), [])

    # 9) deprecated 边：弃用表的引用边转类型
    def test_deprecated_edges(self):
        self.model.deprecate_table("T2", True)
        _steps, _tables, edges = build(self.model)
        dep = by_type(edges, "deprecated")
        self.assertEqual(len(dep), 2)      # T2→S3(extra)、T2→S4(target)
        self.assertEqual({e.src for e in dep}, {"T2"})
        self.assertEqual({e.role for e in dep}, {"target", "extra"})
        # 弃用边不计入 reference（互斥且穷尽）
        self.assertEqual(len(by_type(edges, "reference")), 4)

    # 10) key 全集唯一且两次派生稳定
    def test_edge_key_stable_unique(self):
        keys = [e.key for e in self.edges]
        self.assertEqual(len(keys), len(set(keys)))
        _s, _t, again = build(make_model())
        self.assertEqual([e.key for e in again], keys)

    # 11) 虚拟端点不与真实节点冲突
    def test_virtual_key_not_node(self):
        node_keys = {t.key for t in self.tables} | {s.key for s in self.steps}
        self.assertNotIn(START_KEY, node_keys)
        self.assertNotIn(END_KEY, node_keys)
        for e in by_type(self.edges, "flow"):
            self.assertIn(e.src, node_keys | {START_KEY})
            self.assertIn(e.dst, node_keys | {END_KEY})

    # 12) 边为派生物，不进导出结构
    def test_edges_not_in_export(self):
        data = self.model.to_dict()
        self.assertNotIn("edges", data)
        for s in data["steps"]:
            self.assertNotIn("missing_refs", s)
            self.assertEqual(
                set(s.keys()),
                {"step_id", "type", "name", "target_table_id",
                 "output_table_id", "params", "on_error", "retry_count"})

    # 附：生成顺序稳定（flow → reference|deprecated → produce → dangling）
    def test_generation_order(self):
        ranks = [{"flow": 0, "reference": 1, "deprecated": 1,
                  "produce": 3, "dangling": 4}[e.type] for e in self.edges]
        self.assertEqual(ranks, sorted(ranks))
        self.assertEqual(ranks[0], 0)
        self.assertEqual(ranks[-1], 3)          # 本 fixture 无悬空，末类为 produce

    # 附：注册表键集一致（防漂移）
    # R15/B-67：引用 STEP_COUNT 单一常量，新增功能函数时自动同步（不再手改「9」）
    def test_catalog_key_set(self):
        from gui.models import STEP_COUNT
        self.assertEqual(len(STEP_CATALOG), STEP_COUNT)


class CollisionDetectionTest(unittest.TestCase):
    """撞号检测三场景（2026-09-21 定稿 M4-T1/FF1）。

    R6/F5（2026-09-24）：graph_edges.detect_table_id_collisions 门面已删除，
    本组改用唯一生产入口 WorkflowModel.validate_table_ids_unique()。
    """

    def _model(self):
        from gui.models import WorkflowModel
        m = WorkflowModel()
        m.set_tables([
            {"table_id": "T1", "alias": "a", "sqlite_table": "t1"},
            {"table_id": "T2", "alias": "b", "sqlite_table": "t2"},
        ])
        return m

    def test_no_collision(self):
        m = self._model()
        m.add_step("filter")
        m.add_step("aggregate")
        self.assertEqual(m.validate_table_ids_unique(), [])

    def test_single_collision(self):
        m = self._model()
        s1 = m.add_step("filter")
        s2 = m.add_step("filter")
        s2.output_table_id = s1.output_table_id
        self.assertEqual(m.validate_table_ids_unique(),
                         [s1.output_table_id])

    def test_collision_with_input_table(self):
        m = self._model()
        s1 = m.add_step("filter")
        s1.output_table_id = "T2"   # 与输入表撞号
        self.assertEqual(m.validate_table_ids_unique(), ["T2"])


if __name__ == "__main__":
    unittest.main()
