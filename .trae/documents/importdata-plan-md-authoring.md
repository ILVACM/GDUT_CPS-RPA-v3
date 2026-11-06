# 计划：编写 `_temp/ImportData/plan.md`（ImportData 修复施工图）

> 计划日期：2026-10-17 ｜ 目标交付物：`_temp/ImportData/plan.md`（覆盖写入）
> 运行方式：A（单 Agent；本任务为单文件长文生成，全局一致性要求强，无并行价值）
> Specialist 路由：`architecture-decisions`（范围边界与落点裁定；本轮已 Read 加载）

---

## 1. 摘要

把 `_temp/ImportData/problem.md`（v8 定稿，959 行，A 类 19 ＋ B 类 79）转化为**另一 Agent 可直接开工的代码级施工图** `_temp/ImportData/plan.md`，结构为 Part 0~6（按提示词第二章），逐项采用七段式模板（提示词第三章）。

**关键结论（本轮 Phase 1 实证 + 4 项人工裁定）**

| # | 事项 | 裁定 |
|---|---|---|
| 1 | 输入路径 | `_temp/ImportData/problem.md` **已存在**（959 行 / 94,933 字节，＝上一轮 v8 定稿；`solve-problem` 已改名 `ImportData`）→ 无需 `[REQUIRES_HUMAN_CONFIRMATION]` |
| 2 | P0 顺序与代码事实冲突 | **按代码事实调整**（提示词允许，Part 1 写明理由与证据） |
| 3 | B 类展开深度 | **分层**：A 19 ＋ REQ 12 ＋ B(P0/P1) 44 → 全七段式；B(P2/P3) 35 → 精简四段 |
| 4 | R4 公式求值 | **只做兜底路径**（读 openpyxl 缓存值；缓存空则保留公式文本＋告警）；win32com 分支标「需人工裁定后另行立项」 |
| 5 | 规范化落点 | **新建 `rpa_engine/ops/excel_normalizer.py`**；`excel_preprocessor.py` 保持搬运/读取职责、**不改函数签名** |

**不做**：任何代码修改、编译、运行、安装。

---

## 2. 现状分析（Phase 1 实证，一手证据）

### 2.1 已一手复核的链路事实（用于写「现状与缺陷判定」段）

