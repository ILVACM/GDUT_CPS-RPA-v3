# 任务记录：代码整理 —— CLI 清理（W-18）+ 其余部分梳理（DAG 可视化除外）

## 摘要
- **任务目标**：移除 `rpa_engine/main.py` 的 CLI 交互代码（argparse / run_workflow / `_setup_logging` / CLI 分支），删除 `steps/` 死代码目录，修正旁涉注释与文档口径；GUI 为唯一交互入口
- **任务状态**：✅ 已完成
- **开始时间**：2026-09-13 17:28 (UTC+8)
- **最后更新**：2026-09-13
- **要点摘要**：main.py 瘦身完成（CLI 全删，4,489 → 546 B，GUI 薄壳）；steps/ 死代码目录物理删除；旁涉注释与 9 处文档口径同步；验收 A1/A4/A5/A6 通过、A2/A3 环境受限降级（移交真机）、A7/A8 移交人工（W-20）；Reviewer/Auditor 双独立复核通过；exe 已失效待人工重建
- **操作人**：黄泊凯

## 用户输入

> "整理现有代码：除 GUI 交互部分中的 DAG 可视化外，对其余部分（尤其重点清理 CLI 相关代码）进行梳理与优化。请先制定整理计划，明确涉及的模块、清理范围、潜在风险与验证方式，待人工确认合理后再执行。"

> 后续指令："计划确认，执行"（4 项决策点全部采纳推荐项）

## Agent 理解与决策

**边界（依约束一「ETL 架构刚性」）**：本轮"优化"= **删除死代码 + 修正注释/文档口径**，**不做任何功能性重构、性能优化、接口重设计**——`engine/` 与 `ops/` 的逻辑一行不改（唯一例外：`executor.py:41` 一句 docstring）；DAG 可视化相关全部不动。

**取证结论（2 个只读探查代理，均有 文件:行号）**：
- `run_workflow` / `argparse` 在 `rpa_engine/**` 生产代码中**零外部调用方**（仅 `main.py` 自身 :40 定义 + :126 自调用）
- `gui/app.py` 完全自足（自带 `_setup_gui_logging` :167-177、自检 :199、Qt 初始化 :211），**不 import main 任何符号** → 删 CLI 对 GUI 零影响
- `_setup_logging` 仅被 `run_workflow:60` 调用，可随删，无需搬迁
- `main.py` **文件必须保留**——PyInstaller 打包入口薄壳（`spec:13` 明示 `app.py` 无 `__main__` 守卫）；瘦身后退化为 `main()` 调 `launch_gui()`
- `steps/` 为**纯死代码**：生产代码零 import；7 个业务文件引用的 `register_step` 已不存在，**物理上不可加载**
- 纠偏：`_select_step`(:345) / `_harvest_current_form`(:359) 是**活跃** GUI 表单收拢机制，**不可删**；`parser.py` 5 处 v3 字样是 D4 决策的有意报错口径，**不清理**

**决策（D1~D4 全部按推荐）**：D1 steps/ 物理删除 + 同步 6 处文档（git 历史可回溯）｜D2 本轮尝试重建 exe（不可行登记 W-20）｜D3 含文档杂项（目录树补 `paths.py`、模板路径订正、根 `.gitignore:43` 格式修正）｜D4 真机 GUI 启动验收移交人工、不阻塞关闭

## 执行流程

### 流程概览
- 总步骤数：8
- 多 Agent 协作：是（编码类角色集：Coder=主 Agent 亲写 / Reviewer / Tester；文档阶段切构建类 + Auditor）

### 步骤记录

#### Step 1: 备份受控文件并新建本记录
- 状态：✅ 已完成
- 执行内容：13 个文件 + `steps/` 整目录 + 根 `.gitignore` 备份至 `_temp/BackUp/*.bak-20260913-pre-cleanup`；按 `TEMPLATE.md` 新建本记录（先有后写）
- 涉及文件：`_temp/BackUp/*`（13 + steps 目录 + 1）

#### Step 2: 编码（Coder=主 Agent 亲写）
- 状态：✅ 已完成
- 执行内容：
  - `rpa_engine/main.py` 整体重写为 GUI 薄壳（删 `argparse`/`run_workflow`/`_setup_logging`/CLI 分支；保留 `__main__` 守卫 + `main()` 调 `launch_gui()`）；4,489 → 546 B
  - `rpa_engine/steps/` 整目录物理删除（9 个 .py + `__pycache__`）
  - `engine/executor.py:41` 删 1 行 docstring（Reviewer 复核：其余逐字节一致）
  - `gui/main_window.py:368` 注释改为"（与引擎 execute_workflow 同一链路）"
  - `RPA_Workflow_v3.spec` :12-14/:17 注释改口径（`hiddenimports` 未动）
