"""
rpa_engine/gui/page_operation_config.py

v3.1 阶段 2 —— 操作配置页（P3 重做版；2026-09-20 M-b/M-c 改造）。

布局：
- 顶栏：[< 返回数据选择] + 单一「添加功能步骤 ▾」QToolButton（Qt.Popup
  功能区：搜索/最近使用/四分组网格卡片，2026-09-21 定稿 D-B/M3-T3）
  + 保存配置 + 清空
- 主体（左右分割 6:4）：
  - 左侧：节点图（五类边由 gui.graph_edges 单一事实源驱动；画布严格只读，
    调序能力已随 C1 裁定取消，M3/M13）
  - 右侧面板三态（M15/M25）：步骤＝目标表选择 + 内联参数表单 + 连线说明 +
    删除；数据表＝表信息 + 连线说明 + 弃用/恢复；无选中＝空提示
- 模板栏：模板列表 + 应用（表数校验）/ 刷新 / 导入
- 底栏：退出程序 + 开始执行

交互要点（对应需求 2/5/7）：
- 步骤参数在右侧面板内联表单中编辑（forms.py 表单，QWidget 内嵌非弹窗）
- 表弃用/恢复：点击画布表节点 → 右侧表详情面板按钮（可逆，无二次确认；
  覆盖原表为不可逆操作，保存/执行前强制二次确认，M25/D-3）
- 模板应用前置校验：模板要求的数据表数 ≤ 当前已导入数据表数，否则阻止
- 回退暂存由主窗口负责（本页提供 restore_config 恢复入口）

Signals:
    go_back_to_input():      返回阶段 1
    start_workflow():        开始执行
    exit_clicked():          退出程序
    save_config_requested(): 保存当前配置为模板
"""

from collections import deque
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from PyQt5.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QSizeGrip   # R6/E7（P2-7）：frameless 缩放手柄
from PyQt5.QtWidgets import (
    QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton, QScrollArea,
    QSplitter, QToolButton, QVBoxLayout, QWidget,
)

from gui import styles
from gui.forms import get_form_class
from gui.graph_edges import build_edges, specs_from_model
from gui.models import (STEP_CATALOG, WorkflowModel, categories,
                        category_ops, display_name, extra_input_ids,
                        is_end_op, ordinal_map, title_of)
from gui.recent_steps import load_recent, push_recent
from gui.node_graph import (
    CANVAS_WARN_STEPS, GraphLayoutData, NodeGraphScene, NodeGraphView,
    NodeStatus, StepLayoutEntry,
)
from gui.user_template_manager import UserTemplateManager, parse_template_file
from paths import get_engine_root

ENGINE_ROOT = get_engine_root()


