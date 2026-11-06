# 任务记录：新增"保存为历史配置"功能（用户模板保存与复用）

## 摘要
- **任务目标**：新增"保存为历史配置"功能——UserTemplateManager 模块 + 配置/报告界面保存按钮 + 模板列表集成
- **任务状态**：已完成
- **开始时间**：2026-08-22 14:30 (UTC+8)
- **最后更新**：2026-08-22 14:30 (UTC+8)
- **要点摘要**：模式 B（Analyzer×2 并行 → Coder-Manager → Coder-GUI → Coordinator 写入自检）；历史配置与预设模板同 schema，[应用] 加载逻辑对用户模板透明
- **操作人**：黄泊凯

## 用户输入
任务提示词（粘贴文件）核心要求：
1. 新建 UserTemplateManager 模块（save/load/list_templates/delete/get_merged_list），存储目录默认 `workspace/user_templates`，JSON + `__meta` 元数据（加载时剥离）
2. 用户配置界面新增 [保存配置] 按钮（QInputDialog 命名 → save → 重名覆盖确认 → 刷新列表）
3. 结果报告界面新增 [保存本次配置] 按钮（仅成功状态可点；配置来源为本轮执行的实际配置，非当前表单值）
4. 模板列表集成：数据源改为 get_merged_list()，列表项显示 [用户]/[预设] 前缀；[应用] 按 source 分支取 dict（user 走 manager.load，preset 走原逻辑），覆盖导入路径不变；新增 [删除]（仅用户模板，二次确认）
5. 硬性约束：不改 [应用] 核心覆盖逻辑、不改引擎层、不改 build/spec、无新依赖、纯 JSON、保存前必须校验、预设模板不可删、不编译
6. 强制多 Agent 协作模式（Coordinator + Analyzer-GUI + Analyzer-Template + Coder-Manager + Coder-GUI）

## Agent 理解与决策
- 执行模式判定：**模式 B**（提示词显式要求；涉及新建 1 模块 + 修改 ≥3 个 GUI 文件，超模式 A 阈值；环境支持子 Agent 派发）
- 任务定性：满足任务定义 3 条（文件修改 + 显式多 Agent + 步骤 ≥5），纳入锚点机制
- 关键设计预判（待 Analyzer 验证）：
  - UserTemplateManager 位置倾向 `gui/user_template_manager.py`（纯逻辑无 Qt 依赖，与 models.py 数据层风格一致），最终由 Analyzer 建议
  - 保存前校验复用现有 parser.parse_workflow + validator.validate_workflow（dict → 临时文件 → 解析校验）
  - 按钮文本采用纯 ASCII（项目有 Unicode 图标渲染问题前科，Fix-2 注释明确使用纯 ASCII "[+]" 方案）
  - 报告页保存的配置来源：MainWindow 持有本轮落盘的 gui_workflow.json 路径，执行结束时传递给报告页

## 执行流程

### 流程概览
- 总步骤数：8
- 多 Agent 协作：是（4 个子 Agent：Analyzer-GUI、Analyzer-Template、Coder-Manager、Coder-GUI）

### 步骤记录

#### Step 1: 开工程序（锚点层覆写 + 任务记录创建）
- 状态：✅ 已完成
- 执行内容：读取 agent-execution-mode.md §5 声明格式；覆写锚点层；创建本任务记录文件
- 涉及文件：AGENTS.md（修改）、docs/task-records/2026-08-22-user-template-save.md（创建）
- 决策记录：按方案 A（新任务）启动，锚点层前任务状态为"已完成"

#### Step 2: Phase A — Analyzer-GUI + Analyzer-Template 并行分析
- 状态：✅ 已完成
- 执行内容：两个 Explore 子 Agent 并行，分别分析三界面布局/信号槽与模板区数据源/加载链路
- 涉及文件：只读（page_config.py / page_report.py / main_window.py / models.py / parser.py / test_full_etl.json / app.py 局部）
- 子 Agent：Analyzer-GUI ✅、Analyzer-Template ✅
- 关键结论：① 配置页按钮锚点=流程步骤标题行（清空按钮左侧）；② 报告页按钮锚点=左侧底栏（确定按钮左侧），fill() 的 status 参数承担 enable 联动；③ 本轮配置来源=MainWindow 在 start_workflow 落盘成功后记录的 model.to_dict() 内存快照；④ load_from_dict 天然忽略顶层多余键，__meta 并列方案可行；⑤ parser 接受文件路径且忽略未知键；⑥ 关键缺陷预警：back_to_config 不刷新模板列表，保存成功后必须显式 refresh

