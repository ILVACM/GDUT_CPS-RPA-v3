"""W-03 动态配置语义单元测试（unittest，纯标准库）。

运行方式（在 SampleCode 目录下）：
    python -m unittest discover -s tests -v

覆盖（原 W-03_dynamic_dag_deep_test_PLAN §13，已并入 ../plan.md）：插入三态位置（含 export 前插）、
删除级联（表消失/悬空 incomplete/statuses 清理）、update_params 校验、
弃用（标记/恢复/消费者 incomplete）、表集合推导（overwrite/copy/export/sequential）、
export_workflow 完整性、边界（删首/删末/空流程/弃用表加消费者）、reset 隔离。

2026-09-17 细节优化新增覆盖：边模型不变量（EdgeModelTest：五类边 schema/计数/
role/label/key 唯一稳定/虚拟 key 隔离/导出契约）、起止连接边自适应（删首步跟随、
删结束步 fallback、空流程 0 条）、is_end 派生与唯一性、锚点选中结束步仍插其前、
missing_refs 口径隔离（弃用与缺参不计入悬空）。
"""

import sys
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend import mock_backend as mb  # noqa: E402


class DynBase(unittest.TestCase):
    """每个用例前重置内存态，防单例污染（X15）。"""

    def setUp(self):
        mb.reset_state()

    def keys(self):
        return [s["key"] for s in mb.get_dag()["steps"]]

    def table_keys(self):
        return [t["key"] for t in mb.get_dag()["tables"]]

    def step(self, key):
        for s in mb.get_dag()["steps"]:
            if s["key"] == key:
                return s
        return None

    def edges(self, etype=None):
        """取当前边列表（可按 type 过滤）；边为后端单一事实源（ADR-3）。"""
        es = mb.get_dag()["edges"]
        return [e for e in es if etype is None or e["type"] == etype]


class InsertPositionTest(DynBase):
    """插入三态位置（定案 1/5/6）。"""

    def test_no_anchor_before_trailing_export(self):
        k = mb.add_step("filter", None)
        order = self.keys()
        self.assertEqual(order[-2], k)          # 末步 export 之前
        self.assertEqual(order[-1], "S5")

    def test_anchor_step_inserts_after(self):
        k = mb.add_step("aggregate", ("step", "S1"))
        order = self.keys()
        self.assertEqual(order[order.index("S1") + 1], k)

    def test_anchor_derived_table_after_producer(self):
        k = mb.add_step("copy_table", ("table", "T3"))   # T3 由 S1 产出
        order = self.keys()
        self.assertEqual(order[order.index("S1") + 1], k)

    def test_anchor_input_table_after_last_consumer(self):
        k = mb.add_step("copy_table", ("table", "T2"))   # 消费者 S2(3)/S4(5)
        order = self.keys()
        self.assertEqual(order[order.index("S4") + 1], k)

    def test_anchor_input_table_no_consumer_tail(self):
        mb.remove_step("S2")
        mb.remove_step("S4")                            # T2 无消费者
        k = mb.add_step("copy_table", ("table", "T2"))
        order = self.keys()
        self.assertEqual(order[-2], k)                  # 末尾 export 前

    def test_new_step_incomplete_and_pending(self):
        k = mb.add_step("filter", None)
        self.assertEqual(self.step(k)["config_state"], "incomplete")
        self.assertEqual(mb.get_dag()["statuses"][k], "pending")

    def test_anchor_end_step_inserts_before(self):
        """锚点选中结束步时，新步骤仍插到其前（_tail_adjust 全分支统一）。"""
        k = mb.add_step("filter", ("step", "S5"))
        order = self.keys()
        self.assertEqual(order[-1], "S5")           # 结束步恒在末位
        self.assertEqual(order[-2], k)

    def test_unknown_op_returns_none(self):
        self.assertIsNone(mb.add_step("no_such_op", None))


