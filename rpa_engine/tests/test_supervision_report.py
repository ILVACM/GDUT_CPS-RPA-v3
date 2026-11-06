"""
rpa_engine/tests/test_supervision_report.py

supervision_report 专属单测（plan.md §6.1，共 26 条）。
纯标准库 unittest + openpyxl；执行：

  cd rpa_engine
  python -m unittest tests.test_supervision_report -v
"""

import re
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from ops.supervision_report import (
    BLANK_LABEL, EMPTY_CELL, OUTPUT_NAME_PREFIX, OUTPUT_TIME_FMT,
    SHEET_DEPT, SHEET_PROF, SHEET_TODO, TOTAL_LABEL,
    ERR_DATE_COL, ERR_EMPTY_DATA, ERR_MISSING_COLUMN, ERR_OUTPUT_PATH,
    ERR_WORKDAY_RANGE, ERR_WRITE_FAIL,
    build_supervision_report, probe_period, workday_hint,
)

DDL_FULL = ("CREATE TABLE {t} (部门 TEXT, 检查人 TEXT, 检查时间 TEXT, "
            "专业名称 TEXT, 不合格项 INTEGER, 工单状态 TEXT)")


def _conn(ddl=DDL_FULL, table="t1"):
    conn = sqlite3.connect(":memory:")
    conn.execute(ddl.format(t=table))
    return conn


def _add(conn, rows, table="t1"):
    marks = ",".join(["?"] * len(rows[0]))
    conn.executemany(f"INSERT INTO {table} VALUES ({marks})", rows)
    conn.commit()


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig")


def _read_sheets(p: Path):
    import openpyxl
    wb = openpyxl.load_workbook(str(p))
    out = {}
    for name in wb.sheetnames:
        out[name] = [[c.value for c in row] for row in wb[name].iter_rows()]
    return wb.sheetnames, out


