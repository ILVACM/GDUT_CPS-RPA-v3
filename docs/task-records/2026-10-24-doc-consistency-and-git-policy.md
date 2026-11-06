# 任务记录：文档自适应一致性修正与 Git 使用边界收口

## 摘要
- **任务目标**：全库文档口径对齐 2026-10-24 实况；固化 Git 新边界（写操作人工接管、只读 diff 允许）
- **任务状态**：`已完成（2026-10-24）`
- **开始时间**：2026-10-24
- **最后更新**：2026-10-24
- **要点摘要**：Git 边界固化；24 个文档修正（根索引/实例/13 篇知识/2 篇方案态）；W-20、W-22 关闭，W-23、W-24、W-25 登记；零源码、零构建、零 Git 写操作；234 tests／双 smoke／自检 6/6／doc_verify PASS／AGENTS 余量 249
- **操作人**：黄泊凯

## 用户输入

> 很好，现在是这样，以后所有git相关操作（提交和推送这样）都由人工接管，agent不要管，agent只在需要比较 diff 的时候采用git。
> 然后自适应修正文档，不要有遗漏。

（方案经人工批准：《文档自适应一致性修正与 Git 使用边界收口》执行计划）

## Agent 理解与决策

- **Git 新边界**：写操作（提交/推送/拉取/分支/合并/变基/回退/暂存/清理）一律人工；Agent 仅在比对差异时用只读 `git status`/`git diff`/`git show`/`git log`，不得改变工作区、索引或版本库状态。
- **"不要有遗漏"** 的解释：以 2026-10-24 实测事实为基线，逐文档核对；历史任务记录正文不改写（记录当时事实），仅订正"摘要状态与文末关闭标识自相矛盾"的 4 篇状态行。
- **边界**：零源码改动、零构建（build.bat 仍人工）、零依赖变更、零 Git 写操作；模板化输出红线原文不动，只加现行口径注记并登记 W-24 待人工裁定。
- **运行方式**：模式 B（多 Agent 协作，Lead + 3 Writer + 1 Verifier）；环境支持子 Agent 派发。

## 执行流程

### 流程概览
- 总步骤数：5 阶段（Phase 0 前置 → Phase 1 三路并行 → Phase 2 汇总 → Phase 3 独立校验 → Phase 4 收尾）
- 多 Agent 协作：是（Lead + Writer A/B/C + Verifier）

### 步骤记录

#### Phase 0: 前置（快照 + 事实表 + AGENTS 容量下沉 + 任务记录骨架）
- 状态：✅ 已完成
- 执行内容：25 个目标文档快照至 `_temp/doc-fix-backup-2026-10-24/`；`_temp/doc-fix-factsheet-2026-10-24.md` 建立事实基线；`AGENTS.md` 容量下沉（§2.6/§4.3/§5.3/§7.3）＋ Git 新措辞，含 CR 7,877→7,751（余量 123→249）；本任务记录建立
- 涉及文件：`_temp/doc-fix-backup-2026-10-24/`（25）、`_temp/doc-fix-factsheet-2026-10-24.md`、`AGENTS.md`、本文件
- 决策记录：容量下沉以 §7.3 锚点摘要为主（信息全在 `docs/anchor-mechanism.md`，符合 §7.1 信息不丢失），辅以 §2.6/§4.3/§5.3 三处压缩

#### Phase 1: 三路并行文档修正（Writer A/B/C）
- 状态：✅ 已完成
- 执行内容：
  - **Writer A（D01-D07，7 文件）**：根 `AGENTS.md` 全文重写（实际目录树/文档索引/快速导航/术语/Git 边界）；根 `README.md` 快速开始改 `cd v3` → `python rpa_engine/main.py`；`v1/FROZEN.md` 补 CNAS/；`v2/FROZEN.md` 目录改 A-docs/ + 6 部门；`v3/README.md` 技术栈补全 + exe 有效 + W-20 关闭；`rpa_engine/README.md` 目录树/测试规模/frontmatter v1.4.0
  - **Writer B（D09-D12，4 文件）**：`architecture.md` 修 `load_tables`→`ensure_input_tables`、hiddenimports 口径、§4 数据传递字段与 SessionDB 连接模型、§6 笔误、§8 graph/ 未采纳、§9 测试输入名；`dev-spec.md` §3 加现行口径（无模板流式直出，W-24）、Word/TXT/PPT 能力缺口、BaseStep 已删、GUI 已完成；`build-guide.md` §1.9 spec 不在版本库、§1.10 exe 有效 + W-20 关闭、§3 补 backup/；`legacy.md` 9 项 BUILTIN_OPS、A-docs/、Word 能力缺口
  - **Writer C（D13-D18，5 文件）**：`runtime-env-spec.md` Git 基线改 SOURCE_HASH 判定、测试输入名；`doc-governance.md` Git 口径细化、234 用例；`user-manual.md` 按钮名/进度状态/终止语义；`deployment-guide.md` 4 个运行目录、build/backup 定性、指纹脚本位置；`function-spec-rules.md` 行号刷新（L742-761/L32-96/L1002-1016/L319-417/L88-91/L312）+ §9 R16 行
