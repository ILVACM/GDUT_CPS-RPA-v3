"""
rpa_engine/gui/page_progress.py

操作进度界面：左侧步骤状态列表（白=未执行/浅黄=执行中/浅绿=完成/浅红=失败，文字恒黑），
底栏提供 [终止操作] 按钮。（2026-09-18 W-19：右侧 ConsolePanel 已移除，日志改由 logs/ 文件承载）
"""

from typing import Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QHBoxLayout,
)

from gui.styles import COLOR_PENDING, COLOR_RUNNING, COLOR_DONE, COLOR_FAILED


class ProgressPage(QWidget):
    """操作进度界面：只读步骤状态 + 终止操作 + 放弃执行。

    Signals:
        abort_clicked:     用户点击 [终止操作]。
        discard_clicked:   用户点击 [放弃执行]（返回阶段 1）。
    """

    abort_clicked = pyqtSignal()
    discard_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        # step_id → 行号 映射（setup_steps 重建）
        self._id_to_row: Dict[str, int] = {}

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        # 步骤状态列表 + [终止操作] 底栏（W-19 后独占页面，日志不再展示于 GUI）
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self._list = QListWidget()
        # 只读列表：去掉焦点框，避免选中高亮覆盖状态背景色
        self._list.setFocusPolicy(Qt.NoFocus)
        self._abort_btn = QPushButton("终止操作")
        self._abort_btn.clicked.connect(self.abort_clicked.emit)
        self._discard_btn = QPushButton("放弃执行")
        self._discard_btn.setToolTip("放弃当前执行并返回数据选择页")
        self._discard_btn.clicked.connect(self.discard_clicked.emit)
        bottom = QHBoxLayout()
        bottom.addWidget(self._discard_btn)
        bottom.addStretch(1)
        bottom.addWidget(self._abort_btn)
        left_layout.addWidget(self._list)
        left_layout.addLayout(bottom)

        root.addWidget(left, 1)

    def setup_steps(self, steps_meta: List[Tuple[str, str]]) -> None:
        """重建步骤列表：仅显示步骤名，全部置待执行白，文字恒黑。"""
        self._list.clear()
        self._id_to_row = {}
        for row, (step_id, step_name) in enumerate(steps_meta):
            item = QListWidgetItem(step_name)
            # 只读列表：仅保留 Enabled，去掉可选中标志
            item.setFlags(Qt.ItemIsEnabled)
            item.setBackground(QColor(COLOR_PENDING))
            item.setForeground(QColor(Qt.black))
            self._list.addItem(item)
            self._id_to_row[step_id] = row

    def _set_row_color(self, step_id: str, color: str) -> None:
        """按 step_id 设置行背景色；未知 step_id 静默忽略。"""
        row = self._id_to_row.get(step_id)
        if row is None:
            return
        item = self._list.item(row)
        if item is not None:
            item.setBackground(QColor(color))

    def mark_running(self, step_id: str) -> None:
        """执行中 → 浅黄。"""
        self._set_row_color(step_id, COLOR_RUNNING)

    def mark_done(self, step_id: str) -> None:
        """完成 → 浅绿。"""
        self._set_row_color(step_id, COLOR_DONE)

    def mark_failed(self, step_id: str) -> None:
        """失败 → 浅红（D2 补充态）。"""
        self._set_row_color(step_id, COLOR_FAILED)

    def reset_states(self) -> None:
        """返回配置页前调用：所有行恢复待执行白 + 复位终止按钮。"""
        for row in range(self._list.count()):
            item = self._list.item(row)
            if item is not None:
                item.setBackground(QColor(COLOR_PENDING))
        self.set_abort_enabled(True)

    def set_abort_enabled(self, on: bool) -> None:
        """启用/禁用 [终止操作] 按钮（防重复点击）。"""
        self._abort_btn.setEnabled(on)
