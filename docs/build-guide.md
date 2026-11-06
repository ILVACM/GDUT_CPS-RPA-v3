---
title: Build Guide — V3 RPA 工作流引擎编译配置规范
type: knowledge
scope: global
status: active
owner: 黄泊凯
last-updated: 2026-10-24
tags: [编译, 打包, 构建, spec, PyInstaller]
binding: constraint
confidence: 已校验一致（原 --specpath 差异 2026-08-18 已按实际修正；§1.7 hiddenimports 2026-08-24 按 v3.1 spec 实测更新）；2026-10-24 R16 收口：§1.9 spec 恢复路径更正（spec 被 .gitignore 忽略、不在版本库）、§1.10 构建产物有效性按 2026-10-24 实测改为「有效」（W-20 关闭）、§3 中间产物结构补 `backup/`
content-revision: 2026-10-24
---

# Build Guide — V3 RPA 工作流引擎编译配置规范

> 所属层级：知识层（docs/），经 AGENTS.md §2.5 背书具 [约束] 效力
> 本文档描述 PyInstaller 编译配置的结构与修改规范，供 agent 在修改或重建 spec 时作为权威参考。
>
> **适用范围**：修改编译配置、重建 spec 文件、排查打包问题时查阅
> **最后更新**：2026-10-24（R16 文档一致性收口：§1.9 spec 恢复路径更正为"不在版本库、无法 git 恢复"；§1.10 构建产物有效性按 2026-10-24 实测更新为「有效」、W-20 已关闭；§3 中间产物结构补 `backup/`。历史 2026-09-13：新增 §1.10「构建产物有效性判定」，自 AGENTS.md §8 承接；历史 2026-08-24：§1.7 hiddenimports 按 v3.1 spec 实测更新为 paths+ops 全模块+openpyxl+PyQt5.sip；可信度升为 [已校验一致]。历史：2026-08-21 v2.2 升级新增 YAML 元信息区；内容修订基线 2026-08-18）｜**可信度状态**：[已校验一致]（原 §1.3/§1.4/§1.7/§3 关于 --specpath 的差异 2026-08-18 已按实际 build.bat 行为修正；§1.7 hiddenimports 于 2026-08-24 按 v3.1 spec 更新；§1.9/§1.10 于 2026-10-24 按版本库与构建产物实测校正）

---

## 1. 编译配置规范（PyInstaller spec）

### 1.1 概述

spec 文件是 PyInstaller 的打包配方，属于**工程配置文件**，不是知识库文档本身。
本节描述其结构、与 build.bat 的关系、修改边界和重建流程，供 agent 在修改或重建 spec 时作为权威参考。

spec 文件位置：`v3/RPA_Workflow_v3.spec`

### 1.2 文件结构说明

| 区块 | 作用 | agent 关注点 |
|------|------|-------------|
| `Analysis()` | 声明入口、搜索路径、数据文件、隐式依赖 | 新增模块/资源时修改此处 |
| `PYZ()` | Python 字节码归档 | 通常无需修改 |
| `EXE()` | 最终可执行文件配置（名称、图标、单文件模式） | 改名/改图标时修改此处 |
| `COLLECT()` | 收集运行时依赖（非 onefile 模式使用） | onefile 模式下此区块不被使用 |

### 1.3 与 build.bat 的关系

- build.bat 通过**位置参数**传递 spec 文件：`pyinstaller ... "%SPEC_FILE%"`（非 `--specpath`）
- build.bat 不使用 `--specpath`：直接传入既有 spec 文件时 PyInstaller 不再生成 spec 副本，仅覆盖 `--workpath`/`--distpath`（2026-08-18 按实际 build.bat 调用行修正 [存在差异→已修正]）
- build.bat 命令行参数会**覆盖** spec 文件中的同名运行时配置（如 `--distpath`、`--workpath`）
- 修改源码 spec 后无需同步修改 build.bat，反之亦然
- 但两者的**语义应保持一致**；若发现冲突，以 build.bat 命令行参数为运行时真相，并在输出中标注不一致项供人工裁决

