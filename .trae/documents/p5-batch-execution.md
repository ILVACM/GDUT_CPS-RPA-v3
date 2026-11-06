# 计划：执行 **P5 批次**（元数据与报告，6 REQ）

> 计划日期：2026-10-18 ｜ 施工依据：`_temp/ImportData/plan.md` **§1.1 的 P5 行**（L395）＋ 6 项条目正文
> 前置：**P-0／P0／P1／P2／P3／P4 均已完成并验收**（P4：118 用例 OK／双 smoke OK／自检 6/6／`VERIFY_P4_ALL_OK`）
> 运行方式：**C（多 Agent 协作）**——派 **`Agent-P5`** 子 Agent 执行；Coordinator（我）负责分发、验证、仲裁与写回
> 本批 6 项：`REQ-H1`、`REQ-H5`、`REQ-H6`、`REQ-H7`、`REQ-H9`、`REQ-H10`

---

## 1. 摘要

把"程序做了什么"变成**用户看得见的交付物**：重复列名去重、全空列/尾空行处理、非单元格内容丢弃告知、超长数字精度提示，并把元数据表、处理报告、失败清单**落盘**，同时给 `temp/normalized/` 建立幂等与目录管理。

**批内串行**（§1.1 L395 明定：`REQ-H9` **依赖** `REQ-H1/H5/H6/H7` 的产出）。

---

## 2. 现状分析（Phase 1 实测）

| 现场 | 实测 | 用途 |
|---|---|---|
| §1.1 L377 | `Agent-P5` ｜ P5 ｜ `REQ-H1`／`H5`／`H6`／`H7`／`H9`／`H10` ｜ "`REQ-H9` 依赖前者的产出 → **串行**" | 分发依据 |
| §1.1 L395（P5 行） | 6 REQ；分配 **`Agent-P5`**；❌ **串行**；备注：**"同一新建文件的产出汇总关系"** | 批次口径 |
| **条目位置（已按当前磁盘重新定位）** | `REQ-H1`@**L2256**、`REQ-H5`@**L2452**、`REQ-H6`@**L2515**、`REQ-H7`@**L2579**、`REQ-H9`@**L2643**、`REQ-H10`@**L2733** | 子 Agent 的读取范围 |
| `REQ-H9` §1 定位（L2646-2648） | 文件＝**`rpa_engine/ops/excel_normalizer.py`**（落盘函数）／**`rpa_engine/gui/main_window.py`**（`failed` 清单落盘）；骨架含 `write_normalize_report(result, out_dir, …)`／`write_meta_table(conn, result, sqlite_table, …)`（L2673/2679） | ⇒ **无新模块文件**，落盘能力进 normalizer |
| `REQ-H10` | 骨架含 `load_normalized_cache(key)`／`save_normalized_cache`（L2763 附近）；涉及 **`rpa_engine/paths.py`**（§0.7 清单第 19 项 `[UNVERIFIED]`：需读 `paths.py` 全文核实命名与风格） | 子 Agent 须**先核实该 `[UNVERIFIED]`** |
| `REQ-H7` | 落在**扫描侧**（`excel_preprocessor.scan_sheets`，read_only 阶段）；"**只提示，不改数据**"（源文件精度已丢，任何"修复"都是编造） | 子 Agent 须定位扫描侧 |
| `REQ-H1` 与 `A-03` 的关系 | `REQ-H1` 实现要点 ②"空列名按 `未命名列_N` 归一"＝**与 `A-03` 改动点 1 第 ② 条共用一处实现**（P2 已声明：空列名留给 P5 处理，`[ADJUSTED-10]`） | **本批须落地该归一** |
| 跨批交互提示 | `A-11` 的 `cleanup_stale_files` 只清 `temp/input_selection`（`_cleanup_stale_sessions` 入参），而 `temp/normalized/` 是**另一目录**，故 H10 的产物**不会被超龄清理误删** —— 子 Agent 须**实测确认**并在报告注明 | 防误改清理逻辑 |

> **教训应用**：本计划的条目行号取自**当前磁盘**（此前一版行号已被我写入 §0.7.5/§0.7.6 整体后移）。

---

## 3. 分发方案（decision-complete）

### 3.1 派发 `Agent-P5`（general-purpose Sub-Agent，前台）

**下发内容**：

