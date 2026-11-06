# W-03 审查发现修复轮报告（F1-F10 零遗留闭环）

> **⚠ 归档注记（2026-09-24 R10）**：本文件为历史轮次快照，正文未改写。现位于 `_temp/ledger_2026-09-24/`；文中指向已清理 `_temp` 件（GUI 细节方案／M5 设计／审计报／审计方案／运行流程简报／repo-context／verify 留痕）的旧路径，其章节骨架与结论沉淀位置见同夹 `CLEANUP_MANIFEST.md` §2～§3，引用对账见 §5。

> 日期：2026-09-21｜执行：模式 B（主控实施，3 只读子 agent 素材复核于审查轮）｜状态：**已完成，全部发现闭环**
> 依据：`_temp/W-03_runtime_flow_and_tech_brief.md` 第三部分 F1-F10；冻结方案 `_temp/W-03_GUI_detail_optimization_plan.md`（只读，未修改）；获批执行计划 `.trae/documents/W-03审查发现修复轮执行计划.md`。

## 1. 任务理解与验收标准

对上一轮只读审查的 10 条发现逐条自适应处置（修复/显式延期/判非问题/待人工确认），确保零遗留；全量回归（52+新增用例、33 项冒烟、6 项自检）与 FF1-FF5 全绿；修改限于 gui/tests/_temp；零新依赖；不触 SampleCode/docs/AGENTS/ops 架构/生产 SQLite；不涉 D-B3/D-C3 独立议题。

## 2. 规约读取与技术栈确认

- AGENTS.md（R3 锚点在案）：红线 §2.1/§2.2 全遵守；`rpa_engine/tests/` 豁免通道内新增用例；**冲突记录**：用户边界禁改 AGENTS.md ⇒ 本轮锚点/task-record（docs/）更新**显式延期至治理轮**（见 §8 延期表），修复记录以本报告为载体。
- 技术栈未变：Python 3.11.15 / PyQt5 5.15.2 / SQLite WAL / pandas / loguru / openpyxl / unittest；新增文件 import 仅标准库+项目内（复检 grep 证实：json/sqlite3/tempfile/unittest/pathlib + engine/gui 模块）。
- 冻结方案未修改；SampleCode 未触碰；engine/ 仅只读走查（executor/step_executor 零改动——F2 修复落 GUI 层计数口径，未动引擎）。

## 3. 发现来源

`_temp/W-03_runtime_flow_and_tech_brief.md` 第三部分 F1-F10（上一轮多 agent 审查产出，原文完整在案，非重建）。

## 4. 发现 → 处置表（零遗留）

