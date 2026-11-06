# 任务记录：修复 v4 首轮真机试用反馈的 2 项 BUG

## 摘要
- **任务目标**：修复用户真机试用反馈的表头行按钮 setText 报错与模板保存失败两项 BUG
- **任务状态**：已完成
- **开始时间**：2026-08-23 22:00 (UTC+8)
- **最后更新**：2026-08-23 22:20 (UTC+8)
- **要点摘要**：BUG1 包装容器 setText；BUG2 v3 校验残留；4+32 PASS 验证全绿
- **操作人**：黄泊凯

## 用户输入
> 现在开始修复测试试用过程中发现的 BUG：
> 1. `'QWidget' object has no attribute 'setText'` 报错，对数据表设置表头行时出现的报错；
> 2. `保存失败：配置必须包含 'workflow' 对象` 报错，保存配置文件时候的报错，这一步存在有可能是我误操作的可能，但是你要分析是程序功能本身的 BUG，还是 GUI 引导的缺失

## Agent 理解与决策

### BUG 定性
- **BUG 1**：程序 BUG（100% 复现）。`_add_row` 将表头行按钮经 `_center_widget()` 包装后放入单元格，`_on_pick_header` 中 `cellWidget(row, 4)` 返回包装容器 QWidget 而非 QPushButton，`.setText()` 必然 AttributeError。
- **BUG 2**：程序 BUG（100% 复现，**非误操作**）。`UserTemplateManager.save()` 残留 v3 结构校验（强制 `config["workflow"]`），而 v4 的 `model.to_dict()` 产出 `{__meta, name, global, tables, steps}` 从不含 `workflow` 键——任何用户保存必败。顺带发现引导缺口：零步骤保存静默通过，补确认引导。

### 决策
- 修复方案经 Plan Mode 人工确认后执行（计划文件 .trae/documents/bugfix-header-btn-and-template-save.md）
- BUG 2 波及 save/load/load_preset 三处 + docstring，一并 v4 化（templates/user/ 无 v3 遗留模板——BUG 2 导致 v4 后从未成功保存过，无需兼容分支）

## 执行流程

### 流程概览
- 总步骤数：4（诊断/修复×3/验证/收尾）
- 多 Agent 协作：否（单 Agent 直接执行）

### 步骤记录

#### Step 1: 诊断（Plan Mode 只读探索）
- 状态：✅ 已完成
- 执行内容：读取 user_template_manager.py 全文 + page_input_selection.py 相关段，钉死两 BUG 证据链；输出修复计划并经人工确认

#### Step 2: 三处修复
- 状态：✅ 已完成
- 执行内容：
  - FIX 1 [page_input_selection.py `_on_pick_header`]：经 `findChildren(QPushButton)` 取真实按钮更新文本（与勾选状态恢复 L386-390 同模式）
  - FIX 2 [user_template_manager.py]：docstring 存储规则 v4 化；`save()` 入参校验改为 tables/steps 列表检查 + payload 改 v4 平铺（__meta 后写合并，保留 schema_version）；`load()`/`load_preset()` 校验同步 v4
  - FIX 3 [page_operation_config.py]：保存按钮接新增 `_on_save_clicked` 槽，零步骤时弹确认引导
- 涉及文件：rpa_engine/gui/page_input_selection.py、rpa_engine/gui/user_template_manager.py、rpa_engine/gui/page_operation_config.py

#### Step 3: 验证
- 状态：✅ 已完成
- 执行内容：新建 _temp/bugfix-verify-test.py（T1 表头按钮含回归钉子/T2 模板 v4 roundtrip/T3 v3 结构拒绝/T4 空步骤引导三分支）；跑三套既有回归 + py_compile
- 决策记录：首轮测试暴露两个问题——① T1 的 patch 未模拟选中行（测试缺陷，补 patch selected_row_index）；② T4 发现修复代码自身缺陷 `box.button(QMessageBox.RejectRole)` PyQt5 绑定不接受 ButtonRole（已删除该行修正）。两处修正后全绿。
- 验证结果：bugfix 4 PASS / 0 FAIL；回归 19+7+6 PASS / 0 FAIL；py_compile OK

#### Step 4: 锚点收尾
- 状态：✅ 已完成
- 执行内容：锚点层覆写 + 本记录创建

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 修改 | rpa_engine/gui/page_input_selection.py | FIX 1：findChildren 取真实按钮 |
| 修改 | rpa_engine/gui/user_template_manager.py | FIX 2：save/load/load_preset + docstring v4 化 |
| 修改 | rpa_engine/gui/page_operation_config.py | FIX 3：_on_save_clicked 空步骤引导 |
| 创建 | _temp/bugfix-verify-test.py | 修复验证脚本（4 项） |
| 修改 | AGENTS.md | 锚点层覆写（§7.6） |
| 创建 | 本记录 | 任务详情 |

## 关闭标识
- **完成时间**：2026-08-23 22:20 (UTC+8)
- **最终状态**：✅ 全部完成
- **关闭说明**：两项 BUG 均定性为程序缺陷并修复（BUG 2 与用户疑虑的"误操作"无关）；4 项修复验证 + 32 项回归全绿