class OperationConfigPage(QWidget):
    """阶段 2：操作配置页。"""

    go_back_to_input = pyqtSignal()
    start_workflow = pyqtSignal()
    exit_clicked = pyqtSignal()
    save_config_requested = pyqtSignal()

    def __init__(
        self,
        model: WorkflowModel,
        tpl_manager: UserTemplateManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.model = model
        self._tpl_manager = tpl_manager
        self._selected_step_index: int = -1
        self._selected_table_id: Optional[str] = None   # 表详情态（M25）
        self._inline_form = None            # 当前内联参数表单（收拢用）
        # G-01/B-15：表单所属步骤的稳定标识（uid）；收拢回写按 uid 定位，
        # 与下标解耦，杜绝插入/删除后下标漂移把表单值误写进相邻步骤
        self._form_step_uid: Optional[str] = None
        self._last_edges: List[Any] = []    # 最近一次派生的五类边（连线说明用）

        # 阶段 1 传入的数据表注册表 [{table_id, alias, ...}]
        self._table_entries: List[Dict[str, Any]] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        # ---- 顶栏 ----
        root.addLayout(self._build_top_bar())

        # ---- 主体：节点图 | 参数面板 ----
        self._param_container = QWidget()
        self._param_layout = QVBoxLayout(self._param_container)
        self._param_layout.setContentsMargins(0, 0, 0, 0)

        self._scene = NodeGraphScene()
        self._graph_view = NodeGraphView(self._scene)
        self._scene.step_selected.connect(self._on_node_step_selected)
        self._scene.table_selected.connect(self._on_node_table_selected)
        self._scene.no_selection.connect(self._on_no_node_selected)

        main_split = QSplitter(Qt.Horizontal)
        main_split.addWidget(self._graph_view)
        main_split.addWidget(self._param_container)
        main_split.setStretchFactor(0, 6)
        main_split.setStretchFactor(1, 4)
        root.addWidget(main_split, 1)

        # ---- 模板栏 ----
        root.addLayout(self._build_template_bar())

        # ---- 撤销条（2026-09-21 定稿 D-C4：一步撤销 + 清空 5 秒撤销条） ----
        self._undo_stack: deque = deque(maxlen=10)
        self._undo_gen: int = 0   # 撤销条定时代际号（F3：防旧回调提前隐藏）
        # G-20/B-31（裁定 G12）：撤销前置"后续改动"判据——压栈后待回填的
        # "压栈后状态"指纹与已回填值；不一致（＝窗口期内有改动）拒绝撤销
        self._undo_pending: bool = False
        self._undo_expected_sig: Optional[str] = None

        # ---- R6/D5-2（P2-9）：画布合并刷新定时器（50ms 单发；高频操作
        # 只画最后一次；需要即时画布的场景走 refresh_graph 直调）----
        self._graph_timer = QTimer(self)
        self._graph_timer.setSingleShot(True)
        self._graph_timer.setInterval(50)
        self._graph_timer.timeout.connect(self._refresh_graph)
        self._canvas_warned = False   # 规模警戒每会话提示一次（D7）

        # R6/E10（P3-8）：模型变更通知回调（主窗口接线为 last_config
        # 防抖写；本页面所有模型变更路径均汇聚到画布刷新入口触发）
        self.on_model_changed = None
        self._undo_bar = QWidget()
        undo_layout = QHBoxLayout(self._undo_bar)
        undo_layout.setContentsMargins(8, 2, 8, 2)
        self._undo_label = QLabel("")
        undo_layout.addWidget(self._undo_label, 1)
        self._undo_btn = QPushButton("撤销")
        self._undo_btn.clicked.connect(self._on_undo_clicked)
        undo_layout.addWidget(self._undo_btn)
        self._undo_bar.hide()
        root.addWidget(self._undo_bar)

        # ---- 底栏 ----
        root.addLayout(self._build_bottom_bar())

        self._show_param_panel(self._build_empty_param_panel())
        self._schedule_graph_refresh()
        self._refresh_templates()

    # ------------------------------------------------------------------ #
    # 构建函数
    # ------------------------------------------------------------------ #

    def _build_top_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()

        btn_back = QPushButton("[< 返回数据选择]")
        btn_back.setToolTip("返回输入数据选择页（当前配置将暂存）")
        btn_back.clicked.connect(self.go_back_to_input.emit)
        bar.addWidget(btn_back)

        bar.addSpacing(8)
        # 单一「添加功能步骤 ▾」入口 + Qt.Popup 功能区（2026-09-21 定稿
        # D-B/M3-T3：搜索框/最近使用/四分组网格卡片；外点/ESC 自动关闭；
        # 卡片文字仅来自 StepMeta display/desc，禁硬编码 op 名）
        self._btn_add = QToolButton()
        self._btn_add.setText("添加功能步骤 ▾")
        self._btn_add.setToolTip("点击打开功能区，选择要添加的功能步骤")
        self._btn_add.clicked.connect(self._toggle_add_popup)
        bar.addWidget(self._btn_add)
        self._build_add_popup()

        bar.addStretch(1)
        btn_save = QPushButton("保存配置")
        btn_save.clicked.connect(self._on_save_clicked)
        bar.addWidget(btn_save)
        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self._on_clear_steps)
        bar.addWidget(btn_clear)
        return bar

    # ------------------------------------------------------------------ #
    # 「添加功能步骤」功能区弹层（2026-09-21 定稿 D-B/M3-T3/T4/T5）
    # ------------------------------------------------------------------ #

    def _build_add_popup(self) -> None:
        """Qt.Popup 功能区：搜索框（默认聚焦）+ 最近使用 + 四分组网格卡片。"""
        self._add_popup = QWidget(None, Qt.Popup)
        lay = QVBoxLayout(self._add_popup)
        self._add_search = QLineEdit()
        self._add_search.setPlaceholderText("搜索功能（名称或关键词）")
        self._add_search.textChanged.connect(self._filter_popup)
        lay.addWidget(self._add_search)

        self._recent_box = QHBoxLayout()
        lay.addLayout(self._recent_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        content = QWidget()
        self._add_grid = QGridLayout(content)
        scroll.setWidget(content)
        lay.addWidget(scroll, 1)

        self._add_cards: Dict[str, QPushButton] = {}
        row = 0
        for cat in categories():
            title = QLabel(cat)
            title.setStyleSheet("font-weight: bold;")
            self._add_grid.addWidget(title, row, 0, 1, 4)
            row += 1
            col = 0
            for key in category_ops(cat):
                meta = STEP_CATALOG[key]
                btn = QPushButton(f"{meta.display}\n{meta.desc}")
                btn.setToolTip(meta.desc)
                if meta.deprecated:
                    btn.setEnabled(False)
                    btn.setText(f"{meta.display}（已停用）")
                btn.setProperty(
                    "search_text",
                    f"{meta.display} {' '.join(meta.keywords)} {key}".lower())
                btn.clicked.connect(
                    lambda _=False, k=key: self._on_add_popup_clicked(k))
                self._add_grid.addWidget(btn, row, col, 1, 1)
                self._add_cards[key] = btn
                col += 1
            row += 1
        self._refresh_recent_box()

    def _refresh_recent_box(self) -> None:
        """最近使用区重建（≤5、去重；无历史整区隐藏，定稿 Q2）。"""
        while self._recent_box.count():
            item = self._recent_box.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        recents = [k for k in load_recent() if k in STEP_CATALOG
                   and not STEP_CATALOG[k].deprecated]
        if recents:
            lbl = QLabel("最近使用:")
            self._recent_box.addWidget(lbl)
            for k in recents:
                b = QPushButton(STEP_CATALOG[k].display)
                b.clicked.connect(
                    lambda _=False, kk=k: self._on_add_popup_clicked(kk))
                self._recent_box.addWidget(b)
        self._recent_box.addStretch(1)

    def _filter_popup(self, text: str) -> None:
        """搜索过滤：display+keywords+key 命中才显示卡片。"""
        t = text.strip().lower()
        for key, btn in self._add_cards.items():
            hit = (not t) or (t in str(btn.property("search_text")))
            btn.setVisible(hit)

    def _toggle_add_popup(self) -> None:
        if self._add_popup.isVisible():
            self._add_popup.hide()
            return
        self._add_search.clear()
        self._filter_popup("")
        self._add_popup.adjustSize()
        pos = self._btn_add.mapToGlobal(
            QPoint(0, self._btn_add.height()))
        self._add_popup.move(pos)
        self._add_popup.show()
        self._add_search.setFocus()

    def _on_add_popup_clicked(self, key: str) -> None:
        self._add_popup.hide()
        self._on_add_step(key)

    def _build_template_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.addWidget(QLabel("模板"))
        self._tpl_list = QListWidget()
        self._tpl_list.setMaximumHeight(72)
        self._tpl_list.setToolTip("双击或点击[应用]覆盖当前配置（应用前校验数据表数量）")
        bar.addWidget(self._tpl_list, 1)

        btn_apply = QPushButton("应用")
        btn_apply.clicked.connect(self._on_apply_template)
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self._refresh_templates)
        btn_import = QPushButton("导入")
        btn_import.clicked.connect(self._on_add_template)
        bar.addWidget(btn_apply)
        bar.addWidget(btn_refresh)
        bar.addWidget(btn_import)
        self._tpl_list.itemDoubleClicked.connect(
            lambda _item: self._on_apply_template()
        )
        return bar

    def _build_bottom_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.addStretch(1)
        btn_exit = QPushButton("退出程序")
        btn_exit.clicked.connect(self.exit_clicked.emit)
        bar.addWidget(btn_exit)
        btn_start = QPushButton("开始执行")
        btn_start.setObjectName("btn_primary")
        btn_start.clicked.connect(self._on_start_clicked)
        bar.addWidget(btn_start)
        # R6/E7（P2-7）：frameless 窗口拖拉缩放手柄（右下角）
        bar.addWidget(QSizeGrip(self))
        return bar

    # ------------------------------------------------------------------ #
    # 参数面板
    # ------------------------------------------------------------------ #

    def _build_empty_param_panel(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        hint = QLabel("点击左侧节点图中的步骤\n查看与编辑参数")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #999999; font-size: 14px;")
        layout.addWidget(hint)
        return w

    def _build_step_param_panel(self, step_index: int) -> QWidget:
        """选中步骤面板：目标表选择 + 内联参数表单 + 步骤控制（无弹窗）。"""
        if not (0 <= step_index < len(self.model.steps)):
            return self._build_empty_param_panel()

        step = self.model.steps[step_index]
        w = QWidget()
        layout = QVBoxLayout(w)

        header = QLabel(
            f"步骤 {step_index + 1}: "
            f"{title_of(self.model.steps, step.step_id)}")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        layout.addWidget(QLabel(f"操作类型: {display_name(step.type)}"))

        # 目标数据表选择（可用 = 输入表 + 前序派生表）
        layout.addWidget(QLabel("目标数据表（本步骤操作哪张表）"))
        self._target_combo = QComboBox()
        available = self.model.available_table_ids(upto_step=step_index)
        for tid in available:
            self._target_combo.addItem(f"{tid} ({self.model.alias_of(tid)})", tid)
        cur = step.target_table_id
        idx = self._target_combo.findData(cur)
        if idx >= 0:
            self._target_combo.setCurrentIndex(idx)
        elif cur:
            # G-02/B-16（裁定 G4）：步骤引用的数据表已不存在——**不得静默
            # 改写 step.target_table_id**；下拉置空态（-1）+ 中文提示 +
            # 刷新画布 + 入撤销栈（使本次状态变化可撤销）
            self._target_combo.setCurrentIndex(-1)
            self._notify_missing_target(step)
        elif self._target_combo.count() > 0:
            # 目标表为空（尚未选择）：置空态交由用户显式选择，不改写模型
            # （原实现静默选中首项并直写 step.target_table_id，属静默改写）
            self._target_combo.setCurrentIndex(-1)
        self._target_combo.currentIndexChanged.connect(
            lambda i, si=step_index: self._on_target_changed(si, i)
        )
        layout.addWidget(self._target_combo)

        # 派生表编号（产出表操作自动分配）
        if step.output_table_id:
            layout.addWidget(QLabel(f"产出数据表编号: {step.output_table_id}"
                                    f"（后续步骤可引用）"))

        # 内联参数表单（改进：直接显示编辑，参数在切换/保存/开始时收拢）
        form_cls = get_form_class(step.type)
        self._inline_form = None
        self._form_step_uid = None
        if form_cls is not None:
            self._inline_form = self._make_form(step, available, parent=w)
            # G-01/B-15：登记表单所属步骤稳定标识，供收拢时按 uid 回写
            self._form_step_uid = step.uid
            layout.addWidget(self._inline_form)

        # 连线说明（M15/ADR-4 第 3 层：承接原画布色卡说明区的解释职能，
        # 数据源＝graph_edges 派生的五类边，蓝本 _edge_summary）
        layout.addWidget(QLabel("连线说明"))
        edge_lbl = QLabel(self._edge_summary("step", step.step_id))
        edge_lbl.setWordWrap(True)
        edge_lbl.setTextFormat(Qt.RichText)
        edge_lbl.setStyleSheet(
            f"color: {styles.GRAPH_CARD_SUBTITLE}; font-size: 12px;")
        layout.addWidget(edge_lbl)

        layout.addStretch(1)

        # 步骤控制（M15/C1：上移/下移按钮已删除——执行顺序即添加顺序，
        # 调序需求由删除重加承载；步骤删除保留）
        ctrl = QHBoxLayout()
        btn_del = QPushButton("[del]")
        btn_del.clicked.connect(lambda: self._on_delete_step(step_index))
        ctrl.addWidget(btn_del)
        layout.addLayout(ctrl)
        return w

    def _build_table_param_panel(self, table_id: str) -> QWidget:
        """表详情面板（M25①：选中表 → 表信息 + 连线说明 + 弃用/恢复）。

        弃用为可逆操作、无二次确认（对称性决策 d2）；弃用后画布即时呈现
        灰虚线弃用边，导出时按弃用闭包过滤（models.to_dict）。
        """
        w = QWidget()
        layout = QVBoxLayout(w)

        header = QLabel(f"数据表 {table_id}")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        entry = next((e for e in self._table_entries
                      if e["table_id"] == table_id), None)
        if entry is not None:
            producer_line = "来源: 外部导入（输入表）"
            alias = entry.get("alias", "") or "—"
            src = Path(entry.get("file_path", "") or "").name or "—"
            sheet = entry.get("sheet_name", "") or ""
            layout.addWidget(QLabel("角色: 输入表"))
            layout.addWidget(QLabel(f"别名: {alias}"))
            layout.addWidget(QLabel(f"来源文件: {src}"
                                    + (f"（{sheet}）" if sheet else "")))
        else:
            producer = next((s for s in self.model.steps
                             if s.output_table_id == table_id), None)
            layout.addWidget(QLabel("角色: 结果表（由步骤产出）"))
            layout.addWidget(QLabel(f"别名: {self.model.alias_of(table_id)}"))
            producer_line = (f"产出步骤: 「{producer.name}」"
                             if producer else "产出步骤: —")
        layout.addWidget(QLabel(producer_line))

        deprecated = table_id in self.model.deprecated_tables
        dep_lbl = QLabel("弃用状态: " + ("<b>已弃用</b>（导出时将连同其下游"
                                        "步骤一并剔除）" if deprecated
                                        else "正常使用"))
        dep_lbl.setWordWrap(True)
        dep_lbl.setTextFormat(Qt.RichText)
        layout.addWidget(dep_lbl)

        layout.addWidget(QLabel("连线说明"))
        edge_lbl = QLabel(self._edge_summary("table", table_id))
        edge_lbl.setWordWrap(True)
        edge_lbl.setTextFormat(Qt.RichText)
        edge_lbl.setStyleSheet(
            f"color: {styles.GRAPH_CARD_SUBTITLE}; font-size: 12px;")
        layout.addWidget(edge_lbl)

        layout.addStretch(1)

        btn = QPushButton("恢复使用" if deprecated else "弃用此表")
        btn.setToolTip("弃用后该表及其下游步骤不再参与执行（可逆，随时恢复）")
        btn.clicked.connect(
            lambda _c=False, t=table_id, f=deprecated:
            self._on_deprecate_table(t, not f))
        layout.addWidget(btn)
        return w

    def _show_param_panel(self, panel: QWidget) -> None:
        while self._param_layout.count():
            item = self._param_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._param_layout.addWidget(panel)

    # ------------------------------------------------------------------ #
    # 步骤管理
    # ------------------------------------------------------------------ #

    def _resolve_insert_index(self) -> int:
        """三态锚点解析（K6/C2，对齐 docs/plan/DAG_refactor_plan.md §8.6 L573
        原文，现场核对 grep -n "插入三态锚点" docs/plan/DAG_refactor_plan.md；
        ②消费者的 is_end 排除＝§8.6"同 is_end 保护"语义的展开，§9.4 项②）。

        返回 insert_step 的插入下标（插入时点口径 [0, len(steps)]）；
        直扫 model.steps，不读 _last_edges 快照（E9 单一源）。
        """
        steps = self.model.steps
        sel = self._selected_step_index
        if 0 <= sel < len(steps):                           # ① 选中步骤态
            if is_end_op(steps[sel].type):
                return sel                                  # 选中结束步→插其前（C2）
            return sel + 1                                  # 否则插其后
        tid = self._selected_table_id
        if tid:                                             # ② 选中表态
            p = -1                                          # 最后产出步下标
            c = -1                                          # 最后消费者下标（排除 is_end）
            for i, s in enumerate(steps):
                if s.output_table_id == tid:
                    p = i
                if ((s.target_table_id == tid
                     or tid in extra_input_ids(s))
                        and not is_end_op(s.type)):  # is_end 不计入消费者（§9.4 项②）
                    c = i
            if p >= 0:
                return p + 1                                # 产出步后
            if c >= 0:
                return c + 1                                # 最后消费者后
            # 两者皆无 → 按「无选中」处理（走③）
        if steps and is_end_op(steps[-1].type):             # ③ 无选中：末尾+is_end 保护
            return len(steps) - 1
        return len(steps)                                   # 空流程返回 0（§4.4 首行一致）

    def _on_add_step(self, type_name: str) -> None:
        if not self._table_entries:
            QMessageBox.information(self, "提示", "请先在阶段 1 选择数据表")
            return
        idx = self._resolve_insert_index()
        step = self.model.insert_step(idx, type_name)
        push_recent(type_name)
        self._refresh_recent_box()
        self._schedule_graph_refresh()
        # 添加后自动选中：右侧内联表单立即展开 + 画布卡片选中高亮（M3-T5；
        # G-01/B-15：插入后按**实际对象位置**重算下标，不沿用旧下标 sel/idx，
        # step_id 取 renumber 后值）
        idx_new = next(i for i, s in enumerate(self.model.steps) if s is step)
        self._select_step(idx_new)
        self._scene.select_node("step", step.step_id)
        logger.info(f"[operation_config] 添加步骤: {type_name}")

    def _on_delete_step(self, index: int) -> None:
        if 0 <= index < len(self.model.steps):
            self._harvest_current_form(show_errors=False)
            self._push_undo(f"删除步骤 {index + 1}")
            self.model.remove_step(index)
            if self._selected_step_index == index:
                self._selected_step_index = -1
            elif self._selected_step_index > index:
                self._selected_step_index -= 1
            self._show_panel_for(self._selected_step_index)
            self._schedule_graph_refresh()

    def _on_clear_steps(self) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("确认清空")
        box.setText("确定要清空所有已配置的步骤吗？")
        box.setIcon(QMessageBox.Question)
        btn_ok = box.addButton("确定", QMessageBox.AcceptRole)
        box.addButton("取消", QMessageBox.RejectRole)
        box.exec_()
        if box.clickedButton() is not btn_ok:
            return
        # 先收拢当前表单再压栈（对齐 _on_delete_step 先例，2026-09-21 审计
        # P5：撤销"清空"须还原用户所见现场）
        self._harvest_current_form(show_errors=False)
        self._push_undo("清空全部步骤")
        self.model.reset_steps()
        self._selected_step_index = -1
        self._show_param_panel(self._build_empty_param_panel())
        self._schedule_graph_refresh()

    # ------------------------------------------------------------------ #
    # 撤销（2026-09-21 定稿 D-C4/M2-T7/T8：一步撤销 + 5 秒撤销条）
    # ------------------------------------------------------------------ #

    def _push_undo(self, label: str) -> None:
        """破坏性操作前压栈编辑态快照（栈深≤10，快照仅模型数据）。

        F3 修复：快照含 _next_step_num（临时号分配连续性）；撤销条定时
        带代际号，连续压栈时旧代际回调不再提前隐藏新撤销条。

        G-20/B-31：栈满（maxlen）丢弃最老快照时记 warning（不再静默）；
        压栈即清空"压栈后状态"指纹，待首个模型刷新回填（撤销前置比对用）。
        """
        if (self._undo_stack.maxlen is not None
                and len(self._undo_stack) >= self._undo_stack.maxlen):
            logger.warning(
                f"[operation_config] 撤销栈已满"
                f"（maxlen={self._undo_stack.maxlen}），最旧快照将被丢弃")
        self._undo_stack.append((label, deepcopy({
            "tables": self.model.tables,
            "steps": self.model.steps,
            "deprecated": set(self.model.deprecated_tables),
            "states": dict(self.model.table_states),
            "next_step_num": self.model._next_step_num,
        })))
        self._undo_pending = True
        self._undo_expected_sig = None
        self._show_undo_bar(label)

    def _undo_last(self) -> bool:
        """弹出栈顶快照并恢复模型；空栈返回 False。

        G-20/B-31（裁定 G12）：撤销前比对当前模型与"压栈后状态"指纹；
        若窗口期（撤销条存活期）内存在后续改动则**拒绝撤销**并给出中文
        提示，避免静默整覆盖 tables/steps/deprecated/table_states 抹掉
        其它改动；无后续改动时行为与原先一致。
        """
        if not self._undo_stack:
            return False
        if (self._undo_expected_sig is not None
                and self._model_signature() != self._undo_expected_sig):
            logger.warning(
                "[operation_config] 撤销被拒：检测到撤销后有新的改动")
            QMessageBox.warning(
                self, "无法撤销",
                "检测到撤销后有新的改动，已取消本次撤销。\n"
                "请先确认这些改动后再操作。")
            return False
        label, snap = self._undo_stack.pop()
        self.model.tables = snap["tables"]
        self.model.steps = snap["steps"]
        self.model.deprecated_tables = snap["deprecated"]
        self.model.table_states = snap["states"]
        self.model._next_step_num = snap["next_step_num"]
        self.model.reconcile()
        self._undo_pending = False
        self._undo_expected_sig = None
        logger.info(f"[operation_config] 撤销: {label}")
        return True

    def _model_signature(self) -> str:
        """模型状态指纹（G-20/B-31 撤销前置"后续改动"判据）。

        覆盖数据表、步骤（含 uid/目标表/参数）与弃用/状态投影，用于比对
        压栈后的现场是否被窗口期内的其它改动改动过。
        """
        return repr((
            [(t.table_id, t.alias, t.sqlite_table, t.file_path, t.sheet_name)
             for t in self.model.tables],
            [(s.step_id, s.uid, s.type, s.target_table_id, s.output_table_id,
              repr(s.params)) for s in self.model.steps],
            sorted(self.model.deprecated_tables),
            sorted(self.model.table_states.items()),
        ))

    def reset_undo_stack(self) -> None:
        """清空撤销栈并隐藏撤销条（新一轮/恢复配置时调用，F3）。"""
        self._undo_stack.clear()
        self._undo_pending = False
        self._undo_expected_sig = None
        self._undo_gen += 1
        self._hide_undo_bar()

    def _on_undo_clicked(self) -> None:
        if self._undo_last():
            self._selected_step_index = -1
            self._show_panel_for(-1)
            self._schedule_graph_refresh()
        self._undo_gen += 1
        self._hide_undo_bar()

    def _show_undo_bar(self, label: str) -> None:
        self._undo_label.setText(f"已执行：{label}（5 秒内可撤销）")
        self._undo_bar.show()
        self._undo_gen += 1
        gen = self._undo_gen
        QTimer.singleShot(5000, lambda g=gen: self._hide_undo_bar_if(g))

    def _hide_undo_bar_if(self, gen: int) -> None:
        """代际校验隐藏：仅当无更新的撤销条时生效（F3）。"""
        if gen == self._undo_gen:
            self._undo_bar.hide()

    def _hide_undo_bar(self) -> None:
        self._undo_bar.hide()

    def _on_save_clicked(self) -> None:
        """保存配置入口：收拢 + 全量校验 + 覆盖确认，零步骤时确认引导。

        注：弃用闭包过滤后步骤为空**允许**保存模板（plan §4.2 条 5，
        执行侧拦截见 _confirm_active_steps）。
        """
        if not self._harvest_current_form(show_errors=True):
            return
        if not self._check_table_ids_unique():
            return
        if self.model.steps and not self._validate_all_steps():
            return
        if not self._confirm_overwrite_steps():
            return
        if not self.model.steps:
            box = QMessageBox(self)
            box.setWindowTitle("确认保存")
            box.setText(
                "当前未配置任何操作步骤，保存的模板将只包含数据表选择。\n是否继续？"
            )
            box.setIcon(QMessageBox.Question)
            btn_ok = box.addButton("继续保存", QMessageBox.AcceptRole)
            box.addButton("取消", QMessageBox.RejectRole)
            box.exec_()
            if box.clickedButton() is not btn_ok:
                return
        self.save_config_requested.emit()

    def _source_dir_for(self, table_id: str) -> str:
        """目标表源文件父目录（SupervisionReportForm 默认路径用）。"""
        from pathlib import Path
        for e in self._table_entries:
            if e.get("table_id") == table_id:
                p = str(e.get("source_path") or e.get("file_path") or "")
                return str(Path(p).parent) if p else ""
        return ""

    def _make_form(self, step, available, parent=None):
        """表单构造唯一入口（内联面板与全量校验共用，防两处参数漂移）。

        历史缺陷：内联面板传全上下文、_validate_all_steps 只传 4 参，
        导致 supervision_report 表单在校验路径上 AttributeError。
        统一入口后，新增上下文参数只需改此处一处。

        Args:
            step: StepConfig（取 params 与 target_table_id）。
            available: 该步骤可用的数据表 ID 列表。
            parent: 可选父控件（内联嵌入时传 w；校验时传 None）。

        Returns:
            表单实例；操作类型无表单类时返回 None。
        """
        form_cls = get_form_class(step.type)
        if form_cls is None:
            return None
        return form_cls(
            step.params,
            table_ids=available,
            conn_columns=self._conn_columns(),
            parent=parent,
            source_dir=self._source_dir_for(step.target_table_id),
            registry=self._table_entries,
            target_table_id=step.target_table_id or "")

    def _refresh_form_context(self, step_index: int) -> None:
        """目标表变更后刷新内联表单上下文（默认路径与期间提示联动，M7）。"""
        if (step_index == self._selected_step_index
                and self._inline_form is not None
                and hasattr(self._inline_form, "refresh_context")):
            step = self.model.steps[step_index]
            self._inline_form.refresh_context(
                source_dir=self._source_dir_for(step.target_table_id),
                registry=self._table_entries,
                target_table_id=step.target_table_id or "")

    def _on_target_changed(self, step_index: int, combo_index: int) -> None:
        """目标表下拉变更 → 更新模型 + 状态机重算 + 刷新图（F4）。"""
        if 0 <= step_index < len(self.model.steps) and self._target_combo:
            tid = self._target_combo.itemData(combo_index)
            if tid:
                self.model.steps[step_index].target_table_id = tid
                self.model.reconcile()
                self._schedule_graph_refresh()
                self._refresh_form_context(step_index)

    def _notify_missing_target(self, step) -> None:
        """目标表引用失效提示（G-02/B-16，裁定 G4）。

        步骤引用的数据表已不存在时：不改写 ``step.target_table_id``，
        弹中文提示「请重新选择」+ 刷新画布 + 入撤销栈（保证本次状态变化
        可撤销）。用户随后经下拉重新选择目标表即可恢复正常（可重新选择）。
        """
        QMessageBox.warning(
            self, "目标数据表失效",
            f"步骤「{step.name}」引用的数据表（{step.target_table_id}）"
            "已不存在，请重新选择。")
        self._push_undo(f"目标表失效提示（{step.name}）")
        self._schedule_graph_refresh()

    # ------------------------------------------------------------------ #
    # 步骤选择与内联表单收拢
    # ------------------------------------------------------------------ #

    def _select_step(self, idx: int) -> None:
        """切换选中步骤：先尽力收拢当前内联表单，再显示新面板。"""
        self._harvest_current_form(show_errors=False)
        self._selected_step_index = idx
        self._selected_table_id = None
        self._show_panel_for(idx)

    def _select_table(self, table_id: str) -> None:
        """切换选中数据表（M25①：表详情态，含弃用/恢复入口）。"""
        self._harvest_current_form(show_errors=False)
        self._selected_step_index = -1
        self._selected_table_id = table_id
        self._inline_form = None
        self._form_step_uid = None
        self._show_param_panel(self._build_table_param_panel(table_id))

    def _show_panel_for(self, idx: int) -> None:
        """显示指定步骤的面板（不收拢表单，收拢由 _select_step 负责）。"""
        if 0 <= idx < len(self.model.steps):
            self._show_param_panel(self._build_step_param_panel(idx))
        else:
            self._inline_form = None
            self._form_step_uid = None
            self._show_param_panel(self._build_empty_param_panel())

    def _harvest_current_form(self, show_errors: bool) -> bool:
        """收拢当前内联表单参数到模型。

        Args:
            show_errors: True 时校验失败弹警告（保存/开始场景）；
                False 时仅记日志尽力保存（切换步骤场景）。

        Returns:
            bool: 收拢成功（或无表单可收拢）返回 True。
        """
        form = getattr(self, "_inline_form", None)
        uid = getattr(self, "_form_step_uid", None)
        if form is None or not uid:
            return True
        # G-01/B-15：按稳定标识（uid）定位待回写步骤，与下标解耦——杜绝
        # 插入/删除后下标漂移，把当前表单值误写进相邻步骤（新步骤因此继承
        # 上一被选步骤的表单参数，含导出路径）
        step = next((s for s in self.model.steps if s.uid == uid), None)
        if step is None:
            return True
        old_mode = step.params.get("output_mode")
        ok, result = form.try_apply()
        if ok:
            # R6/A4（P2-5）：增量合并——表单只覆盖其管理的键，未管理键
            # （外部 JSON 的 logic="OR"、_cp 折叠注入到无控件父步的
            # output_mode 等）原样保留，不再整包替换静默丢失
            merged = dict(step.params)
            merged.update(result)
            step.params = merged
            # F4：params 直写后状态机重算；output_mode 变化时画布即时刷新
            # （produce 边/派生表节点随 overwritten 态增减）
            self.model.reconcile()
            if step.params.get("output_mode") != old_mode:
                self._schedule_graph_refresh()
            return True
        step_name = step.name
        if show_errors:
            QMessageBox.warning(
                self, "参数错误",
                f"步骤「{step_name}」参数未通过校验：\n{result}"
            )
        else:
            logger.warning(
                f"[operation_config] 切换步骤时表单参数未应用（保留原值）"
                f"「{step_name}」: {result}"
            )
        return False

    # ------------------------------------------------------------------ #
    # 节点图交互
    # ------------------------------------------------------------------ #

    def _on_node_step_selected(self, step_id: str) -> None:
        for idx, step in enumerate(self.model.steps):
            if step.step_id == step_id:
                self._select_step(idx)
                return

    def _on_node_table_selected(self, table_id: str) -> None:
        """画布表节点点击（M-b 起参数为表 ID）→ 表详情面板（M25①）。"""
        self._select_table(table_id)

    def _on_no_node_selected(self) -> None:
        self._selected_table_id = None
        self._select_step(-1)

    def _on_deprecate_table(self, table_id: str, flag: bool) -> None:
        """弃用/恢复数据表（M25①：可逆、无二次确认，对称性决策 d2）。

        弃用只改前端内存态（model.deprecated_tables，不入 v3.1 JSON）；
        画布即时重绘（灰虚线弃用边 + 灰化表节点），导出时按弃用闭包过滤。
        """
        self.model.deprecate_table(table_id, flag)
        self._schedule_graph_refresh()
        self._selected_table_id = table_id
        self._show_param_panel(self._build_table_param_panel(table_id))
        logger.info(f"[operation_config] 表 {table_id} "
                    f"{'已弃用' if flag else '已恢复使用'}")

    # ------------------------------------------------------------------ #
    # 连线说明（M15；数据源＝graph_edges 五类边，蓝本 _edge_summary）
    # ------------------------------------------------------------------ #

    def _tname(self, table_id: str) -> str:
        """表 ID → 用户可读名（找不到时回退 ID 本身）。"""
        for e in self._table_entries:
            if e["table_id"] == table_id:
                return self._table_display(e)
        for s in self.model.steps:
            if s.output_table_id == table_id:
                return f"{table_id} {self.model.alias_of(table_id)}"
        return table_id

    def _sname(self, step_id: str) -> str:
        """步骤 ID → 实时标题（P8 同源 title_of；找不到时回退 ID 本身）。"""
        return title_of(self.model.steps, step_id)

    def _edge_summary(self, kind: str, key: str) -> str:
        """连线说明（人话富文本）：承接原画布色卡说明区的解释职能。

        画布无常驻色卡说明区（ADR-1/ADR-4），节点/边语义在此按当前边列表
        逐条说明，使无技术背景用户点任一节点即可读懂"读什么、产什么、
        哪里有问题"。
        """
        if kind == "step":
            ins: List[str] = []
            dep_ins: List[str] = []
            outs: List[str] = []
            dang = 0
            for e in self._last_edges:
                if e.type == "reference" and e.dst == key:
                    ins.append(self._tname(e.src))
                elif e.type == "deprecated" and e.dst == key:
                    dep_ins.append(self._tname(e.src))
                elif e.type == "produce" and e.src == key:
                    outs.append(f"{self._tname(e.dst)}（{e.label or '—'}）")
                elif e.type == "dangling" and e.dst == key:
                    dang += 1
            seg = ["读取：%s" % ("、".join(ins) if ins else "—")]
            if dep_ins:
                seg.append(
                    "<span style='color:%s'>读取（已弃用）：%s</span>"
                    % (styles.GRAPH_DEPRECATED_TAG, "、".join(dep_ins)))
            seg.append("产出：%s"
                       % ("、".join(outs) if outs else "—（本步不产生新表）"))
            if dang:
                seg.append(
                    "<span style='color:%s'>输入缺失 %d 处"
                    "（画布红虚线＋⚠）</span>"
                    % (styles.GRAPH_DETAIL_FAILED, dang))
            return "；".join(seg)
        prod: List[str] = []
        cons: List[str] = []
        dep_cons: List[str] = []
        for e in self._last_edges:
            if e.type == "produce" and e.dst == key:
                prod.append(f"「{self._sname(e.src)}」")
            elif e.type == "reference" and e.src == key:
                cons.append(f"「{self._sname(e.dst)}」")
            elif e.type == "deprecated" and e.src == key:
                dep_cons.append(f"「{self._sname(e.dst)}」")
        seg = ["来源：%s" % ("、".join(prod) if prod else "外部导入（输入表）"),
               "被引用：%s" % ("、".join(cons + dep_cons)
                              if (cons or dep_cons) else "暂无步骤使用")]
        if dep_cons:
            seg.append(
                "<span style='color:%s'>本表已弃用：下游引用会提示待配置"
                "</span>" % styles.GRAPH_DEPRECATED_TAG)
        return "；".join(seg)

    # ------------------------------------------------------------------ #
    # 图刷新
    # ------------------------------------------------------------------ #

    def set_input_tables(self, table_entries: List[Dict[str, Any]]) -> None:
        """接收阶段 1 确认导入的数据表注册表。"""
        self._table_entries = list(table_entries)
        self._selected_step_index = -1
        self._inline_form = None
        self._show_param_panel(self._build_empty_param_panel())
        self._schedule_graph_refresh()

    def _table_display(self, entry: Dict[str, Any]) -> str:
        """表显示名（F6：委托 models.alias_of 单一源，registry 别名兜底）。"""
        tid = entry.get("table_id", "")
        alias = self.model.alias_of(tid)
        if not alias or alias == tid:
            alias = entry.get("alias", "")
        return f"{tid} {alias}"

    def _conn_columns(self) -> Dict[str, List[str]]:
        """输入表真实列名映射 {table_id: [列名]}（导入时随注册表下发）。

        派生表（步骤产出）不在 _table_entries，无列清单即不校验
        （运行期引擎守卫兜底）。
        """
        return {e["table_id"]: e.get("columns", [])
                for e in self._table_entries}

    def _schedule_graph_refresh(self) -> None:
        """R6/D5-2（P2-9）：合并刷新入口——50ms 内高频触发只画最后一次。

        超过 CANVAS_WARN_STEPS（D7 裁定 150 步）时一次性告警（日志＋
        状态栏，若主窗口提供）。原 13 处 self._schedule_graph_refresh() 高频调用
        点全部收口到本方法；即时性场景（执行前对齐）走 refresh_graph。
        """
        if (not self._canvas_warned
                and len(self.model.steps) > CANVAS_WARN_STEPS):
            self._canvas_warned = True
            logger.warning(
                f"[operation_config] 流程步骤较多（{len(self.model.steps)} 步，"
                f"警戒阈值 {CANVAS_WARN_STEPS}），界面刷新变慢属正常现象")
            sb = getattr(self.window(), "statusBar", None)
            if callable(sb):
                sb().showMessage("流程步骤较多，界面刷新变慢属正常现象", 5000)
        # G-20/B-31：压栈后的首个模型刷新＝回填"压栈后状态"指纹，供
        # _undo_last 撤销前置比对（窗口期内的后续改动将被检出并拒绝撤销）
        if self._undo_pending:
            self._undo_expected_sig = self._model_signature()
            self._undo_pending = False
        # R6/E10（P3-8）：画布刷新入口＝模型变更汇聚点，联动防抖保存
        cb = self.on_model_changed
        if callable(cb):
            cb()
        self._graph_timer.start()

    def _refresh_graph(self) -> None:
        """按模型状态重建节点图。

        2026-09-20 M16/D3 + M-b：布局条目与表列一律持**表 ID**（显示名由
        ``TableSpec.display`` 携带）；五类边由 ``gui.graph_edges`` 单一派生
        （输入＝未过滤模型，弃用态经 ``deprecated_tables`` 传入——渲染保留
        弃用表灰化显示，导出才过滤闭包）；渲染层按边列表绘制，不再自行
        推导连线（ADR-3）。
        """
        # 编号 → 显示名（输入表 + 派生表；派生表统一取 models.alias_of 单一源）
        id_to_display: Dict[str, str] = {
            e["table_id"]: self._table_display(e) for e in self._table_entries
        }
        for s in self.model.steps:
            if s.output_table_id:
                id_to_display.setdefault(
                    s.output_table_id,
                    f"{s.output_table_id} "
                    f"{self.model.alias_of(s.output_table_id)}")

        entries: List[StepLayoutEntry] = []
        ordinals = ordinal_map(self.model.steps)   # P8：循环外一次预算
        for step in self.model.steps:
            # 有序输入表编号（target 在前，mapping/merge 额外表在后；
            # 额外输入表派生统一走 models.extra_input_ids 数据层单一来源）
            input_ids: List[str] = []
            if step.target_table_id:
                input_ids.append(step.target_table_id)
            for tid in extra_input_ids(step):
                if tid not in input_ids:
                    input_ids.append(tid)

            entries.append(StepLayoutEntry(
                step_id=step.step_id,
                # 实时标题（display_name+位序，2026-09-21 审计 P8：
                # 删步自动收缩、消除 name 快照重号；ordinals 循环外预算）
                step_name=(f"{display_name(step.type)} "
                           f"{ordinals.get(step.step_id, 0)}"),
                op_type=step.type,
                status=NodeStatus.PENDING,
                input_tables=input_ids,
                output_table=step.output_table_id or None,
                # M17：is_end 唯一性由数据层 graph_edges.normalize_end 保证
                # （仅最后一个结束类操作为结束步）；渲染层结束锚点＝is_end 步，
                # 无结束类操作时 fallback 到末步（ADR-2）
                is_end=is_end_op(step.type),   # F6：与 graph_edges 同源判定
            ))

        # 五类边（单一事实源）+ 表列视图（含弃用态/派生表 producer）
        step_specs, table_specs = specs_from_model(self.model, id_to_display)
        edges = build_edges(step_specs, table_specs,
                            self.model.deprecated_tables)
        self._last_edges = edges

        self._scene.rebuild(GraphLayoutData(table_specs, entries, edges=edges))
        # R6/D5-3（P2-9）：视口自适配仅在步骤数变化时执行——保留用户
        # 缩放/平移位置（原每次全量重建后强制重置视口）
        _n_steps = len(self.model.steps)
        if getattr(self, "_last_fit_n", None) != _n_steps:
            self._last_fit_n = _n_steps
            self._graph_view.fit_to_scene()

    def update_step_status(self, step_id: str, status: NodeStatus,
                           reason: str = "") -> None:
        self._scene.update_step_status(step_id, status, reason)

    def set_step_runtime_status(self, step_id: str, state: str,
                                message: str = "") -> None:
        """运行期状态接线：将引擎执行状态字符串映射为节点图着色。

        Args:
            step_id: 引擎步骤编号（S1/S2/...）。
            state: worker 转发的状态 ∈ {running, completed, failed}。
            message: 失败原因文案（state=failed 时显示为卡片下方人话气泡，
                P0-⑥；其余状态忽略）。
        """
        mapping = {
            "running": NodeStatus.RUNNING,
            "completed": NodeStatus.DONE,
            "failed": NodeStatus.FAILED,
        }
        node_status = mapping.get(state)
        if node_status is not None:
            self.update_step_status(
                step_id, node_status,
                message if state == "failed" else "")

    def refresh_graph(self) -> None:
        """公共刷新入口（2026-09-21 修复轮 F1）：供 main_window 在
        save_json（内部 renumber 改 step_id）后重建画布，使 scene 键与
        执行期信号的 S{n} 对齐，消除运行状态失联。

        R6/D5-2 注：本入口保持**即时直调**（执行前对齐不允许 50ms 延迟）；
        高频交互路径走 _schedule_graph_refresh 合并。
        """
        self._refresh_graph()

    def reset_runtime_status(self) -> None:
        """执行前重置：全部步骤节点回到 PENDING（模型未变，不触发重建）。"""
        for s in self.model.steps:
            self.update_step_status(s.step_id, NodeStatus.PENDING)

    def set_output_tables(self, mapping: Dict[str, str]) -> None:
        """执行期回写：派生表编号→物理表名（画布表节点 tooltip，定稿 M2-T9）。"""
        self._scene.set_output_tables(mapping)

    # ------------------------------------------------------------------ #
    # 开始执行前置校验
    # ------------------------------------------------------------------ #

    def _check_table_ids_unique(self) -> bool:
        """数据表编号唯一性即时校验（2026-09-21 审计 P3，单一判定源
        models.validate_table_ids_unique）；撞号弹窗拦截并返回 False。"""
        dups = self.model.validate_table_ids_unique()
        if dups:
            QMessageBox.warning(
                self, "数据表编号冲突",
                f"发现 {len(dups)} 个数据表编号重复：{'、'.join(dups)}。"
                "同一编号对应两张不同的表，程序无法判断该用哪一张。\n"
                "请在右侧为相关步骤重新选择「结果保存到」，"
                "或点「清空步骤」重新配置。")
            return False
        return True

    def _on_start_clicked(self) -> None:
        """开始执行：收拢 + 空流程/弃用拦截 + 全量校验 + 目标表校验 +
        覆盖确认（M25②③）+ 编号唯一性拦截（P3）。"""
        if not self._harvest_current_form(show_errors=True):
            return
        if not self._check_table_ids_unique():
            return
        if not self.model.steps:
            QMessageBox.warning(self, "提示", "尚未配置任何操作步骤")
            return
        if not self._confirm_active_steps():
            return
        if not self._validate_all_steps():
            return
        for s in self.model.steps:
            if not s.target_table_id:
                QMessageBox.warning(
                    self, "提示",
                    f"步骤「{s.name}」未选择目标数据表，请点击该步骤后选择"
                )
                return
        if not self._confirm_overwrite_steps():
            return
        self.start_workflow.emit()

    def _confirm_active_steps(self) -> bool:
        """弃用闭包过滤后步骤为空 → 拦截执行（M25③/plan §4.2 条 5）。

        空流程允许保存模板（_on_save_clicked 不拦截），但无可执行内容时
        不允许启动执行；提示用户恢复弃用表或改存模板。
        """
        closed_steps, _closed_tables = self.model.deprecated_closure()
        if len(closed_steps) < len(self.model.steps):
            return True
        QMessageBox.warning(
            self, "提示",
            "所有步骤都因其引用的数据表被弃用而不会执行，没有可运行的内容。\n"
            "请在右侧面板「恢复使用」相关数据表，或将当前选择「保存配置」为模板。"
        )
        return False

    def _confirm_overwrite_steps(self) -> bool:
        """覆盖原表模式的强制二次确认（M25②/D-3：覆盖不可逆必须强确认）。

        Returns:
            bool: 全部覆盖步骤均确认返回 True；任一取消返回 False（阻断
            保存/执行）。
        """
        for i, s in enumerate(self.model.steps):
            if (s.params or {}).get("output_mode") != "overwrite_target":
                continue
            tname = (self._tname(s.target_table_id)
                     if s.target_table_id else "目标数据表")
            box = QMessageBox(self)
            box.setWindowTitle("确认覆盖")
            box.setText(
                f"步骤 {i + 1}「{s.name}」选择将结果覆盖保存到「{tname}」。\n"
                "原表数据将被替换且不可恢复，是否继续？"
            )
            box.setIcon(QMessageBox.Warning)
            btn_ok = box.addButton("确认覆盖", QMessageBox.AcceptRole)
            box.addButton("取消", QMessageBox.RejectRole)
            box.exec_()
            if box.clickedButton() is not btn_ok:
                return False
        return True

    # 各操作类型的目标表列名提取规则：params 键 →（子键，字段中文名）
    # 子键 None 表示 params 值本身即列名列表；否则为 dict 列表的子字段名。
    _COLUMN_PARAM_KEYS = {
        "filter": [("conditions", "column", "筛选条件列")],
        "dedup": [("key_columns", None, "去重依据列")],
        "aggregate": [("group_by", None, "分组列"),
                      ("metrics", "column", "统计指标列"),
                      ("conditions", "column", "过滤条件列")],
        "mapping_match": [("match_columns", "key", "本表匹配列")],
        "rename_columns": [("mapping", "key", "原列名")],
        "convert_dtype": [("column", None, "转换列")],
    }

    def _validate_all_steps(self) -> bool:
        """全量校验所有步骤参数（未选中编辑过的步骤也会被检查）。

        修复缺陷：此前仅校验当前选中步骤的内联表单，用户添加多步而
        未逐一编辑时，空参数直接放行到引擎才报错。
        本轮增补（缺口 A）：目标表列名存在性校验——列名错误在配置期
        拦截并提示可用列，不再漏到运行期才报错。

        Returns:
            bool: 全部通过返回 True；失败时弹警告并自动定位到问题步骤。
        """
        conn_columns = self._conn_columns()
        for i, step in enumerate(self.model.steps):
            params = step.params
            available = self.model.available_table_ids(upto_step=i)
            form = self._make_form(step, available)
            if form is not None:
                ok, result = form.try_apply()
                if not ok:
                    self._warn_and_focus(i, f"参数未配置完整：\n{result}")
                    return False
                params = result
            # 目标表列名存在性校验（缺口 A）
            col_err = self._check_step_columns(
                step, params, conn_columns)
            if col_err:
                self._warn_and_focus(i, col_err)
                return False
        return True

    def _warn_and_focus(self, step_index: int, detail: str) -> None:
        """警告弹窗（含步骤定位）并选中问题步骤。"""
        step = self.model.steps[step_index]
        QMessageBox.warning(
            self, "参数错误",
            f"步骤 {step_index + 1}「{step.name}」{detail}\n\n"
            f"已自动选中该步骤，请在右侧补全参数。"
        )
        self._select_step(step_index)

    @classmethod
    def _check_step_columns(
        cls,
        step,
        params: Dict[str, Any],
        conn_columns: Dict[str, List[str]],
    ) -> Optional[str]:
        """校验步骤引用的目标表列名均真实存在（缺口 A）。

        派生表（不在 conn_columns / 列清单为空）跳过校验；
        "*"（整表计数通配）放行。

        Returns:
            Optional[str]: 无问题返回 None；否则返回中文错误描述。
        """
        rules = cls._COLUMN_PARAM_KEYS.get(step.type)
        if not rules:
            return None
        known = conn_columns.get(step.target_table_id) or []
        if not known:
            return None    # 派生表/列清单缺失：不校验
        for key, sub, label in rules:
            value = params.get(key)
            if not value:
                continue
            if sub is None:
                cols = list(value)
            elif isinstance(value, dict):
                cols = list(value.keys())      # 如 rename 的 {原列名: 新列名}
            else:
                cols = [item.get(sub, "") for item in value
                        if isinstance(item, dict)]
            bad = [c for c in cols if c and c != "*" and c not in known]
            if bad:
                return (f"的{label}不存在: {'、'.join(bad)}\n"
                        f"可用列: {'、'.join(known)}")
        return None

    # ------------------------------------------------------------------ #
    # 模板管理
    # ------------------------------------------------------------------ #

    def _refresh_templates(self) -> None:
        self._tpl_list.clear()
        try:
            for t in self._tpl_manager.list_templates():
                name = t.get("name", t.get("filename", "?"))
                item = QListWidgetItem(str(name))
                item.setData(256, t.get("filename", ""))
                self._tpl_list.addItem(item)
        except Exception as e:
            logger.warning(f"[operation_config] 模板列表刷新失败: {e}")

    # 公开别名：主窗口保存模板成功后即时刷新列表
    refresh_templates = _refresh_templates

    def _on_apply_template(self) -> None:
        """应用模板：表数校验（需求 5）→ 覆盖当前配置。"""
        item = self._tpl_list.currentItem()
        if item is None:
            QMessageBox.information(self, "提示", "请先在模板列表选择一个模板")
            return
        filename = item.data(256)
        try:
            data = self._tpl_manager.load(filename)
        except (ValueError, OSError) as e:
            QMessageBox.warning(self, "提示", f"模板加载失败: {e}")
            return

        # 需求 5：模板要求的数据表数不得高于当前已导入数
        tpl_tables = data.get("tables", []) if isinstance(data, dict) else []
        n_current = len(self._table_entries)
        if len(tpl_tables) > n_current:
            QMessageBox.warning(
                self, "无法应用模板",
                f"该模板需要 {len(tpl_tables)} 张输入数据表，"
                f"但当前只导入了 {n_current} 张。\n"
                f"请返回阶段 1 补选数据表后再应用。"
            )
            return

        # 确认覆盖
        box = QMessageBox(self)
        box.setWindowTitle("应用模板")
        box.setText(f"应用模板「{item.text()}」将覆盖当前全部配置，是否继续？")
        box.setIcon(QMessageBox.Question)
        btn_ok = box.addButton("确定", QMessageBox.AcceptRole)
        box.addButton("取消", QMessageBox.RejectRole)
        box.exec_()
        if box.clickedButton() is not btn_ok:
            return

        # 模板表引用位置映射（输入表按序→当前 registry；派生表重分配新号），
        # 再经单一入口载入（registry 权威，2026-09-21 定稿 M2-T5/根治 H2）
        self._push_undo(f"应用模板「{item.text()}」")
        mapped = self._map_template_ids(data)
        self.model.load_session(list(self._table_entries), mapped)
        self._selected_step_index = -1
        self._show_param_panel(self._build_empty_param_panel())
        self._schedule_graph_refresh()
        QMessageBox.information(self, "提示", "模板已应用")

    def _map_template_ids(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """模板表编号 → 当前编号位置映射（2026-09-21 定稿 M2-T5/根治 H2）。

        输入表：模板第 i 张 → 当前 registry 第 i 张 table_id；派生表：按步骤序
        重分配 T101+ 新号（经 model._alloc_table_id 排除集保证唯一）；超出当前
        表数的输入表引用保持原编号（dangling 画布可视化 + 执行前 validator 拦截）。
        """
        tpl_ids = [t.get("table_id", "") for t in data.get("tables", [])
                   if isinstance(t, dict)]
        cur_ids = [e["table_id"] for e in self._table_entries]
        mapping: Dict[str, str] = {}
        for i, tid in enumerate(tpl_ids):
            if tid:
                mapping[tid] = cur_ids[i] if i < len(cur_ids) else tid
        # 派生表（不在模板输入表集合内）按步骤序重分配新号
        for s in data.get("steps", []):
            oid = s.get("output_table_id", "") if isinstance(s, dict) else ""
            if oid and oid not in mapping:
                mapping[oid] = self.model.alloc_table_id(
                    extra_used=set(mapping.values()) - set(cur_ids))

        def remap(v: str) -> str:
            return mapping.get(v, v) if v else v

        out = dict(data)
        steps = []
        for s in data.get("steps", []):
            if not isinstance(s, dict):
                continue
            ns = dict(s)
            ns["target_table_id"] = remap(s.get("target_table_id", ""))
            ns["output_table_id"] = remap(s.get("output_table_id", ""))
            params = dict(s.get("params", {}))
            if params.get("match_table_id"):
                params["match_table_id"] = remap(params["match_table_id"])
            if isinstance(params.get("match_table_ids"), list):
                params["match_table_ids"] = [
                    remap(x) for x in params["match_table_ids"]]
            # 兜底剥离过期物理名（2026-09-21 审计 P9a：派生表物理名跨会话
            # 必失配，入口即剥；与 to_dict 双口径 pop 语义对齐）
            if "output_table" in params:
                logger.warning(
                    f"[operation_config] 模板步骤 {s.get('step_id', '')} 携带"
                    "过期物理表名 output_table，已剥离（派生表物理名由执行期"
                    "自动分配）")
                params.pop("output_table")
            ns["params"] = params
            steps.append(ns)
        out["steps"] = steps
        return out

    def _on_add_template(self) -> None:
        """从外部 JSON 文件导入模板。"""
        src, _ = QFileDialog.getOpenFileName(
            self, "选择模板文件", str(ENGINE_ROOT),
            "JSON 文件 (*.json);;所有文件 (*.*)"
        )
        if not src:
            return
        try:
            data = parse_template_file(Path(src))
            if "tables" not in data:
                raise ValueError("非 v3.1 模板（缺少 tables 字段）")
        except ValueError:
            QMessageBox.warning(self, "提示", "文件不是有效的 v3.1 工作流配置")
            return
        try:
            name = Path(src).stem
            ok, msg = self._tpl_manager.save(name, data)
            if not ok:
                QMessageBox.warning(self, "提示", f"模板导入失败: {msg}")
                return
        except OSError as e:
            QMessageBox.warning(self, "提示", f"模板导入失败: {e}")
            return
        self._refresh_templates()
        QMessageBox.information(self, "提示", f"模板已导入: {name}")

    # ------------------------------------------------------------------ #
    # 暂存（回退恢复用）
    # ------------------------------------------------------------------ #

    # get_staged_config 已删除（2026-09-21 修复轮 F5：零调用死代码，且其
    # 默认过滤口径与主窗口编辑态暂存策略 to_dict(include_deprecated=True)
    # 相悖；暂存出口唯一＝main_window._back_to_input_selection）

    def restore_config(self, data: Dict[str, Any],
                       table_entries: List[Dict[str, Any]]) -> None:
        """恢复暂存配置（从阶段 1 返回时；单一入口，定稿 M2-T5）。"""
        self._table_entries = list(table_entries)
        self.model.load_session(list(table_entries), data)
        self.reset_undo_stack()   # 跨会话撤销栈清空（F3）
        self._selected_step_index = -1
        self._inline_form = None
        self._form_step_uid = None
        self._show_param_panel(self._build_empty_param_panel())
        self._schedule_graph_refresh()
