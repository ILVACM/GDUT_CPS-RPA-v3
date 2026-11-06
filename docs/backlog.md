---
title: Backlog — 规约与文档治理待办清单
type: knowledge
scope: global
status: active
owner: 黄泊凯
last-updated: 2026-11-01
tags: [待办, backlog, 治理队列]
binding: reference
confidence: 已校验一致（首版自 _temp/repo-context-report.md §4.6 映射，2026-09-13——该文件已于 2026-09-24 R10 清理，其队列职能由本文件独承，骨架见 `_temp/ledger_2026-09-24/CLEANUP_MANIFEST.md` §2.6；状态逐项与磁盘实测对齐；2026-09-24 R7 新增 W-22；2026-10-24 R16 关闭 W-20/W-22、新增 W-23/W-24、统计重算；2026-11-01 R17 关闭 W-23（运行产物移出版本控制）、W-24（模板化输出裁定暂缓），统计重算）
content-revision: 2026-10-24
---

# Backlog — 规约与文档治理待办清单

> **权威声明**：本文件是 W 编号待办清单的**唯一受管辖活载体**（知识层，经 docs/INDEX.md 索引）。
> `_temp/repo-context-report.md` §4.6 为 2026-09-13 的**来源快照**（`_temp/` 无约束力；该文件已于 2026-09-24 R10 清理，见 ledger 夹 CLEANUP_MANIFEST §2.6）；二者冲突以本文件为准，来源追溯仍指向该 §4.6。
> 历史沿革：Q-1~Q-10（2026-09-02 队列）与 G-1~G-6（结构性缺口）已于 2026-09-13 合并映射为 W 编号；Q 队列文件 `_temp/todo-from-context-report.md` 曾作为历史记录、不再作为执行入口，已于 2026-09-14 随 `_temp` 清理删除。

## 1. 执行约定

1. **逐项由人工下指令驱动**（如"处理 W-06"），Agent **不自动批量推进**
2. 大改动（尤其规约变更）走「方案 → 人工复核 → 执行」，方案落 `_temp/`
3. 每项完成后回写本文件的**状态**列（本节为 2026-09-02 约定的延续，此前未被执行，已于 2026-09-13 补齐）
4. 涉及规约文档变更的，须执行 [docs/doc-governance.md](./doc-governance.md) §4 全局更新校验机制
5. **Git 写操作（提交/推送/拉取/分支/合并/回退/暂存/清理等）由人工接管，Agent 不执行**；Agent 仅在比对差异时使用**只读** git（`status`/`diff`/`show`/`log`），不得改变工作区、索引或版本库状态（2026-10-24 口径细化，见 `AGENTS.md` §1）

## 2. 待办主表

状态取值：`待指令` / `执行中` / `已完成` / `已裁定关闭` / `已撤销`

