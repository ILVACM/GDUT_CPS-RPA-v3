"""引擎失败 / 重试 / 取消 / 清理路径单测（B-43，原 P1-2；与 F-07 重叠面）。

覆盖（与 B-05／B-20／B-26／B-33／B-35／B-36 对应）：
- stop 策略 → 抛 ExecutionError（B-05 终止语义基础）；
- retry 策略重试耗尽 → 抛 ExecutionError（B-26）；
- skip 策略 → 不中断执行、步骤判失败、后续步骤继续（B-20 状态口径）；
- 步骤间取消 / 导出循环内取消 → 归并 status="cancelled"（B-33 取消识别）；
- 真实失败（无取消请求）→ 抛 ExecutionError，不被标 cancelled（B-35）；
- 完成后中间表清理路径 → 输入表保留、派生中间表删除（B-36 所在面）。

用 engine 既有可测入口（parse_workflow + execute_workflow + cancel_check 回调桩）
构造三态，断言状态与枚举；纯标准库 unittest，禁 Qt。执行：
    cd rpa_engine && python -m unittest discover -s tests -v
"""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from engine.executor import ExecutionError, execute_workflow
from engine.parser import parse_workflow


def _parse(data: dict):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "wf.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return parse_workflow(str(p))


def _wf(steps, **global_kw) -> dict:
    return {
        "__meta": {"schema_version": "3.1"}, "name": "失败路径流程",
        "global": dict(global_kw),
        "tables": [{"table_id": "T1", "alias": "数据",
                    "source": {"file": "", "sheet": "S1", "header_row": 1},
                    "sqlite_table": "t1"}],
        "steps": steps,
    }


def _ok_step(step_id="S1", out_id="T101", index_col="a", value="0"):
    return {"step_id": step_id, "type": "filter", "name": "筛选",
            "target_table_id": "T1", "output_table_id": out_id,
            "params": {"conditions": [
                {"column": index_col, "op": ">", "value": value}]},
            "on_error": "stop", "retry_count": 3}


def _bad_step(step_id="S1", out_id="T101", on_error="stop", retry_count=3):
    """条件列 "zzz" 不存在 → filter_table 必失败。"""
    return {"step_id": step_id, "type": "filter", "name": "筛选",
            "target_table_id": "T1", "output_table_id": out_id,
            "params": {"conditions": [
                {"column": "zzz", "op": "=", "value": "x"}]},
            "on_error": on_error, "retry_count": retry_count}


class _EngineCase(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("CREATE TABLE t1 (a INTEGER, b TEXT)")
        self.conn.executemany("INSERT INTO t1 VALUES (?, ?)",
                              [(1, "x"), (2, "y"), (3, "z")])
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def table_names(self):
        return {r[0] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}


class FailurePolicyTest(_EngineCase):
    """stop / retry 策略：失败与重试耗尽均以 ExecutionError 终止。"""

    def test_stop_policy_raises(self):
        wf = _parse(_wf([_bad_step(on_error="stop")]))
        with self.assertRaises(ExecutionError):
            execute_workflow(wf, self.conn)

    def test_retry_exhausted_raises(self):
        wf = _parse(_wf([_bad_step(on_error="retry", retry_count=2)]))
        with self.assertRaises(ExecutionError) as cm:
            execute_workflow(wf, self.conn)
        self.assertIn("重试", str(cm.exception))     # 重试耗尽消息（B-26）

    def test_skip_policy_continues_and_marks_failure(self):
        """skip 不中断：跳过步骤不注册派生表，后续步骤继续执行。

        现状口径（B-20 待修面）：status 仍为 "completed"，但 steps_succeeded
        < steps_total → success=False；跳过步骤的派生表未登记。
        """
        wf = _parse(_wf([_bad_step(step_id="S1", out_id="T101",
                                   on_error="skip"),
                         _ok_step(step_id="S2", out_id="T102")]))
        result = execute_workflow(wf, self.conn)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(result["success"])
        self.assertEqual(result["steps_succeeded"], 1)
        self.assertEqual(result["steps_total"], 2)
        self.assertNotIn("T101", result["output_tables"])   # 跳过步未登记
        self.assertIn("T102", result["output_tables"])      # 后续步继续执行


class CancelPathTest(_EngineCase):
    """取消：步骤间检查点与长循环内取消均归并 status="cancelled"。"""

    def test_cancel_before_step(self):
        wf = _parse(_wf([_ok_step(step_id="S1", out_id="T101"),
                         _ok_step(step_id="S2", out_id="T102")]))
        result = execute_workflow(wf, self.conn, cancel_check=lambda: True)
        self.assertEqual(result["status"], "cancelled")
        self.assertFalse(result["success"])
        self.assertEqual(result["steps_succeeded"], 0)
        self.assertEqual(result["output_tables"], {})

    def test_cancel_during_export_loop(self):
        data = _wf([_ok_step(step_id="S1", out_id="T101")])
        with tempfile.TemporaryDirectory() as td:
            data["steps"].append({
                "step_id": "S2", "type": "export", "name": "导出",
                "target_table_id": "T101", "output_table_id": "",
                "params": {"output_path": str(Path(td) / "o.xlsx"),
                           "sheet_name": "数据"},
                "on_error": "stop", "retry_count": 3})
            wf = _parse(data)
            calls = []

            def cancel_check():
                calls.append(1)
                return len(calls) >= 3   # S1/S2 前置放行，导出循环内终止

            result = execute_workflow(wf, self.conn, cancel_check=cancel_check)
        self.assertEqual(result["status"], "cancelled")
        self.assertFalse(result["success"])


class RealFailureSemanticsTest(_EngineCase):
    """真实失败（无取消请求）不得被误标为 cancelled（B-35）。"""

    def test_real_failure_not_cancelled(self):
        events = []
        wf = _parse(_wf([_bad_step(on_error="stop")]))
        with self.assertRaises(ExecutionError):
            execute_workflow(wf, self.conn,
                             progress_callback=lambda sid, st, msg:
                                 events.append((sid, st, msg)),
                             cancel_check=lambda: False)
        # 步骤级如实上报 failed（非 cancelled）
        self.assertIn(("S1", "failed"), [(s, st) for s, st, _ in events])


class CleanupPathTest(_EngineCase):
    """完成后清理中间表；输入表保留；派生映射仍登记（B-36 所在面）。"""

    def test_cleanup_removes_intermediate_keeps_input(self):
        # 两步链：S1 引用输入表 T1，S2 引用 S1 派生表 T101
        data = _wf([_ok_step(step_id="S1", out_id="T101"),
                    {"step_id": "S2", "type": "filter", "name": "筛选 2",
                     "target_table_id": "T101", "output_table_id": "T102",
                     "params": {"conditions": [
                         {"column": "a", "op": ">", "value": 1}]},
                     "on_error": "stop", "retry_count": 3}])
        wf = _parse(data)
        result = execute_workflow(wf, self.conn)
        self.assertEqual(result["status"], "completed")
        names = self.table_names()
        self.assertIn("t1", names)                  # 输入表保留
        self.assertNotIn("t_s1", names)             # 中间表已清理
        self.assertNotIn("t_s2", names)
        # 派生表号 → 物理名映射仍登记（现状口径；B-36 目标为过滤已删表号）
        self.assertEqual(set(result["output_tables"]), {"T101", "T102"})


if __name__ == "__main__":
    unittest.main()
