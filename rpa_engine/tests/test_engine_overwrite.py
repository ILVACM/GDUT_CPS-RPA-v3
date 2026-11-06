"""引擎级实测：覆盖原表两步链（2026-09-21 修复轮 F8②）。

内存 SQLite + to_dict 翻译产物真执行，验证：
- 两步链结构（S{n} 产中间表 + S{n}_cp copy_table 写回物理名）；
- 执行后目标物理表内容＝筛选结果（覆盖成立）；
- output_tables 回写派生表映射；cp 步计入执行步骤数（F2 口径源头）。

纯标准库 unittest + 引擎，禁 Qt。执行：
    cd rpa_engine && python -m unittest discover -s tests -v
"""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from engine.executor import ExecutionError, execute_workflow
from engine.parser import parse_workflow
from engine.validator import validate_workflow
from gui.models import WorkflowModel


class OverwriteTwoStepChainTest(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("CREATE TABLE t1 (a INTEGER, b TEXT)")
        self.conn.executemany(
            "INSERT INTO t1 VALUES (?, ?)",
            [(1, "x"), (2, "y"), (3, "z")])
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def _model(self) -> WorkflowModel:
        m = WorkflowModel()
        m.set_tables([{
            "table_id": "T1", "alias": "员工", "sqlite_table": "t1",
            "file_path": "", "sheet_name": "S1", "header_row": 1,
        }])
        s = m.add_step("filter")
        s.target_table_id = "T1"
        s.params = {
            "conditions": [{"column": "a", "op": ">", "value": "1"}],
            "output_mode": "overwrite_target",
        }
        return m

    def test_translation_structure(self):
        m = self._model()
        data = m.to_dict()
        steps = data["steps"]
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[1]["step_id"], steps[0]["step_id"] + "_cp")
        self.assertEqual(steps[1]["type"], "copy_table")
        self.assertEqual(steps[1]["params"].get("output_table"), "t1")
        # F2 口径源头：执行步骤数（含 cp）> 模型步骤数
        self.assertEqual(len(steps), len(m.steps) + 1)

    def test_execute_overwrites_target(self):
        m = self._model()
        data = m.to_dict()
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wf.json"
            p.write_text(json.dumps(data, ensure_ascii=False),
                         encoding="utf-8")
            wf = parse_workflow(str(p))
        self.assertTrue(validate_workflow(wf))
        result = execute_workflow(wf, self.conn)
        self.assertEqual(result["status"], "completed")
        # 目标物理表被覆盖为筛选结果（a>1 → 2,3）
        rows = self.conn.execute(
            "SELECT a FROM t1 ORDER BY a").fetchall()
        self.assertEqual([r[0] for r in rows], [2, 3])
        # 派生中间表登记回写（供画布 tooltip/报告页）
        self.assertEqual(result["output_tables"].get("T101"),
                         f"t_{m.steps[0].uid}")


class ProgressMetaTest(unittest.TestCase):
    """进度页 meta 与执行步骤数同源（2026-09-21 审计 P4）。"""

    def test_progress_meta_matches_exec_total(self):
        m = WorkflowModel()
        m.set_tables([{
            "table_id": "T1", "alias": "员工", "sqlite_table": "t1",
            "file_path": "", "sheet_name": "S1", "header_row": 1,
        }])
        s = m.add_step("filter")
        s.target_table_id = "T1"
        s.params = {
            "conditions": [{"column": "a", "op": ">", "value": "1"}],
            "output_mode": "overwrite_target",
        }
        data = m.to_dict()
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wf.json"
            p.write_text(json.dumps(data, ensure_ascii=False),
                         encoding="utf-8")
            wf = parse_workflow(str(p))
        meta = [(sd.step_id, sd.name) for sd in wf.steps]
        self.assertEqual(len(meta), len(wf.steps))
        self.assertEqual(meta[-1][0], f"{wf.steps[0].step_id}_cp")
        self.assertTrue(meta[-1][1].endswith("（写回原表）"))


class TUidEngineTest(unittest.TestCase):
    """M5-a：t_{uid} 真执行链 + 外部 JSON 回退 t_s{n}（§3.3 例3/例4）。"""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("CREATE TABLE t1 (a INTEGER, b TEXT)")
        self.conn.executemany(
            "INSERT INTO t1 VALUES (?, ?)",
            [(1, "x"), (2, "y"), (3, "z")])
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def _model(self) -> WorkflowModel:
        m = WorkflowModel()
        m.set_tables([{
            "table_id": "T1", "alias": "员工", "sqlite_table": "t1",
            "file_path": "", "sheet_name": "S1", "header_row": 1,
        }])
        s = m.add_step("filter")
        s.target_table_id = "T1"
        s.params = {
            "conditions": [{"column": "a", "op": ">", "value": "1"}],
            "output_mode": "overwrite_target",
        }
        return m

    def test_overwrite_parent_stable_name(self):
        m = self._model()
        uid = m.steps[0].uid
        data = m.to_dict()
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wf.json"
            p.write_text(json.dumps(data, ensure_ascii=False),
                         encoding="utf-8")
            wf = parse_workflow(str(p))
        self.assertTrue(validate_workflow(wf))
        result = execute_workflow(wf, self.conn)
        self.assertEqual(result["status"], "completed")
        # overwrite 父步中间表稳定名（M5-a：t_{uid}）
        self.assertEqual(result["output_tables"].get("T101"), f"t_{uid}")
        # cp 步把 t_{uid} 内容写回 t1（既有断言口径保持）
        rows = self.conn.execute(
            "SELECT a FROM t1 ORDER BY a").fetchall()
        self.assertEqual([r[0] for r in rows], [2, 3])

    def test_external_json_fallback_t_s(self):
        data = {"__meta": {"schema_version": "3.1"}, "name": "外部回退",
                "global": {"keep_db": False},
                "tables": [{"table_id": "T1", "alias": "员工",
                            "source": {"file": "", "sheet": "S1",
                                       "header_row": 1},
                            "sqlite_table": "t1"}],
                "steps": [{"step_id": "S1", "type": "filter",
                           "name": "筛选 1",
                           "target_table_id": "T1",
                           "output_table_id": "T101",
                           "params": {"conditions": [
                               {"column": "a", "op": ">", "value": "1"}]},
                           "on_error": "stop", "retry_count": 3}]}
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wf.json"
            p.write_text(json.dumps(data, ensure_ascii=False),
                         encoding="utf-8")
            wf = parse_workflow(str(p))
        result = execute_workflow(wf, self.conn)
        self.assertEqual(result["status"], "completed")
        # params 无 output_table → 引擎回退 t_s{step_index}（K3 双轨）
        self.assertEqual(list(result["output_tables"].values()), ["t_s1"])


