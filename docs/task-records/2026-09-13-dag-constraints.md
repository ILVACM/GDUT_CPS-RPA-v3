# 任务记录：确立 DAG 重构两条强约束 + CLI 弃用的规约调整（纯文档，零代码）

## 摘要
- **任务目标**：将「ETL 架构刚性」（底层）与「最高目标原则」（顶层/GUI 交互）两条强约束写入 `AGENTS.md` §2 红线，细则落 `docs/architecture.md`；并按"程序不再需要 CLI 交互、全部改为 GUI"同步调整相关规约表述
- **任务状态**：✅ 已完成
- **开始时间**：2026-09-13 16:06 (UTC+8)
- **最后更新**：2026-09-13
- **要点摘要**：两条强约束写入 AGENTS.md §2 红线（§2.1 条 6 最高目标原则 / §2.2 条 9 ETL 架构刚性）、细则落 architecture.md §8.4+§10；CLI 口径统一为"废弃（目标态）"并登记 W-18/W-19；AGENTS.md 含 CR 7,701 → **7,794（余量 206）**；三步五查 + 独立复查通过；零代码改动
- **操作人**：黄泊凯

## 用户输入

> "好的，我们正式进入对当前RPA引擎GUI交互中DAG可视化部分的重构工作。请在此前已有框架的基础上，先补充并明确两条强约束，并据此调整相关约束文档，为后续的重构设计与代码实现做准备。
> 约束一（底层）：严格保证使用当前ETL架构设计，它是当前程序实现的技术底层与功能基础，不得偏离或替换。
> 约束二（顶层/GUI交互）：确立"最高目标原则"，即目标用户为没有任何技术背景的企业文员，一切交互必须从简且易懂；所有将用户交互指令翻译为底层操作指令的中间转换均由程序代码完成，技术细节对用户完全隐藏，也无需可见。
> 此外，当前程序不再需要CLI交互，全部改为GUI交互，请据此自适应修改相关约束规定。
> 当前阶段仅进行文档调整与约束梳理，不要进行任何代码相关操作，也不要输出代码。制定修改计划（注意自适应结合多agent协作模式，尤其在校验验证阶段），并在人工确认后执行。"

> 后续指令："计划确认，执行"

## Agent 理解与决策

**关键释义（已确认 D1）**：约束一（JSON 参数文件为业务逻辑唯一载体）与约束二（转换全由代码完成）**不冲突**——约束二约束的是**用户层**；JSON 参数文件仍为唯一载体，只是由 GUI 代码生成与维护、用户从不接触。§2.2 条 2 不变。

**关键区分（取证结论）**：CLI 字面引用分三类，仅第一类属本次调整对象——
1. **程序 CLI 交互**（`main.py` 的 `argparse`/`--cli`/传 `workflow_json`）：本次调整（文档口径 + 登记 W-18 编码待办）
2. **构建期命令行**（`build.bat` 的 `--build-dir/--output/--clean`、`pyinstaller` 命令行、`build-guide.md`）：**无关，不动**
3. **历史任务记录**（`docs/task-records/*` 中"CLI 适配"等当时事实）：**不动**（§7.1 信息不丢失）

**取证要点**：源码侧仅 `rpa_engine/main.py` 一处 `argparse`（`:14/92-134`，入口判定在 `:115`）；`executor.py:41`、`gui/main_window.py:368` 为旁涉注释；`gui/app.py:211` 的 `sys.argv` 仅供 Qt 初始化；`build.bat:47-83` 为构建脚本自身参数解析。

**决策（4 项口径，用户全部采纳推荐项）**：D1 JSON 仍唯一载体、对用户隐藏｜D2 细则复用 `docs/architecture.md`（§8.4 + §10），不新增文档、不增 §2.5 背书项｜D3 CLI 标废弃（`[方案态]`）+ 登记 W-18｜D4 本轮即写入可理解性验收判据（含界面文案禁用词表）