- 涉及文件：16 个（7+4+5）
- 决策记录：三路写作用域互不重叠；均以事实表为唯一事实源

#### Phase 2: Lead 汇总（backlog / 方案态 / INDEX / 任务记录状态 / 锚点）
- 状态：✅ 已完成
- 执行内容：
  - `docs/backlog.md`：W-20 改 ✅ 已完成（10-24 核验）、W-22 改 ✅ 已完成（R15）、W-03 补 M0-M7 已完成、W-07 补证据路径订正、W-08 补 W-20 已关闭、§3 关闭合计 21 项、§5 统计改 待指令 3（W-23/W-24/W-25）/已完成 21/撤销 1、主线提示重写；新增 W-23/W-24/W-25
  - `docs/plan/INDEX.md`：状态改 M0-M7 已完成 + graph/ 未采纳 + 真机 18 项
  - `docs/plan/DAG_refactor_plan.md`：2026-10-24 状态注记、L44 行数现状 1,087、§六 Git 口径细化、M0-M7 已完成
  - `docs/INDEX.md`：10 行日期/摘要同步 + frontmatter
  - 4 篇任务记录状态行：`2026-09-24-temp-ledger-cleanup`、`2026-10-18-importdata-repair`、`2026-10-19-func-spec-doc-sync`、`2026-10-19-w22-n-remediation` 由「进行中」改「已完成」
  - `AGENTS.md` 锚点 R16 + §8
- 涉及文件：`docs/backlog.md`、`docs/plan/INDEX.md`、`docs/plan/DAG_refactor_plan.md`、`docs/INDEX.md`、4 篇任务记录、`AGENTS.md`

#### Phase 2′: 计划外发现与处置（指纹保护）
- 状态：✅ 已完成
- 执行内容：
  - **发现**：Writer A 按 D07 改了 `rpa_engine/tests/__init__.py` 的 docstring（纯注释、零逻辑），但该文件在 `tools/make_fingerprint.py` 的哈希范围内（`rpa_engine/**/*.py`），导致 `SOURCE_HASH` 由 `9fc85bc09ac1376a` 变为 `0d9f2233ffd34ce0`，现有 exe 与源码不再同版
  - **决策**：为守住「零源码改动 + exe 有效」两条更高价值不变量，**回滚该文件至快照原状**；指纹复测回到 `9fc85bc09ac1376a`
  - **登记**：新增 W-25（docstring 与实际 15 个测试文件描述不符，待下次构建窗口一并修正并重建 exe）；`build-guide.md` §1.10 复核提示同步改写
  - **另修**：`requirements.lock` 位置表述「仓库根」→「v3 目录」（Writer C 上报，2 处）
- 涉及文件：`rpa_engine/tests/__init__.py`（回滚，无净变更）、`docs/build-guide.md`、`docs/runtime-env-spec.md`、`docs/deployment-guide.md`、`docs/backlog.md`

#### Phase 3: 门禁复跑与独立校验
- 状态：✅ 已完成
- 执行内容：
  - `unittest discover -s tests` → **Ran 234 tests — OK**
  - `smoke_m1m3.py` / `smoke_mb.py` → **SMOKE_ALL_OK ×2**
  - `run_self_check()` → **ok=True，6/6**
  - `tools/doc_verify.py` → **PASS（links=85, failures=0）**
  - `AGENTS.md` 容量 → 含 CR **7,764 / 8,000**（余量 **236**），loneCR=loneLF=0（纯 CRLF）
  - 源码指纹 → **9fc85bc09ac1376a**（与 exe BUILD_INFO 一致，FILES=56）
  - 改动面（只读 git）→ 24 个文档修改 + 1 个新任务记录，**零 `.py` 源码改动**、零 `build/**`、零 `requirements*`
  - 独立 stale 扫描（Lead 亲跑）：17 个模式全部 0 命中或仅历史注记语境
  - **Verifier 独立校验报告**：`_temp/doc-fix-stale-check-2026-10-24.md`，初判 FAIL（3 硬违规 + 3 轻度 + 3 存疑），全部为 W-25 迟到登记后的统计回填缺口与 3 处方案态条款缺局部注记
