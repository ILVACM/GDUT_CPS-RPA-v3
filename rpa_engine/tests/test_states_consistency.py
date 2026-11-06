"""R6/E4（P2-3）：两本账对账——模型 table_states vs 画布边派生态。

防漂移门禁：reconcile 的状态账本与 graph_edges 的边类型派生（单一事实
源，五类边 flow/reference/deprecated/produce/dangling）必须口径一致；
任一侧变更导致分叉时本用例即红。

纯标准库 unittest（graph_edges 无 Qt 依赖，headless import 安全）。执行：
    cd rpa_engine && python -m unittest discover -s tests
"""

import unittest

from gui.graph_edges import build_edges, specs_from_model
from gui.models import WorkflowModel


def _model() -> WorkflowModel:
    m = WorkflowModel()
    m.set_tables([
        {"table_id": "T1", "alias": "员工", "sqlite_table": "t1"},
        {"table_id": "T2", "alias": "标准", "sqlite_table": "t2"},
    ])
    s1 = m.add_step("filter")            # T1 → T101
    s2 = m.add_step("mapping_match")     # T101 × T2 → T102
    s2.params = {"match_table_id": "T2",
                 "match_columns": {"a": "a"}, "mode": "inner_join"}
    s2.target_table_id = s1.output_table_id
    s3 = m.add_step("aggregate")         # T102 → 覆盖写回（不产表）
    s3.target_table_id = s2.output_table_id
    s3.params = {"group_by": ["a"],
                 "metrics": [{"func": "count", "column": "*", "alias": "n"}],
                 "output_mode": "overwrite_target"}
    return m


def _edges_of(m: WorkflowModel):
    m.reconcile()
    step_specs, table_specs = specs_from_model(m)
    return build_edges(step_specs, table_specs), step_specs, table_specs


class StatesConsistencyTest(unittest.TestCase):

    def test_produce_reference_consistent(self):
        m = _model()
        edges, _, table_specs = _edges_of(m)
        t101 = m.steps[0].output_table_id
        # 模型账本：T101 被 S2 引用
        self.assertEqual(m.table_states.get(t101), "referenced")
        # 画布账本：存在 S1 的 produce 边与涉及 T101 的 reference 边
        prod = [e for e in edges if e.type == "produce"]
        self.assertTrue(any(t101 in (e.src, e.dst) for e in prod),
                        f"produce 边缺失 T101: {[(e.src, e.dst) for e in prod]}")
        ref = [e for e in edges if e.type == "reference"]
        self.assertTrue(any(t101 in (e.src, e.dst) for e in ref))
        # 派生表节点在位（产表步骤收录）
        self.assertIn(t101, {t.key for t in table_specs})

    def test_overwrite_no_produce_edge_consistent(self):
        m = _model()
        edges, _, table_specs = _edges_of(m)
        s3 = m.steps[2]
        t103 = s3.output_table_id
        # 模型账本：overwritten＝产出步自身持覆盖模式（reconcile L571-574
        # 口径：produced_by[tid].params.output_mode=="overwrite_target"）
        self.assertEqual(m.table_states.get(t103), "overwritten")
        # 画布账本：覆盖父步无 produce 边、其输出表不收录为表节点
        #（specs_from_model：覆盖模式为原地修改，不产生表节点）
        prod_s3 = [e for e in edges
                   if e.type == "produce" and s3.step_id in (e.src, e.dst)]
        self.assertEqual(prod_s3, [])
        self.assertNotIn(t103, {t.key for t in table_specs})
        # T102（被 S3 引用的上游表）两本账均为 referenced
        t102 = m.steps[1].output_table_id
        self.assertEqual(m.table_states.get(t102), "referenced")
        ref = [e for e in edges if e.type == "reference"]
        self.assertTrue(any(t102 in (e.src, e.dst) for e in ref))

    def test_deprecated_consistent(self):
        m = _model()
        m.deprecate_table("T2", True)
        edges, _, _ = _edges_of(m)
        # 模型账本：T2 弃用
        self.assertEqual(m.table_states.get("T2"), "deprecated")
        # 画布账本：T2 的 reference 边升级为 deprecated 类型
        dep = {e.src for e in edges if e.type == "deprecated"}
        self.assertIn("T2", dep)

    def test_dangling_consistent(self):
        m = _model()
        s4 = m.add_step("dedup")
        s4.target_table_id = "T999"      # 引用不存在的编号
        s4.params = {"key_columns": ["a"], "keep": "first"}
        edges, _, _ = _edges_of(m)
        # 模型账本：T999 悬空
        self.assertEqual(m.table_states.get("T999"), "dangling")
        # 画布账本：dangling 边指向该步骤
        dang = [e for e in edges if e.type == "dangling"]
        self.assertTrue(any(e.dst == s4.step_id for e in dang),
                        f"dangling 边缺失: {[(e.src, e.dst) for e in dang]}")

    def test_input_declared_consistent(self):
        m = _model()
        edges, _, table_specs = _edges_of(m)
        self.assertIn(m.table_states.get("T1"), ("declared", "referenced"))
        self.assertIn("T1", {t.key for t in table_specs})


if __name__ == "__main__":
    unittest.main()
