# 任务记录：修复 v4 编译版实测反馈第一项（frozen 路径落缓存区 + 默认名时间戳重复）

## 摘要
- **任务目标**：frozen（exe）环境所有可写数据锚定 exe 所在目录；模板默认名时间戳去重
- **任务状态**：已完成
- **开始时间**：2026-08-24 12:00 (UTC+8)
- **最后更新**：2026-08-24 12:20 (UTC+8)
- **要点摘要**：新增 paths.py 统一双环境路径解析；10 文件修改；4 PASS 新验证 + 46 PASS 回归
- **操作人**：黄泊凯

## 用户输入
> 全流程跑通。现在调整第一项：保存与导出路径——编译成单个 .exe 后实际运行时，程序启动使用系统盘缓存区（C:\Users\HBK\AppData\Local\Temp），运行中保存/导出虽确认成功，但程序关闭后系统清理缓存全部丢失。要求开发与编译环境都默认使用程序所在根目录（python 自适应检测运行/开发环境）。另外保存配置默认名（时间戳）出现两串完全相同的时间戳被拼接。

## Agent 理解与决策

### 诊断
- **路径问题根因**：全库 8 处 `Path(__file__).resolve().parent.parent` 推导引擎根。PyInstaller onefile 下 `__file__` 指向解包临时目录 `Temp\_MEIxxxx\rpa_engine\...`——运行期"存在且可写"（故实测保存/导出确认成功），退出即被 bootloader 删除。开发环境为真实源码路径，故离屏测试从未暴露
- **命名问题根因**：保存对话框默认名 `%Y-%m-%d_%H:%M:%S` → `_alloc_filename` 又拼自身时间戳前缀 `{YYYYMMDD_HHmmss}_{safe_name}.json`，safe_name 经 sanitize（`:`→`_`）后与 stamp 重复 → `20260824_001530_2026-08-24_00_15_30.json`

### 决策
- **可写/只读资源分流**：exe 所在目录 = workspace/logs/temp/templates/user（持久可写）；`sys._MEIPASS` = 预设模板等打包只读资源（datas 携带）。杜绝向解包临时目录写入任何东西
- 统一模块 `rpa_engine/paths.py` 作为全库唯一路径基准；8 处 `__file__` 推导全部替换
- ExportForm 空路径预填引擎根下 `导出结果.xlsx`（用户显式路径完全尊重）
- 默认名去重仅检测"默认时间戳形态"（正则），自定义名维持时间戳前缀防重名
- spec：hiddenimports 显式声明 paths（部分延迟 import 静态分析可能遗漏）；datas 逻辑零改动仅注释同步
- 计划经 Plan Mode 人工确认（.trae/documents/bugfix5-frozen-paths-timestamp-dup.md）

## 执行流程

### 流程概览
- 总步骤数：3（修复/验证/收尾）
- 多 Agent 协作：否

### 步骤记录

#### Step 1: 修复（10 文件）
- 状态：✅ 已完成
- 执行内容：
  - ✚ [paths.py] 新建：is_frozen/get_engine_root/get_bundle_dir 双环境解析
  - [gui/app.py、main_window.py、page_input_selection.py、page_operation_config.py、page_config.py] ENGINE_ROOT 改 `get_engine_root()`
  - [gui/user_template_manager.py] ENGINE_ROOT/BUNDLE_DIR 分流；templates_root 默认 BUNDLE_DIR/templates（预设只读）；storage_dir 仍 ENGINE_ROOT/templates/user（可写持久）；_alloc_filename 默认时间戳形态去重（新增 _DEFAULT_NAME_RE）
  - [gui/forms.py] ExportForm 空路径预填引擎根/导出结果.xlsx；_browse 起始目录智能
  - [ops/session_db.py、ops/excel_preprocessor.py] 根路径改 get_engine_root()（延迟 import）
  - [RPA_Workflow_v3.spec] hiddenimports 增 'paths'；datas 注释同步 v4 现状（逻辑零改动）

#### Step 2: 验证
- 状态：✅ 已完成
- 执行内容：新建 `_temp/bugfix5-verify-test.py`：
  - T1 paths 双态（开发态=frozen 模拟 monkeypatch sys.frozen/executable/_MEIPASS）
  - T2 frozen 模拟全链落盘（MainWindow 完整链路：ENGINE_ROOT/session db/TEMP_DIR/用户模板全部断言落模拟 exe 目录而非源码目录）
  - T3 默认名去重（`20260824_001530.json` vs 自定义 `20260824_001530_我的模板.json`）
  - T4 导出默认路径（空则锚定/显式尊重）
- 验证结果：4 PASS / 0 FAIL；六套回归 19+7+6+7+3+4=46 PASS / 0 FAIL；py_compile 10 文件 OK

#### Step 3: 收尾
- 状态：✅ 已完成
- 执行内容：锚点层覆写 + 本记录创建

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 创建 | rpa_engine/paths.py | 双环境路径解析唯一基准 |
| 修改 | rpa_engine/gui/app.py 等 5 个 gui 文件 | ENGINE_ROOT 统一替换 |
| 修改 | rpa_engine/gui/user_template_manager.py | 根路径分流 + 默认名去重 |
| 修改 | rpa_engine/gui/forms.py | 导出默认路径 |
| 修改 | rpa_engine/ops/session_db.py、excel_preprocessor.py | 根路径替换 |
| 修改 | RPA_Workflow_v3.spec | hiddenimports+注释（逻辑零改动） |
| 创建 | _temp/bugfix5-verify-test.py | 验证脚本（4 项含 frozen 模拟） |
| 修改 | AGENTS.md | 锚点层覆写 |
| 创建 | 本记录 | 任务详情 |

## 关闭标识
- **完成时间**：2026-08-24 12:20 (UTC+8)
- **最终状态**：✅ 全部完成
- **关闭说明**：frozen 路径锚定 exe 根（重新编译后生效）+ 默认名去重；编译版复测移交用户