- 涉及文件：5 项（见下表）

#### Step 3: Tester 验收（子 Agent，只读）
- 状态：✅ 已完成
- 执行内容：环境探测（两可用解释器均缺 pandas/loguru/openpyxl/PyQt5；项目专用 conda 环境 `CPS-GPES_RPA-py311` **不存在**）→ A1 全 35 个 .py 语法 OK；A2/A3 依 §8 条 7 **降级移交**（环境缺依赖）；A4 静态复核三项全零（CLI 残留=0、steps 导入残留=0、活跃代码清单未触碰）
- 复验：测试全程无写盘（`compile()` 替代 `py_compile` 避免 .pyc）

#### Step 4: Reviewer 复核（子 Agent，只读）
- 状态：✅ 已完成
- 执行内容：R1~R5 全过——executor/main_window/spec 与备份逐字节级吻合（仅预期改动）；steps/ 删除完整无残留引用；`engine/`、`ops/` 逻辑与 DAG 可视化冻结文件（`node_graph.py`/`models.py`/`page_operation_config.py`）零改动；四条架构边界未触碰；活跃函数未误删
- 结论：可按预期放行

#### Step 5: 文档同步（主 Agent，两批）
- 状态：✅ 已完成
- 执行内容：
  - `docs/architecture.md`：:192 CLI 口径、:205 steps/ 删除注记、:273 层级表、头部最后更新
  - `docs/dev-spec.md`：:107 日志总则入口口径（`main.py` 已无 `_setup_logging`）、:355/:357 正例路径标注"已删除"、:537 入口行、变更记录追加
  - `README.md`：:21 CLI 已移除、:28 结构概览 steps/ 注记（**Auditor 阻断项**）
  - `rpa_engine/README.md`：调试入口小节收口为"已移除"（**保留历史命令**）、目录树补 `paths.py`、steps/ 行、:121 模板路径订正 `workspace/user_templates/`→`templates/user`、:38 注释时态（**Auditor 建议项**）
  - `RPA_Workflow_v3.spec` :17 去 steps；`rpa_engine/templates/README.md` 归档表述；`../.gitignore:43` 中文说明行改注释（D3）
  - `docs/backlog.md`：W-18 → ✅ 已完成；新增 **W-20**（exe 重建，沙箱无项目 conda 环境，移交人工）；W-08 注记"前提失效"；§5 统计与建议顺序同步

#### Step 6: Auditor 全局校验（子 Agent，只读）+ 阻断修正
- 状态：✅ 已完成
- 执行内容：按 `doc-governance.md` §4 分步执行 → Step 1/2 全过、Step 3 因 **1 项阻断**（`README.md:28` 结构概览仍列 steps/ 为现存组成）未过；当场修正该阻断 + 1 项建议（`rpa_engine/README.md:38` 注释时态）后复验通过
- 五项校验：链接 45 篇真断链 0；元信息合规；层级一致；INDEX 同步（10 篇）；约束力合规（steps/ 专项排查：`steps[]` 字段与 `steps/` 目录区分无误判）

#### Step 7: exe 重建评估（D2）
- 状态：✅ 已完成（按降级路径处理）
- 执行内容：环境探测确认沙箱无项目 conda 环境（`CPS-GPES_RPA-py311` 不存在）→ 按 D2 既定降级路径**登记 W-20**（移交人工），并在 `AGENTS.md` §8 标注 exe 已失效；未强行执行 build.bat

