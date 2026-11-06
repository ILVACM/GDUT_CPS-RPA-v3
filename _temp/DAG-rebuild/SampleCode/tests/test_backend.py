"""W-03 伪后端单元测试（unittest，纯标准库）。

运行方式（在 SampleCode 目录下）：
    python -m unittest discover -s tests -v

覆盖：数据文件加载与 meta 完整性、get_dag 结构与引用完整性、
get_node 三类返回、set_status 合法/非法/未知 key 与深拷贝隔离。
"""

import sys
import unittest
from pathlib import Path

# 把项目根（SampleCode/）加入 sys.path，
# 使 `from backend.mock_backend import ...` 可解析
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.mock_backend import get_dag, get_meta, get_node, set_status


class MetaTest(unittest.TestCase):
    """get_meta：数据文件可加载、meta 字段齐全。"""

    def test_meta_fields_complete(self):
        meta = get_meta()
        self.assertEqual(meta["workflow_name"], "电费月度汇总")
        self.assertEqual(meta["version"], "demo-1.0")
        self.assertEqual(meta["data_note"], "示例数据，可替换")
        self.assertEqual(meta["total_steps"], 6)


class GetDagTest(unittest.TestCase):
    """get_dag：结构数量、引用完整性、状态覆盖。"""

    def test_tables_six_two_inputs_four_derived(self):
        tables = get_dag()["tables"]
        self.assertEqual(len(tables), 6)
        inputs = [t for t in tables if t["is_input"]]
        derived = [t for t in tables if not t["is_input"]]
        self.assertEqual(len(inputs), 2)
        self.assertEqual(len(derived), 4)
        # 输入表在前
        self.assertTrue(tables[0]["is_input"])
        self.assertTrue(tables[1]["is_input"])
        # 派生表按产出步骤序：producer_step 的 seq 递增
        seq_by_key = {s["key"]: s["seq"] for s in get_dag()["steps"]}
        producer_seq = [seq_by_key[t["producer_step"]] for t in derived]
        self.assertEqual(producer_seq, sorted(producer_seq))

    def test_steps_six_in_seq_order(self):
        steps = get_dag()["steps"]
        self.assertEqual(len(steps), 6)
        self.assertEqual([s["seq"] for s in steps], [1, 2, 3, 4, 5, 6])

    def test_step_table_references_exist(self):
        dag = get_dag()
        table_keys = {t["key"] for t in dag["tables"]}
        for step in dag["steps"]:
            if step["target_table"] is not None:
                self.assertIn(step["target_table"], table_keys,
                              f"{step['key']} target_table 不存在")
            for extra in step["extra_inputs"]:
                self.assertIn(extra, table_keys,
                              f"{step['key']} extra_inputs 含未知表 {extra}")
            if step["output_table"] is not None:
                self.assertIn(step["output_table"], table_keys,
                              f"{step['key']} output_table 不存在")

    def test_end_step_output_table_none(self):
        end_steps = [s for s in get_dag()["steps"] if s["is_end"]]
        self.assertEqual(len(end_steps), 1)
        self.assertIsNone(end_steps[0]["output_table"])
        self.assertEqual(end_steps[0]["op_type"], "export")

    def test_statuses_cover_all_steps(self):
        dag = get_dag()
        self.assertEqual(set(dag["statuses"]),
                         {s["key"] for s in dag["steps"]})
        for status in dag["statuses"].values():
            self.assertIn(status, ("pending", "running", "done", "failed"))

    def test_failed_step_has_fail_reason(self):
        dag = get_dag()
        failed = sorted(k for k, v in dag["statuses"].items()
                        if v == "failed")
        self.assertEqual(failed, ["S2"])
        self.assertIn("S2", dag["fail_reasons"])
        self.assertTrue(dag["fail_reasons"]["S2"])


class GetNodeTest(unittest.TestCase):
    """get_node：表 / 步骤 / 未知 key 三类返回。"""

    def test_table_node_kind(self):
        node = get_node("T1")
        self.assertIsNotNone(node)
        self.assertEqual(node["kind"], "table")
        self.assertEqual(node["display"], "电费明细表（1月）")
        self.assertTrue(node["is_input"])

    def test_step_node_with_fail_reason(self):
        node = get_node("S2")
        self.assertIsNotNone(node)
        self.assertEqual(node["kind"], "step")
        self.assertEqual(node["status"], "failed")
        self.assertTrue(node["fail_reason"])  # 非空
        self.assertEqual(node["op_type"], "mapping_match")

    def test_unknown_keys_return_none(self):
        self.assertIsNone(get_node("T99"))
        self.assertIsNone(get_node("S99"))
        self.assertIsNone(get_node("X1"))


class SetStatusTest(unittest.TestCase):
    """set_status：合法更新、非法值、未知 key、深拷贝隔离。"""

    def _restore(self, key, status):
        set_status(key, status)

    def test_valid_update_visible_in_get_dag(self):
        self.assertTrue(set_status("S3", "running"))
        self.assertEqual(get_dag()["statuses"]["S3"], "running")
        self.addCleanup(self._restore, "S3", "pending")

    def test_invalid_status_rejected(self):
        self.assertFalse(set_status("S3", "finished"))
        self.assertFalse(set_status("S3", ""))
        self.assertFalse(set_status("S3", "DONE"))  # 大小写敏感
        self.assertEqual(get_dag()["statuses"]["S3"], "pending")

    def test_unknown_key_rejected(self):
        self.assertFalse(set_status("S99", "done"))
        self.assertFalse(set_status("T1", "done"))  # 表 key 不可设状态

    def test_set_status_does_not_touch_other_fields(self):
        before = get_dag()
        self.assertTrue(set_status("S4", "running"))
        self.addCleanup(self._restore, "S4", "pending")
        after = get_dag()
        self.assertEqual(after["statuses"]["S4"], "running")
        # 其他字段不受影响
        self.assertEqual(after["tables"], before["tables"])
        self.assertEqual(after["steps"], before["steps"])
        self.assertEqual(after["fail_reasons"], before["fail_reasons"])

    def test_get_dag_returns_deep_copy(self):
        dag = get_dag()
        dag["statuses"]["S3"] = "failed"
        dag["steps"][0]["name"] = "被污染的名称"
        dag["tables"][0]["display"] = "被污染的表名"
        fresh = get_dag()
        self.assertEqual(fresh["statuses"]["S3"], "pending")
        self.assertNotEqual(fresh["steps"][0]["name"], "被污染的名称")
        self.assertNotEqual(fresh["tables"][0]["display"], "被污染的表名")


if __name__ == "__main__":
    unittest.main()
