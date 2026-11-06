# 计划：执行 **P0 批次**（解锁导入链路 ＋ 异常隔离，7 项）

> 计划日期：2026-10-18 ｜ 施工依据：`_temp/ImportData/plan.md` §1.1 的 P0 批 ＋ 各条目 Part 2 正文 ＋ **§0.7.1 实测核实结果**
> 前置：**P-0 已完成并验收**（容量 7,622／余量 378；`doc_verify` PASS；8 项 P0 级 `[UNVERIFIED]` 已清零；4 条 `[ADJUSTED]` 已回写）
> 本批 7 项：`A-10` → `A-19` → `A-01` → `A-02` → `A-13` → `A-14` → `A-17`
> 运行方式：**A→C 混合**——本批由 Coordinator **直接执行**（见 §4-D1），后续 P1~P6 按 §0.8 分发 Sub-Agent

---

## 1. 摘要

把"导入数据"这条路打通——这是整条链的**解锁批**：不修它，后面 18 项在真机上根本复现不了。7 项改动落在 **7 个文件**，其中 `A-01`／`A-10`／`A-13`／`A-14` 同属"源文件身份 ＋ 异常可见性"一条线，**必须同批**。

**本批不含**：任何引擎调度改动、GUI 布局改动、步骤功能函数语义改动。

---

## 2. 现状分析（Phase 1 实测锚点）

| 现场 | 实测 | 用途 |
|---|---|---|
| `gui/page_input_selection.py::get_entries` L323-334 | 只导出 4 键（`file_path/sheet_name/alias/header_row`），**无 `source_path`** | `A-10` F1 |
| `gui/page_input_selection.py::set_entries` L336-350 | **L348 已传 `source_path=e.get("source_path","")`** | 恢复侧**无需改** |
| `gui/models.py::TableEntry` L293-303 | 7 字段，**无 `source_path`** | `A-10` F2 |
| `gui/models.py::set_tables` L341-360 | L348-358 由 entries 构造 `TableEntry`，**未传 `source_path`** | `A-10` F3 |
| `gui/models.py::to_dict` L756-757 | `"source": {"file": t.file_path, ...}` | `A-10` F4 |
| `gui/main_window.py` L313-321（registry 构造）／L335-341（身份比对）／L328（失败清单）／L302-306（导入调用）／L257（`_close_session()`）／L459-476（`_close_session` 定义）／L787-791（保存 last_config）／L800（关窗调 `_close_session`） | 均**已逐处核实行号**（见 plan.md §0.7.1） | `A-10/A-19/A-01/A-13` |
| `gui/error_messages.py::_RULES` L20-41／`translate_error` L44-52 | 键＝类名小写、对输入 `.lower()`；**无**「模块缺件／禁字符／非 Excel」3 条规则 | `A-13` F2 |
| `gui/app.py::_excepthook` L259-266 | L264 `QMessageBox.critical(None, "程序异常", str(exc_value))` | `A-14` |
| `gui/app.py` L10-21 import 区 | 标准库＋`loguru`＋`engine.registry`＋`paths`；`error_messages` 仅依赖 `paths` | `A-14` 无循环风险 |
| `RPA_Workflow_v3.spec` `hiddenimports` L27-53 | **17 项**（13 个 `ops` 模块 ＋ `openpyxl` 等），**无 `'xlrd'`** | `A-17` F1 |
| `requirements.txt` L12 | 裸 `xlrd`（无版本约束、无注释） | `A-17` F2 |
| `engine/executor.py` L42-44／L47-51／L54-68 | `_IMPORT_ROOTS` 仅含 `temp/input_selection`；`register_import_root()` 现成钩子（内部查重） | `A-01` F2 的**必需附加步** |

---

## 3. 变更内容（逐项 · decision-complete）

> **改前/改后为语义示意**（plan.md §0.2.1）——执行时以本地源码真实文本为准做**等价替换**；行号已核实，但缩进/注释以实际为准。

### 3.1 `A-10` 步骤配置永久丢失（源文件身份贯通）

