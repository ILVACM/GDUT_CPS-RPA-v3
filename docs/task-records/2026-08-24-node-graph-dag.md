# 任务记录：节点图重构为 DAG 风格（起点终点 + 分叉合并 + 箭头）

## 摘要
- **任务目标**：将用户配置页「步骤流程」节点图重构为类 Git 树状图的有向无环图渲染
- **任务状态**：已完成
- **开始时间**：2026-08-24 14:00 (UTC+8)
- **最后更新**：2026-08-24 14:30 (UTC+8)
- **要点摘要**：3 文件重构 + 2 测试脚本适配；dag-layout-test 4 PASS + 全量回归 58 PASS
- **操作人**：黄泊凯

## 用户输入
> 节点图重构为 DAG 风格。总体效果参考 git GUI 树状图：有向无环图（方向用箭头指示），重点关注起点终点（起点=输入表、终点=export）与分叉合并（分叉=复制/筛选/去重等产生新表、合并=合并/匹配等减少表）。之前渲染有"不该着色的线被着色、该着色的节点被隐藏"等 BUG。

## Agent 理解与决策

### 现状诊断
- 数据模型已具备所需信息：`StepConfig.target_table_id/output_table_id`、`OUTPUT_OPS`（6 类产新表）、`params.match_table_id(s)`。
- 旧渲染缺陷：无箭头、无起点/终点标识、分叉/合并无显式标记、步骤节点固定最左、着色仅灰/绿两色、派生列无引用仍画绿色短桩。

### 决策
- 操作性质四分类：`end`(export) / `merge`(mapping_match, merge_tables) / `fork`(filter, dedup, aggregate, copy_table) / `sequential`(rename_columns, convert_dtype)。
- 布局：列=表（输入左/派生右）、行=步骤（从上到下）；步骤节点按输入/输出列中心区间动态定位。
- 分叉：源列线穿过步骤行继续 + 新表列线分出（绿色菱形标记）；合并：多输入列线汇聚终止 + 新表列线（橙色标记）。
- 列线：输入灰、派生蓝；无引用不画（消短桩）；合并输入列线终止于合并行。
- 边界：合并后输入表列线终止（数据汇入新表语义）；跨合并复用渲染本轮不做。
- 规格经 Spec 模式审批（.trae/specs/refactor-node-graph-dag/）。

## 执行流程

### 流程概览
- 总步骤数：3（实现/验证/收尾）
- 多 Agent 协作：否

### 步骤记录

#### Step 1: 三文件重构
- 状态：✅ 已完成
- 执行内容：
  - [models.py] 新增 STEP_KIND 映射 + classify_step()（覆盖 9 类操作）
  - [node_graph.py] StepLayoutEntry 增 input_tables/kind/is_end；新增 _arrow_polygon/_DotMarker/_ForkMarker/_col_cx/_row_y；rebuild 重构（步骤节点动态定位）；_build_connections 拆为 _build_columns/_build_links/_build_markers；StepNode 增 setZValue(1)；删除 STEP_NODE_X/V_STEP
  - [page_operation_config.py] _refresh_graph 构造 input_ids → input_tables，传入 kind=classify_step/is_end
- 涉及文件：rpa_engine/gui/models.py、node_graph.py、page_operation_config.py

#### Step 2: 验证
- 状态：✅ 已完成
- 执行内容：新建 _temp/dag-layout-test.py（T1 典型工作流标记/节点/箭头数量、T2 classify_step、T3 派生表无引用不画线、T4 合并输入线终止）；全量回归
- 决策记录：①测试 helper 的 QApplication 被 GC 销毁连带 scene items → 改模块级 _ensure_app 持有；②_build_columns 的 usage 初版基于 table_roles（含 output）导致派生表"被自己 output 引用"误画线 → 改基于 input_tables；③StepNode 与交点圆点 z 值相同导致 itemAt 命中圆点（"该着色节点被隐藏"的根源）→ StepNode setZValue(1)；④bugfix2/bugfix4 两个测试脚本因 STEP_NODE_X 删除/连线算法变更失败 → 同步适配新实现
- 验证结果：dag-layout 4 PASS；全量 58 PASS（19+7+6+7+3+4+4+4）

#### Step 3: 收尾
- 状态：✅ 已完成
- 执行内容：tasks.md/checklist.md 全勾选 + 锚点层覆写 + 本记录创建

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 修改 | rpa_engine/gui/models.py | STEP_KIND + classify_step |
| 修改 | rpa_engine/gui/node_graph.py | DAG 布局/连线/标记重构 |
| 修改 | rpa_engine/gui/page_operation_config.py | _refresh_graph 数据构造 |
| 修改 | _temp/bugfix2-verify-test.py | 适配新连线算法 |
| 修改 | _temp/bugfix4-verify-test.py | 移除 STEP_NODE_X 依赖 |
| 创建 | _temp/dag-layout-test.py | DAG 验证测试（4 项） |
| 创建 | .trae/specs/refactor-node-graph-dag/* | 规格三件套 |
| 修改 | AGENTS.md | 锚点层覆写 |
| 创建 | 本记录 | 任务详情 |

## 关闭标识
- **完成时间**：2026-08-24 14:30 (UTC+8)
- **最终状态**：✅ 全部完成
- **关闭说明**：节点图 DAG 重构落地（箭头/起点终点/分叉合并/着色修复）；GUI 真机视觉验收移交用户