### 1.4 中间产物目录结构

编译时所有中间产物统一归入 `build/` 目录（可通过 `--build-dir` 自定义）：

```
<build-dir>/
├── work/          ← PyInstaller 工作目录（--workpath），临时分析产物
├── dist/          ← 编译输出的 .exe 原始位置（--distpath）
├── RPA_Workflow_v3.exe  ← 最终交付副本（Step 4 从 dist/ 复制而来）
├── BUILD_INFO.txt       ← 构建元信息（自动生成）
└── backup/              ← 旧 exe 构建备份（原子发布留存，RPA_Workflow_v3_<时间戳>.exe）
```

> 项目根目录下不应出现 `dist/`、`*.spec`（源码 spec 除外）等残留。
> build.bat Step 2 会自动清理历史残留。
> **2026-10-24 注记**：`build/backup/` 为构建备份目录（非程序运行目录），当前存 4 个历史 exe（2026-09-24～2026-10-19）。

### 1.5 .exe 交付路径

| 场景 | .exe 位置 |
|------|----------|
| 默认（无 --output） | `<build-dir>/RPA_Workflow_v3.exe` |
| `--output <目录>` | `<build-dir>/RPA_Workflow_v3.exe` + `<目录>/RPA_Workflow_v3.exe` |
| `--output <文件路径>` | `<build-dir>/RPA_Workflow_v3.exe` + `<文件路径>`（含重命名） |

> `build/` 根目录下的 .exe 副本始终存在，是清理操作的安全锚点。

### 1.6 中间产物清理机制

- **默认行为**：保留 `build/` 内所有内容（便于调试和增量编译）
- **原子发布（R6/C2-P1-9，2026-09-24 起）**：编译在 `build/_build_tmp/` 临时目录进行，成功后才发布——旧 exe 先移入 `build/backup/RPA_Workflow_v3_<时间戳>.exe` 留存，再复制新包；任一环节失败旧包无损。原 Step 2"先 `rmdir /s /q build/` 再编译"逻辑已废除。**用户数据保护红线**：脚本任何分支不删除 `build/` 下 `workspace/`、`logs/`、`storage/`、`temp/`、`backup/` 五目录及已发布 exe
- **测试门禁（R6/C2-D4①，默认强制）**：打包前自动跑 `python -m unittest discover -s tests` ＋ `tools/smoke/` 双冒烟（cwd=rpa_engine），任一失败即中止且不触碰任何现有产物；`--skip-tests` 显式跳过并在 `BUILD_INFO.txt` 记 `TESTS_SKIPPED=1`（需人工审查）
- **`--clean` 行为**：编译成功并确认 .exe 已发布后，删除 `_build_tmp/` 及历史遗留中间目录（`work/`、`spec/`、`dist/`、`*.toc`、`*.waf*`、`__pycache__/`），**仅保留** `.exe`、`BUILD_INFO.txt`、`backup/` 与用户数据五目录
- **安全保障**：清理前会再次验证 .exe 存在，验证失败则中止清理并报错
- **脚本消息语言（R6 备注）**：build.bat 消息改为纯 ASCII 英文——原文件为 GBK 编码中文，编辑易致编码损坏；参数接口与行为契约不变
- agent 在执行 `--clean` 编译前，应提醒用户确认不需要保留中间产物用于调试

### 1.7 关键配置项含义

> 以下值以当前项目实际 spec 文件为准。

