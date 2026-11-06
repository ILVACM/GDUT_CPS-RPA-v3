# R16 文档一致性修正 · 独立只读校验报告（Verifier）

> 校验人：Verifier（独立于 Writer A/B/C）
> 校验时间：2026-10-24 16:47～17:10（Asia/Shanghai）
> 事实基线：`_temp/doc-fix-factsheet-2026-10-24.md`
> 任务记录：`docs/task-records/2026-10-24-doc-consistency-and-git-policy.md`
> 纪律声明：本报告为唯一写入文件；全程未修改任何受管辖文件、未执行任何 git 写操作。
> 扫描范围：根 `AGENTS.md`、根 `README.md`、`v3/AGENTS.md`、`v3/README.md`、`v3/rpa_engine/README.md`、`v3/docs/*.md`（12 篇 + INDEX）、`v3/docs/plan/*.md`（2 篇），共 **20 个文件**。
> 排除范围（按指令）：`docs/task-records/**`、`docs/analysis/**`、`_temp/**`。

---

## 1. 结论

**FAIL — 3 项硬违规 + 3 项轻度违规 + 3 项存疑。**

- **核心目标已达成**：A 表 20 个 stale 模式中 17 个完全干净或仅存合规历史注记；B 表 21 项事实中 18 项与基线/实测完全一致；C 项 doc_verify PASS；D 项零源码/零构建/零依赖改动；E 项四道门禁全绿。
- **剩余问题高度集中**：`W-25` 于 16:47 迟到登记后，三处跨文件统计/待办摘要未回填（`docs/INDEX.md`、`docs/backlog.md`、`v3/AGENTS.md`），另加 1 处「2 篇方案态文档」表述、1 处 AGENTS 头部日期滞后、3 处方案态 `Test/unit` 条款缺局部作废注记。
- **修复量小**：全部为文本替换，预计 8 行内可闭合，不涉及事实重算或代码。

> 判定口径：A 表「违规」= 仍作**现行事实陈述**且与 2026-10-24 实况/基线冲突；带明确日期或「已删除/已废弃/未采纳/历史状态」注记者判「合规（历史注记）」。

---

## 2. A 表：Stale 字符串扫描逐模式结果

扫描方式：PowerShell `Select-String -Encoding UTF8`（`-SimpleMatch`，正则项单独标注），文件清单见报告头。共 20 个模式。