| # | 文件 · 位置 | 改前（语义） | 改后（语义） |
|---|---|---|---|
| F1 | `gui/page_input_selection.py::get_entries` L328-333 | 字典 4 键 | 追加 `"source_path": str(entry.source_path or entry.file_path),` |
| F2 | `gui/models.py::TableEntry` L293-303 | 字段止于 `uid` | 追加 `source_path: str = ""   # 原始文件路径（复现信息；R11/A-10）` |
| F3 | `gui/models.py::set_tables` L348-358 | `TableEntry(...)` 未传该字段 | 追加 `source_path=str(e.get("source_path", "") or ""),` |
| F4 | `gui/models.py::to_dict` L756-757 | `"file": t.file_path,` | `"file": (t.source_path or t.file_path),` |
| F5 | `gui/main_window.py::_on_confirm_import` registry 构造 L313-321 | 注册表项无 `source_path` | 追加 `"source_path": e.get("source_path", e["file_path"]),` |

- 改动点 4（`A-10` §3）的**备选路径不再需要**（模型层已接收该字段）→ 在 plan.md 该条目旁补 `[ADJUSTED: 采用新增字段路径，未采用 main_window 侧替换法]`。

### 3.2 `A-19` 换表身份只比 `sheet_name`（身份三元组）

| # | 文件 · 位置 | 改后（语义） |
|---|---|---|
| F1 | `gui/main_window.py` L335-341 | 用局部函数 `_ident(e)` 生成 **（文件名, 源路径, sheet 名）三元组**；`old_map`／`new_map` 均改为存三元组；`disturbed` 判据改为三元组不等 |
| F2 | 同段弹窗文案 L349-352 | 追加一句"（本次所选文件的来源路径或工作表与上次不同）"，使用户理解触发原因 |

- 实现（示意）：`def _ident(e): src = str(e.get("source_path") or e.get("file_path") or ""); return (Path(src).name, src, e.get("sheet_name", ""))`；`pathlib.Path` **已在该文件导入**，不新增依赖。

### 3.3 `A-01` 经 [add] 选入的文件导入 100% 失败（**含 `[ADJUSTED-1]` 强制附加步**）

| # | 文件 · 位置 | 改后（语义） |
|---|---|---|
| F1 | `gui/page_input_selection.py::get_entries` L328-333 | **与 `A-10` F1 同一次改动**（不重复改） |
| F2 | `gui/main_window.py::_on_confirm_import` 导入调用 L302-306 | ① `src = e.get("source_path") or e["file_path"]`；② **附加步（`[ADJUSTED-1]`）**：`from engine.executor import register_import_root` ＋ `register_import_root(Path(src).parent)`（每条目一次；该函数内部查重，幂等）；③ `import_excel_table(conn, src, ...)` |
| F3 | `gui/main_window.py::_close_session` 定义 L459-476 | 签名改为 `def _close_session(self, clear_copies: bool = True) -> None:`；L462-465 的 `clear_temp_copies()` 调用包进 `if clear_copies:` |
| F4 | `gui/main_window.py` L257 | `self._close_session()` → `self._close_session(clear_copies=False)` |
| F5 | 其余 `_close_session(` 调用点 | **执行时先 Grep 全部调用点**；除 L257 外一律保持默认 `True`（退出/关窗仍清副本） |

- **为何用"参数化 + 备选路径"**（`A-01` §3 改动点 3 的**备选**）：不把副本清理"挪到导入后"，避免"未选中的行其副本被删→回阶段 1 预览失效"的回归。本方案把"清副本"从"确认导入前"推迟到"退出/关窗"，**最小改动面**。
- **为何必须调 `register_import_root()`**：`_IMPORT_ROOTS` 只含 `temp/input_selection`；`A-10` 落地后 `source.file` 变成原始路径，阶段 3 的 `ensure_input_tables` → `_validate_import_path`（L105）会抛 `ParserError` 且**不在** L110 捕获面内 → 逃逸为 `failed`。本步是**两项能共存的前提**。
- **GUI 侧路径校验**（`A-01` §4）：本批以"`source_path` 为空时回落副本路径"＋"`register_import_root()` 显式放行源目录"替代新增校验函数（`[ADJUSTED: 以注册钩子替代新增校验函数；理由＝改动面更小、语义等价]`）；**不新增安全边界放宽之外的机制**。

### 3.4 `A-02` exe 态 `.xls` 崩溃 ＋ 入口按钮锁死

