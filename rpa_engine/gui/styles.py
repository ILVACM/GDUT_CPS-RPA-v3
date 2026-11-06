"""
rpa_engine/gui/styles.py

GUI 全局样式模块：集中定义配色常量与全局 QSS 文本。
扁平风格（无渐变/无阴影/无动画），由 MainWindow.__init__ 统一应用。
"""

# -------------- 配色常量（唯一来源：节点态 + 图态；进度页着色/节点图/QSS 共同引用） --------------

COLOR_SELECTED: str = "#cfe8ff"    # 选中浅蓝
COLOR_DONE: str = "#c8f0c8"        # 完成浅绿
COLOR_RUNNING: str = "#fdf3c0"     # 运行浅黄
COLOR_PENDING: str = "#ffffff"     # 待执行白
COLOR_FAILED: str = "#f6caca"      # 失败浅红（D2 补充态）

# ---------------- 节点图（DAG 画布）图态配色 ----------------
# 2026-09-20 M20-b 落地：取值以 SampleCode 视觉词表为准（最高依据），
# 覆盖 node_graph 原 27 处硬编码 hex；M-b 阶段将 node_graph 引用改道至此。

# 画布与表节点
GRAPH_CANVAS_BG: str = "#fafafa"        # 画布背景
GRAPH_TABLE_FILL: str = "#2b7cd3"       # 表节点填充
GRAPH_TABLE_STROKE: str = "#1a5ca8"     # 表节点描边
GRAPH_TABLE_HOVER: str = "#3a8ce2"      # 表节点悬停填充
GRAPH_TABLE_FOCUS: str = "#0d47a1"      # 表节点选中描边
GRAPH_TABLE_HOVER_BG: str = "#e8f0fa"   # 表节点悬停文字底
GRAPH_TEXT_ON_FILL: str = "#ffffff"     # 深底之上的文字/描边（表名、卡片标题）

# 五类边（正本 §4.3 词表 / plan.md §1.3）
GRAPH_LANE_IN: str = "#999999"          # 输入表泳道（reference 纵向段）
GRAPH_LANE_DEV: str = "#4a90d9"         # 派生表泳道
GRAPH_ACCESS: str = "#888888"           # 数据引用边（表 → 步骤横向段）
GRAPH_LINK: str = "#555555"             # 兼容旧横向数据流线（M-b 后由 ACCESS 取代）
GRAPH_PRODUCE: str = "#2ecc71"          # 数据产出边（步骤 → 操作表，绿实线）
GRAPH_PRODUCE_LABEL: str = "#2e7d32"    # 产出边标签文字（白底衬底上可读）
GRAPH_DEPRECATED: str = "#757575"       # 弃用引用边（灰虚线）
GRAPH_DEPRECATED_FILL: str = "#9e9e9e"  # 已弃用表节点填充
GRAPH_DANGLING: str = "#d9534f"         # 悬空输入标记边（红虚线短桩）

# 起止标识与流程性质标记
GRAPH_START: str = "#2ecc71"            # 开始标识与 flow 连线
GRAPH_END: str = "#d9534f"              # 结束标识与 flow 连线
GRAPH_FORK: str = "#2ecc71"             # 分叉标记（M-b 后由产出边标签承载语义）
GRAPH_MERGE: str = "#e67e22"            # 合并标记（同上）

# 步骤卡片状态描边（与 COLOR_* 填充配套）
GRAPH_STATUS_PENDING: str = "#aaaaaa"
GRAPH_STATUS_RUNNING: str = "#f0ad4e"
GRAPH_STATUS_DONE: str = "#5cb85c"
GRAPH_STATUS_FAILED: str = "#d9534f"
GRAPH_INCOMPLETE: str = "#f0ad4e"       # 待配置（参数/输入不完整）橙描边
GRAPH_SELECTED: str = "#2b7cd3"         # 选中/悬停/高亮描边色

# 失败人话气泡
GRAPH_BUBBLE_BG: str = "#fdeceb"
GRAPH_BUBBLE_BORDER: str = "#d9534f"

# 卡片/表节点文字（M-b 补充：node_graph 零字面色口径）
GRAPH_CARD_TITLE: str = "#222222"       # 步骤卡片标题
GRAPH_CARD_SUBTITLE: str = "#666666"    # 步骤卡片业务副标题
GRAPH_TABLE_SUBTEXT: str = "#d7e9ff"    # 派生表「由「X」生成」小字
GRAPH_DEPRECATED_TAG: str = "#616161"   # 已弃用角标底 / 弃用说明文字
GRAPH_EMPTY_HINT: str = "#888888"       # 空流程提示文字