| # | 模式 | 命中数 | 命中位置 | 判定 |
|---|------|-------|---------|------|
| 1 | `templates/workflows` | 1 | 根 `AGENTS.md:72`（"原 `templates/workflows/`（7 个测试模板）已随 v3 预设架构归档清理"） | ✅ 合规（已归档注记） |
| 2 | `steps/` | 15 | 根 `AGENTS.md:71`；`v3/AGENTS.md:32`；`architecture.md:20/220/291/406/407`；`backlog.md:51`；`dev-spec.md:358/360/556`；`legacy.md:100`；`runtime-env-spec.md:36`；`v3/README.md:30/36`；`rpa_engine/README.md:135` | ✅ 合规（全部为「已删除/已废弃/原…」历史注记） |
| 3 | `backup/` | 20 | 根 `AGENTS.md:8/66/73/110`；根 `README.md:35`；`architecture.md:220/405`；`build-guide.md:10/20/60/65/80/82/170`；`deployment-guide.md:20/25/27/45`；`docs/INDEX.md:32`；`plan/DAG_refactor_plan.md:18/20/494/589`；`rpa_engine/README.md:103/159` | ✅ 合规（根 `backup/` 均为「不存在」注记；其余均为 `build/backup/` 或 `_temp/BackUp/` 历史语境，0 处把根 `backup/` 当现行路径） |
| 4 | `code/` | 4 | 根 `AGENTS.md:8/73`；根 `README.md:22/23` | ✅ 合规（均为「不存在/已失效」注记；大小写敏感复核无其他命中） |
| 5 | `STEP_REGISTRY` / `BaseStep` / `register_step` | 6 | `architecture.md:220`（三词同段）；`dev-spec.md:10/203/211/558`；`docs/INDEX.md:23` | ✅ 合规（均含「已删除/原…机制已删除」注记） |
| 6 | `AcceptanceReport` / `ArchivedAcceptanceReport` | 2 | 根 `AGENTS.md:38`（"（原 AcceptanceReport/）"）；`legacy.md:22`（HTML 注释"AcceptanceReport/ → A-docs/"） | ✅ 合规（历史更名注记）；`ArchivedAcceptanceReport` **0 命中** |
| 7 | `Test/unit` | 8 | `plan/DAG_refactor_plan.md:18/48/58/448/452/457/505/521` | ⚠️ **部分违规**：L48/L58/L505 共 3 处仍作方案条款陈述、无局部作废注记；L18/L448/L452/L457/L521 有「备选作废/改址/已作废」注记（合规）。详见 §5-4 |
| 8 | `gui/graph` | 10 | `architecture.md:310`（"五层包方案未采纳"）；`backlog.md:36`（同）；`plan/DAG_refactor_plan.md:24/45/90-94/99/206/494`；`v3/README.md:49`；`rpa_engine/README.md:34` | ✅ 合规（均已标注「未采纳」或属方案态设计原文；0 处把 `gui/graph/` 当现行目录） |
| 9 | `88+ 用例` | 0 | — | ✅ 合规 |
| 10 | `118 用例` | 2 | `v3/README.md:45`（2026-09-24 完善度修复轮）、`:47`（2026-09-24 功能函数规约固化） | ⚠️ 合规（历史日期注记）但**与字面 0 命中期望不符**，建议加"当时"字样（见 §6-1） |
| 11 | `基线 191` | 2 | `function-spec-rules.md:10`（"§8 基线 118→191"）、`:308`（"§8 基线 191→234"） | ✅ 合规（历史沿革记录，现行基线已写 234） |
| 12 | `7 个步骤类型` | 1 | `legacy.md:22`（HTML 注释"§3「7 个步骤类型」→「9 项用户操作 BUILTIN_OPS」"） | ✅ 合规（已废弃注记） |
| 13 | `7 种预设` | 1 | `architecture.md:280`（"v3 的 7 种预设步骤类型…已全部废弃"） | ✅ 合规（已废弃语境） |
| 14 | `尚未实现`（GUI 语境） | 2 | `dev-spec.md:558`（变更记录引用旧表述）；`plan/DAG_refactor_plan.md:10`（方案态声明） | ✅ 合规（GUI 现状均已改「四阶段已完成（2026-09-20 M0-M7 闭环）」） |
| 15 | `exe 待重建` | 1 | `v3/README.md:21`（"（2026-10-24 更新：原表述为"exe 待重建（W-20）"）"） | ✅ 合规（历史注记） |
| 16 | `已失效` | 9 | 根 `README.md:23`；`backlog.md:41/52`；`build-guide.md:129`（HTML 注释）；`doc-governance.md:18/169`；`function-spec-rules.md:120`；`v3/README.md:43/49` | ✅ 合规（均为历史时点注记；build-guide 现行状态明写「**有效**」） |
| 17 | `M0 启动待人工指令` / `M0 门控解除.*启动待` | 1 / 0 | `plan/DAG_refactor_plan.md:21`（已加"（**历史状态**：M0-M7 已于 2026-09-20 全阶段闭环）"） | ✅ 合规（历史注记）；正则项 0 命中 |
| 18 | `五个数据目录` | 0 | — | ✅ 合规（`build-guide.md:170`、`deployment-guide.md:27` 的「五个目录」均指 `build/` 下 workspace/logs/storage/temp/backup，属正确语境） |
| 19 | `任务状态.*进行中` | 2 | `v3/AGENTS.md:182`（当前任务锚点 R16，确实进行中）；`backlog.md:42`（W-09 历史说明） | ✅ 合规（非历史任务记录的伪造状态） |
| 20 | `仓库根.*requirements\.lock` / `88+` | 0 / 0 | — | ✅ 合规（`runtime-env-spec.md:35` 已改 `v3/requirements.lock` 并注明"非仓库根"） |

**A 表小结**：20 模式中 **16 完全合规**、**3 合规但字面偏离**（#7 部分、#10、#11）、**1 项存在违规**（#7 `Test/unit` 3 处）。

---

## 3. B 表：事实交叉核对（21 项，逐项实测）

