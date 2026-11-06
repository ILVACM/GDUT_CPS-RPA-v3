# 任务记录：W-03 三细节问题 M1-M4 实施闭环（表头选择重构 / Ribbon 弹层 / 数据层一致性）

> 日期：2026-09-21｜执行：模式 B（主控实施，无子 agent）｜状态：已完成（R3；R2=M0 DAG 重构闭环）
> 依据：`_temp/W-03_GUI_detail_optimization_plan.md`（定稿 [冻结]，12 项决策人工裁定）＋
> `.trae/documents/W-03三细节问题实施执行计划.md`（获批执行计划）。

## 摘要

按定稿串行实施 M1（表头行选择 QTableView 重构）→ M2（uid/最小空号分配器/七态状态机/
级联 B/load_session 单一入口/撞号检测/撤销栈/执行期回写）→ M3（StepMeta 注册表 +
Qt.Popup 功能区弹层 + 最近使用 + 添加联动）→ M4（单测扩充 + 四阶段链路冒烟 + 治理收尾）。
测试基线 22 → **52 用例全绿**；smoke_m1m3 全场景（M1-M4）SMOKE_ALL_OK；自检 6 项 ALL_OK。

## 用户输入

- 「效果符合预期，继续开发，完成所有剩余工作」（M0 轮）→ 本轮：「开始实施」（定稿获批）。

## Agent 理解与决策（实施级细化，不改变定稿决策）

| # | 决策 | 说明 |
|---|---|---|
| D16 | **级联 B 采"保留引用"解释**（定稿矛盾调和） | 定稿 M2-T4 wording"置空"与 §7.4 dangling 视觉不可同时成立（置空后引用消失即无 dangling 边）；保留下游对已删派生表编号的引用 → missing_refs 判"表不存在" → dangling 边/红虚线/缺输入角标/待配置橙边框/用户重指全链路自洽；调和记录同时写入 models.remove_step docstring |
| D17 | main/more 按钮＝分类代表派生 | 定稿 M3-T2"category+order 派生"唯一自洽规则：每分类 order 最小者为主按钮（4 分类→4 主按钮：filter/mapping_match/copy_table/export），其余归 more；与 09-15 定案 5 的 MAIN 列表差异（aggregate↔export）记录在案，人工如需恢复旧 4 项改 category 代表规则或加 main 字段一行 |
| D18 | recent_steps 落独立文件 gui/recent_steps.py | 定稿允许二选一；独立以隔离 IO 与降级逻辑 |
| D19 | smoke_m1m3 增量创建 | M1 骨架→M2/M3/M4 场景追加，满足各里程碑即时门禁；终态即定稿 M4-T2 DoD |
| D20 | page_report.fill 增参采用末尾可选参 | 旧调用兼容；worker 信号 (str,float)→(str,float,dict) 单连接点同步 |
| D21 | 合并单元格填充落 dialog 层 | openpyxl read_only 取不到 merged_cells 范围；空值前向填充启发式在 `_HeaderRowDialog._forward_fill_merged` 执行并记录填充列供摘要标注（DoD 不变：无空洞+标注） |

## 执行流程

