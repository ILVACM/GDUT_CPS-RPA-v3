# 计划：problem.md 修订 —— 导入阻断性问题分类与关联代码分析

> 计划日期：2026-10-17 ｜ 目标文件：`_temp/solve-problem/problem.md`（覆盖重写）
> 运行方式：A（单 Agent，只改 `_temp/` 下 1 份 md ＋ 1 份 .bak）｜ 模式 B 不需要（无并行价值，全局一致性要求强）
> Specialist 路由：`architecture-decisions`（设计边界与范围裁定；已 Read 加载）

---

## 1. 摘要

把 `_temp/solve-problem/problem.md`（现状 665 行、v7）**覆盖重写**为「A/B 二分 ＋ 代码定位 ＋ 规则编号映射」的修订版（v8）：

- **A 类**＝根因落在「Excel 数据表 → SQLite 导入链路」且可被需求规则 R1~R7 / H1~H10 覆盖的阻断问题（含文件级 / 表级 / 单元格级三档阻断等级）；
- **B 类**＝不属于上述范围、但不解决则程序无法启动 / 无法完成 / 无法验证的问题，按 P0~P3 四档优先级排布；
- 每条问题给出 `文件::函数::行号` ＋ 判定（缺少容错 / 逻辑错误 / 缺失实现 / 已废弃）＋ 阻断后果＋规则编号；
- 原编号（F/G/H/J/DM/B/C/D/E/N 系列）**一个不删**，全部在附录 A 映射表可溯源；
- 不可再生的历史资产（原 §5/§6/§9/§10/§11、§8.5 已知取舍）**整段进附录**，不丢失。

**零代码改动**：不触碰 `rpa_engine/**`、`docs/**`、`AGENTS.md`、依赖与构建脚本。

---

## 2. 现状分析（Phase 1 实证）

### 2.1 导入链路的真实构成（一手核实）

| 环节 | 函数 | 文件::行号 | 关键事实 |
|---|---|---|---|
| 复制入临时区 | `validate_and_copy` | `rpa_engine/ops/excel_preprocessor.py::validate_and_copy` L29-67 | L49-50 仅接受 `.xlsx/.xls`；L58-63 同名冲突**只比同后缀**加序号；L65 `shutil.copy2`（**保留源 mtime**） |
| xls→xlsx 转换 | `ensure_xlsx` | 同文件 L70-128 | L102 `pd.read_excel(src, engine="xlrd", sheet_name=None)` 写死 xlrd；L117-119 `with_suffix(".xlsx")` **无冲突检测、`wb.save` 无条件覆盖** |
| 轻量扫描 | `scan_sheets` | 同文件 L131-168 | L155 `load_workbook(read_only=True, data_only=True)` 只读元信息（＝H8 的「扫描侧」已具备） |
| 按表头行读取 | `read_excel_sheet` | 同文件 L171-220 | L210-215 `pd.read_excel(skiprows=header_row-1, header=0)`：**无 dtype 控制、无 na_values、无 merge、无 hyperlink、无公式求值、无内容清洗** |
| 导入 SQLite | `table_importer.import_excel_table` | `rpa_engine/ops/table_importer.py` L29-101 | L85 重复表头**仅告警**（pandas 已自动加后缀）；L91 `import_dataframe(..., if_exists="replace")` |
| 落库收口 | `sqlite_manager.import_dataframe` | `rpa_engine/ops/sqlite_manager.py` L124-155 | L148-149 `with txn(conn): df.to_sql(...)`；docstring 称「事务自动回滚」 |

### 2.2 需求规则 R1~R7 / H1~H10 的现状覆盖度（逐条实证）

