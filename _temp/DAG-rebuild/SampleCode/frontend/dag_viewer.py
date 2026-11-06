# -*- coding: utf-8 -*-
"""W-03 DAG 可视化演示 — 前端（设计验证原型，`_temp/` 临时实验区）

呈现 W-03 用户视角改造效果（2026-09-15 范围收敛后口径），供人工检验方案合理性。
- 单一流程视图（面向无技术背景文职用户）：业务化步骤卡片（序号徽章+操作中文名+
  业务说明）、端口不显示、开始/结束人话标记、失败人话气泡、表节点角标（输入表/结果表）
- 交互：Ctrl+滚轮缩放（钳制）、空白拖拽平移、全览、点击详情、
  点步骤高亮上下游泳道+关联边、模拟运行
- 顶部信息条：流程名（正式重构时 = 运行参数文件名称，由后端传入；
  对用户只显示流程名，禁用"参数文件"等术语）+ 进度"已完成 N/M" + 四色迷你进度条

2026-09-17 细节优化（三项，见 .trae/documents/W-03_dag_visualizer细节优化代码修改计划.md）：
- ①画布**无常驻色卡说明区**：语义由颜色/线型/箭头/节点角标/产出边标签 + 右侧详情面板
  「连线说明」承载（ADR-1/ADR-4）
- ②开始/结束标识**动态自适应**：装饰图元 + 起止连接边；开始锚定首步、结束锚定
  is_end 步（无则末步 fallback）；不占布局行、不可选中、不可删除（ADR-2）
- ③**五类边**由后端 edges 单一事实源驱动：reference（数据引用）/ produce（数据产出，
  绿色向上 + 标签"新表"/"复制新表"）/ flow（起止连接）/ dangling（悬空红虚线）/
  deprecated（弃用引用灰虚线）（ADR-3）
- 画布严格只读不变：所有边与标识图元均 setAcceptedMouseButtons(Qt.NoButton)

运行（GUI）：      python dag_viewer.py
运行（无头验证）： python dag_viewer.py --offscreen
                  → 导出 artifacts/w03-preview.png 后退出（目录自动重建；工程内部验证通道，非 GUI 功能）

技术约束：PyQt5（QGraphicsScene/View），零第三方依赖；只经伪后端接口取数。
"""
import os
import sys
from pathlib import Path

# --offscreen 必须在 import PyQt5 之前生效
_OFFSCREEN = "--offscreen" in sys.argv
if _OFFSCREEN:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# 使 `from backend.mock_backend import ...` 在任意 cwd 下可用
_ROOT = Path(__file__).resolve().parents[1]          # SampleCode/（原 W-03_dag_visualizer，09-18 固化更名）
sys.path.insert(0, str(_ROOT))

from backend.mock_backend import (get_meta, get_dag, get_node, set_status,   # noqa: E402
                                  add_step, remove_step, update_params,
                                  deprecate_table)
from backend.func_registry import (MAIN_BUTTONS, MORE_BUTTONS, op_name_cn,   # noqa: E402
                                   produce_label)

from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer                            # noqa: E402
from PyQt5.QtGui import (QColor, QPen, QBrush, QFont, QFontMetricsF,      # noqa: E402
                         QPainter, QPainterPath, QPolygonF)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,          # noqa: E402
                             QGraphicsScene, QGraphicsView, QGraphicsItem,
                             QGraphicsSimpleTextItem, QPushButton,
                             QHBoxLayout, QVBoxLayout, QLabel,
                             QScrollArea, QMenu, QMessageBox)

sys.path.insert(0, str(Path(__file__).resolve().parent))   # frontend/ 目录
from param_panel import ParamPanel                          # noqa: E402

# ---- 布局常量（CONTRACTS.md §4，2026-09-15 单一视图口径）----
COL_CX0, COL_DX = 120, 240          # col_cx(j) = 120 + 240·j
HEADER_BOTTOM = 118                 # 表头底线
TABLE_W, TABLE_H = 160, 40
STEP_W = 140
STEP_H = 70
ROW_CY0 = 193                       # row_cy(r) = 193 + 100·r
ROW_DX = 100
STACK_SP = 16
ARROW_L, ARROW_HW = 9.0, 4.5
SCENE_MARGIN, FIT_MARGIN = 40, 20
ZOOM_MIN, ZOOM_MAX = 0.40, 2.50
CANVAS_BG = "#fafafa"

# ---- 起止标识与产出边常量（2026-09-17 细节优化 ADR-2/§5.1）----
ANCHOR_DX = 35                    # 卡片顶边锚点偏移：flow 走 ccx-35、produce 走 ccx+35
FLOW_LEN = 12                     # 起止连接边长度
FLOW_GAP = 6                      # 连接边端点与卡片边缘的间隙
MARKER_TEXT_H = 16                # 12px bold 标识文字高度（offscreen 不渲染文字时按此估算）
END_AVOID_GAP = 32                # 结束标识失败避让位移（失败气泡占 bottom+5..+27）
EMPTY_HINT = "暂无步骤，请从上方功能按钮添加"

# ---- 视觉词表（CONTRACTS.md §5）----
STATUS_FILL = {"pending": "#ffffff", "running": "#fdf3c0", "done": "#c8f0c8",
               "failed": "#f6caca", "selected": "#cfe8ff"}
STATUS_STROKE = {"pending": ("#aaaaaa", 1.0), "running": ("#f0ad4e", 2.0),
                 "done": ("#5cb85c", 1.0), "failed": ("#d9534f", 2.0)}
SEL_STROKE = ("#2b7cd3", 2.0)
HOVER_STROKE = ("#2b7cd3", 2.0)
HIGHLIGHT = ("#2b7cd3", 2.5)        # 选中步骤相邻 lane/edge
TABLE_FILL, TABLE_STROKE = "#2b7cd3", "#1a5ca8"
TABLE_HOVER, TABLE_FOCUS = "#3a8ce2", "#0d47a1"
LANE_IN, LANE_DEV, ACCESS_C = "#999999", "#4a90d9", "#888888"
BUBBLE_BG, BUBBLE_BORDER = "#fdeceb", "#d9534f"
INCOMPLETE_STROKE = ("#f0ad4e", 2.0)   # 待配置（参数/输入不完整）
DEPRECATED_FILL, DEPRECATED_EDGE = "#9e9e9e", "#757575"   # 已弃用表
DANGLING_C = "#d9534f"                 # 悬空输入（红虚线）
PRODUCE_C = "#2ecc71"                  # 数据产出边（绿实线：这一步产出了新表/新分支）
PRODUCE_LABEL_C = "#2e7d32"            # 产出边标签文字（深绿，白底衬底上可读）
START_C, END_C = "#2ecc71", "#d9534f"  # 开始/结束标识与 flow 连线（同生产 _COLOR_START/_COLOR_END）
EDGE_Z = -4                            # produce/flow 边层级（低于节点，被不透明卡片遮蔽）
# 边样式优先级（_edge_style 实现口径）：高亮 > deprecated（弃用引用边灰虚线）> 常态色；
# dangling 为独立图元（红虚线短桩），不与上述链路竞争。
STATUS_CN = {"pending": "待执行", "running": "执行中", "done": "已完成", "failed": "已失败"}
STATUS_DETAIL_COLOR = {"pending": "#666666", "running": "#b8860b",
                       "done": "#2e7d32", "failed": "#c62828"}


def _font(px, bold=False):
    f = QFont("Microsoft YaHei")
    f.setPixelSize(px)
    f.setBold(bold)
    return f


