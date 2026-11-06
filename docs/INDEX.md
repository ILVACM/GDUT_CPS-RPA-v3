---
title: INDEX — 知识层入口
type: index
scope: global
status: active
owner: 黄泊凯
last-updated: 2026-11-01
tags: [索引, 知识层, 路由]
confidence: 已校验一致（清单与 docs/ 实际知识文件一一对应；plan/ 已划归方案态层；doc-governance/anchor-mechanism 为 2026-09-06 精简剥离新增；backlog.md 为 2026-09-13 新增；2026-09-24 R6/E6 新增 user-manual/deployment-guide；2026-09-24 R7 新增 function-spec-rules，共 13 篇）；2026-09-13 同步 architecture §8.4/§10 与 dev-spec 入口口径；2026-09-24 R6/E1 日期列与 frontmatter 全量同步（doc_verify 脚本核查）；2026-10-24 R16 全量复核（10 篇文档口径修正后日期与摘要同步）；2026-11-01 R17 同步 W-23/W-24 关闭（运行产物移出版本控制、模板化输出裁定暂缓）
---

# INDEX — 知识层入口

> `task-records/` 为任务执行记录目录，非知识文档，不纳入知识层管辖。
> `plan/` 为方案态层（描述"将要做的事"），不列入本索引，入口见 [plan/INDEX.md](./plan/INDEX.md)；分层判定原则见 AGENTS.md §4.1。

## 1. 知识层文档清单

