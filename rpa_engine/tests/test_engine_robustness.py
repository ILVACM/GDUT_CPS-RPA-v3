"""R6 批次 D：引擎健壮性单测（取消/阈值/清理/白名单/索引/清理纯函数）。

纯标准库 unittest + engine/ops（cleanup 静态方法经 gui.main_window 导入，
headless 安全），禁 QApplication。执行：
    cd rpa_engine && python -m unittest discover -s tests
"""

import json
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from engine.executor import (
    ExecutionError, _step_timeout_sec, _validate_import_path,
    execute_workflow, register_import_root,
)
from engine.parser import ParserError, parse_workflow
from ops import sql_safety
from ops.sql_safety import ensure_index


def _parse(data: dict):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "wf.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return parse_workflow(str(p))


def _two_step_wf(**global_kw) -> dict:
    return {
        "__meta": {"schema_version": "3.1"}, "name": "D 批流程",
        "global": dict(global_kw),
        "tables": [{"table_id": "T1", "alias": "员工",
                    "source": {"file": "", "sheet": "S1", "header_row": 1},
                    "sqlite_table": "t1"}],
        "steps": [
            {"step_id": "S1", "type": "filter", "name": "筛选 1",
             "target_table_id": "T1", "output_table_id": "T101",
             "params": {"conditions": [
                 {"column": "a", "op": ">", "value": "0"}]},
             "on_error": "stop", "retry_count": 3},
            {"step_id": "S2", "type": "filter", "name": "筛选 2",
             "target_table_id": "T101", "output_table_id": "T102",
             "params": {"conditions": [
                 {"column": "a", "op": ">", "value": "1"}]},
             "on_error": "stop", "retry_count": 3}]}


