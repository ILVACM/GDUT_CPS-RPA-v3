---
title: RPA 工作流引擎（v3/rpa_engine/）使用指南
type: instance
scope: instance
status: active
owner: 黄泊凯
last-updated: 2026-11-01
tags: [引擎, 使用指南, 启动, 打包, GUI]
version: 1.5.0
binding: self_contained
confidence: 已校验一致（实例层执行文档；2026-09-13 按 docs/doc-governance.md §9 标签落位规范补记 binding/confidence）；2026-09-13 CLI 交互口径调整（废弃目标态）；2026-10-24 R16 同步目录树（storage/temp/tools/templates-user）、测试规模（15 文件/234 用例）与 build/ 子目录；2026-11-01 R17 运行数据目录不纳入版本控制（v3/.gitignore，W-23）
governance: instance
inherits_from:
  - docs/runtime-env-spec.md
overrides: none
---

# RPA 工作流引擎（v3/rpa_engine/）

> 参数文件驱动的轻量级执行引擎。业务逻辑完全由 JSON 参数文件定义，
> 引擎负责解析、校验和按序执行。

---

## 启动方式

### 主入口：GUI（四阶段已完成）

GUI 基于 PyQt5，面向非技术文员，提供四个阶段页面：输入数据选择、操作配置、运行追踪、结果报告（阶段 4 确认后返回阶段 1，形成闭环）。
交互方式为非拖拽式（鼠标点击/键盘输入/鼠标拖动），交互界面只显示关键信息（步骤名称、状态、结果）。
原 print 调试输出经 loguru 落盘 logs/ 文件（GUI 终端面板已随 W-19 移除，2026-09-18），详细日志同由 loguru 记录到文件。

> 2026-10-24 注记：DAG 重构里程碑 M0-M7 已于 2026-09-20 全部完成（原表述"框架主体已实现"为当时口径）；
> 实际实现为 `gui/node_graph.py` 单文件（1,087 行），`gui/graph/` 五层包方案未采纳；余真机回归 18 项待人工。

### 调试入口（CLI 已移除）

> **CLI 交互代码已于 2026-09-13 移除**（见 `docs/backlog.md` W-18）：`main.py` 的 CLI 分支、`run_workflow`、`argparse` 依赖均已删除，`main()` 现为 GUI 薄壳。以下为**历史用法**，仅留档参考。

```bash
# 历史用法（已移除，2026-09-13）
# 方式 1：脚本调用（需在 rpa_engine 目录下执行）
python main.py path/to/workflow.json

# 方式 2：脚本调用（需在仓库根目录下执行）
python rpa_engine/main.py path/to/workflow.json

# 强制 CLI 模式开关（必须同时提供 workflow_json 路径）
python main.py path/to/workflow.json --cli
```

说明（历史行为）：不带参数启动 GUI；带 workflow_json 路径（或 `--cli`）走 CLI 分支；`--cli` 未附路径时 argparse 报错退出（退出码 2）。**现为 GUI 唯一交互入口。**

> ⚠️ GUI 生成工作流 JSON 时的关键规避要点（v3.1 口径，已内联，无需跳转）：
> ① 步骤参数键名使用代码侧命名（如 `rename_columns` 用 `mapping`，勿用 `column_mapping`/`new_column` 等别名）；
> ② 步骤 `params` 键须在该操作的 `param_keys` 白名单内（见 docs/architecture.md §6 用户操作目录清单），白名单外参数会被校验拦截；
> ③ PPT 导出为预留能力：v3.1 用户操作目录（BUILTIN_OPS）无此操作，GUI 操作目录中不显示。

### 编译打包（一键生成单文件 exe）

开发流程末端的打包入口为 `v3/build.bat`（纯 cmd，**ASCII 编码**：R6/C2 起中文提示已改为纯 ASCII 以保证跨编辑器/Agent 编码安全），
基于 `v3/RPA_Workflow_v3.spec` 调用 PyInstaller，产出单文件 GUI 可执行程序。**构建由人工执行，Agent 不代跑。**

**前置条件**：

