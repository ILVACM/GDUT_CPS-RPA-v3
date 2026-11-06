# 计划：落地 P6 三项遗留决策（①A-09① 降级 ②[P4-7] 维持默认 ③[P4-4] 二者并存）

> 计划日期：2026-10-18 ｜ 依据：人工对本轮三项遗留项的**决策指令** ＋ `_temp/ImportData/plan.md` 正文
> 前置：A 链 19 项已闭环（P-0~P6 全部验收）；当前基线 **Ran 118 tests — OK**／双 smoke `SMOKE_ALL_OK`／自检 6/6
> 范围：**仅此三项**；**不动 B 类（B-01~B-79）任何内容**

---

## 1. 摘要

| 决策 | 性质 | 落点 |
|---|---|---|
| **① `A-09`① 分块读取 → 走 §6 降级（维持现状）** | **纯文档** | `plan.md` 的 `A-09` 条目内新增 `[ADJUSTED]` 标注（现只记在 §0.7.8，需在**条目本体**可查） |
| **② `[P4-7]` JSON 全局配置 → 维持默认（留待后续专项）** | **纯文档** | `plan.md` §0.7.6 的 `[P4-7]` 状态改为"**已裁定：维持默认，留待后续专项**" |
| **③ `[P4-4]` 导出侧日期列判定 → 二者并存（元数据优先 ＋ 值形态兜底）** | **代码 ＋ 文档** | `ops/exporter.py` 的日期判定段；`plan.md` 的 `[P4-4]` 状态改为"**已落地：二者并存**"＋落点 |

**不动**：`excel_preprocessor.py`（决策①明示不需改）、`import_excel_table`／`normalize_sheet` 签名、引擎调度／GUI 布局／步骤函数、B 类。

---

## 2. 现状分析（Phase 1 实测）

| 现场 | 实测 | 用途 |
|---|---|---|
| `ops/exporter.py` L61-67 | `export_table(conn, table_name, output_path, sheet_name="数据", cancel_check=None)` —— **已持有 `conn`** | ⇒ 决策③**可直接查元数据表**，无需改签名 |
| 同文件 L36-58 | 值形态判定：`_DATE_OUT_RE`／`_DATETIME_OUT_RE` 严格匹配 ＋ `_iso_to_datetime(value)`（仅接受 `YYYY-MM-DD`／`YYYY-MM-DD HH:MM:SS`） | 现行口径（**须保留为兜底**） |
| 同文件 L127-135 | 写入循环：`dt, fmt = _iso_to_datetime(v)`；`dt is not None` → 写 `datetime` ＋ `number_format`；否则 `cell.value = v`（原样） | 决策③的**改动点** |
| 同文件 L101 | `columns = get_table_columns(conn, table_name)` → 列名**按序**可得（`columns[c_i-1]` 可判列） | 元数据按列名对齐 |
| `ops/excel_normalizer.py` L916-937 | `write_meta_table(conn, result, sqlite_table, table_id)`：建**统一表 `__normalize_meta`**，DDL＝`(table_id TEXT, sqlite_table TEXT, column TEXT, original_type TEXT, was_formula INTEGER, was_hyperlink INTEGER, was_merged INTEGER, all_empty INTEGER, was_error INTEGER, normalized TEXT, cleaned INTEGER)` | 决策③的**查询键＝`sqlite_table`**；标记列＝`original_type='datetime'` |
| P4 已落地 | `normalize_datetime_column`（H2）写入 `original_type='datetime'`；`__normalize_meta` 由 P6 接线落盘 | 元数据来源确实存在 |

> **关键**：`export_table` 的 `table_name` 与 `__normalize_meta.sqlite_table` **同源**（都是物理表名）✓ 可直接等值查询。

---

## 3. 变更内容（decision-complete）

### 3.1 决策① 文档更新（`plan.md` 的 `A-09` 条目）

在 `A-09` 条目的 **§6（风险与回滚）之后、§7（验收标准）之前**（或 §6 内末尾）**新增**：

```
> **[ADJUSTED] A-09 ①（分块读取）已裁定走 §6 降级（2026-10-18）**
> - **原因**：pandas 3.0.5 的 `pd.read_excel` **无 `chunksize` 形参、也无 `**kwds`**（传 `chunksize=` 直接 `TypeError`；`engine_kwargs={'chunksize':…}` 透传给 `openpyxl.load_workbook` 亦 `TypeError`）——计划指定机制在当前依赖下**架构上不可实现**。
> - **走法**：依 §6 降级，只做 ②③（**大表文案预告 ＋ `psutil` 内存阈值监控**），**不做分块**。
> - **影响**：`ops/excel_preprocessor.py` **无需修改**；`CHUNK_ROW_THRESHOLD` 常量**保留**，当前降级路径下**无消费方**（不为它造消费点）；A-04 的 `dtype=object`／`keep_default_na=False` 约束**原样保留**。
> - **验收口径**：§7 的三条判据在降级路径下**同样成立**（大表有提示且能完成／峰值不升／常规表不变），**不要求分块必须实现**。
```

