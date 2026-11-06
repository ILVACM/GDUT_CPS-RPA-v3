# V3 - 当前重构升级版本

> 本目录承载 CPS-GPES RPA（南方电网广电监）项目的活跃开发代码，聚焦 RPA 工作流引擎的实现与迭代。

## 定位

- 版本号：v3.1（数据表驱动架构，自 v3 预设步骤架构迭代而来，2026-08-23 定稿）｜状态：✅ 活跃开发中 [已校验一致]
- 定位：已具备生产交付形态（真机项待人工）[已校验一致]（2026-10-24 更新：原表述为"当前功能重构活跃版本，即将用于正式业务生产"）
- 上级项目：CPS-GPES RPA（仓库标识 CPS-GPES_RPA-20250312）

## 项目简介

V3 RPA 工作流引擎是一个参数驱动的 ETL 框架，核心思想是"引擎与业务逻辑分离"：所有业务逻辑只存在于 JSON 参数文件中，引擎仅负责解析、调度、异常处理和资源清理。[已校验一致]

**核心特性**：三段式执行流水线（解析 → 校验 → 执行）；10 项用户操作目录 `BUILTIN_OPS`（filter/dedup/mapping_match/aggregate/export/merge_tables/copy_table/rename_columns/convert_dtype/supervision_report，经 `ops/step_executor` 统一分发；v3 七类预设步骤已废弃并移除）；数据表驱动参数文件（tables[]+steps[]，JSON 是业务逻辑唯一载体）；异常策略三档（stop/skip/retry）；SQLite 共享连接（WAL 模式）。[已校验一致]

**技术栈**：Python 3.11（实际构建 3.11.15）| SQLite 3 (WAL) | pandas >=2.0,<4 | openpyxl >=3.1 | xlrd >=2.0 | loguru >=0.7 | psutil >=5.9 | PyQt5 >=5.15,<6 | PyInstaller >=6.22（打包）[已校验一致]（2026-09-24 R6/C4：python-docx/python-pptx 死依赖已移除；2026-10-24 按 `requirements.txt` 补全 pandas 上界 `<4`、xlrd、PyQt5 上界 `<6`、pyinstaller 版本约束与 Python 3.11 口径，锁定清单见 requirements.lock）

## 快速开始

- GUI 启动：`python rpa_engine/main.py`（无参数）。**CLI 交互代码已移除（2026-09-13，W-18）**：`main.py` 的 CLI 分支已删除；历史 CLI 用法见 rpa_engine/README.md；exe 已于 2026-10-19 重建并核验（`SOURCE_HASH` `9fc85bc09ac1376a` 与当前源码一致，FILES=56），**W-20 已关闭**。[已校验一致]（2026-10-24 更新：原表述为"exe 待重建（W-20）"）
- 编译打包：在 v3 目录运行 `build.bat`（需已激活 conda 环境），默认产出 build\RPA_Workflow_v3.exe。[已校验一致]
- 运行方式判定：Agent 接到任务后首跳 `docs/agent-execution-mode.md` 确定运行模式。[已校验一致]

## 项目结构概览

- `AGENTS.md` — 规约总纲（约束层唯一载体，唯一第一入口）｜`docs/` — 知识层（INDEX + 13 篇知识文档 + task-records/ 任务记录目录）+ 方案态层（plan/：INDEX + 实施方案）｜`knowledge/` — 实例层索引（INDEX + Instances-INDEX，实例文档位于自然位置）[已校验一致]
- 面向使用者/管理员：`docs/user-manual.md`（用户手册：四步上手＋常见错误自救表）｜`docs/deployment-guide.md`（部署指南：便携版约定＋指纹核对）（2026-09-24 R6/E6 新增）[已校验一致]
- 面向开发者/Agent：`docs/function-spec-rules.md`（功能函数设计与变更规约：三位一体、双记录表、交互位置固化、变更顺序＋13 项登记清单）（2026-09-24 R7 新增，经 AGENTS §2.5 背书具 [约束] 效力）[已校验一致]
- `rpa_engine/` — 工作流引擎实现（engine/ 三段式编排、ops/ 操作函数层、gui/ 四阶段页面、templates/；steps/ 已删除（2026-09-13，原废弃实现）；运行时目录由 paths.py 按需生成，不预置于仓库，详见 rpa_engine/README.md）[已校验一致]
- `Test/` — 端到端测试资源（测试工作暂缓）｜`build/` — 编译产出｜`_temp/` — 临时工作文件（非正式交付物）[已校验一致]

## 当前状态速览

- GUI 渲染相关问题已全部解决（2026-08-18 用户确认）；Agent 规约体系已建成（2026-08-18），并于 2026-08-21 升级至 Project-Spec-build v2.2 达标（任务执行锚点机制启用，详见 AGENTS.md）。[已校验一致]
- v3.1 数据表驱动架构重构已完成（2026-08-23），新增 14 文件、修改 11 文件、禁用 9 旧步骤文件（steps/ 全部 [DEPRECATED v3]；该目录已于 2026-09-13 删除）、归档 8 旧工作流模板；py_compile 22/22 通过。[已校验一致]
- 已知阻塞详见 docs/architecture.md §9（#1/#2/#4 已修复，#3 export_ppt 仍为预留；入口指针见 AGENTS.md §5.4「已知阻塞」）。[已校验一致]

