"""功能函数（ops / step_executor）契约单测（B-42，原 P1-1；与 H-19 重叠面）。

覆盖：
- 全部 BUILTIN_OPS 的逐操作契约（filter / dedup / aggregate / mapping_match /
  export / merge_tables / copy_table / rename_columns / convert_dtype）：
  返回值语义、边界拒绝、缺省口径；
- step_executor 契约：参数白名单（param_keys）、各操作缺省值口径、输出表
  自动命名（t_s{n}）与回显、返回值消费口径（success/message/output_table/
  output_table_id 键集合）、未定义操作/表编号的失败口径；
- 三个文本解析器（gui.forms）的一致策略与往返（与 B-30 共用面）；
- B-28 改动点 3 往返单测补录（R13）：前导零／NOT IN／混合条件／无 repr。

仅做"操作层契约与解析一致性"，不测 GUI 交互。纯标准库 unittest；直调 ops /
step_executor；解析器经 gui.forms 延迟导入（对齐 test_step_catalog 范式），
不新建 QApplication。执行：
    cd rpa_engine && python -m unittest discover -s tests -v
"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from ops.aggregator import aggregate_table
from ops.exporter import export_table
from ops.filter_dedup import dedup_table, filter_table
from ops.mapping_matcher import match_tables
from ops.step_executor import BUILTIN_OPS, execute_step, get_op_func, list_ops
from ops.table_lifecycle import (
    copy_table,
    guard_overwrite_target,
    merge_tables,
)
from ops.table_schema import convert_dtype, rename_columns


def _seed_conn() -> sqlite3.Connection:
    """标准测试库：t(区域 TEXT, 数量 INTEGER, 编号 TEXT) 共 4 行。"""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t (区域 TEXT, 数量 INTEGER, 编号 TEXT)")
    conn.executemany(
        "INSERT INTO t VALUES (?, ?, ?)",
        [("东区", 3, "007"), ("东区", 5, "12"),
         ("西区", 5, "007"), ("西区", 8, "99")],
    )
    conn.commit()
    return conn


class _ConnCase(unittest.TestCase):
    def setUp(self):
        self.conn = _seed_conn()

    def tearDown(self):
        self.conn.close()

    def table_names(self):
        return {r[0] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}

    def row_count(self, table):
        return self.conn.execute(
            f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]


# ---------------------------------------------------------------------------
# filter / dedup / aggregate / mapping_match（Layer 2 业务操作契约）
# ---------------------------------------------------------------------------

class FilterContractTest(_ConnCase):
    """filter_table：条件组合 / 空条件拒绝 / 前导零值按原文本传参。"""

    def test_multi_condition_and(self):
        n = filter_table(
            self.conn, "t",
            [{"column": "区域", "op": "=", "value": "东区"},
             {"column": "数量", "op": ">", "value": 3}],
            "f_and", "AND")
        self.assertEqual(n, 1)
        self.assertEqual(self.row_count("f_and"), 1)
        rows = self.conn.execute(
            'SELECT 区域, 数量 FROM f_and').fetchall()
        self.assertEqual(rows, [("东区", 5)])

    def test_multi_condition_or(self):
        n = filter_table(
            self.conn, "t",
            [{"column": "区域", "op": "=", "value": "东区"},
             {"column": "数量", "op": ">", "value": 5}],
            "f_or", "OR")
        self.assertEqual(n, 3)

    def test_empty_conditions_rejected(self):
        with self.assertRaises(ValueError):
            filter_table(self.conn, "t", [], "f_empty", "AND")

    def test_leading_zero_value_preserved(self):
        """ops 层不数值化：值 "007" 按文本原样传参，"7" 不匹配。"""
        n1 = filter_table(
            self.conn, "t",
            [{"column": "编号", "op": "=", "value": "007"}], "f_z", "AND")
        self.assertEqual(n1, 2)
        n2 = filter_table(
            self.conn, "t",
            [{"column": "编号", "op": "=", "value": "7"}], "f_z2", "AND")
        self.assertEqual(n2, 0)

    def test_invalid_column_rejected(self):
        with self.assertRaises(ValueError):
            filter_table(
                self.conn, "t",
                [{"column": "不存在列", "op": "=", "value": "x"}], "f_bad")


class DedupContractTest(_ConnCase):
    """dedup_table：保留首/末 / 空键拒绝 / keep 非法拒绝。"""

    def test_keep_first(self):
        n = dedup_table(self.conn, "t", ["区域"], "first", "d_first")
        self.assertEqual(n, 2)
        vals = [r[0] for r in self.conn.execute(
            'SELECT 数量 FROM d_first ORDER BY 数量').fetchall()]
        self.assertEqual(vals, [3, 5])          # 各区域首次出现行

    def test_keep_last(self):
        n = dedup_table(self.conn, "t", ["区域"], "last", "d_last")
        self.assertEqual(n, 2)
        vals = [r[0] for r in self.conn.execute(
            'SELECT 数量 FROM d_last ORDER BY 数量').fetchall()]
        self.assertEqual(vals, [5, 8])          # 各区域末次出现行

    def test_empty_key_rejected(self):
        with self.assertRaises(ValueError):
            dedup_table(self.conn, "t", [], "first", "d_empty")

    def test_invalid_keep_rejected(self):
        with self.assertRaises(ValueError):
            dedup_table(self.conn, "t", ["区域"], "middle", "d_bad")


class AggregateContractTest(_ConnCase):
    """aggregate_table：分组 / 指标解析（函数白名单 / count(*) / 别名）。"""

    def test_group_by_sum(self):
        n = aggregate_table(
            self.conn, "t", ["区域"],
            [{"column": "数量", "func": "sum"}], "a_sum")
        self.assertEqual(n, 2)
        rows = dict(self.conn.execute(
            'SELECT 区域, 数量_sum FROM a_sum').fetchall())
        self.assertEqual(rows, {"东区": 8, "西区": 13})

    def test_count_star_whole_table(self):
        n = aggregate_table(
            self.conn, "t", [],
            [{"column": "*", "func": "count", "alias": "总数"}], "a_cnt")
        self.assertEqual(n, 1)
        self.assertEqual(
            self.conn.execute('SELECT 总数 FROM a_cnt').fetchone()[0], 4)

    def test_unsupported_func_rejected(self):
        with self.assertRaises(ValueError):
            aggregate_table(
                self.conn, "t", [], [{"column": "数量", "func": "median"}],
                "a_bad")

    def test_non_count_star_rejected(self):
        with self.assertRaises(ValueError):
            aggregate_table(
                self.conn, "t", [], [{"column": "*", "func": "sum"}], "a_bad2")

    def test_duplicate_alias_rejected(self):
        with self.assertRaises(ValueError):
            aggregate_table(
                self.conn, "t", [],
                [{"column": "数量", "func": "sum", "alias": "x"},
                 {"column": "数量", "func": "max", "alias": "x"}], "a_dup")

    def test_default_alias(self):
        n = aggregate_table(
            self.conn, "t", [], [{"column": "数量", "func": "mean"}], "a_def")
        self.assertEqual(n, 1)
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(a_def)")]
        self.assertIn("数量_mean", cols)

    def test_invalid_group_column_rejected(self):
        with self.assertRaises(ValueError):
            aggregate_table(
                self.conn, "t", ["不存在"],
                [{"column": "数量", "func": "sum"}], "a_bad3")


class MappingMatchContractTest(_ConnCase):
    """mapping_match：JOIN 模式 / 右表列 r_ 前缀 / 非法模式拒绝。"""

    def setUp(self):
        super().setUp()
        self.conn.execute("CREATE TABLE r (区域 TEXT, 分值 INTEGER)")
        self.conn.executemany("INSERT INTO r VALUES (?, ?)",
                              [("东区", 10), ("西区", 20)])
        self.conn.commit()

    def test_inner_join_row_count_and_prefix(self):
        n = match_tables(self.conn, "t", "r", {"区域": "区域"},
                         "inner_join", "m_inner")
        self.assertEqual(n, 4)
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(m_inner)")]
        self.assertIn("r_分值", cols)

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            match_tables(self.conn, "t", "r", {"区域": "区域"},
                         "cross_join", "m_bad")

    def test_same_table_rejected(self):
        with self.assertRaises(ValueError):
            match_tables(self.conn, "t", "t", {"区域": "区域"},
                         "inner_join", "m_bad2")

    def test_empty_match_columns_rejected(self):
        with self.assertRaises(ValueError):
            match_tables(self.conn, "t", "r", {}, "inner_join", "m_bad3")


# ---------------------------------------------------------------------------
# export / copy / merge / rename / convert（返回值语义与边界）
# ---------------------------------------------------------------------------

class ExportContractTest(_ConnCase):
    """export_table：返回导出行数 / 缺省 sheet / 路径与表名校验。"""

    def test_export_returns_row_count(self):
        from openpyxl import load_workbook
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "o.xlsx"
            n = export_table(self.conn, "t", str(out))
            self.assertEqual(n, 4)                       # 不含表头
            self.assertTrue(out.is_file())
            wb = load_workbook(str(out))
            try:
                ws = wb.active
                self.assertEqual(ws.title, "数据")       # 缺省 sheet 名
                self.assertEqual([c.value for c in ws[1]],
                                 ["区域", "数量", "编号"])
            finally:
                wb.close()

    def test_non_xlsx_suffix_rejected(self):
        """R15/B-49（原 H-26）：后缀非 .xlsx 时**报错**，不再静默改写。
        旧行为「no_ext → no_ext.xlsx」已废止（D10 所见即所得）。"""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "no_ext"
            with self.assertRaises(ValueError):
                export_table(self.conn, "t", str(out))
            self.assertFalse((Path(td) / "no_ext.xlsx").exists())

    def test_csv_suffix_rejected_not_rewritten(self):
        """R15/B-49：报表.csv 不得被静默改写为 报表.xlsx。"""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "报表.csv"
            with self.assertRaises(ValueError):
                export_table(self.conn, "t", str(out))
            self.assertFalse((Path(td) / "报表.xlsx").exists())

    def test_xlsx_suffix_export_ok(self):
        """R15/B-49 反向：合法 .xlsx 路径正常导出（行为未受影响）。"""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "ok.xlsx"
            self.assertEqual(export_table(self.conn, "t", str(out)), 4)
            self.assertTrue(out.is_file())

    def test_missing_table_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                export_table(self.conn, "no_such", str(Path(td) / "o.xlsx"))

    def test_empty_output_path_rejected(self):
        with self.assertRaises(ValueError):
            export_table(self.conn, "t", "")


class LifecycleContractTest(_ConnCase):
    """copy_table / merge_tables 返回 None；rename/convert 返回 bool。"""

    def test_copy_returns_none_and_copies(self):
        self.assertIsNone(copy_table(self.conn, "t", "t_copy"))
        self.assertEqual(self.row_count("t_copy"), 4)
        cols_src = [r[1] for r in self.conn.execute("PRAGMA table_info(t)")]
        cols_dst = [r[1] for r in self.conn.execute(
            "PRAGMA table_info(t_copy)")]
        self.assertEqual(cols_src, cols_dst)

    def test_copy_same_name_rejected(self):
        with self.assertRaises(ValueError):
            copy_table(self.conn, "t", "t")

    def test_merge_returns_none_and_unions(self):
        self.conn.execute("CREATE TABLE t2 (区域 TEXT, 数量 INTEGER, 编号 TEXT)")
        self.conn.executemany("INSERT INTO t2 VALUES (?, ?, ?)",
                              [("北区", 1, "1"), ("南区", 2, "2")])
        self.conn.commit()
        self.assertIsNone(merge_tables(self.conn, ["t", "t2"], "m"))
        self.assertEqual(self.row_count("m"), 6)

    def test_merge_needs_two_tables(self):
        with self.assertRaises(ValueError):
            merge_tables(self.conn, ["t"], "m_bad")

    def test_merge_mismatched_columns_rejected(self):
        self.conn.execute("CREATE TABLE t3 (区域 TEXT, 数量 INTEGER)")
        self.conn.commit()
        with self.assertRaises(ValueError):
            merge_tables(self.conn, ["t", "t3"], "m_bad2")

    def test_rename_returns_true_on_success(self):
        self.assertTrue(rename_columns(self.conn, "t", {"区域": "地区"}))
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(t)")]
        self.assertIn("地区", cols)
        self.assertNotIn("区域", cols)

    def test_rename_returns_false_when_column_missing(self):
        self.assertFalse(rename_columns(self.conn, "t", {"不存在": "x"}))

    def test_convert_returns_true_on_success(self):
        self.assertTrue(convert_dtype(self.conn, "t", "数量", "INTEGER", "TEXT"))
        col_type = [r[2] for r in self.conn.execute(
            "PRAGMA table_info(t)") if r[1] == "数量"][0]
        self.assertEqual(col_type, "TEXT")

    def test_convert_invalid_path_rejected(self):
        with self.assertRaises(ValueError):
            convert_dtype(self.conn, "t", "数量", "INTEGER", "BLOB")

    def test_guard_overwrite_blocks_nonempty_live_table(self):
        self.conn.execute("CREATE TABLE g (x INTEGER)")
        self.conn.execute("INSERT INTO g VALUES (1)")
        self.conn.commit()
        with self.assertRaises(ValueError):
            guard_overwrite_target(self.conn, "g")
        self.assertIsNone(guard_overwrite_target(self.conn, "g_free"))


# ---------------------------------------------------------------------------
# step_executor 契约（参数白名单 / 缺省口径 / 输出表命名 / 返回值消费）
# ---------------------------------------------------------------------------

class StepExecutorRegistryContractTest(unittest.TestCase):
    """注册表 argparse：操作名清单、函数查找、参数白名单口径。"""

    def test_list_ops_sorted_and_complete(self):
        from gui.models import STEP_COUNT
        self.assertEqual(list_ops(), sorted(BUILTIN_OPS.keys()))
        # R15/B-67：引用 STEP_COUNT 单一常量（原硬编码 9）
        self.assertEqual(len(list_ops()), STEP_COUNT)

    def test_get_op_func_lookup(self):
        self.assertTrue(callable(get_op_func("filter")))
        self.assertIsNone(get_op_func("not_exist_op"))

    def test_param_keys_whitelist(self):
        expected = {
            "filter": {"conditions", "logic", "output_table"},
            "dedup": {"key_columns", "keep", "output_table"},
            "mapping_match": {"match_table_id", "match_columns", "mode",
                              "output_table"},
            "aggregate": {"group_by", "metrics", "conditions", "output_table"},
            "export": {"output_path", "sheet_name"},
            "merge_tables": {"match_table_ids", "output_table"},
            "copy_table": {"output_table"},
            "rename_columns": {"mapping"},
            "convert_dtype": {"column", "from_type", "to_type"},
        }
        for op, keys in expected.items():
            self.assertEqual(BUILTIN_OPS[op]["param_keys"], keys, op)


class StepExecutorDispatchContractTest(_ConnCase):
    """execute_step：缺省口径 / 输出表命名 / 失败口径 / 返回值消费。"""

    def _map(self):
        return {"T1": "t"}

    def test_return_dict_key_shape(self):
        step = {"step_id": "S1", "type": "filter", "name": "筛选",
                "target_table_id": "T1", "output_table_id": "T101",
                "params": {"conditions": [
                    {"column": "数量", "op": ">", "value": 0}]}}
        r = execute_step(step, self.conn, self._map(), 1)
        self.assertEqual(set(r), {"success", "message",
                                  "output_table", "output_table_id"})
        self.assertTrue(r["success"])
        self.assertEqual(r["output_table_id"], "T101")   # 派生表编号回显

    def test_output_table_default_naming(self):
        step = {"step_id": "S1", "type": "filter", "name": "筛选",
                "target_table_id": "T1",
                "params": {"conditions": [
                    {"column": "数量", "op": ">", "value": 0}]}}
        r = execute_step(step, self.conn, self._map(), 7)
        self.assertTrue(r["success"])
        self.assertEqual(r["output_table"], "t_s7")      # 缺省 t_s{n}
        self.assertIn("t_s7", self.table_names())
        self.assertIsNone(r["output_table_id"])          # 未声明派生编号

    def test_output_table_explicit_honored(self):
        step = {"step_id": "S1", "type": "filter", "name": "筛选",
                "target_table_id": "T1",
                "params": {"output_table": "myout",
                           "conditions": [
                               {"column": "数量", "op": ">", "value": 0}]}}
        r = execute_step(step, self.conn, self._map(), 1)
        self.assertEqual(r["output_table"], "myout")
        self.assertIn("myout", self.table_names())

    def test_filter_default_logic_is_and(self):
        conds = [{"column": "区域", "op": "=", "value": "东区"},
                 {"column": "数量", "op": ">", "value": 5}]
        step = {"step_id": "S1", "type": "filter", "name": "筛选",
                "target_table_id": "T1", "params": {"conditions": conds}}
        r = execute_step(step, self.conn, self._map(), 1)
        self.assertTrue(r["success"])
        self.assertEqual(self.row_count(r["output_table"]), 0)   # AND

    def test_filter_explicit_or_honored(self):
        conds = [{"column": "区域", "op": "=", "value": "东区"},
                 {"column": "数量", "op": ">", "value": 5}]
        step = {"step_id": "S1", "type": "filter", "name": "筛选",
                "target_table_id": "T1",
                "params": {"logic": "OR", "output_table": "out_or",
                           "conditions": conds}}
        r = execute_step(step, self.conn, self._map(), 1)
        self.assertEqual(self.row_count(r["output_table"]), 3)

    def test_dedup_default_keep_is_first(self):
        step = {"step_id": "S1", "type": "dedup", "name": "去重",
                "target_table_id": "T1",
                "params": {"key_columns": ["区域"], "output_table": "out_d"}}
        r = execute_step(step, self.conn, self._map(), 1)
        self.assertTrue(r["success"])
        vals = sorted(r0[0] for r0 in self.conn.execute(
            'SELECT 数量 FROM out_d'))
        self.assertEqual(vals, [3, 5])                   # first 策略

    def test_export_default_sheet_name(self):
        from openpyxl import load_workbook
        with tempfile.TemporaryDirectory() as td:
            step = {"step_id": "S1", "type": "export", "name": "导出",
                    "target_table_id": "T1",
                    "params": {"output_path": str(Path(td) / "e.xlsx")}}
            r = execute_step(step, self.conn, self._map(), 1)
            self.assertTrue(r["success"])
            self.assertIsNone(r["output_table"])         # export 不产表
            wb = load_workbook(str(Path(td) / "e.xlsx"))
            try:
                self.assertEqual(wb.active.title, "数据")   # 缺省 sheet
            finally:
                wb.close()

    def test_non_output_op_has_no_output_table(self):
        step = {"step_id": "S1", "type": "rename_columns", "name": "改表头",
                "target_table_id": "T1",
                "params": {"mapping": {"区域": "地区"}}}
        r = execute_step(step, self.conn, self._map(), 1)
        self.assertTrue(r["success"])
        self.assertIsNone(r["output_table"])

    def test_unknown_op_rejected(self):
        step = {"step_id": "S1", "type": "nope", "name": "x",
                "target_table_id": "T1", "params": {}}
        r = execute_step(step, self.conn, self._map(), 1)
        self.assertFalse(r["success"])
        self.assertIn("未定义", r["message"])

    def test_missing_target_table_id_rejected(self):
        step = {"step_id": "S1", "type": "filter", "name": "x", "params": {}}
        r = execute_step(step, self.conn, self._map(), 1)
        self.assertFalse(r["success"])
        self.assertIn("缺少 target_table_id", r["message"])

    def test_undefined_table_id_rejected(self):
        step = {"step_id": "S1", "type": "filter", "name": "x",
                "target_table_id": "T9", "params": {"conditions": [
                    {"column": "区域", "op": "=", "value": "东区"}]}}
        r = execute_step(step, self.conn, self._map(), 1)
        self.assertFalse(r["success"])
        self.assertIn("未定义", r["message"])

    def test_mapping_match_missing_match_table_rejected(self):
        step = {"step_id": "S1", "type": "mapping_match", "name": "x",
                "target_table_id": "T1", "params": {}}
        r = execute_step(step, self.conn, self._map(), 1)
        self.assertFalse(r["success"])
        self.assertIn("缺少 match_table_id", r["message"])

    def test_export_missing_output_path_rejected(self):
        step = {"step_id": "S1", "type": "export", "name": "x",
                "target_table_id": "T1", "params": {}}
        r = execute_step(step, self.conn, self._map(), 1)
        self.assertFalse(r["success"])
        self.assertIn("缺少 output_path", r["message"])


# ---------------------------------------------------------------------------
# 三个文本解析器（gui.forms）的一致策略与往返（与 B-30 共用面）
# ---------------------------------------------------------------------------

def _parsers():
    """延迟导入 gui.forms 解析器（对齐 test_step_catalog 的延迟导入范式）。"""
    from gui.forms import (
        format_conditions,
        parse_condition_lines,
        parse_list_value,
        parse_pair_lines,
        parse_token_list,
    )
    return (parse_pair_lines, parse_token_list, parse_list_value,
            parse_condition_lines, format_conditions)


class ParseContractTest(unittest.TestCase):
    """解析器一致策略：空项丢弃、清单解析、条件往返一致。"""

    def test_pair_lines_ignores_blank_and_incomplete(self):
        parse_pair_lines, _, _, _, _ = _parsers()
        self.assertEqual(
            parse_pair_lines("a=1\n\nbad\n=2\nk=\n  x = 9 "),
            {"a": "1", "x": "9"})

    def test_token_list_split_dedup(self):
        _, parse_token_list, _, _, _ = _parsers()
        self.assertEqual(parse_token_list(" a , b ,a ,, "), ["a", "b"])

    def test_list_value_strips_parens(self):
        _, _, parse_list_value, _, _ = _parsers()
        self.assertEqual(parse_list_value("(a, b、c)"), ["a", "b", "c"])

    def test_three_parsers_drop_empty_consistently(self):
        """三个解析器一致丢弃空项（parse_pair_lines 丢空行/空键值）。"""
        parse_pair_lines, parse_token_list, parse_list_value, _, _ = _parsers()
        self.assertEqual(parse_token_list("a,,b"), ["a", "b"])
        self.assertEqual(parse_list_value("a,,b"), ["a", "b"])
        self.assertEqual(parse_pair_lines("a=1\n\n\nb=2"), {"a": "1", "b": "2"})

    def test_condition_in_value_is_list(self):
        _, _, _, parse_condition_lines, _ = _parsers()
        parsed = parse_condition_lines("区域 IN 东区, 西区")
        self.assertEqual(parsed, [{"column": "区域", "op": "IN",
                                   "value": ["东区", "西区"]}])

    def test_condition_is_null_value_none(self):
        _, _, _, parse_condition_lines, _ = _parsers()
        self.assertEqual(parse_condition_lines("备注 IS NULL"),
                         [{"column": "备注", "op": "IS NULL", "value": None}])

    def test_condition_number_converted(self):
        _, _, _, parse_condition_lines, _ = _parsers()
        self.assertEqual(parse_condition_lines("数量 > 5"),
                         [{"column": "数量", "op": ">", "value": 5}])

    def test_condition_date_preserved_as_text(self):
        _, _, _, parse_condition_lines, _ = _parsers()
        self.assertEqual(parse_condition_lines("日期 = 2026-02-20"),
                         [{"column": "日期", "op": "=",
                           "value": "2026-02-20"}])

    def test_condition_unparsable_line_raises(self):
        _, _, _, parse_condition_lines, _ = _parsers()
        with self.assertRaises(ValueError):
            parse_condition_lines("随便乱写无操作符")

    def test_condition_list_round_trip(self):
        """format_conditions ↔ parse_condition_lines：list 值往返一致。"""
        _, _, _, parse_condition_lines, format_conditions = _parsers()
        conds = [{"column": "区域", "op": "IN", "value": ["东区", "西区"]}]
        text = format_conditions(conds)
        self.assertEqual(parse_condition_lines(text), conds)

    # ------------------------------------------------------------------
    # R13/B-28 改动点 3 补录（plan.md B-28 §5 验证口径／§7 验收标准）
    # ------------------------------------------------------------------

    def test_condition_list_round_trip_leading_zeros(self):
        """前导零 list 值往返后仍为原文本列表（不被数值化，B-28 §5 用例）。"""
        _, _, _, parse_condition_lines, format_conditions = _parsers()
        conds = [{"column": "电表号", "op": "IN", "value": ["0123", "0456"]}]
        text = format_conditions(conds)
        self.assertEqual(parse_condition_lines(text), conds)

    def test_condition_not_in_round_trip(self):
        """NOT IN list 值往返恒等（B-14/B-28 共用解析实现）。"""
        _, _, _, parse_condition_lines, format_conditions = _parsers()
        conds = [{"column": "供电所", "op": "NOT IN", "value": ["A所", "B所"]}]
        text = format_conditions(conds)
        self.assertEqual(parse_condition_lines(text), conds)

    def test_condition_mixed_round_trip_order_preserved(self):
        """list／标量／日期／IS NULL 混合条件往返恒等且顺序不变。"""
        _, _, _, parse_condition_lines, format_conditions = _parsers()
        conds = [
            {"column": "区域", "op": "IN", "value": ["东区", "西区"]},
            {"column": "数量", "op": ">", "value": 5},
            {"column": "日期", "op": "=", "value": "2026-02-20"},
            {"column": "备注", "op": "IS NULL", "value": None},
        ]
        text = format_conditions(conds)
        self.assertEqual(parse_condition_lines(text), conds)

    def test_condition_list_render_no_python_repr(self):
        """渲染文本无 Python repr 痕迹（B-28 §5 失败判据显式断言）。"""
        _, _, _, _, format_conditions = _parsers()
        text = format_conditions(
            [{"column": "电表号", "op": "IN", "value": ["0123", "0456"]}])
        self.assertNotIn("[", text)
        self.assertNotIn("]", text)
        self.assertNotIn("'", text)
        self.assertEqual(text, "电表号 IN 0123、0456")

    def test_condition_paren_form_round_trip_stable(self):
        """圆括号输入形态解析为 list 后，二次往返稳定（幂等）。"""
        _, _, _, parse_condition_lines, format_conditions = _parsers()
        expected = [{"column": "电表号", "op": "IN",
                     "value": ["0123", "0456"]}]
        first = parse_condition_lines("电表号 IN (0123, 0456)")
        self.assertEqual(first, expected)
        second = parse_condition_lines(format_conditions(first))
        self.assertEqual(second, expected)


if __name__ == "__main__":
    unittest.main()