- **入口文件**：`rpa_engine/main.py` — GUI 启动入口，修改需同步验证启动链路
- **pathex**：`['rpa_engine']` — 模块搜索路径，新增顶层包时需追加
- **datas**：`[('rpa_engine/templates', 'templates')]` — 需打包的非代码资源（工作流模板目录），新增资源目录时必须同步更新
- **hiddenimports**：`['paths', 'ops', 'ops.sql_safety', 'ops.session_db', 'ops.excel_preprocessor', 'ops.sqlite_manager', 'ops.table_importer', 'ops.table_lifecycle', 'ops.table_schema', 'ops.table_content', 'ops.filter_dedup', 'ops.mapping_matcher', 'ops.aggregator', 'ops.exporter', 'ops.step_executor', 'openpyxl', 'PyQt5.sip']` — 动态导入的模块，运行时 ImportError 的首要排查点。<!-- 同步更新 2026-08-24: v3.1 口径——原清单 ['steps','openpyxl','pptx','PyQt5.sip'] 为 v3 旧值；v3.1 操作函数层（ops/）为动态引用面（engine.registry / gui.app 经跨包引用），需显式声明 ops 包全部模块以保证 BUILTIN_OPS 完整打包；另含 paths（运行环境自适应路径解析，部分模块延迟 import）。与 RPA_Workflow_v3.spec L27-L53 实测一致 -->
- **icon**：`None` — 应用图标路径，项目暂无 ico 文件，PyInstaller 使用默认图标
- **name**：`'RPA_Workflow_v3'` — 输出文件名
- **onefile / windowed**：`True / True`（`console=False`）— 单文件模式 + GUI 无控制台窗口，切换需充分测试
- **upx**：`False` — 不启用 UPX 压缩（降低杀软误报概率）
- **workpath / distpath**：由 build.bat 命令行参数覆盖（不使用 `--specpath`），spec 内不硬编码输出路径

### 1.8 修改红线

| ✅ 允许 agent 自主修改 | ❌ 禁止 agent 自主修改（需人工确认） |
|------------------------|-------------------------------------|
| hiddenimports 增删（修复 ImportError） | 入口文件路径变更 |
| datas 新增项目内资源目录 | onefile ↔ onedir 模式切换 |
| pathex 新增项目内模块路径 | windowed 改为 console（影响用户体验） |
| icon 路径修正 | 删除任何现有 datas/hiddenimports 条目 |
| 注释补充与格式整理 | 修改 Analysis() 的 excludes 白名单 |

> 原则：**只增不删、只修不改核心**。任何涉及"删除现有配置"或"切换打包模式"
> 的操作，必须在输出中明确标注 `[REQUIRES_HUMAN_CONFIRMATION]` 并暂停等待确认。

### 1.9 重建流程

当 spec 文件丢失或损坏时，agent 应按以下顺序重建：

1. **无法从 git 恢复（2026-10-24 更正）**：`RPA_Workflow_v3.spec` 被根 `.gitignore` 的 `*.spec` 规则忽略，**不在版本库中**（`git ls-files` 无记录），因此原"`git checkout HEAD -- v3/RPA_Workflow_v3.spec`"路径不可用
2. 由**人工**按本节 §1.7「关键配置项含义」中的值重建 spec，或取人工备份恢复；spec 的写入属人工职责（Git 写操作亦一律人工执行）
3. 重建后必须执行一次试编译验证（`pyinstaller --dry-run` 或实际编译）

### 1.10 构建产物有效性判定

> 承接自 `AGENTS.md` §8（2026-09-13 精简下沉）；本节是编译侧判据的权威载体。