| 文件路径 | 标题 | 一句话摘要 | 标签/分类 | 最后更新 | 可信度状态 |
|----------|------|------------|-----------|----------|-----------|
| [agent-execution-mode.md](./agent-execution-mode.md) | Agent 运行方式判定规范 | A/B/C/D 四种运行模式定义、选择标准、环境能力检测方法、降级策略与输出声明格式；多 Agent 协作规范（§6，含编码类角色集） | 运行方式、模式判定、降级 | 2026-09-13 | [已校验一致] |
| [architecture.md](./architecture.md) | Architecture — V3 RPA 工作流引擎架构设计 | 参数文件 v3.1 Schema（tables[]+steps[]，自 v3 迭代而来）、三段式执行流程、BUILTIN_OPS 用户操作目录与分发机制（§3；2026-10-19 R15 字段表改 8 字段集）、数据传递规则（§4，2026-10-24 按代码修正 target/output_table_id 与 SessionDB 连接口径）、10 项用户操作清单（§6，2026-11-02 增 supervision_report）、四阶段 GUI 架构与生命周期（§8.0）、已知阻塞与规避策略（§9）、§8.4 交互设计原则（最高目标原则）、§10 架构刚性边界（ETL 底层不可偏离） | 架构、引擎、设计 | 2026-11-02 | [已校验一致] |
| [dev-spec.md](./dev-spec.md) | Dev-Spec — V3 RPA 工作流引擎编码规范 | SQLite 规则、Pandas 红线、Output 规则（2026-10-24 加现行口径：export 为 write_only 流式直出、无模板）、异常处理、日志、内存管理、Anti-Patterns、通用编码规范（T1-T48 提炼，§8-§17）；2026-09-13 入口口径调整（GUI 为唯一交互入口，CLI 废弃目标态）；2026-09-18 日志口径更新（GUI 终端面板随 W-19 移除，print 经 loguru 落盘）；2026-10-24 修正 GUI 已完成/依赖已移除/BaseStep 已删等口径；2026-11-01 模板化输出改「暂缓」（W-24 裁定） | 规范、编码、红线 | 2026-11-01 | [已校验一致] |
| [build-guide.md](./build-guide.md) | Build Guide — V3 RPA 工作流引擎编译配置规范 | spec 文件结构、关键配置项、修改红线、重建流程（2026-10-24 修正：spec 被 .gitignore 忽略、不在版本库）、build.bat 参数体系、构建产物有效性判定（§1.10；2026-10-24 状态更新：exe 2026-10-19 构建、SOURCE_HASH 一致、W-20 关闭） | 编译、打包、构建、spec | 2026-10-24 | [已校验一致] |
| [legacy.md](./legacy.md) | Legacy — 遗留系统说明与 v2 关系 | v3 引擎与 v1/v2 模块的关系、冻结策略、迁移边界、可复用资产（2026-10-24 修正：v3.1 为 9 项 BUILTIN_OPS、v2 目录为 A-docs/、Word/TXT/PPT 无对应操作） | 遗留、迁移、边界 | 2026-10-24 | [已校验一致] |
| [runtime-env-spec.md](./runtime-env-spec.md) | Runtime Environment Spec — V3 运行与构建环境规范 | 操作系统/硬件基线、Python 与依赖版本、SQLite WAL 约束、构建交付与环境限制；2026-10-19 R15 §3 依赖基线回写实测版本并指向 requirements.lock（v3 目录）；2026-10-24 修正 Git 基线（.git 存在、以 SOURCE_HASH 判定）与测试输入文件名 | 环境、依赖、构建 | 2026-10-24 | [已校验一致] |
| [doc-governance.md](./doc-governance.md) | 文档治理与维护规范 | 文档变更操作规范、维护职责矩阵、生命周期与元信息区、全局更新校验机制（五项校验+三步流程）、实例文档维护、冲突解决与豁免、源码↔规约同步规则、验收与回归记录规范（2026-10-24 基线更新为 234 用例）、标签体系落位规范、约束层容量与下沉规则（§1~§5 自 AGENTS.md §7.1-7.5 迁入；§6 自 §4.6 迁入；§7~§10 于 2026-09-13 新增；经背书具 [约束] 效力） | 文档治理、元信息区、生命周期、校验机制 | 2026-10-24 | [已校验一致] |
| [anchor-mechanism.md](./anchor-mechanism.md) | 任务执行锚点记录追踪机制（规定层） | 锚点机制规定层全文：任务定义、运作规则、三层结构、迭代任务、写入规则、运作流程（自 AGENTS.md §7.6 迁入，经背书具 [约束] 效力） | 锚点机制、任务记录、任务追踪 | 2026-09-06 | [已校验一致] |
| [backlog.md](./backlog.md) | Backlog — 规约与文档治理待办清单 | W 编号待办主表（含状态与处置依据）、执行约定、已关闭归档、撤销登记；W 清单的**唯一受管辖活载体**（`_temp/repo-context-report.md` §4.6 为来源快照，该文件已随 R10 `_temp` 清理，骨架见 `_temp/ledger_2026-09-24/CLEANUP_MANIFEST.md`）；2026-10-24：W-20/W-22 关闭、W-23/W-24/W-25 新增；2026-11-01：W-23（运行产物移出版本控制）/W-24（模板化输出暂缓）关闭，统计 23/1/1 | 待办、backlog、治理队列 | 2026-11-01 | [已校验一致] |
| [analysis/DAG_visualization_analysis.md](./analysis/DAG_visualization_analysis.md) | DAG 节点图可视化模块分析报告 | 阶段2 节点图四层诊断：现状/P0-P2 问题清单/五项根因/影响评估/改进方向（R1-R6 优先级）+ "位置错乱与重叠"专项诊断（S1-S6，坐标四假设排查）；基线 4308a6d + offscreen 渲染实测 | 节点图、DAG、布局算法、交互 | 2026-09-18 | [已校验一致] |
| [user-manual.md](./user-manual.md) | User Manual — RPA 数据处理工具用户手册 | 面向无技术背景使用者的四步上手指南（选择数据/搭流程/运行/看结果）、常见错误自救表（与 error_messages 规则表同源）、注意事项与求助渠道；2026-10-24 按代码实况修正按钮名、进度状态与终止/放弃语义 | 用户手册、文员、四阶段、自救表 | 2026-10-24 | [已校验一致] |
| [deployment-guide.md](./deployment-guide.md) | Deployment Guide — RPA 数据处理工具部署指南（便携版） | 便携版约定（安装=复制、必须可写目录）、更新=替换 exe（原子发布、旧包移入 build/backup/、build 下五目录保护）、指纹核对方法、故障排查入口、环境要求；2026-10-24 修正运行目录为 4 个（backup 非运行目录）与指纹脚本执行位置 | 部署、便携版、更新、指纹、日志 | 2026-10-24 | [已校验一致] |
| [function-spec-rules.md](./function-spec-rules.md) | Function Spec Rules — 功能函数设计与变更规约 | 人工裁定的 4 条 [约束] 规定：三位一体（Python 函数/JSON 参数/GUI 节点）、双记录表同步与冲突裁定（以代码为准）、前端交互位置固化（右侧面板唯一入口＋添加弹层全量选项）、增删改变更顺序与 canonical 登记清单 13 项；含文档版功能函数记录表（10 项全字段）与 18 行待补强/待实施登记（16 项＋P 系列 2 行，backlog W-22，2026-10-19 R15 结清后关闭）；2026-10-19 R14 审计同步（四处"9"断言/基线 234/行号锚点刷新）；2026-10-24 R16 行号锚点再刷新 | 功能函数、三位一体、记录表、交互位置、变更顺序 | 2026-11-02 | [已校验一致] |

