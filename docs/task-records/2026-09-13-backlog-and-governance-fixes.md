# 任务记录：处置其余待办（W-06 ~ W-14 非 DAG 部分 + 新-1/新-2），W-02/W-03 冻结不动

## 摘要
- **任务目标**：按用户指令，对除 W-02/W-03 之外的全部待办制定并执行修复计划（含队列升格与容量写法规约）
- **任务状态**：✅ 已完成
- **开始时间**：2026-09-13 15:35 (UTC+8)
- **最后更新**：2026-09-13
- **要点摘要**：W-06~W-10 与 W-14（非 DAG 部分）已处置；W-13 撤销；W-15 顺延；新增 `docs/backlog.md`（队列升格）与 `docs/doc-governance.md` §7~§10、编码类角色集；AGENTS.md 含 CR 7,628 → 7,701（余量 299）；三步五查通过；源码零改动
- **操作人**：黄泊凯

## 用户输入

> "对于 `W-02`、`W-03` 两项，都先不要动，这是关键工作内容，对除此之外的其他问题，制定修复计划（你自适应裁决，并给出推荐方案），并在人工确认后执行计划进行修复"

（附：4 项处置口径经 AskUserQuestion 确认，全部采纳推荐项）

## Agent 理解与决策

**范围界定**：W-02（DAG 9 项歧义裁定）、W-03（用户视角改造方案拍板）为用户明示的"关键工作内容"，本轮冻结；连带冻结其载体 `docs/plan/DAG_refactor_plan.md`，故 **W-15 与 W-14 的计划书部分顺延**（已确认）。

**关键反转（W-13 撤销）**：`docs/task-records/2026-09-06-agents-spec-refactor.md` L22/L52 已载明"**不为其补建三条任务记录（用户未要求留痕）**"——09-02 轮次不留痕系既有裁定，故 W-13 不应补录而应**撤销**。属"重新审视既有结论后推翻自己的新增待办"。

**关键事实校准（影响 G-5 措辞）**：任务记录中反复出现的"58 项测试套件"实为 `_temp/` 下 8 个一次性脚本的 PASS 累加（19+7+6+7+3+4+4+4），**当前不可复现**——全库无 pytest/unittest 测试文件、`Test/` 仅 2 个 xlsx、测试工作按 `docs/architecture.md` §9 #4 暂缓。故 G-5 只表述"验收记录规范"，**不得暗示存在可复现回归套件**。

**裁定类结论（仅记录，不改文件/不改规定层）**：
- **W-07**：`Test/` 双份同名 xlsx = **正常中间产物**。`rpa_engine/gui/page_input_selection.py:35` 定义 `TEMP_DIR = ENGINE_ROOT/"temp"/"input_selection"`（:196 mkdir、:250 调用），`rpa_engine/ops/excel_preprocessor.py:52-67` 以 `shutil.copy2` 原样复制；两文件 md5/sha256 全同、git blob 哈希相同（`8404103e…`）、均被跟踪；`AGENTS.md` §6 明文"temp/ 运行产物保留不删" → **保留不删**
- **W-08**：**不重打包**。源码零改动（最后提交 2026-09-09），判据已落 `docs/build-guide.md` §1.10；M0 编码后按 §1.9/§2 重建
- **W-09**：**关闭，无需改动**。规定层已定义锚点层含「状态」字段，现值 `已完成` 已能表达"无进行中任务"；`docs/anchor-mechanism.md` 为规定层且无修改必要

**设计要点**：G-4/G-5/G-6 草案原文取自 `_temp/agents-spec-refactor-plan.md` §3.7/§3.8/§3.9（旧落点 §7.7/§7.8/§3.1 已失效），重新择址 `docs/doc-governance.md` §7/§8 与 `docs/agent-execution-mode.md` §6；标签落位规范与约束层容量规则分别落 doc-governance §9/§10。

## 执行流程

### 流程概览
- 总步骤数：8
- 多 Agent 协作：是（子 Agent 3 个：2 × Explore 取证〔Test 双份／G-4·5·6 素材／W-13·14·15〕，1 × Plan 实施设计）

### 步骤记录

#### Step 1: 备份受控文件并新建本记录
- 状态：✅ 已完成
- 执行内容：10 个受控文件备份至 `_temp/BackUp/*.bak-20260913-pre-backlog`；按 `TEMPLATE.md` 新建本记录（先有后写）
- 涉及文件：`_temp/BackUp/*`（10）、`docs/task-records/2026-09-13-backlog-and-governance-fixes.md`
- 复验：`git ls-files --eol` 记录开工前行尾基线（AGENTS.md / README.md / docs/INDEX.md / docs/agent-execution-mode.md / rpa_engine/README.md / _temp/pending-items.md = CRLF；docs/doc-governance.md / _temp/todo-from-context-report.md = LF）

#### Step 2: 新建 docs/backlog.md（队列升格）
- 状态：✅ 已完成
- 执行内容：W 清单受管辖载体落地（知识层，CRLF）；含权威声明、执行约定、W-01~W-17 主表、已关闭归档、W-13 撤销登记、推进顺序与统计
- 涉及文件：`docs/backlog.md`

