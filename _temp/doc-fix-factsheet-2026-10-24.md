# 文档一致性修正 · 事实基线（2026-10-24）

> 性质：`_temp/` 临时参考（无约束力）。本文件是本轮所有 Writer 的**唯一事实来源**；
> 与任何文档冲突时以本表 + 代码实测为准。所有数据均为 2026-10-24 实测。

---

## 1. 版本与仓库

| 事实 | 权威值 | 证据 |
|---|---|---|
| 仓库根 | `D:\cps-gpes_rpa-20250312` | 目录实测 |
| 活跃工作区 | `v3/` | `AGENTS.md` |
| Git remote | `origin https://gitee.com/ILVACM/cps-gpes_rpa-20250312.git` | `git remote -v` |
| Git 分支 | **`master`**（不是 main） | `git branch` |
| HEAD | `703c67e`（2026-10-24 14:51 人工提交） | `git log -1` |
| `.gitattributes` | 不存在 | `Test-Path` |
| `core.autocrlf` | `true` | `git config` |
| 根 `backup/` | **不存在** | `Test-Path` |
| 根 `code/` | **不存在** | `Test-Path` |
| v1 | `BaseDEMO/`、`CNAS/`、`FROZEN.md` | 目录实测 |
| v2 | `A-docs/`、`ConsultDepartment/`、`FinanceDepartment/`、`SafetyandQualityDepartment/`、`ScienceandTechnologyInnovationDepartment/`、`SuperVisionDepartment/`、`FROZEN.md` | 目录实测；**无** `BaseDEMO/`、**无** `ArchivedAcceptanceReport/` |

---

## 2. 引擎代码实况

| 事实 | 权威值 | 证据 |
|---|---|---|
| 用户操作目录 | **9 项** `BUILTIN_OPS`：filter/dedup/mapping_match/aggregate/export/merge_tables/copy_table/rename_columns/convert_dtype | `ops/step_executor.py` L61-193 |
| 每项字段 | **8 字段**：`func`/`description`/`output`/`param_keys`/`params_schema`/`extra_input_min`/`overwritable`/`deprecated` | 同上 |
| 参数契约唯一源 | `params_schema`；`default_params()` 与 `execute_step` 回退均派生于此 | `ops/step_executor.py` L196-214；`gui/models.py` L1002-1016 |
| 代码总行数 | `rpa_engine/` 共 **17,397 行** Python：gui 7,986（16 文件）／ops 4,499（15）／tests 3,247（16）／engine 723（5）／tools 942（2） | 实测统计 |
| 执行链 | `gui/worker.py`(QThread) → `engine/executor.execute_workflow()` → `ops/step_executor.execute_step()` | 代码 |
| SQLite 连接 | `ops/session_db.SessionDB` 是**唯一连接创建点**；`new_connection()` 供 worker 线程自建；WAL + synchronous=NORMAL + busy_timeout=5000 | `ops/session_db.py` L64-80 |
| 兜底补导 | `engine/executor.ensure_input_tables()`（**不是** `load_tables`） | `engine/executor.py` L81-124 |
| 输出表命名 | GUI 链路 `t_{uid}`（`gui/models.py` L742-761）；外部 JSON 缺省回退 `t_s{n}`（`ops/step_executor.py` L312） | 代码 |
| 导出实现 | `ops/exporter.export_table` 用 `Workbook(write_only=True)` **流式直出、无模板**；输出目录自动创建；后缀非 `.xlsx` 抛中文 `ValueError` | `ops/exporter.py` L144-173 |
| PPT/Word/TXT 导出 | **v3.1 无对应用户操作**（PPT 为预留能力；Word/TXT 无实现） | `architecture.md` §6/§9 #3 |
| `steps/` 目录 | **已删除**（2026-09-13） | 目录实测 |
| `gui/graph/` 包 | **不存在**；DAG 重构实际落在 `gui/node_graph.py` 单文件（1,087 行） | 目录实测 |
| `templates/workflows/` | **不存在** | 目录实测 |
| `templates/outputs/` | 仅 `.gitkeep` | 目录实测 |
| `templates/user/` | 存在（运行时创建，用户配置模板） | 目录实测 |
| `Test/temp/` | **不存在** | 目录实测 |
| `Test/input/` | `测试输入0.xlsx`、`测试输入1.xlsx`、`测试输入2.xlsx`、`测试输入3.xlsx` | 目录实测 |

---

## 3. 运行数据目录（程序运行期创建）

**4 个运行数据目录**（`paths.get_engine_root()` 下）：

1. `workspace/` — 会话库、`last_config.json`、`gui_workflow.json`、`normalize_report/`
2. `logs/` — `gui_YYYY-MM-DD.log`（loguru，按日滚动）
3. `storage/` — `recent_steps.json`（最近使用）
4. `temp/` — `input_selection/`（导入副本）、`normalized/`（规范化产物）

另：`templates/user/`（用户配置模板，运行时创建）。

> `backup/` **不在**程序运行期创建；`build/backup/` 是 build.bat 的构建备份目录（旧 exe）。
> `build.bat` 保护的是 **build 目录下**的 `workspace/logs/storage/temp/backup` 五个目录（若存在）。

---

## 4. 测试与门禁

