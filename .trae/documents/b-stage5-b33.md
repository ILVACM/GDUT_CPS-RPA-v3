# 计划：B 链 阶段 5（`B-33`）— 单条 · **改源码** · ⚠️ 越界风险最高

> 计划日期：2026-10-19 ｜ 上游：已批准的《B 类 13 项代码执行计划》§3.1 阶段 5
> **已完成**：阶段 0／1／2／3／4 ⇒ **9/13**，门禁全绿（`Ran 119 OK`）

---

## 1. 摘要

| 项 | 内容 |
|---|---|
| 条目 | **`B-33`**（原编号 `H-23`；症状：**补导阶段点「终止」被降级成「执行失败」**） |
| 文件 | `rpa_engine/ops/table_importer.py` ＋ **`rpa_engine/engine/executor.py`** ⚠️ |
| 施工依据 | 附件 `### B-33` @**L2185~L2243** |
| 门禁 | 回归 ≥119 `/` 双冒烟 `/` 自检 `/` `doc_verify` `/` AGENTS 容量 |

**⚠️ 本阶段的核心风险**：这是 13 项中**唯一触及 `engine/` 的阶段**。附件 §三 与 `plan.md` §0.1 均明令「**不动引擎调度逻辑**（`engine/executor.py` 的**步骤分发**、**信号定义**、**线程模型**）」。⇒ **边界必须写死**（见 §3）。

---

## 2. 现状分析（Phase 1）

| 项 | 实测 | 处置 |
|---|---|---|
| 条目区间 | `### B-33` @**L2185** → `### B-34` @**L2244** | Sub-Agent 只读该段 |
| 涉及文件 | `ops/table_importer.py`（**Layer 1**，非 9 项 BUILTIN_OPS）＋ `engine/executor.py` | 2 文件 |
| **越界边界（决定性）** | 上轮已核实：`B-33` 在 `executor.py` 的落点＝**`ensure_input_tables`**（补导辅助函数），**不是** `execute_workflow` 的步骤分发/信号/线程；且该函数 **`A-16` 已放行**（判据改为"表存在**且**行数>0"） | **只允许改 `ensure_input_tables` 及其直接调用面**；**任何**对分发/信号/线程/`execute_workflow` 主体的改动 → 立即 `[SUB_AGENT_BLOCKED]` |
| **文件复用与回滚点** | 两文件均**已被 A 链改过**（`table_importer`：P2／P4／P5／P6；`executor`：P4/A-16）⇒ `阶段0` 快照是 **B1 前**版本，用它回滚会**连带撤销 A 链成果** | **先取阶段前快照** → `backup/B1/阶段5/`（卫生措施，同阶段 4） |
| 台账判据 | `[ACTION]`（"`table_importer`＝Layer 1；`ensure_input_tables` 非分发/信号/线程，A-16 已放行"） | ✓ 与上述边界一致 |

---

## 3. 变更内容（委派 1 个 Sub-Agent，任务书要点）

- **先备份**：复制 `ops/table_importer.py` 与 `engine/executor.py` **当前**内容 → `_temp/ImportData/backup/B1/阶段5/`（**本阶段干净回滚点**；**不得**用 `阶段0` 版本回滚，会连带撤销 A 链）。
- **读取**：附件 `B-33` L2185~2243 的「1. 定位 ~ 8. Agent 执行指引」；**回读真实源码核实行号**（前四阶段已累计 **17 处**附件行号失准；本项附件曾记 `executor` L221-224，上轮核实**实为 L217-225 一带**）⇒ 以实况为准，不符记 `[ADJUSTED]`。
- **🔴 越界边界（硬性 · 违反即失败）**：
  1. **`engine/executor.py` 内只允许改 `ensure_input_tables`**（及其直接相关的调用/返回值），**严禁**触碰 `execute_workflow` 的**步骤分发**、**信号定义/连接**、**线程模型**、重试/清理主体；
  2. 若附件要求改上述任一 ⇒ **立即停手**，输出 `[SUB_AGENT_BLOCKED]`（附：目标位置、为何判为越界、2~3 个替代选项），**不得自行扩权**。
