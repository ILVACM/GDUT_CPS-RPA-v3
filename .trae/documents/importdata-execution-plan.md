# 计划：按 plan.md 执行 ImportData 导入链路修复（多 Agent 协作）

> 计划日期：2026-10-18 ｜ 施工依据：`_temp/ImportData/plan.md`（6,140 行，唯一依据）
> 项目根：`d:\CPS-GPES_RPA-20250312\v3` ｜ 引擎根：`rpa_engine`
> 运行方式：**C（多 Agent 协作）**——Coordinator＝本 Agent；Sub-Agent＝按批分发（`Agent` 工具的 general-purpose）
> Specialist 路由：`architecture-decisions`（跨条目耦合裁定；本会话已 Read 加载）
> 已获人工授权：① **P-0 可执行**（修改 `AGENTS.md` 腾容量）② **门禁按 plan.md 用 conda**

---

## 1. 摘要

按 plan.md 的批次顺序 **P-0 → P0 → P1 → P2 → P3 → P4 → P5 → P6** 逐批施工，B 类并行。每批结束跑 plan.md §1.4 门禁、输出简报；全部完成走 §6.6 汇聚验收。

**本次交付的是「分批执行的完整链条」，不是一次性全改完**：每批独立可验证、可回滚、可人工提交（**git 由人工执行**，见 §4-D3）。

| 阶段 | 内容 | 项数 | 涉及文件 |
|---|---|---|---|
| **P-0** | 腾 `AGENTS.md` 容量 ＋ 登记任务锚点 ＋ 清 8 项 P0 级 `[UNVERIFIED]` ＋ 回写 `[ADJUSTED]` | — | `AGENTS.md`、`docs/architecture.md`、`docs/task-records/`、`plan.md` |
| **P0** | 解锁导入链路 ＋ 异常隔离（`A-10`→`A-19`→`A-01`→`A-02`→`A-13`→`A-14`→`A-17`） | 7 A | `gui/page_input_selection.py`、`gui/main_window.py`、`gui/models.py`、`gui/error_messages.py`、`gui/app.py`、`RPA_Workflow_v3.spec`、`requirements.txt` |
| **P1** | 临时区与格式转换（`A-11`、`A-12`、`A-18`） | 3 A | `ops/excel_preprocessor.py` |
| **P2** | 表头规范化（`A-03`、`REQ-R2`） | 1 A＋1 REQ | `ops/table_importer.py`、`ops/excel_preprocessor.py`、`gui/error_messages.py` |
| **P3** | 单元格处理 R3/R4/R5（`A-05`、`REQ-R4`、`REQ-R5`） | 1 A＋2 REQ | 新建 `ops/excel_normalizer.py` |
| **P4a** | 类型/内容/特殊值（`A-04`、`A-06`、`A-07`、`A-08`、`REQ-R7`、`REQ-H3`、`REQ-H4`） | 4 A＋3 REQ | `ops/excel_normalizer.py`、`ops/exporter.py` |
| **P4b** | `G-5` 三件套（`A-15`、`A-16`） | 2 A | `ops/sqlite_manager.py`、`ops/table_lifecycle.py`、`ops/filter_dedup.py`、`ops/aggregator.py`、`ops/mapping_matcher.py`、`engine/executor.py`、`ops/table_importer.py` |
| **P5** | 元数据与报告（`REQ-H1/H5/H6/H7/H9/H10`） | 6 REQ | `ops/excel_normalizer.py`、`paths.py`、会话库元数据表 |
| **P6** | 接入与端到端联调（`A-09`） | 1 A | `gui/main_window.py`、`ops/excel_preprocessor.py` |
| **B 类** | `Agent-B1`：`B-01`~`B-44`（本轮施工）；`B-45`~`B-79` **仅登记不动** | 44 B | 约 20 个文件（见 plan.md Part 3） |

---

## 2. 现状分析（Phase 1 实测）

### 2.1 已解出的 P0 级 `[UNVERIFIED]`（8 项中已解 5，余 3 项在 P-0 内解）