1. **M1**：page_input_selection.py——`_HeaderRowDialog` 重构（QTableView+QStandardItemModel+`_HeaderBadgeDelegate` 徽章/行高≥28/整行高亮；摘要 QLabel 富文本解耦；`_on_row_clicked` 命中只认 index.row()；resize 860×520+双向滚动+ResizeToContents 首列 Fixed；`_PREVIEW_ROWS` 20→50；空表按钮禁用+QMessageBox；合并填充+摘要标注；mangle 规则不变）。修复 0 列时 `setSectionResizeMode(0,…)` 越界 access violation。
2. **M2**：models.py——uid（`_new_uid` uuid4 hex[:8]，to_dict 剔除，set_tables/load_from_dict 生成）；`_alloc_table_id(extra_used)` T101+ 最小空号（删 `_next_table_num`）；`reconcile()` 七态投影+弃用集摘除消失表；`set_output_mode/reset_steps/validate_table_ids_unique`；`remove_step` 级联 B（D16）；`load_session(registry,data)` 单一入口。graph_edges `detect_table_id_collisions` 入 `__all__`（specs_from_model 签名未动）。调用点改接：main_window L266/L286/L497 区、page 模板（新增 `_map_template_ids` 位置映射：输入按序+派生重分配）/restore_config。worker 信号扩参+out_tables；main_window `_on_workflow_finished` 回写；node_graph `set_output_tables` tooltip（rebuild 后重应用）；page_report.fill 增列。page 撤销栈 `_push_undo/_undo_last/_on_undo_clicked/_show_undo_bar/_hide_undo_bar`（deque maxlen=10 + QTimer 5s）挂删除/清空/模板三钩子。
3. **M3**：models.py——`StepMeta` dataclass（`__getitem__`/`__iter__` 兼容层）+ `_STEP_META_RAW` 9 项（display/desc 与旧 tuple 逐字一致）+ `display_name/main_buttons/more_buttons/categories/category_ops`；删 MAIN_BUTTONS/MORE_BUTTONS 硬编码列表。app.py 项4b 增 StepMeta 字段完整性+order 唯一+分组派生断言。page——单一「添加功能步骤 ▾」QToolButton + `_build_add_popup`（Qt.Popup：搜索框默认聚焦/最近使用区/四分组网格卡片/弃用置灰）+ `_filter_popup/_toggle_add_popup/_on_add_popup_clicked/_refresh_recent_box`；`_on_add_step` 添加后 push_recent+自动 `_select_step`+`scene.select_node`；`_build_step_param_panel` 改 display_name（双下标清零）。node_graph `select_node` 公共方法（不发信号防环）。新建 gui/recent_steps.py（storage/recent_steps.json，≤5 去重，降级不崩）。
4. **M4**：tests 新增 test_step_catalog.py（12 项）+ test_graph_edges.py 扩 CollisionDetectionTest（3 场景）；smoke_m1m3 追加 M4 场景（模板映射/零撞号/to_dict→parse→validate 闭环/清空→撤销）；README 目录树同步；本记录＋AGENTS 锚点 R3。

## 涉及文件

| 文件 | 改动 |
|---|---|
| rpa_engine/gui/page_input_selection.py | M1 全量重构（弹窗/Delegate/50 行/空表/合并填充） |
| rpa_engine/gui/models.py | uid/分配器/reconcile/级联 B/load_session/StepMeta/派生函数/删硬编码列表 |
| rpa_engine/gui/graph_edges.py | detect_table_id_collisions + __all__ |
| rpa_engine/gui/page_operation_config.py | 调用点改接/模板映射/撤销栈/undo bar/Ribbon 弹层/添加联动/set_output_tables |
| rpa_engine/gui/main_window.py | load_session 三处/_on_workflow_finished 扩参回写 |
| rpa_engine/gui/worker.py | workflow_finished 信号扩参 + out_tables |
| rpa_engine/gui/node_graph.py | set_output_tables/select_node + rebuild 重应用 |
| rpa_engine/gui/page_report.py | fill 增 output_tables 可选参+派生表→物理名列 |
| rpa_engine/gui/recent_steps.py | **新建**（最近使用持久化） |
| rpa_engine/gui/app.py | 项4b StepMeta 完整性+分组派生断言 |
| rpa_engine/tests/test_models_data.py | **新建**（15 项） |
| rpa_engine/tests/test_step_catalog.py | **新建**（12 项） |
| rpa_engine/tests/test_graph_edges.py | 扩 CollisionDetectionTest（3 场景，共 17 项） |
| _temp/DAG-rebuild/smoke_m1m3.py | **新建**（M1-M4 全场景冒烟） |
| rpa_engine/README.md | 目录树同步（recent_steps/tests 4 文件） |
| AGENTS.md | 锚点 R3 + §8 主线 |

