"""R6/B1（P0-2）：错误话术翻译层单测。

纯标准库 unittest，禁 Qt。执行：
    cd rpa_engine && python -m unittest discover -s tests
"""

import unittest

from gui.error_messages import _RULES, log_hint, translate_error

_FORBIDDEN = ("SQL", "sqlite", "物理表", "t_s", "no such",
              "OperationalError", "PermissionError", "ValueError")


class TranslateErrorTest(unittest.TestCase):

    def test_known_column_error(self):
        out = translate_error("OperationalError: no such column: 区域")
        self.assertIn("数据列不存在", out)
        self.assertNotIn("no such column", out)

    def test_empty_fallback(self):
        for raw in ("", None):
            out = translate_error(raw)
            self.assertIn("意外问题", out)
            self.assertIn("日志", out)

    def test_permission_error_self_rescue(self):
        out = translate_error("PermissionError: [Errno 13] 员工.xlsx")
        self.assertIn("占用", out)
        self.assertIn("重试", out)
        self.assertNotIn("Errno", out)

    def test_rules_clean_and_nonempty(self):
        for key, reason, action in _RULES:
            self.assertTrue(key and reason and action)
            for word in _FORBIDDEN:
                self.assertNotIn(word, reason)
                self.assertNotIn(word, action)

    def test_log_hint_points_to_logs(self):
        self.assertTrue(log_hint().endswith("logs"))
