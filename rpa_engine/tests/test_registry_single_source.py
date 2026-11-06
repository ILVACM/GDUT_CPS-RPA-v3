"""功能函数记录表「单一源」单测（R15/B-41~B-65 主要判据）。

覆盖（原编号 → R15 项）：
- B-59（B7）参数白名单与契约一致：`param_keys` ≡ schema 键 ∪ GUI 注入键
- B-64（D2）`params_schema` 唯一源：键集/默认值与 `param_keys`、`default_params` 三方一致
- B-69（P2-1）`default_params` 派生自 schema（不再手写清单）
- B-41（B9）**引擎回退 ≡ schema 默认值**：`mapping_match.mode` 缺省 left_join
  （不再静默丢主表未匹配行）、`convert_dtype.from_type/to_type` 缺省不再必然报错
- B-53（D4）已弃用操作被 validator 拒绝
- B-63（D1）`extra_input_min` 契约
- B-65（D3）`overwritable` 声明与表单挂载函数一致
- B-03（F-05）导出 write_only 行为等价（日期格式保留）
- B-76（§8.2-1）注释与实现一致（write_only 已落地）

纯标准库 unittest（gui 侧延迟导入，沿用既有范式）。执行：
    cd rpa_engine && python -m unittest discover -s tests -v
"""

import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from engine.registry import BUILTIN_OPS
from engine.validator import ValidationError, validate_steps
from gui.models import STEP_CATALOG, default_params
from ops.exporter import export_table
from ops.step_executor import (GUI_INJECTED_PARAM_KEYS, execute_step,
                               param_defaults, param_schema)


def _conn_with(statements=()) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    for stmt in statements:
        conn.execute(stmt)
    return conn


class ParamContractSingleSourceTest(unittest.TestCase):
    """B-59／B-64／B-69：白名单／契约／默认值三方一致。"""

    def test_param_keys_equals_schema_plus_gui_injected(self):
        for k, entry in BUILTIN_OPS.items():
            schema_keys = {p["key"] for p in entry["params_schema"]}
            expected = schema_keys | (GUI_INJECTED_PARAM_KEYS
                                      if entry["output"] else set())
            self.assertEqual(set(entry["param_keys"]), expected,
                             f"{k} 的 param_keys 与 params_schema/GUI 注入键不一致")

    def test_schema_entries_have_full_declaration(self):
        for k, entry in BUILTIN_OPS.items():
            for p in entry["params_schema"]:
                for field_name in ("key", "type", "required", "default"):
                    self.assertIn(field_name, p, f"{k}.{p.get('key')} 缺 {field_name}")

    def test_default_params_derives_from_schema(self):
        for k in STEP_CATALOG:
            self.assertEqual(default_params(k), param_defaults(k),
                             f"{k} default_params 与 schema 默认值不一致")

    def test_default_params_matches_record_table(self):
        """§3.2 文档版记录表宣称的默认值须与代码一致（B-41 覆盖的 2 项）。"""
        self.assertEqual(default_params("mapping_match")["mode"], "left_join")
        self.assertEqual(default_params("convert_dtype")["from_type"], "TEXT")
        self.assertEqual(default_params("convert_dtype")["to_type"], "INTEGER")

    def test_engine_fallback_equals_schema_default(self):
        """引擎各分支回退值 ≡ schema 默认值（同源，无第二份清单）。"""
        for k, entry in BUILTIN_OPS.items():
            for p in entry["params_schema"]:
                self.assertEqual(param_defaults(k)[p["key"]], p["default"])


class EngineFallbackBehaviorTest(unittest.TestCase):
    """B-41：省略参数键时的**实际行为**（不含 mode/from_type 的手写 JSON）。"""

    def test_mapping_match_default_keeps_unmatched_rows(self):
        """缺省 mode → left_join：主表未匹配行**保留**（原 inner_join 会丢弃）。"""
        conn = _conn_with([
            "CREATE TABLE L (id INTEGER, name TEXT)",
            "INSERT INTO L VALUES (1, 'a'), (2, 'b')",
            "CREATE TABLE R (id INTEGER, val TEXT)",
            "INSERT INTO R VALUES (1, 'x')",
        ])
        res = execute_step(
            {"step_id": "S1", "type": "mapping_match", "name": "",
             "target_table_id": "T1",
             "params": {"match_table_id": "T2", "match_columns": {"id": "id"}}},
            conn, {"T1": "L", "T2": "R"}, 1)
        self.assertTrue(res["success"], res["message"])
        out = res["output_table"]
        self.assertEqual(conn.execute(f"SELECT COUNT(*) FROM {out}").fetchone()[0], 2,
                         "缺省 mode 应为 left_join（保留主表全部行）")

    def test_mapping_match_explicit_inner_join_still_drops(self):
        """显式 inner_join 时仍只保留匹配行（用户显式选择不受影响）。"""
        conn = _conn_with([
            "CREATE TABLE L (id INTEGER, name TEXT)",
            "INSERT INTO L VALUES (1, 'a'), (2, 'b')",
            "CREATE TABLE R (id INTEGER, val TEXT)",
            "INSERT INTO R VALUES (1, 'x')",
        ])
        res = execute_step(
            {"step_id": "S1", "type": "mapping_match", "name": "",
             "target_table_id": "T1",
             "params": {"match_table_id": "T2", "match_columns": {"id": "id"},
                        "mode": "inner_join"}},
            conn, {"T1": "L", "T2": "R"}, 1)
        self.assertTrue(res["success"], res["message"])
        out = res["output_table"]
        self.assertEqual(conn.execute(f"SELECT COUNT(*) FROM {out}").fetchone()[0], 1)

    def test_convert_dtype_default_from_to_types_succeed(self):
        """缺省 from_type/to_type → TEXT→INTEGER（原空串会**必然报错**）。"""
        conn = _conn_with([
            "CREATE TABLE cd (a TEXT)",
            "INSERT INTO cd VALUES ('1'), ('2')",
        ])
        res = execute_step(
            {"step_id": "S1", "type": "convert_dtype", "name": "",
             "target_table_id": "T1", "params": {"column": "a"}},
            conn, {"T1": "cd"}, 1)
        self.assertTrue(res["success"], res["message"])


