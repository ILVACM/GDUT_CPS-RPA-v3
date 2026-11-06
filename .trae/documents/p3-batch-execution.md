# 计划：执行 **P3 批次**（新建规范化模块，3 项）

> 计划日期：2026-10-18 ｜ 施工依据：`_temp/ImportData/plan.md` §1.1 的 P3 批 ＋ `A-05`／`REQ-R4`／`REQ-R5` 正文 ＋ **Part 4 契约**（L5768-5822）＋ 管线顺序规范（L2330）
> 前置：**P-0／P0／P1／P2 均已完成并验收**（P2：118 用例 OK／双 smoke OK／自检 6/6）
> 本批 3 项：`A-05`（R3 合并格拆分）、`REQ-R4`（公式兜底）、`REQ-R5`（超链接展开）——**同属新建文件 `ops/excel_normalizer.py`**，故串行
> 运行方式：A（单 Agent 直接执行；三项同文件，且共享一个管线入口）

---

## 1. 摘要

**新建 Layer 0 基础设施模块** `ops/excel_normalizer.py`：落地 Part 4 的对外契约（`NormalizeResult` 四字段 ＋ `normalize_sheet` 完整签名），并实现三个规则函数（R3/R4/R5）。**本批只建模块，不接线**——把 `table_importer` L76 改调 `normalize_sheet` 由 **`A-04`（P4）** 承担（plan.md §4.3 明确）。

共 **1 个新建文件**（约 300 行），**0 个既有文件改动**。

---

## 2. 现状分析（Phase 1 实测）

| 现场 | 实测 | 用途 |
|---|---|---|
| `ops/excel_normalizer.py` | **不存在**（`Glob` 确认） | 新建型 |
| plan.md L5768-5822 | Part 4 契约：`NORMALIZE_RULES_VERSION="v1"`／`MERGED_SPLIT_LIMIT=10_000`／`NormalizeResult`（`dataframe`／`meta`／`report_entries`／`warnings`）／`normalize_sheet(file_path, sheet_name, header_row, *, sheet_info=None, max_significant_digits=5, na_policy="preserve", enable_cache=True, progress=None)` | 必须逐字对齐 |
| plan.md L2330 | **强制管线顺序**：公式兜底(R4) → 错误值(H4) → 超链接(R5) → 清洗(R7) → 空值策略(A-08) → 类型推断(A-04)，"顺序即为实现规范，不得颠倒" | 管线骨架 |
| plan.md L5839 | `table_importer.py` ① L76 改调 `normalize_sheet` **归属 `A-04`**（含 `A-03`／`REQ-R2`／`REQ-H1`） | ⇒ 本批**不接线** |
| plan.md `A-05` §3 骨架 | `split_merged_cells(ws, df, header_rows) -> tuple`；① 取 `ws.merged_cells.ranges` ② 左上角值写满全区（**计入 skiprows 偏移**）③ 记 `splits` ④ **不改临时区文件** | 实现依据 |
| plan.md `REQ-R4` §3 骨架 | `resolve_formula_cells(ws_tex, ws_val, df, offset_rows, offset_cols=0) -> tuple`；**两次开簿**（`data_only=True` 取值／`False` 取公式）；只对"缓存为空"的格取公式原文；命中→写公式原文 ＋ 记 `(行,列,原文,"cached_empty")`；**绝不静默填 NULL** | 实现依据 |
| plan.md `REQ-R5` §3 骨架 | `expand_hyperlinks(ws, df, offset_rows) -> tuple`；`cell.hyperlink.target`；只记 `target`／**不展开外链**；先快速探测再全表遍历；记 `(行,列,显示文本,目标)` | 实现依据 |
| `ops/excel_preprocessor.py` | `read_excel_sheet`／`scan_sheets`／`read_header_row` 已可用（P2 新增后者） | 复用读取能力 |
| `RPA_Workflow_v3.spec` | `'ops.excel_normalizer'` **已在 P0/A-17 预登记** | 打包无遗漏 |

> **未决技术点（须执行第 0 步实测）**：`openpyxl` **read_only 模式**下 `ws.merged_cells.ranges` 是否可用。可用 → 按骨架（read_only×2）；不可用 → 采用"**先全量开簿只取合并区与超链接元数据，随即 `close()`＋`gc.collect()`，再以只读模式取值**"并回写 `[ADJUSTED]`。

---

## 3. 变更内容（decision-complete）

### 3.1 新建文件 `rpa_engine/ops/excel_normalizer.py`

> 文件头 docstring 参照 `ops/table_importer.py` 的既有风格（Layer 0 说明 ＋ 依赖库 ＋ 内存说明）。