class SupervisionReportTest(unittest.TestCase):
    def _run(self, rows, table="t1", wc=0, extras=None, ddl=DDL_FULL):
        conn = _conn(ddl, table)
        _add(conn, rows, table)
        td = tempfile.mkdtemp()
        out = Path(td) / "out.xlsx"
        n = build_supervision_report(conn, table, str(out),
                                     workday_count=wc,
                                     extra_tables=extras or [])
        return out, out.with_suffix(".txt"), n

    # T-01 总表单数
    def test_t01_total(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")] * 3
        _, txt, n = self._run(rows)
        self.assertEqual(n, 2)
        self.assertIn("共填写履职表单3张", _read_text(txt))

    # T-02 不重复人数（表1 合计行）
    def test_t02_distinct_persons(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("B", "李四", "2026-09-01", "配网专业", 0, "已闭环")]
        xlsx, _, _ = self._run(rows)
        _, sheets = _read_sheets(xlsx)
        self.assertEqual(sheets[SHEET_DEPT][-1][0], TOTAL_LABEL)
        self.assertEqual(sheets[SHEET_DEPT][-1][1], 2)

    # T-03 自然日人均（2 位 HALF_UP：2.125 → 2.13；银行家舍入会错算 2.12）
    def test_t03_nat_avg_half_up(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")] * 32
        rows += [("A", "张三", "2026-09-16", "配网专业", 0, "已闭环")] * 2
        # 34 行 / 1 人 / 16 天 = 2.125
        _, txt, _ = self._run(rows)
        self.assertIn("自然日平均每人每日填写表单2.13张", _read_text(txt))

    # T-04 工作日人均（分子固定，分母=workday_count）
    def test_t04_workday_avg(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "李四", "2026-09-01", "配网专业", 0, "已闭环")]
        _, txt, _ = self._run(rows, wc=1)   # 2/2/1 = 1.00
        self.assertIn("工作日平均每人每日填写表单1.00张", _read_text(txt))

    # T-05 有问题表单边界（>0 才计）
    def test_t05_bad_boundaries(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", None, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", -1, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", 1, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", 3, "已闭环")]
        _, txt, _ = self._run(rows)
        self.assertIn("有发现问题表单2张", _read_text(txt))

    # T-06 已闭环＝交集口径
    def test_t06_closed_intersection(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 1, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "张三", "2026-09-01", "配网专业", 1, "草稿")]
        _, txt, _ = self._run(rows)
        self.assertIn("已闭环1张", _read_text(txt))

    # T-07 草稿/整改中＝全表口径（非"问题表单剩余"）
    def test_t07_draft_fixing_full_table(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "草稿"),
                ("A", "张三", "2026-09-01", "配网专业", 0, "整改中"),
                ("A", "张三", "2026-09-01", "配网专业", 5, "草稿")]
        _, txt, _ = self._run(rows)
        self.assertIn("其余有2张草稿、1张整改中", _read_text(txt))

    # T-08 部门数动态（构造 3 个 → 表1 3 行 + 合计）
    def test_t08_dept_dynamic(self):
        rows = [("一部门", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("二部门", "李四", "2026-09-01", "配网专业", 0, "已闭环"),
                ("三部门", "王五", "2026-09-01", "配网专业", 0, "已闭环")]
        xlsx, _, _ = self._run(rows)
        _, sheets = _read_sheets(xlsx)
        self.assertEqual(len(sheets[SHEET_DEPT]), 1 + 3 + 1)

    # T-09 专业占比
    def test_t09_prof_pct(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")] * 3
        rows += [("A", "李四", "2026-09-01", "线路专业", 0, "已闭环")]
        xlsx, _, _ = self._run(rows)
        _, sheets = _read_sheets(xlsx)
        body = sheets[SHEET_PROF][1:-1]
        self.assertEqual([r[2] for r in body], ["75.0%", "25.0%"])
        self.assertEqual(sheets[SHEET_PROF][-1], [TOTAL_LABEL, 4, "100%"])

    # T-10 Excel 3 张 sheet（名称与顺序）
    def test_t10_three_sheets(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")]
        xlsx, _, _ = self._run(rows)
        names, _ = _read_sheets(xlsx)
        self.assertEqual(names, [SHEET_DEPT, SHEET_PROF, SHEET_TODO])

    # T-10b txt 单行 + BOM + 数值一致
    def test_t10b_txt(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")]
        _, txt, _ = self._run(rows)
        raw = txt.read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        text = _read_text(txt)
        self.assertNotIn("\n", text)
        self.assertIn("共填写履职表单1张", text)

    # T-10c 多表合并（UNION ALL：行数相加）
    def test_t10c_merge(self):
        conn = _conn()
        _add(conn, [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")] * 2)
        conn.execute(DDL_FULL.format(t="t2"))
        _add(conn, [("B", "李四", "2026-09-01", "配网专业", 0, "已闭环")] * 3,
             table="t2")
        td = tempfile.mkdtemp()
        out = Path(td) / "out.xlsx"
        build_supervision_report(conn, "t1", str(out), extra_tables=["t2"])
        self.assertIn("共填写履职表单5张", _read_text(out.with_suffix(".txt")))

    # T-10d output_path 为空
    def test_t10d_empty_output_path(self):
        conn = _conn()
        _add(conn, [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")])
        with self.assertRaises(ValueError) as cm:
            build_supervision_report(conn, "t1", "")
        self.assertIn(ERR_OUTPUT_PATH, str(cm.exception))

    # T-10e 默认文件名格式（命名常量）
    def test_t10e_name_format(self):
        name = (OUTPUT_NAME_PREFIX + "-"
                + datetime.now().strftime(OUTPUT_TIME_FMT) + ".xlsx")
        self.assertRegex(name, r"^履职表单报告统计-\d{12}\.xlsx$")

    # T-11 模板渲染无残留占位符
    def test_t11_no_placeholder_left(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 1, "已闭环")]
        _, txt, _ = self._run(rows)
        text = _read_text(txt)
        self.assertNotIn("{", text)
        self.assertNotIn("}", text)

    # T-12 期间识别与标签（单月 / 跨月）
    def test_t12_period(self):
        conn = _conn()
        _add(conn, [("A", "张三", "2026-09-10", "配网专业", 0, "已闭环"),
                    ("A", "张三", "2026-09-20", "配网专业", 0, "已闭环")])
        probe = probe_period(conn, "t1")
        self.assertTrue(probe["found"])
        self.assertEqual(probe["date_min"], "2026-09-10")
        self.assertEqual(probe["date_max"], "2026-09-20")
        self.assertEqual(probe["natural_days"], 11)
        self.assertEqual(probe["workday_default"], 7)
        td = tempfile.mkdtemp()
        out = Path(td) / "out.xlsx"
        build_supervision_report(conn, "t1", str(out))
        self.assertTrue(
            _read_text(out.with_suffix(".txt")).startswith("9月"))
        conn2 = _conn()
        _add(conn2, [("A", "张三", "2026-03-05", "配网专业", 0, "已闭环"),
                     ("A", "张三", "2026-07-01", "配网专业", 0, "已闭环")])
        td2 = tempfile.mkdtemp()
        out2 = Path(td2) / "out.xlsx"
        build_supervision_report(conn2, "t1", str(out2))
        self.assertTrue(
            _read_text(out2.with_suffix(".txt")).startswith("3月-7月"))

    # T-12b 脏日期：计入总数、不参与期间、txt 行尾提示
    def test_t12b_dirty_date(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "张三", "乱码", "配网专业", 0, "已闭环")]
        _, txt, _ = self._run(rows)
        text = _read_text(txt)
        self.assertIn("共填写履职表单2张", text)
        self.assertTrue(text.endswith("（另有 1 行日期无法识别）"))

    # T-12c 口径告警文案
    def test_t12c_workday_hint(self):
        self.assertIn("16", workday_hint(16, 22) or "")
        self.assertIn("22", workday_hint(16, 22) or "")
        self.assertIsNone(workday_hint(22, 22))
        self.assertIsNone(workday_hint(0, 22))
        self.assertIsNone(workday_hint(5, None))

    # T-13 缺列报中文可读错误
    def test_t13_missing_column(self):
        ddl = ("CREATE TABLE {t} (部门 TEXT, 检查人 TEXT, 检查时间 TEXT, "
               "专业名称 TEXT, 工单状态 TEXT)")
        conn = _conn(ddl)
        _add(conn, [("A", "张三", "2026-09-01", "配网专业", "已闭环")])
        with self.assertRaises(ValueError) as cm:
            build_supervision_report(conn, "t1", str(Path(tempfile.mkdtemp()) / "o.xlsx"))
        self.assertIn(ERR_MISSING_COLUMN.format(col="不合格项"), str(cm.exception))

    # T-14 空表 / 全脏日期
    def test_t14_empty_and_all_dirty(self):
        conn = _conn()
        with self.assertRaises(ValueError) as cm:
            build_supervision_report(conn, "t1", str(Path(tempfile.mkdtemp()) / "o.xlsx"))
        self.assertIn(ERR_EMPTY_DATA, str(cm.exception))
        conn2 = _conn()
        _add(conn2, [("A", "张三", "x", "配网专业", 0, "已闭环")])
        with self.assertRaises(ValueError) as cm2:
            build_supervision_report(conn2, "t1", str(Path(tempfile.mkdtemp()) / "o.xlsx"))
        self.assertIn(ERR_DATE_COL, str(cm2.exception))

    # T-15 输出不可写
    def test_t15_unwritable(self):
        conn = _conn()
        _add(conn, [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")])
        td = tempfile.mkdtemp()
        blocker = Path(td) / "blocker"
        blocker.write_text("x", encoding="utf-8")
        with self.assertRaises(ValueError) as cm:
            build_supervision_report(conn, "t1", str(blocker / "o.xlsx"))
        self.assertIn(ERR_WRITE_FAIL, str(cm.exception))

    # T-16 常量区唯一性（静态检查）
    def test_t16_constants_only(self):
        import ops.supervision_report as _sup_mod
        text = Path(_sup_mod.__file__).read_text(encoding="utf-8")
        first_def = text.index("\ndef ")
        tail = text[first_def:]
        literals = ["部门", "检查人", "检查时间", "专业名称", "不合格项",
                    "工单状态", "已闭环", "草稿", "整改中",
                    SHEET_DEPT, SHEET_PROF, SHEET_TODO, OUTPUT_NAME_PREFIX,
                    BLANK_LABEL, TOTAL_LABEL]
        for lit in literals:
            self.assertNotIn(lit, tail, f"业务字面量 {lit!r} 泄漏进函数体")

    # T-17 合计行人数＝全表去重（一人跨两部门 ≠ 相加）
    def test_t17_total_persons_distinct(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("B", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "李四", "2026-09-01", "配网专业", 0, "已闭环")]
        xlsx, _, _ = self._run(rows)
        _, sheets = _read_sheets(xlsx)
        self.assertEqual(sheets[SHEET_DEPT][-1][1], 2)

    # T-18 合计行人均＝全表重算（≠ 部门均值的平均）
    def test_t18_total_avg_full_recompute(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环"),
                ("A", "张三", "2026-09-02", "配网专业", 0, "已闭环"),
                ("B", "李四", "2026-09-01", "配网专业", 0, "已闭环"),
                ("B", "王五", "2026-09-01", "配网专业", 0, "已闭环"),
                ("B", "赵六", "2026-09-02", "配网专业", 0, "已闭环")]
        xlsx, _, _ = self._run(rows)
        _, sheets = _read_sheets(xlsx)
        # A: 2/1/2=1.0；B: 3/3/2=0.5；部门均值平均=0.75→"0.8"（错误算法）
        # 合计：5 行/4 人/2 天=0.625→"0.6"（正确算法，两者不同即为本用例目的）
        self.assertEqual(sheets[SHEET_DEPT][-1][3], "0.6")

    # T-19 表3 全部门 + 编号自然序
    def test_t19_all_depts_and_order(self):
        rows = [("第一总监项目部", "张三", "2026-09-01", "配网专业", 0, "草稿"),
                ("第一总监项目部", "", "2026-09-01", "配网专业", 0, "草稿"),
                ("第三总监项目部", "李四", "2026-09-01", "配网专业", 0, "已闭环"),
                ("藏粤直流总监项目部", "王五", "2026-09-01", "配网专业", 0, "整改中")]
        xlsx, _, _ = self._run(rows)
        _, sheets = _read_sheets(xlsx)
        body = sheets[SHEET_TODO][1:]
        labels = [r[0] for r in body]
        self.assertIn("第三（0张）", labels)
        third = body[labels.index("第三（0张）")]
        self.assertEqual(third[1], EMPTY_CELL)
        self.assertEqual(third[2], EMPTY_CELL)
        # 空检查人的行计入 N 张（2＝张三 1 + 空 1），但不生成人员条目
        self.assertEqual(body[labels.index("第一（2张）")][1], "张三（1张）")
        self.assertLess(labels.index("第一（2张）"),
                        labels.index("藏粤直流（1张）"))

    # T-20 文件冲突：同批 -2 后缀，不覆盖原文件
    def test_t20_conflict_suffix(self):
        rows = [("A", "张三", "2026-09-01", "配网专业", 0, "已闭环")]
        conn = _conn()
        _add(conn, rows)
        td = tempfile.mkdtemp()
        out = Path(td) / "out.xlsx"
        out.write_text("old-xlsx", encoding="utf-8")
        out.with_suffix(".txt").write_text("old-txt", encoding="utf-8")
        build_supervision_report(conn, "t1", str(out))
        self.assertEqual(out.read_text(encoding="utf-8"), "old-xlsx")
        self.assertEqual(out.with_suffix(".txt").read_text(encoding="utf-8"),
                         "old-txt")
        self.assertTrue((Path(td) / "out-2.xlsx").exists())
        self.assertTrue((Path(td) / "out-2.txt").exists())


if __name__ == "__main__":
    unittest.main()