class OverwriteDerivedEngineTest(unittest.TestCase):
    """R6/A1（P0-1）执行级：覆盖写回派生表真生效、无游离逻辑名表。"""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("CREATE TABLE t1 (a INTEGER, b TEXT)")
        self.conn.executemany(
            "INSERT INTO t1 VALUES (?, ?)",
            [(1, "x"), (2, "y"), (3, "z"), (2, "w")])
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_overwrite_derived_target_executes(self):
        m = WorkflowModel()
        m.set_tables([{
            "table_id": "T1", "alias": "员工", "sqlite_table": "t1",
            "file_path": "", "sheet_name": "S1", "header_row": 1,
        }])
        s1 = m.add_step("filter")
        s1.target_table_id = "T1"
        s1.params = {
            "conditions": [{"column": "a", "op": ">", "value": "1"}],
        }
        s2 = m.add_step("dedup")
        s2.target_table_id = s1.output_table_id   # 写回目标＝派生表 T101
        s2.params = {"key_columns": ["a"], "keep": "first",
                     "output_mode": "overwrite_target"}
        uid1 = s1.uid
        data = m.to_dict()
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wf.json"
            p.write_text(json.dumps(data, ensure_ascii=False),
                         encoding="utf-8")
            wf = parse_workflow(str(p))
        self.assertTrue(validate_workflow(wf))
        result = execute_workflow(wf, self.conn)
        self.assertEqual(result["status"], "completed")
        # 无游离逻辑名表（P0-1 修复核心：不再写出名为 "T101" 的表）
        stray = self.conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='T101'").fetchall()
        self.assertEqual(stray, [])
        # 写回命中：t_{uid1} 内容＝dedup 结果（a>1 去重 → 2,3）
        rows = self.conn.execute(
            f"SELECT a FROM t_{uid1} ORDER BY a").fetchall()
        self.assertEqual([r[0] for r in rows], [2, 3])
        # 输入表未被触碰
        n_t1 = self.conn.execute("SELECT COUNT(*) FROM t1").fetchone()[0]
        self.assertEqual(n_t1, 4)


class HonestReportTest(unittest.TestCase):
    """R6/A2（P3-9）：skip 降级 → status=completed 但 success=False。"""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("CREATE TABLE t1 (a INTEGER, b TEXT)")
        self.conn.executemany("INSERT INTO t1 VALUES (?, ?)",
                              [(1, "x"), (2, "y")])
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_skip_marks_success_false(self):
        data = {"__meta": {"schema_version": "3.1"}, "name": "跳过口径",
                "global": {"keep_db": False},
                "tables": [{"table_id": "T1", "alias": "员工",
                            "source": {"file": "", "sheet": "S1",
                                       "header_row": 1},
                            "sqlite_table": "t1"}],
                "steps": [
                    {"step_id": "S1", "type": "filter", "name": "筛选 1",
                     "target_table_id": "T1", "output_table_id": "T101",
                     "params": {"conditions": [
                         {"column": "不存在的列", "op": ">", "value": "1"}]},
                     "on_error": "skip", "retry_count": 3},
                    {"step_id": "S2", "type": "filter", "name": "筛选 2",
                     "target_table_id": "T1", "output_table_id": "T102",
                     "params": {"conditions": [
                         {"column": "a", "op": ">", "value": "1"}]},
                     "on_error": "stop", "retry_count": 3}]}
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wf.json"
            p.write_text(json.dumps(data, ensure_ascii=False),
                         encoding="utf-8")
            wf = parse_workflow(str(p))
        result = execute_workflow(wf, self.conn)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(result["success"])       # 诚实口径：非全步成功
        self.assertEqual(result["steps_succeeded"], 1)

    def test_retry_exhausted_raises(self):
        """R6/B3（P2-14/D6②）：重试耗尽＝失败（不再静默继续）。"""
        data = {"__meta": {"schema_version": "3.1"}, "name": "重试耗尽",
                "global": {"keep_db": False},
                "tables": [{"table_id": "T1", "alias": "员工",
                            "source": {"file": "", "sheet": "S1",
                                       "header_row": 1},
                            "sqlite_table": "t1"}],
                "steps": [
                    {"step_id": "S1", "type": "filter", "name": "筛选 1",
                     "target_table_id": "T1", "output_table_id": "T101",
                     "params": {"conditions": [
                         {"column": "不存在的列", "op": ">", "value": "1"}]},
                     "on_error": "retry", "retry_count": 2}]}
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wf.json"
            p.write_text(json.dumps(data, ensure_ascii=False),
                         encoding="utf-8")
            wf = parse_workflow(str(p))
        with self.assertRaises(ExecutionError) as cm:
            execute_workflow(wf, self.conn)
        self.assertIn("重试 2 次", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
