# 任务记录：功能函数设计规范固化到 agent 规约（R7 规约整理轮）

## 摘要

- **任务目标**：功能函数设计规范固化到 agent 规约（4 条规定）
- **任务状态**：`已完成（零代码改动，W-22 待人工裁定立项）`
- **轮次**：R7（侦察→设计→写入→自检）
- **前序轮次**：W-03 完善度修复轮（R6，09-24 人工验收通过）
- **开始时间**：2026-09-24
- **最后更新**：2026-09-24
- **要点摘要**：新建 `docs/function-spec-rules.md`（[约束]）承载 4 条规定全文＋文档版记录表（9 项全字段）＋canonical 登记清单 13 项＋16 项待补强登记；AGENTS.md 仅加 §2.6 指针与 §2.5 背书 1 行，并按 doc-governance §10.2 等量下沉 6 处保持容量合规（7,774→7,800／余量 200）；architecture.md 两处文档失实按代码实况修正；backlog 登记 W-22；只读审查子 agent 发现 5 项高优先偏差已同轮修正；**本轮零代码改动**（118 用例回归全绿）
- **操作人**：黄泊凯（人工裁定）＋ AI Agent（TRAE，规约整理）

## 用户输入

关键指令（原文要点）：

> 「本次任务为"功能函数设计规范固化到 agent 规约"，属于规约整理阶段，不是实施阶段。你必须先只读侦察当前 agent 规约、知识层、代码规范和现有功能函数登记结构，然后把这 4 条规定写入合适的规约文件，使得以后任何 agent 一旦涉及功能函数相关操作，自动按规范执行。严禁修改任何代码、数据、依赖、设计稿或功能函数实现。输出后立即停止，等待人工下一步指令。」

4 条规定：①三位一体（后端 Python 函数／JSON 参数记录与格式规范／前端 GUI 设置界面；增删改必检三者；前两者 agent 可自行生成，GUI 部分必须由用户额外说明）②双记录表（代码版与文档版实时同步，冲突以代码为准；明确字段、同步义务、冲突裁定）③前端交互位置固化（配置只在"用户配置"阶段 DAG 右侧面板；"添加功能步骤"按钮须显示全部选项且来源为记录表单一源；其它位置不得承担配置职责）④变更工作流顺序（新增＝后端→记录表与 JSON 规范→前端；删除＝先查依赖再自适应调整；修改＝先定位影响面再按后端→JSON→前端；动手前必须先列影响面、不得跳步）。

多 agent 协作要求：主 agent 上下文 ≤80K、子 agent ≤60K 且返回 ≤2K、最多并发 3 个、仅主 agent 写规约文件。

## Agent 理解与决策

**运行方式判定**（AGENTS §3 → agent-execution-mode.md）：模式 C（单 agent 主控）＋只读子 agent 协作；不执行 git、不执行 build.bat。

**SEM 路由**：primary＝`ai-coding-governance`（产出物＝仓库级 agent 规则集）；secondary＝`documentation-lifecycle`（唯一事实源／新鲜度／INDEX 登记）。

**4 项人工裁定**（Plan Mode 提问，全部采纳推荐项）：

| # | 决策点 | 裁定 | 理由 |
|---|--------|------|------|
| 1 | AGENTS.md 承载策略 | 极简指针（§2.6）＋等量下沉 | 实测余量仅 226 字符，4 条全文（≥3,000 字符）必超 8,000 上限；doc-governance §10.2 要求"余量 <200 先下沉等量细节"，且禁压 §2.1/§2.2 红线本体 |
| 2 | 细则落点 | 新建 `docs/function-spec-rules.md` | 4 条规定跨架构＋编码＋治理三层，塞进 architecture 或 dev-spec 任一都会割裂；独立专章便于单次加载 |
| 3 | 文档版记录表载体 | 放新专章 §3.2 | 规则与表同文件、一处维护；architecture §6 保留引擎视角摘要并声明"以代码为准＋以专章为唯一载体"，避免双源 |
| 4 | GUI 缺说明时行为 | 硬停止＋《GUI 待确认清单》 | 最贴合"不说明就容易胡乱发挥"的立法意图；清单模板落专章 §2.4 |

**其余关键决策**：

