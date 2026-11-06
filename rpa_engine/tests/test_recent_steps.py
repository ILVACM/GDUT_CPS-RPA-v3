"""最近使用持久化单测（2026-09-21 修复轮 F8⑤）。

覆盖：损坏 JSON 静默降级空列表；push 去重+置顶+上限 5。
测试前后备份/恢复 storage/recent_steps.json，不污染用户数据。
纯标准库 unittest。执行：
    cd rpa_engine && python -m unittest discover -s tests -v
"""

import unittest

from gui import recent_steps


class RecentStepsTest(unittest.TestCase):

    def setUp(self):
        self._path = recent_steps._recent_file()
        self._backup = (self._path.read_bytes()
                        if self._path.is_file() else None)

    def tearDown(self):
        if self._backup is None:
            self._path.unlink(missing_ok=True)
        else:
            self._path.write_bytes(self._backup)

    def test_corrupt_file_falls_back_empty(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text("{corrupt!!", encoding="utf-8")
        self.assertEqual(recent_steps.load_recent(), [])

    def test_push_dedup_and_cap(self):
        for k in ["a", "b", "c", "d", "e", "f", "a"]:
            recent_steps.push_recent(k)
        self.assertEqual(recent_steps.load_recent(),
                         ["a", "f", "e", "d", "c"])

    def test_missing_file_returns_empty(self):
        self._path.unlink(missing_ok=True)
        self.assertEqual(recent_steps.load_recent(), [])


if __name__ == "__main__":
    unittest.main()
