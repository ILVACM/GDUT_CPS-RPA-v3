# `_temp` 清理清单（CLEANUP MANIFEST）

> **状态**：清理态 [待人工审核]｜生成：2026-09-24 R10｜执行：AI Agent（人工四项裁定见下）
> **用途**：本夹为删除动作**唯一回退线索**。`_temp` 未被 `.gitignore` 收录且待删文件多为**未跟踪**状态 → **删除不可经 git 恢复**（已用 `git check-ignore` 实测确认，退出码 1）。
> **人工裁定**：①新夹名 `ledger_2026-09-24` ②力度＝标准档 ③verify 13 份全删并加注 ④删除前先落本清单。

---

## §1 处置总表（`_temp` 顶层 30 件）

### 1.1 归档 10 件（移入本夹，文件名与子夹名不变）

| 原路径（`_temp\` 下） | 体积 | 行数 | 归档理由 |
|----------------------|------|------|----------|
| `open_issues_ledger_2026-09-24.md` | 50,881 B | 407 | **台账本体**：103 条登记→6 根因/26 组，排期唯一入口 |
| `HANDOVER_2026-09-24.md` | 38,512 B | 511 | 台账 B 系列（B-01~B-16）明细出处；含实测基线与命令清单 |
| `data_import_issue_scan.md` | 28,689 B | 250 | 台账 DM 系列（42 条）＋G 系列（8 处缺口）明细出处 |
| `RPA_engine_maturity_assessment.md` | 31,527 B | 240 | 台账 P 系列证据（L119-137）；`docs/function-spec-rules.md` L227/L255/L283 活跃引用 |
| `RPA_engine_remediation_plan.md` | 108,036 B | 867 | R6 冻结施工图（37 项/35 任务/89 步），偏差留痕依据 |
| `W-03_Remediation_round_2026-09-24/REPORT.md` | 23,666 B | 119 | R6 全轮报告（§8 门禁矩阵、§9 人工清单）；AGENTS 原 §8 指向件 |
| `function_spec_rules_round_2026-09-24/REPORT.md` | 18,518 B | 175 | R7 规约整理报告；`docs/function-spec-rules.md` L10 活跃引用 |
| `W-03_M5_round_2026-09-24/REPORT.md` | 8,227 B | 71 | R5 报告；台账 B-10（M5 真机 5 条，L64-L71）证据件 |
| `W-03_fix_round_S1S3_2026-09-21/REPORT.md` | 9,175 B | 83 | R4 审计修复轮报告（里程碑证据） |
| `W-03_fix_round_2026-09-21/REPORT.md` | 11,410 B | 94 | R3 三细节修复轮报告（里程碑证据） |

> **行数口径**：§1.1／§1.2 行数为**处置前实测值**；归档件后统一加"⚠ 归档注记"头部（＋2 行），故现值 ＋2（例：成熟度 240→242、修复施工图 867→869、扫描 250→252、HANDOVER 511→513、台账 407→408 含位置说明行）。

### 1.2 删除·过时 6 件（档案见 §2）

| 路径 | 体积 | 行数 | 删除理由 |
|------|------|------|----------|
| `W-03_GUI_detail_optimization_plan.md` | 39,516 B | 288 | R3 冻结施工图，已实施验收完毕；结论已入 task-record 与 `function-spec-rules.md` |
| `M5_design_plan.md` | 107,647 B | 798 | R5 冻结施工图，已实施验收完毕；t_{uid} 结论已入 `docs/architecture.md` |
| `W-03_table_step_audit_report.md` | 16,360 B | 84 | R4 审计产出（22 项），已被解决方案与修复轮吸收 |
| `W-03_table_step_audit_solution_plan.md` | 101,108 B | 715 | R4 施工图（53 原子任务），已实施完毕 |
| `W-03_runtime_flow_and_tech_brief.md` | 15,218 B | 72 | R3 前只读审查产出（F1-F10），已全部闭环；docs/ 与 AGENTS 零引用 |
| `repo-context-report.md` | 7,859 B | 66 | 已被 `docs/backlog.md` 取代为唯一活载体（INDEX L29 自述） |

### 1.3 删除·工具留痕 14 件（档案见 §3）

`verify-20260924-{1001,1006,1012,1018,1020,1042,1158,1202,1231,1237,1239,1240,1312}.md` 共 13 份（合计 **4,945 B**、197 行），**另加 R10 本轮执行中自行产生的 1 份** `verify-20260928-1347.md`（FAIL 中间态，见 §3 末行）。理由：AGENTS §6 定义 `_temp`＝"校验中间产物"；可重跑 `tools/doc_verify.py` 再生。

### 1.4 未触碰

`_temp\DAG-rebuild\`（含 `SampleCode\` 冻结基线、`plan.md`、`M5_kickoff_plan.md`、`artifacts\`）——人工明令整体不动。

---

## §2 被删 6 件档案（章节标题树＋要点＋结论沉淀位置）

### 2.1 `W-03_GUI_detail_optimization_plan.md`（288 行／39,516 B）

- **状态头**：`# W-03 GUI 三细节问题优化方案（定稿）` ＋ `> 状态：定稿 [冻结] / Frozen，待实施｜日期：2026-09-21`（状态头滞后，实际已实施）
- **标题树**：§1 任务理解与验收标准｜§2 本地规约读取·技术栈确认·冲突记录｜§3 决策冻结汇总表｜§4 当前实现只读分析摘要｜§5 问题一：表头行选择重构（5.1 根因／5.2 方案 A QTableView＋Model＋Delegate／5.3 测试与人工验收）｜§6 问题二：Ribbon/添加功能步骤（6.1 问题／**6.2 StepMeta 注册表与 key 铁律**／6.3 弹层方案 B／6.4 交互流程与联动／6.5 扩展方式与验收）｜§7 问题三：实时记录更新（7.1 根因／7.2 uid 与显示编号分离／7.3 表生命周期七态／7.4 删除级联 B 悬空化／7.5 前后端同步协议／7.6 验收清单）｜§8 前后端映射与同步设计｜§9 实施任务拆解 M1-M4（26 任务）｜§10 实施期禁令（6 条）｜§11 验收门禁｜§12 实施顺序与里程碑｜§13 风险登记 R-1~R-6｜**§14 已否决方案存档 N1-N10**｜§15 声明
- **关键数字**：12 项决策（D-A／D-B／D-B2／D-B3／D-C1~C4／Q1~Q4）；§6.5 新增功能＝"6 处登记"（已被取代）；§9 26 任务（M1×6、M2×10、M3×6、M4×4）；§7.3 七态状态机；§14 十条否决；真机清单 ≥15 条
- **结论沉淀位置**：`docs/task-records/2026-09-21-w03-three-details-m1-m4.md`（L4 依据、L91「26 任务全落地」）；`docs/function-spec-rules.md`（L227 取代其 6 处口径、L30 四分类、key 铁律源自 §6.2）；`_temp/ledger_2026-09-24/function_spec_rules_round_2026-09-24/REPORT.md` L68；台账 L314
- **曾被我引用**：`docs/function-spec-rules.md` L227；task-records 3 处；HANDOVER L112/135/263；台账 L314；`W-03_fix_round_2026-09-21/REPORT.md`