| 规则 | 现状 | 证据 |
|---|---|---|
| R1 格式统一 | **部分**：入口已限后缀、xls 已转换；**转换失败无文件级隔离与明确提示** | `excel_preprocessor.py` L49-50、L102；`page_input_selection.py` L376-420 异常元组 |
| R2 表头规范化 | **部分**：`skiprows` 物化已实现；**「指定行全空则拒绝并提示」缺失** | `excel_preprocessor.py` L210-215 |
| R3 合并单元格拆分 | **缺失** | 全链路无 `merged_cells` 处理 |
| R4 公式求值替换 | **缺失**（无 win32com；pandas/openpyxl 读缓存值，缓存空→静默 `None`） | `read_excel_sheet` L210 无 `data_only` 显式控制、无兜底 |
| R5 超链接展开 | **缺失** | 无 `cell.hyperlink` 读取 |
| R6 智能类型推断 | **缺失**（改由 pandas 自行推断） | `read_excel_sheet` L210-215 无 `dtype`/`infer_objects` |
| R7 内容清洗 | **缺失**（无 strip / 无 `\x00` 去除 / 无 `na_values` 控制） | 同上 |
| H1 重复列名 | **部分**（pandas 加后缀 + 仅日志，未入报告） | `table_importer.py` L85-89 |
| H2 日期时间 | **缺失** | 无 ISO 8601 规范化 |
| H3 布尔值 | **缺失** | — |
| H4 错误值 | **缺失** | — |
| H5 全空行/列 | **缺失** | — |
| H6 非单元格内容 | **缺失** | — |
| H7 超长数字精度 | **缺失**（无扫描期检测提示） | — |
| H8 扫描与预处理分离 | **部分**（`scan_sheets` read_only 已具备；预处理侧无独立规范化阶段） | `excel_preprocessor.py` L155 |
| H9 可追溯性 | **缺失**（无处理报告） | — |
| H10 幂等与回滚 | **部分**（副本加序号；**无 `temp/normalized/`、无幂等标记**；单表隔离靠调用方 try/except） | `validate_and_copy` L58-63；`main_window._on_confirm_import` L294-328 |

**结论**：需求 17 条规则中 **10 条完全缺失、6 条部分实现、仅 1 条（H8 扫描侧）实质具备** → A 类条目大量落在「缺失实现」，而非「已实现但写错」。

### 2.3 调用方与异常传播路径（一手核实）

- 阶段 1→2 入口：`main_window.py::_on_confirm_import` L241-400。**逐表 try/except 已存在**（L322-328 捕 `ValueError/FileNotFoundError/PermissionError/OSError/sqlite3.Error`），失败进 `failed[]` 并在 L356-360 弹「部分导入失败」→ **单表隔离是"部分存在"**，不是全无。
- 但该元组**漏 `ImportError`（xlrd）/`zipfile.BadZipFile`/`lxml.etree.ParseError`/`RuntimeError`**：`page_input_selection.py` L376-420 的 `[add]` 侧元组为 `(FileNotFoundError, ValueError, PermissionError)`；`app.py::_excepthook` 直接用 `str(exc_value)` 弹出，**未经 `error_messages.translate_error`**。
- 未捕获异常 → `sys.excepthook` → 文员看到 `No module named 'xlrd'` 原文（违反 AGENTS §2.1 条 6）。
- 环境事实（N-05 成立）：`requirements.txt` 已于 2026-10-05 被外部插入裸 `xlrd`（无版本约束）；`RPA_Workflow_v3.spec` 的 `hiddenimports` **仍无 `'xlrd'`**；全库**无 `import xlrd`**（`engine="xlrd"` 为字符串传参，PyInstaller 静态分析收集不到）→ **exe 态读 `.xls` 仍必失败**。

### 2.4 执行期必须先解决的三处「文档 ↔ 代码」冲突（AGENTS §4.6/§4.7）

子 Agent 复核结果与原 problem.md 记载**不一致**，须在 Step 2 逐条实测裁定，冲突以代码为准并标 `[存在差异]`：

| 冲突点 | 原 problem.md 记载 | 子 Agent 复核 | 处置 |
|---|---|---|---|
| `step_executor` 返回值契约 | 逐字丢弃 ops 返回值、**恒 `success=True`**（§5 根因2 / G-08 / P1-6） | `step_executor.py` L283-316 无输出操作失败时返回 **`success=False`** | Step 2 亲读该段代码实测；结论写进 G-08/P1-6 的「判定」字段 |
| `executor` 中间表清理时机 | `on_error=skip` 仍 `completed` → 中间表被清理（G-10） | `executor.py` L235-249 **失败/取消时不清** | 同上 |
| `copy_table` 的 `dst ∈ 源表` 守卫 | 同文件 L117-118 **有**守卫（G-07 因此定性为"遗漏非设计"） | `table_lifecycle.py` L95-140 **无**该守卫 | 同上 |

> 这三条不定，G-08 / G-10 / G-07 的 A/B 归属与「判定」字段就会写错。

---

## 3. 变更内容（Proposed Changes）

### 3.1 唯一写入面