#### Step 8: 锚点收尾
- 状态：✅ 已完成
- 执行内容：锚点层状态 `执行中` → `已完成`，要点摘要回填实测结果；AGENTS.md 终值含 CR 7,760（余量 240，满足 §10）

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 备份 | `_temp/BackUp/*.bak-20260913-pre-cleanup`（13 个 + `steps/` 目录 + 根 `.gitignore`） | 执行前快照 |
| 新建 | `docs/task-records/2026-09-13-code-cleanup.md` | 本记录 |
| 新建 | `_temp/verify-code-cleanup.md` | 验收与全局校验报告 |
| 重写 | `rpa_engine/main.py` | CLI 全删，瘦身为 GUI 薄壳（4,489 → 546 B） |
| 删除 | `rpa_engine/steps/`（9 个 .py + `__pycache__`） | 纯死代码目录（生产代码零引用） |
| 修改 | `rpa_engine/engine/executor.py` | :41 删 1 行 docstring（其余逐字节一致） |
| 修改 | `rpa_engine/gui/main_window.py` | :368 改 1 行注释 |
| 修改 | `RPA_Workflow_v3.spec` | :12-14/:17 注释改（hiddenimports 未动） |
| 修改 | `README.md` | :21 CLI 已移除；:28 结构概览 steps/ 注记 |
| 修改 | `rpa_engine/README.md` | 调试入口小节收口、目录树补 paths.py、steps/ 行、:121 模板路径订正、:38 时态 |
| 修改 | `docs/dev-spec.md` | :107 日志总则、:355/:357、:537、变更记录 |
| 修改 | `docs/architecture.md` | :192、:205、:273、头部 |
| 修改 | `docs/backlog.md` | W-18 完成、W-20 新增、W-08 注记、§5 统计/顺序 |
| 修改 | `rpa_engine/templates/README.md` | 归档表述 |
| 修改 | `../.gitignore` | :43 中文说明行改注释（D3） |
| **规约同步**（`doc-governance.md` §7 检查清单） | ① 命中（删 `steps/` 包目录）→ architecture §3.4/层级表、dev-spec 2 处、README 目录树、spec:17、templates/README 已同步；② 命中（`main.py` 入口行为变化）→ rpa_engine/README、README、architecture:192 已同步；③ 未命中（GUI 页面零改动）；4 项清单逐项过 | 无 `[待补充]` 遗留 |

## 验收（依 doc-governance §8 强制要求）

> 声明：本仓库当前无可复现的自动化回归套件（测试按 `docs/architecture.md` §9 #4 暂缓）；`_temp/` 历史脚本仅在**重跑并留痕**后作证据。

| # | 验收条目 | 方式 | 通过判据 | 结果 |
|---|----------|------|----------|------|
| A1 | 语法完整性 | `py_compile` 全部存活模块 | 全部 OK | ✅ 通过（35/35 个 .py OK，0 FAIL；用 `compile()` 零写盘） |
| A2 | 导入冒烟 | 依次 import engine / ops 各模块 / `gui.app`（不实例化 QApplication） | 全部无异常 | ⚠️ 降级（本机缺 pandas/loguru/openpyxl/PyQt5，移交真机环境执行） |
| A3 | 引擎侧功能回归 | 重跑 `_temp/engine-smoke-test.py`，留痕 `_temp/verify-code-cleanup.md` | 与历史口径一致，无 FAIL | ⚠️ 降级（同上，环境缺依赖，移交真机） |
| A4 | 静态复核（grep） | ① 生产代码 `argparse`/`--cli`/`run_workflow`/`_setup_logging` 残留=0 ② `from steps`/`import steps` 残留=0 ③ 活跃代码清单未被触碰 | 三项全零 | ✅ 通过（三项全零；`gui/app.py:211` 的 `sys.argv` 仅供 Qt 初始化，点名不算残留） |
| A5 | 规约同步（§7 检查清单） | 三类触发逐类判定 + 4 项清单 + 本节含「规约同步」行 | 逐项确认留痕 | ✅ 通过（①②命中并已同步、③未命中；4 项清单逐项过，「规约同步」行见上表） |
| A6 | 全局更新校验 | `doc-governance.md` §4 三步 + 五项 | 全过 | ✅ 通过（Auditor 独立执行；1 项阻断已当场修正后复验通过） |
| A7 | 真机 GUI 启动（人工） | 移交用户：`python rpa_engine/main.py`（或重建后的 exe）应直接进入四阶段 GUI | 移交人工 | 移交（待真机确认） |
| A8 | exe 重建 | 运行 `build.bat`，核对 `BUILD_INFO.txt` 时间戳；沙箱不可行则登记 W-20 | 产出新 exe 或登记 | 移交人工（沙箱无项目 conda 环境，已登记 W-20） |

## 关闭标识
- **完成时间**：2026-09-13 17:45 (UTC+8)
- **最终状态**：✅ 全部完成
- **关闭说明**：W-18 完成——`main.py` CLI 交互代码全部移除（GUI 薄壳）、`steps/` 死代码目录物理删除、旁涉注释与 9 处文档口径同步；验收 A1/A4/A5/A6 通过、A2/A3 依 §8 条 7 降级（环境缺依赖，移交真机）、A7/A8 为既定移交项（D2 已登记 W-20）；Reviewer 与 Auditor 双独立复核通过；exe（2026-08-31）已失效，待人工重建（W-20）。*注：A2/A3/A7/A8 均为"移交"而非"失败"，故依 §8 条 4 本任务可按"全部完成"关闭，移交项已在要点摘要与本节明列。*