- 必须在已激活的 conda 环境中运行（脚本检测 `CONDA_DEFAULT_ENV`，否则告警中止）
- 环境内已安装 PyInstaller；未安装时脚本提示执行 `pip install pyinstaller`

**执行方式与参数用法**（在 v3 目录下运行）：

```bat
rem 无参数：默认输出到 v3\build\
build.bat

rem 自定义输出目录（绝对路径）
build.bat D:\Deploy

rem 自定义输出目录（相对路径，基于 v3 目录解析）
build.bat ..\dist\prod
```

**产出物**：

- `<输出目录>\RPA_Workflow_v3.exe` — 单文件 GUI 可执行程序（无控制台窗口；spec 的 `datas` 已内置 `rpa_engine/templates/` 目录资源）
- `<输出目录>\BUILD_INFO.txt` — 构建信息（构建时间、输出路径、conda 环境名、Python 版本、PyInstaller 版本、`SOURCE_HASH` 源码指纹、`GIT_REV` 构建时提交哈希；GBK 编码，UTF-8 工具读取乱码属正常现象）

> 2026-10-24 注记：现行 `templates/` 已不含工作流模板（v3 预设模板已归档清理），仅含 `README.md` 与 `outputs/.gitkeep`；
> 用户模板 `templates/user/` 于 exe 同级运行时创建，不打包内置。构建产物有效性判定以 `SOURCE_HASH` 为准（见 docs/build-guide.md §1.10）。

> ⚠️ 输出路径参数禁止包含 `&`、`|`、`<`、`>`、`^`、`"` 等特殊字符（脚本检测到即告警中止）。

---

## 目录结构