| 动作 | 路径 | 说明 |
|---|---|---|
| 新建（备份） | `_temp/solve-problem/problem.md.bak` | 覆盖前整体复制原文件，防不可逆丢失 |
| **覆盖重写** | `_temp/solve-problem/problem.md` | 唯一交付物 |
| 不写 | 其余全部路径 | `rpa_engine/**`、`docs/**`、`AGENTS.md`、依赖、脚本、构建产物一律不动 |

### 3.2 目标文件结构（七章 ＋ 附录 A~F）

```markdown
# problem.md（修订版 v8，2026-10-17）
0. 修订说明        性质（_temp 无约束力/不可作执行依据）｜本次口径｜与原 v7 的关系｜编号稳定性声明
1. 一页速读        A/B 计数｜头号问题（F-01）｜B 类四档分布｜硬前置｜可达性口径
2. 分类判定规则     A 类两条款 AND 判据｜B 类四档定义（P0~P3）｜判定四值｜可信度标签表
3. A 类：导入阻断性问题（约 19 项）      按 文件级 / 表级 / 单元格级 三档分组
4. B 类：非导入范围但阻塞运行（其余全部） 按 P0 / P1 / P2 / P3 四档分组
附录 A  问题 → 代码位置 → 规则编号 映射表（行数 = 实测原问题总数，含原编号与状态列）
附录 B  统计（A/B 计数、各档计数、FIXED/OBSOLETE/UNVERIFIED 计数）
附录 C  原 §9 人工裁定 34 项 × 新编号 交叉映射（保留原裁定编号 F1/F2/Q1~Q9/F3~F8/G*/G13~G17 与结论摘要）
附录 D  原 §5（三条系统性根因）＋ §6（source_path 根因拆解）原文保留
附录 E  原 §10（方法论与可信度）＋ §11（建议执行顺序）原文保留
附录 F  §8.5 已知人工取舍 5 项（标 [NON-DEFECT]，不入 A/B）
```

### 3.3 分类判定规则（写进正文第 2 章，供后续复用）

**A 类（两条款 AND，缺一不可）**
1. 问题根因落在「Excel 数据表 → SQLite 导入链路」（读取／预处理／表头／类型推断／建表／插入／连接／临时副本／确认导入调用方／导入失败呈现）；
2. 可被 R1~R7 或 H1~H10 中至少一条覆盖。
→ 必须输出：阻断等级（文件级／表级／单元格级）、规则编号、异常链。

**B 类（其余全部，四档优先级）**
| 档 | 判据（满足任一） | 典型 |
|---|---|---|
| **P0 阻塞运行** | 崩溃／abort／卡死／无法启动／无法完成／无法验证修复效果（含按钮不可见、模板或测试资源缺失） | 启动失败、QThread UB、重入无响应、导出 OOM 写满磁盘、导出先截断、不可逆删表、弃用通路一启用即自检失败 |
| **P1 静默错误结果** | 程序报 ✅、日志无痕、报表直接交付却错 | 丢行／吞值／假成功／假报告／静默 0 行 |
| **P2 体验与格式** | 结果正确性未受损，仅体验／格式／可诊断性受损 | 提示语技术化、后缀静默改写、超时仅进日志 |
| **P3 本次范围外** | 与导入链路及运行阻塞均无关（规约缺口／记录表／环境口径／注释不实） | W-22 守卫与字段缺口、E3/A4 口径、N-01~N-04 |

**判定四值**：`缺少容错`｜`逻辑错误`｜`缺失实现`｜`已废弃`。
**标签**：`[FIXED]`｜`[FIXED-PARTIAL]`｜`[OBSOLETE]`｜`[UNVERIFIED]`｜`[存在差异]`｜`[NO_CODE_MATCH]`｜`[NON-DEFECT]`｜`[REQUIRES_HUMAN_CONFIRMATION]`。

### 3.4 A 类条目初判清单（Step 2 逐条实测后写定）