| # | 类别 | 处置 | 涉及文件与函数 | 验证方式 | 验证结果 |
|---|------|------|----------------|----------|----------|
| F1 | 执行期画布失联（高） | **已修复** | page_operation_config.py 新增公共 `refresh_graph()`；main_window.py `start_workflow` 在 worker.prepare 后、reset_runtime_status 前调用（renumber 后 scene 键与信号 S{n} 对齐） | smoke F1 场景：add_step→refresh→to_dict(renumber)→断言旧键失联（stale=['S3']）→refresh_graph→scene 键==模型 step_id→update_step_status("S1",RUNNING) 命中生效 | ✅ 3 检查点全过 |
| F2 | 报告页计数失真（中） | **已修复** | main_window.py `__init__` 增 `_exec_total`；`start_workflow` parse 后 `=len(workflow.steps)`（含 cp 合成步）；`_on_workflow_finished` fill total 改 `_exec_total or len(model.steps)` | smoke F2 场景：overwrite 模型 1 步 → to_dict 2 步（+cp）断言；test_engine_overwrite `test_translation_structure` 同口径断言 | ✅ |
| F3 | 撤销栈边界（中） | **已修复** | page：快照增 `next_step_num`（_push_undo/_undo_last）；`_undo_gen` 代际号 + `_hide_undo_bar_if(gen)`（旧代际不隐藏）；新增公共 `reset_undo_stack()`；restore_config 末尾调用；main_window `_new_round` 调用 | smoke F3 场景：连续压栈 gen 递增、旧代际回调不隐藏、当前代际隐藏、快照含 next_step_num、撤销复原 | ✅ 5 检查点全过 |
| F4 | reconcile/刷新旁路（中） | **已修复** | page `_on_target_changed` 直写后加 `model.reconcile()`；`_harvest_current_form` try_apply 成功写回后 `reconcile()` + output_mode 变化时 `_refresh_graph()`（produce 边/派生表节点即时更新）；combo 初始化直写与 _on_target_changed 信号同源已覆盖 | smoke F4 场景：模板超界引用 load_session 后 `table_states["T9"]=="dangling"` 即时成立；57 用例回归 reconcile 语义无破坏 | ✅ |
| F5 | 死代码五项（低） | **部分修复+部分判非问题** | 删 page `get_staged_config`（零调用且口径与编辑态暂存策略相悖，留删除说明注释）；**保留判非问题**：`set_output_mode`（冻结方案 M2-T3 交付物，UI 经表单直写 params 属既定实现）、`move_step`（模型通用 API，零调用无害，冻结方案未要求删除）、`table_states`（冻结方案 §7.3 状态机投影交付物，测试/撤销快照/F4 修复消费）、`main_buttons/more_buttons`（自检 4b 分组完备守卫 + test_step_catalog 消费，D17 派生规则载体） | grep `def get_staged_config\|\.get_staged_config\(` 0 命中；保留项依据本表留痕 | ✅ |
| F6 | 单一事实源旁路（低） | **已修复** | page 装配 `is_end=(step.type=="export")` 改 `is_end_op(step.type)`（import 自 models，与 graph_edges/normalize_end 同源）；`_table_display` 改委托 `model.alias_of` 单一源（registry 别名兜底） | grep `is_end=\(step\.type` 0 命中；52+5 用例回归（normalize_end/alias_of 断言在案） | ✅ |
| F7 | 跨层私有调用（低） | **已修复** | models 新增公共委托 `alloc_table_id(extra_used)`/`deprecated_closure()`（私有实现保留）；page 两处调用改公共名（_map_template_ids/_confirm_active_steps） | grep `model\._alloc_table_id\(\|model\._deprecated_closure\(` 0 命中 | ✅ |
| F8 | 测试盲区（中） | **已修复（⑦延期人工）** | ①F1 链→smoke F1 场景；②overwrite 两步链执行期实测→新建 tests/test_engine_overwrite.py（内存 SQLite 真执行：t1 覆盖为筛选结果 [2,3]、output_tables["T101"]=="t_s1"、validate 通过）；③cp 计数→smoke F2+单测结构断言；④模板映射→smoke F6 超界场景补齐；⑤recent_steps 降级→新建 tests/test_recent_steps.py（损坏 JSON 空列表/去重置顶上限 5/缺文件空列表，备份恢复不污染用户数据）；⑥撤销定时→smoke F3 gen 场景；⑦弹窗真机交互→**显式延期**（offscreen 无法覆盖真实 DPI/鼠标事件，列真机清单） | 57 用例全绿 + smoke_m1m3 全场景 ALL_OK | ✅（⑦见 §8） |
| F9 | 废弃残留 | **判定非问题** | 复检：`_next_table_num/MAIN_BUTTONS 常量/QTextEdit 实例/table_reorder/_clear_extra_ref/highlight_step/_build_columns/StepNode/TableNode` 大小写敏感全仓 grep **0 命中**（PowerShell 5 命中为大小写不敏感误报，实为合法函数 `main_buttons()`；page_input_selection L107 注释提及属说明性文字） | Grep 工具（大小写敏感）全仓 0 命中 | ✅ 干净 |
| F10 | 配置期不写 SQLite | **判定非问题** | 复检成立：SQLite 写入仅阶段1导入（main_window `_on_confirm_import`）与执行期 worker/executor；gui/ 无 sqlite3 直连；本轮新增引擎测试用 `sqlite3.connect(":memory:")`+tempfile，零生产库写入 | grep gui/ 0 命中 + 测试代码走查 | ✅ 合规 |

## 5. 本轮修改文件清单

| 文件 | 改动摘要 | 对应发现 |
|---|---|---|
| rpa_engine/gui/page_operation_config.py | refresh_graph 公共口；undo 快照 next_step_num/gen 代际/reset_undo_stack/_hide_undo_bar_if；restore_config 清栈；_on_target_changed+reconcile；harvest reconcile+mode 变化刷新；删 get_staged_config；is_end_op；_table_display 委托 alias_of；两处公共委托改接 | F1/F3/F4/F5/F6/F7 |
| rpa_engine/gui/main_window.py | _exec_total 初始化+赋值+fill 口径；start_workflow 挂 refresh_graph；_new_round 挂 reset_undo_stack | F1/F2/F3 |
| rpa_engine/gui/models.py | 公共委托 alloc_table_id/deprecated_closure | F7 |
| rpa_engine/tests/test_engine_overwrite.py | **新建**：两步链翻译结构+内存 SQLite 真执行覆盖实测（2 用例） | F8② |
| rpa_engine/tests/test_recent_steps.py | **新建**：损坏降级/去重上限/缺文件（3 用例，备份恢复） | F8⑤ |
| _temp/DAG-rebuild/smoke_m1m3.py | 追加 F1/F2/F4/F6/F3 五组修复验证场景（13 检查点） | F1-F4/F6/F8 |
| _temp/ledger_2026-09-24/W-03_fix_round_2026-09-21/REPORT.md | 本报告（新建目录+文件） | — |