| # | 文件 · 位置 | 改后（语义） |
|---|---|---|
| F1 | `gui/page_input_selection.py` 文件头 import 区 | 补 `import zipfile`（若未导入）＋ `from gui.error_messages import translate_error` |
| F2 | `gui/page_input_selection.py::_on_add_files` L417 | 异常元组扩容：`except (FileNotFoundError, ValueError, PermissionError, ImportError, OSError, zipfile.BadZipFile) as e:` |
| F3 | 同函数（紧随其后） | **追加第 2 段** `except Exception as e:` → `logger.exception("[input_selection] 文件处理未预期异常")` ＋ 人话提示 ＋ `continue`（覆盖 `lxml` 解析类异常；**不引入 `lxml` 直接依赖**） |
| F4 | 同函数 L418-419 | 提示文案改为 `translate_error(f"{type(e).__name__}: {e}")` |
| F5 | 同函数 L376-429 的 `for` 循环 | 整体包 `try: … finally: self._btn_import.setEnabled(len(self._entries) > 0)`（**保证异常不逃出槽函数、按钮必复位**） |

- 说明：`ImportError` 的根因（`spec` 缺 `'xlrd'`）由 `A-17` 修；本项保证"即使缺件也只坏该文件、按钮可用"。

### 3.5 `A-13` 导入失败清单恒为兜底话术

| # | 文件 · 位置 | 改后（语义） |
|---|---|---|
| F1 | `gui/main_window.py` L328 | `translate_error(str(err))` → `translate_error(f"{type(err).__name__}: {err}")` |
| F2 | `gui/error_messages.py::_RULES` L20-41 | **在 `("no such column", …)` 之前**插入 3 条：`("modulenotfounderror", …)`／`("标识符包含禁止字符", …)`／`("文件不是 excel 格式", …)` |

### 3.6 `A-14` 全局兜底弹技术原文

| # | 文件 · 位置 | 改后（语义） |
|---|---|---|
| F1 | `gui/app.py::_excepthook` L263-264 | 改为**函数内**导入 `from gui.error_messages import translate_error, log_hint`，弹窗文案＝`translate_error(f"{exc_type.__name__}: {exc_value}")` ＋ 日志目录提示；L261 的技术日志**保留** |

### 3.7 `A-17` `.xls` 老格式支持链断裂

| # | 文件 · 位置 | 改后（语义） |
|---|---|---|
| F1 | `RPA_Workflow_v3.spec` `hiddenimports` L27-53 | 追加 `'xlrd',`（附注释：xlrd 以字符串传参给 `pd.read_excel(engine="xlrd")`，从未 `import`，静态分析收集不到）＋ `'ops.excel_normalizer',`（P3 将新建的模块，**预先登记**） |
| F2 | `requirements.txt` L12 | `xlrd` → `xlrd>=2.0            # .xls 读取（ops/excel_preprocessor.py engine="xlrd"）`（与其它行的注释风格一致） |

- **exe 重建与真机 `.xls` 验证＝`P-2`，由人工执行**（本批只改文件，验证挂起）。

---

## 4. 假设与决策

| # | 决策 | 来源 |
|---|---|---|
| **D1** | **本批由 Coordinator 直接执行**（不派 Sub-Agent）：因含 `A-01`＋`A-10`＋白名单的**跨条目耦合**，需全局判断；后续 P1~P6 按 plan.md §0.8 分发 | 工程判断（已向人工披露） |
| **D2** | `A-01` 的副本清理采用 plan.md §3 的**备选路径**（`clear_copies` 参数化），**不**把清理挪到导入后（避免"未选中行的副本被删→预览失效"） | plan.md A-01 §3 备选 |
| **D3** | `A-02` 以"精确元组 ＋ `except Exception` 兜底"覆盖异常面；**不直接 `import lxml`**（避免把 lxml 变成硬依赖） | §0.1 硬约束（不引入新依赖） |
| **D4** | `A-01` 的 GUI 路径校验以 `register_import_root()` 实现，**不新增校验函数**（改动面最小、语义等价） | plan.md A-01 §4 备选 |
| **D5** | `A-10` 采用"新增 `TableEntry.source_path` 字段"路径，**不采用** `main_window` 侧替换法 | plan.md A-10 §3 备选 |
| **D6** | 本批**不执行 git**；完成后输出「待人工提交清单」 | `AGENTS.md` §1 |
| **D7** | 改动前备份：7 个目标文件 → `_temp/ImportData/backup/P0/` | plan.md 各条目 §6 |
| **D8** | 门禁按 plan.md §1.4 用 **conda**（`CPS-GPES_RPA-py311`）＋ `QT_QPA_PLATFORM=offscreen` | 人工裁定（2026-10-18） |
| **D9** | 门禁失败处置：**先判性质**（修复暴露旧缺陷 → 登记回报；本批引入回归 → 回滚该文件并 `[SUB_AGENT_BLOCKED]`） | plan.md D10 |
| **D10** | 若 118 用例出现失败且集中在 `tests/` 对 `TableEntry`／`_RULES`／`get_entries` 的既有断言 → 属**契约变更**，同步更新测试并登记 | 工程判断 |

