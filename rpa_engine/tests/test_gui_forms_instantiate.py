"""
rpa_engine/tests/test_gui_forms_instantiate.py

GUI 表单可实例化门禁（防"初始化顺序 / 构造参数漂移"类缺陷回归）。

背景（2026-11-03 缺陷）：
- `SupervisionReportForm.__init__` 在创建「追加数据表」控件之前就读取它
  → `AttributeError: no attribute '_list'`，点选即崩；
- `_validate_all_steps` 构造表单时只传 4 个参数、缺 registry 上下文，
  即使内联面板修好，点「开始」/「保存配置」仍会崩。

本门禁补上"表单真的能 new 出来"这一层——此前 260 条用例只验证
`get_form_class(k) is not None`（类存在），从不实例化。

执行：
  cd rpa_engine
  python -m unittest tests.test_gui_forms_instantiate -v
"""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication  # noqa: E402

from gui.forms import _FORM_CLASSES  # noqa: E402
from gui.models import default_params  # noqa: E402

_APP = None


def _ensure_app():
    """offscreen 下确保 QApplication 单例存在（QWidget 依赖）。"""
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


# 一张典型履职表单的列清单（覆盖新操作所需的 6 列）
_COLS = ["部门", "检查人", "检查时间", "专业名称", "不合格项", "工单状态"]

_REGISTRY = [{
    "table_id": "T1",
    "alias": "履职表单",
    "source_path": r"D:\Test\zeng\履职表单.xlsx",
    "file_path": r"D:\Test\zeng\履职表单.xlsx",
    "date_range": {"min": "2026-09-01", "max": "2026-09-30"},
    "workday_default": 22,
}]


class FormInstantiationTest(unittest.TestCase):
    """表单实例化门禁（10 类全量）。"""

    def setUp(self):
        _ensure_app()

    def test_all_forms_instantiate_with_context(self):
        """全部 10 类表单：带完整上下文构造不抛异常。"""
        for key, cls in _FORM_CLASSES.items():
            with self.subTest(op=key):
                form = cls(
                    default_params(key),
                    table_ids=["T1", "T2"],
                    conn_columns={"T1": list(_COLS)},
                    registry=_REGISTRY,
                    target_table_id="T1",
                    source_dir=r"D:\Test\zeng",
                )
                self.assertIsNotNone(form)

    def test_supervision_report_minimal_context(self):
        """新表单：仅 4 参（无 registry/source_dir）构造也不崩。

        对应 `_validate_all_steps` 的历史构造路径——缺上下文时
        `_selected_ids()` 必须安全返回空列表。
        """
        cls = _FORM_CLASSES["supervision_report"]
        form = cls(default_params("supervision_report"),
                   table_ids=["T1"], conn_columns={"T1": list(_COLS)})
        self.assertIsNotNone(form)
        self.assertEqual(form._selected_ids(), [])

    def test_supervision_report_zero_interaction_params(self):
        """零操作收拢参数：`try_apply()` 通过且 output_path 非空。

        需求：用户点选该函数后即可执行，最多只改工作日天数。
        """
        cls = _FORM_CLASSES["supervision_report"]
        form = cls(
            default_params("supervision_report"),
            table_ids=["T1", "T2"],
            conn_columns={"T1": list(_COLS)},
            registry=_REGISTRY,
            target_table_id="T1",
            source_dir=r"D:\Test\zeng",
        )
        ok, result = form.try_apply()
        self.assertTrue(ok, f"零操作收拢失败: {result}")
        self.assertTrue(result.get("output_path"), "默认保存路径为空")
        self.assertEqual(result.get("extra_table_ids"), [])
        self.assertIn(result.get("workday_count"), (0, 22))


if __name__ == "__main__":
    unittest.main()
