# AGENTS.md — V3 RPA 工作流引擎规约总纲

> 状态: 活跃 | 最后更新: 2026-11-01
> 所属层级：约束层（唯一载体，体系内最高权威）｜按 Project-Spec-build v2.2 §5.1 组织
> 锚点三层：[docs/anchor-mechanism.md](docs/anchor-mechanism.md)｜「当前任务锚点」｜docs/task-records/

## 1. 项目上下文

- **项目概述**：参数驱动的 ETL 框架；业务逻辑只在 JSON 参数文件（"引擎与业务逻辑分离"），引擎负责解析、调度、异常处理与资源清理。核心引擎与 GUI 四阶段页面已完成。**当前版本代际 v3.1（schema_version "3.1"）为全库唯一现行代号**。
- **业务域**：南方电网广电监 RPA —— ETL 数据处理（Excel 抽取 → SQL 聚合 → 模板化输出）
- **技术栈**：Python 3.11.15 / SQLite3(WAL) / pandas / PyQt5 等 [已校验一致]；完整清单见 [docs/runtime-env-spec.md](docs/runtime-env-spec.md)
- **团队规模**：单人开发 + AI Agent 协助
- **版本控制**：Git（remote=gitee，分支 `master`）[已校验一致]。**Git 写操作（提交/推送/分支/合并/回退等）一律人工接管，Agent 不执行**；仅在比对差异时用**只读** git（status/diff/show/log）。变更追溯以 docs/task-records/ 为主

## 2. 核心规则（红线）

### 2.1 核心原则

1. **ETL分层**：严禁直接对原始Excel频繁读写，必须 Extract → Transform → Load
2. **SQLite核心**：SQLite是中间数据载体和步骤间传递枢纽
3. **Pandas辅助**：SQLite负责重负载关联/聚合，Pandas仅负责复杂逻辑精加工
4. **模板化输出（暂缓）**：目标态为"预设模板 + 数据填充"，严禁代码硬编码样式；现行 `export` 为无模板流式直出，模板能力**暂缓**（W-24 已裁定，不阻塞交付）
5. **内存安全**：16GB 办公电脑，严格管控 Pandas 内存峰值
6. **最高目标原则**：目标用户为**无技术背景的企业文员**——一切交互必须从简、易懂；"用户交互指令 → 底层操作指令"的中间转换全部由程序代码完成，技术细节对用户完全隐藏、无需可见（细则见 [docs/architecture.md](docs/architecture.md) §8.4）

### 2.2 引擎级约束（不可违反）

1. 引擎禁止硬编码业务逻辑（具体SQL/路径/列名），业务逻辑只存在于JSON参数文件
2. JSON工作流定义文件是业务逻辑**唯一载体**
3. GUI 为**唯一交互入口**（程序不提供 CLI 交互）；GUI 只生成和编辑参数文件，不直接执行业务；引擎可被程序化调用、不依赖 GUI
4. 步骤不得自建 SQLite 连接，必须用引擎传入的共享连接（WAL）
5. 新增操作只在 `ops/` 实现并登记 `BUILTIN_OPS`，不改编排代码（v3 steps/ 已删除，见 architecture.md §3.4）
6. 禁止修改遗留部门脚本（`v2/` 各部门脚本保持独立）
7. 新开发必须用工作流引擎架构，禁止新建硬编码脚本
8. 步骤间经 SQLite 表名传递数据，禁止直接传 DataFrame
9. **ETL 架构刚性**：不得偏离或替换当前 ETL 架构（数据表驱动 + SQLite 中间层 + JSON 参数为业务逻辑唯一载体）——它是技术底座与功能基础；仅可在其内扩展（细则见 [docs/architecture.md](docs/architecture.md) §10；前端/后端界定：**前端=GUI交互层含DAG可视化、后端=ETL技术底层**，见 §8）

### 2.3 编码规范

红线摘要与完整规范见 [docs/dev-spec.md](docs/dev-spec.md)（经 §2.5 背书，[约束]）。

### 2.4 命名/分支/提交/审查约定

- **命名/分支/提交**：命名约定见 [docs/dev-spec.md](docs/dev-spec.md)；分支与提交同 §1（Agent 不执行 Git 写操作）。**审查**：规约变更必须执行全局更新校验（[docs/doc-governance.md](docs/doc-governance.md) §4）；源码变更以 §2 红线为基准

### 2.5 知识层细则约束力背书条款

以下 docs/ 细则经本文件显式引用，具 **[约束]** 效力（违反即为执行错误）；冲突时以本文件为准：