| # | 核对项 | 基线值 | 实测值 | 结果 |
|---|-------|--------|--------|------|
| 1 | `BUILTIN_OPS` 项数 | 9 项 | **9 项**（filter/dedup/mapping_match/aggregate/export/merge_tables/copy_table/rename_columns/convert_dtype） | ✅ 一致 |
| 2 | 每项字段数 | 8 字段 | **8 字段**（func/description/output/param_keys/params_schema/extra_input_min/overwritable/deprecated），9 项全一致 | ✅ 一致 |
| 3 | 单元测试规模 | 234 用例 / 15 文件 | **234 用例 / 15 文件**；逐文件 5/7/8/15/5/17/38/67/3/20/16/5/16/9/3，与基线清单完全吻合 | ✅ 一致 |
| 4 | 知识文档数 | 13 篇（不含 INDEX） | **13 篇**（docs 顶层 12 + `analysis/DAG_visualization_analysis.md`）；INDEX 列 13 行 | ✅ 一致 |
| 5 | 任务记录数 | 48 篇 + TEMPLATE | 基线为修正前：**tracked 48 篇 + TEMPLATE**；现文件系统 **49 篇 + TEMPLATE**（+本轮新增 2026-10-24 记录，未跟踪） | ✅ 预期增量（全库无「48/49 篇」硬断言，0 处需改） |
| 6 | 运行数据目录 | 4 个 + `templates/user` | `rpa_engine/workspace`、`logs`、`storage`、`temp` **均存在**；`templates/user/` 存在；`v3/` 根下无这 4 个目录 | ✅ 一致 |
| 7 | `build/backup/` | 存在且 4 个历史 exe | **存在**，4 个：`20260924_104118`、`20261018_210145`、`20261019_025839`、`20261019_035709`（2026-09-24～2026-10-19） | ✅ 一致 |
| 8 | exe 构建时间 | 2026-10-19 03:57:09 | BUILD_INFO `2026/10/19 周一 3:57:09.15`；文件 mtime `2026/10/19 3:57:08` | ✅ 一致 |
| 9 | `SOURCE_HASH` | `9fc85bc09ac1376a` | BUILD_INFO = `9fc85bc09ac1376a` | ✅ 一致 |
| 10 | `TESTS_SKIPPED` | 0 | **0** | ✅ 一致 |
| 11 | exe 大小 | 73,792,711 字节 | **73,792,711** | ✅ 一致 |
| 12 | 当前源码指纹 | `9fc85bc09ac1376a`（FILES=56） | 实跑 `python tools/make_fingerprint.py` → `SOURCE_HASH=9fc85bc09ac1376a`、`FILES=56`、`GIT_REV=703c67ef…` | ✅ 一致（exe 与源码同版、有效） |
| 13 | Git 分支 | `master` | `* master` | ✅ 一致 |
| 14 | HEAD | `703c67e`（2026-10-24 14:51） | `703c67e 2026-10-24 14:51 update` | ✅ 一致 |
| 15 | Git remote | gitee `ILVACM/cps-gpes_rpa-20250312` | `origin https://gitee.com/ILVACM/cps-gpes_rpa-20250312.git`（fetch/push） | ✅ 一致 |
| 16 | W-20 / W-22 | 已完成 | backlog L52 W-20 ✅（2026-10-24 核验关闭）、L55 W-22 ✅（R15 结清） | ✅ 一致 |
| 17 | W-23/W-24/W-25 + 统计 | 待指令 3；已完成 21；撤销 1（21/3/1） | backlog 主表 **W-23/W-24/W-25 均 ⏸️ 待指令**、L78 统计 **21/3/1** ✅；但 `docs/INDEX.md:29` 仍写 **21/2/1**、`backlog.md:74` 仅列 W-23/W-24、`v3/AGENTS.md:187/196` 仅列 W-23/W-24 | ⚠️ **3 处不一致**（详见 §5） |
| 18 | M0-M7 | 全部完成（2026-09-20） | `backlog.md:74/85`、`dev-spec.md:351/390`、`plan/DAG_refactor_plan.md:24/494`、`plan/INDEX.md:21`、`rpa_engine/README.md:33-34`、`v3/README.md:49`、`v3/AGENTS.md:192` 全部写「已完成 2026-09-20」 | ✅ 一致 |
| 19 | `Test/input/` | 测试输入0~3.xlsx | **4 个**：`测试输入0.xlsx`(10,312) / `1`(10,476) / `2`(10,561) / `3`(10,459) | ✅ 一致 |
| 20 | `rpa_engine/tests/__init__.py` | 原 2 文件描述，未改 | 内容仍为「仅承载 DAG 重构移植清单：test_graph_edges.py / test_translation.py」；`git status` 该文件**无任何改动** | ✅ 一致（已回滚） |
| 21 | 根 `AGENTS.md`/`README.md` 路径引用 | 不再引用不存在路径 | 树中全部路径实测存在（v1/v2/v3 全树、engine/ops/gui/tests/tools/templates/build/Test/_temp 等）；两文件相对链接 **11 + 7 = 18 条，坏链 0** | ✅ 一致 |