---

## 5. 验证步骤

| # | 验收项 | 判据 |
|---|---|---|
| V1 | 场景 **S1（头号）** | 阶段 1 用 [add] 选入 2-sheet 样本 → 勾选 → 「确认并导入」→ 阶段 2 正确显示 T1／T2（**无「全部数据表导入失败」**） |
| V2 | `[ADJUSTED-1]` 回归 | 导入后触发 `ensure_input_tables` 补导路径（删掉会话库中的输入表再执行）→ **不报** `输入文件路径不在允许范围` |
| V3 | 配置恢复 | 配 2 步 → 关闭程序 → 重开 → 表清单与步骤均恢复；`workspace/last_config.json` 的 `tables[].source.file` **为原始路径**（非 `temp/input_selection/` 副本） |
| V4 | 身份比对 | 同名 sheet 换文件（`A/电费.xlsx` → `B/电费.xlsx`）→ 出现「引用已变化」提醒；同一文件重导**不误报** |
| V5 | 异常隔离 | 0 字节／改名 xlsx 导入 → 只该文件失败、其余照常、按钮可用、提示为中文人话 |
| V6 | 话术 | `translate_error("PermissionError: [Errno 13] …")` 命中「文件正被其他程序占用」；`.xls` 缺件走新规则 |
| V7 | 交付配置 | `spec` 含 `'xlrd'` 与 `'ops.excel_normalizer'`；`requirements.txt` 的 `xlrd` 有版本约束 |
| V8 | 统一门禁 | ① `unittest discover` ≥118 用例且 `OK` ② 双 smoke 退出码 0 ③ 自检 `ok==True` 且 6 项 |
| V9 | 未越界 | 未改引擎调度结构／GUI 布局／步骤函数语义；无新第三方依赖；无绝对路径 |
| V10 | 交付物 | 7 个文件改动落盘并可 `Read` 抽查；备份快照存在于 `_temp/ImportData/backup/P0/` |

---

## 6. 执行顺序（批准后）

1. 备份 7 个目标文件 → `_temp/ImportData/backup/P0/`。
2. Grep 全部 `_close_session(` 调用点（确认除 L257 外均为默认清副本）。
3. 逐项施工（**按依赖序**）：`A-10`（F1-F5）→ `A-19` → `A-01`（F2-F5；F1 复用 A-10 的 F1）→ `A-02` → `A-13` → `A-14` → `A-17`。
4. 每个文件改完即做**语法自检**：`conda run … python -m py_compile <file>`（避免低错）。
5. 跑 §5 的 V8 统一门禁；记录实测输出。
6. 跑 V2／V3／V4／V5 场景验证（可脚本化的做脚本，GUI 部分用 `offscreen` 直接调用槽函数）。
7. 更新 `docs/task-records/2026-10-18-importdata-repair.md`（追加 Step 4：P0 批）。
8. 在 plan.md 各条目旁补 `[ADJUSTED]`（`A-01`／`A-10` 的备选路径选用记录）。
9. 输出批次简报（提示词 §六格式）＋「待人工提交清单」。

---

## 7. 待人工确认项（执行中随时提出）

| # | 事项 | 触发条件 |
|---|---|---|
| Q-1 | `A-17` 的 **exe 重建 ＋ 真机 `.xls` 验证**（`P-2`）须由人工执行；本批只改文件并将该验证标为挂起 | 执行 `A-17` 时 |
| Q-2 | 若 118 用例因 `TableEntry`／`_RULES` 契约变更而失败 → 我同步改测试并**回报**，不静默 | 门禁失败时 |
| Q-3 | 若 `register_import_root()` 在 GUI 侧无合适调用点（例如 `e` 中 `source_path` 恒为空）→ 以源码为准改为只注册 `file_path` 的父目录，并回写 `[ADJUSTED]` | 执行 `A-01` 时 |