**字符预算（硬约束）**：`AGENTS.md` 开工前 **含 CR 7,701 / 8,000（余量 299）**；两条新红线 + 条 3 改写 ≈ +225，同步压缩 §7.2（−45）、§8（−90）、锚点层（−150），净 ≈ −55 → 目标余量 ≥ 200

## 执行流程

### 流程概览
- 总步骤数：8
- 多 Agent 协作：是（5 个子 Agent：Writer A / Writer B / Indexer / Auditor / Verifier）

### 步骤记录

#### Step 1: 备份受控文件并新建本记录
- 状态：✅ 已完成
- 执行内容：7 个受控文件备份至 `_temp/BackUp/*.bak-20260913-pre-dagconst`；按 `TEMPLATE.md` 新建本记录（先有后写）
- 涉及文件：`_temp/BackUp/*`（7）、本记录
- 复验：`git ls-files --eol` 记录基线（AGENTS.md / README.md / docs/INDEX.md / docs/architecture.md / docs/dev-spec.md / rpa_engine/README.md 均为 **w/crlf**）

#### Step 2: Writer A —— 扩写 docs/architecture.md
- 状态：✅ 已完成
- 执行内容：新增 **§8.4 交互设计原则（最高目标原则）**（目标用户与可理解性验收判据含界面技术术语禁用词表／交互从简／转换全由代码完成／技术细节隐藏／与既有条款关系）与 **§10 架构刚性边界（ETL 底层不可偏离）**（架构基线／允许的扩展／禁止的替换／与 §8.4 的关系／对 DAG 重构的约束）；§3.2 的 "GUI 与 CLI 均经此接入" 改口径；frontmatter 与头部同步
- 涉及文件：`docs/architecture.md`（350 → 416 行；§8.4 落 339-369、§10 落 384-416）
- 子 Agent：Writer A（general-purpose）；回报 CRLF 保真、`lone_CR=0`、7 处断言通过

#### Step 3: Writer B —— CLI 口径三文件同步
- 状态：✅ 已完成
- 执行内容：`README.md:21` 启动说明改口径并标 `[方案态]`；`rpa_engine/README.md` tags 去 `CLI`、调试入口小节改写为"已废弃 + 历史用法保留"、目录树注释改口径；`docs/dev-spec.md` GUI 条目索引两行 + 变更记录追加一行 + frontmatter
- 涉及文件：`README.md`、`rpa_engine/README.md`（127→130 行）、`docs/dev-spec.md`（549→550 行）
- 子 Agent：Writer B；回报 3 文件均 CRLF、`lone_CR=0`，且 task-records / build.bat / build-guide / .spec / 源码**未被改动**

#### Step 4: Indexer —— 索引与待办登记
- 状态：✅ 已完成
- 执行内容：`docs/INDEX.md` architecture/dev-spec 摘要与最后更新同步、§3 路由补 3 行；`docs/backlog.md` 新增 **W-18**（移除 main.py CLI 分支，编码任务）/ **W-19**（评估 §8.2 阶段 3 ConsolePanel 技术信息暴露，交 W-03）、§5 统计（待指令 3→5）与建议顺序
- 涉及文件：`docs/INDEX.md`（54→57 行）、`docs/backlog.md`（76→78 行）
- 子 Agent：Indexer；回报两文件 CRLF、`lone_CR=0`，`docs/plan/**`、`_temp/**`、`rpa_engine/**` 未动

#### Step 5: 主 Agent 亲写 AGENTS.md
- 状态：✅ 已完成
- 执行内容：§2.1 新增条 6「最高目标原则」；§2.2 新增条 9「ETL 架构刚性」、条 3 改写为「GUI 为唯一交互入口（不提供 CLI 交互）…引擎可被程序化调用、不依赖 GUI」；§7.2 与 §8 压缩；锚点层覆写
- 决策记录：首次落盘后含 CR 7,829（余量 171）**不满足 doc-governance §10 的余量 ≥200**，遂补充压缩 §3 模式枚举、§7.1、§4.2、§6 表行，并进一步压缩后定稿 **7,794（余量 206）**
- 涉及文件：`AGENTS.md`（CRLF 保真、196 行、`lone_CR=0`）

