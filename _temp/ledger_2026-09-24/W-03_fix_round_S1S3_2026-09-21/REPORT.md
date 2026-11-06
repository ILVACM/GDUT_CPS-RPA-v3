# W-03 审计方案 S1-S3 实施轮报告（零遗留闭环）

> **⚠ 归档注记（2026-09-24 R10）**：本文件为历史轮次快照，正文未改写。现位于 `_temp/ledger_2026-09-24/`；文中指向已清理 `_temp` 件（GUI 细节方案／M5 设计／审计报／审计方案／运行流程简报／repo-context／verify 留痕）的旧路径，其章节骨架与结论沉淀位置见同夹 `CLEANUP_MANIFEST.md` §2～§3，引用对账见 §5。

> 日期：2026-09-21｜执行：模式 B（主控实施）｜依据：`_temp/W-03_table_step_audit_solution_plan.md`（施工图级，修订三；人工批准）＋ `.trae/documents/审计方案S1-S3实施执行计划.md`（获批）。
> 边界遵守：仅改 rpa_engine/gui、engine/validator.py、ops/step_executor.py（仅注释）、rpa_engine/tests、_temp；SampleCode/docs/AGENTS/冻结方案零触碰；零新第三方依赖；生产 SQLite 零写入。

## 1. 实施摘要（S1/S2/S3 全落地）

- **S1 高危轮**：P1 编辑态无损化——`to_dict` 双口径分叉（编辑态 get 保留 output_mode+不展开 _cp；业务口径 pop+展开不变）＋模板出口切编辑态（`_on_save_current_config`）＋ `_collapse_copy_steps` 三级父步定位折叠迁移（load_from_dict 接线，存量业务口径文件自动修复）；P2——models 新增 `apply_registry`，`_on_confirm_import` 改接（启动恢复步骤不再被清空）。
- **S2 小修轮（9 组）**：P3 撞号双接线（page `_check_table_ids_unique` 挂开始/保存两入口＋validator `validate_tables(tables, steps=None)` 交叉查重）；P4 进度页 meta 改 workflow.steps 同源（含 cp 行）；P5 清空压栈前补 harvest；P6 `_alloc_table_id` used 并入 dangling 键集（防复活）；P7 InputEntry.source_path＋(源文件,sheet) 查重＋一次性提示；P8 `ordinal_map/title_of` 纯函数＋四处收口（卡片装配/面板头/_sname/alias_of）；P9a `_map_template_ids` 兜底剥离 output_table＋warning；P9c TableSpec.sqlite_table＋输入表构造期 tooltip；P9d `_new_round` 补 `set_input_tables([])`。
- **S3 守卫轮**：R2 `test_produced_state`＋reconcile docstring/字段注释统一"6 记录态+1 隐式态"；R5 step_executor 注释区休眠标注；R6 自检项4 守卫①（跨层产表口径）＋项4b 守卫②③（default_params⊆param_keys／非弃用必有表单）＋GuardRuleTest 3 例＋smoke 守卫破坏场景（破坏→双项报红→恢复绿）。
- **S3-T4/T5（architecture.md 对齐/治理收尾）按方案约定跳过——待人工放行 H6**。

## 2. 修改文件清单（12 项）