### 2.2 `M5_design_plan.md`（798 行／107,647 B）

- **状态头**：`# M5 设计方案（M5-a 物理名 t_{uid} ＋ M5-b 插入锚点，按序实施）` ＋ `> 状态：定稿 [冻结] / Frozen，待实施｜2026-09-21 人工批准`（滞后，已实施）
- **标题树**：§1 任务理解与验收标准｜§2 取证摘要（E1-E11；2.1 具体化取证更新）｜§3 M5-a 设计：物理名 t_{uid}（3.1 K1-K4 裁定／3.2 函数级施工图 含 3.2.1 to_dict·load_from_dict／3.3 测试清单 含 3.3.1／3.4 边界与异常 含 3.4.1 边界矩阵 12 行）｜§4 M5-b 设计：三态锚点插入（4.1 K5-K8／4.2 施工图 含 4.2.1 insert_step·add_step·_resolve_insert_index·_on_add_step／4.3 测试清单 含 4.3.1／4.4 边界 含 4.4.1 边界矩阵 10 行）｜§5 里程碑与门禁（5.1 任务→文件→原子步骤汇总）｜§6 原子任务表 11 项（6.1 共 35 步逐条）｜§7 裁定记录与风险（C1-C3 已裁定，无待确认）｜§8 声明｜§9 本轮修复说明 9 项（9.1 二次复核 4 项／9.2 提示项修正 3 项／9.3 已知瑕疵自适应 3 项／9.4 具体化后复核 5 项）｜§10 具体化说明（八维度，新增 12 子节）｜§11 具体化后自检
- **关键数字**：基线 79 用例（17+9+29+15+3+3+3）；K1-K8 八项裁定；C1-C3 人工裁定；11 项原子任务／35 步（T1×4…T11×5）；新增 9 单测方法＋2 smoke 场景节；验收标准 12 条
- **结论沉淀位置**：`docs/task-records/2026-09-24-w03-m5-tuid-insert-anchor.md`（L66「35 原子步骤全部落地」）；`docs/architecture.md` L182/226/229（t_{uid} 三处＝C1 放行项）；`_temp/ledger_2026-09-24/W-03_M5_round_2026-09-24/REPORT.md`
- **曾被我引用**：task-records L4；HANDOVER L113/262；台账 L314；M5 REPORT L3/L71
- **保留线索**：`_temp/DAG-rebuild/M5_kickoff_plan.md`（立项框架，DAG-rebuild 内未动）