#### Step 6: 校验阶段（多 Agent）+ 修正 + 收尾
- 状态：✅ 已完成
- 执行内容：
  - **Auditor**（独立子 Agent）：按 `doc-governance.md` §4 分步执行三步 + 五项校验 → **三步全过、五项全 ✅**；提出问题 3 项（均【建议】级，无【阻断】）
  - **Verifier**（独立子 Agent）：残留 CLI 分类复查（"应当改但仍未改" = **无**）、误改检查（`rpa_engine/**`、`.spec`、`build.bat`、`docs/plan/**`、`anchor-mechanism.md` **零改动**）、AGENTS.md 三口径与行尾、新条款冲突核验（**无矛盾**）
  - **采纳 Auditor 全部 3 项建议**：① `README.md` slim2 数值 7,613 → **7,628**（与 doc-governance §10、backlog W-01 统一）② `doc-governance.md` §4 Step 1 的七类章节列序对齐 AGENTS.md 实际（子目录职责边界 在 维护与校验 之前）③ `docs/backlog.md` §3 关闭计数 10 → **12 项**（与 §5 统计一致）
  - 锚点收尾（状态 → `已完成`、要点摘要回填实测值）
- 涉及文件：`_temp/verify-dag-constraints.md`

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 备份 | `_temp/BackUp/*.bak-20260913-pre-dagconst`（7 个） | 执行前快照 |
| 新建 | `docs/task-records/2026-09-13-dag-constraints.md` | 本记录 |
| 待建 | `_temp/verify-dag-constraints.md` | 校验报告 |
| 备份 | `_temp/BackUp/*.bak-20260913-pre-dagconst`（7 个） | 执行前快照 |
| 新建 | `docs/task-records/2026-09-13-dag-constraints.md` | 本记录 |
| 新建 | `_temp/verify-dag-constraints.md` | 全局更新校验报告 |
| 修改 | `docs/architecture.md` | 新增 §8.4（339-369）+ §10（384-416）；§3.2 口径；frontmatter/头部 |
| 修改 | `AGENTS.md` | §2.1 条 6、§2.2 条 9、条 3 改写、§3/§4.2/§6/§7.1/§7.2/§8 压缩、锚点覆写 |
| 修改 | `README.md` | 启动说明改口径（`[方案态]` + W-18）；slim2 数值订正 7,628 |
| 修改 | `rpa_engine/README.md` | tags / 调试入口小节 / 目录树注释口径 |
| 修改 | `docs/dev-spec.md` | GUI 条目索引两行 + 变更记录一行 + frontmatter |
| 修改 | `docs/INDEX.md` | 两行摘要与最后更新、§3 路由补 3 行、frontmatter |
| 修改 | `docs/backlog.md` | 新增 W-18/W-19、§5 统计与顺序、§3 计数口径订正 |
| 修改 | `docs/doc-governance.md` | §4 Step 1 七类章节列序订正（1 行） |
| **规约同步**（§7 检查清单） | 源码变更=无；规约变更已同步 `docs/INDEX.md`、`docs/backlog.md`、`README.md` | 无 `[待补充]` 遗留 |

## 关闭标识
- **完成时间**：2026-09-13 16:20 (UTC+8)
- **最终状态**：✅ 全部完成
- **关闭说明**：两条强约束（§2.1 条 6 最高目标原则 / §2.2 条 9 ETL 架构刚性）已写入约束层红线，细则落 `docs/architecture.md` §8.4/§10；CLI 口径统一为"废弃（目标态）"并登记 W-18/W-19；AGENTS.md 含 CR **7,794（余量 206）**满足 §10 判据；三步五查 + 独立复查双通过；**零代码改动**（`rpa_engine/**`、`.spec`、`build.bat` 均未动）