engine/ops 与 SampleCode **零改动**；git 操作留人工。

## 验收

- ✅ `python -m unittest discover -s tests` → **Ran 52 tests OK**（22 基线 + 15 + 12 + 3）。
- ✅ `_temp/DAG-rebuild/smoke_mb.py` → SMOKE_ALL_OK（33 项基线无回归）。
- ✅ `_temp/DAG-rebuild/smoke_m1m3.py` → SMOKE_ALL_OK（M1 18 项 + M2 10 项 + M3 12 项 + M4 8 项场景）。
- ✅ `run_self_check()` → 6 项 ALL_OK（项4b 含 StepMeta 完整性）。
- ✅ grep 门禁：`blockNumber/self._text/<-- 表头` 0 命中；生产代码 `.set_tables(`/`_next_table_num` 0 命中；`STEP_CATALOG[x][0]` 双下标 0 命中；MAIN_BUTTONS/MORE_BUTTONS 0 命中。
- ✅ FF1-FF5：唯一性（单测+冒烟零撞号）/三键集（自检 4b）/五类边计数（smoke_mb）/点击行==选中行（smoke M1-S2）/Ribbon 项数==非弃用键数（smoke M3-S1 卡片 9）。

## 真机人工验收清单（≥15 条，待人工）

1. 表头弹窗：单击第 N 行→徽章唯一+摘要同步「第 N 行」；摘要区/空白点击不误选。
2. 表头弹窗：50 行 xlsx 双向滚动可见全列；列宽自适应不溢出。
3. 表头弹窗：空 sheet 行按钮灰置+点击提示；合并单元格表头无空洞+摘要「(合并)」标注。
4. 表头弹窗：重复列名预警橙色 span+ mangle(.1) 与导入后真实表头一致。
5. 125%/150% DPI 下弹窗与主表不错位不裁字。
6. 删除中间步骤：下游卡片红虚线短桩+⚠+「输入缺失」角标+橙边框；右面板连线说明含悬空提示。
7. 删除/清空/应用模板后 5 秒撤销条出现；点撤销完全复原；超时自动消失。
8. 执行结束后悬停派生表节点 tooltip 显示「物理表: t_s{n}」；报告页列「派生表 → 物理表名」。
9. 「添加功能步骤 ▾」唯一入口一眼认定；弹层外点/ESC 关闭；搜索框默认聚焦。
10. 弹层搜索「vlookup」仅命中跨表映射匹配；空搜索全显示；四分组标题序正确。
11. 最近使用：添加 filter 后重开弹层置顶显示；重启后保持；≤5 去重。
12. 添加步骤后右侧内联表单立即展开+画布卡片选中高亮。
13. 应用模板：输入表按序映射、派生表新号无撞号；画布列与目标表下拉一致。
14. 清空→撤销：步骤与弃用态完全复原。
15. 改中文名（StepMeta.display）后旧模板/last_config 正常打开（key 稳定铁律）。
16. 主按钮 4 项（filter/跨表映射匹配/数据表复制/结果导出）与「更多功能」弹层分组符合 D17 派生预期（人工确认接受或要求调整）。
17. exe 重建判据：docs/build-guide.md §1.10（人工重建后全清单复跑）。
18. [已过时-待确认] 3 项裁定：正本 §5.9 #9（焦点模式 0.15 暗化）/#11（tooltip）/#15（右键菜单）——现行口径为选中联动 0.3 淡化/无 tooltip/画布只读无右键菜单，请人工归档裁定。

## 关闭标识

**本轮（R3/M1-M4）完成**：定稿 26 任务全落地；M5 独立议题（D-B3 插入锚点、D-C3 物理名
t_{uid}）未启动，留人工立项。

**待人工**：真机清单 18 条；exe 重建（W-20）；D17 主按钮派生结果确认；[已过时-待确认] 3 项裁定。
