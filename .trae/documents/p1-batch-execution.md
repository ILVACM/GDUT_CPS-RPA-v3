# 计划：执行 **P1 批次**（临时区与格式转换，3 项）

> 计划日期：2026-10-18 ｜ 施工依据：`_temp/ImportData/plan.md` §1.1 的 P1 批 ＋ 各条目 Part 2 正文 ＋ §0.7.1／§0.7.2
> 前置：**P-0 与 P0 均已完成并验收**（P0：118 用例 OK／双 smoke OK／自检 6/6）
> 本批 3 项：`A-11`、`A-12`、`A-18`（串行；`A-12` 与 `A-18` 共用同一处改动）
> 运行方式：A（单 Agent 直接执行——本批文件高度重叠 `excel_preprocessor.py`，且与 A-10/A-01 的落地状态耦合）

---

## 1. 摘要

修"临时区副本"的两类毛病：① **超龄清理误删**（`copy2` 把源文件的旧 mtime 带给副本）；② **同名异后缀静默覆盖**（`.xls` 转出的 `.xlsx` 无条件覆盖既有副本）。共 **5 处代码改动**，落在 **2 个文件**。

**本批不含**：`read_excel_sheet` 的类型/空值改造（属 P4/P2）、任何引擎调度或 GUI 布局改动。

---

## 2. 现状分析（Phase 1 实测）

| 现场 | 实测 | 用途 |
|---|---|---|
| `ops/excel_preprocessor.py` L17-23 | `import gc`／`shutil`／`Path`／`typing`／`pandas`／`loguru` —— **无 `import os`** | `A-11` F1 需补 |
| 同文件 L58-63 | 同名查重**只比同后缀**：`while dst.exists(): dst = f"{src.stem}_{counter}{src.suffix}"` | `A-12` F2 |
| 同文件 L65 | `shutil.copy2(src, dst)`（**保留源 mtime**） | `A-11` F1 |
| 同文件 L117-119 | `new_path = src.with_suffix(".xlsx")` ＋ `wb.save(str(new_path))`（**无冲突检测**） | `A-12` F1 ＝ `A-18` 同一处 |
| `gui/main_window.py` L236-237 | 启动序：`_cleanup_stale_sessions()` **先于** `_restore_last_config()` | `A-11` F3 |
| `gui/main_window.py` L699-733 | `cleanup_stale_files(ws_root, temp_root, cutoff_hours=24)`：L721 `cutoff`；L723-730 `temp_root.iterdir()` 按 `st_mtime < cutoff` → `p.unlink()`（**无引用保护**） | `A-11` F2 |
| `gui/main_window.py` L735-739 | `_cleanup_stale_sessions()`＝`cleanup_stale_files(ENGINE_ROOT/"workspace", ENGINE_ROOT/"temp"/"input_selection")` | `A-11` F2 的入参路径 |

> **行号已随 P0 落地而位移**（`cleanup_stale_files` 由 679 → **699**）；执行时仍以**实际文本**定位（plan.md §0.2.1）。

### 2.1 跨条目交互发现（须记 `[ADJUSTED]`）

**`A-10` 已消解 `A-11` 的主症状**：`A-10` 落地后 `last_config` 的 `tables[].source.file` 落**原始路径**，而 `cleanup_stale_files` 只清 `temp/input_selection` 下的**副本** → 「含早于 24h 的 `.xlsx` 时恢复 100% 失效」这一原症状**已不复现**（恢复判据查的是原始文件，不受 temp 清理影响）。

**本批仍做 `A-11` 三项的理由**：① `F1` 是**防御性**修正（副本 mtime 归零，避免"刚复制的副本立刻被判超龄"）；② `F2`／`F3` 覆盖**迁移期**——工作区里已存在的**旧** `last_config`（`A-10` 之前落盘）其 `source.file` 仍指向副本，若被清理则恢复失败；③ `F3` 使"先恢复、后清理"的顺序语义正确，成本极低。