| 环节 | 文件::函数::行号 | 关键事实（已核实） |
|---|---|---|
| 复制入临时区 | `rpa_engine/ops/excel_preprocessor.py::validate_and_copy` L29-67 | L49-50 仅收 `.xlsx/.xls`；L58-63 同名冲突**只比同后缀**；L65 `shutil.copy2`（保源 mtime）；**返回临时副本路径** |
| xls→xlsx | `::ensure_xlsx` L70-128 | L102 `pd.read_excel(src, engine="xlrd", sheet_name=None)`；L117-119 `with_suffix(".xlsx")` 无冲突检测、`wb.save` 无条件覆盖 |
| 轻量扫描 | `::scan_sheets` L131-168 | L155 `load_workbook(read_only=True, data_only=True)`（只读元信息） |
| 按表头读取 | `::read_excel_sheet` L171-220 | L210-215 `pd.read_excel(skiprows=header_row-1, header=0)`：**无 dtype/无 na_values/无 merge/无 hyperlink/无公式求值/无清洗** |
| 导入 SQLite | `rpa_engine/ops/table_importer.py::import_excel_table` L29-101 | L85 重复表头**仅告警**；L91 `import_dataframe(..., if_exists="replace")` |
| 落库收口 | `rpa_engine/ops/sqlite_manager.py::import_dataframe` L124-155 | L148-149 `with txn(conn): df.to_sql(...)`；L140 docstring 称「事务自动回滚」 |
| 事务实现 | `rpa_engine/ops/sql_safety.py::txn` L258-277 | 仅 commit/rollback；**DDL 语义由连接隔离级别决定** |
| 会话连接 | `rpa_engine/ops/session_db.py::SessionDB.__init__` L37-59 / `new_connection` L64-80 | 库名 `{session_id}.db`（**无 PID**）；`sqlite3.connect()` **未设 `isolation_level`** → 默认 legacy ⇒ **DDL 自动提交成立**（A-15/DM-30 由「结构成立」升级为**已核实**） |
| 确认并导入 | `rpa_engine/gui/main_window.py::_on_confirm_import` L241-400 | L257 `_close_session()` **先于**导入；L302-306 用 `e["file_path"]`（副本路径）；L322-328 逐表 try/except（**不含 ImportError/BadZipFile/ParseError**）；L328 只传 `str(err)`；L335-341 身份只比 `sheet_name` |
| 选文件槽 | `rpa_engine/gui/page_input_selection.py::_on_add_files` L376-429 | L402/L406 `_temp_copies.append`；L417 异常元组 `(FileNotFoundError, ValueError, PermissionError)`；L429 `setEnabled` |
| 副本清理 | `::clear_temp_copies` L357-374 | L367 `p.unlink()`；`_temp_copies` 初始于 L287 |
| 条目导出 | `::get_entries` L324-335 | 仅导出 `file_path/sheet_name/alias/header_row`（**无 source_path**） |
| 全局兜底 | `rpa_engine/gui/app.py::_excepthook` L259-266 | L264 直弹 `str(exc_value)`，未过翻译层 |
| 翻译层 | `rpa_engine/gui/error_messages.py::translate_error` L44-52 / `_RULES` L20-41 | 对输入 `.lower()` 后按**类名小写**匹配（`permissionerror` 在 L25）⇒ 键小写**正确**，断点在调用方丢类名 |
| 步骤执行 | `rpa_engine/ops/step_executor.py` L296-316 | L299 丢弃 `entry["func"]` 返回值 → 恒 `success=True` |
| 类型转换 | `rpa_engine/ops/table_schema.py::convert_dtype` L105-203 | L187-197 `INSERT ... SELECT` **无 CAST**；L203 恒 `return True` |
| 产表守卫 | `rpa_engine/ops/table_lifecycle.py` L95-140 / `merge_tables` L143-211 | `copy_table` L117-118 以 `src==dst` 拦截；`merge_tables` **无** `dst ∈ table_names` 守卫 |
| 补导 | `rpa_engine/engine/executor.py::ensure_input_tables` L80-111 | L92 仅判 `table_exists`；L110 只捕 `(ValueError, FileNotFoundError)` |
| 工作线程 | `rpa_engine/gui/worker.py` L61-122 | L112-117 `conn.commit()` 有 try、**`conn.close()` 裸调用**；L121 emit |

### 2.2 提示词前提与代码事实的冲突（已在 Part 1 说明）

提示词第四章 P0 断言「当前问题是导入直接失败导致流程中断 → 须先建容错骨架」。**代码事实否证**：
1. 逐表 `try/except` **已存在**（`main_window.py:322-328`）；
2. 主症状真根因是**副本先删后导入**（`_close_session()` L257 → `clear_temp_copies()` L367 → 导入读 `e["file_path"]` L303），抛出的是 `FileNotFoundError`——**已被捕获**。
⇒ 先建骨架治不了主症状。故 P0 调整为「**解锁导入链路 ＋ 异常元组扩容**」（详见 §3.2）。

### 2.3 执行期仍需补读的文件（用于填精确行号）

`gui/page_operation_config.py`、`gui/forms.py`、`gui/models.py`（`main_buttons` L127 / `default_params` L917 / `collect_file_stats` L940 已知）、`gui/page_report.py`、`gui/graph_edges.py`、`gui/node_graph.py`、`gui/user_template_manager.py`、`engine/parser.py`、`engine/validator.py`、`ops/exporter.py`、`ops/filter_dedup.py`、`ops/aggregator.py`、`ops/mapping_matcher.py`、`ops/table_importer.py`（已读）、`page_input_selection.py::_scan_sheets` L623 / `_preview_rows` L644、`rpa_engine/tests/test_step_catalog.py`。
未读到精确行号者一律标 `[UNVERIFIED]` 并列入 Part 6 补全清单。

---

## 3. 变更内容（交付物结构，decision-complete）

### 3.1 改造项总清单与计数规则（**须写进 Part 0**）

| 类型 | 数量 | 来源 | 闭合要求 |
|---|---|---|---|
| **DEF-A** | **19** | `problem.md` 的 A 类 19 条（覆盖 21 个原编号） | 与 problem.md **1:1** 闭合 |
| **DEF-B** | **79** | `problem.md` 的 B 类 79 条（覆盖 80 个原编号） | 与 problem.md **1:1** 闭合 |
| **REQ** | **12** | 需求规则中**零 problem.md 编号**的缺失实现 | 单列，标注「来源＝需求规则编号」 |
| 合计 | **110** | — | 见 Part 6 闭合表 |

