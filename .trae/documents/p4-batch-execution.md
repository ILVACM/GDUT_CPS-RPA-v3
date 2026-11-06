# 计划：执行 **P4 批次**（类型/内容/特殊值 ＋ 写库原子，9 项）

> 计划日期：2026-10-18 ｜ 施工依据：`_temp/ImportData/plan.md` **§1.1 的 P4 行**（L343）＋ 9 项条目正文 ＋ §1.6 的 `G-5` 裁定
> 前置：**P-0／P0／P1／P2／P3 均已完成并验收**（P3：118 用例 OK／双 smoke OK／自检 6/6）
> 运行方式：**C（多 Agent 协作）**——按 plan.md §0.8 派 **`Agent-P4`** 子 Agent 执行；Coordinator（我）负责分发、验证、仲裁与写回
> 本批 9 项：`A-04`、`A-06`、`A-07`、`A-08`、`REQ-R7`、`REQ-H3`、`REQ-H4`、`A-15`、`A-16`

---

## 1. 摘要

P4 是 A 链**最大的一批**：把 P3 建好的 `excel_normalizer.py` 补齐为完整管线（类型推断／日期／布尔／空值／错误值／清洗），并**首次接线**（`table_importer` 改调 `normalize_sheet`），同时收口写库原子性（`A-15`／`A-16`，已按 §1.6 的 `G-5` 三件套裁定）。

**规格体量**：9 项在 plan.md 中合计约 600+ 行（含每项的七段式与 §8 Agent 执行指引）。故按 plan.md §0.8 的既定机制，**派 `Agent-P4` 子 Agent 执行**（上下文隔离），Coordinator 只读 §1.1 分发、验交付物、跑门禁、写回留痕。**这与前四批"我直接执行"的做法不同，理由见 §4-D1。**

---

## 2. 现状分析（Phase 1 实测）

| 现场 | 实测 | 用途 |
|---|---|---|
| plan.md §1.1 L343 | **P4 行原文**：`A-04`（前导零与类型推断）、`A-06`（日期降级）、`A-07`（日期筛选 0 行）、`A-08`（NA 字面吞值）、`REQ-R7`、`REQ-H3`、`REQ-H4`、**`A-15`（写库非原子）**、**`A-16`（空壳表跳过补导）**；6 A＋3 REQ；分配 **`Agent-P4`**；"`A-15`／`A-16` 目标文件与其余条目**不重叠** → 可拆并行子 Agent（**默认随 `Agent-P4` 顺序执行**）" | 分发依据 |
| plan.md 条目位置 | `A-04`@L678、`A-06`@L833、`A-07`@L905、`A-08`@L968、`A-15`@L1535、`A-16`@L1628、`REQ-R7`@L2138、`REQ-H3`@L2274、`REQ-H4`@L2334 | 子 Agent 的读取范围（**只读这些段**） |
| `rpa_engine/ops/excel_normalizer.py` | P3 已落地：契约 ＋ R3/R4/R5 ＋ `FULL_LOAD_MAX_ROWS` 护栏；**管线中 H4／R7／A-08／A-04 仍未实现** | 本批补齐 |
| 目标文件（按 §1.1） | 模块侧：`ops/excel_normalizer.py` ＋ `ops/table_importer.py`（**`A-04` 的接线**）；写库侧：`ops/sqlite_manager.py` ＋ `engine/executor.py`（`A-15`／`A-16`）→ **两侧不重叠** | 可拆但本批**串行**（见 D2） |
| plan.md L2330 | **强制管线顺序**：公式兜底(R4) → 错误值(H4) → 超链接(R5) → 清洗(R7) → 空值策略(A-08) → 类型推断(A-04) | 本批须把 H4/R7/A-08/A-04 插到位 |

---

## 3. 分发方案（decision-complete）

### 3.1 派发 `Agent-P4`（general-purpose Sub-Agent，前台）

**下发内容（作为 prompt 的固定前缀与指令）**：

1. **施工图唯一来源**：`d:\CPS-GPES_RPA-20250312\v3\_temp\ImportData\plan.md`。**只读以下段落**（不得整读文件）：
   `A-04`@L678~`A-05` 前、`A-06`@L833~`A-07` 前、`A-07`@L905~`A-08` 前、`A-08`@L968~`A-09` 前、`A-15`@L1535~`A-16` 前、`A-16`@L1628~ 下一 `###` 前、`REQ-R7`@L2138~`REQ-H1` 前、`REQ-H3`@L2274~`REQ-H4` 前、`REQ-H4`@L2334~`REQ-H5` 前；另读 **§1.1 L337-346**、**§1.6（`G-5` 裁定）**、**Part 0 §0.1／§0.2／§0.2.1**（硬约束与"语义示意"规则）。