class TableDerivationTest(DynBase):
    """表集合推导（要点 3/4）。"""

    def test_new_filter_creates_table(self):
        before = len(self.table_keys())
        k = mb.add_step("filter", ("step", "S1"))
        self.assertEqual(len(self.table_keys()), before + 1)
        out = self.step(k)["output_table"]
        t = mb.get_node(out)
        self.assertFalse(t["is_input"])
        self.assertEqual(t["producer_step"], k)
        self.assertTrue(t["display"].endswith("结果"))

    def test_overwrite_mode_no_new_table(self):
        before = len(self.table_keys())
        k = mb.add_step("filter", ("step", "S1"))
        mb.update_params(k, {"conditions": "x>1", "output_mode": "overwrite_target"})
        self.assertEqual(len(self.table_keys()), before)
        self.assertIsNone(self.step(k)["output_table"])

    def test_switch_back_new_table_restores(self):
        k = mb.add_step("filter", ("step", "S1"))
        mb.update_params(k, {"conditions": "x>1", "output_mode": "overwrite_target"})
        mb.update_params(k, {"conditions": "x>1", "output_mode": "new_table"})
        self.assertIsNotNone(self.step(k)["output_table"])

    def test_copy_table_produces(self):
        k = mb.add_step("copy_table", ("step", "S0"))
        self.assertIsNotNone(self.step(k)["output_table"])
        # 产出边：新增 1 条 produce 边，标签为复制专用文案（ADR-4/D-7）
        pr = [e for e in self.edges("produce") if e["from"] == k]
        self.assertEqual(len(pr), 1)
        self.assertEqual(pr[0]["label"], "复制新表")
        self.assertEqual(pr[0]["to"], self.step(k)["output_table"])
        # 新表落在新列（表集合 +1），producer_step 指向复制步骤
        out = self.step(k)["output_table"]
        self.assertEqual(mb.get_node(out)["producer_step"], k)

    def test_convert_dtype_no_table(self):
        k = mb.add_step("convert_dtype", ("step", "S0"))
        self.assertIsNone(self.step(k)["output_table"])

    def test_export_op_no_table(self):
        k = mb.add_step("export", ("step", "S1"))
        self.assertIsNone(self.step(k)["output_table"])
        # 结束步唯一：新导出步骤不是最后一个 export，is_end 仍归 S5
        ends = [s["key"] for s in mb.get_dag()["steps"] if s.get("is_end")]
        self.assertEqual(ends, ["S5"])
        self.assertFalse(self.step(k)["is_end"])

    def test_export_becomes_end_when_last(self):
        """删掉原结束步后再加导出步骤 → 新步骤拿到 is_end（修 add_step 硬编码）。"""
        mb.remove_step("S5")
        k = mb.add_step("export", None)
        self.assertTrue(self.step(k)["is_end"])
        self.assertIsNone(self.step(k)["output_table"])

    def test_two_exports_only_last_is_end(self):
        k1 = mb.add_step("export", ("step", "S1"))
        k2 = mb.add_step("export", ("step", "S3"))
        ends = [s["key"] for s in mb.get_dag()["steps"] if s.get("is_end")]
        self.assertEqual(ends, ["S5"])              # 唯一且为最后一个 export
        self.assertFalse(self.step(k1)["is_end"])
        self.assertFalse(self.step(k2)["is_end"])


class RemoveCascadeTest(DynBase):
    """删除级联（要点 2/3）。"""

    def test_remove_producer_table_gone_downstream_dangling(self):
        self.assertTrue(mb.remove_step("S1"))
        self.assertNotIn("T3", self.table_keys())
        s2 = self.step("S2")
        self.assertEqual(s2["config_state"], "incomplete")   # target T3 悬空

    def test_remove_cleans_statuses(self):
        mb.remove_step("S2")
        self.assertNotIn("S2", mb.get_dag()["statuses"])
        self.assertNotIn("S2", mb.get_dag()["fail_reasons"])

    def test_remove_first_step(self):
        self.assertTrue(mb.remove_step("S0"))
        self.assertEqual([s["seq"] for s in mb.get_dag()["steps"]], [1, 2, 3, 4, 5])
        # 开始连接边跟随新首步（起止标识自适应，调整点②）
        fl = [e for e in self.edges("flow") if e["from"] == mb.START_KEY]
        self.assertEqual(len(fl), 1)
        self.assertEqual(fl[0]["to"], "S1")

    def test_remove_last_export(self):
        self.assertTrue(mb.remove_step("S5"))
        self.assertFalse(any(s.get("is_end") for s in mb.get_dag()["steps"]))
        # 结束连接边 fallback 到新末步 → 画布仍有结束标识（调整点②）
        fl = [e for e in self.edges("flow") if e["to"] == mb.END_KEY]
        self.assertEqual([e["from"] for e in fl], ["S4"])

    def test_remove_unknown_false(self):
        self.assertFalse(mb.remove_step("S99"))

    def test_seq_renumber_after_insert_remove(self):
        mb.add_step("aggregate", ("step", "S1"))
        mb.remove_step("S3")
        self.assertEqual([s["seq"] for s in mb.get_dag()["steps"]],
                         list(range(1, len(mb.get_dag()["steps"]) + 1)))


