# -*- coding: utf-8 -*-
"""M-b/M-c 渲染冒烟（工程内部门禁载体：FF3；非 GUI 功能）。

2026-09-24（R6/E5，D8 裁定）：自 _temp/DAG-rebuild/ 迁入正式工具目录。
注：M13"调序能力零残留"三处为否定存在断言（not hasattr），本身即真断言，
经 R6 复核保持不变（冻结方案 E5-3 该子项判定为无需修改，偏差记 REPORT §1）。

覆盖：五类边计数不变量 / 图元结构 / 选中高亮联动 / 失败气泡 /
弃用重绘 / 空态提示 / 表详情面板 / 覆盖确认与空流程拦截存在性 / 截图。
运行：cd rpa_engine && python tools\smoke\smoke_mb.py
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ENGINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ENGINE))

from PyQt5.QtWidgets import QApplication  # noqa: E402

from gui.models import WorkflowModel  # noqa: E402
from gui.node_graph import (  # noqa: E402
    AccessItem, FlowEdgeItem, LaneItem, NodeStatus, ProduceEdgeItem,
    StepCardItem, TableItem,
)
from gui.page_operation_config import OperationConfigPage  # noqa: E402

# R6/D5-2 兼容：画布刷新增 50ms 合并定时器后，冒烟需即时断言——
# 类级补丁将合并入口指回直调（仅测试通道，生产路径不受影响）
OperationConfigPage._schedule_graph_refresh = OperationConfigPage._refresh_graph
from gui.user_template_manager import UserTemplateManager  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    tag = "OK " if cond else "FAIL"
    print(f"[{tag}] {name} {detail}")
    if not cond:
        FAILS.append(name)


def counts(scene):
    return {
        "steps": len(scene._step_items),
        "tables": len(scene._table_items),
        "lanes": len(scene._lane_items),
        "access": len(scene._access_items),
        "produce": len(scene._produce_items),
        "flow": len(scene._flow_items),
        "markers": len(scene._marker_items),
    }


def edge_counts(edges):
    out = {}
    for e in edges:
        out[e.type] = out.get(e.type, 0) + 1
    return out


def main():
    app = QApplication(sys.argv)
    model = WorkflowModel()
    entries = [
        {"table_id": "T1", "alias": "员工名册", "sqlite_table": "t1",
         "file_path": "D:/x/roster.xlsx", "sheet_name": "Sheet1",
         "header_row": 1, "columns": ["姓名", "部门", "工号", "金额"]},
        {"table_id": "T2", "alias": "补贴标准", "sqlite_table": "t2",
         "file_path": "D:/x/subsidy.xlsx", "sheet_name": "Sheet1",
         "header_row": 1, "columns": ["部门", "标准"]},
    ]
    model.set_tables(entries)

    page = OperationConfigPage(model, UserTemplateManager())
    page.set_input_tables(entries)

    # S1 filter(T1)→T101；S2 mapping_match(T1, 匹配 T101)→T102；
    # S3 aggregate(T102)→T103；S4 copy_table(T2)→T104；S5 export(T103)；
    # S6 filter(T999 悬空)
    s1 = model.add_step("filter")
    s1.params = {"conditions": [{"column": "金额", "op": ">", "value": 0}],
                 "output_mode": "new_table"}
    s2 = model.add_step("mapping_match")
    s2.target_table_id = "T1"
    s2.params = {"match_table_id": s1.output_table_id,
                 "match_columns": [{"key": "部门", "value": "部门"}],
                 "fill_column": "标准", "match_column": "部门"}
    s3 = model.add_step("aggregate")
    s3.target_table_id = s2.output_table_id
    s3.params = {"group_by": ["部门"],
                 "metrics": [{"column": "金额", "agg": "sum",
                              "alias": "总额"}]}
    s4 = model.add_step("copy_table")
    s4.target_table_id = "T2"
    s5 = model.add_step("export")
    s5.target_table_id = s3.output_table_id
    s6 = model.add_step("filter")
    s6.target_table_id = "T999"
    s6.params = {"conditions": [{"column": "金额", "op": ">", "value": 0}]}
    page._refresh_graph()
    scene = page._scene

    ec = edge_counts(page._last_edges)
    c = counts(scene)
    print("edges:", ec)
    print("items:", c)
    exp_tables = 2 + len([s for s in model.steps if s.output_table_id])
    check("flow 恒 2", ec.get("flow") == 2)
    check("dangling=1（T999）", ec.get("dangling") == 1)
    check("produce=产表步骤数", ec.get("produce") == exp_tables - 2,
          f"{ec.get('produce')}/{exp_tables - 2}")
    check("reference 边存在", ec.get("reference", 0) >= 6,
          str(ec.get("reference")))
    check("步骤卡片 6", c["steps"] == 6)
    check("表节点 = 输入+派生", c["tables"] == exp_tables,
          f"{c['tables']}/{exp_tables}")
    check("泳道 = 被引用表数", c["lanes"] >= 5)
    check("起止标识 2", c["markers"] == 2)
    check("produce 图元=produce 边", c["produce"] == ec.get("produce", 0))
    check("flow 图元恒 2（起止各一）", c["flow"] == 2)
    check("sceneRect 非空", not scene.sceneRect().isNull(),
          str(scene.sceneRect()))

    # 悬空角标：S6 卡片 missing 非空
    s6_item = scene._step_items[s6.step_id]
    check("S6 输入缺失角标", bool(s6_item.missing), str(s6_item.missing))
    # 副标题（STEP_DESC）
    check("卡片副标题非空", bool(scene._step_items[s1.step_id].subtitle))

    # 点击联动（信号 + 高亮不崩）
    got = []
    scene.step_selected.connect(lambda k: got.append(("step", k)))
    scene.table_selected.connect(lambda k: got.append(("table", k)))
    scene._on_item_click("step", s1.step_id)
    check("step_selected 发射", ("step", s1.step_id) in got)
    check("选中步骤淡化生效",
          scene._step_items[s3.step_id].opacity() < 1.0)
    scene._on_item_click("table", "T1")
    check("table_selected 发射（表 ID）", ("table", "T1") in got)
    check("表详情面板态", page._selected_table_id == "T1")
    scene.clear_selection()
    check("清选中恢复不透明",
          scene._step_items[s3.step_id].opacity() == 1.0)

    # 失败气泡
    scene.update_step_status(s1.step_id, NodeStatus.FAILED, "筛选条件列不存在")
    check("失败原因写入卡片",
          scene._step_items[s1.step_id].fail_reason == "筛选条件列不存在")
    scene.update_step_status(s1.step_id, NodeStatus.PENDING)

    # 弃用 T2 → S4 入闭包 → deprecated 边 + 表节点灰化
    model.deprecate_table("T2", True)
    page._refresh_graph()
    ec2 = edge_counts(page._last_edges)
    check("弃用产生 deprecated 边", ec2.get("deprecated", 0) >= 1, str(ec2))
    check("T2 表节点弃用态", scene._table_items["T2"].deprecated)
    model.deprecate_table("T2", False)
    page._refresh_graph()
    check("恢复后无 deprecated 边",
          edge_counts(page._last_edges).get("deprecated", 0) == 0)

    # 连线说明（M15）
    summary = page._edge_summary("step", s4.step_id)
    check("步骤连线说明含产出", "复制新表" in summary, summary)
    tsum = page._edge_summary("table", "T1")
    check("表连线说明含被引用", "被引用" in tsum)

    # 空流程空态提示
    n_steps = len(model.steps)
    model.steps.clear()
    page._refresh_graph()
    texts = [it.text() for it in scene.items()
             if it.__class__.__name__ == "QGraphicsSimpleTextItem"]
    check("空态提示文案", any("暂无步骤" in t for t in texts), str(texts))
    check("空流程 flow=0", len(scene._flow_items) == 0)

    # 截图（全量场景恢复后）
    model.steps.clear()
    for s in (s1, s2, s3, s4, s5, s6):
        model.steps.append(s)
    page._refresh_graph()
    for _ in range(5):
        app.processEvents()
    art = Path(__file__).resolve().parent / "artifacts"
    art.mkdir(parents=True, exist_ok=True)
    # 全场景渲染（不受 viewport 尺寸限制，完整目检画布）
    from PyQt5.QtGui import QImage, QPainter
    rect = scene.sceneRect()
    img = QImage(int(rect.width()), int(rect.height()),
                 QImage.Format_ARGB32)
    img.fill(0xFFFAFAFA)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    scene.render(painter)
    painter.end()
    ok = img.save(str(art / "mb-preview.png"))
    check("截图保存", ok, f"{img.width()}x{img.height()}")

    # 覆盖确认/空流程拦截方法存在（弹窗行为留真机清单）
    check("_confirm_overwrite_steps 存在",
          callable(getattr(page, "_confirm_overwrite_steps", None)))
    check("_confirm_active_steps 存在",
          callable(getattr(page, "_confirm_active_steps", None)))
    check("_build_table_param_panel 存在",
          callable(getattr(page, "_build_table_param_panel", None)))
    # M13：调序能力零残留
    check("无 table_reorder 信号",
          not hasattr(scene, "table_reorder_requested"))
    check("步骤面板无上移/下移",
          not hasattr(page, "_on_move_step"))
    check("模型步骤数恢复", len(model.steps) == n_steps)

    print()
    if FAILS:
        print("SMOKE_FAIL:", FAILS)
        return 1
    print("SMOKE_ALL_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
