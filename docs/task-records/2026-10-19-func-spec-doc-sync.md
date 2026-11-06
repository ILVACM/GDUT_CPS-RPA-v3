# 任务记录：功能函数增改指引无歧义性审计与文档同步

## 摘要
- **任务目标**：审计功能函数（三位一体）的文档规定与代码实现是否给 Agent 提供无歧义增改指引；修补发现的文档漂移
- **任务状态**：`已完成（2026-10-19）`
- **开始时间**：2026-10-19
- **最后更新**：2026-10-19
- **要点摘要**：审计结论＝框架一流/实质准确/3 处漂移（第四处「9」断言、基线 118→191、行号锚点×8）；修补＝纯文档同步批（function-spec-rules.md），F4（B9 新增功能指引歧义）留痕提请人工裁定
- **操作人**：黄泊凯

## 用户输入

> 现在就剩功能函数需要进行优化了，现在你首先自适应综合扫描理解分析，当前程序实现以及文档规定，是否提供了清楚准确的指引，使得 agent 能没有歧义的添加修改功能函数。用通俗易懂的语言说明分析结果。

（计划经人工批准后施工：`\.trae\documents\func-spec-guidance-audit-and-doc-sync.md`）

## Agent 理解与决策

- 审计对象＝`docs/function-spec-rules.md`（[约束] 规约）↔ 代码实况（`ops/step_executor.py`、`gui/models.py`、`gui/forms.py`、`gui/app.py`、`engine/{registry,validator}.py`、tests、smoke、spec）
- 方法＝one-tool-call 测试（Agent 视角逐锚点核验）＋文档↔代码逐项比对
- 修补范围严格限定为文档同步（最小改动）；B9 双源歧义属 backlog W-22 人工裁定范畴，不自行写入规约

## 执行流程

### 流程概览
- 总步骤数：4
- 多 Agent 协作：否

### 步骤记录

#### Step 1: 审计（one-tool-call 测试＋逐锚点核验）
- 状态：✅ 已完成
- 执行内容：10 项代表行为测试（8 定位全过、2 口径 FAIL）；§3.2 表 9 行实质内容逐项核对与代码一致；发现 F1（第四处「9」断言 `tests/test_ops_contracts.py` L334 未登记，R12 阶段 7 新增）、F2（§8 基线 118 → 实际 191）、F3（约 8 处行号锚点漂移：`_FORM_CLASSES` L548-576→L584-612、`OUTPUT_OPS` L176-177→L185-186、`STEP_KIND` L184-194→L193-203、`PRODUCE_LABEL` L216-226→L225-235、`default_params` L917-937→L978-998、`extra_input_ids` L897-914→L926、`to_dict` t_{uid} L708→L719-737、`app.py` 自检 L47-243→L48-247／L108→L109、`execute_step` 分发 L209-294→L212-294、`main_buttons`/`more_buttons` L135/L148→L136/L152）、F4（B9 双源无新增功能行为指引）
- 涉及文件：只读（上述代码文件＋function-spec-rules.md）
- 决策记录：`step_executor.py` L52-109／L196-201、`validator.py` L89-93、`models.py` L32-93、`registry.py`、smoke L185-219、`test_graph_edges.py` L200、`test_translation.py` L149 均无漂移，不改动相关表述

#### Step 2: function-spec-rules.md 文档同步施工
- 状态：✅ 已完成
- 执行内容：①§5.5 项 13「三处」→「四处」等值断言（补 `tests/test_ops_contracts.py` L334）；②§7 E3/A4 同步「四处」＋`app.py` L108→L109；③§8 项 1 基线 118→191（R13 终态）；④§3.2 表头核对日期→2026-10-19、注记 1 `models.py` L708→L737；⑤§3.4 行号刷新五行（`OUTPUT_OPS` L185-186／`STEP_KIND` L193-203／`PRODUCE_LABEL` L225-235／`default_params` L977-998／`extra_input_ids` L925-942／`_FORM_CLASSES` L584-612／自检 L48-247）；⑥§5.5 项 3 分发区 L209-294→L212-294；⑦frontmatter 日期＋confidence 追加审计说明；⑧§9 追加 R14 变更行
- 涉及文件：`docs/function-spec-rules.md`（修改）
- 决策记录：**计划外发现 F5**——§3.2 注记 4 与 §7 B5 声称「弃用一启用即自检失败」，但代码实况为 B-13（R12 阶段 1）已将按钮并集校验改用 `active_catalog_keys()`（`app.py` L186-192）且有 `test_deprecated_self_check_passes` 回归保护（docstring 明言「功能级弃用通路可用，不再一启用即自检失败」）。处置＝按 §3.5「以代码为准」在注记 4 追加〔2026-10-19 审计注记〕（保留原文，符合 §7.1「已有内容保留」）；**B5 处置状态不改**（§7 禁令「处置状态由人工更新」），提请人工确认

#### Step 3: 门禁
- 状态：✅ 已完成
- 执行内容：AGENTS.md 行尾归一 CRLF → `doc_verify` 首跑拦截 INDEX 日期不同步（function-spec-rules 2026-09-24 ≠ frontmatter 2026-10-19）→ 同步 `docs/INDEX.md` 该行（日期＋摘要追加 R14 说明）→ 复跑 `doc_verify PASS (links=86, failures=0)`；`unittest discover`：`Ran 191 tests — OK`（零代码改动，基线不受影响）
- 涉及文件：`docs/INDEX.md`（修改，门禁强制同步项）

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 修改 | `docs/function-spec-rules.md` | R14 审计同步：四处「9」断言／基线 191／行号锚点刷新／注记 4 审计注记／§9 变更行 |
| 修改 | `docs/INDEX.md` | function-spec-rules 行日期同步＋摘要追加 R14 说明（doc_verify 门禁强制） |
| 修改 | `AGENTS.md` | 锚点登记（新任务）＋行尾归一 CRLF |
| 新建 | `docs/task-records/2026-10-19-func-spec-doc-sync.md` | 本文件 |

## 遗留提请人工裁定（不在本批处置）

1. **F4（B9 双源缺新增功能行为指引）**：新增功能函数时 GUI `default_params()` 与引擎 `.get()` 回退应保持一致还是允许分叉，规约未给行为指引——建议随 W-22 裁定
2. **F5（§7 B5 疑似已解决）**：B-13 已修复按钮并集校验弃用口径＋回归保护在位，B5 行「待补强（最高优先）」的处置状态建议人工确认后更新（含 backlog W-22 关联项）

## 关闭标识
- **完成时间**：2026-10-19
- **最终状态**：✅ 全部完成（审计＋文档同步＋门禁 PASS；F4/F5 留痕移交人工）
- **关闭说明**：功能函数增改指引的无歧义性已恢复至「文档↔代码一致」状态；后续 Agent 按 §5.5 四处断言清单施工不会踩暗坑