**REQ 判定规则（写进 Part 0，消除 §5.3 字面冲突）**
- 若某需求规则的实现**恰好由某 A 类问题的修复完成** → **不单列 REQ 项**，仅在该 A 项「对应规则」标注；
- 若某需求规则**在 problem.md 完全无对应编号** → 单列 `REQ-??`，并在 Part 0 声明「来源＝需求说明第一/二章的需求规则，非新增问题」。

**据此得到的 REQ 12 项**：`REQ-R2`（指定行全空拒绝）、`REQ-R4`（公式兜底求值）、`REQ-R5`（超链接展开）、`REQ-R7`（trim/`\x00` 清洗与空值口径）、`REQ-H1`（重复列名报告化）、`REQ-H3`（布尔→1/0＋元数据）、`REQ-H4`（错误值→NULL＋原文留痕）、`REQ-H5`（全空列标记/尾部空行裁剪）、`REQ-H6`（图片/图表/批注丢弃＋告知）、`REQ-H7`（超长数字扫描期提示）、`REQ-H9`（元数据表＋处理报告＋失败清单落盘）、`REQ-H10`（`temp/normalized/` 幂等与目录管理）。
**不单列**：R1→A-02/A-17；R3→A-05；R6→A-04；H2→A-06/A-07；H8→A-09。

### 3.2 修复顺序（P0~P6 ＋ 待裁定批 ＋ B 类）

| 优先 | 内容 | 项数 | 前置依赖 | 可并行 |
|---|---|---|---|---|
| **P0** | **解锁导入链路 ＋ 异常隔离骨架**：A-10（导出 `source_path`）→ A-19（身份三元组）→ A-01（副本顺序/路径口径）→ A-02（异常元组扩容＋按钮复位）→ A-13（失败清单带类名）→ A-14（excepthook 过翻译层）→ A-17（`spec` 补 `'xlrd'` ＋ `requirements` 改 `xlrd>=2.0`） | 7 A | 无 | ❌（批内有序） |
| **P1** | 临时区与格式转换：A-11（`copy2`/清理顺序）、A-12（同名异后缀覆盖）、A-18（转换产物冲突检测） | 3 A | P0 | 同文件 → **建议串行提交** |
| **P2** | 表头规范化：A-03（表头禁字符预检）＋ REQ-R2 | 1 A＋1 REQ | P1 | ❌ |
| **P3** | 单元格处理 R3/R4/R5：A-05（合并格拆分填充）＋ REQ-R4 ＋ REQ-R5 | 1 A＋2 REQ | P2 | ✅ 三项彼此并行 |
| **P4** | 类型/内容/特殊值：A-04、A-06、A-07、A-08 ＋ REQ-R7、REQ-H3、REQ-H4 | 4 A＋3 REQ | P3 | ❌（同一读入口） |
| **P5** | 元数据与报告：REQ-H1、REQ-H5、REQ-H6、REQ-H7、REQ-H9、REQ-H10 | 6 REQ | P4 | 部分可并行（H9 与 H1/H5/H6/H7 有产出依赖） |
| **P6** | 接入导入流程：A-09（H8 扫描/预处理分离＋主线程）＋ **端到端联调**（新建模块接线、阶段切换、GUI 错误回显） | 1 A | P5 | ❌ |
| **P-待裁定** | A-15（写库非原子）、A-16（空壳表跳过补导） | 2 A | **`G-5` 方案经人工裁定**（裁定 G.1-8） | ❌ |
| **B 类** | P0 13 ＋ P1 31 ＝ 44 项（全七段式）；P2 5 ＋ P3 30 ＝ 35 项（精简四段） | 79 B | 与 A 类无依赖者可随时并行 | ✅ |

**顺序调整说明（必写进 Part 1）**：依据 §2.2 的三条代码证据，把「解锁导入链路」提到原 P0 的「异常隔离骨架」之前并合并为同一批；其余 P1~P6 沿用提示词原序。

### 3.3 交付物结构（Part 0~6）