def _elide(fm, text, width):
    """省略号截断；offscreen 下 metrics 可能为 0，此时原样返回。"""
    if not text:
        return text
    try:
        w = fm.width(text)
    except Exception:
        w = width
    if w <= 0:
        return text
    return fm.elidedText(text, Qt.ElideRight, width)


class StepCardItem(QGraphicsItem):
    """步骤卡片 140×70：序号徽章+标题（操作中文名）+副标题（业务说明）+失败气泡。"""

    def __init__(self, info):
        super().__init__()
        self.step = info["step"]
        self.key = self.step["key"]
        self.rect = info["rect"]
        self.config_state = info.get("config_state", "ok")
        self.missing = list(info.get("missing", []))
        self.status = "pending"
        self.fail_reason = ""
        self.selected = False
        self.hovered = False
        self.on_click = None
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        # 左右各留 55 容纳失败气泡（气泡可比卡片宽），底部留 48 容纳气泡
        return self.rect.adjusted(-55, -8, 55, 48)

    def _bubble_rect(self):
        if self.status != "failed" or not self.fail_reason:
            return QRectF()
        fm = QFontMetricsF(_font(10))
        w = fm.width(self.fail_reason)
        if w <= 0:
            w = len(self.fail_reason) * 10
        bw = min(w + 16, 230)
        return QRectF(self.rect.center().x() - bw / 2, self.rect.bottom() + 5, bw, 22)

    def shape(self):
        path = QPainterPath()
        path.addRect(self.rect.adjusted(-2, -2, 2, 2))
        b = self._bubble_rect()
        if not b.isNull():
            path.addRect(b.adjusted(-2, -2, 2, 2))
        return path

    def mousePressEvent(self, e):
        if self.on_click:
            self.on_click("step", self.key)
        e.accept()

    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()

    def paint(self, p, option, widget=None):
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect
        st = self.status
        # 填充链：失败>运行中>完成>选中>常态（§5.8）
        if st == "failed":
            fill = STATUS_FILL["failed"]
        elif st == "running":
            fill = STATUS_FILL["running"]
        elif st == "done":
            fill = STATUS_FILL["done"]
        elif self.selected:
            fill = STATUS_FILL["selected"]
        else:
            fill = STATUS_FILL["pending"]
        # 描边链：选中>悬停>待配置(incomplete)>状态>常态
        if self.selected:
            border, bw = SEL_STROKE
        elif self.hovered:
            border, bw = HOVER_STROKE
        elif self.config_state == "incomplete":
            border, bw = INCOMPLETE_STROKE
        else:
            border, bw = STATUS_STROKE.get(st, ("#aaaaaa", 1.0))
        p.setBrush(QBrush(QColor(fill)))
        p.setPen(QPen(QColor(border), bw))
        p.drawRoundedRect(r, 8, 8)

        # 序号徽章（P0-②）
        br_ = QRectF(r.left() + 5, r.top() + 5, 18, 18)
        p.setBrush(QBrush(QColor("#2b7cd3")))
        p.setPen(Qt.NoPen)
        p.drawEllipse(br_)
        p.setFont(_font(10, True))
        p.setPen(QColor("#ffffff"))
        p.drawText(br_, Qt.AlignCenter, str(self.step.get("seq", "")))
        # 标题行 = 操作中文名
        fm = QFontMetricsF(_font(13, True))
        title = _elide(fm, self.step.get("name", ""), r.width() - 32)
        p.setFont(_font(13, True))
        p.setPen(QColor("#222222"))
        p.drawText(QRectF(r.left() + 27, r.top() + 2, r.width() - 32, 22),
                   Qt.AlignVCenter | Qt.AlignLeft, title)
        # 副标题行 = 业务说明（12px #666，超宽省略）
        sub = self.step.get("business_desc", "")
        if sub:
            p.setFont(_font(12))
            p.setPen(QColor("#666666"))
            tr_ = QRectF(r.left() + 6, r.top() + 27, r.width() - 12, r.height() - 32)
            fm2 = QFontMetricsF(_font(12))
            sw = fm2.width(sub)
            if 0 < sw <= tr_.width():
                p.drawText(tr_, Qt.AlignVCenter | Qt.AlignLeft, sub)
            else:
                sub2 = fm2.elidedText(sub, Qt.ElideRight, tr_.width() * 2 - 8) if sw > 0 else sub
                p.drawText(tr_, Qt.AlignTop | Qt.AlignLeft | Qt.TextWordWrap, sub2)

        # 角标：悬空输入（红）> 待配置（橙）
        if self.missing or self.config_state == "incomplete":
            if self.missing:
                tag_txt, tag_bg = "输入缺失", DANGLING_C
            else:
                tag_txt, tag_bg = "待配置", "#f0ad4e"
            tagr = QRectF(r.right() - 52, r.top() + 3, 48, 14)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(tag_bg)))
            p.drawRoundedRect(tagr, 2, 2)
            p.setFont(_font(9, True))
            p.setPen(QColor("#ffffff"))
            p.drawText(tagr, Qt.AlignCenter, tag_txt)

        # 失败人话气泡（P0-⑥）
        if st == "failed":
            bub = self._bubble_rect()
            if not bub.isNull():
                p.setBrush(QBrush(QColor(BUBBLE_BG)))
                p.setPen(QPen(QColor(BUBBLE_BORDER), 1))
                p.drawRoundedRect(bub, 6, 6)
                fm3 = QFontMetricsF(_font(10))
                txt = _elide(fm3, self.fail_reason, bub.width() - 10)
                p.setFont(_font(10))
                p.setPen(QColor(BUBBLE_BORDER))
                p.drawText(bub, Qt.AlignCenter, txt)


class TableItem(QGraphicsItem):
    """表节点 160×40 深蓝白字；输入表 y=60 / 派生表 y=78（错位示"由步骤产出"）；
    角标「输入表/结果表」；结果表底部小字"由X生成"。"""

    def __init__(self, table, col, producer_name):
        super().__init__()
        self.table = table
        self.key = table["key"]
        self.producer_name = producer_name
        self.is_input = bool(table.get("is_input"))
        self.deprecated = bool(table.get("deprecated"))
        self.focus = False
        self.hovered = False
        self.on_click = None
        self.setAcceptHoverEvents(True)
        self.x = COL_CX0 + COL_DX * col - TABLE_W / 2
        # 输入表主体 y=60（C5：调序条取消后上移，与派生表 y=78 错位区分）
        self.ty = 60 if self.is_input else 78
        self.body = QRectF(self.x, self.ty, TABLE_W, TABLE_H)
        self._r = self.body.adjusted(-6, -4, 6, 4)

    def boundingRect(self):
        return self._r

    def mousePressEvent(self, e):
        if self.on_click:
            self.on_click("table", self.key)
        e.accept()

    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()

    def paint(self, p, option, widget=None):
        p.setRenderHint(QPainter.Antialiasing)
        # 主体（弃用：灰填充+虚线边）
        if self.deprecated:
            fill = DEPRECATED_FILL
            pen = QPen(QColor(DEPRECATED_EDGE), 1.0)
            pen.setStyle(Qt.DashLine)
        else:
            fill = TABLE_HOVER if self.hovered else TABLE_FILL
            pen = QPen(QColor(TABLE_FOCUS if self.focus else TABLE_STROKE),
                       2.0 if self.focus else 1.0)
            if not self.is_input:
                pen.setStyle(Qt.DashLine)
        p.setBrush(QBrush(QColor(fill)))
        p.setPen(pen)
        p.drawRoundedRect(self.body, 6, 6)
        # 角标（弃用表显示「已弃用」）
        tag = "已弃用" if self.deprecated else ("输入表" if self.is_input else "结果表")
        tagr = QRectF(self.x + 3, self.ty + 2, max(34, len(tag) * 9 + 10), 13)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#1a5ca8" if not self.deprecated else "#616161")))
        p.drawRoundedRect(tagr, 2, 2)
        p.setFont(_font(9, True))
        p.setPen(QColor("#ffffff"))
        p.drawText(tagr, Qt.AlignCenter, tag)
        # 主文字 = display
        fm = QFontMetricsF(_font(11, True))
        disp = _elide(fm, self.table.get("display", ""), TABLE_W - 10)
        p.setFont(_font(11, True))
        p.setPen(QColor("#ffffff"))
        if not self.is_input:
            p.drawText(QRectF(self.x, self.ty + 15, TABLE_W, 14), Qt.AlignCenter, disp)
            p.setFont(_font(9))
            p.setPen(QColor("#d7e9ff"))
            p.drawText(QRectF(self.x, self.ty + 28, TABLE_W, 11), Qt.AlignCenter,
                       "由「%s」生成" % self.producer_name)
        else:
            p.drawText(QRectF(self.x, self.ty + 15, TABLE_W, 22), Qt.AlignCenter, disp)