| 编号 | 事项 | 关联位置 | 状态 | 处置依据 / 说明 |
|------|------|----------|------|------------------|
| **W-01** | AGENTS.md 注入字符计数口径裁定与处置 | `AGENTS.md` | ✅ 已完成（09-13） | 口径 = 含 CR；8,104 → 7,628（≤8000，截断解除）；`docs/task-records/2026-09-13-agents-slim-v2.md` |
| **W-02** | DAG 9 项定稿歧义逐条裁定（采纳/拒绝/补充） | `_temp/DAG-rebuild/plan.md` 附录 B（原歧义正本已并入） A~I | ✅ 已完成（09-14） | **9 项全部采纳**并回写 plan 正本+副本（`docs/plan/DAG_refactor_plan.md` §4.2/4.7/5.1/5.2/5.4/5.5/5.6/5.8/§3.3）；歧义文件正本已随 09-18 `_temp` 收敛清理并入 `_temp/DAG-rebuild/plan.md` 附录 B；记录 `docs/task-records/2026-09-14-w02-ambiguity-rulings.md` |
| **W-03** | 用户视角改造方案拍板（P0 6 项 / P1 3 项） | `_temp/DAG-rebuild/plan.md`（原 `README.md` §4 已并入） | ✅ 已完成（09-16；**M0-M7 已完成 09-20**） | 人工测试验证+范围收敛（09-15 取消/保留清单）+动态扩展定案（09-16）；**D6 回写 plan 正本第八章**（动态配置与用户视角呈现层规范）+调序条款取消同步（C1 待办同批关闭）+P0 口径同步（row_cy 193/卡片 70px）；示范验证 46 单测+7 场景全绿（09-18 固化 SampleCode 后为 61 单测+11 场景）；**M0-M7 已于 2026-09-20 全阶段闭环**（实际实现为 `gui/node_graph.py` 单文件，`gui/graph/` 包方案未采纳）；记录 `docs/task-records/2026-09-20-m0-mb-me-canvas-page.md` |
| **W-04** | 修正 `Instances-INDEX` L22 断链 | `knowledge/Instances-INDEX.md` L22 | ✅ 已完成（09-13） | 改为 `../docs/doc-governance.md`；全库复扫真断链 0 |
| **W-05** | 同步同文件 `last-updated` | 同上文件头 | ✅ 已完成（09-13） | 2026-08-21 → 2026-09-13 |
| **W-06** | 回写 `_temp/todo-from-context-report.md` 执行记录表 | `_temp/todo-from-context-report.md` | ✅ 已完成（09-13） | 补记 Q-1~Q-10 实况 + Q→W 映射 + 历史缺口说明。**注**：该源文件已于 09-14 随 `_temp` 清理删除，本记录为留档 |
| **W-07** | `Test/` 双份同名 xlsx 性质裁定 | `Test/input/`、运行期副本目录 | ✅ 已裁定关闭（09-13；**10-24 证据路径订正**） | **正常中间产物，保留不删**：`gui/page_input_selection.py:35/196/250` + `ops/excel_preprocessor.py:52-67` `shutil.copy2` 生成；两文件 md5 相同且均被 git 跟踪；`AGENTS.md` §6 明文"运行产物保留不删"。**2026-10-24 注记**：`Test/temp/input_selection/` 已不存在；实际副本目录为 `rpa_engine/temp/input_selection/`（当时 git 跟踪 224 个文件，见 W-23）；**2026-11-01 R17：运行产物已移出版本控制**（`v3/.gitignore` + `git rm --cached`），工作区文件保留不删，结论不变 |
| **W-08** | 是否现在重打包 exe | `build/RPA_Workflow_v3.exe` | ✅ 已裁定关闭（09-13） | **不重打包**（依当时"源码零改动"前提）；判据见 `docs/build-guide.md` §1.10。**注**：2026-09-13 代码清理后源码已变更，exe 已失效，后续重建见 W-20（**W-20 已于 2026-10-24 核验关闭**） |
| **W-09** | 锚点层是否需承载"当前无进行中任务" | `AGENTS.md`「当前任务锚点」、`docs/anchor-mechanism.md` | ✅ 已裁定关闭（09-13） | **关闭，无需改动**：规定层已定义锚点层含「状态」字段，现值 `已完成` 已能表达；规定层无修改必要 |
| **W-10** | G-4 / G-5 / G-6 落地 | `docs/doc-governance.md` §7/§8、`docs/agent-execution-mode.md` §6 | ✅ 已完成（09-13） | §7 源码↔规约同步规则；§8 验收与回归记录规范（含事实校准：无现成回归套件）；编码类角色集 Coder/Reviewer/Tester |
| **W-11** | 记忆层与磁盘不一致 | `.workbuddy/memory/` | ✅ 已完成（09-12） | 已修正 `MEMORY.md` 并补日志 |
| **W-12** | 环境校验手法注记 | `_temp/repo-context-report.md` §0.5（已随 R10 清理，见 ledger 夹 CLEANUP_MANIFEST §2.6） | ✅ 已完成（09-12） | 已固化 |
| **W-13** | 补录 2026-09-02 任务记录 | `docs/task-records/` | 🚫 已撤销（09-13） | 见 §4 撤销登记 |
| **W-14** | 标签体系用法统一 | `docs/doc-governance.md` §9、`rpa_engine/README.md` | ✅ 已完成（09-18 闭环） | 已完成：§9 标签落位规范（binding 四档 ↔ 四标签映射）+ 实例 README 补 `binding`/`confidence`；**顺延部分已于 09-18 闭环**：`docs/plan/DAG_refactor_plan.md` 的 `binding` 经 §9 四档映射核对——方案态层且已无未裁定条目（F 批 09-18 裁定回写），保持 `reference` 并在正本 frontmatter 记录结论 |
| **W-15** | 复核 `DAG_refactor_plan.md` L463 对「§7.2」的引用 | `docs/plan/DAG_refactor_plan.md`（真身=附录 A 的 D6 裁定行，含字符串「AGENTS.md §1/§2.4/§7.2」；行号随回写漂移，以字符串定位） | ✅ 已完成（09-18 闭环） | 复核结论：所记 L463 处并无 §7.2 引用（该处为 §七 风险表表头）；真身 D6 裁定行的「AGENTS.md §1/§2.4/§7.2」表述经核对**准确**（AGENTS §7.2=治理细则索引），无需改正文；本条以复核结论关闭 |
| **W-16** | 待办队列落位（原 `_temp/pending-items.md` 已过时） | 本文件 | ✅ 已完成（09-13） | 队列升格为受管辖文档 `docs/backlog.md`；`AGENTS.md` §8 指针改向本文件；旧文件头部标注 `[已过时-待确认]`。**注**：原 `_temp/pending-items.md` 已于 09-14 随 `_temp` 清理删除 |
| **W-17** | 约束层容量与写法规约缺失 | `docs/doc-governance.md` §10 | ✅ 已完成（09-13） | 固化：口径 = 含 CR；上限 8,000 且余量 <200 须先下沉；行尾必须 CRLF；下沉目标与复测要求 |
| **W-18** | 移除 `main.py` 的 CLI 交互分支与 `argparse` 依赖 | `rpa_engine/main.py:14/92-134`；连带 `RPA_Workflow_v3.spec:12/14` 注释、`rpa_engine/engine/executor.py:41`、`rpa_engine/gui/main_window.py:368` 旁涉注释 | ✅ 已完成（09-13） | 执行：main.py 瘦身（CLI 分支 / `run_workflow` / `argparse` / `_setup_logging` 已删，`main()` 为 GUI 薄壳）；`steps/` 死代码目录物理删除；旁涉注释与文档口径同步；验收 A1/A4 通过、A2/A3 环境受限降级（移交真机）、A5~A6 过；记录 `docs/task-records/2026-09-13-code-cleanup.md` |
| **W-20** | 重建 `build/RPA_Workflow_v3.exe`（源码已变更，现有 exe 已失效） | `build.bat`、`docs/build-guide.md` §1.9/§2 | ✅ 已完成（2026-10-24 核验） | **构建由人工接管（R2）**：Agent 不执行 build.bat、不修改 `build/` 产物；真实环境路径见 `docs/runtime-env-spec.md` §2（R5，`C:\Users\hbk\.conda\envs\CPS-GPES_RPA-py311`）；有效性判据见 `docs/build-guide.md` §1.10。**2026-10-24 核验**：`build/RPA_Workflow_v3.exe` 2026-10-19 03:57 构建，`SOURCE_HASH=9fc85bc09ac1376a` 与当前源码重算一致（FILES=56），`TESTS_SKIPPED=0` → **有效**；本条关闭 |
| **W-19** | 评估 `architecture.md` §8.2 阶段 3 ConsolePanel 的技术信息暴露 | `docs/architecture.md` §8.2、§8.4 第 4 条；`rpa_engine/gui/` | ✅ 已裁定关闭（09-18） | 2026-09-13 新发现：ConsolePanel 将引擎日志直接呈现在面向用户的主界面，与「最高目标原则」的技术细节隐藏要求存在潜在冲突。**裁定=移除**：删除 `gui/widgets.py`（ConsolePanel）；`worker.py` 移除 loguru→GUI 转发与 `log_message` 信号；`page_progress/page_report` 移除右侧容器与 `attach_console`、页面改独占布局；日志改由 `logs/gui_*.log` 文件承载（开发者排查入口）；architecture §8.1/8.2/8.4 与 dev-spec §5/§17 同步改口径。记录 `docs/task-records/2026-09-18-w19-consolepanel-removal.md` |
| **W-21** | 存疑项 5 条补充裁定落地登记（R1~R5） | 本文件 + `docs/runtime-env-spec.md` + `docs/build-guide.md` + `rpa_engine/templates/README.md` + `README.md` | ✅ 已完成（09-14） | R1 GUI 先重构设计后代码（生效）；R2 `build/` 及构建产物 Agent 忽略/人工接管（执行）；R3 模板全部失效清理（执行，见 W-21 注）；R4 `_temp` 清理至仅 DAG-rebuild + repo-context-report.md（执行）；R5 conda 环境 `CPS-GPES_RPA-py311` 路径固化 `C:\Users\hbk\.conda\envs\CPS-GPES_RPA-py311`（生效，落 runtime-env-spec §2）。**注**：R3/R4 物理清理随本记录同步执行 |
| **W-22** | 功能函数规约待补强项群（16 项：守卫缺口 / 记录表字段缺口 / 测试与硬编码口径） | `docs/function-spec-rules.md` §7（逐项附代码行号证据）；关联 `rpa_engine/gui/models.py`、`gui/app.py`、`gui/forms.py`、`ops/step_executor.py`、`engine/validator.py` | ✅ 已完成（2026-10-19 R15；**2026-10-24 结账关闭**） | R7 规约整理轮（2026-09-24）**只登记不实施**；**R15（2026-10-19）经人工批准施工**（方案＝`.trae/documents/backlog-remediation-control-pack.md`）：核心＝`BUILTIN_OPS.params_schema` **单一源化**（闭合 B9＝B-41／D2＝B-64／P2-1＝B-69），并闭合 B1（B-54）／B2（B-55）／B3（B-56）／B4（B-57）／B6（B-58）／B7（B-59）／B8（B-60）／C1（B-61 删字段）／C2（B-62 删字段）／D1（B-63）／D3（B-65）／D4（B-53）／E1（B-66）／E3-A4（B-67／B-68）；B5 复核确认已由 B-13（R12）解决；P2-2 维持既有裁定（不改 9 分支）；**P1-6（返回值消费）转受控例外**（红线③，随 B-18／B-44）。处置状态逐行见 §7「R15 处置」列；**2026-10-24 结账：状态由「执行中」改「已完成」，统计口径同步** |
| **W-23** | `rpa_engine/temp/` 运行产物被 git 跟踪 + 启动清理会删夹具 | `rpa_engine/temp/`、`v3/.gitignore`、`gui/main_window.py::cleanup_stale_files` | ✅ 已完成（2026-11-01 R17） | **2026-10-24 R16 登记**：`git ls-files v3/rpa_engine/temp` = 249 个文件被跟踪；`cleanup_stale_files`（默认 `cutoff_hours=24`）在 `MainWindow` 构造时清理超龄副本 → 任何一次真机启动都会让工作区变脏。**2026-11-01 R17 执行**（经人工指令授权单次 Git 索引操作）：新建 `v3/.gitignore`（`rpa_engine/temp|storage|workspace|logs/` 四条）；`git rm -r --cached` 移出 **250 条**（temp 249 ＋ storage/recent_steps.json 1），**工作区文件全部保留**；程序清理逻辑不变。**commit/push 仍由人工执行**。证据见 `_temp/repo-scan-2026-10-23.md` §五 B′、任务记录 `2026-11-01-w23-w24-remediation.md` |
| **W-24** | "模板化输出"红线 vs 现行 `export` 无模板流式直出的口径冲突 | `AGENTS.md` §2.1 条 4、`docs/dev-spec.md` §3、`ops/exporter.py` | ✅ 已裁定关闭（暂缓，2026-11-01 R17） | **2026-10-24 R16 登记**：`AGENTS.md` §2.1 条 4 要求"预设模板 + 数据填充"，但 `ops/exporter.export_table` 为 `Workbook(write_only=True)` **流式直出、无模板**；`templates/outputs/` 仅 `.gitkeep`。**2026-11-01 人工裁定＝暂缓**：规则改为「**模板化输出（暂缓）**」——目标态保留、现行实现不变、**不阻塞交付**；`AGENTS.md` §2.1 条 4 / `dev-spec.md` §3 / `architecture.md` §6 三处同步为「暂缓」表述；模板能力不实现（如日后恢复，按功能函数规约新增 `ops/` 操作并登记 `BUILTIN_OPS`） |
| **W-25** | `rpa_engine/tests/__init__.py` docstring 与实际测试规模不符（写 2 个文件，实际 15 个） | `rpa_engine/tests/__init__.py`、`tools/make_fingerprint.py` | ⏸️ 待指令（人工，随下次构建窗口） | **2026-10-24 R16 登记**：该文件在源码指纹计算范围内（`rpa_engine/**/*.py`），修正 docstring 会使 `SOURCE_HASH` 由 `9fc85bc09ac1376a` 变为其它值，导致现有 exe 失效需重建。本轮为守住「零源码改动 + exe 有效」两条不变量，**已回滚该文件**；docstring 修正与 exe 重建应在同一人工构建窗口内完成。 |