| 新编号 | 原编号 | 规则 | 等级 | 代码位置（已核实） | 初判 |
|---|---|---|---|---|---|
| A-01 | F-01 | R1＋H10 | 文件级 | `page_input_selection.py::clear_temp_copies` L357-374 ↔ `main_window.py::_on_confirm_import` L302-306（用副本路径、清理先于导入） | 逻辑错误 |
| A-02 | H-01＋**J-03**（合并，J-03 保留交叉引用） | R1＋H10 | 文件级 | `page_input_selection.py::[add] 异常元组` L417 ＋ `excel_preprocessor.py::ensure_xlsx` L102 ＋ `RPA_Workflow_v3.spec::hiddenimports` | 缺少容错 |
| A-03 | G-06 | R2 | 表级 | `sql_safety.py::标识符禁字符校验` L35-66 ＋ `table_importer.py::import_excel_table` L91（表头无清洗） | 缺少容错 |
| A-04 | J-01 | R6 | 单元格级 | `excel_preprocessor.py::read_excel_sheet` L210-215（无 dtype 控制） | 缺失实现 |
| A-05 | H-09 | R3＋H8 | 表级 | 同 A-04 位置（无 merged 处理） | 缺失实现 |
| A-06 | H-15 | H2 | 单元格级 | 同上 | 缺失实现 |
| A-07 | H-16 | H2 | 单元格级 | 同上（日期带时间部分入库致等值筛选 0 行） | 缺失实现 |
| A-08 | H-06 | R7 | 单元格级 | 同上（无 `na_values` 控制，字面 `NA`→NULL） | 缺失实现 |
| A-09 | F-08 | H8 | 表级 | `main_window.py` L294-306（主线程全量导入）＋ `excel_preprocessor.py::scan_sheets` L155（扫描侧已只读） | 缺少容错 |
| A-10 | H-04 | R1＋H10 | 文件级 | `page_input_selection.py::get_entries` L324-335（不导出 `source_path`） | 逻辑错误 |
| A-11 | H-05 | H10 | 文件级 | `excel_preprocessor.py::validate_and_copy` L65（`copy2` 保 mtime）↔ 启动超龄清理 | 逻辑错误 |
| A-12 | F-09 | H10 | 文件级 | `excel_preprocessor.py::validate_and_copy` L58-63 ＋ `::ensure_xlsx` L117-119 | 逻辑错误 |
| A-13 | H-21 | R1＋产物4 | 文件级 | `main_window.py` L328（`str(err)` 丢异常类名）＋ `error_messages.py` L18-51（规则键全小写不匹配） | 缺少容错 |
| A-14 | H-24 | R1 | 异常传播 | `app.py::_excepthook` L259-266（未经 `translate_error`） | 缺少容错 |
| A-15 | DM-30 | 产物2＋H10 | 表级 | `sqlite_manager.py::import_dataframe` L148-149（DDL 自动提交、非原子建表） | 逻辑错误 |
| A-16 | DM-31 | H10 | 表级 | `executor.py::ensure_input_tables` L80-111（仅判表存在，空壳表跳过补导） | 缺少容错 |
| A-17 | DM-01 | R1 | 文件级 | `requirements.txt` ＋ `spec hiddenimports` | **[FIXED-PARTIAL]**（依赖已插、打包侧仍缺） |
| A-18 | DM-03 | H10 | 文件级 | `excel_preprocessor.py::ensure_xlsx` L117-119（转换产物无冲突检测） | 缺少容错 |
| A-19 | H-18 | R1＋H10 | 文件级 | `main_window.py` L335-341（身份只比 `sheet_name`） | 逻辑错误（**边界项**，见 §4-A10） |

> 边界与例外：**F-04／H-12／H-13／H-14／H-19／H-20／H-03／H-26／G-01／G-02／G-03** 根因在 `forms.py`／`page_operation_config.py`（非导入链路）→ 归 B；**J-06／G-07／J-07／J-08／H-11／H-23** 仅手写 JSON 可达、根因在 ops 产表逻辑（非导入链路）→ 归 B；**G-07 与 J-06 合并为「产表操作不可逆删表」同一条**（依据原 §9-G6 裁定）。

### 3.5 条目字段模板（写进正文，逐条填）

**A 类（7 字段，缺一不可）**
```
### A-01 [原编号: F-01] [R1][文件级] 标题
- 现象：
- 根因：
- 代码位置：`文件路径::函数名`（含行号）
- 判定：缺少容错 / 逻辑错误 / 缺失实现 / 已废弃
- 阻断后果：→ 具体异常链（单元格读取失败 → … → 整轮入库失败 / GUI 卡死）
- 对应规则：R1（＋H10）
- 备注：[FIXED-PARTIAL] / [存在差异] / [UNVERIFIED] / [NO_CODE_MATCH]（按需）
```
**B 类（6 字段）**
```
### B-01 [原编号: xx] [P0] 标题
- 现象：
- 为何不归入 A 类：
- 不解决的后果：（崩溃 / 流程卡死 / 无法启动 / 无法完成 / 无法验证修复 / 静默错误结果）
- 触发环节：
- 代码位置：
- 建议优先级：P0（理由一句话）
```