- [docs/agent-execution-mode.md](docs/agent-execution-mode.md)：运行方式判定与多 Agent 协作规范
- [docs/architecture.md](docs/architecture.md)：架构、参数文件 Schema、数据传递规则
- [docs/dev-spec.md](docs/dev-spec.md)：编码规范与 Anti-Patterns
- [docs/build-guide.md](docs/build-guide.md)：编译配置红线、重建流程、构建产物有效性判定
- [docs/legacy.md](docs/legacy.md)：遗留系统冻结与迁移边界
- [docs/doc-governance.md](docs/doc-governance.md)：文档治理细则与冲突解决豁免（§1~§10）
- [docs/anchor-mechanism.md](docs/anchor-mechanism.md)：锚点机制规定层
- [docs/function-spec-rules.md](docs/function-spec-rules.md)：功能函数三位一体、双记录表、交互位置固化与变更顺序

[docs/runtime-env-spec.md](docs/runtime-env-spec.md) 为环境通用知识，[参考]，不在背书清单内。

### 2.6 功能函数规约（指针）

功能函数＝三形态一体（`ops/` 函数／JSON `steps[]`／前端 DAG 节点）；四项 [约束] 见 [docs/function-spec-rules.md](docs/function-spec-rules.md)，增删改或 GUI 参数配置须先加载；**GUI 形态未经用户说明即硬停止**并列待确认清单。

## 3. 执行模式判定（强制首项）

**Agent 接到任何任务后、执行实际操作前，必须先确定运行方式**（硬性前置，不可跳过）：路由 → [docs/agent-execution-mode.md](docs/agent-execution-mode.md)（A/B/C/D 四种模式、选择标准、环境检测、降级策略与声明格式）。

### 3.1 多 Agent 协作规范（运行期）

4 项协作原则与分工架构见 [docs/agent-execution-mode.md](docs/agent-execution-mode.md) §6。

## 4. 文档体系路由

### 4.1 四层结构

| 层 | 载体 | 入口 | 职责 |
|----|------|------|------|
| 约束层 | `AGENTS.md`（唯一） | 本文件 | 上下文、核心规则、路由、模式判定、全局约束、目录边界、维护校验与锚点入口 |
| 知识层 | `docs/` | [docs/INDEX.md](docs/INDEX.md) | 描述"已存在的事实"：规范、架构、构建、环境、遗留、现状分析 |
| 方案态层 | `docs/plan/` | [docs/plan/INDEX.md](docs/plan/INDEX.md) | 描述"将要做的事"：计划、蓝图、里程碑；生命周期独立 |
| 实例层 | 自然位置 | [knowledge/Instances-INDEX.md](knowledge/Instances-INDEX.md) | 模块实现细节、使用/配置/执行指南 |

- **分层判定**：知识层答「现在是什么」，方案态层答「将来要做什么」。
- `docs/task-records/` 为锚点详情层（非知识文档）；实例散布自然位置不集中存放；`knowledge/INDEX.md` 为实例领域索引。

### 4.2 路由链路

- 知识层：AGENTS.md → [docs/INDEX.md](docs/INDEX.md) → 各知识文档；方案态层：→ [docs/plan/INDEX.md](docs/plan/INDEX.md)
- 实例层：→ [knowledge/INDEX.md](knowledge/INDEX.md) → [Instances-INDEX](knowledge/Instances-INDEX.md) → 实例文档；模式判定首跳：[agent-execution-mode.md](docs/agent-execution-mode.md)

### 4.3 关键词/主题路由

详细路由见各层 INDEX（禁止绕过）：[docs/INDEX.md](docs/INDEX.md) §3｜[docs/plan/INDEX.md](docs/plan/INDEX.md)｜[knowledge/INDEX.md](knowledge/INDEX.md)。

### 4.4 链接与 INDEX 规范

- 跨文档引用用**相对路径**、链接文本须描述性；INDEX 为**纯导航文件**（不得含规范条款或实质内容）；**渐进式加载**，每次仅加载最小文档集

### 4.5 约束力层级与标签

约束力层级：`AGENTS.md` ＞ `docs/` ＞ 实例文档，冲突时上层覆盖下层。四级约束力标签：

| 标签 | 适用范围 | 含义 |
|------|----------|------|
| `[约束]` | AGENTS.md 及 §2.5 背书细则 | 违反即为执行错误 |
| `[参考]` | docs/ 一般知识 | 应遵守；冲突以约束层为准 |
| `[自包含指令]` | 实例文档 | 正文自包含，不依赖跳转 |
| `[待裁定]` | 方案态层 | 未经人工裁定，**Agent 不得据此执行**；裁定后转 `[约束]`/`[参考]` 或删除 |

### 4.6 冲突解决

层级冲突以高层级为准并登记 `_temp/conflict-log.md`；四类冲突与豁免规则见 [docs/doc-governance.md](docs/doc-governance.md) §6。

### 4.7 可信度标签使用说明

六标签用于关键信息段落与决策、校验报告结论，**必须强制使用**（各标签的人工复核建议见 [docs/doc-governance.md](docs/doc-governance.md) §9）：