### 2.3 `W-03_table_step_audit_report.md`（84 行／16,360 B）

- **状态头**：`# 数据表与功能步骤专项审计报告（只读，2026-09-21）` ＋ `> 状态：审计产出，零代码修改`
- **标题树**：第一层 通俗说明（人话版）｜第二层 逐点判定（7 判定点）｜第三层 问题与解决思路（高危／中低危／记录项／待人工确认）｜声明
- **关键数字**：7 判定点；达标 2（3、6）／部分达标 4（1、2、5、7）／未达标 1（4）；高危 P1/P2；中低危 P3-P8 六行＋P9；记录项 5 条；待人工确认 4 项；基线 57 用例＋33 冒烟＋自检 6 项
- **结论沉淀位置**：`docs/task-records/2026-09-21-w03-audit-s1s3-fix-round.md`；`_temp/ledger_2026-09-24/W-03_fix_round_S1S3_2026-09-21/REPORT.md`；台账分组 B 多项（B1/B2/B3/B4/D3/D4 源自本审计的记录项）
- **曾被我引用**：task-records L4；HANDOVER L117

### 2.4 `W-03_table_step_audit_solution_plan.md`（715 行／101,108 B）

- **状态头**：`# W-03 审计问题解决方案（数据表/功能步骤/翻译同步三主线）` ＋ `> 状态：方案态 [待审核]｜2026-09-21 修订二`（滞后，已实施）
- **标题树**：§1 任务理解与验收标准｜§2 规约读取·冲突记录｜§3 问题清单总表（22 项）｜§4 逐问题解决方案（4.1 P1 编辑态无损化＋_cp 折叠／4.2 P2 apply_registry／4.3 P3 撞号双接线／4.4 P4 进度页口径／4.5 P5 清空前 harvest／4.6 P6 dangling 防复活／4.7 P7 同 sheet 查重／4.8 P8 标题实时派生／4.9-4.12 P9a-d／4.13 R2 produced 断言／4.14 R5 target_param 休眠注记／4.15 R6 注册表守卫补三条／4.16 R1 uid 休眠／4.17 R3 move_step 零调用）｜§5 数据表主线汇总｜§6 功能步骤主线汇总｜§7 翻译同步主线汇总｜§8 实施顺序与里程碑（8.1 原子任务总表 53 项）｜§9 风险与待人工确认｜§10 声明｜§11 瑕疵修复说明 9 项｜§12 具体化说明｜§13 具体化后自检
- **关键数字**：22 项（P1-P8、P9a-d、R1-R6、H1-H4）；处置分解「修复 13＋判记录不改 4＋休眠注记 1＋沿袭 4」；**53 原子任务＝S1×15／S2×31／S3×7**；边界表 40 行；33 个用例条目
- **结论沉淀位置**：`docs/task-records/2026-09-21-w03-audit-s1s3-fix-round.md`；S1-S3 REPORT（已归档）；台账分组 B（B7/D2/D3 等多条源自本方案的记录项）
- **曾被我引用**：task-records L4；HANDOVER L116；台账 L314；S1S3 REPORT L3

### 2.5 `W-03_runtime_flow_and_tech_brief.md`（72 行／15,218 B）