- **其他禁令**：只改上述 2 文件；不改附件/`plan.md`/`docs`/`build`；**不 `git`**；**不动 GUI 布局**；**不改 `ops/` 9 项 BUILTIN_OPS 行为**（`table_importer` 属 Layer 1，其**既有签名/返回值不得变**）；**不引新依赖**；不用 `eval/exec/pickle`。
- **签名不变**：`table_importer.import_excel_table` 等既有签名与返回值保持（附件与 `plan.md` §0.2 均明令）；`ensure_input_tables` 的调用契约保持。
- **语义等价**：附件"改前"为语义示意；找不到逐字文本 → 按**函数名＋行为特征**定位，**严禁全文替换**；失败 → `[SUB_AGENT_BLOCKED]`。
- **注释更正**：与实际不符的注释一并更正。
- **回归重点**：`A-16` 既有判据（表存在**且**行数>0）**必须仍生效**；`test_engine_overwrite`／`test_engine_robustness` 等 engine 相关用例**必须仍全绿**。

---

## 4. 假设与决策

| # | 决策 | 依据 |
|---|---|---|
| **G1** | **1 个 Sub-Agent**，单条 `B-33` | 附件 §五 阶段 5 |
| **G2** | 只改 `ops/table_importer.py` ＋ `engine/executor.py` | 附件「1. 定位」 |
| **G3** | 🔴 **`executor.py` 内只许改 `ensure_input_tables`**；碰分发/信号/线程 → `[SUB_AGENT_BLOCKED]` | 附件 §三 ＋ `plan.md` §0.1 ＋ 上轮核实（`A-16` 已放行该函数） |
| **G4** | **先取阶段前快照**（两文件已被 A 链改过） | 卫生措施（同阶段 4） |
| **G5** | `git` 不执行 | `AGENTS.md` §1 |
| **G6** | Coordinator 复核＝**精确比对（对 `阶段5` 快照）＋ 门禁重跑 ＋ 锚点 ＋ A 链成果保全（`A-16` 判据与 `import_dataframe_atomic` 调用仍在）** | 阶段 4 已验证有效 |
| **G7** | 上下文到批界则阶段边界停手 | 既往纪律 |

---

## 5. 验证步骤

| # | 项 | 判据 |
|---|---|---|
| Z1 | `B-33` 落地 | 其「7. 验收标准」全勾选（**补导阶段终止不再被降级为"执行失败"**） |
| Z2 | 文件面 | 精确比对：本阶段**只** `table_importer.py`／`executor.py` 变化（其余相对 `阶段0` 的已改项**均为阶段 1~4 既有成果**） |
| Z3 | 🔴 **越界核对** | **`executor.py` 的改动只在 `ensure_input_tables` 内**（用 `git diff` 该文件**逐 hunk 目视**，确认无 `execute_workflow`／信号／线程段） |
| Z4 | **A 链成果保全** | `A-16` 判据（`行数 > 0`）仍在；`import_dataframe_atomic` 调用仍在 `table_importer` |
| Z5 | 门禁 | `Ran ≥119 — OK`／双 `SMOKE_ALL_OK`／自检 `ok=True`／`doc_verify PASS`／AGENTS 容量达标 |
| Z6 | 回滚点 | `backup/B1/阶段5/{table_importer.py,executor.py}` 已建且为**本阶段前**内容 |
| Z7 | 留痕 | `plan.md` §0.7.9 追加阶段 5 段；任务记录追加 Step 20 |

---

## 6. 执行顺序

1. **备份** → `backup/B1/阶段5/`。
2. 派 1 个 Sub-Agent 执行 `B-33` ＋ 自验 ＋ 门禁。
3. Coordinator 复核（**含 `executor.py` diff 逐 hunk 越界目视**）。
4. 写 `plan.md` §0.7.9 阶段 5 段 ＋ 任务记录 Step 20。
5. 报告（附件 §九 模板，累计 **10/13**）→ 阶段 6 待续。

---

## 7. 待人工确认项

| # | 事项 |
|---|---|
| Q-1 | `git` 不执行（`AGENTS.md` §1） |
| Q-2 | **若 Sub 报 `[SUB_AGENT_BLOCKED]`（附件要求动 `executor` 分发/信号/线程）** ⇒ 我**不自行扩权**，升级 `[REQUIRES_HUMAN_CONFIRMATION]`＋选项，等你裁定 |
| Q-3 | 真机验证（`P-2`）仍须人工 |