**(a) 模块常量与契约**（逐字对齐 Part 4）
```python
NORMALIZE_RULES_VERSION = "v1"      # 规则版本；规则变更须递增（使 H10 缓存失效）
MERGED_SPLIT_LIMIT = 10_000         # 单表合并区上限（超过则只告警不拆分）

@dataclass
class NormalizeResult:
    dataframe: "Any"
    meta: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    report_entries: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
```
`meta` 的列键**逐字对齐** Part 4：`original_type`／`was_formula`／`was_hyperlink`／`was_merged`／`all_empty`／`normalized`／`cleaned`。

**(b) `normalize_sheet(...)` 签名**：逐字对齐 Part 4（含 5 个 keyword-only 参数与 docstring 的 `Raises` 三条）。**本批实现的管线（按强制顺序排位）**：
```
① read_excel_sheet(...)        # 复用既有读取（表头行物化、sheet_info 复用）
② split_merged_cells(...)      # R3 —— 表级结构修正，须在单元格级之前（见 §4-D2）
③ resolve_formula_cells(...)   # R4 —— 「公式兜底」＝强制管线第 1 段，位置不变
④ expand_hyperlinks(...)       # R5 —— 强制管线第 3 段（H4 在其前，本批未实现）
⑤ （H4 错误值／R7 清洗／A-08 空值／A-04 类型推断：本批**不实现**，仅为后续批次保留顺序位置与 `# TODO(批次)` 注记，不写占位代码）
⑥ 汇总 meta／report_entries／warnings → 返回 NormalizeResult
```
- **不实现**未在本批的规则：不得写"空实现占位函数"（避免后续批次误认为已实现）。

**(c) `split_merged_cells(ws, df, header_rows) -> tuple[pd.DataFrame, List[Dict]]`**（R3）
- 逐条落地 `A-05` §3 的①②③④：`ws.merged_cells.ranges` → 左上角值 → 写入该区**所有**单元格（列坐标＋`header_rows` 行偏移对齐 df）→ 记 `splits` → **不写回文件**。
- 超 `MERGED_SPLIT_LIMIT` → **不拆分**，`warnings` 追加人话告警 ＋ 记 `report_entries`（如实标注"未拆分"）。
- 单区异常（越界/写入失败）→ 记 warning **continue**（单元格级容错）。

**(d) `resolve_formula_cells(ws_tex, ws_val, df, offset_rows, offset_cols=0) -> tuple`**（R4，**兜底路径＝不引入 win32com**）
- 逐条落地 `REQ-R4` §3 的①②③④：只对"`ws_val` 缓存为空"的格去 `ws_tex` 取公式文本；命中 → 该格写公式原文 ＋ 记 `(行, 列, 公式原文, "cached_empty")` ＋ `warnings` 追加"该表含未计算公式，已保留公式文本"；**绝不**静默填 NULL。
- `formula_cells` 为空时**零开销**返回原 df（不复制第二份全量 DataFrame）。

**(e) `expand_hyperlinks(ws, df, offset_rows) -> tuple`**（R5）
- 逐条落地 `REQ-R5` §3 的①②③④：**先快速探测**（任一 `cell.hyperlink` 才继续遍历）；命中 → 值替换为 `cell.hyperlink.target`；记 `(行, 列, 显示文本, 目标地址)`；**不展开** `location` 形式外链（仅记 `target`）。

**(f) 职责边界**（逐字对齐 Part 4）：**不负责** Excel 读取（复用 `read_excel_sheet`）、SQLite 写入、话术翻译、重试与取消；**不登记** `BUILTIN_OPS`（Layer 0 基础设施，不属功能函数三形态，见 plan.md §4.1 职责边界）。

---

## 4. 假设与决策

| # | 决策 | 依据 |
|---|---|---|
| **D1** | **本批不接线**：`table_importer` L76 改调 `normalize_sheet` 归 **`A-04`（P4）** | plan.md §4.3（该行明确归属 `A-04`／`A-03`／`REQ-R2`／`REQ-H1`） |
| **D2** | 本批管线次序＝ **read → R3 → R4 → R5**：`R3` 置于单元格级之前（表级结构先修正，后续单元格级处理才有完整对象）；`R4`／`R5` 严格保持强制管线中的相对位次 | 工程判断 ＋ plan.md L2330（强制顺序对 R4/R5 的相对位次有约束） |
| **D3** | 本批**为后续批次的管线阶段留位但不写空实现** | 避免后续误判"已实现"（"不要添加不会被使用的占位代码"） |
| **D4** | **不引入 `pywin32`／`win32com`**；R4 只做兜底路径 | plan.md `REQ-R4` 明确"本轮不引入 win32com"＋ §0.2 条 1 |
| **D5** | read_only 下 `merged_cells` 的可用性由**执行第 0 步实测**决定，含既定降级方案（见 §2 注） | 技术未知点，不得凭猜测实现 |
| **D6** | 新函数**均接受调用方传入的 `ws`**（不自建连接／不自开簿；开簿由 `normalize_sheet` 统一管理并 `close()`） | plan.md 各条 §4 ＋ `AGENTS.md` §2.2 条 4 |
| **D7** | 内存：全程**不得同时持有两份全量 DataFrame**；`resolve_formula_cells` 仅在命中时才就地写回 | plan.md `A-05` §4 ＋ §0.2 条 6 |
| **D8** | 不执行 git；完成后输出「待人工提交清单」 | `AGENTS.md` §1 |
| **D9** | 门禁按 plan.md §1.4 用 conda ＋ `QT_QPA_PLATFORM=offscreen` | 人工裁定（2026-10-18） |
| **D10** | 本批交付物**不含**测试文件（`tests/test_ops_contracts.py` 归 `B-42`）；验收走脚本 | plan.md §4.1b |

---

## 5. 验证步骤（全部脚本化，`openpyxl` 造样本）

| # | 验收项 | 判据 |
|---|---|---|
| **V0** | **技术前置实测** | 合并格样本以 `read_only=True` 打开后 `ws.merged_cells.ranges` 可读 → 记结论；不可读则按 §2 降级并回写 `[ADJUSTED]` |
| V1 | **`A-05`** 合并格拆分 | `A2:A4` 合并为 `华东`、B 列 100/200/300 → df 三行均为 `华东`；`splits` 含 1 条记录；**回读原文件仍为合并状态**（未改本体） |
| V2 | **`A-05`** 降级 | patch `MERGED_SPLIT_LIMIT=0` → **不拆分** ＋ `warnings` 出现"未拆分"人话告警 |
| V3 | **`REQ-R4`** 无缓存 | 脚本写入 `=1+2` 且**不**用 Excel 打开 → 该格**非 NULL**、值为公式原文；`formula_cells` 含 `"cached_empty"`；`warnings` 非空 |
| V4 | **`REQ-R4`** 有缓存 | 以 XML 注入 `<v>3</v>` 造出带缓存的公式格 → 该格为 `3`（缓存值），**不被公式原文覆盖** |
| V5 | **`REQ-R5`** 超链接 | A2 显示 `查看明细`、target `https://example.invalid/abc` → 该格值为 **URL**；`link_cells` 含 `(行,列,"查看明细",URL)` |
| V6 | 契约与素性 | `NormalizeResult` 四字段齐备；`normalize_sheet` 的 **keyword-only** 参数可省略调用；无公式无合并无链接的普通表 → 行为与 `read_excel_sheet` 一致（值不变） |
| V7 | 回归 | `py_compile` **0**；`unittest discover` ≥118 用例 `OK`；双 smoke `SMOKE_ALL_OK` 0/0；自检 6/6；`import ops.excel_normalizer` 成功 |
| V8 | 未越界 | **未改动任何既有文件**；未接线到 `table_importer`；未引入新依赖（`openpyxl`／`pandas`／`dataclasses`／`typing`）；无绝对路径；`requirements.txt` 无 `pywin32` |

