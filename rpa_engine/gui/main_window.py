"""
rpa_engine/gui/main_window.py

GUI 主窗口（v3.1 定稿）：无边框 + 自绘标题栏，QStackedWidget 四页切换，
worker 信号路由，SessionDB 会话生命周期管理。

页面索引：
    0 — InputSelectionPage（阶段 1：输入数据选择）
    1 — OperationConfigPage（阶段 2：操作配置）
    2 — ProgressPage（阶段 3：运行追踪）
    3 — ReportPage（阶段 4：结果报告）

核心状态：
- SessionDB：阶段 1 确认导入时创建 → 阶段 2/3 共享 → 新一轮/关闭时清理
- _staged_config：阶段 2 回退阶段 1 时的配置暂存（需求 7）
"""

import json
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
import psutil
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QLabel,
    QPushButton, QMessageBox, QApplication, QInputDialog,
    QProgressDialog,
)

from gui.app import SelfCheckResult
from gui.error_messages import log_hint, translate_error
from gui.models import WorkflowModel, collect_file_stats
from gui.page_input_selection import InputSelectionPage
from gui.page_operation_config import OperationConfigPage
from gui.page_progress import ProgressPage
from gui.page_report import ReportPage
from gui.styles import build_qss, TITLE_BAR_HEIGHT
from gui.user_template_manager import UserTemplateManager
from gui.worker import EngineWorker

from engine.parser import ParserError, parse_workflow
from engine.validator import ValidationError, validate_workflow
from ops import SessionDB
from ops.excel_preprocessor import scan_sheets
from ops.table_importer import import_excel_table, take_last_normalize_result
from ops.excel_normalizer import (
    write_failed_list, write_meta_table, write_normalize_report,
)
from ops.sql_safety import get_table_columns
from paths import get_engine_root

ENGINE_ROOT = get_engine_root()

# R11/A-09：导入期提示阈值（不改线程模型，仅做提示与内存可观测）
LARGE_TABLE_ROWS = 200_000   # 单表行数超此值 → 进度对话框预告"界面可能暂无响应"
MEM_WARN_MB = 2048           # 导入后进程 RSS 超此值（MB）→ 记警告并在对话框提示


def _import_progress_label(table_id: str, alias: str, rows: int) -> str:
    """R11/A-09：导入进度对话框的逐表文案（大表给出"可能无响应"的预告）。"""
    text = f"正在导入 {table_id}（{alias}）…"
    if rows > LARGE_TABLE_ROWS:
        text += "\n该表较大，导入期间界面可能暂无响应，请耐心等待"
    return text


def _is_stale_session(p: Path) -> bool:
    """R11/B-02（P0 数据损失）：判定会话库文件是否为"孤儿"（无对应存活进程）。

    会话库命名格式（见 _on_confirm_import）：``session_<ts>_<pid>.db``
    （含 ``.db-wal`` / ``.db-shm`` 伴生文件）。从文件名尾部数字段解析
    PID，该 PID 仍有存活进程（``psutil.pid_exists``）→ 判为在用实例，
    返回 False（不删）；否则判为孤儿，返回 True（可删）。无法解析出
    数字 PID 的异常/旧格式文件名 → 保守返回 False 并记 warning，宁可
    留下孤儿库也绝不误删在用库（优于误删，见 B-02「6. 风险与回滚」）。
    """
    name = p.name
    for suf in (".db-wal", ".db-shm", ".db"):
        if name.endswith(suf):
            name = name[: -len(suf)]
            break
    tail = name.rsplit("_", 1)[-1]
    if not tail.isdigit():
        logger.warning(f"[main] 会话库名无法解析 PID，保守不删: {p.name}")
        return False
    return not psutil.pid_exists(int(tail))


class TitleBar(QWidget):
    """自绘标题栏：标题文本 + 右侧三按钮（— / ▢❐ / ✕）+ 拖动 + 双击切换最大化。"""

    close_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("title_bar")
        # 普通 QWidget 必须设置 WA_StyledBackground 才会绘制 QSS 背景色
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._drag_pos: Optional[QPoint] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("RPA 数据处理工具")
        layout.addWidget(title)
        layout.addStretch(1)

        # R6/C1（P0-3）：关于按钮——版本与源码指纹（交付包自证身份）
        self._btn_about = QPushButton("关于")
        self._btn_about.setObjectName("btn_about")
        self._btn_about.setToolTip("查看版本与构建信息")
        self._btn_about.clicked.connect(self._show_about)

        self._btn_min = QPushButton("—")
        self._btn_min.setObjectName("btn_min")
        self._btn_max = QPushButton("▢")
        self._btn_max.setObjectName("btn_max")
        self._btn_close = QPushButton("✕")
        self._btn_close.setObjectName("btn_close")

        self._btn_min.clicked.connect(lambda: self.window().showMinimized())
        self._btn_max.clicked.connect(self._toggle_max)
        self._btn_close.clicked.connect(self.close_requested.emit)

        for btn in (self._btn_about, self._btn_min, self._btn_max,
                    self._btn_close):
            btn.setFixedHeight(TITLE_BAR_HEIGHT)
            layout.addWidget(btn)

    def _show_about(self) -> None:
        """R6/C1（P0-3）：frozen 读同目录 BUILD_INFO 指纹段；源码态显示开发版。"""
        import sys as _sys
        lines = ["RPA 数据处理工具", ""]
        if getattr(_sys, "frozen", False):
            info = Path(_sys.executable).parent / "BUILD_INFO.txt"
            if info.exists():
                txt = info.read_text(encoding="utf-8", errors="replace")
                keys = ("BUILD_TIME", "SOURCE_HASH", "GIT_REV",
                        "PYTHON", "PYINSTALLER", "TESTS_SKIPPED")
                keep = [ln.strip() for ln in txt.splitlines()
                        if any(k in ln for k in keys)]
                lines.extend(keep or ["构建信息不可用"])
            else:
                lines.append("构建信息文件缺失（BUILD_INFO.txt）")
        else:
            lines.append("开发版（源码运行，无构建指纹）")
        QMessageBox.information(self, "关于", "\n".join(lines))

    def _toggle_max(self) -> None:
        win = self.window()
        if win.isMaximized():
            win.showNormal()
            self._btn_max.setText("▢")
        else:
            win.showMaximized()
            self._btn_max.setText("❐")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and not self.window().isMaximized():
            self.window().move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self._toggle_max()


