# 任务记录：修复两项防御缺口（配置期列名校验 + 表头行生效预览）

## 摘要
- **任务目标**：缺口 A——列名错误在配置期拦截（不再漏到运行期）；缺口 B——表头行选择显示生效列名预览
- **任务状态**：已完成
- **开始时间**：2026-08-24 13:00 (UTC+8)
- **最后更新**：2026-08-24 13:25 (UTC+8)
- **要点摘要**：4 文件修改；4 PASS 新验证（含实测场景钉子）+ 50 PASS 回归
- **操作人**：黄泊凯

## 用户输入
> 你刚刚发现的两个缺口，你根据实际情况自适应制定方案并修复。

（前轮分析：缺口 A=阶段 2 表单不校验列名存在性（BaseParamForm 的 conn_columns 参数从未被传入）；缺口 B=表头行选择无结果预览，用户无法预见"选第 2 行→表头变 行1×10→自动编号 行1.1…"的后果）

## Agent 理解与决策

- 保留自由文本输入（多列粘贴场景下拉框更繁琐），校验拦截达到"配置期报错"目标即可
- 列名数据源：主窗口导入瞬间一次性 get_table_columns 查询，随注册表 `columns` 字段下发——页面/表单零连接依赖（不碰引擎连接红线）
- 双层校验分层：MappingMatch 右表列在表单层（表单知道 match_table_id）；目标表列在页面层 _validate_all_steps（页面知道 step.target_table_id，按 _COLUMN_PARAM_KEYS 映射提取六类操作的列名字段）
- 派生表（未执行、列名不可知）跳过校验，运行期引擎守卫兜底（上轮实测已验证守卫有效）
- 表头预览按 pandas mangle 规则模拟重复列名自动编号，选中行变化即刷新，零额外交互
- 计划经 Plan Mode 人工确认（.trae/documents/bugfix6-column-validation-header-preview.md）

## 执行流程

### 流程概览
- 总步骤数：3（修复/验证/收尾）
- 多 Agent 协作：否

### 步骤记录

#### Step 1: 四文件修复
- 状态：✅ 已完成
- 执行内容：
  - [main_window.py] 导入成功后注册表条目增 `columns` 字段（get_table_columns 一行查询，失败不阻断导入）
  - [page_operation_config.py] `_conn_columns()` 辅助；内联表单构建传 conn_columns；`_validate_all_steps` 增 `_check_step_columns`（_COLUMN_PARAM_KEYS 六类操作映射，支持列表/dict 两种参数形态）；警告文案含步骤名/坏列/可用列并 `_select_step` 自动定位
  - [forms.py] `BaseParamForm._check_columns` 工具方法；`MappingMatchForm.validate_params` 增右表列校验
  - [page_input_selection.py] `_HeaderRowDialog._header_summary`：生效列名清单（mangle 模拟）+ 重复列名预警 + 删行提示，`_build_preview` 顶部拼接

#### Step 2: 验证
- 状态：✅ 已完成
- 执行内容：新建 `_temp/bugfix6-verify-test.py`：
  - T1 实测场景前置拦截（真实导入表头=2 的 xlsx → 列名 行1/行1.1/行1.2 → dedup 填"列1" → 开始执行被拦 + 警告含坏列与可用列）
  - T2 覆盖面（filter/aggregate 三字段/rename/convert 坏列全拦；合法列与 * 通配放行；派生表跳过）
  - T3 MappingMatch 表单层右表校验（坏列拦/双合法过/无清单跳过）
  - T4 表头预览（正常表头清单无警告；重复表头显示 行1、行1.1、行1.2 + 预警 + "第 1 行将被删除"）
- 决策记录：首轮 3 FAIL 均为测试/文案瑕疵——patch 捕获参数越界（改 join(a[1:])）、摘要文案"第 1 至 1 行"与断言不匹配（改单行特殊化）；T2 rename 未拦截为**产品代码真缺陷**（dict 参数形态未处理，遍历 str 无 .get 被 isinstance 过滤为空）——补 isinstance(value, dict) 取 keys 分支后全绿
- 验证结果：4 PASS / 0 FAIL；七套回归 19+7+6+7+3+4+4=50 PASS / 0 FAIL；py_compile 4 文件 OK

#### Step 3: 收尾
- 状态：✅ 已完成
- 执行内容：锚点层覆写 + 本记录创建

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 修改 | rpa_engine/gui/main_window.py | 注册表增 columns 字段 |
| 修改 | rpa_engine/gui/page_operation_config.py | conn_columns 构建 + _check_step_columns 列校验 |
| 修改 | rpa_engine/gui/forms.py | _check_columns 工具 + MappingMatch 右表校验 |
| 修改 | rpa_engine/gui/page_input_selection.py | 表头生效列名摘要 |
| 创建 | _temp/bugfix6-verify-test.py | 验证脚本（4 项） |
| 修改 | AGENTS.md | 锚点层覆写 |
| 创建 | 本记录 | 任务详情 |

## 关闭标识
- **完成时间**：2026-08-24 13:25 (UTC+8)
- **最终状态**：✅ 全部完成
- **关闭说明**：两缺口闭环（列名错误配置期拦截+自动定位；表头选择后果可视化）；GUI 真机复测移交用户