---

## 3. 变更内容（decision-complete）

> 改前/改后为**语义示意**；执行时以实际文本等价替换（§0.2.1）。

### 3.1 `A-11` 超龄清理用 mtime 但 `copy2` 保留源 mtime

| # | 文件 · 位置 | 改前（语义） | 改后（语义） |
|---|---|---|---|
| F1 | `ops/excel_preprocessor.py` L18 附近 | 只有 `import gc`／`import shutil` | 追加 `import os` |
| F2 | `ops/excel_preprocessor.py::validate_and_copy` L65 | `shutil.copy2(src, dst)` | `shutil.copyfile(src, dst)` ＋ `os.utime(dst, None)`（**副本 mtime ＝ 当前时间**）＋ 注释说明"超龄判据只反映副本在本机的存活时长" |
| F3 | `gui/main_window.py::cleanup_stale_files` 的 temp 循环（L721-730） | 仅按 `p.stat().st_mtime < cutoff` 判删 | **删除前加引用保护**：先读 `workspace/last_config.json` 的 `tables[].source.file` 组成 `protected` 集合（`Path(...).resolve()`）；`if p.resolve() in protected: continue`。读取失败（文件不存在/JSON 坏）→ `protected` 为空集，**行为与改动前一致** |
| F4 | `gui/main_window.py::__init__` L236-237 | `_cleanup_stale_sessions()` → `_restore_last_config()` | **交换顺序**：`_restore_last_config()` → `_cleanup_stale_sessions()`（先恢复、后清理；配合 F3 的保护集合） |

- **不变量**：`cleanup_stale_files` 的**签名与返回值不变**（静态纯函数、可注入路径直测——既有单测依赖此特性）；会话库清理逻辑**不动**。
- **实现提示**：`last_config.json` 路径与 `_restore_last_config` 同源（`ENGINE_ROOT / "workspace" / "last_config.json"`）。

### 3.2 `A-12` 同名异后缀静默覆盖已导入副本

| # | 文件 · 位置 | 改后（语义） |
|---|---|---|
| F1 | `ops/excel_preprocessor.py::ensure_xlsx` L117-119 | `new_path = src.with_suffix(".xlsx")` 后**加同款查重**：`counter = 1; while new_path.exists(): new_path = src.with_name(f"{src.stem}_{counter}.xlsx"); counter += 1`（随后照旧 `wb.save`） |
| F2 | `ops/excel_preprocessor.py::validate_and_copy` L58-63 | 查重条件**扩展为跨后缀**：`while dst.exists() or (temp_path / f"{dst.stem}.xlsx").exists():`（其余不变） |

- **注**：`F1` 与 `A-18` 为**同一处改动**（`A-18` 不再另设改动点，按 plan.md `A-18` §3 结语执行）；`A-18` 的验收复用 `F1` 的用例。

### 3.3 `A-18` 转换产物无冲突检测

**无独立改动点**——与 §3.2 的 `F1` 同一处（plan.md `A-18` §3 已注明"与 `A-12` 改动点 1 为同一处改动"）；本批只为其**运行验收用例**并回写 `[ADJUSTED: 与 A-12 F1 同处实现]`。

---

## 4. 假设与决策