1. 新章节号取 **§2.6**（紧随 §2.5 背书条款），不重排任何既有编号、不复用已下沉留空的 §7.4~§7.6——依据 doc-governance §4 Step 1 的编号硬依赖与历史"编号零重排"实践。
2. 文档版记录表在人工列举的 8 字段外**增列"GUI 表单类"**：规定 1 要求三形态可见，该列为代码实况（`_FORM_CLASSES`），不引入新口径。
3. **canonical 登记清单定为 13 项**，取代历史"6 处"（`_temp/W-03_GUI_detail_optimization_plan.md` §6.5）与"7 处＋9 分支"（`_temp/RPA_engine_maturity_assessment.md` P2-2）两套并存口径（消解 A3 冲突）。
4. 规定 3 的"必须显示所有选项"细化为"弃用项置灰＋标『（已停用）』、不隐藏"——取 `page_operation_config.py` L216-238 实况，避免与既有实现相悖。
5. `architecture.md` 两处**文档失实按代码实况修正**（不改代码迁就文档）：①L126 称 `validate_workflow()` 含参数白名单校验 → 实况为执行期 `step_executor` L196-201 静默丢弃＋DEBUG 日志；②字段表未记 `target_param`/`match_param` 为零消费者休眠元数据。依据 doc-governance §7（源码↔规约同步，以代码为准）。
6. 代码层 16 项缺口**只登记不实施**（专章 §7＋backlog W-22），并在 §7 明写"任何 agent 不得据本节自行改代码"——遵守用户"严禁修改任何代码"指令。
7. Rule Designer 角色由主 agent 承担（子 agent 返回预算 ≤2K tokens，装不下完整专章草案；且用户规定"仅主 agent 写规约文件"）；Consistency Reviewer 由只读子 agent 承担。

## 执行流程

### 流程概览

- 总步骤数：8
- 多 Agent 协作：是（并发 3 个只读侦察子 agent ＋ 1 个只读一致性审查子 agent；主 agent 唯一写入方）

### 步骤记录

#### Step 1: 能力自检与 SEM 路由

- 状态：✅ 已完成
- 执行内容：确认多 agent 能力可用（Task 子 agent）；加载 `ai-coding-governance` 与 `documentation-lifecycle` 两份 specialist 规约
- 涉及文件：只读（插件目录 2 文件）
- 决策记录：primary/secondary 各 1，符合"单一 primary"铁律

#### Step 2: 只读侦察（3 子 agent 并发）

- 状态：✅ 已完成
- 执行内容：Spec Scout（规约结构与容量约束）／Registry Scout（代码层登记结构与 23 项缺口）／Context Scout（GUI 交互位置与既有方案资产）
- 涉及文件：只读（AGENTS.md、docs/ 12 篇＋2 INDEX、tools/doc_verify.py、rpa_engine 的 ops/engine/gui/tests/tools、_temp 4 份方案）
- 子 Agent：3 个，均返回 ≤2K 摘要，零写入
- 决策记录：确认三条硬约束——AGENTS 容量余量 226、章节编号锁定、docs/ 无字符上限

#### Step 3: 4 项决策点人工裁定

- 状态：✅ 已完成
- 执行内容：Plan Mode 提问 4 项（承载策略／专章落点／记录表载体／GUI 缺说明行为），全部采纳推荐项
- 决策记录：见上节表

#### Step 4: 写入新规约专章

- 状态：✅ 已完成
- 执行内容：新建 `docs/function-spec-rules.md`（§0 前提与概念／§1 触发条件与加载义务／§2 规定 1＋硬停止＋清单模板／§3 规定 2＋文档版记录表 9 行＋字段定义 10 项＋代码版载体清单＋同步与冲突裁定／§4 规定 3＋实现口径＋边界澄清／§5 规定 4＋三类变更序＋13 项登记清单／§6 与既有红线关系／§7 待补强登记／§8 校验与门禁／§9 变更记录）
- 涉及文件：创建 `docs/function-spec-rules.md`
- 决策记录：记录表 9 行取值（`param_keys`／`default_params()` 默认值）逐行核对 `ops/step_executor.py` L52-109 与 `gui/models.py` L917-937 后写入，禁止编造

#### Step 5: 知识层与导航同步

- 状态：✅ 已完成
- 执行内容：INDEX 登记＋路由 2 行＋篇数 12→13；architecture §3/§6/§8.2 交叉引用＋A1/A2 失实修正；dev-spec GUI 条目索引节增 [约束] 交叉引用＋变更记录；doc-governance §7 增触发④（功能函数变更→同步专章 §3.2）、§9 接收 AGENTS §4.7 第三列（六标签复核建议）、§7 收尾清单改 ①②③④；backlog 新增 W-22＋统计表 待指令 1→2；README 篇数/导航/R7 状态行
- 涉及文件：修改 `docs/INDEX.md`、`docs/architecture.md`、`docs/dev-spec.md`、`docs/doc-governance.md`、`docs/backlog.md`、`README.md`

