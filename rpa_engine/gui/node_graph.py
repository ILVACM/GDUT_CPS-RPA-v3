"""
rpa_engine/gui/node_graph.py

v3.1 节点图渲染模块（2026-09-20 M-b 重写）：QGraphicsView / QGraphicsScene
工作流可视化。蓝本＝`_temp/DAG-rebuild/SampleCode/frontend/dag_viewer.py`
（M1-M12 条目逐项对照移植）；五类边由 ``gui.graph_edges`` 单一事实源驱动
（ADR-3），渲染层不自行推导连线关系：

- reference / deprecated → LaneItem 纵向泳道 + AccessItem 横向接入段
- produce → ProduceEdgeItem（卡片顶边右锚点竖直向上至表头底线，绿色 +
  「新表 / 复制新表」标签）
- dangling → 红虚线短桩 + ⚠（悬空输入绝不静默）
- flow → FlowEdgeItem 起止连接边（配合「▶ 开始 / ■ 结束」装饰标识，ADR-2）

节点：
- TableItem：数据表节点 160×40（输入表 y=60 / 派生表 y=78 错位；角标三态
  「输入表 / 结果表 / 已弃用」；弃用灰填充虚线边；派生表虚线边 +「由「X」生成」）
- StepCardItem：步骤卡片 140×70（序号徽章 + 操作中文名 + 业务副标题
  （STEP_DESC 静态映射，D-2=a）+ 角标（输入缺失红 / 待配置橙）+ 失败人话气泡）

交互（正本 §1.2）：Ctrl+滚轮缩放（钳制 [0.40, 2.50] 锚定鼠标）、空白左键
拖拽平移（按缩放比换算）、点击节点选中（关联边高亮、无关节点淡化）、
空白点击清除选中。画布严格只读：全部边 / 标识图元
``setAcceptedMouseButtons(Qt.NoButton)``，点击穿透为空白语义。

配色零字面色：全部引用 ``gui.styles`` GRAPH_* / COLOR_*（节点态 + 图态
配色唯一来源，M2/M20）。
"""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from loguru import logger
from PyQt5.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import (
    QBrush, QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen,
    QPolygonF,
)
from PyQt5.QtWidgets import (
    QGraphicsItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView,
)

from gui import styles
from gui.graph_edges import EdgeSpec, TableSpec
from gui.models import step_desc

# ---------------------------------------------------------------------------
# 布局常量（M1；口径＝SampleCode CONTRACTS §4 单一视图定稿）
# ---------------------------------------------------------------------------
COL_CX0: int = 120        # col_cx(j) = 120 + 240·j
COL_DX: int = 240
HEADER_BOTTOM: int = 118  # 表头底线
TABLE_NODE_W: int = 160
TABLE_NODE_H: int = 40
TABLE_TOP_IN: int = 60    # 输入表主体 y（调序条取消后上移，C1/C5）
TABLE_TOP_DEV: int = 78   # 派生表主体 y（与输入表错位示"由步骤产出"）
STEP_NODE_W: int = 140
STEP_NODE_H: int = 70     # 卡片需容纳徽章+标题+业务副标题（P0-②）
ROW_CY0: int = 193        # row_cy(r) = 193 + 100·r
ROW_DX: int = 100
STACK_SP: int = 16        # 多输入端口纵向堆叠间距
ARROW_L: float = 9.0      # 箭头长度
ARROW_HW: float = 4.5     # 箭头半宽
SCENE_MARGIN: int = 40    # sceneRect = 内容包围盒 ± 40
FIT_MARGIN: int = 20      # 全览外扩边距
ZOOM_MIN: float = 0.40
ZOOM_MAX: float = 2.50

# 起止标识与产出边常量（ADR-2 / 正本 §5.1）
ANCHOR_DX: int = 35       # 卡片顶边锚点偏移：flow 走 ccx-35、produce 走 ccx+35
FLOW_LEN: int = 12        # 起止连接边长度
FLOW_GAP: int = 6         # 连接边端点与卡片边缘的间隙
MARKER_TEXT_H: int = 16   # 12px bold 标识文字高度（offscreen 按此估算）
END_AVOID_GAP: int = 32   # 结束标识失败避让位移（气泡占 bottom+5..+27）
EDGE_Z: int = -4          # produce/flow 边层级（低于节点，被不透明卡片遮蔽）
EMPTY_HINT: str = "暂无步骤，请从上方功能按钮添加"