## 2. 实例层入口指针

> 实例层领域索引：[knowledge/INDEX.md](../knowledge/INDEX.md)；实例注册表：[knowledge/Instances-INDEX.md](../knowledge/Instances-INDEX.md) —— 本索引不列实例层明细。

## 3. 关键词/主题路由

Agent 按以下关键词/主题定位知识层目标文档：

| 关键词/主题 | 目标文档 |
|-------------|----------|
| 运行方式、模式判定、多 Agent 协作选择、降级 | agent-execution-mode.md |
| 架构、引擎、三段式、注册机制、数据流、参数文件 Schema、GUI 架构、GUI 生命周期、已知阻塞 | architecture.md |
| 编码规范、SQLite、Pandas、红线、Anti-Patterns、内存、异常处理、注释、docstring、print 调试输出 | dev-spec.md |
| 编译、打包、构建、PyInstaller、spec、exe、build.bat、输出路径 | build-guide.md |
| 遗留、v1、v2、冻结、迁移、复用 | legacy.md |
| 运行环境、硬件基线、Python 版本、依赖、WAL、conda、GBK | runtime-env-spec.md |
| 文档治理、元信息区、生命周期、校验机制、冲突解决、豁免、INDEX 维护 | doc-governance.md |
| 锚点机制、任务记录、任务追踪 | anchor-mechanism.md |
| 待办、backlog、W 编号、治理队列、已完成/已撤销登记 | backlog.md |
| 现状分析、问题诊断、专项诊断、可视化分析 | analysis/（知识层） |
| 用户手册、使用说明、四步上手、常见错误、自救表、注意事项 | user-manual.md |
| 部署、安装、更新、便携版、可写目录、指纹核对、BUILD_INFO、故障排查 | deployment-guide.md |
| 功能函数、用户操作、三位一体、双记录表、BUILTIN_OPS、STEP_CATALOG、新增操作、删除操作、变更顺序、登记清单 | function-spec-rules.md |
| 右侧面板、添加功能步骤、参数配置入口、参数表单、交互位置固化 | function-spec-rules.md §4 |
| 最高目标原则、文员可理解性、交互设计、界面禁用词表、用户视角 | architecture.md §8.4 |
| 架构刚性边界、ETL 不可偏离、允许与禁止的扩展方式 | architecture.md §10 |
| CLI 弃用、唯一交互入口 | dev-spec.md（GUI 条目索引）、backlog.md W-18 |

**标准路由流程**：`AGENTS.md → docs/INDEX.md → 目标文档`（运行方式判定首跳为 `AGENTS.md → docs/agent-execution-mode.md`；实施方案类文档经 `AGENTS.md → docs/plan/INDEX.md`）