2. **执行顺序（批内有序）**：`A-04` → `A-06` → `A-07` → `A-08` → `REQ-R7` → `REQ-H3` → `REQ-H4` → `A-15` → `A-16`。
3. **硬约束前缀（必须遵守）**：
   - 不引入新依赖（`requirements.txt` 不得新增；**禁 `pywin32`／`win32com`**）；不用 `eval`/`exec`/`pickle`；不写绝对路径。
   - **不改** 引擎调度结构（步骤分发、信号、线程模型）／GUI 布局（仅「确认并导入」槽内可加错误回显）／步骤功能函数语义（`ops/` 的 9 项 BUILTIN_OPS 行为）。
   - `import_excel_table`／`read_excel_sheet`／`scan_sheets`／`normalize_sheet` 的**签名与返回值结构不变**（除该项明确要求者）。
   - 管线顺序（L2330）**不得颠倒**。
   - 内存：不得同时持有两份全量 DataFrame（就地 `iat` 写回；dtype 不兼容时用既有 `_ensure_object_col()` 护栏）。
   - **`[ADJUSTED-13]` 已知缺口不解决**：纯公式行被 `skip_blank_lines` 丢弃属 H5/A-08 之外的口径，若该项正文未要求修，则**不得顺手修**（超范围）。
   - **不得修改** `AGENTS.md`／`docs/**`／`build/**`；**不执行任何 git 命令**。
4. **"改前/改后为语义示意"**（§0.2.1）：找不到完全一致的文本**不是缺陷**，按语义等价定位；定位失败 → `[SUB_AGENT_BLOCKED]`，**不得猜测硬改**。
5. **自验（子 Agent 自跑，允许跑统一门禁——本批两侧串行、无并发干扰）**：
   - `conda run -n CPS-GPES_RPA-py311 python -m py_compile <改动文件>`
   - `conda run -n CPS-GPES_RPA-py311 python -m unittest discover -s tests`（cwd=`rpa_engine`，需 `QT_QPA_PLATFORM=offscreen`）→ 期望 **Ran 118 tests — OK**
   - 双冒烟 `tools/smoke/smoke_m1m3.py`／`smoke_mb.py` → `SMOKE_ALL_OK`
   - 为 9 项各写**脚本化验收**（`openpyxl` 造样本）写入 `_temp/ImportData/verify_p4_scenarios.py` 并跑通
6. **交付与汇报格式**：逐项 `[SUB_AGENT_COMPLETE]` 或 `[SUB_AGENT_BLOCKED]`（附原因＋已尝试＋2~3 选项）；**汇总报告须含**：① 每项状态 ② 每项**实际改动的文件＋函数＋行号锚点** ③ 门禁输出**逐字** ④ 新发现的 `[ADJUSTED]` ⑤ 验收脚本路径与结果 ⑥ 未接线/遗留说明。
7. **备份**：改动前把每个既有目标文件复制到 `_temp/ImportData/backup/P4/`（新建文件无需备份）。

### 3.2 Coordinator（我）的验证与写回（不外包）

| # | 动作 |
|---|---|
| V1 | **交付物存在性核对**：读子 Agent 报告后，逐一 `Grep`/`Read` 抽查其声称的改动锚点是否真实落盘（**信任但验证**） |
| V2 | **跑统一门禁**（我自己再跑一遍）：`py_compile` ＋ `unittest discover`（≥118 OK）＋ 双 smoke ＋ 自检 6/6 |
| V3 | **跑子 Agent 的验收脚本**（我也跑一遍），核对关键判据：前导零保留为文本／日期入 TEXT／布尔 1-0／字面 `NA` 保留／错误值→NULL 且不中断／清洗生效／写库原子（失败不留半成品）／空壳表被补导 |
| V4 | **越界检查**：`git status --porcelain` 只看不改；确认 `AGENTS.md`／`docs/**`／`build/**` 未被子 Agent 触碰；`requirements.txt` 无新增 |
| V5 | **仲裁**：若子 Agent 报 `[SUB_AGENT_CONFLICT]`／`[SUB_AGENT_BLOCKED]` → 按 §6.6 规则处理（同一文件冲突按批次序；签名变更升级 `[REQUIRES_HUMAN_CONFIRMATION]`） |
| V6 | **写回**：plan.md 新增「§0.7.6 P4 批次施工记录」；`docs/task-records/2026-10-18-importdata-repair.md` 追加 **Step 8** 并同步「涉及文件汇总」与「关闭标识」 |

