# 任务记录：AGENTS.md 精简——机制细则剥离至 docs/（doc-governance + anchor-mechanism）

## 摘要
- **任务目标**：执行已批准的《AGENTS.md 精简方案》（计划文件 blazing-vortex-newton-FKl7EHMD.md）——剥离 §7.1~7.5 至新建 docs/doc-governance.md、§7.6 主体至新建 docs/anchor-mechanism.md、§3.1 至 docs/agent-execution-mode.md §6；AGENTS.md 压缩至 ≤8000 字符（wc -m 实测）；§2.5 背书 +2 行保持剥离细则 [约束] 效力
- **任务状态**：已完成
- **轮次**：单轮
- **前序轮次**：无（前置：同日早前的规约修改任务已关闭，详见 2026-09-06-agents-spec-refactor.md）
- **开始时间**：2026-09-06 14:30 (UTC+8)
- **最后更新**：2026-09-06
- **要点摘要**：AGENTS.md 448 行 18,702 字符 → 215 行 7,992 字符（wc -m 达标）；剥离 8 项映射零丢失；§2.5 背书 5→7 项；INDEX 9 篇同步；活引用修正 5 处；第二级精简启用（§4.3 下沉 INDEX、§2.3 摘并等）；三步五查全过（详见 _temp/verify-agents-slim.md）；源码零改动
- **操作人**：黄泊凯

## 用户输入
- "@AGENTS.md，对该文件分析，是否能进行精简，将不必要的内容，剥离到`docs/`中的相关文档，并通过相对路径进行索引"
- AskUserQuestion 裁定：剥离组织="2 新文档+1 扩充"；约束力="加入背书保持[约束]"；锚点保留="独立成篇，摘要留约束层"；精简程度="硬目标 ≤8000 字符"（均选推荐项）
- 计划批准：ExitPlanMode 已确认（2026-09-06）

## Agent 理解与决策

- 精简核心论据：AGENTS.md 现 448 行 / 18,702 字符（wc -m 实测），超注入上限截断于 §6，§7/§7.6/锚点层/§8 在 IDE 注入通道不可见——锚点机制在最常用入口失效。
- 策略：机制细则原样迁入知识层（仅章节重编号与交叉引用改写），信息零丢失；约束层保留摘要与路由；细则经 §2.5 背书维持 [约束] 效力。
- 执行顺序：先迁移（步骤 3-5）后改写（步骤 6），校验（步骤 8）按新位置 doc-governance.md §4 执行，避免"校验规则自身搬家"风险。

## 执行流程

### 流程概览
- 总步骤数：10
- 多 Agent 协作：否（单 Agent 直接执行，模式 A；剥离目标位置明确、映射表完备，无需拆分）

### 步骤记录

#### Step 1: 备份 3 文件
- 状态：✅ 已完成
- 执行内容：cp 至 _temp/BackUp/，`*bak-20260906-pre-slim` 后缀；实测 AGENTS.md = 448 行 / 18,702 字符
- 涉及文件：AGENTS.md、docs/INDEX.md、docs/agent-execution-mode.md（读取源）；_temp/BackUp/3 个 .bak（写入）

#### Step 2: 建任务记录 + 锚点层
- 状态：✅ 已完成
- 执行内容：新建本任务记录；AGENTS.md 锚点层覆写为本任务（执行中）

#### Step 3: 新建 docs/doc-governance.md
- 状态：✅ 已完成
- 执行内容：原 §7.1~§7.5 迁入为 §1~§5；改写点：内部互引改本文档 §n、指向 AGENTS.md 的引用保留、Step1 锚点检查句改写、AGENTS.md §4.x 引用加前缀限定、相对路径加 ../ 前缀、[待补充] 处置段后续迁入（见 Step 6 注）
- 涉及文件：docs/doc-governance.md（新建）

