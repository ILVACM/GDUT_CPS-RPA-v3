"""
rpa_engine/gui/app.py

GUI 应用入口：日志配置、启动自检（6 项，≤3 秒）、主窗口启动。

- 模块级禁止 import gui.main_window（MainWindow 仅在 launch_gui 内惰性导入，防循环）。
- last_config 只负责读取；写入动作在 MainWindow._save_last_config。
"""

import importlib
import json
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from engine.registry import BUILTIN_OPS
from paths import get_engine_root

ENGINE_ROOT = get_engine_root()
WORKSPACE_DIR = ENGINE_ROOT / "workspace"
LAST_CONFIG_PATH = WORKSPACE_DIR / "last_config.json"


@dataclass
class SelfCheckItem:
    """单项自检结果。"""

    name: str
    ok: bool
    detail: str


@dataclass
class SelfCheckResult:
    """整体自检结果（含上次配置载入）。"""

    ok: bool
    items: List[SelfCheckItem]
    elapsed_ms: int
    last_config: Optional[Dict[str, Any]]


def run_self_check() -> SelfCheckResult:
    """
    启动自检（6 项按序执行，均为快速操作，总预算 3 秒）：
    1. Python 版本 ≥3.9；2. 依赖可导入；3. 目录可写；
    4. 用户操作目录注册（项数见 gui.models.STEP_COUNT）；4b. 注册表字段完整性；5. 载入上次配置。
    """
    t0 = time.time()
    items: List[SelfCheckItem] = []
    last_config: Optional[Dict[str, Any]] = None

    # 项1：Python 版本
    py_ok = sys.version_info >= (3, 9)
    items.append(SelfCheckItem(
        name="Python 版本检查",
        ok=py_ok,
        detail=f"当前版本 {sys.version.split()[0]}（要求 ≥3.9）",
    ))

    # 项2：依赖可导入
    failed_modules: List[str] = []
    for mod_name in ["pandas", "openpyxl", "loguru", "psutil", "PyQt5"]:
        try:
            importlib.import_module(mod_name)
        except ImportError:
            failed_modules.append(mod_name)
    if failed_modules:
        dep_ok, dep_detail = False, "缺失依赖: " + ", ".join(failed_modules)
    else:
        dep_ok, dep_detail = True, "全部依赖可导入"
    items.append(SelfCheckItem(name="依赖检查", ok=dep_ok, detail=dep_detail))

    # 项3：目录可写（不存在则创建，写入临时文件后立即删除验证权限）
    dir_problems: List[str] = []
    for rel in ("workspace", "logs", "temp"):
        target = ENGINE_ROOT / rel
        try:
            target.mkdir(parents=True, exist_ok=True)
            probe = target / ".selfcheck_probe.tmp"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
        except OSError as e:
            dir_problems.append(f"{rel}: {e}")
    if dir_problems:
        # R6/C3（P1-10/D3② 便携约定）：失败提示人话化＋安置指引
        dir_ok = False
        dir_detail = ("当前文件夹不允许写入（" + "; ".join(dir_problems)
                      + "）。请把程序整体移动到可写位置（例如 D:\\RPA工具），"
                        "不要放在 C:\\Program Files 或只读盘/受保护目录。")
    else:
        dir_ok, dir_detail = True, "workspace/logs/temp 均可写"
    items.append(SelfCheckItem(name="目录可写检查", ok=dir_ok, detail=dir_detail))

    # 项4：用户操作目录注册（BUILTIN_OPS，v3.1 应有 STEP_COUNT 项）
    #      并逐键比对 GUI 侧 STEP_CATALOG（models.py 副本）与引擎注册表，
    #      防止两处目录漂移（新增操作漏同步时启动即报错）
    try:
        from engine.registry import BUILTIN_OPS
        from gui.models import OUTPUT_OPS, STEP_CATALOG, STEP_COUNT
        registered = len(BUILTIN_OPS)
        engine_keys = set(BUILTIN_OPS.keys())
        gui_keys = set(STEP_CATALOG.keys())
        if registered < STEP_COUNT:
            reg_ok = False
            reg_detail = (f"应注册至少 {STEP_COUNT} 种操作，"
                          f"实际 {registered}: {sorted(engine_keys)}")
        elif engine_keys != gui_keys:
            reg_ok = False
            reg_detail = (
                "GUI 操作目录与引擎注册表不一致——"
                f"引擎多出: {sorted(engine_keys - gui_keys) or '无'}；"
                f"GUI 多出: {sorted(gui_keys - engine_keys) or '无'}"
            )
        else:
            # 守卫①跨层产表口径（2026-09-21 审计 R6）：引擎 output 标志
            # 与 GUI OUTPUT_OPS 必须逐键一致（画布分号 vs 引擎建表）
            mismatch = [k for k in gui_keys
                        if bool(BUILTIN_OPS[k].get("output"))
                        != (k in OUTPUT_OPS)]
            if mismatch:
                reg_ok = False
                reg_detail = f"跨层产表口径不一致: {sorted(mismatch)}"
            else:
                reg_ok = True
                reg_detail = (f"已注册 {registered} 种操作"
                              "（GUI 目录逐键比对一致+跨层产表口径一致）")
    except Exception as e:
        reg_ok = False
        reg_detail = f"操作目录注册失败: {type(e).__name__}: {e}"
    items.append(SelfCheckItem(name="操作目录注册检查", ok=reg_ok, detail=reg_detail))

    # 项4b：注册表字段完整性（2026-09-18 M22）
    #      校验 STEP_KIND/PRODUCE_LABEL/OUTPUT_OPS 三口径自洽与按钮分组完备，
    #      防止生产注册表字段漂移（仅自洽性校验，不依赖未实现字段；失败不抛异常）
    try:
        from engine.registry import BUILTIN_OPS
        from gui.forms import get_form_class
        from gui.models import (OUTPUT_OPS, PRODUCE_LABEL, STEP_CATALOG,
                                STEP_KINDS, STEP_KIND, active_catalog_keys,
                                default_params, main_buttons, more_buttons)
        problems: List[str] = []
        catalog_keys = set(STEP_CATALOG.keys())
        if set(PRODUCE_LABEL.keys()) != catalog_keys:
            problems.append(
                f"PRODUCE_LABEL 键集不一致: {sorted(set(PRODUCE_LABEL.keys()) ^ catalog_keys)}")
        orders: List[int] = []
        for t, meta in STEP_CATALOG.items():
            # R15/B-55（原编号 B2）：STEP_KIND 值域校验（非法值不再静默回退）
            kind = STEP_KIND.get(t)
            if kind not in STEP_KINDS:
                problems.append(f"{t} 的 STEP_KIND 取值非法: {kind!r}")
            if (t in OUTPUT_OPS) != (PRODUCE_LABEL.get(t) is not None):
                problems.append(f"{t} 的 OUTPUT_OPS 与 PRODUCE_LABEL 口径不一致")
            # StepMeta 字段完整性（2026-09-21 定稿 M3-T6）
            if not meta.display or not meta.desc or not meta.category:
                problems.append(f"{t} 的 StepMeta display/desc/category 存在空值")
            if not isinstance(meta.keywords, tuple):
                problems.append(f"{t} 的 StepMeta keywords 非 tuple")
            # R15/B-58（原编号 B6）：keywords 非空守卫——空 tuple 会使弹层
            # 搜索退化为仅 display＋key，用户搜不到别名
            if not meta.keywords:
                problems.append(f"{t} 的 StepMeta keywords 为空（弹层搜索退化）")
            if not isinstance(meta.deprecated, bool):
                problems.append(f"{t} 的 StepMeta deprecated 非 bool")
            # 守卫②默认参数 ⊆ 引擎白名单（2026-09-21 审计 R6：防静默丢参）
            extra_keys = (set(default_params(t))
                          - set(BUILTIN_OPS.get(t, {}).get("param_keys", set())))
            if extra_keys:
                problems.append(
                    f"{t} 的 default_params 键超出 param_keys 白名单: "
                    f"{sorted(extra_keys)}")
            orders.append(meta.order)
        if len(set(orders)) != len(orders):
            problems.append("StepMeta order 存在重复")
        # 操作符白名单单一源守卫（R6/F4，2026-09-24）：
        # 界面下拉 _OPS 必须 ⊆ 引擎 SUPPORTED_OPERATORS（防两处清单漂移）
        from gui.forms import _OPS
        from ops.sql_safety import SUPPORTED_OPERATORS
        extra_ops = [op for op in _OPS if op not in SUPPORTED_OPERATORS]
        if extra_ops:
            problems.append(f"界面操作符超出引擎白名单: {extra_ops}")
        # 守卫③非弃用操作必有参数表单（2026-09-21 审计 R6：防新步无表单）
        missing_forms = [k for k, mm in STEP_CATALOG.items()
                         if not mm.deprecated and get_form_class(k) is None]
        if missing_forms:
            problems.append(f"非弃用操作缺参数表单: {sorted(missing_forms)}")
        main_set, more_set = set(main_buttons()), set(more_buttons())
        # B-13：按钮分组比对口径与按钮侧同源（排除弃用），避免任一功能被
        # 标记 deprecated=True 时两侧集合大小不等导致启动自检失败
        active_keys = set(active_catalog_keys())
        if main_set | more_set != active_keys:
            problems.append(
                f"按钮分组并集不一致: {sorted((main_set | more_set) ^ active_keys)}")
        if main_set & more_set:
            problems.append(f"按钮分组交集非空: {sorted(main_set & more_set)}")
        if problems:
            reg4b_ok, reg4b_detail = False, "; ".join(problems)
        else:
            reg4b_ok = True
            reg4b_detail = "注册表字段自洽（kind/produce_label/产表口径/StepMeta/按钮分组）"
    except Exception as e:
        reg4b_ok = False
        reg4b_detail = f"注册表字段完整性检查失败: {type(e).__name__}: {e}"
    items.append(SelfCheckItem(name="注册表字段完整性检查", ok=reg4b_ok, detail=reg4b_detail))

    # 项5：载入上次配置（文件不存在/解析失败均视为通过，不阻断启动）
    cfg_detail = "未发现历史配置（首次启动）"
    if LAST_CONFIG_PATH.is_file():
        try:
            raw = json.loads(LAST_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                last_config = raw
                cfg_detail = "已载入上次配置"
            else:
                logger.warning("[app] last_config.json 根节点不是对象，忽略")
                cfg_detail = "历史配置格式异常，已忽略"
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"[app] last_config.json 解析失败: {e}")
            cfg_detail = "历史配置解析失败，已忽略"
    items.append(SelfCheckItem(name="上次配置载入", ok=True, detail=cfg_detail))

    # 项5 附加：引用路径存在性检查（v3.1：tables[].source.file 与 export output_path），
    # 缺失仅记 DEBUG，不阻断、不弹窗
    if isinstance(last_config, dict):
        for t in last_config.get("tables", []) or []:
            if not isinstance(t, dict):
                continue
            src = t.get("source", {})
            f = src.get("file")
            if isinstance(f, str) and f and not Path(f).exists():
                logger.debug(f"[app] last_config 引用路径不存在: {t.get('table_id', '?')}.file = {f}")
        for s in last_config.get("steps", []) or []:
            if not isinstance(s, dict):
                continue
            params = s.get("params")
            if not isinstance(params, dict):
                continue
            for key in ("output_path",):
                value = params.get(key)
                if isinstance(value, str) and value and not Path(value).exists():
                    logger.debug(
                        f"[app] last_config 引用路径不存在: "
                        f"{s.get('step_id', '?')}.{key} = {value}"
                    )

    ok = all(item.ok for item in items)
    elapsed_ms = int((time.time() - t0) * 1000)
    return SelfCheckResult(ok=ok, items=items, elapsed_ms=elapsed_ms, last_config=last_config)