### 3.6 附录 A 映射表列定义

| 原编号 | 归属（A/B） | 阻断等级／优先级 | 规则编号 | 代码位置 | 状态 |
|---|---|---|---|---|---|
| F-01 | A（A-01） | 文件级 | R1＋H10 | `page_input_selection.py::clear_temp_copies` L357-374 | 有效 |
| J-03 | A（并入 A-02） | 文件级 | R1 | `page_input_selection.py` L417 | 已合并 |

**行数 = 实测原问题总数**（Step 2 用枚举清点后写定，见 §4-A2）。

### 3.7 Step 1~4 与提示词的对应

| 提示词步骤 | 本计划落点 |
|---|---|
| Step 1 读取 | 按已批准清单（约 20 文件，见 §2 已实测部分）；无需再取新文件 |
| Step 2 裁定矩阵 | 逐条提取原编号 → 判 A/B → 定位代码（`文件::函数::行号`）→ 匹配规则（A）／写「为何不归入 A」（B）→ 写阻断后果；**同时解决 §2.4 三处冲突** |
| Step 3 清理 | 标 `[FIXED]`／`[FIXED-PARTIAL]`／`[OBSOLETE]`；合并重复（J-03→H-01；G-07＋J-06；P1-1↔H-19、P1-2↔F-07、P1-6↔G-08 三组重叠按原 §9-Q8 合并保留双向引用） |
| Step 4 重写 | 覆盖 `problem.md` ＋ 附录 A~F ＋ 自检 |

---

## 4. 假设与决策（Assumptions & Decisions）

| # | 决策 | 来源 |
|---|---|---|
| A1 | 非 A 非 B 的问题**并入 B 类**，用「建议优先级」字段分 P0~P3 四档；正文只保留 A/B 两节 | 人工裁定（2026-10-17） |
| A2 | **全量收录**：§4 故障级 59 ＋ §7 台账组（DM-01/DM-03/DM-24/DM-30/DM-31/B-01/B-02/B5/D4/G-5/G-7）＋ §7.5 W-22 群（B1~B9/C1/C2/D1~D4/E1 与 E3/A4、P1-1/P1-2/P1-6/P2-1/P2-2）＋ §8.2 注释谎报 4 处 ＋ §8.3 环境发现 N-01~N-05 → 实测清点后写定（预估 ≈99 行）；`H-10` 为空号不计数 | 人工裁定（2026-10-17） |
| A3 | 原 §5/§6/§10/§11 **原样保留**为附录 D/E，不改写、不拆并 | 人工裁定（2026-10-17） |
| A4 | 原 §9 34 项裁定保留为**附录 C 交叉映射**（原裁定编号＋结论摘要），后续章节引用一律指向附录 C | 人工裁定（2026-10-17） |
| A5 | 读取清单批准全量（约 20 文件） | 人工裁定（2026-10-17） |
| A6 | §8.5「已知人工取舍」5 项**不入 A/B**，单列附录 F 标 `[NON-DEFECT]` | 该节原文已自述「不是缺陷」 |
| A7 | 覆盖前先落 `problem.md.bak` 备份 | 防不可逆丢失（不可再生裁定资产） |
| A8 | 文档 ↔ 代码冲突一律**以代码为准**，并标 `[存在差异]`（§2.4 三处 + Step 2 新发现） | AGENTS §4.6／§4.7 |
| A9 | 不新增问题编号、不改需求规则定义，只做匹配；无法对应代码者标 `[NO_CODE_MATCH]`，不确定处标 `[UNVERIFIED]` | 提示词硬性约束 |
| A10 | `H-18` 列为 **A 类边界项**（根因在导入确认调用方 `main_window.py` L335-341，且原 §9-G3 明令「须修」）；备注注明「若不认可可降 B/P1」 | 本计划判断，**待人工确认** |
| A11 | H-24 与 A-02 同因（xlrd `ImportError` 未经翻译层），A/B 归属按「异常传播路径」纳入 A 并备注交叉引用 | 本计划判断 |
| A12 | `_temp/` 文件变更**豁免锚点机制**（AGENTS §7.3 任务定义①仅指非临时目录文件）；problem.md 无约束力（AGENTS §6）故**不强制**跑 `doc_verify.py`，也不更新「当前任务锚点」 | AGENTS 规约 |
| A13 | Git 提交由人工接管，Agent 不执行任何 git 写操作 | AGENTS §1 |
| A14 | 不执行 `build.bat`、不安装依赖、不修改 `requirements.txt`／`spec`（仅作为证据引用） | R2 裁定 |

