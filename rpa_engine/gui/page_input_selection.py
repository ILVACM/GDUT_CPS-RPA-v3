"""
rpa_engine/gui/page_input_selection.py

v3.1 阶段 1 —— 输入数据选择页（P2 重做版）。

完整链路（对应需求 1/2）：
- [add] → Windows 文件对话框多选 → 复制到临时区 → XLSX 预处理
  → 扫描全部数据表 → 逐行加入表格（默认全选 + 默认别名）
- 每行：复选框（勾选灰底）| 标识名称（可编辑，≤50字）| 来源文件 |
  源数据表 | 表头行（弹窗选择，第 N 行则删前 N-1 行语义）| [del]
- [确认并导入] → 校验（非空/长度/查重）→ emit confirm_import

编号 T1..Tn 分配与 SQLite 导入由主窗口执行（会话跨页面共享）。

Signals:
    confirm_import(list): 确认导入，携带 entries 列表
        [{file_path, sheet_name, alias, header_row(1-based)}]
"""

import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from PyQt5.QtCore import QRect, QSize, Qt, pyqtSignal
from PyQt5.QtGui import (
    QBrush, QColor, QPainter, QStandardItem, QStandardItemModel,
)
from PyQt5.QtWidgets import (
    QCheckBox, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QPushButton, QStyle, QStyledItemDelegate,
    QTableWidget, QTableView, QVBoxLayout, QWidget,
)

from gui import styles
from gui.error_messages import translate_error
from paths import get_engine_root

ENGINE_ROOT = get_engine_root()
TEMP_DIR = ENGINE_ROOT / "temp" / "input_selection"

# Excel 文件过滤器
_EXCEL_FILTER = "Excel 文件 (*.xlsx *.xls);;所有文件 (*.*)"

# 别名最大长度（中文字）
_ALIAS_MAX_LEN = 50

# 表头选择弹窗预览行数（2026-09-21 定稿 Q3：20→50，弹窗内滚动查看）
_PREVIEW_ROWS = 50

# 勾选行背景色（灰色，区别于默认白色）
_CHECKED_BG = "#E0E0E0"
_UNCHECKED_BG = "#FFFFFF"


# ---------------------------------------------------------------------------
# 数据载体
# ---------------------------------------------------------------------------

@dataclass
class InputEntry:
    """单行输入数据源描述。"""

    file_path: Path = field(default_factory=lambda: Path())  # 临时区 xlsx
    sheet_name: str = ""
    alias: str = ""
    header_row: int = 1    # 1-based：表头所在行号（第 N 行 → 删前 N-1 行）
    selected: bool = True
    # 源文件绝对路径（2026-09-21 审计 P7 查重键；临时副本 file_path 每次
    # 不同不可作键——validate_and_copy 同名加 _1 后缀）；不持久化
    source_path: str = ""


# ---------------------------------------------------------------------------
# 表头行选择弹窗（2026-09-21 定稿 D-A：QTableView 真表格 + 摘要解耦）
# ---------------------------------------------------------------------------

class _HeaderBadgeDelegate(QStyledItemDelegate):
    """行号列委托：绘制行号 + 选中行「✓ 表头」徽章（单选保证唯一）。

    选中态经 ``QStyle.State_Selected`` 判定（ SingleSelection+SelectRows 下
    整行高亮由视图承载）；行高下限 28px 保证徽章可读。
    """

    def paint(self, painter: QPainter, option, index) -> None:
        super().paint(painter, option, index)
        if index.column() != 0:
            return
        painter.save()
        r = option.rect
        if option.state & QStyle.State_Selected:
            badge = QRect(r.left() + 32, r.top() + 4,
                          r.width() - 36, r.height() - 8)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(styles.GRAPH_TABLE_FILL)))
            painter.drawRoundedRect(badge, 3, 3)
            painter.setPen(QColor(styles.GRAPH_TEXT_ON_FILL))
            painter.setFont(painter.font())
            painter.drawText(badge, Qt.AlignCenter, "✓ 表头")
        painter.restore()

    def sizeHint(self, option, index) -> QSize:
        hint = super().sizeHint(option, index)
        width = 90 if index.column() == 0 else hint.width()
        return QSize(max(hint.width(), width), max(hint.height(), 28))