| §0.7 编号 | 条目 | 实测结论 | 来源 |
|---|---|---|---|
| 1 | `A-01` | **`_IMPORT_ROOTS`（`engine/executor.py` L42-44）只含 `temp/input_selection`**；`_validate_import_path`（L54-68）在白名单外一律抛 `ParserError`，仅由 `ensure_input_tables` L105 调用；L47-51 已有 `register_import_root()` 扩展钩子 | `executor.py` L40-68 实读 |
| 3 | `A-14` | `app.py` L10-21 为标准库 + `loguru` + `engine.registry` + `paths` —— **`error_messages` 只依赖 `paths`**，函数内导入可避免循环 | `app.py` L1-42 实读 |
| 6 | `B-07` | `MainWindow.start_workflow` **在 L480**；四处 `request_cancel` 位于 L250／415／429／445 | Grep 实测 |
| 7 | `B-11` | 四处置位点 **L249-254／L414-418／L428-433／L444-448**（均在 `if self.worker.isRunning():` 内）；消费点在 **L584-585** | Grep 实测 |
| 8 | `B-13` | `app.py` **L186** `if main_set | more_set != catalog_keys:` —— 比对的是**未过滤弃用**的 `catalog_keys`（L146 同款），与 `models.main_buttons()`（L127，已过滤）口径不一致 → **B-13 成立** | Grep 实测 |
| 2 / 4 / 5 | `A-10`／`B-05`／`B-06` | **待 P-0 内精读**：① `models.py::to_dict` 内 `source.file` 赋值行（区间 L650-708）；② 终止按钮控件名（`main_window.py` 内 Grep `终止|放弃`）；③ `EngineWorker(` 构造点 | 待执行 |

### 2.2 三处需回写 plan.md 的 `[ADJUSTED: 原因]`（本次发现）

1. **【关键｜跨条目耦合】`A-01` ＋ `A-10` ＋ 导入白名单**：`A-01` 改用 `source_path` 直读原始文件、`A-10` 令 `source.file` 落为原始路径之后，**阶段 3 的兜底补导**（`ensure_input_tables` L91-108 → `_validate_import_path` L105）会因原始路径不在 `_IMPORT_ROOTS` 内而抛 `ParserError`（其异常类型**不属** L110 捕获面 `(ValueError, FileNotFoundError)` → 会逃逸为 `failed`）。
   **处置（写进 plan.md）**：`A-01` 改动点 2 追加第 4 步 —— 在导入循环内对每个 `source_path` 的父目录调用 **`engine.executor.register_import_root(Path(src).parent)`**（复用 L47-51 现成钩子，**不新增白名单机制**）；并在 `A-01` §4「必须遵循的规约」补引该函数。
2. **【口径】`_validate_import_path` 抛的是 `ParserError` 而非 `ValueError`** → 影响 `B-33`（补导阶段终止降级）的捕获面描述；在 `B-33` 条目旁标 `[ADJUSTED: 异常类型为 ParserError]`。
3. **【GUI 直调不受白名单约束】**：`main_window.py` L303 的 `import_excel_table` 直调**不经** `_validate_import_path` → `A-01`/`A-02` 的 GUI 侧校验属**新增防护**（非"修复既有校验"），据此调整 `A-01` §4 的措辞。

### 2.3 环境与门禁事实

- 测试：`rpa_engine/tests/` 10 个测试文件（基线 ≥118 用例）
- 冒烟：`rpa_engine/tools/smoke/smoke_m1m3.py`、`smoke_mb.py`（需 `QT_QPA_PLATFORM=offscreen`）
- 自检：`gui/app.py::run_self_check`（6 项）
- 规约体检：`tools/doc_verify.py`（cwd＝仓库根）；`AGENTS.md` 当前含 CR **7,728**／上限 8,000／余量 **272**

---

## 3. 变更内容（decision-complete）

### 3.1 执行协议（逐字遵守）