---

## 4. 假设与决策

| # | 决策 | 依据 |
|---|---|---|
| **D1** | **本批改派子 Agent**（不再由我直接执行）——理由：① 9 项规格约 600+ 行，我当前上下文已高位；② plan.md §0.8 的既定机制即为此设计；③ 两侧文件不重叠，适合隔离执行。**代价**：我无法在子 Agent 执行中实时观察，故对其产出执行 §3.2 的"信任但验证"全流程 | plan.md §0.8＋§1.1 L343 |
| **D2** | **子 Agent 串行**（只派一个 `Agent-P4`，不拆并行）——避免两个 Sub-Agent 并发跑门禁时争用共享临时区／工作区导致结果不可信；plan.md 亦写明"**默认随 `Agent-P4` 顺序执行**" | plan.md §1.1 L343 |
| **D3** | `A-04` 的**接线**（`table_importer` L76 改调 `normalize_sheet`）在本批落地 → P3 成果首次进入真实导入路径 | plan.md §4.3（该行归属 `A-04`） |
| **D4** | `A-15`／`A-16` 按 **§1.6 的 `G-5` 三件套**（活表覆盖守卫／写入原子性／有效性判据）实现 | plan.md §1.6 |
| **D5** | 子 Agent 的验收脚本命名 `verify_p4_scenarios.py`；其**不得**覆盖既有 `verify_p0~p3` 文件 | 留痕不覆盖 |
| **D6** | 不执行 git；完成后输出「待人工提交清单」 | `AGENTS.md` §1 |
| **D7** | 若子 Agent 未能完成或产出不可信 → 我**接管剩余项**并如实回报（不掩饰） | 工程判断 |
| **D8** | 「纯公式行」`[ADJUSTED-13]` 缺口**本批不修**（除非某条目正文明确要求） | 防超范围 |

---

## 5. 验证步骤（批级验收）

| # | 项 | 判据 |
|---|---|---|
| V1 | 交付物真实性 | §3.2-V1 抽查：子 Agent 声称的每处改动锚点在磁盘上**可查到** |
| V2 | 统一门禁 | `py_compile` 0；`unittest discover` ≥118 `OK`；双 smoke `SMOKE_ALL_OK` 0/0；自检 6/6 |
| V3 | 九项功能 | 按 §3.2-V3 的判据逐项核对（含 `verify_p4_scenarios.py` 全绿） |
| V4 | 越界 | `AGENTS.md`／`docs/**`／`build/**` 未被触碰；`requirements.txt` 无新增；无绝对路径 |
| V5 | 闭合 | plan.md §0.7.6 ＋ 任务记录 Step 8 ＋ 汇总表/关闭标识同步；`[ADJUSTED]` 如实登记 |

---

## 6. 执行顺序（批准后）

1. 由我建 `_temp/ImportData/backup/P4/` 目录（子 Agent 落地前备份既有目标文件）。
2. 派 `Agent-P4`（prompt＝§3.1 全部内容）。
3. 收报告 → 跑 §3.2-V1~V5。
4. 中断/失败处理：按 D7。
5. 写回 §0.7.6 ＋ Step 8 ＋ 汇总同步。
6. 输出批次简报（含子 Agent 的逐项状态）＋「待人工提交清单」。

---

## 7. 待人工确认项

| # | 事项 | 触发条件 |
|---|---|---|
| Q-1 | **本批改派子 Agent**（与前四批做法不同）——若你希望我仍直接执行，需明示（会显著拉长单轮上下文） | 你显式要求时 |
| Q-2 | 若 `A-04` 的接线导致既有 118 用例出现失败 → 先判性质（契约变更 / 修复暴露旧缺陷），回归则回滚该文件并回报 | 门禁失败时 |
| Q-3 | `A-15`／`A-16` 的 `G-5` 残余风险（WAL 锁等待、循环导入、守卫误拦"故意覆盖活表"）若在执行中实证 → 升级 `[REQUIRES_HUMAN_CONFIRMATION]` | 子 Agent 报告时 |