---

## 5. 验证步骤（Verification）

| # | 验收项 | 判据 |
|---|---|---|
| V1 | 备份完整 | `problem.md.bak` 存在且与原文件逐字节一致（比对行数 665 ＋ hash） |
| V2 | 映射表行数 | 附录 A 数据行数 **== 实测原问题总数**（枚举清点脚本输出，逐项对齐，无多无少） |
| V3 | 无重叠无遗漏 | A∪B 的原编号集合 == 全部原编号；A∩B == ∅；`H-10` 已标注为空号 |
| V4 | A 类规则齐备 | 每个 A 项**至少一条**规则编号（R1~R7 或 H1~H10），无空值 |
| V5 | 代码位置可核 | 全部 `文件::函数::行号` 经 Read/Grep 复核真实存在；不得出现不存在的文件或函数；冲突项标 `[存在差异]` |
| V6 | 编号可溯源 | 全部原编号（F/G/H/J/DM/B/C/D/E/N 系列）在正文或附录可检索到 |
| V7 | 结构与字段齐备 | 七章 ＋ 附录 A~F 完整；A 项 7 字段、B 项 6 字段无缺 |
| V8 | 抽样反查 | 随机抽 ≥8 条（含 ≥5 个 A 项）按「代码位置」回读源码，确认「判定」与「阻断后果」与代码一致 |
| V9 | 变更面收敛 | 除 `problem.md` 与 `problem.md.bak` 外，`git --no-optional-locks status --porcelain` 无新增/修改条目 |
| V10 | 统计自洽 | 附录 B 的 A/B 计数、三档阻断等级计数、四档优先级计数与正文条目数逐一相符 |
| V11 | 自检清单逐条过 | 提示词「七、硬性约束」6 条 ✅ 全过（覆盖重写 / 编号不删 / A 项必有规则 / 不编造位置 / 不扩范围 / 不删编号） |

---

## 6. 执行顺序（批准后）

1. 备份：复制 `problem.md` → `problem.md.bak`（校验 hash 一致）。
2. Step 1 补读：`page_input_selection.py` L320-470、`app.py` L240-290、`sql_safety.py` L30-70、`step_executor.py` L280-320、`executor.py` L70-120＋L170-260、`table_lifecycle.py` L95-211、`excel_preprocessor.py`（已读）→ **解决 §2.4 三处冲突**。
3. Step 2 裁定矩阵：逐条产出 原编号 → A/B → 代码位置 → 规则／为何不归 A → 阻断后果；同时清点原问题总数。
4. Step 3 清理：标 FIXED / FIXED-PARTIAL / OBSOLETE / UNVERIFIED；按 §3.7 合并重复并保留双向引用。
5. Step 4 覆盖重写 `problem.md`（含附录 A~F）。
6. 跑 V1~V11 全部门禁；输出实测证据（行数、计数、抽样回读结果）。
7. 若过程中出现「问题条目无法对应任何代码」「原问题已在架构变更中自然消除」等情形 → 暂停并标 `[REQUIRES_HUMAN_CONFIRMATION]`（附说明与建议选项）。

---

## 7. 待人工确认项（执行中随时提出）

| # | 事项 | 触发条件 |
|---|---|---|
| Q-1 | `H-18` 是否算 A 类（或降 B/P1） | 见 §4-A10 |
| Q-2 | §2.4 三处冲突的最终定性（若实测结果与原记载相反，则 G-08/G-10/G-07 的判定与归属需人工复核） | Step 2 实测后 |
| Q-3 | 若清点出的「原问题总数」与预估 ≈99 差异较大（±10 以上），回报人工后再写映射表 | Step 2 清点后 |
| Q-4 | 任何 `[NO_CODE_MATCH]` 条目 | Step 2 |