def _setup_gui_logging() -> None:
    """GUI 模式日志：写入 logs/gui_YYYY-MM-DD.log（DEBUG 级，滚动保留）。

    B-01：日志目录不可写（程序装在只读目录/受保护目录）时回退到用户可写的
    临时目录（tempfile.gettempdir()/RPA_Workflow_v3_logs）；mkdir 与 logger.add
    两处失败均不抛异常，避免日志初始化阻断启动（只读目录下"静默无反应"）。
    """
    log_dir = ENGINE_ROOT / "logs"
    # 改动点1：mkdir 包 try/except，失败则回退到用户可写的临时目录
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        fallback = Path(tempfile.gettempdir()) / "RPA_Workflow_v3_logs"
        print(f"[gui] 程序所在目录不可写（{log_dir}）：{e}；"
              f"日志改写到 {fallback}", file=sys.stderr)
        log_dir = fallback
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e2:
            print(f"[gui] 临时日志目录亦不可用（{log_dir}）：{e2}；"
                  "已跳过文件日志", file=sys.stderr)
            return
    # 改动点2：logger.add 以「解析后的可用目录」为目标，失败亦不抛
    try:
        logger.add(
            log_dir / "gui_{time:YYYY-MM-DD}.log",
            level="DEBUG",
            rotation="10 MB",
            retention="30 days",
            encoding="utf-8",
        )
    except Exception as e:  # 文件日志初始化失败仅提示，不阻断启动
        print(f"[gui] 日志文件初始化失败：{e}", file=sys.stderr)