### 3.2 决策② 文档更新（`plan.md` §0.7.6 的 `[P4-7]`）

把 §0.7.6 遗留段中 `[P4-7]` 的表述改为：

```
- **[P4-7] 已裁定：维持当前默认（2026-10-18）** —— `max_significant_digits=5`／`na_policy="preserve"`。
  原因：真正接线需**改 `import_excel_table` 签名**以透传 `global_config`，而签名字与返回值**受 §0.2 条 2 硬约束保护**（不改既有签名）→ 属**架构死锁**，仓促处理会横跨多个模块；且当前默认值**不导致数据错误**。
  **留待后续专项**：先设计完整的 `global_config` 透传链路（含 JSON 参数 Schema 与引擎注入点）再实施。
```

### 3.3 决策③ 代码更新（`ops/exporter.py`）

| # | 位置 | 改后（语义示意） |
|---|---|---|
| F1 | `ops/exporter.py` 常量区（L36-41 附近） | 新增**宽松形态**正则（**无歧义**限定）：`_LOOSE_DATE_RE`＝`^\d{4}[/.]\d{1,2}[/.]\d{1,2}$`；`_LOOSE_DATETIME_RE`＝`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$`（含 `T` 分隔） |
| F2 | 同文件 `_iso_to_datetime` **之后** | 新增 `_parse_datetime_loose(value)` → `(datetime, fmt)`：先走**严格** `_iso_to_datetime`；未命中再试宽松形态（`/`、`.` 分隔 → 解析为日期；`T` 分隔 → 解析为 datetime）；**任何解析失败返回 `(None, None)`**（**不得引入新失败**，遵裁定 G10 精神） |
| F3 | 同文件新增助手 | `_datetime_columns(conn, table_name) -> set`：`try: SELECT column FROM __normalize_meta WHERE sqlite_table=? AND original_type='datetime'`；**表不存在／任何 sqlite3.Error → 返回空集**（⇒ 无元数据时行为与今日**完全一致**） |
| F4 | `export_table` 内（`columns` 取得之后） | `dt_cols = _datetime_columns(conn, table_name)`（**不改签名**） |
| F5 | 写入循环 L127-135 | **元数据优先、值形态兜底**：<br>① 列名 `columns[c_i-1]` **在 `dt_cols` 内** → 用 `_parse_datetime_loose(v)`（可吃 `YYYY/M/D` 等宽松形态）；命中 → 写 `datetime` ＋ `number_format`；未命中 → **原样写**；<br>② 列名**不在 `dt_cols` 内** → 仍用**严格** `_iso_to_datetime(v)`（**完全保留现状**，向后兼容）；<br>③ 二者皆未命中 → `cell.value = v`（原样） |

- **不变量**：`export_table` 的**签名与返回值不变**；**不引入新依赖**（仅 `re`／`sqlite3`／`datetime`，均已在用）；回落路径**必须存在**；`SELECT` 仍走 `quote_ident`／显式列名（沿用既有安全约定）。
- **内存**：`_datetime_columns` 只取一个列名集合（≤列数），**不加载行数据**。

### 3.4 决策③ 文档更新

`plan.md` §0.7.6 遗留段中 `[P4-4]` 改为：

```
- **[P4-4] 已落地：二者并存（2026-10-18）** —— **元数据优先（`__normalize_meta.original_type='datetime'`）＋ 值形态兜底（严格 ISO 严格匹配）**。
  落点：`ops/exporter.py` —— 新增 `_datetime_columns()`／`_parse_datetime_loose()`；`export_table` 写入循环按"列在元数据标记集内→宽松解析／否则→严格解析"分支。
  兼容性：**无 `__normalize_meta`（旧库/旧会话）时 `dt_cols` 为空集 → 行为与改动前逐格等价**。
```

### 3.5 无残留标记（Step 5）

全文 Grep `[TODO]`／`[FIXME]`／`[XXX]` → 若有真实残留则处理；若仅出现在"禁止性表述/本报告描述"内则**标注说明**（沿用既往口径）。

---

## 4. 假设与决策

