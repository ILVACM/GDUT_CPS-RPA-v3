"""依赖 ↔ 代码 ↔ 打包 交叉校验单测（R15/B-52，原编号 G-7）。

背景：`A-17` 是"依赖清单与打包配置失守"的实例（`xlrd` 只进
`requirements.txt` 未进 spec `hiddenimports` → exe 场景 ImportError）。
本文件建立**自动交叉校验**：扫描 `rpa_engine/` 全部生产 `.py` 的 import，
逐个断言其来源合法——标准库 / 本仓库内包（`ops`/`engine`/`gui`/`paths` 等）/
`requirements.txt` 声明的第三方 / spec `hiddenimports` 声明的模块。

判据（不引入新依赖，纯标准库 `ast` + `sys.stdlib_module_names`）：
  每个顶层 import 名 ∈ stdlib ∪ in-repo ∪ requirements ∪ hiddenimports

执行：
    cd rpa_engine && python -m unittest discover -s tests -v
"""

import ast
import re
import sys
import unittest
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parent.parent          # rpa_engine/
REPO_ROOT = ENGINE_ROOT.parent                                  # 仓库根

# 本仓库内部顶层包/模块（v3 引擎自身代码）
IN_REPO_TOP_LEVEL = {"ops", "engine", "gui", "paths", "main"}

# 源码扫描范围：生产代码（tests/ 与 tools/ 为测试/工具链，不参与打包）
SCAN_DIRS = ("ops", "engine", "gui")
SCAN_TOP_FILES = ("paths.py", "main.py")


def _strip_extras(pip_line: str) -> str:
    """`pandas>=2.0,<4  # 注释` → `pandas`（取包名，去注释与版本约束）。"""
    line = pip_line.split("#", 1)[0].strip()
    return re.split(r"[<>=!~;\[\s]", line, maxsplit=1)[0].strip()


def _requirements_names() -> set:
    names = set()
    text = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = _strip_extras(line)
        if name:
            names.add(name.lower())
    return names


def _hiddenimports_names() -> set:
    """从 RPA_Workflow_v3.spec 的 hiddenimports 列表提取顶层模块名。"""
    spec = REPO_ROOT / "RPA_Workflow_v3.spec"
    if not spec.is_file():
        return set()
    text = spec.read_text(encoding="utf-8")
    block = re.search(r"hiddenimports\s*=\s*\[(.*?)\]", text, re.S)
    if not block:
        return set()
    names = set()
    for raw in re.findall(r"['\"]([^'\"]+)['\"]", block.group(1)):
        names.add(raw.split(".")[0].lower())
    return names


def _import_names(path: Path) -> set:
    """该文件的顶层 import 名集合（ast 解析，忽略相对导入）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    return names


def _production_files():
    for d in SCAN_DIRS:
        yield from sorted((ENGINE_ROOT / d).rglob("*.py"))
    for f in SCAN_TOP_FILES:
        p = ENGINE_ROOT / f
        if p.is_file():
            yield p


class DependencyCrossCheckTest(unittest.TestCase):
    """B-52：所有生产 import 均可由「标准库 ∪ 本项目 ∪ 声明依赖 ∪ 打包声明」解释。"""

    def setUp(self):
        self.stdlib = set(sys.stdlib_module_names)
        self.requirements = _requirements_names()
        self.hidden = _hiddenimports_names()

    def test_boundary_names_discovered(self):
        """前置：requirements 与 spec hiddenimports 均能解析出内容（防解析失效）。"""
        self.assertIn("pandas", self.requirements)
        self.assertIn("pyqt5", self.requirements)
        self.assertTrue(self.hidden, "spec hiddenimports 未解析到内容")

    def test_every_production_import_is_declared(self):
        allowed = (self.stdlib | IN_REPO_TOP_LEVEL
                   | self.requirements | self.hidden)
        unknown: dict = {}
        for path in _production_files():
            for name in _import_names(path):
                if name.lower() not in allowed:
                    unknown.setdefault(name, []).append(
                        str(path.relative_to(REPO_ROOT)))
        self.assertEqual(
            unknown, {},
            f"存在未声明的第三方 import（须补 requirements.txt 或 spec hiddenimports）: {unknown}")

    def test_xlrd_regression_a17(self):
        """A-17 回归：xlrd 已在 requirements **且**在 spec hiddenimports（防单侧修复）。"""
        self.assertIn("xlrd", self.requirements)
        self.assertIn("xlrd", self.hidden)

    def test_spec_hiddenimports_are_in_repo_or_declared(self):
        """spec 声明项本身必须是本仓库包或其外部依赖（防笔误/过期条目）。"""
        for name in self.hidden:
            self.assertTrue(
                name in IN_REPO_TOP_LEVEL or name in self.requirements,
                f"spec hiddenimports 条目无法归因: {name}")

    def test_lock_exists_and_contains_pandas(self):
        """B-50／B-71：lock 存在且含 pandas（主链路依赖不得被精简剔除）。"""
        lock = REPO_ROOT / "requirements.lock"
        self.assertTrue(lock.is_file(), "requirements.lock 不存在")
        text = lock.read_text(encoding="utf-8")
        self.assertIn("pandas==", text)
        self.assertIn("python-docx", text)   # B-72：废弃包原样记录并告警


if __name__ == "__main__":
    unittest.main()