| 事实 | 权威值 |
|---|---|
| 单元测试 | **234 用例 / 15 个测试文件**（`rpa_engine/tests/`） |
| 测试文件清单 | test_dependency_contract(5)、test_engine_failure_paths(7)、test_engine_overwrite(8)、test_engine_robustness(15)、test_error_messages(5)、test_graph_edges(17)、test_models_data(38)、test_ops_contracts(67)、test_recent_steps(3)、test_registry_guards(20)、test_registry_single_source(16)、test_states_consistency(5)、test_step_catalog(16)、test_translation(9)、test_validator_cross(3) |
| 门禁冒烟 | `tools/smoke/smoke_m1m3.py`、`tools/smoke/smoke_mb.py` → `SMOKE_ALL_OK` ×2 |
| 启动自检 | 6 项（Python 版本/依赖/目录可写/操作目录注册/注册表字段完整性/上次配置载入）→ `ok=True` |
| 文档体检 | `tools/doc_verify.py` → PASS（links=86） |
| 文档体检报告 | `_temp/verify-20261024-1519.md` |

---

## 5. 文档体系规模

| 事实 | 权威值 |
|---|---|
| 知识层文档 | **13 篇**（docs/ 顶层 md，不含 INDEX） |
| 方案态文档 | **1 篇**（DAG_refactor_plan.md）＋ INDEX |
| 任务记录 | **48 篇** ＋ TEMPLATE.md |
| 实例层 | 1 篇（rpa_engine/README.md） |
| AGENTS.md 容量 | 含 CR **7,877 / 8,000**，余量 **123**（修正前）；目标 ≤7,800（余量≥200） |
| 行尾 | 纯 CRLF（loneCR=0、loneLF=0） |

---

## 6. 构建产物

| 事实 | 权威值 | 证据 |
|---|---|---|
| exe 路径 | `build/RPA_Workflow_v3.exe`（73,792,711 字节） | 目录实测 |
| 构建时间 | **2026-10-19 03:57:09** | `build/BUILD_INFO.txt` |
| `SOURCE_HASH` | **`9fc85bc09ac1376a`** | BUILD_INFO |
| 当前源码重算 | **`9fc85bc09ac1376a`**（FILES=56） | `tools/make_fingerprint.py` |
| 结论 | **exe 与源码同版、有效** | 指纹一致 |
| `TESTS_SKIPPED` | 0 | BUILD_INFO |
| `GIT_REV`（构建时） | `bd017166...`（构建时 HEAD，现 HEAD 已前进到 `703c67e`） | BUILD_INFO |
| 判定口径 | 以 `SOURCE_HASH` 为准；`GIT_REV` 仅辅助追溯 | `build-guide.md` §1.10 |
| `build/backup/` | 4 个历史 exe（2026-09-24 ~ 2026-10-19） | 目录实测 |

---

## 7. 待办状态（2026-10-24）

| 编号 | 状态 | 说明 |
|---|---|---|
| W-01~W-12、W-14~W-19、W-21 | ✅ 已完成/已裁定关闭 | 见 backlog |
| W-13 | 🚫 已撤销 | — |
| **W-20** | ✅ **已完成（2026-10-24 核验）** | exe 2026-10-19 重建，SOURCE_HASH 与源码一致 |
| **W-22** | ✅ **已完成（2026-10-19 R15）** | 15 行闭合＋B5 已解决；P1-6 转受控例外 |
| **W-23**（新） | ⏸️ 待指令（人工） | `rpa_engine/temp/` 224 个文件被 git 跟踪 + 启动清理会删夹具 |
| **W-24**（新） | ⏸️ 待指令（人工裁定） | “模板化输出”红线 vs `export` 无模板流式直出 |

统计：待指令 **2**（W-23、W-24）｜已完成/已裁定关闭 **21**｜已撤销 **1**。

---

## 8. DAG 重构状态

| 事实 | 权威值 |
|---|---|
| M0-M7 | **全部完成（2026-09-20）** |
| 实际实现 | `gui/node_graph.py` 单文件（1,087 行）；`gui/graph/` 五层包方案**未采纳**（F 批裁定 2026-09-20） |
| 五类边 | `gui/graph_edges.py` 单一事实源 |
| 剩余 | 真机回归清单 18 项（人工） |

---

## 9. Git 使用边界（本轮新口径，2026-10-24）

- **写操作**（提交/推送/拉取/分支/合并/变基/回退/暂存/清理等）**一律人工接管，Agent 不执行**。
- **只读**（`git status`/`git diff`/`git show`/`git log`）**允许**，用于比对差异，不得改变工作区、索引或版本库状态。
- 构建（`build.bat`、`build/`）仍由人工接管（R2）。

---

## 10. 历史遗留说明

- 根 `AGENTS.md`/`README.md` 上次实质更新为 2026-08-30，严重滞后。
- 4 篇任务记录摘要状态为「进行中」但文末关闭标识为「已完成」（2026-09-24-temp-ledger-cleanup、2026-10-18-importdata-repair、2026-10-19-func-spec-doc-sync、2026-10-19-w22-n-remediation）。
- `_temp/repo-scan-2026-10-23.md` 记录 2026-10-23 扫描结论（含误删夹具事件与还原留痕），本轮引用不修改。