- **状态头**：`# W-03 运行流程通俗说明 ＋ 技术底层 ＋ 校验审查发现（只读审查轮，2026-09-21）` ＋ `> 状态：只读审查产出，未修改任何代码/配置/数据`
- **标题树**：第一部分 通俗运行流程（阶段 1 启动／2 输入数据选择／3 流程步骤配置／4 执行／5 保存·加载·模板·回退）｜第二部分 关键点技术底层实现（11 个关键点）｜第三部分 校验审查发现 F1-F10
- **关键数字**：F1-F10（高 1＝F1；中 4＝F2/F3/F4/F8；低 3＝F5/F6/F7；已确认 2＝F9/F10）；几何常量 col_cx=120+240j、row_cy=193+100r、HEADER_BOTTOM=118、卡片 140×70、表 160×40；契约 7 键；七态；tests 52 用例
- **结论沉淀位置**：`_temp/ledger_2026-09-24/W-03_fix_round_2026-09-21/REPORT.md`（L4/L18 依据本文件 F1-F10，F 项全闭环）；`docs/architecture.md` §8（流程与布局规格）
- **曾被我引用**：F 轮 REPORT；HANDOVER L117。**`docs/`、`AGENTS.md`、`README.md`、台账、导入扫描中对本文零引用（grep 实测）** → 删除风险最低的一件

### 2.6 `repo-context-report.md`（66 行／7,859 B）

- **状态头**：`# 仓库上下文分析报告` ＋ `> 生成时间：2026-09-13｜扫描模式：单agent分层` ＋ §5 `本报告经人工确认后作为后续所有工作会话的唯一上下文基线。确认人：黄泊凯 确认时间：2026-09-13`
- **标题树**：§1 项目说明分析（1.1 说明来源／1.2 项目核心信息／1.3 一致性校验结果）｜§2 规约现状｜§3 当前情况（任务锚点机制）｜§4 待确认/存疑项（6 条，各附 2026-09-14 R1~R5 处置）｜§5 上下文基线声明
- **关键数字**：说明文件 3 份；§1.3 交叉验证 5 条；§2 规范文件清单 14 条；task-records 34 篇＋TEMPLATE；§4 六条存疑项；P0 6 项／P1 3 项
- **⚠ 重要事实**：现行文件**只有 §1~§5，不存在 §4.6 与 §0.5**；而 `docs/backlog.md` L10/L17（称 §4.6）、L45（称 §0.5）与 `docs/INDEX.md` L29（称 §4.6）**在本轮之前即已指向不存在的小节**（该文件曾被重写为 66 行摘要版，历史 365 行版含 §4.6）。故删除不新增追溯损失，加注即可。
- **结论沉淀位置**：`docs/backlog.md`（唯一活载体，取代其队列职能）；`docs/` 各知识文档；`_temp/ledger_2026-09-24/HANDOVER_2026-09-24.md` §4（当前基线实况）
- **曾被我引用**：`docs/backlog.md` L10/L17/L45/L54；`docs/INDEX.md` L29；task-records 2 处；README L42-43；**`_temp/DAG-rebuild/plan.md` L580（该处按人工边界不改写，见 §5 末）**

---

## §3 被删 14 份 verify 档案（`tools/doc_verify.py` 生成）

