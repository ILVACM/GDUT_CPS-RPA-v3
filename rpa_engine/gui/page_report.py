"""
rpa_engine/gui/page_report.py

结果报告界面：左侧结果说明（总体状态/步骤进度/总耗时/读取与输出文件清单），
底栏 [确定] 返回输入数据选择页（阶段 1，保留本次数据与配置）。（2026-09-18 W-19：右侧 ConsolePanel 已移除）
"""

from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QTextBrowser, QPushButton, QToolButton,
    QVBoxLayout, QHBoxLayout,
)

# status → 用户可见中文文案（未知值一律按"异常终止"）
_STATUS_TEXT = {
    "completed": "正常完成",
    "completed_partial": "部分完成（有步骤被跳过）",   # R6/A2（P3-9）
    "cancelled": "用户主动终止",
    "failed": "异常终止",
}


class ReportPage(QWidget):
    """结果报告界面：结果说明 + 确定返回 + 新一轮操作。

    Signals:
        confirm_clicked:       用户点击 [确定]（返回输入数据选择页，阶段 1）。
        new_round_clicked:     用户点击 [新一轮操作]（返回阶段 1，清空状态）。
        save_config_requested: 用户点击 [保存本次配置]。
    """

    confirm_clicked = pyqtSignal()
    new_round_clicked = pyqtSignal()
    save_config_requested = pyqtSignal()   # [保存本次配置] → 主窗口统一的历史配置保存流程

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        # 结果说明（W-19 后独占页面，日志不再展示于 GUI）
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self._browser = QTextBrowser()
        # R6/B1（P0-2/D9）：技术详情折叠区——文件绝对路径与派生表物理名
        # 映射默认隐藏，主区仅人话摘要
        self._tech_toggle = QToolButton()
        self._tech_toggle.setText("技术详情")
        self._tech_toggle.setCheckable(True)
        self._tech_toggle.setToolTip("展开查看文件路径与数据表技术信息")
        self._tech_browser = QTextBrowser()
        self._tech_browser.setVisible(False)
        self._tech_toggle.toggled.connect(self._tech_browser.setVisible)
        self._confirm_btn = QPushButton("确定")
        self._confirm_btn.clicked.connect(self.confirm_clicked.emit)
        # [保存本次配置]：将本次执行配置保存为历史模板（仅正常完成时启用，由 fill 控制）
        self._save_btn = QPushButton("保存本次配置")
        self._save_btn.setToolTip("将本次执行的配置保存为历史配置模板（仅正常完成时可用）")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self.save_config_requested.emit)
        self._new_round_btn = QPushButton("[新一轮操作]")
        self._new_round_btn.setToolTip("清空状态并返回数据选择页开始新一轮操作")
        self._new_round_btn.clicked.connect(self.new_round_clicked.emit)
        bottom = QHBoxLayout()
        bottom.addWidget(self._new_round_btn)
        bottom.addStretch(1)
        bottom.addWidget(self._save_btn)
        bottom.addWidget(self._confirm_btn)
        left_layout.addWidget(self._browser)
        left_layout.addWidget(self._tech_toggle)
        left_layout.addWidget(self._tech_browser)
        left_layout.addLayout(bottom)

        root.addWidget(left, 1)

    def fill(self, status: str, done: int, total: int,
             input_files: List[str], output_files: List[str], duration: float,
             output_tables: Optional[Dict[str, str]] = None,
             overwrite_ids: Optional[set] = None) -> None:
        """填充结果说明：状态文案、步骤进度、总耗时、读取/输出文件数与逐行绝对路径。

        output_tables（2026-09-21 定稿 M2-T9）：派生表编号→SQLite 物理表名
        映射（执行期回写，消除 H5 不可见部分）；末尾可选参保持旧调用兼容。
        overwrite_ids（R6/A3-P3-10）：覆盖链父步的派生表号集合，命中的
        映射行标注"中间结果（已写回）"，其余标注"输出"。
        """
        # 完成态（含部分完成，R6/A2）允许将本次执行配置保存为历史模板
        self._save_btn.setEnabled(
            status in ("completed", "completed_partial"))
        status_text = _STATUS_TEXT.get(status, "异常终止")
        # 主区（人话摘要，R6/B1-P0-2：绝对路径与物理名不入主区）
        lines: List[str] = []
        lines.append(f"总体状态: {status_text}")
        lines.append(f"步骤进度: {done}/{total}")
        lines.append(f"总耗时: {duration:.2f} 秒")
        lines.append("")
        lines.append(f"读取文件数: {len(input_files)}")
        lines.append("")
        lines.append(f"输出文件数: {len(output_files)}")
        self._browser.setPlainText("\n".join(lines))
        # 技术详情区（折叠，默认隐藏）：路径清单＋派生表物理名映射
        tech: List[str] = []
        tech.append("读取文件:")
        for p in input_files:
            tech.append(f"  {p}")
        tech.append("")
        tech.append("输出文件:")
        for p in output_files:
            tech.append(f"  {p}")
        if output_tables:
            tech.append("")
            tech.append("派生表 → 物理表名:")
            for tid, phys in output_tables.items():
                # R6/A3（P3-10）：覆盖链中间表标注，消除"多出一张表"误读
                tag = ("（中间结果，已写回）"
                       if (overwrite_ids and tid in overwrite_ids)
                       else "（输出）")
                tech.append(f"  {tid} → {phys} {tag}")
        self._tech_browser.setPlainText("\n".join(tech))