```
v3/
├── build.bat                    # 一键编译打包脚本（PyInstaller，用法见"编译打包"小节）
├── RPA_Workflow_v3.spec         # PyInstaller 编译配置（由 build.bat 调用；被根 .gitignore 的 *.spec 忽略，不入库）
├── build/                       # 编译输出目录（人工接管）
│   ├── RPA_Workflow_v3.exe      # 单文件 GUI 可执行程序（当前有效版本）
│   ├── BUILD_INFO.txt           # 构建信息（含 SOURCE_HASH / GIT_REV）
│   ├── backup/                  # 构建备份（历史 exe，由 build.bat 自动移入）
│   ├── logs/                    # 构建目录下的运行日志（build.bat 保护，不删除）
│   ├── storage/                 # 构建目录下的运行数据（build.bat 保护，不删除）
│   ├── temp/                    # 构建目录下的运行临时文件（build.bat 保护，不删除）
│   ├── templates/               # 打包用模板资源
│   ├── workspace/               # 构建目录下的运行工作区（build.bat 保护，不删除）
│   ├── work/                    # PyInstaller 中间产物
│   └── dist/                    # PyInstaller 原始 exe
└── rpa_engine/
    ├── main.py                    # 引擎入口（GUI 为唯一交互入口；CLI 交互代码已移除，见 docs/backlog.md W-18）
    ├── paths.py                    # 运行环境路径解析（ENGINE_ROOT / 打包根 / 用户模板目录）
    ├── engine/                    # 三段式执行引擎（v3.1：数据表驱动）
    │   ├── __init__.py
    │   ├── parser.py              # v3.1 JSON → WorkflowDef 解析（tables + steps）
    │   ├── validator.py           # 全量校验（表编号/操作白名单/引用链）
    │   ├── executor.py            # 编排器（兜底补导 + 步骤循环 + 异常策略）
    │   └── registry.py            # 用户操作目录接口（BUILTIN_OPS 再导出）
    ├── ops/                       # 操作函数层（v3.1 核心，L0-L3 四层）
    │   ├── sql_safety.py          # L0：SQL 安全（quote_ident/build_where/txn）
    │   ├── session_db.py          # L0：会话数据库（唯一连接创建点，WAL）
    │   ├── excel_preprocessor.py  # L0：Excel 预处理（复制/转换/扫描/表头行）
    │   ├── excel_normalizer.py    # L0：Excel 规范化（表头/类型统一）
    │   ├── sqlite_manager.py      # L0：数据交换（DF 导入导出/只读 SQL）
    │   ├── table_importer.py      # L1：Excel → SQLite 导入
    │   ├── table_lifecycle.py     # L1：表生命周期（建/删/复制/合并）
    │   ├── table_schema.py        # L1：表结构（改名/类型转换/列信息）
    │   ├── table_content.py       # L1：行级增删改查
    │   ├── filter_dedup.py        # L2：条件筛选 + 条件去重
    │   ├── mapping_matcher.py     # L2：跨表映射匹配（SQL JOIN，r_ 前缀防重名）
    │   ├── aggregator.py          # L2：条件统计（分组/整表/多指标）
    │   ├── exporter.py            # L2：结果导出（流式 xlsx，零 DataFrame）
    │   └── step_executor.py       # L3：BUILTIN_OPS 目录（10 项）+ 单步分发
    ├── steps/                     # （已删除，2026-09-13；原 v3 废弃实现，历史见 git 历史）
    ├── gui/                       # GUI 核心交互模块（四阶段页面 + 节点图 + 后台线程）
    │   └── app(启动自检)/main_window(主窗口)/page_input_selection(阶段1)/page_operation_config(阶段2)/page_progress(阶段3)/page_report(阶段4)/node_graph(节点图)/graph_edges(五类边派生)/worker(执行线程)/models(数据+翻译层+StepMeta注册表)/forms(9类参数表单)/user_template_manager(历史配置模板)/recent_steps(最近使用持久化)/styles
    ├── tests/                     # 单元测试：16 个测试文件 / 263 用例
    │   ├── test_ops_contracts.py(67) / test_models_data.py(38) / test_registry_guards.py(20)
    │   ├── test_graph_edges.py(17) / test_step_catalog.py(16) / test_registry_single_source.py(16)
    │   ├── test_engine_robustness.py(15) / test_translation.py(9) / test_engine_overwrite.py(8)
    │   └── test_engine_failure_paths.py(7) / test_dependency_contract.py(5) / test_error_messages.py(5)
    │       / test_states_consistency.py(5) / test_recent_steps.py(3) / test_validator_cross.py(3)
    ├── tools/
    │   └── smoke/                 # 门禁冒烟脚本（smoke_m1m3.py、smoke_mb.py）
    ├── templates/
    │   ├── outputs/               # （示例输出模板已于 2026-09-14 清理失效，仅留 .gitkeep 占位）
    │   ├── user/                  # 用户配置模板（运行时创建，UserTemplateManager 管理）
    │   └── README.md              # 模板目录说明
    ├── workspace/                 # 运行数据目录：会话库、last_config.json、gui_workflow.json、normalize_report/（自动创建）
    ├── logs/                      # 运行数据目录：日志（loguru 输出，gui_YYYY-MM-DD.log）
    ├── storage/                   # 运行数据目录：recent_steps.json（最近使用持久化，自动创建）
    └── temp/                      # 运行数据目录：input_selection/（导入副本）、normalized/（规范化产物）
```

> ⚠️ 引擎无独立配置文件，所有运行配置统一从工作流 JSON 的 `global` 字段读取（`global_config` 为 parser.py 中 dataclass 的属性名，非 JSON 键）。

> **2026-10-24 注记**：运行数据目录共 4 个（`workspace/`、`logs/`、`storage/`、`temp/`），均由 `paths.get_engine_root()` 定位、运行期按需创建；
> 另 `templates/user/` 为用户配置模板目录（运行时创建）。`backup/` 不在运行期创建——`build/backup/` 是 build.bat 的构建备份目录（存放旧 exe）。
> **2026-11-01 注记（W-23）**：上述 4 个运行数据目录已由 `v3/.gitignore` 排除，**不纳入版本控制**（目录由代码按需 mkdir，清理逻辑不变）；仓库中不再跟踪其内容。
> 测试规模口径：`rpa_engine/tests/` 现为 **16 个测试文件 / 263 用例**（原表述"DAG 重构验证通道"为 2026-09-20 阶段口径，现已扩充为全量单元测试）。

---

> 本文件为实例层执行文档（governance: instance），经 knowledge/Instances-INDEX.md 注册；正文自包含，可直接执行。
