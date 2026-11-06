# plan.md — ImportData 导入链路修复施工图

> **2026-11-02 清理注记**：本任务已于 2026-10-19 收官（A 链 19 项 + B 链 13 项全部落地）。配套材料 `problem.md`、`backup/`（各批次改前快照）、`*_scenarios.py`（批次脚本化验收）、`*_artifacts/`（批次产物样例）、`p4~p6-subagent-report.md`、`plan.md.bak_v1/v2`、`lock_header.txt`、`probe_*.py` 已随本次 `_temp` 清理删除；**本文保留为 B 类 79 项台账证据**（被 `docs/backlog.md` 与 3 篇任务记录共 17 处引用）。正文中指向上述材料的行内引用为**历史指向**，删除清单见 `_temp/CLEANUP_MANIFEST-2026-11-02.md`。

> **性质**：本文件位于 `_temp/`，按 `AGENTS.md` §6 **无约束力**；是**施工图**而非规约。可被另一 Agent 直接执行。
> **问题来源（唯一）**：`_temp/ImportData/problem.md`（v8 定稿，959 行；A 类 19 条 / B 类 79 条 / 101 个原编号）
> **需求来源**：需求说明（R1~R7 共 7 条核心规则 ＋ H1~H10 共 10 条隐含处理项 ＋ 产物 1~4）
> **生成日期**：2026-10-17｜**依据**：problem.md 全文 ＋ 导入链路三层源码一手复核
> **本文件不做任何事**：不含代码实现动作、不编译、不运行、不安装。它只描述"改哪个文件的哪一行、改前改后是什么"。
> **2026-10-18 决策确认**：① G-5 裁定（§1.6）已按人工审核通过，保持 agent 已有处理不变；② B-49 默认口径采用"抛中文错误"（不再静默改写后缀），保持现状不变。

---

## Part 0 · 计划概览

### 0.0 本轮施工范围速查（2026-10-19）

| 项目 | 内容 |
|---|---|
| 本轮做什么 | ① 修正本文件的计数/分类/噪音不一致 ② 产出干净可执行的施工依据，为 B 类代码修改做准备 |
| 本轮不做什么 | ① **不动源码**（零代码）② 不动 GUI 布局 ③ 不动引擎调度 ④ 不引入新依赖 ⑤ 不做真机验证 |
| 需人工拍板 | ① **B-49 已裁定本轮不施工** ② 其余无（三点遗留决策已于 10-18 落定） |
| 施工依据 | 本文件为唯一施工依据；`AGENTS.md` 为约束层 |
| 硬约束红线 | 不改函数签名／不引入新依赖／路径用相对路径／`git` 人工接管（`AGENTS.md` §1） |
| **本轮可施工** | **13 项**：`B-01`／`B-02`／`B-13`／`B-14`／`B-15`／`B-16`／`B-21`／`B-28`／`B-31`／`B-33`／`B-39`／`B-42`／`B-43` |
| 台账 | Part 3 头部《B 类分类台账》79 行 = 机读分类唯一出处 |

### 0.1 本次范围（**不可突破**）

| | 内容 |
|---|---|
| ✅ **做** | ① 新建 Excel 规范化预处理模块 ② 接入「确认并导入」链路 ③ 导入链路的既存缺陷修复（problem.md 的 A 类 19 条）④ **不解决就跑不通**的 B 类阻塞项（problem.md 的 B 类 79 条中本次可施工者） |
| ❌ **不做** | 引擎调度逻辑（`engine/executor.py` 的步骤分发、信号定义、线程模型）；GUI 布局（仅允许在「确认并导入」槽函数内增加错误回显）；步骤功能函数实现（Layer 2/Layer 3，即 `ops/` 下的 9 项 BUILTIN_OPS 行为）；引入任何新的第三方依赖；`eval`/`exec`/`pickle` |
| **本轮修订（2026-10-18）** | ① 确认 G-5 裁定（§1.6）不变 ② 确认 B-49 口径不变 ③ 全文一致性校对（B-45~B-49 概要完整性、文件清单计数、UNVERIFIED 占位清单、闭合表、多 Agent 标记统一、批次归属一致性） ④ 头部追加决策确认注释 |

### 0.2 硬约束（施工时必须逐条遵守）

1. **不引入新依赖**：仅允许使用 `pandas`／`openpyxl`／`xlrd`／`loguru`／`psutil`／`PyQt5`（已在 `requirements.txt`）。**win32com 不在允许清单内**（见 `REQ-R4` 的降级设计）。
2. **不改既有函数签名／返回值结构／异常约定**（除本计划明确要求者）：`excel_preprocessor.validate_and_copy/ensure_xlsx/scan_sheets/read_excel_sheet`、`table_importer.import_excel_table`、`sqlite_manager.import_dataframe` 的签名与返回值**保持不变**。
3. **步骤不得自建 SQLite 连接**（`AGENTS.md` §2.2 条 4）：新建模块只接收调用方传入的 `conn`，**不得**创建连接。
4. **路径全部用项目相对路径**：本文件内不得出现 `D:\`、`C:\` 绝对路径。
5. **不硬编码业务逻辑**（§2.2 条 1）：不得在代码里写死列名、表名、具体业务规则；阈值（如 5 位有效数字）走可配置项。
6. **内存安全**（§2.1 条 5）：16GB 目标机，`pandas` 峰值须受控；大表不得在内存里产生两份以上全量副本。
7. **改代码时若发现注释与实际行为不符，须一并更正**（problem.md 附录 C · 裁定 G14）。
8. **git 由人工接管**，Agent 不执行任何 git 写操作（`AGENTS.md` §1）。

### 0.2.1 执行须知（全局，优先级等同硬约束）

> **执行须知：本计划中所有"改前/改后"代码片段均为语义示意**，用于说明修改意图和逻辑方向。实际实施时，必须以本地源码的真实内容为准进行等价替换，**不得进行机械式文本匹配**（如全文搜索替换）。若代码风格（缩进、空行、注释）与示意不一致，**以实际源码风格为准**。

操作细则：

1. 任何"改前"片段若在源码中**找不到完全一致的文本**，**这不是缺陷**——按**语义等价**定位目标代码（例如函数名 + 行为特征）。
2. 若语义等价定位仍然失败，**不得猜测、不得硬改**，须输出 `[SUB_AGENT_BLOCKED]`（见 §0.8）并附：目标文件、意图、已尝试的定位方式、建议选项。
3. 本条的优先级**等同 §0.2 硬约束**：违反（例如用全文替换去机械匹配）即为执行错误。

### 0.3 前置条件（P-0 ／ P-1〔已解除〕／ P-2，开工前必须先满足）

| 编号 | 前置 | 为什么必须先做 | 完成判据 |
|---|---|---|---|
| **P-0** | **腾 `AGENTS.md` 容量** | 2026-10-17 实测：含 CR **7,728**／上限 8,000／余量 **272 字**（198 行／纯 CRLF）。本轮将产生新任务锚点（3~4 条要点，约 400+ 字），不腾则 `doc_verify` 门禁项（容量）必失败 | 下沉 3 处（`AGENTS.md` §2.6 功能函数指针压为 2 行；§5.4 已知阻塞摘要整段下沉 `docs/architecture.md` §9；§8 当前任务上下文两段并为 1 行）→ 腾出 ≥400 字 → 复测三口径（含 CR 字符数 ≤8,000、loneCR=0、loneLF=0） | **实测结果（2026-10-18，R11）**：下沉 2 处（§2.6 去重复枚举／§8 改写为 R11 上下文）＋删 4 处与链接文档重复的括注（§1／§2.3／§5.1／§5.4）→ 含 CR **7,622**／余量 **378**；`doc_verify` **PASS**（links=86，failures=0）；锚点已登记为 **R11**。**`[ADJUSTED-4]`**：原列的"§5.4 下沉"**不成立**（已是纯指针，无可下沉内容）；净腾 106 未达 ≥400 理想值，但满足硬门禁（≤8,000 且余量 ≥200）——详见 §0.7.1 |
| **P-1** | ~~**`G-5` 方案经人工裁定**~~ → **已解除（2026-10-18）** | **原门禁**：`A-15`（写库非原子）与 `A-16`（空壳表跳过补导）的修法须先出方案、人工裁定后才能实施（problem.md 附录 C · 裁定 Q2／附录 G 第 8 项：台账纪律 6 禁止 Agent 自行设计）。**解除依据**：2026-10-18 修订指令明确要求"自主裁定 `G-5` 并解除待裁定状态" → **本版 §1.6 已给出 `G-5` 三件套裁定（守卫 ＋ 原子写 ＋ 有效性判据）**，该门禁的立法对象（"无方案即施工"）已不成立。原裁定引用保留可溯 | **本版 §1.6 的 `G-5` 裁定即为结果** → `A-15`／`A-16` 已并入 **P4**（见 §1.1），可直接开工 |
| **P-2** | **exe 重建与 `.xls` 真机验证由人工执行** | 构建由人工接管（`AGENTS.md` §1 ＋ 裁定 R2）；Agent 不跑 `build.bat`、不修改 `build/` 产物 | 人工执行 `build.bat` → 用真实 `.xls` 验证导入链路 → 回填 `build/BUILD_INFO.txt` 指纹 |

### 0.4 术语

| 术语 | 含义 |
|---|---|
| **DEF-A** | 缺陷修复项，来源＝`problem.md` 的 A 类条目（导入链路阻断），**与 problem.md 1:1 闭合** |
| **DEF-B** | 缺陷处理项，来源＝`problem.md` 的 B 类条目（非导入范围但阻塞运行），**与 problem.md 1:1 闭合** |
| **REQ** | 规则落地项，来源＝**需求规则**（R1~R7 / H1~H10）中**在 problem.md 完全无对应编号**的缺失实现；单列并标注来源，**不计入 problem.md 闭合** |
| **三形态** | 功能函数的三形态一体：后端 Python 函数（`ops/`）／JSON 参数文件 `steps[]` 元素／前端 DAG 步骤节点（`docs/function-spec-rules.md` §0） |
| **Layer 0 / 1 / 2** | `Layer 0`＝基础设施（`ops/excel_preprocessor.py`、`ops/sqlite_manager.py`、`ops/session_db.py`）；`Layer 1`＝数据表导入（`ops/table_importer.py`）；`Layer 2`＝用户操作目录（`ops/` 的 9 项 BUILTIN_OPS） |
| **阻断等级** | 文件级（该文件整份中止）／表级（该 sheet 失败，其余表不受影响）／单元格级（该格数据错，表仍入库） |
| **判定四值** | `缺少容错`｜`逻辑错误`｜`缺失实现`｜`已废弃` |
| **占位标签** | `[UNVERIFIED]`＝本文件生成时未读到精确代码（须实施者补读）｜`[待裁定]`＝须人工先裁定｜`[REQUIRES_HUMAN_CONFIRMATION]` |
| **`t_{uid}` / `t_s{n}`** | GUI 编辑态固化的派生表物理名（`gui/models.py`）／`step_executor` 的缺省回退名（`ops/step_executor.py L205-207`） |

### 0.5 改造项总清单与计数规则

| 类型 | 数量 | 来源 | 与 problem.md 的闭合要求 |
|---|---|---|---|
| **DEF-A** | **19** | problem.md A 类 19 条（覆盖 21 个原编号） | 1:1 闭合（见 Part 6 闭合表） |
| **DEF-B** | **79** | problem.md B 类 79 条（覆盖 80 个原编号） | 1:1 闭合（见 Part 6 闭合表） |
| **REQ** | **12** | 需求规则 R1~R7 / H1~H10 中**无 problem.md 编号**的缺失实现 | 单列；**不参与** problem.md 闭合计数 |
| **合计** | **110** | — | — |

**REQ 判定规则（用于消除「plan.md 不得出现 problem.md 之外的新问题」的字面冲突）**

- **规则一**：若某需求规则的实现**恰好由某个 A 类条目的修复完成**（即两者改动点为同一处），则**不单列 REQ 项**，只在该 A 条目的「对应规则」字段标注；
- **规则二**：若某需求规则**在 problem.md 中完全没有任何编号**（既非缺陷条目、也不被任何 A 类条目覆盖），则**单列** `REQ-??`，并在本节声明其「来源＝需求说明的规则编号」，**明确不是新增问题**。

**据此得到的 12 项 REQ**：`REQ-R2`（指定表头行全空则拒绝并提示）、`REQ-R4`（公式兜底求值）、`REQ-R5`（超链接展开为地址文本）、`REQ-R7`（trim 与 `\x00` 清洗、空值口径）、`REQ-H1`（重复列名去重并报告）、`REQ-H3`（布尔值→1/0 ＋ 元数据标记）、`REQ-H4`（错误值→NULL ＋ 原文留痕）、`REQ-H5`（全空列保留但标记／尾部全空行裁剪）、`REQ-H6`（图片/图表/批注丢弃并告知）、`REQ-H7`（超长数字精度扫描期提示）、`REQ-H9`（元数据表 ＋ 规范化处理报告 ＋ 失败清单落盘）、`REQ-H10`（`temp/normalized/` 幂等与目录管理）。

**不单列 REQ 的规则及其承接条目**：`R1`→`A-02`／`A-17`；`R3`→`A-05`；`R6`→`A-04`；`H2`→`A-06`／`A-07`；`H8`→`A-09`；`R4` 的 COM 分支→见 `REQ-R4` 的降级设计（不单独成项）。

**已合并项声明（原编号保留可溯）**：`J-03` 并入 `A-02`；`B-01` 并入 `A-17`；`G-07` 并入 `B-12`。同一对改动点被多个条目引用时，在相应条目「修改方案」中注明「见 XX 项，本项不另设改动点」。

### 0.6 本文件与 problem.md 的对应方式

- **DEF-A / DEF-B**：本文件 Part 2／Part 3 的每个条目**逐字沿用 problem.md 的编号与标题要点**，并补齐七段式（定位／现状／修改方案／约束／验证／风险回滚／验收标准）。Part 6 闭合表给出 `problem.md 编号 ↔ 本文件条目` 的一一对应。
- **REQ**：Part 2′ 单列，Part 6 闭合表标注「来源＝需求规则，非 problem.md 条目」。
- **冲突以代码为准**：若某条目在施工时发现与本文件记载不符，以实际代码为准并回报（problem.md 附录 G 第 4 项）。

### 0.7 `[UNVERIFIED]` 占位清单与处理优先级

> **用途**：把全文散落的 `[UNVERIFIED]` 占位**集中成一张按优先级排的待核实清单**，使各 Sub-Agent 在动手前先清掉自己那批的占位。
> **与 §6.4 的关系**：本节是**优先级视图**（看"谁必须先核实什么"）；§6.4 是**补读明细**（含"需人工/实施者提供"的完整措辞）。两节行数一致（**各 20 行**）。
> **优先级判定规则**：① 位于 **P0 批次**条目内 → **P0（最高）**；② 位于其余**本轮施工**条目内 → **P1**；③ 位于**本轮不施工**条目（P2/P3）或仅影响验证 → **P2**。
> **计数口径**：本表与 §6.4 均为**汇总条目数（各 20 条）**；正文中另有 **28 处**对同一批占位的引用（各条目正文标注、§0.2.1／§1.5／§6.2 的引用），故全文 `[UNVERIFIED]` 字样出现次数为 **48**。不变量应为「**§0.7 行数 ＝ §6.4 行数**」（当前均 20），而非与全文出现次数相等。

| 编号 | 所在位置（条目） | 占位内容摘要 | 优先级 | 建议人工/实施者提供 |
|---|---|---|---|---|
| 1 | `A-01` §4 | `engine/executor.py` L40-68 的 `_IMPORT_ROOTS` 与 `_validate_import_path` 语义 | **P0** | 读该段后确认：`source_path` 所在目录是否被允许；若不允许，须在 GUI 侧补等价校验或调整白名单 |
| 2 | `A-10` 改动点 3 | `gui/models.py::to_dict` 内 `source.file` 构造的**实际行号** | **P0** | 读 L650-720 定位赋值行 |
| 3 | `A-14` 改动点 2 | `gui/app.py` L1-40 的 import 区 ＋ `sys.excepthook` 注册处行号 | **P0** | 读后确认无循环导入风险 |
| 4 | `B-05` 改动点 1 | 终止按钮的控件名与"不支持中断集合"的判定位置 | **P0** | 读 GUI 终止相关代码 |
| 5 | `B-06` 改动点 1 | `EngineWorker` 的构造点（parent 传参处） | **P0** | 读 `main_window.py` 构造段 |
| 6 | `B-07` 改动点 1 | `MainWindow.start_workflow` 的精确行号（v7 记载 L539-547） | **P0** | 读该函数头 |
| 7 | `B-11` 改动点 1 | 四处 `_ignore_next_finish` 置位点的精确行号与分支结构 | **P0** | 读四处上下文 |
| 8 | `B-13` 改动点 1 | `gui/app.py::run_self_check` 中比对 `catalog_keys` 的精确行号（v7 记载 L185-188） | **P0** | 读自检函数 |
| 9 | `A-16` 改动点 1 | `engine/executor.py` 引入 `table_row_count` 是否造成循环导入 | P1 | 实测导入链 |
| 10 | `B-15` 改动点 1/2 | 新增步骤插入点与收拢逻辑的精确行号（v7 记载 L501-513／L674-698／L477-480） | P1 | 读 `page_operation_config.py` 对应段 |
| 11 | `B-17` 改动点 1 | 六处收拢调用点与两处遗漏点的精确行号（v7 记载 L157／L299 与 L652/660/519/541/616/998） | P1 | 读全文定位 |
| 12 | `B-21` 改动点 1 | `gui/graph_edges.py` dangling 判定的精确行号（v7 记载 L203） | P1 | 读该函数 |
| 13 | `B-22` 改动点 1 | 模板载入保留 `step_id` 的精确位置 | P1 | 读 `models.py` 模板路径 |
| 14 | `B-26` 改动点 2 | `engine/executor.py` 重试分支的精确行号（v7 记载 L279-282） | P1 | 读 `_execute_with_retry` |
| 15 | `B-39` | `engine/parser.py` 版本经 `str()` 归一比较的**实际实现行**（v7 记载 L124） | P1 | 读 L118-133 |
| 16 | `B-04`／`B-41`／`B-59` | `step_executor.py` L188-200 的 `global_config` 获取方式与参数白名单实现 | P1 | 读该段 |
| 17 | `B-47` | `gui/user_template_manager.py` 保存路径的精确行号（v7 记载 `:509-531`／`save:230-234`） | P2 | 读该文件（该条目本轮不施工） |
| 18 | `REQ-H6` | openpyxl 只读模式下 `ws._images`／`ws._charts`／批注的**可用性** | P2 | 实测探测 |
| 19 | `REQ-H10` 改动点 1 | `rpa_engine/paths.py` 既有函数命名与风格 | P2 | 读 `paths.py` 全文 |
| 20 | Qt 行为类（`G-04`／`G-05`／`G-11`／`H-04b`／`H-25`） | 实机行为（problem.md 亦标 `[UNVERIFIED]`） | P2 | **须人工验证（Agent 不可执行）**；位置＝Part 5 **§5.2**（场景矩阵） |

**处置规则**：实施者在动工前补读上表，把结果回填到对应条目；**未回填不得声称该条已完成**。

### 0.7.1 P0 级占位核实结果（R11 施工轮，2026-10-18）

> **性质**：本小节是 §1.5「P0 批次动手前核实义务」的**履行记录**——**8 项 P0 级占位已全部核实**；正文条目内的 `[UNVERIFIED]` 标记**以本小节结论为准**（施工时按此实施，**无需再回读源码**）。

| # | 条目 | 核实结论（实测行号） |
|---|---|---|
| 1 | `A-01` | `engine/executor.py` **L42-44** 的 `_IMPORT_ROOTS` **仅含 `temp/input_selection`**；`_validate_import_path`（**L54-68**）对该目录外一律抛 `ParserError`；仅由 `ensure_input_tables` **L105** 调用；**L47-51** 已有 `register_import_root()` 现成钩子 |
| 2 | `A-10` | `gui/models.py::WorkflowModel.to_dict` 的 `source.file` 赋值在 **L756-757**（`"source": {"file": t.file_path, ...}`）；`TableEntry` 字段定义在 **L293-303**（**无 `source_path` 字段**）；透传链＝`set_tables` **L341**／`apply_registry` **L362**／`load_from_dict` **L855** |
| 3 | `A-14` | `gui/app.py` **L10-21** 为 import 区（标准库＋`loguru`＋`engine.registry`＋`paths`）；`error_messages` 仅依赖 `paths` → **函数内导入无循环风险** |
| 4 | `B-05` | 终止按钮**不在 `main_window.py`**，而在 **`gui/page_progress.py`**：`self._abort_btn = QPushButton("终止操作")`（**L46-47**）、`set_enabled(on)`（**L103-104**）、`reset_all()`（**L95**）；信号 `abort_clicked` → `main_window.py` **L550** |
| 5 | `B-06` | `EngineWorker()` 构造点在 **`gui/main_window.py` L157**（`self.worker = EngineWorker()`）→ 改为 `EngineWorker(self)` 即建立父子绑定 |
| 6 | `B-07` | `MainWindow.start_workflow` 位于 **L480**；四处 `request_cancel` 在 **L250／L415／L429／L445** |
| 7 | `B-11` | 四处 `_ignore_next_finish` 置位点＝**L249-254／L414-418／L428-433／L444-448**（均在 `if self.worker.isRunning():` 内）；消费点在 **L584-585** |
| 8 | `B-13` | `gui/app.py` **L186** `if main_set | more_set != catalog_keys:` 用的是**未过滤弃用**的 `catalog_keys`（**L146** 同款）；`models.main_buttons()` 在 **L127**（已过滤）→ 口径不一致，**B-13 成立** |

**`[ADJUSTED]` 记录（本轮实测修正，共 4 条）**

- **`[ADJUSTED-1]`（关键·跨条目耦合）`A-01` ＋ `A-10` ＋ 导入白名单**：两项落地后，阶段 3 兜底补导会在 `_validate_import_path` 处被拒——抛的是 `ParserError`，且**不属** L110 的捕获面 `(ValueError, FileNotFoundError)` → 会逃逸为 `failed`。
  **处置**：`A-01` 改动点 2 追加第 4 步——导入循环内对每个 `source_path` 的父目录调用 `engine.executor.register_import_root(Path(src).parent)`（复用 **L47-51** 现成钩子，**不新增白名单机制**）；`A-10` 改动点 3 须新增 `TableEntry.source_path` 字段并四处透传（见核实结论 2）。
- **`[ADJUSTED-2]` `B-05` 的 GUI 落点更正**：终止按钮控件＝`gui/page_progress.py::_abort_btn`（**L46-47**）＋`set_enabled`（**L103-104**），**不是** `main_window.py`。
- **`[ADJUSTED-3]` `B-33` 的异常类型**：`_validate_import_path` 抛的是 **`ParserError`**（非 `ValueError`）——其捕获面描述须按此校正。
- **`[ADJUSTED-4]` P-0 的下沉方案与实际不符**：§0.3 所列"§5.4 已知阻塞摘要整段下沉"**不成立**（实测 §5.4 已是两行纯指针，无可下沉内容）。实际下沉＝`§2.6` 去重复枚举 ＋ `§8` 改写为 R11 上下文 ＋ 删 `§1／§2.3／§5.1／§5.4` 中与链接文档重复的括注。
  **结果**：含 CR **7,622**／余量 **378**（原 7,728／272；净腾 **106**，未达 ≥400 理想值，但满足硬门禁"≤8,000 且余量 ≥200"）；`doc_verify` **PASS**（links=86，failures=0）；锚点已登记为 **R11**，详情层 `docs/task-records/2026-10-18-importdata-repair.md` 已建。

### 0.7.2 P0 批次施工记录（R11，2026-10-18 已落地）

> **状态**：✅ **7 项／18 处改动全部落地**；门禁全绿。本节为"已施工"的留痕，**供 P1~P6 的施工者参考现状**。

| 条目 | 落地改动（文件 · 位置） |
|---|---|
| `A-10` | `gui/page_input_selection.py::get_entries` 新增 `source_path` 键；`gui/models.py`：`TableEntry` 新增 `source_path` 字段 ＋ `set_tables` 透传 ＋ `to_dict` 改为 `(t.source_path or t.file_path)`；`gui/main_window.py` registry 补 `source_path` 键 |
| `A-19` | `gui/main_window.py` 身份比对改为**三元组**（局部函数 `_ident`＝文件名＋源路径＋sheet 名）＋ 弹窗文案补「来源路径或工作表与上次不同」 |
| `A-01` | 同一文件导入改 `src = e.get("source_path") or e["file_path"]` ＋ **`register_import_root(Path(src).parent)`**；`_close_session(clear_copies: bool = True)` 参数化；L257 调用改传 `clear_copies=False`（其余 4 处收尾路径保持 `True`） |
| `A-02` | `_on_add_files`：异常元组扩容为 `(FileNotFoundError, ValueError, PermissionError, ImportError, OSError, zipfile.BadZipFile)` ＋ 第 2 段 `except Exception` 兜底（记 `logger.exception`）＋ `finally` 复位 `_btn_import`；提示文案经 `translate_error`；文件头补 `import zipfile` 与 `translate_error` |
| `A-13` | `main_window.py` 失败清单改传 `f"{type(err).__name__}: {err}"`；`error_messages.py::_RULES` 新增 3 条（`modulenotfounderror`／`标识符包含禁止字符`／`文件不是 excel 格式`），置于特异规则区首 |
| `A-14` | `gui/app.py::_excepthook` 弹窗改为 `translate_error(...)` ＋ `log_hint()`（技术日志与 traceback **保留**） |
| `A-17` | `RPA_Workflow_v3.spec` 的 `hiddenimports` ＋`'xlrd'`／`'ops.excel_normalizer'`（各附注释）；`requirements.txt` 的 `xlrd` → `xlrd>=2.0` ＋ 来源注释 |

**`[ADJUSTED]` 落实记录（本批实际选用）**

- **`[ADJUSTED-5]` `A-10`**：采用 §3 改动点 3 的**首选路径**（新增 `TableEntry.source_path` 字段并四处透传），**未采用**"`main_window` 侧落盘前替换 `file` 字段"的备选。
- **`[ADJUSTED-6]` `A-01`**：采用 §3 改动点 3 的**备选路径**（`_close_session(clear_copies=…)` 参数化，把"清副本"从"确认导入前"推迟到"退出／换轮／中止"）——理由：避免"未选中行的副本被删 → 回阶段 1 预览失效"。
- **`[ADJUSTED-7]` `A-01` 的 GUI 侧校验**：以 `register_import_root()` 放行源目录实现，**未新增校验函数**（改动面最小、语义等价）。

**实测门禁证据（2026-10-18）**

| 门禁 | 实测 |
|---|---|
| `py_compile`（5 个 gui 文件） | 退出码 **0** |
| `unittest discover -s tests` | **Ran 118 tests — OK**（零回归，基线未降） |
| `smoke_m1m3.py` / `smoke_mb.py` | `SMOKE_ALL_OK`；退出码 **0 / 0** |
| 启动自检 `run_self_check` | `ok=True`，**6 项全 True** |
| 脚本化场景（`_temp/ImportData/verify_p0_scenarios.py`） | ① 3 条新话术规则均命中、未命中走兜底；② `source.file` 有源路径→**原始路径**、无→回落副本；③ `_validate_import_path` **未登记必拒（`ParserError`）／登记后放行**；④ 身份三元组"同一文件不误报／同名 sheet 换文件会提醒"；⑤ 0 字节 xlsx 抛 `BadZipFile`（**在新元组内**，且实测其**非** `OSError` 子类 → 显式列入是必需的） |

**挂起项（须人工／真机）**

- **`P-2`**：exe 重建 ＋ 真实 `.xls` 导入真机验证（`A-02`／`A-17` 的交付面）
- **S1 的真机 GUI 会话语义**：阶段 1→2 端到端（本批已用 `offscreen` ＋脚本覆盖核心机制；真机确认仍建议执行）

### 0.7.3 P1 批次施工记录（R11，2026-10-18 已落地）

> **状态**：✅ 3 项／6 处改动落地；门禁全绿。

| 条目 | 落地改动（文件 · 位置） |
|---|---|
| `A-11` | `ops/excel_preprocessor.py`：补 `import os`；`validate_and_copy` 的 `shutil.copy2` → **`shutil.copyfile` ＋ `os.utime(dst, None)`**（副本 mtime 归零）。`gui/main_window.py`：`cleanup_stale_files` 的超龄循环**加引用保护**（读 `workspace/last_config.json` 的 `tables[].source.file` 组成 `protected` 集合，命中即跳过删除；读取失败＝空集、行为同旧）；`__init__` 启动序**交换**为「先 `_restore_last_config()`、后 `_cleanup_stale_sessions()`」 |
| `A-12` | `validate_and_copy` 查重扩展为**跨后缀**（`while dst.exists() or (temp_path / f"{dst.stem}.xlsx").exists()`）；`ensure_xlsx` 转换产物**加序号查重**（`while new_path.exists(): new_path = src.with_name(f"{src.stem}_{counter}.xlsx")`） |
| `A-18` | **与 `A-12` 的 `ensure_xlsx` 改动为同一处**（该条目 §3 已注明），**无独立改动点** |

**`[ADJUSTED]` 记录（本轮新增）**

- **`[ADJUSTED-8]` 跨条目交互：`A-10`（P0 已落地）已消解 `A-11` 的主症状** —— `last_config` 的 `tables[].source.file` 现落**原始路径**，而超龄清理只清 `temp/input_selection` 下的**副本** → 「含早于 24h 的 `.xlsx` 时恢复 100% 失效」**不再复现**（恢复判据查的是原始文件）。
  **仍执行 `A-11` 三项的理由**：① `F1`（副本 mtime 归零）为**防御性**修正；② 引用保护 ＋ 启动序交换覆盖**迁移期**（`A-10` 之前落盘的旧 `last_config` 仍指向副本）；③ 成本极低。
- **`[ADJUSTED-9]` `A-18` 与 `A-12` 同处实现** —— 无独立改动点，共用验收用例（V3／V4）。
- **不变量已保持**：`cleanup_stale_files` 仍是**静态纯函数**（签名与返回值不变、路径可注入），既有单测未受影响。

**实测门禁证据（2026-10-18）**

| 门禁 | 实测 |
|---|---|
| `py_compile`（2 文件） | 退出码 **0** |
| `unittest discover -s tests` | **Ran 118 tests — OK**（零回归） |
| `smoke_m1m3.py` / `smoke_mb.py` | `SMOKE_ALL_OK`；退出码 **0 / 0** |
| 启动自检 | `ok=True`，**6 项全 True** |
| 脚本化场景（`_temp/ImportData/verify_p1_scenarios.py`） | ① 源 mtime 72h 旧 → **副本 mtime 归零（0.000h）**；② `cleanup_stale_files` 只删**无引用**的超龄文件（removed=1），**被引用的副本保留**；③ 预置 `X.xlsx` 时 `X.xls` 副本改名 **`X_1.xls`**（跨后缀查重生效）；④ 转换产物查重已落地（结构核对）；⑤ `ensure_xlsx(.xlsx)` 直通返回原路径（不回归） |

**挂起项（并归入 `P-2`）**

- **真实 `.xls` → `.xlsx` 转换的"产物不覆盖"实机验证**（需真实 `.xls` 文件，属 `P-2` 人工真机项）

### 0.7.4 P2 批次施工记录（R11，2026-10-18 已落地）

> **状态**：✅ 2 项／4 处改动落地（含 1 个新函数）；门禁全绿。

| 条目 | 落地改动（文件 · 位置） |
|---|---|
| `A-03` | `ops/table_importer.py`：在 `df.empty` 检查之后、重复列名告警之前插入**列名禁字符预检**——复用 **`ops.sql_safety._FORBIDDEN_IDENT_CHARS`**（同源常量，未另写字面量表）逐列检测，命中即 `raise ValueError`（消息含**列号**与字符 `repr`）；**空列名跳过**不拒绝 |
| `REQ-R2` | `ops/excel_preprocessor.py`：**新增 `read_header_row(file_path, sheet_name, header_row) -> Optional[List[Any]]`**（`load_workbook(read_only=True, data_only=True)` **只读目标行**，`finally: wb.close()`；越界返回 `None`；非 `.xlsx`／sheet 不存在 → `ValueError`；文件不存在 → `FileNotFoundError`）。`ops/table_importer.py`：imports 补 `read_header_row`；在 `cancel_check` 之后、`read_excel_sheet` 之前插入**全空表头行预检** → `raise ValueError("…第 N 行为空，不能作为表头…")` |

**`[ADJUSTED]` 记录（本轮新增）**

- **`[ADJUSTED-10]` `A-03` 的"空列名归一／重复列名去重"不在本批做** —— 与 **`REQ-H1`（P5）** 是同一逻辑；本批的禁字符预检**主动跳过空列名**。理由：避免两批实现同一逻辑，且防止"空列名的表在 P2 就被拒、永远到不了 P5 的归一"。
- **`[ADJUSTED-11]` `A-03` 的 error_messages 新规则已在 P0 落地** —— `("标识符包含禁止字符", …)` 已存在于 `_RULES`（P0/A-13）；本批**不重复添加**，`gui/error_messages.py` **未改**。

**实测门禁证据（2026-10-18）**

| 门禁 | 实测 |
|---|---|
| `py_compile`（2 文件） ＋ 模块导入自检 | 退出码 **0**；`read_header_row`／`import_excel_table` 均可调用 |
| `unittest discover -s tests` | **Ran 118 tests — OK**（零回归） |
| `smoke_m1m3.py` / `smoke_mb.py` | `SMOKE_ALL_OK`；退出码 **0 / 0** |
| 启动自检 | `ok=True`，**6 项全 True** |
| 脚本化场景（`_temp/ImportData/verify_p2_scenarios.py`，`openpyxl` 造样本） | ① 换行表头 → `ValueError`「第 1 列表头包含不可用字符 `'\n'`」；② 制表符表头 → 「第 2 列…`'\t'`」；③ 中文/空格/括号表头（`金额（元）`／`数量 个`／`A-B(1)`）→ **正常导入**（不误伤）；④ 空列名 → **未被预检拒绝**（交 `REQ-H1`）；⑤ 指定全空行作表头 → `ValueError`「第 1 行为空，不能作为表头」；改指定真表头 → 正常导入；⑥ `read_header_row` 直测：全空行返回 `[None, None]`、越界返回 `None`、不存在的 sheet 抛 `ValueError` |

### 0.7.5 P3 批次施工记录（R11，2026-10-18 已落地）

> **状态**：✅ 3 项落地（**新建 1 个模块 366 行**、**0 个既有文件改动**）；门禁全绿。

| 条目 | 落地内容（文件 · 函数） |
|---|---|
| 模块契约 | 新建 `rpa_engine/ops/excel_normalizer.py`：`NORMALIZE_RULES_VERSION="v1"`／`MERGED_SPLIT_LIMIT=10_000`／`FULL_LOAD_MAX_ROWS=100_000`；`NormalizeResult` 四字段（`dataframe`／`meta`／`report_entries`／`warnings`）＋ `normalize_sheet(...)` 签名（含 5 个 keyword-only 参数）**逐字对齐 Part 4** |
| `A-05` | `split_merged_cells(ws, df, header_rows)`：取 `merged_cells.ranges` → 左上角值填满全区（计入表头行偏移）→ 记 `splits`（含"列名"供 `meta.was_merged`）→ **不改临时区文件**；超 `MERGED_SPLIT_LIMIT` → **不拆分** ＋ `WAY_NOT_DONE` 记录 ＋ 人话告警 |
| `REQ-R4` | `resolve_formula_cells(ws_tex, ws_val, df, offset_rows, offset_cols)`：只对"缓存为空"的格取公式原文 → **就地写回**（不复制全量表）→ 记 `(行,列,原文,"cached_empty")` ＋ 人话告警；**绝不静默填 NULL**；**未引入 win32com** |
| `REQ-R5` | `expand_hyperlinks(ws, df, offset_rows)`：**先快速探测**再遍历 → 值替换为 `hyperlink.target`（`location` 形式外链**不**展开）→ 记 `(行,列,显示文本,目标地址)` |

**`[ADJUSTED]` 记录（本轮新增）**

- **`[ADJUSTED-12]` R3／R5 必须全量开簿（第 0 步实测结论）** —— `ReadOnlyWorksheet` **既无 `merged_cells` 属性**（实测 `AttributeError`），其 **`cell.hyperlink` 也恒为 `None`**（不报错但不填充）。故这两个函数的 `ws` 只能来自 `read_only=False` 的全量开簿。为守内存红线（§2.1 条 5／§0.2 条 6），模块新增常量 **`FULL_LOAD_MAX_ROWS = 100_000`**：超此行数则**跳过 R3／R5**，写 `WAY_NOT_DONE` 报告条目 ＋ 人话告警（**不静默**）。
- **`[ADJUSTED-13]` 已知缺口：纯公式行会被读取层丢弃** —— `read_excel_sheet` 走的 `pd.read_excel` 默认 `skip_blank_lines=True`；若某行**仅由无缓存公式**组成（其余格全空），该行在进入 `normalize_sheet` **之前**即被丢弃（实测 `行数: 0`），故 R4（作用于 df）无法覆盖。该情形属 **H5（全空行裁剪）／A-08（空值策略）** 的 **P4 范围**，本批**不超范围实现**，仅如实留痕（验收 V3c）。

**执行中自测暴露并修复的两处实现缺陷**

1. **行号换算 off-by-one** —— R4／R5 的 Excel 行号原写 `offset_rows+1+ri`，**漏算表头自身占行** → 修正为 `offset_rows+2+ri`（表头位于 `offset_rows+1`）。`A-05` 用的 `ri = r-1-header_rows` 换算本就正确，故仅 R4/R5 受影响（首轮 V3／V5 暴露）。
2. **dtype 上溯护栏** —— pandas 的 `iat` **不做 dtype 上溯**：把 str（公式原文／链接地址）写入 float64 列会抛错 → 新增 `_ensure_object_col(df, ci, value)`，**只把目标列**转 `object`（不复制整表）、数值写数值列时不做无谓转换；三处写格点（R3／R4／R5）统一调用。

**实测门禁证据（2026-10-18）**

| 门禁 | 实测 |
|---|---|
| `py_compile` ＋ 模块导入自检 | 退出码 **0**；4 个函数均可调用；`requirements.txt` **无 `pywin32`／`win32com`** |
| `unittest discover -s tests` | **Ran 118 tests — OK**（零回归） |
| `smoke_m1m3.py` / `smoke_mb.py` | `SMOKE_ALL_OK`；退出码 **0 / 0** |
| 启动自检 | `ok=True`，**6 项全 True** |
| 脚本化场景（`_temp/ImportData/verify_p3_scenarios.py`） | ① `A2:A4` 合并 `华东` → 3 行全 `华东`、`GROUP BY 地区` 得 `{华东:600}`（**无 NULL 分组**）、**回读原文件仍为合并状态**；② `MERGED_SPLIT_LIMIT=0` → 不拆分 ＋ 告警；③ 无缓存公式 → 值 `'=1+2'`（**非 NULL**）＋ 报告 1 条 ＋ 人话告警；④ XML 注入 `<v>3</v>` → 值 `3`（**缓存优先**，未被公式原文覆盖）；⑤ 超链接 → 值 `https://example.invalid/abc` ＋ 报告 1 条；⑥ 普通表与 `read_excel_sheet` 结果**逐格一致**、四字段齐备、keyword-only 可省略 |

**本批未接线（按 plan.md §4.3）**

- `table_importer` L76 改调 `normalize_sheet` 归 **`A-04`（P4）**；本批模块**尚无调用方**（P4 立即接入，不构成遗留死代码）。

### 0.7.6 P4 批次施工记录（R11，2026-10-18 已落地 · **由 `Agent-P4` 子 Agent 执行**）

> **状态**：✅ 9 项全部落地；门禁全绿，且经 **Coordinator 独立复核**（锚点抽查 13/13 ＋ 门禁重跑 ＋ 越界核对）。

| 条目 | 落地改动（文件 · 函数） |
|---|---|
| `A-04` | `ops/excel_preprocessor.py::read_excel_sheet` 的 `pd.read_excel` 追加 `keep_default_na=False, na_values=[], dtype=object`（前导零保留为文本）；`ops/excel_normalizer.py` 新增 `infer_cell_type`／`normalize_column_types`；**`ops/table_importer.py` 改调 `normalize_sheet`（＝接线，P3 成果首次进入真实导入路径）** |
| `A-06` | `ops/excel_normalizer.py::normalize_datetime_column`（日期 → ISO 8601 TEXT ＋ 元数据）；`ops/exporter.py::_iso_to_datetime` ＋ 写行改逐格 `ws.cell` 以设 `number_format` |
| `A-07` | `gui/forms.py`：`_DATE_VALUE_RE` **窄日期模式**（日期值不被改写）＋ 条件框格式提示；日期等值省略 `00:00:00` 使等值可命中 |
| `A-08` | `ops/excel_normalizer.py::apply_na_policy`（`preserve` 默认／`pandas`）；与读取层 `keep_default_na=False` 配合，使字面 `NA`／`N/A`／`None`／`null` **保留** |
| `REQ-R7` | `ops/excel_normalizer.py::clean_cell_text`／`_clean_one`（strip 含全角空格、去 `\x00`；**仅数据单元格**） |
| `REQ-H3` | `ops/excel_normalizer.py::is_bool_column`／`_bool_to_int`（整列布尔 → 1/0；元数据 `original_type="bool"`） |
| `REQ-H4` | `ops/excel_normalizer.py::normalize_error_cells` ＋ **新增 `collect_workbook_errors`**（错误值 → NULL ＋ 从工作表读回原文留痕；**不中断导入**） |
| `A-15` | `ops/sqlite_manager.py::import_dataframe_atomic`（临时表 → 校验行数 → `DROP`／`RENAME`，失败清理不留半成品）；`ops/table_lifecycle.py::guard_overwrite_target` ＋ 四处产表函数接线（`filter_dedup`／`aggregator`／`mapping_matcher`／`merge_tables`） |
| `A-16` | `engine/executor.py::ensure_input_tables`：短路判据改「表存在**且**行数 > 0」＋ 报错文案补充 |

**子 Agent 上报的 7 条 `[ADJUSTED]`（Coordinator 已逐条核对，均属正当取舍）**

- **`[P4-1]`** `read_excel_sheet` 追加 `dtype=object` —— 施工图 `A-04` 只述根因"无 dtype 约束"未给改动点；**实测** pandas 对文本存储的 `"007"` 仍强转 int64，故前导零只能在**读取层**以 dtype 约束保留（签名与返回值不变）。
- **`[P4-2]` `infer_cell_type` 浮点阈值口径（施工图内部矛盾）** —— 施工图规则 ③ 用 `group(1)+group(2)` 位数（`1234.56`→6 位 > 5→str），与其 `A-04 §5` 验收（金额 `1234.56`→REAL）**自相矛盾**；改按「**整数部分位数 ≤ 阈值**」判定以满足验收。
- **`[P4-3]` `REQ-H4` 原文留痕来源** —— **实测** openpyxl 把错误值存为 `data_type='e'`，`pandas.read_excel` 读成 NaN → df 内**已无原文**（骨架 `normalize_error_cells(df, meta)` 取不到）→ 新增 `collect_workbook_errors(ws,…)` 从工作表读回后留痕。
- **`[P4-4]` `A-06` 导出侧日期列判定** —— `REQ-H9` 元数据（P5 才做）尚不可用 → 改用**值形态判定**（严格 ISO 文本 → datetime ＋ `number_format`，解析失败回落原文）。
- **`[P4-5]`** 详见子 Agent 报告 `_temp/ImportData/p4-subagent-report.md`。
- **`[P4-6]` `A-07` 条件值不改写的匹配模式** —— 施工图宽模式 `^[\d\-: ]+$` 会误伤 `金额 > 100` 这类普通数值条件 → 改**窄日期模式**。
- **`[P4-7]` 阈值／空值策略的 JSON `global` 接线未做** —— `import_excel_table` 签名不可变且无 global 入参 → 本批走 normalizer 默认（`max_significant_digits=5`／`na_policy="preserve"`），接线留待 P5／P6。

**实测门禁证据（2026-10-18）**

| 门禁 | 子 Agent 自报 | **Coordinator 亲自重跑** |
|---|---|---|
| `py_compile`（11 个改动文件） | 退出码 **0** | — |
| `unittest discover -s tests` | Ran 118 — OK | **Ran 118 tests — OK** ✅ |
| `smoke_m1m3.py` / `smoke_mb.py` | `SMOKE_ALL_OK` 0／0 | **`SMOKE_ALL_OK` 0 / 0** ✅ |
| 启动自检 | ok=True，6/6 | **`ok=True`** ✅ |
| 验收脚本 `verify_p4_scenarios.py`（38 条断言） | `VERIFY_P4_ALL_OK` | **`VERIFY_P4_ALL_OK`** ✅ |
| **锚点真实性抽查（13 处）** | — | **13/13 命中** ✅ |
| **越界核对** | 未改 AGENTS/docs/build | **`AGENTS.md` mtime 14:54（P-0 时间，早于 P4）／`build/` 未动／docs 近 3h 仅 Coordinator 本人写的任务记录** ✅ |
| `requirements.txt` 无新增、无 `pywin32` | 是 | **16 行；`pywin32` 命中 0** ✅ |

**遗留与提示（如实登记）**

- **未接线**：`max_significant_digits`／`na_policy` 的 JSON `global` 覆盖（`[P4-7]`）；`normalize_sheet` 的 `enable_cache`（H10，P5）；`REQ-H9` 元数据表／报告落盘（P5）——故导出侧走"值形态判定"。
- **既有行为变化（提示）**：A-04 走文本读取后，列类型由 `to_sql` 按**值**判定（int→INTEGER／float→REAL／str→TEXT）；**混合列整体落 TEXT**；阈值默认 5，故 ≥6 位整数的数字列会落为文本（施工图 `A-04 §6` 已列为已知风险）。
- **`[ADJUSTED-13]` 缺口保持不修**（纯公式行被 `skip_blank_lines` 丢弃）。
- **回滚点**：`_temp/ImportData/backup/P4/` 共 **11 个快照** —— 6 个由 Coordinator 预置（`excel_normalizer`／`excel_preprocessor`／`executor`／`sqlite_manager`／`table_importer`／`table_lifecycle`）＋ **5 个由 Coordinator 用只读 `git show HEAD:` 补齐**（`exporter`／`filter_dedup`／`aggregator`／`mapping_matcher`／`forms`）。**原因：我的预置备份清单（本批计划 §3.1 项 7）漏列了这 5 个实际被改的文件 —— 属计划缺陷，已记录并补救。**

**遗留项终态（2026-10-18 人工裁定落地）**

- **`[P4-7]` 已裁定：维持当前默认（留待后续专项）** —— `max_significant_digits=5`／`na_policy="preserve"`。
  原因：真正接线需**改 `import_excel_table` 签名**以透传 `global_config`，而签名与返回值受 **§0.2 条 2 硬约束保护**（不改既有签名）→ 属**架构死锁**，仓促处理会横跨多个模块；且当前默认值**不导致数据错误**（阈值 5 位／字面 NA 保留）。
  **后续专项建议**：先设计完整的 `global_config` 透传链路（含 JSON 参数 Schema 与引擎注入点）再实施。
- **`[P4-4]` 已落地：二者并存（元数据优先 ＋ 值形态兜底）** —— 导出时先查 `__normalize_meta` 中该表 `original_type='datetime'` 的列，命中则按**宽松形态**解析（`YYYY/M/D`／`YYYY.M.D`／`YYYY-MM-DDTHH:MM(:SS)`，**无歧义限定**）；未命中则回落**严格值形态**判定（现状口径）。
  落点：`ops/exporter.py` —— 新增 `_datetime_columns(conn, table_name)`／`_parse_datetime_loose(value)` ＋ `export_table` 写入循环分支（`columns[c_i-1] in dt_cols`）。
  **兼容性**：**无 `__normalize_meta`（旧库／旧会话）时 `dt_cols` 为空集 → 行为与改动前逐格等价**；任何解析失败一律原样写（不引入新失败）。
  实测：见 `_temp/ImportData/verify_d3_scenarios.py`（`VERIFY_D3_DONE`／V4a~V4e 全 PASS）。

**批次机制说明（本轮首次派子 Agent）**

- 按 plan.md §1.1 L343 的分配（`Agent-P4`）与 §0.8 协作机制执行；**单个子 Agent 串行**（不拆并行，避免并发门禁争用共享临时区／工作区）。
- Coordinator 执行了"**信任但验证**"全流程（V1 锚点抽查 → V2 门禁重跑 → V3 验收脚本重跑 → V4 越界核对 → V5 仲裁），**未发现子 Agent 的不实声明**；子 Agent 自报"无阻塞"，并经复核认可。

### 0.7.7 P5 批次施工记录（R11，2026-10-18 已落地 · 由 `Agent-P5` 子 Agent 执行）

> **状态**：✅ **5 项完成 ＋ `REQ-H9` 部分完成**（三个落盘函数已建并直测，**报告/元数据表的自动写入接线归 P6**）；门禁全绿且经 **Coordinator 独立复核**。

| 条目 | 落地改动（文件 · 函数） |
|---|---|
| `REQ-H1` | `ops/excel_normalizer.py::dedup_columns()`（重复名 → `原名_2`／`_3`；**空列名 → `未命名列_N`**，＝承接 P2 的 `[ADJUSTED-10]`）；`ops/table_importer.py` 的重复表头段改为防御性残留日志 |
| `REQ-H5` | `excel_normalizer.py::handle_empty_cols_rows()`（全空列保留并标 `all_empty`／尾部全空行裁剪） |
| `REQ-H6` | `excel_normalizer.py::detect_non_cell_content()`（`_images`／`_charts`）＋ 批注改由遍历 `cell.comment`（≤200k 单元格护栏）；**结果告知用户**（人话） |
| `REQ-H7` | `excel_normalizer.py::detect_precision_loss()`（整数位 > 15 → 提示；**只读不改数据**） |
| `REQ-H9` | `excel_normalizer.py::write_normalize_report()`（JSON ＋ 人读文本，**无技术词**）／`write_meta_table()`（统一表 `__normalize_meta`）／`write_failed_list()`（JSON ＋ 人读）；`gui/main_window.py` 的 `failed` 由 `List[str]` → `List[Dict]` ＋ **真接线落盘**（弹窗＋落盘双通道）。**报告/元数据表的"每次导入自动写"调用点留待 P6** |
| `REQ-H10` | `rpa_engine/paths.py::get_normalized_dir()`（新增，**既有 API 未动**）；`excel_normalizer.py::normalized_cache_key`／`load_normalized_cache`／`_save_normalized_cache`（JSON 元数据 + `size+mtime` 指纹；**禁 pickle**） |

**子 Agent 上报的 `[ADJUSTED]`（Coordinator 已逐条核对认可）**

- **H1 落地位置**：施工图称调用点＝`table_importer`，实际落在 `normalize_sheet` 读取后（满足「`NormalizeResult.dataframe.columns` 为唯一列名来源」＋报告随 result 携带＋可直测）；`table_importer` 该段改为防御日志 —— 语义等价（§0.2.1），`PRAGMA table_info` 端到端已验。
- **H6 探测位置**：施工图称在 `scan_sheets` **只读**阶段；**实测只读模式 `_images`／`_charts`／`_comments` 均缺失**（与 P3 发现的 `merged_cells`／`hyperlink` 同源限制），且 openpyxl 3.1.5 全量模式 `ws._comments` 恒为空表 → 改在 `normalize_sheet` **全量开簿**阶段探测，批注改走遍历 `cell.comment`。**未改 `scan_sheets` 返回结构**。
- **H10 缓存**：遵「禁 pickle／pyarrow」→ JSON 元数据、不落 DataFrame；「跳过全量开簿」仅在缓存表明该表**无 Stage A 变换**（合并格／公式／错误值／超链接皆空）时生效，以保证两次结果一致。
- **`paths.py` 的 `[UNVERIFIED]` 已核实**：既有 API 为 `get_engine_root()`／`get_bundle_dir()`，新增同风格 `get_normalized_dir()`，**既有函数签名未动**。

**管线位次（本批负责项不在六段强制清单内，未颠倒）**：
`读取 → [H1] → [H7] → 阶段A(合并格→公式→错误值→[H6]→超链接) → 阶段B(清洗→空值→类型) → [H5] → 返回`

**实测门禁证据（2026-10-18）**

| 门禁 | 子 Agent 自报 | **Coordinator 亲自重跑** |
|---|---|---|
| `py_compile`（4 个 .py） | 退出码 **0** | — |
| `unittest discover -s tests` | Ran 118 — OK | **Ran 118 tests — OK** ✅ |
| `smoke_m1m3.py` / `smoke_mb.py` | `SMOKE_ALL_OK` ×2 | **`SMOKE_ALL_OK` ×2** ✅ |
| 验收脚本 `verify_p5_scenarios.py`（26 条断言） | `VERIFY_P5_ALL_OK` | **`VERIFY_P5_ALL_OK`** ✅ |
| **锚点真实性抽查（10 处）** | — | **10/10 命中** ✅ |
| **`backup/P5/` 覆盖核对** | 报告 4 个修改文件 | **4 个文件与清单一一对应** ✅（**P4 的备份缺口未复现**） |
| H9 落盘产物存在性 | 已 Read 回验 | **磁盘可见**：`p5_artifacts/h9/{T1_normalize.json,T1_normalize.txt,failed_list.json,failed_list.txt}` ✅ |
| 越界核对 | 未改 AGENTS/docs/build/plan.md | **`AGENTS.md` mtime 14:54（P-0 时间）／`BUILD_INFO.txt` 9-24／`requirements.txt` 16 行、`pywin32` 命中 0** ✅ |

**跨批交互实测结论（子 Agent 提供，Coordinator 认可）**

- `temp/normalized/`（H10 产物）**不会**被 `A-11` 的超龄清理误删：`_cleanup_stale_sessions` 只把 `temp/input_selection` 作 `temp_root`（同级兄弟目录不在扫描范围）；沙盒实测"两者同设 48h 旧 mtime → normalized 存活、input_selection 旧副本被删" ✓ **未改任何清理逻辑**。

**遗留与已知缺口（如实登记）**

- **`REQ-H9` 的报告/元数据表未接入导入主流程** —— 函数已实现并直测，但"每次导入自动写报告/元数据表"需要**会话时间戳目录与调用点**，属 **P6「新建模块接线」** 范畴；且 `import_excel_table` 签名不可改（无法回传 `NormalizeResult`）。**失败清单已在 `main_window` 真接线。**
- H10 缓存目录**无自动 pruning**（跨会话保留，靠 `size+mtime` 指纹自然失效）。
- H6 对超大表（>200k 单元格）跳过批注探测；行数 >100k 或命中缓存跳过开簿时不探测。
- 元数据表 `__normalize_meta` 建表用字面名（非业务逻辑），仅供追溯。
- `[ADJUSTED-13]` 缺口保持不修。

**批次机制说明**

- 沿用 `Agent-P5` **串行**子 Agent；**备份责任已下放给子 Agent**（本批 4 个修改文件全部有改前快照，且覆盖与报告清单一致 → **P4 暴露的"父 Agent 预置清单漏列"缺陷未复现**）。
- Coordinator 执行"**信任但验证**"全流程（V1 锚点抽查 → V2 门禁重跑 → V3 验收脚本重跑 → V4 越界＋**备份覆盖核对** → V5 仲裁）；子 Agent 自报"无阻塞"，经复核认可。

### 0.7.8 P6 批次施工记录（R11，2026-10-18 已落地 · 由 `Agent-P6` 子 Agent 执行）— **A 链收官**

> **状态**：✅ `A-09` ②③ 落地 ＋ **① 依 §6 降级**；✅ 新建模块接线完成（P5 遗留闭环）；门禁全绿并**经 Coordinator 独立复核**。
> 🏁 **A 类 19 项至此全部闭环**（P0 7 ＋ P1 3 ＋ P2 1 ＋ P3 1 ＋ P4 6 ＋ P6 1）；`REQ-H9` 的"报告/元数据表接线"由本批补齐。

| 任务 | 落地 |
|---|---|
| `A-09` ② | `gui/main_window.py`：新增 `LARGE_TABLE_ROWS=200_000`／`MEM_WARN_MB=2048`；`_import_progress_label()`（逐表文案，大表预告"该表较大、导入期间界面可能暂无响应"）；`_on_confirm_import` 导前预扫行数→文案→`processEvents()`；导后 **`psutil`** 取 RSS，超 `MEM_WARN_MB` 记警告 ＋ 文案提示（**既有 `MEMORY_WARN_ROWS=500_000` 判定未改**） |
| `A-09` ③ | `_on_confirm_import` 显式 `setCancelButton(None)`（保持不可取消的现状）＋ 冻结预告由 ② 的逐表文案承载 |
| `A-09` ① | **❌ 未落地 —— 按 §6 降级**。**实测**：pandas 3.0.5 的 `pd.read_excel` **无 `chunksize` 形参、也无 `**kwds`** → 传 `chunksize=` 直接 `TypeError`；`engine_kwargs={'chunksize':…}` 透传给 `load_workbook` 亦 `TypeError`。**计划指定机制在当前依赖下架构上不可实现** → 依 §6「仅加提示 ＋ 内存阈值修正，不做分块」。**`ops/excel_preprocessor.py` 未改**（Coordinator 复核实测该文件 `chunksize` 命中 **0**），`dtype=object` ＋ `keep_default_na=False` 约束**原样保留**（**未**为分块回退 A-04） |
| 接线（P5 遗留） | `gui/main_window.py` 每表导入成功后调 `write_normalize_report`（目录＝`workspace/normalize_report/<session_id>`，与失败清单同源）＋ `write_meta_table`（会话库统一表 `__normalize_meta`）；`ops/table_importer.py` 增设模块级**桥接槽** ＋ 新增 `take_last_normalize_result()`（**既有签名/返回值不变**）；落盘后置 `norm.dataframe=None` 释放大对象（守内存）。**阶段切换与 GUI 错误回显为既有实现、保留未改；GUI 布局排版无改动** |
| 判断项（任务三） | **`[P4-7]`**（JSON `global` 接线）与 **`[P4-4]`**（元数据驱动日期列判定）**均未做** —— plan.md 原文未明确归属 P6 → 按纪律列 **"留待人工裁定" ＋ 各 3 个选项**，未自行扩范围 |

**子 Agent 上报的 `[ADJUSTED]`（Coordinator 已逐条核对认可）**

- **P6-1** 分块不可行 → §6 降级；`CHUNK_ROW_THRESHOLD` 未下调（降级下无消费方，不留死常量消费点）。
- **P6-2** plan 的预告阈值＝`rows > 200_000`，故 5 万行样本本就不触发预告 → 另建 **200,001 行**真实表以验证"导入前有文案提示"。
- **P6-3** 抽出 `_import_progress_label` 纯函数（语义等价、便于验收）。
- **P6-4** REQ-H9 结果经模块级**桥接槽**回传（因 `import_excel_table` 签名不可改）；落盘后释放 DataFrame。
- **P6-5** 行数预扫用临时区 xlsx 并复用 `sheet_info`（顺带省一次开簿）。

**实测门禁证据（2026-10-18）**

| 门禁 | 子 Agent 自报 | **Coordinator 亲自重跑** |
|---|---|---|
| `py_compile` | `PY_COMPILE_OK` | — |
| `unittest discover -s tests` | Ran 118 — OK | **Ran 118 tests — OK** ✅ |
| `smoke_m1m3.py` / `smoke_mb.py` | `SMOKE_ALL_OK` ×2 | **`SMOKE_ALL_OK` ×2** ✅ |
| 启动自检 | — | **`ok=True`** ✅ |
| `verify_p6_scenarios.py`（37 条断言） | `VERIFY_P6_ALL_OK` | **`VERIFY_P6_ALL_OK`** ✅ |
| 大表样本（子 Agent 实测） | 5 万行×10 列（33.4s）＋ **200,001 行×2 列**（11.7s，真实触发预告）＋ 常规 1 万行×5 列 | 如实采信（见 D6） |
| **锚点抽查（7 处）** | — | **7/7 命中**；且 **`excel_preprocessor.py` 的 `chunksize` 命中 0**（降级未留残留）✅ |
| **线程模型未改证据** | 未改 `worker.py` | **`worker.py` mtime ＝ 09-24（全部批次前后完全未动）**；`executor.py` 10-18 16:49 系 **P4/A-16** 的 `ensure_input_tables`，**非 P6** ✅ |
| **`backup/P6/` 覆盖核对** | 报告 2 个既有文件 | **2 个文件一一对应** ✅ |
| 越界核对 | 未改 AGENTS/docs/build/plan.md | **`AGENTS.md` mtime 14:54（P-0）／`BUILD_INFO.txt` 9-24／`requirements.txt` 16 行无 pywin32** ✅ |

**遗留与已知缺口（如实登记）**

- **`A-09` 改动点 ①（分块读取）未实现** —— 计划指定机制在当前依赖下不可用，依 §6 降级；**若日后要真正分块，须先由人工裁定技术路线**（选项：升级 pandas／改用 openpyxl 流式逐行读取／改用其它读取器）。
- **`[P4-7]`／`[P4-4]` 留待人工裁定**（各附 3 选项，见子 Agent 报告「任务三」）。
- 预扫失败时静默跳过预告并按"无预告"继续（`logger.debug` 留痕，不阻断导入）。
- 桥接槽在**单线程串行假设**下安全；未来若并发导入需改为显式传参。
- `norm.dataframe=None` 依赖 `NormalizeResult` 为可变 dataclass（落盘专用一次性实例，安全）。
- **`P-2`（exe 重建 ＋ 真机 `.xls` 验证）始终挂起，须人工执行。**

**A 链收官声明（R11，2026-10-18）**

- ✅ **A 类 19 项全部闭环**：`A-01`~`A-19`（P0 7 ＋ P1 3 ＋ P2 1 ＋ P3 1 ＋ P4 6 ＋ P6 1）。
- **REQ 侧**：`REQ-R2`／`R3`／`R4`／`R5`／`R6`（由 `A-04` 承载）／`R7` ＋ `REQ-H1`／`H3`／`H4`／`H5`／`H6`／`H7`／`H9`／`H10` 均已落地；**`REQ-H9` 的接线由本批补齐**。
- **未闭环项（如实）**：`A-09`①（降级）、`[P4-7]`、`[P4-4]`（均留待人工裁定）；**B 类 `B-01`~`B-44` 未施工**；人工 **`P-2`**。
- **规约侧**：`AGENTS.md` 的锚点 R11 状态**仍为"进行中"**（因 B 类未完成），本批仅记录进度，**不改锚点状态**。

### 0.7.9 B 链施工记录（R12，2026-10-19 起 · **首次改源码**）

> **依据**：人工上传的《B 类操作执行提示词》（§一/§八 只认 **13 项**）＋ 本文件 Part 3 对应条目 ＋ `AGENTS.md`
> **13 项**：`B-01`／`B-02`／`B-13`／`B-14`／`B-15`／`B-16`／`B-21`／`B-28`／`B-31`／`B-33`／`B-39`／`B-42`／`B-43`（＝台账 `[ACTION]` 13 项）
> **阶段**：阶段0 备份 → 1(`B-01`→`B-13` ∥ `B-02`) → 2(`B-14`→`B-28`) → 3(`B-15`→`B-16`→`B-31`) → 4(`B-21`) → 5(`B-33`) → 6(`B-39`) → 7(`B-42` ∥ `B-43`)；**阶段间串行**，每阶段后跑 §七 门禁 5 项。
> **口径**：**只做 13 项**；附件 §四 虽含 `B-01~B-44` 全文复本，**越界项（台账 `[BLOCKED-*]`）一律不碰**（亦合附件 §八 第 4 条"无越界"）。
> **`[ADJUSTED]`（本轮发现）**：附件 §五 允许"阶段 4 `B-21` 与阶段 2 并行"，但 `B-21` 改 `gui/models.py` 而 **`B-13`（阶段 1）也改 `models.py`** ⇒ 依"阶段间串行"执行，**不并行**；另 `B-01` 与 `B-13` **同改 `gui/app.py`** ⇒ 阶段 1 内二者**由同一 Sub-Agent 串行**（`A1`），仅与 `B-02`（`A2`）并行。

**阶段 0（备份）—— 已完成**
- 12 个文件改前快照 → `_temp/ImportData/backup/B1/阶段0/`（含 `app.py`／`main_window.py`／`session_db.py`／`models.py`／`test_step_catalog.py`／`forms.py`／`sql_safety.py`／`page_operation_config.py`／`graph_edges.py`／`table_importer.py`／`executor.py`／`parser.py`）
- 基线：**Ran 118 tests — OK**（改前）

**阶段 1（`B-01`／`B-02`／`B-13`）—— ✅ 已完成并复核**

| 条目 | 落地（文件 · 位置） | `[ADJUSTED]` 行号更正 |
|---|---|---|
| `B-01` | `gui/app.py`：L13 补 `import tempfile`；`_setup_gui_logging` L247-279（`mkdir` 包 try→失败回退 `Path(tempfile.gettempdir())/"RPA_Workflow_v3_logs"`；`logger.add` 以"解析后可用目录"为目标且失败不抛）；`launch_gui` L308-313 **顺序改为「自检先取 → 日志（包 try）」** | 附件称函数 L246-256／调用 L277-278；实为 L246 起／调用原 L281-282 |
| `B-02` | `gui/main_window.py`：L19 补 `import os`；新增模块级 `_is_stale_session(p)->bool`（尾部 PID 段解析＋`psutil.pid_exists`；**异常名保守不删**）L73-92；会话库命名 L301-305 改为 `f"{…:%Y%m%d_%H%M%S}_{os.getpid()}"`；`cleanup_stale_files` 删库循环 L817-827 加守卫＋docstring L801-812 更正。**`ops/session_db.py` 经核实按附件"本项不改"⇒ 未改** | 附件称 cleanup L679-707／命名 L259-261／调用 L236；实为 L800-855／L278-280／L256 |
| `B-13` | `gui/models.py`：**新增** `active_catalog_keys()->List[str]` L127-133，`main_buttons`/`more_buttons` L136-157 共用过滤（排除 `deprecated`）；`gui/app.py` L143-145 导入＋L186-192 并集比对改同源口径；`tests/test_step_catalog.py` L10-12/L61-64＋**新增 `test_deprecated_self_check_passes`** | 附件称比对 L185-188／按钮集 L127-142；与实况基本相符（`main_buttons` L127 起） |

- **Coordinator 独立复核（哈希比对，不采信自报）**：与本阶段快照比对 → **恰好 4 个文件被改**（`app.py`／`main_window.py`／`models.py`／`test_step_catalog.py`），与两组自报范围**逐字吻合**；`session_db.py` **确认未改**；**其余 8 文件（`forms`／`sql_safety`／`page_operation_config`／`graph_edges`／`table_importer`／`executor`／`parser`）全部未碰** ⇒ 后续阶段文件未被误伤
- **门禁（Coordinator 重跑）**：`Ran 119 tests — OK`（**用例 +1**，来自 B-13 新用例）｜`smoke_m1m3`／`smoke_mb` 双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **越界核对**：`engine/executor.py` **哈希未变**｜`engine/parser.py` **哈希未变**｜`requirements.txt` 16 行、**无新依赖**（仅标准库 `tempfile`／`os`＋已在册 `psutil`）
- **阶段 2（`B-14` → `B-28`，串行）—— ✅ 已完成并复核**

| 条目 | 落地（文件 · 位置） | `[ADJUSTED]` 行号更正 |
|---|---|---|
| `B-14` | `gui/forms.py`：`_OPS_ORDER` L35-36 **补入 `"NOT IN"` 且置于 `"IN"` 之前**；解析期按 `len` 降序匹配 ⇒ **`NOT IN` 不再被切成错列名**；**新增 `parse_list_value()`** L188-198（逗号/顿号/圆括号切分＋strip，**跳过数值化改写**，遵裁定 G8）；`parse_condition_lines` L204-222 值改走该解析器 ⇒ `build_where` 收到 **list 而非标量（`IN` 必现失败消除）**。`ops/sql_safety.py`：`build_where` IN/NOT IN 分支 L136-146 标量输入 → 抛**中文可操作提示**「`'IN' 需要多个值，请用逗号分隔，列: …`」，**不静默改写**；**`build_where` 签名与 `SUPPORTED_OPERATORS` 未动** | `_OPS_ORDER` 实为 L35-36／`parse_condition_lines` 改前实为 L204-206／`_maybe_number` 实为 L223／`build_where` IN 分支实为 L137-145 |
| `B-28` | `gui/forms.py::format_conditions` L251-264：list 值改用 `"、".join(...)` 渲染，**不再输出 Python repr**（如 `['a','b']`）⇒ **与解析器往返一致（"打开即退化"消除）**；改动点 2「共用解析」由 `B-14` 的 `parse_list_value` 承接（非独立改点） | 附件记 L226 起，改前实为 L235／改后 L251 |

- **Coordinator 独立复核（哈希比对）**：本阶段**只新增改动 2 个文件**（`gui/forms.py`／`ops/sql_safety.py`）；**其余 6 个（`page_operation_config`／`graph_edges`／`table_importer`／`executor`／`parser`／`session_db`）全部未碰** ⇒ 后续阶段文件未被误伤
- **门禁（重跑）**：`Ran 119 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **越界核对**：`engine/executor.py`／`engine/parser.py` **哈希未变**｜`requirements.txt` 16 行、无新依赖
- **锚点核实**：`parse_list_value` ×2／`NOT IN` ×16／`format_conditions` ×4／`需要多个值` ×2 均命中
- **`[ADJUSTED]`（本轮）**：受"仅改这两个文件"硬约束，`B-28` 改动点 3「新增往返单测」**未落地为测试文件**，改以**行内往返断言**验证（list→文本→list 恒等、无 repr）；证据：`IN` 解析→`['0123','0456']`；`build_where`→`"电表号" IN (?, ?)`；`NOT IN`→`"电表号" NOT IN (?)`；标量→中文提示；往返渲染 `电表号 IN 0123、0456` 解析回原 list

**阶段 3（`B-15` → `B-16` → `B-31`，全在 `gui/page_operation_config.py`，串行）—— ✅ 已完成并复核**

| 条目 | 落地（关键方法 · 行区间） | `[ADJUSTED]` 行号更正 |
|---|---|---|
| `B-15` | `_harvest_current_form` 改为按**稳定标识 `uid`** 回写（新增 `_form_step_uid`，切表/空面板/restore 时清空）⇒ 与下标解耦；`_on_add_step` 插入后按**实际对象位置**（`s is step`）重算 `idx_new` ⇒ **不再把上一被选步骤的参数灌进新步骤（"导出路径 100% 失效"消除）**。落点 L82-86／L378-386／L516-529／L746-786 | v7 记 L501-513／L674-698／L477-480 ⇒ 实为 L516-529／L746-786／L479-514（整体下移） |
| `B-16` | 目标表下拉 `findData` 未命中且 `cur` 非空时**不改写** `step.target_table_id`（遵裁定 G4），`setCurrentIndex(-1)` 置空态 ＋ **新增 `_notify_missing_target()`**（中文弹窗「…已不存在，请重新选择」）＋ 走**既有** `_schedule_graph_refresh` 刷新画布 ＋ `_push_undo` ⇒ **不再静默改写、有提示、入撤销栈**。落点 L345-366／L707-716 | 附件记 L346-354 ⇒ 实为 L345-366 |
| `B-31` | 新增**压栈后状态指纹** —— `_push_undo` 置 `_undo_pending`，`_schedule_graph_refresh` 首个刷新时回填 `_undo_expected_sig`；`_undo_last` 入口比对当前指纹，不一致则**拒绝撤销**并弹「检测到撤销后有新的改动，已取消本次撤销」；栈满（`deque(maxlen=10)`）**记 warning 不再静默丢最老快照**。落点 L121-124／L568-591／L593-622／L624-637／L942-949 | 附件记 `_undo_last` L567 起 ⇒ 实为 L593 起 |

- **Coordinator 独立复核（哈希比对）**：本阶段**只新增改动 1 个文件**（`gui/page_operation_config.py`）；**其余 5 个（`session_db`／`graph_edges`／`table_importer`／`executor`／`parser`）全部未碰**；八处关键方法（`_on_add_step`／`_build_step_param_panel`／`_undo_last`／`_push_undo`／`_on_target_changed`／`restore_config`／`_schedule_graph_refresh`／`class`）**全部仍在**（无整段删除）
- **行数核实（澄清）**：阶段 0 快照 **1167 行** → 当前 **1247 行**（**净 +80**）；`git diff --stat` ＝ **+98 / −12** ⇒ 与子 Agent 自报一致（~~"1315 行"系**我计划内的数字失准**，此处更正~~）
- **门禁（重跑）**：`Ran 119 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **越界核对**：**未增删控件/未重排布局/未改样式表**（"刷新画布"只调**既有** `_schedule_graph_refresh` 通道）｜`engine/executor.py`／`engine/parser.py` **哈希未变**｜`requirements.txt` 16 行、**无新依赖**
- **锚点核实**：`_notify_missing_target` ×2／`_model_signature` ×3／`_form_step_uid` ×7／`已不存在` ×3／`已取消本次撤销` ×1／`_schedule_graph_refresh` ×15 均命中

**阶段 4（`B-21`）—— ✅ 已完成并复核**

| 条目 | 落地（关键方法 · 行区间） | `[ADJUSTED]` 行号更正 |
|---|---|---|
| `B-21` | **根因**：覆盖模式（`output_mode=overwrite_target`）的产出编号被 `specs_from_model` 排除出表节点，而 `graph_edges.build_edges` 原用**表节点集**判悬空 ⇒ 下游引用该编号即**误判 dangling**；同时模型 `reconcile` 的 alive 账本又把它记为 `overwritten`（存活）——**两本账分叉**。**修法**：`build_edges` 悬空判定基准改为**存活集** —— 新增 `models.py::alive_table_ids(tables, steps)`（＝输入表 ∪ 全部步骤产出编号，**与 `reconcile` 的 alive 同源**）＋ `models.py::edge_state(table_id)->str`（单表状态访问器）；`reconcile` 的 alive 改为**复用同一函数**（口径单源化）。⇒ **覆盖产出的中间表被识别为"存活但无节点"，引用它不再出红虚线（假悬空告警消除）**。落点：`graph_edges.py` L24-25／L275-280／L307-311；`models.py` L570／L597-613／L946-975 | v7 记 `graph_edges` 悬空判定 L203 ⇒ 实为 **L302-305（改前）／L307-311（改后）**；v7 记 `models` overwritten L568-571 ⇒ 实为 `reconcile` 覆盖分支 **L579-582（改前）**，`reconcile` 整体 L553-595 |

- **Coordinator 独立复核（精确比对）**：本阶段**只改 2 个文件** —— `models.py`／`graph_edges.py` 相对 `backup/B1/阶段4/` 快照**均已改**；其余 10 文件相对 `阶段0` 显示 6 个已改（**＝阶段 1~3 既有成果，本阶段未新增**）⇒ 跨阶段零误伤
- **阶段 1 成果保全（本阶段新增复核项）**：`gui/models.py` 的 `active_catalog_keys` 命中 **4 ＝ 阶段 4 前基线 4** ⇒ **阶段 1 的 `B-13` 成果未被回退/误伤** ✓
- **门禁（重跑）**：`Ran 119 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **越界核对**：**五类边契约七字段仍在**（`config_state`／`deprecated` 命中 53）｜未增删控件/未重排布局/未改样式｜`engine/executor.py`／`engine/parser.py` **哈希未变**｜`requirements.txt` 16 行、**无新依赖**
- **锚点核实**：`alive_table_ids` ×5／`edge_state` ×1 命中；`git diff --stat` ＝ `graph_edges.py` 14 行 ＋ `models.py` **+81 / −?（合计 +81 / −14）**
- **复现验证（自证）**：`T102`（overwrite 中间表，state=overwritten）节点集 `['T1','T2','T101']`、**`dangling=[]`**（改前会得假悬空 `[(T102,S3)]`）；**真悬空场景**（T9／T999／T101 删步后）**仍正常判 dangling** ⇒ 消除假阳性而**未放宽真告警**

**阶段 5（`B-33`）—— ✅ 已完成并复核 · 逐 hunk 零越界**

| 条目 | 落地（关键函数 · 行区间） | `[ADJUSTED]` 行号更正 |
|---|---|---|
| `B-33` | **只改 `engine/executor.py` 的 `ensure_input_tables`**（+8 行，L115-124）：在其补导段的 `except (ValueError, FileNotFoundError)` **之后新增 `except RuntimeError as e:` 分支** —— 因 `table_importer` 的取消以 `RuntimeError` 抛出、此前逃逸至 `execute_workflow` 的兜底 `except Exception`（→`failed`）；现以 **`cancel_check()` 二次判定**区分：**为真 → 抛 `ExecutionError("收到终止请求，停止补导输入表…")`**，由既有 `execute_workflow::except ExecutionError`（同口径二次判定）**归并为 `status="cancelled"`**；**为假 → `raise` 原样上抛，真实错误仍归 `failed`** ⇒ **"补导终止被降级为执行失败"消除**。**`ops/table_importer.py` 经核实为 no-op（其消息已含「收到终止请求」，改动点 2 现状已满足）⇒ 未改一行** | 附件记导入段 L107-111 ⇒ 实为改前 **L112-116**；兜底 `except` 附件记 L221-224 ⇒ 实为改前 **L217-225** |

- **🔴 越界核对（本阶段核心）**：对 `backup/B1/阶段5/executor.py` 做**逐 hunk diff** —— 唯一 hunk 头为 **`@@ -115,4 +115,12 @@ def ensure_input_tables(...)`** ⇒ **改动完全落在 `ensure_input_tables` 内**；**无** `execute_workflow`／信号／线程／重试／清理段 hunk。executor 内 def 清单另证：`ensure_input_tables` L81／`execute_workflow` L127／`_execute_with_retry` L275 —— **改动仅在 L115-124** ✓ **零越界**
- **`table_importer.py`**：与 `阶段5` 快照**逐字一致（零 diff）** ⇒ 子 Agent"未改"自报**属实**；`import_dataframe_atomic` 调用仍在（L147）
- **A 链成果保全**：由上述 hunk 直接证明 **`A-16` 判据行（`table_exists(...) and table_row_count(...) > 0`）未被触碰** ✓
- **门禁（重跑）**：`Ran 119 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **跨阶段面**：其余 10 文件相对 `阶段0` 的 8 个已改**均为阶段 1~4 既有成果**（本阶段未新增）；`engine/parser.py` **未改**（阶段 6 待做）
- **回滚点**：`backup/B1/阶段5/{table_importer.py(131行),executor.py(255行)}`（**本阶段前**内容；因两文件均已被 A 链改过，**未**用更旧的 `阶段0` 版本）

**阶段 6（`B-39`）—— ✅ 已完成并复核 · 逐 hunk 零越界 ＋ 零误伤**

| 条目 | 落地（关键函数 · 行区间） | `[ADJUSTED]` 行号更正 |
|---|---|---|
| `B-39` | **只改 `engine/parser.py::parse_workflow` 的版本门禁块**（L120-133）：原 `version = str(meta.get("schema_version") or "")` 用 `str()` 把 JSON **数字 `3.1`** 归一成 `"3.1"` 而落入白名单 ⇒ **静默放行**；现**删除该归一**，改为先做 **`isinstance(raw_version, str)` 严格类型判定** —— **非字符串**（数字／`null` 等）一律抛**既有 `ParserError`**，中文人话：「**参数文件版本号格式非法（schema_version=3.1）；版本号必须写成字符串 "3.1"，不能写数字或其它类型。请在 GUI 中重新生成参数文件**」；**字符串路径保持原样**（先过类型，再走 `_SUPPORTED_SCHEMA_VERSIONS` 白名单）⇒ **数字型版本不再静默放行**。**未新增异常类型／未改白名单内容／签名与返回值结构不变**；注释 L121-122 同步更正 | 附件记白名单 L65／校验 L127-132／`str()` 归一 L124 —— **实况一致**（无 `[ADJUSTED]`） |

- **🔴 越界核对（逐 hunk）**：唯一 hunk 头 ＝ **`@@ -120,7 +120,14 @@ def parse_workflow(file_path: str) -> WorkflowDef:`** ⇒ **改动完全落在版本门禁块内**；**无**表解析／步骤解析／返回构造段 hunk（`table_id = str`／`step_id = str` 锚点各仍 **1** 处，未动）
- **✅ 不误伤（Coordinator 本人实测，决定性）**：
  ```
  ver=3.1(数字) → REJECT「版本号必须写成字符串 "3.1"…」    ← 症状消除
  ver=3(int) / None → REJECT
  ver='3.1'     → PASS                                    ← 既有配置零误伤
  ver='3.2' / '' → REJECT（原白名单逻辑不变）
  ```
- **门禁（重跑）**：`Ran 119 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **文件面**：`parser.py` 162 → **169 行**（+7，与 hunk 一致）；**本阶段未碰 `executor.py`**（证据＝parser.py 的 diff **仅 1 个 hunk**）
- **回滚点**：`backup/B1/阶段6/parser.py`（本阶段前内容）

**阶段 7（`B-42` ∥ `B-43`，新建测试）—— ✅ 已完成并复核 · 收官**

| 条目 | 产出（新文件） | 新增用例 | 覆盖要点 | 附件核实 |
|---|---|---|---|---|
| `B-42` | `rpa_engine/tests/test_ops_contracts.py`（**460 行**） | **60** | 9 项 BUILTIN_OPS 逐操作契约（filter 条件组合／**前导零按原文本传参**、dedup、aggregate 分组与指标解析、mapping_match JOIN＋`r_` 前缀、export 行数/缺省 sheet/路径校验、copy/merge、rename/convert、`guard_overwrite_target`）＋ `step_executor` 契约（`param_keys` 白名单、filter/dedup/export 缺省口径、输出表命名、返回值键集合 `{success,message,output_table,output_table_id}`、失败口径）＋ **三个解析器一致性与往返** | 相符 |
| `B-43` | `rpa_engine/tests/test_engine_failure_paths.py`（**144 行**） | **7** | `stop`→`ExecutionError`；**retry 耗尽**→`ExecutionError`；`skip`→不中断；**步骤间取消→`cancelled`**；**导出循环内取消→`cancelled`（`B-33`）**；**真实失败（无取消请求）→抛错且 `progress_callback` 如实上报 `failed`**；完成后中间表清理路径 | 相符 |

- **Coordinator 独立复核**：**用例数 119 → 186**（**+67**，>119 ✓）；仅新文件 `Ran 67 — OK`；双 `SMOKE_ALL_OK`；自检 `ok=True`；`doc_verify PASS`；**新文件 PyQt5 命中 0**／unittest 1／无 `eval-exec-pickle`；**tests 面 git 状态仅 1 个既有 `M`（`test_step_catalog.py`＝阶段 1 成果）＋ 2 个 `??`（新文件）** ⇒ **无既有测试被改、本阶段零源码改动** ✓
- **子 Agent 如实标注的两处"目标语义未落地"**（**均属台账 `[BLOCKED-越界]` 项，本轮**不施工** ⇒ 属预期**）：① `B-20` 的 skip 分支 `status` 仍 `completed`（未断言 `partial`，按现状断言并注释待修面）；② `B-36` 的 `output_tables` 清理后仍留派生表映射（按现状断言并注释待修面）
- **回滚**：新建型 ⇒ 回滚＝**删除两新文件**（无改前快照；不影响源码）

**🏁 B 链 13 项收官（R12，2026-10-19）**

- ✅ **13 项全部落地**：`B-01`／`B-02`／`B-13`（阶段 1）＋ `B-14`／`B-28`（阶段 2）＋ `B-15`／`B-16`／`B-31`（阶段 3）＋ `B-21`（阶段 4）＋ `B-33`（阶段 5）＋ `B-39`（阶段 6）＋ `B-42`／`B-43`（阶段 7）
- **门禁**：`Ran 186 tests — OK`（基线 118 → **+68**）｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`｜AGENTS 容量达标（余量 378）
- **越界**：**零**（阶段 5／6 对 `engine/` 的改动均经**逐 hunk** 证实在 `ensure_input_tables`／版本门禁块内；未动 GUI 布局；未改 9 项 BUILTIN_OPS 语义；无新依赖）
- **回滚点**：`backup/B1/阶段0`~`阶段6` 分阶段快照齐备
- **仍待人工**：**`P-2`（exe 重建 ＋ 真实 `.xls` 真机验证）** —— 13 项全绿**不等于**打包版可交付

### 0.8 多 Agent 协作机制

> **动机**：本文件 5,000+ 行、18 万+ 字符，**单 Agent 上下文无法容纳**。故按批次拆分给多个 Sub-Agent 并行/串行执行。
> **可执行性判据**：本节的协议是**硬约定**——标记名、触发条件、处理方式均已定死；Sub-Agent 不需要理解全局即可开工（每条的「§8 Agent 执行指引」给了它自己的上下文边界）。

#### 0.8.1 协作架构

| 角色 | 职责 | 读取范围（**关键**：不应整读 plan.md） |
|---|---|---|
| **Coordinator（总协调 Agent）** | ① 按批次分发任务；② 收集结果并核对交付物；③ 仲裁文件冲突；④ 执行批次门禁与最终验收；⑤ 汇总后交人工验收 | 仅 §0.1（范围）／§0.2（硬约束）／§0.2.1（执行须知）／§0.7（占位优先级）／§1.1（批次表）／§1.4（门禁）／§6.2（自检）／§6.3（闭合表）／§6.6（验收流程） |
| **Sub-Agent** | 只做被分配的那**一个批次**（批次内条目**顺序执行**） | **仅**该批次的条目（每条的 §1~§8）＋ 该条目 §8「上下文范围」列明的源码文件 |

#### 0.8.2 任务拆分规则

1. **按优先级批次拆分，不按单条目拆分**：同一批次（如 P3）的所有改造项交**同一个** Sub-Agent **顺序**执行。
2. **理由**：同批次条目常改**同一文件**（如 P1 的三项都在 `excel_preprocessor.py`；P3 的三项都在 `excel_normalizer.py`）——若拆给多个 Agent 会同时改同一文件而冲突。
3. **跨批次**：若两批次的目标文件**不重叠**，可分配给不同 Sub-Agent **同时开工**；重叠则串行。重叠名单见 §1.1 的「可并行」与「备注」两列。
4. **批次内的顺序**：以 §1.1「批次内容」列从左到右为序（P0 批内已显式排序）。

#### 0.8.3 通信协议（标记名全文统一，不得改写）

| 标记 | 触发条件 | 必须附带 |
|---|---|---|
| `[SUB_AGENT_COMPLETE]` | 该批次分配的全部条目已完成 | **交付物清单**：文件路径 ＋ 关键函数签名/接口契约 ＋ 本批新增/修改的行区间 |
| `[SUB_AGENT_BLOCKED]` | 遇到阻塞（改前片段定位失败、依赖缺失、测试环境不可用等） | 原因描述 ＋ **已尝试方案** ＋ 2~3 个**建议选项** |
| `[SUB_AGENT_CONFLICT]` | 检测到**同一文件被两方改动** | 冲突文件 ＋ 双方改动摘要 ＋ 冲突行区间 |
| `[REQUIRES_HUMAN_CONFIRMATION]` | 需人工裁决（含 Coordinator 无法仲裁的冲突） | 问题描述 ＋ 建议选项 ＋ 影响面 |

**升级规则**：Coordinator 收到 `[SUB_AGENT_BLOCKED]` 后，**先自行解决**（重定位、调整方案、改用降级策略）；确实无法解决时才升级为 `[REQUIRES_HUMAN_CONFIRMATION]`。

#### 0.8.4 交付物交接

1. 每个批次完成后，Sub-Agent 必须输出 **交付物清单**（文件列表 ＋ 关键函数签名/接口契约）。
2. **下一批次通过文件系统读取上批产物**，**不通过上下文传递**（避免上下文污染）。
3. Coordinator **确认文件存在**（`Test-Path`／`Read` 抽查）后才分发下一批次。
4. 批次门禁（§1.4）由 Coordinator 执行；未过门禁不得分发下一批。

#### 0.8.5 全局约束传递

Coordinator 在分发任务时，**必须**把以下三节作为**上下文前缀**发给每个 Sub-Agent，确保其知晓全局规则：

1. §0.1 本次范围（不可突破）；
2. §0.2 硬约束（8 条）；
3. §0.2.1 执行须知（语义示意，禁机械文本匹配）。

#### 0.8.6 Agent 名册

| Agent | 批次 | 范围 | 备注 |
|---|---|---|---|
| `Agent-P0` | P0 | `A-10`→`A-19`→`A-01`→`A-02`→`A-13`→`A-14`→`A-17` | 开工前须先核实 **8 项 P0 级 `[UNVERIFIED]`**（§1.5） |
| `Agent-P1` | P1 | `A-11`、`A-12`、`A-18` | 同一文件 → 串行 |
| `Agent-P2` | P2 | `A-03`、`REQ-R2` | — |
| `Agent-P3` | P3 | `A-05`、`REQ-R4`、`REQ-R5` | 同一新建文件 → 串行（**已修正**原"可并行"标注） |
| `Agent-P4` | P4 | `A-04`、`A-06`、`A-07`、`A-08`、`REQ-R7`、`REQ-H3`、`REQ-H4`、**`A-15`、`A-16`** | `A-15`/`A-16` 目标文件与其余条目不重叠，可拆并行 |
| `Agent-P5` | P5 | `REQ-H1`、`REQ-H5`、`REQ-H6`、`REQ-H7`、`REQ-H9`、`REQ-H10` | `REQ-H9` 依赖前者的产出 → 串行 |
| `Agent-P6` | P6 | `A-09` ＋ 端到端联调 | 需 `P-2`（人工 build）配合验证 |
| `Agent-B1` | B 类（本轮施工） | `B-01`~`B-44` | 可与 A 链并行；多数须待 P0 解锁后才**可验证** |
| `Agent-B2` | B 类（本轮登记不施工） | `B-45`~`B-79` | 本轮**不施工**，仅登记（触发条件见各条目） |

---

## Part 1 · 修复顺序与依赖图

### 1.1 批次顺序表

| 优先级 | 批次内容（含条目） | 项数 | 前置依赖 | 可并行 | 分配 Agent | 备注 |
|---|---|---|---|---|---|---|
| **P0** | **解锁导入链路 ＋ 异常隔离骨架** <br>`A-10`（导出 `source_path`）→ `A-19`（身份三元组比对）→ `A-01`（副本顺序与路径口径）→ `A-02`（异常元组扩容 ＋ 按钮复位）→ `A-13`（失败清单带类名）→ `A-14`（excepthook 过翻译层）→ `A-17`（`spec` 补 `'xlrd'` ＋ `requirements` 改 `xlrd>=2.0`） | 7 A | P-0 | ❌ **批内有序**（按左→右） | **`Agent-P0`** | 开工前须先核实 **8 项 P0 级 `[UNVERIFIED]`**（见 §1.5） |
| **P1** | **临时区与格式转换** <br>`A-11`（`copy2` mtime 与清理顺序）、`A-12`（同名异后缀覆盖）、`A-18`（转换产物冲突检测） | 3 A | P0 | ⚠️ 三项目标**同一文件** → **串行提交** | **`Agent-P1`** | 禁同批改同一文件（`excel_preprocessor.py`） |
| **P2** | **表头规范化** <br>`A-03`（表头禁字符预检）、`REQ-R2`（全空表头行拒绝） | 1 A＋1 REQ | P1 | ❌ | **`Agent-P2`** | 两者同属读取/预检入口 → 串行 |
| **P3** | **单元格处理 R3/R4/R5** <br>`A-05`（合并格拆分填充）、`REQ-R4`（公式兜底）、`REQ-R5`（超链接展开） | 1 A＋2 REQ | P2 | ❌ **三项的改动点全在新建文件 `ops/excel_normalizer.py` → 必须串行**（**已修正**原"✅ 三项彼此可并行"的标注，理由见 §1.2） | **`Agent-P3`** | 修正记录见 §1.2 第 3 条 |
| **P4** | **类型/内容/特殊值 ＋ 写库原子（含已裁定的 `G-5`）** <br>`A-04`（前导零与类型推断）、`A-06`（日期降级）、`A-07`（日期筛选 0 行）、`A-08`（NA 字面吞值）、`REQ-R7`、`REQ-H3`、`REQ-H4`、**`A-15`（写库非原子）**、**`A-16`（空壳表跳过补导）** | 6 A＋3 REQ | P3 | ⚠️ `A-15`／`A-16` 的目标文件（`sqlite_manager.py`／`engine/executor.py`）与其余条目**不重叠** → 可拆并行子 Agent（默认随 `Agent-P4` 顺序执行） | **`Agent-P4`** | `A-15`／`A-16` 已按 §1.6 裁定**并入本批**（原为「P-待裁定」） |
| **P5** | **元数据与报告** <br>`REQ-H1`、`REQ-H5`、`REQ-H6`、`REQ-H7`、`REQ-H9`、`REQ-H10` | 6 REQ | P4 | ⚠️ `REQ-H9` 依赖 `REQ-H1/H5/H6/H7` 的产出 → **串行** | **`Agent-P5`** | 同一新建文件的产出汇总关系 |
| **P6** | **接入导入流程与端到端联调** <br>`A-09`（扫描/预处理分离 ＋ 主线程阻塞）＋ 新建模块接线、阶段切换、GUI 错误回显联调 | 1 A | P5 | ❌ | **`Agent-P6`** | 需 `P-2`（人工 build）配合验证交付面 |
| **B 类** | `B-01`~`B-44`（P0/P1，七段式，**本轮施工**）；`B-45`~`B-79`（P2/P3，精简四段，**本轮仅登记**） | 79 B | 与 A 类无依赖者可随时并行（但多数须待 P0 解锁后才**可验证**） | ✅ | **`Agent-B1`**（`B-01`~`B-44`）／**`Agent-B2`**（`B-45`~`B-79`） | `B2` **本轮不施工**；`B1` 可与 A 链并行 |

### 1.2 顺序调整说明（相对提示词第四章）

**调整**：提示词原表把「P0 ＝ 异常隔离与单表容错机制」列为第一优先，并断言"当前问题是导入直接失败导致流程中断，若不先建立容错骨架，后续每一项修复失败都会再次导致整轮崩溃"。**本计划将 P0 调整为「解锁导入链路 ＋ 异常隔离骨架」合并批**，理由为三条已一手复核的代码证据：

1. **逐表 `try/except` 已存在**：`rpa_engine/gui/main_window.py::_on_confirm_import` L322-328 已按表捕获 `(ValueError, FileNotFoundError, PermissionError, OSError, sqlite3.Error)`，失败会累加进 `failed[]` 并在 L356-360 弹「部分导入失败」→ **单表隔离并非缺失**。
2. **主症状的真根因是副本生命周期**：`_on_confirm_import` L257 先调 `_close_session()`（其内部 `page_input_selection.py::clear_temp_copies` L357-374 删除全部导入副本），随后 L302-306 仍以 `e["file_path"]`（＝临时区副本路径）导入 → 抛 `FileNotFoundError`——**该异常已被 L322 捕获**。⇒ 只建骨架不能治主症状。
3. **异常元组的缺口是"哪一类异常"的问题**，而非"有没有 except"的问题：缺 `ImportError`（xlrd）／`zipfile.BadZipFile`／`lxml.etree.ParseError` → 属 `A-02`，与骨架建设同批完成后即闭合。

**未调整部分**：`P1`~`P6` 的规则推进顺序（R1→R2→R3/R4/R5→R6/R7→元数据报告→接入）**沿用提示词原序**。

**2026-10-18 修订带来的三处批次改动（本版新增）**

1. **`P-待裁定` 行已删除**：`A-15`／`A-16` 按 2026-10-18 修订指令**自主裁定 `G-5` 后并入 P4**（裁定内容见 §1.6；原门禁 `P-1` 的覆盖关系见 §0.3）。此举使可执行改造项由 108 项增至 **110 项**（全部 110 项本轮均可执行，唯 `B-45`~`B-79` 为登记不施工）。
2. **P4 的项数由「4 A＋3 REQ」变为「6 A＋3 REQ」**：新增 `A-15`、`A-16` 两项；其目标文件（`ops/sqlite_manager.py`、`engine/executor.py`）与 P4 其余条目（`ops/excel_normalizer.py`、`ops/exporter.py`）**不重叠**，故可在 P4 内拆分并行子 Agent。
3. **P3 的「可并行」由 ✅ 改为 ❌（自洽性修正）**：`A-05`／`REQ-R4`／`REQ-R5` 的改动点**同属新建文件 `ops/excel_normalizer.py`**（分别为 `split_merged_cells`／`resolve_formula_cells`／`expand_hyperlinks`），三项必须**在同一文件内串行落地**——原标注「✅ 三项彼此可并行」与本文件 §1.1 P1 行「禁同批改同一文件」原则自相矛盾，本版已修正。

### 1.3 依赖图

```
P-0（腾 AGENTS 容量）
  └─> P0（解锁＋隔离：A-10 → A-19 → A-01 → A-02 → A-13 → A-14 → A-17）
        ├─> P1（A-11, A-12, A-18）─> P2（A-03, REQ-R2）─> P3（A-05, REQ-R4, REQ-R5）※同文件串行
        │      └─> P4（A-04, A-06, A-07, A-08, REQ-R7, REQ-H3, REQ-H4 ＋ A-15, A-16）
        │            └─> P5（REQ-H1, REQ-H5, REQ-H6, REQ-H7, REQ-H9, REQ-H10）
        │                  └─> P6（A-09 ＋ 端到端联调）
        └─> B 类（B-01…B-79；多数须待 P0 完成后才可在真机验证）

P-1（**已解除**，2026-10-18）→ G-5 裁定见 §1.6，A-15/A-16 已并入 P4
P-2（人工 build ＋ 真机 .xls 验证）─> 验证 A-02 / A-17 的交付面
```

### 1.4 每批的门禁（批次完成后必须执行的验证动作）

| 批次 | 门禁动作 | 通过判据 |
|---|---|---|
| 每批 | 全量回归：`conda run -n CPS-GPES_RPA-py311 python -m unittest discover -s tests`（cwd＝`rpa_engine`） | 用例数不减（当前基线 118）且 `OK` |
| 每批 | 双冒烟：`rpa_engine/tools/smoke/smoke_m1m3.py`、`smoke_mb.py`（先设 `QT_QPA_PLATFORM=offscreen`） | 两脚本退出码 0 |
| 每批 | 启动自检 6 项：`rpa_engine/gui/app.py::run_self_check` | `r.ok == True` |
| 改规约后 | 文档体检：`conda run -n CPS-GPES_RPA-py311 python tools/doc_verify.py`（cwd＝仓库根） | `PASS`、链接 0 失败 |
| 涉 `AGENTS.md` | 容量三口径复测（含 CR ≤8,000／loneCR=0／loneLF=0） | 余量 ≥200 且本次新增后仍达标 |
| P6 后 | **真机会话**：在真机 GUI 上走完「选文件 → 确认并导入 → 配置 → 执行 → 导出」（人工执行） | P0 解锁后的簇 1／簇 2 路径可走通 |
| P-2 后 | 人工构建 ＋ 真实 `.xls` 导入成功 | exe 态不再出现 `No module named 'xlrd'` |

### 1.5 P0 批次的动手前核实义务（硬性）

`Agent-P0`（以及任何承担 P0 批次条目的 Sub-Agent）在**动手前**必须：

1. 先清掉该批次涉及的 **8 项 P0 级 `[UNVERIFIED]`**（清单见 §0.7 第 1~8 行；明细见 §6.4 第 1~8 行）：
   `A-01`（`_IMPORT_ROOTS` 语义）、`A-10`（`to_dict` 赋值行号）、`A-14`（`app.py` import 区与钩子注册行号）、`B-05`（终止按钮控件名与判定位置）、`B-06`（`EngineWorker` 构造点）、`B-07`（`start_workflow` 行号）、`B-11`（四处 `_ignore_next_finish` 行号）、`B-13`（`run_self_check` 比对行号）。
2. 把核实结果**回填到对应条目的相应字段**（把 `[UNVERIFIED]` 替换为实测行号/结论）。
3. **未回填不得开工**；若某处核实发现与本计划记载**冲突**，按 §0.6「冲突以代码为准」处理，并在交付物清单中说明差异。
4. 核实过程中若发现阻塞（例如 `_IMPORT_ROOTS` 不允许 `source_path` 所在目录），输出 `[SUB_AGENT_BLOCKED]`（标记定义见 §0.8.3）并附建议选项，不得自行放宽安全边界。

### 1.6 `G-5` 裁定（2026-10-18，本版新增；解除 `A-15`/`A-16` 的「P-待裁定」）

**裁定结论（三件套）**

1. **`G-5①` 活表覆盖守卫**：`rpa_engine/ops/table_lifecycle.py` 新增 `guard_overwrite_target(conn, output_table) -> None`；判据＝「表存在**且** `table_row_count > 0` → 抛中文 `ValueError`」。
   复用方（**必须同源，不得各写一套**）：`filter_dedup.py`（L81／L155 两处）、`aggregator.py`（产表处）、`mapping_matcher.py`（L217）、`table_lifecycle.py::merge_tables`（L196-203）。
2. **`G-5②` 写入原子性**：`rpa_engine/ops/sqlite_manager.py` 新增 `import_dataframe_atomic(df, table_name, conn, if_exists="replace", tmp_suffix="__tmp_import") -> int`；流程＝「建临时表（唯一后缀）→ `to_sql` → 校验行数 == `len(df)` → `DROP` 旧表 → `ALTER TABLE ... RENAME TO`」；**任一步失败都不留半成品**（`except` 内 `DROP` 临时表）。`table_importer.py` 的落库调用改用它；`import_dataframe` **保留不动**（签名与行为不变）。
3. **`G-5③` 有效性判据**：`rpa_engine/engine/executor.py::ensure_input_tables` 的短路条件改为「表存在**且**行数 > 0」（空壳表视为需补导）。

**裁定依据与理由**

1. **技术实质来自既有裁定**：problem.md 附录 C 的 **裁定 Q7** 已给出「临时表 → 校验行数 → 原子 rename」的实质结论；本裁定**不改其技术实质**，只补齐 ① 守卫与 ③ 判据的落点。
2. **门禁覆盖关系（显式记录，不得静默）**：problem.md 附录 G 第 8 项与裁定 Q2 设有「`G-5` 须**先出方案再裁定**」的人工门禁；**`plan.md` 修订指令（2026-10-18）**明确要求"自主裁定 `G-5` 并解除待裁定状态" → **本裁定由该指令授权解除该门禁**，原裁定引用保留可溯（见 §0.3 的 `P-1` 行）。
3. **不违反立法目的**：该门禁所防的是"**无方案即施工**"；本版已给出完整方案（①＋②＋③，且 `A-15`／`A-16` 的「3. 修改方案」已含逐改动点的改前/改后），门禁的适用前提已消失。
4. **落地位置**：`G-5②`＋`G-5①` 由 `A-15` 承载、`G-5③` 由 `A-16` 承载；两者已并入 **P4**（见 §1.1），其目标文件（`sqlite_manager.py`／`executor.py`）与 P4 其余条目**不重叠**。

**残余风险（须在交付物清单中声明）**

- ① `ALTER TABLE ... RENAME TO` 在 WAL 下可能引入锁等待 → 降级路径见 `A-15` §6。
- ② `table_row_count` 引入 `engine/executor.py` 需实测无循环导入（属 `[UNVERIFIED]`，见 §0.7 第 9 行）。
- ③ 守卫会拦住"故意覆盖非空活表"的既有用法——这是**需求意图**，须在报告与提示中说明"请改用新表名"。


---

## Part 2 · A 类问题逐项改造方案（19 项）

> 顺序＝problem.md 的 A 编号顺序；每项标题下注明所属**批次**（施工顺序见 Part 1 §1.1）。
> 每项含七段：定位／现状与缺陷判定／修改方案／约束／验证／风险与回滚／验收标准。

---

### A-01 [原编号: F-01] 经 [add] 选入的文件导入 100% 失败

> 规则：R1＋H10 ｜ 等级：文件级 ｜ **批次：P0** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/gui/main_window.py`、`rpa_engine/gui/page_input_selection.py`
- 目标：`MainWindow._on_confirm_import`（L241-400）／`InputSelectionPage.clear_temp_copies`（L357-374）／`InputSelectionPage.get_entries`（L324-335）
- 调用链：上游 `InputSelectionPage._on_import`（L431-461）→ `confirm_import.emit` → 本处 `MainWindow._on_confirm_import` L257（`_close_session()`）与 L303（`import_excel_table`）→ 下游 `ops/table_importer.py::import_excel_table`
- 存在性判定：✅ 已存在（三个函数均已存在）

#### 2. 现状与缺陷判定
```python
# main_window.py L256-257（导入前先关会话）
        # 关闭旧会话（新一轮确认）
        self._close_session()
# main_window.py L302-306（仍用副本路径导入）
            try:
                import_excel_table(
                    conn, e["file_path"], e["sheet_name"],
                    int(e["header_row"]), sqlite_table,
                )
# page_input_selection.py L366-368（清理即物理删除）
                if p.is_file():
                    p.unlink()
                    removed += 1
```
- 缺陷类型：**【逻辑错误】**（副本"先删后用"＋路径口径用副本而非原始文件）
- 阻断后果链：`_on_confirm_import` L257 → `_close_session()` → `clear_temp_copies()` L367 `p.unlink()` 删除本轮全部 `.xlsx` 副本 → L303 读 `e["file_path"]`（＝副本路径）→ `FileNotFoundError` → L322 捕获入 `failed[]` → L361-364「全部数据表导入失败，无法继续」→ **中止于阶段 1/2 之间，阶段 2/3/4 全部不可达**

#### 3. 修改方案
**A. 修改型**（目标已存在；三处改动**必须同批**）
- 改动点 1：`page_input_selection.py::get_entries` L329-334
  - 改前：字典键为 `file_path`／`sheet_name`／`alias`／`header_row`
  - 改后：追加 `"source_path": str(entry.source_path or entry.file_path),`
  - 说明：`InputEntry` 已有 `source_path` 字段且 `_add_row`（签名 L467-475）已接收并在 L494 写入 → 只需在此导出它（承接 `A-10`）
- 改动点 2：`main_window.py::_on_confirm_import` L302-306
  - 改前：`import_excel_table(conn, e["file_path"], e["sheet_name"], int(e["header_row"]), sqlite_table,)`
  - 改后：
    ```python
    src = e.get("source_path") or e["file_path"]
    import_excel_table(conn, src, e["sheet_name"],
                       int(e["header_row"]), sqlite_table,)
    ```
  - 说明：导入优先读原始文件；原始文件缺失时回落副本（保兼容）
- 改动点 3：`page_input_selection.py` 新增 `clear_temp_copies()` 的**延后调用点**
  - 改前：`clear_temp_copies()` 只在 `main_window.py::_close_session` L462-463 被调用（即导入前）
  - 改后：新增方法 `InputSelectionPage.prune_copies(items: List[Path]) -> int`（只删传入清单内的副本），并在 `main_window.py::_on_confirm_import` L330（导入循环结束、`progress.setValue(len(entries))` 之后）调用；`_close_session()` 内改为只调用 `prune_copies([])`＋会话库收口
  - 说明：副本在本轮导入**完成之后**才回收，消除"先删后用"
- **B. 新建型**：不适用
- **C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：阶段 1 页面布局与表格列定义；`import_excel_table` 的 6 参数签名
- 不可引入的新依赖：是
- 必须保留的接口/信号：`InputSelectionPage.confirm_import` 信号（`main_window.py` L211-218 已连接）；`clear_temp_copies` 方法名（`main_window.py` L463 引用，若改名须同步）
- 必须遵循的规约：`AGENTS.md` §2.2 条 4（不自建连接）；`AGENTS.md` §2.1 条 6（错误人话化）；**路径白名单**——`engine/executor.py` L40-68 定义 `_IMPORT_ROOTS`，仅在 `ensure_input_tables`（L105 `_validate_import_path`）生效；`main_window.py` L303 的直调**不经该白名单**。实施者须先读 L40-68 确认语义：若 `source_path` 所在目录不被允许，须在 GUI 侧补等价校验（拒绝不存在路径／非 `.xlsx/.xls` 后缀）或回报人工调整白名单 `[UNVERIFIED]`

#### 5. 验证
- 用例构造：新建 2 sheet 的 `样本A.xlsx`（sheet 名 `1月`／`2月`），阶段 1 用 [add] 选入 → 勾选两行 → 点「确认并导入」
- 期望输出：阶段 2 正确显示 T1／T2 两个表；画布出现两张表节点；`temp/input_selection/` 下副本在导入完成后被回收
- 失败判据：出现「全部数据表导入失败，无法继续」；日志出现 `导入失败 <alias>: FileNotFoundError`；阶段 1 重开后列表为空
- 自证方式：`logs/gui_*.log` 断言无 `FileNotFoundError`；临时库（`keep_db=true`）中 `SELECT COUNT(*) FROM t1`／`t2` 均 > 0

#### 6. 风险与回滚
- 可能回归点：① 手工构造的无 `source_path` 条目 → 依赖回落分支；② 副本回收延后使 `temp/input_selection/` 暂存增多；③ 白名单校验过严误拦合法文件
- 回滚方式：改前将 `main_window.py`／`page_input_selection.py` 复制到 `_temp/ImportData/backup/`（实施者创建），回退＝覆盖还原
- 降级策略：若「改动点 3」实现成本过高，采用**备选**——`_close_session()` 不动，仅把 `clear_temp_copies()` 的调用从 `_close_session()` 内移出到「新一轮操作／退出」路径；若 GUI 侧白名单无法实现，则回报人工并在 `executor._validate_import_path` 侧纳入 `source_path` 目录

#### 7. 验收标准
- [ ] 阶段 1 用 [add] 选入 2 个 sheet 全部导入成功，阶段 2 正确显示
- [ ] 关闭程序重开，「恢复上次配置」能回填表清单，无 `FileNotFoundError`
- [ ] 118 用例回归全绿 ＋ 双 smoke 退出码 0 ＋ 启动自检 6 项通过

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/main_window.py`、`rpa_engine/gui/page_input_selection.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-02 [原编号: H-01（＋J-03 已并入）] exe 态 `.xls` 导入崩溃 ＋ 入口按钮锁死

> 规则：R1＋H10 ｜ 等级：文件级 ｜ **批次：P0** ｜ 判定：**【缺少容错】** ｜ 状态：`[FIXED-PARTIAL]`

#### 1. 定位
- 文件：`rpa_engine/gui/page_input_selection.py`、`rpa_engine/ops/excel_preprocessor.py`、`RPA_Workflow_v3.spec`、`rpa_engine/gui/app.py`
- 目标：`InputSelectionPage._on_add_files`（L376-429，异常元组在 L417）／`ensure_xlsx`（L70-128，`engine="xlrd"` 在 L102）／`spec` 的 `hiddenimports` 段／`app.py::_excepthook`（L259-266）
- 调用链：上游 `_on_add_files`（L376）→ 本处 `validate_and_copy`／`ensure_xlsx`／`_scan_sheets` → 下游 `app.py` 的 `sys.excepthook`
- 存在性判定：✅ 已存在（需改异常元组与打包清单）

#### 2. 现状与缺陷判定
```python
# page_input_selection.py L417（异常元组缺口）
            except (FileNotFoundError, ValueError, PermissionError) as e:
                logger.warning(f"[input_selection] 文件处理失败 {fpath}: {e}")
                QMessageBox.warning(self, "提示", f"文件处理失败：\n{fpath}\n\n{e}")
                continue
# excel_preprocessor.py L102（字符串 engine，全库无 import xlrd）
    sheets = pd.read_excel(src, engine="xlrd", sheet_name=None)
```
- 缺陷类型：**【缺少容错】**（打包缺项 ＋ 异常元组覆盖不全，二者耦合）
- 阻断后果链：exe 态 `xlrd` 缺失 → `pd.read_excel(engine="xlrd")` 抛 `ImportError` → 不在 L417 元组内 → **逃出槽函数** → `app.py::_excepthook` L259-266 接管 → ①循环中断、同批其后文件**完全不处理** ②L429 `self._btn_import.setEnabled(len(self._entries) > 0)` **未执行** → 入口按钮保持禁用 → **文件级中断 ＋ 流程卡死**；`J-03`（加密容器 OLE2／BIFF 改名／纯文本改名／zip 截断／0 字节 → `zipfile.BadZipFile`；sheet XML 损坏 → `lxml.etree.ParseError`）为同一元组缺口的第 2 类触发源

#### 3. 修改方案
**A. 修改型**（目标已存在）
- 改动点 1：`page_input_selection.py::_on_add_files` L417
  - 改前：`except (FileNotFoundError, ValueError, PermissionError) as e:`
  - 改后：`except (FileNotFoundError, ValueError, PermissionError, ImportError, OSError) as e:` ＋ 追加一条针对 `zipfile.BadZipFile`／`lxml.etree.ParseError` 的分支（二者非 `OSError` 子类，须显式列出，例如 `except (ImportError, OSError, zipfile.BadZipFile, lxml.etree.ParseError) as e:`，并在文件头补 `import zipfile`；`lxml` 若不便导入则用 `Exception` 兜底但需记录 `type(e).__name__`）
  - 说明：把"单个文件失败"限制在**该文件**内，不逃出槽函数；`continue` 语义保持不变
- 改动点 2：同函数 L422-429
  - 改前：`setEnabled` 仅出现在 L429（异常逃逸时到不了）
  - 改后：把 `self._btn_import.setEnabled(len(self._entries) > 0)` 移入 `finally:`（或用 `try/finally` 包住整个 `for` 循环）
  - 说明：无论中途是否异常，按钮状态始终复位
- 改动点 3：`RPA_Workflow_v3.spec` 的 `hiddenimports`
  - 改前：17 项（含 13 个 ops 模块），**无 `'xlrd'`**
  - 改后：追加 `'xlrd',`（附注释 `# xlrd 以字符串形式传给 pandas.read_excel(engine="xlrd")，从未被 import，PyInstaller 静态分析收集不到`）
  - 说明：补齐打包链（另见 `A-17`）
- 改动点 4：`page_input_selection.py::_on_add_files` L418-419
  - 改前：`QMessageBox.warning(self, "提示", f"文件处理失败：\n{fpath}\n\n{e}")`
  - 改后：`QMessageBox.warning(self, "提示", f"文件处理失败：\n{fpath}\n\n{translate_error(f'{type(e).__name__}: {e}')}")`（须在文件头 `from gui.error_messages import translate_error`）
  - 说明：原始异常仅进日志，用户面走人话（承接 `A-13` 的同类口径）
- **B. 新建型**：不适用
- **C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`ensure_xlsx` 的签名与返回语义；`spec` 的 `datas`／入口配置
- 不可引入的新依赖：是（`xlrd` 已在 `requirements.txt`，**不是新依赖**；`zipfile` 属标准库）
- 必须保留的接口/信号：`_on_add_files` 的方法名与槽绑定；`_btn_import` 对象名
- 必须遵循的规约：`AGENTS.md` §2.1 条 6（人话）；`docs/build-guide.md` §1.10（构建产物有效性）；`office-plugin` 不适用；改 `spec` 属交付配置变更，**构建由人工执行**（裁定 R2）

#### 5. 验证
- 用例构造：① 一组 `a.xlsx` ＋ `b.xls` ＋ `c.xlsx`（exe 态）② 一个改名成 `.xlsx` 的 BIFF 文件 ③ 一个 0 字节 `.xlsx`
- 期望输出：三个文件各自被独立处理——`a.xlsx`／`c.xlsx` 正常入行，`b.xls` 若打包缺件则**只该文件失败并给人话**，其余不受影响；按钮始终可用
- 失败判据：出现未捕获异常弹窗（技术原文）；同批后续文件未被处理；按钮保持禁用
- 自证方式：`logs/gui_*.log` 见 `[input_selection] 文件处理失败 <path>: ImportError` 但**无** `[gui] 未预期异常`；UI 上「确认并导入」按钮可点

#### 6. 风险与回滚
- 可能回归点：① 异常元组放宽后误吞编程错误（用 `type(e).__name__` 记日志以保排查）；② `finally` 中 `setEnabled` 与既有 `_rebuild_table` 的按钮状态逻辑冲突
- 回滚方式：`spec` 与 `page_input_selection.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：`lxml` 导入失败时以 `except Exception` 兜底但**必须**记录类名；若 exe 重建后 `xlrd` 仍缺失，回落为「入口拒绝 `.xls` 并给明确提示」（R1 的文件级中止语义）

#### 7. 验收标准
- [ ] exe 态选 `.xls` 不再弹技术原文；该文件失败时**其余文件仍被处理**，按钮可用
- [ ] 源码态选损坏／0 字节 xlsx 时只该文件失败，不逃出槽函数
- [ ] `spec` 的 `hiddenimports` 含 `'xlrd'`；人工重建后 `build/BUILD_INFO.txt` 指纹回填

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/page_input_selection.py`、`rpa_engine/ops/excel_preprocessor.py`、`RPA_Workflow_v3.spec`、`rpa_engine/gui/app.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-03 [原编号: G-06] 表头含换行/制表符 → 整表操作 100% 失败

> 规则：R2 ｜ 等级：表级 ｜ **批次：P2** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/ops/sql_safety.py`、`rpa_engine/ops/excel_preprocessor.py`、`rpa_engine/gui/error_messages.py`
- 目标：`sql_safety.quote_ident`（L39-66，禁字符常量在 L36）／`read_excel_sheet`（L171-220）／导入预检落点 `ops/table_importer.py::import_excel_table`（L29-101）
- 调用链：上游 `main_window.py::_on_confirm_import` L303 → `import_excel_table` → 本处 `read_excel_sheet` L210 读取表头 → 下游 `sqlite_manager.import_dataframe` L149 `to_sql` → `quote_ident`
- 存在性判定：✅ 已存在（校验已存在，**预检缺失**）

#### 2. 现状与缺陷判定
```python
# sql_safety.py L36 与 L58-62
_FORBIDDEN_IDENT_CHARS = ('"', "\x00", "\n", "\r", "\t")
...
    for ch in _FORBIDDEN_IDENT_CHARS:
        if ch in name:
            raise ValueError(
                f"quote_ident: 标识符包含禁止字符 {repr(ch)}: {name!r}"
            )
# excel_preprocessor.py L210-215（表头原样，无预检）
    df = pd.read_excel(
        str(src),
        sheet_name=sheet_name,
        skiprows=header_row - 1,
        header=0,
    )
```
- 缺陷类型：**【缺少容错】**（禁用字符校验只在建表期抛错；读入期无预检，错误在人话层面不可达且发生在半途）
- 阻断后果链：Excel 表头含 `\n`／`\t` → `pd.read_excel` 原样带入列名 → `to_sql` 建表经 `quote_ident` → `ValueError: 标识符包含禁止字符 '\n'` → `main_window.py` L322 捕获入 `failed[]` → **表级失败**（其余表因逐表 try 仍可导入），且用户看到的是技术原文而非"哪张表哪个表头有问题"

#### 3. 修改方案
**A. 修改型**（目标已存在）＋ 少量新建逻辑
- 改动点 1：`ops/table_importer.py::import_excel_table`（在 L76 `read_excel_sheet` 之后、L91 `import_dataframe` 之前插入）
  - 改前：直接 `import_dataframe(df, table_name, conn, if_exists="replace")`
  - 改后：插入三段校验——
    ① 逐列名检测 `_FORBIDDEN_IDENT_CHARS`（复用 `sql_safety._FORBIDDEN_IDENT_CHARS`，**不从外部硬编码字符表**）；命中则 `raise ValueError(f"数据表 [{sheet_name}] 的第 {i+1} 列表头包含不可用字符 {repr(ch)}（常见于表头里的换行或制表符），请先在 Excel 中清理该表头后重试")`
    ② 检测空列名（`""`／`"nan"`）→ 按 `REQ-H1` 归一为 `未命名列_{i}` 并记报告
    ③ 检测列名重复 → 按 `REQ-H1` 去重
  - 说明：把失败**前移**到导入入口，并给人话＋定位（第几列、什么字符）
- 改动点 2：`rpa_engine/gui/error_messages.py::_RULES`（L20-41）
  - 改前：无"标识符含禁止字符"规则（原记载：该规则目前缺失）
  - 改后：在 `_RULES` 内新增一条（放在 `("no such column", ...)` 之前，保证特异规则优先）：
    ```python
    ("标识符包含禁止字符", "该数据表的表头里有不可用的字符（常见为换行或制表符）。",
     "请在 Excel 中清理该表头后重新导入。"),
    ```
  - 说明：沿既有「键＝原始文本子串（小写）」机制（`translate_error` 已对输入 `.lower()`），故键须为小写
- **B. 新建型**：不适用（无新文件）
- **C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`quote_ident` 的禁字符集合与抛错行为（保持"所见即所得"：**不得**静默清洗列名——裁定 G1）；`read_excel_sheet` 返回值结构
- 不可引入的新依赖：是
- 必须保留的接口/信号：`import_dataframe` 的签名；`quote_ident` 的行为
- 必须遵循的规约：`AGENTS.md` §2.1 条 6（人话）；裁定 G1「导入前预检并拒绝 ＋ 人话提示」（**不得**静默改名清洗）

#### 5. 验证
- 用例构造：构造 `表头异常.xlsx`，第 1 行表头写 `金额\n（元）`（含换行）与 `数量\t`（含制表符）
- 期望输出：该表导入失败，弹窗/失败清单出现中文说明并指出具体列号；同批其他表正常入库
- 失败判据：用户看到 `标识符包含禁止字符` 原文；或该表被静默导入（列名被偷偷清洗）
- 自证方式：`logs/gui_*.log` 见 `导入失败 <alias>: ValueError: 数据表 [<sheet>] 的第 2 列表头包含不可用字符`；UI 失败清单文本为中文人话

#### 6. 风险与回滚
- 可能回归点：① 预检使原本"能导入"的脏表头变为失败（**这是预期行为**，须在用户手册/提示中说明）；② 与 `REQ-H1` 的列名去重逻辑重复执行
- 回滚方式：`table_importer.py`／`error_messages.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若预检引发回归，至少保留 `error_messages` 的新规则（把技术原文变人话），预检降级为「WARNING 并继续」

#### 7. 验收标准
- [ ] 含换行/制表符表头的表**失败并给出中文化提示（含列号）**，同批其他表不受影响
- [ ] 中文、空格、括号列名**仍可正常导入**（不得因预检误伤）
- [ ] 回归全绿（含 `tests/test_error_messages.py` 的禁用词断言）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/sql_safety.py`、`rpa_engine/ops/excel_preprocessor.py`、`rpa_engine/gui/error_messages.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-04 [原编号: J-01] 文本型数字列的前导零在导入入口被整列抹掉

> 规则：R6＋H7 ｜ 等级：单元格级 ｜ **批次：P4** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_preprocessor.py`（读取入口）＋ 新建 `rpa_engine/ops/excel_normalizer.py`
- 目标：`read_excel_sheet`（L171-220，`pd.read_excel` 在 L210-215）；新模块的类型推断函数（见 Part 4 契约）
- 调用链：上游 `table_importer.import_excel_table` L76 → 本处 `read_excel_sheet` → 下游 `sqlite_manager.import_dataframe` L149
- 存在性判定：⚠️ 部分存在（读取已存在；**类型推断规则未实现**）

#### 2. 现状与缺陷判定
```python
# excel_preprocessor.py L210-215（无 dtype、无 infer 抑制）
    df = pd.read_excel(
        str(src),
        sheet_name=sheet_name,
        skiprows=header_row - 1,
        header=0,
    )
```
- 缺陷类型：**【缺失实现】**（R6 未实现；丢值发生在 pandas 解析层，早于任何业务逻辑）
- 阻断后果链：Excel 文本列 `['007','008','009']` → `pd.read_excel` 无 dtype 约束 → pandas 强转 `int64` → 落库 INTEGER → 导出后 `7/8/9` → **前导零不可逆丢失**（预览层显示仍为 `007`，用户零感知；身份证号／订单号／电表号全错）

#### 3. 修改方案
**B. 新建型 ＋ A. 修改型（组合）**
- 改动点 1（新建）：`rpa_engine/ops/excel_normalizer.py`
  - 骨架（完整骨架见 Part 4 §4.2）：核心函数
    ```python
    def infer_cell_type(raw: str, max_significant_digits: int = 5) -> tuple:
        """按 R6 判定单元格目标类型。

        规则：空值→NULL；整数且去负号后位数 ≤ 阈值→int；
        浮点且有效数字 ≤ 阈值→float；其余（超长数字、身份证、订单号、
        前导零编码）一律 str。
        Returns: (value, target_type)  target_type ∈ {"NULL","int","float","str"}
        """
    ```
  - 判定细则（**须逐条实现，不得用"酌情"口径**）：
    ① `raw` 去首尾空白后为空／`""` → `(None, "NULL")`
    ② 正则 `^-?\d+$`：去负号后 `len(digits) <= max_significant_digits` → `(int(digits), "int")`；否则 → `(raw, "str")`
       - **特例（先于 ② 判定）**：以 `0` 开头且长度 > 1 的数字串（前导零编码）→ 直接 `(raw, "str")`
    ③ 正则 `^-?\d*\.\d+$`（且 `m.group(1)+m.group(2)` 有效数字位数 ≤ 阈值）→ `(float(raw), "float")`；否则 → `(raw, "str")`
    ④ 其余 → `(raw, "str")`
  - 阈值来源：`max_significant_digits` 默认 5，**须可配置**（从 JSON `global` 读，缺省 5；不得硬编码在业务分支里）

> **[裁定] `[P4-7]` 阈值／空值策略的 JSON `global` 接线 → 维持默认（2026-10-18，留待后续专项）**
> - **裁定结论**：维持当前默认（`max_significant_digits=5`／`na_policy="preserve"`）；本项的"须可配置"**暂不接线**。
> - **原因**：真正接线需**改 `import_excel_table` 的签名**以透传 `global_config`，而签名与返回值受 **§0.2 条 2 硬约束保护**（不改既有签名）→ **架构死锁**；透传链路横跨 `engine → table_importer → normalize_sheet` 多个模块，不适合仓促处理。
> - **当前默认值合理**：阈值 5 位／字面 NA 保留，**不导致数据错误**（已在 P4／P6 实测）。
> - **后续专项建议**：先设计完整的 `global_config` 透传链路（含 JSON 参数 Schema 与引擎注入点）再实施。
> - 完整留痕见 §0.7.6「遗留项终态」。

- 改动点 2（修改）：`ops/table_importer.py::import_excel_table` L76
  - 改前：`df = read_excel_sheet(xlsx_path, sheet_name, header_row, sheet_info=sheet_info)`
  - 改后：`result = normalize_sheet(xlsx_path, sheet_name, header_row, sheet_info=sheet_info, max_significant_digits=<全局配置>)`；`df = result.dataframe`
  - 说明：读取仍在 `excel_preprocessor`（不在其内做类型推断），**规范化在 normalizer 内完成**
- **C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`read_excel_sheet` 的签名与返回值；`import_dataframe` 的行为
- 不可引入的新依赖：是（仅 `re`／`pandas`／`openpyxl`）
- 必须保留的接口/信号：`import_excel_table` 的 6 参数签名与 `int` 返回值
- 必须遵循的规约：R6 规则定义（**不得修改规则本身**，只做实现）；`AGENTS.md` §2.1 条 5（内存）；`docs/function-spec-rules.md`（属 Layer 0 模块，**不登记 `BUILTIN_OPS`**，见 Part 4 §4.1）

#### 5. 验证
- 用例构造：`类型推断.xlsx` 第 1 行表头 `编码|金额|身份证|数量`；数据行 `007|1234.56|440101199001011234|12`
- 期望输出：落库后 `PRAGMA table_info` 显示 `编码` 为 TEXT、值为 `'007'`；`金额` 为 REAL `1234.56`；`身份证` 为 TEXT 且原文完整；`数量` 为 INTEGER `12`
- 失败判据：`编码` 变为 `7`（INTEGER）；`身份证` 被截断或转数字；导出后前导零消失
- 自证方式：临时库 `SELECT 编码, typeof(编码), 身份证 FROM t1 LIMIT 1`；导出文件回读比对原文

#### 6. 风险与回滚
- 可能回归点：① 阈值过小使本该是数字的短列变 str（如 `金额 = 1000000` 7 位 → str）；② 逐单元格 Python 循环拖慢大表
- 回滚方式：`table_importer.py` 备份；normalizer 为新增文件，回退＝删除文件并还原 `table_importer.py` 调用行
- 降级策略：大表（> `MEMORY_WARN_ROWS = 500_000`）时允许降级为「按列采样前 N 行推断整列类型」（须在报告中标注"抽样推断"），并在 `REQ-H9` 报告中如实记录

#### 7. 验收标准
- [ ] `007` 类前导零编码导入后仍为文本 `007`，导出回读一致
- [ ] 短整数仍为 INTEGER、短小数仍为 REAL（未被一律转 str）
- [ ] 阈值可由 JSON 配置覆盖；超阈值的长数字一律 str

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_preprocessor.py`（读取入口）＋ 新建 `rpa_engine/ops/excel_normalizer.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-05 [原编号: H-09] 合并单元格：预览前向填充、真实导入不填 → 分组统计 100% 错

> 规则：R3＋H8 ｜ 等级：表级 ｜ **批次：P3** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）＋ `rpa_engine/gui/page_input_selection.py`（预览侧，仅作对照）
- 目标：normalizer 的 `split_merged_cells`；预览侧 `InputSelectionPage._preview_rows`（L644 起）
- 调用链：上游 `table_importer.import_excel_table` → `normalize_sheet` → 本处合并格拆分 → 下游 `import_dataframe`
- 存在性判定：❌ 不存在（真实导入路径**全链路无 merged_cells 处理**）

#### 2. 现状与缺陷判定
```python
# page_input_selection.py 预览侧填充（仅作用于预览副本，真实路径无对应实现）
# 该处按合并格前向填充预览行；而真实导入：
# excel_preprocessor.py L210-215  pd.read_excel(...)  →  未拆分的合并格仅左上角有值
```
- 缺陷类型：**【缺失实现】**（预览与真实导入行为不一致；R3 未实现）
- 阻断后果链：含合并单元格的报表 → 预览显示"华东/华东/华东"、真实入库只有第 1 行有值 → 未填充单元格读为 `None` → 落库 NULL → `aggregate` 产生一个 NULL 分组（如"华东=100 ＋ NULL=500"）→ **表级结果错误**，界面提示与真实行为不符 → 用户不可察觉

#### 3. 修改方案
**B. 新建型**（normalizer 内新函数）
- 新建位置：`rpa_engine/ops/excel_normalizer.py`（与 `REQ-R4`／`REQ-R5`／`A-04` 共用同一新文件，**各自独立函数**）
- 骨架：
  ```python
  def split_merged_cells(ws, df: "pd.DataFrame", header_rows: int) -> tuple:
      """R3：把所有合并单元格拆开，原内容复制到每一个被拆出的单元格。

      Args:
          ws: 已打开的 openpyxl 工作表（只读/全量由调用方决定）。
          df: 已按表头行读入的 DataFrame（列名已上移）。
          header_rows: 表头占用的行数（默认 1）。
      Returns:
          (df_out, splits)  splits 为每条拆分的 (sheet, 首格坐标, 波及行列数, 值)
      """
  ```
- 实现要点（**须逐条落地**）：① 用 `ws.merged_cells.ranges` 取全部合并区；② 对每个区取左上角值，写入该区覆盖的所有单元格（与 `df` 的行列坐标对齐，须计入 `skiprows` 偏移）；③ 每条拆分记入 `splits` 供 `REQ-H9` 报告；④ **不修改**临时区文件本体（只改内存 DataFrame）
- 注意：不得改变 `normalize_sheet` 的返回结构（`NormalizeResult`，见 Part 4）
- **A. 修改型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：预览侧 `_preview_rows` 的现有行为（本项只修**真实导入路径**；预览与真实的一致性由 `A-09`＋`REQ-H9` 的提示承载）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`normalize_sheet` 的签名与 `NormalizeResult` 字段
- 必须遵循的规约：R3 规则定义；`AGENTS.md` §2.1 条 5（不得在内存中复制第二份全量 DataFrame——拆分须就地写回或用 openpyxl 侧数据构造）

#### 5. 验证
- 用例构造：`合并格.xlsx`——A 列 `地区` 的 A2:A4 合并为 `华东`，B 列 `金额` 为 100／200／300
- 期望输出：入库后 3 行 `地区` 均为 `华东`；`SELECT 地区, SUM(金额) FROM t1 GROUP BY 地区` 得 `华东=600`（**无 NULL 分组**）
- 失败判据：出现 `NULL=500` 分组；或仅第 1 行有 `华东`
- 自证方式：临时库 `SELECT 地区, COUNT(*) FROM t1 GROUP BY 地区`；`REQ-H9` 报告中出现对应拆分记录

#### 6. 风险与回滚
- 可能回归点：① 拆分后数据量与用户预期不符（原本"空"的格被填值）；② 大合并区（如整列合并）导致值污染
- 回滚方式：normalizer 为新增文件；回退＝在 `table_importer` 调用处回切 `read_excel_sheet`
- 降级策略：若某 sheet 的合并区数量超阈值（如 > 10,000），降级为「仅记录 `splits` 并在报告中告警，不做拆分」，避免超时（须如实标注"未拆分"）

#### 7. 验收标准
- [ ] 合并格拆分后分组统计结果与预览/预期一致，无 NULL 分组
- [ ] `REQ-H9` 报告中可查每条拆分的坐标与值
- [ ] 拆分不修改临时区文件本体（回读原文件仍为合并状态）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）＋ `rpa_engine/gui/page_input_selection.py`（预览侧，仅作对照）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-06 [原编号: H-15] 导出时日期降级为文本

> 规则：H2 ｜ 等级：单元格级 ｜ **批次：P4** ｜ 判定：**【缺失实现】**
>
> **[已落地] 导出侧日期列判定 ＝「二者并存」（2026-10-18，D3）**
> - **元数据优先**：导出时先查 `__normalize_meta` 中该表 `original_type='datetime'` 的列，命中则按**宽松形态**解析（`YYYY/M/D`／`YYYY.M.D`／`YYYY-MM-DDTHH:MM(:SS)`，**无歧义限定**）。
> - **值形态兜底**：未命中标记的列，**保留原有严格 ISO 值形态判定**（向后兼容）。
> - **落点**：`ops/exporter.py` —— 新增 `_datetime_columns(conn, table_name)`／`_parse_datetime_loose(value)`；`export_table` 内注入 `dt_cols` ＋ 写入循环分支（`columns[c_i-1] in dt_cols`）。**签名未变**、**未引入新依赖**。
> - **兼容性**：**无 `__normalize_meta`（旧库／旧会话）时 `dt_cols` 为空集 → 行为与改动前逐格等价**；任何解析失败一律原样写（不引入新失败）。
> - **实测**：`_temp/ImportData/verify_d3_scenarios.py`（`VERIFY_D3_DONE`；V4a~V4e 全 PASS：有元数据时 `2026/1/5`→真日期、无元数据时同值仍为字符串、严格 ISO 两种情形均转日期、6 个非法形态全部不解析）。
> - 完整留痕见 §0.7.6「遗留项终态」。

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建，导入侧规范化）＋ `rpa_engine/ops/exporter.py`（导出侧回写）
- 目标：normalizer 的日期规范化（H2）；`exporter.export_table`（L35-110，`ws.append` 在 L87／L99）
- 调用链：导入侧 `read_excel_sheet` → normalizer → 落库 TEXT；导出侧 `sqlite_manager.fetch*`／cursor → `exporter.export_table` L99 → `wb.save` L102
- 存在性判定：❌ 不存在（无 ISO 8601 规范化、无元数据标记、导出无日期格式回写）

#### 2. 现状与缺陷判定
```python
# exporter.py L87 与 L99（原样写回，无 number_format 设置）
    ws.append(list(columns))
    ...
        for row in rows:
            ws.append(list(row))
```
- 缺陷类型：**【缺失实现】**（H2 未实现；值未丢但格式降级）
- 阻断后果链：`pd.read_excel` 返回 `datetime64[us]` → 落库为 TEXT `'2026-02-20 00:00:00'` → 导出 `ws.append` 原样写入字符串 → 回读 `data_type='s'`／`number_format='General'` → **单元格级交付质量降级**（交付报表日期列无法做日期运算/筛选），并连带 `A-07`（等值筛选 0 行）

#### 3. 修改方案
**B. 新建型（导入侧）＋ A. 修改型（导出侧）**
- 改动点 1（新建）：`ops/excel_normalizer.py::normalize_datetime_column`
  - 骨架：
    ```python
    def normalize_datetime_column(series: "pd.Series", meta: dict, col: str) -> "pd.Series":
        """H2：日期/时间统一转为 ISO 8601 字符串（TEXT），并在元数据标记原始类型。

        解析失败必须回落原文本（不得抛错、不得静默填 NULL）。
        """
    ```
  - 实现要点：`pd.to_datetime(series, errors="coerce")` → 成功者 `dt.strftime("%Y-%m-%d %H:%M:%S")`（**无时间部分时用 `%Y-%m-%d`**）；`NaT` 的原始文本**原样保留**；`meta[col]["original_type"] = "datetime"` ＋ `meta[col]["normalized"] = "iso8601"`
- 改动点 2（修改）：`ops/exporter.py::export_table` L87-99
  - 改前：表头与每行 `ws.append(list(...))`
  - 改后：① 表头后追加一行**类型行**（可选，用于回读还原，须由 `REQ-H9` 元数据驱动）② 对判定为日期列的单元格，`ws.cell(row=..., column=..., value=datetime_obj).number_format = "yyyy-mm-dd hh:mm:ss"`（**须**先 `from datetime import datetime` 并 `datetime.strptime` 解析；**解析失败必须回落写原始字符串**）
  - 说明：从 TEXT 反解为 datetime 写回真实日期格式（裁定 G10：解析失败不得引入新失败）
- **C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`export_table` 的签名与返回行数；`Workbook` 的 `write_only` 选择（属 `B-03`，本次不改）
- 不可引入的新依赖：是（`datetime` 属标准库）
- 必须保留的接口/信号：`export_table` 的 5 参数签名（含 `cancel_check`）
- 必须遵循的规约：H2 规则定义；裁定 G10（导出写回真日期格式；**解析失败回落 TEXT**）；`AGENTS.md` §2.1 条 5

#### 5. 验证
- 用例构造：`日期.xlsx` 的 `日期` 列为 `2026-02-20`／`2026-02-21 13:45:00`／非法文本 `待定`
- 期望输出：落库为 ISO 8601 TEXT；导出回读 `日期` 列为**真日期格式**（`number_format` 非 `General`、`data_type='d'`）；`待定` 行仍为文本
- 失败判据：导出列仍为 `General` 文本；或非法值行被写成 NULL／抛错导致导出失败
- 自证方式：导出文件用 openpyxl 回读断言 `cell.number_format` 与 `cell.data_type`

#### 6. 风险与回滚
- 可能回归点：① 解析耗时（逐单元格 `strptime`）；② 时区/精度（分钟截断）
- 回滚方式：`exporter.py` 备份；normalizer 新文件可删
- 降级策略：解析失败立即回落写原始字符串并 `logger.warning`（不得中断导出）；若导出耗时超阈值（如 > 2 倍基线），降级为「不写 number_format，仅保证 ISO 文本」

#### 7. 验收标准
- [ ] 日期列导出后为真日期格式，可在 Excel 中做日期运算
- [ ] 非法日期文本原样保留（未被吞成 NULL、未导致导出失败）
- [ ] `REQ-H9` 元数据中该列 `original_type` 标为 `datetime`

> 状态：**已落地（二者并存）** —— 见上方 `[已落地]` 块；实测见 `_temp/ImportData/verify_d3_scenarios.py`。

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建，导入侧规范化）＋ `rpa_engine/ops/exporter.py`（导出侧回写）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-07 [原编号: H-16] 日期等值筛选静默返回 0 行

> 规则：H2 ｜ 等级：单元格级 ｜ **批次：P4** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）＋ `rpa_engine/gui/forms.py`（条件框提示）
- 目标：normalizer 的日期规范化（**与 `A-06` 同一改动点**）；`forms.py` 条件输入控件（`parse_condition_lines` L181／`format_conditions` L226）
- 调用链：上游 `forms.build_where`／`sql_safety.build_where`（L74 起）→ 下游 SQL 等值比较
- 存在性判定：❌ 不存在（无日期规范化 → 库内值带时间部分）

#### 2. 现状与缺陷判定
```python
# forms.py L196（条件值构造）与 L226（条件回填）
                        "value": _maybe_number(val),
...
def format_conditions(conditions: List[Dict[str, Any]]) -> str:
```
- 缺陷类型：**【缺失实现】**（H2 未实现导致库内值带 `00:00:00`，等值匹配不上；条件框亦无格式提示）
- 阻断后果链：用户填 `日期 = 2026-02-20` → 库内值为 `2026-02-20 00:00:00` → 等值比较不成立 → **静默 0 行**（区间写法可用）→ 用户拿到空表却见 ✅

#### 3. 修改方案
**A. 修改型**（改动点 1 与 `A-06` 共用；改动点 2 独立）
- 改动点 1：**见 `A-06` 改动点 1**（同一天数规范化改动点，本项不另设改动）
  - 说明：日期统一为 ISO 8601 且**无时间部分时省略 `00:00:00`**，使 `2026-02-20` 可被等值命中
- 改动点 2：`rpa_engine/gui/forms.py` 条件输入控件提示
  - 改前：条件值为自由文本 `QLineEdit`／文本域，无格式提示
  - 改后：在条件值控件的 `setToolTip`／`setPlaceholderText` 中补「日期请填 `YYYY-MM-DD`；如需精确到时刻请填 `YYYY-MM-DD HH:MM:SS`」；若该控件为通用文本域，则在 `parse_condition_lines`（L181-212）对命中 `^[\d\-: ]+$` 的值不做 `_maybe_number` 转换（L196）
  - 说明：**不得**改写用户输入（裁定 G8），只做提示
- **B. 新建型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`forms.py` 的界面排版（仅允许补 tooltip／placeholder）；`_maybe_number` 对**非日期**值的既有行为
- 不可引入的新依赖：是
- 必须保留的接口/信号：`parse_condition_lines`／`format_conditions` 的签名与返回结构
- 必须遵循的规约：裁定 G8「用户输入不得被程序改写 ＋ 明确提示」；裁定 G10「条件框加格式提示」

#### 5. 验证
- 用例构造：导入含 `日期` 列的样本（值 `2026-02-20`），在阶段 2 配置筛选 `日期 = 2026-02-20`
- 期望输出：命中 1 行（非 0 行）；条件框有格式提示
- 失败判据：返回 0 行；或用户填 `2026-02-20` 被程序改写成 `20260220` 等
- 自证方式：执行后报告页步数/行数；临时库 `SELECT COUNT(*) FROM t1 WHERE 日期 = '2026-02-20'` ≥ 1

#### 6. 风险与回滚
- 可能回归点：① 省略时间部分可能影响"同日不同时刻"的等值语义（须在报告中说明）；② tooltip 文案过长截断
- 回滚方式：`forms.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若省略时间部分引发歧义，降级为「保留完整时间 + 只加提示」（等值筛选仍可能 0 行，须在 `REQ-H9` 报告中提示用户改用区间）

#### 7. 验收标准
- [ ] 填 `日期 = 2026-02-20` 能命中数据（≥1 行）
- [ ] 条件框存在日期格式提示；用户输入未被程序改写
- [ ] 回归全绿（含 `tests/test_translation.py` / `test_validator_cross.py`）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）＋ `rpa_engine/gui/forms.py`（条件框提示）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-08 [原编号: H-06] 字面 `NA`／`N/A`／`None`／`null` 被静默吞成 NULL

> 规则：R7 ｜ 等级：单元格级 ｜ **批次：P4** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）＋ `rpa_engine/ops/excel_preprocessor.py`（读取入口）
- 目标：`read_excel_sheet`（L171-220，`pd.read_excel` 在 L210-215）；normalizer 的空值口径控制
- 调用链：上游 `table_importer.import_excel_table` L76 → 本处读取／规范化 → 下游 `sqlite_manager.import_dataframe` L149
- 存在性判定：❌ 不存在（无 `na_values`／`keep_default_na` 控制）

#### 2. 现状与缺陷判定
```python
# excel_preprocessor.py L210-215（未控制 na_values / keep_default_na）
    df = pd.read_excel(
        str(src),
        sheet_name=sheet_name,
        skiprows=header_row - 1,
        header=0,
    )
```
- 缺陷类型：**【缺失实现】**（R7 未实现；pandas 默认 `STR_NA_VALUES` 把字面文本当缺失值）
- 阻断后果链：`B2='NA'` → pandas 视为 NaN → `import_dataframe` L149 落库为 `typeof='null'` → 导出空单元格 → **单元格级静默丢值**（原文彻底消失，无日志、无提示）；`无`／`空`／`否`／`-` 不受影响

#### 3. 修改方案
**B. 新建型 ＋ A. 修改型（组合）**
- 改动点 1（新建）：`ops/excel_normalizer.py::apply_na_policy`
  - 骨架：
    ```python
    def apply_na_policy(df: "pd.DataFrame", policy: str = "preserve") -> tuple:
        """R7：按策略决定"哪些字面文本算空值"。

        policy="preserve"（默认，裁定 G11）：仅真空／全空白算 NULL，
            字面 NA/N/A/None/null/nan/#N/A 等**原样保留**；
        policy="pandas"：沿用 pandas 默认 STR_NA_VALUES（即当前现状）。
        Returns: (df_out, nulled_cells)
        """
    ```
  - 实现要点：读出时以 `keep_default_na=False, na_values=[]`（把所有字面保留为字符串），再由本函数按策略决定是否转 NULL；`nulled_cells` 记录 (行号, 列名, 原值) 供 `REQ-H9` 报告
- 改动点 2（修改）：`ops/excel_preprocessor.py::read_excel_sheet` L210-215
  - 改前：`pd.read_excel(str(src), sheet_name=sheet_name, skiprows=header_row - 1, header=0)`
  - 改后：追加 `keep_default_na=False, na_values=[]`
  - 说明：把"什么算空值"的决定权从 pandas 收回本程序（否则无法实现 R7 的任何策略）
  - **注意**：`read_excel_sheet` 的**签名与返回值不变**；参数追加不破坏调用方
- **C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`read_excel_sheet` 的签名与返回值；`import_dataframe` 的 `if_exists` 语义
- 不可引入的新依赖：是
- 必须保留的接口/信号：`read_excel_sheet(file_path, sheet_name, header_row=1, sheet_info=None)` 的 4 个参数
- 必须遵循的规约：R7 规则定义；裁定 G11「提供开关，默认保持现状（preserve）」；`AGENTS.md` §2.2 条 1（默认值走配置，不硬编码）

#### 5. 验证
- 用例构造：`空值口径.xlsx` 的 `备注` 列含 `NA`／`N/A`／`None`／`null`／空白 各 1 行
- 期望输出：默认策略下 4 个字面文本**原样入库**（非 NULL），空白行为 NULL；切到 `pandas` 策略时行为与今日一致（转 NULL）
- 失败判据：默认策略下 `NA` 仍变 NULL；或切换策略后无差异
- 自证方式：临时库 `SELECT 备注, typeof(备注) FROM t1`；`REQ-H9` 报告出现 `nulled_cells` 条目（仅 blank 行）

#### 6. 风险与回滚
- 可能回归点：① `keep_default_na=False` 使 pandas 不再识别空字符串 → 须由 `apply_na_policy` 补上"全空白→NULL"；② 影响既有 118 用例中的类型断言
- 回滚方式：`excel_preprocessor.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若改动引发回归，回退 `read_excel_sheet` 参数并**仅保留开关常量**（默认 `pandas`，等价今日行为），把 H6 记为「需人工裁定后启用」

#### 7. 验收标准
- [ ] 默认策略下 `NA`／`N/A`／`None`／`null` 原样保留，空白归一为 NULL
- [ ] 策略可由 JSON 配置切换，`pandas` 策略行为与改动前一致
- [ ] 118 用例回归全绿

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）＋ `rpa_engine/ops/excel_preprocessor.py`（读取入口）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-09 [原编号: F-08] 预览与真实导入不一致 ＋ 大表在主线程全量导入

> 规则：H8 ｜ 等级：表级 ｜ **批次：P6** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/gui/main_window.py`、`rpa_engine/ops/excel_preprocessor.py`
- 目标：`MainWindow._on_confirm_import`（L241-400，导入循环 L294-330）；`scan_sheets`（L131-168）
- 调用链：上游 `confirm_import` 信号 → 本处 L294-330 主线程循环 → 下游 `import_excel_table`
- 存在性判定：⚠️ 部分存在（扫描侧 `scan_sheets` L155 已 read_only；**确认后的全量导入仍在主线程、无分块**）

#### 2. 现状与缺陷判定
```python
# main_window.py L294-301（主线程逐表全量导入，每表只 processEvents 一次）
        for i, e in enumerate(entries):
            table_id = f"T{i + 1}"
            sqlite_table = f"t{i + 1}"
            progress.setValue(i)
            progress.setLabelText(
                f"正在导入 {table_id}（{e['alias']}）…"
            )
            QApplication.processEvents()
# excel_preprocessor.py L155（扫描侧已只读）
    wb = load_workbook(str(src), read_only=True, data_only=True)
```
- 缺陷类型：**【缺少容错】**（H8 只实现了扫描侧；全量导入在 GUI 主线程，20 万行级会冻结界面，且 `MEMORY_WARN_ROWS = 500_000` 对 20 万行不触发）
- 阻断后果链：确认导入 → 主线程 `pd.read_excel` 全量加载（实测 20 万行×10 列 ≈ 22s 无响应、RSS +130MB）→ `processEvents()` 每表仅一次 → 界面全程冻结、进度不可见、**无法取消** → 内存峰值叠加 → **表级失败或整体卡死**

#### 3. 修改方案
**A. 修改型**（目标已存在）
- 改动点 1：`ops/excel_preprocessor.py::read_excel_sheet` L210-215 —— 增加分块读取参数
  - 改前：单次 `pd.read_excel(...)`
  - 改后：保留签名不变；新增内部阈值判断——当 `scan_sheets` 提供的 `sheet_info` 显示 `rows > CHUNK_ROW_THRESHOLD`（现常量 L26＝1_000_000，**建议下调并在报告中说明**）时，改为 `pd.read_excel(..., chunksize=CHUNK_SIZE)` 逐块合并，且每块后 `gc.collect()`
  - 说明：控制单次内存峰值（§2.1 条 5）
- 改动点 2：`gui/main_window.py::_on_confirm_import` L294-330
  - 改前：在 GUI 主线程 for 循环内同步导入
  - 改后：
    ```python
    # 每表导前显式刷新生效（保持既有 processEvents）
    QApplication.processEvents()
    # 每表导入后追加一次进度刷新 + 内存警戒检查（psutil）
    if psutil.Process().memory_info().rss / 1024 / 1024 > MEM_WARN_MB:
        logger.warning(...)  # 并在进度对话框文案中提示"内存占用较高"
    ```
    ＋ 把 `MEMORY_WARN_ROWS` 的判定改为**双阈值**：`rows > 200_000` 即在前述进度对话框文案中提示"该表较大，导入期间界面可能暂无响应"
  - 说明：**不改线程模型**（提示词 §5.1 禁止动线程模型）→ 本项只做「有提示 ＋ 内存可控 ＋ 阈值失效修正」
- 改动点 3：`gui/main_window.py` L285-289 进度对话框
  - 改前：`QProgressDialog("正在导入数据表…", None, 0, len(entries), self)`
  - 改后：调用 `setCancelButton(None)` 保持不可取消（现状）**但**在标签文案中给出可能冻结的预告（见改动点 2）
- **B. 新建型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：**线程模型**（提示词 §5.1 明令）；GUI 布局排版
- 不可引入的新依赖：是（`psutil` 已在 `requirements.txt`）
- 必须保留的接口/信号：`confirm_import` 信号；`read_excel_sheet` 的签名
- 必须遵循的规约：`AGENTS.md` §2.1 条 5（内存峰值）；§5.3（四阶段生命周期）；H8「扫描与预处理分离」

#### 5. 验证
- 用例构造：① 20 万行×10 列 xlsx ② 1 万行常规表
- 期望输出：① 导入前有"较大表、界面可能暂无响应"的文案；导入过程 RSS 峰值低于改动前；② 常规表无提示、行为不变
- 失败判据：界面无任何提示即冻结；或 RSS 峰值不降反升
- 自证方式：`logs/gui_*.log` 中的内存数值；用任务管理器/`psutil` 采样对比改动前后峰值

#### 6. 风险与回滚
- 可能回归点：① 分块读取改变 dtype 推断结果（与 `A-04` 的推断规则叠加）；② 阈值下调导致过多提示
- 回滚方式：`main_window.py`／`excel_preprocessor.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若分块读取破坏 dtype 一致性，降级为「仅加提示与内存阈值修正，不做分块」（保住 §2.1 条 5 的可观测性）

> **[ADJUSTED] `A-09` ①（分块读取）已裁定走 §6 降级（2026-10-18）**
> - **原因**：pandas 3.0.5 的 `pd.read_excel` **无 `chunksize` 形参、也无 `**kwds`**（传 `chunksize=` 直接 `TypeError`；`engine_kwargs={'chunksize':…}` 透传给 `openpyxl.load_workbook` 亦 `TypeError`）——计划指定机制在当前依赖下**架构上不可实现**。
> - **走法**：依 §6 降级，只做 ②③（**大表文案预告 ＋ `psutil` 内存阈值监控**），**不做分块**。
> - **影响**：`ops/excel_preprocessor.py` **无需修改**；`CHUNK_ROW_THRESHOLD` 常量**保留**，在降级路径下**无消费方**（不为它造消费点）；`A-04` 的 `dtype=object`／`keep_default_na=False` 约束**原样保留**（**未**为分块回退）。
> - **验收口径**：§7 的三条判据在降级路径下**同样成立**（大表有提示且能完成／峰值不升／常规表不变），**不要求分块必须实现**。
> - **落地留痕**：见 §0.7.8（P6 施工记录）与 `docs/task-records/2026-10-18-importdata-repair.md` Step 10。

#### 7. 验收标准
- [ ] 20 万行级表导入前出现明确文案提示；导入可完成（不 OOM）
- [ ] 内存峰值较改动前下降或持平；常规表行为不变
- [ ] 未改动线程模型（`worker.py` 与 `executor` 的分发逻辑不变）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/main_window.py`、`rpa_engine/ops/excel_preprocessor.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-10 [原编号: H-04] 步骤配置永久丢失

> 规则：R1＋H10 ｜ 等级：文件级 ｜ **批次：P0** ｜ 判定：**【逻辑错误】** ｜ 与 `A-01` 同属「源文件身份」链条

#### 1. 定位
- 文件：`rpa_engine/gui/page_input_selection.py`、`rpa_engine/gui/main_window.py`
- 目标：`InputSelectionPage.get_entries`（L324-335）／`InputSelectionPage._add_row`（L467-536，`source_path` 入参在 L474、写入在 L488-495）／`MainWindow._restore_last_config`（L715-772）
- 调用链：上游 `_on_import` L455 `get_entries()` → 本处 `confirm_import` → 下游 `main_window.py` 注册表构造 L313-321 → `models.py::to_dict`（`source.file`） → 恢复时 `main_window.py` L742
- 存在性判定：⚠️ 部分存在（`source_path` 字段**已在 `InputEntry` 与 `_add_row` 中存在**，仅 `get_entries` 未导出）

#### 2. 现状与缺陷判定
```python
# page_input_selection.py L329-334（未导出 source_path）
                result.append({
                    "file_path": str(entry.file_path),
                    "sheet_name": entry.sheet_name,
                    "alias": entry.alias.strip(),
                    "header_row": entry.header_row,  # 1-based
                })
# page_input_selection.py L488-495（source_path 已存在于条目）
        entry = InputEntry(
            file_path=file_path,
            sheet_name=sheet_name,
            alias=alias,
            header_row=header_row,
            selected=True,
            source_path=source_path,
        )
# main_window.py L740-742（恢复判据只读 source.file）
            f = src.get("file", "")
            tid = t.get("table_id", "")
            if f and Path(f).is_file():
```
- 缺陷类型：**【逻辑错误】**（导出键缺失 → 落盘的是副本路径 → 副本在会话收尾被删 → 恢复判据全假）
- 阻断后果链：`get_entries()` 无 `source_path` → `last_config.json` 的 `source.file` 落为**临时区副本路径** → `clear_temp_copies()` 在收尾时删除副本 → 下次启动 `main_window.py` L742 `Path(f).is_file()` 全假 → L756-760 无有效条目 → `model.reset()` → **文件级：步骤配置永久丢失**

#### 3. 修改方案
**A. 修改型**（目标已存在）
- 改动点 1：`page_input_selection.py::get_entries` L329-334
  - 改前：4 键字典（见上）
  - 改后：追加第 5 键 `"source_path": str(entry.source_path or entry.file_path),`
  - 说明：与 `A-01` 改动点 1 **为同一处改动**（两者共用），本项不另设改动点
- 改动点 2：`main_window.py::_on_confirm_import` 的注册表构造 L313-321
  - 改前：注册表项含 `file_path`（副本路径），无 `source_path`
  - 改后：追加 `"source_path": e.get("source_path", e["file_path"]),`
  - 说明：让模型层能把原始路径写入 `source.file`
- 改动点 3：`rpa_engine/gui/models.py::WorkflowModel.to_dict`（`source.file` 落盘处，约 L690-708）
  - 改前：`source.file ＝ 表的副本路径`
  - 改后：`source.file ＝ 注册表 `source_path`（有则优先，否则回落副本路径）`
  - 说明：**改前须先读 L650-720 确认实际赋值行号**；若模型层不接收 `source_path`，则改为在 `main_window.py` 侧写 `last_config` 前统一替换 `file` 字段
  - `[UNVERIFIED]`：`to_dict` 内 `source` 的具体构造行号本轮未逐行读取
- 改动点 4：`main_window.py::_restore_last_config` L742 判据
  - 改前：`if f and Path(f).is_file():`
  - 改后：`if f and Path(f).is_file():` **保持不变**（判据本身正确），但**须先确保落盘的是原始路径**（改动点 3）；另在 L752-754 的 warning 文案中加入"请重新选择该文件"的人话指引
- **B. 新建型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`InputEntry` 的字段集合（`source_path` 已在）；`models.py` 的表/步结构
- 不可引入的新依赖：是
- 必须保留的接口/信号：`get_entries()` 的返回类型（`List[Dict[str, Any]]`）；`load_session` 签名
- 必须遵循的规约：`AGENTS.md` §2.2 条 2（JSON 是业务逻辑唯一载体）；裁定 F1①「贯通 `source_path`」

#### 5. 验证
- 用例构造：阶段 1 选 `样本A.xlsx` → 配置 2 个步骤 → 关闭程序 → 重开
- 期望输出：阶段 1 回填上次的表；阶段 2 恢复 2 个步骤；`workspace/last_config.json` 的 `tables[].source.file` 为**原始文件绝对路径**（非 `temp/input_selection/` 下的副本）
- 失败判据：重开后列表为空／步骤丢失；或 `source.file` 仍指向副本
- 自证方式：直接读 `workspace/last_config.json` 断言路径；关闭再开启后 UI 断言

#### 6. 风险与回滚
- 可能回归点：① 原始文件被移动/删除后仍尝试恢复 → 由 L742 判据拦截（预期行为）；② 手工构造的 entries 无 `source_path` → 回落分支
- 回滚方式：三个文件备份至 `_temp/ImportData/backup/`
- 降级策略：若模型层改动风险高，采用备选——仅在 `main_window.py::_save_last_config` L787-791 落盘前把 `source.file` 替换为 `source_path`

#### 7. 验收标准
- [ ] 重开程序后表清单与步骤配置均正确恢复
- [ ] `workspace/last_config.json` 中 `source.file` 为原始路径
- [ ] 原始文件被删除时**跳过恢复并告警**（不崩溃、不清空模型造成误判）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/page_input_selection.py`、`rpa_engine/gui/main_window.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-11 [原编号: H-05] 超龄清理用 mtime 但 `copy2` 保留源 mtime → 启动即删副本

> 规则：H10 ｜ 等级：文件级 ｜ **批次：P1** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_preprocessor.py`、`rpa_engine/gui/main_window.py`
- 目标：`validate_and_copy`（L29-67，`shutil.copy2` 在 L65）／`MainWindow.cleanup_stale_files`（L679-707，超龄判定 L695-704）／`MainWindow.__init__` 启动序（L235-237）
- 调用链：上游 `page_input_selection._on_add_files` L400 `validate_and_copy` → 本处 `copy2`；另一侧 `MainWindow` 启动 L236 `_cleanup_stale_sessions()` → L237 `_restore_last_config()`
- 存在性判定：⚠️ 部分存在（两段逻辑均存在，**语义冲突**）

#### 2. 现状与缺陷判定
```python
# excel_preprocessor.py L65（copy2 保留源文件 mtime）
    shutil.copy2(src, dst)
# main_window.py L695-704（按 mtime 判超龄删除）
        cutoff = _time.time() - cutoff_hours * 3600
        temp_root = Path(temp_root)
        if temp_root.is_dir():
            for p in temp_root.iterdir():
                try:
                    if p.is_file() and p.stat().st_mtime < cutoff:
                        p.unlink()
# main_window.py L236-237（清理先于恢复）
        self._cleanup_stale_sessions()   # R6/D2-3：启动清理孤儿会话库/超龄副本
        self._restore_last_config()
```
- 缺陷类型：**【逻辑错误】**（`copy2` 语义与"超龄"判据互相矛盾；且清理序先于恢复）
- 阻断后果链：源 `.xlsx` 的 mtime 早于 24h → `copy2` 把同一 mtime 带给副本 → 启动时 L700 判定超龄 → `p.unlink()` → L237 `_restore_last_config()` 读取 `source.file`（＝副本）时 `is_file()` 全假 → **文件级：恢复功能对真实文件 100% 失效**（`.xls` 转换产物因 mtime 新而幸免）

#### 3. 修改方案
**A. 修改型**（目标已存在）
- 改动点 1：`ops/excel_preprocessor.py::validate_and_copy` L65
  - 改前：`shutil.copy2(src, dst)`
  - 改后：`shutil.copyfile(src, dst)`（只复制内容，**不**复制源 mtime）＋ 显式 `os.utime(dst, None)`（把副本 mtime 设为当前时间）
  - 说明：让"超龄"判据只反映**副本在本机的存活时长**，与源文件年龄解耦
  - 前置：文件头补 `import os`
- 改动点 2：`gui/main_window.py::cleanup_stale_files` L695-704
  - 改前：仅按 `st_mtime` 判超龄
  - 改后：在删除前追加保护——若该副本正被当前 `last_config.json` 的 `tables[].source.file` 引用，则**跳过删除**（读取 `last_config.json` 取得引用集合，集合为空时行为不变）
  - 说明：即使 mtime 判据命中，也不误删"上次配置正在引用"的副本
- 改动点 3：`gui/main_window.py::__init__` L236-237
  - 改前：`_cleanup_stale_sessions()` 先于 `_restore_last_config()`
  - 改后：交换顺序为 `_restore_last_config()` → `_cleanup_stale_sessions()`
  - 说明：先恢复（读引用）再清理，配合改动点 2 的保护集合
- **B. 新建型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`_cleanup_stale_sessions` 的对外签名（L709-713）；`validate_and_copy` 的返回值（仍是副本路径 `str`）
- 不可引入的新依赖：是（`os`／`shutil` 属标准库）
- 必须保留的接口/信号：`validate_and_copy(file_path, temp_dir) -> str`
- 必须遵循的规约：`AGENTS.md` §2.1 条 6；H10「幂等与回滚：产物落 `temp/normalized/`，不得被超龄清理误删」

#### 5. 验证
- 用例构造：① 复制一个 mtime 为 3 天前的 `旧文件.xlsx` → 用 [add] 选入 → 关闭程序 → 立刻重开 ② 正常新文件同流程
- 期望输出：① 重开后「恢复上次配置」**成功**回填 ② 正常流程不变
- 失败判据：重开后列表为空（说明副本仍被误删）
- 自证方式：关闭前记录 `temp/input_selection/` 文件清单与 mtime；重开后核对副本是否仍在、恢复是否成功

#### 6. 风险与回滚
- 可能回归点：① 副本永不"超龄"（若同时清了 mtime）→ 磁盘残留增多，须靠改动点 2 的引用判定＋会话收尾清理兜底；② 交换启动顺序影响其他启动逻辑
- 回滚方式：两文件备份至 `_temp/ImportData/backup/`
- 降级策略：若交换顺序有副作用，保留原序但**必须以改动点 1＋2 兜底**（副本 mtime 已是当前时间，不会被误删）

#### 7. 验收标准
- [ ] 源文件 mtime 早于 24h 时，重开程序仍能恢复配置
- [ ] `temp/input_selection/` 不会因"源文件年龄"被误删副本
- [ ] 更换文件后旧副本仍能被正常回收（不产生永久残留）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_preprocessor.py`、`rpa_engine/gui/main_window.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-12 [原编号: F-09] 同名异后缀静默覆盖已导入副本

> 规则：H10 ｜ 等级：文件级 ｜ **批次：P1** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_preprocessor.py`
- 目标：`validate_and_copy`（L29-67，同名查重 L58-63）／`ensure_xlsx`（L70-128，`with_suffix` 在 L117-119）
- 调用链：上游 `page_input_selection._on_add_files` L400／L404 → 本处两函数 → 下游 `_scan_sheets` L408
- 存在性判定：✅ 已存在（两处查重逻辑均在，**口径不一致**）

#### 2. 现状与缺陷判定
```python
# excel_preprocessor.py L58-63（查重只比同后缀）
    dst = temp_path / src.name
    counter = 1
    while dst.exists():
        dst = temp_path / f"{src.stem}_{counter}{src.suffix}"
        counter += 1
# excel_preprocessor.py L117-119（转换产物直接覆盖）
    new_path = src.with_suffix(".xlsx")
    sheet_count = len(wb.sheetnames)
    wb.save(str(new_path))
```
- 缺陷类型：**【逻辑错误】**（`.xls` 转换产物按"去后缀 + `.xlsx`"命名，不查是否存在，`wb.save` 无条件覆盖）
- 阻断后果链：已存在 `电费.xlsx` 副本（另一张已登记表）→ 用户再选 `电费.xls` → 复制为 `电费.xls` 副本 → `ensure_xlsx` 转换目标 `电费.xlsx` **已存在** → `wb.save` **覆盖之** → 后续导入读到的"电费.xlsx"内容被替换 → **文件级：静默错表**（用户原始文件未损，但入库数据错且已登记副本被破坏）

#### 3. 修改方案
**A. 修改型**（目标已存在）
- 改动点 1：`ops/excel_preprocessor.py::ensure_xlsx` L117-119
  - 改前：`new_path = src.with_suffix(".xlsx")` ＋ 直接 `wb.save(str(new_path))`
  - 改后：
    ```python
    new_path = src.with_suffix(".xlsx")
    counter = 1
    while new_path.exists():
        new_path = src.with_name(f"{src.stem}_{counter}.xlsx")
        counter += 1
    ```
    ＋ 保持其后 `wb.save(str(new_path))`
  - 说明：转换产物也走"加序号"规则，与 `validate_and_copy` 口径一致（**不静默覆盖**）
- 改动点 2：`ops/excel_preprocessor.py::validate_and_copy` L58-63
  - 改前：`while dst.exists(): dst = temp_path / f"{src.stem}_{counter}{src.suffix}"`
  - 改后：改为**跨后缀**查重——构造 `dst` 后，同时检测 `temp_path / f"{dst.stem}.xlsx"` 是否已存在；若存在则同样递增 `counter`
  - 说明：堵住"同名异后缀"这一整类冲突（`A-18` 为其转换侧的另一触发面）
- **B. 新建型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`ensure_xlsx` 的返回值语义（仍返回 xlsx 路径字符串）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`validate_and_copy(file_path, temp_dir) -> str`；`ensure_xlsx(file_path) -> str`
- 必须遵循的规约：裁定 Q4「不接受同名异格式覆盖，一律加序号改名 ＋ 提示」

#### 5. 验证
- 用例构造：同目录放 `电费.xls`（旧格式）与 `电费.xlsx`（不同内容），先用 [add] 选 `.xlsx`，再选 `.xls`
- 期望输出：两者各自生成**不同名**副本（如 `电费.xlsx`／`电费_1.xlsx`）；两张表内容互不干扰，均可正确导入
- 失败判据：第二次选择后第一张表内容被替换；`temp/input_selection/` 中只剩一个 `电费.xlsx`
- 自证方式：导入后对比两表行数与列名；列出 `temp/input_selection/` 文件清单

#### 6. 风险与回滚
- 可能回归点：① 序号命名使副本名变长（须确保 `clean_alias_name` 仍能生成合理默认别名）；② 跨后缀查重误判（罕见）
- 回滚方式：`excel_preprocessor.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：极端情况（同目录同名文件 > 50 个）时改为「拒绝并提示用户改名」，避免无上限序号

#### 7. 验收标准
- [ ] 同名异后缀两组文件均生成独立副本，互不覆盖
- [ ] 两张表内容正确、行数列名与源文件一致
- [ ] 副本命名规则与 `validate_and_copy` 口径一致（不再出现"一处加序号、一处覆盖"）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_preprocessor.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-13 [原编号: H-21] 导入失败清单恒为兜底话术

> 规则：R1＋产物4 ｜ 等级：文件级 ｜ **批次：P0** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/gui/main_window.py`、`rpa_engine/gui/error_messages.py`
- 目标：`MainWindow._on_confirm_import`（L322-328）／`error_messages.translate_error`（L44-52，`_RULES` L20-41，`permissionerror` 在 L25）
- 调用链：上游 `import_excel_table` 抛错 → 本处 L322 捕获 → L328 `translate_error(str(err))` → 下游 L356-360 失败清单弹窗
- 存在性判定：✅ 已存在（翻译层健全，**调用方丢类名**）

#### 2. 现状与缺陷判定
```python
# main_window.py L326-328（只传 str(err)，类名丢失）
                logger.error(f"[main_window] 导入失败 {e['alias']}: "
                             f"{type(err).__name__}: {err}")
                failed.append(f"{e['alias']}: {translate_error(str(err))}")
# error_messages.py L25 与 L44-52（键＝类名小写；translate_error 对输入 lower）
    ("permissionerror", "文件正被其他程序占用（例如 Excel 未关闭）。",
...
def translate_error(raw) -> str:
    if not raw:
        return f"{_FALLBACK}{_NEXT_FALLBACK}"
    low = str(raw).lower()
    for key, reason, action in _RULES:
        if key in low:
```
- 缺陷类型：**【缺少容错】**（调用方丢弃 `type(err).__name__`，而 `_RULES` 的匹配键恰是类名小写；`str(PermissionError)` 文本为 `[Errno 13] Permission denied: ...`，**不含** `permissionerror` → 永不命中）
- **机制纠偏（相对 problem.md v7）**：`translate_error` 自身对输入做了 `.lower()`，故**规则键为小写是正确的**；真正断点在 `main_window.py` L328 丢类名（problem.md §0 差异表 3）
- 阻断后果链：`PermissionError`（Excel 未关闭占用）→ `str(err)` 无类名 → `_RULES` 全部不命中 → 走 L52 兜底「程序遇到意外问题……请把日志文件发给管理员查看」→ **文件级：失败清单不可自救**（违反 `AGENTS.md` §2.1 条 6）；对比 `ops/step_executor.py` L316 传了 `type(e).__name__` → 可命中

#### 3. 修改方案
**A. 修改型**（目标已存在）
- 改动点 1：`gui/main_window.py::_on_confirm_import` L328
  - 改前：`failed.append(f"{e['alias']}: {translate_error(str(err))}")`
  - 改后：`failed.append(f"{e['alias']}: {translate_error(f'{type(err).__name__}: {err}')}")`
  - 说明：把类名一并送入翻译层，使 `permissionerror`／`filenotfounderror`／`memoryerror` 三条规则**可达**
- 改动点 2：`gui/error_messages.py::_RULES`（L20-41）
  - 改前：9 条规则（无"xlrd 缺件"、无"不支持的文件格式"、无"标识符含禁止字符"）
  - 改后：追加 3 条（**放在特异规则区、`no such column` 之前**）：
    ```python
    ("modulenotfounderror", "程序缺少读取该文件所需的功能组件。",
     "请把日志文件发给管理员（此为交付包不完整，非文件问题）。"),
    ("标识符包含禁止字符", "该数据表的表头里有不可用的字符（常见为换行或制表符）。",
     "请在 Excel 中清理该表头后重新导入。"),
    ("文件不是 excel 格式", "所选文件不是 Excel 格式，无法读取。",
     "请确认文件为 .xlsx 或 .xls 后重试。"),
    ```
  - 说明：三条均对应本次新暴露/新引入的失败面（`A-02`／`A-03`／`A-17`），键仍用小写（与 `translate_error` 的 `.lower()` 机制一致）
- **B. 新建型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`translate_error` 的签名与 `.lower()` 机制；`_FALLBACK` 文案不变
- 不可引入的新依赖：是（`error_messages.py` 为纯标准库，可被单测）
- 必须保留的接口/信号：`translate_error(raw) -> str`；`log_hint()`
- 必须遵循的规约：`AGENTS.md` §2.1 条 6（人话）；`docs/architecture.md` §8.4 禁用词表（返回值中不得出现 SQL／表名／SQLite／物理名等技术词）；改动须同步 `tests/test_error_messages.py`

#### 5. 验证
- 用例构造：① 用 Excel 打开源文件使其被占用 → 导入 ② exe 态导入 `.xls`
- 期望输出：① 提示「文件正被其他程序占用（例如 Excel 未关闭）。请关闭占用该文件的程序后重试。」 ② 提示「程序缺少读取该文件所需的功能组件。……」（人话，而非 `No module named 'xlrd'`）
- 失败判据：仍出现「程序遇到意外问题」兜底，或出现技术原文
- 自证方式：单测断言 `translate_error("PermissionError: [Errno 13] ...")` 命中规则；`tests/test_error_messages.py` 关注禁用词

#### 6. 风险与回滚
- 可能回归点：① 新增规则键与既有规则冲突（须保证特异规则在前）；② 误命中（例如普通文本含 `标识符包含禁止字符`）
- 回滚方式：`main_window.py`／`error_messages.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若新规则引发误命中，则收窄键（如改用 `标识符包含禁止字符 ` 带尾空格）或回退改动点 2、仅保留改动点 1

#### 7. 验收标准
- [ ] 「文件被占用」场景给出可自救的中文提示（不再是管理员兜底话术）
- [ ] `.xls` 缺件场景给出中文提示，无技术原文
- [ ] `tests/test_error_messages.py` 通过；禁用词断言未破坏

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/main_window.py`、`rpa_engine/gui/error_messages.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-14 [原编号: H-24] 全局兜底弹技术原文而非人话

> 规则：R1 ｜ 等级：文件级（异常传播） ｜ **批次：P0** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/gui/app.py`
- 目标：`_excepthook`（L259-266，直弹在 L264）
- 调用链：任意槽函数未捕获异常 → `sys.excepthook` → 本处 → `QMessageBox.critical`
- 存在性判定：✅ 已存在（需接翻译层）

#### 2. 现状与缺陷判定
```python
# app.py L259-266
def _excepthook(exc_type, exc_value, exc_tb) -> None:
    """全局未预期异常兜底：记录日志并弹框提示。"""
    logger.opt(exception=(exc_type, exc_value, exc_tb)).error("[gui] 未预期异常")
    try:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "程序异常", str(exc_value))
    except ImportError:
        print(f"[gui] 未预期异常: {exc_value}", file=sys.stderr)
```
- 缺陷类型：**【缺少容错】**（未经 `error_messages.translate_error`；弹的是原始异常文本）
- 阻断后果链：任何逃出槽函数的异常（如 `A-02` 的 `ImportError`）→ L264 直弹 `str(exc_value)` → 文员看到 `No module named 'xlrd'` 等技术原文 → **文件级：错误不可理解、无法自救**（违反 `AGENTS.md` §2.1 条 6）；`A-02` 的异常元组补全后本钩子仍须保留（防其他未预期异常）

#### 3. 修改方案
**A. 修改型**（目标已存在）
- 改动点 1：`gui/app.py::_excepthook` L263-264
  - 改前：`QMessageBox.critical(None, "程序异常", str(exc_value))`
  - 改后：
    ```python
    from gui.error_messages import translate_error, log_hint
    QMessageBox.critical(
        None, "程序遇到问题",
        f"{translate_error(f'{exc_type.__name__}: {exc_value}')}\n\n"
        f"详细日志：{log_hint()}")
    ```
  - 说明：把技术原文换成"人话原因＋下一步动作"，并给出日志目录（人话化的同时保留可诊断性）；技术原文仍完整落日志（L261 不变）
- 改动点 2：`gui/app.py` 文件头
  - 改前：无 `error_messages` 导入
  - 改后：在 L246 `_setup_gui_logging` 之前补 `from gui.error_messages import translate_error, log_hint`（**须先读 L1-40 的 import 区确认无循环导入**）`[UNVERIFIED]`
- **B. 新建型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`_excepthook` 的注册方式（`sys.excepthook = _excepthook`，行号须自查）`[UNVERIFIED]`
- 不可引入的新依赖：是
- 必须保留的接口/信号：`_excepthook(exc_type, exc_value, exc_tb)` 的签名（`sys.excepthook` 协议）
- 必须遵循的规约：`AGENTS.md` §2.1 条 6；`docs/architecture.md` §8.4 禁用词表

#### 5. 验证
- 用例构造：临时在任一槽函数内 `raise RuntimeError("测试：内部错误")` 触发钩子（验证后移除）
- 期望输出：弹窗文案为中文人话＋日志目录提示；`logs/gui_*.log` 内保留完整 traceback
- 失败判据：弹窗出现英文异常名或原始堆栈文本
- 自证方式：单测直接调用 `_excepthook(RuntimeError, RuntimeError("x"), None)` 断言弹窗文本（可用 monkeypatch 替换 `QMessageBox`）

#### 6. 风险与回滚
- 可能回归点：① 与 `error_messages.py` 形成循环导入（`error_messages` 只依赖 `paths`，风险低）；② 弹窗文案过长
- 回滚方式：`app.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若循环导入发生，改为在 L264 处**函数内**导入（`from gui.error_messages import translate_error`）

#### 7. 验收标准
- [ ] 未预期异常弹窗为中文人话并含日志目录指引
- [ ] `logs/gui_*.log` 仍保留完整技术栈（可诊断性不降）
- [ ] 启动自检 6 项仍全绿（钩子改动不影响启动）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/app.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-15 [原编号: DM-30] 写库不原子，空表被当成功

> 规则：产物2＋H10 ｜ 等级：表级 ｜ **批次：P4**（`G-5` 已裁定，见 §1.6） ｜ 判定：**【逻辑错误】** ｜ 前置：无

#### 1. 定位
- 文件：`rpa_engine/ops/sqlite_manager.py`、`rpa_engine/ops/sql_safety.py`、`rpa_engine/ops/session_db.py`
- 目标：`import_dataframe`（L124-155，`with txn(conn)` 在 L148、`to_sql` 在 L149）／`txn`（L258-277）／`SessionDB.new_connection`（L64-80）
- 调用链：上游 `table_importer.import_excel_table` L91 → 本处 `import_dataframe` → 下游 `df.to_sql(..., if_exists="replace")`
- 存在性判定：✅ 已存在（原子性缺失）

#### 2. 现状与缺陷判定
```python
# sqlite_manager.py L148-149（事务只包 to_sql；DDL 自动提交）
    with txn(conn):
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
# sql_safety.py L271-277（txn 仅 commit/rollback）
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
# session_db.py L74-79（连接未设 isolation_level → 默认 legacy）
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
```
- 缺陷类型：**【逻辑错误】**（`replace` 语义的 `DROP TABLE`／`CREATE TABLE` 属 DDL；python sqlite3 默认 legacy 隔离级别下 **DDL 自动提交**，`txn` 的 `rollback()` 无法撤销已执行的 DDL）→ 同时构成**注释谎报**：L140 docstring 称「写入失败（事务自动回滚）」与事实不符（见 `B-77`）
- 阻断后果链：导入中途失败 → 数据 INSERT 被回滚、**旧表已被 DROP 且无法恢复** → 库里残留空壳表 → 下游 `ensure_input_tables`（`A-16`）因"表已存在"跳过补导 → **表级失败 ＋ 空壳表污染**（「要么完整、要么什么都没有」不成立）

#### 3. 修改方案
**A. 修改型（实施型；`G-5` 已裁定，见 §1.6）**
- 改动点 1（新增共用守卫）：`rpa_engine/ops/table_lifecycle.py` 新增
  ```python
  def guard_overwrite_target(conn, output_table: str) -> None:
      """G-5①：目标表为「存在且非空」的活表时拒绝覆盖。

      Raises:
          ValueError: 目标表已存在且行数 > 0（DDL 自动提交、不可回滚，故拒绝）。
      """
  ```
  - 说明：四处产表函数（`filter_dedup.py` L81／L155、`aggregator.py` 产表处、`mapping_matcher.py` L217）与 `merge_tables`（`table_lifecycle.py`）**均改调它**——不得各写一套判据
- 改动点 2（新增函数）：`rpa_engine/ops/sqlite_manager.py::import_dataframe_atomic`
  ```python
  def import_dataframe_atomic(df, table_name: str, conn,
                              if_exists: str = "replace",
                              tmp_suffix: str = "__tmp_import") -> int:
      """G-5②：原子导入 = 建临时表 → INSERT → 校验行数 → DROP 旧表 → RENAME。
      Raises:
          ValueError: 表名为空 / 行数校验不符。
          sqlite3.Error: 任一 SQL 失败（调用方按策略处理）。
      """
  ```
  - 实现要点（逐条落地，不得省略）：① 临时表名 `f"{table_name}{tmp_suffix}_{int(time.time()*1000)}"`（唯一后缀防撞名）；② `df.to_sql(临时表, conn, if_exists="replace", index=False)`；③ 校验 `table_row_count(临时表, conn) == len(df)`，不符即抛 `ValueError`；④ 在 `with txn(conn)` 内 `DROP TABLE IF EXISTS <目标表>` 后 `ALTER TABLE <临时表> RENAME TO <目标表>`；⑤ `except` 分支内 `DROP TABLE IF EXISTS <临时表>`（**任一步失败都不留半成品**）
- 改动点 3（切换调用）：`rpa_engine/ops/table_importer.py` 的落库调用（L91 附近 `import_dataframe(...)`）→ 改调 `import_dataframe_atomic(...)`
  - 说明：`import_dataframe` 本身**保留不动**（签名与行为不变），供其它调用方兼容
- 改动点 4（注释更正，受理定 G14 约束）：`sqlite_manager.py` L128／L140 的「事务内」「写入失败（事务自动回滚）」→ 更正为「legacy 隔离级别下 DDL 自动提交，原子性由 `import_dataframe_atomic` 的临时表 + `RENAME` 保证」
- **B. 新建型**：不适用（改动点 1／2 均为**同文件内新增函数**，仍归"修改型"）　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`import_dataframe` 的签名（保留供兼容）；`txn` 的语义
- 不可引入的新依赖：是
- 必须保留的接口/信号：`import_dataframe(df, table_name, conn, if_exists="replace") -> None`；`table_row_count(table_name, conn) -> int`
- 必须遵循的规约：`AGENTS.md` §2.2 条 4（不得自建连接）；**本版 §1.6 的 `G-5` 裁定**（活表覆盖守卫 ＋ 临时表→校验行数→原子 rename）；裁定 G14（注释须与行为一致）

#### 5. 验证
- 用例构造：构造一个导入中途必失败的表（例如含超长/非法列名，或人为在 INSERT 中注入错误），目标表名与已有表同名且已有表含 10 行
- 期望输出：失败后**旧表的 10 行仍在**（未被 DROP）；无空壳表残留；`SELECT COUNT(*)` 与失败前一致
- 失败判据：旧表被删或变为 0 行；库里出现空壳表
- 自证方式：失败前后对比 `PRAGMA table_info` 与 `COUNT(*)`

#### 6. 风险与回滚
- 可能回归点：① `ALTER TABLE ... RENAME TO` 与 WAL 下的锁竞争；② 临时表名冲突（须用唯一后缀）
- 回滚方式：`sqlite_manager.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若原子 rename 引发锁问题，降级为「先备份旧表为 `xxx__bak_<ts>` → 失败时恢复」，并在报告中标注"降级路径"

#### 7. 验收标准
- [ ] 导入中途失败后旧表数据完好，无空壳表
- [ ] 成功路径行为与改动前一致（行数、列名、类型）
- [ ] L140／L128 注释与实际行为一致（同步完成）
- [ ] **已按 §1.6 的 `G-5` 裁定实施**（活表覆盖守卫 ＋ 原子 rename）——本项已解除「P-待裁定」状态，可直接开工

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/sqlite_manager.py`、`rpa_engine/ops/sql_safety.py`、`rpa_engine/ops/session_db.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-16 [原编号: DM-31] 空壳表跳过补导

> 规则：H10 ｜ 等级：表级 ｜ **批次：P4**（`G-5` 已裁定，见 §1.6） ｜ 判定：**【缺少容错】** ｜ 前置：无

#### 1. 定位
- 文件：`rpa_engine/engine/executor.py`
- 目标：`ensure_input_tables`（L80-111，存在性判定在 L91-93）
- 调用链：上游 `execute_workflow` L155 → 本处 → 下游 `import_excel_table` L108-109
- 存在性判定：✅ 已存在（判据不完整）

#### 2. 现状与缺陷判定
```python
# executor.py L91-93（只判表存在，不判行数）
    for t in workflow.tables:
        if table_exists(conn, t.sqlite_table):
            continue
```
- 缺陷类型：**【缺少容错】**（有效性判据缺"行数 > 0"）
- 阻断后果链：上一轮失败留下空壳表 → 本轮回合 `table_exists` 为真 → `continue` 跳过补导 → 下游步骤在空表上运算 → **表级失败或静默错误结果**（与 `A-15` 构成同一根因的两面）

#### 3. 修改方案
**A. 修改型（实施型；`G-5` 裁定第 ③ 条，见 §1.6）**
- 改动点 1：`engine/executor.py::ensure_input_tables` L92
  - 改前：`if table_exists(conn, t.sqlite_table):`
  - 改后：`if table_exists(conn, t.sqlite_table) and table_row_count(conn, t.sqlite_table) > 0:`
  - 说明：把"存在但空"视为需补导；须在文件头补 `from ops.sqlite_manager import table_row_count`（**注意循环导入风险，须实测**）`[UNVERIFIED]`
- 改动点 2：同函数 L100-104（缺 source 信息时的报错）
  - 改前：仅报"不在会话库中且缺少 source 复现信息"
  - 改后：文案补充"（该表可能为空表，需要重新导入）"，便于定位
- **B. 新建型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`execute_workflow` 的阶段结构（L150-159）；`_validate_import_path` 白名单语义（L105）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`ensure_input_tables(workflow, conn, cancel_check=None) -> None`
- 必须遵循的规约：**本版 §1.6 的 `G-5` 裁定第 ③ 条**（有效性判据＝「表存在**且**行数 > 0」）；`AGENTS.md` §2.2 条 4；**不得**为此改动步骤分发逻辑

#### 5. 验证
- 用例构造：① 手工创建一张 0 行表并令对应 `tables[]` 的 `source` 存在 → 执行工作流 ② 正常非空表同流程
- 期望输出：① 触发补导（日志出现 `兜底补导`）并成功写入数据 ② 正常表不补导（行为不变）
- 失败判据：0 行表被跳过导致下游空表运算；或正常表被反复重复导入
- 自证方式：`logs/gui_*.log` 的 `[executor] 兜底补导` 记录；执行前后该表 `COUNT(*)`

#### 6. 风险与回滚
- 可能回归点：① `table_row_count` 导入造成循环依赖（`sqlite_manager` → `sql_safety` → …）→ 须实测；② 每次执行都查行数带来轻微开销
- 回滚方式：`executor.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若循环导入不可解，改为在本函数内**局部导入**（函数内 `from ops.sqlite_manager import table_row_count`）

#### 7. 验收标准
- [ ] 空壳表（存在但 0 行）会被补导，不再静默跳过
- [ ] 非空表的既有短路行为不变（无重复导入）
- [ ] **已按 §1.6 的 `G-5` 裁定第 ③ 条实施**（空壳表视为需补导）——本项已解除「P-待裁定」状态，可直接开工

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/engine/executor.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-17 [原编号: DM-01（＋B-01 已并入）] `.xls` 老格式支持链断裂

> 规则：R1 ｜ 等级：文件级 ｜ **批次：P0** ｜ 判定：**【缺少容错】** ｜ 状态：**`[FIXED-PARTIAL]`**

#### 1. 定位
- 文件：`requirements.txt`、`RPA_Workflow_v3.spec`、`rpa_engine/ops/excel_preprocessor.py`
- 目标：依赖清单第 5 行附近（`xlrd` 行）；`spec` 的 `hiddenimports` 段；`ensure_xlsx` L102
- 调用链：`ensure_xlsx` L102 `pd.read_excel(engine="xlrd")` → 运行期模块解析 → （exe 态）PyInstaller 收集清单
- 存在性判定：⚠️ 部分存在（`requirements.txt` 已含裸 `xlrd`；**`spec` 无 `'xlrd'`**）

#### 2. 现状与缺陷判定
```text
# requirements.txt（2026-10-05 被外部插入，无版本约束、无注释）
xlrd
# RPA_Workflow_v3.spec（hiddenimports 17 项，含 13 个 ops 模块；无 xlrd）
# excel_preprocessor.py L14 docstring 声明依赖 xlrd>=2.0
# excel_preprocessor.py L102
    sheets = pd.read_excel(src, engine="xlrd", sheet_name=None)
```
- 缺陷判定补充事实（本轮实测）：**全库 `^\s*import xlrd` 命中数 = 0**；`spec` 内 `xlrd` 命中数 = 0；`requirements.txt` 命中 1
- 缺陷类型：**【缺少容错】**（打包链缺项：PyInstaller 静态分析依赖 `import` 语句，而 xlrd 仅以字符串形式传给 pandas → 收集不到 → 必须显式列入 `hiddenimports`）
- 阻断后果链：exe 态选 `.xls` → `ensure_xlsx` L102 → `ImportError` → 逃逸（见 `A-02`）→ **文件级中断 ＋ 入口按钮锁死**

#### 3. 修改方案
**A. 修改型**（目标已存在）
- 改动点 1：`requirements.txt` 的 `xlrd` 行
  - 改前：`xlrd`
  - 改后：`xlrd>=2.0          # .xls 读取（ops/excel_preprocessor.py L102 engine="xlrd"；见 excel_preprocessor.py 顶部 docstring）`
  - 说明：补版本约束与来源注释（与既有条目风格一致：`pandas>=2.0          # ...`）
- 改动点 2：`RPA_Workflow_v3.spec` 的 `hiddenimports`
  - 改前：17 项，无 `'xlrd'`
  - 改后：追加 `'xlrd',` 与 `'ops.excel_normalizer',`（后者见 `Part 4`；须附注释说明"xlrd 从未被 import，静态分析收集不到"）
  - 说明：补齐打包链（本项只加 `'xlrd'`；`'ops.excel_normalizer'` 属新建模块登记，见 Part 4）
- **B. 新建型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`spec` 的 `datas`／入口配置／`console=False`；`requirements.txt` 的其他条目
- 不可引入的新依赖：**是**（`xlrd` 已在清单中，本项只补版本约束与打包清单，**不新增包**）
- 必须保留的接口/信号：`ensure_xlsx(file_path) -> str`
- 必须遵循的规约：`AGENTS.md` §1（**构建由人工接管**，Agent 不跑 `build.bat`、不改 `build/`）；`docs/build-guide.md` §1.10（产物有效性判据）

#### 5. 验证
- 用例构造：一个真实 `.xls` 文件（老格式 BIFF）
- 期望输出：源码态导入成功；人工重建 exe 后，exe 态导入 `.xls` 成功
- 失败判据：exe 态仍报 `No module named 'xlrd'`
- 自证方式：人工执行 `build.bat` → 检查 `build/work/.../warn-RPA_Workflow_v3.txt` 中**不再**出现 `missing module named xlrd`（v7 记载原值：`warn-RPA_Workflow_v3.txt:279`）`[UNVERIFIED]` → 用真实 `.xls` 走一遍导入

#### 6. 风险与回滚
- 可能回归点：`hiddenimports` 增加会略增包体；错误拼写会静默无效（须核对 exe 行为）
- 回滚方式：`spec`／`requirements.txt` 备份至 `_temp/ImportData/backup/`
- 降级策略：若 exe 仍收集不到，降级为「显式 `import xlrd` 于 `ensure_xlsx`」或改用其他读取路径，并回报人工（**不得**引入新依赖）

#### 7. 验收标准
- [ ] `requirements.txt` 的 `xlrd` 有版本约束与来源注释
- [ ] `spec` 的 `hiddenimports` 含 `'xlrd'`
- [ ] 人工重建后 exe 态可导入 `.xls`；构建警告不再出现 `missing module named xlrd`

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `requirements.txt`、`RPA_Workflow_v3.spec`、`rpa_engine/ops/excel_preprocessor.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-18 [原编号: DM-03] 转换产物无冲突检测

> 规则：H10 ｜ 等级：文件级 ｜ **批次：P1** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_preprocessor.py`
- 目标：`ensure_xlsx`（L70-128，产物路径与大写在 L117-119）
- 调用链：上游 `page_input_selection._on_add_files` L404 → 本处 → 下游 L408 `_scan_sheets`
- 存在性判定：❌ 不存在（无检测）

#### 2. 现状与缺陷判定
```python
# excel_preprocessor.py L117-119（with_suffix 无冲突检测、无条件覆盖）
    new_path = src.with_suffix(".xlsx")
    sheet_count = len(wb.sheetnames)
    wb.save(str(new_path))
```
- 缺陷类型：**【缺少容错】**（目标路径直接由源名推导，不检查是否已存在）
- 阻断后果链：临时区已有同名 `.xlsx`（可能是另一张已登记表的副本）→ 转换产物路径相同 → `wb.save` **覆盖** → 后续导入读到被替换的内容 → **文件级：静默错表**（与 `A-12` 同机制的两个触发面）

#### 3. 修改方案
**A. 修改型**（目标已存在）
- 改动点 1：`ops/excel_preprocessor.py::ensure_xlsx` L117-119
  - 改前：`new_path = src.with_suffix(".xlsx")`
  - 改后：
    ```python
    new_path = src.with_suffix(".xlsx")
    counter = 1
    while new_path.exists():
        new_path = src.with_name(f"{src.stem}_{counter}.xlsx")
        counter += 1
    ```
  - 说明：**与 `A-12` 改动点 1 为同一处改动**（避免重复施工）；差异仅在于本项强调"转换侧"的触发链
- **B. 新建型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`ensure_xlsx` 的返回值语义（仍为 xlsx 路径字符串）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`ensure_xlsx(file_path) -> str`
- 必须遵循的规约：裁定 Q4（不静默覆盖，改名＋提示）

#### 5. 验证
- 用例构造：临时区预置一个与 `电费.xls` 同名（去后缀）的 `电费.xlsx` 副本，再选入 `电费.xls`
- 期望输出：转换产物为 `电费_1.xlsx`（不覆盖既有）；既有副本内容不变
- 失败判据：既有 `电费.xlsx` 内容被替换
- 自证方式：转换前后对比既有副本的行数/列名；列出临时区文件清单

#### 6. 风险与回滚
- 可能回归点：序号命名导致的默认别名变化（`clean_alias_name(file_path.stem)` 会带上 `_1`）
- 回滚方式：`excel_preprocessor.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若序号命名影响别名可读性，改为「在同名时拒绝并提示用户改名」（仍需人工裁定）

#### 7. 验收标准
- [ ] `.xls` 转换不覆盖既有同名 `.xlsx`
- [ ] 转换产物可被正常扫描与导入
- [ ] 与 `A-12` 使用同一实现（无两套查重口径）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_preprocessor.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### A-19 [原编号: H-18] 换表身份只比 `sheet_name` → 同名 sheet 静默错表

> 规则：R1＋H10 ｜ 等级：文件级 ｜ **批次：P0** ｜ 判定：**【逻辑错误】** ｜ 已裁定：**保留 A 类**（problem.md 附录 G 第 1 项）

#### 1. 定位
- 文件：`rpa_engine/gui/main_window.py`
- 目标：`_on_confirm_import` 的编号重排检测段（L332-352，身份映射在 L335-341）
- 调用链：上游 导入循环 L294-330 → 本处 L335-341 → 下游 L342-352 弹窗
- 存在性判定：✅ 已存在（比对口径不完整）

#### 2. 现状与缺陷判定
```python
# main_window.py L335-341（旧/新身份映射只取 table_id → sheet_name）
        old_map = {e["table_id"]: e.get("sheet_name")
                   for e in self._table_entries}
        if old_map and self.model.steps:
            new_ids = {e["table_id"] for e in registry}
            new_sheet = {e["table_id"]: e.get("sheet_name") for e in registry}
            disturbed = {tid for tid, sh in old_map.items()
                         if tid not in new_ids or new_sheet.get(tid) != sh}
```
- 缺陷类型：**【逻辑错误】**（身份比对缺少文件维度；`sheet_name` 相同时视为"未变化"）
- 阻断后果链：导 `A\电费.xlsx`（sheet `1月`）→ 配置 5 步 → 返回阶段 1 → 改导 `B\电费.xlsx`（sheet 也叫 `1月`）→ `disturbed` 为空 → L342 弹窗**不弹** → 步骤继续指向新表 → **文件级：步骤静默指向错误数据表**（结果错但程序报成功）

#### 3. 修改方案
**A. 修改型**（目标已存在）
- 改动点 1：`gui/main_window.py::_on_confirm_import` L335-341
  - 改前：`old_map`／`new_sheet` 仅取 `sheet_name`
  - 改后：
    ```python
    def _identity(e):
        """身份三元组：文件名 + 源路径 + sheet 名（R1：源文件身份须可复现）。"""
        src = str(e.get("source_path") or e.get("file_path") or "")
        return (Path(src).name, src, e.get("sheet_name", ""))
    old_map = {e["table_id"]: _identity(e) for e in self._table_entries}
    new_map = {e["table_id"]: _identity(e) for e in registry}
    disturbed = {tid for tid, ident in old_map.items()
                 if tid not in new_map or new_map.get(tid) != ident}
    ```
  - 说明：任一维（文件名／路径／sheet）不同即视为"身份变化"→ 弹窗提醒（承接 `A-10` 的 `source_path`）
- 改动点 2：同段 L349-352 弹窗文案
  - 改前：`"数据表编号已重新分配，以下步骤引用的表发生变化，请检查其参数：\n"`
  - 改后：追加说明"（本次所选文件的来源路径或工作表与上次不同）"，使用户理解原因
- **B. 新建型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：编号分配规则（`table_id = f"T{i+1}"`，L295）；阶段 2 的步骤结构
- 不可引入的新依赖：是（`pathlib.Path` 已在 `main_window.py` 使用）
- 必须保留的接口/信号：`_table_entries`（旧注册表快照）与 `registry`（本轮回填）的既有语义
- 必须遵循的规约：裁定 F1③（改 `:335-341` 用 `source_path` 比对，三元组任一不同即提示）；裁定 G3（**须修，不降级为取舍**）

#### 5. 验证
- 用例构造：目录 `A/` 与 `B/` 各放一个 `电费.xlsx`（sheet 名同为 `1月`，内容不同）；先导 A 配 1 步，返回阶段 1 再导 B
- 期望输出：出现「数据表引用已变化」提醒，指出受影响步骤
- 失败判据：无任何提醒，步骤继续引用（已被替换的）同名 sheet
- 自证方式：UI 断言弹窗出现；断点/日志检查 `disturbed` 集合非空

#### 6. 风险与回滚
- 可能回归点：① 误报（同一文件重新导入时路径相同 → 不触发，正确）；② `source_path` 缺失时退化为路径比对（`file_path` 为副本路径，跨会话必变 → 可能**过度提醒**）
- 回滚方式：`main_window.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若 `source_path` 未贯通（即 `A-10` 未落地），先把比对降级为「`sheet_name` ＋ 源文件大小/行数指纹」；**不得**因此保留静默行为

#### 7. 验收标准
- [ ] 同名 sheet 换文件时出现提醒并列出受影响步骤
- [ ] 同一文件重新导入时不产生误报
- [ ] 与 `A-10` 同批交付（`source_path` 已贯通）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/main_window.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

## Part 2′ · 规则落地项（REQ，12 项）

> **来源声明**：本节各项来源＝**需求说明的需求规则**（R1~R7／H1~H10），**不是** problem.md 的问题条目；其判定依据为「该规则在 problem.md 中完全没有对应编号」（判定规则见 Part 0 §0.5）。因此本节**不参与** problem.md 的闭合计数。
> 顺序＝批次顺序（P2→P5）。

---

### REQ-R2 [来源: 需求 R2] 指定表头行全空时拒绝并提示

> 规则：R2 ｜ 等级：表级 ｜ **批次：P2** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）／`rpa_engine/ops/excel_preprocessor.py`
- 目标：`read_excel_sheet`（L171-220，`skiprows` 在 L213）；阶段 1 的表头行选择 `_HeaderRowDialog`／`InputSelectionPage._on_pick_header`（L559-576）
- 调用链：上游 `page_input_selection._on_pick_header`（用户选行）→ 存 `entry.header_row` → `import_excel_table` → 本处校验 → 下游 `pd.read_excel(skiprows=...)`
- 存在性判定：⚠️ 部分存在（「表头行上移」＝`skiprows` 已实现 L213；**"全空则拒绝"未实现**——现有防护仅覆盖"整表预览全空"：`_add_row` L520-522 禁用按钮、`_on_pick_header` L561-564 提示）

#### 2. 现状与缺陷判定
```python
# excel_preprocessor.py L210-215（skiprows 物化已实现，但无"该行是否全空"校验）
    df = pd.read_excel(
        str(src),
        sheet_name=sheet_name,
        skiprows=header_row - 1,   # 物化"删前 N-1 行"
        header=0,                  # 跳过后的首行作为表头
    )
```
- 缺陷类型：**【缺失实现】**（现有防护只判"整表无内容"，不判"用户选中的那一行是否全空"）
- 阻断后果链：用户选中一个全空行作表头（例如报表中夹着一条分隔空行）→ `skiprows` 上移该空行 → 读入后列名为 `Unnamed: 0`／`nan` 系列 → 建表列名语义丢失（配合 `REQ-H1` 才不崩，但语义已错）→ **表级：表头语义错误**（结果错误但程序报成功）

#### 3. 修改方案
**A. 修改型 ＋ B. 新建型（组合）**
- 改动点 1（修改）：`ops/table_importer.py::import_excel_table`（在 L76 读取之前插入预检）
  - 改前：直接调用 `read_excel_sheet` / `normalize_sheet`
  - 改后：先以只读方式取该表头行原始内容（复用 `sheet_info`／`scan_sheets` 已开簿结果，避免三次开簿）：
    ```python
    header_vals = read_header_row(xlsx_path, sheet_name, header_row)   # 见改动点 2
    if header_vals is None or all(str(v or "").strip() == "" for v in header_vals):
        raise ValueError(
            f"数据表 [{sheet_name}] 的第 {header_row} 行为空，"
            f"不能作为表头。请重新选择表头行后重试。")
    ```
  - 说明：把失败前移到导入入口并给人话
- 改动点 2（新建函数）：`ops/excel_preprocessor.py::read_header_row(file_path, sheet_name, header_row) -> Optional[List[Any]]`
  - 骨架：
    ```python
    def read_header_row(file_path: str, sheet_name: str, header_row: int) -> Optional[List[Any]]:
        """只读取出指定表头行的原始单元格值（不读整表，供 R2 全空校验）。

        Returns: 该行原值列表；行号越界返回 None。
        """
    ```
  - 说明：用 `load_workbook(read_only=True, data_only=True)` 逐格读取该一行，**不加载整表**（§2.1 条 5）
- **C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`read_excel_sheet` 的签名与 `skiprows` 语义；阶段 1 的表头行 UI 交互（不改布局）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`_on_pick_header` 的交互；`entry.header_row`（1-based）
- 必须遵循的规约：R2 规则定义（**不得**改成"自动找表头行"——需求明定由用户人工指定）；`AGENTS.md` §2.1 条 5

#### 5. 验证
- 用例构造：`表头空行.xlsx`——第 1 行为空、第 2 行为真表头、第 3 行起数据；用户在阶段 1 选第 1 行作表头
- 期望输出：导入失败并提示「第 1 行为空，不能作为表头。请重新选择表头行后重试。」
- 失败判据：导入成功但列名为 `Unnamed: 0` 等；或抛技术原文
- 自证方式：UI 失败清单文案；`logs/gui_*.log` 中的 ValueError 文本

#### 6. 风险与回滚
- 可能回归点：① 表头行含"看似空白"的合法列名（如全角空格）→ 判定须 `strip()` 后再比较；② 多开一次簿带来的耗时
- 回滚方式：`table_importer.py`／`excel_preprocessor.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若多开簿耗时不可接受，则复用 `normalize_sheet` 首行的 `header_vals` 结果（一次开簿同时产出）

#### 7. 验收标准
- [ ] 选中全空行作表头时被拒绝且给出中文提示
- [ ] 正常表头行（含中文、空格）不被误拒
- [ ] 只读方式取表头行，未加载整表（内存增幅可忽略）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）／`rpa_engine/ops/excel_preprocessor.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### REQ-R4 [来源: 需求 R4] 公式求值替换（本轮只做兜底路径）

> 规则：R4 ｜ 等级：单元格级 ｜ **批次：P3** ｜ 判定：**【缺失实现】** ｜ **人工裁定：本轮不引入 win32com**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）
- 目标：normalizer 的 `resolve_formula_cells`
- 调用链：上游 `normalize_sheet` → 本处 → 下游 `apply_na_policy`（`A-08`）／类型推断（`A-04`）
- 存在性判定：❌ 不存在（全链路无公式处理逻辑）

#### 2. 现状与缺陷判定
```text
现状：读取走 pd.read_excel（openpyxl 默认 data_only 语义），
     - 文件曾被 Excel 打开过 → 有缓存值 → 读到值（正确）
     - 从未被打开过（或公式结果未缓存）→ 读到 None → 落库 NULL（静默丢值）
```
- 缺陷类型：**【缺失实现】**（R4 未实现；且现状是"静默填 NULL"，正是需求明令禁止的行为）
- 阻断后果链：含公式的单元格无缓存值 → `pd.read_excel` 得 `None` → 落库 NULL → 导出空单元格 → **单元格级静默丢值**（原文彻底消失，无日志、无提示）

#### 3. 修改方案
**B. 新建型**（`excel_normalizer.py` 内新函数；**不引入 win32com**）
- 骨架：
  ```python
  def resolve_formula_cells(ws_tex, ws_val, df, offset_rows: int, offset_cols: int = 0) -> tuple:
      """R4（兜底路径）：对缓存值为空的单元格，读其公式原文并保留 + 告警。

      设计（本轮人工裁定）：不调用 Excel COM（不引入 pywin32，遵循"不引入新依赖"）。
      策略：优先用 openpyxl 缓存值；缓存为空且该格存在公式 → 写入公式原文
            并记入告警（绝不静默填 NULL）。
      Returns: (df_out, formula_cells)
      """
  ```
- 实现要点：
  ① 需**两次开簿**：`load_workbook(..., read_only=True, data_only=True)`（取值）与 `load_workbook(..., read_only=True, data_only=False)`（取公式文本）——**须在同一函数内复用、及时 `wb.close()` 并 `gc.collect()`**（§2.1 条 5）
  ② 只对"缓存值为空"的格去取公式文本（避免全表扫描双份）
  ③ 命中 → `df` 对应格写公式原文（如 `=SUM(B2:B9)`），并在 `formula_cells` 记 `(行, 列, 公式原文, "cached_empty")`
  ④ **绝不**把空缓存写成 NULL 而不留痕
- 职责边界：本函数只做"公式兜底与留痕"；**不做**类型转换（→ `A-04`）、不做空值策略（→ `A-08`）
- **A. 修改型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`read_excel_sheet` 的签名；**不得**引入 `pywin32`／`win32com`（硬约束 §0.2 条 1）
- 不可引入的新依赖：**是**（本项即因该约束而降级）
- 必须保留的接口/信号：`NormalizeResult.dataframe`／`warnings`（Part 4 契约）
- 必须遵循的规约：R4 容错等级＝**单元格级**（不得因单格失败放弃整表）；"绝不静默填 NULL"

#### 5. 验证
- 用例构造：① `公式.xlsx` 由脚本（openpyxl）写入，**不**用 Excel 打开（无缓存）——A1=`=1+2` ② 同文件再用 Excel 打开保存一次（有缓存）
- 期望输出：① 该格入库为公式原文且报告/告警含"缓存为空、已保留公式文本" ② 该格入库为缓存值
- 失败判据：① 入库 NULL 且无任何告警；② 因公式问题导致整表导入失败
- 自证方式：临时库 `SELECT typeof(列), 列`；`REQ-H9` 报告中 `formula_cells` 条目

#### 6. 风险与回滚
- 可能回归点：① 双开簿使大文件内存/耗时上升；② 公式原文入库改变既有列语义（用户看到 `=SUM(...)`）
- 回滚方式：normalizer 为新增文件；回退＝在 `table_importer` 回切 `read_excel_sheet`
- 降级策略：若双开簿不可接受，降级为「仅告警留痕（不写公式原文）＋ 报告提示用户'该表含未计算公式，请在 Excel 中打开并保存后重试'」——**仍不得静默填 NULL**

#### 7. 验收标准
- [ ] 公式缓存为空时**不静默填 NULL**：或保留公式原文，或留痕告警并提示用户重试
- [ ] 有缓存时行为与改动前一致（读到计算值）
- [ ] 未引入任何新依赖；`requirements.txt` 无 `pywin32`
- [ ] win32com 分支在本计划中标注为「需人工裁定后另行立项」（见 Part 6 待人工补全清单）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### REQ-R5 [来源: 需求 R5] 超链接展开为链接地址文本

> 规则：R5 ｜ 等级：单元格级 ｜ **批次：P3** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）
- 目标：normalizer 的 `expand_hyperlinks`
- 调用链：上游 `normalize_sheet` → 本处 → 下游 类型推断与空值策略
- 存在性判定：❌ 不存在（全链路无 `cell.hyperlink` 读取）

#### 2. 现状与缺陷判定
```text
现状：pd.read_excel 只取单元格显示值；超链接单元格的显示文本（如"查看明细"）
     被读入，"查看明细" 指向的地址完全丢失。
```
- 缺陷类型：**【缺失实现】**（R5 未实现）
- 阻断后果链：超链接单元格 → 只有显示文本入库 → 地址信息丢失 → **单元格级信息丢失**（交付报表丢失原始链接，用户无法追溯；且不属于"错误值"，程序静默通过）

#### 3. 修改方案
**B. 新建型**
- 骨架：
  ```python
  def expand_hyperlinks(ws, df, offset_rows: int) -> tuple:
      """R5：超链接单元格替换为链接地址文本（不展开外部引用）。

      Args:
          ws: data_only=False 打开的工作表（超链接元数据在此模式下可读）。
          df: 已读入的 DataFrame（列名已上移）。
          offset_rows: skiprows 偏移（header_row - 1）。
      Returns:
          (df_out, link_cells)  link_cells 记 (行, 列, 显示文本, 目标地址)
      """
  ```
- 实现要点：① 遍历 `ws.iter_rows`，取 `cell.hyperlink.target`（`location` 形式的外链**不**展开，仅记录 `target`）；② 命中则把该格值替换为**地址文本**；③ 每条记入 `link_cells` 供 `REQ-H9` 报告；④ 仅在检测到任一 `cell.hyperlink` 时才做全表遍历（先做一次快速探测以省开销）
- 注意：R5 明定"**不展开外部引用**"——即不解析、不下载、不实现公式化引用，只把地址写成文本
- **A. 修改型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：读取主链路；不得改变 `normalize_sheet` 返回结构
- 不可引入的新依赖：是（`openpyxl` 已在清单）
- 必须保留的接口/信号：`NormalizeResult.dataframe`
- 必须遵循的规约：R5 规则定义（不展开外部引用）；`AGENTS.md` §2.1 条 5

#### 5. 验证
- 用例构造：`超链接.xlsx`——A1 单元格显示 `查看明细`，超链接指向 `https://example.invalid/abc`
- 期望输出：入库值为 `https://example.invalid/abc`；报告中出现该替换记录
- 失败判据：入库值仍为 `查看明细`（地址丢失）；或程序尝试访问外链
- 自证方式：临时库查询该格值；`REQ-H9` 报告的 `link_cells` 条目

#### 6. 风险与回滚
- 可能回归点：① 用户本期望保留"显示文本"→ 属**需求明确要求**，须在报告中告知；② 全表遍历耗时
- 回滚方式：normalizer 新文件可删；调用点回切
- 降级策略：若遍历耗时不可接受，降级为「仅在报告中列出超链接位置，不做替换」并标注"未展开"

#### 7. 验收标准
- [ ] 超链接单元格入库为地址文本，且报告可查
- [ ] 不访问外链、不展开外部引用
- [ ] 无超链接的表行为不变（无额外耗时）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### REQ-R7 [来源: 需求 R7] 内容清洗（trim／`\x00`）与空值口径

> 规则：R7 ｜ 等级：单元格级 ｜ **批次：P4** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）
- 目标：normalizer 的 `clean_cell_text`
- 调用链：上游 `normalize_sheet` → 本处 → 下游 `A-08` 的空值策略与 `A-04` 的类型推断
- 存在性判定：❌ 不存在（无 strip、无 `\x00` 去除）

#### 2. 现状与缺陷判定
```text
现状：单元格文本原样入库——首尾空格、全角空格、不可见控制字符 \x00 全部保留。
     空值判定交由 pandas 默认规则（见 A-08）。
```
- 缺陷类型：**【缺失实现】**（R7 未实现）
- 阻断后果链：带首尾空格的文本 → 入库含空格 → 分组/匹配（`aggregate` 的 GROUP BY、`mapping_match` 的连接键）**静默不相等** → 结果错误但程序报成功（单元格级静默错误，排查极难）

#### 3. 修改方案
**B. 新建型**
- 骨架：
  ```python
  def clean_cell_text(series: "pd.Series", meta: dict, col: str) -> "pd.Series":
      """R7：逐单元格去除首尾空格与 null 字符；空值统一规范化为 NULL。

      说明：仅对 str 类型生效（数值/日期不动）；清洗后为空的单元格
            交 A-08 的空值策略统一处理（避免双口径）。
      Returns: 清洗后的 Series（meta[col]["cleaned"] = True 若发生变更）。
      """
  ```
- 实现要点：① `str.strip()`；② 去除 `\x00`（`.replace("\x00", "")`）与 `\x0b`／`\x0c`；③ 同时处理全角空格 `\u3000`（strip 前后）；④ 仅记录"发生变更"的列与条数（不逐格记录，避免报告爆炸）
- 注意：**不得**改变数值/日期列；**不得**与 `A-08` 的空值策略重复（清洗后为空的格交 `A-08` 判定）
- **A. 修改型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：读取链路；不得在 `read_excel_sheet` 内做清洗（职责归 normalizer）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`NormalizeResult.dataframe`
- 必须遵循的规约：R7 规则定义；**裁定 G1／D10「所见即所得」的边界**——表头**不得**静默清洗（属 `A-03` 拒绝口径），仅**数据单元格**可清洗

#### 5. 验证
- 用例构造：`清洗.xlsx` 的 `地区` 列含 `" 华东 "`、`"华东\u3000"`、`"华东\x00"` 三种变体，另有 1 行干净 `"华东"`
- 期望输出：4 行入库后 `地区` 全为 `华东`；按 `地区` 分组得 1 组（非 4 组）
- 失败判据：分组出现 4 个组；或表头被清洗（违反 D10 边界）
- 自证方式：`SELECT 地区, COUNT(*) FROM t1 GROUP BY 地区`；对比改动前结果

#### 6. 风险与回滚
- 可能回归点：① 业务上"首尾空格有意义"的极端场景（罕见，须在报告中告知）；② 逐列 apply 的性能
- 回滚方式：normalizer 新文件可删
- 降级策略：若性能不达标，仅对"参与分组/匹配的列"清洗（须在报告中标注清洗范围）

#### 7. 验收标准
- [ ] `" 华东 "`／`"华东\u3000"`／`"华东\x00"` 清洗后与 `"华东"` 一致
- [ ] 数值/日期列未被清洗
- [ ] 表头未被静默清洗（仍走 `A-03` 的拒绝口径）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### REQ-H1 [来源: 需求 H1] 重复列名自动去重并在报告中列出

> 规则：H1 ｜ 等级：表级 ｜ **批次：P5** ｜ 判定：**【缺失实现】**（现状＝仅日志）

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）／`rpa_engine/ops/table_importer.py`
- 目标：normalizer 的 `dedup_columns`；`import_excel_table`（L84-89 的重复表头告警）
- 调用链：上游 `normalize_sheet` → 本处 → 下游 `import_dataframe`
- 存在性判定：⚠️ 部分存在（pandas 会自动加 `.1` 后缀；`table_importer` L85-89 **仅 `logger.warning`**，未进报告）

#### 2. 现状与缺陷判定
```python
# table_importer.py L84-89（现状：仅日志，不报告）
    if len(set(map(str, df.columns))) != len(df.columns):
        logger.warning(
            f"[table_importer] 源数据表存在重复表头，pandas 已自动加后缀: "
            f"{list(df.columns)}"
        )
```
- 缺陷类型：**【缺失实现】**（去重结果非确定性命名、未进报告；`金额.1` 与需求要求的 `金额_2` 不一致）
- 阻断后果链：重复表头 → pandas 产生 `金额`／`金额.1` → 用户看不懂、报告未告知 → **表级：列名歧义**（下游步骤按 `金额` 引用时会命中第一个，静默错列）

#### 3. 修改方案
**B. 新建型**
- 骨架：
  ```python
  def dedup_columns(columns: List[str]) -> tuple:
      """H1：重复列名按 `原名`、`原名_2`、`原名_3` 归一（确定性命名）。

      Returns: (new_columns, renamed)  renamed 记 (原值, 新值, 该名出现次数)
      """
  ```
- 实现要点：① 首次出现保持原名，第 2 次起为 `原名_2`／`原名_3`…（**与需求措辞一致**，替代 pandas 的 `.1`）；② 空列名按 `未命名列_N` 归一（与 `A-03` 改动点 1 的第 ② 条共用一处实现）；③ 全部变更记入 `renamed` → 交 `REQ-H9` 报告
- 调用点：`ops/table_importer.py` L84-89 的告警段改为「调用 `dedup_columns` ＋ 把 `renamed` 写入报告」；`table_importer` 的日志保留（便于开发者排查）
- **A. 修改型**：不适用　**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`import_dataframe` 的列名语义；表头**内容**不得被改写（D10：仅处理"重名"，不处理"脏字符"）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`NormalizeResult.dataframe.columns` 为唯一的列名来源
- 必须遵循的规约：H1 规则定义（`金额`→`金额`、`金额_2`、`金额_3`）；`AGENTS.md` §2.1 条 6（报告须人可读）

#### 5. 验证
- 用例构造：`重名列.xlsx` 表头为 `金额|金额|金额|备注`
- 期望输出：入库列名为 `金额`／`金额_2`／`金额_3`／`备注`；`REQ-H9` 报告列出重命名记录
- 失败判据：列名为 `金额`／`金额.1`／`金额.2`；或报告无记录
- 自证方式：`PRAGMA table_info(t1)`；报告文件内容

#### 6. 风险与回滚
- 可能回归点：① 既有 `tests/test_step_catalog.py` 等对列名的断言（须检查）；② 与 `A-03` 的空列名归一重复实现
- 回滚方式：`table_importer.py` 备份；normalizer 新文件可删
- 降级策略：若重命名破坏既有测试，保留 pandas 行为但**必须**把变更写入报告（报告要求优先于命名风格）

#### 7. 验收标准
- [ ] 重复列名按 `_2`／`_3` 归一，报告列出
- [ ] 空列名归一为 `未命名列_N` 并入报告
- [ ] 回归全绿

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）／`rpa_engine/ops/table_importer.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### REQ-H3 [来源: 需求 H3] 布尔值 → 1/0（INTEGER）＋元数据标记

> 规则：H3 ｜ 等级：单元格级 ｜ **批次：P4** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）
- 目标：normalizer 的类型推断分支（与 `A-04` 的 `infer_cell_type` 同处）
- 调用链：`normalize_sheet` → `infer_cell_type` → 本项分支 → 下游落库
- 存在性判定：❌ 不存在

#### 2. 现状与缺陷判定
```text
现状：Excel 布尔单元格（TRUE/FALSE）经 pandas 读取后表现为 Python bool
     → to_sql 后落库为 INTEGER 0/1（部分场景）或 TEXT 'True'/'False'（取决于列混合情况）
     且无元数据标记，无法在回传时还原为布尔。
```
- 缺陷类型：**【缺失实现】**（结果形态不确定、无元数据）
- 阻断后果链：布尔列混合其它类型 → 落库形态不一致（同列 storage class 混杂）→ 导出后既有 `1/0` 又有 `True/False` → **单元格级结果不一致**（用户按 1/0 统计时漏数）

#### 3. 修改方案
**B. 新建型**（并入 `infer_cell_type` 的判定链）
- 实现要点（在 `A-04` 的 `infer_cell_type` 判定级次中插入一级）：
  - 新增判定级：`isinstance(raw, bool)` 或字符串（`strip().upper()` ∈ {`TRUE`,`FALSE`}）→ 返回 `(1 if truthy else 0, "int")`，并在 `meta[col]["original_type"] = "bool"`、`meta[col]["normalized"] = "bool01"`
  - **须在类型推断之前**执行（bool 是 int 的子类，Python 里 `True == 1`，若先走整数分支会丢失标记）
- 调用点：`normalize_sheet` 的列级推断循环
- **A. 修改型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`A-04` 的阈值口径（5 位可配）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`infer_cell_type(raw, max_significant_digits) -> (value, target_type)`
- 必须遵循的规约：H3 规则定义（`TRUE/FALSE` → `1/0`（INTEGER）＋元数据标记）

#### 5. 验证
- 用例构造：`布尔.xlsx` 的 `是否有效` 列含 `TRUE`／`FALSE`／空白
- 期望输出：入库为 INTEGER `1`／`0`／NULL；元数据 `original_type = "bool"`
- 失败判据：入库为 TEXT `TRUE`／`False`；或 `1/0` 与 `True/False` 混杂
- 自证方式：`SELECT 是否有效, typeof(是否有效) FROM t1`；元数据表查询

#### 6. 风险与回滚
- 可能回归点：① 文本列中恰好写着 `TRUE` 的普通文本被误转（须限定"整列皆为布尔形态"才转，否则保留文本并告警）
- 回滚方式：normalizer 新文件可删
- 降级策略：无法确定列级语义时，降级为「保留原文本 ＋ 报告标记疑似布尔列」

#### 7. 验收标准
- [ ] 布尔列入库为 INTEGER 1/0，元数据标记 `bool`
- [ ] 混有普通文本的列不被误转（保留文本并告警）
- [ ] 无布尔列的表行为不变

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### REQ-H4 [来源: 需求 H4] 错误值 → NULL ＋ 原文留痕（不中断导入）

> 规则：H4 ｜ 等级：单元格级 ｜ **批次：P4** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）
- 目标：normalizer 的 `normalize_error_cells`
- 调用链：`normalize_sheet` → 本处 → 下游 `A-08` 空值策略
- 存在性判定：❌ 不存在

#### 2. 现状与缺陷判定
```text
现状：Excel 错误值（#N/A／#DIV/0!／#VALUE!／#REF! 等）经 pandas 读取后
     常表现为字符串（如 "#N/A"）或 NaN，落库形态不确定，且无留痕。
```
- 缺陷类型：**【缺失实现】**（形态不确定、无留痕、与 `A-08` 的字面 `NA` 口径可能互相干扰）
- 阻断后果链：错误值单元格 → 或入库为 `#DIV/0!` 文本（污染数据）、或为 NULL 但无留痕 → **单元格级结果不确定 ＋ 不可追溯**；若误判为"字面 NA 保留"则错误值会进报表

#### 3. 修改方案
**B. 新建型**
- 骨架：
  ```python
  ERROR_VALUE_PATTERN = r"^#(N/A|DIV/0!|VALUE!|REF!|NAME\?|NUM!|NULL!|GETTING_DATA)$"

  def normalize_error_cells(df, meta: dict) -> tuple:
      """H4：Excel 错误值统一转 NULL ＋ 原文留痕（绝不中断导入）。

      Returns: (df_out, error_cells)  error_cells 记 (行, 列, 原文)
      """
  ```
- 实现要点：① 判定**须在 `A-08` 的字面 NA 保留策略之前**执行（否则 `#N/A` 会被"保留"策略放过）；② 命中 → 置 NULL 并记原文；③ 单格失败绝不影响整表（R4/H4 均为单元格级容错）
- 调用点：`normalize_sheet` 的处理管线顺序＝**公式兜底(R4) → 错误值(H4) → 超链接(R5) → 清洗(R7) → 空值策略(A-08) → 类型推断(A-04)**（顺序即为实现规范，不得颠倒）
- **A. 修改型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`A-08` 的字面 NA 保留策略（须靠**顺序**保证互不干扰，不靠改策略）
- 不可引入的新依赖：是（`re` 标准库）
- 必须保留的接口/信号：管线顺序（见上）
- 必须遵循的规约：H4 规则定义（统一转 NULL ＋ 记录错误原文到元数据，**不中断导入**）

#### 5. 验证
- 用例构造：`错误值.xlsx` 的 `比率` 列含 `#DIV/0!`／`#N/A`／`0.5`
- 期望输出：前两格入库 NULL；`0.5` 正常；元数据记录两条错误原文；**该表仍成功导入**
- 失败判据：`#DIV/0!` 作为文本入库；或该表导入失败
- 自证方式：`SELECT 比率, typeof(比率) FROM t1`；元数据表；`REQ-H9` 报告

#### 6. 风险与回滚
- 可能回归点：① 与 `A-08` 的 `NA` 保留策略冲突（靠管线顺序规避）；② 正则误伤（`#N/A` 出现在普通文本中，如 `编号#N/A-01`）→ 须用**整格完全匹配**（`fullmatch`）
- 回滚方式：normalizer 新文件可删
- 降级策略：若正则误伤，收窄为"仅当整列为错误值形态时处理"

#### 7. 验收标准
- [ ] 错误值入库为 NULL，元数据留原文，导入不中断
- [ ] 普通文本中的 `#` 序列不被误转（整格匹配）
- [ ] 与 `A-08` 策略并存无冲突（`#N/A` 走 H4、字面 `NA` 走 A-08）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### REQ-H5 [来源: 需求 H5] 全空列保留并标记／尾部全空行裁剪

> 规则：H5 ｜ 等级：表级 ｜ **批次：P5** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）
- 目标：normalizer 的 `handle_empty_cols_rows`
- 调用链：`normalize_sheet` → 本处 → 下游 `import_dataframe`
- 存在性判定：❌ 不存在

#### 2. 现状与缺陷判定
```text
现状：全空列原样入库（无标记）；尾部全空行也被原样入库（形成"0 行数据却有 N 行空行"的观感）。
```
- 缺陷类型：**【缺失实现】**（H5 未实现）
- 阻断后果链：报表尾部习惯性留白 → 入库含大量全空行 → 行数统计虚高（用户按行数核对报表时对不上）；全空列无标记 → 元数据无法解释"为什么多了这一列" → **表级结果观感错误**

#### 3. 修改方案
**B. 新建型**
- 骨架：
  ```python
  def handle_empty_cols_rows(df, meta: dict) -> tuple:
      """H5：全空列保留但标记；尾部连续全空行裁剪。

      Returns: (df_out, empty_cols, trimmed_rows)
      """
  ```
- 实现要点：① **尾部**连续全空行裁剪（不得裁剪中间空行——中间空行是数据行）；② 全空列保留且 `meta[col]["all_empty"] = True`；③ 裁剪行数写入 `trimmed_rows` 供报告
- **A. 修改型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：数据行语义（中间空行必须保留）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`NormalizeResult.dataframe`
- 必须遵循的规约：H5 规则定义（全空列**保留**但标记；**尾部**全空行裁剪）

#### 5. 验证
- 用例构造：`空列空行.xlsx`——3 列（第 3 列全空），5 行数据 ＋ 尾部 20 行空白
- 期望输出：入库 3 列（第 3 列标记 `all_empty`）；行数 ＝ 5（尾部 20 行被裁剪）
- 失败判据：行数仍为 25；或第 3 列被删除
- 自证方式：`SELECT COUNT(*), COUNT(第3列) FROM t1`；元数据 `all_empty` 标记；报告中的 `trimmed_rows`

#### 6. 风险与回滚
- 可能回归点：① 尾部空行中夹着"有格式无值"的行（openpyxl 可能读为 None）→ 属预期裁剪；② 中间空行被误裁（须严格只裁尾部）
- 回滚方式：normalizer 新文件可删
- 降级策略：若裁剪引发争议，改为"仅在报告中提示尾部空行数，不实际裁剪"

#### 7. 验收标准
- [ ] 尾部全空行被裁剪且报告记录条数
- [ ] 中间空行保留
- [ ] 全空列保留并带元数据标记

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### REQ-H6 [来源: 需求 H6] 非单元格内容（图片/图表/批注）丢弃并告知

> 规则：H6 ｜ 等级：表级 ｜ **批次：P5** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）
- 目标：normalizer 的 `detect_non_cell_content`
- 调用链：`scan_sheets`（L131-168，read_only 阶段）→ 本处探测 → `REQ-H9` 报告
- 存在性判定：❌ 不存在（全链路无 `_images`／`_charts`／`_comments` 读取）

#### 2. 现状与缺陷判定
```text
现状：pd.read_excel 只取单元格值——图片、图表、批注全部静默丢弃，
     用户在导入后无法知道"哪些内容没进来"。
```
- 缺陷类型：**【缺失实现】**（H6 未实现；丢弃行为本身**符合**需求，但"告知"缺失）
- 阻断后果链：含图表的报表 → 图表/批注静默消失 → 用户以为数据完整 → **表级信息丢失但无告知**（易引发交付争议）

#### 3. 修改方案
**B. 新建型**
- 骨架：
  ```python
  def detect_non_cell_content(ws) -> dict:
      """H6：探测非单元格内容（图片/图表/批注），仅统计用于告知，不予导入。

      Returns: {"images": n, "charts": n, "comments": n}
      """
  ```
- 实现要点：① 在 `scan_sheets` 的只读开簿阶段顺带统计（`ws._images`／`ws._charts`／有批注的单元格数——`[UNVERIFIED]`：openpyxl 只读模式下 `_images`/`_charts` 可用性须实施者实测）；② 统计结果进 `REQ-H9` 报告与阶段 1 提示（不阻断导入）
- **A. 修改型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：**导入行为**（明定丢弃，不得尝试转换图片/图表）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`scan_sheets` 的返回结构（`[{"sheet_name","rows","cols"}]`）——如需扩展须**追加键**而非改结构
- 必须遵循的规约：H6 规则定义（明确丢弃 ＋ 报告中告知用户）

#### 5. 验证
- 用例构造：`含图表.xlsx`——1 个柱状图 ＋ 1 张图片 ＋ 1 个批注
- 期望输出：数据正常导入；报告出现「该数据表含 1 张图表、1 张图片、1 处批注，这些内容不会被导入」
- 失败判据：报告无任何告知；或导入失败
- 自证方式：`REQ-H9` 报告文件内容

#### 6. 风险与回滚
- 可能回归点：只读模式下属性不可用 → 探测抛错（须包 try/except 并降级为"未探测"）
- 回滚方式：normalizer 新文件可删
- 降级策略：探测失败时仅写「未能探测非单元格内容」，**不得**中断导入

#### 7. 验收标准
- [ ] 含图片/图表/批注的表在报告中明确告知，且导入成功
- [ ] 探测失败不影响导入（有 try/except 兜底）
- [ ] 无该内容的表不产生噪音报告

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### REQ-H7 [来源: 需求 H7] 超长数字精度扫描期检测与提示

> 规则：H7 ｜ 等级：单元格级 ｜ **批次：P5** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）／`rpa_engine/ops/excel_preprocessor.py`
- 目标：normalizer 的 `detect_precision_loss`；只读扫描 `scan_sheets`（L131-168）
- 调用链：`scan_sheets`（只读）→ 本处检测 → `REQ-H9` 报告／阶段 1 提示
- 存在性判定：❌ 不存在

#### 2. 现状与缺陷判定
```text
现状：Excel 自身对数字仅保留 15 位有效数字；超过部分的精度在源文件中已丢失，
     但程序不检测、不提示，用户以为"数字是准的"。
```
- 缺陷类型：**【缺失实现】**（H7 未实现）
- 阻断后果链：18 位订单号在 Excel 中已变 `...000` 尾数 → 导入后仍为 15 位精度数字 → 用户拿到的编码与原始系统不一致 → **单元格级交付质量风险但静默**（无法在导入侧修复，只能提示）

#### 3. 修改方案
**B. 新建型**
- 骨架：
  ```python
  def detect_precision_loss(df, meta: dict, threshold_digits: int = 15) -> list:
      """H7：扫描阶段检测超长数字列并提示（源文件精度已丢失，不可修复）。

      Returns: [(列名, 样本值, 位数)] —— 仅提示，不改数据。
      """
  ```
- 实现要点：① 检测数字型值的**整数部分位数 > 15** 或文本型长数字；② 结果进报告与阶段 1 提示（**只提示，不改数据**——源文件已丢失，任何"修复"都是编造）；③ 与 `A-04`（超阈值一律 str）配合：`A-04` 保证 15 位以上**文本**不被转数字，H7 保证**数字型**精度损失被提示
- **A. 修改型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：不得尝试"补零"或"还原"精度（属编造数据）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`NormalizeResult.warnings`
- 必须遵循的规约：H7 规则定义（扫描阶段检测并提示用户）

#### 5. 验证
- 用例构造：`精度.xlsx` 的 `编号` 列为数字 `123456789012345678`（18 位）
- 期望输出：报告出现「`编号` 列存在超长数字（18 位），Excel 已将其精度限制为 15 位有效数字，请核对源数据」
- 失败判据：无任何提示；或程序"补齐"尾数
- 自证方式：`REQ-H9` 报告内容；数据未被修改（与原 Excel 读出的值一致）

#### 6. 风险与回滚
- 可能回归点：误报（如普通小数被算作超长）→ 只对"有效数字位数"判定
- 回滚方式：normalizer 新文件可删
- 降级策略：若检测成本高，降级为"仅对文本型长数字告警"

#### 7. 验收标准
- [ ] ≥16 位的数字列在报告中被提示，且数据未被改写
- [ ] 常规列不产生噪音告警
- [ ] 与 `A-04` 的超阈值 str 规则协同（长数字不因类型转换被吞）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）／`rpa_engine/ops/excel_preprocessor.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### REQ-H9 [来源: 需求 H9／产物 2·3·4] 元数据表 ＋ 规范化处理报告 ＋ 失败清单落盘

> 规则：H9 ｜ 等级：表级 ｜ **批次：P5** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）／`rpa_engine/gui/main_window.py`（失败清单）
- 目标：normalizer 的 `NormalizeResult.meta`／`report_entries`／`warnings` 的**落盘**；`main_window.py` L290-291 的 `failed` 清单落盘
- 调用链：各规范化函数产出记录 → 汇总为 `NormalizeResult` → 本处落盘 → 用户可查阅
- 存在性判定：❌ 不存在（无处理报告、无元数据表、失败清单仅存在于内存 → 弹窗）

#### 2. 现状与缺陷判定
```python
# main_window.py L290-291 与 L356-360（失败清单只存在于内存与弹窗，不落盘）
        registry: List[Dict[str, Any]] = []
        failed: List[str] = []
...
        if failed:
            QMessageBox.warning(
                self, "部分导入失败",
                "以下数据表导入失败：\n" + "\n".join(failed)
            )
```
- 缺陷类型：**【缺失实现】**（H9 未实现；产物 2/3/4 全部缺失）
- 阻断后果链：用户无法查看"哪些格被拆分/哪些值被转 NULL/哪些列被改名/哪些文件未入库" → 交付争议无法追溯 → **表级可追溯性缺失**（问题发生时无法定位，只能重启排查）

#### 3. 修改方案
**B. 新建型**
- 新建位置：`rpa_engine/ops/excel_normalizer.py` 内的报告写出函数
- 骨架：
  ```python
  def write_normalize_report(result: "NormalizeResult", out_dir: str,
                              table_id: str, alias: str) -> dict:
      """H9／产物 3：把规范化过程写入可读报告（JSON＋人读文本）。

      Returns: {"json": path, "text": path}
      """
  def write_meta_table(conn, result: "NormalizeResult", sqlite_table: str,
                       table_id: str) -> int:
      """产物 2：把逐列原始 Excel 类型/公式/超链接/合并拆分标记写入元数据表。

      Returns: 写入行数。
      """
  def write_failed_list(failed: List[Dict[str, str]], out_dir: str) -> str:
      """产物 4：把未能入库的文件/表与原因写成失败清单。

      Returns: 清单文件路径。
      """
  ```
- 实现要点：
  ① 报告目录：`workspace/normalize_report/<会话时间戳>/`；每表一份 JSON ＋ 一份人读 `.txt`（简体中文，禁用词表约束）
  ② 元数据表：在**同一会话库**内建表 `__meta_{sqlite_table}`（或统一表 `__normalize_meta`，含 `table_id`／`column`／`original_type`／`was_formula`／`was_hyperlink`／`was_merged`／`all_empty`）→ 支撑"无损互转"；**须在报告中说明该表仅供追溯，不参与业务**
  ③ 失败清单：`main_window.py` 的 `failed` 列表改为 `List[Dict]`（含 `alias`／`sheet`／`file`／`reason`／`stage`），在导入循环结束后调用 `write_failed_list` 落盘，弹窗仍保留（双通道）
  ④ 报告内容**不得**包含技术词（SQL／表名／SQLite／物理名 → 用"数据表编号/标识名称"表述），遵守 `docs/architecture.md` §8.4
- **A. 修改型**：`main_window.py` 的 `failed` 结构改造（第 ③ 条）
- **C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`_on_confirm_import` 的阶段切换逻辑；弹窗交互（保留）
- 不可引入的新依赖：是（`json`／`pathlib` 标准库）
- 必须保留的接口/信号：`NormalizeResult` 四字段；`failed` 变量名（可改类型）
- 必须遵循的规约：H9；产物 2/3/4；`docs/architecture.md` §8.4 禁用词表；`AGENTS.md` §5.2（内存——报告须流式写，不得全量驻留）

#### 5. 验证
- 用例构造：一次导入 3 张表，其中 1 张必失败（含 `\n` 表头）、1 张含合并格与公式、1 张干净
- 期望输出：`workspace/normalize_report/<ts>/` 下有 3 份 JSON ＋ 3 份人读报告；会话库内有元数据表且行数 ＝ 列数之和；失败清单文件含 1 条（表 + 原因）；弹窗与文件内容一致
- 失败判据：报告目录不存在；元数据表缺失；失败清单为空；报告中出现技术词
- 自证方式：列目录、读 JSON、查会话库 `SELECT COUNT(*) FROM __normalize_meta`

#### 6. 风险与回滚
- 可能回归点：① 报告读写拖慢导入（须流式/异步）；② 元数据表与业务表混放导致误用（须文档说明＋命名前缀 `__`）；③ 禁用词表被报告的"技术细节折叠"破坏
- 回滚方式：normalizer 新文件可删；`main_window.py` 备份
- 降级策略：若落盘影响性能，降级为「仅落盘 JSON（不生成人读文本）」，并在 UI 保留弹窗

#### 7. 验收标准
- [ ] 每次导入后报告目录含 JSON ＋ 人读报告，内容与实际处理一致
- [ ] 会话库内元数据表行数 ＝ 被导入表列数之和
- [ ] 失败清单落盘，与弹窗内容一致
- [ ] 报告文本无技术词（SQL/表名/SQLite/物理名）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）／`rpa_engine/gui/main_window.py`（失败清单）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### REQ-H10 [来源: 需求 H10] `temp/normalized/` 幂等与目录管理

> 规则：H10 ｜ 等级：文件级 ｜ **批次：P5** ｜ 判定：**【缺失实现】**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_normalizer.py`（新建）／`rpa_engine/paths.py`（目录常量）
- 目标：normalizer 的产物落盘与幂等标记；`paths.py` 的目录定义
- 调用链：上游 `normalize_sheet` → 本处（产物落 `temp/normalized/`）；与 `A-01`／`A-11` 的副本生命周期协同
- 存在性判定：❌ 不存在（全库无 `temp/normalized/`；`paths.py` 未定义该目录）

#### 2. 现状与缺陷判定
```text
现状：规范化产物只存在于内存（DataFrame）；无落盘、无幂等标记；
     同一文件在同一会话内重复导入会重复做全部规范化（含双开簿、公式扫描）。
```
- 缺陷类型：**【缺失实现】**（H10 未实现）
- 阻断后果链：重复导入同一文件 → 全流程重跑（大表下显著变慢）→ 且无"已处理"标记可供排查 → **文件级：幂等与可追溯缺失**

#### 3. 修改方案
**B. 新建型 ＋ A. 修改型**
- 改动点 1（修改）：`rpa_engine/paths.py`
  - 改前：无 `normalized` 目录常量
  - 改后：新增 `def get_normalized_dir() -> Path`（返回 `ENGINE_ROOT / "temp" / "normalized"`，并按需 `mkdir(parents=True, exist_ok=True)`）；**须先读 `paths.py` 全文确认既有函数命名与风格** `[UNVERIFIED]`
- 改动点 2（新建）：`ops/excel_normalizer.py`
  - 骨架：
    ```python
    def normalized_cache_key(file_path: str, sheet_name: str, header_row: int,
                             rules_version: str) -> str:
        """H10：规范化产物的幂等键（文件指纹 + sheet + 表头行 + 规则版本）。"""

    def load_normalized_cache(key: str) -> "Optional[NormalizeResult]":
        """H10：命中缓存则直接返回结果；未命中返回 None。"""
    ```
  - 实现要点：① 产物用 `pickle`？**禁止**（§0.2 条 1 禁 `pickle`）→ 改用 `json` ＋ `parquet`／`csv`？`parquet` 需 `pyarrow`（**新依赖，禁**）→ 故改为「**缓存元数据用 JSON，DataFrame 不落盘**」：即缓存仅记录"该 (文件指纹+sheet+表头行+规则版本) 已处理过"及其 `meta`/`warnings`，**数据本身仍每次重新读取**（避免引入新依赖与磁盘膨胀）
    - 说明：这是在不引入新依赖前提下符合 H10 的最小实现；若人工希望连数据一起缓存，须另行裁定（列入 Part 6 待裁定）
  ② 规则版本：定义常量 `NORMALIZE_RULES_VERSION = "v1"`，规则变更时递增（保证旧缓存失效）
  ③ 会话内幂等：同一会话内重复导入同一 sheet 时命中缓存 → 跳过重复的公式/超链接扫描（但**仍读取数据**），并在报告标注"命中缓存"
- **C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`paths.py` 既有函数；不得引入 `pyarrow`／`pickle`
- 不可引入的新依赖：**是**（本项实现即受此约束而降级）
- 必须保留的接口/信号：`paths.py` 既有 API 不变（仅新增）
- 必须遵循的规约：H10（产物落 `temp/normalized/`、同会话重复执行不重复处理、任一表失败不影响其他表）；`AGENTS.md` §2.1 条 5（磁盘与内存）

#### 5. 验证
- 用例构造：同一 `样本A.xlsx` 的同一 sheet，在同一会话内导入两次（返回阶段 1 再导入一次）
- 期望输出：第二次命中缓存 → 报告标注"命中缓存" → 总耗时下降；数据结果与第一次一致
- 失败判据：第二次仍全量重跑且无缓存标记；或结果与第一次不一致
- 自证方式：`temp/normalized/` 下的缓存文件；报告的"命中缓存"条目；两次耗时对比

#### 6. 风险与回滚
- 可能回归点：① 缓存陈旧（文件内容变了但指纹未变）→ 指纹须含 `size + mtime + 路径`；② `temp/normalized/` 被 `A-11` 的超龄清理误删 → 该目录**不在** `input_selection` 下，故不受其清理影响（须核实 `cleanup_stale_files` 的入参 L711-713）
- 回滚方式：删 `temp/normalized/` 即可（无副作用）；`paths.py` 回退新增函数
- 降级策略：若缓存引发不一致，直接关闭缓存（`NORMALIZE_CACHE_ENABLED=False`），H10 记为"仅目录管理已落地"

#### 7. 验收标准
- [ ] 同会话重复导入命中缓存并在报告中标注
- [ ] 缓存键含文件指纹与规则版本；文件变更或规则升级后缓存失效
- [ ] 未引入任何新依赖（无 `pyarrow`／`pickle`）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_normalizer.py`（新建）／`rpa_engine/paths.py`（目录常量）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

## Part 3 · B 类问题处理方案（79 项）

> **B 类分类台账（2026-10-18 由 `Agent-B3.1`／`B3.2`／`B3.34` 三个只读分类 Sub-Agent 逐条判定，Coordinator 单点汇入）**
>
> **分类口径**（唯一判据来源＝本文件 §0.1 红线原文，**未自造新红线**）：
> - **`[ACTION]`** —— 不触碰 §0.1 四项红线（① `engine/executor.py` 的步骤分发/信号定义/线程模型；② GUI 布局；③ `ops/` 9 项 BUILTIN_OPS 行为；④ 新依赖／`eval`/`exec`/`pickle`／硬编码绝对路径）
> - **`[BLOCKED-真机依赖]`** —— 其**验证**须真机会话（Qt 控件/运行期线程/退出码/竞态），Agent 无真机环境 ⇒ **移出施工清单**，原文保留
> - **`[BLOCKED-越界]`** —— 需碰上述红线 ⇒ **移出施工清单**，原文保留
> - **`[已覆盖]`** —— 已由已完成的 A 链闭合（或与 A 链同一改动点）⇒ 不重复施工
> - **`不齐`** —— 该条缺"修改位置／修改逻辑／预期结果"三要素之一（[ACTION] 者见下方《方案补全建议》）
>
> **口径裁定（2026-10-19，交叉复核后统一；消解台账原有自相矛盾）**：
> - **①** `ops/` 内**守卫型／写盘实现型**变更（新增 `raise` 守卫、改 `export_table` 写盘、改返回值消费等）**一律计入 §0.1 ③**——因 §0.1 ③ 的字面是「9 项 BUILTIN_OPS **行为**」，守卫与写盘**改变该 op 的可观测行为**。据此：**B-03／B-04／B-09** 由 `[ACTION]` 移入 `[BLOCKED-越界]`；**B-12** 归 `[已覆盖]` 并记 ③ 根因；**B-25** 维持 `[BLOCKED-越界]`（统一后不再矛盾）。
> - **②** `[已覆盖]` 的**唯一口径** ＝「已由**已完成的 A 链**闭合」。据此 **B-44 的"已覆盖＝是"作废**（B-18 非 A 链，且实测 `L299` 仍丢弃返回值）→ 改"否"。
> - **③** `B-49` 同时**命中 ③ 与人工"本轮不施工"** ⇒ 双标 `[BLOCKED-越界＋本轮不施工]`（人工裁定优先，越界属性如实保留）。
> - **施工盘子**（术语统一）＝「`[ACTION]` 且非 `[已覆盖]` 且非 `[BLOCKED-本轮不施工]`，且属 P0/P1」。—— 本轮 ＝ **13 项**（名单见 Part 0 §0.0 与本节合计段）。
>
> **本轮口径（人工裁定）**：① **零删除**——真机/越界项**只标注、不删原文**（合 `AGENTS.md` §7.1）；② 范围**仅 Part 3**；③ **零代码改动**。

| 条目 | 原编号 | 分类 | 判据（引 §0.1 第X条／须真机／3.4 原文理由） | 真机 | 越界点 | 已覆盖 | 三要素 |
|---|---|---|---|---|---|---|---|
| B-01 | F-02 | `[ACTION]` | 均不涉（日志容错） | 否 | — | — | 齐 |
| B-02 | F-03 | `[ACTION]` | 均不涉（清理守卫＋PID 命名；psutil 已在册） | 否 | — | — | 齐 |
| B-03 | F-05 | `[BLOCKED-越界]` | ③（`ops/exporter.py::export_table` 的 `Workbook()`→`write_only=True` 属 BUILTIN_OP `export` 行为，从严计 ③）；**实测 L163 仍为普通 `Workbook()` ⇒ N10 未落地、"与 N10 重叠"不成立** | 否 | ③ | **否（实测未落地）** | 齐 |
| B-04 | F-06 | `[BLOCKED-越界]` | ③（`ops/mapping_matcher.py::match_tables` 入口新增 `raise ValueError` 守卫 ⇒ 改变该 op 可观测行为，从严计 ③；与 B-25 同性质、口径统一） | 否 | ③ | — | 齐 |
| B-05 | F-07 | `[BLOCKED-真机依赖＋越界]` | ③（8 个 ops 追加 `cancel_check`＝行为变更）＋②（终止按钮置灰/tooltip）；断言须真机 | **是** | ③＋② | — | 齐 |
| B-06 | G-04 | `[BLOCKED-真机依赖＋越界]` | ①（QThread parent 绑定／`wait` 消费／统一 `_shutdown`）；退出码须真机 | **是** | ① | — | 齐 |
| B-07 | G-05 | `[BLOCKED-真机依赖＋越界]` | ①（运行中 QThread 重入守卫 `isRunning()`）；时序须真机 | **是** | ① | — | 齐 |
| B-08 | G-11 | `[BLOCKED-真机依赖＋越界]` | ①（`worker.run` finally 包 `conn.close` 保信号可达）；abort 须真机 | **是** | ① | — | 齐 |
| B-09 | H-02 | `[BLOCKED-越界]` | ③（`ops/exporter.py::export_table` 的 `wb.save` → tmp＋`os.replace` 原子写＝BUILTIN_OP `export` 写盘实现变更，从严计 ③） | 否 | ③ | — | 齐 |
| B-10 | H-04b | `[BLOCKED-真机依赖＋越界]` | ①（收尾序列含线程；`closeEvent`/`exit_app` 统一）；须真机 | **是** | ① | — | 齐 |
| B-11 | H-25 | `[BLOCKED-真机依赖＋越界]` | ①（信号：陈旧 `finished` 隔离＋`worker.wait`）；竞态须真机 | **是** | ① | — | 齐 |
| B-12 | J-06（＋G-07） | `[已覆盖]` | ③（四个 BUILTIN_OP 模块新增"覆盖非空活表"守卫＋`dst∈源表`报错，从严计 ③）；**A-15 `guard_overwrite_target` 已接线四处＋`merge_tables` ⇒ 本轮不重复施工** | 否 | ③（从严） | **是** | 齐 |
| B-13 | B5 | `[ACTION]` | 均不涉（自检/访问器/测试口径自洽） | 否 | — | — | 齐 |
| B-14 | F-04 | `[ACTION]` | 均不涉（`forms.py` 解析逻辑＋`sql_safety` 补**中文报错**） | 否 | — | — | 齐 |
| B-15 | G-01 | `[ACTION]` | 均不涉（新增步骤插入点／按 `step_id` 回写＝GUI 逻辑） | 部分 | — | — | **不齐** |
| B-16 | G-02 | `[ACTION]` | 均不涉（提示/空态/画布 refresh＝GUI 逻辑非布局） | 部分 | — | — | 齐 |
| B-17 | G-03 | `[BLOCKED-真机依赖]` | 须真机（自证＝"UI 回填值"） | **是** | — | — | 齐 |
| B-18 | G-08 | `[BLOCKED-越界]` | ③（`step_executor` 返回值消费＋`table_schema::rename_columns` 行为） | 否 | ③ | — | 齐 |
| B-19 | G-09 | `[BLOCKED-越界]` | ③（`convert_dtype` 行为语义） | 否 | ③ | — | 齐 |
| B-20 | G-10 | `[BLOCKED-越界]` | ①（executor 步骤循环＋status 值域/信号＋清理条件） | 否 | ① | — | 齐 |
| B-21 | G-13 | `[ACTION]` | 均不涉（`graph_edges` dangling 判定＋状态访问器） | 否 | — | — | 齐 |
| B-22 | G-14 | `[BLOCKED-真机依赖]` | 须真机（自证＝"画布节点计数"） | **是** | — | — | 齐 |
| B-23 | H-03 | `[BLOCKED-真机依赖]` | 须真机（自证＝UI 断言＋确认框） | **是** | — | — | 齐 |
| B-24 | H-07 | `[BLOCKED-越界]` | ③（`mapping_matcher` full_join SQL 语义改写） | 否 | ③ | — | 齐 |
| B-25 | H-08 | `[BLOCKED-越界]` | ③（`merge_tables` 入口新增守卫） | 否 | ③ | 部分（A-15 已落地该函数，但"重复参与"未覆盖） | 齐 |
| B-26 | H-11 | `[BLOCKED-越界]` | ①（executor 重试分支） | 否 | ① | — | 齐 |
| B-27 | H-13 | `[BLOCKED-真机依赖]` | 须真机（自证＝UI 回填显示） | **是** | — | — | 齐 |
| B-28 | H-14 | `[ACTION]` | 均不涉（`forms::format_conditions` 回填渲染） | 否 | — | — | 齐 |
| B-29 | H-17 | `[BLOCKED-真机依赖]` | 须真机（自证＝报告页与磁盘对比） | **是** | — | 部分（依赖 B-20） | 齐 |
| B-30 | H-19 | `[BLOCKED-真机依赖]` | 须真机（自证含 UI 错误提示） | **是** | — | 部分（与 B-42 合并立项） | 齐 |
| B-31 | H-20 | `[ACTION]` | 均不涉（`_undo_last` 逻辑；撤销栈机制不动） | 部分 | — | — | 齐 |
| B-32 | H-22 | `[BLOCKED-真机依赖]` | 须真机（自证＝UI 文本） | **是** | — | 部分（与 A-13/A-14 同域，断点不同） | 齐 |
| B-33 | H-23 | `[ACTION]` | 均不涉（`table_importer`＝Layer 1；`ensure_input_tables` 非分发/信号/线程，A-16 已放行） | 否 | — | 部分（与 B-05/B-35 同批） | 齐 |
| B-34 | J-02 | `[BLOCKED-越界]` | ③（`exporter` 步骤函数内新增逐格检查＋报告） | 否 | ③ | 部分（同文件与 B-03/**B-49 实测未覆盖**） | 齐 |
| B-35 | J-04 | `[BLOCKED-越界]` | ①（executor 步骤循环内异常/取消判定＋status） | 否 | ① | — | 齐 |
| B-36 | J-05 | `[BLOCKED-越界]` | ①（executor 清理段＋返回结构） | 否 | ① | 部分 | 齐 |
| B-37 | J-07 | `[BLOCKED-越界]` | ③（派生命名）＋①（注册冲突） | 否 | ③＋① | 部分（自动名改形未覆盖） | 齐 |
| B-38 | J-08 | `[BLOCKED-越界]` | ③（`STEP_CATALOG` 产出声明口径） | 否 | ③ | — | 齐 |
| B-39 | J-09 | `[ACTION]` | 均不涉（`engine/parser.py` 版本门禁） | 否 | — | — | 齐 |
| B-40 | DM-24 | `[BLOCKED-真机依赖]` | 须真机（原文自标"暂缓/待 A-17 真机跑通后裁定"） | **是** | 潜在③ | — | **不齐** |
| B-41 | B9 | `[BLOCKED-越界]` | ③（`step_executor` 各分支回退值＝执行行为语义） | 否 | ③ | — | 齐 |
| B-42 | P1-1 | `[ACTION]` | 均不涉（新建 `tests/test_ops_contracts.py`） | 否 | — | 部分（与 B-30 合并） | 齐 |
| B-43 | P1-2 | `[ACTION]` | 均不涉（新建 `tests/test_engine_failure_paths.py`） | 否 | — | 部分（对应 B-05/B-20/B-26/B-33/B-35/B-36） | 齐 |
| B-44 | P1-6 | `[BLOCKED-越界]` | ③（`step_executor` L299 返回值消费；原文自述"见 B-18"） | 否 | ③ | **否（与 B-18 同一改动点；实测 L299 仍丢弃返回值 → 未覆盖）** | 齐 |
| B-45 | F-10 | `[BLOCKED-真机依赖]` | 须真机（完成判定＝各跑一次 `build.bat` 构建，属 P-2 域） | **是** | — | — | 齐 |
| B-46 | F-11 | `[BLOCKED-真机依赖＋越界]` | ①（`executor.progress_callback` 契约＋`worker.progress` 信号分支；原文自述"属引擎调度域"） | **是** | ① | — | 齐 |
| B-47 | G-12 | `[ACTION]` | 3.3/3.4 原文理由"属模板管理域（非导入链路）"；原子替换写法不触红线 | 否 | — | — | 齐 |
| B-48 | H-12 | `[ACTION]` | 原文理由"裁定维持按字面匹配，通配符开关不在本轮"；`sql_safety` 非 9 项 BUILTIN_OPS | 否 | — | — | 齐 |
| B-49 | H-26 | `[BLOCKED-越界＋本轮不施工]` | **人工裁定本轮不施工**（体验优化、非功能阻断；建议后续单独立项）｜③（`ops/exporter.py::export_table` 后缀处理属 BUILTIN_OP `export`）｜**实测 `exporter.py` L143-144 仍 `with_suffix(".xlsx")` 静默改写 → 未覆盖** | 否 | ③ | **否（实测未覆盖）** | 齐 |
| B-50 | B-02 | `[ACTION]` | 原文理由"属环境/交付域；裁定 Q1 定方案 C（裸 `pip freeze`）须人工执行" | 否 | — | — | **不齐** |
| B-51 | G-5（台账） | `[已覆盖]` | 本项＝`A-15`/`A-16` 的**方案前置**；P4 已落地两式 → 缺口已闭合 | 否 | — | **是** | **不齐** |
| B-52 | G-7（台账） | `[ACTION]` | 原文理由"裁定 Q2 同 B-51（先出方案再裁定）；A-17 可用人工核对替代" | 否 | — | — | **不齐** |
| B-53 | D4 | `[ACTION]` | 原文理由"裁定 Q3 定为 W-22 第一批，须人工逐项立项"；`engine/validator.py` 不属① | 否 | — | — | **不齐** |
| B-54 | B1 | `[ACTION]` | 原文理由"属功能函数记录表域" | 否 | — | — | **不齐** |
| B-55 | B2 | `[ACTION]` | 同 B-54 | 否 | — | — | **不齐** |
| B-56 | B3 | `[ACTION]` | 同 B-54 | 否 | — | — | **不齐** |
| B-57 | B4 | `[BLOCKED-越界]` | 原文理由"同 B-54；**且本次不改 GUI 布局与表单结构**"→ literal 命中 §0.1 ② | 否 | ② | — | **不齐** |
| B-58 | B6 | `[ACTION]` | 同 B-54 | 否 | — | — | **不齐** |
| B-59 | B7 | `[ACTION]` | 原文理由"涉及 `step_executor` 白名单（非 9 分支行为、非红线）" | 否 | — | — | **不齐** |
| B-60 | B8 | `[ACTION]`（谓词贴近②，从严可改判越界） | 原文理由"属前端键域"；交付物＝常量声明 | 否 | — | — | **不齐** |
| B-61 | C1 | `[ACTION]` | 原文理由"纯记录表缺口，无功能影响" | 否 | — | — | **不齐** |
| B-62 | C2 | `[ACTION]` | 同 B-61 | 否 | — | — | **不齐** |
| B-63 | D1 | `[ACTION]` | 原文理由"记录表结构变更须走专章 §5.5 登记清单（13 项）" | 否 | — | — | **不齐** |
| B-64 | D2 | `[ACTION]` | 同 B-63 | 否 | — | — | **不齐** |
| B-65 | D3 | `[ACTION]` | 同 B-63（落地后与 B-20/B-21 关联，须协调） | 否 | — | — | **不齐** |
| B-66 | E1 | `[ACTION]` | 原文理由"属守卫测试域；B-42/B-43 已补单测，守卫镜像另批" | 否 | — | — | **不齐** |
| B-67 | E3 | `[ACTION]` | 原文理由"本次不新增/删除功能函数，无口径漂移风险" | 否 | — | — | **不齐** |
| B-68 | A4 | `[ACTION]` | 同 B-67 | 否 | — | — | **不齐** |
| B-69 | P2-1 | `[ACTION]` | 原文理由"B-41 已覆盖其核心后果"；**但 B-41 属未施工 → 核心后果实未闭合** | 否 | — | — | **不齐** |
| B-70 | P2-2 | `[ACTION]` | 原文缺陷类型"**【已裁定不触红线】**（裁定 P2-2）" | 否 | — | — | **不齐** |
| B-71 | N-01 | `[ACTION]` | 原文理由"属依赖锁定域（B-50）"；④"引入新依赖"≠记录既有依赖 | 否 | — | — | **不齐** |
| B-72 | N-02 | `[ACTION]` | 原文理由"裁定不卸载（避免影响其他工具），仅 lock 注明" | 否 | — | — | **不齐** |
| B-73 | N-03 | `[ACTION]` | 原文理由"属文档/命令口径" | 否 | — | — | **不齐** |
| B-74 | N-04 | `[ACTION]` | 原文理由"属依赖域；本次不引入新依赖，无升级动作" | 否 | — | — | **不齐** |
| B-75 | N-05 | `[已覆盖]` | 本项＝`A-17` 的**环境侧证据**；P0 已落地（spec ＋ `xlrd>=2.0`） | 否 | — | **是** | **不齐** |
| B-76 | §8.2-1 | `[ACTION]` | 原文理由"注释更正随 B-03 改动点 4"；**B-03 未施工 → 注释未改（实测 `exporter.py` L10 仍是旧文）** | 否 | — | — | **不齐** |
| B-77 | §8.2-2 | `[已覆盖]` | 原文"随 A-15 同步更正"；**实测 `sqlite_manager.py` 注释已更正** | 否 | — | **是** | **不齐** |
| B-78 | §8.2-3 | `[已覆盖]` | 原文"随 A-15 同步更正"；**实测 `sqlite_manager.py` docstring 已更正** | 否 | — | **是** | **不齐** |
| B-79 | §8.2-4 | `[ACTION]` | 原文理由"`A-05` 落地后再改（避改两次）"；`A-05` 已落地但文案未改 → 未覆盖；改文案非布局 | 否 | — | **否（实测未覆盖）** | **不齐** |

**分类合计（恒等式，6 项，2026-10-19 复核后重算）**：`[ACTION]` **40** ｜ `[BLOCKED-真机依赖]` **9** ｜ `[BLOCKED-越界]` **17** ｜ 兼有 **7** ｜ `[已覆盖]` **5** ｜ `[BLOCKED-本轮不施工]` **1**（B-49）⇒ 逐项相加 ＝ **79** ✓
**本轮可施工 ＝ 13 项**（＝ `[ACTION]` 40 **减去** 27 项 P2/P3"本轮不施工"，且不含已覆盖）：`B-01`／`B-02`／`B-13`／`B-14`／`B-15`／`B-16`／`B-21`／`B-28`／`B-31`／`B-33`／`B-39`／`B-42`／`B-43`；其余 **66 项**（真机 9 ＋ 越界 17 ＋ 兼有 7 ＋ 已覆盖 5 ＋ 不施工 1 ＋ P2/P3 的 ACTION 27）**移出施工清单但原文保留**。

### 《R15 处置表》（2026-10-19 追加 · 等价于台账「本批处置」列；台账原文一字未改）

> **授权依据**：人工批准方案 `.trae/documents/backlog-remediation-control-pack.md`（R15 控制包施工轮）。办结明细见 `docs/task-records/2026-10-19-w22-n-remediation.md`。

| 条目 | R15 处置 | 责任方／触发 |
|---|---|---|
| B-45 | 受控例外（`build.bat` 属构建域，Agent 不碰） | 人工／下次真机构建窗口 |
| B-46 | 受控例外（红线① `executor` 回调 ＋ 须真机） | 人工／真机批立项 |
| B-47 | 施工：模板保存改「临时文件 ＋ `os.replace`」原子替换（复用 B-09 写法）＋ 残留 `~*.tmp` 启动清理 | Agent／本批 |
| B-48 | **已裁定关闭**（有意设计，维持「按字面匹配」；通配符开关不在范围） | — |
| B-49 | 施工：后缀非 `.xlsx` 改抛中文 `ValueError`（不再静默改写） | Agent／本批 |
| B-50 | 施工：生成 `requirements.lock`（`pip freeze` 原样写入） | Agent／本批 |
| B-51 | **结账关闭（已覆盖）**：A-15＋A-16 已落地两式 | — |
| B-52 | 施工：新增「依赖↔代码↔打包」交叉校验单测 | Agent／本批 |
| B-53 | 施工：`BUILTIN_OPS` 增 `deprecated`＋`validator` 拒绝已弃用 type（闭合 D4） | Agent／本批 |
| B-54 | 施工：单测断言 `description` ≡ `display`（守卫 B1） | Agent／本批 |
| B-55 | 施工：`STEP_KIND` 值域校验（守卫 B2） | Agent／本批 |
| B-56 | 施工：`OUTPUT_OPS` ≡ `fork∪merge` 单测（守卫 B3） | Agent／本批 |
| B-57 | 施工：目录键↔表单类双向断言（守卫 B4） | Agent／本批 |
| B-58 | 施工：自检扩 `keywords` 非空判定（守卫 B6） | Agent／本批 |
| B-59 | 施工：`param_keys` ⊇ schema 键单测（守卫 B7） | Agent／本批 |
| B-60 | 施工：`output_mode` 常量集中声明（守卫 B8） | Agent／本批 |
| B-61 | 施工：**删除** `StepMeta.icon`（零消费者） | Agent／本批 |
| B-62 | 施工：**删除** `target_param`／`match_param`（零消费者；启用撞 P2-2 裁定） | Agent／本批 |
| B-63 | 施工：新增 `extra_input_min`（D1） | Agent／本批 |
| B-64 | 施工：新增 `params_schema` 为唯一源（D2） | Agent／本批 |
| B-65 | 施工：新增 `overwritable`，表单挂载由其驱动（D3） | Agent／本批 |
| B-66 | 施工：补齐自检规则单测镜像（E1） | Agent／本批 |
| B-67 | 施工：四处「9」断言改引用单一常量（E3） | Agent／本批 |
| B-68 | 施工：非门禁「9 项」文案统一引用常量（A4） | Agent／本批 |
| B-69 | 施工：`default_params` 派生于 `params_schema`（P2-1） | Agent／本批 |
| B-70 | **已裁定关闭（维持）**：不改 9 分支结构 | — |
| B-71 | 施工：lock 必含 pandas（不手工删） | Agent／本批 |
| B-72 | 施工：lock 头部注明「含 2 个已声明废弃包，勿安装」 | Agent／本批 |
| B-73 | 施工：命令清单统一 `CPS-GPES_RPA-py311`（下划线） | Agent／本批 |
| B-74 | 施工：`pandas` 加上界＋回写实测版本 | Agent／本批 |
| B-75 | **结账关闭（已覆盖）**：A-17 已补 `xlrd>=2.0`＋spec | — |
| B-76 | 施工：随 B-03 更正 `exporter.py` L9-11 注释 | Agent／本批 |
| B-77 | **结账关闭（已覆盖）**：A-15 已更正注释 | — |
| B-78 | **结账关闭（已覆盖）**：A-15 已更正 docstring | — |
| B-79 | 施工：预览摘要文案按 A-05 真实口径更新（仅文案） | Agent／本批 |
| **B-41**（原编号 B9，属 B-01~B-44） | 施工：引擎回退对齐单源（`mode`→`left_join`；`from_type/to_type`→`TEXT`/`INTEGER`） | Agent／本批 |
| **B-03**（原编号 F-05，属 B-01~B-44） | 施工：`export_table` 改 `write_only=True`＋`WriteOnlyCell`（降级预案见控制包 §五 条 4） | Agent／本批 |
| **B-18／B-44／B-25／B-24／B-19／B-37／B-38／B-34**（红线③ 其余） | 受控例外（op 语义/写盘/派生命名，需逐项立项） | 人工／后续批 |
| **B-05~B-11／B-17／B-20／B-22／B-23／B-26／B-27／B-29／B-30／B-32／B-35／B-36／B-40**（红线①＋真机） | 受控例外（`executor` 运行域／须真机断言） | 人工／真机批立项 |


### 《方案补全建议》（仅 `[ACTION]` 且"三要素不齐"者；由分类 Sub-Agent 逐条给出）

> 落点待补的补"修改位置"，判据缺的补"预期结果"。**本轮仅登记建议，不写入条目正文**（零代码、零正文改动）。

| 条目 | 缺 | 一句话补全建议 |
|---|---|---|
| B-15 | 位置 | 补读该类后回填"新增步骤插入点"与"收拢回写"的**函数名＋精确行号**（§0.7 待清项） |
| B-50 | 逻辑＋判据 | `conda run -n CPS-GPES_RPA-py311 pip freeze > requirements.lock`；判据＝lock 行数>0 且头部注明 2 废弃包 |
| B-52 | 位置＋判据 | 落点建议 `gui/app.py` 自检项或新单测；判据＝每个 import 模块都在 requirements 与 spec hiddenimports 内 |
| B-53 | 判据 | `engine/validator.py` 对已弃用 type 直接报错，且用例覆盖 |
| B-54 | 位置＋判据 | 落点＝单测文件；判据＝`BUILTIN_OPS[k].description` ≡ `StepMeta[k].display` |
| B-55 | 判据 | 非法 `STEP_KIND` 值不再静默回退，报错＋单测覆盖 |
| B-56 | 位置＋判据 | 定落点；判据＝`OUTPUT_OPS` ≡ `STEP_KIND(fork∪merge)` 单测通过 |
| B-58 | 位置＋判据 | 定自检项位置；判据＝`keywords` 空 tuple 被判失败 |
| B-59 | 判据 | 白名单 ⊇ 目录 `param_keys`，单测通过 |
| B-60 | 位置＋判据 | 常量落点建议 `gui/models.py`；判据＝4 处引用同一常量 |
| B-61 | 判据 | `StepMeta.icon` 非空且被消费，或删除并补单测 |
| B-62 | 判据 | `target_param`/`match_param` 启用或被删 |
| B-63 | 判据 | 记录表含 `inputs.extra_min`，且专章 §5.5 登记清单更新 |
| B-64 | 判据 | `params_schema` 存在且被校验消费 |
| B-65 | 判据 | `_OVERWRITABLE` 落地并与 B-20/B-21 口径一致 |
| B-66 | 判据 | 自检 15 条规则各有对应单测镜像 |
| B-67 | 判据 | 3 处"9"断言改为引用常量，功能增删时自动同步 |
| B-68 | 判据 | 10+ 处文案统一引用常量 |
| B-69 | 判据 | `default_params` 由目录自动派生且与 B-41 取值一致 |
| B-70 | 逻辑＋判据 | 明确为"人工裁定后重构"，补裁定后的可判定动作与判据 |
| B-71 | 判据 | 生成的 lock 含 pandas 且安装可复现 |
| B-72 | 判据 | lock 头部含废弃包告警文本 |
| B-73 | 判据 | 命令清单全部用 `CPS-GPES_RPA-py311`（下划线，零连字符） |
| B-74 | 判据 | pandas 带上界＋实测版本回写 |
| B-76 | 判据 | `exporter.py` L9-11 注释与新行为一致（随 B-03） |
| B-79 | 判据 | 预览摘要文案与 A-05 落地后的真实填充口径一致 |
| B-40 | 全部 | 属"暂缓/待 A-17 真机裁定"，**不在本轮补全范围**（且已被判 BLOCKED-真机依赖） |

---

> **说明**：B 类＝不在预处理范围、但不解决则程序无法启动／无法完成／无法验证的问题。
> **深度**：`B-01`~`B-44`（P0 13 ＋ P1 31）＝完整七段式；`B-45`~`B-79`（P2 5 ＋ P3 30）＝精简四段（存在性判定／缺陷类型／为何本次不施工／触发条件）。
> **批次**：与 A 类无依赖者可随时并行；但多数 B 类项**须待 P0 解锁后才具备可验证性**（见 Part 1 §1.1）。

### 3.1 P0 阻塞运行（13 项，七段式）

> **本组提示（2026-10-19）**：含真机依赖项与越界项者**已在台账标注并移出施工清单**（原文保留）；**本轮可施工项以 Part 3 头部台账为准**；`§0.3` 的 `P-2`（exe 重建＋真机 `.xls` 验证）为**活前置，不动**。

---

### B-01 [原编号: F-02] 只读目录启动静默失败

> 等级：P0（无法启动） ｜ **批次：B 类（可并行）** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/gui/app.py`
- 目标：`_setup_gui_logging`（L246-256）／`launch_gui`（L269-277 起）
- 调用链：上游 `main.py` → `launch_gui()` L277 `_setup_gui_logging()` → 下游 L278 `run_self_check()`
- 存在性判定：✅ 已存在（缺 try）

#### 2. 现状与缺陷判定
```python
# app.py L246-256（mkdir 裸调用，无 try）
def _setup_gui_logging() -> None:
    log_dir = ENGINE_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(log_dir / "gui_{time:YYYY-MM-DD}.log", level="DEBUG", ...)
# app.py L277-278（日志初始化早于自检）
    _setup_gui_logging()
    result = run_self_check()
```
- 缺陷类型：**【缺少容错】**（日志初始化早于自检，且无 try；`spec` 为 `console=False` → 异常无处输出）
- 阻断后果链：程序装在只读目录 → L249 `mkdir` 抛 `PermissionError`/`OSError` → 在 L278 自检之前逃逸 → 无 GUI 可弹（`QApplication` 尚未构造）→ 文员双击"什么都没发生" → **P0：无法启动**（自检第 3 项的人话提示永远到不了）

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`gui/app.py::_setup_gui_logging` L249
  - 改前：`log_dir.mkdir(parents=True, exist_ok=True)`
  - 改后：包 try/except，失败则回退到**用户可写的临时目录**并记录（例如 `Path(tempfile.gettempdir()) / "RPA_Workflow_v3_logs"`；文件头补 `import tempfile`）
- 改动点 2：同函数 L250-256 的 `logger.add`
  - 改前：直接以 `log_dir` 为目标
  - 改后：以「解析后的可用目录」为目标；两处失败都不抛
- 改动点 3：`launch_gui` L277-278 顺序
  - 改前：日志 → 自检
  - 改后：**自检结果先取**，日志初始化包在 try 内；若日志目录不可写，则自检项中直接体现"程序所在目录不可写"的人话（配合 `A-14` 的钩子）
- **B. 新建型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`launch_gui` 的返回值语义（进程退出码）；`spec` 的 `console=False`
- 不可引入的新依赖：是（`tempfile` 标准库）
- 必须保留的接口/信号：`_setup_gui_logging() -> None`；`launch_gui() -> int`
- 必须遵循的规约：`AGENTS.md` §2.1 条 6；`docs/deployment-guide.md`（便携版"必须可写目录"约定）

#### 5. 验证
- 用例构造：把程序复制到只读目录（或用只读账户）启动
- 期望输出：程序启动并给出人话提示（"程序所在目录不可写，请换到可写目录"）；日志落到临时目录
- 失败判据：双击无任何反应；或进程静默退出无提示
- 自证方式：在只读目录下运行并观察是否有弹窗/日志；检查临时目录下日志文件生成

#### 6. 风险与回滚
- 可能回归点：① 日志目录改变导致既有排障习惯（`logs/gui_*.log`）失效 → 须在提示中说明新位置；② `tempfile` 目录在清理策略下被删
- 回滚方式：`app.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：无法弹窗时（`QApplication` 未构造）至少 `print(..., file=sys.stderr)`（exe 态不可见但源码态可诊断）

#### 7. 验收标准
- [ ] 只读目录启动不再"静默无反应"，给出中文提示
- [ ] 正常目录启动行为不变（日志仍在 `logs/`）
- [ ] 启动自检 6 项在全绿环境仍通过

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/app.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-02 [原编号: F-03] 双开无条件删掉运行中实例的会话库

> 等级：P0（不可逆数据损失） ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/gui/main_window.py`
- 目标：`MainWindow.cleanup_stale_files`（L679-707，会话库删除在 L688-694）／`_cleanup_stale_sessions`（L709-713）；`ops/session_db.py::SessionDB.__init__`（L37-59）
- 调用链：启动 → `_cleanup_stale_sessions()` L236 → 本处 L688 `glob("session_*.db*")` → `p.unlink()`
- 存在性判定：✅ 已存在（无进程存活判定）

#### 2. 现状与缺陷判定
```python
# main_window.py L687-694（无进程判定，直接 unlink）
        if ws_root.is_dir():
            for p in ws_root.glob("session_*.db*"):
                try:
                    p.unlink()
                    removed += 1
# session_db.py L56-59（库名不含 PID）
        self.db_path = str(
            (db_dir_path if db_dir_path.is_absolute() else engine_root / db_dir_path)
            / f"{session_id}.db"
        )
```
- 缺陷类型：**【逻辑错误】**（假设"启动时无运行中会话"，且库名不含 PID → 无法区分实例）
- 阻断后果链：实例 A 正在使用 `workspace/session_*.db` → 实例 B 启动 → L690 `p.unlink()` 无条件删除 → 实例 A 已导入的全部数据表丢失（Excel 原件不受影响）→ **P0：不可逆数据损失**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`gui/main_window.py::_on_confirm_import` L259-261（会话库命名）
  - 改前：`session_id = datetime.now().strftime("%Y%m%d_%H%M%S")` ＋ `SessionDB(f"session_{session_id}")`
  - 改后：`session_id = f"{datetime.now():%Y%m%d_%H%M%S}_{os.getpid()}"`（**库名带 PID**；文件头补 `import os`）
- 改动点 2：`gui/main_window.py::cleanup_stale_files` L688-694
  - 改前：`for p in ws_root.glob("session_*.db*"): p.unlink()`
  - 改后：
    ```python
    import psutil
    for p in ws_root.glob("session_*.db*"):
        if not _is_stale_session(p):      # 见改动点 3
            continue
        try:
            p.unlink(); removed += 1
        except OSError as e:
            logger.warning(...)
    ```
- 改动点 3：新增模块级辅助函数 `_is_stale_session(p: Path) -> bool`
  - 实现要点：从文件名解析 PID（格式 `session_<ts>_<pid>.db*`）→ `psutil.pid_exists(pid)` → 存在则**不删**；解析失败（旧格式文件）保守处理＝**不删**并记 warning；`psutil` 已在依赖清单
- 改动点 4：`ops/session_db.py::close` L121-131
  - 说明：本项不改（仍按 `keep_db` 决定）；但须保证新增的 `-wal`/`-shm` 后缀匹配不遗漏（`glob("session_*.db*")` 已覆盖）
- **B. 新建型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`SessionDB` 的构造签名（`session_id` 仍为字符串）；`close(keep_db)` 语义
- 不可引入的新依赖：是（`psutil` 已在清单）
- 必须保留的接口/信号：`SessionDB(session_id, db_dir="workspace")`；`_cleanup_stale_sessions() -> int`
- 必须遵循的规约：裁定 F2（库名带 PID ＋ 只删无对应活进程的库；须处理极小概率的 **PID 复用**）

#### 5. 验证
- 用例构造：启动实例 A 并导入一张表 → 保持 A 运行 → 启动实例 B
- 期望输出：B 启动**不删除** A 的会话库；A 仍可正常执行
- 失败判据：A 的会话库消失 / A 后续执行报"表不存在"
- 自证方式：两次启动前后列出 `workspace/` 文件清单；A 侧执行一次工作流成功

#### 6. 风险与回滚
- 可能回归点：① PID 复用导致误判"仍存活" → 累积孤儿库（可接受，优于误删）；② 旧格式文件名（无 PID）保守不删 → 需一次性人工清理
- 回滚方式：`main_window.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：解析 PID 失败时改为「按文件 mtime 超过 24h 才删」并记 warning

#### 7. 验收标准
- [ ] 双开时运行中实例的会话库不被删除
- [ ] 单实例正常关闭后其库仍被清理（`keep_db=False`）
- [ ] 旧格式孤儿库有明确的清理路径（人工或按 mtime 兜底）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/main_window.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-03 [原编号: F-05] 导出内存线性增长 → 大表被 OOM 杀掉

> 等级：P0（无法完成） ｜ **批次：B 类（可并行）** ｜ 判定：**【逻辑错误】**（注释亦谎报，见 `B-76`）

#### 1. 定位
- 文件：`rpa_engine/ops/exporter.py`
- 目标：`export_table`（L35-110，`Workbook()` 在 L82，`save` 在 L102）
- 调用链：上游 `step_executor` export 分支 → 本处 → 下游 `wb.save`
- 存在性判定：✅ 已存在（缺 `write_only`）

#### 2. 现状与缺陷判定
```python
# exporter.py L82 与 L99（普通模式 Workbook，全部行驻留内存）
    wb = Workbook()
...
        for row in rows:
            ws.append(list(row))
# exporter.py L9-11（注释谎报）
- 修复 N10：全程不使用 pandas/pd.read_sql，改为 cursor 流式取数
  分批写入 openpyxl（每批 5000 行），内存占用恒定，大表导出安全。
```
- 缺陷类型：**【逻辑错误】**（"分批取数"≠"分批写盘"：`Workbook()` 普通模式下所有 cell 对象常驻内存 → 内存随行数线性增长）
- 阻断后果链：大表导出 → 内存线性增长 → 进程被系统 OOM 杀掉 → 本轮全部中间结果丢失 → **P0：无法完成**（注释还误导排查方向）

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`ops/exporter.py` L82
  - 改前：`wb = Workbook()`
  - 改后：`wb = Workbook(write_only=True)`
  - 说明：`write_only` 模式下 `ws.append` 逐行流式写盘，内存恒定（裁定 F3）
- 改动点 2：同文件 L83-84（`wb.active` 在 write_only 模式不可用）
  - 改前：`ws = wb.active` ＋ `ws.title = ...`
  - 改后：`ws = wb.create_sheet(title=str(sheet_name)[:31])`
  - 说明：write_only 模式无 `active` 工作表
- 改动点 3：L87／L99 的 `ws.append(list(...))` —— **保持不变**（与 write_only 兼容：只能 append，不能随机写单元格／改列宽／多次 save）
- 改动点 4：L9-11 注释
  - 改后：「使用 `Workbook(write_only=True)` 流式写出，内存占用恒定；**不得**回退为普通模式（会随行数线性增长）」
- **B. 新建型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`export_table` 的签名与返回值（`int` 行数）；`BATCH_SIZE`（L32）
- 不可引入的新依赖：**是**（明确❌ xlsxwriter——裁定 F3 未采纳）
- 必须保留的接口/信号：`export_table(conn, table_name, output_path, sheet_name="数据", cancel_check=None) -> int`
- 必须遵循的规约：裁定 F3（`Workbook(write_only=True)`）；裁定 G14（注释须与行为一致）；`AGENTS.md` §2.1 条 5

#### 5. 验证
- 用例构造：① 100 万行×20 列的表导出 ② 常规 1 万行表导出 ③ 含 `.csv` 后缀的路径（顺带覆盖 `B-49`）
- 期望输出：① 导出完成且进程 RSS 峰值显著低于改动前（不再是线性增长）② 常规表结果与改动前逐格一致 ③ 后缀改写行为不变（`B-49` 维持现状）
- 失败判据：进程被杀；导出文件缺行；列宽/格式与改动前不一致（write_only 不允许改列宽，须确认现状未依赖列宽）
- 自证方式：`psutil` 采样导出期间 RSS；导出文件回读行数/列数与源表一致

#### 6. 风险与回滚
- 可能回归点：① write_only 下 `ws.append` 对超长文本（>32767）仍会截断（属 `B-34`，不属本项）；② 若未来有人要设置列宽/冻结窗格，write_only 不支持 → 须在注释中写明
- 回滚方式：`exporter.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若 write_only 与既有代码不兼容，回退为普通模式但**必须**改注释并加内存警戒（不得保留谎报注释）

#### 7. 验收标准
- [ ] 大表导出完成（不被 OOM），RSS 峰值不随行数线性增长
- [ ] 导出文件行数/列名/值与改动前一致
- [ ] 注释与实际行为一致

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/exporter.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-04 [原编号: F-06] JOIN 输出无上限 → 低基数匹配键触发笛卡尔积写满磁盘

> 等级：P0（无法完成） ｜ **批次：B 类** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/ops/mapping_matcher.py`
- 目标：`match_tables`（产表段 L216-221）
- 调用链：上游 `step_executor` mapping_match 分支 → 本处 `CREATE TABLE AS` → 下游 `table_row_count`（仅日志）
- 存在性判定：✅ 已存在（无上限／无预估）

#### 2. 现状与缺陷判定
```python
# mapping_matcher.py L216-221（建表后仅取行数用于日志）
    with txn(conn):
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(output_table)}")
        conn.execute(f"CREATE TABLE {quote_ident(output_table)} AS {sql}")

    from ops.sqlite_manager import table_row_count
    row_count = table_row_count(output_table, conn)
```
- 缺陷类型：**【缺少容错】**（无 `LIMIT`／无行数预估／无输出上限；`ensure_index` 仅作用于输入表匹配列）
- 阻断后果链：低基数匹配键（如"地区"）→ 左 5 万 × 右 5 万 → 笛卡尔积 25 亿行 → `CREATE TABLE AS` 持续写入 → **磁盘写满** → 后续步骤全部失败 → **P0：无法完成**（且磁盘写满会波及会话库）

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`ops/mapping_matcher.py` 在 L216 建表**之前**插入预估与上限检查
  - 改前：直接 `DROP TABLE` + `CREATE TABLE AS`
  - 改后：
    ```python
    left_n = table_row_count(left_table, conn)
    right_n = table_row_count(right_table, conn)
    if max_output_rows > 0 and left_n * right_n > max_output_rows:
        raise ValueError(
            f"匹配结果预计约 {left_n * right_n} 行，超出上限 "
            f"{max_output_rows} 行。请收窄匹配条件后重试。")
    ```
  - 说明：以**乘积上界**做保守预估（宁可误报也不写满磁盘）；阈值来自 JSON `global.max_output_rows`（默认给一个远超正常台账的值，见裁定 F4）
- 改动点 2：同文件同段 —— 保持 `DROP`／`CREATE` 语义不变（属 `B-12` 专项）
  - 说明：本项**不**改产表语句，只加前置上限
- 改动点 3：`rpa_engine/ops/step_executor.py` mapping_match 分支（约 L236-242）
  - 改后：把 `max_output_rows` 从 `step_config`／`global_config` 传入（**须先读 `step_executor.py` L188-200 的 `global_config` 获取方式**）`[UNVERIFIED]`
- **B. 新建型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：匹配 SQL 的语义（LEFT/RIGHT/FULL JOIN 与列序）；`match_columns` 参数结构
- 不可引入的新依赖：是
- 必须保留的接口/信号：`match_tables(conn, left_table, right_table, match_columns, mode, output_table) -> int`
- 必须遵循的规约：裁定 F4（**超限＝报错中断，不截断**；上限可配）；裁定 G6（本项不涉"不可逆删表"，后者见 `B-12`）

#### 5. 验证
- 用例构造：① 左表 10 万行、右表 10 万行、匹配键为单值 `地区='华东'`（构造笛卡尔积） ② 正常 1:1 匹配
- 期望输出：① 执行前报错"预计约 100 亿行，超出上限"并中断（**不产生大表**） ② 正常匹配结果与改动前一致
- 失败判据：磁盘被写满；或超限被静默截断（丢数据）
- 自证方式：执行前后磁盘可用空间；`logs/gui_*.log` 的上限报错；正常场景结果比对

#### 6. 风险与回滚
- 可能回归点：① 误报（乘积上界远大于实际结果，如键唯一时）→ 阈值须给足够大并可在 JSON 调大；② 两次 `COUNT(*)` 带来开销（大表全表扫描）
- 回滚方式：`mapping_matcher.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若预估开销不可接受，降级为「不预估，但在 `CREATE TABLE AS` 后立即检查行数，超限则 `DROP` 并报错」——**仍不得截断**

#### 7. 验收标准
- [ ] 笛卡尔积场景在执行前/后报错中断，不写满磁盘
- [ ] 正常匹配行为与改动前一致
- [ ] 上限可由 JSON 配置；未配置时有安全默认值

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/mapping_matcher.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-05 [原编号: F-07] 「终止」对 8/9 操作无效

> 等级：P0（无法中止 → 大任务无法完成） ｜ **批次：B 类** ｜ 判定：**【缺失实现】** ｜ **GUI 形态已裁定**

#### 1. 定位
- 文件：`rpa_engine/ops/`（8 个函数签名）／`rpa_engine/ops/step_executor.py` L261（唯一传 `cancel_check` 的分支）／`rpa_engine/gui/` 终止按钮
- 目标：`filter_table`／`dedup_table`／`match_tables`／`aggregate_table`／`copy_table`／`merge_tables`／`rename_columns`／`convert_dtype` 的签名
- 调用链：上游 GUI 终止按钮 → `worker.request_cancel` → `cancel_check` → 仅 `export`／`table_importer` 分支消费
- 存在性判定：⚠️ 部分存在（机制已存在，**8 个函数未接线**）

#### 2. 现状与缺陷判定
```python
# step_executor.py L258-262（仅 export 分支传 cancel_check）
        call_args.update(
            table_name=target_table,
            output_path=output_path,
            sheet_name=clean_params.get("sheet_name", "数据"),
            cancel_check=cancel_check,
        )
# 其余 8 个分支（L212-250, L263-294）均未传 cancel_check
```
- 缺陷类型：**【缺失实现】**（`cancel_check` 未接入 8 个操作）
- 阻断后果链：执行 `mapping_match`（大 JOIN）期间点终止 → `cancel_check` 无人消费 → SQL 继续跑（SQLite 无法中断运行中的 SQL）→ 600s 超时**只是 warning**（`executor.py` L179-186）→ **P0：无法中止**，用户只能强杀进程（连带 `B-06`／`B-08` 风险）

#### 3. 修改方案
**A. 修改型 ＋ GUI 形态（已裁定）**
- 改动点 1（**本轮必做**）：终止按钮形态 —— 悬停 `tooltip` ＋ 点击时弹提示（problem.md 附录 G 第 2 项）
  - 改前：终止按钮始终可点，点击后对 8/9 操作无效果（无任何反馈）
  - 改后：当当前步骤类型属于"不支持中断集合"时，按钮**置灰**且 `setToolTip("本步骤不支持中断")`；若因状态机要求必须可点，则点击时弹信息框「本步骤不支持中断，请等待其完成」
  - 说明：§2.3 GUI 形态硬停止由此解除；**不改界面排版**
- 改动点 2（**与 `P1-2`／`B-43` 合并立项**，本轮可只登记）：8 个 ops 函数加 `cancel_check` 参数
  - 改前签名：`filter_table(conn, table_name, conditions, output_table, logic="AND") -> int`（示例）
  - 改后签名：追加**关键字参数** `cancel_check: Optional[Callable[[], bool]] = None`（**保持向后兼容**），并在**批处理循环**（如有）内每 N 行检查一次
  - 说明：SQLite 无法中断运行中的 SQL → 只能在 Python 侧循环内检查；`filter`／`dedup`／`aggregate` 为单条 SQL，**无法中断** → 归入"不支持中断集合"
- 改动点 3：`ops/step_executor.py` L212-250／L263-294
  - 改后：把 `cancel_check=cancel_check` 补入上述可中断分支（`copy_table`／`merge_tables`／`rename_columns`／`convert_dtype`）
- 注意：不得改变既有分支结构与参数白名单（`step_executor.py` L196-201）
- **B. 新建型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`step_executor` 的 9 分支结构（裁定 P2-2 已判"手写 9 分支不触红线"，但不得重构）；参数白名单
- 不可引入的新依赖：是
- 必须保留的接口/信号：8 个 ops 函数的**现有位置参数**（只允许追加关键字参数）；`request_cancel()`／`is_cancelled`
- 必须遵循的规约：裁定 F6（置灰＋提示；§2.3 硬停止解除）；裁定 F7（与 `P1-2` 合并）；`AGENTS.md` §2.2 条 5（不改编排代码）

#### 5. 验证
- 用例构造：① 执行含大 JOIN 的工作流，点击终止 ② 执行含 `copy_table` 的 3 步流程，点击终止
- 期望输出：① 按钮置灰＋提示"本步骤不支持中断"（不再是无反馈） ② `copy_table` 步骤在检查点中止，返回 `cancelled`
- 失败判据：点击终止后界面无任何反馈；或终止被误标为 `failed`
- 自证方式：UI 断言 tooltip；`logs/gui_*.log` 的 `收到终止请求`；`worker` 侧 `status`

#### 6. 风险与回滚
- 可能回归点：① 置灰逻辑依赖步骤类型判断，可能与状态机不同步；② 追加关键字参数影响 `tests/` 中的签名断言
- 回滚方式：`ops/`（涉及文件）与 GUI 文件备份至 `_temp/ImportData/backup/`
- 降级策略：若置灰实现复杂，至少实现「点击时弹提示」；8 函数接线可延后（但须登记）

#### 7. 验收标准
- [ ] 不支持中断的操作：按钮置灰并有 tooltip；点击（若可点）有提示
- [ ] 支持中断的操作：终止在检查点生效并正确返回 `cancelled`
- [ ] 未改组步骤分支结构；`tests/` 全绿

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/`（8 个函数签名）／`rpa_engine/ops/step_executor.py` L261（唯一传 `cancel_check` 的分支）／`rpa_engine/gui/` 终止按钮
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-06 [原编号: G-04] 执行中关闭程序 → QThread 运行中被析构（UB）

> 等级：P0（崩溃） ｜ **批次：B 类** ｜ 判定：**【缺少容错】** ｜ `[UNVERIFIED]`（Qt 行为**须人工验证，Agent 不可执行**）

#### 1. 定位
- 文件：`rpa_engine/gui/worker.py`／`rpa_engine/gui/main_window.py`
- 目标：`EngineWorker.__init__`（L32-36）／`MainWindow.closeEvent`（L795-802）／`MainWindow.exit_app`（L776-779）
- 调用链：关闭窗口 → `closeEvent` → `worker.wait(3000)`（返回值被丢弃）→ 下游 `_close_session`
- 存在性判定：✅ 已存在（无父子绑定、`wait` 返回值未消费）

#### 2. 现状与缺陷判定
```python
# worker.py L32-36（parent=None 无父子绑定）
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._cancel_event = None
# main_window.py L797-802（wait 返回值未消费；exit_app 完全绕过 closeEvent）
        if self.worker.isRunning():
            self.worker.request_cancel()
            self.worker.wait(3000)
        self._close_session()
        self._save_last_config()
```
- 缺陷类型：**【缺少容错】**（无父子绑定 ＋ `wait` 返回值未消费 ＋ `exit_app` L776-779 直接 `quit()` 绕过 `closeEvent`）
- 阻断后果链：执行中关闭程序 → QThread 仍在运行 → 对象被析构 → **未定义行为（进程 abort）** → **P0：崩溃**（`exit_app` 路径完全绕过收尾，风险更高）

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`gui/worker.py::EngineWorker.__init__` L32-33
  - 改前：`def __init__(self, parent: Optional[QObject] = None) -> None:` ＋ `super().__init__(parent)`
  - 改后：**保持不变**（签名兼容），但 `main_window.py` 构造处改为传入 `self` 作为 parent（**须先定位构造点**）`[UNVERIFIED]`
- 改动点 2：`gui/main_window.py::closeEvent` L797-799
  - 改前：`if self.worker.isRunning(): self.worker.request_cancel(); self.worker.wait(3000)`
  - 改后：消费返回值——
    ```python
    if self.worker.isRunning():
        self.worker.request_cancel()
        if not self.worker.wait(5000):
            logger.warning("[main] worker 未在 5 秒内结束")
            self._ignore_next_finish = True
    ```
- 改动点 3：`gui/main_window.py::exit_app` L776-779
  - 改前：`self._save_last_config(); QApplication.quit()`
  - 改后：改为走与 `closeEvent` 相同的收尾序列（抽公共方法 `_shutdown()`：worker 收尾 → `_close_session()` → `_save_last_config()` → `QApplication.quit()`）
  - 说明：消除"两条退出路径行为不一致"（这是 `B-10` 的同一根因面）
- **B. 新建型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：**线程模型**（提示词 §5.1）；`EngineWorker` 的信号定义
- 不可引入的新依赖：是
- 必须保留的接口/信号：`EngineWorker(parent=None)`；`request_cancel`／`is_cancelled`／`workflow_finished` 等 4 信号
- 必须遵循的规约：`AGENTS.md` §5.3（四阶段生命周期）；裁定 D2-1（`wait` 返回值须消费）

#### 5. 验证
- 用例构造：① 执行中直接关闭窗口 ② 执行中点「退出程序」
- 期望输出：两条路径均先优雅收尾（worker 停止、会话关闭、配置保存），进程正常退出，无 abort
- 失败判据：进程崩溃/abort；或关闭后配置未保存/会话库残留
- 自证方式：**人工会话验证**（**人工执行，Agent 跳过**）观察退出码与 `logs/`；对比两条路径的收尾日志一致性

#### 6. 风险与回滚
- 可能回归点：① 等待时间加长导致"关窗变慢"（可接受）；② `_shutdown` 抽取影响既有退出行为
- 回滚方式：`main_window.py`／`worker.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若统一收尾风险高，先只修 `wait` 返回值消费（改动点 2），把 `exit_app` 统一留待后续

#### 7. 验收标准
- [ ] 执行中关闭窗口不产生 abort，正常退出
- [ ] `exit_app` 与关窗行为一致（同一收尾序列）
- [ ] `[UNVERIFIED]` 项（Qt 实机行为）由**人工会话验证**（**人工执行，Agent 跳过**）确认并回填

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/worker.py`／`rpa_engine/gui/main_window.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-07 [原编号: G-05] 旧任务未收尾时再点「开始执行」→ 新工作流不执行也不报错

> 等级：P0（流程卡死） ｜ **批次：B 类** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/gui/worker.py`／`rpa_engine/gui/main_window.py`
- 目标：`EngineWorker.prepare`（L38-50）／`MainWindow.start_workflow`（约 L480-560，**唯一无 `isRunning()` 守卫处**）
- 调用链：GUI 按钮 → `start_workflow` → `worker.prepare` → `worker.start()`
- 存在性判定：✅ 已存在（缺重入守卫）

#### 2. 现状与缺陷判定
```python
# worker.py L38-50（复用同一 QThread，clear 共享取消标志）
    def prepare(self, workflow, sdb) -> None:
        self._workflow = workflow
        self._sdb = sdb
        self._cancel_event = self._cancel_event or _CancelFlag()
        self._cancel_event.clear()
```
- 缺陷类型：**【缺少容错】**（对运行中的 QThread 调 `start()` 是**空操作** → 既无异常也无进度）
- 阻断后果链：旧任务未收尾 → 用户再点开始执行 → `prepare` 覆盖 `_workflow` 并清取消标志 → `QThread::start()` 对运行中线程无效 → **新工作流根本不执行也不报错** → 用户以为已开始、实则空等 → **P0：流程卡死**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`gui/main_window.py::start_workflow`（入口处，须先精确定位行号）`[UNVERIFIED]`
  - 改前：无守卫，直接 `prepare` ＋ `start`
  - 改后：
    ```python
    if self.worker.isRunning():
        QMessageBox.information(
            self, "提示",
            "上一次执行还没有结束。\n请先点击「放弃执行」结束它，再重新开始。")
        return
    ```
  - 说明：裁定 G5 明定「弹提示拒绝 ＋ 引导去点放弃」；不得静默排队
- 改动点 2：`gui/worker.py::prepare` L49-50
  - 改后：追加防御——`if self.isRunning(): raise RuntimeError("worker 正在运行，拒绝 prepare")`（双保险，避免将来别处误用）
- **B. 新建型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：线程模型；`prepare` 的参数结构
- 不可引入的新依赖：是
- 必须保留的接口/信号：`prepare(workflow, sdb) -> None`；`request_cancel`／`is_cancelled`
- 必须遵循的规约：裁定 G5（弹提示拒绝＋引导）；`AGENTS.md` §2.1 条 6

#### 5. 验证
- 用例构造：启动一个耗时工作流（大 JOIN）→ 在运行中再点「开始执行」
- 期望输出：弹出中文提示引导点「放弃执行」；无新的执行被静默吞掉
- 失败判据：按钮点了无任何反应；或两条执行并行（更危险）
- 自证方式：UI 断言提示框；`logs/gui_*.log` 记录

#### 6. 风险与回滚
- 可能回归点：`isRunning()` 在某些 Qt 平台下的时序差异（`[UNVERIFIED]` 需**人工验证（Agent 不可执行）**）
- 回滚方式：`main_window.py`／`worker.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若 `isRunning()` 不可靠，改用"本地状态标记 ＋ 信号回写"双判据

#### 7. 验收标准
- [ ] 运行中再点开始执行：弹出中文提示且不启动新执行
- [ ] 正常（非运行中）点击行为不变
- [ ] **人工会话验证**（**人工执行，Agent 跳过**）确认 `isRunning()` 判定可靠（回填 `[UNVERIFIED]`）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/worker.py`／`rpa_engine/gui/main_window.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-08 [原编号: G-11] `worker.run()` 的 `conn.close()` 未包 try → `finished` 不发（进程 abort）

> 等级：P0（崩溃） ｜ **批次：B 类** ｜ 判定：**【缺少容错】** ｜ `[UNVERIFIED]`（Qt 行为**须人工验证，Agent 不可执行**）

#### 1. 定位
- 文件：`rpa_engine/gui/worker.py`
- 目标：`EngineWorker.run`（L61-122，`finally` 段 L111-122）
- 调用链：本处 `finally` → `conn.close()` L117 → `workflow_finished.emit` L121
- 存在性判定：✅ 已存在（`commit` 有 try、`close` 无 try）

#### 2. 现状与缺陷判定
```python
# worker.py L111-122（close 裸调用 → emit 可能被跳过）
        finally:
            if conn is not None:
                try:
                    conn.commit()
                except Exception:
                    pass
                conn.close()
                logger.info("[worker] worker 线程连接已关闭")
            self.workflow_finished.emit(status, time.time() - t_start,
                                        out_tables, success)
```
- 缺陷类型：**【缺少容错】**（`conn.close()` 若抛错（如连接已被外部关闭）→ 异常逃出 `run()` → **L121 `workflow_finished.emit` 永不执行** → GUI 停在"运行中"，且 QThread 内未捕获异常在 PyQt5 ≥5.5 下触发 `qFatal` → **进程 abort**）
- 阻断后果链：会话库被外部删除（`B-02`）或连接异常关闭 → `close()` 抛 `sqlite3.ProgrammingError` → 跳过 emit → GUI 卡在运行态 ＋ 进程 abort → **P0：崩溃 ＋ 流程卡死**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`gui/worker.py` L117
  - 改前：`conn.close()`
  - 改后：
    ```python
    try:
        conn.close()
    except Exception as e:  # noqa: BLE001 关闭失败不阻断信号发送
        logger.warning(f"[worker] 连接关闭失败（忽略）: {e}")
    ```
- 改动点 2：同函数 L121-122 `emit` 位置
  - 改后：**保持不变**（仍在 `finally` 内、close 之后），但由改动点 1 保证可达
- **B. 新建型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：线程模型；信号定义与参数个数（4 参 `workflow_finished`）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`workflow_finished(str, float, dict, bool)`
- 必须遵循的规约：`AGENTS.md` §2.1 条 6；裁定 D2-1

#### 5. 验证
- 用例构造：① 正常执行完成 ② 人为在 `finally` 前破坏连接（如手工删除会话库）
- 期望输出：两条路径均发出 `finished`；GUI 不会停在运行态；无 abort
- 失败判据：GUI 卡在"执行中"；进程 abort
- 自证方式：**人工会话验证**（**人工执行，Agent 跳过**）；`logs/` 的 `worker 线程连接已关闭`／`连接关闭失败` 记录

#### 6. 风险与回滚
- 可能回归点：吞掉真实错误导致排障困难 → 用 `logger.warning` 留痕（已含）
- 回滚方式：`worker.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：无（本项改动极小，不建议降级）

#### 7. 验收标准
- [ ] `conn.close()` 失败时仍发出 `finished`，GUI 不卡在运行态
- [ ] 正常路径行为不变
- [ ] **人工会话验证**（**人工执行，Agent 跳过**）确认无 abort（回填 `[UNVERIFIED]`）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/worker.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-09 [原编号: H-02] 导出先截断既有文件、失败即留损坏 zip

> 等级：P0（不可逆损坏交付物） ｜ **批次：B 类** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/ops/exporter.py`
- 目标：`export_table`（L35-110，`save` 在 L102；目录创建 L73）
- 调用链：本处 → `wb.save(str(out))` → 下游 openpyxl `ZipFile(filename,'w')`
- 存在性判定：✅ 已存在（无临时文件 + 原子替换）

#### 2. 现状与缺陷判定
```python
# exporter.py L73 与 L102（直接对目标路径开写）
    out.parent.mkdir(parents=True, exist_ok=True)
...
    wb.save(str(out))
```
- 缺陷类型：**【缺少容错】**（`wb.save` → openpyxl 以 `'w'` 打开目标 zip → **一开始即截断既有文件**；全库无「临时文件 + `os.replace`」）
- 阻断后果链：导出目标已存在旧报表 → `wb.save` 截断它 → 导出中途失败（OOM／磁盘满／进程被杀）→ 目标文件只剩**损坏的半截 zip** → 旧报表也回不来 → **P0：不可逆损坏交付物**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`ops/exporter.py` L102
  - 改前：`wb.save(str(out))`
  - 改后：
    ```python
    tmp_out = out.with_name(f"~{out.name}.tmp")
    wb.save(str(tmp_out))
    os.replace(str(tmp_out), str(out))   # 原子替换
    ```
  - 说明：失败时目标文件**保持原样**（只可能残留 `.tmp`，可清理）；文件头补 `import os`
- 改动点 2：同函数 L100-104 前后
  - 改后：把 `wb.save` 包 try/except，失败时尝试 `tmp_out.unlink()` 并 `raise`（保留原因给上层），确保不留半截文件
- 改动点 3：`ops/exporter.py` L73
  - 说明：`mkdir` 保持不变（目录先建不影响原子性）
- **B. 新建型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`export_table` 的签名与返回值；`cancel_check` 语义
- 不可引入的新依赖：是（`os` 标准库）
- 必须保留的接口/信号：`export_table(...) -> int`
- 必须遵循的规约：`AGENTS.md` §2.1 条 5；裁定 F3 不矛盾（本项与 `B-03` 可在同批或相邻批完成）

#### 5. 验证
- 用例构造：① 目录已存在 `报表.xlsx`（含 100 行有效数据），导出时人为制造失败（如磁盘写满/中断） ② 正常导出
- 期望输出：① 旧 `报表.xlsx` **内容完好**（未被截断） ② 正常导出结果与改动前一致，无 `.tmp` 残留
- 失败判据：旧文件被截断为损坏 zip；或正常导出后残留 `~*.tmp`
- 自证方式：失败前后对旧文件求 md5/行数；正常导出后列目录

#### 6. 风险与回滚
- 可能回归点：① 跨分区 `os.replace` 失败（同目录内替换，风险低）；② 目标路径为网络盘时的原子性
- 回滚方式：`exporter.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若 `os.replace` 在目标盘不可用，降级为「先备份旧文件为 `.bak`，导出成功后删除 `.bak`」

#### 7. 验收标准
- [ ] 导出失败时既有文件内容完好，无损坏 zip
- [ ] 正常导出结果一致，无 `.tmp` 残留
- [ ] 与 `B-03`（write_only）同批验证

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/exporter.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-10 [原编号: H-04b] 点标题栏 × 关闭会把好配置存成坏配置

> 等级：P0（下次启动无法恢复） ｜ **批次：B 类** ｜ 判定：**【逻辑错误】** ｜ `[UNVERIFIED]`（Qt 语义**须人工验证，Agent 不可执行**）

#### 1. 定位
- 文件：`rpa_engine/gui/main_window.py`
- 目标：`closeEvent`（L795-802）／`exit_app`（L776-779）／`_close_session`（L459-476）
- 调用链：点 × → `closeEvent` → `_close_session()`（L800）→ `_save_last_config()`（L801）
- 存在性判定：✅ 已存在（顺序错误）

#### 2. 现状与缺陷判定
```python
# main_window.py L795-802（先删副本，再存配置）
        self._close_session()
        self._save_last_config()
        event.accept()
# main_window.py L776-779（退出按钮：先存后退）
    def exit_app(self) -> None:
        self._save_last_config()
        QApplication.quit()
```
- 缺陷类型：**【逻辑错误】**（两条退出路径顺序不一致；点 × 时 `_close_session()` 先删副本，随后 `_save_last_config()` 落盘的 `source.file` 指向已删副本）
- 阻断后果链：点 × 关闭 → L800 删副本 → L801 存配置（`source.file` 指向已删副本，且**因改动前 `get_entries` 也无 `source_path`** 故必为副本路径）→ 下次启动恢复判据全假 → 配置丢失 → **P0：下次启动无法恢复**（反直觉：崩溃/断电与「退出程序」按钮反而能恢复）

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`gui/main_window.py::closeEvent` L800-801
  - 改前：`self._close_session()` 然后 `self._save_last_config()`
  - 改后：交换为 `self._save_last_config()` 然后 `self._close_session()`
  - 说明：与 `exit_app` L776-779 的顺序一致（先存后清）
- 改动点 2：抽取公共收尾方法 `_shutdown(self) -> None`（与 `B-06` 改动点 3 **同一处改动**）
  - 改后：`closeEvent` 与 `exit_app` 均调用 `_shutdown()`，其中顺序固定为「worker 收尾 → `_save_last_config()` → `_close_session()`」
- 注意：本项与 `A-10`／`A-01` 相互依赖——仅交换顺序**不足以**根治（`source.file` 仍需是原始路径）；须与 `A-10` 同批验证
- **B. 新建型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：`_save_last_config` 的"编辑态导出"口径（`include_deprecated=True`，L788）；
- 不可引入的新依赖：是
- 必须保留的接口/信号：`closeEvent(event)`；`exit_app() -> None`
- 必须遵循的规约：裁定 D2-1／D2-2（收尾顺序与 `wait` 返回值消费）

#### 5. 验证
- 用例构造：① 配好 2 步 → 点 × 关闭 → 重开 ② 配好 2 步 → 点「退出程序」→ 重开
- 期望输出：两条路径重开后**均能恢复**表与步骤
- 失败判据：点 × 后重开列表为空／步骤丢失（两条路径行为不一致）
- 自证方式：对比两条路径的 `workspace/last_config.json` 内容（`source.file` 应为原始路径）＋ UI 恢复结果

#### 6. 风险与回滚
- 可能回归点：① 交换顺序后 `_close_session` 在保存之后 → 若保存失败仍会清理（可接受）；② 与 `B-06` 的 `_shutdown` 抽取耦合
- 回滚方式：`main_window.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若 `_shutdown` 抽取风险高，仅交换 L800-801 两行

#### 7. 验收标准
- [ ] 点 × 关闭后重开能恢复配置（与「退出程序」路径一致）
- [ ] `last_config.json` 的 `source.file` 为原始路径
- [ ] 与 `A-10`／`A-01` 同批验证通过

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/main_window.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-11 [原编号: H-25] 陈旧 `finished` 劫持导航 → 点「放弃」后仍被拽进报告页

> 等级：P0（流程卡死／导航错乱） ｜ **批次：B 类** ｜ 判定：**【缺少容错】** ｜ `[UNVERIFIED]`（竞态**须人工验证，Agent 不可执行**）

#### 1. 定位
- 文件：`rpa_engine/gui/main_window.py`
- 目标：四处 `_ignore_next_finish` 置位分支（v7 记载 L249-254／L414-418／L428-433／L444-448）`[UNVERIFIED]`
- 调用链：`worker.workflow_finished` 跨线程投递 → `_on_workflow_finished` 消费 `_ignore_next_finish`
- 存在性判定：⚠️ 部分存在（置位条件不完整）

#### 2. 现状与缺陷判定
```text
现状（v7 记载，本轮未逐行复核）：
  四处均在 `if not self.worker.wait(N)` 分支内才置 `_ignore_next_finish = True`；
  而 `wait()` 返回 True（即线程已正常结束）时**不置位**，
  且 `workflow_finished` 是跨线程队列投递 → 存在"旧 finished 在导航后到达"的窗口。
```
- 缺陷类型：**【缺少容错】**（陈旧信号未隔离）
- 阻断后果链：用户点「放弃执行」→ 旧 `finished` 仍在队列 → 导航到阶段 1 后被该信号"拽"进报告页；另 `QApplication.processEvents()` 可能在**导入中途**弹出上一轮的失败框 → **P0：导航错乱／流程卡死**

#### 3. 修改方案
**A. 修改型**（须先复核实际行号与分支结构）`[UNVERIFIED]`
- 改动点 1：`main_window.py` 四处置位点
  - 改前：仅在 `if not self.worker.wait(N)` 时置位
  - 改后：改为**无条件置位**——只要执行了 `request_cancel()` ＋ `wait()`（无论返回值），就置 `self._ignore_next_finish = True`
  - 说明：取消场景下旧 `finished` 一律忽略
- 改动点 2：`_on_workflow_finished`（消费端）
  - 改后：消费时先检 `_ignore_next_finish`，为真则**清位并直接 return**（不导航）；为其后到达的**第二轮**信号留出位置（须保证只忽略一次）
- 改动点 3：导入循环中的 `QApplication.processEvents()`（`_on_confirm_import` L301）
  - 改后：保持调用，但确保 `_ignore_next_finish` 已在上一轮置位（由改动点 1 保证），避免导入中途弹上一轮失败框
- **B. 新建型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：导航（阶段切换）逻辑本身；`workflow_finished` 信号定义
- 不可引入的新依赖：是
- 必须保留的接口/信号：`_ignore_next_finish` 语义（单次忽略）
- 必须遵循的规约：裁定 D2-1（旧任务回调忽略）；`AGENTS.md` §5.3

#### 5. 验证
- 用例构造：① 执行大任务 → 点「放弃执行」→ 观察是否被拽进报告页 ② 展开执行中途返回阶段 1 并重新导入 → 观察是否弹上一轮失败框
- 期望输出：两次均不被陈旧信号影响；导航停留在用户预期页
- 失败判据：点放弃后进入报告页；或导入中途弹出上一轮失败框
- 自证方式：**人工会话验证**（**人工执行，Agent 跳过**）（竞态须人工复现）；`logs/` 中的收尾日志顺序

#### 6. 风险与回滚
- 可能回归点：无条件置位可能误吞**本轮**的 finished（若取消后本轮立即结束）→ 须靠"单次忽略"语义与信号顺序保证
- 回滚方式：`main_window.py` 备份至 `_temp/ImportData/backup/`
- 降级策略：若无法稳定区分新旧信号，改为在 `finished` 回调内用"执行轮次序号"比对（须设计轮次计数）

#### 7. 验收标准
- [ ] 点「放弃执行」后不被陈旧 `finished` 拽进报告页
- [ ] 导入中途不弹上一轮失败框
- [ ] **人工会话验证**（**人工执行，Agent 跳过**）确认竞态修复（回填 `[UNVERIFIED]`）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/main_window.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-12 [原编号: J-06（＋G-07 已并入）] 产表操作不可逆删表 ／ `merge_tables` 缺 `dst ∈ 源表` 守卫

> 等级：P0（不可逆删除）／可达性低（GUI 不可达） ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**（属"修遗漏"）

#### 1. 定位
- 文件：`rpa_engine/ops/filter_dedup.py`（L81／L155）／`rpa_engine/ops/aggregator.py`（L137 附近）／`rpa_engine/ops/mapping_matcher.py`（L217）／`rpa_engine/ops/table_lifecycle.py`（L133、`merge_tables` L196-203）
- 目标：四处 `DROP TABLE IF EXISTS <output_table>` ＋ `merge_tables` 的守卫
- 调用链：上游 `step_executor` 对应分支 → 本处 `DROP` → 下游 `CREATE TABLE AS`
- 存在性判定：✅ 已存在（缺守卫）

#### 2. 现状与缺陷判定
```python
# filter_dedup.py L81 与 L83（先 DROP 再 CREATE AS）
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(output_table)}")
        conn.execute(
            f"CREATE TABLE {quote_ident(output_table)} AS {sql}",
# mapping_matcher.py L216-218（同一模式）
    with txn(conn):
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(output_table)}")
        conn.execute(f"CREATE TABLE {quote_ident(output_table)} AS {sql}")
# table_lifecycle.py L196-203（merge：DROP dst 后按序 INSERT，无 dst∈源表 守卫）
    with txn(conn):
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(dst_table)}")
        conn.execute(f"CREATE TABLE {quote_ident(dst_table)} ({cols_def})")
        for name in table_names:
            conn.execute(f"INSERT INTO ... SELECT ... FROM {quote_ident(name)}")
```
- 缺陷类型：**【逻辑错误】**（DDL 自动提交 → `DROP` 不可回滚；`merge_tables` 未拦截"目标表又在源表列表里"）
- 阻断后果链：手写 JSON 使 `output_table` 指向活表 → `DROP TABLE` 先执行 → `CREATE TABLE AS` 失败（或成功但源表已毁）→ **不可逆删表**（v7 实测：`tables_after: []`，整个会话库被清空）；`merge_tables` 中 `dst ∈ table_names` 时 L197 `DROP dst` 先把源数据删掉 → 静默丢数据且报成功。**GUI 路径不可达**（`models.py` 恒写 `t_uid`、`step_executor.py` L207 恒派生 `t_s{n}`）

#### 3. 修改方案
**A. 修改型**（裁定 G6：合并为「产表操作不可逆删表」专项）
- 改动点 1：四处产表函数的入口守卫（统一模式）
  - 改前：直接 `DROP TABLE IF EXISTS <output_table>`
  - 改后：在建表前插入——
    ```python
    if table_exists(conn, output_table):
        _guard = table_row_count(output_table, conn)
        if _guard > 0:
            raise ValueError(
                f"目标表已存在且非空，直接覆盖会导致原数据不可恢复。"
                f"请改用其他目标表名。")
    ```
  - 说明：**只拦"活表"**（空表允许覆盖，避免破坏既有重跑语义）；四处（`filter_dedup` L81/L155、`aggregator` L137、`mapping_matcher` L217）须用**同一辅助函数**（避免四套口径）
- 改动点 2：`ops/table_lifecycle.py::merge_tables` L161-165
  - 改前：仅校验源表数量、`dst_table` 非空、源表存在、列集合一致
  - 改后：追加守卫——
    ```python
    if dst_table in set(table_names):
        raise ValueError(
            f"merge_tables: 目标表 [{dst_table}] 不能同时作为参与合并的源表"
            f"（否则其原数据会被先删除）。")
    ```
  - 说明：属**修遗漏**（同文件 `copy_table` L117-118 已有等价的 `src == dst` 拦截，可在注释中引用该先例）
- 改动点 3：四处 `DROP` 语句的注释
  - 改后：注明"DDL 自动提交、不可回滚；覆盖前须经守卫校验"
- **B. 新建型**：新增模块级辅助 `ops/table_lifecycle.py::guard_overwrite_target(conn, output_table) -> None`（供四处共用）
- **C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：产表 SQL 语义（`CREATE TABLE AS` 与列序）；`copy_table` L113-118 的既有拦截（作为先例保留）
- 不可引入的新依赖：是
- 必须保留的接口/信号：四个产表函数的签名与返回值；`merge_tables(conn, table_names, dst_table) -> None`
- 必须遵循的规约：裁定 G6（合并专项）；裁定 Q7（DDL 自动提交的认知）；`AGENTS.md` §2.2 条 4

#### 5. 验证
- 用例构造：① 手写 JSON：`filter` 的 `output_table` 设为某活表名 → 执行 ② 手写 JSON：`merge_tables` 的 `dst_table` 同时出现在 `match_table_ids` 中 → 执行
- 期望输出：① ② 均**报错拒绝**，源表数据完好（`COUNT(*)` 不变）
- 失败判据：表被 DROP；`tables_after` 为空；或静默丢数据且报成功
- 自证方式：执行前后 `SELECT COUNT(*)` 与 `sqlite_master` 表清单比对（v7 的 `J-06` 曾实跑 `output_table:"t1" → tables_after: []`）

#### 6. 风险与回滚
- 可能回归点：① 守卫会拦住原本"故意覆盖活表"的用法（**这正是需求意图**，须在报告中提示改用新表名）；② 四处改造不一致导致漏口
- 回滚方式：四个 `ops` 文件备份至 `_temp/ImportData/backup/`
- 降级策略：若守卫引发正常流程回归，降级为「WARNING ＋ 在报告中显式标注'已覆盖非空表'」，**不得**静默

#### 7. 验收标准
- [ ] `output_table`／`dst_table` 指向非空活表时**报错拒绝**，原数据完好
- [ ] 空表覆盖语义保留（重跑不报错）
- [ ] `merge_tables` 的 `dst ∈ 源表` 被拦截，且与 `copy_table` 的先例口径一致

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/filter_dedup.py`（L81／L155）／`rpa_engine/ops/aggregator.py`（L137 附近）／`rpa_engine/ops/mapping_matcher.py`（L217）／`rpa_engine/ops/table_lifecycle.py`（L133、`merge_tables` L196-203）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-13 [原编号: B5] 弃用通路一启用即致启动自检失败

> 等级：P0（启动即失败） ｜ **批次：B 类（W-22 第一批）** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/gui/models.py`／`rpa_engine/gui/app.py`／`rpa_engine/tests/test_step_catalog.py`
- 目标：`models.main_buttons`（L127-142）与弃用过滤闭包；`app.run_self_check`（约 L175-243）的按钮并集比对；测试中的同口径断言
- 调用链：启动 → `run_self_check()` → 比对"按钮集合"与"目录键集合" → 下游 自检项通过/失败
- 存在性判定：✅ 已存在（比对口径一侧未过滤弃用）

#### 2. 现状与缺陷判定
```python
# models.py L127（按钮集合排除弃用）
def main_buttons() -> List[str]:
# app.py 自检（约 L185-188，v7 记载：拿**未过滤**弃用的 catalog_keys 比对）
#   → 一旦有 deprecated=True 的功能，两边集合大小不等 → 自检失败
```
- 缺陷类型：**【逻辑错误】**（两侧口径不一致：一侧已过滤弃用、一侧未过滤）
- 阻断后果链：一旦某功能被标记 `deprecated=True` → 启动自检失败 → 弹框并退出 → **P0：无法启动**（功能级弃用通路**实际不可用**，[推断]）

#### 3. 修改方案
**A. 修改型**（裁定 Q3：W-22 第一批放行项）
- 改动点 1：`gui/app.py::run_self_check` 的弃用过滤（须先精确定位比对行）`[UNVERIFIED]`
  - 改前：使用未过滤 `catalog_keys`
  - 改后：改用**已过滤弃用**的键集合（与 `main_buttons`／`more_buttons` 同源，建议统一调用 `models` 内的单一访问器，如 `active_catalog_keys()`）
- 改动点 2：`gui/models.py`
  - 改后：新增单一访问器 `active_catalog_keys() -> List[str]`（＝排除 `deprecated` 后的键集合），供自检与按钮生成**共用**（消除双口径）
- 改动点 3：`rpa_engine/tests/test_step_catalog.py`（同口径断言）
  - 改后：把断言改为基于 `active_catalog_keys()`，并**新增**一例：构造一个 `deprecated=True` 功能 → 断言自检仍通过（回归保护）
- **B. 新建型**／**C. 废弃型**：不适用

#### 4. 约束
- 本次不可动：功能函数的三形态结构与 `STEP_CATALOG`；自检项数量（6 项）
- 不可引入的新依赖：是
- 必须保留的接口/信号：`main_buttons()`／`more_buttons()` 的返回类型；`run_self_check() -> SelfCheckResult`
- 必须遵循的规约：`docs/function-spec-rules.md`（**涉功能函数增删改须先加载该文件**；本项为守卫口径修正，不改功能集合）；裁定 Q3／G14

#### 5. 验证
- 用例构造：临时把某个功能的 `deprecated` 置 True → 启动
- 期望输出：启动自检**通过**；按钮区不出现该功能；画布/面板口径一致
- 失败判据：自检失败并退出
- 自证方式：`run_self_check().ok == True`；单测新增用例通过

#### 6. 风险与回滚
- 可能回归点：① 过滤后按钮与目录不一致（须靠单一访问器消除）；② `test_step_catalog.py` 既有断言（须同步改）
- 回滚方式：三个文件备份至 `_temp/ImportData/backup/`
- 降级策略：若无法统一访问器，至少让自检侧与按钮侧**引用同一个过滤函数**

#### 7. 验收标准
- [ ] 存在 `deprecated=True` 功能时启动自检仍通过
- [ ] `test_step_catalog.py` 新增"弃用后自检通过"用例且全绿
- [ ] 弃用功能不出现在按钮区（既有行为不变）
#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/models.py`／`rpa_engine/gui/app.py`／`rpa_engine/tests/test_step_catalog.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

### 3.2 P1 静默错误结果（31 项，七段式）

> **本组提示（2026-10-19）**：含真机依赖项与越界项者**已在台账标注并移出施工清单**（原文保留）；**本轮可施工项以 Part 3 头部台账为准**；`§0.3` 的 `P-2`（exe 重建＋真机 `.xls` 验证）为**活前置，不动**。

---

### B-14 [原编号: F-04] `IN` 必现失败；`NOT IN` 被切成错列名

> 等级：P1 ｜ **批次：B 类（可并行）** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/gui/forms.py`（`_OPS_ORDER` L33、`parse_condition_lines` L181-212、`_maybe_number` L214）／`rpa_engine/ops/sql_safety.py`（`build_where` L74 起，IN 分支）
- 存在性判定：✅ 已存在（两处口径不一致）

#### 2. 现状与缺陷判定
```python
# forms.py L33-35（_OPS_ORDER 无 "NOT IN"）
_OPS_ORDER = ["=", "!=", ">", "<", ">=", "<=", ...]
_OPS = [op for op in _OPS_ORDER if op in SUPPORTED_OPERATORS]
# forms.py L196 与 L214（标量被转数字）
                        "value": _maybe_number(val),
def _maybe_number(val: str) -> Any:
```
- 缺陷类型：**【逻辑错误】**（`build_where` 对 `IN` 强制要求 list，而表单侧把值转成标量 → 必失败；`_OPS_ORDER` 缺 `NOT IN` → 手输 `列 NOT IN (...)` 被 `" IN "` 分隔符切开，得 `{"column":"列 NOT","op":"IN"}`）
- 阻断后果链：用户填 `IN` 条件 → 值被 `_maybe_number` 转标量 → `build_where` 校验失败 → 步骤失败；`NOT IN` → 错列名 → 查询报"列不存在" → **P1：功能不可用 ＋ 静默错误**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`forms.py::_OPS_ORDER` L33 —— 补 `"NOT IN"`，且置于 `"IN"` **之前**（保证 `" IN "` 分隔符优先匹配更长的运算符）
- 改动点 2：`forms.py::parse_condition_lines` L196 —— 当运算符为 `IN`／`NOT IN` 时，值**必须**解析为 list（按逗号/顿号切分并 strip），**跳过** `_maybe_number`
- 改动点 3：`ops/sql_safety.py::build_where`（IN 分支）—— 收到标量时抛**中文**错误（"`IN` 需要多个值，请用逗号分隔"），**不得**静默改写
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`SUPPORTED_OPERATORS` 集合（`sql_safety.py` L20-33）；`build_where` 签名；裁定 G8（不改写用户输入）
- 必须保留：`parse_condition_lines(text) -> List[Dict[str, Any]]`

#### 5. 验证
- 用例构造：条件 `电表号 IN (0123, 0456)` 与 `电表号 NOT IN (0123)`
- 期望输出：`IN` 命中 2 行；`NOT IN` 正确解析且列名为 `电表号`
- 失败判据：`IN` 执行报错；列名变为 `电表号 NOT`
- 自证方式：执行结果行数；`logs/` 中的 SQL 参数

#### 6. 风险与回滚
- 风险：`_OPS_ORDER` 顺序变化影响下拉展示顺序（须核对 `_OPS` 派生结果）
- 回滚：`forms.py`／`sql_safety.py` 备份至 `_temp/ImportData/backup/`
- 降级：若 list 解析实现复杂，至少修改动点 1＋3（让 `NOT IN` 不错列名）

#### 7. 验收标准
- [ ] `IN` 用 list 值可执行；`NOT IN` 不再错列名
- [ ] 标量误用时给中文提示而非静默改写
- [ ] `tests/test_validator_cross.py` 等回归全绿

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/forms.py`（`_OPS_ORDER` L33、`parse_condition_lines` L181-212、`_maybe_number` L214）／`rpa_engine/ops/sql_safety.py`（`build_where` L74 起，IN 分支）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-15 [原编号: G-01] 新增步骤把「上一被选步骤」的表单参数灌进新步骤 → 导出路径 100% 失效

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】** ｜ `[UNVERIFIED]`

#### 1. 定位
- 文件：`rpa_engine/gui/page_operation_config.py`（新增步骤插入点与收拢逻辑，v7 记载 L501-513／L674-698／L477-480）
- 存在性判定：✅ 已存在（插入点与下标口径错位）

#### 2. 现状与缺陷判定
```text
现状（v7 记载，本轮未逐行复核）：选中 end 步时插入点＝sel，收拢按**旧下标**取值
   → 新步骤继承了"上一被选步骤"的表单值（含导出路径）
```
- 缺陷类型：**【逻辑错误】**（插入点与收拢下标口径不一致）
- 阻断后果链：新增步骤 → 表单值错位继承 → `output_path` 指向上一配置的路径 → 导出写入默认文件并覆盖既有 → **P1：导出路径 100% 失效（静默）**
- 失败判据：新步骤参数与上一被选步骤相同（含路径）

#### 3. 修改方案
**A. 修改型**（须先补读 L470-530 与 L660-700 取精确行号）
- 改动点 1：新增步骤插入点计算 —— 改前按 `sel`（旧下标）；改后按**当前模型步骤列表的实际插入位置**（插入后立即重算下标）
- 改动点 2：收拢逻辑 —— 改前按旧下标回写表单；改后按 `step_id`（`t_{uid}`／稳定标识）回写，**不依赖下标**
- 改动点 3：新增步骤的默认参数 —— 必须用 `models.default_params(type_name)` 的**空白默认值**（不得继承邻居表单值）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：GUI 布局；`models.insert_step` 的签名；功能函数三形态（`docs/function-spec-rules.md`）
- 必须保留：`step_id` 作为步骤稳定标识

#### 5. 验证
- 用例构造：配置步 1（导出路径 `A.xlsx`）→ 选中步 1 → 新增步 2（另一个导出）
- 期望输出：步 2 的 `output_path` 为**空白默认值**（需用户填写），而非 `A.xlsx`
- 失败判据：步 2 继承 `A.xlsx`；或导出写入 `A.xlsx` 并覆盖
- 自证方式：`to_dict()` 导出的 JSON 中各步参数

#### 6. 风险与回滚
- 风险：改为按 `step_id` 回写可能影响既有插入/删除流程（须先读 M5 三态插入逻辑）
- 回滚：`page_operation_config.py` 备份至 `_temp/ImportData/backup/`
- 降级：至少保证"新步骤不继承邻居表单值"（改动点 3）

#### 7. 验收标准
- [ ] 新增步骤参数为空白默认值，不继承上一被选步骤
- [ ] 导出路径不再被静默复用/覆盖
- [ ] 插入/删除/撤销流程回归全绿

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/page_operation_config.py`（新增步骤插入点与收拢逻辑，v7 记载 L501-513／L674-698／L477-480）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-16 [原编号: G-02] 「目标表」被静默改写，不刷新画布、不入撤销栈、无提示

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/gui/page_operation_config.py`
- 目标：L346-354（目标表下拉回填）
- 存在性判定：✅ 已存在（静默 `setCurrentIndex(0)`）

#### 2. 现状与缺陷判定
```python
# page_operation_config.py L346-354（找不到当前值就静默改回第 0 项）
        cur = step.target_table_id
        ...
            self._target_combo.setCurrentIndex(0)
            step.target_table_id = self._target_combo.itemData(0)
```
- 缺陷类型：**【逻辑错误】**（`findData(cur) < 0` 时静默改写 `step.target_table_id`，不刷新画布、不入撤销栈、无提示）
- 阻断后果链：换表后编号变化 → 下拉找不到原值 → 静默改成第 0 项 → 步骤指向**错误的表** → 画布仍画旧红虚线 → **P1：步骤静默指向错误的表**

#### 3. 修改方案
**A. 修改型**（裁定 G4）
- 改动点 1：`page_operation_config.py` L353-354
  - 改前：`setCurrentIndex(0)` ＋ 直写 `step.target_table_id`
  - 改后：**不改写** `step.target_table_id`；改为弹提示「该步骤引用的数据表已不存在，请重新选择」并保持下拉为空态（`setCurrentIndex(-1)`）
- 改动点 2：同处 → 触发画布刷新（`refresh`）并**入撤销栈**（保证可撤销该提示带来的状态变化）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：GUI 布局；撤销栈机制（`_undo_last` L567）
- 必须保留：`step.target_table_id` 的语义（不得被程序改写——裁定 G4）
- 规约：裁定 G4「弹提示 ＋ 不静默改写」

#### 5. 验证
- 用例构造：配好步骤引用 T2 → 返回阶段 1 换表使 T2 消失 → 回到阶段 2
- 期望输出：弹出中文提示；`target_table_id` **仍为 T2**（未被改写）；画布刷新
- 失败判据：`target_table_id` 被改为 T1 且无提示
- 自证方式：`to_dict()` 中该步的 `target_table_id`

#### 6. 风险与回滚
- 风险：下拉为空态可能阻断用户新增步骤（须保证可重新选择）
- 回滚：`page_operation_config.py` 备份
- 降级：若空态不可行，至少保留原值＋红框提示

#### 7. 验收标准
- [ ] 目标表失效时弹提示且不静默改写
- [ ] 画布随提示刷新；状态变化可撤销
- [ ] 用户可重新选择目标表

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/page_operation_config.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-17 [原编号: G-03] 离开阶段 2 不收拢表单 → 已填参数 100% 丢失

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】** ｜ `[UNVERIFIED]`

#### 1. 定位
- 文件：`rpa_engine/gui/page_operation_config.py`（收拢调用点：v7 记载 L652/660/519/541/616/998；**返回 L157 与退出 L299 均不收拢**）

#### 2. 现状与缺陷判定
```text
现状（v7 记载，本轮未逐行复核）：仅在新选步骤/切页等时机收拢表单，
  `返回阶段 1`（L157）与 `退出/进入执行`（L299）路径**不收拢**，
  而 main_window 侧仍直接 `to_dict()` 落盘 → 未收拢的表单值丢失
```
- 缺陷类型：**【逻辑错误】**（遗漏收拢调用点）
- 阻断后果链：用户填完参数 → 点返回/执行 → 表单未回写模型 → `to_dict()` 落盘的是旧值 → **P1：已填参数 100% 丢失**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`page_operation_config.py` 的返回路径（L157 附近）与退出/执行路径（L299 附近）
- 改后：两条路径均**先调用收拢**（抽出统一方法 `_flush_form()`，内部即现有多处收拢逻辑），再 emit/切换
- 改动点 2：把现散落 6 处的收拢调用统一替换为 `_flush_form()`（**不改行为**，只统一入口，避免将来再漏）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：GUI 布局；阶段切换信号
- 必须保留：`page_operation_config` 的对外信号与 `restore_config`
- 不得改变"收拢即写回模型"的语义

#### 5. 验证
- 用例构造：在步骤 1 填参数后**直接**点返回阶段 1，再返回阶段 2
- 期望输出：参数仍在（未丢失）
- 失败判据：参数被清空/回退到旧值
- 自证方式：`to_dict()` 落盘 JSON；UI 回填值

#### 6. 风险与回滚
- 风险：统一 `_flush_form()` 可能改变某些路径的时序（须逐路径验证）
- 回滚：`page_operation_config.py` 备份
- 降级：仅补两处遗漏调用点（不改其余 6 处）

#### 7. 验收标准
- [ ] 返回阶段 1 后参数不丢失
- [ ] 进入执行前参数已完整落盘
- [ ] 其余收拢时机行为不变

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/page_operation_config.py`（收拢调用点：v7 记载 L652/660/519/541/616/998；**返回 L157 与退出 L299 均不收拢**）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-18 [原编号: G-08] `rename_columns` 的 False 返回被丢弃 → 改名没生效却显示成功

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】** ｜ 机制＝§5 根因 2（已复核）

#### 1. 定位
- 文件：`rpa_engine/ops/step_executor.py`（L296-316）／`rpa_engine/ops/table_schema.py`（`rename_columns`，`all_success` 返回在 L102 附近）

#### 2. 现状与缺陷判定
```python
# step_executor.py L297-311（丢弃返回值 → 恒 success=True）
    try:
        t0 = time.time()
        entry["func"](**call_args)
        ...
        return {"success": True, "message": ...}
# table_schema.py L99-102（rename_columns 以 bool 表达成败）
    return all_success
```
- 缺陷类型：**【逻辑错误】**（`entry["func"]` 的返回值被完全丢弃；`rename_columns` 返回 `False`（部分列未改）时仍报成功）
- 阻断后果链：改名部分失败 → 返回 False 被丢 → `success=True` → GUI 显示 ✅ → **P1：静默错误（改名未生效却报成功）**；同一机制的 `convert_dtype`（`B-19`）与 `P1-6`（`B-44`）同根

#### 3. 修改方案
**A. 修改型**（须与 `B-44`／`B-19` 同批，避免三套口径）
- 改动点 1：`ops/step_executor.py` L299
  - 改前：`entry["func"](**call_args)`
  - 改后：`ret = entry["func"](**call_args)`；随后按统一规则判定——
    ```python
    if entry.get("output", False):
        success = True                     # 产表类以"表已产生"为准
    elif ret is False or (isinstance(ret, int) and ret < 0):
        success = False                    # 无产出类以返回值为准
    else:
        success = True
    ```
- 改动点 2：同函数 L306-311 —— 改为返回 `{"success": success, ...}`，失败时 `message` 使用 `fail()` 的中文口径
- 改动点 3：`ops/table_schema.py::rename_columns` —— 保持返回 bool（不改签名），但**须在部分失败时如实返回 False**（复核 `all_success` 的赋值逻辑）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：9 分支结构；`step_executor` 的参数白名单（L196-201）
- 必须保留：`execute_step(...) -> Dict[str, Any]` 的键集合（`success`／`message`／`output_table`／`output_table_id`）
- 规约：裁定 Q8（`P1-6`↔`G-08` 合并）；裁定 G2（`convert_dtype` 须真的返回 False，否则本项感知不到）

#### 5. 验证
- 用例构造：构造 `rename_columns` 部分失败（如映射表含不存在的列名）
- 期望输出：步骤状态为失败，GUI 显示 ❌ 并给人话原因
- 失败判据：GUI 显示 ✅ 但列名未变
- 自证方式：`progress_callback` 的 failed 事件；临时库 `PRAGMA table_info` 对比

#### 6. 风险与回滚
- 风险：返回值判定规则影响所有 9 个操作的状态（须逐个回归）
- 回滚：`step_executor.py`／`table_schema.py` 备份
- 降级：先只对"无产出类"启用返回值判定，产表类保持原口径

#### 7. 验收标准
- [ ] `rename_columns` 部分失败时步骤报失败（不再假成功）
- [ ] 9 个操作的成功/失败判定与各自返回值语义一致
- [ ] 118 用例回归全绿

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/step_executor.py`（L296-316）／`rpa_engine/ops/table_schema.py`（`rename_columns`，`all_success` 返回在 L102 附近）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-19 [原编号: G-09] `convert_dtype` 无 CAST → 声明类型变了但值不转

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**（已一手复核）

#### 1. 定位
- 文件：`rpa_engine/ops/table_schema.py::convert_dtype`（L105-203）

#### 2. 现状与缺陷判定
```python
# table_schema.py L187-197（建新表 + INSERT ... SELECT，**无 CAST**）
    with txn(conn):
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(temp_table)}")
        conn.execute(f"CREATE TABLE {quote_ident(temp_table)} ({cols_def})")
        conn.execute(
            f"INSERT INTO {quote_ident(temp_table)} ({cols_str}) "
            f"SELECT {cols_str} FROM {quote_ident(table_name)}"
        )
# table_schema.py L203（恒返回 True）
    return True
```
- 缺陷类型：**【逻辑错误】**（只改列声明类型、不做值转换；且恒 `return True`）
- 阻断后果链：REAL→INTEGER 时小数被保留为 real → 同列 storage class 混杂 → 导出/统计结果不可预期 → **P1：静默部分转换**

#### 3. 修改方案
**A. 修改型**（裁定 G2）
- 改动点 1：`table_schema.py::convert_dtype` L190-193
  - 改前：`INSERT INTO ... SELECT <列> FROM <表>`
  - 改后：目标列加 `CAST`——`SELECT ..., CAST(<目标列> AS <to_upper>), ... FROM <表>`
- 改动点 2：CAST 失败的处理（裁定 G2）——**跳过该列并告警**（非步骤失败）：用 `try/except sqlite3.Error` 捕捉 → 记 `warnings` 并**返回 False**（让 `B-18` 的返回值判定生效）
- 改动点 3：L203 `return True` → 改为按上述结果返回 `bool`（成功 True，跳过/失败 False）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`ALLOWED_TYPE_CONVERSIONS` 白名单；`convert_dtype` 签名与返回类型（bool）
- 规约：裁定 G2（CAST 失败＝跳过该列并告警；**须同步让 `convert_dtype` 真的返回 False**）

#### 5. 验证
- 用例构造：`金额` 列含 `1.5`／`2`，执行 `REAL → INTEGER`
- 期望输出：`typeof(金额)` 全为 `integer`（`1.5` 按 SQLite CAST 语义取整）；若有无法转换值则告警且该列跳过
- 失败判据：同列出现 `real` 与 `integer` 混杂且无告警
- 自证方式：`SELECT 金额, typeof(金额) FROM t GROUP BY 1`

#### 6. 风险与回滚
- 风险：CAST 引入数据值变化（如 `1.5→1`）——属**需求预期**，须在报告中说明
- 回滚：`table_schema.py` 备份
- 降级：若 CAST 引发回归，仅保留"返回值如实"（改动点 3）＋ 报告标注"仅声明类型变更"

#### 7. 验收标准
- [ ] 类型转换后同列 storage class 一致
- [ ] 无法转换的列被跳过并告警（步骤不失败）
- [ ] `convert_dtype` 返回真实成败（配合 `B-18` 生效）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/table_schema.py::convert_dtype`（L105-203）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-20 [原编号: G-10] `on_error=skip` 时 status 仍 `completed` → 中间表被清理、排查现场丢失

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**（已一手复核）

#### 1. 定位
- 文件：`rpa_engine/engine/executor.py`
- 目标：步骤循环（L196-210）与清理段（L235-249）

#### 2. 现状与缺陷判定
```python
# executor.py L196-210（skip 仅 warning，status 不变）
            else:
                if progress_callback:
                    progress_callback(step.step_id, "failed", str(result.get("message", "")))
                if step.on_error == "stop": ...
                if step.on_error == "retry": ...
                logger.warning(f"[executor] 步骤 [{step.step_id}] 失败已跳过（策略 skip）")
# executor.py L239（status == "completed" 即清理）
    if status == "completed" and not workflow.global_config.get("keep_db", False):
```
- 缺陷类型：**【逻辑错误】**（skip 后 `status` 仍为 `completed`，与"有步骤失败"的事实矛盾；清理条件只看 status）
- 阻断后果链：skip 策略下步骤失败 → status 仍 completed → L239 命中 → 中间表被删 → 排查现场丢失 ＋ 报告页显示"完成" → **P1：静默错误结果 ＋ 现场丢失**

#### 3. 修改方案
**A. 修改型**（裁定 G7）
- 改动点 1：`executor.py` 步骤循环（L196-210）
  - 改后：skip 发生时置 `status = "partial"`（新增状态值），并保留 `steps_succeeded/steps_total` 口径
- 改动点 2：L239 清理条件
  - 改前：`if status == "completed" and not keep_db`
  - 改后：`if status == "completed" and not keep_db`（**保持不变**，即 `partial` 不清理 → 保留现场）
- 改动点 3：**必须同步处理 `_cp` 合成步**（v7 §8.4 警告）：`protected` 集合（L240-242）在 `partial` 场景下须同样参与保护，否则跳过时目标表不写回而中间表仍被清
- 改动点 4：返回值的 `status` 取值域文档与消费方（`worker.py` L98、`main_window.py`）须接受 `partial`
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`execute_workflow` 的阶段结构；`on_error` 三档语义
- 必须保留：`execute_workflow(...) -> Dict[str, Any]` 的键集合（`status` 新增取值）
- 规约：裁定 G7（status 改 `partial` ＋ 保留中间表；**须同步 `_cp` 合成步**）

#### 5. 验证
- 用例构造：3 步工作流，第 2 步 `on_error=skip` 且必失败
- 期望输出：`status == "partial"`；第 1 步的派生表**仍存在**；报告页不显示"全部完成"
- 失败判据：`status == "completed"`；中间表被删
- 自证方式：执行返回值；`sqlite_master` 表清单

#### 6. 风险与回滚
- 风险：新增 `status` 取值影响 `worker`／GUI 的既有分支（须全链路核对）
- 回滚：`executor.py` 备份
- 降级：若不改 status，则至少把清理条件改为 `and steps_succeeded == steps_total`

#### 7. 验收标准
- [ ] skip 场景 status 为 `partial`，中间表保留
- [ ] `_cp` 合成步在 partial 下目标表不被误删
- [ ] GUI 报告页不显示"完成"（诚实报告）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/engine/executor.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-21 [原编号: G-13] 画布把「覆盖原表」的派生表判为 dangling → 假悬空告警

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】** ｜ `[UNVERIFIED]`

#### 1. 定位
- 文件：`rpa_engine/gui/graph_edges.py`（v7 记载 dangling 判定 L203）／`rpa_engine/gui/models.py`（`overwritten` 状态 v7 记载 L568-571）

#### 2. 现状与缺陷判定
```text
现状（v7 记载）：graph_edges 判 dangling 的口径 ↔ models 的 overwritten 状态自相矛盾
  → "覆盖原表"的派生表被标为悬空（红虚线告警），而模型认为其有效
```
- 缺陷类型：**【逻辑错误】**（画布与模型各自演化、口径不一致——§5 根因 3）
- 阻断后果链：用户看到**假悬空告警** → 误判流程有问题 → 反复调整参数 → **P1：误导用户（静默错误展示）**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`gui/graph_edges.py` 的 dangling 判定 —— 与 `models.py` 的覆盖状态**同源**（改为查询模型侧的 `overwritten`／`deprecated` 闭包，不再独立判定）
- 改动点 2：`gui/models.py` —— 抽出单一状态访问器（如 `edge_state(table_id) -> str`），供画布消费
- **B/C**：不适用

#### 4. 约束
- 本次不可动：五类边契约（七字段）；画布只读原则
- 必须保留：`build_edges` 的返回契约
- 规约：裁定 G-04／G-13 同批；§2.2 条 9（前端不越界改后端）

#### 5. 验证
- 用例构造：配置一步"覆盖原表"的导出（`output_mode=overwrite`）
- 期望输出：不出现红虚线悬空告警
- 失败判据：出现假悬空
- 自证方式：`tests/test_graph_edges.py` 新增该场景断言

#### 6. 风险与回滚
- 风险：状态口径改为单一源可能影响 `test_states_consistency.py`
- 回滚：两文件备份
- 降级：若同源改造过大，先在 dangling 判定处**排除 overwritten 集合**

#### 7. 验收标准
- [ ] 覆盖原表的派生表不再被判 dangling
- [ ] `test_graph_edges.py`／`test_states_consistency.py` 全绿

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/graph_edges.py`（v7 记载 dangling 判定 L203）／`rpa_engine/gui/models.py`（`overwritten` 状态 v7 记载 L568-571）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-22 [原编号: G-14] 导入模板致 `step_id` 重复 → 编辑错步

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【缺少容错】** ｜ `[UNVERIFIED]`

#### 1. 定位
- 文件：`rpa_engine/gui/models.py`（模板载入保留原 `step_id`）／`page_operation_config.py`（取首个匹配）／`node_graph.py`（dict 建键）／`engine/validator.py`

#### 2. 现状与缺陷判定
```text
现状：模板导入原样保留 step_id；面板按 step_id 取首个匹配；画布 dict 建键
  → 重号时面板编辑到错的步、画布只渲染 1 张卡；validator 不查重 step_id
```
- 缺陷类型：**【缺少容错】**（无唯一性守卫）
- 阻断后果链：导入模板 → `step_id` 重复 → 用户点第 2 张卡改的是第 1 步 / 只渲染 1 张卡 → **P1：编辑错步 ＋ 画布缺卡**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`gui/models.py` 模板载入路径 —— 载入时**重新分配** `step_id`（或按 `_new_uid()` 去重），保持 `t_{uid}` 机制
- 改动点 2：`engine/validator.py::validate_steps`（L74-102）—— 追加 `step_id` 唯一性校验（与 `output_table_id` 查重同风格），重复即抛 `ValidationError`（中文）
- 改动点 3：`gui/page_operation_config.py` 取代首个匹配 —— 改为按**步骤在列表中的索引**定位（消除重号歧义）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`t_{uid}` 物理名机制；模板文件格式
- 必须保留：`step_id` 的对外语义；`validate_steps` 的签名
- 规约：`docs/function-spec-rules.md`（若触及功能函数记录表须先加载）

#### 5. 验证
- 用例构造：构造含重复 `step_id` 的模板 JSON → 导入
- 期望输出：`step_id` 被重新分配（或校验期明确报错）；面板编辑的是可见的那一步；画布卡片数与步骤数一致
- 失败判据：编辑错步；画布只出 1 张卡
- 自证方式：`to_dict()` 的 `step_id` 唯一性；画布节点计数

#### 6. 风险与回滚
- 风险：重新分配 `step_id` 可能使既有模板引用的编号失效（须在同一载入流程内同步引用）
- 回滚：`models.py`／`validator.py` 备份
- 降级：至少加 validator 查重（让重复在解析期暴露）

#### 7. 验收标准
- [ ] 重复 `step_id` 被消除或在解析期报错
- [ ] 面板编辑目标与画布卡片一一对应
- [ ] 既有模板导入仍可用

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/models.py`（模板载入保留原 `step_id`）／`page_operation_config.py`（取首个匹配）／`node_graph.py`（dict 建键）／`engine/validator.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-23 [原编号: H-03] 导出目标零保护，可静默覆盖任意既有文件

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/ops/exporter.py`（L69-73 只挡副本区）／`rpa_engine/gui/forms.py`（导出路径自由文本）／`rpa_engine/gui/app.py`（存在性检查为 DEBUG 死代码）

#### 2. 现状与缺陷判定
```python
# exporter.py L68-72（只阻止写入导入副本区，不检查既有文件）
    # R6/D7（P2-13）：导出路径不得指向程序导入副本区（防覆盖输入副本）
    _copy_area = (Path(get_engine_root()) / "temp" / "input_selection").resolve()
    _out_res = out.resolve()
    if _out_res == _copy_area or _copy_area in _out_res.parents:
        raise ValueError("export_table: 导出路径不得指向程序导入副本区")
```
- 缺陷类型：**【缺少容错】**（无"目标已存在"确认；表单为自由文本无校验）
- 阻断后果链：用户填任意路径 → 导出直接覆盖既有文件（可能覆盖他人数据）→ **P1：静默覆盖既有文件**

#### 3. 修改方案
**A. 修改型**（裁定 Q4 统一方向：不静默覆盖）
- 改动点 1：`gui/forms.py` 导出路径控件 —— 加"目标文件已存在"提示（或在 `page_operation_config` 保存时校验）
- 改动点 2：`gui/main_window.py`／`page_progress` 执行前 —— 若目标已存在则弹确认（默认按钮＝取消），用户确认后才执行
- 改动点 3：`ops/exporter.py` —— 保持只挡副本区（不新增拒绝），覆盖确认由 GUI 侧承担（导出可由 JSON 直接调用，不在 ops 层强制）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`export_table` 签名；GUI 布局
- 规约：裁定 Q4；`AGENTS.md` §2.1 条 6

#### 5. 验证
- 用例构造：导出到一个已存在的 `报表.xlsx`
- 期望输出：弹出确认框（默认取消）；确认后覆盖并成功
- 失败判据：无确认即静默覆盖
- 自证方式：UI 断言；目标文件 mtime 变化

#### 6. 风险与回滚
- 风险：确认框影响批量导出体验（可接受）
- 回滚：`forms.py` 备份
- 降级：至少给路径控件加"已存在"红色提示

#### 7. 验收标准
- [ ] 覆盖既有文件前有确认（默认取消）
- [ ] 导出路径控件对已存在文件给出提示
- [ ] 正常新路径导出无额外打扰

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/exporter.py`（L69-73 只挡副本区）／`rpa_engine/gui/forms.py`（导出路径自由文本）／`rpa_engine/gui/app.py`（存在性检查为 DEBUG 死代码）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-24 [原编号: H-07] `full_join` 静默丢行（`UNION` 对整个复合结果去重）

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**（已一手复核）

#### 1. 定位
- 文件：`rpa_engine/ops/mapping_matcher.py`（L209-214）

#### 2. 现状与缺陷判定
```python
# mapping_matcher.py L209-214（UNION 去重作用于整个复合结果）
        sql_rev = _right_view_select(...)
        # UNION 去重合并（交集行在两个视角各出现一次，UNION 去重后保留一份）
        sql = f"{sql_fwd} UNION {sql_rev}"
```
- 缺陷类型：**【逻辑错误】**（作者意图是"去交集重复"，但 `UNION` 对整个结果集去重 → **连分支内部的重复行也去掉了**）
- 阻断后果链：左 3 行（含 2 行相同）＋ 右 2 行 → 得 3 行（应 4）→ **丢 1 行且无报错**；界面文案承诺"保留两表全部行" → **P1：静默丢行**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`mapping_matcher.py` L213-214
  - 改前：`sql_fwd UNION sql_rev`
  - 改后：用 `UNION ALL` ＋ 显式排除交集——仅保留"左视角 LEFT JOIN 中右表匹配为 NULL 的行"与"右视角 LEFT JOIN 中左表匹配为 NULL 的行"＋ 两份 `INNER JOIN`
    （等价式：`SELECT ... WHERE 右键 IS NULL` `UNION ALL` `SELECT ... WHERE 左键 IS NULL` `UNION ALL` `SELECT ... INNER JOIN ...`）
  - 说明：**语义等价的 disjoint 分解**，避免对分支内部去重；**不可**简单换成 `UNION ALL`（那样交集会重复）
- 改动点 2：`mapping_matcher.py` 顶部 docstring（L14-16）
  - 改后：注明"full_join 采用 disjoint 分解，不使用 UNION 去重"
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`match_columns` 结构；列序（左列在前）；`right_join`／`left_join`／`inner_join` 语义
- 必须保留：`match_tables(...) -> int` 签名
- 规约：`AGENTS.md` §2.2 条 1（不得硬编码业务）；`B-04`（输出上限）同批验证

#### 5. 验证
- 用例构造：左表 3 行（其中 2 行完全相同的辅助列值）＋ 右表 2 行，`mode=full_join`
- 期望输出：结果 4 行（保留两表全部行、交集不重复、分支内部重复**保留**）
- 失败判据：结果为 3 行（丢行）
- 自证方式：`SELECT COUNT(*)`；逐行核对；v7 记载该场景实测为 3 行（应 4）

#### 6. 风险与回滚
- 风险：三路 `UNION ALL` 的列序/别名对齐（须逐列核对）；性能略降
- 回滚：`mapping_matcher.py` 备份
- 降级：若分解实现复杂，改 `UNION`→`UNION ALL` 并把交集行在**子查询内**去重（需额外 `DISTINCT`）

#### 7. 验收标准
- [ ] `full_join` 不再丢分支内部重复行
- [ ] 交集行不重复出现
- [ ] `left/right/inner_join` 行为不变

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/mapping_matcher.py`（L209-214）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-25 [原编号: H-08] `merge_tables` 无「同一张表重复参与」守卫 → 源表被重复计入

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/ops/table_lifecycle.py::merge_tables`（L143-211，INSERT 循环 L199-203）／`rpa_engine/gui/forms.py`（合并列表取 `available_table_ids()`）

#### 2. 现状与缺陷判定
```python
# table_lifecycle.py L199-203（按传入顺序 INSERT，不去重）
        for name in table_names:
            conn.execute(
                f"INSERT INTO {quote_ident(dst_table)} ({cols_str}) "
                f"SELECT {cols_str} FROM {quote_ident(name)}"
            )
```
- 缺陷类型：**【缺少容错】**（未去重；`forms.py` 的合并列表**含本步目标表自身**，提示语还写"目标表本身自动参与合并"）
- 阻断后果链：同一张表在列表中重复 → 被 INSERT 两次 → 行数翻倍 → **P1：静默数据翻倍**（同一机制在 `mapping_matcher.py` L146-147 **有**守卫 → 属遗漏非设计）

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`ops/table_lifecycle.py::merge_tables` 入口（L161-165 附近）
  - 改后：`if len(set(table_names)) != len(table_names): raise ValueError("merge_tables: 同一张数据表不能重复参与合并")`
- 改动点 2：`gui/forms.py` 合并列表构造 —— 排除本步目标表；并把提示语从"目标表本身自动参与合并"改为"目标表由系统指定，无需勾选"
- **B/C**：不适用

#### 4. 约束
- 本次不可动：列集合一致性校验；`merge_tables` 签名
- 规约：裁定 Q8（重叠登记合并）；与 `B-12` 的 `dst∈源表` 守卫**同批**（二者都在本函数入口）

#### 5. 验证
- 用例构造：`match_table_ids = ['T1','T1']`
- 期望输出：报错拒绝（中文）
- 失败判据：结果行数翻倍且报成功
- 自证方式：`SELECT COUNT(*)`；错误信息

#### 6. 风险与回滚
- 风险：既有"故意重复"用例（无正当场景）
- 回滚：两文件备份
- 降级：不适用

#### 7. 验收标准
- [ ] 重复参与被拒绝且给中文提示
- [ ] GUI 合并列表不再含目标表自身
- [ ] 正常合并行为不变

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/table_lifecycle.py::merge_tables`（L143-211，INSERT 循环 L199-203）／`rpa_engine/gui/forms.py`（合并列表取 `available_table_ids()`）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-26 [原编号: H-11] `retry_count<=0` → 该步一次都不执行；非法值抛裸 `ValueError` 逃逸

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【缺少容错】**（已一手复核）

#### 1. 定位
- 文件：`rpa_engine/engine/parser.py`（L190 `retry_count=int(...)`）／`rpa_engine/engine/executor.py`（重试分支）／`rpa_engine/gui/main_window.py`（异常捕获面）

#### 2. 现状与缺陷判定
```python
# parser.py L190（裸 int()，非法值抛 ValueError）
            retry_count=int(s.get("retry_count", 3)),
```
- 缺陷类型：**【缺少容错】**（① `attempts = retry_count` → `range(1, 0+1)` 为空 → 该步**未执行**即被判定"重试 0 次后仍失败"；② 非数字抛裸 `ValueError`，而 GUI 只捕 `(ParserError, ValidationError)` → 逃逸到 excepthook）
- 阻断后果链：`retry_count` 填 `0` → 步骤未执行却报失败；填 `"abc"` → `ValueError` 逃逸 → 走 `A-14` 的钩子（原文弹窗）→ **P1：语义错 ＋ 异常逃逸**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`parser.py` L190 —— 改为安全解析：非整数或 `< 1`（或与 `stop`/`skip` 口径统一为"至少执行 1 次"）抛 **`ParserError`**（中文，指明字段与合法范围）
- 改动点 2：`engine/executor.py` 重试分支 —— `attempts` 至少为 1；并统一口径（`stop`/`skip` 配 `0` 时行为与 `retry` 一致）
- 改动点 3：`gui/main_window.py`（工作流加载处）异常捕获面 —— 追加 `ParserError` 已在集合内则无需改；确认无遗漏
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`StepDef.retry_count` 字段与默认值 3；`on_error` 三档语义
- 规约：`AGENTS.md` §2.1 条 6

#### 5. 验证
- 用例构造：JSON `retry_count` 分别为 `0`／`"abc"`／`3`
- 期望输出：`0` → 明确报错（或统一为执行 1 次）；`"abc"` → 中文 `ParserError`（不弹技术原文）；`3` → 行为不变
- 失败判据：步骤未执行却报"重试 0 次后仍失败"；裸 `ValueError`
- 自证方式：加载工作流的错误提示；`logs/` 异常类型

#### 6. 风险与回滚
- 风险：口径统一可能改变既有测试期望
- 回滚：`parser.py` 备份
- 降级：仅修非法值报错（改动点 1），`0` 语义留待裁定

#### 7. 验收标准
- [ ] `retry_count=0` 有明确中文报错或统一语义（不含"未执行"歧义）
- [ ] 非数字值走 `ParserError` 人话，不逃逸
- [ ] 正常值行为不变

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/engine/parser.py`（L190 `retry_count=int(...)`）／`rpa_engine/engine/executor.py`（重试分支）／`rpa_engine/gui/main_window.py`（异常捕获面）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-27 [原编号: H-13] 筛选条件值被强制转数字 → 静默命中 0 行、前导零不可逆丢失

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**（已一手复核）

#### 1. 定位
- 文件：`rpa_engine/gui/forms.py`（`_maybe_number` L214；调用点 L196；回填 `format_conditions` L226）

#### 2. 现状与缺陷判定
```python
# forms.py L196（条件值被转数字）与 L214（转换实现）
                        "value": _maybe_number(val),
...
def _maybe_number(val: str) -> Any:
# format_conditions L226 起（回填再丢一次前导零）
```
- 缺陷类型：**【逻辑错误】**（用户输入被程序改写；`int("1_000")=1000`、全角 `"１２３"→123` 等同样被吞）
- 阻断后果链：条件 `电表号 = 0123456789` → 值变 `123456789` → 查询静默 **0 行**；回填再次丢前导零 → 用户无法察觉差异 → **P1：静默错误结果**

#### 3. 修改方案
**A. 修改型**（裁定 G8）
- 改动点 1：`forms.py::_maybe_number` / 调用点 L196 —— **不做**自动转换；值原样作为字符串透传（引号与比较由 `build_where` 的参数化占位符处理）
- 改动点 2：`format_conditions`（L226）—— 回填时使用**真值**（list 用真 list；字符串原样），不再 `f"...{value}..."` 拼接丢精度
- 改动点 3：若确需数值比较语义，改为由用户显式选择运算符或类型（**不得**程序猜测）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`build_where` 的参数化机制（L146-160）
- 规约：裁定 G8（不改写用户输入 ＋ 明确提示）；裁定 H-12 随本项定调（不自动改写）

#### 5. 验证
- 用例构造：条件 `电表号 = 0123456789`（源列含 `0123456789`）
- 期望输出：命中 1 行（非 0 行）；回填值仍为 `0123456789`
- 失败判据：0 行；或回填值为 `123456789`
- 自证方式：执行结果；UI 回填显示；`SELECT COUNT(*)`

#### 6. 风险与回滚
- 风险：全部按字符串比较会改变既有"数值比较"用例（如 `金额 > 100` 仍由 SQL 数值语义处理，不受影响）；须回归验证
- 回滚：`forms.py` 备份
- 降级：至少回填不丢精度（改动点 2）

#### 7. 验收标准
- [ ] 前导零条件命中正确行数
- [ ] 回填值与原输入一致（无精度丢失）
- [ ] 数值/区间条件行为不变

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/forms.py`（`_maybe_number` L214；调用点 L196；回填 `format_conditions` L226）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-28 [原编号: H-14] 合法 list 参数被回填成字符串 → 打开即退化

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/gui/forms.py::format_conditions`（L226 起）

#### 2. 现状与缺陷判定
```python
# forms.py L226 起（list 被拼成字符串）
def format_conditions(conditions: List[Dict[str, Any]]) -> str:
    ...
        f"...{c.get('value', '')}"     # list 形态被渲染为 "['a','b']"
```
- 缺陷类型：**【逻辑错误】**（list 参数在回填时字符串化 → 再次解析时触发 `B-14` 的 IN 故障）
- 阻断后果链：外部 JSON 的合法 list 条件 → 打开配置即被渲染成 `['a','b']` 文本 → 保存后变为字符串 → 执行时 `IN` 失败 → **P1：功能退化**

#### 3. 修改方案
**A. 修改型**（裁定 G8）
- 改动点 1：`forms.py::format_conditions` —— list 值时用逗号连接（`"、".join(map(str, v))`）渲染，**不**输出 Python repr
- 改动点 2：`forms.py::parse_condition_lines` —— 与 `B-14` 改动点 2 共用同一"list 解析"实现（保证往返一致）
- 改动点 3：新增/确认往返单测（`list → 文本 → list` 恒等）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：条件字典结构（`column`／`op`／`value`）
- 规约：裁定 G8；与 `B-14` 同批（共用解析器）

#### 5. 验证
- 用例构造：外部 JSON 含 `{"column":"电表号","op":"IN","value":["0123","0456"]}` → 打开配置 → 保存 → 再打开
- 期望输出：往返后 `value` 仍为**真 list**
- 失败判据：变为字符串 `"['0123', '0456']"` 或 `"0123、0456"`
- 自证方式：`to_dict()` 的 JSON；单测往返断言

#### 6. 风险与回滚
- 风险：分隔符选择（顿号 vs 逗号）影响用户输入习惯 → 解析器两种都接受
- 回滚：`forms.py` 备份
- 降级：至少不输出 Python repr

#### 7. 验收标准
- [ ] list 条件往返后仍为 list
- [ ] 与 `B-14` 共用同一解析实现
- [ ] 往返单测通过

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/forms.py::format_conditions`（L226 起）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-29 [原编号: H-17] 报告页「输出文件数／清单」是假的

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/gui/models.py::collect_file_stats`（L940 起）／`rpa_engine/gui/page_report.py`

#### 2. 现状与缺陷判定
```python
# models.py L940（纯按模型罗列：不判存在性、不看该步是否成功）
def collect_file_stats(model: WorkflowModel, engine_root: Path) -> Dict[str, List[str]]:
```
- 缺陷类型：**【逻辑错误】**（"输出文件清单"来自模型声明而非实际产物）
- 阻断后果链：步骤未执行/失败 → 报告页仍列出该文件 → 文员取到**上轮陈旧文件或空位** → **P1：假报告**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`models.py::collect_file_stats` —— 增加存在性判定（`Path(path).is_file()`）与该步**执行状态**过滤（依赖 `B-20` 的 `partial` 状态）
- 改动点 2：`gui/page_report.py` —— 区分"已生成（含大小/时间）"与"未生成"，并对未生成给出原因
- **B/C**：不适用

#### 4. 约束
- 本次不可动：报告页布局（仅改数据来源与文案）
- 规约：裁定 G7（诚实报告）；与 `B-20` 同批

#### 5. 验证
- 用例构造：3 步流程，第 2 步失败（skip），第 3 步未执行
- 期望输出：报告页只列**真实存在**的文件；未生成的标"未生成"并给原因
- 失败判据：报告页列出不存在的文件
- 自证方式：对比报告页清单与磁盘实际文件

#### 6. 风险与回滚
- 风险：区分状态需 `executor` 提供步骤级结果（与 `B-20` 耦合）
- 回滚：两文件备份
- 降级：至少加存在性判定（改动点 1）

#### 7. 验收标准
- [ ] 报告页文件清单与磁盘实际一致
- [ ] 未生成项有明确说明
- [ ] 与 `B-20` 状态口径一致

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/models.py::collect_file_stats`（L940 起）／`rpa_engine/gui/page_report.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-30 [原编号: H-19] 解析静默丢项 → 参数少一半却校验通过

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/gui/forms.py`（`parse_pair_lines` L157、`parse_token_list` L171、`parse_condition_lines` L181）

#### 2. 现状与缺陷判定
```python
# forms.py L157 / L171 / L181（三种解析器策略不一致）
def parse_pair_lines(text: str) -> Dict[str, str]:
def parse_token_list(text: str) -> List[str]:
def parse_condition_lines(text: str) -> List[Dict[str, Any]]:
```
- 缺陷类型：**【逻辑错误】**（同一文件内两种相反策略：`parse_pair_lines` 空值/无 `=` 行**静默丢弃**、重名键后者覆盖前者；而 `parse_condition_lines` 抛 `ValueError`）
- 阻断后果链：用户填的参数被静默丢弃 → 参数少一半但校验通过 → 执行结果错 → **P1：静默错误结果**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`forms.py::parse_pair_lines` —— 与 `parse_condition_lines` 统一为**拒绝式**：空值行/无 `=` 行/重名键均抛 `ValueError`（中文，指明第几行）
- 改动点 2：`parse_token_list` —— 空 token 静默丢弃改为"过滤空项但**记录**丢弃数量供提示"
- 改动点 3：三个解析器的公共实现抽为 `_parse_lines(text, *, mode) -> ...`（消除双策略）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：表单控件的输入形态（多行文本）
- 规约：裁定 Q8（`P1-1`↔`H-19` 合并）；`AGENTS.md` §2.1 条 6

#### 5. 验证
- 用例构造：参数行含"空值行"与"重名键"
- 期望输出：解析报错并指明行号；不再静默丢项
- 失败判据：参数被静默丢弃且校验通过
- 自证方式：UI 错误提示；`to_dict()` 参数条数

#### 6. 风险与回滚
- 风险：改为拒绝式会让既有"宽松输入"用例失败（属预期）
- 回滚：`forms.py` 备份
- 降级：至少对"重名键"拒绝

#### 7. 验收标准
- [ ] 空值/无 `=`/重名键均被拒绝并给人话（含行号）
- [ ] 三个解析器策略一致
- [ ] 新增解析单测（`P1-1`／`B-42` 承接）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/forms.py`（`parse_pair_lines` L157、`parse_token_list` L171、`parse_condition_lines` L181）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-31 [原编号: H-20] 撤销会静默吞掉窗口期内的其它改动

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**（已一手复核）

#### 1. 定位
- 文件：`rpa_engine/gui/page_operation_config.py::_undo_last`（L567 起）

#### 2. 现状与缺陷判定
```python
# page_operation_config.py L567 起（整覆盖四类结构）
    def _undo_last(self) -> bool:
```
- 缺陷类型：**【逻辑错误】**（撤销时整体覆盖 `model.tables/steps/deprecated/table_states`；撤销条存活窗口内（v7 记载 5s）用户的其它改动被**无声抹掉**；栈为 `deque(maxlen=10)`，超限静默丢最老快照）
- 阻断后果链：删步 → 5 秒内改参数 → 点撤销 → 新改动被覆盖 → **P1：数据丢失且无提示**

#### 3. 修改方案
**A. 修改型**（裁定 G12）
- 改动点 1：`_undo_last` 入口 —— 先比对"当前 model 状态"与"快照后状态"，**不一致则拒绝撤销**并提示「检测到撤销后有新的改动，已取消本次撤销」
- 改动点 2：撤销条存活窗口（v7 记载 5s）—— 缩短或改为"有后续改动即失效"（裁定 G12 原话）
- 改动点 3：栈满（`maxlen=10`）时记 warning（不再静默）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：撤销栈的存储结构（`deque`）
- 规约：裁定 G12（撤销改为"有后续改动即失效"）

#### 5. 验证
- 用例构造：删步 → 5 秒内改参数 → 点撤销
- 期望输出：拒绝撤销并提示（参数改动保留）
- 失败判据：改动被无声抹掉
- 自证方式：`to_dict()` 前后对比

#### 6. 风险与回滚
- 风险：拒绝撤销可能让用户困惑 → 提示文案须说明原因
- 回滚：`page_operation_config.py` 备份
- 降级：至少加"后续改动即失效"判据

#### 7. 验收标准
- [ ] 撤销不会吞掉窗口期内的其它改动
- [ ] 拒绝时给出中文提示
- [ ] 无后续改动时撤销行为不变

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/page_operation_config.py::_undo_last`（L567 起）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-32 [原编号: H-22] 「引用未定义的数据表」的完美中文报错被丢弃 → 兜底

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/engine/validator.py::validate_table_references`（L105-137，报错在 L116-118）／`rpa_engine/gui/worker.py`（L102-110）／`rpa_engine/gui/main_window.py`（错误回显）

#### 2. 现状与缺陷判定
```python
# validator.py L115-119（已是完美中文报错）
        if s.target_table_id not in available:
            raise ValidationError(
                f"步骤 [{s.step_id}] 引用未定义的数据表: {s.target_table_id}"
                f"（可用: {sorted(available)}）"
            )
# worker.py L105-107（只 logger.error，不回传）
        except ExecutionError as e:
            logger.error(f"[worker] 工作流执行失败: {e}")
            status = "failed"
```
- 缺陷类型：**【缺少容错】**（`worker` 未把错误文本回传 GUI，导致用户面拿空串）
- 阻断后果链：`stop`/`retry` 耗尽路径下 `ValidationError` 的完美中文被丢弃 → GUI 收到空串 → `translate_error("")` → 兜底话术 → **P1：可诊断信息丢失**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`gui/worker.py` L102-110 —— 在 `except` 分支保留 `str(e)`，通过信号或返回值回传（如给 `workflow_finished` 增加信息载荷或新增信号）
- 改动点 2：`gui/main_window.py` 消费端 —— 收到后走 `translate_error`（若已是中文则直出）
- 改动点 3：`worker.py` L108-110 的 `except Exception` 亦须回传（避免 `A-14` 兜底）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`workflow_finished` 的**现有 4 参数**（只允许新增信号或追加可选参数，避免破坏连接）
- 规约：`AGENTS.md` §2.1 条 6

#### 5. 验证
- 用例构造：构造引用未定义表的 JSON（手写）→ 执行（`on_error=stop`）
- 期望输出：GUI 显示「步骤 [S2] 引用未定义的数据表: T101（可用: [...]）」
- 失败判据：显示兜底话术
- 自证方式：UI 文本；`logs/` 中原文

#### 6. 风险与回滚
- 风险：新增信号需同步连接（`main_window.py` L211-233 区）
- 回滚：`worker.py`／`main_window.py` 备份
- 降级：至少把 `str(e)` 写进 `logger` 之外的返回值 `message`

#### 7. 验收标准
- [ ] 校验失败的中文原因呈现在 GUI（不是兜底）
- [ ] 未破坏既有信号连接
- [ ] 回归全绿

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/engine/validator.py::validate_table_references`（L105-137，报错在 L116-118）／`rpa_engine/gui/worker.py`（L102-110）／`rpa_engine/gui/main_window.py`（错误回显）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-33 [原编号: H-23] 补导阶段点「终止」被降级成「执行失败」

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/ops/table_importer.py`（L72-73 抛 `RuntimeError`）／`rpa_engine/engine/executor.py`（导入段 L107-111 只捕 `(ValueError, FileNotFoundError)`；兜底 L221-224）

#### 2. 现状与缺陷判定
```python
# executor.py L107-111（只捕两类异常，RuntimeError 逃逸）
        try:
            import_excel_table(conn, src_file, src_sheet, int(header_row),
                               t.sqlite_table, cancel_check=cancel_check)
        except (ValueError, FileNotFoundError) as e:
            raise ExecutionError(f"数据表 {t.table_id} 补导失败: {e}")
# table_importer.py L72-73（取消抛 RuntimeError）
    if cancel_check is not None and cancel_check():
        raise RuntimeError("步骤已取消：收到终止请求")
```
- 缺陷类型：**【逻辑错误】**（取消语义的 `RuntimeError` 未被识别 → 落入兜底 `except Exception` → `status="failed"`）
- 阻断后果链：补导中终止 → 状态变 `failed` → 用户看到"执行失败"而非"已终止" → **P1：状态语义错误**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`engine/executor.py::ensure_input_tables` 捕获面（L107-111）—— 追加识别取消：`except RuntimeError as e:`，若 `cancel_check()` 为真 → `raise ExecutionError("收到终止请求…")`（与循环内取消同口径，见 `executor.py` L212-220）
- 改动点 2：`ops/table_importer.py` L72-73 —— 抛 `RuntimeError` 保持不变（不改签名与语义），但**在消息中保留"收到终止请求"字样**（供上层识别）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`import_excel_table` 签名；`ExecutionError` 类型
- 规约：裁定 D1-3（循环内取消归并为 `cancelled`）

#### 5. 验证
- 用例构造：使 `ensure_input_tables` 需补导（删掉会话库中的输入表）＋ 执行中点终止（仅手写 JSON 可达）
- 期望输出：`status == "cancelled"`
- 失败判据：`status == "failed"`
- 自证方式：执行返回值；`logs/` 的取消记录

#### 6. 风险与回滚
- 风险：`RuntimeError` 捕获面放宽可能吞掉真实的运行错误 → 用 `cancel_check()` 二次判定
- 回滚：`executor.py` 备份
- 降级：至少区分"消息含收到终止请求"的 `RuntimeError`

#### 7. 验收标准
- [ ] 补导阶段终止返回 `cancelled`（非 `failed`）
- [ ] 真实运行错误仍报 `failed`
- [ ] 与 `executor.py` 循环内取消口径一致

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/table_importer.py`（L72-73 抛 `RuntimeError`）／`rpa_engine/engine/executor.py`（导入段 L107-111 只捕 `(ValueError, FileNotFoundError)`；兜底 L221-224）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-34 [原编号: J-02] 超 32767 字符的单元格在导出侧被静默截断

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【缺少容错】**

#### 1. 定位
- 文件：`rpa_engine/ops/exporter.py`（L98-99 `ws.append`）

#### 2. 现状与缺陷判定
```python
# exporter.py L98-99（openpyxl 单元格上限 32767 静默截断）
        for row in rows:
            ws.append(list(row))
```
- 缺陷类型：**【缺少容错】**（读端不截断、写端截断；无 warning、无日志、报告页无提示）
- 阻断后果链：文件中 40000 字符 → `read_excel` 读回 40000 → 落库 40000 → 写簿 → 回读 **32767** → **P1：静默丢 7233 字符**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`ops/exporter.py::export_table` L98-99 —— 写前检测 `len(str(cell)) > 32767`：截断并**记 warning ＋ 写入报告**（与 `REQ-H9` 协同）
- 改动点 2：同处 —— 报告条目含（行号、列名、原长度）
- 改动点 3：文档/注释 —— 注明"Excel 单元格硬上限 32767 字符"
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`export_table` 签名；`BATCH_SIZE`
- 规约：`AGENTS.md` §2.1 条 6（须告知）；不做"跨单元格拆分"（超出需求）

#### 5. 验证
- 用例构造：源表含 1 个 40000 字符的单元格 → 导出
- 期望输出：导出成功；报告/日志中出现截断告警（含原长度）
- 失败判据：静默截断无任何记录
- 自证方式：导出文件回读长度；报告条目

#### 6. 风险与回滚
- 风险：逐格 `len()` 检查带来开销（仅对字符串列）
- 回滚：`exporter.py` 备份
- 降级：至少写 warning

#### 7. 验收标准
- [ ] 超长单元格截断时报告/日志可见（含原长度与位置）
- [ ] 正常单元格行为不变
- [ ] 导出成功（不因超长失败）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/exporter.py`（L98-99 `ws.append`）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-35 [原编号: J-04] 真实步骤失败被改标为「已取消」，异常被吞

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**（已一手复核）

#### 1. 定位
- 文件：`rpa_engine/engine/executor.py`（L212-220）

#### 2. 现状与缺陷判定
```python
# executor.py L212-220（在 except ExecutionError 里再调 cancel_check）
    except ExecutionError:
        if cancel_check is not None and cancel_check():
            status = "cancelled"
            logger.warning("[executor] 收到终止请求，执行已终止（循环内中断）")
        else:
            status = "failed"
            raise
```
- 缺陷类型：**【逻辑错误】**（真实失败时若用户**恰好**在此期间点了终止，失败被改标为"已取消"且不 re-raise）
- 阻断后果链：`progress_callback` 已发 `S1 failed "条件列不存在"`，而最终返回 `{"status":"cancelled"}` → **P1：状态与事实矛盾**（与 `H-23`／`B-33` 方向相反）

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`executor.py` L212-220 —— 区分"**因取消而中断**"与"**失败后恰好又被取消**"：循环内取消应当由取消点直接 `break`（L166-169 已有），而非依赖 `except` 分支的二次判定
  - 改后：`except ExecutionError` 分支**只**置 `failed` 并 `raise`（**删除**二次 `cancel_check` 判定）；循环内取消路径统一走 L166-169 的显式 `break`（L167 `status = "cancelled"`）
- 改动点 2：确认 `exporter`／`table_importer` 抛出的取消（`RuntimeError("…收到终止请求")`）由 `B-33` 的捕获面转成 `ExecutionError("收到终止请求…")`，并在 L212 分支按消息前缀识别 → 归 `cancelled`
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`ExecutionError` 类型；`on_error` 三档
- 规约：裁定 D1-3（取消与失败归并口径）

#### 5. 验证
- 用例构造：① 构造必失败步骤（不点终止）② 构造必失败步骤 ＋ 期间点终止
- 期望输出：① `failed` ② **`failed`**（真实失败优先，不得被标为 cancelled）
- 失败判据：② 返回 `cancelled`
- 自证方式：执行返回值与 `progress_callback` 事件对比

#### 6. 风险与回滚
- 风险：删除二次判定后需确保所有取消路径都能被 L166 与消息识别覆盖（否则取消会被误报 failed，即 `B-33` 的反面）
- 回滚：`executor.py` 备份
- 降级：保留二次判定但**仅在异常消息含"收到终止请求"时**归 `cancelled`

#### 7. 验收标准
- [ ] 真实失败永不被标为 `cancelled`
- [ ] 取消仍能正确标为 `cancelled`
- [ ] `progress_callback` 的 `failed` 事件与最终 status 一致

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/engine/executor.py`（L212-220）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-36 [原编号: J-05] `output_tables` 返回值指向刚被自己删掉的表 → 报告页给死表号

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**（已一手复核）

#### 1. 定位
- 文件：`rpa_engine/engine/executor.py`（清理 L239-249；返回 L251-259）／`rpa_engine/gui/worker.py`（L100）／`rpa_engine/gui/main_window.py`（回写 GUI）

#### 2. 现状与缺陷判定
```python
# executor.py L239-249（清理 output_tables 的物理表）与 L251-259（仍原样返回）
    if status == "completed" and not workflow.global_config.get("keep_db", False):
        protected = {...}
        for phys in list(output_tables.values()):
            if phys in protected:
                continue
            try:
                delete_table(conn, phys)
# L258
        "output_tables": output_tables,
```
- 缺陷类型：**【逻辑错误】**（清理后仍返回同一字典；`worker.py` L100 → `main_window.py` 原样回写 GUI）
- 阻断后果链：`keep_db=False` 且末步为派生表 → 返回 `{'T2':'t_s1'}` 但 `t_s1` 已删 → **P1：报告页给出不存在的表号**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`executor.py` L243-249 —— 删除表的同时从返回字典移除（或在 L251-259 返回前过滤掉已删除项）
- 改动点 2：返回时**保留一条说明**（如 `"cleaned_tables": [...]`）以便报告页解释"中间表已清理"
- 改动点 3：`gui/main_window.py` 消费端 —— 仅展示仍存在的表（与 `B-29` 同批）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`output_tables` 的键语义（派生表编号 → 物理名）
- 规约：裁定 G7（诚实报告）；与 `B-20`／`B-29` 同批

#### 5. 验证
- 用例构造：`keep_db=false` ＋ 末步为派生表
- 期望输出：返回的 `output_tables` 不包含已删表（或明确标注已清理）；报告页不显示死表号
- 失败判据：返回 `{'T2':'t_s1'}` 而 `t_s1` 不存在
- 自证方式：执行返回值；`sqlite_master`

#### 6. 风险与回滚
- 风险：过滤后 GUI 可能少显示内容 → 需同步文案
- 回滚：`executor.py` 备份
- 降级：至少追加 `cleaned_tables` 说明

#### 7. 验收标准
- [ ] 返回值不再指向已删除的表
- [ ] 报告页无死表号
- [ ] 与 `B-20`／`B-29` 口径一致

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/engine/executor.py`（清理 L239-249；返回 L251-259）／`rpa_engine/gui/worker.py`（L100）／`rpa_engine/gui/main_window.py`（回写 GUI）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-37 [原编号: J-07] `t_s{n}` 自动命名与显式 `output_table` 撞名 → 静默 0 行 ＋ `success=true`

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/ops/step_executor.py`（L205-207 派生命名）＋四处产表 `DROP IF EXISTS`（见 `B-12`）

#### 2. 现状与缺陷判定
```python
# step_executor.py L205-207（缺省回退为 t_s{step_index}）
    output_table = None
    if entry["output"]:
        output_table = clean_params.pop("output_table", None) or f"t_s{step_index}"
```
- 缺陷类型：**【逻辑错误】**（自动名与显式名可能相同；产表 `DROP IF EXISTS` 直接覆盖）
- 阻断后果链：S1 显式 `t_s2`、S2 自动命名 `t_s2` → `DROP` 覆盖 S1 结果 → S3 复制得 **0 行**（原 3 行）而 `success=true 3/3`；清理阶段对同一物理名 `DELETE` 两次 → **P1：静默丢数据**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`ops/step_executor.py` L207 —— 自动名改为**不可撞名**的形式（如 `t_s{step_index}_{uid}` 或先检查同会话内是否已存在同名，存在则递增）；**不得**改变"缺省回退"的存在性
- 改动点 2：`engine/executor.py` —— 注册派生表时若发现物理名冲突，报错（防御性）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：GUI 侧 `t_{uid}` 机制（`models.py`）
- 规约：与 `B-12`（不可逆删表专项）同批

#### 5. 验证
- 用例构造：手写 JSON，S1 显式 `output_table="t_s2"`，S2 缺省
- 期望输出：两步物理名不撞（或明确报错）；S3 结果行数与 S1 一致（非 0 行）
- 失败判据：0 行且报成功
- 自证方式：`output_tables` 与 `sqlite_master`；行数

#### 6. 风险与回滚
- 风险：改名影响既有 JSON 兼容性（自动名仅内部使用）
- 回滚：`step_executor.py` 备份
- 降级：至少加冲突报错

#### 7. 验收标准
- [ ] 自动名不与显式名撞名
- [ ] 撞名时能报错而非静默覆盖
- [ ] 正常流程行为不变

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/step_executor.py`（L205-207 派生命名）＋四处产表 `DROP IF EXISTS`（见 `B-12`）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-38 [原编号: J-08] 无产出操作声明 `output_table_id` → 校验通过但运行期必失败

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【逻辑错误】**（已一手复核）

#### 1. 定位
- 文件：`rpa_engine/engine/validator.py`（L135-137 无条件加入）／`rpa_engine/engine/executor.py`（L191 派生号注册条件）

#### 2. 现状与缺陷判定
```python
# validator.py L135-137（无条件把 output_table_id 加入可用集合）
        # 注册派生表
        if s.output_table_id:
            available.add(s.output_table_id)
# executor.py L191（派生号注册还要求 result["output_table"]）
                if result["output_table_id"] and result["output_table"]:
```
- 缺陷类型：**【逻辑错误】**（两侧条件不一致：校验无条件、执行要求非空）
- 阻断后果链：`export`／`rename_columns`／`convert_dtype`（`output=False`）声明 `output_table_id` → 校验通过 → 执行期派生号未注册 → 下游步骤报"数据表编号 'T5' 未定义" → **P1：校验放行、运行期必失败**

#### 3. 修改方案
**A. 修改型**
- 改动点 1：`validator.py::validate_table_references` L135-137 —— 改为**有条件**加入：仅当该操作有产出（与 `step_executor` 的 `input_ids`/`output_ids` 口径同源）时才加入
- 改动点 2：`step_executor.py::STEP_CATALOG` 的产出声明（`input_ids`/`output_ids`）作为**单一事实源**供 validator 引用（消除双口径）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`validate_table_references` 签名；步骤目录结构
- 规约：`docs/function-spec-rules.md`（若触及记录表须先加载）

#### 5. 验证
- 用例构造：手写 JSON，`export` 步骤声明 `output_table_id="T5"`，后续步骤引用 `T5`
- 期望输出：**校验期**即报错（而非运行期）
- 失败判据：校验通过、运行期才报"未定义"
- 自证方式：`validate_workflow` 结果；错误消息

#### 6. 风险与回滚
- 风险：改为有条件后可能拒绝既有合法 JSON（无产出操作本就不该声明派生号）
- 回滚：`validator.py` 备份
- 降级：至少在校验期给 warning

#### 7. 验收标准
- [ ] 无产出操作声明派生号在校验期被拒
- [ ] 有产出操作的引用校验行为不变
- [ ] `tests/test_validator_cross.py` 全绿

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/engine/validator.py`（L135-137 无条件加入）／`rpa_engine/engine/executor.py`（L191 派生号注册条件）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-39 [原编号: J-09] `schema_version` 为 JSON 数字 `3.1` → 静默放行

> 等级：P1 ｜ **批次：B 类** ｜ 判定：**【缺少容错】** ｜ `[UNVERIFIED]`（经 `str()` 比较的具体行号未逐行复核）

#### 1. 定位
- 文件：`rpa_engine/engine/parser.py`（版本白名单 L65；校验 L127-132）

#### 2. 现状与缺陷判定
```python
# parser.py L65 与 L127-132（白名单校验；版本值经 str() 归一后比较）
_SUPPORTED_SCHEMA_VERSIONS = {"3.1"}
...
    if version not in _SUPPORTED_SCHEMA_VERSIONS:
        raise ParserError(...)
```
- 缺陷类型：**【缺少容错】**（JSON 里写数字 `3.1` 经 `str()` 后与 `"3.1"` 相等 → 放行；而 `"3.0"`／`"3.1.0"`／`""`／`null` 均已人话拒绝）
- 阻断后果链：手写 JSON 用数字版本号 → 静默放行（宽松而非崩溃）→ **P1：版本门禁不严**（不大可能引发运行错误，但破坏"严格门禁"口径）

#### 3. 修改方案
**A. 修改型**（须先复核实际归一行为）`[UNVERIFIED]`
- 改动点 1：`parser.py` 版本读取处 —— 改为**类型严格**：要求 `isinstance(version, str)`，否则抛 `ParserError`（中文，说明 `schema_version` 必须是字符串 `"3.1"`）
- 改动点 2：错误文案补正例（`"3.1"`）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：`_SUPPORTED_SCHEMA_VERSIONS` 内容；`ParserError` 类型
- 规约：`AGENTS.md` §2.2 条 2（JSON 是唯一载体）；版本门禁口径

#### 5. 验证
- 用例构造：`schema_version` 分别为 `"3.1"`（字符串）与 `3.1`（数字）
- 期望输出：字符串通过；数字被明确拒绝并给人话
- 失败判据：数字静默通过
- 自证方式：加载工作流的错误提示

#### 6. 风险与回滚
- 风险：若既有 JSON 由程序生成且用数字，会全部被拒（须核查 `models.to_dict` 产出类型）
- 回滚：`parser.py` 备份
- 降级：至少给 warning

#### 7. 验收标准
- [ ] 数字型 `schema_version` 被明确拒绝并给人话
- [ ] 字符串 `"3.1"` 正常通过
- [ ] 程序自身生成的 JSON 不受影响（先核查产出类型）

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/engine/parser.py`（版本白名单 L65；校验 L127-132）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-40 [原编号: DM-24] `.xls` 二次降级，类型与空值被处理两次

> 等级：P1 ｜ **批次：B 类（暂缓）** ｜ 判定：**【逻辑错误】** ｜ **裁定 Q6：待 `A-17` 真机跑通后再定**

#### 1. 定位
- 文件：`rpa_engine/ops/excel_preprocessor.py`（`ensure_xlsx` L70-128 ↔ `read_excel_sheet` L171-220）

#### 2. 现状与缺陷判定
```text
现状：.xls 先经 pd.read_excel(engine="xlrd") 读入 → 写出 xlsx（类型已被推断过一次）
      → 后续按表头读取再经 pd.read_excel 推断一次 → 类型/空值被处理两次
```
- 缺陷类型：**【逻辑错误】**（两段口径叠加）
- 阻断后果链：`.xls` 的类型与空值语义被二次处理 → 与 `.xlsx` 路径结果**不一致** → **P1：两条路径结果差异**

#### 3. 修改方案
**C. 废弃型／暂缓**（裁定 Q6）
- 说明：改 xlrd 直读会触碰 RC2 类型契约地盘（20 条 P1，不在本次范围）
- 处置：本项**本次不实施**；待 `A-17` 修完并用真实 `.xls` 在真机跑通后由人工裁定
- 若裁定后实施：在 `ensure_xlsx` 中改为"保留原始单元格类型写出"或在 `read_excel_sheet` 中对 xls 来源跳过二次推断（须新增来源标记）
- **A/B**：不适用（前置未满足）

#### 4. 约束
- 本次不可动：类型契约（RC2 地带）
- 规约：裁定 Q6（暂不整改）；`docs/function-spec-rules.md`

#### 5. 验证（暂缓）
- 用例构造：同一份数据的 `.xls` 与 `.xlsx` 两个版本，分别导入
- 期望输出：两路径的列类型与空值结果一致（裁定后作为验收判据）
- 失败判据：类型/空值不一致
- 自证方式：`PRAGMA table_info` ＋ 抽样值对比

#### 6. 风险与回滚
- 风险：改动会波及 20 条 P1 类型契约问题
- 回滚：不适用（暂缓）
- 降级：本项本身就是"暂缓"，无需再降级

#### 7. 验收标准
- [ ] **本次不实施**，仅在 Part 6 待人工补全清单登记
- [ ] `A-17` 真机跑通后由人工裁定是否实施

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/excel_preprocessor.py`（`ensure_xlsx` L70-128 ↔ `read_excel_sheet` L171-220）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-41 [原编号: B9] 参数默认值双源且取值相反

> 等级：P1 ｜ **批次：B 类（W-22 第一批）** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/gui/models.py::default_params`（L917 起）／`rpa_engine/ops/step_executor.py`（各分支回退值，如 L240 `mode` 回退 `inner_join`、L292-293 `from_type/to_type` 回退 `""`）

#### 2. 现状与缺陷判定
```python
# step_executor.py L240（引擎回退）
            mode=clean_params.get("mode", "inner_join"),
# step_executor.py L292-293（类型回退为空串）
            from_type=clean_params.get("from_type", ""),
            to_type=clean_params.get("to_type", ""),
```
- 缺陷类型：**【逻辑错误】**（GUI 侧默认值与引擎侧回退值**两处来源且取值不同**）
- 阻断后果链：界面显示"左连接"（`left_join`），手写 JSON 省略该键时按 `inner_join` 执行 → 结果错 → **P1：静默错误结果**（用户零感知）

#### 3. 修改方案
**A. 修改型**（裁定 Q3：W-22 第一批）
- 改动点 1：确立**单一事实源**——把各操作的默认值集中到 `ops/step_executor.py::STEP_CATALOG` 的 `default_params`（或独立常量表），GUI 侧改为**引用同一来源**
- 改动点 2：`step_executor.py` 各分支的 `clean_params.get(k, <回退>)` 改为 `clean_params.get(k, CATALOG_DEFAULTS[op][k])`
- 改动点 3：新增守卫单测：断言 GUI 默认值 == 引擎回退值（覆盖全部有默认键的操作）
- **B/C**：不适用

#### 4. 约束
- 本次不可动：9 分支结构；参数白名单（L196-201）
- 规约：裁定 Q3（W-22 第一批：B5＋D4＋B9）；`docs/function-spec-rules.md`（涉功能函数默认值须登记）

#### 5. 验证
- 用例构造：`mapping_match` 省略 `mode` 键 → 执行
- 期望输出：行为＝界面显示（`left_join`）
- 失败判据：按 `inner_join` 执行
- 自证方式：执行结果行数；新增守卫单测

#### 6. 风险与回滚
- 风险：默认值变更会改变既有 JSON 的执行行为（属**修正**，须在报告中说明）
- 回滚：`step_executor.py`／`models.py` 备份
- 降级：至少让引擎回退值与 GUI 一致

#### 7. 验收标准
- [ ] GUI 默认值与引擎回退值一致（守卫单测覆盖）
- [ ] 省略键时行为与界面一致
- [ ] 回归全绿

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/gui/models.py::default_params`（L917 起）／`rpa_engine/ops/step_executor.py`（各分支回退值，如 L240 `mode` 回退 `inner_join`、L292-293 `from_type/to_type` 回退 `""`）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-42 [原编号: P1-1] 功能函数专属单测缺失（与 H-19 重叠）

> 等级：P1 ｜ **批次：B 类（与 B-30 合并）** ｜ 判定：**【缺失实现】**（测试缺口）

#### 1. 定位
- 文件：`rpa_engine/tests/`（现 10 个测试文件）

#### 2. 现状与缺陷判定
```text
现状：tests/ 下无逐操作（9 项 BUILTIN_OPS）的专属单测；
      "功能函数专属单测缺失" 导致修复效果无法验证。
```
- 缺陷类型：**【缺失实现】**（测试覆盖缺口）
- 阻断后果链：修复无回归网 → 修完不知是否修好 → **P1：无法验证修复效果**（属 problem.md 定义的"可验证性阻塞"）

#### 3. 修改方案
**B. 新建型**（裁定 Q8：与 `H-19`／`B-30` 合并立项）
- 新建位置：`rpa_engine/tests/test_ops_contracts.py`
- 骨架（用例清单）：
  ```text
  test_filter_*      条件组合 / 空条件 / 前导零值
  test_dedup_*       保留首/末 / 空键
  test_aggregate_*   分组 / 指标解析（覆盖 H-19 的解析策略）
  test_export_*      ... （导出相关内容）
  test_copy/merge_rename/convert_*  签名与返回值语义
  test_parse_contracts  三个解析器的一致策略（与 B-30 共用）
  ```
- 职责边界：只做"操作层契约与解析一致性"；**不**测 GUI 交互（GUI 回归见 Part 1 §1.4 的真机会话）
- **A/C**：不适用

#### 4. 约束
- 本次不可动：既有 10 个测试文件的内容（只新增）
- 规约：`rpa_engine/tests/` 的豁免通道（`AGENTS.md` §6 ＋ `architecture.md` §9 #4）

#### 5. 验证
- 用例构造：新增用例本身
- 期望输出：`unittest discover` 用例数增加且全绿
- 失败判据：新用例失败（说明对应操作有问题，须修）
- 自证方式：`conda run -n CPS-GPES_RPA-py311 python -m unittest discover -s tests`

#### 6. 风险与回滚
- 风险：新用例可能暴露既有缺陷（**这正是目的**，须登记为发现问题）
- 回滚：删除新增测试文件
- 降级：不适用

#### 7. 验收标准
- [ ] 新增逐操作契约单测，用例数上升且全绿
- [ ] 解析器一致性（与 `B-30`）覆盖
- [ ] 不修改既有测试文件

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/tests/`（现 10 个测试文件）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-43 [原编号: P1-2] 失败/重试/取消路径零测试（与 F-07 重叠）

> 等级：P1 ｜ **批次：B 类（与 B-05 合并）** ｜ 判定：**【缺失实现】**（测试缺口）

#### 1. 定位
- 文件：`rpa_engine/tests/`（现无失败/重试/取消路径用例）

#### 2. 现状与缺陷判定
```text
现状：无 on_error=stop/skip/retry 的分支用例，无取消路径用例
      → B-05（终止）、B-20（skip 状态）、B-33/B-35（取消语义）修复后无法验证。
```
- 缺陷类型：**【缺失实现】**（测试覆盖缺口）
- 阻断后果链：失败/重试/取消语义修复无回归网 → **P1：无法验证修复效果**

#### 3. 修改方案
**B. 新建型**（裁定 Q8／F7：与 `F-07`／`B-05` 合并立项）
- 新建位置：`rpa_engine/tests/test_engine_failure_paths.py`
- 骨架（用例清单）：
  ```text
  test_stop_policy_raises         stop 策略抛 ExecutionError
  test_skip_policy_partial        skip → status == "partial"（B-20）
  test_retry_exhausted_raises     重试耗尽 → ExecutionError（B-26）
  test_cancel_before_step         步骤间取消 → cancelled
  test_cancel_during_loop         循环内取消 → cancelled（B-33）
  test_real_failure_not_cancelled 真实失败不被标 cancelled（B-35）
  test_output_tables_after_cleanup 清理后返回值不含死表号（B-36）
  ```
- **A/C**：不适用

#### 4. 约束
- 本次不可动：既有测试文件
- 规约：`rpa_engine/tests/` 豁免通道

#### 5. 验证
- 用例构造：新增用例本身
- 期望输出：用例数增加且全绿
- 失败判据：新用例失败
- 自证方式：`unittest discover`

#### 6. 风险与回滚
- 风险：取消路径需构造 `cancel_check` 桩（须设计简单回调）
- 回滚：删除新增文件
- 降级：不适用

#### 7. 验收标准
- [ ] 失败/重试/取消/清理路径均有用例
- [ ] 用例数上升且全绿
- [ ] 与 `B-05`／`B-20`／`B-26`／`B-33`／`B-35`／`B-36` 一一对应

#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/tests/`（现无失败/重试/取消路径用例）
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

---

### B-44 [原编号: P1-6] 部分列处理失败仍报成功（机制＝§5 根因 2，与 G-08 重叠）

> 等级：P1 ｜ **批次：B 类（与 B-18 合并）** ｜ 判定：**【逻辑错误】**

#### 1. 定位
- 文件：`rpa_engine/ops/step_executor.py`（L296-316）／`rpa_engine/ops/table_schema.py`

#### 2. 现状与缺陷判定
```python
# step_executor.py L299（丢弃返回值 —— 与 B-18 同一行）
        entry["func"](**call_args)
```
- 缺陷类型：**【逻辑错误】**（与 `B-18` **同一机制**：`ops` 以 return bool 表达成败，`step_executor` 丢弃）
- 阻断后果链：部分列处理失败 → 返回 False 被丢 → `success=True` → 用户看到 ✅ 而数据不完整 → **P1：静默错误结果**

#### 3. 修改方案
**A. 修改型**（裁定 Q8：与 `G-08`／`B-18` 合并）
- 改动点 1：**见 `B-18` 改动点 1-2**（同一处改动，本项不另设改动点）
- 改动点 2：逐操作复核"以 bool/int 表达成败"的 ops 清单（`rename_columns`／`convert_dtype`／其它），确保返回值语义被统一消费
- **B/C**：不适用

#### 4. 约束
- 本次不可动：9 分支结构；参数白名单
- 规约：裁定 Q8（`P1-6`↔`G-08` 合并）；裁定 G2（`convert_dtype` 须真的返回 False）

#### 5. 验证
- 用例构造：构造"部分列处理失败"的 `convert_dtype`／`rename_columns`
- 期望输出：步骤报失败（或 partial）
- 失败判据：报成功
- 自证方式：`progress_callback`；临时库对比

#### 6. 风险与回滚
- 风险：与 `B-18` 同批改动，回归面相同
- 回滚：同 `B-18`
- 降级：同 `B-18`

#### 7. 验收标准
- [ ] 部分列失败不再报成功（与 `B-18` 同批验收）
- [ ] 所有以返回值表达成败的 ops 均被消费
- [ ] 回归全绿
#### 8. Agent 执行指引
- **本改造项的上下文范围**：仅需读取 `rpa_engine/ops/step_executor.py`（L296-316）／`rpa_engine/ops/table_schema.py`
- **不需要读取**：其它改造项条目；`engine/executor.py` 的步骤分发与线程模型（除本项明确列出者）；GUI 布局与样式；`build/**`；`tests/**`（除本项新增测试外）
- **执行步骤概要**：① 按本项「3. 修改方案」逐改动点落地（**改前/改后为语义示意**，见 Part 0 §0.2.1，禁止机械文本匹配）；② 按本项「5. 验证」构造用例；③ 逐项勾选本项「7. 验收标准」
- **完成判定**：本项「7. 验收标准」全部勾选，且「5. 验证」的失败判据均未出现
- **完成后输出**：`[SUB_AGENT_COMPLETE]` ＋ 交付物清单（文件路径 ＋ 关键函数签名）
- **阻塞时输出**：`[SUB_AGENT_BLOCKED]` ＋ 原因 ＋ 已尝试方案 ＋ 建议选项
- **文件冲突时输出**：`[SUB_AGENT_CONFLICT]` ＋ 冲突文件 ＋ 双方改动摘要

### 3.3 P2 体验与格式（5 项，精简四段）

> **本轮不施工（人工裁定 2026-10-19）** —— 本组 5 项**本轮仅登记、不施工**（原文一字未删，合 `AGENTS.md` §7.1）。分类见 Part 3 头部台账对应行；如需施工请人工逐项立项。
>
> **本组提示**：含真机依赖项与越界项者**已在台账标注并移出施工清单**（原文保留）；**本轮可施工项以 Part 3 头部台账为准**；`§0.3` 的 `P-2` 为**活前置，不动**。

> 四段口径：**存在性判定** ／ **缺陷类型** ／ **为何本次不施工** ／ **触发条件**（将来施工的入口）。

#### B-45 [原编号: F-10] [P2] 非中文系统下旧 exe 无法回滚
- **存在性判定**：✅ 已存在（`build.bat` 的 locale 切片段与备份/覆盖三段，含 `echo [INFO] Old exe backed up` 无条件输出）
- **缺陷类型**：**【缺少容错】**（时间戳依赖 locale 切片 → 非中文系统下备份失败但脚本仍报成功）
- **为何本次不施工**：属**构建脚本**域（`build.bat`），且构建由人工接管（裁定 R2）；不在"预处理＋导入接入"范围
- **触发条件**：人工执行构建时发现备份未生成 → 修 `build.bat`（locale 无关时间戳 ＋ `move` 后检查 `errorlevel`），须在非中文 locale 下验证
- **修改方案概要**（供将来实施者直接开工，无需回读源码）
  - 目标文件：`build.bat`（仓库根）
  - 目标位置：备份/覆盖三段（`move` 旧 exe 到 `backup/`、生成带时间戳的文件名、覆盖新 exe）
  - 核心改动逻辑：① 时间戳改为 **locale 无关**取法（不依赖 `%date%` 的本地化格式）；② `move` 之后**显式**检查 `errorlevel`，非 0 即报错并以非 0 退出，**不得**继续执行覆盖；③ 删除"无条件 `echo [INFO] Old exe backed up`"式的假成功输出
  - 关键片段示意（**语义示意**，非精确 diff）：
    ```bat
    for /f %%I in ('wmic os get localdatetime ^| findstr "^[0-9]"') do set TS=%%I
    set TS=%TS:~0,8%_%TS:~8,6%
    move "%DIST%\RPA_Workflow_v3.exe" "%BAK%\RPA_Workflow_v3_%TS%.exe" >nul
    if errorlevel 1 ( echo [ERROR] 旧 exe 备份失败，已中止 & exit /b 1 )
    ```
  - 完成判定：在 `zh-CN` 与 `en-US` 两种 locale 下各跑一次构建，均生成 `backup/RPA_Workflow_v3_<yyyyMMdd_HHmmss>.exe` 且无假成功输出

#### B-46 [原编号: F-11] [P2] 步骤超时只进日志 → 文员只能干等
- **存在性判定**：✅ 已存在（`engine/executor.py` 计时告警段，仅 `logger.warning`，`step_timeout_sec` 默认 600）
- **缺陷类型**：**【缺少容错】**（不进 `progress_callback`，用户界面无提示）
- **为何本次不施工**：涉及执行期进度回调语义（`executor` 的 `progress_callback` 契约），属引擎调度域（§0.1 ❌ 不动）；且 600s 阈值对导入链路无直接影响
- **触发条件**：需要用户可见的超时提示时 → 在 `executor` 计时段追加回调（须同步 `worker` 与 GUI 展示）
- **修改方案概要**（供将来实施者直接开工）
  - 目标文件：`rpa_engine/engine/executor.py`（计时段）＋ `rpa_engine/gui/worker.py`（回调转发）
  - 目标位置：步骤计时告警段（现状仅 `logger.warning`，`step_timeout_sec` 默认 600）
  - 核心改动逻辑：超时判定命中时**追加一次** `progress_callback(step.step_id, "timeout", <中文文案>)`；`worker.progress` 增 `state == "timeout"` 分支 → 复用 `step_failed` 文案通道或新增信号，把文案送到 GUI 进度框/状态栏（**不中断执行**，仅提示）
  - 关键片段示意：
    ```python
    if progress_callback is not None and elapsed > timeout_sec:
        progress_callback(
            step.step_id, "timeout",
            f"步骤 [{step.step_id}] 已运行 {elapsed:.0f}s，超过阈值 {timeout_sec}s；"
            f"如长时间无进展，可点击终止并改小数据量后重试")
    ```
  - 完成判定：构造一个耗时超阈值的步骤，界面出现上述中文文案且执行**不中断**（与 `B-05` 的置灰语义不冲突）

#### B-47 [原编号: G-12] [P2] 新建模板路径崩溃窗口留半截 JSON 且无法删除
- **存在性判定**：✅ 已存在（`gui/user_template_manager.py` 保存路径，`tmp_path == target_path` 分支）
- **缺陷类型**：**【缺少容错】**（写一半崩溃后残留不可读 JSON）
- **为何本次不施工**：属模板管理域（非导入链路）；`[UNVERIFIED]` 具体行号未读
- **触发条件**：模板功能被纳入修复批次时 → 改为"临时文件 ＋ 原子替换"（复用 `B-09` 的写法）
- **修改方案概要**（供将来实施者直接开工）
  - 目标文件：`rpa_engine/gui/user_template_manager.py`
  - 目标位置：模板保存路径（`save` 与 `tmp_path == target_path` 分支；精确行号见 Part 0 §0.7 第 17 行）`[UNVERIFIED]`
  - 核心改动逻辑：改为「先写 `~{name}.tmp` → `os.replace(tmp, target)`」原子替换（与 `B-09` 同一写法）；`except` 分支内 `tmp.unlink(missing_ok=True)`；启动时清理残留 `~*.tmp`（避免崩溃残留堆积）
  - 关键片段示意：
    ```python
    tmp_path = target.with_name(f"~{target.name}.tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_path, target)          # 原子替换；中途失败只留 .tmp
    ```
  - 完成判定：写入过程中强杀进程 → 目录内只残留 `~*.tmp`，且**原模板文件内容完好**、下次启动能被清理

#### B-48 [原编号: H-12] [P2] `LIKE` 的 `%`/`_` 被转义成字面量 → 模糊匹配等于
- **存在性判定**：✅ 已存在（`ops/sql_safety.py` LIKE 转义分支，注释明写"按字面匹配"）
- **缺陷类型**：**【有意设计】**（非缺陷；`sql_safety` 注释自证）
- **为何本次不施工**：裁定明确定调——维持"按字面匹配"，通配符开关**不在本轮范围**
- **触发条件**：人工裁定"加通配符开关"后 → 在 `build_where` 的 LIKE 分支增加可选转义开关（默认保持现状）
- **修改方案概要**（供将来实施者直接开工）
  - 目标文件：`rpa_engine/ops/sql_safety.py`
  - 目标函数：`build_where` 的 `LIKE` 转义分支（注释现明写"按字面匹配"＝有意设计）
  - 核心改动逻辑：新增关键字开关 `like_escape: bool = True`（**默认 True ＝保持现状**）；`False` 时不转义 `%`／`_`，使其恢复通配语义；该开关同时纳入 JSON `global.like_escape` 与 GUI 条件框提示文案
  - 关键片段示意：
    ```python
    val = str(value)
    if like_escape:
        val = val.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    params.append(f"%{val}%")
    ```
  - 完成判定：开关 `True` 时 `LIKE 'A_B'` 只命中字面 `A_B`；`False` 时命中 `AxB`／`A1B` 等；**两种模式下既有 118 用例均通过**
  - **前置**：本项在 problem.md 中被定为「有意设计」，加开关属**能力变更** → 须先有独立人工裁定才可实施

#### B-49 [原编号: H-26] [P2] 导出路径被静默改写后缀
> **[本轮不施工]** 人工裁定（2026-10-19）：体验优化、非功能阻断，建议后续单独立项；分类＝`[BLOCKED-越界＋本轮不施工]`（③：`ops/exporter.py::export_table` 属 BUILTIN_OP `export`）—— 见 Part 3 头部台账。
- **存在性判定**：✅ 已存在（`ops/exporter.py` L66-67 `out.with_suffix(".xlsx")`）
- **缺陷类型**：**【逻辑错误】**（`报表.csv` → `报表.xlsx`，界面零提示；与 `B-29` 交叉显示不一致）
- **为何本次不施工**：属导出侧体验问题；本次 P3/P5 的导出改造聚焦"内存/原子性/截断告知"，不改后缀语义
- **触发条件**：与 `B-03`／`B-09` 同批处理导出侧时 → 改为"提示用户后缀将被改写"或"按用户后缀处理"
- **修改方案概要**（供将来实施者直接开工）
  - 目标文件：`rpa_engine/ops/exporter.py`
  - 目标位置：`export_table` 的后缀处理（L66-67 `out.with_suffix(".xlsx")`）
  - 核心改动逻辑（**本版默认口径**）：后缀不是 `.xlsx` 时**不再静默改写**，改为抛中文 `ValueError`，使"所见即所得"（D10）与 R1 同域一致；若要保留"按用户后缀处理"的能力，须先由人工裁定（见交付报告 Q-2）
  - 关键片段示意：
    ```python
    out = Path(output_path)
    if out.suffix.lower() != ".xlsx":
        raise ValueError(
            f"export_table: 导出文件必须为 .xlsx，当前为 "
            f"{out.suffix or '（无后缀）'}，请修改导出路径后重试")
    ```
  - 完成判定：导出路径填 `报表.csv` → 弹出上述中文提示且**不生成任何文件**；填 `报表.xlsx` → 正常导出，且既有导出用例全绿

### 3.4 P3 本次范围外（30 项，精简四段）

> **本轮不施工（人工裁定 2026-10-19）** —— 本组 30 项**本轮仅登记、不施工**（原文一字未删，合 `AGENTS.md` §7.1）。分类见 Part 3 头部台账对应行；如需施工请人工逐项立项。
>
> **本组提示**：含真机依赖项与越界项者**已在台账标注并移出施工清单**（原文保留）；**本轮可施工项以 Part 3 头部台账为准**；`§0.3` 的 `P-2` 为**活前置，不动**。

#### B-50 [原编号: B-02] [P3] 依赖未锁定；`requirements.lock` 不存在
- **存在性判定**：❌ 不存在（`requirements.txt` 头注指向不存在的 lock）
- **缺陷类型**：**【缺失实现】**（环境可复现性缺口）
- **为何本次不施工**：属环境/交付域，与预处理＋导入接入无关；裁定 Q1 已定"方案 C（裸 `pip freeze`）"，须人工执行且注意环境名**下划线**（`CPS-GPES_RPA-py311`）
- **触发条件**：人工生成 lock 时 → `conda run -n CPS-GPES_RPA-py311 pip freeze` 原样写入 ＋ 头部注明"含 2 个已声明废弃包，勿安装"

#### B-51 [原编号: G-5（台账）] [P3] 写入原子性与空壳表防护零覆盖（结构性缺口）
- **存在性判定**：⚠️ 部分存在（守卫缺失；`A-15`／`A-16` 为其具体表现）
- **缺陷类型**：**【缺失实现】**（守卫体系缺口）
- **为何本次不施工**：裁定 Q2 明定"**先出方案再裁定**"；未裁定前**不得实施**（台账纪律 6）。本项＝`A-15`／`A-16` 的**方案前置**
- **触发条件**：Agent 出 `G-5` 方案 → 人工裁定 → 方可实施 `A-15`／`A-16`（**优先级最高**，因它阻塞 A 类两项）

#### B-52 [原编号: G-7（台账）] [P3] 依赖 ↔ 代码 ↔ 打包无交叉校验守卫
- **存在性判定**：❌ 不存在（无自动交叉校验；`A-17` 即其失守实例）
- **缺陷类型**：**【缺失实现】**（守卫体系缺口）
- **为何本次不施工**：裁定 Q2 同 `B-51`（先出方案再裁定）；且 `A-17` 已可用"人工核对 spec／requirements"替代
- **触发条件**：`G-5` 方案落地后 → 再出 `G-7` 方案（建议检查项：每个 `import` 的模块都在 `requirements.txt` 与 `spec hiddenimports` 内）
- **⚠️ 勿与** §4 的 `G-07` 混同（后者＝`B-12` 的 `merge_tables` 守卫）

#### B-53 [原编号: D4] [P3] 弃用口径前后端不闭合
- **存在性判定**：❌ 不存在（引擎侧无弃用字段；手写 JSON 仍可执行已弃用操作）
- **缺陷类型**：**【缺失实现】**（前后端口径不一致）
- **为何本次不施工**：裁定 Q3 定为 W-22 **第一批**（与 `B5` 同批），须人工逐项立项；本计划已登记但需独立批次
- **触发条件**：W-22 第一批开工时 → `engine/validator.py` 增加弃用字段校验（与 `B-13` 的状态口径同源）

#### B-54 [原编号: B1] [P3] 中文名双源无守卫
- **存在性判定**：❌ 不存在（`BUILTIN_OPS[k]["description"]` ↔ `StepMeta.display` 两处来源）
- **缺陷类型**：**【缺失实现】**（记录表/守卫缺口）
- **为何本次不施工**：属功能函数记录表域（`docs/function-spec-rules.md`），不在预处理＋导入接入范围
- **触发条件**：功能函数优化批开工前（须先加载专章）→ 加守卫单测断言两源一致

#### B-55 [原编号: B2] [P3] `STEP_KIND` 值域无守卫
- **存在性判定**：❌ 不存在（错值静默回退 `sequential`）
- **缺陷类型**：**【缺少容错】**
- **为何本次不施工**：同 `B-54`（记录表域）
- **触发条件**：功能函数优化批 → `gui/models.py` 加值域校验 ＋ 单测

#### B-56 [原编号: B3] [P3] `OUTPUT_OPS` ↔ `STEP_KIND(fork∪merge)` 等式无守卫
- **存在性判定**：❌ 不存在
- **缺陷类型**：**【缺失实现】**（守卫缺口）
- **为何本次不施工**：同 `B-54`
- **触发条件**：功能函数优化批 → 加等式守卫单测

#### B-57 [原编号: B4] [P3] 孤儿表单类无反向守卫
- **存在性判定**：❌ 不存在（`gui/forms.py` 表单注册无反向校验）
- **缺陷类型**：**【缺失实现】**
- **为何本次不施工**：同 `B-54`；且本次不改 GUI 布局与表单结构
- **触发条件**：功能函数优化批 → 加"目录键 ↔ 表单类"双向断言

#### B-58 [原编号: B6] [P3] `keywords` 非空无守卫
- **存在性判定**：⚠️ 部分存在（自检仅判 tuple 类型，未判非空）
- **缺陷类型**：**【缺少容错】**
- **为何本次不施工**：同 `B-54`
- **触发条件**：功能函数优化批 → 自检项扩展

#### B-59 [原编号: B7] [P3] 参数白名单反向覆盖无守卫
- **存在性判定**：⚠️ 部分存在（白名单过滤已有 L196-201，反向覆盖无守卫）
- **缺陷类型**：**【缺失实现】**
- **为何本次不施工**：涉及 `step_executor` 白名单（与本次 A 类改动同文件，但属不同语义面，避免同批互相干扰）
- **触发条件**：功能函数优化批 → 加"白名单 ⊇ 目录 param_keys"单测

#### B-60 [原编号: B8] [P3] 前端键 `output_mode` 无集中声明（散落 4 处）
- **存在性判定**：❌ 不存在（散落多处）
- **缺陷类型**：**【缺失实现】**（双源风险）
- **为何本次不施工**：属功能函数前端键域；本次不改前端交互形态
- **触发条件**：功能函数优化批 → 集中声明常量供各处引用

#### B-61 [原编号: C1] [P3] `StepMeta.icon` 全为空串、零消费者
- **存在性判定**：⚠️ 部分存在（字段在、值为空、无消费者）
- **缺陷类型**：**【缺失实现】**（记录表字段缺口）
- **为何本次不施工**：纯记录表缺口，无功能影响
- **触发条件**：功能函数优化批 → 决定"补齐图标"或"删除字段"

#### B-62 [原编号: C2] [P3] `target_param`／`match_param` 零消费者休眠元数据
- **存在性判定**：⚠️ 部分存在（字段休眠；v7 记载 architecture 已修正该文档失实）
- **缺陷类型**：**【缺失实现】**（记录表字段缺口）
- **为何本次不施工**：同 `B-61`
- **触发条件**：功能函数优化批 → 决定启用或删除

#### B-63 [原编号: D1] [P3] 无 `inputs.extra_min` 字段
- **存在性判定**：❌ 不存在（专章记录表缺该字段）
- **缺陷类型**：**【缺失实现】**（表达能力不足）
- **为何本次不施工**：记录表结构变更须走专章 §5.5 登记清单（13 项），属独立批次
- **触发条件**：功能函数优化批 → 按专章登记清单补齐

#### B-64 [原编号: D2] [P3] 无 `params_schema`
- **存在性判定**：❌ 不存在
- **缺陷类型**：**【缺失实现】**
- **为何本次不施工**：同 `B-63`
- **触发条件**：功能函数优化批 → 按专章登记清单补齐

#### B-65 [原编号: D3] [P3] 无「可覆盖操作集」字段（`_OVERWRITABLE` 未落地）
- **存在性判定**：❌ 不存在
- **缺陷类型**：**【缺失实现】**
- **为何本次不施工**：同 `B-63`；**注意**：本项落地后与 `B-20`（覆盖原表状态）、`B-21`（画布口径）有关联，须协调
- **触发条件**：功能函数优化批 → 按专章登记清单补齐

#### B-66 [原编号: E1] [P3] 守卫规则双写：自检 15 条仅 5 条有单测镜像
- **存在性判定**：⚠️ 部分存在（自检 15 条规则，单测镜像仅 5 条）
- **缺陷类型**：**【缺失实现】**（测试缺口）
- **为何本次不施工**：属守卫测试域；本计划已在 `B-42`／`B-43` 补操作与失败路径单测，守卫镜像另批
- **触发条件**：功能函数优化批 → 为剩余 10 条自检规则补单测

#### B-67 [原编号: E3] [P3] 「9 项」口径散落（3 处等值断言 ＋ 自检下限守卫）
- **存在性判定**：⚠️ 部分存在（3 处等值断言与多处非门禁口径）
- **缺陷类型**：**【逻辑错误】**（硬编码计数口径，功能增删时易漂移）
- **为何本次不施工**：本次**不新增/删除功能函数**（只做预处理与链路修复），无口径漂移风险
- **触发条件**：任何功能函数增删时 → 同步修改 3 处「9」等值断言 ＋ `app.py` 下限守卫（专章 §5.5 登记清单）

#### B-68 [原编号: A4] [P3] 「9 项」非门禁口径面（10+ 处）
- **存在性判定**：⚠️ 部分存在（散落多处注释/文案）
- **缺陷类型**：**【逻辑错误】**（同类口径漂移）
- **为何本次不施工**：同 `B-67`
- **触发条件**：与 `B-67` 同批统一改为引用常量

#### B-69 [原编号: P2-1] [P3] 默认参数手写清单（与 B9 同源）
- **存在性判定**：⚠️ 部分存在（`gui/models.py::default_params` 手写）
- **缺陷类型**：**【缺失实现】**（双源；与 `B-41` 同源）
- **为何本次不施工**：`B-41` 已覆盖其核心后果（取值相反）；"清单手写"的工程化改造留待功能函数批
- **触发条件**：`B-41` 落地后 → 评估是否改为从目录自动派生

#### B-70 [原编号: P2-2] [P3] 分发 9 分支手写
- **存在性判定**：✅ 已存在（`step_executor.py` 9 分支）
- **缺陷类型**：**【已裁定不触红线】**（结构性，非缺陷；裁定 P2-2）
- **为何本次不施工**：已裁定"不改 9 分支结构"；本次所有改动都必须在既有分支内完成
- **触发条件**：若要重构须人工重新裁定（本计划不做）

#### B-71 [原编号: N-01] [P3] pandas 不能从 lock 中剔除
- **存在性判定**：✅ 已存在（`pd.read_excel` 为 `.xlsx` 主链路依赖）
- **缺陷类型**：**【环境事实】**（非缺陷）
- **为何本次不施工**：属依赖锁定域（`B-50`）；本条是"禁令性事实"（推翻手工精简 lock 的方案）
- **触发条件**：生成 lock 时**必须**包含 pandas（不得手工删）

#### B-72 [原编号: N-02] [P3] 废弃包仍在环境里（`python-docx`／`python-pptx`）
- **存在性判定**：✅ 已存在（conda 环境内仍在；`requirements.txt` 已移除声明）
- **缺陷类型**：**【环境事实】**（环境与声明不一致）
- **为何本次不施工**：裁定：**不卸载**（避免影响其他工具）；仅在 lock 头注明
- **触发条件**：生成 lock 时 → 头部注明"含 2 个已声明废弃包，勿安装"

#### B-73 [原编号: N-03] [P3] conda 环境名是下划线；部分命令清单写成连字符
- **存在性判定**：✅ 已存在（`requirements.txt` 头注与命令清单曾用连字符 → `EnvironmentLocationNotFound`）
- **缺陷类型**：**【逻辑错误】**（口径不一致，照抄命令会卡死）
- **为何本次不施工**：属文档/命令口径；本次不新增/修改命令清单（本计划内命令一律用**下划线**）
- **触发条件**：任何回写命令清单时 → 统一 `CPS-GPES_RPA-py311`

#### B-74 [原编号: N-04] [P3] 版本漂移（pandas 3.0.5 无上界；PyQt5 5.15.11）
- **存在性判定**：✅ 已存在（清单仅 `>=2.0`，无上界）
- **缺陷类型**：**【缺少容错】**（口径失准、升级风险）
- **为何本次不施工**：属依赖域；本次**不引入新依赖**，也无升级动作
- **触发条件**：`B-50` 生成 lock 时 → 给 pandas 加上界并回写实际实测版本

#### B-75 [原编号: N-05] [P3] `requirements.txt` 被外部插入裸 `xlrd`；打包侧未动
- **存在性判定**：✅ 已存在（10-05 外部插入；`spec` 仍无 `'xlrd'`）
- **缺陷类型**：**【缺少容错】**（本项是 `A-17` 的**环境侧证据**）
- **为何本次不施工**：其实质阻断面已在 `A-17`／`A-02` 处置；本项仅作事实留痕
- **触发条件**：与 `A-17` 同批（补版本约束 ＋ `spec hiddenimports`）

#### B-76 [原编号: §8.2-1] [P3] `ops/exporter.py` 注释谎报「内存占用恒定，大表导出安全」
- **存在性判定**：✅ 已存在（L9-11 注释）
- **缺陷类型**：**【逻辑错误】**（注释与行为不符）
- **为何本次不施工**：其**行为侧**由 `B-03` 修；注释更正随 `B-03` 改动点 4 一并完成
- **触发条件**：`B-03` 施工时同步更正（裁定 G14：改代码时须一并更正注释）

#### B-77 [原编号: §8.2-2] [P3] `ops/sqlite_manager.py` 声称「事务内」
- **存在性判定**：✅ 已存在（L128 注释）
- **缺陷类型**：**【逻辑错误】**（注释与 legacy DDL 语义不符）
- **为何本次不施工**：随 `A-15`（待裁定）施工时同步更正
- **触发条件**：`A-15` 落地时同步更正（裁定 G14）

#### B-78 [原编号: §8.2-3] [P3] `ops/sqlite_manager.py` 声称「写入失败（事务自动回滚）」
- **存在性判定**：✅ 已存在（L140 docstring）
- **缺陷类型**：**【逻辑错误】**（与 DDL 自动提交事实不符，已在 `A-15` 标注）
- **为何本次不施工**：随 `A-15` 同步更正
- **触发条件**：`A-15` 落地时同步更正（裁定 G14）

#### B-79 [原编号: §8.2-4] [P3] `page_input_selection.py` 预览摘要未说明「导入时不会填充」
- **存在性判定**：✅ 已存在（预览摘要文案）
- **缺陷类型**：**【逻辑错误】**（提示与真实行为不符，与 `A-05` 联动）
- **为何本次不施工**：`A-05` 施工后"预览与导入是否填充"的口径会变化 → 文案须在 `A-05` 落地后再改（避免改两次）
- **触发条件**：`A-05`／`REQ-H9` 落地后同步更新摘要文案（裁定 G14）

---

## Part 4 · 新增/修改文件清单与接口契约

### 4.1 新建文件（共 1 个）

#### 4.1.1 `rpa_engine/ops/excel_normalizer.py`

**完整骨架**

```python
"""
rpa_engine/ops/excel_normalizer.py

Layer 0 — Excel 数据表规范化模块（ImportData 修复轮新增）。

职责：把「Excel 数据表」规范化为「标准数据表」（表头在第 1 行、单元格独立且为纯值），
     并产出元数据与处理报告，支撑 Excel ↔ SQLite 的无损互转。

处理管线（顺序固定，不得颠倒）：
    R2 表头行校验 → R3 合并单元格拆分 → R4 公式兜底 → H4 错误值 → R5 超链接
    → H3 布尔 → R7 内容清洗 → A-08 空值策略 → A-04 类型推断
    → H1 列名归一 → H5 空列/尾部空行 → H7 精度检测

依赖库：pandas>=2.0, openpyxl>=3.1, re（标准库）—— 不引入任何新依赖。
约束：本模块**不得**自行创建 SQLite 连接（AGENTS.md §2.2 条 4）；所有 DB 操作由调用方
      传入 conn（如 REQ-H9 的元数据表写入）。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

NORMALIZE_RULES_VERSION = "v1"      # 规则版本；规则变更须递增（使 H10 缓存失效）
MERGED_SPLIT_LIMIT = 10_000         # 单表合并区上限（超过则只告警不拆分）


@dataclass
class NormalizeResult:
    """规范化结果（表的唯一输出载体）。"""
    dataframe: "Any"                    # pd.DataFrame：表头在第 1 行、单元格为纯值
    meta: Dict[str, Dict[str, Any]] = field(default_factory=dict)
        # 逐列元数据：col -> {original_type, was_formula, was_hyperlink,
        #                    was_merged, all_empty, normalized, cleaned}
    report_entries: List[Dict[str, Any]] = field(default_factory=list)
        # 处理报告条目：(sheet, 位置, 原始内容, 处理方式, 结果)
    warnings: List[str] = field(default_factory=list)
        # 用户可见告警（人话；禁技术词）


def normalize_sheet(
    file_path: str,
    sheet_name: str,
    header_row: int,
    *,
    sheet_info: Optional[List[Dict[str, Any]]] = None,
    max_significant_digits: int = 5,
    na_policy: str = "preserve",
    enable_cache: bool = True,
    progress: Optional[Any] = None,
) -> NormalizeResult:
    """把指定 sheet 规范化为标准数据表。

    Args:
        file_path: 临时区 xlsx 路径。
        sheet_name: 目标 sheet。
        header_row: 表头行号（1 起始）。
        sheet_info: 已扫描的 sheet 元信息（复用，避免重复开簿）。
        max_significant_digits: R6 阈值（默认 5，可由 JSON global 覆盖）。
        na_policy: "preserve"（默认）｜"pandas"（R7／A-08 的空值口径）。
        enable_cache: 是否启用 H10 幂等缓存（仅缓存元数据与告警，不缓存数据）。
        progress: 可选进度回调（每阶段一次）。

    Returns:
        NormalizeResult。

    Raises:
        ValueError: 表头行为空（REQ-R2）／列名含禁止字符（A-03）／表不存在。
        FileNotFoundError: 文件不存在。
        RuntimeError: 取消（沿用导入链的取消语义，见 B-33）。
    """
```

**职责边界**
- **负责**：单元格/表级规范化、元数据产出、处理报告产出、幂等缓存（仅元数据）。
- **不负责**：Excel 读取（复用 `excel_preprocessor.read_excel_sheet` 的能力）、SQLite 建表与写入（交 `sqlite_manager`）、异常话术翻译（交 `gui/error_messages`）、重试与取消策略（交 `engine/executor`）。
- **是否需登记 `BUILTIN_OPS`／功能函数记录表**：**否**。理由：本模块是 **Layer 0 基础设施**，不属「功能函数三形态一体」（不进 JSON `steps[]`、不出现在 DAG 节点），故**不需要**按 `docs/function-spec-rules.md` §5.5 的 13 项登记清单落地；但**必须**在 `spec` 的 `hiddenimports` 登记（见 §4.3）。

### 4.1b 新建文件（测试，共 2 个）

| 新建文件 | 用途 | 关联条目 |
|---|---|---|
| `rpa_engine/tests/test_ops_contracts.py` | 逐操作契约用例 ＋ 三个解析器一致性用例 | B-42 |
| `rpa_engine/tests/test_engine_failure_paths.py` | 失败/重试/取消/清理路径用例 | B-43 |

> 说明：这两项原列在 §4.2 内，本版移出至本节，使 §4.2 **只含被修改的既有文件**（计数见 §4.2b）。

### 4.2 修改文件清单（共 29 个）

| 文件 | 改动点 | 签名/返回值是否变化 | 关联条目 |
|---|---|---|---|
| `rpa_engine/ops/excel_preprocessor.py` | ① `validate_and_copy` L65 `copy2`→`copyfile`＋`os.utime`；② 同名跨后缀查重（L58-63）；③ `ensure_xlsx` L117-119 产物加序号；④ `read_excel_sheet` L210-215 追加 `keep_default_na=False, na_values=[]`；⑤ 新增 `read_header_row()` | ❌ 四个既有函数签名与返回值**不变** | A-11、A-12、A-18、A-08、REQ-R2 |
| `rpa_engine/ops/table_importer.py` | ① L76 改调 `normalize_sheet`；② L76 前插表头行全空预检与列名/重复列名校验；③ L84-89 告警段改调 `dedup_columns` | ❌ `import_excel_table(...) -> int` 不变 | A-04、A-03、REQ-R2、REQ-H1 |
| `rpa_engine/ops/sqlite_manager.py` | 新增 `import_dataframe_atomic()`（A-15，**待裁定**）；更正 L128／L140 注释 | ❌ `import_dataframe` 不变（新增函数） | A-15、B-77、B-78 |
| `rpa_engine/ops/exporter.py` | ① L82 `Workbook(write_only=True)`；② L83-84 改 `create_sheet`；③ L102 临时文件＋`os.replace`；④ L98-99 超长单元格检测告警；⑤ 更正 L9-11 注释 | ❌ `export_table(...) -> int` 不变 | B-03、B-09、B-34、B-76 |
| `rpa_engine/ops/sql_safety.py` | IN／NOT IN 分支收到标量时抛中文错误（**不改白名单与转义语义**） | ❌ 不变 | B-14 |
| `rpa_engine/ops/mapping_matcher.py` | ① 建表前插入输出行数上限校验；② `full_join` 改 disjoint 分解（替换 `UNION`）；③ `DROP` 前加活表守卫；④ 更正 docstring | ❌ `match_tables(...) -> int` 不变 | B-04、B-24、B-12 |
| `rpa_engine/ops/filter_dedup.py` | `DROP TABLE IF EXISTS` 前加活表守卫（L81／L155 两处） | ❌ 不变 | B-12 |
| `rpa_engine/ops/aggregator.py` | 同上（产表处） | ❌ 不变 | B-12 |
| `rpa_engine/ops/table_lifecycle.py` | ① `merge_tables` 加 `dst ∈ 源表` 与重复参与守卫；② `DROP` 前加活表守卫 | ❌ `merge_tables` 不变 | B-12、B-25 |
| `rpa_engine/ops/table_schema.py` | ① `convert_dtype` 加 `CAST`＋失败跳过并**如实返回 bool**；② 复核 `rename_columns` 的部分失败返回 False | ❌ 两个函数签名与 bool 返回类型不变 | B-19、B-18 |
| `rpa_engine/ops/step_executor.py` | ① L299 接收返回值并据产出类型判定 `success`；② 各分支回退值改用目录默认值（B-41）；③ 自动表名防撞名（B-37）；④ 4 个分支补传 `cancel_check`（B-05） | ❌ `execute_step(...) -> Dict[str, Any]` 键集合不变 | B-18、B-41、B-37、B-05、B-44 |
| `rpa_engine/engine/executor.py` | ① `ensure_input_tables` L92 判据加行数（**待裁定**）与取消识别；② skip 置 `partial`；③ `except ExecutionError` 删二次取消判定；④ 清理后过滤返回字典 | ⚠️ `execute_workflow` 返回值新增 `status="partial"` 取值与 `cleaned_tables` 键（**加法变更**） | A-16、B-33、B-20、B-35、B-36 |
| `rpa_engine/engine/validator.py` | ① 派生号注册改为有条件；② 追加 `step_id` 唯一性校验 | ❌ 签名不变；抛出异常仍为 `ValidationError` | B-38、B-22 |
| `rpa_engine/engine/parser.py` | ① `retry_count` 安全解析（`ParserError`）；② `schema_version` 类型严格 | ❌ 不变 | B-26、B-39 |
| `rpa_engine/gui/page_input_selection.py` | ① `get_entries` 导出 `source_path`；② `_on_add_files` 异常元组扩容＋`finally` 复位按钮＋人话化；③ 新增 `prune_copies()`；④ 文件头补 `import zipfile`／`translate_error` | ❌ 既有方法签名不变（新增一个方法） | A-01、A-10、A-02、A-13 |
| `rpa_engine/gui/main_window.py` | ① 导入调用点改 `source_path` 优先；② 失败清单带类名＋结构改为字典并落盘；③ 身份三元组比对；④ L800-801 收尾顺序交换＋抽 `_shutdown()`；⑤ 会话库名带 PID；⑥ 陈旧会话清理加进程判定；⑦ 启动清理顺序调整；⑧ 进度文案预告 | ⚠️ `failed` 变量类型由 `List[str]` 改 `List[Dict[str, str]]`（内部变量，非对外契约） | A-01、A-10、A-13、A-19、B-10、B-02、A-11、A-09 |
| `rpa_engine/gui/models.py` | ① `to_dict` 的 `source.file` 用 `source_path`；② 新增 `active_catalog_keys()`；③ `collect_file_stats` 加存在性与状态过滤；④ 模板载入重新分配 `step_id` | ⚠️ `active_catalog_keys()` 为新增函数；`collect_file_stats` 返回结构不变 | A-10、B-13、B-29、B-22 |
| `rpa_engine/gui/forms.py` | ① `_OPS_ORDER` 补 `NOT IN` 且置前；② list 值解析/回填往返一致；③ 三个解析器统一拒绝式；④ 导出路径已存在提示；⑤ 条件框日期格式提示 | ❌ 三个解析器签名不变（返回结构不变） | B-14、B-28、B-30、B-23、A-07 |
| `rpa_engine/gui/page_operation_config.py` | ① 新增步骤不继承邻居表单值；② 目标表失效弹提示且**不改写**；③ 抽 `_flush_form()` 并在返回/退出路径调用；④ 撤销加"后续改动即失效"；⑤ 编辑定位改按索引 | ❌ 对外信号不变 | B-15、B-16、B-17、B-31、B-22 |
| `rpa_engine/gui/app.py` | ① `_excepthook` 过翻译层；② `_setup_gui_logging` 加 try＋回退目录；③ 自检弃用口径与 `active_catalog_keys()` 对齐 | ❌ 签名不变 | A-14、B-01、B-13 |
| `rpa_engine/gui/error_messages.py` | `_RULES` 新增 3 条（模块缺件／标识符禁字符／非 Excel 格式） | ❌ `translate_error`／`log_hint` 不变 | A-13、A-03、A-02 |
| `rpa_engine/gui/worker.py` | ① `finally` 的 `conn.close()` 包 try；② 错误文本回传；③ `prepare` 加运行中防御 | ⚠️ 新增回传通道（信号或可选参数），现有 4 参 `workflow_finished` 不删不改 | B-08、B-32、B-07 |
| `rpa_engine/gui/graph_edges.py` | dangling 判定与 `models` 状态同源 | ❌ `build_edges` 契约不变 | B-21 |
| `rpa_engine/gui/user_template_manager.py` | 保存改临时文件＋原子替换 | ❌ 不变 | B-47（P2，非本轮） |
| `rpa_engine/paths.py` | 新增 `get_normalized_dir()` | ⚠️ 新增函数（既有 API 不变） | REQ-H10 |
| `rpa_engine/tests/test_step_catalog.py` | 断言改基于 `active_catalog_keys()` ＋ 新增弃用场景 | — | B-13 |
| `build.bat` | locale 无关时间戳 ＋ `move` 后检查 `errorlevel` | — | B-45（P2，非本轮，**人工执行**） |
| `requirements.txt` | `xlrd` → `xlrd>=2.0`（补版本约束与来源注释） | — | A-17 |
| `RPA_Workflow_v3.spec` | `hiddenimports` 追加 `'xlrd'` 与 `'ops.excel_normalizer'`（各附注释） | — | A-02、A-17、REQ 系列（新模块） |

### 4.2b 文件计数自洽校验表（唯一计数口径）

| 分类 | 数量 | 明细 |
|---|---|---|
| 新建·源码模块（§4.1） | 1 | `rpa_engine/ops/excel_normalizer.py` |
| 新建·测试（§4.1b） | 2 | `rpa_engine/tests/test_ops_contracts.py`、`rpa_engine/tests/test_engine_failure_paths.py` |
| 新建·交付配置（§4.3） | 1 | `requirements.lock` |
| **新建合计** | **4** | — |
| 修改·`rpa_engine/`（§4.2 前 26 行） | 26 | `ops/` 11 ＋ `engine/` 3 ＋ `gui/` 10 ＋ `paths.py` 1 ＋ `tests/` 1 |
| 修改·构建与依赖（§4.2 后 3 行） | 3 | `build.bat`、`requirements.txt`、`RPA_Workflow_v3.spec` |
| **修改合计** | **29** | ＝ §4.2 表数据行数（**必须相等**） |
| **触及文件总计** | **33** | 29 ＋ 4 |

**实测修正说明**：修订前提示词称"§4.2 只列了约 13 个文件"与实况不符（本版实测为 **29 行**）；原「生成报告」的"修改文件 28 个"亦与表内行数不符 → 本版已按上表对齐为 **修改 29 ＋ 新建 4 ＝ 33**。
**口径说明**：§4.2 表行数（**29**）＝ 修改·`rpa_engine/`（**26**，源码与测试）＋ 修改·构建与依赖（**3**，`build.bat`／`requirements.txt`／`RPA_Workflow_v3.spec`）。修订指令中的"修改·源码模块行数 ＝ §4.2 表行数"应按"**29 ＝ 26 ＋ 3**"理解（二者仅分类方式不同，**数值一致**）。

### 4.3 新建文件（交付配置）与人工执行指引

| 文件 | 新建内容 | 关联 | 执行方 |
|---|---|---|---|
| `requirements.lock` | 裸 `pip freeze` 原样写入（头部注明"含 2 个已声明废弃包，勿安装"） | B-50 | **人工执行** |

**人工执行指引（Agent 不执行）**：`requirements.txt`（`xlrd` → `xlrd>=2.0`）与 `RPA_Workflow_v3.spec`（`hiddenimports` 追加 2 项）的**改动内容已列在 §4.2**；其改动须由人工在构建前完成，并执行 `build.bat` 重建 exe（`AGENTS.md` §1：构建由人工接管）。

### 4.4 登记清单（本轮的登记义务）

| 登记项 | 内容 | 状态 |
|---|---|---|
| `spec hiddenimports` | ＋`'xlrd'`、＋`'ops.excel_normalizer'`（共 2 项） | 本计划已写明（§4.3） |
| 功能函数记录表（专章 §5.5 十三项） | **不涉**——本次不新增/删除/改名任何功能函数（只改既有实现与守卫口径） | 已判定 |
| `BUILTIN_OPS` | **不涉**——新建模块为 Layer 0，不进操作目录 | 已判定 |
| `AGENTS.md` 任务锚点 | 施工完成后须登记新锚点；**前置＝P-0 腾容量**（现余量 272 字） | 待施工后执行（人工/后续轮） |
| `docs/task-records/` | 施工完成后须补任务记录（按 `doc-governance.md` §7 同步规则） | 待施工后执行 |

---

## Part 5 · 验证矩阵

> `Part 2`／`Part 2′`／`Part 3` 的每条条目已自带 §5 验证与 §7 验收标准；本部分给出**批次级门禁**与**端到端场景**，避免逐项重复。

### 5.1 批次级门禁（每批完成后必跑）

| 批次 | 门禁命令（cwd） | 通过判据 |
|---|---|---|
| 每批 | `conda run -n CPS-GPES_RPA-py311 python -m unittest discover -s tests`（`rpa_engine`） | 用例数 ≥ 118 且 `OK` |
| 每批 | 设 `QT_QPA_PLATFORM=offscreen` 后跑 `python tools/smoke/smoke_m1m3.py` 与 `smoke_mb.py`（`rpa_engine`） | 两脚本退出码 0 |
| 每批 | `python -c "import sys; sys.path.insert(0,'.'); from gui.app import run_self_check; r=run_self_check(); print('OK' if r.ok else 'FAIL', len(r.items))"`（`rpa_engine`，offscreen） | 输出 `OK 6` |
| 改规约／文档后 | `python tools/doc_verify.py`（仓库根） | `PASS`、链接失败 0 |
| 涉 `AGENTS.md` | 容量三口径复测 | 含 CR ≤8,000；loneCR=0；loneLF=0；余量 ≥200 |
| P6 后 | **真机 GUI 会话**（人工） | 阶段 1→2→3→4 全链路走通；`A-01`／`A-02`／`A-19` 场景通过 |
| P-2 后 | 人工 `build.bat` ＋ 真实 `.xls` 导入 | exe 态无 `No module named 'xlrd'`；`build/work/**/warn-*.txt` 无该 missing 记录 |

### 5.2 端到端场景矩阵

| # | 场景 | 样本构造 | 通过判据 | 覆盖条目 |
|---|---|---|---|---|
| S1 | **解锁导入**（头号场景） | 2 sheet 的 `样本A.xlsx`；阶段 1 [add] 选入 → 勾选 → 确认并导入 | 两表入库；阶段 2 显示 T1／T2；关闭重开可恢复表与步骤 | A-01、A-10、A-19、B-10 |
| S2 | **exe 态 `.xls`** | exe ＋ `a.xlsx`／`b.xls`／`c.xlsx` 多选 | `b.xls` 不使其余文件丢失；按钮可用；无技术原文 | A-02、A-17、A-14、A-13 |
| S3 | **脏表头隔离** | `表头异常.xlsx`（表头含 `\n`）＋正常表同批 | 脏表失败并给中文（含列号）；正常表入库 | A-03（隔离机制见 `A-02`） |
| S4 | **合并格分组** | `合并格.xlsx`（A2:A4 合并 `华东`） | `SELECT 地区, SUM(金额) GROUP BY 地区` 得 `华东=600`，无 NULL 分组 | A-05、REQ-H9 |
| S5 | **类型保真** | `类型推断.xlsx`（`007`／`1234.56`／18 位身份证） | `007` 为文本；短数仍数值；长数字不转数值 | A-04、REQ-H7 |
| S6 | **公式无缓存** | 脚本生成的 `公式.xlsx`（未被 Excel 打开） | 不静默填 NULL：或保留公式原文，或告警提示 | REQ-R4 |
| S7 | **错误值与字面 NA** | `错误值.xlsx`（`#DIV/0!`）＋`空值口径.xlsx`（字面 `NA`） | `#DIV/0!`→NULL＋留痕；字面 `NA` 保留 | REQ-H4、A-08 |
| S8 | **超链接** | `超链接.xlsx`（显示"查看明细"，指向 URL） | 入库为地址文本；报告留痕 | REQ-R5 |
| S9 | **清洗与列名** | `清洗.xlsx`（`" 华东 "` 等）＋`重名列.xlsx` | 分组只 1 组；列名为 `金额`／`金额_2`／`金额_3` | REQ-R7、REQ-H1 |
| S10 | **空列/尾部空行** | `空列空行.xlsx`（3 列＋尾部 20 空行） | 行数 = 数据行；全空列保留并标记 | REQ-H5 |
| S11 | **告知类** | `含图表.xlsx`（图＋批注） | 导入成功且报告告知 | REQ-H6 |
| S12 | **报告与元数据** | 一次导入 3 表（1 失败） | 报告目录 3 份 JSON＋人读；元数据表行数 = 列数之和；失败清单落盘 | REQ-H9、REQ-H10 |
| S13 | **IN／NOT IN** | 条件 `电表号 IN (0123, 0456)` 与 `NOT IN` | `IN` 命中 2 行；`NOT IN` 列名正确 | B-14、B-28 |
| S14 | **前导零筛选** | 条件 `电表号 = 0123456789` | 命中 1 行（非 0 行）；回填不丢前导零 | B-27 |
| S15 | **假成功** | `rename_columns` 部分失败 | 步骤报失败（非 ✅） | B-18、B-44、B-19 |
| S16 | **skip 现场** | 3 步流程，第 2 步 skip 必失败 | `status == "partial"`；第 1 步派生表仍在 | B-20、B-29、B-36 |
| S17 | **不可逆删表** | 手写 JSON：`output_table` 指向活表；`merge` 的 `dst` 在源表内 | 两场景均报错拒绝，原数据完好 | B-12、B-25 |
| S18 | **导出安全** | ① 大表导出 ② 目标已存在 ③ 含 40000 字符单元格 | ① 不被 OOM ② 覆盖前确认 ③ 截断有告警 | B-03、B-09、B-23、B-34 |
| S19 | **取消与失败语义** | ① 大 JOIN 点终止 ② 必失败步＋期间点终止 | ① 提示"不支持中断"或正确 `cancelled` ② 报 `failed`（不被标 cancelled） | B-05、B-33、B-35 |
| S20 | **双开与退出** | ① 双开 ② 执行中关窗 ③ 点 × 后重开 | ① 会话库不被误删 ② 无 abort ③ 配置可恢复 | B-02、B-06、B-10、B-11 |
| S21 | **弃用通路** | 临时把某功能 `deprecated=True` | 启动自检仍通过；按钮区不出现该功能 | B-13 |
| S22 | **目录不可写** | 只读目录启动 | 给出中文提示（不静默无反应） | B-01 |

### 5.3 逐项验收指针

- `A-01`~`A-19`：判据见各条目 **§7 验收标准**（共 19 组）。
- `REQ-R2`~`REQ-H10`：判据见各条目 **§7 验收标准**（共 12 组）。
- `B-01`~`B-44`：判据见各条目 **§7 验收标准**（共 44 组）。
- `B-45`~`B-79`：**本次不施工**，判据见各条目 **触发条件**（施工时按"触发条件"重写为可勾选验收标准）。

---

## Part 6 · 回滚与应急预案 ＋ 自检清单

### 6.1 回滚与应急

| 项 | 内容 |
|---|---|
| **备份策略** | 施工前在 `_temp/ImportData/backup/` 下按批次建立快照：每批开工前复制本批将改动的文件（保原名），文件名后缀 `.bak_<批次>`；新增文件（`ops/excel_normalizer.py`、两个测试文件）无需备份（删除即回退） |
| **回滚步骤** | ① 停止当前批次；② 用 `backup/` 内对应文件覆盖还原；③ 若已改 `spec`／`requirements.txt`，同步还原；④ 跑 Part 5 §5.1 的批次门禁确认回到基线（118 用例 OK／双 smoke 0／自检 6/6） |
| **最小回滚单位** | 单条目（每个条目的改动点都落在明确文件与行号上，可按条目独立回退） |
| **回滚禁区** | 不得回滚 `build/` 产物（人工管辖）；不得回滚 `_temp/ImportData/problem.md`（问题清单是唯一来源，须保持稳定） |
| **应急总原则** | 任一条目实现失败 → **降级到该条目 §6 的降级策略**；仍失败 → 回滚该条目并登记为"待人工裁定"，**不得**留下半成品（宁可回退也不留中间态） |

**关键条目的应急预案**

| 条目 | 失败现象 | 应急动作 |
|---|---|---|
| `A-01` | 改后导入仍失败 | 立刻回滚三处改动（三处必须同批原则）；改用备选方案（仅挪 `clear_temp_copies()` 调用点） |
| `A-02` | `xlrd` 仍缺件 | 入口先拒绝 `.xls` 并给明确提示（R1 文件级中止语义），把打包修复留给人工重建 |
| `REQ-R4` | 双开簿导致耗时不可接受 | 降级为"仅告警留痕 ＋ 提示用户在 Excel 中打开保存后重试"，**绝不**静默填 NULL |
| `REQ-H9` | 报告落盘拖慢导入 | 降级为"只落 JSON 不生成人读文本"，保留弹窗 |
| `REQ-H10` | 缓存导致结果不一致 | 直接关闭缓存（`enable_cache=False`），H10 仅保留目录管理 |
| `B-03` | `write_only` 与既有代码不兼容 | 回退普通模式但**必须**更正谎报注释并加内存警戒 |
| `B-04` | 预估开销过大 | 改为"建表后立即检查行数，超限则 DROP 并报错"（仍不得截断） |
| `A-15`／`A-16` | 未获 `G-5` 方案裁定 | **不得开工**（硬前置）；已开工则立刻回滚 |

### 6.2 自检清单（施工完成后逐项勾选）

**范围**
- [ ] 未改动 `engine/executor.py` 的步骤分发结构、信号定义、线程模型
- [ ] 未改动 GUI 布局（仅改了槽函数内的错误回显与状态处理）
- [ ] 未改动 Layer 2/Layer 3 的步骤功能函数**行为语义**（只改返回值消费与守卫）
- [ ] 未引入任何新第三方依赖（`requirements.txt` 仅版本约束与注释变更）
- [ ] 未使用 `eval`／`exec`／`pickle`
- [ ] 未新建顶层 `ops/`／`tests/` 目录（新建文件均在 `rpa_engine/` 下）

**质量**
- [ ] 每处改动都落在"文件＋行号＋改前/改后"的粒度（无"优化此处"类表述）
- [ ] 所有路径为项目相对路径（全文无 `D:\`／`C:\`）
- [ ] 每条 A／REQ 项含 ≥1 条规则编号（R1~R7／H1~H10）
- [ ] 每条 A／REQ／B(P0/P1) 项含可勾选验收标准（`- [ ]`）
- [ ] 未合并改造项：`J-03`→`A-02`、`B-01`→`A-17`、`G-07`→`B-12` 三处已合并项**编号仍保留**

**一致性**
- [ ] problem.md 的 101 个编号在本文件均有且仅有一个对应改造项（见 §6.3）
- [ ] 本文件未出现 problem.md 之外的新问题（`REQ` 项已声明来源，见 Part 0 §0.5）
- [ ] 批次顺序与 Part 1 §1.2 的调整说明一致
- [ ] `[UNVERIFIED]` 项全部集中在 §6.4
- [ ] `[UNVERIFIED]` 占位已全部回填，或经人工确认可暂留（清单见 Part 0 §0.7 与 §6.4）
- [ ] 改前/改后代码片段均已确认是语义示意而非精确 diff（见 Part 0 §0.2.1）
- [ ] 多 Agent 协作标记（`[SUB_AGENT_COMPLETE]`／`[SUB_AGENT_BLOCKED]`／`[SUB_AGENT_CONFLICT]`／`[REQUIRES_HUMAN_CONFIRMATION]`）已按 Part 0 §0.8 使用，未自造标记名

### 6.3 闭合性核对表（problem.md 101 编号 ↔ 本文件条目）

| problem.md 编号 | 本文件对应项 | 状态 |
|---|---|---|
| F-01 | A-01 | 闭合 |
| H-01 | A-02 | 闭合 |
| J-03 | A-02 | 闭合（**已合并**，原编号保留） |
| G-06 | A-03 | 闭合 |
| J-01 | A-04 | 闭合 |
| H-09 | A-05 | 闭合 |
| H-15 | A-06 | 闭合 |
| H-16 | A-07 | 闭合 |
| H-06 | A-08 | 闭合 |
| F-08 | A-09 | 闭合 |
| H-04 | A-10 | 闭合 |
| H-05 | A-11 | 闭合 |
| F-09 | A-12 | 闭合 |
| H-21 | A-13 | 闭合 |
| H-24 | A-14 | 闭合 |
| DM-30 | A-15 | 闭合 |
| DM-31 | A-16 | 闭合 |
| DM-01 | A-17 | 闭合 |
| B-01 | A-17 | 闭合（**已合并**，原编号保留） |
| DM-03 | A-18 | 闭合 |
| H-18 | A-19 | 闭合 |
| F-02 | B-01 | 闭合 |
| F-03 | B-02 | 闭合 |
| F-04 | B-14 | 闭合 |
| F-05 | B-03 | 闭合 |
| F-06 | B-04 | 闭合 |
| F-07 | B-05 | 闭合 |
| F-10 | B-45 | 闭合 |
| F-11 | B-46 | 闭合 |
| G-01 | B-15 | 闭合 |
| G-02 | B-16 | 闭合 |
| G-03 | B-17 | 闭合 |
| G-04 | B-06 | 闭合 |
| G-05 | B-07 | 闭合 |
| G-07 | B-12 | 闭合（**已合并**，原编号保留） |
| G-08 | B-18 | 闭合 |
| G-09 | B-19 | 闭合 |
| G-10 | B-20 | 闭合 |
| G-11 | B-08 | 闭合 |
| G-12 | B-47 | 闭合 |
| G-13 | B-21 | 闭合 |
| G-14 | B-22 | 闭合 |
| H-02 | B-09 | 闭合 |
| H-03 | B-23 | 闭合 |
| H-04b | B-10 | 闭合 |
| H-07 | B-24 | 闭合 |
| H-08 | B-25 | 闭合 |
| H-11 | B-26 | 闭合 |
| H-12 | B-48 | 闭合 |
| H-13 | B-27 | 闭合 |
| H-14 | B-28 | 闭合 |
| H-17 | B-29 | 闭合 |
| H-19 | B-30 | 闭合 |
| H-20 | B-31 | 闭合 |
| H-22 | B-32 | 闭合 |
| H-23 | B-33 | 闭合 |
| H-25 | B-11 | 闭合 |
| H-26 | B-49 | 闭合 |
| J-02 | B-34 | 闭合 |
| J-04 | B-35 | 闭合 |
| J-05 | B-36 | 闭合 |
| J-06 | B-12 | 闭合 |
| J-07 | B-37 | 闭合 |
| J-08 | B-38 | 闭合 |
| J-09 | B-39 | 闭合 |
| DM-24 | B-40 | 闭合 |
| G-5 | B-51 | 闭合 |
| G-7 | B-52 | 闭合 |
| B-02 | B-50 | 闭合 |
| B5 | B-13 | 闭合 |
| D4 | B-53 | 闭合 |
| B1 | B-54 | 闭合 |
| B2 | B-55 | 闭合 |
| B3 | B-56 | 闭合 |
| B4 | B-57 | 闭合 |
| B6 | B-58 | 闭合 |
| B7 | B-59 | 闭合 |
| B8 | B-60 | 闭合 |
| B9 | B-41 | 闭合 |
| C1 | B-61 | 闭合 |
| C2 | B-62 | 闭合 |
| D1 | B-63 | 闭合 |
| D2 | B-64 | 闭合 |
| D3 | B-65 | 闭合 |
| E1 | B-66 | 闭合 |
| E3 | B-67 | 闭合 |
| A4 | B-68 | 闭合 |
| P1-1 | B-42 | 闭合 |
| P1-2 | B-43 | 闭合 |
| P1-6 | B-44 | 闭合 |
| P2-1 | B-69 | 闭合 |
| P2-2 | B-70 | 闭合 |
| N-01 | B-71 | 闭合 |
| N-02 | B-72 | 闭合 |
| N-03 | B-73 | 闭合 |
| N-04 | B-74 | 闭合 |
| N-05 | B-75 | 闭合 |
| §8.2-1 | B-76 | 闭合 |
| §8.2-2 | B-77 | 闭合 |
| §8.2-3 | B-78 | 闭合 |
| §8.2-4 | B-79 | 闭合 |

| **合计** | **101 行**（A 侧 21 ＋ B 侧 80） | — |

### 6.4 `[UNVERIFIED]` 清单（须由实施者补读后回填）

| # | 位置 | 未核实内容 | 需人工/实施者提供 |
|---|---|---|---|
| 1 | `A-01` §4 | `engine/executor.py` L40-68 的 `_IMPORT_ROOTS` 与 `_validate_import_path` 语义 | 读该段后确认：`source_path` 所在目录是否被允许；若不允许，须在 GUI 侧补等价校验或调整白名单 |
| 2 | `A-10` 改动点 3 | `gui/models.py::to_dict` 内 `source.file` 构造的**实际行号**（本轮只读到 L650-720 的函数范围） | 读 L650-720 定位赋值行 |
| 3 | `A-14` 改动点 2 | `gui/app.py` L1-40 的 import 区，以及 `sys.excepthook` 注册处行号 | 读后确认无循环导入风险 |
| 4 | `A-16` 改动点 1 | `engine/executor.py` 引入 `table_row_count` 是否造成循环导入 | 实测导入链 |
| 5 | `B-05` 改动点 1 | 终止按钮的控件名与"不支持中断集合"的判定位置 | 读 GUI 终止相关代码 |
| 6 | `B-06` 改动点 1 | `EngineWorker` 的构造点（parent 传参处） | 读 `main_window.py` 构造段 |
| 7 | `B-07` 改动点 1 | `MainWindow.start_workflow` 的精确行号（v7 记载 L539-547） | 读该函数头 |
| 8 | `B-11` 改动点 1 | 四处 `_ignore_next_finish` 置位点的精确行号与分支结构 | 读四处上下文 |
| 9 | `B-13` 改动点 1 | `gui/app.py::run_self_check` 中比对 `catalog_keys` 的精确行号（v7 记载 L185-188） | 读自检函数 |
| 10 | `B-15` 改动点 1/2 | 新增步骤插入点与收拢逻辑的精确行号（v7 记载 L501-513／L674-698／L477-480） | 读 `page_operation_config.py` 对应段 |
| 11 | `B-17` 改动点 1 | 六处收拢调用点与两处遗漏点的精确行号（v7 记载 L157／L299 与 L652/660/519/541/616/998） | 读全文定位 |
| 12 | `B-21` 改动点 1 | `gui/graph_edges.py` dangling 判定的精确行号（v7 记载 L203） | 读该函数 |
| 13 | `B-22` 改动点 1 | 模板载入保留 `step_id` 的精确位置 | 读 `models.py` 模板路径 |
| 14 | `B-26` 改动点 2 | `engine/executor.py` 重试分支的精确行号（v7 记载 L279-282） | 读 `_execute_with_retry` |
| 15 | `B-39` | `engine/parser.py` 版本经 `str()` 归一比较的**实际实现行**（v7 记载 L124） | 读 L118-133 |
| 16 | `B-47` | `gui/user_template_manager.py` 保存路径的精确行号（v7 记载 `:509-531`／`save:230-234`） | 读该文件 |
| 17 | `REQ-H6` | openpyxl 只读模式下 `ws._images`／`ws._charts`／批注的**可用性** | 实测探测 |
| 18 | `REQ-H10` 改动点 1 | `rpa_engine/paths.py` 既有函数命名与风格（本轮未读该文件全文） | 读 `paths.py` |
| 19 | `B-04`／`B-41`／`B-59` | `step_executor.py` L188-200 的 `global_config` 获取方式与白名单实现 | 读该段 |
| 20 | 全部 Qt 行为类条目 | `G-04`／`G-05`／`G-11`／`H-04b`／`H-25`（problem.md 标 `[UNVERIFIED]`）的实机行为 | **须人工验证（Agent 不可执行）**；位置＝Part 5 **§5.2**（场景矩阵） |

> 处置规则：实施者在动工前补读上表，把结果回填到对应条目；**未回填不得声称该条已完成**。

### 6.5 未施工声明（本文件的性质）

| 项 | 声明 |
|---|---|
| 未执行代码修改 | ✅ 本文件生成全程**未改动任何源码**（`rpa_engine/**` 零改动） |
| 未执行编译/运行 | ✅ 未执行 `build.bat`、未运行程序、未跑测试 |
| 未安装依赖 | ✅ 未执行任何 `pip`／`conda install` |
| 未引入新依赖 | ✅ 本计划的全部方案仅使用既有依赖（含明确排除 `pywin32`／`pyarrow`／`xlsxwriter`） |
| 范围未越界 | ✅ 仅覆盖「Excel 规范化预处理模块 ＋ 接入导入流程」，未触及引擎调度与 GUI 布局 |
| 未执行 git | ✅ 未做任何 git 写操作（`AGENTS.md` §1） |
| 路径规范 | ✅ 全文为项目相对路径 |
| 唯一来源 | ✅ 问题清单唯一来源＝`_temp/ImportData/problem.md`（v8，101 编号） |

### 6.6 多 Agent 验收流程

> 本节是 Coordinator 的**收口动作**；协议标记定义见 §0.8.3。

#### 6.6.1 汇总

1. 收集所有已完成批次的 `[SUB_AGENT_COMPLETE]` 报告。
2. **核对交付物清单中的文件是否实际存在**（`Test-Path` ＋ 抽查关键函数签名），凡清单有而磁盘无者，视为该批**未完成**。
3. 检查**无未解决的 `[SUB_AGENT_CONFLICT]`**；有则先走 §6.6.2 仲裁。
4. 执行该批次的 §1.4 门禁；未过门禁不得分发下一批。

#### 6.6.2 冲突检测与仲裁

| 冲突类型 | 仲裁规则 |
|---|---|
| **同一文件的修改冲突** | 按优先级批次顺序，**高优先级批次的修改优先**；低优先级批次须在其基础上重新套用（不得覆盖高优先改动） |
| **接口签名变更冲突** | **不自行仲裁** → 升级为 `[REQUIRES_HUMAN_CONFIRMATION]`（因签名属对外契约，见 §0.2 条 2） |
| **两份 `[SUB_AGENT_COMPLETE]` 声称改了同一行区间** | 以文件实际内容为准，回溯双方改动摘要，判定归属后要求低优先级方重新提交 |

#### 6.6.3 最终验收

1. Coordinator 执行 §6.2 自检清单**全部条目**（范围／质量／一致性）。
2. 全部通过 → 输出**最终报告**并标记 `[REQUIRES_HUMAN_CONFIRMATION]`，**等待人工验收**（不得自行宣布交付）。
3. 任一项检查失败 → 输出**失败详情**（失败项 ＋ 证据 ＋ 建议动作）并**暂停**，不得继续后续批次。
4. 最终报告须包含：已完成批次清单、各批交付物、§6.3 闭合表复核结果（仍为 101 行）、未回填的 `[UNVERIFIED]` 残余项、以及 `P-2`（人工 build ＋ 真机 `.xls`）的待办状态。

---

## 生成报告（本文件的生成记录）

### 概览

| 项 | 数量 |
|---|---|
| problem.md 条目总数 | **101 编号**（A 侧 21 ＋ B 侧 80） |
| **A 类改造项（DEF-A）** | **19 项**（修改型 17 / 新建型 2[^1] / 废弃型 0） |
| **规则落地项（REQ）** | **12 项**（修改型 5 / 新建型 6 / 组合型 1） |
| **B 类处理项（DEF-B）** | **79 项**（七段式 44 / 精简四段 35） |
| 合计改造项 | **110 项** |
| 新建文件 | **4 个**（1 模块 `ops/excel_normalizer.py` ＋ 2 测试 `tests/test_ops_contracts.py`／`tests/test_engine_failure_paths.py` ＋ 1 交付配置 `requirements.lock`）；明细见 §4.1／§4.1b／§4.3 |
| 修改文件 | **29 个**（`rpa_engine/` 26 ＋ 构建与依赖 3：`build.bat`／`requirements.txt`／`RPA_Workflow_v3.spec`）；明细见 §4.2，计数自洽校验见 §4.2b |
| 触及文件总计 | **33 个**（29 ＋ 4） |
| **口径说明（2026-10-19 实测）** | 「修改 29」＝本计划的**修改清单**（§4.2 表 29 行）；**实际 `git` 受跟踪源码变更 ＝ 17 个**（另 `RPA_Workflow_v3.spec` 被 `.gitignore` 的 `*.spec` 忽略、`build.bat` 未改；`AGENTS.md`／`docs/`／任务记录等变更不计入源码）—— 两者**口径不同，非计数错误** |
| `[UNVERIFIED]` 占位 | **20 处**（见 §6.4） |
| `[NO_CODE_MATCH]` | **0 处** |

[^1]: `A-01` 的三处改动含"新增 `prune_copies()` 方法"（新建逻辑并入修改型条目）；`A-15`／`A-16` 以"**同文件内新增函数**"实现（`import_dataframe_atomic`／`guard_overwrite_target`），计为修改型。另有 **2 个测试文件**为新建，按其归属记在 `B-42`／`B-43`（新建型）；**新建合计 4 个**（1 模块 ＋ 2 测试 ＋ 1 lock）见 §4.2b。

### 修订概览（2026-10-18，共 6 项）

| 修订 | 内容 | 状态 | 落点 |
|---|---|---|---|
| **1** | `B-45`~`B-49` 补「修改方案概要」 | ✅ 完成 | §3.3：5 项各含"目标文件／目标位置／核心改动逻辑／关键片段示意／完成判定" |
| **2** | 文件清单计数修正 | ✅ 完成 | §4.1b（新建测试移到此处）／§4.2（**29 行**，补 `requirements.txt`＋`spec`）／§4.2b（计数校验）／§4.3／本节概览 |
| **3** | `[UNVERIFIED]` 集中管理 ＋ 优先级 | ✅ 完成 | §0.7（**20 行**，其中 **P0 级 8 项**）／§1.5（P0 动手前核实义务）／§6.2（自检项） |
| **4** | 「改前/改后＝语义示意」全局声明 | ✅ 完成 | §0.2.1（优先级等同硬约束）／§6.2（自检项） |
| **5** | 裁定 `G-5`、解除 `A-15`/`A-16` 待裁定 | ✅ 完成 | §1.6（三件套裁定 ＋ 覆盖理由 ＋ 残余风险）／§0.3（`P-1` 标"已解除"）／§1.1（并入 **P4**）／§1.2／§1.3／`A-15`、`A-16` 条目本体（已改实施型） |
| **6** | 多 Agent 协作机制 | ✅ 完成 | §0.8（架构／拆分规则／协议／交接／约束前缀／名册）／§1.1（**＋2 列**，共 7 列）／**75 项**各加「§8 Agent 执行指引」／§6.6（多 Agent 验收流程） |
| **7** | 决策确认 + 全文一致性校对 | ✅ 完成 | 头部注释 + §0.1 + §6.3 + §6.4 + 生成报告 |

### 本轮校对结果（2026-10-18）

| 校对 | 结果 | 实测证据 |
|---|---|---|
| 1｜`B-45`~`B-49` 概要完整性 | ✅ **5/5 完整** | 每项含 目标文件／目标位置／核心改动逻辑／关键片段示意／完成判定；`B-49` 口径＝**抛中文错误**（人工已确认，见头部决策确认②） |
| 2｜文件清单计数 | ✅ **一致** | §4.2 = **29 行**；§4.2b 新建 **4**／修改 **26＋3＝29**／合计 **33**；生成报告同值（口径说明见 §4.2b） |
| 3｜`[UNVERIFIED]` 占位清单 | ✅ **一致（口径已明示）** | §0.7 = §6.4 = **20 行**；正文另有 **28 处**引用，合计 **48** 次出现（口径说明见 §0.7） |
| 4｜闭合性核对表 | ✅ **一致** | §6.3 = **101 行** ＝ problem.md 编号总数（首 F-01／末 §8.2-4／无重复编号） |
| 5｜多 Agent 标记统一 | ✅ **全文统一** | 仅 4 种标准标记（`[SUB_AGENT_COMPLETE]`／`[SUB_AGENT_BLOCKED]`／`[SUB_AGENT_CONFLICT]`／`[REQUIRES_HUMAN_CONFIRMATION]`），**无自造变体**；§0.8.3 协议表 ↔ 75 个「§8」段 ↔ §6.6 三方一致 |
| 6｜批次顺序与条目归属 | ✅ **一致** | 31 条 `> 规则：` 行批次标注与 §1.1 逐格相符：P0 **7A**／P1 **3A**／P2 **1A+1REQ**／P3 **1A+2REQ**／P4 **6A+3REQ**／P5 **6REQ**／P6 **1A**（合 31）；无遗漏、无多余 |
| 占位扫描（步骤 10） | ✅ **干净** | `[TODO]`／`[FIXME]`／`[XXX]`／`[TBD]` **0 命中**；代码围栏成对；禁词仅出现在禁止性表述内 |

### 顺序调整说明

调整 **2 处**：① **P0 合并批**——提示词原 P0＝「异常隔离与单表容错机制」，本计划调整为 **P0＝「解锁导入链路 ＋ 异常隔离骨架」**（理由为三条一手代码证据：逐表 `try/except` 已存在于 `main_window.py:322-328`；主症状真根因是副本生命周期 `main_window.py:257`＋`page_input_selection.py:367`；抛出的是**已被捕获**的 `FileNotFoundError`）——详见 §1.2。② **`A-15`／`A-16` 由「P-待裁定」并入 P4**——2026-10-18 修订指令授权**自主裁定 `G-5`**（三件套见 **§1.6**），原「先出方案再裁定」门禁已在 §0.3 标「**已解除**」并保留原裁定引用。`P1`~`P6` 的规则推进顺序沿用提示词原序。

### `[UNVERIFIED]` / `[NO_CODE_MATCH]` 清单

见 §6.4（20 条，含 problem.md 原有 10 条 Qt 行为类）。

### 闭合性核对

| 项 | 结果 |
|---|---|
| 闭合表行数 | **101 行**（＝problem.md 编号总数） |
| 无遗漏 | ✅ A 侧 21＋B 侧 80，逐条对应（见 §6.3） |
| 无重复 | ✅ 101 个编号各出现一次 |
| `REQ` 项来源 | 已在 Part 0 §0.5 声明（需求规则，非新增问题） |
| 已合并项 | `J-03`→`A-02`／`B-01`→`A-17`／`G-07`→`B-12`，编号均保留 |

### 声明

- 未执行代码修改：✅
- 未执行编译/运行：✅
- 未引入新依赖：✅
- 范围未越界（仅预处理＋导入接入）：✅
- 所有路径为相对路径：✅

---

> **给 Coordinator 与施工者的一句话**：Coordinator 先读 **§0.1／§0.2／§0.2.1／§0.7／§1.1／§1.4／§6.6**（**无需整读全文**）→ 按 §1.1 分发 Sub-Agent（协议与标记名见 §0.8，**不得自造标记**）→ 每批结束跑 §1.4 门禁 → 全部完成后走 §6.6 最终验收并标 `[REQUIRES_HUMAN_CONFIRMATION]` 交人工验收。**`P-0`（腾 `AGENTS.md` 容量）是第一个动作**；`A-15`／`A-16` 已按 **§1.6** 裁定，**可直接开工**（不再是"待裁定"）。