def _edge_style(edge_type, color, width, highlight):
    """按边类型解析连线样式，返回 (颜色, 线宽, 是否虚线)。

    参数：
        edge_type -- 边类型（reference 数据引用边 / deprecated 弃用引用边）
        color     -- 常态颜色（输入列或派生列泳道色、接入段色）
        width     -- 常态线宽
        highlight -- 是否处于选中高亮态
    样式优先级（§6.4）：高亮 > deprecated（弃用引用边，灰虚线）> 常态色实线。
    """
    if highlight:
        return HIGHLIGHT[0], HIGHLIGHT[1], False
    if edge_type == "deprecated":
        return DEPRECATED_EDGE, 1.5, True
    return color, width, False


class LaneItem(QGraphicsItem):
    """数据引用边的纵向段（泳道）：输入列 #999999 / 派生列 #4a90d9 宽 2.0；
    末位骑线消费者处画下向箭头；表被弃用时整条转灰虚线（deprecated 样式）。"""

    def __init__(self, x, y0, y1, color, arrow, table_key, step_keys,
                 edge_type="reference"):
        super().__init__()
        self.x = x
        self.y0 = min(y0, y1)
        self.y1 = max(y0, y1)
        self.color = color
        self.arrow = arrow
        self.table_key = table_key
        self.step_keys = step_keys
        self.edge_type = edge_type       # reference / deprecated（后端边驱动）
        self.highlight = False
        self._r = QRectF(x - 8, self.y0 - 2, 16, self.y1 - self.y0 + 14)

    def boundingRect(self):
        return self._r

    def paint(self, p, option, widget=None):
        p.setRenderHint(QPainter.Antialiasing)
        col, wd, dash = _edge_style(self.edge_type, self.color, 2.0, self.highlight)
        pen = QPen(QColor(col), wd)
        if dash:
            pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        p.drawLine(QPointF(self.x, self.y0), QPointF(self.x, self.y1))
        if self.arrow:
            p.setBrush(QBrush(QColor(col)))
            p.setPen(QPen(QColor(col), 1))
            p.drawPolygon(QPolygonF([
                QPointF(self.x, self.y1),
                QPointF(self.x - ARROW_HW, self.y1 - ARROW_L),
                QPointF(self.x + ARROW_HW, self.y1 - ARROW_L)]))


class AccessItem(QGraphicsItem):
    """数据引用边的横向接入段：源列中心 → 卡片左/右缘，宽 1.5，末端箭头（长 9 半宽 4.5）。"""

    def __init__(self, x0, y, x1, table_key, step_key, edge_type="reference"):
        super().__init__()
        self.x0, self.y, self.x1 = x0, y, x1
        self.table_key = table_key
        self.step_key = step_key
        self.edge_type = edge_type       # reference / deprecated（后端边驱动）
        self.dir = 1 if x1 >= x0 else -1
        self.highlight = False
        self._r = QRectF(min(x0, x1) - 5, y - 6, abs(x1 - x0) + 10, 12)

    def boundingRect(self):
        return self._r

    def paint(self, p, option, widget=None):
        p.setRenderHint(QPainter.Antialiasing)
        col, wd, dash = _edge_style(self.edge_type, ACCESS_C, 1.5, self.highlight)
        pen = QPen(QColor(col), wd)
        if dash:
            pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        p.drawLine(QPointF(self.x0, self.y), QPointF(self.x1, self.y))
        tip = QPointF(self.x1, self.y)
        p.setBrush(QBrush(QColor(col)))
        p.setPen(QPen(QColor(col), 1))
        p.drawPolygon(QPolygonF([
            tip,
            QPointF(self.x1 - self.dir * ARROW_L, self.y - ARROW_HW),
            QPointF(self.x1 - self.dir * ARROW_L, self.y + ARROW_HW)]))


class ProduceEdgeItem(QGraphicsItem):
    """数据产出边：步骤卡片顶边右锚点（ccx+35）竖直向上连到顶部操作表表头底线。

    与数据引用边（自上而下 / 横向汇入卡片）方向相反 → 无画布色卡说明区时靠"方向 + 绿色 +
    文字标签"三重区分；「数据表复制」标签为"复制新表"，一眼看出这里长出新分支。
    画布只读：本图元不接收任何鼠标事件（Qt.NoButton，点击穿透为空白语义）。
    """

    def __init__(self, x, y_top, y_bottom, label, step_key, table_key):
        super().__init__()
        self.x = x
        self.y_top = min(y_top, y_bottom)        # 上端 = 表头底线（箭头 tip）
        self.y_bottom = max(y_top, y_bottom)     # 下端 = 卡片顶边
        self.label = label or ""
        self.step_key = step_key
        self.table_key = table_key
        self.highlight = False
        self.setAcceptedMouseButtons(Qt.NoButton)
        # 包围盒：含箭头与右侧标签衬底（标签宽按字数估算，offscreen 下 metrics 为 0）
        lab_w = (len(self.label) * 10 + 14) if self.label else 0
        self._r = QRectF(x - 8, self.y_top - ARROW_L - 2,
                         16 + lab_w, (self.y_bottom - self.y_top) + ARROW_L + 6)

    def boundingRect(self):
        return self._r

    def paint(self, p, option, widget=None):
        p.setRenderHint(QPainter.Antialiasing)
        if self.highlight:
            col, wd = HIGHLIGHT
        else:
            col, wd = PRODUCE_C, 2.0
        p.setPen(QPen(QColor(col), wd))
        p.drawLine(QPointF(self.x, self.y_bottom), QPointF(self.x, self.y_top))
        # 向上箭头：tip 落在表头底线，指向被产出的操作表
        p.setBrush(QBrush(QColor(col)))
        p.setPen(QPen(QColor(col), 1))
        p.drawPolygon(QPolygonF([
            QPointF(self.x, self.y_top),
            QPointF(self.x - ARROW_HW, self.y_top + ARROW_L),
            QPointF(self.x + ARROW_HW, self.y_top + ARROW_L)]))
        if not self.label:
            return
        # 标签：白底圆角衬底 + 深绿字，贴边中段右侧（避免压线不可读）
        fm = QFontMetricsF(_font(9, True))
        tw = fm.width(self.label)
        if tw <= 0:                              # offscreen 不渲染文字，按字数估算
            tw = len(self.label) * 10
        midy = (self.y_top + self.y_bottom) / 2
        box = QRectF(self.x + 5, midy - 7, tw + 8, 14)
        p.setPen(QPen(QColor(col), 1))
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawRoundedRect(box, 3, 3)
        p.setFont(_font(9, True))
        p.setPen(QColor(PRODUCE_LABEL_C if not self.highlight else col))
        p.drawText(box, Qt.AlignCenter, self.label)