1. **施工图唯一来源**：`_temp/ImportData/plan.md`（**禁止整读**）。只读：**Part 0 §0.1／§0.2／§0.2.1**、**§1.1（L377-396）**、以及 6 项条目正文：`REQ-H1`@L2256、`REQ-H5`@L2452、`REQ-H6`@L2515、`REQ-H7`@L2579、`REQ-H9`@L2643、`REQ-H10`@L2733（各自读到下一个 `###` 前）。
2. **执行顺序（批内有序）**：`REQ-H1` → `REQ-H5` → `REQ-H6` → `REQ-H7` → `REQ-H9` → `REQ-H10`。
3. **硬约束前缀**：不引入新依赖；不用 `eval`/`exec`/`pickle`；不写绝对路径；不改引擎调度结构／GUI 布局（仅「确认并导入」槽内可加错误回显）／步骤功能函数语义；保持 `import_excel_table`／`read_excel_sheet`／`scan_sheets`／`normalize_sheet` 的**签名与返回值结构不变**；管线顺序（施工图 L2330 附近）不得颠倒；内存不得同时持有两份全量 DataFrame；**不得修改** `AGENTS.md`／`docs/**`／`build/**`／`plan.md`／既有 `verify_p0~p4` 与 `probe_p3*` 文件；**不执行任何 git 命令**。
4. **先核实 1 项 `[UNVERIFIED]`**：`REQ-H10` 改动点 1 依赖 `rpa_engine/paths.py` 的既有函数命名与风格 → **先读 `paths.py` 全文**再动手；若与施工图假设不符，按实际实现并记 `[ADJUSTED]`。
5. **`REQ-H7` 的边界**：**只提示、不改数据**（不得"补零/还原"）；`REQ-H1` 的**空列名归一**须在本批落地（承接 P2 的 `[ADJUSTED-10]`）；`REQ-H6` 的"丢弃非单元格内容"须**告知用户**（报告条目，不得静默）。
6. **备份（本批由你自负其责——修正 P4 教训）**：**在改任何一个既有文件之前**，先把它复制到 `_temp/ImportData/backup/P5/`（**你实际会改的每一个**，不要依赖我预置清单；P4 曾因我的预置清单漏列 5 个文件而无快照）。新建文件无需备份。在报告中列出你实际改动的**全部**文件清单。
7. **自验（把输出逐字带回）**：`py_compile` 每个改动文件；cwd=`<仓库根>/rpa_engine` ＋ `QT_QPA_PLATFORM=offscreen` 下 `unittest discover -s tests` → 期望 `Ran 118 tests` ＋ `OK`；双冒烟 → `SMOKE_ALL_OK`；写 `_temp/ImportData/verify_p5_scenarios.py`（`openpyxl` 造样本，cwd=仓库根，`sys.path.insert(0,"rpa_engine")`）为 6 项各写**可判定**断言并跑通；把完整报告写到 `_temp/ImportData/p5-subagent-report.md`。
8. **交付与汇报格式**：逐项 `[SUB_AGENT_COMPLETE]`／`[SUB_AGENT_BLOCKED]`（附原因＋已尝试＋2~3 选项）；汇总须含 ① 逐项状态 ② **实际改动的全部文件＋函数＋行号锚点** ③ 门禁输出逐字 ④ 新 `[ADJUSTED]` ⑤ 验收脚本路径与结果行 ⑥ 遗留/未接线说明 ⑦ **实测确认"`temp/normalized/` 不被超龄清理误删"的结论**。
9. **"改前/改后为语义示意"**：找不到完全一致的文本**不是缺陷**，按语义等价定位；定位失败 → `[SUB_AGENT_BLOCKED]`，不得猜测硬改。

### 3.2 Coordinator（我）的验证与写回（不外包）

| # | 动作 |
|---|---|
| **V1** | **交付物真实性**：按子 Agent 报告逐处 `Grep`／`Read` 抽查其声称的改动锚点**全部**是否落盘（P4 抽查 13/13 通过） |
| **V2** | **统一门禁重跑**：`py_compile` ＋ `unittest discover`（≥118 OK）＋ 双 smoke ＋ 自检 6/6 |
| **V3** | **验收脚本重跑**：`verify_p5_scenarios.py`；核对关键判据（列名去重与报告、全空列标记/尾空行裁剪、非单元格内容丢弃＋告知、精度提示不改数据、元数据表/报告/失败清单**确实落盘**、H10 幂等不重复处理） |
| **V4** | **越界与完备性**：`git status --porcelain`（只看）；确认 `AGENTS.md`／`docs/**`／`build/**` 未动（用 mtime 比对）；`requirements.txt` 无新增；**且核对 `backup/P5/` 的覆盖是否等于子 Agent 报告的改动文件集**（防再次出现 P4 的备份缺口） |
| **V5** | **仲裁**：`[SUB_AGENT_CONFLICT]`／`[SUB_AGENT_BLOCKED]` 按 §6.6 处理；签名变更升级 `[REQUIRES_HUMAN_CONFIRMATION]` |
| **V6** | **写回**：plan.md 新增「§0.7.7 P5 批次施工记录」；任务记录追加 **Step 9** ＋ 同步「涉及文件汇总」与「关闭标识」 |