#### Step 4: 新建 docs/anchor-mechanism.md
- 状态：✅ 已完成
- 执行内容：原 §7.6 全文迁入；"本节（§7.6）"→"本文档"；TEMPLATE.md 相对路径恰好修正（task-records/TEMPLATE.md 自 docs/ 出发可达）；头部规定层声明；锚点层载体改述为 AGENTS.md
- 涉及文件：docs/anchor-mechanism.md（新建）

#### Step 5: 扩充 docs/agent-execution-mode.md
- 状态：✅ 已完成
- 执行内容：追加 §6 多 Agent 协作规范（原 §3.1 的 4 原则 + 6 角色表原样）；头部 last-updated/content-revision → 2026-09-06
- 涉及文件：docs/agent-execution-mode.md

#### Step 6: 改写 AGENTS.md（多轮）
- 状态：✅ 已完成
- 执行内容：§2.5 背书 5→7 项；§2.3 摘并为引用行；§2.4 git 行并 §1；§3.1 压缩 3 行；§4.1 职责改述；§4.3 收缩为 INDEX 入口行；§4.7 [待补充] 处置段下沉 doc-governance §4；§7 重组三小节（7.1 核心条款 / 7.2 索引 / 7.3 锚点摘要）；§1/§8/锚点层压缩
- 决策记录：①wc 实测 11,468 > 8000，启用计划第二级精简清单（§4.3 下沉 INDEX、§2.3 摘并、§2.5 表格 bullet 化等）②发现并行 Edit 竞态（同文件多 Edit 互相覆盖致编辑丢失，字符数未按预期下降），改为全量 Write + 串行 Edit 修复；最终 214 行 / 7,992 字符达标
- 涉及文件：AGENTS.md（全量改写）

#### Step 7: 同步 docs/INDEX.md + README.md
- 状态：✅ 已完成
- 执行内容：INDEX 头部 confidence 更新；agent-execution-mode 行补 §6 摘要与日期；新增 doc-governance/anchor-mechanism 两行（7→9 篇）；§3 路由表 +2 行；README L27 篇数 7→9
- 涉及文件：docs/INDEX.md、README.md

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 读取 | AGENTS.md / docs/INDEX.md / docs/agent-execution-mode.md / README.md / docs/task-records/TEMPLATE.md | 迁移原文与格式确认 |
| 写入 | _temp/BackUp/{AGENTS,docs-INDEX,agent-execution-mode}*.bak-20260906-pre-slim | 备份 |
| 新建 | docs/doc-governance.md | 原 §7.1~7.5（§1~§5） |
| 新建 | docs/anchor-mechanism.md | 原 §7.6 规定层全文 |
| 扩充 | docs/agent-execution-mode.md | +§6 多 Agent 协作规范；头部更新 |
| 改写 | AGENTS.md | 全量：背书 7 项 / §3.1 压缩 / §4.3 下沉 / §7 重组 / §1§8 压缩 / 锚点层 |
| 修改 | docs/INDEX.md | +2 条目、路由 +2 行、agent-execution-mode 行更新（7→9 篇） |
| 修改 | README.md | L27 篇数 7→9 |
| 修改 | docs/plan/INDEX.md / docs/plan/DAG_refactor_plan.md / docs/task-records/TEMPLATE.md / knowledge/Instances-INDEX.md | 活引用修正（旧 §7.x → 新位置） |
| 新建 | _temp/verify-agents-slim.md | 三步五查校验报告 |

## 关闭标识
- **完成时间**：2026-09-06 15:10 (UTC+8)
- **最终状态**：✅ 全部完成
- **关闭说明**：10 步全部执行完毕；AGENTS.md 7,992 字符（wc -m）达标，注入截断问题解除；剥离零丢失、背书生效、活引用清零、三步五查通过（_temp/verify-agents-slim.md）；源码零改动，exe 仍有效。执行备注：同文件多 Edit 并行会发生竞态覆盖（本轮实测教训），已改为全量 Write + 串行 Edit 修复。
