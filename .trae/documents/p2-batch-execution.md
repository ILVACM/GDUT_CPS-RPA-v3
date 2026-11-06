# 计划：执行 **P2 批次**（表头规范化，2 项）

> 计划日期：2026-10-18 ｜ 施工依据：`_temp/ImportData/plan.md` §1.1 的 P2 批 ＋ 各条目 Part 2／Part 2′ 正文 ＋ §0.7.1／§0.7.2／§0.7.3
> 前置：**P-0 / P0 / P1 均已完成并验收**（P1：118 用例 OK／双 smoke OK／自检 6/6）
> 本批 2 项：`A-03`（表头禁字符预检）、`REQ-R2`（指定表头行全空则拒绝）
> 运行方式：A（单 Agent 直接执行；两项同属导入入口，串行）

---

## 1. 摘要

把两类"表头问题"的失败**前移到导入入口并给人话定位**：① 表头含**换行/制表符等 5 个禁字符**（原失败发生在 `to_sql` 建表期，用户只见技术原文）；② 用户选中的**表头行整行皆空**（原防护只覆盖"整表无内容"）。

共 **3 处改动**，落在 **2 个文件**（`gui/error_messages.py` **不改**——所需规则已在 P0 落地）。

---

## 2. 现状分析（Phase 1 实测）

| 现场 | 实测 | 用途 |
|---|---|---|
| `ops/table_importer.py` L29-101 | 导入链路：L61-62 `scan_sheets` → L72-73 `cancel_check` → L76-77 `read_excel_sheet` → L79-82 `df.empty` 检查 → L84-89 重复列名告警 → L91 `import_dataframe` | 两处预检的插入点 |
| `ops/sql_safety.py` L36 | `_FORBIDDEN_IDENT_CHARS = ('"', "\x00", "\n", "\r", "\t")`（**同源常量**，禁止在本批另写字面量表） | `A-03` 复用 |
| `ops/excel_preprocessor.py` L171-220 | `read_excel_sheet` 已实现（含 `sheet_info` 复用）；**无** `read_header_row` | `REQ-R2` 新建函数 |
| `ops/excel_preprocessor.py` L152-168 | `scan_sheets`：`load_workbook(read_only=True, data_only=True)` 的既有用法（可照抄该模式） | `REQ-R2` 实现参考 |
| `gui/error_messages.py` L20-31 | **已含** `("标识符包含禁止字符", …)` 规则（P0/A-13 落地） | ⇒ `A-03` 的"加规则"**无需重做** |

> 行号取自当前磁盘（P1 后）；执行时以**实际文本**定位（plan.md §0.2.1）。

### 2.1 两处 `[ADJUSTED]`（本批施工前先确认口径）

- **`[ADJUSTED-10]` `A-03` 的"空列名归一／重复列名去重"不在本批做**：plan.md `A-03` §3 改动点 1 的 ②③ 与 **`REQ-H1`（P5）** 是同一逻辑 → 本批只实现 ①（禁字符预检），并在预检中**跳过空列名**（不拒绝），把空列名交给 P5 的 `REQ-H1` 归一。理由：避免两批实现同一逻辑，且防止"空列名的表在 P2 就被拒、永远到不了 P5 的归一"。
- **`[ADJUSTED-11]` `A-03` 的 error_messages 新规则已在 P0 落地**：`("标识符包含禁止字符", "该数据表的表头里有不可用的字符（常见为换行或制表符）。", "请在 Excel 中清理该表头后重新导入。")` 已存在于 `_RULES`。⇒ 本批**不重复添加**，`gui/error_messages.py` **不改**。

---

## 3. 变更内容（decision-complete）

> 改前/改后为**语义示意**；执行时以实际文本等价替换（§0.2.1）。

### 3.1 `A-03` 表头含换行/制表符 → 整表操作失败

| # | 文件 · 位置 | 改后（语义） |
|---|---|---|
| F1 | `ops/table_importer.py`：在 **`df.empty` 检查（L79-82）之后、重复列名告警（L84）之前**插入 | 复用**同源常量**做逐列预检：<br>`from ops.sql_safety import _FORBIDDEN_IDENT_CHARS`；对 `df.columns` 逐列——**空列名跳过**（`[ADJUSTED-10]`）；命中任一禁字符则 `raise ValueError(f"数据表 [{sheet_name}] 的第 {i+1} 列表头包含不可用字符 {repr(ch)}（常见于表头里的换行或制表符），请先在 Excel 中清理该表头后重试")` |
| F2 | `gui/error_messages.py` | **不改**（规则已在 P0 落地，`[ADJUSTED-11]`） |

- **不变量**：`import_excel_table` 的**签名与返回值不变**；抛出的异常仍是 **`ValueError`**（上层 `main_window` 的逐表 `try/except` 已覆盖 → 表级失败、不影响其他表）。

### 3.2 `REQ-R2` 指定表头行全空则拒绝并提示