**B 表小结**：21 项中 **18 项完全一致**、**1 项预期增量**（#5）、**1 项内部不一致**（#17，3 处文本）、**1 项一致但需注意**（#2 字段数）。

---

## 4. C / D / E 结果

### C. 结构检查

| 检查项 | 结果 |
|-------|------|
| `python tools/doc_verify.py` | ✅ **PASS**（`links=85, failures=0`；报告 `_temp/verify-20261024-1709.md`）。注：基线为 `links=86`，差 1 来自 `v3/AGENTS.md` §7.3 压缩删除 1 条 `anchor-mechanism.md` 重复链接（44→43），非断链 |
| 修改文档 frontmatter `last-updated` = `docs/INDEX.md` 日期列 | ✅ **13/13 全部一致**（agent-execution-mode 09-13、architecture 10-24、dev-spec 10-24、build-guide 10-24、legacy 10-24、runtime-env-spec 10-24、doc-governance 10-24、anchor-mechanism 09-06、backlog 10-24、analysis 09-18、user-manual 10-24、deployment-guide 10-24、function-spec-rules 10-24） |
| `v3/AGENTS.md` 容量（Python 脚本实测，非 `wc -m`） | ✅ 含 CR **7,649 / 8,000**（余量 **351** ≥200）；LF 归一化 7,453；196 行；`loneCR=0, loneLF=0`（纯 CRLF） |
| 根 `AGENTS.md` 行尾 | ✅ 6,084 字符，CRLF=150，`loneCR=0, loneLF=0` |
| `docs/plan/INDEX.md` 状态 vs `DAG_refactor_plan.md` 头部注记 | ✅ 一致：均写「M0-M7 已完成 2026-09-20；实际实现 `node_graph.py` 单文件；`graph/` 包方案未采纳；余真机回归 18 项待人工」 |
| 相对链接可达 | ✅ doc_verify 覆盖 + 独立复算（根 AGENTS 11/0、根 README 7/0、v3/AGENTS 43/0） |
| 文件编码/行尾 | ✅ 全部 UTF-8；根 `AGENTS.md`、`v3/AGENTS.md`、根 `README.md`、`legacy.md`、`agent-execution-mode.md` 为 CRLF，其余 docs 为 LF（与 git `core.autocrlf=true` 及历史一致，doc_verify 仅强制 `v3/AGENTS.md` CRLF，已满足） |

### D. 改动面检查（只读 git）

```text
git status --porcelain  →  24 个 M + 1 个新增任务记录 + _temp/ 产物（详见下）
git diff --stat         →  24 files changed, 335 insertions(+), 223 deletions(-)
```

- ✅ **无 `v3/rpa_engine/**/*.py` 改动**：`git status -- v3/rpa_engine` 仅 `README.md` 一个 M；`tests/__init__.py` 无改动（已回滚，指纹复测证明）。
- ✅ **无 `v3/build/**`、`v3/requirements*` 改动**：`git status -- v3/build v3/requirements.txt v3/requirements.lock` 输出为空。
- ✅ **索引干净**：`git diff --cached --name-only` 为空（无暂存，无 git 写操作痕迹）。
- ✅ 分支 `master`，HEAD `703c67e`，remote gitee 正常。

**实际改动文件清单（24 个 M）**：

| 组 | 文件 |
|----|------|
| 根索引 | `AGENTS.md`、`README.md` |
| 冻结声明 | `v1/FROZEN.md`、`v2/FROZEN.md` |
| v3 入口 | `v3/AGENTS.md`、`v3/README.md`、`v3/rpa_engine/README.md` |
| 知识层 | `v3/docs/INDEX.md`、`architecture.md`、`backlog.md`、`build-guide.md`、`deployment-guide.md`、`dev-spec.md`、`doc-governance.md`、`function-spec-rules.md`、`legacy.md`、`runtime-env-spec.md`、`user-manual.md` |
| 方案态层 | `v3/docs/plan/DAG_refactor_plan.md`、`v3/docs/plan/INDEX.md` |
| 任务记录（仅摘要状态行） | `2026-09-24-temp-ledger-cleanup.md`、`2026-10-18-importdata-repair.md`、`2026-10-19-func-spec-doc-sync.md`、`2026-10-19-w22-n-remediation.md` |
| 新增 | `v3/docs/task-records/2026-10-24-doc-consistency-and-git-policy.md`（未跟踪） |