class ParamsValidationTest(DynBase):
    """输入完整性校验（要点 2，X6）。"""

    def test_missing_required_param_incomplete_with_labels(self):
        k = mb.add_step("filter", ("step", "S1"))
        ok, state, missing = mb.update_params(k, {"target_table": "T1"})
        self.assertFalse(ok)
        self.assertEqual(state, "incomplete")
        self.assertIn("筛选条件", missing)

    def test_fill_required_becomes_ok(self):
        k = mb.add_step("filter", ("step", "S1"))
        mb.update_params(k, {"target_table": "T1"})
        ok, state, _ = mb.update_params(k, {"target_table": "T1", "conditions": "a>1"})
        self.assertTrue(ok)
        self.assertEqual(state, "ok")

    def test_merge_needs_extra_input(self):
        k = mb.add_step("merge_tables", ("step", "S1"))
        mb.update_params(k, {"target_table": "T3"})
        self.assertEqual(self.step(k)["config_state"], "incomplete")
        mb.update_params(k, {"target_table": "T3", "extra": 1})
        # extra_inputs 属数据模型字段：直接改模块内部态再 recompute 验证
        for s in mb._STEPS:
            if s["key"] == k:
                s["extra_inputs"] = ["T5"]
        mb.recompute()
        self.assertEqual(self.step(k)["config_state"], "ok")

    def test_update_unknown_step(self):
        ok, state, missing = mb.update_params("S99", {"a": 1})
        self.assertFalse(ok)
        self.assertEqual(missing, [])


class DeprecateTest(DynBase):
    """弃用语义（要点 2，X7）。"""

    def test_deprecate_consumers_incomplete(self):
        self.assertTrue(mb.deprecate_table("T3", True))
        self.assertEqual(self.step("S2")["config_state"], "incomplete")
        self.assertTrue(mb.get_node("T3")["deprecated"])

    def test_restore_consumers_ok(self):
        mb.deprecate_table("T3", True)
        mb.deprecate_table("T3", False)
        self.assertEqual(self.step("S2")["config_state"], "ok")

    def test_deprecate_input_table(self):
        mb.deprecate_table("T1", True)
        self.assertEqual(self.step("S0")["config_state"], "incomplete")
        self.assertEqual(self.step("S1")["config_state"], "incomplete")

    def test_deprecate_unknown_false(self):
        self.assertFalse(mb.deprecate_table("T99", True))

    def test_consumer_added_on_deprecated_table_incomplete(self):
        mb.deprecate_table("T5", True)
        k = mb.add_step("copy_table", ("step", "S3"))
        mb.update_params(k, {"target_table": "T5"})
        self.assertEqual(self.step(k)["config_state"], "incomplete")


class ExportWorkflowTest(DynBase):
    """导出与隔离（定案 4）。"""

    def test_export_structure(self):
        wf = mb.export_workflow()
        self.assertEqual(set(wf.keys()), {"meta", "tables", "steps"})
        self.assertEqual(len(wf["steps"]), 6)

    def test_export_deepcopy_isolation(self):
        wf = mb.export_workflow()
        wf["steps"][0]["name"] = "篡改"
        self.assertNotEqual(mb.get_dag()["steps"][0]["name"], "篡改")

    def test_reset_restores(self):
        mb.add_step("filter", None)
        mb.remove_step("S1")
        mb.reset_state()
        self.assertEqual(len(mb.get_dag()["steps"]), 6)
        self.assertEqual(len(mb.get_dag()["tables"]), 6)