# 详情面板状态文字
GRAPH_DETAIL_PENDING: str = "#666666"
GRAPH_DETAIL_RUNNING: str = "#b8860b"
GRAPH_DETAIL_DONE: str = "#2e7d32"
GRAPH_DETAIL_FAILED: str = "#c62828"

# 自绘标题栏固定高度（像素）
TITLE_BAR_HEIGHT: int = 36


def build_qss() -> str:
    """构造全局 QSS 文本。

    覆盖范围：基础字体、扁平按钮（含主按钮/禁用态）、自绘标题栏三按钮、
    QListWidget 选中浅蓝、滚动条基础样式、分隔条与输入/展示控件边框。
    """
    return f"""
/* ============ 基础字体（微软雅黑/系统默认） ============ */
QWidget {{
    font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
    font-size: 13px;
    color: #222222;
}}

/* ============ 主窗口背景 ============ */
MainWindow {{
    background-color: #f5f6f8;
}}

/* ============ 扁平按钮（无渐变/无阴影） ============ */
QPushButton {{
    background-color: #ffffff;
    border: 1px solid #c8c8c8;
    border-radius: 3px;
    padding: 4px 14px;
}}
QPushButton:hover {{
    background-color: #e8f2ff;
    border-color: #2b7cd3;
}}
QPushButton:pressed {{
    background-color: #d5e6f7;
}}
QPushButton:disabled {{
    background-color: #f2f2f2;
    border-color: #dcdcdc;
    color: #a0a0a0;
}}

/* 主按钮（开始执行） */
QPushButton#btn_primary {{
    background-color: #2b7cd3;
    border: 1px solid #2b7cd3;
    color: #ffffff;
    padding: 6px 24px;
}}
QPushButton#btn_primary:hover {{
    background-color: #3a8ce2;
}}
QPushButton#btn_primary:pressed {{
    background-color: #1f6ab8;
}}

/* ============ 自绘标题栏（Fix-4：深色背景，白字白按钮，保证对比度） ============ */
QWidget#title_bar {{
    background-color: #2d2d30;
}}
QWidget#title_bar QLabel {{
    color: #ffffff;
    background: transparent;
    font-size: 14px;
}}
QPushButton#btn_min, QPushButton#btn_max, QPushButton#btn_close {{
    background: transparent;
    border: none;
    border-radius: 0px;
    color: #ffffff;
    font-size: 13px;
    min-width: 42px;
    max-width: 42px;
    padding: 0px;
}}
QPushButton#btn_min:hover, QPushButton#btn_max:hover {{
    background-color: #3e3e42;
}}
QPushButton#btn_close:hover {{
    background-color: #e81123;
}}
QPushButton#btn_min:pressed, QPushButton#btn_max:pressed {{
    background-color: #505054;
}}
QPushButton#btn_close:pressed {{
    background-color: #c50f1f;
}}

/* ============ 列表控件（功能区/模板区/步骤列表） ============ */
QListWidget {{
    background-color: #ffffff;
    border: 1px solid #d9d9d9;
    outline: none;
}}
QListWidget::item {{
    padding: 4px;
    border-bottom: 1px solid #f0f0f0;
}}
QListWidget::item:selected {{
    background-color: {COLOR_SELECTED};
    color: #222222;
}}
QListWidget::item:disabled {{
    color: #a0a0a0;
}}

/* ============ 输入/展示控件边框 ============ */
QPlainTextEdit, QTextBrowser, QLineEdit, QSpinBox, QTableWidget {{
    background-color: #ffffff;
    border: 1px solid #d9d9d9;
    border-radius: 2px;
    padding: 2px;
}}
QScrollArea {{
    border: 1px solid #d9d9d9;
    background-color: #fafafa;
}}

/* ============ 分隔条 ============ */
QSplitter::handle {{
    background-color: #d9d9d9;
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}
QSplitter::handle:vertical {{
    height: 2px;
}}

/* ============ 滚动条（基础扁平样式） ============ */
QScrollBar:vertical {{
    background-color: #f0f0f0;
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background-color: #c1c1c1;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: #a8a8a8;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
QScrollBar:horizontal {{
    background-color: #f0f0f0;
    height: 10px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background-color: #c1c1c1;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: #a8a8a8;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}
"""