## 3. 已关闭归档

2026-09-12 与 2026-09-13 两轮共关闭 **12 项**：W-01、W-04、W-05、W-06、W-07、W-08、W-09、W-10、W-11、W-12，以及 W-16、W-17；2026-09-14 增补关闭 **W-21**（登记 5 条裁定）与 **W-02**（9 项歧义裁定）；2026-09-16 关闭 **W-03**（D6 回写+门控解除，M0-M7 已于 09-20 闭环）；2026-09-18 关闭 **W-14/W-15/W-19**；2026-09-13 关闭 **W-18**；**2026-10-24 关闭 W-20（exe 重建核验）与 W-22（R15 结清）**。截至 2026-10-24，关闭合计 **21 项**（W-01~W-12、W-14~W-22；W-13 撤销）。

## 4. 撤销登记

**W-13｜补录 2026-09-02「方案打磨」轮次任务记录 —— 已撤销（2026-09-13）**

- **撤销依据**：`docs/task-records/2026-09-06-agents-spec-refactor.md` L22/L52 已明确记载"**不为其补建三条任务记录（用户未要求留痕）**"——该轮不留痕系既有裁定（Q-8 处置的一部分），补录会与既有裁定相悖。
- **实质结论已保留**：该轮的核心结论（"文职零培训不能理解"）与 9 项歧义指向已由 `AGENTS.md` §8 门控句与 `docs/plan/INDEX.md` 承载。
- **可比方案**：若日后需要该轮留痕，应作为"补录"并在记录中标注数据来源（`.workbuddy/memory/2026-09-02.md` 与 `_temp/` 产物），且须先取得明确指令。