class EdgeModelTest(DynBase):
    """边模型不变量（2026-09-17 细节优化 ADR-3：边为后端单一事实源）。"""

    ALLOWED_TYPES = {"reference", "produce", "flow", "dangling", "deprecated"}
    ALLOWED_FIELDS = {"key", "type", "from", "to", "role", "label", "missing"}

    def test_edge_schema_and_type_enum(self):
        es = self.edges()
        self.assertTrue(es)
        for e in es:
            self.assertIn(e["type"], self.ALLOWED_TYPES)
            self.assertEqual(set(e.keys()), self.ALLOWED_FIELDS)

    def test_reference_count(self):
        """reference + deprecated 计数 == 各步有效引用数（互斥且穷尽）。"""
        dag = mb.get_dag()
        tkeys = {t["key"] for t in dag["tables"]}
        expect = 0
        for s in dag["steps"]:
            refs = [s["target_table"]] if s.get("target_table") else []
            refs += [e for e in (s.get("extra_inputs") or []) if e]
            expect += len([r for r in refs if r in tkeys])
        got = len(self.edges("reference")) + len(self.edges("deprecated"))
        self.assertEqual(got, expect)
        self.assertGreater(got, 0)

    def test_reference_role_recorded(self):
        """主输入/辅输入角色在数据层可查（本轮不做视觉区分，D-2）。"""
        roles = {e["role"] for e in self.edges("reference")}
        self.assertEqual(roles, {"target", "extra"})
        extras = [e for e in self.edges("reference") if e["role"] == "extra"]
        self.assertTrue(all(e["from"] == "T2" for e in extras))   # 演示数据仅台账为辅输入

    def test_produce_count_and_label(self):
        dag = mb.get_dag()
        producers = [s for s in dag["steps"] if s.get("output_table")]
        pr = self.edges("produce")
        self.assertEqual(len(pr), len(producers))
        self.assertEqual({e["label"] for e in pr}, {"新表"})      # 初始无复制步骤
        k = mb.add_step("copy_table", ("step", "S0"))
        pr2 = [e for e in self.edges("produce") if e["from"] == k]
        self.assertEqual(len(pr2), 1)
        self.assertEqual(pr2[0]["label"], "复制新表")

    def test_flow_edges(self):
        """steps 非空 → flow 恒 2 条：__start__→首步、结束步→__end__。"""
        fl = self.edges("flow")
        self.assertEqual(len(fl), 2)
        start = [e for e in fl if e["from"] == mb.START_KEY]
        end = [e for e in fl if e["to"] == mb.END_KEY]
        self.assertEqual([e["to"] for e in start], ["S0"])
        self.assertEqual([e["from"] for e in end], ["S5"])

    def test_flow_zero_when_empty(self):
        for k in [s["key"] for s in mb.get_dag()["steps"]]:
            mb.remove_step(k)
        self.assertEqual(mb.get_dag()["steps"], [])
        self.assertEqual(self.edges("flow"), [])
        self.assertEqual(self.edges("produce"), [])
        self.assertEqual(self.edges("reference"), [])

    def test_dangling_count(self):
        self.assertEqual(self.edges("dangling"), [])              # 初始无悬空
        mb.remove_step("S1")                                      # T3 消失 → S2 悬空
        steps = mb.get_dag()["steps"]
        expect = sum(len(s.get("missing_refs") or []) for s in steps)
        self.assertEqual(len(self.edges("dangling")), expect)
        self.assertGreater(expect, 0)
        for s in steps:
            if s.get("missing_refs"):
                self.assertEqual(s["config_state"], "incomplete")  # 单向蕴含
        for e in self.edges("dangling"):
            self.assertEqual(e["missing"], e["from"])
            self.assertNotIn(e["missing"], {t["key"] for t in mb.get_dag()["tables"]})

    def test_missing_refs_scope(self):
        """missing_refs 口径隔离：弃用表与缺参都不计入悬空（避免与 deprecated 重复）。"""
        mb.deprecate_table("T3", True)
        s2 = self.step("S2")
        self.assertEqual(s2["config_state"], "incomplete")
        self.assertEqual(s2["missing_refs"], [])
        self.assertEqual(self.edges("dangling"), [])
        k = mb.add_step("filter", ("step", "S1"))
        mb.update_params(k, {"target_table": "T1"})               # 缺必填参数
        self.assertEqual(self.step(k)["config_state"], "incomplete")
        self.assertEqual(self.step(k)["missing_refs"], [])

    def test_deprecated_edges(self):
        self.assertEqual(self.edges("deprecated"), [])
        mb.deprecate_table("T3", True)
        dep = self.edges("deprecated")
        self.assertTrue(dep)
        self.assertTrue(all(e["from"] == "T3" for e in dep))
        self.assertFalse([e for e in self.edges("reference") if e["from"] == "T3"])
        mb.deprecate_table("T3", False)
        self.assertEqual(self.edges("deprecated"), [])
        self.assertTrue([e for e in self.edges("reference") if e["from"] == "T3"])

    def test_edge_key_stable_unique(self):
        e1 = mb.get_dag()["edges"]
        keys = [e["key"] for e in e1]
        self.assertEqual(len(keys), len(set(keys)))               # 全集唯一
        mb.recompute()
        self.assertEqual([e["key"] for e in mb.get_dag()["edges"]], keys)
        self.assertEqual(mb.get_dag()["edges"], e1)               # 重算幂等

    def test_virtual_key_not_node(self):
        """起止虚拟 key 不得被 get_node 误路由（命名空间隔离）。"""
        self.assertIsNone(mb.get_node(mb.START_KEY))
        self.assertIsNone(mb.get_node(mb.END_KEY))

    def test_edges_not_in_export(self):
        """导出契约不含派生字段（edges / missing_refs）。"""
        wf = mb.export_workflow()
        self.assertEqual(set(wf.keys()), {"meta", "tables", "steps"})
        for s in wf["steps"]:
            self.assertNotIn("missing_refs", s)


if __name__ == "__main__":
    unittest.main()
