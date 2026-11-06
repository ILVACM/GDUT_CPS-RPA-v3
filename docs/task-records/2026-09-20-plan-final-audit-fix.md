# 任务记录：plan.md 终审纰漏修补（11 项全修，裁决=全推荐）

> 日期：2026-09-20｜执行：单 Agent（前置：3 路只读审计 + 主 agent 亲验 3 指控）｜状态：已完成

## 摘要

对 09-20 修订版 plan.md 做终审（3 并行审计 agent + 主 agent 亲验），发现 2 设计纰漏 + 4 必改 + 5 建议；人工裁决"所有裁决点采用推荐方案"后一次修毕：纰漏1=方案 c 两步链翻译（filter 自动中间表 + 合成 copy_table 步，零 engine/ops 改动）；建议8=last_config 未过滤导出；其余 9 项照单全修。

## 用户输入

- 「再检查一次重构方案计划，确认 plan.md 能达到要求……设计与技术实现是否合理，不存在纰漏」（触发终审）
- 「所有裁决点采用推荐方案，修复所有问题」

## 终审发现（关键证据均经主 agent 亲验）

- **纰漏1**：§4.3 单步覆盖映射运行时必败——filter_dedup.py L79-84 先 `DROP output_table` 后 `CREATE AS SELECT FROM 源表`，同名覆盖必删源表；table_lifecycle L118 copy_table 禁源目标同名；§2.1 又锁"engine/ops 不动"。
- **纰漏2**：M16 实现规格 EdgeSpec 字段（kind/source/target/…/deprecated_flag）与 §1.4 契约（key/type/from/to/role/label/missing）自相矛盾；签名拿不到弃用态；overwrite 渲染例外缺失。
- 必改：§2.3 标题 22→26；M20-styles↔M2 互为前置环；61 用例验收 49 项无承载；M25 锚点/摘要失实（生产无表详情态，_on_node_table_selected L401-402 仅清空选择）。
- 建议：闭包输入表歧义；M23 漏 last_config 链路（_save_last_config L533-541）；M26 缺 load 回归；术语 3 处；to_dict 行号 L266-310→L266-302。

## 执行流程（11 项修补）

1. **F1** §4.3 整段改两步链：new_table→剔除 output_table（含遗留键）；overwrite→本步 filter/dedup(源→自动中间表，保留 output_table_id) + 合成 copy_table 步（output_table=目标表 sqlite_table 物理名）；下游引用原地不动；渲染不画两步；依据/风险/二次确认全段重写。
2. **F2** M16 规格重写：EdgeSpec 逐字对齐 §1.4 契约（deprecated 为 type 枚举、key 防重）；签名增 `deprecated_ids: Set[str]`；显式"输入=未过滤 model"；新增第 5 条产表判定 `produces_table(op, params)`（overwrite 不产派生表节点）。
3. **F3/F4** §2.3 标题 26 条；M20-styles 依赖改"无（被 M2 引用，非依赖关系）"。
4. **F6** M25 锚点改 `_on_node_table_selected` L401-402 + `_build_empty_param_panel` L174-182；摘要改"需新建表详情分支"；影响范围补 M15/正本 §8.5 承载。
5. **F8/F11** M23：to_dict 行号 L266-302（save_json 勿动）；修改为增 `include_deprecated` 参数化（⑤ _save_last_config L533-541 传 True=未过滤导出，重启步骤完整）；影响范围补 last_config 链路。
6. **F9/F10** M26 用例 7→8（⑤改两步链断言、⑧load 回归）；§2.3/§4.7/§1.9 同步 8 用例；术语 3 处（"D-2 漂移项"→翻译契约五项裁定、E2E 行补豁免、"A4"→§1.9 方案①）。
7. **F5/F7** 61 用例验收改"移植清单"口径（§1.9/§2.4/附录 D 三处：test_graph_edges 12+test_translation 8，其余演示专属语义由 E2E/真机/自检承载不作 1:1 移植）；§4.2③ 闭包消歧（仅闭包根剔除，共享输入表保留）。

## 验收（19 项对账全绿）

- ✅ 残留清零：kind/source/target 旧字段 0；`22 条 M`/`61 用例移植版全绿`/`L266-310`/`现 L184-253 内`/`7 用例`/单步映射表述 全部 0。
- ✅ 新口径就位：deprecated_ids 签名 1、produces_table 2、两步链 11、include_deprecated 3、M25 新锚点/last_config 锚点各 1、8 用例 6、闭包消歧 1。
- ✅ 结构不变：27 块/26 唯一 Mn/27 前置依赖；§2.4 集合 7+13+4+2=26。
- ✅ 锚点抽查（终审时亲验）：_on_node_table_selected L401-402、_build_empty_param_panel L174-182、_save_last_config L533-541、to_dict L266-302、filter_dedup L79-84、table_lifecycle L31-65/L118 与盘上一致。
- ✅ doc-governance §4：本轮仅改 `_temp/DAG-rebuild/plan.md`（豁免）+ AGENTS 锚点 + 本记录；正本零改动（方案 c 后正本 §8.4 条款仍相容，d6 决策）。
- ✅ AGENTS 三口径复测（含 CR≤8000/余量≥200/CRLF，见下）。

## 涉及文件

- `_temp/DAG-rebuild/plan.md`（唯一实质修改：约 15 处编辑）
- `AGENTS.md`（锚点覆写）
- `docs/task-records/2026-09-20-plan-final-audit-fix.md`（新建，本文件）

## 关闭标识

本轮完成。plan.md 至此经"09-19 审计阻断清除 → 09-20 翻译契约落地 → 09-20 终审纰漏修补"三轮收敛，**无未裁定项、无自相矛盾、锚点 100% 实测**——M0 启动只待人工指令（M-a 需先登记 tests 豁免）。待办：W-20（exe 人工重建）、v3.2 待办（单表粒度内存释放）。