| # | 决策 | 依据 |
|---|---|---|
| **D1** | **①②为纯文档更新**；**③为代码＋文档** —— 与人工指令一致 | 本提示词"决策 1/2 为纯文档""决策 3 需要改代码" |
| **D2** | **不改任何函数签名**（`export_table`／`import_excel_table`／`normalize_sheet`） | 人工决策②的裁定理由 ＋ §0.2 条 2 |
| **D3** | 决策③的"元数据判定"落地为**宽松形态解析**（无歧义限定：`/`／`.` 分隔日期、`T` 分隔 datetime），**不是**无限放宽；解析失败一律原样写 | "元数据优先"须比值形态更准，且不得引入新失败 |
| **D4** | **回落路径必须存在**且**无元数据时行为逐格等价**（`dt_cols` 空集 ⇒ 与改动前一致） | 人工指令"回落路径必须保留，防止旧数据崩溃" |
| **D5** | **`plan.md` 为单一写者（我）**：子 Agent **不得**改 `plan.md`／`docs/**`／`AGENTS.md`／`build/**`；其落点在报告中回报，由我写入 | 避免并发写同一文件 |
| **D6** | **`git commit` 建议由人工执行** —— 人工指令 Step 5 后附"建议版本控制"，与 `AGENTS.md` §1「Git 操作由人工接管，Agent 不执行」**冲突**；按规约层优先：Agent **不执行 git**，只在报告中给「待人工提交清单」 | `AGENTS.md` §1（约束层最高权威） |
| **D7** | 改动前备份 `ops/exporter.py` → `_temp/ImportData/backup/D3/` | 回滚点 |
| **D8** | 若子 Agent 遇阻（如 `__normalize_meta` 在实际导出链路上不可达）→ `[SUB_AGENT_BLOCKED]`（附选项），**不得猜测** | 该指令"遇不确定输出 BLOCKED" |
| **D9** | **不动 B 类**任何内容 | 范围约束 |

---

## 5. 验证步骤

| # | 项 | 判据 |
|---|---|---|
| V1 | 三项状态更新 | plan.md 内 `A-09` 条目含 `[ADJUSTED]` 降级标注；`[P4-7]` 为"已裁定：维持默认"；`[P4-4]` 为"已落地：二者并存"＋落点 |
| V2 | 代码锚点存在 | `exporter.py` 含 `_datetime_columns`／`_parse_datetime_loose`／`__normalize_meta` 查询；`export_table` **签名未变**（`conn, table_name, output_path, sheet_name, cancel_check`） |
| V3 | **回归** | `py_compile` 0；`unittest discover` ≥118 `OK`；双 smoke `SMOKE_ALL_OK`；自检 6/6 |
| V4 | 决策③功能 | ① 建 `__normalize_meta` 标记某列为 datetime ＋ 该列值用**宽松形态**（如 `2026/1/5`）→ 导出写出**真日期**（`number_format` 生效）；② **不建元数据表**时同一数据 → 行为与改动前**逐格一致**（宽松形态值**不被**转成日期）；③ 严格 ISO 值在两种情况下**都被正确转换**（不回归） |
| V5 | 越界与备份 | `AGENTS.md`／`docs/**`／`build/**`／B 类未动；`requirements.txt` 无新增；**无新依赖**；`backup/D3/` 有 `exporter.py` 改前快照 |
| V6 | 无残留标记 | `[TODO]`／`[FIXME]`／`[XXX]` 无真实残留（或已标注原因） |

---

## 6. 执行顺序（批准后）

1. 建 `_temp/ImportData/backup/D3/` 并备份 `ops/exporter.py`。
2. 派 **`Agent-D3`** 子 Agent（仅决策③的代码改动 ＋ 自验 ＋ 报告；**禁止改 plan.md/docs/AGENTS/build/git**）。
3. 收报告 → 复核（V2 锚点、V3 门禁重跑、V4 功能、V5 越界）。
4. **我**写文档：plan.md 的 `A-09` `[ADJUSTED]`（①）、§0.7.6 的 `[P4-7]`（②）与 `[P4-4]`（③）状态；`docs/task-records/2026-10-18-importdata-repair.md` 追加 **Step 11** 并同步汇总/关闭标识。
5. 跑 Step 5（残留标记扫描）。
6. 输出完成报告（按人工给定格式）＋「待人工提交清单」。

---

## 7. 待人工确认项

| # | 事项 | 触发条件 |
|---|---|---|
| Q-1 | **`git commit`** —— 人工指令"建议版本控制"，但 `AGENTS.md` §1 规定 **Agent 不执行 git** → 我按规约**不执行**，仅输出待提交清单（**如需我提交，请明示覆盖该规约**） | 始终 |
| Q-2 | 决策③的**宽松形态范围**（`/`／`.`／`T`）——若你认为应仅限严格 ISO（即不引入宽松解析）→ 请明示，我改为"仅元数据标记列强制走严格解析＋其余不变" | 复核时 |
| Q-3 | 若子 Agent 报 `[SUB_AGENT_BLOCKED]`（元数据表在导出链路不可达）→ 我升级 `[REQUIRES_HUMAN_CONFIRMATION]` ＋ 2~3 选项 | 子 Agent 报告时 |