1. **严格按批**：`P-0 → P0 → P1 → P2 → P3 → P4a → P4b → P5 → P6`；**前批门禁不过，不得开下一批**（plan.md §1.1／提示词 §二）。
2. **Sub-Agent 只读自己那批**：每条目从 plan.md 按**行区间**读取（用 `Grep` 定位 `### A-xx`／`### REQ-xx`／`### B-xx` 的起止行，再用 `Read` 的 `offset/limit` 切片），**不得整读 plan.md**（412 KB）。
3. **前缀必须下发**：分发时把 plan.md **§0.1 ＋ §0.2 ＋ §0.2.1**（范围／硬约束／执行须知）作为上下文前缀随任务一并给出（§0.8.5）。
4. **标记只用 4 个**：`[SUB_AGENT_COMPLETE]`／`[SUB_AGENT_BLOCKED]`／`[SUB_AGENT_CONFLICT]`／`[REQUIRES_HUMAN_CONFIRMATION]`（§0.8.3；后两者由 Coordinator 发出）。
5. **交付物走文件系统**：每批完成后 Coordinator 用 `Read`／`Test-Path` 抽查产物确实落盘，再分发下一批（§0.8.4 条 2-3）。
6. **改前/改后为语义示意**：以本地源码真实文本为准做**等价替换**，禁止全文机械匹配（§0.2.1）。
7. **不得改引擎调度／GUI 布局／步骤功能函数语义**（plan.md §0.1 ❌ 列）。

### 3.2 阶段 P-0（前置，先做）

| 步骤 | 动作 | 完成判据 |
|---|---|---|
| P-0.1 | 读 `AGENTS.md` §2.6／§5.4／§8 现文，按 §0.3 方案**下沉 3 处**：① §2.6 功能函数指针压为 2 行；② §5.4 已知阻塞摘要整段下沉 `docs/architecture.md` §9；③ §8 当前任务上下文两段并为 1 行。**红线 §2.1／§2.2 一字不动** | 含 CR 字符数下降且 **≤8,000**；loneCR=0；loneLF=0；余量 **≥200** |
| P-0.2 | 跑 `conda run -n CPS-GPES_RPA-py311 python tools/doc_verify.py`（cwd＝仓库根） | `PASS`、链接失败 0、容量项通过 |
| P-0.3 | 登记本轮任务锚点：改 `AGENTS.md`「当前任务锚点」（5 秒摘要）＋ 新增 `docs/task-records/2026-10-18-importdata-repair.md`（详情层） | 锚点含 目标／状态／轮次／要点／详情索引；`doc_verify` 复跑仍 `PASS` |
| P-0.4 | 清余下 3 项 P0 级 `[UNVERIFIED]`：① Grep `source.file` 定位 `models.py::to_dict` 赋值行；② Grep `终止\|放弃` 定 `main_window.py` 终止按钮控件名；③ Grep `EngineWorker(` 定构造点 | 3 项结论**回填 plan.md §0.7 对应行**（`[UNVERIFIED]` → 实测行号） |
| P-0.5 | 回写 §2.2 的 3 处 `[ADJUSTED: 原因]` 到 plan.md（`A-01` §3-§4、`B-33` 旁注） | 三处标注落盘 |

### 3.3 批次执行明细（P0~P6）

**统一门禁（每批必跑，§1.4）**
```
（cwd=rpa_engine）
1) $env:QT_QPA_PLATFORM='offscreen'
2) conda run -n CPS-GPES_RPA-py311 python -m unittest discover -s tests     → 用例数 ≥118 且 OK
3) conda run -n CPS-GPES_RPA-py311 python tools/smoke/smoke_m1m3.py         → 退出码 0
4) conda run -n CPS-GPES_RPA-py311 python tools/smoke/smoke_mb.py           → 退出码 0
5) （offscreen）自检：from gui.app import run_self_check → ok == True 且 6 项
```

