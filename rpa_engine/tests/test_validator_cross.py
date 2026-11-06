"""引擎交叉查重单测（2026-09-21 审计 P3/S2-T1-4）。

validate_tables(tables, steps) 输入∩派生编号交叉查重；steps 缺省兼容。
纯标准库 unittest，禁 Qt。执行：
    cd rpa_engine && python -m unittest discover -s tests -v
"""

import unittest

from engine.parser import StepDef, TableDef
from engine.validator import ValidationError, validate_tables


def _table(tid: str) -> TableDef:
    return TableDef(table_id=tid, alias=tid,
                    source={"file": "", "sheet": "", "header_row": 1},
                    sqlite_table=tid.lower())


def _step(sid: str, out: str) -> StepDef:
    return StepDef(step_id=sid, type="filter", name="筛选",
                   target_table_id="T1", output_table_id=out,
                   params={}, on_error="stop", retry_count=3)


class CollisionCrossTest(unittest.TestCase):

    def test_cross_collision_raises(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_tables([_table("T1")], [_step("S1", "T1")])
        self.assertIn("T1", str(ctx.exception))

    def test_default_steps_compat(self):
        validate_tables([_table("T1"), _table("T2")])   # 不抛

    def test_no_cross_pass(self):
        validate_tables([_table("T1")], [_step("S1", "T101")])   # 不抛


if __name__ == "__main__":
    unittest.main()