class FlowEdgeItem(QGraphicsItem):
    """起止连接边：开始标识→首步卡片顶边左锚点 / 末步卡片底边→结束标识。

    仅此两段（不画步骤→步骤的流程控制边，执行顺序由序号徽章 + 行序承载，ADR-3）。
    画布只读：不接收鼠标事件（Qt.NoButton）。
    """

    def __init__(self, x, y_far, y_near, color, step_key):
        super().__init__()
        self.x = x
        self.y_far = min(y_far, y_near)          # 远离卡片的一端
        self.y_near = max(y_far, y_near)         # 靠近卡片的一端（箭头 tip）
        self.color = color
        self.step_key = step_key
        self.highlight = False
        self.setAcceptedMouseButtons(Qt.NoButton)
        self._r = QRectF(x - 8, self.y_far - 2, 16, (self.y_near - self.y_far) + 6)

    def boundingRect(self):
        return self._r

    def paint(self, p, option, widget=None):
        p.setRenderHint(QPainter.Antialiasing)
        if self.highlight:
            col, wd = HIGHLIGHT
        else:
            col, wd = self.color, 1.5
        p.setPen(QPen(QColor(col), wd))
        p.drawLine(QPointF(self.x, self.y_far), QPointF(self.x, self.y_near))
        # 箭头恒指向卡片一侧（开始→首步；末步→结束标识）
        p.setBrush(QBrush(QColor(col)))
        p.setPen(QPen(QColor(col), 1))
        p.drawPolygon(QPolygonF([
            QPointF(self.x, self.y_near),
            QPointF(self.x - ARROW_HW, self.y_near - ARROW_L),
            QPointF(self.x + ARROW_HW, self.y_near - ARROW_L)]))


class MiniBar(QWidget):
    """迷你进度条：绿=done / 橙=running / 红=failed / 灰=pending 分段（P0-③）。"""

    SEGMENTS = (("done", "#5cb85c"), ("running", "#f0ad4e"),
                ("failed", "#d9534f"), ("pending", "#cccccc"))

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 10)
        self._counts = {}

    def set_counts(self, counts):
        self._counts = counts
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(QPen(QColor("#bbbbbb"), 1))
        p.setBrush(QBrush(QColor("#f0f0f0")))
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 3, 3)
        total = sum(self._counts.get(k, 0) for k, _ in self.SEGMENTS)
        if total <= 0:
            return
        x = 1.0
        for k, color in self.SEGMENTS:
            n = self._counts.get(k, 0)
            if n <= 0:
                continue
            seg = (w - 2.0) * n / total
            p.fillRect(QRectF(x, 1.0, seg, h - 2.0), QColor(color))
            x += seg


class CanvasView(QGraphicsView):
    """画布：Ctrl+滚轮缩放（钳制 [0.40,2.50] 锚定鼠标）；空白左键拖拽平移。"""

    def __init__(self, window):
        super().__init__()
        self._win = window
        self._pan = None
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setBackgroundBrush(QBrush(QColor(CANVAS_BG)))
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setFrameShape(QGraphicsView.NoFrame)

    def wheelEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            d = e.angleDelta().y()
            if d:
                factor = 1.15 if d > 0 else (1.0 / 1.15)
                cur = self.transform().m11()
                target = max(ZOOM_MIN, min(ZOOM_MAX, cur * factor))
                if abs(target - cur) > 1e-9:
                    self.scale(target / cur, target / cur)
            e.accept()
            return
        super().wheelEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            it = self.itemAt(e.pos())
            if not isinstance(it, (StepCardItem, TableItem)):
                self._pan = (e.globalPos(),
                             self.horizontalScrollBar().value(),
                             self.verticalScrollBar().value())
                self.viewport().setCursor(Qt.ClosedHandCursor)
                self._win.clear_selection()
                e.accept()
                return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._pan is not None and e.buttons() & Qt.LeftButton:
            gp, h0, v0 = self._pan
            dx = e.globalPos().x() - gp.x()
            dy = e.globalPos().y() - gp.y()
            s = self.transform().m11() or 1.0
            self.horizontalScrollBar().setValue(int(h0 - dx / s))
            self.verticalScrollBar().setValue(int(v0 - dy / s))
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._pan is not None:
            self._pan = None
            self.viewport().setCursor(Qt.ArrowCursor)
            e.accept()
            return
        super().mouseReleaseEvent(e)