def _excepthook(exc_type, exc_value, exc_tb) -> None:
    """全局未预期异常兜底：记录日志并弹框提示。"""
    logger.opt(exception=(exc_type, exc_value, exc_tb)).error("[gui] 未预期异常")
    try:
        from PyQt5.QtWidgets import QMessageBox
        from gui.error_messages import translate_error, log_hint
        QMessageBox.critical(
            None, "程序遇到问题",
            f"{translate_error(f'{exc_type.__name__}: {exc_value}')}\n\n"
            f"详细日志：{log_hint()}")
    except ImportError:
        print(f"[gui] 未预期异常: {exc_value}", file=sys.stderr)


def launch_gui() -> int:
    """
    GUI 启动序列：自检 → 日志 → QApplication（先于失败弹框创建，R7）
    → 自检失败弹框退出 / 成功则构建 MainWindow 并进入事件循环。

    B-01：自检结果先取（先于日志初始化），日志初始化包 try 容错（目录不可
    写时回退临时目录、不抛异常）——避免只读目录下 mkdir 异常先于自检逃逸
    导致"文员双击什么都没发生"；自检项 3 已含"程序所在目录不可写"人话提示。

    Returns:
        int: 进程退出码。
    """
    result = run_self_check()
    # B-01（改动点3）：日志初始化包 try，任何异常都不阻断启动
    try:
        _setup_gui_logging()
    except Exception as e:
        print(f"[gui] 日志初始化异常（已忽略）：{e}", file=sys.stderr)

    # PyQt5 自身缺失的降级：无法弹框，stderr 输出自检明细
    try:
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QApplication, QMessageBox
    except ImportError as e:
        print(f"[gui] PyQt5 不可用，无法启动图形界面: {e}", file=sys.stderr)
        for item in result.items:
            mark = "通过" if item.ok else "失败"
            print(f"  [{mark}] {item.name}: {item.detail}", file=sys.stderr)
        return 1

    # R6/E7（P2-7）：高分屏适配（必须在 QApplication 构造前设置；
    # 字号保留 px——HighDpi 属性下自动缩放，避免 pt 换算引入回归）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    if not result.ok:
        lines = [f"{item.name}: {item.detail}" for item in result.items if not item.ok]
        QMessageBox.critical(None, "启动自检失败", "\n".join(lines))
        return 1

    sys.excepthook = _excepthook

    # 惰性导入（防循环）：MainWindow 模块级反向引用本模块的 SelfCheckResult
    from gui.main_window import MainWindow
    win = MainWindow(result)
    win.show()
    return app.exec_()
