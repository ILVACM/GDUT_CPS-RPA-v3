"""GUI 配置 → 后端执行参数翻译层 E2E 测试（2026-09-20 M23/M26）。

覆盖 `_temp/DAG-rebuild/plan.md` §4.7 八用例：roundtrip 闭合、弃用闭包级联
（输入表/派生表）、new_table 与 overwrite 两步链映射、STEP_DESC 完整性、
空流程处置、load 回归。

纯 parse/validate 层验证——不触 SQLite、不产生运行时副作用（临时文件用
tempfile 并自动清理）。
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.parser import parse_workflow                      # noqa: E402
from engine.validator import validate_workflow                # noqa: E402
from gui.models import (STEP_CATALOG, STEP_DESC, WorkflowModel,  # noqa: E402
                        step_desc)


def make_model() -> WorkflowModel:
    """5 步 / 2 输入表工作流（S1 转换 → S2 筛选 → S3 映射 → S4 统计 → S5 导出）。"""
    m = WorkflowModel("翻译层测试流程")
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
    s3.params = {"match_table_id": "T2", "match_columns": {"户号": "户号"},
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


def roundtrip(data) -> bool:
    """导出字典 → 落临时文件 → parse → validate，返回是否全通。"""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "wf.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        wf = parse_workflow(str(p))
        return bool(validate_workflow(wf)) and wf


class TranslationTest(unittest.TestCase):
    """翻译层八用例（plan.md §4.7）。"""

    def setUp(self) -> None:
        self.model = make_model()

    # ① roundtrip：GUI 模型 → v3.1 JSON → parse → validate 闭合
    def test_roundtrip(self):
        data = self.model.to_dict()
        self.assertEqual(data["__meta"]["schema_version"], "3.1")
        self.assertEqual(len(data["tables"]), 2)
        self.assertEqual(len(data["steps"]), 5)
        wf = roundtrip(data)
        self.assertTrue(wf)
        self.assertEqual(len(wf.steps), 5)

    # ② 输入表弃用级联：闭包内步骤剔除、共享表保留
    def test_deprecate_input_table_cascade(self):
        self.model.deprecate_table("T1", True)
        data = self.model.to_dict()
        self.assertEqual([t["table_id"] for t in data["tables"]], ["T2"])
        self.assertEqual([s["type"] for s in data["steps"]], ["aggregate"])
        self.assertTrue(roundtrip(data))
        # 恢复后回到全量（可逆）
        self.model.deprecate_table("T1", False)
        self.assertEqual(len(self.model.to_dict()["steps"]), 5)

    # ③ 派生表弃用级联：产出步骤与下游消费步骤入闭包
    def test_deprecate_derived_table_cascade(self):
        derived = self.model.steps[1].output_table_id      # T3（筛选结果）
        self.model.deprecate_table(derived, True)
        data = self.model.to_dict()
        self.assertEqual([s["type"] for s in data["steps"]],
                         ["convert_dtype", "aggregate"])
        self.assertEqual([t["table_id"] for t in data["tables"]], ["T1", "T2"])
        self.assertTrue(roundtrip(data))

    # ④ new_table：剔除前端键；遗留 output_table 被替换为固化 t_{uid}
    # （M5-a/K2），不产合成步骤
    def test_new_table_mapping(self):
        self.model.steps[1].params["output_mode"] = "new_table"
        self.model.steps[1].params["output_table"] = "legacy_phys"   # 旧文件遗留
        data = self.model.to_dict()
        self.assertEqual(len(data["steps"]), 5)
        p = data["steps"][1]["params"]
        self.assertNotIn("output_mode", p)
        self.assertEqual(p["output_table"],
                         f"t_{self.model.steps[1].uid}")   # 遗留值被替换
        self.assertTrue(roundtrip(data))

    # ⑤ overwrite：两步链（本步产中间表 + 合成 copy_table 写回目标物理名）
    def test_overwrite_two_step_chain(self):
        self.model.steps[1].params["output_mode"] = "overwrite_target"
        inter = self.model.steps[1].output_table_id        # T3
        data = self.model.to_dict()
        self.assertEqual(len(data["steps"]), 6)

        main_step, copy_step = data["steps"][1], data["steps"][2]
        self.assertEqual(main_step["type"], "filter")
        self.assertEqual(main_step["output_table_id"], inter)
        self.assertNotIn("output_mode", main_step["params"])
        # M5-a/K2：父步中间表物理名固化为 t_{uid}
        self.assertEqual(main_step["params"]["output_table"],
                         f"t_{self.model.steps[1].uid}")

        self.assertEqual(copy_step["type"], "copy_table")
        self.assertEqual(copy_step["step_id"], f"{main_step['step_id']}_cp")
        self.assertEqual(copy_step["target_table_id"], inter)
        self.assertEqual(copy_step["output_table_id"], "")
        # 目标表取 sqlite_table 物理名（T1 → t1），非逻辑编号
        self.assertEqual(copy_step["params"], {"output_table": "t1"})

        # 下游引用原地不动（S3 仍引用中间表编号）
        self.assertEqual(data["steps"][3]["target_table_id"], inter)
        self.assertTrue(roundtrip(data))

    # ⑥ STEP_DESC：全量齐全（引用 STEP_COUNT）、键集与操作目录一致、与目录说明同源
    def test_step_desc_complete(self):
        from gui.models import STEP_COUNT
        self.assertEqual(len(STEP_DESC), STEP_COUNT)
        self.assertEqual(set(STEP_DESC.keys()), set(STEP_CATALOG.keys()))
        for op, desc in STEP_DESC.items():
            self.assertIsInstance(desc, str)
            self.assertTrue(desc.strip())
            self.assertEqual(desc, STEP_CATALOG[op][1])
            self.assertEqual(step_desc(op), desc)
        self.assertEqual(step_desc("__unknown__"), "")

    # ⑦ 空流程：全表弃用 → 导出无步骤无表（存模板允许，启动由页面拦截）
    def test_all_deprecated_empty_export(self):
        self.model.deprecate_table("T1", True)
        self.model.deprecate_table("T2", True)
        data = self.model.to_dict()
        self.assertEqual(data["steps"], [])
        self.assertEqual(data["tables"], [])
        # 未过滤导出仍保全量（编辑态）
        self.assertEqual(len(self.model.to_dict(include_deprecated=True)["steps"]), 5)

    # ⑧ load 回归：遗留键剔除 + 未过滤导出可完整还原
    def test_load_regression(self):
        old = self.model.to_dict()
        old["steps"][1]["params"]["output_table"] = "legacy_phys"
        old["steps"][1]["params"]["output_mode"] = "new_table"
        m2 = WorkflowModel()
        m2.load_from_dict(old)
        out = m2.to_dict()
        # M5-a/K2+K3：遗留 output_table 被剔除；业务口径固化为 t_{新 uid}
        # （业务 JSON 无 uid 键，load 重生成 → 物理名随新 uid，K3 预期）
        self.assertEqual(out["steps"][1]["params"]["output_table"],
                         f"t_{m2.steps[1].uid}")
        self.assertNotIn("output_mode", out["steps"][1]["params"])
        # 编辑态口径保全注入的 output_mode（2026-09-21 审计 P1，替代原
        # "双口径均剔除"的固化断言）；output_table 编辑态剥离（M5-a）
        full2 = m2.to_dict(include_deprecated=True)
        self.assertEqual(full2["steps"][1]["params"]["output_mode"], "new_table")
        self.assertNotIn("output_table", full2["steps"][1]["params"])

        # 弃用后：业务导出过滤，编辑态导出保全量；载入不还原弃用态
        self.model.deprecate_table("T1", True)
        self.assertEqual(len(self.model.to_dict()["steps"]), 1)
        full = self.model.to_dict(include_deprecated=True)
        self.assertEqual(len(full["steps"]), 5)
        m3 = WorkflowModel()
        m3.load_from_dict(full)
        self.assertEqual(len(m3.steps), 5)
        self.assertEqual(m3.deprecated_tables, set())

    # ⑨ 编辑态无损往返（2026-09-21 审计 P1）：保 output_mode、不展开 _cp、
    #    重载幂等；业务口径仍完整两步链
    def test_overwrite_editing_roundtrip(self):
        self.model.steps[1].params["output_mode"] = "overwrite_target"
        d1 = self.model.to_dict(include_deprecated=True)
        self.assertEqual(len(d1["steps"]), 5)
        self.assertEqual(d1["steps"][1]["params"]["output_mode"],
                         "overwrite_target")
        self.assertFalse(any(s["step_id"].endswith("_cp") for s in d1["steps"]))
        m2 = WorkflowModel()
        m2.load_from_dict(d1)
        d2 = m2.to_dict(include_deprecated=True)
        self.assertEqual(d1["steps"], d2["steps"])
        d3 = m2.to_dict()
        self.assertEqual(len(d3["steps"]), 6)
        self.assertTrue(any(s["step_id"].endswith("_cp") for s in d3["steps"]))


if __name__ == "__main__":
    unittest.main()