| # | 文件 · 位置 | 改后（语义） |
|---|---|---|
| F1 | `ops/excel_preprocessor.py`：**新增 `read_header_row(file_path, sheet_name, header_row) -> Optional[List[Any]]`**（放在 `scan_sheets` 之后、`read_excel_sheet` 之前） | 用 `load_workbook(read_only=True, data_only=True)` **只读该一行**（不加载整表，遵 §2.1 条 5）；`finally: wb.close()`；文件不存在 → `FileNotFoundError`；非 `.xlsx` → `ValueError`；sheet 不存在 → `ValueError`；行号越界 → 返回 `None` |
| F2 | `ops/table_importer.py`：在 **`cancel_check`（L72-73）之后、`read_excel_sheet`（L76）之前**插入预检 | `header_vals = read_header_row(xlsx_path, sheet_name, int(header_row))`；若 `header_vals is not None` 且**全部** `str(v or "").strip() == ""` → `raise ValueError(f"数据表 [{sheet_name}] 的第 {header_row} 行为空，不能作为表头。请在界面中重新选择表头行后重试")` |
| F3 | `ops/table_importer.py` L22 imports | 追加 `read_header_row` 到既有的 `from ops.excel_preprocessor import read_excel_sheet, scan_sheets` |

- **不变量**：`read_excel_sheet` 的签名／返回值不变；`scan_sheets` 不变；`read_header_row` 为**新增公开函数**（不改既有 API）。
- **粒度**：`read_header_row` 越界返回 `None` → **不拒绝**（越界情形由 `read_excel_sheet` 的既有校验报错，不重复拦截）。

---

## 4. 假设与决策

| # | 决策 | 来源 |
|---|---|---|
| **D1** | 本批**串行由 Coordinator 直接执行**（两项同属导入入口；且与 P0 已落地的规则耦合） | plan.md §1.1 P2 备注 |
| **D2** | `A-03` **只做禁字符预检**；空列名归一／重复列名去重**留给 P5 的 `REQ-H1`** | `[ADJUSTED-10]`（避免重复实现） |
| **D3** | `A-03` 的 error_messages 规则**已在 P0 落地**，本批不重复添加 | `[ADJUSTED-11]` |
| **D4** | 禁字符集合**必须复用 `sql_safety._FORBIDDEN_IDENT_CHARS`**，不得另写字面量表 | plan.md `A-03` §3 明确要求 |
| **D5** | `read_header_row` **只读目标行**（read_only 模式），不加载整表 | plan.md `REQ-R2` §3 ＋ §0.2 条 6（内存） |
| **D6** | 预检失败抛 **`ValueError`**（非自定义异常），使 GUI 逐表 `try/except` 自动获得"表级隔离" | plan.md `A-03` §5 ＋ P0 已验证的隔离机制 |
| **D7** | 不执行 git；完成后输出「待人工提交清单」 | `AGENTS.md` §1 |
| **D8** | 改动前备份 2 个目标文件 → `_temp/ImportData/backup/P2/` | plan.md 各条目 §6 |
| **D9** | 门禁按 plan.md §1.4 用 conda ＋ `QT_QPA_PLATFORM=offscreen` | 人工裁定（2026-10-18） |

---

## 5. 验证步骤（全部可脚本化，用 `openpyxl` 造样本）

| # | 验收项 | 判据 |
|---|---|---|
| V1 | `A-03` 换行表头 | 构造表头 `金额\n（元）` → `import_excel_table` 抛 `ValueError`，消息含**列号**与"不可用字符" |
| V2 | `A-03` 制表符表头 | 构造表头 `数量\t` → 同上（表级失败） |
| V3 | `A-03` **不误伤** | 中文／空格／括号表头（`金额（元）`、`数量 个`）→ **正常导入** |
| V4 | `A-03` 空列名不拒（`[ADJUSTED-10]`） | 表头含空列名 → 预检**跳过**（不抛预检 ValueError），留给 P5 归一 |
| V5 | `REQ-R2` 全空表头行 | 第 1 行全空、第 2 行真表头 → 指定第 1 行 → 抛 `ValueError`（"该行为空，不能作为表头"）；改为第 2 行 → **正常导入** |
| V6 | 回归 | `py_compile` **0**；`unittest discover` ≥118 用例 `OK`；双 smoke `SMOKE_ALL_OK` 0/0；自检 6/6 |
| V7 | 未越界 | `import_excel_table`／`read_excel_sheet`／`scan_sheets` 的**签名与返回值不变**；`read_header_row` 为新增函数；未新增依赖；无绝对路径 |

---

## 6. 执行顺序（批准后）

1. 备份 `ops/table_importer.py`、`ops/excel_preprocessor.py` → `_temp/ImportData/backup/P2/`。
2. 改 `excel_preprocessor.py`：新增 `read_header_row`（`REQ-R2` F1）。
3. 改 `table_importer.py`：imports 补 `read_header_row`（F3）→ 表头行全空预检（`REQ-R2` F2）→ 列名禁字符预检（`A-03` F1）。
4. `py_compile` 两文件 → 写 `_temp/ImportData/verify_p2_scenarios.py` 跑 V1~V5。
5. 跑 V6 统一门禁（118 用例／双 smoke／自检）。
6. 追加任务记录 Step 6；plan.md 新增「§0.7.4 P2 批次施工记录」并回写 `[ADJUSTED-10/-11]`。
7. 输出批次简报 ＋「待人工提交清单」。

---

## 7. 待人工确认项

| # | 事项 | 触发条件 |
|---|---|---|
| Q-1 | 若你希望 `A-03` 的**空列名也在 P2 拒绝**（而非留给 P5 归一）→ 我改为不跳过空列名并回报 | 你显式要求时 |
| Q-2 | 若既有单测断言"表头含禁字符的表能导入"→ 属契约变更（该行为本就是缺陷），我会**回报**并同步调整 | 门禁失败时 |