```
Part 0  计划概览：范围｜硬约束｜前置条件（AGENTS 容量腾空、G-5 方案待裁定）｜术语（DEF/REQ/三形态/Layer0）
        ＋ 改造项总清单与计数规则（§3.1）＋ 已合并项声明（J-03→A-02、B-01→A-17、G-07→B-12）
Part 1  修复顺序与依赖图：§3.2 表 ＋ 顺序调整说明 ＋ 可并行标注
Part 2  A 类逐项改造方案：A-01…A-19（19 项，全七段式）
Part 2' 规则落地项：REQ-R2/R4/R5/R7/H1/H3/H4/H5/H6/H7/H9/H10（12 项，全七段式）
Part 3  B 类逐项处理方案：B-01…B-44（七段式）；B-45…B-79（精简四段）
Part 4  新增/修改文件清单与接口契约：逐文件列出「新建/修改＋改动点＋签名是否变化」；含 spec/requirements 登记项
Part 5  验证矩阵：问题 → 用例 → 通过判据（逐项一行，含样本构造）
Part 6  回滚与应急预案 ＋ 自检清单（含闭合性核对表、[UNVERIFIED] 清单、待人工补全清单）
```

### 3.4 接口契约（Part 4 必写）

| 项 | 契约 |
|---|---|
| `rpa_engine/ops/excel_normalizer.py`（新建） | 对外唯一入口 `normalize_sheet(file_path, sheet_name, header_row, *, extra_inputs=None) -> NormalizeResult`；`NormalizeResult` 至少含 `dataframe`（表头在第 1 行）、`meta`（逐列原始 Excel 类型/曾为公式/曾为超链接/曾被拆合并格）、`report_entries`、`warnings`；**不得**自行建 SQLite 连接（AGENTS §2.2 条 4） |
| `excel_preprocessor.py`（修改） | **5 个既有函数签名与返回值保持不变**；只允许新增薄调用 |
| `table_importer.py`（修改） | `import_excel_table(conn, xlsx_path, sheet_name, header_row, table_name, sheet_info=None, cancel_check=None) -> int` **签名不变**；内部改为经 normalizer 取 DataFrame |
| `sqlite_manager.import_dataframe`（修改，仅 A-15 批） | 签名不变；改造为「临时表 → 校验行数 → 原子 rename」 |
| `main_window.py::_on_confirm_import`（修改） | 不改 GUI 布局；仅改导入调用点（`source_path` 优先）、异常元组、身份比对、失败清单文本 |
| `RPA_Workflow_v3.spec` / `requirements.txt` | `hiddenimports` ＋1 项 `'xlrd'` ＋1 项 `'ops.excel_normalizer'`（若 PyInstaller 不在 ops 包发现则显式列出）；`xlrd` → `xlrd>=2.0` |

### 3.5 生成策略（分批写入，避免单次超长）

| 批 | 内容 | 预估 |
|---|---|---|
| 1 | Part 0 ＋ Part 1 | ~180 行 |
| 2 | Part 2（A 19 项七段式） | ~650 行 |
| 3 | Part 2′（REQ 12 项七段式） | ~420 行 |
| 4 | Part 3 前段（B-01…B-44 七段式） | ~800 行 |
| 5 | Part 3 后段（B-45…B-79 精简四段） | ~220 行 |
| 6 | Part 4~6 ＋ 完成报告 | ~280 行 |
| 合计 | | **~2550 行** |

写入方式：批 1 用 Write 建文件；批 2~6 用 `[System.IO.File]::AppendAllText`（UTF-8 无 BOM、`\n` 连接）追加，避免单次 Write 超长与截断风险。

---

## 4. 假设与决策