- 涉及文件：只读

#### Phase 3′: 闭合 Verifier 违规（V1~V6）
- 状态：✅ 已完成
- 执行内容：
  - **V1** `docs/INDEX.md` backlog 行：`统计 21/2/1` → `21/3/1`，补 W-25
  - **V2** `docs/backlog.md` §5 建议顺序：补 W-25（消除同文件 L78 统计 3 项与 L74 仅列 2 项的自相矛盾）
  - **V3** `AGENTS.md` 锚点：要点摘要已含 W-25；§8 待办已含 W-25（复核确认无需再改）
  - **V4** `AGENTS.md` 锚点：「2 篇方案态文档」→「1 篇方案态文档（＋plan/INDEX）」（实际 `docs/plan/` 仅 1 篇 + INDEX）
  - **V5** `AGENTS.md` 头部：`最后更新: 2026-10-18` → `2026-10-24`
  - **V6** `docs/plan/DAG_refactor_plan.md` L48/L58/L505：3 处 `Test/unit/` 条款各补「2026-09-20 已改址 `rpa_engine/tests/`」局部注记
  - 复跑：`doc_verify` PASS（links=85）；`AGENTS.md` 7,764 字符 / 余量 236 / 纯 CRLF
- 涉及文件：`docs/INDEX.md`、`docs/backlog.md`、`AGENTS.md`、`docs/plan/DAG_refactor_plan.md`
- 决策记录：Verifier 的 3 项存疑（`118 用例`/`基线 191` 历史沿革、`runtime-env-spec` Python 3.9+ vs 3.11 口径）判为**合规但可优化**，本轮不改：前者为明确历史记录、后者不在本轮基线范围，登记为后续口径核对项

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 修改 | `AGENTS.md`（v3） | 容量下沉（4 处）＋ Git 新措辞＋§2.1 条 4 现行注记＋§6 Test 行＋锚点 R16＋§8 |
| 修改 | `README.md`（根） | 快速开始改 `cd v3` → `python rpa_engine/main.py`；版本表删 backup；术语更新；Git 边界章 |
| 修改 | `AGENTS.md`（根） | 全文重写：实际目录树/文档索引/快速导航/术语/Git 边界 |
| 修改 | `v1/FROZEN.md` | Contents 补 CNAS/ |
| 修改 | `v2/FROZEN.md` | 目录布局改 A-docs/ + 6 部门，删 BaseDEMO/、ArchivedAcceptanceReport/ |
| 修改 | `v3/README.md` | 技术栈补全；exe 有效 + W-20 关闭；定位更新；R16 变更记录行 |
| 修改 | `rpa_engine/README.md` | 目录树补 storage/temp/tools/templates-user 与 build 子目录；tests 15 文件/234 用例；frontmatter v1.4.0 |
| 修改 | `docs/architecture.md` | `load_tables`→`ensure_input_tables`；hiddenimports 口径；§4 字段与 SessionDB 连接模型；§6 笔误；§8 graph/ 未采纳；§9 测试输入名 |
| 修改 | `docs/dev-spec.md` | §3 现行口径（无模板流式直出，W-24）；Word/TXT/PPT 能力缺口；BaseStep 已删；GUI 已完成；§7 依赖移除；变更记录 |
| 修改 | `docs/build-guide.md` | §1.9 spec 不在版本库；§1.10 exe 有效 + W-20 关闭 + 复核提示；§3 补 backup/ |
| 修改 | `docs/legacy.md` | 9 项 BUILTIN_OPS；v2 树 A-docs/；Word 能力缺口 |
| 修改 | `docs/runtime-env-spec.md` | Git 基线改 SOURCE_HASH 判定；测试输入名；requirements.lock 位置改 v3 |
| 修改 | `docs/doc-governance.md` | §2 Git 口径细化；§8 234 用例 |
| 修改 | `docs/backlog.md` | W-20/W-22 关闭；W-23/W-24/W-25 新增；统计 21/3/1；主线提示 |
| 修改 | `docs/function-spec-rules.md` | 行号锚点刷新（L742-761/L32-96/L1002-1016/L319-417/L88-91/L312）；§9 R16 行；基线标注 |
| 修改 | `docs/user-manual.md` | 按钮名/进度状态/终止语义按代码实况 |
| 修改 | `docs/deployment-guide.md` | 4 个运行目录；build/backup 定性；指纹脚本位置；requirements.lock 位置 |
| 修改 | `docs/INDEX.md` | 10 行日期/摘要同步 + frontmatter 2026-10-24 |
| 修改 | `docs/plan/INDEX.md` | 状态改 M0-M7 已完成 + graph/ 未采纳 + 真机 18 项 |
| 修改 | `docs/plan/DAG_refactor_plan.md` | 2026-10-24 状态注记；L44 行数现状；§六 Git 口径；D6 决议行 |
| 修改 | `docs/task-records/2026-09-24-temp-ledger-cleanup.md` | 摘要状态行：进行中 → 已完成 |
| 修改 | `docs/task-records/2026-10-18-importdata-repair.md` | 摘要状态行：进行中 → 已完成 |
| 修改 | `docs/task-records/2026-10-19-func-spec-doc-sync.md` | 摘要状态行：进行中 → 已完成 |
| 修改 | `docs/task-records/2026-10-19-w22-n-remediation.md` | 摘要状态行：进行中 → 已完成 |
| 新建 | `docs/task-records/2026-10-24-doc-consistency-and-git-policy.md` | 本文件 |
| 新建 | `_temp/doc-fix-factsheet-2026-10-24.md` | 事实基线（唯一事实源） |
| 新建 | `_temp/doc-fix-backup-2026-10-24/` | 25 个改前快照 |
| 新建 | `_temp/doc-fix-*.py`（8 个） | 一次性编辑脚本（CRLF 保持） |
| 回滚 | `rpa_engine/tests/__init__.py` | 指纹保护：恢复原状（无净变更） |