| 标签 | 含义 |
|------|------|
| `[已校验一致]` | 文档与实际代码/配置完全吻合 |
| `[存在差异]` | 文档与实际不一致，已按实际修正 |
| `[推测]` | 基于单一客观线索推测 |
| `[推断]` | 多处间接证据综合推断（≥2 且相互印证） |
| `[待补充]` | 无任何线索 |
| `[方案态]` | 描述未实现的目标方案，**不参与文档↔代码比对** |

## 5. 全局约束

### 5.1 行为约束

1. 本文件为规约总纲、唯一第一入口、最高权威；冲突按 §4.5/§4.6 处理
2. 执行任何操作前必读本文件并按 §3 确定运行方式
3. 文档查阅必须经路由（§4），禁止跳过索引
4. 渐进式加载，禁止全量加载规约体系
5. 规约文档变更后必须执行全局更新校验机制（[docs/doc-governance.md](docs/doc-governance.md) §4）
6. 管辖范围见 §6 子目录职责边界表；源代码、build/、运行时数据不管辖

### 5.2 内存安全基线

16GB 办公电脑，Pandas 峰值严格管控（红线 §2.1 条 5）；细则见 [docs/dev-spec.md](docs/dev-spec.md) §2.3、基线 [docs/runtime-env-spec.md](docs/runtime-env-spec.md) §1。

### 5.3 GUI 应用生命周期

四阶段循环（启动自检 → 输入数据选择 → 操作配置 → 运行追踪 → 结果报告 → 返回）规格见 [docs/architecture.md](docs/architecture.md) §8.0/§8.2。

### 5.4 已知阻塞

已知阻塞表见 [docs/architecture.md](docs/architecture.md) §9。

## 6. 子目录职责边界

| 顶层目录/文件 | 一句话职责 |
|---------------|-----------|
| `AGENTS.md` | 约束层唯一载体：规约总纲与任务锚点层 |
| `README.md` | 快速导航，仅同步展示，无约束力 |
| `docs/` | 知识层：通用知识细则 + task-records/ 任务记录 |
| `knowledge/` | 实例层索引与注册表 |
| `rpa_engine/` | 工作流引擎实现（详见 rpa_engine/README.md） |
| `Test/` | 端到端测试资源（暂缓，architecture.md §9 #4）；运行产物保留不删且不纳入版本控制（`v3/.gitignore`，W-07/W-23）；回归口径见 doc-governance §8 条 2 |
| `.trae/` `.zcode/` `build/` | 工具产物与编译产出，规约管辖外（前两者扫描排除） |
| `_temp/` | 校验中间产物、冲突登记、临时参考（无约束力） |

## 7. 维护与校验

### 7.1 变更操作核心条款

1. 任何规约文档变更后必须立即执行全局更新校验机制（[docs/doc-governance.md](docs/doc-governance.md) §4）
2. 已有内容必须保留（可移动/重组），信息不得丢失；过时内容标 `[已过时-待确认]` 而非删除

### 7.2 治理细则索引

治理细则十节见 [docs/doc-governance.md](docs/doc-governance.md) §1~§10（该文件各节标题即索引）。

### 7.3 任务执行锚点机制（摘要）

规定层全文见 [docs/anchor-mechanism.md](docs/anchor-mechanism.md)：任务定义（非临时目录写入/多 Agent/≥5 步）、三层结构（规定层/锚点层/详情层）、写入规则与迭代轮次均以该文件为准；规定层一经写入，非显式指令不得修改。

## 当前任务锚点

- **任务目标**：`_temp` 临时目录清理（目标已完成的中间产物）
- **任务状态**：`已完成`
- **轮次**：R18（_temp 清理轮；R17＝W-23/W-24 处置，已完成）
- **前序轮次**：R17（docs/task-records/2026-11-01-w23-w24-remediation.md）→ 本轮
- **开始时间**：2026-11-02
- **最后更新**：2026-11-02
- **要点摘要**：`_temp` 222→33 文件、3.86→1.11 MB；删 186 个（脚本/转储/提取图/未引用 verify/R16 快照/ImportData 过程产物）；保留项零断链；234 tests／双 smoke／自检／doc_verify 全绿；零源码/零构建
- **详情索引**：[docs/task-records/2026-11-02-temp-cleanup.md](docs/task-records/2026-11-02-temp-cleanup.md)

## 8. 当前任务上下文

**当前主线**：**R18 `_temp` 清理（11-02）已完成**：按「目标已完成 + 零引用 + 纯中间产物」判据删除 186 个文件，`_temp` 收敛为 3 目录 + 8 文件；保留项均有文档引用。

**上一轮**：R17 W-23/W-24 处置（11-01），见 [docs/task-records/2026-11-01-w23-w24-remediation.md](docs/task-records/2026-11-01-w23-w24-remediation.md)。

**待办**：W-25（tests docstring 随构建窗口）待人工；真机批与构建项仍人工；队列见 [docs/backlog.md](docs/backlog.md)。
