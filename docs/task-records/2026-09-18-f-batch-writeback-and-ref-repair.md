# 任务记录：F 批裁定回写正本 + C 类失效引用改道 + M18/M22 生产最小改动

> 日期：2026-09-18｜执行：单 Agent（主控，断点续跑）｜状态：已完成

## 摘要

人工裁定（09-18）：A 类全部以示范代码 SampleCode 为准（F-1 图例废止 / F-2 起止标识修订 / F-3 五类边词表入正本 / M22 纳入）；B 类已人工验证关闭（N1-N15 真机 + git status 零改动）；C 类自适应修改；W-14/W-15 同批闭环。执行含断点续跑：上一轮已完成正本 14/16 锚点回写，本轮补齐剩余 2 锚点 + 生产最小改动 + C 类收尾 + 治理联动。

## 用户输入

- 「A类全部以示范代码为准（app.py 启动自检增加注册表字段完整性），B类已经人工验证，C类自适应修改。整理计划文件 `_temp/DAG-rebuild/plan.md`」（两次下达，第二次为断点续跑确认）。

## Agent 理解与决策

- D1 断点续跑、已完成项不重做（断点核验：正本 frontmatter/L22/§4.3/§5.8/§六/§八 已落盘，experiments 引用正本内清零）。
- D2 W-15 闭环不写死行号（真身=正本附录 A D6 裁定行，以字符串「AGENTS.md §1/§2.4/§7.2」定位；经核对表述准确，无需改正文）。
- D3 backlog 统计收敛：待指令=2（W-19/W-20）、部分完成=0、已完成=18。
- D4 analysis 证据索引仅追加归档标注、不删行（doc-governance §7.1）。
- D5 根 README 零改动（核实无 DAG 指引行，L41 历史表述仍准确）。
- D6 M1-M17/M19-M21 不提前执行（属 M0-M5 批次）。
- W-14 结论：binding 经 doc-governance §9 四档映射核对——方案态层且已无未裁定条目 → 保持 `reference`，结论记入正本 frontmatter。

## 执行流程

### 流程概览

R1 正本收尾 → R2 生产最小改动 → R3 C 类收尾 → R4 plan.md 整理+治理联动 → R5 验证。

### 步骤记录

#### Step 1: R1 正本收尾（2 锚点）
- §8.6 图例行改写为「画布无常驻图例（F-1 废止原 7 词条口径）+ 语义三层承载」；附录 A D2 行追加 F-2 修订注。

#### Step 2: R2 生产最小改动（M18+M22）
- `rpa_engine/gui/models.py`：typing 补 `Optional`；classify_step 末（L64 后）纯增量追加 `PRODUCE_LABEL`（copy_table="复制新表"）、`MAIN_BUTTONS`/`MORE_BUTTONS`、`produce_label()`、`is_end_op()`；`STEP_CATALOG` 旧二元组不变（零读取点改动）。
- `rpa_engine/gui/app.py`：docstring 自检清单 5→6 项；项4 后新增「项4b 注册表字段完整性」（STEP_KIND/PRODUCE_LABEL/OUTPUT_OPS 三口径自洽 + 按钮分组并集/交集校验；except→ok=False 不抛异常）。
- 实测：conda 环境 `run_self_check()` 6 项全 OK。

#### Step 3: R3 C 类收尾
- `AGENTS.md`：L3 日期→09-18；锚点块覆写为 F 批任务（详情索引=本记录）；§8 主线基线→`SampleCode/`（61+11，09-18 人工真机验证）+ F 批已裁定；DAG 上下文→plan.md+SampleCode。
- `docs/backlog.md`：L7 日期；W-02/W-03 关联位置改道 plan.md；W-14/W-15 → ✅ 09-18 闭环；§5 顺序行/统计表（2/0/18）/主线提示同步。
- `docs/analysis/DAG_visualization_analysis.md`：L7 日期；L18 边界声明与附录 A/B 各追加 09-18 归档注（不删行）。
- 根 `README.md`：零改动（D5）。

#### Step 4: R4 plan.md 整理 + 治理联动
- `_temp/DAG-rebuild/plan.md`：头部「2026-09-18 裁定落地」注记；§2.2 条5 与 M11 去 F-2 依赖措辞；M18/M22 标已执行（M18 采独立 PRODUCE_LABEL 方案）；附录 D 验收补 F-2 口径与已闭环项；附录 E 收敛为「裁定与失效引用处置登记」。
- `docs/plan/INDEX.md`：L21 条目摘要/状态/日期同步；L7 日期。
- 本记录新建。

#### Step 5: R5 验证
- grep 正本「图例」仅存 F-1 注记/历史注；docs/+AGENTS 的 `_temp/DAG-rebuild/experiments` 活指针 0。
- 自检 6 项全 OK；破坏复测项4b 报 FAIL 后还原复测 OK。
- SampleCode 61 用例全绿。
- AGENTS 容量复测：含 CR 字符数 ≤8000、余量 ≥200、CRLF（见验收节）。
- doc-governance §4 三步执行 + 完成确认格式输出（见验收节）。

## 涉及文件汇总

| 文件 | 改动类型 |
|---|---|
| docs/plan/DAG_refactor_plan.md | F-1/F-2/F-3 回写 + W-14 注记 + C 类改道（16 锚点） |
| rpa_engine/gui/models.py | M18 纯增量（5 符号 + Optional 导入） |
| rpa_engine/gui/app.py | M22 项4b + docstring |
| AGENTS.md | 日期/锚点/§8 |
| docs/backlog.md | W-02/03 改道、W-14/15 闭环、统计、日期 |
| docs/analysis/DAG_visualization_analysis.md | 归档标注×3 + 日期 |
| docs/plan/INDEX.md | 条目+日期 |
| _temp/DAG-rebuild/plan.md | 裁定落地注记 + M11/M18/M22 升级 + 附录 D/E 收敛 |
| docs/task-records/2026-09-18-f-batch-writeback-and-ref-repair.md | 新建（本文件） |

## 验收

- ✅ [校验通过] doc-governance §4 全局更新校验（2026-09-18）
  - Step1 AGENTS 自洽：锚点/§8/日期一致；三口径复测＝含 CR 7,664 / LF 归一 7,468 / 行数 196（余量 336≥200）；行尾按 doc-governance §10.3 恢复 CRLF（历史 LF 偏离本轮修正，冗余细节按 §10.2 下沉至本记录与 plan.md）。
  - Step2 索引与五项校验：链接完整性（改道目标均存在：SampleCode/、plan.md、本记录）；元信息完整（last-updated 同步 4 文件）；层级一致（plan 层 binding=reference 经 §9 映射核对）；INDEX 同步（L21+L7）；约束力合规（无 [约束] 误标）。
  - Step3 README 同步：本轮零改动，理由=根 README 无 DAG 指引行且 L41 历史表述仍准确。
  - 执行路径：主控 Agent 单轮执行 + 断点核验子 agent 只读复核。
- 编码类验收：自检 6 项全 OK + 破坏复测 OK/FAIL 符合预期 + SampleCode 61 用例全绿。

## 关闭标识

本轮完成，待续事项：W-19 单独裁定、W-20 exe 人工重建、M0 启动指令、D-2 漂移项（output_mode 等，M0 移植前裁定）。