class _HeaderRowDialog(QDialog):
    """弹窗显示前 50 行预览（QTableView 真表格），单击某行设为表头。

    命中只认 ``clicked(index).row()``（消除旧 QTextEdit 字符画的块号偏移
    缺陷）；生效列名摘要/重复列名预警/删行提示移至顶部 QLabel 富文本区，
    与点选区解耦。
    """

    def __init__(self, rows: List[List[str]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("选择表头行")
        self.resize(860, 520)
        self._rows: List[List[str]] = [list(r) for r in rows]
        self._filled_cols: List[int] = self._forward_fill_merged(self._rows)
        self._selected_row: int = 0

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("点击某一行设为表头（该行上移为第一行，数据从下一行开始）："))

        self._summary = QLabel()
        self._summary.setTextFormat(Qt.RichText)
        self._summary.setWordWrap(True)
        layout.addWidget(self._summary)

        self._model = QStandardItemModel()
        self._view = QTableView()
        self._view.setModel(self._model)
        self._view.setEditTriggers(QTableView.NoEditTriggers)
        self._view.setSelectionMode(QTableView.SingleSelection)
        self._view.setSelectionBehavior(QTableView.SelectRows)
        self._view.setItemDelegateForColumn(0, _HeaderBadgeDelegate(self._view))
        self._view.verticalHeader().setVisible(False)
        self._view.setHorizontalScrollMode(QTableView.ScrollPerPixel)
        self._view.clicked.connect(self._on_row_clicked)
        self._fill_model()
        # 表头 resize 模式须在模型列存在后设置（0 列时 setSectionResizeMode
        # 越界会触发 access violation）
        hheader = self._view.horizontalHeader()
        hheader.setSectionResizeMode(QHeaderView.ResizeToContents)
        if self._model.columnCount() > 0:
            hheader.setSectionResizeMode(0, QHeaderView.Fixed)
            self._view.setColumnWidth(0, 90)
        layout.addWidget(self._view, 1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self.accept)
        bottom.addWidget(btn_ok)
        layout.addLayout(bottom)

        self._view.selectRow(0)
        self._refresh_summary()

    # ------------------------------------------------------------------ #
    # 数据与渲染
    # ------------------------------------------------------------------ #

    @staticmethod
    def _forward_fill_merged(rows: List[List[str]]) -> List[int]:
        """合并单元格非锚点空值按列前向填充（原地），返回被填充列索引。

        openpyxl read_only 模式取不到 merged_cells 范围，采用空值前向填充
        启发式；填充列在摘要中标注「来自合并单元格」。
        """
        filled: set = set()
        if not rows:
            return []
        n_cols = max(len(r) for r in rows)
        for c in range(n_cols):
            last = ""
            for r in rows:
                val = r[c] if c < len(r) else ""
                if val == "" and last != "":
                    if c < len(r):
                        r[c] = last
                    else:
                        r.append(last)
                    filled.add(c)
                elif val != "":
                    last = val
        return sorted(filled)

    def _fill_model(self) -> None:
        """预览行写入 QStandardItemModel（行号列 + 数据列，全部只读）。"""
        self._model.clear()
        n_cols = max([len(r) for r in self._rows], default=0)
        self._model.setColumnCount(n_cols + 1)
        self._model.setHorizontalHeaderLabels(
            ["行号"] + [f"列{i + 1}" for i in range(n_cols)])
        for idx, row in enumerate(self._rows):
            items = [QStandardItem(str(idx + 1))]
            for c in range(n_cols):
                items.append(QStandardItem(row[c] if c < len(row) else ""))
            for it in items:
                it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self._model.appendRow(items)

    def _refresh_summary(self) -> None:
        """顶部摘要区刷新（富文本：重复预警橙、删行提示灰）。"""
        lines = self._header_summary(self._selected_row)
        parts = []
        for line in lines:
            if line.startswith("⚠"):
                parts.append(f"<span style='color:#e67e22;'>{line}</span>")
            elif line.startswith("提示"):
                parts.append(f"<span style='color:#666666;'>{line}</span>")
            else:
                parts.append(line)
        self._summary.setText("<div>" + "<br/>".join(parts) + "</div>")

    def _header_summary(self, idx: int) -> List[str]:
        """选中表头行的生效效果摘要（列名清单 + 重复列名预警 + 删行提示）。

        重复列名按 pandas mangle 规则模拟自动编号（行1, 行1.1, …），
        让用户在选择前即预见导入后的真实表头。
        """
        if not (0 <= idx < len(self._rows)):
            return []
        raw = [str(c) if c is not None else "" for c in self._rows[idx]]
        cols = [c if c.strip() else f"未命名{p + 1}" for p, c in enumerate(raw)]

        lines = [f"当前选择：第 {idx + 1} 行作为表头"]
        # 模拟 pandas 重复列名自动编号
        seen: Dict[str, int] = {}
        mangled: List[str] = []
        has_dup = False
        for c in cols:
            if c in seen:
                seen[c] += 1
                mangled.append(f"{c}.{seen[c]}")
                has_dup = True
            else:
                seen[c] = 0
                mangled.append(c)
        lines.append(f"生效后列名（共 {len(mangled)} 列）: {'、'.join(mangled)}")
        if self._filled_cols:
            cols_txt = "、".join(f"第 {c + 1} 列" for c in self._filled_cols)
            lines.append(f"⚠ {cols_txt}来自合并单元格，已按上方值填充")
            # R15/B-79：消除「预览＝导入结果」的误解——上方表格是原始形态，
            # 合并单元格填充只在导入时发生
            lines.append("提示：上方预览为原始形态；上述合并单元格填充仅在导入时生效")
        if has_dup:
            lines.append("⚠ 检测到重复列名，导入时将自动编号（如上），"
                         "后续引用请使用编号后的名称")
        if idx > 0:
            deleted = "第 1 行" if idx == 1 else f"第 1 至 {idx} 行"
            lines.append(f"提示：{deleted}将被删除，"
                         f"第 {idx + 1} 行上移为第一行（表头）")
        return lines

    # ------------------------------------------------------------------ #
    # 交互
    # ------------------------------------------------------------------ #

    def _on_row_clicked(self, index) -> None:
        """单击数据行设为表头（命中只认 index.row()）。"""
        row = index.row()
        if 0 <= row < len(self._rows):
            self._selected_row = row
            self._view.selectRow(row)
            self._refresh_summary()
            self._view.viewport().update()

    def selected_row_index(self) -> int:
        """返回选中的 0-based 行索引。"""
        return self._selected_row


# ---------------------------------------------------------------------------
# 主页面
# ---------------------------------------------------------------------------

class InputSelectionPage(QWidget):
    """阶段 1：输入数据选择页。"""

    confirm_import = pyqtSignal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._entries: List[InputEntry] = []
        # R6/D3-1（P1-7）：本会话导入副本清单（会话收尾 clear_temp_copies
        # 清理；启动超龄清理由 main_window._cleanup_stale_sessions 承担）
        self._temp_copies: List[Path] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        # ---- 顶栏 ----
        top_bar = QHBoxLayout()
        self._btn_add = QPushButton("[add]")
        self._btn_add.setToolTip("添加 Excel 文件（支持多选，自动复制到临时区并转为 xlsx）")
        self._btn_add.clicked.connect(self._on_add_files)
        top_bar.addWidget(self._btn_add)
        top_bar.addStretch(1)
        self._btn_import = QPushButton("[确认并导入]")
        self._btn_import.setToolTip("校验并将选中的数据表导入数据库")
        self._btn_import.clicked.connect(self._on_import)
        self._btn_import.setEnabled(False)
        top_bar.addWidget(self._btn_import)
        root.addLayout(top_bar)

        # ---- 表格 ----
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["选择", "标识名称", "来源文件", "源数据表", "表头行", "删除"]
        )
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        root.addWidget(self._table)

        TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def get_entries(self) -> List[Dict[str, Any]]:
        """返回选中行的条目字典列表（file_path 为临时区 xlsx 路径）。"""
        result: List[Dict[str, Any]] = []
        for entry in self._entries:
            if entry.selected:
                result.append({
                    "file_path": str(entry.file_path),
                    "sheet_name": entry.sheet_name,
                    "alias": entry.alias.strip(),
                    "header_row": entry.header_row,  # 1-based
                    # R11/A-10：带出原始文件路径（副本路径跨会话必变，不能作复现信息）
                    "source_path": str(entry.source_path or entry.file_path),
                })
        return result

    def set_entries(self, entries: List[Dict[str, Any]]) -> None:
        """回退恢复：用既有条目重建表格（含预览数据用于表头选择）。"""
        self._entries.clear()
        self._table.setRowCount(0)
        for e in entries:
            preview = self._preview_rows(
                Path(e["file_path"]), e["sheet_name"]
            )
            self._add_row(
                Path(e["file_path"]), e["sheet_name"], preview,
                alias=e.get("alias", ""),
                header_row=e.get("header_row", 1),
                source_path=e.get("source_path", ""),
            )
        self._btn_import.setEnabled(len(self._entries) > 0)

    # ------------------------------------------------------------------ #
    # 槽函数
    # ------------------------------------------------------------------ #

    def clear_temp_copies(self) -> int:
        """R6/D3-1（P1-7）：会话收尾清理已登记的导入副本（仅删仍存在的）。

        Returns:
            int: 实际删除文件数。
        """
        removed = 0
        for p in self._temp_copies:
            try:
                if p.is_file():
                    p.unlink()
                    removed += 1
            except OSError as e:
                logger.debug(f"[input_selection] 副本清理失败（跳过）{p.name}: {e}")
        self._temp_copies = []
        if removed:
            logger.info(f"[input_selection] 会话收尾清理导入副本 {removed} 个")
        return removed

    def _on_add_files(self) -> None:
        """文件对话框多选 → 复制临时区 → XLSX 预处理 → 扫描 → 加行。"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择 Excel 文件", str(ENGINE_ROOT), _EXCEL_FILTER
        )
        if not files:
            return

        from ops.excel_preprocessor import (
            clean_alias_name, ensure_xlsx, validate_and_copy,
        )

        # 同 (源文件, sheet) 查重（2026-09-21 审计 P7：堵重复导入内存翻倍）
        existing = {
            (e.source_path or str(Path(e.file_path).resolve()), e.sheet_name)
            for e in self._entries
        }
        skipped: List[str] = []

        added = 0
        # R11/A-02：异常隔离——单文件失败只坏该文件，绝不逃出槽函数；
        # finally 保证入口按钮状态必复位（W-22/P0：按钮锁死）
        try:
            for fpath in files:
                src = str(Path(fpath).resolve())
                try:
                    # ① 复制到临时区（防原文件被占用/修改）
                    copied = validate_and_copy(fpath, temp_dir=str(TEMP_DIR))
                    # R6/D3-1：副本登记（会话收尾清理，堵住"只进不出"）
                    self._temp_copies.append(Path(copied))
                    # ② 确保为 xlsx（xls 全 sheet 转换）
                    xlsx_path = ensure_xlsx(copied)
                    if str(xlsx_path) != str(copied):
                        self._temp_copies.append(Path(xlsx_path))
                    # ③ 扫描全部数据表并加行（重复 sheet 静默跳过，循环后一次提示）
                    for sheet_name, preview in self._scan_sheets(Path(xlsx_path)):
                        key = (src, sheet_name)
                        if key in existing:
                            skipped.append(f"{Path(fpath).name}/{sheet_name}")
                            continue
                        existing.add(key)
                        self._add_row(Path(xlsx_path), sheet_name, preview,
                                      source_path=src)
                        added += 1
                except (FileNotFoundError, ValueError, PermissionError,
                        ImportError, OSError, zipfile.BadZipFile) as e:
                    # R11/A-02：异常元组扩容——含 exe 态 xlrd 缺件（ImportError）、
                    # 加密/损坏/伪扩展名（zipfile.BadZipFile）与各类 OSError
                    logger.warning(f"[input_selection] 文件处理失败 {fpath}: "
                                   f"{type(e).__name__}: {e}")
                    QMessageBox.warning(
                        self, "提示",
                        f"文件处理失败：\n{fpath}\n\n"
                        f"{translate_error(f'{type(e).__name__}: {e}')}")
                    continue
                except Exception as e:  # noqa: BLE001 单文件兜底：不逃出槽函数
                    logger.exception(
                        f"[input_selection] 文件处理未预期异常 {fpath}")
                    QMessageBox.warning(
                        self, "提示",
                        f"文件处理失败：\n{fpath}\n\n"
                        f"{translate_error(f'{type(e).__name__}: {e}')}")
                    continue
        finally:
            # R11/A-02：无论中途是否异常，按钮状态与行数保持一致
            self._btn_import.setEnabled(len(self._entries) > 0)

        if added:
            logger.info(f"[input_selection] 新增 {added} 张数据表")
        if skipped:
            QMessageBox.information(
                self, "提示",
                f"已跳过 {len(skipped)} 张重复的数据表"
                "（同一文件的同一张表只导入一次）：\n" + "、".join(skipped))

    def _on_import(self) -> None:
        """校验（非空/长度/查重）→ emit confirm_import。"""
        if not self._entries:
            return

        seen_aliases: set = set()
        for row_idx, entry in enumerate(self._entries):
            if not entry.selected:
                continue
            alias = entry.alias.strip()
            if not alias:
                QMessageBox.warning(self, "提示", f"第 {row_idx + 1} 行标识名称为空")
                return
            if len(alias) > _ALIAS_MAX_LEN:
                QMessageBox.warning(
                    self, "提示",
                    f"第 {row_idx + 1} 行标识名称超过 {_ALIAS_MAX_LEN} 字"
                )
                return
            if alias in seen_aliases:
                QMessageBox.warning(self, "提示", f"标识名称重复: {alias}")
                return
            seen_aliases.add(alias)

        selected = self.get_entries()
        if not selected:
            QMessageBox.warning(self, "提示", "未勾选任何数据表")
            return

        logger.info(f"[input_selection] 确认导入 {len(selected)} 张数据表")
        self.confirm_import.emit(selected)

    # ------------------------------------------------------------------ #
    # 表格构建
    # ------------------------------------------------------------------ #

    def _add_row(
        self,
        file_path: Path,
        sheet_name: str,
        preview_rows: List[List[str]],
        alias: str = "",
        header_row: int = 1,
        source_path: str = "",
    ) -> None:
        """追加一行（默认别名经清洗，默认全选）。"""
        from ops.excel_preprocessor import clean_alias_name

        row = self._table.rowCount()
        self._table.insertRow(row)

        # 默认别名：{清洗后文件名}-sheet_{清洗后表名}，截断 50 字
        if not alias:
            stem = clean_alias_name(file_path.stem) or "文件"
            sheet = clean_alias_name(sheet_name) or "表"
            alias = f"{stem}-sheet_{sheet}"[:_ALIAS_MAX_LEN]

        entry = InputEntry(
            file_path=file_path,
            sheet_name=sheet_name,
            alias=alias,
            header_row=header_row,
            selected=True,
            source_path=source_path,
        )
        self._entries.append(entry)

        # 列 0：复选框（勾选灰底）
        chk = QCheckBox()
        chk.setChecked(True)
        chk.stateChanged.connect(lambda state, r=row: self._on_check_changed(r, state))
        self._table.setCellWidget(row, 0, self._center_widget(chk))

        # 列 1：标识名称（可编辑）
        le_alias = QLineEdit(alias)
        le_alias.textChanged.connect(lambda text, r=row: self._on_alias_changed(r, text))
        self._table.setCellWidget(row, 1, le_alias)

        # 列 2：来源文件
        lbl_file = QLabel(file_path.name)
        lbl_file.setToolTip(str(file_path))
        self._table.setCellWidget(row, 2, self._center_widget(lbl_file))

        # 列 3：源数据表
        lbl_sheet = QLabel(sheet_name)
        self._table.setCellWidget(row, 3, self._center_widget(lbl_sheet))

        # 列 4：表头行按钮（空表/全空预览禁用 + 提示，2026-09-21 定稿 M1-T5）
        btn_header = QPushButton(f"第{header_row}行")
        if not preview_rows or all(all(c == "" for c in r) for r in preview_rows):
            btn_header.setEnabled(False)
            btn_header.setToolTip("该数据表无内容，无法选择表头行")
        else:
            btn_header.setToolTip("点击选择表头所在行（该行上移为第一行）")
        btn_header.clicked.connect(
            lambda _=False, r=row, pr=preview_rows: self._on_pick_header(r, pr)
        )
        self._table.setCellWidget(row, 4, self._center_widget(btn_header))

        # 列 5：删除按钮
        btn_del = QPushButton("[del]")
        btn_del.clicked.connect(lambda _=False, r=row: self._on_delete_row(r))
        self._table.setCellWidget(row, 5, self._center_widget(btn_del))

        # 默认勾选 → 灰底
        self._apply_row_bg(row, True)

    def _on_check_changed(self, row: int, state: int) -> None:
        """勾选状态变化 → 更新模型 + 行背景着色。"""
        if 0 <= row < len(self._entries):
            checked = (state == Qt.Checked)
            self._entries[row].selected = checked
            self._apply_row_bg(row, checked)

    def _apply_row_bg(self, row: int, checked: bool) -> None:
        """整行背景着色：勾选灰 / 未选白。"""
        color = _CHECKED_BG if checked else _UNCHECKED_BG
        for col in range(6):
            widget = self._table.cellWidget(row, col)
            if widget is not None:
                # 列1为 QLineEdit 需保留自身可编辑样式，仅设背景
                widget.setStyleSheet(f"background-color: {color};")

    def _on_alias_changed(self, row: int, text: str) -> None:
        """同步别名编辑。"""
        if 0 <= row < len(self._entries):
            self._entries[row].alias = text

    def _on_pick_header(self, row: int, preview_rows: List[List[str]]) -> None:
        """弹窗选择表头行（1-based 存储与显示）。"""
        if not preview_rows or all(all(c == "" for c in r) for r in preview_rows):
            QMessageBox.information(
                self, "提示", "该数据表无内容，无法选择表头行")
            return
        dlg = _HeaderRowDialog(preview_rows, self)
        if dlg.exec_() == QDialog.Accepted:
            idx = dlg.selected_row_index()  # 0-based
            if 0 <= row < len(self._entries):
                self._entries[row].header_row = idx + 1  # 转 1-based
                # cellWidget 返回 _center_widget 的包装容器，需经 findChildren
                # 取出真实 QPushButton 再更新文本（修复 setText AttributeError）
                wrapper = self._table.cellWidget(row, 4)
                if wrapper is not None:
                    for btn in wrapper.findChildren(QPushButton):
                        btn.setText(f"第{idx + 1}行")
                        break

    def _on_delete_row(self, row: int) -> None:
        """删除行：更新模型后整表重建（消除旧实现的索引错位缺陷）。"""
        if 0 <= row < len(self._entries):
            del self._entries[row]
            self._rebuild_table()
        self._btn_import.setEnabled(len(self._entries) > 0)

    def _rebuild_table(self) -> None:
        """按 _entries 重建整表（删除行后索引安全）。"""
        self._table.setRowCount(0)
        entries = list(self._entries)
        self._entries.clear()
        for entry in entries:
            preview = self._preview_rows(entry.file_path, entry.sheet_name)
            self._add_row(
                entry.file_path, entry.sheet_name, preview,
                alias=entry.alias, header_row=entry.header_row,
                source_path=entry.source_path,
            )
            # 恢复勾选状态
            last = len(self._entries) - 1
            self._entries[last].selected = entry.selected
            if not entry.selected:
                chk = self._table.cellWidget(last, 0)
                if chk is not None:
                    for child in chk.findChildren(QCheckBox):
                        child.setChecked(False)
                        break
                self._apply_row_bg(last, False)

    # ------------------------------------------------------------------ #
    # 静态辅助
    # ------------------------------------------------------------------ #

    @staticmethod
    def _center_widget(widget: QWidget) -> QWidget:
        """水平居中包装。"""
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(widget)
        return wrapper

    @staticmethod
    def _scan_sheets(file_path: Path) -> List[tuple]:
        """扫描 xlsx 全部数据表：[(sheet名, 前 50 行预览（_PREVIEW_ROWS）)]。

        预览数据供表头行选择弹窗使用（表头行需看内容才能判断）。
        """
        from openpyxl import load_workbook

        wb = load_workbook(str(file_path), read_only=True, data_only=True)
        result: List[tuple] = []
        for sname in wb.sheetnames:
            ws = wb[sname]
            rows: List[List[str]] = []
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i >= _PREVIEW_ROWS:
                    break
                rows.append([str(c) if c is not None else "" for c in row])
            result.append((sname, rows))
        wb.close()
        return result

    @staticmethod
    def _preview_rows(file_path: Path, sheet_name: str) -> List[List[str]]:
        """读取指定 sheet 前 N 行预览（表头选择弹窗数据）。"""
        from openpyxl import load_workbook

        try:
            wb = load_workbook(str(file_path), read_only=True, data_only=True)
            if sheet_name not in wb.sheetnames:
                wb.close()
                return []
            ws = wb[sheet_name]
            rows: List[List[str]] = []
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i >= _PREVIEW_ROWS:
                    break
                rows.append([str(c) if c is not None else "" for c in row])
            wb.close()
            return rows
        except Exception as e:
            logger.warning(f"[input_selection] 预览读取失败 {file_path.name}[{sheet_name}]: {e}")
            return []