## 5. 推进顺序与统计

**建议顺序**：历史项（W-02/W-03/F 批/W-14/W-15/W-19）**全部已完成**；**M0-M7 已于 2026-09-20 全阶段闭环**；**W-20 已于 2026-10-24 核验关闭**；**W-22 已于 2026-10-19 R15 结清**。**W-23 已于 2026-11-01 完成**（运行产物移出版本控制）；**W-24 已于 2026-11-01 裁定暂缓并关闭**。当前仅剩：**W-25（tests docstring 修正随构建窗口）**；真机批与构建项仍为人工责任（受控例外）。

| 状态 | 计数 | 编号 |
|------|------|------|
| ⏸️ 待指令 | 1 | W-25 |
| ✅ 已完成 / 已裁定关闭 | 23 | W-01~W-12、W-14~W-24 |
| 🚫 已撤销 | 1 | W-13 |

> **W-22 说明（R7，2026-09-24）**：功能函数规约待补强项群为**规约整理轮的登记产物**，非紧急缺陷；18 行明细与行号证据见 `docs/function-spec-rules.md` §7。**2026-10-24 状态：R15 已结清（15 行闭合＋B5 已解决＋P2-1 闭合＋P2-2 维持裁定＋P1-6 转受控例外），本条关闭**。
> **R15 执行说明（2026-10-19）**：经人工批准，按 `.trae/documents/backlog-remediation-control-pack.md` 施工，与 `_temp/ImportData/plan.md` 台账 `B-45`~`B-79`（35 项）**同批结清**。闭合与例外明细见 `docs/function-spec-rules.md` §7「R15 处置」列及 `docs/task-records/2026-10-19-w22-n-remediation.md`。

> **主线提示（2026-11-01）**：M0-M7 已完成（09-20）；W-20 已核验关闭；W-22 已结清；**W-23 已完成**（运行产物移出版本控制）；**W-24 已裁定暂缓并关闭**。**下一步待人工裁定：W-25（tests docstring 修正随构建窗口）**；真机批（受控例外）与构建重建仍由人工接管。
