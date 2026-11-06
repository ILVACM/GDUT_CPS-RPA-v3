# 任务记录：翻译契约五项裁定落地（plan.md §4 + M23-M26 + 正本注）

> 日期：2026-09-20｜执行：单 Agent（模式 B：1 个只读探查子 agent + 主 agent 编辑）｜状态：已完成

## 摘要

人工裁定（09-20，针对 09-20 只读分析报告的 G1-G6 缺口与 D-1~D-5 裁决项）：**D-1=B** 弃用前端翻译降级（弃用闭包不写入参数 JSON + 会话清理兜底）；**D-2=a** business_desc=STEP_CATALOG 静态描述（操作类型级）；**D-3** 覆盖映射（overwrite→output_table 同名 DROP+CREATE）+ UI 强制二次确认；**D-4** 演示 export_workflow 不补 v3.1 转换；**D-5** E2E 翻译测试纳入 `rpa_engine/tests/`。落点：`_temp/DAG-rebuild/plan.md` 新增 §4 翻译契约章 + M23-M26 四条目；正本 §8.1/8.3/8.4 加执行注。

## 用户输入

- 「按建议方案执行：D-1 选 B，D-2 选 a，D-3 按拟定映射加二次确认，D-4 不补，D-5 纳入测试，并更新 plan.md」。

## Agent 理解与决策

- 前置分析（09-20 只读报告）：渲染方向（模型→DAG）plan.md M16/正本 §八已覆盖；编辑方向基础互转（to_dict/load_from_dict/parse/validate/保存/加载）生产已在位；**缺口=动态语义翻译**（G1 弃用/G2 覆盖模式/G3 待配置态对齐/G4 business_desc 来源/G5 演示格式差异/G6 E2E）。
- 非裁定实现决策：d1 弃用入口=右面板表详情按钮（正本 §8.5 面板=配置唯一入口）；d2 弃用可逆无确认、覆盖必二次确认；d3 business_desc 粒度降级（a 案固有，接受）；d4 load_from_dict 不还原弃用态（弃用=前端编辑意图，非持久业务逻辑，符合"JSON=业务逻辑唯一载体"）；d5 M23-M26 属 M0 批次本轮不执行。

## 执行流程

1. 只读探查子 agent + 主 agent 定向 grep 核实全部落点锚点（plan.md 结构、models/forms/page 行号、正本 §8.1/8.3/8.4、SampleCode business_desc 数据级来源、page L320-327 二次确认先例）。
2. plan.md 修订（P1-P8）：头部 09-20 注记；§1.9 增 E2E 验收行；§2.3 映射表扩为 26 条（M23-M26）；§2.4 顺序/对账表/归属修订记录（M23/M24→M-a、M25→M-c、M26→M-d）；M4 备注与前置依赖改 STEP_DESC/M23；新增 §4 翻译契约章（4.1 对齐表/4.2 弃用闭包/4.3 覆盖映射/4.4 config_state 投影/4.5 STEP_DESC/4.6 演示格式/4.7 E2E 七用例）；§3 末新增 M23-M26 四块（8 字段+前置依赖）；附录 D 验收补 M-a/M-c/M-d；附录 E D-2 关闭。
3. 正本加注（P9）：§8.1 底层语义行加 B 案执行注；§8.3 弃用行加注；§8.4 扩展字段补 STEP_DESC；frontmatter last-updated→09-20；头部追加 09-20 翻译契约裁定注记行。
4. 治理收尾（P10）：plan/INDEX 条目+日期同步；本记录新建；AGENTS 锚点+日期。

## 涉及文件

| 文件 | 改动 |
|---|---|
| _temp/DAG-rebuild/plan.md | 头注/§1.9/§2.3/§2.4/M4/§4 新章/M23-M26/附录 D/E |
| docs/plan/DAG_refactor_plan.md | §8.1/8.3/8.4 注 + frontmatter + 头部注记 |
| docs/plan/INDEX.md | 条目摘要/状态/日期 |
| docs/task-records/2026-09-20-translation-contract-ruling.md | 新建（本文件） |
| AGENTS.md | 锚点覆写 + 日期 |

SampleCode 零改动（冻结基线；README L56 历史表述由正本 §8.1 注覆盖）。

## 验收

- ✅ grep 对账：plan.md `^### M\d+` 27 块（唯一编号 M1-M26，M20 双落点）；`- 前置依赖：` 27 处；`^## 4\.` 位于 §3 与附录 A 之间；附录 E「D-2 漂移项…M0 移植前裁定」0 残留、已改为五项裁定关闭。
- ✅ 正本 grep：§8.1 执行注/§8.3 注/§8.4 STEP_DESC 命中；last-updated=09-20；头部 09-20 注记在位。
- ✅ doc-governance §4 全局更新校验（2026-09-20）：Step1 AGENTS 自洽（锚点/日期/容量三口径复测含 CR≤8000、余量≥200、CRLF 复归一）；Step2 索引+五项校验（链接完整、元信息同步、层级一致、INDEX 同步、无约束力误标）；Step3 README 同步（根 README 无涉零改动；SampleCode 冻结不动）。
- ✅ 交叉核对：§2.3 26 条与 §3 块编号一一对应；§2.4 三阶段集合含新 Mn；M23-M26 锚点（models to_dict L266/forms FilterForm L209/page L320-327/L567-583）与盘上一致。

## 关闭标识

本轮完成。待办收敛：**M0 启动指令**（M-a~M-e 依 plan.md §2.4/§4 可直接开工；M-a 需先登记 tests 豁免）、W-20（exe 人工重建）、单表粒度内存释放（v3.2 待办，§4.2④）。