| # | 决策 | 来源 |
|---|---|---|
| D1 | 输入＝`_temp/ImportData/problem.md`（959 行 v8 定稿）；输出＝`_temp/ImportData/plan.md`（覆盖写入） | Phase 1 实测 |
| D2 | P0 按代码事实调整（解锁优先，隔离并入同批），Part 1 写明证据 | 人工裁定 |
| D3 | B 类分层深度：A 19＋REQ 12＋B 44 全七段式；B P2/P3 35 项精简四段（存在性判定／缺陷类型／为何本次不施工／触发条件），Part 6 仍逐条闭合 | 人工裁定 |
| D4 | R4 只做兜底路径（openpyxl 缓存值；空则保留公式文本＋告警）；win32com 分支标「需人工裁定后另行立项」，**不引入 pywin32** | 人工裁定 |
| D5 | 新建 `rpa_engine/ops/excel_normalizer.py`（承载 R3/R4/R5/R6/R7＋H1~H7 规范化与元数据）；`excel_preprocessor.py` 不改函数签名 | 人工裁定 |
| D6 | REQ 项 12 项单列并声明来源（解法见 §3.1 判定规则），不视为「problem.md 之外的新问题」 | 依提示词第零章 1 ＋ 第四章 P1~P5 反推 |
| D7 | A-15/A-16 列入「P-待裁定」，前置＝`G-5` 方案经人工裁定（裁定 G.1-8）；本轮 plan.md 只写方案骨架、标注前置 | problem.md 附录 G |
| D8 | 未读到精确行号处标 `[UNVERIFIED]` ＋ 进 Part 6 补全清单；不猜测填充 | 提示词第零章 2 |
| D9 | 全部路径用项目相对路径（禁 `D:\`/`C:\`）；不改函数签名/返回值/异常约定（除明确要求项） | 提示词第五章 |
| D10 | 不施工：不写代码、不编译、不运行、不安装、不跑 `build.bat`、不执行 git | 提示词 1.2/第五章 |

---

## 5. 验证步骤（交付物写完后自检）

| # | 验收项 | 判据（可脚本化） |
|---|---|---|
| V1 | 闭合性（DEF） | DEF-A 19 ＋ DEF-B 79 覆盖 problem.md 全部 101 个原编号；Part 6 闭合表行数 ＝ 101 |
| V2 | 条目计数 | A 19 ／ REQ 12 ／ B 79 ＝ 110，与 Part 0 声明一致 |
| V3 | 七段式完整性 | 75 项（19＋12＋44）均含 `#### 1. 定位`…`#### 7. 验收标准` 七段，缺段数 ＝ 0 |
| V4 | 规则映射 | 每条 DEF-A 与 REQ 项「对应规则」含 ≥1 条 `R1~R7`/`H1~H10` |
| V5 | 无模糊表述 | 禁词扫描（`优化此处`/`完善逻辑`/`酌情`/`适当`/`尽量`/`视情况`/`合理处理`/`等等`）命中 ＝ 0 |
| V6 | 相对路径 | 全文无 `D:\`、`C:\` 绝对路径 |
| V7 | 验收标准可勾选 | 每项含 `- [ ]`，且为可客观判断（不含"体验更好"类主观词） |
| V8 | 占位透明 | `[UNVERIFIED]` 全部集中在 Part 6 补全清单，数量与正文标注数一致 |
| V9 | 降级策略齐备 | R4/A-02/A-17 等含 COM 或 Office 缺失场景，均写明兜底行为与告警方式（不得留白） |
| V10 | 未施工声明 | Part 6 与完成报告各含「未改代码／未编译／未运行／未引入新依赖／范围未越界」声明 |
| V11 | 体量与可读 | 总行数 2000~3000；Part 结构完整（Part 0~6 二级标题齐备） |

---

## 6. 执行顺序（批准后）

1. 补读 §2.3 列出的文件（只读），取精确行号；未取到处标 `[UNVERIFIED]`。
2. 生成批 1（Part 0＋1）→ 批 2（Part 2）→ 批 3（Part 2′）→ 批 4（B P0/P1）→ 批 5（B P2/P3）→ 批 6（Part 4~6＋报告）。
3. 每批写完后立即抽检该批的七段式完整性（避免累积返工）。
4. 全量写完后跑 §5 的 V1~V11 自检，输出实测证据（计数、禁词命中、路径扫描、缺段数）。
5. 输出完成报告（提示词第七章格式）＋ `[UNVERIFIED]`/待人工补全清单。

---

## 7. 待人工确认项（若执行中发现）

| # | 事项 | 触发条件 |
|---|---|---|
| Q-1 | 若补读发现某 REQ 项其实已有 problem.md 编号（或反之）→ 调整 REQ 计数并回报 | Step 1 补读后 |
| Q-2 | 若 `excel_normalizer.py` 的新增需在 `BUILTIN_OPS`／功能函数记录表登记（判定为"非功能函数、仅 Layer 0 模块"）→ 若判定不成立，须回报人工 | Step 3 起草 Part 4 时 |
| Q-3 | 任何 `[NO_CODE_MATCH]` 或与 problem.md 记载冲突的新发现 | 全程 |
