"""
rpa_engine/gui/worker.py

GUI 后台执行线程（v3.1 定稿）。

职责边界（根治首轮断链 #2/#4）：
- 本文件仅做线程包装与信号转发，不自写执行循环
- 执行唯一入口 engine.executor.execute_workflow（共享 conn 由主窗口
  经 SessionDB 注入，D8）
"""

import time
from typing import Optional

from PyQt5.QtCore import QThread, QObject, pyqtSignal
from loguru import logger

from engine.executor import ExecutionError, execute_workflow
from engine.parser import ParserError
from engine.validator import ValidationError


class EngineWorker(QThread):
    """引擎执行工作线程：步骤间检查点响应终止请求。"""

    step_started = pyqtSignal(str, str)         # step_id, step_name
    step_completed = pyqtSignal(str, float)      # step_id, 耗时秒
    step_failed = pyqtSignal(str, str)           # step_id, 错误信息
    # R6/A2（P3-9 诚实报告）：第 4 参 success＝executor 全步成功判定
    workflow_finished = pyqtSignal(str, float, dict, bool)   # status, 总耗时秒, output_tables, success

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._cancel_event = None
        self._workflow = None      # WorkflowDef（由主窗口解析校验后传入）
        self._sdb = None           # SessionDB（线程亲和：run 内自建连接）

    def prepare(self, workflow, sdb) -> None:
        """启动前准备：注入已解析的工作流与会话数据库。

        Args:
            workflow: WorkflowDef（已通过 validate_workflow）。
            sdb: SessionDB 对象。连接由 run() 在本线程内经
                sdb.new_connection() 创建（SQLite 线程亲和限制，
                禁止跨线程传递连接对象）。
        """
        self._workflow = workflow
        self._sdb = sdb
        self._cancel_event = self._cancel_event or _CancelFlag()
        self._cancel_event.clear()

    def request_cancel(self) -> None:
        """请求终止（下一个步骤检查点生效）。"""
        if self._cancel_event:
            self._cancel_event.set()

    @property
    def is_cancelled(self) -> bool:
        return bool(self._cancel_event and self._cancel_event.is_set())

    def run(self) -> None:
        """执行：唯一入口 execute_workflow；连接在本线程内创建（线程亲和）。"""
        t_start = time.time()
        status = "failed"
        success = False
        conn = None
        out_tables: dict = {}

        try:
            if self._workflow is None or self._sdb is None:
                raise RuntimeError("worker 未 prepare（缺少工作流或会话数据库）")

            # 线程亲和：在 worker 线程内创建专属连接（SQLite 禁止跨线程
            # 使用连接对象；WAL 支持与主线程连接并存）
            conn = self._sdb.new_connection()

            # 步骤开始时间记录（进度回调驱动信号）
            step_times: dict = {}
            step_names = {s.step_id: s.name for s in self._workflow.steps}

            def progress(step_id: str, state: str, message: str = "") -> None:
                if state == "running":
                    step_times[step_id] = time.time()
                    self.step_started.emit(step_id, step_names.get(step_id, step_id))
                elif state == "completed":
                    elapsed = time.time() - step_times.pop(step_id, time.time())
                    self.step_completed.emit(step_id, elapsed)
                elif state == "failed":
                    step_times.pop(step_id, None)
                    self.step_failed.emit(step_id, message or "步骤执行失败")

            result = execute_workflow(
                self._workflow,
                conn,
                progress_callback=progress,
                cancel_check=(lambda: self.is_cancelled) if self._cancel_event else None,
            )
            status = result["status"]
            success = bool(result.get("success", False))
            out_tables = dict(result.get("output_tables", {}) or {})

        except (ParserError, ValidationError) as e:
            logger.error(f"[worker] 工作流加载失败: {e}")
            status = "failed"
        except ExecutionError as e:
            logger.error(f"[worker] 工作流执行失败: {e}")
            status = "failed"
        except Exception:
            logger.exception("[worker] 执行过程发生未预期异常")
            status = "failed"
        finally:
            if conn is not None:
                try:
                    conn.commit()
                except Exception:
                    pass
                conn.close()
                logger.info("[worker] worker 线程连接已关闭")
            # 日志出口：仅 loguru 文件日志（app.py _setup_gui_logging），
            # 不再向 GUI 转发——ConsolePanel 已移除（W-19，2026-09-18）
            self.workflow_finished.emit(status, time.time() - t_start,
                                        out_tables, success)


class _CancelFlag:
    """线程安全的取消标志（避免 QThread 外部访问 event 限制）。"""

    def __init__(self) -> None:
        import threading
        self._event = threading.Event()

    def set(self) -> None:
        self._event.set()

    def clear(self) -> None:
        self._event.clear()

    def is_set(self) -> bool:
        return self._event.is_set()