# ---------------------------------------------------------------------------
# 状态枚举与视觉词表（M2：全部引用 styles，零硬编码色值）
# ---------------------------------------------------------------------------
class NodeStatus(Enum):
    """步骤节点状态枚举."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


# 卡片填充链（failed>running>done>selected>pending）与描边链
# （selected>hovered>incomplete>状态）取值表
# R6/D5-3（P2-9）：画布步数警戒阈值（D7 裁定可调常量；超过仅告警＋
# 停用视口自动重置，不阻断操作；虚拟化/增量渲染属另行立项范围）
CANVAS_WARN_STEPS = 150

_STATUS_FILL: Dict[NodeStatus, str] = {
    NodeStatus.PENDING: styles.COLOR_PENDING,
    NodeStatus.RUNNING: styles.COLOR_RUNNING,
    NodeStatus.DONE:    styles.COLOR_DONE,
    NodeStatus.FAILED:  styles.COLOR_FAILED,
}
_STATUS_STROKE: Dict[NodeStatus, Tuple[str, float]] = {
    NodeStatus.PENDING: (styles.GRAPH_STATUS_PENDING, 1.0),
    NodeStatus.RUNNING: (styles.GRAPH_STATUS_RUNNING, 2.0),
    NodeStatus.DONE:    (styles.GRAPH_STATUS_DONE, 1.0),
    NodeStatus.FAILED:  (styles.GRAPH_STATUS_FAILED, 2.0),
}
_FILL_SELECTED: str = styles.COLOR_SELECTED
_STROKE_SELECTED: Tuple[str, float] = (styles.GRAPH_SELECTED, 2.0)
_STROKE_HOVER: Tuple[str, float] = (styles.GRAPH_SELECTED, 2.0)
_STROKE_HIGHLIGHT: Tuple[str, float] = (styles.GRAPH_SELECTED, 2.5)
_STROKE_INCOMPLETE: Tuple[str, float] = (styles.GRAPH_INCOMPLETE, 2.0)


def _font(px: int, bold: bool = False) -> QFont:
    """统一字体（微软雅黑）。"""
    f = QFont("Microsoft YaHei")
    f.setPixelSize(px)
    f.setBold(bold)
    return f


def _elide(fm: QFontMetricsF, text: str, width: int) -> str:
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


# ---------------------------------------------------------------------------
# 场景数据载体（M-b：表/步骤/边一律 ID 口径，显示名由 TableSpec.display 携带）
# ---------------------------------------------------------------------------

class GraphLayoutData:
    """描述待渲染的节点与边（2026-09-20 M-b 签名：ID 口径 + edges 驱动）。

    Attributes:
        tables: 列序数据表视图（``gui.graph_edges.TableSpec``；key=表 ID，
            display=列头显示名，含 is_input/producer_step/deprecated）。
        steps: 步骤行视图（``StepLayoutEntry``，表字段持表 ID）。
        edges: 五类边列表（``gui.graph_edges.EdgeSpec``，单一事实源；
            渲染按 type 取样式，不自行推导）。
    """

    def __init__(self, tables: List[TableSpec],
                 steps: List["StepLayoutEntry"],
                 edges: Optional[List[EdgeSpec]] = None) -> None:
        self.tables: List[TableSpec] = list(tables or [])
        self.steps: List["StepLayoutEntry"] = list(steps or [])
        self.edges: List[EdgeSpec] = list(edges or [])


class StepLayoutEntry:
    """描述一个步骤行（M-b 精简：交点圆点/分叉合并标记已删，边关系全由
    ``GraphLayoutData.edges`` 承载，本条目只保留几何定位与卡片文案所需字段）。

    Attributes:
        step_id: 引擎步骤 ID（S1/S2…）。
        step_name: 步骤名（卡片标题，操作中文名）。
        op_type: 操作类型（STEP_CATALOG 键；卡片副标题经 ``step_desc`` 查得）。
        status: 执行状态（装配时通常 PENDING；运行期经
            ``NodeGraphScene.update_step_status`` 更新）。
        input_tables: 有序输入表 ID（target 在前、额外表在后；端口序即此序）。
        output_table: 派生表 ID（可空；覆盖原表模式虽保留 ID，但数据层
            ``produces_table`` 判定不产表 → 不在 tables 列中，锚列自动回退）。
        is_end: 是否结束步（唯一性由数据层 ``graph_edges.normalize_end`` 保证；
            渲染层结束锚点＝is_end 步，无则末步 fallback，ADR-2）。
    """

    def __init__(
        self,
        step_id: str,
        step_name: str,
        op_type: str = "",
        status: NodeStatus = NodeStatus.PENDING,
        input_tables: Optional[List[str]] = None,
        output_table: Optional[str] = None,
        is_end: bool = False,
    ) -> None:
        self.step_id: str = step_id
        self.step_name: str = step_name
        self.op_type: str = op_type
        self.status: NodeStatus = status
        self.input_tables: List[str] = list(input_tables or [])
        self.output_table: Optional[str] = output_table
        self.is_end: bool = is_end


def col_cx(col: int) -> float:
    """列中心 x 坐标：``col_cx(j) = 120 + 240·j``（M6 定稿口径）。"""
    return COL_CX0 + COL_DX * col


def row_cy(row: int) -> float:
    """步骤行中心 y 坐标：``row_cy(r) = 193 + 100·r``（M6 定稿口径）。"""
    return ROW_CY0 + ROW_DX * row


def _config_state_of(entry: StepLayoutEntry, col_of: Dict[str, int],
                     dep_tables: set) -> str:
    """前端校验态投影（plan §4.4）：ok / incomplete。

    轻量口径（渲染层直算，不引入表单校验）：目标表缺失/悬空、目标表已弃用、
    额外输入表引用已弃用表 → incomplete（卡片橙描边 +「待配置」角标）；
    必填参数完整性由保存/开始执行的既有校验兜底（page._validate_all_steps
    + 引擎 validate_workflow），翻译层零额外处理。
    """
    tgt = entry.input_tables[0] if entry.input_tables else ""
    if not tgt or tgt not in col_of or tgt in dep_tables:
        return "incomplete"
    if any(t in dep_tables for t in entry.input_tables[1:]):
        return "incomplete"
    return "ok"


# ---------------------------------------------------------------------------
# 节点图元
# ---------------------------------------------------------------------------

class StepCardItem(QGraphicsItem):
    """步骤卡片 140×70（M4；蓝本 StepCardItem dag_viewer.py:127-261）。

    序号徽章 + 标题（操作中文名）+ 业务副标题（STEP_DESC[type]）+
    角标（输入缺失红 > 待配置橙）+ 失败人话气泡。
    填充链 failed>running>done>selected>pending；
    描边链 selected>hovered>incomplete>状态。
    """

    def __init__(self, info: Dict[str, Any],
                 on_click: Optional[Callable[[str, str], None]] = None) -> None:
        super().__init__()
        entry: StepLayoutEntry = info["entry"]
        self.key: str = entry.step_id
        self.seq: int = info["seq"]
        self.title: str = entry.step_name
        self.subtitle: str = step_desc(entry.op_type)
        self.rect: QRectF = info["rect"]
        self.config_state: str = info.get("config_state", "ok")
        self.missing: List[str] = list(info.get("missing", []))
        self.status: NodeStatus = entry.status
        self.fail_reason: str = ""
        self.selected: bool = False
        self.hovered: bool = False
        self._on_click = on_click
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)

    def set_status(self, status: NodeStatus, reason: str = "") -> None:
        """更新执行状态与失败原因（气泡文案），触发重绘。"""
        self.status = status
        self.fail_reason = reason if status == NodeStatus.FAILED else ""
        self.prepareGeometryChange()
        self.update()

    def boundingRect(self) -> QRectF:
        # 左右各留 55 容纳失败气泡（气泡可比卡片宽），底部留 48 容纳气泡
        return self.rect.adjusted(-55, -8, 55, 48)

    def _bubble_rect(self) -> QRectF:
        if self.status != NodeStatus.FAILED or not self.fail_reason:
            return QRectF()
        fm = QFontMetricsF(_font(10))
        w = fm.width(self.fail_reason)
        if w <= 0:
            w = len(self.fail_reason) * 10
        bw = min(w + 16, 230)
        return QRectF(self.rect.center().x() - bw / 2,
                      self.rect.bottom() + 5, bw, 22)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self.rect.adjusted(-2, -2, 2, 2))
        b = self._bubble_rect()
        if not b.isNull():
            path.addRect(b.adjusted(-2, -2, 2, 2))
        return path

    def mousePressEvent(self, event) -> None:
        if self._on_click:
            self._on_click("step", self.key)
        event.accept()

    def hoverEnterEvent(self, event) -> None:
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event) -> None:
        self.hovered = False
        self.update()

    def paint(self, p: QPainter, option, widget=None) -> None:
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect
        # 填充链：失败>运行中>完成>选中>常态（正本 §5.8）
        if self.status in (NodeStatus.FAILED, NodeStatus.RUNNING,
                           NodeStatus.DONE):
            fill = _STATUS_FILL[self.status]
        elif self.selected:
            fill = _FILL_SELECTED
        else:
            fill = _STATUS_FILL[NodeStatus.PENDING]
        # 描边链：选中>悬停>待配置(incomplete)>状态>常态
        if self.selected:
            border, bw = _STROKE_SELECTED
        elif self.hovered:
            border, bw = _STROKE_HOVER
        elif self.config_state == "incomplete":
            border, bw = _STROKE_INCOMPLETE
        else:
            border, bw = _STATUS_STROKE.get(
                self.status, _STATUS_STROKE[NodeStatus.PENDING])
        p.setBrush(QBrush(QColor(fill)))
        p.setPen(QPen(QColor(border), bw))
        p.drawRoundedRect(r, 8, 8)

        # 序号徽章（P0-②）
        badge = QRectF(r.left() + 5, r.top() + 5, 18, 18)
        p.setBrush(QBrush(QColor(styles.GRAPH_SELECTED)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(badge)
        p.setFont(_font(10, True))
        p.setPen(QColor(styles.GRAPH_TEXT_ON_FILL))
        p.drawText(badge, Qt.AlignCenter, str(self.seq))

        # 标题行 = 操作中文名
        fm = QFontMetricsF(_font(13, True))
        title = _elide(fm, self.title, int(r.width() - 32))
        p.setFont(_font(13, True))
        p.setPen(QColor(styles.GRAPH_CARD_TITLE))
        p.drawText(QRectF(r.left() + 27, r.top() + 2, r.width() - 32, 22),
                   Qt.AlignVCenter | Qt.AlignLeft, title)

        # 副标题行 = 业务说明（12px，双行省略）
        if self.subtitle:
            p.setFont(_font(12))
            p.setPen(QColor(styles.GRAPH_CARD_SUBTITLE))
            tr = QRectF(r.left() + 6, r.top() + 27,
                        r.width() - 12, r.height() - 32)
            fm2 = QFontMetricsF(_font(12))
            sw = fm2.width(self.subtitle)
            if 0 < sw <= tr.width():
                p.drawText(tr, Qt.AlignVCenter | Qt.AlignLeft, self.subtitle)
            else:
                sub2 = (fm2.elidedText(self.subtitle, Qt.ElideRight,
                                       tr.width() * 2 - 8) if sw > 0
                        else self.subtitle)
                p.drawText(tr, Qt.AlignTop | Qt.AlignLeft | Qt.TextWordWrap,
                           sub2)

        # 角标：悬空输入（红）> 待配置（橙）
        if self.missing or self.config_state == "incomplete":
            if self.missing:
                tag_txt, tag_bg = "输入缺失", styles.GRAPH_DANGLING
            else:
                tag_txt, tag_bg = "待配置", styles.GRAPH_INCOMPLETE
            tagr = QRectF(r.right() - 52, r.top() + 3, 48, 14)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(tag_bg)))
            p.drawRoundedRect(tagr, 2, 2)
            p.setFont(_font(9, True))
            p.setPen(QColor(styles.GRAPH_TEXT_ON_FILL))
            p.drawText(tagr, Qt.AlignCenter, tag_txt)

        # 失败人话气泡（P0-⑥）
        if self.status == NodeStatus.FAILED:
            bub = self._bubble_rect()
            if not bub.isNull():
                p.setBrush(QBrush(QColor(styles.GRAPH_BUBBLE_BG)))
                p.setPen(QPen(QColor(styles.GRAPH_BUBBLE_BORDER), 1))
                p.drawRoundedRect(bub, 6, 6)
                fm3 = QFontMetricsF(_font(10))
                txt = _elide(fm3, self.fail_reason, int(bub.width() - 10))
                p.setFont(_font(10))
                p.setPen(QColor(styles.GRAPH_BUBBLE_BORDER))
                p.drawText(bub, Qt.AlignCenter, txt)


class TableItem(QGraphicsItem):
    """数据表节点 160×40（M3；蓝本 TableItem dag_viewer.py:264-338）。

    输入表 y=60 / 派生表 y=78 错位（示"由步骤产出"）；角标三态
    「输入表 / 结果表 / 已弃用」；弃用＝灰填充 + 虚线边；派生表＝虚线边 +
    底部「由「X」生成」小字；hover/focus 换色。调序按钮已删除（C1 裁定）。
    """

    def __init__(self, spec: TableSpec, col: int, producer_name: str = "",
                 on_click: Optional[Callable[[str, str], None]] = None) -> None:
        super().__init__()
        self.key: str = spec.key
        self.display: str = spec.display
        self.is_input: bool = bool(spec.is_input)
        self.deprecated: bool = bool(spec.deprecated)
        self.producer_name: str = producer_name
        self.focus: bool = False
        self.hovered: bool = False
        self._on_click = on_click
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        self.x: float = col_cx(col) - TABLE_NODE_W / 2
        self.ty: float = TABLE_TOP_IN if self.is_input else TABLE_TOP_DEV
        self.body = QRectF(self.x, self.ty, TABLE_NODE_W, TABLE_NODE_H)
        self._r = self.body.adjusted(-6, -4, 6, 4)
        # 输入表物理名 tooltip（2026-09-21 审计 P9c；构造期设置跨 rebuild
        # 保持；派生表 spec.sqlite_table 为空，执行期经 set_output_tables 回写）
        if spec.sqlite_table:
            self.setToolTip(f"物理表: {spec.sqlite_table}")

    def boundingRect(self) -> QRectF:
        return self._r

    def mousePressEvent(self, event) -> None:
        if self._on_click:
            self._on_click("table", self.key)
        event.accept()

    def hoverEnterEvent(self, event) -> None:
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event) -> None:
        self.hovered = False
        self.update()

    def paint(self, p: QPainter, option, widget=None) -> None:
        p.setRenderHint(QPainter.Antialiasing)
        # 主体（弃用：灰填充+虚线边）
        if self.deprecated:
            fill = styles.GRAPH_DEPRECATED_FILL
            pen = QPen(QColor(styles.GRAPH_DEPRECATED), 1.0)
            pen.setStyle(Qt.DashLine)
        else:
            fill = styles.GRAPH_TABLE_HOVER if self.hovered \
                else styles.GRAPH_TABLE_FILL
            pen = QPen(
                QColor(styles.GRAPH_TABLE_FOCUS if self.focus
                       else styles.GRAPH_TABLE_STROKE),
                2.0 if self.focus else 1.0)
            if not self.is_input:
                pen.setStyle(Qt.DashLine)
        p.setBrush(QBrush(QColor(fill)))
        p.setPen(pen)
        p.drawRoundedRect(self.body, 6, 6)

        # 角标（弃用表显示「已弃用」，P0-④）
        tag = ("已弃用" if self.deprecated
               else ("输入表" if self.is_input else "结果表"))
        tagr = QRectF(self.x + 3, self.ty + 2,
                      max(34, len(tag) * 9 + 10), 13)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(styles.GRAPH_DEPRECATED_TAG if self.deprecated
                                 else styles.GRAPH_TABLE_STROKE)))
        p.drawRoundedRect(tagr, 2, 2)
        p.setFont(_font(9, True))
        p.setPen(QColor(styles.GRAPH_TEXT_ON_FILL))
        p.drawText(tagr, Qt.AlignCenter, tag)

        # 主文字 = display（派生表底部附「由「X」生成」小字）
        fm = QFontMetricsF(_font(11, True))
        disp = _elide(fm, self.display, TABLE_NODE_W - 10)
        p.setFont(_font(11, True))
        p.setPen(QColor(styles.GRAPH_TEXT_ON_FILL))
        if not self.is_input:
            p.drawText(QRectF(self.x, self.ty + 15, TABLE_NODE_W, 14),
                       Qt.AlignCenter, disp)
            p.setFont(_font(9))
            p.setPen(QColor(styles.GRAPH_TABLE_SUBTEXT))
            p.drawText(QRectF(self.x, self.ty + 28, TABLE_NODE_W, 11),
                       Qt.AlignCenter, f"由「{self.producer_name}」生成")
        else:
            p.drawText(QRectF(self.x, self.ty + 15, TABLE_NODE_W, 22),
                       Qt.AlignCenter, disp)


# ---------------------------------------------------------------------------
# 边图元（M5：四边图元替换旧交点圆点/独立箭头/起止圆点；全部只读穿透）
# ---------------------------------------------------------------------------

def _edge_style(edge_type: str, color: str, width: float,
                highlight: bool) -> Tuple[str, float, bool]:
    """按边类型解析连线样式，返回 (颜色, 线宽, 是否虚线)。

    样式优先级（正本 §6.4）：高亮 > deprecated（弃用引用边，灰虚线）> 常态色
    实线。dangling 为独立图元（红虚线短桩），不与本链路竞争。
    """
    if highlight:
        return _STROKE_HIGHLIGHT[0], _STROKE_HIGHLIGHT[1], False
    if edge_type == "deprecated":
        return styles.GRAPH_DEPRECATED, 1.5, True
    return color, width, False


class LaneItem(QGraphicsItem):
    """数据引用边的纵向段（泳道）：输入列灰 / 派生列蓝，宽 2.0；
    末位骑线消费者处画下向箭头；表被弃用时整条转灰虚线（deprecated 样式）。"""

    def __init__(self, x: float, y0: float, y1: float, color: str,
                 arrow: bool, table_key: str, step_keys: List[str],
                 edge_type: str = "reference") -> None:
        super().__init__()
        self.x = x
        self.y0 = min(y0, y1)
        self.y1 = max(y0, y1)
        self.color = color
        self.arrow = arrow
        self.table_key = table_key
        self.step_keys = step_keys
        self.edge_type = edge_type       # reference / deprecated（边契约驱动）
        self.highlight = False
        self._r = QRectF(x - 8, self.y0 - 2, 16, self.y1 - self.y0 + 14)

    def boundingRect(self) -> QRectF:
        return self._r

    def paint(self, p: QPainter, option, widget=None) -> None:
        p.setRenderHint(QPainter.Antialiasing)
        col, wd, dash = _edge_style(self.edge_type, self.color, 2.0,
                                    self.highlight)
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
    """数据引用边的横向接入段：源列中心 → 卡片左/右缘，宽 1.5，
    末端箭头（长 9 半宽 4.5，M9：箭头并入边图元 paint，不再独立浮层）。"""

    def __init__(self, x0: float, y: float, x1: float, table_key: str,
                 step_key: str, edge_type: str = "reference") -> None:
        super().__init__()
        self.x0, self.y, self.x1 = x0, y, x1
        self.table_key = table_key
        self.step_key = step_key
        self.edge_type = edge_type       # reference / deprecated（边契约驱动）
        self.dir = 1 if x1 >= x0 else -1
        self.highlight = False
        self._r = QRectF(min(x0, x1) - 5, y - 6, abs(x1 - x0) + 10, 12)

    def boundingRect(self) -> QRectF:
        return self._r

    def paint(self, p: QPainter, option, widget=None) -> None:
        p.setRenderHint(QPainter.Antialiasing)
        col, wd, dash = _edge_style(self.edge_type, styles.GRAPH_ACCESS, 1.5,
                                    self.highlight)
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
    """数据产出边：步骤卡片顶边右锚点（ccx+35）竖直向上连到操作表表头底线。

    与数据引用边（自上而下 / 横向汇入卡片）方向相反 → 无色卡说明区时靠
    "方向 + 绿色 + 文字标签"三重区分；「数据表复制」标签为"复制新表"，
    一眼看出这里长出新分支（ADR-4）。画布只读：Qt.NoButton 点击穿透。
    """

    def __init__(self, x: float, y_top: float, y_bottom: float,
                 label: Optional[str], step_key: str, table_key: str) -> None:
        super().__init__()
        self.x = x
        self.y_top = min(y_top, y_bottom)        # 上端 = 表头底线（箭头 tip）
        self.y_bottom = max(y_top, y_bottom)     # 下端 = 卡片顶边
        self.label = label or ""
        self.step_key = step_key
        self.table_key = table_key
        self.highlight = False
        self.setAcceptedMouseButtons(Qt.NoButton)
        # 包围盒：含箭头与右侧标签衬底（标签宽按字数估算，offscreen 兜底）
        lab_w = (len(self.label) * 10 + 14) if self.label else 0
        self._r = QRectF(x - 8, self.y_top - ARROW_L - 2,
                         16 + lab_w,
                         (self.y_bottom - self.y_top) + ARROW_L + 6)

    def boundingRect(self) -> QRectF:
        return self._r

    def paint(self, p: QPainter, option, widget=None) -> None:
        p.setRenderHint(QPainter.Antialiasing)
        if self.highlight:
            col, wd = _STROKE_HIGHLIGHT
        else:
            col, wd = styles.GRAPH_PRODUCE, 2.0
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
        if tw <= 0:                              # offscreen 按字数估算
            tw = len(self.label) * 10
        midy = (self.y_top + self.y_bottom) / 2
        box = QRectF(self.x + 5, midy - 7, tw + 8, 14)
        p.setPen(QPen(QColor(col), 1))
        p.setBrush(QBrush(QColor(styles.GRAPH_TEXT_ON_FILL)))
        p.drawRoundedRect(box, 3, 3)
        p.setFont(_font(9, True))
        p.setPen(QColor(styles.GRAPH_PRODUCE_LABEL if not self.highlight
                        else col))
        p.drawText(box, Qt.AlignCenter, self.label)


class FlowEdgeItem(QGraphicsItem):
    """起止连接边：开始标识→首步卡片顶边左锚点 / 末步卡片底边→结束标识。

    仅此两段（不画步骤→步骤的流程控制边，执行顺序由序号徽章 + 行序承载，
    ADR-3）。画布只读：Qt.NoButton 点击穿透。
    """

    def __init__(self, x: float, y_far: float, y_near: float, color: str,
                 step_key: str) -> None:
        super().__init__()
        self.x = x
        self.y_far = min(y_far, y_near)          # 远离卡片的一端
        self.y_near = max(y_far, y_near)         # 靠近卡片的一端（箭头 tip）
        self.color = color
        self.step_key = step_key
        self.highlight = False
        self.setAcceptedMouseButtons(Qt.NoButton)
        self._r = QRectF(x - 8, self.y_far - 2, 16,
                         (self.y_near - self.y_far) + 6)

    def boundingRect(self) -> QRectF:
        return self._r

    def paint(self, p: QPainter, option, widget=None) -> None:
        p.setRenderHint(QPainter.Antialiasing)
        if self.highlight:
            col, wd = _STROKE_HIGHLIGHT
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


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------

class NodeGraphScene(QGraphicsScene):
    """场景管理（M7：消费 ``GraphLayoutData.edges`` 的 11 步重绘）。

    点击转发：步骤卡片 → ``step_selected(step_id)``；表节点 →
    ``table_selected(table_id)``（M-b 起为表 ID，非显示名）；空白 →
    ``no_selection()``。选中态在场景内实现高亮/淡化联动（正本 §5.3）。

    Signals:
        step_selected(str):  点击步骤卡片（step_id）。
        table_selected(str): 点击表节点（表 ID）。
        no_selection():      点击空白 / 清除选中。
    """

    step_selected = pyqtSignal(str)
    table_selected = pyqtSignal(str)
    no_selection = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._step_items: Dict[str, StepCardItem] = {}
        self._table_items: Dict[str, TableItem] = {}
        self._lane_items: List[LaneItem] = []
        self._access_items: List[AccessItem] = []
        self._produce_items: List[ProduceEdgeItem] = []
        self._flow_items: List[FlowEdgeItem] = []
        self._marker_items: List[Tuple[str, QGraphicsSimpleTextItem]] = []
        self._step_info: Dict[str, Dict[str, Any]] = {}
        self._step_order: List[str] = []
        self._edges: List[EdgeSpec] = []
        self._content_rect: Optional[QRectF] = None
        self._selected: Optional[Tuple[str, str]] = None   # (kind, key)
        self._output_tables: Dict[str, str] = {}           # 执行期回写映射

    @property
    def content_rect(self) -> Optional[QRectF]:
        """精确内容包围盒（供视图全览；不含 SCENE_MARGIN）。"""
        return self._content_rect

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def rebuild(self, data: GraphLayoutData) -> None:
        """全量重绘（蓝本 rebuild_scene dag_viewer.py:759-938，11 步）。

        连线全部由 ``data.edges`` 驱动（ADR-3，前端不再自行推导）：
        reference/deprecated → 泳道竖线 + 横向接入段；produce → 数据产出边；
        dangling → 红虚线短桩 + ⚠；flow → 起止连接边（配合开始/结束标识）。
        """
        self.clear()
        self._step_items = {}
        self._table_items = {}
        self._lane_items = []
        self._access_items = []
        self._produce_items = []
        self._flow_items = []
        self._marker_items = []
        self._step_info = {}
        self._edges = list(data.edges)
        self._content_rect = None

        tables = list(data.tables)
        steps = list(data.steps)
        col_of: Dict[str, int] = {t.key: j for j, t in enumerate(tables)}
        row_of: Dict[str, int] = {e.step_id: i for i, e in enumerate(steps)}
        smap: Dict[str, StepLayoutEntry] = {e.step_id: e for e in steps}
        self._step_order = [e.step_id for e in steps]
        content = QRectF()            # 精确内容包围盒（不依赖幻影边距）

        dep_tables = {e.src for e in self._edges if e.type == "deprecated"}
        # R6/D5-1（P2-9）：dangling 边按 dst 预分组提出循环——原循环内
        # 全边表过滤为 O(S×E)，同函数 dep_tables/ref_edges 已外提，属漏改
        missing_by_dst: Dict[str, List[str]] = {}
        for e in self._edges:
            if e.type == "dangling":
                missing_by_dst.setdefault(e.dst, []).append(e.src)
        if len(steps) > CANVAS_WARN_STEPS:
            logger.warning(
                f"[node_graph] 画布规模较大：{len(steps)} 步（警戒阈值 "
                f"{CANVAS_WARN_STEPS}），全量重建耗时将上升")

        # -- 1. 步骤几何（missing 取 dangling 边，消除前端双算漂移）--
        for i, entry in enumerate(steps):
            inputs = [t for t in entry.input_tables if t in col_of]
            anchor = (entry.output_table
                      if entry.output_table and entry.output_table in col_of
                      else (inputs[0] if inputs else None))
            acol = col_of.get(anchor, 0)
            ccx = col_cx(acol)
            cyc = row_cy(i)
            rect = QRectF(ccx - STEP_NODE_W / 2, cyc - STEP_NODE_H / 2,
                          STEP_NODE_W, STEP_NODE_H)
            k = len(inputs)
            ride = bool(k == 1 and col_of.get(inputs[0]) == acol) if k \
                else False
            missing = missing_by_dst.get(entry.step_id, [])
            self._step_info[entry.step_id] = {
                "entry": entry, "seq": i + 1, "inputs": inputs,
                "ccx": ccx, "cyc": cyc, "rect": rect, "k": k, "ride": ride,
                "config_state": _config_state_of(entry, col_of, dep_tables),
                "missing": missing,
            }
            content = content.united(rect.adjusted(0, 0, 0, 8))
            if entry.status == NodeStatus.FAILED:      # 失败气泡外扩
                content = content.united(
                    QRectF(ccx - 115, rect.bottom() + 5, 230, 22))

        # -- 2. reference/deprecated → 泳道竖线（M8：延伸至最深消费者，
        #       无 merge 提前截断；消费关系来自边列表单一事实源）--
        ref_edges = [e for e in self._edges
                     if e.type in ("reference", "deprecated")]
        consumers: Dict[str, List[Tuple[str, int]]] = {t.key: []
                                                       for t in tables}
        for e in ref_edges:
            info = self._step_info.get(e.dst)
            if info is None or e.src not in consumers:
                continue
            # 端口序号 = 该表在步骤输入序列中的位置（同表重复引用属异常数据，
            # 按首个端口位处理）
            idx = info["inputs"].index(e.src) if e.src in info["inputs"] else 0
            consumers[e.src].append((e.dst, idx))
        for t in tables:
            cons = consumers[t.key]
            if not cons:
                continue                    # 无引用不画（消除短桩）
            etype = "deprecated" if t.key in dep_tables else "reference"
            x = col_cx(col_of[t.key])
            if t.is_input:
                y0 = float(HEADER_BOTTOM)
            else:
                pr = row_of.get(t.producer_step or "")
                y0 = (row_cy(pr) + STEP_NODE_H / 2 + 2) if pr is not None \
                    else float(HEADER_BOTTOM)
            taps: List[Tuple[float, bool, str]] = []
            for skey, idx in cons:
                info = self._step_info[skey]
                if info["ride"]:
                    taps.append((info["rect"].top() - 2, True, skey))
                else:
                    py = info["cyc"] + (idx - (info["k"] - 1) / 2) * STACK_SP
                    taps.append((py, False, skey))
            y1, ride_last, _last = max(taps, key=lambda tp: tp[0])
            color = styles.GRAPH_LANE_IN if t.is_input else styles.GRAPH_LANE_DEV
            lane = LaneItem(x, y0, y1, color, ride_last, t.key,
                            [c[0] for c in cons], edge_type=etype)
            lane.setZValue(-5)
            self.addItem(lane)
            self._lane_items.append(lane)
            content = content.united(QRectF(x - 5, y0, 10, y1 - y0 + 2))

        # -- 3. 横向接入段（M10：骑线步骤无接入段，由泳道末端箭头承载）--
        for e in ref_edges:
            info = self._step_info.get(e.dst)
            if info is None or info["ride"] or e.src not in col_of:
                continue
            idx = info["inputs"].index(e.src) if e.src in info["inputs"] else 0
            sx = col_cx(col_of[e.src])
            py = info["cyc"] + (idx - (info["k"] - 1) / 2) * STACK_SP
            ex = info["rect"].left() if sx < info["ccx"] else info["rect"].right()
            if abs(ex - sx) < 1:
                continue
            acc = AccessItem(sx, py, ex, e.src, e.dst, edge_type=e.type)
            acc.setZValue(-3)
            self.addItem(acc)
            self._access_items.append(acc)
            content = content.united(
                QRectF(min(sx, ex) - 5, py - 5, abs(ex - sx) + 10, 10))

        # -- 4. 数据产出边（卡片顶边右锚点 ccx+35 竖直向上，绿 + 标签）--
        for e in self._edges:
            if e.type != "produce":
                continue
            info = self._step_info.get(e.src)
            if info is None or e.dst not in col_of:
                continue
            x = info["ccx"] + ANCHOR_DX
            y_bot = info["rect"].top()
            y_top = float(HEADER_BOTTOM)
            if y_bot - y_top < FLOW_LEN + 4:     # 卡片紧贴表头时保底箭头空间
                y_top = y_bot - (FLOW_LEN + 4)
            pe = ProduceEdgeItem(x, y_top, y_bot, e.label, e.src, e.dst)
            pe.setZValue(EDGE_Z)                 # 低于节点：被不透明卡片遮蔽
            self.addItem(pe)
            self._produce_items.append(pe)
            content = content.united(
                QRectF(x - 8, y_top - 4, 90, y_bot - y_top + 8))

        # -- 5. 表节点 --
        for t in tables:
            prod_name = ""
            if not t.is_input and t.producer_step in smap:
                prod_name = smap[t.producer_step].step_name
            it = TableItem(t, col_of[t.key], prod_name,
                           on_click=self._on_item_click)
            it.setZValue(0)
            self.addItem(it)
            self._table_items[t.key] = it
            tx = col_cx(col_of[t.key]) - TABLE_NODE_W / 2
            ty = TABLE_TOP_IN if t.is_input else TABLE_TOP_DEV
            content = content.united(QRectF(tx, ty, TABLE_NODE_W, TABLE_NODE_H))

        # -- 6. 步骤卡片 --
        for key, info in self._step_info.items():
            it = StepCardItem(info, on_click=self._on_item_click)
            it.setZValue(1)
            self.addItem(it)
            self._step_items[key] = it

        # -- 7. 悬空输入：红虚线短桩 + ⚠（绝不静默；dangling 边驱动）--
        dang: Dict[str, List[EdgeSpec]] = {}
        for e in self._edges:
            if e.type == "dangling":
                dang.setdefault(e.dst, []).append(e)
        for skey, es in dang.items():
            info = self._step_info.get(skey)
            if info is None:
                continue
            nm = len(es)
            for im in range(nm):
                py = info["cyc"] + (im - (nm - 1) / 2) * STACK_SP
                pen = QPen(QColor(styles.GRAPH_DANGLING), 1.5)
                pen.setStyle(Qt.DashLine)
                ln = self.addLine(info["rect"].left() - 40, py,
                                  info["rect"].left() - 2, py, pen)
                ln.setZValue(-2)
                ln.setAcceptedMouseButtons(Qt.NoButton)   # 装饰图元：穿透
                warn = self.addSimpleText("⚠", _font(11, True))
                warn.setBrush(QBrush(QColor(styles.GRAPH_DANGLING)))
                warn.setPos(info["rect"].left() - 56, py - 8)
                warn.setZValue(-2)
                warn.setAcceptedMouseButtons(Qt.NoButton)

        # -- 8. 开始/结束标识 + 起止连接边（M11/ADR-2）；空流程画空态提示 --
        if steps:
            content = self._build_markers(content)
        else:
            content = self._add_empty_hint(content, tables)

        if content.isNull():
            content = QRectF(0, 0, 400, 300)
        self._content_rect = content.normalized()
        self.setSceneRect(self._content_rect.adjusted(
            -SCENE_MARGIN, -SCENE_MARGIN, SCENE_MARGIN, SCENE_MARGIN))

        # 选中态跨重建保持（key 仍存在才有效）
        if self._selected:
            kind, key = self._selected
            alive = ((kind == "step" and key in self._step_items)
                     or (kind == "table" and key in self._table_items))
            if not alive:
                self._selected = None
        # 执行期物理名 tooltip 跨重建重应用
        if self._output_tables:
            self.set_output_tables(self._output_tables)
        self._apply_visuals()

    def update_step_status(self, step_id: str, status: NodeStatus,
                           reason: str = "") -> None:
        """更新单个步骤卡片的执行状态（失败时可附人话原因 → 气泡）。

        Args:
            step_id: 引擎步骤 ID。
            status:  新状态。
            reason:  失败原因文案（仅 FAILED 时显示气泡；空则只着色）。
        """
        item = self._step_items.get(step_id)
        if item is None:
            logger.debug(
                f"[node_graph] step_id '{step_id}' not found, "
                f"status update skipped")
            return
        item.set_status(status, reason)

    def clear_selection(self) -> None:
        """清除选中态并发射 no_selection（视图空白按下 / 外部调用）。"""
        self._selected = None
        self._apply_visuals()
        self.no_selection.emit()

    def select_node(self, kind: str, key: str) -> None:
        """外部选中（面板/添加联动，2026-09-21 定稿 M3-T5）。

        置选中态并高亮联动；不发射 step_selected/table_selected 信号
        （避免与页面选择回调成环）。
        """
        self._selected = (kind, key)
        self._apply_visuals()

    def set_output_tables(self, mapping: Dict[str, str]) -> None:
        """执行期回写（2026-09-21 定稿 M2-T9）：派生表编号→SQLite 物理表名。

        为命中的表节点设置 tooltip（消除 H5 的"不可见"部分）；rebuild 后
        需重新调用（tooltip 不跨重建保持）。
        """
        self._output_tables = dict(mapping or {})
        for key, item in self._table_items.items():
            phys = self._output_tables.get(key)
            if phys:
                item.setToolTip(f"物理表: {phys}")

    # ------------------------------------------------------------------ #
    #  Private helpers
    # ------------------------------------------------------------------ #

    def _on_item_click(self, kind: str, key: str) -> None:
        """图元点击回调：置选中态 → 高亮联动 → 转发页面级信号。"""
        self._selected = (kind, key)
        self._apply_visuals()
        if kind == "step":
            self.step_selected.emit(key)
        else:
            self.table_selected.emit(key)

    def _build_markers(self, content: QRectF) -> QRectF:
        """画开始/结束标识与起止连接边，返回更新后的内容包围盒。

        ADR-2：装饰图元——不占布局行（row_cy 公式不变）、不可选中、不可删除、
        不进右侧面板。开始锚定首步（卡片顶边左锚点 ccx-35，与产出边右锚点
        分离）；结束锚定 is_end 步（唯一性由数据层 normalize_end 保证），
        无则末步 fallback。结束步失败时整体下移 END_AVOID_GAP 避让气泡。
        """
        first_key = self._step_order[0]
        first = self._step_info[first_key]
        content = self._add_marker("▶ 开始", styles.GRAPH_START,
                                   first["ccx"] - ANCHOR_DX,
                                   first["rect"].top(), True, first_key,
                                   content)
        end_key = self._step_order[-1]
        for k in self._step_order:
            if self._step_info[k]["entry"].is_end:
                end_key = k
        info = self._step_info[end_key]
        avoid = END_AVOID_GAP if info["entry"].status == NodeStatus.FAILED \
            else 0
        return self._add_marker("■ 结束", styles.GRAPH_END, info["ccx"],
                                info["rect"].bottom(), False, end_key,
                                content, avoid)

    def _add_marker(self, text: str, color: str, cx: float, card_y: float,
                    above: bool, step_key: str, content: QRectF,
                    avoid: int = 0) -> QRectF:
        """画单个起止标识（文字 + flow 连线），并把外扩量并入内容包围盒。

        Args:
            text: 标识文案（"▶ 开始" / "■ 结束"）。
            color: 标识文字与连线颜色。
            cx: 连线所在竖直 x（开始=顶边左锚点；结束=底边中心）。
            card_y: 卡片边缘 y（顶边或底边）。
            above: True=标识在卡片上方（开始）；False=在下方（结束）。
            step_key: 关联步骤 ID（供淡化/高亮联动）。
            content: 当前内容包围盒。
            avoid: 额外避让位移（结束标识遇失败气泡时非 0）。
        """
        if above:
            y_near = card_y - FLOW_GAP - avoid   # 靠卡片一端（箭头 tip）
            y_far = y_near - FLOW_LEN            # 远离卡片一端
            text_y = y_far - 4 - MARKER_TEXT_H   # 文字在连线上方
        else:
            y_near = card_y + FLOW_GAP + avoid
            y_far = y_near + FLOW_LEN
            text_y = y_far + 4                   # 文字在连线下方
        fe = FlowEdgeItem(cx, y_far, y_near, color, step_key)
        fe.setZValue(EDGE_Z)
        self.addItem(fe)
        self._flow_items.append(fe)
        it = QGraphicsSimpleTextItem(text)
        it.setFont(_font(12, True))
        it.setBrush(QBrush(QColor(color)))
        it.setZValue(2)
        it.setAcceptedMouseButtons(Qt.NoButton)  # 装饰图元：点击穿透
        tw = it.boundingRect().width()
        if tw <= 0:                              # offscreen 按字数估算
            tw = len(text) * 12
        it.setPos(cx - tw / 2, text_y)
        self.addItem(it)
        self._marker_items.append((step_key, it))
        half = max(45.0, tw / 2 + 6)             # 外扩半宽（文字+连线）
        return content.united(
            QRectF(cx - half, text_y - 2, half * 2, MARKER_TEXT_H + 8))

    def _add_empty_hint(self, content: QRectF,
                        tables: List[TableSpec]) -> QRectF:
        """空流程提示（无步骤时画布不留全白，给文职用户下一步动作指引）。"""
        if tables:
            cx = col_cx(0) + COL_DX * (len(tables) - 1) / 2
            cy = HEADER_BOTTOM + 60.0
        else:
            cx, cy = 200.0, 150.0
        it = QGraphicsSimpleTextItem(EMPTY_HINT)
        it.setFont(_font(12))
        it.setBrush(QBrush(QColor(styles.GRAPH_EMPTY_HINT)))
        it.setZValue(2)
        it.setAcceptedMouseButtons(Qt.NoButton)
        tw = it.boundingRect().width()
        if tw <= 0:                              # offscreen 按字数估算
            tw = len(EMPTY_HINT) * 12
        it.setPos(cx - tw / 2, cy)
        self.addItem(it)
        return content.united(
            QRectF(cx - tw / 2 - 4, cy - 2, tw + 8, MARKER_TEXT_H + 6))

    def _apply_visuals(self) -> None:
        """按选中态刷新节点/边的高亮与淡化（正本 §5.3 联动表）。

        高亮判定统一为"任一命中即高亮"：步骤选中 → 其引用边/产出边/起止边；
        表选中 → 其泳道 + 引用它的接入段 + 产出它的那条产出边。
        淡化仅在选中步骤时生效（避免选表时整图变淡）。
        """
        sel_kind, sel_key = self._selected or (None, None)
        sel_step = sel_key if sel_kind == "step" else None
        sel_table = sel_key if sel_kind == "table" else None
        related: set = set()
        if sel_step:
            info = self._step_info.get(sel_step)
            if info:
                related = set(info["inputs"])
                outk = info["entry"].output_table
                if outk:
                    related.add(outk)

        for key, it in self._step_items.items():
            it.selected = (sel_kind == "step" and key == sel_key)
            it.setOpacity(0.3 if (sel_step and key != sel_step) else 1.0)
            it.update()
        for key, it in self._table_items.items():
            it.focus = ((sel_kind == "table" and key == sel_key)
                        or (key in related))
            it.setOpacity(0.3 if (sel_step and key not in related) else 1.0)
            it.update()
        for it in self._lane_items:
            it.highlight = bool((sel_step and it.table_key in related)
                                or (sel_table and it.table_key == sel_table))
            it.setOpacity(0.3 if (sel_step and it.table_key not in related)
                          else 1.0)
            it.update()
        for it in self._access_items:
            it.highlight = bool((sel_step and it.step_key == sel_step)
                                or (sel_table and it.table_key == sel_table))
            it.setOpacity(0.3 if (sel_step and it.step_key != sel_step)
                          else 1.0)
            it.update()
        for it in self._produce_items:
            it.highlight = bool((sel_step and it.step_key == sel_step)
                                or (sel_table and it.table_key == sel_table))
            it.setOpacity(0.3 if (sel_step and it.step_key != sel_step)
                          else 1.0)
            it.update()
        for it in self._flow_items:
            it.highlight = bool(sel_step and it.step_key == sel_step)
            it.setOpacity(0.3 if (sel_step and it.step_key != sel_step)
                          else 1.0)
            it.update()
        for skey, it in self._marker_items:
            it.setOpacity(0.3 if (sel_step and skey != sel_step) else 1.0)


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class NodeGraphView(QGraphicsView):
    """视图管理（M12；蓝本 CanvasView dag_viewer.py:559-617）。

    Ctrl+滚轮缩放（钳制 [0.40, 2.50]，AnchorUnderMouse）；空白左键拖拽平移
    （按 transform().m11() 换算滚动条，且按下即清选中）；NoDrag 模式下 item
    的 mousePressEvent 稳定分发，节点点击永不被平移吞掉。
    """

    def __init__(self, scene: Optional[NodeGraphScene] = None,
                 parent=None) -> None:
        if scene is None:
            scene = NodeGraphScene()
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor(styles.GRAPH_CANVAS_BG)))
        self.setFrameShape(QGraphicsView.NoFrame)
        self._pan: Optional[Tuple[Any, int, int]] = None

    def fit_to_scene(self) -> None:
        """全览：内容包围盒外扩 FIT_MARGIN 后适配视口。"""
        scene = self.scene()
        if scene is None:
            return
        rect = getattr(scene, "content_rect", None)
        if rect is None or rect.isNull():
            rect = scene.sceneRect()
        if rect.isNull() or rect.isEmpty():
            return
        self.fitInView(rect.adjusted(-FIT_MARGIN, -FIT_MARGIN,
                                     FIT_MARGIN, FIT_MARGIN),
                       Qt.KeepAspectRatio)

    # ------------------------------------------------------------------ #
    # 缩放 / 平移（与 item 点击互不干扰）
    # ------------------------------------------------------------------ #

    def wheelEvent(self, event) -> None:
        """Ctrl+滚轮缩放（钳制）；普通滚轮滚动。"""
        if event.modifiers() & Qt.ControlModifier:
            d = event.angleDelta().y()
            if d:
                factor = 1.15 if d > 0 else (1.0 / 1.15)
                cur = self.transform().m11()
                target = max(ZOOM_MIN, min(ZOOM_MAX, cur * factor))
                if abs(target - cur) > 1e-9:
                    self.scale(target / cur, target / cur)
            event.accept()
            return
        super().wheelEvent(event)

    def mousePressEvent(self, event) -> None:
        # 空白处（非步骤卡片/表节点）左键按下 → 进入平移态并清选中；
        # 命中节点时正常分发（点击永不被吞）
        if event.button() == Qt.LeftButton:
            it = self.itemAt(event.pos())
            if not isinstance(it, (StepCardItem, TableItem)):
                self._pan = (event.globalPos(),
                             self.horizontalScrollBar().value(),
                             self.verticalScrollBar().value())
                self.viewport().setCursor(Qt.ClosedHandCursor)
                scene = self.scene()
                if isinstance(scene, NodeGraphScene):
                    scene.clear_selection()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._pan is not None and event.buttons() & Qt.LeftButton:
            gp, h0, v0 = self._pan
            dx = event.globalPos().x() - gp.x()
            dy = event.globalPos().y() - gp.y()
            s = self.transform().m11() or 1.0
            self.horizontalScrollBar().setValue(int(h0 - dx / s))
            self.verticalScrollBar().setValue(int(v0 - dy / s))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._pan is not None:
            self._pan = None
            self.viewport().setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