class DeclaredContractFieldsTest(unittest.TestCase):
    """B-63／B-65：`extra_input_min` 与 `overwritable` 声明。"""

    def test_extra_input_min_declared(self):
        self.assertEqual(BUILTIN_OPS["mapping_match"]["extra_input_min"], 2)
        self.assertEqual(BUILTIN_OPS["merge_tables"]["extra_input_min"], 2)
        for k, entry in BUILTIN_OPS.items():
            if k not in ("mapping_match", "merge_tables"):
                self.assertEqual(entry["extra_input_min"], 0, f"{k} extra_input_min 应为 0")

    def test_overwritable_declared(self):
        declared = {k for k, e in BUILTIN_OPS.items() if e["overwritable"]}
        self.assertEqual(declared, {"filter", "dedup"})

    def test_form_mounting_follows_overwritable(self):
        from gui.forms import _is_overwritable
        for k in BUILTIN_OPS:
            self.assertEqual(_is_overwritable(k),
                             bool(BUILTIN_OPS[k]["overwritable"]),
                             f"{k} 表单挂载判定与引擎声明不一致")

    def test_deprecated_flag_present_and_false(self):
        for k, entry in BUILTIN_OPS.items():
            self.assertIn("deprecated", entry, f"{k} 缺 deprecated 字段")
            self.assertFalse(entry["deprecated"], f"{k} 现网不应为弃用")


class DeprecatedRejectedTest(unittest.TestCase):
    """B-53：已弃用操作被 validator 拒绝（前后端弃用口径闭合）。"""

    def _step(self, op):
        from engine.parser import StepDef
        return StepDef(step_id="S1", type=op, target_table_id="T1")

    def test_active_op_passes(self):
        validate_steps([self._step("filter")])       # 不抛异常即通过

    def test_deprecated_op_rejected(self):
        entry = BUILTIN_OPS["filter"]
        original = entry["deprecated"]
        try:
            entry["deprecated"] = True
            with self.assertRaises(ValidationError):
                validate_steps([self._step("filter")])
        finally:
            entry["deprecated"] = original


class ExportWriteOnlyTest(unittest.TestCase):
    """B-03／B-76：write_only 导出行为等价（表头/sheet 名/日期格式保留）。"""

    def _export(self, conn, td, name="o.xlsx"):
        out = Path(td) / name
        n = export_table(conn, "d", str(out))
        return out, n

    def test_export_roundtrip_equivalent(self):
        from openpyxl import load_workbook
        conn = _conn_with([
            "CREATE TABLE d (区域 TEXT, 数量 INTEGER)",
            "INSERT INTO d VALUES ('东区', 1), ('西区', 2)",
        ])
        with tempfile.TemporaryDirectory() as td:
            out, n = self._export(conn, td)
            self.assertEqual(n, 2)
            wb = load_workbook(str(out))
            try:
                ws = wb.active
                self.assertEqual(ws.title, "数据")
                self.assertEqual([c.value for c in ws[1]], ["区域", "数量"])
                self.assertEqual([ws.cell(row=r, column=1).value for r in (2, 3)],
                                 ["东区", "西区"])
            finally:
                wb.close()

    def test_date_number_format_preserved(self):
        """R11/A-06 回归：ISO 文本仍写回真日期且保留 number_format。"""
        from openpyxl import load_workbook
        conn = _conn_with([
            "CREATE TABLE d (日期 TEXT)",
            "INSERT INTO d VALUES ('2026-02-20'), ('2026-02-20 10:00:00')",
        ])
        with tempfile.TemporaryDirectory() as td:
            out, _ = self._export(conn, td)
            wb = load_workbook(str(out))
            try:
                ws = wb.active
                c1, c2 = ws.cell(row=2, column=1), ws.cell(row=3, column=1)
                self.assertIsInstance(c1.value, datetime)
                self.assertEqual(c1.number_format, "yyyy-mm-dd")
                self.assertIsInstance(c2.value, datetime)
                self.assertEqual(c2.number_format, "yyyy-mm-dd hh:mm:ss")
            finally:
                wb.close()


if __name__ == "__main__":
    unittest.main()