**未跟踪产物（非 Writer 交付）**：`v3/_temp/doc-fix-*.py`（9 个修正脚本）、`_temp/doc-fix-backup-2026-10-24/`（25 份快照）、`_temp/doc-fix-factsheet-2026-10-24.md`、`_temp/verify-20261024-*.md`（6 份）。

### E. 门禁复跑

| 门禁 | 命令 | 结果 |
|------|------|------|
| 单元测试 | `python -m unittest discover -s tests`（`QT_QPA_PLATFORM=offscreen`） | ✅ **Ran 234 tests … OK**（0.93s，exit 0） |
| 冒烟 M1-M3 | `python tools/smoke/smoke_m1m3.py` | ✅ **SMOKE_ALL_OK**（exit 0） |
| 冒烟 MB | `python tools/smoke/smoke_mb.py` | ✅ **SMOKE_ALL_OK**（exit 0） |
| 文档体检 | `python tools/doc_verify.py` | ✅ **PASS (links=85, failures=0)**（exit 0） |

---

## 5. 违规清单（文件:行 + 现文 + 应改为）

### 硬违规（现行事实错误，建议本轮闭合）

**V1｜`v3/docs/INDEX.md:29`（backlog 行摘要）**
- 现文：`…2026-10-24：W-20/W-22 关闭、W-23/W-24 新增，统计 21/2/1`
- 应改为：`…2026-10-24：W-20/W-22 关闭、W-23/W-24/W-25 新增，统计 21/3/1`
- 依据：`docs/backlog.md:78` 统计表为「⏸️ 待指令 **3** ｜ W-23、W-24、W-25」；W-25 于 16:47 登记，INDEX（16:45 写）未回填。

**V2｜`v3/docs/backlog.md:74`（§5 建议顺序）**
- 现文：`当前仅剩：**W-23（temp 目录入库，人工执行 git 操作）**、**W-24（模板化输出口径人工裁定）**；真机批与构建项仍为人工责任（受控例外）。`
- 应改为：`当前仅剩：**W-23（temp 目录入库，人工执行 git 操作）**、**W-24（模板化输出口径人工裁定）**、**W-25（tests docstring 修正随构建窗口）**；真机批与构建项仍为人工责任（受控例外）。`
- 依据：同文件 L78 统计 3 项、L85 主线提示已含 W-25 → **文件内自相矛盾**。

**V3｜`v3/AGENTS.md:187` 与 `:196`（当前任务锚点）**
- 现文 L187：`…W-20/W-22 关闭；W-23/W-24 登记；零源码/零构建/零 Git 写`
- 现文 L196：`**待办**：W-23（temp 目录入库）、W-24（模板化输出口径）待人工裁定；真机批与构建项仍人工；队列见 docs/backlog.md。`
- 应改为 L187：`…W-20/W-22 关闭；W-23/W-24/W-25 登记；…`；L196：`**待办**：W-23（temp 目录入库）、W-24（模板化输出口径）、W-25（tests docstring 随构建窗口）待人工裁定；…`
- 依据：backlog 21/3/1 为唯一活载体（`docs/INDEX.md:29` 自述「W 清单的唯一受管辖活载体」）。

### 轻度违规 / 建议项

**V4｜`v3/AGENTS.md:187`**
- 现文：`…13 篇知识文档与 2 篇方案态文档全量对齐…`
- 应改为：`…13 篇知识文档与 1 篇方案态文档（＋plan/INDEX）全量对齐…`
- 依据：基线 §5「方案态文档 **1 篇**（`DAG_refactor_plan.md`）＋ INDEX」；`docs/plan/` 实际仅 1 篇方案文档 + INDEX。

**V5｜`v3/AGENTS.md:3`（头部状态行）**
- 现文：`> 状态: 活跃 | 最后更新: 2026-10-18`
- 应改为：`> 状态: 活跃 | 最后更新: 2026-10-24`
- 依据：本轮实际修改了 `v3/AGENTS.md`（Git 措辞、§2.6/§4.3/§5.3/§7.3 容量下沉、锚点 R16），文件 mtime 2026-10-24 16:33；头部日期为全库唯一仍停在 10-18 的「最后更新」。