#### Step 3: 扩写 docs/doc-governance.md
- 状态：✅ 已完成
- 执行内容：新增 **§7 源码↔规约同步规则**（G-4）、**§8 验收与回归记录规范**（G-5，含事实校准与"禁用表述"清单）、**§9 标签体系落位规范**（binding 四档 ↔ §4.5 四标签）、**§10 约束层容量与下沉规则**；§3 补 `binding` 四档映射；frontmatter 与头部迁移来源同步。§1~§6 编号零改动
- 涉及文件：`docs/doc-governance.md`（161 → 233 行，LF 保持）

#### Step 4: G-6 角色表扩展
- 状态：✅ 已完成
- 执行内容：`docs/agent-execution-mode.md` §6 新增「编码类角色集（Coder / Reviewer / Tester）」表 + 「两套角色集不混用」声明 + 与 §2 职责矩阵的关系说明；frontmatter 与头部同步
- 涉及文件：`docs/agent-execution-mode.md`（CRLF 保持）

#### Step 5: W-14 标签落位 —— 实例文档补字段
- 状态：✅ 已完成（非 DAG 部分）
- 执行内容：`rpa_engine/README.md` frontmatter 补 `binding: self_contained` + `confidence`，`last-updated` → 2026-09-13
- 涉及文件：`rpa_engine/README.md`

#### Step 6: 回写 _temp 两文件
- 状态：✅ 已完成
- 执行内容：① `_temp/todo-from-context-report.md` 回填「执行记录」表（Q-1~Q-10 实况 7 行 + 回写说明 + W 接管声明）；② `_temp/pending-items.md` 头部标注 `[已过时-待确认]` 并指向 `docs/backlog.md`
- 涉及文件：`_temp/todo-from-context-report.md`（LF）、`_temp/pending-items.md`（CRLF）

#### Step 7: AGENTS.md 五处改动并复测字符数
- 状态：✅ 已完成
- 执行内容：§2.5 引用区间 `§1~§6` → `§1~§10`；§3.1 角色表述改「构建类 6 角色 / 编码类 3 角色」；§7.2 索引枚举补 4 项并改 `§1~§10`；§8 待办指针改向 `docs/backlog.md`；锚点层覆写为本任务
- 涉及文件：`AGENTS.md`（CRLF 保持）
- 决策记录：首轮整块替换因摘要行文本差异（"余量 387" vs "余量 372"）断言失败，**未落盘**（避免了半成品），改用逐字段替换
- 复验：196 行 / **含 CR 7,701 ≤ 8,000（余量 299）** / lone_CR = 0

#### Step 8: 全局更新校验（doc-governance §4）
- 状态：✅ 已完成
- 执行内容：三步 + 五项全过——链接（44 篇，真断链 0；`dev-spec.md -> df` 为代码片段伪命中）；元信息（适用 16 篇 0 不合规）；INDEX 同步（docs 10 篇、plan 1 篇全对应）；AGENTS.md 自洽（七类章节齐备、16 个锁定编号全在、§4.5 四标签、§4.7 六标签、7 条路由链接可达）；doc-governance §1~§10 齐备
- 涉及文件：`_temp/verify-backlog-governance-fixes.md`
- 复验：全部为 CRLF/LF 纯行尾且 `lone_CR = 0`；W-01~W-17 在 backlog 全覆盖

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 备份 | `_temp/BackUp/*.bak-20260913-pre-backlog`（10 个） | 执行前快照 |
| 新建 | `docs/backlog.md` | W 清单受管辖活载体（队列升格，W-16） |
| 新建 | `docs/task-records/2026-09-13-backlog-and-governance-fixes.md` | 本记录 |
| 新建 | `_temp/verify-backlog-governance-fixes.md` | 全局更新校验报告 |
| 修改 | `docs/doc-governance.md` | 新增 §7~§10；§3 补 binding 四档映射；frontmatter/头部同步 |
| 修改 | `docs/agent-execution-mode.md` | §6 新增编码类角色集（G-6） |
| 修改 | `AGENTS.md` | §2.5/§3.1/§7.2/§8 四处引用同步 + 锚点层覆写 |
| 修改 | `docs/INDEX.md` | 新增 backlog 行（第 10 篇）；doc-governance 摘要；§3 路由补行 |
| 修改 | `README.md` | 篇数 9→10；补一行 2026-09-13 状态速览 |
| 修改 | `rpa_engine/README.md` | 补 `binding`/`confidence`（W-14） |
| 修改 | `_temp/todo-from-context-report.md` | 回填执行记录表（W-06） |
| 修改 | `_temp/pending-items.md` | 标注 `[已过时-待确认]`（W-16） |
| **规约同步**（doc-governance §7 要求） | `AGENTS.md` §2.5/§7.2 ↔ `docs/doc-governance.md` 章节号；`docs/INDEX.md` ↔ 新增知识文档 | 同步完成，无 `[待补充]` 遗留 |

## 关闭标识
- **完成时间**：2026-09-13 15:50 (UTC+8)
- **最终状态**：✅ 全部完成
- **关闭说明**：除 W-02/W-03（用户冻结）外，其余待办全部处置完毕——W-06/W-07/W-08/W-09/W-10 完成，W-13 撤销，W-14 非 DAG 部分完成（DAG 侧顺延），W-15 顺延，新登记 W-16/W-17 并同步关闭；三步五查通过，AGENTS.md 含 CR 7,701（余量 299），源码零改动
