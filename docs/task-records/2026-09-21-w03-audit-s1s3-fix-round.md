# 任务记录：W-03 数据表/功能步骤审计修复轮（审计→方案→S1-S3 实施→治理收尾）

> 日期：2026-09-21｜执行：模式 B（主控实施 + 只读取证/设计子 agent 分线协作）｜状态：已完成（R4；R3=W-03 三细节 M1-M4）
> 链条文件：审计 `_temp/W-03_table_step_audit_report.md` → 方案 `_temp/W-03_table_step_audit_solution_plan.md`（修订三，施工图级）→ 实施报告 `_temp/W-03_fix_round_S1S3_2026-09-21/REPORT.md`。

## 摘要

以「数据表+功能步骤」双主线完成只读审计（7 判定点：2 达标/4 部分/1 未达标，22 项问题）→ 方案设计（13 修复+4 记录+1 注记+待确认，15 处显式决策）→ 瑕疵修复与施工图具体化（53 原子任务/33 测试条目/40 边界行）→ 人工批准 → S1-S3 实施全落地：P1 编辑态无损化+_cp 折叠迁移、P2 apply_registry（启动恢复回归修复）、P3 撞号双接线、P4 进度口径同源、P5 清空 harvest、P6 dangling 防复活、P7 sheet 查重、P8 标题实时派生、P9a/c/d、R2/R5/R6 守卫。测试基线 57→**79 用例全绿**，真机验收通过（24 条）。

## 用户输入

- 「以数据表和功能步骤为主线专项审计」（只读）→「根据审计报告设计方案落盘」→「修复方案文档瑕疵」→「方案具体化到施工图级」→「再次检查方案」→「批准方案，据此优化 RPA 引擎」→「验收通过，放行 H6，H2 不要，H4 要」。

## Agent 理解与决策（实施级，D22-D24）

| # | 决策 | 说明 |
|---|---|---|
| D22 | _cp 折叠三级父步定位 | 前邻同 id→全表搜→产出==target 兜底；未命中保留+warning（不静默丢）；renumber 仅在 to_dict，载入时序天然安全 |
| D23 | apply_registry 独立公共入口 | 不改 load_session 签名（staged 分支语义保持）；set_tables 单一入口门禁不破 |
| D24 | H2 裁定落实：move_step 保留至下一清理轮删除 | 用户裁定调序 UI 不恢复；按方案 §4.17 既定触发条件处置，本轮不动代码 |

## 执行流程

1. **审计轮**（只读，3 子 agent）：Table/Step Lineage + Translation-Sync 三线取证 → 7 判定点判定 → F 级发现（P1 覆盖语义往返丢失、P2 启动恢复清步骤为最高危，均主控 spot-check 证实）。
2. **方案轮**（只读，3 子 agent + Reviewer）：22 项逐条处置设计、15 处"决策：采用 X 理由 Y"、S1-S3 里程碑；瑕疵修复（9 项）+具体化（8 维度施工图）+复核修订三（53 任务/函数名与计数修正）。
3. **实施轮 S1**：to_dict 双口径分叉（编辑态保 output_mode 不展开 _cp）+_collapse_copy_steps 折叠迁移+模板出口切编辑态+apply_registry；施工修正 3 处（loguru import/孤立夹具/断言 T103）。
4. **实施轮 S2**：9 组 31 任务（撞号 GUI+validator 交叉查重/进度 meta=workflow.steps/清空 harvest/dangling 并入分配排除集/InputEntry.source_path 查重/ordinal_map+title_of 四处收口/模板 output_table 兜底剥离/TableSpec.sqlite_table tooltip/_new_round set_input_tables([])）；graph_edges TableSpec 编辑错位当轮修复。
5. **实施轮 S3**：test_produced_state+6+1 态口径注记+R5 休眠标注+自检三守卫（跨层产表/default_params⊆param_keys/表单覆盖）+GuardRuleTest+smoke 守卫破坏场景。
6. **治理收尾（H6 放行）**：S3-T4 判无需改（architecture.md grep declared/七态/dropped/状态机 **零命中**——对齐对象不存在；6+1 口径唯一载体=models.py reconcile docstring+字段注释，已在位）；本 record+AGENTS 锚点 R4；H2 关闭留痕；H4 落实=M5 立项（`_temp/DAG-rebuild/M5_kickoff_plan.md` 方案态待审核）。

## 涉及文件

代码/测试 15 项（gui 7+validator+step_executor 注释+tests 5+smoke）——全清单见 `_temp/W-03_fix_round_S1S3_2026-09-21/REPORT.md` §2；治理轮新增：本 record、AGENTS.md（锚点/§8）、REPORT §7 追加、M5_kickoff_plan.md。engine/ops 行为零改动（validator 为结构校验扩参、step_executor 仅注释）；SampleCode 冻结基线零触碰；git 留人工。

## 验收

- ✅ `python -m unittest discover -s tests` → **Ran 79 tests OK**（57 基线零回归+22 新增）。
- ✅ smoke_mb 33 项 + smoke_m1m3 全场景（M1-M4+F+S1/S2/S3 共 26 新检查点）SMOKE_ALL_OK。
- ✅ run_self_check 6 项 SELF_OK（项4/4b 含三守卫）。
- ✅ FF1-FF5 全过；复检 grep（step_name=step.name/外部 set_tables/get_form_classes/_next_table_num）0 命中。
- ✅ 真机验收：人工确认通过（既有 18 条+本轮 6 条增补，2026-09-21 裁定）。

## 裁定落实

| 裁定 | 结果 |
|---|---|
| H6 放行 | S3-T4 判无需改（证据见执行流程 6）；S3-T5 本 record+锚点落位 |
| H2 不要 | 调序 UI 不恢复（C1 裁定维持）；move_step 保留至下一清理轮删除（D24） |
| H4 要 | M5 立项：M5-a 物理名 t_{uid}（uid 持久化为前置决策）+ M5-b 插入锚点三态语义；框架=`_temp/DAG-rebuild/M5_kickoff_plan.md`（方案态，人工审核后迁 docs/plan/ 并启动实施） |
| [已过时-待确认] 3 项（正本 §5.9 #9/#11/#15） | 沿袭待归档（焦点模式/tooltip/右键菜单口径见 M1-M4 record） |

## 关闭标识

**本轮（R4）完成**：审计 22 项全处置、13 修复项落地验证、治理收尾落位、三项人工裁定全部落实。

**待人工**：M5 立项方案审核（审核后另行批准实施）；exe 重建（W-20，build-guide §1.10）；下一清理轮（move_step 删除）择期。