| 报告 | 时刻 | 结论 | AGENTS 含 CR／余量 | 行尾 | 备注 |
|------|------|------|--------------------|------|------|
| `verify-20260924-1001.md` | 10:01 | **FAIL（8 项）** | 7,558／余量 442 | loneLF=**196** | 唯一 FAIL：E1 后编辑工具引入 loneLF 漂移；同报告登记 8 项文档问题（architecture §8.2/§8.3、INDEX 6 处日期等），已全部修复 |
| `verify-20260924-1006.md` | 10:06 | 全绿 PASS | 7,754／246 | 纯 CRLF | 修复后复测 |
| `verify-20260924-1012.md` | 10:12 | 全绿 PASS | 7,754／246 | 纯 CRLF | 同上 |
| `verify-20260924-1018.md` | 10:18 | 全绿 PASS（**警告**余量 119＜200） | 7,881／119 | 纯 CRLF | R6 收尾编辑曾超限，随即下沉恢复 |
| `verify-20260924-1020.md` | 10:20 | 全绿 PASS | 7,774／226 | 纯 CRLF | **R6 终版**（`task-records/2026-09-24-w03-remediation-batches.md` L35 引用件，links=77） |
| `verify-20260924-1042.md` | 10:42 | 全绿 PASS | 7,774／226 | 纯 CRLF | R6 后复测；exe 构建（10:41）夹在此后 |
| `verify-20260924-1158.md` | 11:58 | 全绿 PASS（**警告**余量 143） | 7,857／143 | 纯 CRLF | R7 首轮新增后 |
| `verify-20260924-1202.md` | 12:02 | 全绿 PASS（**警告**余量 190） | 7,810／190 | 纯 CRLF | R7 首轮下沉后 |
| `verify-20260924-1231.md` | 12:31 | 全绿 PASS | 7,800／200 | 纯 CRLF | R7 二轮下沉达标 |
| `verify-20260924-1237.md` | 12:37 | 全绿 PASS（**警告**余量 199） | 7,801／199 | 纯 CRLF | 锚点收尾瞬间态 |
| `verify-20260924-1239.md` | 12:39 | 全绿 PASS | 7,798／202 | 纯 CRLF | **R7 终版**（`task-records/2026-09-24-function-spec-rules.md` L144 引用件，links=86） |
| `verify-20260924-1240.md` | 12:40 | 全绿 PASS | 7,798／202 | 纯 CRLF | R7 后复测（HANDOVER §4.10 引用件） |
| `verify-20260924-1312.md` | 13:12 | 全绿 PASS | 7,798／202 | 纯 CRLF | 交接轮实测（HANDOVER §4.10 引用件，links=86） |
| `verify-20260928-1347.md` | 09-28 13:47 | **FAIL（1 项）** | 7,798／202 | 纯 CRLF | **R10 本轮产生**：AGENTS 锚点先行写入指向当时尚未创建的 task-record 链接所致（违反"先有后写"，随即补建文件消除）；links=85 |

**再生方式**：`cd` 至仓库根执行 `conda run -n CPS-GPES_RPA-py311 python tools/doc_verify.py`，将生成新的 `_temp/verify-<时间戳>.md`（**注意：新报告落在 `_temp` 顶层，不再归入本夹**）。

---

## §4 不可逆声明

| 项 | 事实 |
|----|------|
| git 状态 | `_temp` **未被任何 `.gitignore` 收录**（仓库根无 `.gitignore`；上级目录 `.gitignore` 不含 `_temp`）；`git check-ignore -v` 对台账与 verify 文件返回退出码 1 |
| 跟踪状态 | 13 份 verify、台账、HANDOVER、导入扫描、5 份 REPORT 子夹多为 `??` 未跟踪；`RPA_engine_remediation_plan.md` 等若为已修改状态则仅其旧版在库 |
| 后果 | 删除后**无法用 `git checkout`/`restore` 找回** |
| 唯一回退线索 | 本清单 §1～§3（章节标题树＋关键数字＋结论沉淀位置＋各 verify 三口径数字） |
| 可再生项 | 13 份 verify 可重跑 `doc_verify.py` 生成（内容等价于最新一次体检，历史中间态不可复现） |

---

## §5 引用改道对账表（本轮逐条执行并复核）

### 5.1 约束层与知识层（必改）

| # | 位置 | 原引用 | 新引用／加注 |
|---|------|--------|--------------|
| A1 | `AGENTS.md` §8 | ``_temp/W-03_Remediation_round_2026-09-24/REPORT.md`` | 改指向 ``_temp/ledger_2026-09-24/open_issues_ledger_2026-09-24.md``（已于阶段 0 执行，兼作容量规避） |
| A2 | `docs/function-spec-rules.md` L10 | ``_temp/function_spec_rules_round_2026-09-24/REPORT.md`` §5 | 路径插入 `ledger_2026-09-24/` |
| A3 | 同 L227 | ``_temp/W-03_GUI_detail_optimization_plan.md`` §6.5（**删除件**） | 保留原句＋注"（已随 _temp 清理，2026-09-24，见 ledger 夹 CLEANUP_MANIFEST §2.1）" |
| A4 | 同 L227 | ``_temp/RPA_engine_maturity_assessment.md`` P2-2 | 路径插入 `ledger_2026-09-24/` |
| A5 | 同 L255 | 同上 | 同 A4 |
| A6 | 同 L283 | 同上 | 同 A4 |
| A7 | `docs/backlog.md` L10 | ``_temp/repo-context-report.md`` §4.6（**删除件**） | 保留原句＋加"已清理"注（该 §4.6 本轮前即不存在，一并说明） |
| A8 | 同 L17、L45 | 同上 §4.6／§0.5 | 各加"已清理"注 |
| A9 | `docs/INDEX.md` L29 | 同上 §4.6 | 加"已清理"注 |
| B4 | `README.md` L42-43 | `repo-context-report.md`（删除件） | 加"已清理"注 |