- 2026-09-13 约束层二轮精简：`AGENTS.md` 注入字符数（含 CR 口径）8,104 → 7,628，注入截断解除；细节下沉 `docs/doc-governance.md` §6（冲突解决与豁免）与 `docs/build-guide.md` §1.10（构建产物有效性判定）；同步修正 `knowledge/Instances-INDEX.md` 的失效链接。[已校验一致]

- 2026-09-13 治理待办批量处置：新增 `docs/backlog.md`（W 编号待办清单，队列由 `_temp/` 升格为受管辖文档）；`docs/doc-governance.md` 补 §7 源码↔规约同步规则、§8 验收与回归记录规范、§9 标签体系落位规范、§10 约束层容量与下沉规则；`docs/agent-execution-mode.md` §6 新增编码类角色集（Coder/Reviewer/Tester）。[已校验一致]

- 2026-09-14 存疑项 5 条补充裁定落地（R1~R5，登记 `docs/backlog.md` W-21）：GUI 代码先重构设计后开发（R1）；`build/` 及构建产物 Agent 忽略、构建由人工接管（R2）；`rpa_engine/templates/outputs/` 失效模板宣布清理（R3，目录仅留 `.gitkeep`）；`_temp/` 清理至仅剩 `DAG-rebuild/` 汇聚包 + `repo-context-report.md`（R4；**注**：R10 于 09-24 再度收敛，`repo-context-report.md` 已清理，现 `_temp/` 仅剩 `DAG-rebuild/` 与 `ledger_2026-09-24/`）；conda 环境路径 `C:\Users\hbk\.conda\envs\CPS-GPES_RPA-py311` 固化于 `docs/runtime-env-spec.md` §2（R5）。`docs/build-guide.md` §1.10 修正 exe 为"已失效+人工重建"（**历史状态**；2026-10-19 已重建核验，W-20 于 2026-10-24 关闭）。[已校验一致]

- 2026-09-24 完善度修复轮（W-03 R6，批次 A~F）：37 项缺口修复落地——诚实报告（部分完成态）、错误话术人话化（error_messages 翻译层＋技术详情折叠）、build.bat 重构（测试门禁＋源码指纹＋原子发布＋五目录保护）、执行链健壮性（busy_timeout/取消链/超时告警/中间表清理/导入白名单）、画布性能（合并刷新＋预分组）、版本门禁、last_config 防抖、死代码大扫除（move_step/门面/死 API 除名）；回归 118 用例＋双 smoke（迁 `rpa_engine/tools/smoke/`）＋启动自检 6 项全绿；新增 `tools/doc_verify.py` 文档体检脚本与用户手册/部署指南。详见 `_temp/ledger_2026-09-24/W-03_Remediation_round_2026-09-24/REPORT.md`。[已校验一致]

- 2026-09-24 功能函数设计规范固化（W-22 登记，R7 规约整理轮）：人工裁定的 4 条规定（三位一体／双记录表／前端交互位置固化／变更工作流顺序）落地为知识层 [约束] 专章 `docs/function-spec-rules.md`，AGENTS.md 仅增极简指针（§2.6）与背书 1 行并按 doc-governance §10.2 等量下沉保持容量合规；同步修正 `docs/architecture.md` 两处文档失实（参数白名单为执行期过滤、`target_param`/`match_param` 休眠）；代码层 16 项缺口只登记为待补强项（backlog W-22）。**本轮零代码改动**（118 用例回归全绿）。[已校验一致]

- **2026-10-24 文档一致性收口（R16）**：Git 边界固化（写操作人工接管、只读 `git status/diff/show/log` 允许）；本文件同步以下实况——技术栈按 `requirements.txt` 补全（pandas `>=2.0,<4`、xlrd、PyQt5 `<6`、pyinstaller `>=6.22`）；exe 已于 2026-10-19 重建并核验（`SOURCE_HASH` `9fc85bc09ac1376a` 与当前源码一致，FILES=56，`TESTS_SKIPPED=0`），**W-20 已关闭**（上一条 2026-09-14 记录中的"已失效+人工重建"为当时状态）；定位更新为"已具备生产交付形态（真机项待人工）"；M0-M7 已于 2026-09-20 全部完成（实际实现为 `gui/node_graph.py` 单文件 1,087 行，`gui/graph/` 五层包方案未采纳）；单元测试 234 用例 / 15 个测试文件；运行数据目录 4 个（`workspace/`、`logs/`、`storage/`、`temp/`）。[已校验一致]

> 本文件由 Agent 规约体系自动维护，详细信息请参阅 docs/ 目录。