---

## 6. 执行顺序（批准后）

1. 备份：本批**无既有文件改动** → 仅记录 `ops/excel_normalizer.py` 为本批新建产物（无需 backup 目录）。
2. **V0 技术前置实测**（read_only 下 `merged_cells` 可用性）→ 据结果定实现路径；必要时回写 `[ADJUSTED]`。
3. 新建 `ops/excel_normalizer.py`：常量与契约（a）→ `normalize_sheet`（b）→ `split_merged_cells`（c）→ `resolve_formula_cells`（d）→ `expand_hyperlinks`（e）。
4. `py_compile` ＋ `import` 自检 → 写 `_temp/ImportData/verify_p3_scenarios.py` 跑 V1~V6。
5. 跑 V7 统一门禁（118 用例／双 smoke／自检）。
6. 追加任务记录 Step 7；plan.md 新增「§0.7.5 P3 批次施工记录」。
7. 输出批次简报 ＋「待人工提交清单」。

---

## 7. 待人工确认项

| # | 事项 | 触发条件 |
|---|---|---|
| Q-1 | 「有缓存的公式」用例（V4）如 XML 注入不可行，则改为真机验证并归入 `P-2`（我会如实标注未覆盖部分） | V4 执行时 |
| Q-2 | 若你希望本批**顺带接线**（提前让 `table_importer` 调 `normalize_sheet`）→ 与 plan.md §4.3 归属 `A-04` 冲突，需你裁定 | 你显式要求时 |