class MainWindow(QWidget):
    """主窗口：标题栏 + 四页栈；SessionDB/worker 生命周期与跨页信号路由。"""

    def __init__(self, selfcheck: SelfCheckResult) -> None:
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.resize(1280, 800)
        self.setWindowTitle("RPA 数据处理工具")
        self.setStyleSheet(build_qss())

        # ---- 核心状态 ----
        self.model = WorkflowModel()
        self.tpl_manager = UserTemplateManager()
        self._last_run_config: Optional[Dict[str, Any]] = None
        self.worker = EngineWorker()
        # R6/D2-1（P1-5）：陈旧执行回调忽略标志（换轮未收尾时置位）
        self._ignore_next_finish = False
        # R6/E3（P2-6）：keep_db 两端接线之 GUI 端标志——外部 JSON
        # global.keep_db 经 start_workflow 解析后读取；默认删会话库
        self._keep_session_db = False
        # R6/E7（P2-7）：最小尺寸（小屏办公机底栏不再被裁）
        self.setMinimumSize(1100, 700)
        # R6/F6（P3-13）：双开互覆防护——实例标识（启动时间戳）＋启动时刻；
        # start_workflow 写 gui_workflow.json 前做写前读校验
        _now = datetime.now()
        self._instance_id = _now.strftime("%Y%m%d%H%M%S%f")
        self._instance_started = _now.timestamp()
        # R6/E10（P3-8）：last_config 防抖即时写（2s；崩溃保现场；
        # 退出时直写保留）
        self._lc_timer = QTimer(self)
        self._lc_timer.setSingleShot(True)
        self._lc_timer.setInterval(2000)
        self._lc_timer.timeout.connect(self._save_last_config)
        self.stats: Dict[str, List[str]] = {}
        # 执行期步骤总数（含覆盖模式合成 cp 步；2026-09-21 修复轮 F2）
        self._exec_total: int = 0
        self.done_count: int = 0
        self._last_error_message: str = ""   # 最近一次步骤失败原因（worker 透传）

        # v3.1 会话状态
        self._sdb: Optional[SessionDB] = None          # 本轮会话数据库
        self._table_entries: List[Dict[str, Any]] = []  # 本轮数据表注册表
        self._staged_config: Optional[Dict[str, Any]] = None  # 回退暂存（需求 7）
        self._staged_table_count: int = 0

        # ---- 布局 ----
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = TitleBar()
        self.title_bar.setFixedHeight(TITLE_BAR_HEIGHT)

        self.stack = QStackedWidget()
        self.input_selection_page = InputSelectionPage()
        self.operation_config_page = OperationConfigPage(self.model, self.tpl_manager)
        # R6/E10（P3-8）：模型变更（画布刷新汇聚点）→ last_config 防抖写
        self.operation_config_page.on_model_changed = self._lc_timer.start
        self.progress_page = ProgressPage()
        self.report_page = ReportPage()
        self.stack.addWidget(self.input_selection_page)
        self.stack.addWidget(self.operation_config_page)
        self.stack.addWidget(self.progress_page)
        self.stack.addWidget(self.report_page)

        root.addWidget(self.title_bar)
        root.addWidget(self.stack, 1)

        # ---- 信号连接（一次性完成） ----
        # 阶段 1 → 阶段 2（确认导入）
        self.input_selection_page.confirm_import.connect(self._on_confirm_import)
        # 阶段 2 → 阶段 1（回退，暂存配置）
        self.operation_config_page.go_back_to_input.connect(self._back_to_input_selection)
        # 阶段 2 → 阶段 3
        self.operation_config_page.start_workflow.connect(self.start_workflow)
        self.operation_config_page.exit_clicked.connect(self.exit_app)
        self.operation_config_page.save_config_requested.connect(self._on_save_current_config)
        # 阶段 3
        self.progress_page.abort_clicked.connect(self.abort_workflow)
        self.progress_page.discard_clicked.connect(self._discard_to_input)
        # 阶段 4 → 阶段 1（闭环）
        self.report_page.confirm_clicked.connect(self._back_to_input_selection)
        self.report_page.new_round_clicked.connect(self._new_round)
        self.report_page.save_config_requested.connect(self._on_save_run_config)
        # 标题栏
        self.title_bar.close_requested.connect(self.close)
        # Worker 信号
        self.worker.workflow_finished.connect(self._on_workflow_finished)
        self.worker.step_started.connect(self._on_step_started)
        self.worker.step_completed.connect(self._on_step_completed)
        self.worker.step_failed.connect(self._on_step_failed)

        # 启动恢复上次配置（静默，失败仅 DEBUG）
        # R11/A-11：先恢复、后清理——清理须读 last_config 的引用保护集，
        # 顺序颠倒会让"被引用的副本"在恢复之前就被删掉
        self._restore_last_config()
        self._cleanup_stale_sessions()   # R6/D2-3：启动清理孤儿会话库/超龄副本

    # ==================== 阶段 1 → 阶段 2：确认导入 ====================

    def _on_confirm_import(self, entries: List[Dict[str, Any]]) -> None:
        """阶段 1 确认：编号分配 → SessionDB 导入 → 传注册表 → 切阶段 2。

        Args:
            entries: [{file_path(临时区xlsx), sheet_name, alias, header_row(1-based)}]
        """
        # 防御：上一轮 worker 仍在运行（放弃后立即重新确认的边缘场景）
        # 则请求取消并等待，避免旧 worker 持有旧库文件句柄与清理竞态
        if self.worker.isRunning():
            self.worker.request_cancel()
            if not self.worker.wait(3000):
                # R6/D2-1（P1-5）：旧任务未及时收尾——忽略其回调，防劫持导航
                logger.warning("[main] 旧任务未在 3 秒内结束，忽略其执行回调")
                self._ignore_next_finish = True

        # 关闭旧会话（新一轮确认）；R11/A-01：保留副本供本轮导入使用
        self._close_session(clear_copies=False)

        # R11/B-02（P0）：会话库命名带 PID——供启动清理区分"在用/孤儿"实例，
        # 双开时另一实例不会误删本实例正在使用的会话库。
        session_id = f"{datetime.now():%Y%m%d_%H%M%S}_{os.getpid()}"
        try:
            self._sdb = SessionDB(f"session_{session_id}")
        except (OSError, ValueError) as e:
            QMessageBox.critical(self, "错误", f"会话数据库创建失败: {e}")
            return

        # R6/D3-3（P1-7）：磁盘空间预检（源大小×3 安全系数：SQLite 副本
        # ＋WAL＋转换中间态）；不足则人话提示并中止导入
        try:
            required = sum(
                Path(e["file_path"]).stat().st_size
                for e in entries if Path(e["file_path"]).exists()) * 3
            free = shutil.disk_usage(str(ENGINE_ROOT)).free
            if required and free < required:
                QMessageBox.warning(
                    self, "磁盘空间不足",
                    f"本次导入约需 {required // 1048576}MB 空间，"
                    f"当前仅剩 {free // 1048576}MB。\n"
                    "请清理磁盘后重试。")
                self._close_session()
                return
        except OSError as e:
            logger.warning(f"[main] 磁盘预检失败（跳过预检继续）: {e}")

        # 进度对话框（模态，逐表导入）
        progress = QProgressDialog("正在导入数据表…", None, 0, len(entries), self)
        progress.setWindowTitle("导入数据")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        # R11/A-09：保持不可取消（现状），仅以文案预告可能的无响应（见下方逐表文案）
        progress.setCancelButton(None)

        # R11/REQ-H9：报告目录（会话时间戳）——逐表规范化报告与失败清单共用
        report_dir = ENGINE_ROOT / "workspace" / "normalize_report" / session_id

        registry: List[Dict[str, Any]] = []
        failed: List[Dict[str, str]] = []
        conn = self._sdb.conn

        for i, e in enumerate(entries):
            table_id = f"T{i + 1}"
            sqlite_table = f"t{i + 1}"
            progress.setValue(i)
            # R11/A-09：导入前预扫行数——大表在进度对话框中给出"界面可能暂无响应"
            # 预告；扫描结果复用给 import_excel_table（省去其内部重复开簿）。
            sheet_info = None
            rows = 0
            try:
                sheet_info = scan_sheets(str(e["file_path"]))
                rows = next((m["rows"] for m in sheet_info
                             if m["sheet_name"] == e["sheet_name"]), 0)
            except Exception as scan_err:  # noqa: BLE001 预扫失败不影响导入
                logger.debug(f"[main_window] 行数预扫失败（跳过预告）: {scan_err}")
            progress.setLabelText(_import_progress_label(table_id, e["alias"], rows))
            QApplication.processEvents()
            try:
                # R11/A-01[ADJUSTED-1]：改用原始文件导入（副本路径在确认导入
                # 前可能已被清理）；同时把其父目录登记进导入白名单，否则
                # 阶段 3 兜底补导会被 engine.executor._validate_import_path 拒绝。
                src = e.get("source_path") or e["file_path"]
                try:
                    from engine.executor import register_import_root
                    register_import_root(Path(src).parent)
                except Exception as reg_err:  # noqa: BLE001 登记失败不阻断导入
                    logger.debug(f"[main_window] 导入白名单登记失败（忽略）: {reg_err}")
                import_excel_table(
                    conn, src, e["sheet_name"],
                    int(e["header_row"]), sqlite_table,
                    sheet_info=sheet_info,
                )
                # R11/P6/REQ-H9：把本次导入的规范化结果落盘（报告 ＋ 元数据表）。
                # import_excel_table 签名不可改 → 经 table_importer 桥接槽取回结果。
                norm = take_last_normalize_result()
                if norm is not None:
                    try:
                        write_normalize_report(
                            norm, str(report_dir), table_id, e["alias"])
                        write_meta_table(conn, norm, sqlite_table, table_id)
                    except Exception as rep_err:  # noqa: BLE001 落盘失败不阻断导入
                        logger.warning(
                            f"[main_window] 规范化报告落盘失败（忽略）: {rep_err}")
                    finally:
                        # R11/A-09/REQ-H9：落盘后释放大对象（DataFrame），
                        # 避免其跨表存活而抬升内存峰值（内存红线 §2.1 条 5）
                        norm.dataframe = None
                # 导入瞬间查询真实列名（配置期列名校验数据源，缺口 A）
                try:
                    columns = get_table_columns(conn, sqlite_table)
                except Exception as col_err:   # noqa: BLE001 元信息查询失败不阻断导入
                    logger.debug(f"[main_window] 列名查询失败 {table_id}: {col_err}")
                    columns = []
                # R18：统计期间探测（supervision_report GUI 提示用，§3A.3）
                try:
                    from ops.supervision_report import probe_period
                    _probe = probe_period(conn, sqlite_table)
                except Exception as probe_err:  # noqa: BLE001
                    logger.debug(f"[main_window] 期间探测失败（忽略）: {probe_err}")
                    _probe = {}
                registry.append({
                    "table_id": table_id,
                    "alias": e["alias"],
                    "sqlite_table": sqlite_table,
                    "file_path": e["file_path"],
                    # R11/A-10：贯通原始文件路径（副本路径跨会话必变）
                    "source_path": e.get("source_path") or e["file_path"],
                    "sheet_name": e["sheet_name"],
                    "header_row": int(e["header_row"]),
                    "columns": columns,
                    "date_range": {"min": _probe.get("date_min"),
                                   "max": _probe.get("date_max")},
                    "workday_default": _probe.get("workday_default"),
                })
            except (ValueError, FileNotFoundError, PermissionError,
                    OSError, sqlite3.Error) as err:
                # R6/B2（P1-8）：占用/磁盘/损坏库等高发错误全捕获；
                # 原始异常进日志，用户面经翻译层给人话（可自救）
                logger.error(f"[main_window] 导入失败 {e['alias']}: "
                             f"{type(err).__name__}: {err}")
                # R11/A-13：把异常类名一并送进翻译层——_RULES 的匹配键是
                # 类名小写，原先只传 str(err)（不含类名）导致规则永不命中
                # R11/REQ-H9：失败清单改为结构化条目（供落盘产物 4），可读原因
                # 仍走翻译层（用户面人话）
                alias = e["alias"]
                raw = f"{type(err).__name__}: {err}"
                failed.append({
                    "alias": alias,
                    "sheet": e["sheet_name"],
                    "file": str(e.get("source_path") or e["file_path"]),
                    "reason": translate_error(raw),
                    "stage": "导入数据表",
                })

            # R11/A-09：每表导入后刷新进度 ＋ 内存警戒（psutil；不改线程模型）
            mem_mb = psutil.Process().memory_info().rss / 1024 / 1024
            if mem_mb > MEM_WARN_MB:
                logger.warning(
                    f"[main_window] 导入内存占用较高: {mem_mb:.0f}MB "
                    f"（阈值 {MEM_WARN_MB}MB）"
                )
                progress.setLabelText(
                    f"已处理 {table_id}（{e['alias']}）；"
                    f"内存占用较高（{mem_mb:.0f}MB），继续导入中…"
                )
                QApplication.processEvents()

        progress.setValue(len(entries))

        # R6/E9（P3-7）：编号重排检测——旧编号的来源 sheet 变化或编号消失
        # 时，列出引用受影响的步骤提醒用户检查（temp 副本路径跨会话必变，
        # 身份比对采用 sheet_name＋编号集合口径；首导入无旧注册表跳过）
        # R11/A-19：身份三元组（文件名＋源路径＋sheet 名）——原口径只比
        # sheet_name，同名 sheet 换文件时不会提醒（步骤静默指向错误数据表）
        def _ident(e):
            src = str(e.get("source_path") or e.get("file_path") or "")
            return (Path(src).name, src, e.get("sheet_name", ""))

        old_map = {e["table_id"]: _ident(e) for e in self._table_entries}
        if old_map and self.model.steps:
            new_map = {e["table_id"]: _ident(e) for e in registry}
            disturbed = {tid for tid, ident in old_map.items()
                         if tid not in new_map or new_map.get(tid) != ident}
            if disturbed:
                affected = [
                    f"第 {i} 步「{s.name}」"
                    for i, s in enumerate(self.model.steps, 1)
                    if {s.target_table_id, s.output_table_id} & disturbed
                ]
                if affected:
                    QMessageBox.information(
                        self, "数据表引用已变化",
                        "数据表编号已重新分配，以下步骤引用的表发生变化"
                        "（本次所选文件的来源路径或工作表与上次不同），"
                        "请检查其参数：\n" + "\n".join(affected))

        self._table_entries = registry

        if failed:
            # R11/REQ-H9：失败清单双通道——弹窗（内存可见）+ 落盘（可追溯产物 4）
            display = [f"{it['alias']}: {it['reason']}" for it in failed]
            try:
                write_failed_list(failed, str(report_dir))
            except Exception as fe:  # noqa: BLE001 落盘失败不阻断导入
                logger.warning(f"[main_window] 失败清单落盘失败（忽略）: {fe}")
            QMessageBox.warning(
                self, "部分导入失败",
                "以下数据表导入失败：\n" + "\n".join(display)
            )
        if not registry:
            QMessageBox.critical(self, "错误", "全部数据表导入失败，无法继续")
            self._close_session()
            return

        # 模型接收注册表（保留已恢复步骤，2026-09-21 审计 P2 修复：
        # apply_registry 仅刷新表+reconcile，不清 steps——启动恢复的
        # last_config 步骤在确认导入后仍生效）
        self.model.apply_registry(registry)
        self.operation_config_page.set_input_tables(registry)
        self._lc_timer.start()   # R6/E10：确认导入后防抖保存现场

        # 暂存恢复（需求 7）：补选后回到阶段 2 不需重新配置
        if (self._staged_config is not None
                and len(registry) >= self._staged_table_count
                and self._staged_config.get("steps")):
            box = QMessageBox(self)
            box.setWindowTitle("恢复配置")
            box.setText(
                f"检测到回退前已配置 {len(self._staged_config['steps'])} 个步骤，\n"
                f"是否恢复之前的配置？"
            )
            box.setIcon(QMessageBox.Question)
            btn_ok = box.addButton("恢复", QMessageBox.AcceptRole)
            box.addButton("重新配置", QMessageBox.RejectRole)
            box.exec_()
            if box.clickedButton() is btn_ok:
                staged_steps = self._staged_config.get("steps", [])
                # 仅恢复步骤（表引用按当前注册表顺序 T1..Tn 对应；
                # 引用不存在编号→dangling 画布可视化，执行前 validator 拦截）
                self.model.load_session(registry, {
                    "name": self._staged_config.get("name", "GUI 操作"),
                    "steps": staged_steps,
                })
                self.operation_config_page.restore_config(
                    self.model.to_dict(include_deprecated=True), registry
                )
            self._staged_config = None

        self.stack.setCurrentWidget(self.operation_config_page)

    @staticmethod
    def _table_num(table_id: str) -> int:
        try:
            return int(table_id[1:])
        except (ValueError, IndexError):
            return 0

    # ==================== 页面导航（阶段切换） ====================

    def _back_to_input_selection(self) -> None:
        """阶段 2 → 阶段 1：暂存配置后返回（需求 7）。"""
        # R6/D2-2（P1-5）：换轮旧任务防御（与 _on_confirm_import 同口径）
        if self.worker.isRunning():
            self.worker.request_cancel()
            if not self.worker.wait(3000):
                logger.warning("[main] 旧任务未在 3 秒内结束，忽略其执行回调")
                self._ignore_next_finish = True
        if self.model.steps:
            # 编辑态往返暂存：未过滤导出，避免弃用闭包过滤后步骤丢失
            self._staged_config = self.model.to_dict(include_deprecated=True)
            self._staged_table_count = len(self._table_entries)
        self.progress_page.reset_states()
        self.stack.setCurrentWidget(self.input_selection_page)

    def _discard_to_input(self) -> None:
        """阶段 3 放弃执行：中止 worker，返回阶段 1。"""
        if self.worker.isRunning():
            self.worker.request_cancel()
            if not self.worker.wait(1000):
                # R6/D2-1（P1-5）：wait 返回值消费（原为忽略）
                logger.warning("[main] 旧任务未在 1 秒内结束，忽略其执行回调")
                self._ignore_next_finish = True
        self.progress_page.reset_states()
        self.stack.setCurrentWidget(self.input_selection_page)

    def _new_round(self) -> None:
        """阶段 4 → 阶段 1：新一轮操作（清空会话与暂存）。

        注意：model 必须原地 reset 而非替换对象——操作配置页持有同一
        引用，替换会导致页面写入旧模型而保存/执行读取新模型（脱钩）。
        """
        # R6/D2-2（P1-5）：换轮旧任务防御（与 _on_confirm_import 同口径）
        if self.worker.isRunning():
            self.worker.request_cancel()
            if not self.worker.wait(3000):
                logger.warning("[main] 旧任务未在 3 秒内结束，忽略其执行回调")
                self._ignore_next_finish = True
        self._staged_config = None
        self._close_session()
        self.model.reset()
        # 清画布残留（P9d：裸 refresh 不清 _table_entries，set_input_tables
        # 一次清注册表+选中态+面板并重绘空态）
        self.operation_config_page.set_input_tables([])
        self.operation_config_page.reset_undo_stack()   # F3：跨轮清空撤销栈
        self.progress_page.reset_states()
        self.stack.setCurrentWidget(self.input_selection_page)

    def _close_session(self, clear_copies: bool = True) -> None:
        """关闭并清理会话数据库＋（可选）本会话导入副本（R6/D3-2）。

        Args:
            clear_copies: 是否清理临时区副本。**确认导入前必须传 False**
                （R11/A-01：副本先删后导入会让本轮导入 100% 失败）；
                退出／换轮／中止等收尾路径保持默认 True。
        """
        # R6/D3-2（P1-7）：会话收尾清理本轮 temp 副本（用完即清）
        if clear_copies:
            try:
                self.input_selection_page.clear_temp_copies()
            except Exception as e:  # noqa: BLE001 清理失败不阻断收尾
                logger.debug(f"[main] 临时副本清理异常（忽略）: {e}")
        if self._sdb is not None:
            try:
                # R6/E3（P2-6）：keep_db 真接线——外部 JSON global.keep_db
                # 为真时保留会话库供排查（默认仍删）
                self._sdb.close(keep_db=self._keep_session_db)
                if self._keep_session_db:
                    logger.info("[main] keep_db=True：会话库已保留（见 workspace/）")
            except Exception as e:
                logger.warning(f"[main_window] 会话关闭异常: {e}")
            self._sdb = None
        self._keep_session_db = False

    # ==================== 执行控制 ====================

    def start_workflow(self) -> None:
        """开始执行：JSON 落盘 → parse/validate → worker 统一执行。"""
        if not self.model.steps:
            QMessageBox.warning(self, "提示", "流程为空，请先添加操作步骤")
            return
        if self._sdb is None:
            QMessageBox.critical(self, "错误", "会话数据库未初始化，请重新确认导入")
            return

        json_path = ENGINE_ROOT / "workspace" / "gui_workflow.json"
        # R6/F6（P3-13）：双开互覆防护——写前读校验：文件存在且 mtime 晚于
        # 本实例启动时间且内容 instance_id≠本实例 → 放弃写＋warning
        if json_path.exists():
            try:
                if json_path.stat().st_mtime > self._instance_started:
                    raw = json.loads(json_path.read_text(encoding="utf-8"))
                    other_id = str((raw.get("__meta") or {}).get("instance_id", ""))
                    if other_id and other_id != self._instance_id:
                        logger.warning(
                            f"[main] gui_workflow.json 已被其他实例写入"
                            f"（instance_id={other_id}），放弃写入以防互覆")
                        QMessageBox.warning(
                            self, "提示",
                            "检测到另一个程序窗口正在使用运行配置文件。\n"
                            "为避免两个窗口互相覆盖，本次启动已取消。\n"
                            "请关闭另一个窗口后重试。")
                        return
            except (OSError, ValueError) as e:
                logger.debug(f"[main] 写前读校验失败（忽略，直接写）: {e}")
        try:
            self.model.save_json(json_path,
                                 extra_meta={"instance_id": self._instance_id})
        except OSError as e:
            QMessageBox.critical(self, "错误", f"流程配置保存失败: {e}")
            return

        # 解析 + 校验（与引擎 execute_workflow 同一链路）
        try:
            workflow = parse_workflow(str(json_path))
            validate_workflow(workflow)
        except (ParserError, ValidationError) as e:
            QMessageBox.warning(self, "配置校验失败", str(e))
            return

        # R6/E3（P2-6）：keep_db 两端接线——引擎端由 executor 清理开关消费，
        # GUI 端记录标志供 _close_session 决定是否保留会话库
        self._keep_session_db = bool(workflow.global_config.get("keep_db", False))
        self._last_run_config = self.model.to_dict()
        self.stats = collect_file_stats(self.model, ENGINE_ROOT)
        self.done_count = 0
        # F2：报告页 total 口径＝执行参数文件实际步骤数（含 cp 合成步）
        self._exec_total = len(workflow.steps)

        # 进度页 meta 与 _exec_total 同源（parse 后 workflow.steps，含覆盖
        # 模式合成 cp 行，2026-09-21 审计 P4：消除"4 步完成只有 3 行"）
        meta: List[Tuple[str, str]] = [(s.step_id, s.name) for s in workflow.steps]
        self.progress_page.setup_steps(meta)
        self.progress_page.set_abort_enabled(True)

        # worker 统一入口（连接由 worker 在自己线程内创建——SQLite 线程亲和）
        self.worker.prepare(workflow, self._sdb)
        self._last_error_message = ""
        # F1：save_json 内部 renumber 已把 step_id 改写为 S{n}，重建画布使
        # scene 键与执行期信号对齐（否则运行状态/失败气泡静默失联）
        self.operation_config_page.refresh_graph()
        self.operation_config_page.reset_runtime_status()
        self.stack.setCurrentWidget(self.progress_page)
        self.worker.start()

    def abort_workflow(self) -> None:
        """终止操作：置取消标志（步骤间检查点生效）。"""
        self.worker.request_cancel()
        self.progress_page.set_abort_enabled(False)

    # ==================== worker 信号槽 ====================

    def _on_step_started(self, step_id: str, step_name: str) -> None:
        self.progress_page.mark_running(step_id)
        self.operation_config_page.set_step_runtime_status(step_id, "running")

    def _on_step_completed(self, step_id: str, duration: float) -> None:
        self.progress_page.mark_done(step_id)
        self.operation_config_page.set_step_runtime_status(step_id, "completed")
        self.done_count += 1

    def _on_step_failed(self, step_id: str, message: str) -> None:
        self.progress_page.mark_failed(step_id)
        # R6/B1（P0-2）：气泡经翻译层（人话＋下一步）；原文只进日志
        self.operation_config_page.set_step_runtime_status(
            step_id, "failed", translate_error(message))
        # 记录真实失败原因原文（workflow_finished 弹窗时翻译展示）
        self._last_error_message = message

    def _on_workflow_finished(self, status: str, duration: float,
                              output_tables: Optional[Dict[str, str]] = None,
                              success: bool = True) -> None:
        """执行结束 → 结果报告页 + 派生表物理名回写（定稿 M2-T9）。

        R6/A2（P3-9 诚实报告）：第 4 参 success＝executor 全步成功判定；
        completed 且非 success → 显示口径 completed_partial（"部分完成"）；
        输出文件清单改为执行后按实际产物收集（failed/cancelled 不列"已输出"）。
        R6/A3（P3-10）：组装覆盖链父步表号集，报告页标注"中间结果"。
        """
        # R6/D2-2（P1-5）：陈旧回调丢弃（换轮时旧任务未收尾的防劫持）
        if self._ignore_next_finish:
            self._ignore_next_finish = False
            logger.info("[main] 丢弃陈旧执行回调（用户已进入新一轮）")
            return
        self._output_tables = dict(output_tables or {})
        self.operation_config_page.set_output_tables(self._output_tables)
        if status == "completed":
            self.stats = collect_file_stats(self.model, ENGINE_ROOT)
        else:
            self.stats = {**self.stats, "output_files": []}
        display_status = status
        if status == "completed" and not success:
            display_status = "completed_partial"
        overwrite_ids = {
            s.output_table_id for s in self.model.steps
            if s.params.get("output_mode") == "overwrite_target"
            and s.output_table_id
        }
        self.report_page.fill(
            display_status, self.done_count,
            self._exec_total or len(self.model.steps),
            self.stats.get("input_files", []),
            self.stats.get("output_files", []),
            duration,
            output_tables=self._output_tables,
            overwrite_ids=overwrite_ids,
        )
        self.stack.setCurrentWidget(self.report_page)
        if status == "failed":
            # R6/B1（P0-2）：翻译人话＋日志目录指引
            #（原指引所指面板已随 W-19 移除，属死路，字面全库清零）
            reason = translate_error(self._last_error_message)
            QMessageBox.critical(
                self, "执行失败",
                f"工作流执行失败：{reason}\n\n详细日志目录：{log_hint()}",
            )

    # ==================== 历史配置保存 ====================

    def _on_save_current_config(self) -> None:
        # 模板=配置复用载体须无损（编辑态口径：保 output_mode 不展开 _cp，
        # 2026-09-21 审计 P1 修复）；运行配置留档（_on_save_run_config）
        # 维持业务口径（执行交接单快照）
        self._do_save_template(self.model.to_dict(include_deprecated=True))

    def _on_save_run_config(self) -> None:
        if self._last_run_config is None:
            QMessageBox.warning(self, "提示", "没有可保存的执行配置")
            return
        self._do_save_template(self._last_run_config)

    def _do_save_template(self, config: dict) -> None:
        """历史配置模板统一保存流程。"""
        default_name = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        name, ok = QInputDialog.getText(self, "保存配置", "模板名称:", text=default_name)
        if not ok or not name.strip():
            return
        name = name.strip()
        success, msg = self.tpl_manager.save(name, config)
        if not success and msg == "duplicate":
            box = QMessageBox(self)
            box.setWindowTitle("提示")
            box.setText(f"'{name}' 已存在，是否覆盖？")
            box.setIcon(QMessageBox.Question)
            btn_ok = box.addButton("确定", QMessageBox.AcceptRole)
            btn_cancel = box.addButton("取消", QMessageBox.RejectRole)
            box.setDefaultButton(btn_cancel)
            box.exec_()
            if box.clickedButton() is not btn_ok:
                return
            success, msg = self.tpl_manager.save(name, config, overwrite=True)
        if success:
            # 成功提示含完整路径 + 即时刷新模板列表（修复"保存后看不见"）
            full_path = self.tpl_manager.storage_dir / str(msg)
            QMessageBox.information(
                self, "提示",
                f"已保存: {name}\n位置: {full_path}\n\n"
                f"模板列表已更新；重启程序后也可在阶段 2 模板栏找到。"
            )
            try:
                self.operation_config_page.refresh_templates()
            except Exception as e:
                logger.debug(f"[gui] 模板列表刷新失败: {e}")
        else:
            QMessageBox.warning(self, "提示", msg)

    # ==================== 启动恢复 ====================

    @staticmethod
    def cleanup_stale_files(ws_root, temp_root, cutoff_hours: int = 24) -> int:
        """R6/D2-3（P1-5）＋D3-2（P1-7）：孤儿会话库＋超龄副本清理。

        静态纯函数（可注入路径直测）。R11/B-02（P0 修复）：会话库命名已
        带 PID（见 _on_confirm_import），此处**仅删"无对应存活进程"的
        session_*.db*（含 -wal/-shm）孤儿**——双开时另一实例正在使用的
        会话库（其 PID 存活）不会被误删（原实现为启动时无条件全删，属
        不可逆数据损失）；无法解析 PID 的旧格式文件保守保留。temp_root
        下 mtime 早于 cutoff_hours 小时的文件一并清理。

        Returns:
            int: 删除文件数。
        """
        import time as _time
        removed = 0
        ws_root = Path(ws_root)
        if ws_root.is_dir():
            for p in ws_root.glob("session_*.db*"):
                # R11/B-02（P0）：仅删"无对应存活进程"的孤儿库；双开时另一
                # 实例正在使用的会话库（PID 存活）绝不删（不可逆数据损失）。
                if not _is_stale_session(p):
                    continue
                try:
                    p.unlink()
                    removed += 1
                except OSError as e:
                    logger.warning(
                        f"[main] 陈旧会话库清理失败（跳过）{p.name}: {e}")
        cutoff = _time.time() - cutoff_hours * 3600
        temp_root = Path(temp_root)
        # R11/A-11：引用保护——被 last_config 的 tables[].source.file 引用的副本
        # 即便"超龄"也不删（迁移期旧配置仍指向副本，删了会让恢复失败）。
        # 读取失败一律视为"无引用"，行为与改动前一致。
        protected: set = set()
        try:
            _lc = Path(ws_root) / "last_config.json"
            if _lc.is_file():
                _data = json.loads(_lc.read_text(encoding="utf-8"))
                for _t in (_data.get("tables") or []):
                    _f = str((_t.get("source") or {}).get("file") or "")
                    if _f:
                        protected.add(Path(_f).resolve())
        except (OSError, ValueError) as e:
            logger.debug(f"[main] 超龄清理的引用保护集构建失败（跳过）: {e}")
        if temp_root.is_dir():
            for p in temp_root.iterdir():
                try:
                    if not p.is_file():
                        continue
                    if p.resolve() in protected:
                        continue
                    if p.stat().st_mtime < cutoff:
                        p.unlink()
                        removed += 1
                except OSError:
                    continue
        if removed:
            logger.info(f"[main] 清理孤儿文件 {removed} 个（会话库/超龄副本）")
        return removed

    def _cleanup_stale_sessions(self) -> int:
        """启动清理入口（生产路径封装，详见 cleanup_stale_files）。"""
        return self.cleanup_stale_files(
            ENGINE_ROOT / "workspace",
            ENGINE_ROOT / "temp" / "input_selection")

    def _restore_last_config(self) -> None:
        """启动时静默恢复上次配置（v3.1 重写时丢失的旧能力，本轮补回）。

        恢复内容：model 载入 last_config 的 tables+steps；阶段 1 页面
        回填上次所选数据表（仅 source.file 仍存在的表）。用户在阶段 1
        看到上次的表清单，点[确认并导入]即回到完整配置状态。
        """
        path = ENGINE_ROOT / "workspace" / "last_config.json"
        if not path.is_file():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"[gui] last_config 读取失败（跳过恢复）: {e}")
            return

        if not isinstance(data, dict) or not data.get("steps"):
            return  # 无步骤（首次启动/空配置）不恢复

        # 阶段 1 回填候选（仅文件仍存在的表；缺失表跳过并告警）
        entries: List[Dict[str, Any]] = []
        for t in data.get("tables", []):
            if not isinstance(t, dict):
                continue
            src = t.get("source", {}) or {}
            f = src.get("file", "")
            tid = t.get("table_id", "")
            if f and Path(f).is_file():
                entries.append({
                    "table_id": tid,
                    "file_path": f,
                    "sheet_name": src.get("sheet", ""),
                    "alias": t.get("alias", tid),
                    "header_row": int(src.get("header_row", 1)),
                    "sqlite_table": t.get("sqlite_table", ""),
                })
            else:
                logger.warning(
                    f"[gui] 恢复跳过缺失文件的数据表: {tid}: {f}"
                )

        if not entries:
            # 表全部失效则不恢复（步骤引用的表无法重建）
            logger.warning("[gui] 上次配置的数据文件均已失效，不恢复")
            self.model.reset()
            return

        try:
            self.model.load_session(entries, data)
        except Exception as e:
            logger.debug(f"[gui] last_config 载入失败（跳过恢复）: {e}")
            return

        self.input_selection_page.set_entries(entries)
        logger.info(
            f"[gui] 已恢复上次配置: {len(entries)} 表, "
            f"{len(self.model.steps)} 步（在阶段 1 确认导入后生效）"
        )

    # ==================== 界面切换与退出 ====================

    def exit_app(self) -> None:
        """退出程序。"""
        self._save_last_config()
        QApplication.quit()

    def _save_last_config(self) -> None:
        """静默保存 last_config（失败仅记 DEBUG）。

        编辑态导出（include_deprecated=True）：last_config 用于恢复上次编辑现场，
        须保留被弃用的步骤，否则重启后步骤永久丢失（弃用标记本身不持久）。
        """
        try:
            data: Dict[str, Any] = self.model.to_dict(include_deprecated=True)
            path = ENGINE_ROOT / "workspace" / "last_config.json"
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.debug(f"[gui] last_config 保存失败: {e}")

    def closeEvent(self, event) -> None:
        """窗口关闭清理：worker → SessionDB → last_config。"""
        if self.worker.isRunning():
            self.worker.request_cancel()
            self.worker.wait(3000)
        self._close_session()
        self._save_last_config()
        event.accept()