**V6｜`v3/docs/plan/DAG_refactor_plan.md:48 / 58 / 505`（`Test/unit` 条款）**
- 现文 L48：`- 测试交付物（Test/unit/ 4 文件 + README，unittest 风格）`
- 现文 L58：`2. Test/unit/ 布局引擎/边路由/差量单测全绿（人工触发执行，见 §五 5.8）；`
- 现文 L505：`| **M7 收尾** | 删 node_graph.py…；Test/unit/README + AGENTS.md §6 口径同步；…`
- 应改为：三处各追加 `（2026-09-20 已改址 rpa_engine/tests/，见 §5.8 回写注）`
- 依据：A 表期望 `Test/unit` 0 命中或仅历史注记；§5.8 有全局作废注记（L448/L455/L457），但 §1.2 范围、§1.3 成功标准、§六 M7 三处仍作方案条款陈述，易被后续 Agent 误读。
- 风险等级：低（方案态文档，frontmatter 已声明「不参与文档↔代码比对」）。

---

## 6. 未覆盖 / 存疑项

1. **`118 用例`（`v3/README.md:45/47`）**：语境为「2026-09-24 完善度修复轮…回归 118 用例」「本轮零代码改动（118 用例回归全绿）」，属明确历史记录，判合规；但与 A 表字面「0 命中」有偏差。若要求字面清零，可改为「当时 118 用例」。
2. **`基线 191`（`function-spec-rules.md:10/308`）**：语境为「§8 基线 118→191」「191→234」的历史沿革，现行基线已写 234，判合规；同上属字面偏差而非事实错误。
3. **`runtime-env-spec.md:27`**：现文「声明最低版本：Python 3.9+ [src:v3/AGENTS.md 技术栈、requirements.txt]」，但 `requirements.txt` 头部明写「Python 要求：3.11」，`v3/AGENTS.md` 技术栈为 Python 3.11.15。**该条不在本轮基线覆盖范围**，未修改，属潜在文档间口径不一致，建议下轮裁定（是「最低兼容 3.9」还是「要求 3.11」）。
4. **`doc_verify` links=85 vs 基线 86**：差值 1 来自 `v3/AGENTS.md` §7.3 压缩删除 1 条重复的 `anchor-mechanism.md` 链接（44→43），非断链，判合规。
5. **任务记录篇数**：基线 48 篇为修正前口径；本轮新增 `2026-10-24-doc-consistency-and-git-policy.md` 后为 49 篇（tracked 48 + 新增未跟踪 1）。全库无硬编码篇数断言，无需改文。
6. **门禁运行副产物**：本次 E 项实测（以及此前 17:02 的一次运行）在 `v3/rpa_engine/temp/` 下产生未跟踪文件——`input_selection/dup_102~105.xlsx`、`other_51~52.xlsx`、`normalized/0dfa17f3…json` 等。**这是测试/冒烟运行的正常副作用，非 Writer 改动**，但会弄脏工作区，正是 W-23 所述现象（`temp/` 被 git 跟踪 + 启动清理）。建议人工按 W-23 处置时一并清理。
7. **`doc_verify` 自动落盘**：按任务 E 要求运行 `tools/doc_verify.py` 时，脚本自动写入 `_temp/verify-20261024-1649.md` 与 `_temp/verify-20261024-1709.md`（脚本内建行为，非人工编辑），特此披露。
8. **未复核项**：`docs/analysis/**`、`docs/task-records/**`、`_temp/**` 按指令排除，未做 stale 扫描；`v3/docs/task-records/` 仅核对 4 篇摘要状态行已由「进行中」改为「已完成」且与文末关闭标识一致（属任务记录范围，非本次 A 表扫描对象）。
9. **运行方式声明**：本次校验为模式 D（独立只读校验），未派发子 Agent；所有命令均为只读或任务明确要求的门禁复跑。

---

## 7. 复核建议（给 Lead）

1. 优先闭合 **V1/V2/V3** 三处 W-25 统计回填（`docs/INDEX.md:29`、`docs/backlog.md:74`、`v3/AGENTS.md:187/196`），闭合后统计口径统一为 **21/3/1**。
2. 顺手闭合 **V4**（2 篇→1 篇＋INDEX）与 **V5**（AGENTS 头部日期 2026-10-18→2026-10-24）。
3. **V6** 可在本轮或下轮补 3 处 `Test/unit` 局部注记；不阻塞本轮验收。
4. 闭合后重跑 `python tools/doc_verify.py`（应仍 PASS，links=85）即可判定 **PASS**。
5. 提醒：修复后 `v3/AGENTS.md` 字符数会小幅增加（当前 7,649，余量 351，改动约 +40 字符，仍在 8,000 内且余量 ≥200）。

---

*报告结束。本文件为 Verifier 唯一写入产物；未修改任何受管辖文件，未执行 git 写操作。*