class DagViewerWindow(QMainWindow):
    """主窗口：顶部信息条 + 工具栏 + 画布 + 右侧详情面板。"""

    def __init__(self):
        super().__init__()
        self.meta = get_meta()
        self.dag = get_dag()
        self._tables = list(self.dag.get("tables", []))
        self._steps = list(self.dag.get("steps", []))
        self._edges = list(self.dag.get("edges", []))   # 后端边列表（单一事实源）
        self._tmap = {t["key"]: t for t in self._tables}
        self._smap = {s["key"]: s for s in self._steps}
        self.selected = None          # (kind, key) or None
        self._statuses = {}
        self._fail = {}
        self._content_rect = None
        self._layout = {"step_info": {}}
        self.step_items = {}
        self.table_items = {}
        self.lane_items = []
        self.access_items = []
        self.marker_items = []
        self.produce_items = []       # 数据产出边图元
        self.flow_items = []          # 起止连接边图元

        self.sim_timer = QTimer(self)
        self.sim_timer.setInterval(800)
        self.sim_timer.timeout.connect(self._sim_tick)
        self._sim_idx = 0
        self._sim_phase = None
        self._sim_cur = None

        self.setWindowTitle("W-03 DAG 可视化演示 — %s" % self.meta.get("workflow_name", ""))
        self._build_ui()
        self.rebuild_scene()

    # ---------------- UI ----------------
    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 顶部信息条（P0-③）
        bar = QWidget()
        bar.setFixedHeight(28)
        bh = QHBoxLayout(bar)
        bh.setContentsMargins(10, 0, 10, 0)
        # 流程名 = 运行参数文件名称（正式重构时由后端传入；对用户只显示流程名，禁用"参数文件"等术语）
        self.name_lbl = QLabel("%s（%s）" % (self.meta.get("workflow_name", ""),
                                            self.meta.get("version", "")))
        namef = _font(12, True)
        self.name_lbl.setFont(namef)
        self.prog_lbl = QLabel("")
        self.prog_lbl.setFont(_font(12))
        self.mini = MiniBar()
        bh.addWidget(self.name_lbl)
        bh.addStretch(1)
        bh.addWidget(self.prog_lbl)
        bh.addSpacing(10)
        bh.addWidget(self.mini)
        root.addWidget(bar)

        # 工具栏（2026-09-15 收敛：仅「全览」「模拟运行」；2026-09-16 动态化：
        # 注册表驱动的功能按钮组——主按钮 4 项 +「更多功能 ▾」下拉，定案 5）
        tb = QWidget()
        th = QHBoxLayout(tb)
        th.setContentsMargins(8, 4, 8, 4)
        btn_fit = QPushButton("全览")
        btn_fit.clicked.connect(self.fit_all)
        btn_sim = QPushButton("模拟运行")
        btn_sim.clicked.connect(self.on_simulate)
        for w in (btn_fit, btn_sim):
            th.addWidget(w)
        for op in MAIN_BUTTONS:
            b = QPushButton("＋" + op_name_cn(op))
            b.clicked.connect(lambda _c, o=op: self.on_add_step(o))
            th.addWidget(b)
        more = QPushButton("更多功能 ▾")
        menu = QMenu(more)
        for op in MORE_BUTTONS:
            menu.addAction(op_name_cn(op), lambda o=op: self.on_add_step(o))
        more.setMenu(menu)
        th.addWidget(more)
        th.addStretch(1)
        root.addWidget(tb)

        # 中部：画布 + 右侧详情面板
        self.scene = QGraphicsScene(self)
        self.canvas = CanvasView(self)
        self.canvas.setScene(self.scene)
        panel = QWidget()
        panel.setFixedWidth(260)
        pv = QVBoxLayout(panel)
        pv.setContentsMargins(8, 8, 8, 8)
        title = QLabel("详情")
        title.setFont(_font(13, True))
        self.detail_label = QLabel("")
        self.detail_label.setWordWrap(True)
        self.detail_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.detail_label)
        scroll.setFrameShape(QScrollArea.NoFrame)
        pv.addWidget(title)
        pv.addWidget(scroll, 1)
        # 动态操作区（2026-09-16）：参数面板/删除/弃用按钮按选中态填充（X9）
        self.panel_box = QVBoxLayout()
        self.panel_box.setContentsMargins(0, 4, 0, 0)
        pv.addLayout(self.panel_box)

        row = QHBoxLayout()
        row.setContentsMargins(6, 6, 6, 6)
        row.addWidget(self.canvas, 1)
        row.addWidget(panel)
        root.addLayout(row, 1)
        self.setCentralWidget(central)
        self._detail_hint()

    # ---------------- 数据与布局 ----------------
    def _refresh_statuses(self):
        d = get_dag()
        self._statuses = dict(d.get("statuses", {}))
        self._fail = dict(d.get("fail_reasons", {}))
        self.refresh_progress()

    def refresh_progress(self):
        counts = {k: 0 for k in ("pending", "running", "done", "failed")}
        for v in self._statuses.values():
            if v in counts:
                counts[v] += 1
        for s in self._steps:                       # statuses 缺项按 pending 计
            if s["key"] not in self._statuses:
                counts["pending"] += 1
        m = len(self._steps)
        n = counts["done"] + counts["failed"]
        self.prog_lbl.setText("已完成 %d/%d" % (n, m))
        self.mini.set_counts(counts)

    def rebuild_scene(self):
        """全量重绘（演示不需差量刷新；单一流程视图口径）。

        连线全部由后端 edges 驱动（2026-09-17 细节优化 ADR-3，前端不再自行推导）：
        reference/deprecated → 泳道竖线 + 横向接入段；produce → 数据产出边（卡片↑表头）；
        dangling → 红虚线短桩 + ⚠；flow → 起止连接边（配合开始/结束标识）。
        """
        self.scene.clear()
        self.step_items = {}
        self.table_items = {}
        self.lane_items = []
        self.access_items = []
        self.marker_items = []
        self.produce_items = []
        self.flow_items = []
        self._refresh_statuses()

        card_h = STEP_H
        row0 = ROW_CY0
        col_of = {t["key"]: j for j, t in enumerate(self._tables)}
        row_of = {s["key"]: i for i, s in enumerate(self._steps)}
        content = QRectF()                     # 精确内容包围盒（不依赖 boundingRect 幻影边距）

        # 步骤几何（missing 取后端 missing_refs，不再前端自算——消除双算漂移）
        step_info = {}
        for i, s in enumerate(self._steps):
            inputs = ([s["target_table"]] if s.get("target_table") in col_of else [])
            inputs += [k for k in (s.get("extra_inputs") or []) if k in col_of]
            anchor = s.get("output_table") if s.get("output_table") in col_of else (inputs[0] if inputs else None)
            acol = col_of.get(anchor, 0)
            ccx = COL_CX0 + COL_DX * acol
            cyc = row0 + ROW_DX * i
            rect = QRectF(ccx - STEP_W / 2, cyc - card_h / 2, STEP_W, card_h)
            k = len(inputs)
            ride = (k == 1 and col_of.get(inputs[0]) == acol) if k else False
            step_info[s["key"]] = {"step": s, "inputs": inputs, "ccx": ccx, "cyc": cyc,
                                   "rect": rect, "k": k, "ride": ride,
                                   "config_state": s.get("config_state", "ok"),
                                   "missing": list(s.get("missing_refs") or [])}
            content = content.united(rect.adjusted(0, 0, 0, 8))      # 底部外扩容纳失败气泡
            if s["key"] in self._fail:                               # 失败气泡
                content = content.united(QRectF(ccx - 115, rect.bottom() + 5, 230, 22))

        # 数据引用边（reference / deprecated）→ 泳道竖线
        # 消费关系来自后端边列表（单一事实源）；表被弃用时整条转 deprecated 灰虚线样式
        dep_tables = {e["from"] for e in self._edges if e["type"] == "deprecated"}
        ref_edges = [e for e in self._edges if e["type"] in ("reference", "deprecated")]
        consumers = {t["key"]: [] for t in self._tables}
        for e in ref_edges:
            info = step_info.get(e["to"])
            if info is None or e["from"] not in consumers:
                continue
            # 端口序号 = 该表在步骤输入序列中的位置（同表被同一步骤重复引用属异常数据，
            # 此时按首个端口位处理）
            idx = info["inputs"].index(e["from"]) if e["from"] in info["inputs"] else 0
            consumers[e["from"]].append((e["to"], idx))
        for t in self._tables:
            cons = consumers[t["key"]]
            if not cons:
                continue
            etype = "deprecated" if t["key"] in dep_tables else "reference"
            x = COL_CX0 + COL_DX * col_of[t["key"]]
            if t.get("is_input"):
                y0 = HEADER_BOTTOM
            else:
                pr = row_of.get(t.get("producer_step"))
                y0 = (row0 + ROW_DX * pr + card_h / 2 + 2) if pr is not None else HEADER_BOTTOM
            taps = []
            for skey, idx in cons:
                info = step_info[skey]
                if info["ride"]:
                    taps.append((info["rect"].top() - 2, True, skey))
                else:
                    py = info["cyc"] + (idx - (info["k"] - 1) / 2) * STACK_SP
                    taps.append((py, False, skey))
            y1, ride_last, _last = max(taps, key=lambda tp: tp[0])
            color = LANE_IN if t.get("is_input") else LANE_DEV
            lane = LaneItem(x, y0, y1, color, ride_last, t["key"],
                            [c[0] for c in cons], edge_type=etype)
            lane.setZValue(-5)
            self.scene.addItem(lane)
            self.lane_items.append(lane)
            content = content.united(QRectF(x - 5, y0, 10, y1 - y0 + 2))

        # 数据引用边的横向接入段（骑线步骤无接入段，由泳道末端箭头承载）
        for e in ref_edges:
            info = step_info.get(e["to"])
            if info is None or info["ride"] or e["from"] not in col_of:
                continue
            idx = info["inputs"].index(e["from"]) if e["from"] in info["inputs"] else 0
            sx = COL_CX0 + COL_DX * col_of[e["from"]]
            py = info["cyc"] + (idx - (info["k"] - 1) / 2) * STACK_SP
            ex = info["rect"].left() if sx < info["ccx"] else info["rect"].right()
            if abs(ex - sx) < 1:
                continue
            acc = AccessItem(sx, py, ex, e["from"], e["to"], edge_type=e["type"])
            acc.setZValue(-3)
            self.scene.addItem(acc)
            self.access_items.append(acc)
            content = content.united(QRectF(min(sx, ex) - 5, py - 5, abs(ex - sx) + 10, 10))

        # 数据产出边（步骤 → 顶部操作表）：绿色竖直向上 + 标签"新表/复制新表"
        # x 固定为卡片顶边右锚点 ccx+ANCHOR_DX（不与派生表泳道 ccx 共线，避免重叠）
        for e in self._edges:
            if e["type"] != "produce":
                continue
            info = step_info.get(e["from"])
            if info is None or e["to"] not in col_of:
                continue
            x = info["ccx"] + ANCHOR_DX
            y_bot = info["rect"].top()
            y_top = HEADER_BOTTOM
            if y_bot - y_top < FLOW_LEN + 4:      # 卡片紧贴表头时保底留出箭头空间
                y_top = y_bot - (FLOW_LEN + 4)
            pe = ProduceEdgeItem(x, y_top, y_bot, e.get("label"), e["from"], e["to"])
            pe.setZValue(EDGE_Z)                  # 低于节点：穿越同列卡片时被不透明体遮蔽
            self.scene.addItem(pe)
            self.produce_items.append(pe)
            content = content.united(QRectF(x - 8, y_top - 4, 90, y_bot - y_top + 8))

        # 表节点
        for t in self._tables:
            prod_name = ""
            if not t.get("is_input") and t.get("producer_step") in self._smap:
                prod_name = self._smap[t["producer_step"]].get("name", "")
            it = TableItem(t, col_of[t["key"]], prod_name)
            it.on_click = self.on_node_click
            it.setZValue(0)
            self.scene.addItem(it)
            self.table_items[t["key"]] = it
            tx = COL_CX0 + COL_DX * col_of[t["key"]] - TABLE_W / 2
            ty = 60 if t.get("is_input") else 78     # C5：输入表头 y=60（高 40），派生 y=78
            content = content.united(QRectF(tx, ty, TABLE_W, TABLE_H))

        # 步骤卡片
        for key, info in step_info.items():
            it = StepCardItem(info)
            it.on_click = self.on_node_click
            it.setZValue(1)
            self.scene.addItem(it)
            self.step_items[key] = it

        # 悬空输入：红虚线短桩 + ⚠（X12，绝不静默；由后端 dangling 边驱动）
        dang = {}
        for e in self._edges:
            if e["type"] == "dangling":
                dang.setdefault(e["to"], []).append(e)
        for skey, es in dang.items():
            info = step_info.get(skey)
            if info is None:
                continue
            nm = len(es)
            for im in range(nm):
                py = info["cyc"] + (im - (nm - 1) / 2) * STACK_SP
                pen = QPen(QColor(DANGLING_C), 1.5)
                pen.setStyle(Qt.DashLine)
                ln = self.scene.addLine(info["rect"].left() - 40, py,
                                        info["rect"].left() - 2, py, pen)
                ln.setZValue(-2)
                ln.setAcceptedMouseButtons(Qt.NoButton)     # 装饰图元：点击穿透
                warn = self.scene.addSimpleText("⚠", _font(11, True))
                warn.setBrush(QBrush(QColor(DANGLING_C)))
                warn.setPos(info["rect"].left() - 56, py - 8)
                warn.setZValue(-2)
                warn.setAcceptedMouseButtons(Qt.NoButton)

        # 开始/结束人话标识 + 起止连接边（P0-⑤，2026-09-17 动态化）；
        # 空流程改画空态提示（判据 not self._steps：表头仍在时 content 非 null）
        if self._steps:
            content = self._build_markers(step_info, content)
        else:
            content = self._add_empty_hint(content)

        if content.isNull():
            content = QRectF(0, 0, 400, 300)
        self._content_rect = content.normalized()
        self.scene.setSceneRect(self._content_rect.adjusted(
            -SCENE_MARGIN, -SCENE_MARGIN, SCENE_MARGIN, SCENE_MARGIN))
        self._layout = {"step_info": step_info}
        self._apply_visuals()

    def _build_markers(self, step_info, content):
        """画开始/结束标识与起止连接边，返回更新后的内容包围盒。

        调整点②（ADR-2）：装饰图元——不占布局行（row_cy 公式不变）、不可选中、
        不可删除、不进右侧面板。开始锚定首步；结束锚定 is_end 步，无则末步
        （fallback：结束步被删后仍有结束标识）。结束步失败时整体下移 END_AVOID_GAP，
        避开卡片下方 z=1 的不透明失败气泡。
        """
        first_key = self._steps[0]["key"]
        first = step_info[first_key]
        # 开始：卡片顶边左锚点（与产出边右锚点分离，避免同列重叠）
        content = self._add_marker("▶ 开始", START_C, first["ccx"] - ANCHOR_DX,
                                   first["rect"].top(), True, first_key, content)
        end_step = None
        for s in self._steps:
            if s.get("is_end"):
                end_step = s
        if end_step is None:
            end_step = self._steps[-1]
        info = step_info[end_step["key"]]
        avoid = END_AVOID_GAP if self._fail.get(end_step["key"]) else 0
        return self._add_marker("■ 结束", END_C, info["ccx"], info["rect"].bottom(),
                                False, end_step["key"], content, avoid)

    def _add_marker(self, text, color, cx, card_y, above, step_key, content, avoid=0):
        """画单个起止标识（文字 + flow 连线），并把外扩量并入内容包围盒。

        参数：
            text     -- 标识文案（"▶ 开始" / "■ 结束"）
            color    -- 标识文字与连线颜色
            cx       -- 连线所在竖直 x（开始=卡片顶边左锚点；结束=卡片底边中心）
            card_y   -- 卡片边缘 y（顶边或底边）
            above    -- True=标识在卡片上方（开始）；False=在下方（结束）
            step_key -- 关联步骤 key（供淡化/高亮联动）
            content  -- 当前内容包围盒
            avoid    -- 额外避让位移（结束标识遇失败气泡时非 0）
        """
        if above:
            y_near = card_y - FLOW_GAP - avoid       # 靠卡片一端（箭头 tip 指向卡片）
            y_far = y_near - FLOW_LEN                # 远离卡片一端
            text_y = y_far - 4 - MARKER_TEXT_H       # 文字在连线上方，互不重叠
        else:
            y_near = card_y + FLOW_GAP + avoid
            y_far = y_near + FLOW_LEN
            text_y = y_far + 4                       # 文字在连线下方
        fe = FlowEdgeItem(cx, y_far, y_near, color, step_key)
        fe.setZValue(EDGE_Z)
        self.scene.addItem(fe)
        self.flow_items.append(fe)
        it = QGraphicsSimpleTextItem(text)
        it.setFont(_font(12, True))
        it.setBrush(QBrush(QColor(color)))
        it.setZValue(2)
        it.setAcceptedMouseButtons(Qt.NoButton)      # 装饰图元：点击穿透（死点根治）
        tw = it.boundingRect().width()
        if tw <= 0:                                  # offscreen 不渲染文字，按字数估算
            tw = len(text) * 12
        it.setPos(cx - tw / 2, text_y)
        self.scene.addItem(it)
        self.marker_items.append((step_key, it))
        half = max(45.0, tw / 2 + 6)                 # 外扩半宽（覆盖文字与连线）
        return content.united(QRectF(cx - half, text_y - 2, half * 2, MARKER_TEXT_H + 8))

    def _add_empty_hint(self, content):
        """空流程提示（无步骤时画布不留全白，给文职用户下一步动作指引）。"""
        if self._tables:
            cx = COL_CX0 + COL_DX * (len(self._tables) - 1) / 2
            cy = HEADER_BOTTOM + 60
        else:
            cx, cy = 200.0, 150.0
        it = QGraphicsSimpleTextItem(EMPTY_HINT)
        it.setFont(_font(12))
        it.setBrush(QBrush(QColor("#888888")))
        it.setZValue(2)
        it.setAcceptedMouseButtons(Qt.NoButton)
        tw = it.boundingRect().width()
        if tw <= 0:                                  # offscreen 不渲染文字，按字数估算
            tw = len(EMPTY_HINT) * 12
        it.setPos(cx - tw / 2, cy)
        self.scene.addItem(it)
        return content.united(QRectF(cx - tw / 2 - 4, cy - 2, tw + 8, MARKER_TEXT_H + 6))

    # ---------------- 视觉状态（选中高亮）----------------
    def _apply_visuals(self):
        """按选中态刷新节点/边的高亮与淡化（§5.3 联动表）。

        高亮判定统一为"任一命中即高亮"：步骤选中 → 其引用边/产出边/悬空边/起止边；
        表选中 → 其泳道 + 引用它的接入段 + 产出它的那条产出边。
        淡化仅在选中步骤时生效（与既有行为一致，避免选表时整图变淡）。
        """
        sel_kind, sel_key = self.selected or (None, None)
        sel_step = sel_key if sel_kind == "step" else None
        sel_table = sel_key if sel_kind == "table" else None
        related = set()
        if sel_step:
            info = self._layout["step_info"].get(sel_step)
            if info:
                related = set(info["inputs"])
                outk = info["step"].get("output_table")
                if outk:
                    related.add(outk)

        for key, it in self.step_items.items():
            it.status = self._statuses.get(key, "pending")
            it.fail_reason = self._fail.get(key) or ""
            it.selected = (sel_kind == "step" and key == sel_key)
            op = 1.0
            if sel_step and key != sel_step:
                op = 0.3
            it.setOpacity(op)
            it.update()
        for key, it in self.table_items.items():
            it.focus = (sel_kind == "table" and key == sel_key) or (key in related)
            op = 1.0
            if sel_step and key not in related:
                op = 0.3
            it.setOpacity(op)
            it.update()
        for it in self.lane_items:
            it.highlight = bool((sel_step and it.table_key in related)
                                or (sel_table and it.table_key == sel_table))
            op = 1.0
            if sel_step and it.table_key not in related:
                op = 0.3
            it.setOpacity(op)
            it.update()
        for it in self.access_items:
            it.highlight = bool((sel_step and it.step_key == sel_step)
                                or (sel_table and it.table_key == sel_table))
            op = 1.0
            if sel_step and it.step_key != sel_step:
                op = 0.3
            it.setOpacity(op)
            it.update()
        for it in self.produce_items:
            it.highlight = bool((sel_step and it.step_key == sel_step)
                                or (sel_table and it.table_key == sel_table))
            op = 1.0
            if sel_step and it.step_key != sel_step:
                op = 0.3
            it.setOpacity(op)
            it.update()
        for it in self.flow_items:
            it.highlight = bool(sel_step and it.step_key == sel_step)
            op = 1.0
            if sel_step and it.step_key != sel_step:
                op = 0.3
            it.setOpacity(op)
            it.update()
        for skey, it in self.marker_items:
            op = 1.0
            if sel_step and skey != sel_step:
                op = 0.3
            it.setOpacity(op)

    # ---------------- 详情面板 ----------------
    def _detail_hint(self):
        self.detail_label.setText(
            "<div style='color:#888888;font-size:12px'>"
            "提示：点击画布中的步骤卡片或数据表查看详情。<br/><br/>"
            "支持 Ctrl+滚轮缩放、空白处拖拽平移；<br/>"
            "「模拟运行」可观看执行推进效果。</div>")

    def on_node_click(self, kind, key):
        self.selected = (kind, key)
        self._apply_visuals()
        self._show_detail(kind, key)
        self._show_panel()

    def clear_selection(self):
        self.selected = None
        self._apply_visuals()
        self._detail_hint()
        self._show_panel()

    # ---------------- 动态配置（2026-09-16：DAG 只读，配置全在右面板）----------------
    def reload_data(self):
        """从伪后端重读 DAG 并重绘（动态操作后的联动刷新入口）。"""
        d = get_dag()
        self._tables = list(d.get("tables", []))
        self._steps = list(d.get("steps", []))
        self._edges = list(d.get("edges", []))      # 边为后端单一事实源（ADR-3）
        self._tmap = {t["key"]: t for t in self._tables}
        self._smap = {s["key"]: s for s in self._steps}
        self.rebuild_scene()

    def _clear_panel(self):
        while self.panel_box.count():
            it = self.panel_box.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

    def _show_panel(self):
        """右面板三态（X9）：步骤=参数表单+删除；表=弃用操作；无选中=空。"""
        self._clear_panel()
        if not self.selected:
            return
        kind, key = self.selected
        if kind == "step":
            step = self._smap.get(key)
            if not step:
                return
            pnl = ParamPanel(self)
            pnl.build(step, self._tables)
            pnl.saved.connect(lambda f, k=key: self.on_params_saved(k, f))
            self.panel_box.addWidget(pnl)
            btn = QPushButton("删除此步骤")
            btn.clicked.connect(lambda _c, k=key: self.on_delete_step(k))
            self.panel_box.addWidget(btn)
        else:
            t = self._tmap.get(key)
            if not t:
                return
            dep = bool(t.get("deprecated"))
            btn = QPushButton("恢复使用" if dep else "弃用此表")
            btn.clicked.connect(lambda _c, k=key, f=dep: self.on_deprecate(k, not f))
            self.panel_box.addWidget(btn)

    def on_add_step(self, op):
        """注册表驱动插入新步骤（锚点=当前选中态，定案 1/5/6）。"""
        key = add_step(op, self.selected)
        if not key:
            return
        self.reload_data()
        self.selected = ("step", key)      # 插入位置高亮=选中新步骤
        self._apply_visuals()
        self._show_detail("step", key)
        self._show_panel()

    def on_delete_step(self, key):
        name = self._smap.get(key, {}).get("name", key)
        ret = QMessageBox.question(
            self, "删除步骤",
            "确定要删除『%s』这一步吗？删除后它产生的数据表也会消失。" % name,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret != QMessageBox.Yes:
            return
        remove_step(key)
        self.selected = None
        self.reload_data()
        self._detail_hint()
        self._show_panel()

    def on_params_saved(self, key, fields):
        ok, _state, missing = update_params(key, fields)
        self.reload_data()
        self.selected = ("step", key)
        self._apply_visuals()
        self._show_detail("step", key)
        self._show_panel()
        if not ok:
            for i in range(self.panel_box.count()):
                w = self.panel_box.itemAt(i).widget()
                if isinstance(w, ParamPanel):
                    w.show_errors(["缺少：%s" % m for m in missing])

    def on_deprecate(self, key, flag):
        deprecate_table(key, flag)
        self.reload_data()
        self.selected = ("table", key)
        self._apply_visuals()
        self._show_detail("table", key)
        self._show_panel()

    def _tname(self, key):
        """表 key → 业务名（找不到时回退 key 本身）。"""
        t = self._tmap.get(key)
        return t.get("display", key) if t else key

    def _sname(self, key):
        """步骤 key → 操作中文名（找不到时回退 key 本身）。"""
        s = self._smap.get(key)
        return s.get("name", key) if s else key

    def _edge_summary(self, kind, key):
        """连线说明（人话文本）：承接原画布色卡说明区的解释职能（ADR-4 第 3 层补偿）。

        画布不再有常驻色卡说明区，节点/边的语义在此按当前边列表逐条说明，
        使无技术背景用户点任一节点即可读懂"读什么、产什么、哪里有问题"。
        """
        if kind == "step":
            ins, dep_ins, outs = [], [], []
            dang = 0
            for e in self._edges:
                if e["type"] == "reference" and e["to"] == key:
                    ins.append(self._tname(e["from"]))
                elif e["type"] == "deprecated" and e["to"] == key:
                    dep_ins.append(self._tname(e["from"]))
                elif e["type"] == "produce" and e["from"] == key:
                    # 标签唯一来源=注册表 produce_label（边内 label 缺失时回查注册表）
                    lab = e.get("label") or produce_label(
                        self._smap.get(e["from"], {}).get("op_type")) or "—"
                    outs.append("%s（%s）" % (self._tname(e["to"]), lab))
                elif e["type"] == "dangling" and e["to"] == key:
                    dang += 1
            seg = ["读取：%s" % ("、".join(ins) if ins else "—")]
            if dep_ins:
                seg.append("<span style='color:#616161'>读取（已弃用）：%s</span>"
                           % "、".join(dep_ins))
            seg.append("产出：%s" % ("、".join(outs) if outs else "—（本步不产生新表）"))
            if dang:
                seg.append("<span style='color:#c62828'>输入缺失 %d 处"
                           "（画布红虚线＋⚠）</span>" % dang)
            return "；".join(seg)
        prod, cons, dep_cons = [], [], []
        for e in self._edges:
            if e["type"] == "produce" and e["to"] == key:
                prod.append("「%s」" % self._sname(e["from"]))
            elif e["type"] == "reference" and e["from"] == key:
                cons.append("「%s」" % self._sname(e["to"]))
            elif e["type"] == "deprecated" and e["from"] == key:
                dep_cons.append("「%s」" % self._sname(e["to"]))
        seg = ["来源：%s" % ("、".join(prod) if prod else "外部导入（输入表）"),
               "被引用：%s" % ("、".join(cons + dep_cons)
                              if (cons or dep_cons) else "暂无步骤使用")]
        if dep_cons:
            seg.append("<span style='color:#616161'>本表已弃用：下游引用会提示待配置</span>")
        return "；".join(seg)

    def _show_detail(self, kind, key):
        node = get_node(key)
        if kind == "step":
            src = node if (node and node.get("kind") == "step") else self._smap.get(key, {})
            st = self._statuses.get(key, src.get("status", "pending"))
            reason = self._fail.get(key) or src.get("fail_reason") or ""
            info = self._layout["step_info"].get(key)
            ins = [self._tmap[t].get("display", t) for t in (info["inputs"] if info else [])]
            outk = src.get("output_table")
            if outk and outk in self._tmap:
                out = self._tmap[outk].get("display", outk)
            elif src.get("is_end"):
                out = "导出的结果文件"
            else:
                out = "—"
            fail_line = ""
            if st == "failed" and reason:
                fail_line = "<br/>失败原因：<span style='color:#c62828'>%s</span>" % reason
            cfg = src.get("config_state", "ok")
            cfg_line = ("<br/>配置：<span style='color:%s'><b>%s</b></span>"
                        % ("#c62828" if cfg == "incomplete" else "#2e7d32",
                           "待配置（请在下方补全参数）" if cfg == "incomplete" else "已配置"))
            prm = src.get("params") or {}
            prm_line = ("<br/>参数：%s" % "；".join("%s=%s" % (k, v) for k, v in prm.items())
                        if prm else "")
            edge_line = "<br/>连线说明：%s" % self._edge_summary("step", key)
            self.detail_label.setText(
                "<div style='font-size:12px;color:#333333'>"
                "<b style='font-size:13px'>【步骤】%s</b><br/>"
                "序号：%s / %d<br/>"
                "状态：<span style='color:%s'><b>%s</b></span><br/>"
                "业务说明：%s<br/>"
                "输入表：%s<br/>"
                "输出：%s%s%s%s%s</div>"
                % (src.get("name", ""), src.get("seq", "—"), len(self._steps),
                   STATUS_DETAIL_COLOR.get(st, "#666666"), STATUS_CN.get(st, st),
                   src.get("business_desc", "—"), "、".join(ins) or "—", out,
                   cfg_line, prm_line, edge_line, fail_line))
        else:
            src = node if (node and node.get("kind") == "table") else self._tmap.get(key, {})
            is_input = bool(src.get("is_input"))
            pk = src.get("producer_step")
            if is_input:
                producer = "—（外部导入）"
            elif pk in self._smap:
                producer = self._smap[pk].get("name", pk)
            else:
                producer = "—"
            edge_line = "<br/>连线说明：%s" % self._edge_summary("table", key)
            self.detail_label.setText(
                "<div style='font-size:12px;color:#333333'>"
                "<b style='font-size:13px'>【数据表】%s</b><br/>"
                "角色：%s<br/>"
                "业务说明：%s<br/>"
                "产出步骤：%s<br/>"
                "弃用状态：%s%s</div>"
                % (src.get("display", ""), "输入表" if is_input else "结果表",
                   src.get("business_desc", "—"), producer,
                   "<span style='color:#616161'><b>已弃用</b></span>"
                   if src.get("deprecated") else "正常使用", edge_line))

    # ---------------- 工具栏交互 ----------------
    def fit_all(self):
        if self._content_rect is None:
            return
        r = self._content_rect.adjusted(-FIT_MARGIN, -FIT_MARGIN, FIT_MARGIN, FIT_MARGIN)
        self.canvas.fitInView(r, Qt.KeepAspectRatio)

    # ---------------- 模拟运行 ----------------
    def on_simulate(self):
        """按执行序推进：重置后 pending→running→（含失败原因的步骤设为 failed 并定格）。"""
        self.sim_timer.stop()
        for s in self._steps:
            set_status(s["key"], "pending")
        self._refresh_statuses()
        self._sim_idx = 0
        self._sim_phase = "run"
        self._apply_visuals()
        self.sim_timer.start()

    def _sim_tick(self):
        if self._sim_phase == "run":
            while self._sim_idx < len(self._steps) and \
                    self._statuses.get(self._steps[self._sim_idx]["key"]) != "pending":
                self._sim_idx += 1
            if self._sim_idx >= len(self._steps):
                self.sim_timer.stop()
                self._sim_phase = None
                return
            key = self._steps[self._sim_idx]["key"]
            set_status(key, "running")
            self._refresh_statuses()
            self._sim_cur = key
            self._sim_phase = "finish"
        else:
            key = self._sim_cur
            failed = bool(self._fail.get(key))
            set_status(key, "failed" if failed else "done")
            self._refresh_statuses()
            self._sim_phase = "run"
            self._sim_idx += 1
            if failed:                       # 失败定格：停止推进
                self.sim_timer.stop()
                self._sim_phase = None
        self._apply_visuals()
        if self.selected:
            self._show_detail(*self.selected)


def main():
    app = QApplication(sys.argv)
    win = DagViewerWindow()
    win.resize(1280, 800)
    win.show()
    for _ in range(5):
        app.processEvents()
    win.fit_all()
    for _ in range(3):
        app.processEvents()
    if _OFFSCREEN:
        art = _ROOT / "artifacts"
        art.mkdir(parents=True, exist_ok=True)
        p1 = art / "w03-preview.png"
        pix1 = win.canvas.viewport().grab()
        ok1 = pix1.save(str(p1))
        print("[offscreen] w03-preview.png save=%s size=%dx%d" % (ok1, pix1.width(), pix1.height()))
        print("[offscreen] steps=%d tables=%d lanes=%d access=%d produce=%d flow=%d markers=%d"
              % (len(win._steps), len(win._tables), len(win.lane_items),
                 len(win.access_items), len(win.produce_items), len(win.flow_items),
                 len(win.marker_items)))
        return 0                             # 导出后退出，不进事件循环
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
