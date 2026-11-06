---
title: Runtime Environment Spec — V3 运行与构建环境规范
type: knowledge
scope: global
status: active
owner: 黄泊凯
last-updated: 2026-10-24
tags: [环境规范, 依赖, 构建, SQLite, conda]
binding: reference
confidence: 已校验一致（与 build/BUILD_INFO.txt、requirements.txt、requirements.lock、docs/dev-spec.md §12 交叉验证；2026-10-19 R15 §3 依赖基线与实测版本回写并指向 requirements.lock；2026-10-24 R16 复核 §5 构建元信息 Git 口径与 §6 测试输入实况；个别条目单独标注）
content-revision: 2026-10-24
---

# Runtime Environment Spec — V3 运行与构建环境规范

> 所属层级：知识层（docs/）｜约束力：[参考]
> 适用范围：在本项目环境上运行引擎、执行构建、部署交付时的环境参数参考
> 最后更新：2026-10-24（R16 同步 Git 口径与测试输入实况；此前 2026-09-14 R2 构建人工接管 + R5 conda 环境路径固化；2026-08-21 v2.2 升级：自 knowledge/ 迁入 docs/）｜可信度状态：[已校验一致]（与 build/BUILD_INFO.txt、requirements.txt、docs/dev-spec.md §12 交叉验证；裁定条目单独标注）

## 1. 操作系统与硬件基线

- 目标操作系统：Windows（cmd 批处理、GBK 编码产物为常态）[已校验一致]，依据：build.bat 为纯 cmd 脚本、BUILD_INFO.txt 为 GBK 编码 [src:docs/dev-spec.md §12[22]、build/BUILD_INFO.txt]
- 硬件基线：16GB 内存办公电脑，Pandas 内存峰值需严格管控 [已校验一致] [src:AGENTS.md 核心原则（红线）]

## 2. Python 运行时

- 声明最低版本：Python 3.9+ [已校验一致] [src:v3/AGENTS.md 技术栈、requirements.txt]
- 实际构建版本：Python 3.11.15（conda 环境 `CPS-GPES_RPA-py311`，2026-08-15 构建）[已校验一致] [src:build/BUILD_INFO.txt]
- **环境路径（R5，2026-09-14 固化）**：`C:\Users\hbk\.conda\envs\CPS-GPES_RPA-py311`——项目当前实际使用环境，运行/构建均应基于该环境 [裁定] [src:用户补充裁定 R5]
- requirements.txt 注释另提及 py310 验证环境，但当前无 py310 构建产物佐证 [推测]，依据：requirements.txt 头部注释（单一文本线索）

## 3. 关键依赖版本基线

pandas ≥2.0,<4（实测 3.0.5）、openpyxl ≥3.1（实测 3.1.5）、xlrd ≥2.0（实测 2.0.2）、loguru ≥0.7（实测 0.7.3）、psutil ≥5.9（实测 7.2.2）、PyQt5 ≥5.15,<6（实测 5.15.11）（运行）；pyinstaller ≥6.22（打包，实测 6.22.0）[已校验一致] [src:requirements.txt、build/BUILD_INFO.txt]
- **实测版本全量锁定**：见 `v3/requirements.lock`（2026-10-19 R15/B-50 生成，原样 `pip freeze`，不手工增删；抬头含废弃包告警；**2026-10-24 注记**：位于 v3 目录，非仓库根）
- **已移除的废弃依赖声明**：`python-docx`／`python-pptx` 已于 2026-09-24（R6/C4-P3-14）从 `requirements.txt` 移除声明——其所指向的 `steps/` 已于 2026-09-13 物理删除，全库 import 零命中。**环境内仍残留安装**（不卸载，避免影响其他工具），仅于 `requirements.lock` 头部告警「勿据 lock 在新环境安装」[已校验一致] [src:requirements.txt、requirements.lock]

## 4. SQLite 运行约束

- 引擎使用 SQLite WAL 模式共享连接，由引擎统一初始化 [已校验一致] [src:rpa_engine/engine/executor.py PRAGMA journal_mode=WAL]
- **网络/挂载磁盘限制**：沙箱挂载盘（如 9p 协议）不支持 SQLite WAL，验证场景需将数据库置于本地磁盘或 /tmp [推断]，依据：_temp/pending-items.md 环境性事项#9 与历史 verify 结论相互印证（该文件已随 09-14 `_temp` 清理删除，此处为历史依据；R10 后 `_temp` 仅剩 `DAG-rebuild/` 与 `ledger_2026-09-24/`）

## 5. 构建与交付基线

- 打包方式：PyInstaller 单文件 exe（无控制台窗口），templates/ 资源内置 [已校验一致] [src:RPA_Workflow_v3.spec、docs/build-guide.md]
- 构建前置：必须在已激活 conda 环境 `CPS-GPES_RPA-py311`（`C:\Users\hbk\.conda\envs\CPS-GPES_RPA-py311`，R5）中执行 build.bat（脚本检测 `CONDA_DEFAULT_ENV`）[已校验一致] [src:build.bat][裁定: R5]
- **构建由人工接管（R2，2026-09-14）**：Agent 不执行 build.bat、不修改 `build/` 产物；重建动作由人工在真机会话执行 [裁定]
- 构建元信息：build/BUILD_INFO.txt 记录构建时间、输出路径、conda 环境、Python/PyInstaller 版本、源码哈希与 Git 修订；仓库根 `.git` 存在，`BUILD_INFO.txt` 记录 `SOURCE_HASH` 与 `GIT_REV`，有效性判定以 `SOURCE_HASH` 为准（2026-10-24 实测一致），`GIT_REV` 仅辅助追溯 [已校验一致]（2026-10-24 注记：原文"当前 Git 哈希为 N/A（扫描边界内无 .git），产物与代码基线不可追溯"已不成立）
- 编码注意：构建产物文本（BUILD_INFO.txt、build.bat 控制台输出）为 GBK，UTF-8 工具读取会乱码，属正常现象 [已校验一致]

## 6. 测试环境现状

- 按相关规定，测试工作暂不在本仓库执行（2026-08-18 用户裁决）；Test/input/ 下为 `测试输入0~3.xlsx` 四份通用占位数据（列1-列10），与模板 SQL 业务列名不匹配，端到端验证事项暂缓 [已校验一致]（2026-10-24 注记：原文 `Test/input/测试输入.xlsx` 单文件已不成立，实测为 0~3 共四份）[src:docs/architecture.md §9 阻塞#4]