| 批 | 条目（顺序） | 关键落点 | 本批特有验证 |
|---|---|---|---|
| **P0** | `A-10`→`A-19`→`A-01`→`A-02`→`A-13`→`A-14`→`A-17` | `get_entries` 导出 `source_path`；`to_dict` 用 `source_path`；身份三元组比对；`_close_session()` 与副本清理时机拆分；`_on_add_files` 异常元组扩容＋`finally` 复位；`translate_error` 传类名；`_RULES` 新增 3 条；`app._excepthook` 过翻译层；`spec` 补 `'xlrd'`＋`'ops.excel_normalizer'`；`requirements.txt` 改 `xlrd>=2.0` | **场景 S1**：2-sheet 样本经 [add] → 确认导入 → 阶段 2 出现 T1/T2；关闭重开可恢复（plan.md Part 5 §5.2 S1）；**白名单**：导入后 `ensure_input_tables` 不报 `输入文件路径不在允许范围` |
| **P1** | `A-11`、`A-12`、`A-18` | `validate_and_copy`：`copy2`→`copyfile`＋`os.utime`；跨后缀查重；`ensure_xlsx` 产物加序号 | 源文件 mtime 早于 24h 时重开仍可恢复；同名异后缀生成两个副本 |
| **P2** | `A-03`、`REQ-R2` | `import_excel_table` 前置列名/空表头校验；`read_header_row()`；`error_messages` 新规则 | 表头含 `\n` 的表失败并给中文（含列号），同批其余表正常 |
| **P3** | `A-05`、`REQ-R4`、`REQ-R5`（**同文件串行**） | 新建 `ops/excel_normalizer.py`：`split_merged_cells`／`resolve_formula_cells`／`expand_hyperlinks`＋`NormalizeResult`＋管线 | 合并格分组无 NULL 组；公式无缓存不静默 NULL；超链接格入库为地址 |
| **P4a** | `A-04`、`A-06`、`A-07`、`A-08`、`REQ-R7`、`REQ-H3`、`REQ-H4` | normalizer 管线：错误值→NULL→超链接→清洗→空值策略→类型推断；`exporter` 日期写回 | `007` 仍为文本；日期列导出为真日期；字面 `NA` 保留；`#DIV/0!`→NULL＋留痕 |
| **P4b** | `A-15`、`A-16`（`G-5` 三件套） | `guard_overwrite_target()` 四处共用；`import_dataframe_atomic()`（临时表→校验行数→`DROP`→`RENAME`）；`ensure_input_tables` 判据加行数 | 导入中途失败后**旧表 10 行完好、无空壳表**；`output_table` 指向活表被拒；空壳表触发补导 |
| **P5** | `REQ-H1`、`REQ-H5`、`REQ-H6`、`REQ-H7`、`REQ-H9`、`REQ-H10` | 列名归一；空列/尾部空行；非单元格内容告知；超长数字提示；报告＋元数据表＋失败清单落盘；`paths.get_normalized_dir()`＋幂等缓存 | 报告目录 3 份 JSON＋人读；元数据表行数＝列数之和；失败清单落盘；重复导入命中缓存 |
| **P6** | `A-09` | `_on_confirm_import` 进度文案预告＋内存警戒；`read_excel_sheet` 超大表分块 | 20 万行级表导入前有提示；常规表行为不变 |
| **B 类** | `Agent-B1` 串行 `B-01`~`B-44` | plan.md Part 3 §3.1／§3.2 各条目 | 各条目 §7 验收标准逐条勾选；`B-45`~`B-79` **本轮不动** |

**Sub-Agent 分发矩阵（按 §0.8.2：同批次一个 Agent；跨批次文件重叠则串行）**

| Agent | 批次 | 与上一批的文件重叠 | 并行性 |
|---|---|---|---|
| `Agent-P0` | P0 | — | 串行（最先） |
| `Agent-P1` | P1 | 与 P0 不重叠 | P0 通过后启动 |
| `Agent-P4a` / `Agent-P4b` | P4a／P4b | 两者**互不重叠** | **可与彼此并行**；均需 P3 通过 |
| `Agent-P2`／`Agent-P3`／`Agent-P5`／`Agent-P6` | 各一批 | 见 plan.md §1.1「备注」列 | 串行链 |
| `Agent-B1` | B 类（B-01~B-44） | 与 A 链多数不重叠 | **自 P0 通过后即可并行启动**（其多数条目的可验证性依赖 P0 解锁） |
| `Agent-B2` | B-45~B-79 | — | **不启动**（本轮仅登记） |

