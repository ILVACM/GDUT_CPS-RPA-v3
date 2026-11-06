"""注册表 StepMeta 单测（2026-09-21 定稿 M4-T1）。

覆盖：兼容层（下标/解包/display_name 回退）、keywords 搜索命中、分类完备、
主/更多按钮派生不变量。纯标准库 unittest，禁 Qt。执行：
    cd rpa_engine && python -m unittest discover -s tests -v
"""

import unittest

from gui.models import (STEP_CATALOG, active_catalog_keys, categories,
                        category_ops, display_name, main_buttons,
                        more_buttons, step_desc)


class CompatLayerTest(unittest.TestCase):
    def test_subscript_compat(self):
        for key, meta in STEP_CATALOG.items():
            self.assertEqual(STEP_CATALOG[key][0], meta.display)
            self.assertEqual(STEP_CATALOG[key][1], meta.desc)

    def test_tuple_unpack_compat(self):
        for key, meta in STEP_CATALOG.items():
            cn, desc = STEP_CATALOG[key]
            self.assertEqual((cn, desc), (meta.display, meta.desc))

    def test_display_name_fallback(self):
        self.assertEqual(display_name("filter"), "条件筛选")
        self.assertEqual(display_name("not_exist_op"), "not_exist_op")

    def test_step_desc_matches_meta(self):
        for key, meta in STEP_CATALOG.items():
            self.assertEqual(step_desc(key), meta.desc)

    def test_subscript_out_of_range(self):
        with self.assertRaises(KeyError):
            STEP_CATALOG["filter"][2]


class SearchAndCategoryTest(unittest.TestCase):
    def test_keywords_hit(self):
        hits = [k for k, m in STEP_CATALOG.items()
                if "vlookup" in m.keywords or "vlookup" in m.display]
        self.assertEqual(hits, ["mapping_match"])

    def test_categories_cover_all(self):
        covered = set()
        for cat in categories():
            covered.update(category_ops(cat))
        self.assertEqual(covered, set(STEP_CATALOG))

    def test_category_count_four(self):
        self.assertEqual(len(categories()), 4)

    def test_order_unique_and_sorted(self):
        for cat in categories():
            orders = [STEP_CATALOG[k].order for k in category_ops(cat)]
            self.assertEqual(orders, sorted(orders))


class ButtonDerivationTest(unittest.TestCase):
    def test_union_disjoint(self):
        mains, mores = set(main_buttons()), set(more_buttons())
        self.assertEqual(mains | mores, set(active_catalog_keys()))
        self.assertFalse(mains & mores)

    def test_main_is_category_rep(self):
        mains = main_buttons()
        self.assertEqual(len(mains), len(categories()))
        for cat in categories():
            ops = category_ops(cat)
            rep = min(ops, key=lambda k: STEP_CATALOG[k].order)
            self.assertIn(rep, mains)

    def test_deprecated_excluded(self):
        meta = STEP_CATALOG["dedup"]
        old = meta.deprecated
        try:
            meta.deprecated = True
            self.assertNotIn("dedup", main_buttons())
            self.assertNotIn("dedup", more_buttons())
        finally:
            meta.deprecated = old

    def test_deprecated_self_check_passes(self):
        """弃用功能存在时启动自检仍通过（B-13 回归保护）。

        构造一个 deprecated=True 功能后：按钮并集口径须与自检同源
        （＝active_catalog_keys()），且 run_self_check().ok 仍为 True
        （功能级弃用通路可用，不再"一启用即自检失败"）。
        """
        from gui.app import run_self_check
        meta = STEP_CATALOG["dedup"]
        old = meta.deprecated
        try:
            meta.deprecated = True
            mains, mores = set(main_buttons()), set(more_buttons())
            self.assertEqual(mains | mores, set(active_catalog_keys()))
            self.assertNotIn("dedup", mains | mores)
            self.assertTrue(run_self_check().ok)
        finally:
            meta.deprecated = old


class GuardRuleTest(unittest.TestCase):
    """注册表三守卫规则直接断言（2026-09-21 审计 R6；与 app.py 自检项
    4/4b 守卫同源规则，纯标准库断言不调 run_self_check）。"""

    def test_output_ops_cross_layer(self):
        from engine.registry import BUILTIN_OPS
        from gui.models import OUTPUT_OPS, STEP_CATALOG
        for k in STEP_CATALOG:
            self.assertEqual(bool(BUILTIN_OPS[k].get("output")),
                             k in OUTPUT_OPS,
                             f"{k} 跨层产表口径不一致")

    def test_default_params_subset_of_param_keys(self):
        from engine.registry import BUILTIN_OPS
        from gui.models import STEP_CATALOG, default_params
        for k in STEP_CATALOG:
            extra = set(default_params(k)) - set(
                BUILTIN_OPS[k].get("param_keys", set()))
            self.assertEqual(extra, set(),
                             f"{k} default_params 超出白名单: {extra}")

    def test_form_registry_covers_active(self):
        from gui.forms import get_form_class
        from gui.models import STEP_CATALOG
        for k, meta in STEP_CATALOG.items():
            if not meta.deprecated:
                self.assertIsNotNone(get_form_class(k),
                                     f"{k} 缺参数表单")


if __name__ == "__main__":
    unittest.main()
