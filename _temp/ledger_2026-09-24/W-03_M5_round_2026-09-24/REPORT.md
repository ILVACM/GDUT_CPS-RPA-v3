# W-03 M5 实施轮报告（M5-a 物理名 t_{uid} ＋ M5-b 三态锚点插入）

> **⚠ 归档注记（2026-09-24 R10）**：本文件为历史轮次快照，正文未改写。现位于 `_temp/ledger_2026-09-24/`；文中指向已清理 `_temp` 件（GUI 细节方案／M5 设计／审计报／审计方案／运行流程简报／repo-context／verify 留痕）的旧路径，其章节骨架与结论沉淀位置见同夹 `CLEANUP_MANIFEST.md` §2～§3，引用对账见 §5。

> 日期：2026-09-24｜执行模式：多 Agent（主控实施＋取证子 agent×2＋复核子 agent×2）｜依据：`_temp/M5_design_plan.md`（定稿 [冻结]，§6.1 35 原子步骤）＋`.trae/documents/M5方案实施执行计划.md`（人工批准）
> 边界遵守：Agent 不执行 git；`_temp/DAG-rebuild/SampleCode/` 冻结基线未触碰；引擎四文件中 parser/executor/validator 零改动、step_executor 仅注释（实现行原样）。

## §1 实施摘要

**M5-a（物理名 t_{uid}）**：派生表物理名从 `t_s{执行序}` 改为 `t_{步骤uid}`，根治 cp 占序/插步漂移。改造收敛于 `gui/models.py` to_dict 单点：业务口径为产表步（output_table_id 非空唯一判定）写 `params["output_table"]=f"t_{s.uid}"`、编辑态 pop；uid 重复防御（业务口径、就地重生成＋logger.warning）；编辑态 steps 增第 9 键 `"uid"`（retry_count 后居末位）；`load_from_dict` steps 段改 `uid=str(s.get("uid","") or _new_uid())`（编辑态继承、业务口径重生成）。引擎零改动（K2 白名单优先消费通道）；外部手写 JSON 无 output_table → 回退 t_s{n}（K3 双轨）。

**M5-b（三态锚点插入）**：models 新增 `insert_step(index, type_name)`（clamp→构造（add_step 逻辑整体迁移）→OUTPUT_OPS 分配→insert→立即 renumber→_next_step_num→reconcile，K5 序列）；`add_step` 改单行委托（C3）。page 新增 `_resolve_insert_index()` 三态：①选中步 is_end→插其前（C2）否则插其后；②选中表→产出步 p+1／最后消费者 c+1（**is_end 不计入消费者**，方案 §9.4 项②澄清）／皆无走③；③末尾+is_end 保护、空流程 0。`_on_add_step` 改造：idx 解析→insert_step→idx_new clamp 等价式（删 `steps.index(step)` 反查）→refresh→select→select_node（K7 时序）；不压撤销栈（K8）。

**治理**：本 REPORT＋task-record R5＋AGENTS 锚点 R5/§8 更新＋architecture.md 3 处双轨表述（C1 放行项）。

## §2 修改文件清单（10 项）

| 文件 | 改动摘要 | 对应任务 |
|---|---|---|
| rpa_engine/gui/models.py | to_dict 双口径分叉＋uid 防御＋第 9 键；load uid 继承；insert_step 新增；add_step 委托 | M5a-T1/T2/T3、M5b-T6 |
| rpa_engine/gui/page_operation_config.py | _resolve_insert_index 新增；_on_add_step 改写 | M5b-T7/T8 |
| rpa_engine/tests/test_engine_overwrite.py | L78 断言改 f"t_{m.steps[0].uid}"；TUidEngineTest 新增（2 方法） | M5a-T4 |
| rpa_engine/tests/test_models_data.py | PhysicalNameUidTest（4 方法）＋InsertStepTest（3 方法）新增；SessionTest 幂等用例载体改编辑态口径 | M5a-T4、M5b-T6 |
| rpa_engine/tests/test_translation.py | 3 处断言更新为 K2 新契约（output_table==t_{uid}） | M5a-T4（施工期） |
| _temp/DAG-rebuild/smoke_m1m3.py | M5a 节（3 check）＋M5b 节（22 check）新增；F1 场景首 check 按 C3 反转 | M5a-T5、M5b-T9 |
| rpa_engine/ops/step_executor.py | 注释 4 处双轨补注（实现行 L196→L201 逐字符零改动，偏移=注释增量） | M5a-T5 |
| docs/architecture.md | L178/L222/L225 双轨表述（GUI 链路 t_{uid}／外部 JSON 缺省回退 t_s{n}） | M5-T11（C1） |
| AGENTS.md | 锚点 R4→R5＋§8 主线（容量 7,793/余量 207/CRLF 196） | M5-T11 |
| docs/task-records/2026-09-24-w03-m5-tuid-insert-anchor.md | R5 任务记录新建（8 节） | M5-T11 |

**未修改**：rpa_engine/engine/（parser/executor/validator）、gui/node_graph.py、gui/graph_edges.py、gui/app.py、`_temp/DAG-rebuild/SampleCode/`、其余 docs/knowledge。

## §3 回归与门禁结果（全绿，2026-09-24 实跑）