class _ConnCase(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("CREATE TABLE t1 (a INTEGER, b TEXT)")
        self.conn.executemany("INSERT INTO t1 VALUES (?, ?)",
                              [(1, "x"), (2, "y"), (3, "z")])
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def _tables(self):
        return {r[0] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}


class StepTimeoutSecTest(unittest.TestCase):
    """D1-5③：阈值读取四分支（默认/显式/停用/非法回退）。"""

    def test_four_branches(self):
        self.assertEqual(_step_timeout_sec({}), 600)
        self.assertEqual(_step_timeout_sec({"step_timeout_sec": "300"}), 300)
        self.assertEqual(_step_timeout_sec({"step_timeout_sec": 0}), 0)
        self.assertEqual(_step_timeout_sec({"step_timeout_sec": "abc"}), 600)


class CancelFlowTest(_ConnCase):
    """D1-5②：步骤间取消＋循环内取消均归并 status=cancelled。"""

    def test_cancel_between_steps(self):
        wf = _parse(_two_step_wf())
        calls = []

        def cc():
            calls.append(1)
            return len(calls) > 1     # 第 1 次放行，第 2 次起终止

        result = execute_workflow(wf, self.conn, cancel_check=cc)
        self.assertEqual(result["status"], "cancelled")
        self.assertFalse(result["success"])

    def test_cancel_inside_export_loop(self):
        data = _two_step_wf()
        with tempfile.TemporaryDirectory() as td:
            data["steps"][1] = {
                "step_id": "S2", "type": "export", "name": "导出 1",
                "target_table_id": "T101", "output_table_id": "",
                "params": {"output_path": str(Path(td) / "out.xlsx"),
                           "sheet_name": "数据"},
                "on_error": "stop", "retry_count": 3}
            wf = _parse(data)
            calls = []

            def cc():
                calls.append(1)
                return len(calls) > 2   # 步骤前置两次放行，导出循环内终止

            result = execute_workflow(wf, self.conn, cancel_check=cc)
        self.assertEqual(result["status"], "cancelled")
        self.assertFalse(result["success"])


class IntermediateCleanupTest(_ConnCase):
    """D4-3：完成后清理中间表；写回目标保护；keep_db 全保留。"""

    def test_cleanup_intermediate_tables(self):
        wf = _parse(_two_step_wf())
        result = execute_workflow(wf, self.conn)
        self.assertEqual(result["status"], "completed")
        names = self._tables()
        self.assertIn("t1", names)                 # 输入表未被误删
        self.assertNotIn("t_s1", names)            # 中间表已清理
        self.assertNotIn("t_s2", names)

    def test_keep_db_preserves_all(self):
        wf = _parse(_two_step_wf(keep_db=True))
        result = execute_workflow(wf, self.conn)
        self.assertEqual(result["status"], "completed")
        names = self._tables()
        self.assertIn("t_s1", names)               # keep_db=True 全保留
        self.assertIn("t_s2", names)


class VersionGateTest(unittest.TestCase):
    """E2-S2（P1-3）：版本门禁——未知/空串拒绝，键缺失缺省放行。"""

    def test_unknown_version_rejected(self):
        data = _two_step_wf()
        data["__meta"]["schema_version"] = "3.2"
        with self.assertRaises(ParserError):
            _parse(data)

    def test_empty_version_rejected(self):
        data = _two_step_wf()
        data["__meta"]["schema_version"] = ""
        with self.assertRaises(ParserError):
            _parse(data)

    def test_missing_version_defaults_ok(self):
        data = _two_step_wf()
        del data["__meta"]
        wf = _parse(data)
        self.assertEqual(wf.schema_version, "3.1")


class ImportWhitelistTest(unittest.TestCase):
    """D7-3：导入路径白名单（越界拒绝；register 后放行）。"""

    def test_out_of_range_rejected(self):
        with self.assertRaises(ParserError):
            _validate_import_path(str(
                Path(os.environ.get("SystemRoot", "C:\\Windows"))
                / "system32" / "drivers" / "etc" / "x.xlsx"))

    def test_registered_root_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "ok.xlsx"
            f.write_bytes(b"x")
            register_import_root(td)
            _validate_import_path(str(f))          # 不抛即通过


class EnsureIndexTest(_ConnCase):
    """D6-S3：小表不建；阈值注入后建索引且结果不变。"""

    def test_threshold_paths(self):
        ensure_index(self.conn, "t1", ["a"])       # 默认阈值 5 万：不建
        idx = [r[0] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name LIKE 'idx_%'")]
        self.assertEqual(idx, [])
        old = sql_safety.INDEX_ROW_THRESHOLD
        try:
            sql_safety.INDEX_ROW_THRESHOLD = 0     # 阈值注入：建
            ensure_index(self.conn, "t1", ["a"])
            ensure_index(self.conn, "t1", ["a"])   # 幂等
            idx = [r[0] for r in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND name LIKE 'idx_%'")]
            self.assertEqual(idx, ["idx_t1_a"])
        finally:
            sql_safety.INDEX_ROW_THRESHOLD = old
        rows = self.conn.execute("SELECT a FROM t1 ORDER BY a").fetchall()
        self.assertEqual([r[0] for r in rows], [1, 2, 3])   # 结果不变

    def test_missing_table_silent(self):
        ensure_index(self.conn, "no_such_table", ["a"])     # 静默不抛


class StaleFileCleanupTest(unittest.TestCase):
    """D2-4：孤儿会话库全删＋超龄副本删、新副本留（静态纯函数）。"""

    def test_cleanup_stale_files(self):
        from gui.main_window import MainWindow
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "workspace"
            tmp = Path(td) / "temp"
            ws.mkdir()
            tmp.mkdir()
            (ws / "session_1.db").write_text("x")
            (ws / "session_1.db-wal").write_text("x")
            (ws / "gui_workflow.json").write_text("{}")   # 非会话库：保留
            old_f = tmp / "old.xlsx"
            old_f.write_text("x")
            stale = time.time() - 25 * 3600
            os.utime(old_f, (stale, stale))
            new_f = tmp / "new.xlsx"
            new_f.write_text("x")
            removed = MainWindow.cleanup_stale_files(ws, tmp)
            self.assertEqual(removed, 3)                  # 2 会话库 + 1 超龄
            self.assertTrue((ws / "gui_workflow.json").exists())
            self.assertTrue(new_f.exists())
            self.assertFalse(old_f.exists())


class ImportConsistencyTest(unittest.TestCase):
    """D8-S2：sheet_info 复用与缺省路径导入结果一致。"""

    def test_import_same_with_and_without_sheet_info(self):
        from openpyxl import Workbook
        from ops.excel_preprocessor import scan_sheets
        from ops.table_importer import import_excel_table
        conn = sqlite3.connect(":memory:")
        try:
            with tempfile.TemporaryDirectory() as td:
                xp = Path(td) / "s.xlsx"
                wb = Workbook()
                wb.active.title = "S1"
                wb.active.append(["a", "b"])
                wb.active.append([1, "x"])
                wb.active.append([2, "y"])
                wb.save(str(xp))
                info = scan_sheets(str(xp))
                n1 = import_excel_table(conn, str(xp), "S1", 1, "t_a")
                n2 = import_excel_table(conn, str(xp), "S1", 1, "t_b",
                                        sheet_info=info)
            self.assertEqual((n1, n2), (2, 2))
            cols_a = [r[1] for r in conn.execute("PRAGMA table_info(t_a)")]
            cols_b = [r[1] for r in conn.execute("PRAGMA table_info(t_b)")]
            self.assertEqual(cols_a, cols_b)
        finally:
            conn.close()


class ExportCopyAreaGuardTest(_ConnCase):
    """D7-3：导出路径指向导入副本区被拒绝。"""

    def test_export_into_copy_area_rejected(self):
        from ops.exporter import export_table
        from paths import get_engine_root
        bad = Path(get_engine_root()) / "temp" / "input_selection" / "o.xlsx"
        with self.assertRaises(ValueError):
            export_table(self.conn, "t1", str(bad))


if __name__ == "__main__":
    unittest.main()