| 文件 | 改动摘要 | 对应问题 |
|---|---|---|
| rpa_engine/gui/models.py | to_dict 双口径分叉+docstring；_collapse_copy_steps 新增+load_from_dict 接线；apply_registry 新增；_alloc_table_id 并入 dangling；ordinal_map/title_of 新增；alias_of 改 title_of；reconcile/字段注释 6+1 口径；loguru import | P1/P2/P6/P8/R2 |
| rpa_engine/gui/main_window.py | 模板保存 to_dict(True)；_on_confirm_import 改 apply_registry；meta 源改 workflow.steps；_new_round 补 set_input_tables([]) | P1/P2/P4/P9d |
| rpa_engine/gui/page_operation_config.py | _check_table_ids_unique 新增+两入口接线；_on_clear_steps 补 harvest；_map_template_ids 兜底剥离；装配/面板头/_sname 改实时标题+ordinals 预算；import 增 ordinal_map/title_of | P3/P5/P9a/P8 |
| rpa_engine/gui/page_input_selection.py | InputEntry.source_path；_add_row 形参+构造；set_entries/_rebuild_table 透传；_on_add_files 查重+一次性提示 | P7 |
| rpa_engine/gui/graph_edges.py | TableSpec.sqlite_table 字段+docstring；specs_from_model 输入表分支传参 | P9c |
| rpa_engine/gui/node_graph.py | TableItem.__init__ 构造期 tooltip | P9c |
| rpa_engine/gui/app.py | 自检项4 守卫①；项4b 守卫②③（import 增 BUILTIN_OPS/get_form_class/default_params/OUTPUT_OPS） | R6 |
| rpa_engine/engine/validator.py | validate_tables 签名扩 steps+交叉查重；validate_workflow 传参；Optional import | P3 |
| rpa_engine/ops/step_executor.py | 注释区 R5 休眠标注三行（零行为变化） | R5 |
| rpa_engine/tests/test_translation.py | test_load_regression 修正（编辑态保全断言）；+test_overwrite_editing_roundtrip | P1 |
| rpa_engine/tests/test_models_data.py | +CollapseTest 5 例；SessionTest +3 例；AllocatorTest +2 例；+TitleTest 3 例；StateMachineTest +test_produced_state | P1/P2/P6/P8/R2 |
| rpa_engine/tests/test_engine_overwrite.py | +ProgressMetaTest 1 例 | P4 |
| rpa_engine/tests/test_validator_cross.py | **新建** CollisionCrossTest 3 例 | P3 |
| rpa_engine/tests/test_step_catalog.py | +GuardRuleTest 3 例 | R6 |
| _temp/DAG-rebuild/smoke_m1m3.py | +S1 场景 8 项、S2 场景 15 项、S3 守卫场景 3 项 | 全部 |

## 3. 回归与门禁结果（全绿）

| 门禁 | 结果 |
|---|---|
| `python -m unittest discover -s tests` | **Ran 79 tests OK**（57 基线 + 22 新增：Collapse 5/Session 3/Allocator 2/Title 3/produced 1/roundtrip 1/CrossValidator 3/ProgressMeta 1/GuardRule 3；基线零回归） |
| smoke_mb.py（33 项基线） | SMOKE_ALL_OK |
| smoke_m1m3.py（M1-M4+F+S1/S2/S3 全场景） | SMOKE_ALL_OK（新增 26 检查点全过） |
| run_self_check() | SELF_OK 6 项（项4 含守卫①、项4b 含守卫②③） |
| FF1 表编号唯一 | 撞号双接线（GUI 拦截+引擎 raise）+ Allocator/Collision/Cross 8 用例 ✅ |
| FF2 三键集一致 | 自检 4/4b（含跨层产表口径）✅ |
| FF3 五类边计数 | smoke_mb ✅ |
| FF4 点击行==选中行 | smoke M1-S2 ✅ |
| FF5 弹层项数==非弃用键数 | smoke M3-S1 ✅ |

施工期修复 3 处（均即时闭环）：①models 缺 loguru import（NameError）→补；②孤立 _cp 夹具第三级兜底误命中→target 改 T999 落空；③alloc 断言 T102→T103（T102 已被 aggregate 占用，行为正确断言笔误）。另 smoke 两处场景隔离修正（output_tables 残留清理/new_round 前 model.reset）。

## 4. 复检扫描

