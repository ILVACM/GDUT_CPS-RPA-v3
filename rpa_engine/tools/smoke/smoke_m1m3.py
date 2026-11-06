# -*- coding: utf-8 -*-
"""M1-M3 实施冒烟（工程内部门禁载体：FF3/FF4/FF5；非 GUI 功能）。

增量创建：M1 骨架+场景（2026-09-21）→ M2/M3 场景追加 → M4 定稿全场景。
2026-09-24（R6/E5，D8 裁定）：自 _temp/DAG-rebuild/ 迁入正式工具目录，
恒真断言修真（撤销条显示/撞号重绘两处）。
运行：cd rpa_engine && python tools\smoke\smoke_m1m3.py
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ENGINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ENGINE))

from PyQt5.QtWidgets import QApplication  # noqa: E402

from gui.page_input_selection import (  # noqa: E402
    InputSelectionPage, _HeaderRowDialog,
)

# R6/D5-2 兼容：画布刷新增 50ms 合并定时器后，冒烟需即时断言——
# 类级补丁将合并入口指回直调（仅测试通道，生产路径不受影响）
from gui.page_operation_config import OperationConfigPage as _OCP  # noqa: E402
_OCP._schedule_graph_refresh = _OCP._refresh_graph

FAILS = []


def check(name, cond, detail=""):
    tag = "OK " if cond else "FAIL"
    print(f"[{tag}] {name} {detail}")
    if not cond:
        FAILS.append(name)


def make_rows(n=6, dup=False, merged=False):
    rows = [[f"列{c}" + (" dup" if (dup and c == 1) else "")
             for c in range(4)] for _ in range(n)]
    if dup:
        rows[0][1] = rows[0][0]
    if merged:
        for r in rows[2:]:
            r[2] = ""
    return rows


def main():
    app = QApplication(sys.argv)

    # -- M1-S1 弹窗常态：初始选中 0、摘要解耦、无字符画残留 --
    rows = make_rows()
    dlg = _HeaderRowDialog(rows)
    check("M1 初始选中=0", dlg.selected_row_index() == 0)
    from PyQt5.QtCore import Qt as _Qt
    check("M1 摘要 QLabel 存在且 RichText",
          dlg._summary.textFormat() == _Qt.RichText
          and "当前选择：第 1 行作为表头" in dlg._summary.text())
    check("M1 无 QTextEdit 字符画残留", not hasattr(dlg, "_text"))
    check("M1 模型行数=预览行数", dlg._model.rowCount() == len(rows))
    check("M1 行号列首列", dlg._model.horizontalHeaderItem(0).text() == "行号")

    # -- M1-S2 FF4：点击行==选中行（逐行） --
    ff4_ok = True
    for n in range(len(rows)):
        dlg._on_row_clicked(dlg._model.index(n, 1))
        if dlg.selected_row_index() != n:
            ff4_ok = False
        if f"第 {n + 1} 行作为表头" not in dlg._summary.text():
            ff4_ok = False
    check("M1 FF4 点击行==选中行+摘要同步", ff4_ok)

    # -- M1-S3 徽章唯一（SingleSelection+SelectRows） --
    dlg._on_row_clicked(dlg._model.index(3, 0))
    check("M1 徽章唯一（视图单选行3）",
          dlg._view.currentIndex().row() == 3
          and dlg._view.selectionModel().selectedRows().__len__() == 1)

    # -- M1-S4 50 行滚动 --
    rows50 = make_rows(50)
    dlg50 = _HeaderRowDialog(rows50)
    check("M1 50 行全载入", dlg50._model.rowCount() == 50)
    check("M1 垂直滚动条在位",
          dlg50._view.verticalScrollBar() is not None)
    dlg50._on_row_clicked(dlg50._model.index(49, 0))
    check("M1 末行可选中", dlg50.selected_row_index() == 49)

    # -- M1-S5 合并单元格前向填充+摘要标注 --
    rows_m = make_rows(merged=True)
    dlg_m = _HeaderRowDialog(rows_m)
    check("M1 合并填充列检出", 2 in dlg_m._filled_cols,
          str(dlg_m._filled_cols))
    check("M1 填充后无空洞",
          all(dlg_m._model.item(r, 3).text() != "" for r in range(2, 6)))
    check("M1 摘要含合并标注", "来自合并单元格" in dlg_m._summary.text())

    # -- M1-S6 mangle 规则不变 --
    rows_d = make_rows(dup=True)
    dlg_d = _HeaderRowDialog(rows_d)
    check("M1 重复列名 mangle(.1)", ".1" in dlg_d._summary.text())
    check("M1 重复预警橙色 span",
          "color:#e67e22" in dlg_d._summary.text())

    # -- M1-S7 空表/全空预览：按钮禁用 + 弹窗拦截数据 --
    page = InputSelectionPage()
    page._add_row(Path("d:/x/empty.xlsx"), "S1", [])
    from PyQt5.QtWidgets import QPushButton
    wrapper = page._table.cellWidget(0, 4)
    btn = None
    if wrapper is not None:
        for b in wrapper.findChildren(QPushButton):
            btn = b
            break
    check("M1 空预览按钮禁用", btn is not None and not btn.isEnabled())
    page._add_row(Path("d:/x/ok.xlsx"), "S1", make_rows(3))
    wrapper2 = page._table.cellWidget(1, 4)
    btn2 = None
    if wrapper2 is not None:
        for b in wrapper2.findChildren(QPushButton):
            btn2 = b
            break
    check("M1 有内容按钮启用", btn2 is not None and btn2.isEnabled())
    rows_blank = [["", ""], ["", ""]]
    dlg_blank = _HeaderRowDialog(rows_blank)
    check("M1 全空预览不崩", dlg_blank._model.rowCount() == 2)

    # -- M2-S1 级联 B：删中间步 → 下游悬空 + 撤销条 + 撤销复原 --
    from gui.models import WorkflowModel
    from gui.user_template_manager import UserTemplateManager
    model = WorkflowModel()
    model.set_tables([
        {"table_id": "T1", "alias": "员工", "sqlite_table": "t1"},
        {"table_id": "T2", "alias": "标准", "sqlite_table": "t2"},
    ])
    page2 = InputSelectionPage()
    from gui.page_operation_config import OperationConfigPage
    op = OperationConfigPage(model, UserTemplateManager())
    op.set_input_tables([
        {"table_id": "T1", "alias": "员工", "sqlite_table": "t1",
         "columns": ["a", "b"]},
        {"table_id": "T2", "alias": "标准", "sqlite_table": "t2",
         "columns": ["a", "c"]},
    ])
    s1 = model.add_step("filter")
    out1 = s1.output_table_id
    s2 = model.add_step("aggregate")
    s2.target_table_id = out1
    op._refresh_graph()
    check("M2 首派生=T101", out1 == "T101", out1)
    op._on_delete_step(0)
    check("M2 级联下游保留引用(悬空语义)",
          model.steps[0].target_table_id == out1)
    check("M2 撤销条显示", op._undo_bar.isVisibleTo(op))
    dang = [e for e in op._last_edges if e.type == "dangling"]
    check("M2 悬空边生成", len(dang) == 1, str([e.key for e in dang]))
    check("M2 悬空态投影", model.table_states.get(out1) == "dangling",
          str(model.table_states.get(out1)))
    n_before = len(model.steps)
    op._on_undo_clicked()
    check("M2 撤销复原步骤数", len(model.steps) == n_before + 1,
          f"{len(model.steps)}/{n_before + 1}")
    check("M2 撤销后下游引用恢复",
          model.steps[1].target_table_id == out1)

    # -- M2-S2 执行期回写 tooltip --
    op._refresh_graph()
    op.set_output_tables({out1: "t_s1"})
    item = op._scene._table_items.get(out1)
    check("M2 派生表 tooltip 回写",
          item is not None and "t_s1" in (item.toolTip() or ""),
          item.toolTip() if item else "missing")

    # -- M2-S3 撞号检测 UI 链不崩（R6/F5：改走生产入口，冗余门面已删）--
    s_dup = model.add_step("filter")
    s_dup.output_table_id = out1
    check("M2 撞号检出", model.validate_table_ids_unique() == [out1])
    op._refresh_graph()
    check("M2 撞号下重绘不崩",
          out1 in op._scene._table_items and len(op._last_edges) >= 1,
          f"items={out1 in op._scene._table_items} "
          f"edges={len(op._last_edges)}")

    # -- M3-S1 唯一入口 + 弹层结构 --
    check("M3 唯一添加入口", "添加功能步骤" in op._btn_add.text())
    check("M3 弹层存在", op._add_popup is not None)
    # R15/B-67：卡片数断言引用 STEP_COUNT 单一常量（原硬编码 9）
    from gui.models import STEP_COUNT
    check(f"M3 卡片数={STEP_COUNT}", len(op._add_cards) == STEP_COUNT,
          str(len(op._add_cards)))

    # -- M3-S2 搜索过滤 --
    op._filter_popup("vlookup")
    vis = [k for k, b in op._add_cards.items() if not b.isHidden()]
    check("M3 搜索 vlookup 仅命中 mapping_match", vis == ["mapping_match"],
          str(vis))
    op._filter_popup("")
    check("M3 空搜索全显示",
          all(not b.isHidden() for b in op._add_cards.values()))

    # -- M3-S3 最近使用 --
    from gui.recent_steps import push_recent, load_recent
    push_recent("filter")
    push_recent("aggregate")
    op._refresh_recent_box()
    check("M3 最近使用落盘+回读", load_recent()[:2] == ["aggregate", "filter"],
          str(load_recent()))

    # -- M3-S4 分组派生 + StepMeta 兼容层 --
    from gui.models import (STEP_CATALOG, main_buttons, more_buttons)
    mains, mores = main_buttons(), more_buttons()
    check("M3 分组并集=catalog 且不相交",
          set(mains) | set(mores) == set(STEP_CATALOG)
          and not (set(mains) & set(mores)),
          f"{mains}/{mores}")
    check("M3 主按钮=4 分类代表", len(mains) == 4, str(mains))
    cn, desc = STEP_CATALOG["filter"]
    check("M3 StepMeta tuple 解包兼容", cn == "条件筛选" and desc.startswith("按条件"))
    check("M3 StepMeta 下标兼容",
          STEP_CATALOG["filter"][0] == "条件筛选"
          and STEP_CATALOG["filter"][1] == desc)

    # -- M3-S5 添加联动：自动选中+面板展开 --
    n0 = len(op.model.steps)
    op._on_add_step("filter")
    check("M3 添加后步骤+1", len(op.model.steps) == n0 + 1)
    check("M3 添加后自动选中",
          op._selected_step_index == len(op.model.steps) - 1
          and op._scene._selected == ("step", op.model.steps[-1].step_id))

    # -- M4-S1 模板应用位置映射（输入按序 + 派生重分配） --
    tpl = {
        "name": "tpl",
        "tables": [
            {"table_id": "T1", "alias": "x", "sqlite_table": "x",
             "source": {"file": "d:/x/a.xlsx", "sheet": "S1", "header_row": 1}},
            {"table_id": "T2", "alias": "y", "sqlite_table": "y",
             "source": {"file": "d:/x/b.xlsx", "sheet": "S1", "header_row": 1}},
        ],
        "steps": [
            {"step_id": "S1", "type": "filter", "name": "筛选 1",
             "target_table_id": "T1", "output_table_id": "T3",
             "params": {"conditions": []}},
            {"step_id": "S2", "type": "aggregate", "name": "统计 1",
             "target_table_id": "T3", "output_table_id": "",
             "params": {"group_by": [], "metrics": []}},
        ],
    }
    mapped = op._map_template_ids(tpl)
    s1m, s2m = mapped["steps"]
    check("M4 模板输入表按序映射", s1m["target_table_id"] == "T1")
    new_derived = s1m["output_table_id"]
    check("M4 模板派生表重分配 T101+",
          new_derived != "T3" and new_derived.startswith("T1"),
          new_derived)
    check("M4 下游引用同步重映射",
          s2m["target_table_id"] == new_derived)
    op.model.load_session(list(op._table_entries), mapped)
    check("M4 load_session 后零撞号",
          op.model.validate_table_ids_unique() == [])
    op._refresh_graph()

    # -- M4-S2 to_dict → parse → validate 闭环 --
    import json as _json
    import tempfile
    from engine.parser import parse_workflow
    from engine.validator import validate_workflow
    op.model.steps[0].params = {"conditions": [
        {"column": "a", "op": ">", "value": 1}]}
    op.model.steps[1].params = {"group_by": ["a"], "metrics": [
        {"column": "a", "agg": "count", "alias": "n"}]}
    data = op.model.to_dict()
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "wf.json"
        p.write_text(_json.dumps(data, ensure_ascii=False), encoding="utf-8")
        wf = parse_workflow(str(p))
        ok = validate_workflow(wf)
    check("M4 to_dict→parse→validate 闭环", ok)

    # -- M4-S3 清空→撤销 复原 --
    n_before = len(op.model.steps)
    # 清空调用含 QMessageBox，offscreen 下 exec_ 会阻塞 →
    # 用 push_undo + reset_steps 模拟确认后的清空路径
    op._push_undo("清空全部步骤")
    op.model.reset_steps()
    check("M4 清空后步骤为空", len(op.model.steps) == 0)
    op._on_undo_clicked()
    check("M4 撤销复原", len(op.model.steps) == n_before)

    # ===== 修复轮 F 场景（2026-09-21） =====

    # -- F1 链：to_dict renumber 后 refresh_graph 使 scene 键对齐 S{n} --
    # （M5-b/C3：add_step 即时重排，step_NN/S{n} 混合键态已消除——原
    #  "旧键失联"必要性演示随裁定反转为"无失联"不变量，链核心语义不变）
    from gui.node_graph import NodeStatus
    op.model.add_step("filter")   # 新步即时 S{n}（C3）
    op._refresh_graph()
    op.model.to_dict()            # renumber 幂等（step_id 已为 S{n}）
    model_ids = {s.step_id for s in op.model.steps}
    stale = model_ids - set(op._scene._step_items.keys())
    check("F1 即时重排后 scene 键无失联（M5-b/C3）", len(stale) == 0,
          str(sorted(stale)))
    op.refresh_graph()
    check("F1 refresh 后 scene 键==模型 step_id",
          set(op._scene._step_items.keys()) == model_ids)
    op._scene.update_step_status(sorted(model_ids)[0], NodeStatus.RUNNING)
    check("F1 update_step_status 命中生效",
          op._scene._step_items[sorted(model_ids)[0]].status
          == NodeStatus.RUNNING)

    # -- F2 口径：overwrite 两步链执行步骤数 = 模型数 + cp 数 --
    from gui.models import WorkflowModel as _WM
    m2 = _WM()
    m2.set_tables([{"table_id": "T1", "alias": "a", "sqlite_table": "t1"}])
    s_ov = m2.add_step("filter")
    s_ov.target_table_id = "T1"
    s_ov.params = {"conditions": [], "output_mode": "overwrite_target"}
    d_ov = m2.to_dict()
    check("F2 cp 步计入执行总数", len(d_ov["steps"]) == len(m2.steps) + 1,
          f'{len(d_ov["steps"])}/{len(m2.steps) + 1}')

    # -- F6/F4 模板超界引用 → dangling 态 --
    tpl_over = dict(tpl)
    tpl_over["steps"] = [dict(tpl["steps"][0])]
    tpl_over["steps"][0]["target_table_id"] = "T9"
    mapped_o = op._map_template_ids(tpl_over)
    check("F6 超界引用保持原号", mapped_o["steps"][0]["target_table_id"] == "T9")
    op.model.load_session(list(op._table_entries), mapped_o)
    check("F4 超界引用 dangling 态",
          op.model.table_states.get("T9") == "dangling",
          str(op.model.table_states.get("T9")))

    # -- F3 undo gen 代际 --
    op._push_undo("测试A")
    gen_a = op._undo_gen
    op._push_undo("测试B")
    gen_b = op._undo_gen
    check("F3 连续压栈 gen 递增", gen_b > gen_a)
    op._undo_bar.show()
    op._hide_undo_bar_if(gen_a)   # 旧代际不得隐藏
    check("F3 旧代际回调不隐藏", not op._undo_bar.isHidden())
    op._hide_undo_bar_if(gen_b)   # 当前代际隐藏
    check("F3 当前代际回调隐藏", op._undo_bar.isHidden())
    _, snap_top = op._undo_stack[-1]
    check("F3 快照含 next_step_num 键", "next_step_num" in snap_top)
    n_undo = len(op.model.steps)
    op._undo_last()
    check("F3 撤销复原（gen 场景后）", len(op.model.steps) == n_undo)
    op._undo_last()

    # ===== S1 场景（2026-09-21 审计修复轮） =====

    # -- S1-P1 编辑态无损 + 折叠链 --
    m3 = _WM()
    m3.set_tables([{"table_id": "T1", "alias": "a", "sqlite_table": "t1"}])
    s_p1 = m3.add_step("filter")
    s_p1.target_table_id = "T1"
    s_p1.params = {"conditions": [], "output_mode": "overwrite_target"}
    d_edit = m3.to_dict(include_deprecated=True)
    check("S1 编辑态无 _cp 步",
          not any(s["step_id"].endswith("_cp") for s in d_edit["steps"]))
    check("S1 编辑态保全 output_mode",
          d_edit["steps"][0]["params"].get("output_mode") == "overwrite_target")
    d_biz = m3.to_dict()
    check("S1 业务口径展开 _cp",
          any(s["step_id"].endswith("_cp") for s in d_biz["steps"]))
    m4 = _WM()
    m4.load_from_dict(d_biz)
    check("S1 折叠迁移还原 mode",
          len(m4.steps) == 1
          and m4.steps[0].params.get("output_mode") == "overwrite_target")
    check("S1 折叠后无 _cp 残留",
          not any("_cp" in s.step_id for s in m4.steps))

    # -- S1-P2 apply_registry 保 steps --
    m5 = _WM()
    m5.set_tables([{"table_id": "T1", "alias": "a", "sqlite_table": "t1"}])
    m5.add_step("filter")
    m5.steps[0].target_table_id = "T9"
    m5.apply_registry([
        {"table_id": "T1", "alias": "a", "sqlite_table": "t1"},
        {"table_id": "T2", "alias": "b", "sqlite_table": "t2"}])
    check("S1 apply_registry 保 steps", len(m5.steps) == 1)
    check("S1 apply_registry 表刷新",
          [t.table_id for t in m5.tables] == ["T1", "T2"])
    check("S1 apply_registry 悬空投影",
          m5.table_states.get("T9") == "dangling")

    # ===== S2 场景（2026-09-21 审计修复轮） =====

    # -- S2-T1 撞号 GUI 拦截 --
    import gui.page_operation_config as _poc
    _warn_calls = []
    _orig_warning = _poc.QMessageBox.warning
    _poc.QMessageBox.warning = staticmethod(
        lambda *a, **k: _warn_calls.append(a[2] if len(a) > 2 else ""))
    try:
        op.model.steps[-1].output_table_id = "T1"   # 人为撞号
        check("S2 撞号检出 False", op._check_table_ids_unique() is False)
        check("S2 撞号弹窗文案", any("T1" in str(c) for c in _warn_calls))
        op.model.steps[-1].output_table_id = op.model.alloc_table_id()
        check("S2 恢复后 True", op._check_table_ids_unique() is True)
    finally:
        _poc.QMessageBox.warning = _orig_warning

    # -- S2-T2 进度口径（页面级） --
    from gui.page_progress import ProgressPage
    pg = ProgressPage()
    pg.setup_steps([("S1", "筛选 1"), ("S1_cp", "筛选 1（写回原表）")])
    pg.mark_done("S1_cp")
    check("S2 进度页含 cp 行", pg._list.count() == 2
          and "S1_cp" in pg._id_to_row)

    # -- S2-T3 清空前 harvest（撤销还原表单参数） --
    op.model.reset_steps()
    s_c = op.model.add_step("filter")
    op._refresh_graph()
    op._select_step(0)
    if op._inline_form is not None:
        try:
            op._inline_form._logic.setCurrentText("OR")
        except Exception:
            pass
    op._harvest_current_form(show_errors=False)
    op._push_undo("清空全部步骤")
    op.model.reset_steps()
    op._undo_last()
    check("S2 清空撤销复原", len(op.model.steps) == 1
          and op.model.steps[0].uid == s_c.uid)

    # -- S2-T6 标题同源 --
    op._refresh_graph()
    sid = op.model.steps[0].step_id
    check("S2 _sname 实时标题", op._sname(sid) == "条件筛选 1",
          op._sname(sid))

    # -- S2-T7 模板 output_table 兜底剥离 --
    tpl_phys = {"tables": [], "steps": [
        {"step_id": "S1", "type": "filter", "name": "筛选 1",
         "target_table_id": "T1", "output_table_id": "T101",
         "params": {"conditions": [], "output_table": "t_legacy"}}]}
    mapped_p = op._map_template_ids(tpl_phys)
    check("S2 模板物理名剥离",
          "output_table" not in mapped_p["steps"][0]["params"])

    # -- S2-T8 输入表 tooltip --
    op.set_input_tables([
        {"table_id": "T1", "alias": "员工", "sqlite_table": "t1",
         "columns": ["a"]},
        {"table_id": "T2", "alias": "标准", "sqlite_table": "t2",
         "columns": ["a"]},
    ])
    op.model.reset_steps()
    op.model.add_step("filter")
    op._scene._output_tables.clear()   # 清前场景回写残留（隔离构造期断言）
    op._refresh_graph()
    item_t1 = op._scene._table_items.get("T1")
    check("S2 输入表 tooltip 物理名",
          item_t1 is not None and item_t1.toolTip() == "物理表: t1",
          item_t1.toolTip() if item_t1 else "missing")
    der_id = op.model.steps[0].output_table_id
    item_d = op._scene._table_items.get(der_id)
    check("S2 派生表构造期无 tooltip",
          item_d is not None and item_d.toolTip() == "")
    op.set_output_tables({der_id: "t_s1"})
    check("S2 派生表回写 tooltip",
          op._scene._table_items[der_id].toolTip() == "物理表: t_s1")
    op._refresh_graph()
    check("S2 rebuild 后 tooltip 保持",
          op._scene._table_items["T1"].toolTip() == "物理表: t1"
          and op._scene._table_items[der_id].toolTip() == "物理表: t_s1")

    # -- S2-T9 new_round 清场（页面等价路径：model.reset + set_input_tables([])） --
    op.model.reset()
    op.set_input_tables([])
    check("S2 清场后画布空",
          op._table_entries == [] and not op._scene._table_items
          and not op._scene._step_items)

    # -- S2-T5 同 sheet 查重 --
    import tempfile as _tf
    from openpyxl import Workbook as _WB
    import gui.page_input_selection as _pis
    with _tf.TemporaryDirectory() as td:
        xp = Path(td) / "dup.xlsx"
        wb = _WB()
        wb.active.title = "S1"
        wb.active.append(["a", "b"])
        ws2 = wb.create_sheet("S2")
        ws2.append(["c"])
        wb.save(str(xp))
        xp2 = Path(td) / "other.xlsx"
        wb2 = _WB()
        wb2.active.title = "S1"
        wb2.active.append(["z"])
        wb2.save(str(xp2))

        page3 = _pis.InputSelectionPage()
        infos = []
        _orig_info = _pis.QMessageBox.information
        _orig_get = _pis.QFileDialog.getOpenFileNames
        _pis.QMessageBox.information = staticmethod(
            lambda *a, **k: infos.append(a[2] if len(a) > 2 else ""))
        try:
            _pis.QFileDialog.getOpenFileNames = staticmethod(
                lambda *a, **k: ([str(xp)], ""))
            page3._on_add_files()
            n_first = len(page3._entries)
            page3._on_add_files()          # 同文件二次添加
            check("S2 同文件二次添加不翻倍",
                  len(page3._entries) == n_first == 2,
                  f"{len(page3._entries)}/{n_first}")
            check("S2 跳过提示一次", len(infos) == 1
                  and "跳过" in str(infos[0]))
            _pis.QFileDialog.getOpenFileNames = staticmethod(
                lambda *a, **k: ([str(xp2)], ""))
            page3._on_add_files()          # 异文件同 sheet 名 S1
            check("S2 异文件同名不误杀", len(page3._entries) == 3,
                  str(len(page3._entries)))
        finally:
            _pis.QMessageBox.information = _orig_info
            _pis.QFileDialog.getOpenFileNames = _orig_get

    # ===== S3 场景（2026-09-21 审计修复轮：守卫破坏→自检红→恢复绿） =====
    from unittest import mock
    from gui import models as _models
    from gui.app import run_self_check
    check("S3 守卫基线自检绿", run_self_check().ok)
    with mock.patch.object(_models, "OUTPUT_OPS",
                           _models.OUTPUT_OPS - {"filter"}):
        r_bad = run_self_check()
        bad_names = [i.name for i in r_bad.items if not i.ok]
        check("S3 破坏产表口径→自检红", not r_bad.ok, str(bad_names))
    check("S3 恢复后自检绿", run_self_check().ok)

    # ===== M5 场景（M5-a：t_{uid} 漂移根治） =====
    # -- M5a-S1 物理名=t_{uid} + move_step 调序漂移免疫 + tooltip 回写 --
    m5a = WorkflowModel()
    m5a.set_tables([{"table_id": "T1", "alias": "员工", "sqlite_table": "t1"}])
    fa = m5a.add_step("filter")        # → T101
    m5a.add_step("aggregate")          # → T102
    d1 = m5a.to_dict()
    names1 = {s.uid: sd["params"]["output_table"]
              for s, sd in zip(m5a.steps, d1["steps"])}
    check("M5a 物理名=t_{uid}",
          all(v == f"t_{k}" for k, v in names1.items()), str(names1))
    # R6/F1：move_step 已删（H2 清理轮裁定）——调序等效序列 remove+insert；
    # 漂移免疫断言仅对未参与调整的步骤执行（M5 方案 remove+add 口径）
    uid_agg = m5a.steps[1].uid
    m5a.remove_step(0)                 # 删 filter（原 S1）
    m5a.insert_step(1, "filter")       # 末位重插 → 序＝[aggregate, filter]
    d2 = m5a.to_dict()
    names2 = {s.uid: sd["params"]["output_table"]
              for s, sd in zip(m5a.steps, d2["steps"])}
    check("M5a 调序后未参与步骤物理名不变",
          names2.get(uid_agg) == names1.get(uid_agg) == f"t_{uid_agg}",
          str(names2))
    check("M5a 调序等效序列成立",
          [s.type for s in m5a.steps] == ["aggregate", "filter"],
          str([s.type for s in m5a.steps]))
    # tooltip 回写链：共享 op 在 S2-T9 已清场，改用局部页面验证同一链路
    # （set_output_tables({T101: t_{uid}}) → 表节点 toolTip，断言语义不变）
    opm5 = OperationConfigPage(m5a, UserTemplateManager())
    opm5.set_input_tables([
        {"table_id": "T1", "alias": "员工", "sqlite_table": "t1",
         "columns": ["a", "b"]},
    ])
    opm5._refresh_graph()
    opm5.set_output_tables({fa.output_table_id: f"t_{fa.uid}"})
    item = opm5._scene._table_items.get(fa.output_table_id)
    check("M5a tooltip 回写", item is not None
          and f"t_{fa.uid}" in (item.toolTip() or ""),
          item.toolTip() if item else "missing")

    # ===== M5 场景（M5-b：三态锚点插入） =====
    # -- M5b-S1 六态锚点解析 --
    mb = WorkflowModel()
    mb.set_tables([{"table_id": "T1", "alias": "员工", "sqlite_table": "t1"},
                   {"table_id": "T2", "alias": "标准", "sqlite_table": "t2"}])
    mb.add_step("filter")      # → T101，target=T1
    mb.add_step("aggregate")   # → T102，target=T1
    mb.add_step("export")      # is_end，target=T1
    opb = OperationConfigPage(mb, UserTemplateManager())
    opb.set_input_tables([
        {"table_id": "T1", "alias": "员工", "sqlite_table": "t1",
         "columns": ["a", "b"]},
        {"table_id": "T2", "alias": "标准", "sqlite_table": "t2",
         "columns": ["a", "c"]},
    ])
    opb._refresh_graph()
    opb._selected_step_index = -1
    opb._selected_table_id = None
    check("M5b① 无选中→2（末步 is_end 插其前）",
          opb._resolve_insert_index() == 2)
    opb._select_step(0)
    check("M5b② 选中步0→1", opb._resolve_insert_index() == 1)
    opb._select_step(2)
    check("M5b③ 选中 export→2（C2 保护）",
          opb._resolve_insert_index() == 2)
    opb._select_table("T102")
    check("M5b④ 选 T102→2（产出步后 p+1）",
          opb._resolve_insert_index() == 2)
    opb._select_table("T101")
    check("M5b④注 选 T101→1", opb._resolve_insert_index() == 1)
    opb._select_table("T1")
    check("M5b⑤ 选 T1→2（is_end 不计入消费者）",
          opb._resolve_insert_index() == 2)
    opb._select_table("T2")
    check("M5b⑥ 选 T2→2（两者皆无走③）",
          opb._resolve_insert_index() == 2)
    # -- M5b-S2 ①变体：去 export，末步非 is_end→纯末尾 --
    mb_v = WorkflowModel()
    mb_v.set_tables([{"table_id": "T1", "alias": "员工",
                      "sqlite_table": "t1"}])
    mb_v.add_step("filter")
    mb_v.add_step("aggregate")
    opv = OperationConfigPage(mb_v, UserTemplateManager())
    opv.set_input_tables([{"table_id": "T1", "alias": "员工",
                           "sqlite_table": "t1", "columns": ["a", "b"]}])
    opv._refresh_graph()
    opv._selected_step_index = -1
    opv._selected_table_id = None
    check("M5b①变体 去 export→2（纯末尾 len==2）",
          opv._resolve_insert_index() == 2)
    # -- M5b-S3 联动：选中步0后插入 + K7 联动 + K8 不压栈 --
    depth0 = len(opb._undo_stack)
    opb._select_step(0)
    opb._on_add_step("dedup")
    check("M5b 联动 len==4", len(mb.steps) == 4)
    check("M5b 联动 新步位1", mb.steps[1].type == "dedup")
    check("M5b 联动 选中态==1", opb._selected_step_index == 1)
    check("M5b 联动 画布高亮 S2",
          opb._scene._selected == ("step", "S2"),
          str(opb._scene._selected))
    check("M5b 联动 插入不压栈（K8）",
          len(opb._undo_stack) == depth0)
    # -- M5b-S4 撤销交互：删新步→压栈→撤销恢复 4 步原序 --
    opb._on_delete_step(1)
    check("M5b 删除压栈", len(opb._undo_stack) == depth0 + 1)
    check("M5b 删除后 3 步", len(mb.steps) == 3)
    ok_undo = opb._undo_last()
    check("M5b 撤销返回 True", bool(ok_undo))
    check("M5b 撤销恢复 4 步原序",
          len(mb.steps) == 4 and mb.steps[1].type == "dedup"
          and [s.step_id for s in mb.steps] == ["S1", "S2", "S3", "S4"])
    # -- M5b-S5 空流程变体 --
    mb2 = WorkflowModel()
    mb2.set_tables([{"table_id": "T1", "alias": "员工", "sqlite_table": "t1"}])
    opb2 = OperationConfigPage(mb2, UserTemplateManager())
    opb2.set_input_tables([{"table_id": "T1", "alias": "员工",
                            "sqlite_table": "t1", "columns": ["a", "b"]}])
    opb2._refresh_graph()
    check("M5b 空流程→0", opb2._resolve_insert_index() == 0)
    mb2.insert_step(0, "filter")
    check("M5b 空流程插入 S1",
          len(mb2.steps) == 1 and mb2.steps[0].step_id == "S1")

    # ===== M6 场景（R6 批次 A：诚实报告 + 中间表标注 + 表单增量合并） =====
    # -- M6-A2/A3 报告页：部分完成文案 + 中间结果标注 --
    from gui.page_report import ReportPage
    rp = ReportPage()
    rp.fill("completed_partial", 1, 2, [], [], 0.5,
            output_tables={"T101": "t_demo1", "T102": "t_demo2"},
            overwrite_ids={"T101"})
    txt = rp._browser.toPlainText()
    tech = rp._tech_browser.toPlainText()
    check("M6 A2 部分完成文案",
          "部分完成" in txt and "跳过" in txt, txt.splitlines()[0])
    check("M6 B1 主区无物理名（技术详情折叠，P0-2/D9）",
          "t_demo1" not in txt and "t_demo2" not in txt)
    check("M6 A3 中间结果标注（技术详情区）",
          "中间结果" in tech and "（输出）" in tech)
    check("M6 B1 技术详情默认隐藏", not rp._tech_browser.isVisible())
    check("M6 A2 部分完成允许存模板", rp._save_btn.isEnabled())
    rp.fill("completed", 2, 2, [], [], 0.5)
    check("M6 A2 正常完成回归", "正常完成" in rp._browser.toPlainText())
    rp.fill("failed", 0, 2, [], [], 0.5)
    check("M6 A2 失败态禁存模板", not rp._save_btn.isEnabled())

    # -- M6-A4 表单收拢增量合并：logic=OR / output_mode 注入往返不丢 --
    m6 = WorkflowModel()
    m6.set_tables([{"table_id": "T1", "alias": "员工", "sqlite_table": "t1"}])
    f6 = m6.add_step("filter")
    f6.params = {"conditions": [{"column": "a", "op": ">", "value": "1"}],
                 "logic": "OR", "output_mode": "overwrite_target"}
    a6 = m6.add_step("aggregate")
    a6.params = {"group_by": ["a"],
                 "metrics": [{"func": "count", "column": "*", "alias": "n"}],
                 "output_mode": "overwrite_target"}   # _cp 折叠注入形态
    op6 = OperationConfigPage(m6, UserTemplateManager())
    op6.set_input_tables([{"table_id": "T1", "alias": "员工",
                           "sqlite_table": "t1", "columns": ["a", "b"]}])
    op6._refresh_graph()
    op6._select_step(0)      # 挂载 filter 表单（无 logic 控件）
    op6._select_step(1)      # 收拢 step0 → 增量合并
    check("M6 A4 logic=OR 往返不丢",
          m6.steps[0].params.get("logic") == "OR",
          str(m6.steps[0].params.get("logic")))
    check("M6 A4 filter output_mode 往返不丢（有控件路径）",
          m6.steps[0].params.get("output_mode") == "overwrite_target")
    op6._select_step(0)      # 收拢 aggregate 表单（无 output_mode 控件）
    check("M6 A4 aggregate 注入 output_mode 不丢",
          m6.steps[1].params.get("output_mode") == "overwrite_target",
          str(m6.steps[1].params))

    print()
    if FAILS:
        print("SMOKE_FAIL:", FAILS)
        return 1
    print("SMOKE_ALL_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
