# 任务记录：修复 v4 第二轮真机试用反馈（2 BUG + 2 改进）

## 摘要
- **任务目标**：修复保存缺 target_table_id、left/right 调序失效两项 BUG；实施连线全直线+git 式分叉、参数内联编辑弃弹窗两项改进
- **任务状态**：已完成
- **开始时间**：2026-08-23 22:40 (UTC+8)
- **最后更新**：2026-08-23 23:00 (UTC+8)
- **要点摘要**：5 文件修改；7 PASS 新验证 + 36 PASS 回归全绿
- **操作人**：黄泊凯

## 用户输入
> 1. `保存失败：配置校验未通过（步骤 [S1] 缺少 target_table_id）`，保存一直报错，但 GUI 界面上确认所有设置已经到位
> 2. `left`、`right` 按钮失效，无法调整数据表排布顺序
> 3. 绘图连线（非 BUG）：连线全部用直线；产生新表的功能步骤要体现分叉线（像 git fork 分支）
> 4. 配置界面参数显示编辑（非 BUG）：点击功能步骤时右边直接显示参数并允许编辑（放弃弹出式窗口和编辑参数按钮）

## Agent 理解与决策

### BUG 定性
- **BUG 1（保存缺 target）**：QComboBox 向空 combo addItem 首项时 Qt 自动选中并显示（视觉假象），但 `currentIndexChanged` 连接在其后——模型从未同步。叠加 `add_step` 不设默认目标表。100% 程序 BUG（用户"设置已到位"的观感正是假象来源）
- **BUG 2（调序失效）**：`table_moved` 信号发射列显示名（"T1 测试表"），`_on_table_reorder` 按原始别名匹配 → 恒不命中静默返回
- **附带发现 ①**：步骤节点 x=-100 负坐标落在 sceneRect(0,0) 之外（部分不可见）——随连线重构修正
- **附带发现 ②**：`_new_round` 替换 model 对象致操作配置页持有旧引用脱钩（新一轮后页面写入旧模型、保存/执行读新模型）——一并修复

### 决策
- 计划经 Plan Mode 人工确认后执行（.trae/documents/bugfix2-target-reorder-graph-inline.md）
- 内联编辑不设"应用"按钮：切换步骤=尽力静默收拢（日志），保存/开始=强校验弹错中止
- 连线采用 git 提交图语义：纵向列线（输入灰/派生绿）+ 横向步骤线，全直线

## 执行流程

### 流程概览
- 总步骤数：3（修复/验证/收尾）
- 多 Agent 协作：否

### 步骤记录

#### Step 1: 五文件修复
- 状态：✅ 已完成
- 执行内容：
  - [models.py] `add_step` 默认目标表=第一张输入表；新增 `reset()`（原地清空保对象同一性）
  - [forms.py] `BaseParamForm` QDialog→QWidget（移除确定/取消底栏），新增 `try_apply()`
  - [node_graph.py] 常量 STEP_NODE_X=20/LEFT_MARGIN=190（正坐标）；TableNode 增 reorderable（派生列无调序按钮）；StepLayoutEntry 增 primary_input/output_table；GraphLayoutData 增 input_count；`_build_connections` 重写为纵向列线+横向步骤线全直线（派生列绿色、连线 zValue=-1）
  - [page_operation_config.py] BUG1：combo 无选中时显式选首项并同步模型；BUG2：`_on_table_reorder` 改显示名匹配；改进4：内嵌表单+`_select_step`/`_harvest_current_form`，删除弹窗路径；保存/开始入口先收拢；清理 json/shutil 死 import
  - [main_window.py] `_new_round` 改 `model.reset()`
- 涉及文件：上述 5 个 gui 文件

#### Step 2: 验证
- 状态：✅ 已完成
- 执行内容：新建 `_temp/bugfix2-verify-test.py`（T1 默认目标表+combo 同步/T2 保存链路/T3 调序/T4 直线+绿分叉+分叉起点/T5 QWidget 基座+try_apply/T6 内联收拢含非法文本保护/T7 模型同一性）；四套回归 + py_compile
- 决策记录：首轮测试 3 FAIL 均为测试 helper 缺陷（未调 `model.set_tables`，真实链路由主窗口调用），修正 helper 后全绿——非产品代码问题
- 验证结果：新测试 7 PASS / 0 FAIL；回归 19+7+6+4=36 PASS / 0 FAIL；py_compile OK

#### Step 3: 收尾
- 状态：✅ 已完成
- 执行内容：锚点层覆写 + 本记录创建

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 修改 | rpa_engine/gui/models.py | add_step 默认目标表 + reset() |
| 修改 | rpa_engine/gui/forms.py | 表单基座 QWidget 化 + try_apply |
| 修改 | rpa_engine/gui/node_graph.py | 直线分叉连线重写 + 布局修正 + reorderable |
| 修改 | rpa_engine/gui/page_operation_config.py | BUG1/BUG2 修复 + 内联编辑重构 |
| 修改 | rpa_engine/gui/main_window.py | _new_round 模型同一性 |
| 创建 | _temp/bugfix2-verify-test.py | 验证脚本（7 项） |
| 修改 | AGENTS.md | 锚点层覆写 |
| 创建 | 本记录 | 任务详情 |

## 关闭标识
- **完成时间**：2026-08-23 23:00 (UTC+8)
- **最终状态**：✅ 全部完成
- **关闭说明**：2 BUG 根治 + 2 改进落地 + 2 附带缺陷修复；7+36 PASS 全绿；GUI 真机复测移交用户