- grep 门禁：`step_name=step\.name`/`model.set_tables(`/`get_form_classes`/`_next_table_num` 于 gui/*.py **0 命中**；page 内 load_session 仅模板应用（L1127）与 restore_config（L1223）两个合法单一入口调用点。
- graph_edges.py TableSpec 编辑错位（docstring 拼接损坏）当轮发现并修复，py_compile+79 用例证实无残留。
- 新增文件 import 面：test_validator_cross（engine.parser/validator+unittest）、GuardRuleTest（engine.registry/gui.forms/gui.models）——零第三方新增。
- 越界检查：修改仅限 §2 清单；docs/AGENTS/SampleCode/冻结方案零触碰；引擎侧仅 validator 结构校验+step_executor 注释（红线 §2.2-1/§2.2-5 不触）。

## 5. 零遗留清单

**已修复（13 修复项全落地）**：P1/P2/P3/P4/P5/P6/P7/P8/P9a/P9c/P9d/R2/R6——每项验证=对应用例+smoke 场景（§3）。
**判非问题/记录维持（5）**：P9b/R4（记录不改，复核锚点未变化）；R1（uid 休眠，M5 关联）；R3（move_step/set_output_mode 保留）；R5（注释标注落位，判定非缺陷）。
**待人工（4）**：
| # | 事项 | 说明 |
|---|---|---|
| H6 | docs/AGENTS 治理放行 | S3-T4（architecture.md 状态清单对齐 6+1 口径）与 S3-T5（锚点 R4+task-record）待放行后执行 |
| H2 | 调序 UI 恢复与否 | move_step 接线开关随裁定 |
| H4 | M5 提前立项 | t_{uid} 根治执行期物理名漂移＋uid 激活 |
| 真机 | 验收清单增补 | 既有 18 条＋本轮新增 6 条：覆盖模式重启恢复后仍为"覆盖原表"（P1）；启动恢复步骤在确认导入后保留（P2）；撞号弹窗拦截（P3）；进度页含"（写回原表）"行且计数一致（P4）；同文件二次添加跳过提示（P7）；删步后卡片标题序号自动收缩（P8） |

## 6. 声明

本轮实际修改文件＝§2 清单 15 项（代码 9+测试 5+smoke 1，含新建 test_validator_cross.py）；本报告为 _temp 新建；实施轮未修改 SampleCode/docs/AGENTS/冻结方案/生产 SQLite；零新第三方依赖；全部结论附验证证据。

## 7. 治理收尾完成节（H6 放行后追加，2026-09-21）

人工裁定：真机验收通过（24 条）／H6 放行／H2 不要／H4 要。落实结果：

| 项 | 处置 | 证据 |
|---|---|---|
| S3-T4 architecture.md 状态清单对齐 | **判无需改**：grep（declared/七态/dropped/状态机）零命中——对齐对象不存在；6+1 口径唯一载体=models.py reconcile docstring+table_states 字段注释（S3-T1 已落地） | grep 输出零命中；models.py L304-307/L535-543 |
| S3-T5 治理收尾 | 新建 `docs/task-records/2026-09-21-w03-audit-s1s3-fix-round.md`（R4 八节）；AGENTS 锚点 R4+§8 主线更新；doc-governance §4 校验过：容量含 CR 7,789/余量 211≥200、CRLF 复归 196/196（0 裸 LF）、锚点详情索引链接有效 | AGENTS 容量/CRLF 实测输出 |
| H2 关闭 | 调序 UI 不恢复；move_step 保留至下一清理轮删除（方案 §4.17 既定触发）——本轮零代码改动 | task-record 裁定表 |
| H4 立项 | **M5 已立项**：立项框架 `_temp/DAG-rebuild/M5_kickoff_plan.md`（M5-a 物理名 t_{uid}／M5-b 插入锚点；方案态 [待审核]，人工审核批准后实施；docs/plan/ 注册随下一治理轮） | M5_kickoff_plan.md 落盘 |

治理轮修改文件：task-record（新建）、AGENTS.md（锚点/§8）、本报告（本节追加）、M5_kickoff_plan.md（新建）；代码零改动（79 用例基线不变）。