---

## 4. 假设与决策

| # | 决策 | 依据 |
|---|---|---|
| **D1** | **沿用子 Agent 派发**（P4 已验证有效：锚点 13/13、门禁重跑一致、无不实声明） | P4 实践 ＋ plan.md §0.8 |
| **D2** | **单个子 Agent 串行**（6 REQ 相同目标文件且 `REQ-H9` 依赖前四项产出；plan.md §1.1 亦标 ❌ 串行） | §1.1 L395 |
| **D3** | **备份责任下放给子 Agent**（要求它改前备份**自己实际会改的每个既有文件**并在报告列出全集）——**直接修正 P4 的"我预置清单漏列"缺陷** | P4 缺陷记录 |
| **D4** | **不预设"改动文件全集"**：本批预计落在 `ops/excel_normalizer.py`／`ops/excel_preprocessor.py`／`ops/table_importer.py`／`gui/main_window.py`／`rpa_engine/paths.py`（可能含 `engine/executor.py`），但**以子 Agent 实测报告为准** | 避免重蹈 P4 覆辙 |
| **D5** | `REQ-H7` **只提示不改数据**；`REQ-H1` 的**空列名归一**本批落地（承接 `[ADJUSTED-10]`） | 各条目 §3／§4 |
| **D6** | 「纯公式行」`[ADJUSTED-13]` 缺口与 `A-11` 的清理逻辑**本批不主动改**（除某项正文明确要求） | 防超范围 |
| **D7** | 不执行 git 写操作；完成后输出「待人工提交清单」 | `AGENTS.md` §1 |
| **D8** | 若子 Agent 未完成或产出不可信 → 我**接管剩余项**并如实回报 | 工程判断 |

---

## 5. 验证步骤（批级验收）

| # | 项 | 判据 |
|---|---|---|
| V1 | 真实性 | 子 Agent 声称的**每一处**改动锚点在磁盘可查到 |
| V2 | 统一门禁 | `py_compile` 0；`unittest discover` ≥118 `OK`；双 smoke `SMOKE_ALL_OK` 0/0；自检 6/6 |
| V3 | 六项功能 | `verify_p5_scenarios.py` 全绿；四类产物（元数据表／处理报告／失败清单／幂等）**在磁盘可见** |
| V4 | 越界与备份完备 | `AGENTS.md`／`docs/**`／`build/**` 未动；`requirements.txt` 无新增；**`backup/P5/` 覆盖 ＝ 改动文件集** |
| V5 | 闭合 | plan.md §0.7.7 ＋ 任务记录 Step 9 ＋ 汇总/关闭标识同步；`[ADJUSTED]` 如实登记 |

---

## 6. 执行顺序（批准后）

1. 由我建 `_temp/ImportData/backup/P5/` 目录（**内容由子 Agent 自行填充**）。
2. 派 `Agent-P5`（prompt＝§3.1 全部内容）。
3. 收报告 → 跑 §3.2 V1~V5。
4. 中断/失败按 D8。
5. 写回 §0.7.7 ＋ Step 9 ＋ 汇总同步。
6. 输出批次简报 ＋「待人工提交清单」。

---

## 7. 待人工确认项

| # | 事项 | 触发条件 |
|---|---|---|
| Q-1 | 若 `REQ-H9` 的报告落盘路径/文件名与 `REQ-H10` 的 `temp/normalized/` 约定冲突 → 我按 plan.md 原文裁决，若原文未定则升级 `[REQUIRES_HUMAN_CONFIRMATION]` | 执行中 |
| Q-2 | 若 `REQ-H10` 的 `paths.py` 实测与施工图假设不符 → 按实际实现并记 `[ADJUSTED]`，**不**改 `paths.py` 既有函数签名 | 子 Agent 报告时 |
| Q-3 | 若门禁出现失败 → 先判性质（本批回归／修复暴露旧缺陷／契约变更），回归则回滚该文件并回报 | 门禁失败时 |