#### Step 6: AGENTS.md 指针新增与等量下沉

- 状态：✅ 已完成
- 执行内容：§2.5 背书清单 +1 行；新增 §2.6 指针（三形态＋四规则名＋加载义务＋GUI 硬停止）；下沉 6 处（§4.7 第三列→doc-governance §9；§7.2 十节名称列表；§4.6 冲突细则；§6 `Test/` 行；§7.3 三层结构/关键约束合并；§8 主线段压缩）；锚点层改 R7
- 涉及文件：修改 `AGENTS.md`
- 决策记录：**§2.1/§2.2 红线本体零改动**（doc-governance §10.2 禁压条款）；下沉内容全部有接收方，无信息丢失（§4.6 细则已在 doc-governance §6 条 1/条 3；§6 `Test/` 口径已在 doc-governance §8 条 2；§4.7 第三列移入 doc-governance §9）

#### Step 7: 自检一致性与门禁

- 状态：✅ 已完成
- 执行内容：①AGENTS.md 每次编辑后 PowerShell 复固化 CRLF（防 R6 曾出现的 loneLF 漂移）②`tools/doc_verify.py` 三次运行（余量轨迹 143→190→**200**，最终 PASS/links=86/failures=0）③`unittest discover -s tests` → **118 OK**（证明零代码影响）④`git status --porcelain` 只读核查：无任何 `.py` 变更条目 ⑤只读 Consistency Reviewer 子 agent 七节审查（A~G）
- 涉及文件：只读＋`_temp/verify-20260924-1158.md`／`-1202.md`／`-1231.md` 留痕
- 决策记录：**容量二轮下沉**——首轮下沉后余量 190<200，按 doc-governance §10.2 追加 §5.2/§5.4 措辞压缩至余量 200（合规下限）；未启用"压缩红线本体"选项

#### Step 8: 审查发现项修正（同轮闭环）

- 状态：✅ 已完成
- 执行内容：Consistency Reviewer 报出 5 项高优先偏差＋5 项口径问题，全部在**文档侧**修正（零代码改动）：
  1. §3.2 注记 1：`t_{uid}` 归属由"引擎"改 **GUI**（`models.py` L708），补引擎缺省回退 `t_s{n}`（`step_executor.py` L207）
  2. 新增 §3.2 注记 3＋§7 **B9**：参数默认值双源，`mapping_match.mode`（left_join↔inner_join）与 `convert_dtype.from_type/to_type`（TEXT/INTEGER↔空串）两源取值不同
  3. §5.5 项 4：`_STEP_META_RAW`"8 字段"改 **6 元组行**（照原文填 8 值会致导入期 `ValueError`、GUI 起不来）
  4. §5.5 项 13：改为**三处等值断言**（`test_graph_edges.py` L200／`test_translation.py` L149／`smoke_m1m3.py` L188）＋`app.py` L108 定性为**下限守卫**（增至 10 项不失败）
  5. §5.5 项 1：补新建 ops 模块时的 `step_executor.py` import 与 `RPA_Workflow_v3.spec` `hiddenimports` 落点（否则 exe 场景 ImportError）
  6. §6：`execute_step` 加分支由"张力"改 **一致（不触红线）**——对齐 `architecture.md` §3.3"编排代码＝`engine/`"明文界定；画布只读的对应红线由 §10 改指 §2.1 条 6
  7. §7：补 B6 行（`keywords` 非空无守卫）；统一计数口径（18 行＝16 项＋P 系列 2 行）；修正 3 处行号漂移；C2 状态改"已随 W-22 登记"
  8. §3.3：展示序注明"仅代码版承载、不入 §3.2 文档版表"
  9. §8 项 5 术语对齐 doc-governance §10.2/§10.3；§3.5 3c 注"conflict-log 不存在则创建"
  10. frontmatter `confidence` 与 §9 变更记录如实记载本轮审查修正
