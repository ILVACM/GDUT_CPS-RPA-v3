"""注册表守卫镜像单测（R15/B-54~B-58、B-66、B-67；原编号 B1/B2/B3/B4/B6/E1/E3）。

背景：`gui/app.py` 启动自检（项 4／4b）中的注册表守卫此前仅少数有单测镜像
（§7 E1），规则演进易单侧更新。本文件为剩余规则补齐**纯标准库镜像断言**，
并断言「总数单一常量」口径（E3/A4：原四处硬编码「9」）。

覆盖：
- B-54 中文名双源：`BUILTIN_OPS[k]["description"]` ≡ `StepMeta.display`
- B-55 `STEP_KIND` 值域：非法值不再静默回退（`classify_step` 报错）
- B-56 `OUTPUT_OPS` ≡ `STEP_KIND` 的 fork∪merge
- B-57 表单注册双向：`_FORM_CLASSES` 键集 ≡ `STEP_CATALOG` 键集（防孤儿表单）
- B-58 `keywords` 非空（空 tuple 致弹层搜索退化）
- B-66 其余自检规则逐一镜像（PRODUCE_LABEL 键集／order 唯一／StepMeta 非空／
  deprecated 类型／_OPS ⊆ SUPPORTED_OPERATORS／跨层键集一致／下限守卫）
- B-67 总数单一常量 `STEP_COUNT`

纯标准库 unittest（gui.forms 延迟导入，对齐既有范式），不新建 QApplication。执行：
    cd rpa_engine && python -m unittest discover -s tests -v
"""

import unittest

from engine.registry import BUILTIN_OPS
from gui.models import (OUTPUT_OPS, PRODUCE_LABEL, STEP_CATALOG, STEP_COUNT,
                        STEP_KINDS, STEP_KIND, active_catalog_keys,
                        default_params, main_buttons, more_buttons)
from ops.step_executor import list_ops


class DualSourceContractTest(unittest.TestCase):
    """B-54：引擎中文名与 GUI 显示名逐键等同（双源无守卫的镜像）。"""

    def test_description_equals_display(self):
        for k in STEP_CATALOG:
            self.assertEqual(
                BUILTIN_OPS[k]["description"], STEP_CATALOG[k].display,
                f"{k} 的引擎 description 与 GUI display 不一致")


class StepKindDomainTest(unittest.TestCase):
    """B-55：STEP_KIND 值域校验。"""

    def test_all_values_in_domain(self):
        for k, kind in STEP_KIND.items():
            self.assertIn(kind, STEP_KINDS, f"{k} 的 STEP_KIND 取值越界: {kind}")

    def test_classify_step_rejects_invalid_value(self):
        from gui.models import classify_step
        original = STEP_KIND["filter"]
        try:
            STEP_KIND["filter"] = "bogus_kind"
            with self.assertRaises(ValueError):
                classify_step("filter")
        finally:
            STEP_KIND["filter"] = original

    def test_classify_step_unknown_type_falls_back(self):
        from gui.models import classify_step
        self.assertEqual(classify_step("not_exist_op"), "sequential")


class OutputOpsEquationTest(unittest.TestCase):
    """B-56：OUTPUT_OPS ≡ STEP_KIND 的 fork∪merge 集合。"""

    def test_output_ops_equals_fork_merge(self):
        deriving = {k for k, v in STEP_KIND.items() if v in ("fork", "merge")}
        self.assertEqual(deriving, set(OUTPUT_OPS))

    def test_produce_label_keys_match_catalog(self):
        self.assertEqual(set(PRODUCE_LABEL.keys()), set(STEP_CATALOG.keys()))


class FormRegistryBidirectionalTest(unittest.TestCase):
    """B-57：目录键 ↔ 表单类双向一致（防孤儿表单与缺表单）。"""

    def test_form_classes_keys_equal_catalog(self):
        from gui.forms import _FORM_CLASSES
        self.assertEqual(set(_FORM_CLASSES.keys()), set(STEP_CATALOG.keys()),
                         "表单注册键集与操作目录不一致（孤儿表单或漏登记）")

    def test_active_ops_have_form(self):
        from gui.forms import get_form_class
        for k, meta in STEP_CATALOG.items():
            if not meta.deprecated:
                self.assertIsNotNone(get_form_class(k), f"{k} 缺参数表单")


class KeywordsGuardTest(unittest.TestCase):
    """B-58：keywords 非空（空 tuple 使弹层搜索退化）。"""

    def test_keywords_non_empty(self):
        for k, meta in STEP_CATALOG.items():
            self.assertTrue(meta.keywords, f"{k} 的 keywords 为空")

    def test_self_check_fails_on_empty_keywords(self):
        """自检镜像：人为置空 keywords 后启动自检须失败（守卫真实生效）。"""
        from gui.app import run_self_check
        meta = STEP_CATALOG["dedup"]
        original = meta.keywords
        try:
            meta.keywords = ()
            self.assertFalse(run_self_check().ok,
                             "keywords 为空时自检未失败（守卫未生效）")
        finally:
            meta.keywords = original


class RemainingSelfCheckRulesTest(unittest.TestCase):
    """B-66：其余自检规则逐一镜像（与 app.py 项 4／4b 同口径）。"""

    def test_engine_keys_equal_gui_keys(self):
        self.assertEqual(set(BUILTIN_OPS.keys()), set(STEP_CATALOG.keys()))

    def test_registered_count_at_least_step_count(self):
        self.assertGreaterEqual(len(BUILTIN_OPS), STEP_COUNT)

    def test_cross_layer_output_flag(self):
        for k in STEP_CATALOG:
            self.assertEqual(bool(BUILTIN_OPS[k].get("output")), k in OUTPUT_OPS,
                             f"{k} 跨层产表口径不一致")

    def test_default_params_subset_whitelist(self):
        for k in STEP_CATALOG:
            extra = set(default_params(k)) - set(BUILTIN_OPS[k]["param_keys"])
            self.assertEqual(extra, set(), f"{k} default_params 超出白名单: {extra}")

    def test_step_meta_fields_non_empty(self):
        for k, meta in STEP_CATALOG.items():
            self.assertTrue(meta.display and meta.desc and meta.category,
                            f"{k} 的 display/desc/category 存在空值")
            self.assertIsInstance(meta.deprecated, bool)

    def test_orders_unique(self):
        orders = [m.order for m in STEP_CATALOG.values()]
        self.assertEqual(len(set(orders)), len(orders), "StepMeta order 存在重复")

    def test_gui_operators_subset_engine(self):
        from gui.forms import _OPS
        from ops.sql_safety import SUPPORTED_OPERATORS
        extra = [op for op in _OPS if op not in SUPPORTED_OPERATORS]
        self.assertEqual(extra, [], f"界面操作符超出引擎白名单: {extra}")

    def test_button_groups_union_disjoint(self):
        mains, mores = set(main_buttons()), set(more_buttons())
        self.assertEqual(mains | mores, set(active_catalog_keys()))
        self.assertFalse(mains & mores)


class StepCountConstantTest(unittest.TestCase):
    """B-67／B-68：总数单一常量口径（原四处硬编码「9」）。"""

    def test_step_count_derives_from_catalog(self):
        self.assertEqual(STEP_COUNT, len(STEP_CATALOG))

    def test_step_count_equals_engine_registry(self):
        self.assertEqual(STEP_COUNT, len(list_ops()))


if __name__ == "__main__":
    unittest.main()