### 3.4 每批的收尾动作（Coordinator 自做，不外包）

1. 抽查交付物：`Read` 关键函数签名／`Test-Path` 新文件（§0.8.4 条 3）。
2. 跑 §3.3 的统一门禁；记录实测输出（用例数、退出码、自检项数）。
3. 冲突检查：无 `[SUB_AGENT_CONFLICT]`（§6.6.1）。
4. 输出该批**简报**（提示词 §六 格式的批次行）＋**待人工提交清单**（文件列表；**不执行 git**）。
5. 更新 `docs/task-records/` 中本轮任务记录的「轮次」段（逐步追加，禁止编造）。

### 3.5 最终收尾（全部批次完成后）

- 跑 plan.md **§6.2 自检清单**（范围／质量／一致性共 15 项）
- 跑 **§6.6.3 最终验收**：汇总各批 `[SUB_AGENT_COMPLETE]` → 核对交付物 → 无未决冲突 → 输出最终报告并标 `[REQUIRES_HUMAN_CONFIRMATION]` 交人工验收
- 明确挂起项：**P-2（人工 build ＋ 真机 `.xls` 验证）** 与所有 **真机行为类**条目（`B-06`／`B-07`／`B-08`／`B-10`／`B-11`、`A-02`/`A-17` 的 exe 面）

---

## 4. 假设与决策

| # | 决策 | 来源 |
|---|---|---|
| **D1** | 施工依据**只有** plan.md；本提示词不提供实现细节 | 提示词开篇 |
| **D2** | 按批执行、每批门禁、**前批未过不得开下批**；B 类与 A 链无依赖者可并行 | 提示词 §二／plan §1.1 |
| **D3** | **不执行 git**：AGENTS.md §1「Git 操作由人工接管，Agent 不执行」**优先于**提示词 §七的"建议提交" → 改为每批输出「待人工提交清单」 | `AGENTS.md` §1（约束层） |
| **D4** | **P-0 授权执行**（下沉 `AGENTS.md` 3 处＋登记锚点＋跑 `doc_verify`）；红线 §2.1／§2.2 **一字不动** | 人工裁定（2026-10-18） |
| **D5** | 门禁**按 plan.md 用 conda**（`CPS-GPES_RPA-py311`），并置 `QT_QPA_PLATFORM=offscreen` | 人工裁定（2026-10-18） |
| **D6** | 实测代码位置与 plan.md 不符处，**以源码为准**并在 plan.md 标注 `[ADJUSTED: 原因]` | 提示词 §一-4 |
| **D7** | 关键发现：`A-01`＋`A-10` 必须**同时**调 `register_import_root()`，否则阶段 3 兜底补导必失败（§2.2-1） | Phase 1 实测 |
| **D8** | Sub-Agent 只按**行区间**读取 plan.md 的相关条目，不整读（412 KB 超 Read 上限） | plan.md §0.8.1 |
| **D9** | `B-45`~`B-79` **本轮不施工**（仅登记）；`B-01`~`B-44` 由 `Agent-B1` **串行**执行（同批次不拆分，遵 §0.8.2） | plan.md §1.1 |
| **D10** | 门禁失败处置：**先判性质**——"修复暴露旧缺陷"则登记并调整该条验收；"本批引入回归"则回滚该批并 `[SUB_AGENT_BLOCKED]` | 工程判断 |
| **D11** | 停手条件：① 门禁连续 2 次不过且无法定位；② 需触碰硬约束边界（引擎调度／GUI 布局／步骤函数语义）；③ 上下文预算耗尽（停在批界并输出进度报告） | plan.md §6.1 应急 |
| **D12** | 每批改前备份到 `_temp/ImportData/backup/<批>/`（遵各条目 §6「回滚方式」） | plan.md 各条目 §6 |

---

## 5. 验证步骤