未修改：SampleCode/、docs/、AGENTS.md、ops/、engine/（executor/step_executor 零改动）、forms.py、node_graph.py、graph_edges.py、styles.py、worker.py、冻结方案文件。

## 6. 测试与回归结果

| 门禁 | 结果 |
|---|---|
| `python -m unittest discover -s tests` | **Ran 57 tests OK**（52 基线 + test_engine_overwrite 2 + test_recent_steps 3；零回归） |
| smoke_mb.py（33 项基线） | SMOKE_ALL_OK |
| smoke_m1m3.py（M1-M4 + F 修复场景全量） | SMOKE_ALL_OK（F1 3 项/F2 1 项/F6+F4 2 项/F3 5 项全过） |
| run_self_check() | SELF_OK（6 项） |
| FF1 表编号唯一 | test_models_data AllocatorTest/CollisionTest + smoke 零撞号 ✅ |
| FF2 三键集一致 | 自检项 4/4b ✅ |
| FF3 五类边计数 | smoke_mb ✅ |
| FF4 点击行==选中行 | smoke M1-S2 ✅ |
| FF5 弹层项数==非弃用键数 | smoke M3-S1（卡片 9）✅ |

失败与修复过程：本轮回归一次通过，无失败项（smoke F1 场景首版 status=None/属性名 `_status` 两处脚本笔误，执行前修正为 NodeStatus.RUNNING/`status`）。

## 7. 复检扫描结果

- 新增问题：**无**（57 用例+双冒烟+自检全绿；F 场景 13 检查点全过）。
- 回归：**无**（52 基线用例零改动零失败；smoke_mb 33 项不变）。
- 悬空项：**无**（10 条发现全部有处置状态，见 §4）。
- 越界检查：修改文件仅 gui(3)+tests(2 新建)+_temp(2)；无新第三方 import；SampleCode/docs/AGENTS/ops/engine 零触碰；生产 SQLite 零写入（引擎测试用内存库+tempfile）。
- 死代码/私有跨层/is_end 直判/get_staged_config：grep 全 0 命中。

## 8. 零遗留清单

**已修复（7）**：F1、F2、F3、F4、F6、F7、F8（①-⑥）。
**判定非问题（4 项记录）**：F5 保留四项（set_output_mode/move_step/table_states/main_buttons——冻结方案交付物/守卫用途，依据见 §4）、F9（残留清零证实）、F10（合规证实）。
**部分修复（1）**：F5（get_staged_config 已删）。
**显式延期（3，均不影响本轮验收）**：
| 延期项 | 理由 | 影响评估 | 后续里程碑 |
|---|---|---|---|
| F8⑦ 弹窗真机交互自动化 | offscreen 平台无法覆盖真实 DPI/鼠标命中 | 低（FF4 已自动化等价断言；真机清单第 1-5 条承接） | 真机验收轮 |
| AGENTS 锚点/task-record 更新 | 用户本轮边界禁改 AGENTS.md，docs/ 保守不动 | 低（本报告为追溯载体；锚点仍指 R3 记录，无信息丢失） | 治理轮（人工放行后） |
| D17 主按钮派生确认 / [已过时-待确认] 3 项 | 人工裁定事项，非代码缺陷 | 无（现状可用） | 人工验收轮 |

**待人工确认（0 新增）**：上轮遗留人工事项不变（真机清单 18 条、exe 重建 W-20）。

## 9. 风险、建议与后续里程碑

- 风险：F1 修复使 start_workflow 多一次画布重建（毫秒级，无感知）；F2 口径变化后报告页 total 含 cp 步（与进度页行数一致，语义更准）。
- 建议后续：①真机验收轮跑 task-record 18 条+本轮 F 场景人工复核；②治理轮补锚点 R4+task-record（含本报告索引）；③M5 独立议题（D-B3/D-C3）人工立项时以 uid 消费者补全为契机评估 t_{uid}。

## 10. 声明

本轮实际修改文件＝§5 清单 7 项；未修改 SampleCode/docs/AGENTS/ops/engine/冻结方案；零新第三方依赖；生产 SQLite 零写入；全部结论附证据（grep/测试结果/文件+函数定位）。**当前停止，等待人工下一步指令。**