#### Step 3: Coordinator 一致性验证与决策
- 状态：✅ 已完成
- 决策记录：
  - D1 存储目录：`workspace/user_templates`（Spec-1 默认值，服从任务提示词；Analyzer 建议的 user_workflows 不采纳）
  - D2 模块位置：`rpa_engine/gui/user_template_manager.py`（任务允许"或 gui/ 下合适位置"，与 models.py 纯数据层同目录风格一致）
  - D3 按钮文本：纯中文"保存配置"/"保存本次配置"（不用 💾——项目 Fix-2 有 Unicode 渲染问题前科，现有按钮全为纯中文短动词，遵循 dev-spec 项目惯例）
  - D4 重名判定：按 __meta.name（显示名）判重；覆盖时保留原文件名与 created_at，仅更新 workflow 内容
  - D5 列表排序：用户模板（created_at 降序）在前，预设模板（文件名升序）在后
  - D6 校验复用：落盘正式文件后调 parse_workflow + validate_workflow 双重校验，失败删文件（无需临时文件中转；__meta 被两者忽略）
  - D7 报告页配置来源：内存快照（_last_run_config = start_workflow 落盘成功后的 model.to_dict()），不读文件（避免固定路径被下轮覆盖的风险）
  - D8 刷新补漏：保存/删除成功后由 MainWindow 调 config_page.refresh_templates()
  - D9 Manager 实例归属：MainWindow 持有单例，注入 ConfigPage

#### Step 4: Phase B — Coder-Manager 实现 UserTemplateManager
- 状态：✅ 已完成
- 执行内容：子 Agent 按冻结契约实现模块（含 12 项桩冒烟自测），产出写入 _temp/coder-manager-user_template_manager.py
- 涉及文件：_temp/coder-manager-user_template_manager.py（创建，451 行）
- 子 Agent：Coder-Manager ✅
- 决策记录：覆盖场景采用 .tmp 副本校验 + os.replace 原子替换（比契约更稳，原模板零损伤）；同秒文件名碰撞追加 _2/_3 序号

#### Step 5: Coordinator 审核 Manager 代码并落位
- 状态：✅ 已完成
- 执行内容：全文审核 451 行（契约完整性/异常处理/路径穿越防护/回滚逻辑/无 Qt import）→ 审核通过 → 复制到正式位置
- 涉及文件：rpa_engine/gui/user_template_manager.py（创建，19,564 B）

#### Step 6: Phase C — Coder-GUI 实现界面集成
- 状态：✅ 已完成
- 执行内容：子 Agent 按冻结规格修改三个 GUI 文件，产出写入 _temp/coder-gui-*.py
- 涉及文件：_temp/coder-gui-page_config.py / coder-gui-page_report.py / coder-gui-main_window.py（创建）
- 子 Agent：Coder-GUI ✅
- 关键实现：保存对话框流程统一收敛到 MainWindow._do_save_template（QInputDialog → save → 重名覆盖确认 → 刷新）；报告页按钮仅状态 completed 启用；配置快照取 start_workflow 落盘后的 to_dict()

#### Step 7: Coordinator 最终写入 + Phase D 自检
- 状态：✅ 已完成
- 执行内容：
  1. 审核三个 GUI 文件全文（核心覆盖逻辑未动、标记注释全保留）
  2. 备份原始三文件至工作区 backup-user-template-task-20260822/*.orig（无 VCS 仓库的修改前备份义务）
  3. 落位三个正式文件
  4. py_compile 四文件全部通过（Python 3.10.12）
  5. 功能冒烟 10/10 通过（沙箱实测：保存/重名拒绝/覆盖/列表/加载 schema 全等/磁盘结构/合并列表 1 用户+8 预设/删除/路径穿越拦截/校验失败回滚无孤儿文件）
  6. 实例文档同步：rpa_engine/README.md gui 模块清单 11→12（新增 user_template_manager），version 1.1.0→1.2.0，last-updated 2026-08-22
  7. §7.4 快速校验：链接全通、Instances-INDEX 一致、元信息 8/8、引擎层 5 文件 mtime 未变
- 涉及文件：rpa_engine/gui/page_config.py（覆盖）、page_report.py（覆盖）、main_window.py（覆盖）、rpa_engine/README.md（修改）
- 决策记录：自检项"确认无硬编码路径"按项目惯例理解为"使用 ENGINE_ROOT 相对解析"（Path 拼接），与现有代码一致

#### Step 8: 收尾（锚点层更新、任务记录关闭、输出实现报告）
- 状态：✅ 已完成
- 执行内容：本记录写入关闭标识；锚点层置已完成；向用户输出结构化实现报告

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 修改 | AGENTS.md | 锚点层覆写（任务开始/结束各一次） |
| 创建 | docs/task-records/2026-08-22-user-template-save.md | 本任务记录 |
| 创建 | rpa_engine/gui/user_template_manager.py | 用户历史配置模板管理器（451 行） |
| 修改 | rpa_engine/gui/page_config.py | +54 行：保存按钮/模板区合并渲染/应用分支/删除 |
| 修改 | rpa_engine/gui/page_report.py | +9 行：保存本次配置按钮 + 状态联动 |
| 修改 | rpa_engine/gui/main_window.py | +49 行：信号路由/配置快照/统一保存流程 |
| 修改 | rpa_engine/README.md | gui 模块清单同步 + 元信息版本 |
| 创建 | _temp/coder-manager-*.py、_temp/coder-gui-*.py | 子 Agent 中间产物（审核留痕） |
| 备份 | 工作区 backup-user-template-task-20260822/*.orig | 三个被覆盖文件的原始版本 |

## 关闭标识
- **完成时间**：2026-08-22 15:20 (UTC+8)
- **最终状态**：✅ 全部完成
- **关闭说明**：功能实现 + 自检全过（语法 4/4、功能冒烟 10/10）；未编译（遵约束）；待人工在真实环境（conda + PyQt5）做界面走查验收