- **判据（长期有效）**：`.exe` 的有效性取决于**最后一次源码改动**——即 `rpa_engine/**`、`RPA_Workflow_v3.spec`、`build.bat`；仅规约/方案文档（`AGENTS.md`、`docs/`、`knowledge/`、`README.md`）变更**不影响** exe 有效性
- **指纹判据（R6/C1-P0-3，2026-09-24 起的新构建适用）**：`BUILD_INFO.txt` 的 `SOURCE_HASH`＝源码指纹（`tools/make_fingerprint.py` 生成：`rpa_engine/**/*.py` 按相对路径排序、逐文件 sha256（路径+内容）串联后再 sha256 取前 16 位）；交付/验收前重跑该脚本比对——与包内 `BUILD_INFO.txt` 一致→包与源码同版；不一致或缺字段（历史包）→按上条判据判定失效。辅助字段：`GIT_REV`（git 不可用时 N/A）、`TESTS_SKIPPED`（1＝经 `--skip-tests` 打包，需人工审查）。GUI 标题栏"关于"按钮展示同一指纹（frozen 态读同目录 BUILD_INFO）
- **当前状态（2026-10-24 实测）**：`build/RPA_Workflow_v3.exe`（2026-10-19 03:57 构建）**有效**——`BUILD_INFO.txt` 记 `SOURCE_HASH=9fc85bc09ac1376a`，与事实基线采集时（2026-10-24 16:33）对当时工作区源码重算的结果**一致**（`FILES=56`），`TESTS_SKIPPED=0`（未跳过测试门禁）→ 包与源码同版。**W-20 已关闭**。`GIT_REV` 为构建时 HEAD（`bd01716`），现 HEAD 已前进（`703c67e`），**判定一律以 `SOURCE_HASH` 为准**，`GIT_REV` 仅辅助追溯。
  - **复核提示（2026-10-24 R16 收口）**：本轮曾改动 `rpa_engine/tests/__init__.py` 的 docstring（纯注释、零逻辑），该文件在指纹计算范围内，会使 `SOURCE_HASH` 变化；为守住「零源码改动 + exe 有效」两条不变量，**该文件已回滚至原状**，指纹复测仍为 `9fc85bc09ac1376a`（FILES=56）。docstring 与实际 15 个测试文件的描述偏差登记为 W-25，待下次构建窗口一并修正并重建 exe。交付前应以最终源码重跑 `tools/make_fingerprint.py` 与 `BUILD_INFO.txt` 比对。 <!-- 2026-10-24 取代原「截至 2026-09-14 已失效」时点快照；历史：2026-08-31 22:33 构建的旧包因 2026-09-13 W-18 代码清理而失效，另存在 2026-09-24 05:32 构建记录（历史包无 SOURCE_HASH 字段，指纹判据仅对 R6 后新构建生效） -->
- **构建由人工接管（R2，2026-09-14）**：Agent 不执行 build.bat、不修改 `build/` 产物；重建须由人工在真机会话基于 conda 环境 `CPS-GPES_RPA-py311`（路径见 `docs/runtime-env-spec.md` §2）执行
- **重建要求**：源码变更后（尤其 M0 及以后的 DAG 重构编码）须按本文档 §1.9 / §2 重建，并核对 `BUILD_INFO.txt` 的构建时间与产物路径
- **时点提示**：带日期戳的条目属**时点快照**，非长期约束；判据条目为长期有效

---

## 2. build.bat 参数体系

### 2.1 用法

```
build.bat [--build-dir <路径>] [--output <路径>] [--clean]
```

### 2.2 参数说明

| 参数 | 用途 | 默认值 |
|------|------|--------|
| `--build-dir <路径>` | 中间产物根目录（work/dist 子目录均在此下） | `%~dp0build` |
| `--output <路径>` | 最终 .exe 额外复制目标（目录或文件路径） | 无（不额外复制） |
| `--clean` | 编译成功后清理 build\ 内除 .exe 外的中间产物 | 0（不清理） |

### 2.3 向后兼容

裸路径参数（无 `--` 前缀）自动识别为 `--output`，并输出兼容提示。

---

## 3. 中间产物结构

```
build\
├── work\          ← PyInstaller --workpath（编译中间文件）
├── dist\          ← PyInstaller --distpath（编译产物 .exe）
├── RPA_Workflow_v3.exe   ← 最终交付（从 dist\ 复制）
├── BUILD_INFO.txt        ← 构建信息
├── backup\               ← 旧 exe 构建备份（build.bat 原子发布留存，RPA_Workflow_v3_<时间戳>.exe）
└── workspace\ logs\ storage\ temp\ templates\   ← 用户数据/运行目录（构建脚本保护，不删除；若存在）
```

> **2026-10-24 注记**：`backup/` 为 `build/` 下的**构建备份目录**（存历史 exe，非程序运行目录）；`build.bat` 保护 `build/` 下 `workspace/logs/storage/temp/backup` 五个目录（若存在）及已发布 exe。程序运行期实际创建的 4 个数据目录为 `workspace/`、`logs/`、`storage/`、`temp/`（另 `templates/user/`）。