- 涉及文件：`docs/function-spec-rules.md`、`docs/backlog.md`（W-22 计数与 B6/B9）、`AGENTS.md`/`README.md`/本记录（15→16 项口径同步）
- 决策记录：审查建议第 6 项（红线定性）涉及两份 [约束] 文档口径，按 doc-governance §6.2 处理——以 architecture §3.3 的明文界定为准修正本专章，并在 §6 与 REPORT ⑧ 条 5 标注"**待人工确认**"，未擅改 architecture 原文
- 环境侧提示：本次会话注入的 AGENTS.md 快照为 R6 旧版（§2.5 仅 7 篇），磁盘实况已是 R7 新版（8 篇）→ 建议人工确认注入缓存刷新，避免其他 agent 误判专章未获背书

## 涉及文件汇总

| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 创建 | `docs/function-spec-rules.md` | 核心交付物：4 条规定全文（§0~§9），binding: constraint |
| 创建 | `docs/task-records/2026-09-24-function-spec-rules.md` | 本记录 |
| 创建 | `_temp/function_spec_rules_round_2026-09-24/REPORT.md` | 规约整理报告（8 节） |
| 修改 | `AGENTS.md` | §2.5 背书 +1 行、新增 §2.6 指针、6 处等量下沉、锚点 R7、§8 主线更新 |
| 修改 | `docs/INDEX.md` | 登记 1 行＋路由 2 行＋篇数 12→13＋dev-spec/backlog 日期同步 |
| 修改 | `docs/architecture.md` | §3/§6/§8.2 交叉引用；A1（参数白名单为执行期过滤）/A2（休眠字段）失实修正；frontmatter confidence |
| 修改 | `docs/dev-spec.md` | GUI 条目索引节增 [约束] 交叉引用＋变更记录 1 行＋frontmatter 日期 |
| 修改 | `docs/doc-governance.md` | §7 增触发④＋收尾清单 ①②③④；§9 接收六标签复核建议表 |
| 修改 | `docs/backlog.md` | 新增 W-22；§5 统计 待指令 1→2＋W-22 说明；frontmatter |
| 修改 | `README.md` | 篇数 12→13；开发者/Agent 导航行；R7 状态速览 1 条 |
| 只读 | `rpa_engine/**`、`tests/**`、`_temp/DAG-rebuild/**` | **零改动**（侦察与取证） |

## 验收

| # | 验收项 | 结果 |
|---|--------|------|
| 1 | `python tools/doc_verify.py`（仓库根） | ✅ **PASS**，links=86，failures=0（终版 `_temp/verify-20260924-1239.md`） |
| 2 | AGENTS.md 容量三口径（含 CR ≤8,000／余量 ≥200／loneCR=loneLF=0） | ✅ 含 CR **7,798**／余量 **202**／LF 归一 7,600／198 行／`loneCR=0 loneLF=0`（轨迹 7,774→7,857→7,810→7,801→7,798） |
| 3 | 代码零改动（`rpa_engine/**`、`tests/**`、`_temp/DAG-rebuild/**`） | ✅ `git status --porcelain` 无任何 `.py` 变更条目；本轮写入面仅文档＋`_temp` 报告 |
| 4 | 回归零影响（`unittest discover -s tests` 期望 118 OK） | ✅ **Ran 118 tests OK**（与 R6 终态一致） |
| 5 | 4 条规定全部落地且互不冲突、与既有红线不冲突（尤其 §2.2 条 5） | ✅ 审查子 agent A/B 节结论：4 条均落地于专章 §2~§5，含触发条件与判定依据；红线原文零改动；2 处定性表述经审查修正（§6 表内留痕），1 项标注"待人工确认" |
| 6 | INDEX 13 篇 ↔ docs/ 实际一一对应；`binding: constraint` 篇数 = AGENTS §2.5 背书条数（8） | ✅ doc_verify 项 [2] 无失败；8 = 8 |
| 7 | 记录表 9 行取值 ↔ 代码逐格核对 | ✅ 主字段（key/中文名/分类/`param_keys`/是否产表/表单类）逐格相符；审查发现的注记归属错误与默认值双源已修正并登记 B9 |

## 关闭标识

- **完成时间**：2026-09-24
- **最终状态**：✅ 全部完成（1 项定性待人工确认，不阻塞）
- **关闭说明**：4 条规定已固化为具 [约束] 效力的 `docs/function-spec-rules.md`（经 AGENTS §2.5 背书、§2.6 指针引导），后续 agent 涉功能函数操作即按该文件执行；代码层 16 项缺口登记 W-22 待人工立项；**本轮零代码改动**，输出后停止等待人工下一步指令。
