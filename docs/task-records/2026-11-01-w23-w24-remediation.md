# 任务记录：W-23 运行产物移出版本控制 ＋ W-24 模板化输出裁定暂缓

## 摘要
- **任务目标**：执行 W-23（新建 `v3/.gitignore` + `git rm -r --cached` 移出运行产物）；执行 W-24（「模板化输出」红线改为「暂缓」）
- **任务状态**：`已完成（2026-11-01）`
- **开始时间**：2026-11-01
- **最后更新**：2026-11-01
- **要点摘要**：`v3/.gitignore` 忽略 4 个运行目录；250 条运行产物移出索引（工作区保留）；W-24 三处同步「暂缓」；W-23/W-24 关闭；统计 23/1/1；234 tests／双 smoke／自检／doc_verify 全绿；零源码/零构建
- **操作人**：黄泊凯

## 用户输入

> 执行`W-23`，加 .gitignore 并 git rm -r --cached；
> 执行`W-24`，改规矩（标记为暂缓忽略，暂时不用管）

（方案经人工批准：《W-23 运行产物移出版本控制 + W-24 模板化输出裁定暂缓》执行计划）

## Agent 理解与决策

- **W-23**：新建 `v3/.gitignore`（4 条规则：`rpa_engine/temp|storage|workspace|logs/`）；用 `git rm -r --cached` 把已跟踪的 250 条运行产物移出索引，**工作区文件保留**。
- **W-24**：「改规矩」＝把 `AGENTS.md` §2.1 条 4 从「必须模板填充」改为「**模板化输出（暂缓）**」——目标态保留、现行实现不变、不阻塞交付；同步 `dev-spec.md` §3、`architecture.md` §6、`backlog.md`。
- **Git 边界（重要留痕）**：`AGENTS.md` §1 规定「Git 写操作由人工接管，Agent 不执行」。本轮 `git rm --cached` 系**用户在指令中显式指定的单次操作**（原文："加 .gitignore 并 git rm -r --cached"），依指令执行；**红线条文不改**，`git add`/`commit`/`push` 仍归人工。
- **运行方式**：模式 A（单 Agent 直接执行）；文档/治理单一域、改动相互依赖、无并行收益。

## 执行流程

### 流程概览
- 总步骤数：6
- 多 Agent 协作：否

### 步骤记录

#### Step 1: 现状核实
- 状态：✅ 已完成
- 执行内容：核对 HEAD=`585d726`（工作区干净）；`git ls-files v3/rpa_engine/temp`=**249**、`storage/recent_steps.json`=**1**（合计 250）；`v3/.gitignore` 不存在；根 `.gitignore` 138 行无运行目录规则；代码自建目录能力逐处核验（`app.py` L81-84、`page_input_selection.py` L323、`recent_steps.py` L49、`user_template_manager.py` L184）；测试/冒烟不依赖既有夹具（`test_engine_robustness` L263 仅构造路径、`smoke_m1m3` 用 `tempfile.TemporaryDirectory`）
- 涉及文件：只读
- 决策记录：`_temp/`（195 个已跟踪文件）**本次不动**——`docs/` 有 21 处引用其中的证据文件（`DAG-rebuild/plan.md`、`ImportData/plan.md`、`ledger_2026-09-24/*`），移出会破坏可追溯性

#### Step 2: W-23 · 新建 `v3/.gitignore`
- 状态：✅ 已完成
- 执行内容：新建 `v3/.gitignore`，含 4 条规则（`rpa_engine/temp/`、`rpa_engine/storage/`、`rpa_engine/workspace/`、`rpa_engine/logs/`），带 W-23 依据注释与代码 mkdir 位置索引
- 涉及文件：`v3/.gitignore`（新建）
- 决策记录：用 `v3/.gitignore` 而非根文件——规则就近、作用域明确，不污染 v1/v2 共用规则

#### Step 3: W-23 · `git rm --cached` 移出索引
- 状态：✅ 已完成
- 执行内容：
  - `git rm -r --cached -q v3/rpa_engine/temp` → 249 条
  - `git rm --cached -q v3/rpa_engine/storage/recent_steps.json` → 1 条
  - **合计 250 条**进入暂存区（`git diff --cached --numstat` = 250 行）