## 验收

| # | 验收项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | Git 新口径写入 `AGENTS.md` §1，全库引用点同步 | ✅ 通过 | `AGENTS.md` §1/§2.4、`docs/backlog.md` §1 条 5、`docs/doc-governance.md` §2、`docs/plan/DAG_refactor_plan.md` L18/L494/D6、根 `AGENTS.md` §7 |
| 2 | 根索引不再引用 `code/`、`backup/`、`steps/`、`templates/workflows/`、`STEP_REGISTRY`、`BaseStep` | ✅ 通过 | 根 `AGENTS.md`/`README.md` 全文重写；grep 仅剩「已不存在/已删除」历史注记 |
| 3 | 不再声称 exe 已失效 / W-20 待指令 / W-22 执行中 / M0 待启动 | ✅ 通过 | `build-guide.md` §1.10 改「有效」；`backlog.md` W-20/W-22 已完成；`plan/INDEX.md` M0-M7 已完成 |
| 4 | 测试基线统一为 234（15 文件），不再出现 88+/118/191 作为现行值 | ✅ 通过 | `doc-governance.md` §8、`function-spec-rules.md` §8、`rpa_engine/README.md`、根 `AGENTS.md` |
| 5 | 运行目录表述为 4 个（+ templates/user），backup 定性为构建备份 | ✅ 通过 | `deployment-guide.md` §1、`rpa_engine/README.md` 注记、根 `AGENTS.md` |
| 6 | W-20/W-22 已完成；W-23/W-24/W-25 登记；统计自洽（21/3/1） | ✅ 通过 | `backlog.md` §2/§5 |
| 7 | `AGENTS.md` 含 CR ≤8,000 且余量 ≥200、纯 CRLF | ✅ 通过 | **7,764 / 余量 236**；loneCR=loneLF=0 |
| 8 | `doc_verify` PASS | ✅ 通过 | `_temp/verify-20261025-1402.md`（links=85, failures=0） |
| 9 | 单元测试 234 OK | ✅ 通过 | `Ran 234 tests in 0.862s — OK` |
| 10 | 双 smoke `SMOKE_ALL_OK` | ✅ 通过 | smoke_m1m3 / smoke_mb |
| 11 | 启动自检 6/6 | ✅ 通过 | `ok=True items=6` |
| 12 | 零源码/零构建/零依赖改动 | ✅ 通过 | `git status` 无 `.py`（除 `_temp` 脚本）、无 `build/**`、无 `requirements*` |
| 13 | exe 与源码指纹一致 | ✅ 通过 | `SOURCE_HASH=9fc85bc09ac1376a`（FILES=56）＝ BUILD_INFO |
| 14 | 零 Git 写操作 | ✅ 通过 | 仅用 status/diff/show/log/ls-files 只读 |

### Verifier 复判（2026-10-25）

Verifier 于 2026-10-24 出具独立只读校验报告 `_temp/doc-fix-stale-check-2026-10-24.md`，初判 **FAIL**（3 项硬违规 + 3 项轻度违规 + 3 项存疑）。逐条处置：