| # | 决策 | 来源 |
|---|---|---|
| **D1** | 本批**串行由 Coordinator 直接执行**（三项目标同文件 ＋ 与 P0 落地状态耦合） | plan.md §1.1 P1 备注 |
| **D2** | `A-11` **三项全做**（含 `F2`／`F3` 的迁移期兼容），尽管 `A-10` 已消解其主症状——理由见 §2.1 | 工程判断 ＋ plan.md §1.1（P1 未列降级） |
| **D3** | `cleanup_stale_files` 的**签名与"静态纯函数"特性保持不变**（既有单测 `test_engine_*` 依赖） | plan.md `A-11` §4 |
| **D4** | `A-18` 不另设改动点，与 `A-12` F1 同处实现并共用验收 | plan.md `A-18` §3 |
| **D5** | 不执行 git；完成后输出「待人工提交清单」 | `AGENTS.md` §1 |
| **D6** | 改动前备份 2 个目标文件 → `_temp/ImportData/backup/P1/` | plan.md 各条目 §6 |
| **D7** | 门禁按 plan.md §1.4 用 conda ＋ `QT_QPA_PLATFORM=offscreen` | 人工裁定（2026-10-18） |
| **D8** | 若 118 用例失败且落在 `cleanup_stale_files` 的既有断言 → 判性质（契约变更则同步改测试并回报） | plan.md D10 |

---

## 5. 验证步骤

| # | 验收项 | 判据 |
|---|---|---|
| V1 | **A-11 F1**（mtime 归零） | 造一个 mtime ＝ 3 天前的源文件 → `validate_and_copy` → 副本 `st_mtime` ≈ 当前时间（**非**源 mtime） |
| V2 | **A-11 F2/F3**（保护 ＋ 顺序） | 把该副本路径写进 `last_config.json` 的 `source.file` → 跑 `cleanup_stale_files(temp=该目录, cutoff_hours=24)` → 该副本**未被删**；未引用的超龄文件**仍被删** |
| V3 | **A-12 F2**（跨后缀查重） | 临时区预置 `X.xlsx` → `validate_and_copy(X.xls)` → 返回副本名 **`X_1.xls`**（不是 `X.xls`） |
| V4 | **A-12 F1 ＝ A-18**（产物不覆盖） | 上例中 `ensure_xlsx(X_1.xls)` → 产物 **`X_1.xlsx`**；既有 `X.xlsx` **内容不变** |
| V5 | 回归 | `unittest discover` ≥118 用例且 `OK`；双 smoke `SMOKE_ALL_OK` 0/0；自检 6/6；`py_compile` 退出码 0 |
| V6 | 未越界 | 未改 `validate_and_copy`／`ensure_xlsx` 的**签名与返回值**；未新增依赖（`os`／`shutil` 均标准库）；无绝对路径 |

---

## 6. 执行顺序（批准后）

1. 备份 `ops/excel_preprocessor.py`、`gui/main_window.py` → `_temp/ImportData/backup/P1/`。
2. 改 `excel_preprocessor.py`：`import os`（F1）→ `validate_and_copy` 的 `copyfile+utime`（A-11 F2）＋ 跨后缀查重（A-12 F2）→ `ensure_xlsx` 产物查重（A-12 F1／A-18）。
3. 改 `main_window.py`：`cleanup_stale_files` 的引用保护（A-11 F3）→ 启动顺序交换（A-11 F4）。
4. `py_compile` 两文件 → 跑 V1~V4 脚本化验收（写入 `_temp/ImportData/verify_p1_scenarios.py`）。
5. 跑 V5 统一门禁（118 用例／双 smoke／自检）。
6. 追加任务记录 Step 5；在 plan.md 的 `A-11`／`A-12`／`A-18` 旁回写 `[ADJUSTED]`（含 §2.1 的跨条目交互与 `A-18` 同处实现）＋ 新增「§0.7.3 P1 批次施工记录」。
7. 输出批次简报 ＋「待人工提交清单」。

---

## 7. 待人工确认项

| # | 事项 | 触发条件 |
|---|---|---|
| Q-1 | 若你希望 `A-11` 的 `F2`／`F3`（迁移期兼容）**不做**（因 `A-10` 已消解主症状）→ 我改为只做 `F1` 并记录取舍 | 你显式要求时 |
| Q-2 | 若有既有单测断言 `validate_and_copy` 使用 `copy2`（保留 mtime）→ 属契约变更，我会同步改测试并**回报** | 门禁失败时 |