- 核对结果：
  - `git ls-files v3/rpa_engine/temp` → **0**；`storage` → **0**
  - 工作区 `rpa_engine/temp` 文件数 → 仍 **249**；`storage/recent_steps.json` → 仍存在
  - 忽略规则：5 个路径全部命中 `v3/.gitignore`；`templates/outputs/.gitkeep`、`templates/README.md`、`tests/test_recent_steps.py`、`docs/INDEX.md` **未被误忽略**
  - `git status`：`D`=250（已暂存）、`?? v3/.gitignore`=1
- 涉及文件：Git 索引（**未提交**）
- 决策记录：`--cached` 保证工作区文件原样保留，应用与测试不受影响；**不执行** `git add`/`commit`/`push`

#### Step 4: W-24 · 文档改「暂缓」
- 状态：✅ 已完成
- 执行内容：
  - `AGENTS.md` §2.1 条 4：`**模板化输出**：输出必须"预设模板 + 数据填充"…（现行 export 为无模板流式直出；模板能力待实现，见…W-24）` → `**模板化输出（暂缓）**：目标态为"预设模板 + 数据填充"，严禁代码硬编码样式；现行 export 为无模板流式直出，模板能力**暂缓**（W-24 已裁定，不阻塞交付）`
  - `docs/dev-spec.md` §3 现行口径注：`（2026-10-24）…与现行实现的差异登记 W-24（待人工裁定）` → `（2026-11-01 裁定）…**模板化输出暂缓**（W-24 已裁定关闭，不阻塞交付）`
  - `docs/dev-spec.md` L127 / L460：交叉引用由「待人工裁定」改「已裁定暂缓」
  - `docs/architecture.md` §6 `export` 行：追加「模板化输出**暂缓**，W-24 已裁定」
  - `docs/dev-spec.md` 变更记录：追加 2026-11-01 行
- 涉及文件：`AGENTS.md`、`docs/dev-spec.md`、`docs/architecture.md`

#### Step 5: 台账与索引同步
- 状态：✅ 已完成
- 执行内容：
  - `docs/backlog.md`：W-07 补「已移出版本控制」注记；W-23 → ✅ 已完成（2026-11-01 R17，含 250 条明细）；W-24 → ✅ 已裁定关闭（暂缓，2026-11-01 R17）；建议顺序重写；统计改 **待指令 1 / 已完成 23 / 撤销 1**；主线提示重写；frontmatter 日期与 confidence
  - `AGENTS.md`：§6 `Test/` 行改「运行产物保留不删且不纳入版本控制（`v3/.gitignore`，W-07/W-23）」；锚点 R17；§8 上下文；头部日期 2026-11-01
  - `docs/INDEX.md`：architecture/dev-spec/backlog 三行日期→2026-11-01＋摘要同步；frontmatter
  - `rpa_engine/README.md`：运行目录注记补「不纳入版本控制（`v3/.gitignore`，W-23）」；frontmatter v1.5.0 / 2026-11-01
- 涉及文件：`docs/backlog.md`、`AGENTS.md`、`docs/INDEX.md`、`rpa_engine/README.md`

#### Step 6: 门禁复跑
- 状态：✅ 已完成
- 执行内容：
  - `unittest discover -s tests` → **Ran 234 tests — OK**
  - `smoke_m1m3.py` / `smoke_mb.py` → **SMOKE_ALL_OK ×2**
  - `run_self_check()` → **ok=True，6/6**
  - `tools/doc_verify.py` → **PASS**
  - `AGENTS.md` 容量 → 含 CR **7,689 / 8,000**（余量 **311**），纯 CRLF
  - 源码指纹 → **9fc85bc09ac1376a**（不变，零源码改动）