| 门禁 | 结果 |
|---|---|
| `python -m unittest discover -s tests` | **Ran 88 tests OK**（79 基线零回归＋9 新增：PhysicalNameUidTest 4＋InsertStepTest 3＋TUidEngineTest 2；构成＝models_data 36＋graph_edges 17＋step_catalog 15＋translation 9＋engine_overwrite 5＋recent_steps 3＋validator_cross 3） |
| `python ..\_temp\DAG-rebuild\smoke_mb.py` | SMOKE_ALL_OK（33 项，FF3） |
| `python ..\_temp\DAG-rebuild\smoke_m1m3.py` | SMOKE_ALL_OK（既有全场景＋M5a 3 check＋M5b 22 check；FF4=M1-S2、FF5=M3-S1） |
| `run_self_check()` | True 6/6（263ms，FF2 含守卫 4/4b） |
| FF1 | Collision/Allocator/CollisionCross 用例在 88 全绿内 |
| grep 门禁 | `t_{s.uid}`／`uid 重复`／`def insert_step`／`def _resolve_insert_index` 命中；`steps.index(step)` 0 命中；models.py `steps.append` 0 命中；engine/ 目录 `uid|insert_step|_resolve_insert_index` 0 命中 |
| AGENTS 容量三口径 | 含 CR 7,793（≤8,000、余量 207≥200）／crlf 196、loneCR 0、loneLF 0 |

**施工期修复记录（6 项，均在既有任务范围内处置、零新增决策）：**
1. **test_translation 3 处断言**（test_new_table_mapping／test_overwrite_two_step_chain／test_load_regression）：编码 K2 前"双口径无条件 pop"旧契约→更新为新契约 `output_table==f"t_{uid}"`（遗留值替换语义升级）。设计轮 E10 影响面漏记（仅记 L78 一处），按 C3 用例修正原则处置，裁定语义不变。
2. **SessionTest.test_load_to_dict_idempotent**：往返载体由业务口径改编辑态文件（K1：生产 last_config 即编辑态口径；业务口径 load 重生成→物理名漂移为 K3 预期，由 test_uid_persist_roundtrip 覆盖）。
3. **smoke F1 场景首 check 反转**：原"旧 scene 键失联（修复必要性演示）"依赖 step_NN 临时号混合键态——该键态为 C3 裁定刻意消除，反转为"无失联"不变量（len(stale)==0）；F1 链核心语义（scene 键与模型 step_id 对齐）不变，后两 check 原样。
4. **smoke M5a tooltip 场景适配**：共享 op 已被既有 S2-T9 清场场景复位，改用局部页面 opm5 验证同一链路（set_output_tables({T101: t_{uid}})→toolTip），断言语义不变。
5. **AGENTS 容量压缩**：R5 编辑后余量 165<200，按 doc-governance §10 条 2 压缩锚点/§8 非保留块→余量 207（保留块 §2.1/§2.2 未触碰）。
6. **复核子 agent 结论**：4 项通过；5 处非实质偏差备案（A2 分叉 elif 扁平化等价／防御块 seen.add 无条件化为安全侧超集／step_dict 与 `_seen_uids` 命名级（方案 DoD 允许等价文本）／OUTPUT_OPS 注释保留既有 M2-T2/M19 详注／C 方法注释排版级）。

## §4 复检扫描

- 越界检查：Agent 写入仅 §2 清单 10 文件＋本 REPORT＋计划文件（.trae/documents，Plan Mode 授权）；git 提交留人工。
- 死代码：旧单行 pop／`steps.index(step)` 反查 0 残留；move_step 按 H2 裁定原样保留（生产零调用，留清理轮）。
- `t_s{n}` 残留面（全部预期内）：step_executor 实现行回退分支＋注释 4 处双轨注＋architecture.md 双轨表述＋test_external_json_fallback_t_s 断言值。
- smoke 副作用（先例口径）：recent_steps.json／mb-preview.png／自检探针＝瞬态写入，已知情接受。

## §5 零遗留清单

| 项 | 状态 |
|---|---|
| M5a-T1~T5／M5b-T6~T10／M5-T11（35 原子步骤） | ✅ 全部完成（DoD 逐项勾验） |
| 施工期修复 6 项 | ✅ 全部闭环（§3） |
| 待人工：真机 GUI 验收 | ⏸️ 建议清单：①阶段2 选表后阶段3 添加步骤——分别验证选中步/选中表/无选中三态插入位与结束步保护；②中段插入后画布行序顺延+自动选中高亮；③执行一轮 overwrite 流程，报告页/tooltip 查看 t_{uid} 物理名；④模板保存→应用往返（uid 持久）；⑤插入→删除→撤销还原 |
| 待人工：exe 重建（W-20） | ⏸️ 判据 docs/build-guide.md §1.10 |
| 待人工：move_step 删除（下一清理轮） | ⏸️ H2 裁定，独立于 M5 |
| 待人工：git 提交 | ⏸️ Agent 不执行 git（AGENTS §1） |

## §6 声明

本轮唯一执行依据＝`_temp/M5_design_plan.md`（定稿 [冻结]）；K1-K8、C1-C3 裁定、§5 门禁、§6 任务划分零改动；5 处非实质偏差已备案；6 项施工期修复均留痕。**当前停止，等待人工下一步指令。**