| # | 验收项 | 判据 |
|---|---|---|
| V1 | P-0 容量 | `doc_verify.py` `PASS`；含 CR ≤8000／loneCR=0／loneLF=0／余量 ≥200 |
| V2 | P-0 锚点 | `AGENTS.md` 当前任务锚点含本轮目标＋状态＋轮次＋详情索引；`docs/task-records/2026-10-18-importdata-repair.md` 存在 |
| V3 | P-0 占位清零 | plan.md §0.7 的 **8 项 P0 级**均不含 `[UNVERIFIED]`（已回填实测行号） |
| V4 | P-0 回写 | plan.md 含 3 处 `[ADJUSTED:` 标注（`A-01` §3/§4、`B-33`） |
| V5 | 每批门禁 | ① 用例数 ≥118 且 `OK` ② 双 smoke 退出码 0 ③ 自检 `ok==True` 且 6 项 |
| V6 | 每批交付物 | `§8 Agent 执行指引` 的「完成判定」逐条勾选；产物文件实际存在 |
| V7 | 场景验收 | P0→S1；P1→mtime 恢复＋双副本；P2→脏表头隔离；P3→合并格分组；P4a→类型保真／日期／`NA`／错误值；P4b→旧表完好＋空壳表补导；P5→报告＋元数据＋失败清单；P6→大表提示（plan.md Part 5 §5.2） |
| V8 | 冲突 | 无未决 `[SUB_AGENT_CONFLICT]` |
| V9 | §6.2 自检清单 | 15 项全过（范围／质量／一致性） |
| V10 | 未越界 | 未改引擎调度结构／GUI 布局／步骤函数语义；无新第三方依赖；无 `eval`/`exec`/`pickle`；无绝对路径 |
| V11 | 闭合 | `problem.md` 只读未改；plan.md §6.3 仍 101 行 |
| V12 | 挂起项透明 | 最终报告明列 **P-2** 与真机行为类条目的待人工验证清单 |

---

## 6. 执行顺序（批准后）

1. **P-0**：读 `AGENTS.md` 相关节 → 下沉 3 处 → `doc_verify` ＋容量复测 → 登记锚点＋任务记录 → 清 3 项占位 → 回写 3 处 `[ADJUSTED]`。
2. **P0**：分发 `Agent-P0`（前缀＝§0.1/0.2/0.2.1）→ 7 项按序施工 → 抽查＋门禁 → 简报＋待提交清单。
3. **P1** → **P2** → **P3**：逐批同上（P3 为新建模块，注意 `spec.hiddenimports` 已由 P0 的 `A-17` 预置了 `'ops.excel_normalizer'`）。
4. **P4a ∥ P4b**：两 Agent 并行（文件不重叠）→ 各自门禁 → 合并验收。
5. **P5** → **P6**：逐批同上。
6. **B 类**：P0 通过后即启动 `Agent-B1`（串行 `B-01`~`B-44`），与 A 链 P1~P6 并行推进；每完成一组（如每 10 项）输出一次简报。
7. **收尾**：§6.2 自检 ＋ §6.6 最终验收 → 输出完成报告（提示词 §六格式）并标 `[REQUIRES_HUMAN_CONFIRMATION]`。

---

## 7. 待人工确认项（执行中随时提出）

| # | 事项 | 触发条件 |
|---|---|---|
| Q-1 | `A-17` 改 `spec`／`requirements` 属交付配置；**exe 重建与真机 `.xls` 验证（P-2）由人工执行** —— 我改文件后会把验证挂起并在报告中标明 | 执行 P0 时 |
| Q-2 | 若某批改动使既有 118 用例失败，且判定为"修复暴露旧缺陷" → 我会登记为新发现并**回报**后再决定是否调整该条验收 | 门禁失败时 |
| Q-3 | 若 `register_import_root()` 的调用点与 plan.md 描述不符（如 GUI 侧无合适位置） → 以源码为准回写 `[ADJUSTED]`；若因此需放宽安全边界 → 先 `[REQUIRES_HUMAN_CONFIRMATION]` | 执行 P0 时 |