- 涉及文件：只读

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 新建 | `v3/.gitignore` | 4 条运行目录忽略规则（W-23） |
| 修改 | `v3/AGENTS.md` | §2.1 条 4 改「暂缓」；§6 `Test/` 行；锚点 R17；§8；头部日期 |
| 修改 | `docs/backlog.md` | W-07 注记；W-23/W-24 关闭；建议顺序；统计 23/1/1；主线提示；frontmatter |
| 修改 | `docs/dev-spec.md` | §3 现行口径改「暂缓」；L127/L460 交叉引用；变更记录 2026-11-01 行 |
| 修改 | `docs/architecture.md` | §6 `export` 行标注「暂缓」 |
| 修改 | `docs/INDEX.md` | architecture/dev-spec/backlog 三行日期与摘要；frontmatter |
| 修改 | `rpa_engine/README.md` | 运行目录注记补「不纳入版本控制」；frontmatter v1.5.0 |
| 新建 | `docs/task-records/2026-11-01-w23-w24-remediation.md` | 本文件 |
| Git 索引 | `v3/rpa_engine/temp/`（249）、`storage/recent_steps.json`（1） | `git rm --cached` 移出，**工作区保留**；未提交 |

## 验收

| # | 验收项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | `v3/.gitignore` 存在且 4 条规则生效 | ✅ 通过 | `git check-ignore -v` 5 个路径全部命中 |
| 2 | 250 条运行产物移出索引 | ✅ 通过 | `git ls-files` temp=0 / storage=0；`git diff --cached --numstat`=250 |
| 3 | 工作区文件完整保留 | ✅ 通过 | temp 文件数 249 不变；`storage/recent_steps.json` 仍存在 |
| 4 | 关键文件未被误忽略 | ✅ 通过 | `templates/outputs/.gitkeep`、`templates/README.md`、`tests/test_recent_steps.py`、`docs/INDEX.md` 均仍跟踪 |
| 5 | W-24 三处同步「暂缓」 | ✅ 通过 | `AGENTS.md` 条 4 / `dev-spec.md` §3 / `architecture.md` §6 一致 |
| 6 | backlog 状态与统计自洽 | ✅ 通过 | W-23/W-24 ✅；待指令 1（W-25）/ 已完成 23 / 撤销 1 |
| 7 | `AGENTS.md` 含 CR ≤8,000、余量 ≥200、纯 CRLF | ✅ 通过 | 7,689 / 余量 311；loneCR=loneLF=0 |
| 8 | `doc_verify` PASS | ✅ 通过 | 见 `_temp/verify-*.md` |
| 9 | 单元测试 234 OK | ✅ 通过 | `Ran 234 tests — OK` |
| 10 | 双 smoke `SMOKE_ALL_OK` | ✅ 通过 | smoke_m1m3 / smoke_mb |
| 11 | 启动自检 6/6 | ✅ 通过 | `ok=True items=6` |
| 12 | 零源码/零构建/零依赖改动 | ✅ 通过 | `git status` 无 `.py`、无 `build/**`、无 `requirements*` |
| 13 | 源码指纹不变 | ✅ 通过 | `SOURCE_HASH=9fc85bc09ac1376a`（FILES=56） |

## 遗留提请人工裁定

1. **W-25**：`rpa_engine/tests/__init__.py` docstring 与实际 15 个测试文件不符；修正会使指纹变化、需重建 exe，应在同一人工构建窗口内完成。

## 待人工提交清单（Agent 不提交、不推送）

```
# 已暂存（git rm --cached，250 条删除）
v3/rpa_engine/temp/**（249）
v3/rpa_engine/storage/recent_steps.json（1）

# 未跟踪，需 git add
v3/.gitignore

# 已修改
v3/AGENTS.md
v3/docs/backlog.md
v3/docs/dev-spec.md
v3/docs/architecture.md
v3/docs/INDEX.md
v3/rpa_engine/README.md
v3/docs/task-records/2026-11-01-w23-w24-remediation.md（新建）
```

> 建议：`git add -A && git commit -m "W-23 运行产物移出版本控制；W-24 模板化输出裁定暂缓"`（由人工执行）。

## 关闭标识
- **完成时间**：2026-11-01
- **最终状态**：✅ 全部完成
- **关闭说明**：W-23 已完成（`v3/.gitignore` + 250 条 `git rm --cached`，工作区保留）；W-24 已裁定暂缓并关闭（三处文档同步）；门禁全绿；零源码/零构建；**commit/push 由人工接管**。