### 5.2 归档件内部（加注／改同夹相对名）

| # | 位置 | 处置 |
|---|------|------|
| 台账头部 | 新增「位置说明」行：本台账及配套明细统一归档于 `_temp/ledger_2026-09-24/`，清理与对账见同夹 `CLEANUP_MANIFEST.md` | 加注 |
| 台账 L10 明细出处 | `_temp/data_import_issue_scan.md`、`_temp/HANDOVER_2026-09-24.md` | 改同夹相对名 |
| 台账 L304（B-10） | `_temp/W-03_M5_round_2026-09-24/REPORT.md` | 改同夹相对名 |
| 台账 L312 编号说明 | `_temp/HANDOVER_2026-09-24.md` | 改同夹相对名 |
| 台账 L314（4 份冻结方案状态头） | 3 份删除件＋1 份归档件 | 删除件加"已清理，骨架见清单 §2"注；归档件改相对名 |
| 台账 L356-357、L362 | R6/R7 REPORT、导入扫描 | 改同夹相对名 |
| HANDOVER §4.10、§5 | `verify-20260924-1240.md`、`-1312.md` | 加"已清理，数字保留于本文；可重跑再生"注 |
| `W-03_fix_round_2026-09-21/REPORT.md` | 引用 `W-03_runtime_flow_and_tech_brief.md`（删除件） | 加"已清理，见清单 §2.5"注 |
| `W-03_M5_round_2026-09-24/REPORT.md` | 引用 `M5_design_plan.md`（删除件） | 加注，指向清单 §2.2 |
| `W-03_fix_round_S1S3_2026-09-21/REPORT.md` | 引用 `audit_solution_plan.md`（删除件） | 加注，指向清单 §2.4 |
| `function_spec_rules_round_2026-09-24/REPORT.md` | 引用 3 份删除件（GUI 方案／DAG-rebuild plan／remediation plan） | 仅对 2 份删除件加注；DAG-rebuild 路径未动不改 |

### 5.3 task-records 历史记录（**不改写正文**，按 D2 先例）

统一声明落点：`docs/task-records/2026-09-24-temp-ledger-cleanup.md` 末「附：历史 `_temp` 路径统一声明」。涉及 `2026-09-21-w03-three-details-m1-m4.md`、`2026-09-21-w03-audit-s1s3-fix-round.md`、`2026-09-24-w03-m5-tuid-insert-anchor.md`、`2026-09-24-w03-remediation-batches.md`、`2026-09-24-function-spec-rules.md`、`2026-08-24-docs-v4-consistency.md`、`2026-09-14-rulings-adaptation.md`。

### 5.4 已知失效引用·本轮不处置

| 位置 | 引用 | 处置与理由 |
|------|------|-----------|
| `_temp/DAG-rebuild/plan.md` L580 | `repo-context-report.md`（本轮删除） | **不改写**——人工明令 `_temp/DAG-rebuild/` 整体不动；该处属 `_temp` 无约束力区的历史行内引用，失效不影响任何规约校验（`doc_verify` 扫描范围不含 `_temp`）。**待人工复核** |

---

## §6 清理后 `_temp` 目标形态

```
_temp\
├── DAG-rebuild\              (未触碰：SampleCode 冻结基线＋plan.md＋M5_kickoff_plan.md＋artifacts)
└── ledger_2026-09-24\        (本轮新建，11 个文件)
    ├── CLEANUP_MANIFEST.md            ← 本文件
    ├── open_issues_ledger_2026-09-24.md
    ├── HANDOVER_2026-09-24.md
    ├── data_import_issue_scan.md
    ├── RPA_engine_maturity_assessment.md
    ├── RPA_engine_remediation_plan.md
    ├── W-03_Remediation_round_2026-09-24\REPORT.md
    ├── function_spec_rules_round_2026-09-24\REPORT.md
    ├── W-03_M5_round_2026-09-24\REPORT.md
    ├── W-03_fix_round_S1S3_2026-09-21\REPORT.md
    └── W-03_fix_round_2026-09-21\REPORT.md
```

顶层零散文件：**0**（verify 由后续执行动作自然落在 `_temp` 根，属工具行为，不再归档）。