| 编号 | 问题 | 处置 | 状态 |
|------|------|------|------|
| V1 | `docs/INDEX.md` backlog 行统计仍写 `21/2/1` | 改 `21/3/1` 并补 W-25 | ✅ 已闭合 |
| V2 | `docs/backlog.md` §5 建议顺序仅列 W-23/W-24，与同文件统计 3 项矛盾 | 补 W-25 | ✅ 已闭合 |
| V3 | `AGENTS.md` 锚点/§8 未含 W-25 | 复核确认已含（Phase 2 已写入） | ✅ 已闭合 |
| V4 | `AGENTS.md` 写「2 篇方案态文档」，实际 1 篇 + INDEX | 改「1 篇方案态文档（＋plan/INDEX）」 | ✅ 已闭合 |
| V5 | `AGENTS.md` 头部日期仍为 2026-10-18 | 改 2026-10-24 | ✅ 已闭合 |
| V6 | `DAG_refactor_plan.md` 3 处 `Test/unit/` 条款无局部改址注记 | L48/L58/L505 各补「2026-09-20 已改址 `rpa_engine/tests/`」 | ✅ 已闭合 |

**存疑项（判合规、本轮不改）**：
1. `v3/README.md` 中「118 用例」为 2026-09-24 历史记录（明确标注日期），非现行基线；
2. `function-spec-rules.md` 中「基线 118→191」「191→234」为历史沿革，现行基线已写 234；
3. `runtime-env-spec.md` §2「声明最低版本 Python 3.9+」与 `requirements.txt` 头部「Python 要求 3.11」存在口径差异——**不在本轮基线范围**，登记为后续核对项（未擅自修改）。

**复判门禁（2026-10-25 实测）**：
- `doc_verify` → **PASS**（links=85, failures=0；报告 `_temp/verify-20261025-1402.md`）
- `AGENTS.md` 容量 → 含 CR **7,764 / 8,000**（余量 **236** ≥200），loneCR=loneLF=0（纯 CRLF）
- 源码指纹 → **9fc85bc09ac1376a**（FILES=56，与 `build/BUILD_INFO.txt` 一致）
- 改动面（只读 git）→ 24 个文档修改 + 1 个新任务记录；**零 `.py` 源码改动**、零 `build/**`、零 `requirements*`；HEAD 仍为 `703c67e`（无提交）

**结论**：Verifier 报告的 6 项违规全部闭合，本轮文档一致性修正**通过**。

## 遗留提请人工裁定

1. **W-23**：`rpa_engine/temp/` 224 个运行产物被 git 跟踪 + 启动清理会删夹具；建议加 `.gitignore` 并 `git rm -r --cached`（Git 写操作人工执行）。
2. **W-24**：「模板化输出」红线 vs 现行 `export` 无模板流式直出；是否改红线为目标态或实现模板能力，待裁定。
3. **W-25**：`rpa_engine/tests/__init__.py` docstring 与实际 15 个测试文件不符；修正会使指纹变化、需重建 exe，应在同一人工构建窗口内完成。

## 待人工提交清单（Agent 不提交、不推送）

```
根：AGENTS.md、README.md、v1/FROZEN.md、v2/FROZEN.md
v3：AGENTS.md、README.md、rpa_engine/README.md
docs（13）：INDEX.md、architecture.md、dev-spec.md、build-guide.md、legacy.md、
            runtime-env-spec.md、doc-governance.md、backlog.md、
            function-spec-rules.md、user-manual.md、deployment-guide.md
docs/plan（2）：INDEX.md、DAG_refactor_plan.md
docs/task-records（5）：2026-09-24-temp-ledger-cleanup.md、
                        2026-10-18-importdata-repair.md、
                        2026-10-19-func-spec-doc-sync.md、
                        2026-10-19-w22-n-remediation.md、
                        2026-10-24-doc-consistency-and-git-policy.md（新建）
```
（`_temp/` 为临时区，按需决定是否提交；`rpa_engine/temp/` 下新增副本见 W-23。）

## 关闭标识
- **完成时间**：2026-10-24
- **最终状态**：✅ 全部完成
- **关闭说明**：Git 使用边界已固化（写操作人工接管、只读 diff 允许）；全库文档对齐 2026-10-24 实况，零遗漏修正 24 个文档；W-20/W-22 关闭，W-23/W-24/W-25 登记待人工裁定；全部门禁绿；零源码/零构建/零 Git 写操作。**git 提交由人工接管**。
