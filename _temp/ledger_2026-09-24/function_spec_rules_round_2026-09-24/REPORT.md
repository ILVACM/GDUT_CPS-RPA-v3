# R7 规约整理报告：功能函数设计规范固化到 Agent 规约

> **⚠ 归档注记（2026-09-24 R10）**：本文件为历史轮次快照，正文未改写。现位于 `_temp/ledger_2026-09-24/`；文中指向已清理 `_temp` 件（GUI 细节方案／M5 设计／审计报／审计方案／运行流程简报／repo-context／verify 留痕）的旧路径，其章节骨架与结论沉淀位置见同夹 `CLEANUP_MANIFEST.md` §2～§3，引用对账见 §5。

> 轮次：R7｜日期：2026-09-24｜性质：**规约整理，非实施**
> 依据：人工提示词（4 条规定）＋ `.trae/documents/功能函数设计规范固化到agent规约.md`（人工批准）
> SEM 路由：primary＝`ai-coding-governance`；secondary＝`documentation-lifecycle`
> 关联载体：`docs/function-spec-rules.md`（新规约专章）｜`docs/task-records/2026-09-24-function-spec-rules.md`｜AGENTS.md 锚点 R7

---

## ① 本轮任务理解与验收标准

**任务理解**：把人工裁定的 4 条功能函数设计规范写入 agent 规约，使后续任何 agent 一旦涉及功能函数操作即自动按规范执行；本轮属规约整理阶段，**不改代码、不改功能函数实现**，输出后停止等待人工指令。

**4 条规定**：①三位一体（后端 Python 函数／JSON 参数记录与格式规范／前端 GUI 设置界面，增删改必检三者；前两者 agent 可自行生成，GUI 部分必须由用户说明）②双记录表（代码版与文档版实时同步，冲突以代码为准）③前端交互位置固化（配置唯一入口＝"用户配置"阶段 DAG 右侧面板；"添加功能步骤"须显示全部选项且来源为记录表单一源）④变更工作流顺序（新增＝后端→记录表与 JSON 规范→前端；删除＝先查依赖再自适应；修改＝先定影响面再按后端→JSON→前端；动手前必须先列影响面、不得跳步）。

**验收标准（7 项）**：

| # | 标准 | 结果 |
|---|------|------|
| 1 | 4 条规定全部落地，且互相不冲突 | ✅ 落地于 `docs/function-spec-rules.md` §2/§3/§4/§5（含触发条件与判定依据） |
| 2 | 与既有红线不冲突（尤其 AGENTS §2.2 条 5） | ✅ 逐条对照见本报告 ④；1 项历史"张力"表述经审查修正为"一致（不触红线）" |
| 3 | 规约内章节引用、锚点、文件名引用全部正确 | ✅ `doc_verify` PASS（links=86，failures=0）＋审查子 agent 逐条核对 |
| 4 | 代码层缺口只登记为"待补强项/待实施项"，不实际改代码 | ✅ 16 项登记于专章 §7＋backlog W-22；`git status` 无任何 `.py` 变更 |
| 5 | AGENTS.md 容量合规（含 CR ≤8,000、余量 ≥200、纯 CRLF） | ✅ 7,798／余量 202／`loneCR=loneLF=0`（终版报告 `_temp/verify-20260924-1239.md`） |
| 6 | 知识层 INDEX 同步、无幽灵条目 | ✅ 13 篇 ↔ 磁盘一一对应；`binding: constraint` 8 篇 ＝ AGENTS §2.5 背书 8 条 |
| 7 | 回归零影响（证明未触代码） | ✅ `unittest discover -s tests` → **118 OK**（与 R6 终态一致） |

---

## ② 只读侦察摘要

### 2.1 规约体系现状（Spec Scout）

| 项 | 事实 |
|----|------|
| 四层结构 | 约束层 `AGENTS.md`（196→198 行）｜知识层 `docs/` 12 篇（本轮 +1＝13）｜方案态层 `docs/plan/` 1 篇｜详情层 `docs/task-records/` 44 条＋模板 |
| 容量硬约束 | 含 CR ≤8,000、余量 <200 须先下沉、禁压 §2.1/§2.2 红线本体、必须 CRLF（doc-governance §10）；本轮起点 7,774／余量 226 |
| 编号锁定 | doc-governance §4 Step 1 逐字点名 AGENTS §4.1/§4.2/§4.3/§4.5/§4.7/§5.1 条6/§6/§7.3；历史"编号零重排"，§7.4~§7.6 留空不复用 → 新章节只能取 **§2.6** 或 §9+ |
| 自动体检 | `tools/doc_verify.py` 三查（链接／INDEX 日期↔frontmatter／容量与行尾），常量 8000/200 |
| 落点规则 | 治理→doc-governance；架构与 Schema→architecture；编码→dev-spec；待办→backlog（W 编号唯一活载体）；`knowledge/` 不得承载规范细则；`_temp/` 无约束力 |

### 2.2 代码层功能函数登记结构（Registry Scout）

| 载体 | 位置 | 字段 |
|------|------|------|
| `BUILTIN_OPS`（引擎唯一源，9 项） | `ops/step_executor.py` L52-109 | `func`/`description`/`target_param`/`match_param`/`output`/`param_keys` |
| 薄再导出（真转发） | `engine/registry.py` L12-25 | R6/F3 已消双活副本 |
| `StepMeta`＋`STEP_CATALOG` | `gui/models.py` L32-93 | 8 字段（`_STEP_META_RAW` 为 **6 元组**，`icon`/`deprecated` 走默认值） |
| 三张平行表 | `gui/models.py` L176-177／L184-194／L216-226 | `OUTPUT_OPS`／`STEP_KIND`／`PRODUCE_LABEL` |
| 手写默认参数与输入基数 | `gui/models.py` L917-937／L897-914 | `default_params()` 9 分支、`extra_input_ids()` 硬编码 |
| 表单注册 | `gui/forms.py` L548-576 | `_FORM_CLASSES`（9）→ `_build_registry()` 以 `STEP_CATALOG` 键集过滤 |
| 启动自检守卫 | `gui/app.py` L47-243 | 6 项自检；注册表相关守卫 **15 条**（含守卫①②③＋F4） |

### 2.3 规定 3 的实现现状（Context Scout）

**结论：规定 3 在代码中已基本成立**，本轮为"把既有事实升格为 [约束] 条款＋补边界澄清"。

| 要点 | 现状 | 证据 |
|------|------|------|
| 配置只在右侧面板 | 成立（左图 6:右面板 4；三态面板；内联表单无弹窗） | `page_operation_config.py` L105-110／L313-452；`forms.py` L1-14 |
| 添加入口唯一 | 成立（顶栏 `QToolButton "添加功能步骤 ▾"` → `Qt.Popup` 弹层） | 同文件 L152-228 |
| 选项来源＝记录表单一源 | 成立（卡片按 `categories()`/`category_ops()` 渲染，文案只取 `StepMeta.display/desc`，注释明令禁硬编码） | 同文件 L184-228／L161-163 |
| 显示全部选项 | 成立（9 张卡片全显示，弃用项置灰标"（已停用）"、不隐藏） | 同文件 L216-238 |
| 其它位置不承担配置职责 | 成立（画布只读；阶段 1 表格＝数据表级；表态＝表级弃用；模板区＝配置存取）→ 已写入专章 §4.3 边界澄清表 | — |

### 2.4 既有同类约定（升格而非复制）

`_temp/DAG-rebuild/plan.md` §1.1 条 6"右面板为配置唯一入口、画布严格只读"；`_temp/W-03_GUI_detail_optimization_plan.md` §6.2 重命名兼容铁律（`key` 唯一稳定标识、改中文名只动 `display`）与四分类固定 → 均经专章升格为知识层 [约束]（`_temp/` 无约束力，仅作历史裁定出处）。

---

## ③ 4 条规定落点表（规定 → 文件 → 章节）

| 规定 | 主载体（全文） | AGENTS.md 指针 | 交叉引用落点 |
|------|----------------|----------------|--------------|
| 规定 1 三位一体 | `docs/function-spec-rules.md` §0（三形态定义）＋§2（规则本体／生成权限分级／§2.3 硬停止条款／§2.4 待确认清单模板） | §2.6 | `docs/dev-spec.md` GUI 条目索引节（编码侧适用声明） |
| 规定 2 双记录表 | 同文件 §3（§3.1 规则本体／§3.2 文档版记录表 9 行全字段＋5 条注记／§3.3 字段定义 8+2／§3.4 代码版载体清单 10 行／§3.5 同步规则与冲突裁定） | §2.6 | `docs/architecture.md` §6（声明专章 §3.2 为唯一载体、冲突以代码为准）；`docs/doc-governance.md` §7 新增触发④ |
| 规定 3 交互位置固化 | 同文件 §4（§4.1 规则本体 6 条／§4.2 实现口径 7 行／§4.3 边界澄清 3 行） | §2.6 | `docs/architecture.md` §8.2 阶段 2 行增 [约束] 注 |
| 规定 4 变更工作流顺序 | 同文件 §5（§5.1 前置铁律／§5.2 新增序／§5.3 删除序／§5.4 修改序＋key 稳定性铁律／§5.5 canonical 登记清单 13 项） | §2.6 | `docs/dev-spec.md`（编码侧顺序）；`docs/backlog.md` W-22（待补强项群） |
| 配套：与红线关系 | 同文件 §6（7 行对照表＋冲突裁定） | §2.2 条 5 原文零改动 | — |
| 配套：待补强登记 | 同文件 §7（18 行表＋治理登记句） | — | `docs/backlog.md` W-22 |
| 配套：校验与门禁 | 同文件 §8（6 项必跑清单） | — | — |

**AGENTS.md 变更明细**：§2.5 背书清单 +1 行（8 条）；新增 §2.6 指针（三形态＋四规则名＋加载义务＋GUI 硬停止）；锚点层改 R7；§8 主线更新。**§2.1/§2.2 红线本体零改动**。

**等量下沉 6 处**（doc-governance §10.2 要求；信息全部有接收方，无丢失）：

| # | 下沉/压缩处 | 信息去向 |
|---|-------------|----------|
| 1 | §4.7 六标签表第三列（人工复核建议） | `doc-governance.md` §9 新增"六可信度标签的人工复核建议"表（§4.7 保留标签与含义两列，Step 1 校验仍合规） |
| 2 | §7.2 治理细则十节名称列表 | `doc-governance.md` 各节标题即索引 |
| 3 | §4.6 冲突解决细则（README 无约束力、`_temp/` 仅临时参考） | `doc-governance.md` §6 条 1／条 3 已承载（原文核对相符） |
| 4 | §6 `Test/` 行豁免细节 | `doc-governance.md` §8 条 2 已承载（R6 事实校准条款） |
| 5 | §1 版本控制括注（`_temp` 快照 09-14 清理） | `doc-governance.md` §2 注已承载 |
| 6 | §7.3 三层结构/关键约束/迭代任务三 bullet 合二；§4.4 两 bullet 合一（与 §5.1 条 3/4 去重）；§5.2/§5.4/§8 措辞压缩 | 规定层 `anchor-mechanism.md` 全文；§5.1 条 3/4 原文保留 |

**容量轨迹**：7,774（起点／余量 226）→ 7,857（新增后／余量 143 ❌）→ 7,810（首轮下沉后／余量 190 ❌）→ 7,801（锚点收尾后／余量 199 ❌）→ **7,798（措辞微调后／余量 202 ✅）**；全程 `loneCR=loneLF=0`（每次编辑后 PowerShell 复固化 CRLF）。四次 doc_verify 留痕：`_temp/verify-20260924-1158.md`／`-1202.md`／`-1231.md`／`-1237.md`／`-1239.md`（终版）。

---

## ④ 与既有红线的冲突检查结果

| 专章条款 | 对应红线 | 结论 |
|----------|----------|------|
| §2 三位一体（后端在 `ops/` 实现） | AGENTS §2.2 条 5 | **细化**，不冲突 |
| §2.2 生成权限分级／§2.3 硬停止 | AGENTS §2.1 条 6 最高目标原则 | **更严**，合规细化 |
| §3 双记录表（冲突以代码为准） | §2.2 条 5；doc-governance §7 | **一致** |
| §4 交互位置固化（右侧面板唯一入口、内联表单、禁技术词） | §2.1 条 6；architecture §8.4 禁用词 | **细化** |
| §4.2 画布只读 | §2.1 条 6（出处＝`_temp` ADR-3 历史裁定，经专章升格） | **一致**；审查修正：原写"对应 architecture §10"，实核 §10.5 只界定"DAG 属前端、后端零改动"、**无画布只读条款** → 已改指 §2.1 条 6 |
| §5 变更顺序（共享 conn、禁自建连接） | §2.2 条 4 | **一致** |
| §5.5 项 3（`execute_step` 加分支） | §2.2 条 5"**不改编排代码**" | **一致（不触红线）**——审查修正：`architecture.md` §3.3 明文界定"编排代码＝`engine/`"，分发分支位于 `ops/step_executor.py`（§3.1 标题即"操作目录定义（ops/step_executor.py）"、§10.1 称 `BUILTIN_OPS` 为唯一扩展点）；历史 `_temp` 评估记为"张力"（`_temp/` 无约束力）已修正，P2-2 价值重述为可维护性收益。**如人工另有裁定，以裁定为准（待人工确认）** |

**结论**：无实质冲突；红线原文零改动；2 处定性表述经审查修正并留痕（§6 表内）。

---

## ⑤ 规约内引用与锚点自检结果

| # | 检查项 | 结果 |
|---|--------|------|
| 1 | `doc_verify.py`（链接可达／INDEX 日期↔frontmatter／AGENTS 容量与行尾） | ✅ **PASS**，links=86，failures=0（`_temp/verify-20260924-1231.md`） |
| 2 | 专章内部 § 交叉引用（§2.3/§2.4/§3.2~§3.5/§5.2~§5.5/§6/§7/§8 与 B/C/D/E/P 编号） | ✅ 审查子 agent 逐条核对，全部存在 |
| 3 | 外部引用（architecture §3.1/§3.3/§6/§8.4/§10、doc-governance §6/§7/§9/§10、backlog W-22、build-guide §1.7、`_temp` 四处来源、代码文件行号） | ✅ 全部可达；`_temp` 引用仅作历史裁定出处并已注明 |
| 4 | 反向引用成环 | ✅ INDEX（清单＋路由 2 行）、README、dev-spec、architecture（§3/§6/§8.2）、doc-governance §7 触发④、AGENTS §2.5/§2.6 均已指向专章 |
| 5 | AGENTS 锚点"详情索引"指向的 task-record 存在 | ✅ `docs/task-records/2026-09-24-function-spec-rules.md` |
| 6 | INDEX 13 篇 ↔ 磁盘一一对应；`binding: constraint` 篇数 ＝ §2.5 背书条数 | ✅ 8 ＝ 8 |
| 7 | 行号证据 | ⚠️ 审查发现 3 处漂移（`models.py` ±2 行、`step_executor` 分发区 L209-294、assessment L119-137）→ **已全部修正**；其余 20+ 处命中 |
| 8 | 记录表 9 行取值 ↔ 代码 | ✅ key／中文名／分类／`param_keys`／是否产表／表单类**逐格相符**；⚠️ 审查发现注记 1 的 `t_{uid}` 归属错误（实为 GUI 注入）与默认值双源未登记 → **已修正并新增 B9** |
| 9 | 环境侧提示 | ⚠️ 本次会话注入的 AGENTS.md 快照为 R6 旧版（§2.5 仅 7 篇、锚点仍为 R6）；磁盘实况已是 R7 新版。属注入缓存滞后，非文档缺陷——**建议人工确认注入刷新**，否则其他 agent 可能误判专章"未获背书" |

---

## ⑥ 待补强项 / 待实施项清单（16 项＋P 系列 5 编号，只登记不实施）

> 全文与行号证据见 `docs/function-spec-rules.md` §7；治理入口＝`docs/backlog.md` **W-22**（待人工裁定立项）。

| 类别 | 编号 | 一句话 | 优先 |
|------|------|--------|------|
| 弃用通路 | **B5** | `deprecated=True` 一启用即致启动自检失败（按钮并集校验用未过滤弃用的键集）→ 功能级弃用实际不可用 [推断] | 最高 |
| 双源缺口 | **B9** | 参数默认值双源：`default_params()`（GUI）vs `execute_step` `.get()` 回退（引擎），且 `mapping_match.mode`（left_join↔inner_join）与 `convert_dtype.from_type/to_type`（TEXT/INTEGER↔空串）**取值不同** | 高（R7 审查新发现） |
| 守卫缺口 | B1／B2／B3／B4／B6／B7／B8／E1 | 中文名双源无守卫／`STEP_KIND` 值域／`OUTPUT_OPS↔STEP_KIND` 等式／孤儿表单类反向／`keywords` 非空／白名单反向覆盖／前端键集中声明／守卫单测镜像仅 5/15 | 中 |
| 字段缺口 | C1／C2／D1／D2／D3／D4 | `icon` 休眠／`target_param`+`match_param` 休眠／无 `extra_min`／无 `params_schema`／无"可覆盖操作集"字段／弃用口径前后端不闭合 | 中 |
| 口径硬编码 | E3/A4 | "9 项"三处**等值断言**（`test_graph_edges.py` L200、`test_translation.py` L149、`smoke_m1m3.py` L188）新增第 10 项即红；`app.py` L108 为下限守卫（不失败） | 中 |
| 人工另行立项 | P1-1／P1-2／P1-6／P2-1／P2-2 | 功能函数专属单测缺失／失败·重试·取消·解析报错路径零测试／返回值契约未定（部分列失败仍报成功）／默认参数手写清单／分发 9 分支手写（承 R6 排除清单） | 待立项 |

---

## ⑦ 修订文件清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 创建 | `docs/function-spec-rules.md` | 核心交付物：§0~§9，binding: constraint |
| 创建 | `docs/task-records/2026-09-24-function-spec-rules.md` | R7 任务记录（含验收节） |
| 创建 | `_temp/ledger_2026-09-24/function_spec_rules_round_2026-09-24/REPORT.md` | 本报告 |
| 创建 | `.trae/documents/功能函数设计规范固化到agent规约.md` | 执行计划（人工批准，Plan Mode 产物） |
| 修改 | `AGENTS.md` | §2.5 背书 +1 行（7→8）；新增 §2.6 指针；6 处等量下沉；锚点 R7；§8 主线更新；红线本体零改动；容量 7,774→7,800（余量 200） |
| 修改 | `docs/INDEX.md` | 清单 +1 行；路由 +2 行；篇数 12→13；dev-spec/backlog 日期同步；frontmatter |
| 修改 | `docs/architecture.md` | §3/§6/§8.2 增 [约束] 交叉引用；**A1 修正**（参数白名单为执行期过滤，非 validate 阶段）；**A2 修正**（`target_param`/`match_param` 休眠、`param_keys` 执行期语义）；frontmatter confidence |
| 修改 | `docs/dev-spec.md` | GUI 条目索引节增 [约束] 交叉引用；变更记录 +1 行；frontmatter 日期 |
| 修改 | `docs/doc-governance.md` | §7 增触发④（功能函数变更→同步专章 §3.2）＋收尾清单 ①②③④；§9 接收六标签复核建议表 |
| 修改 | `docs/backlog.md` | 新增 W-22（16 项）；§5 统计 待指令 1→2＋W-22 说明；frontmatter |
| 修改 | `README.md` | 篇数 12→13；开发者/Agent 导航行；R7 状态速览 1 条 |
| 生成 | `_temp/verify-20260924-1158.md`／`-1202.md`／`-1231.md` | doc_verify 三次留痕（143→190→200 余量轨迹） |
| **零改动** | `rpa_engine/**`（含 `tests/`、`tools/`）、`_temp/DAG-rebuild/**`、`build.bat`、`build/**`、依赖文件、任何 `.db` | 见 ⑧ 声明 |

---

## ⑧ 声明

1. **本轮未修改任何代码**：`rpa_engine/**` 下所有 `.py`、`tests/**`、`tools/**`、`_temp/DAG-rebuild/**`（含冻结基线 `SampleCode/`）零改动；`git --no-optional-locks status --porcelain -- "*.py" "*.spec" "rpa_engine"` 输出**无任何 `.py`／`.spec` 变更条目**。如实披露：该命令列出 3 个未跟踪文件 `rpa_engine/temp/input_selection/{dup_36,dup_37,other_18}.xlsx`——系**本轮运行回归套件时产生的运行期临时副本**（非代码、非本轮编辑），位于 `AGENTS.md` §6 明示"temp/ 运行产物保留不删"的豁免目录，按规约保留不清理。
2. **规约文件是唯一写入范围**：写入面＝`AGENTS.md`＋`docs/**`（6 篇）＋`README.md`＋`docs/task-records/`＋`_temp/`（本报告与 doc_verify 留痕）。未安装依赖、未启动服务、未执行 git 写操作、未写 SQLite、未生成或覆盖构建产物。
3. **回归零影响**：`python -m unittest discover -s tests`（cwd=`rpa_engine`，conda `CPS-GPES_RPA-py311`）→ **Ran 118 tests OK**，与 R6 终态一致，反证未触代码。
4. **多 agent 分工**：3 个只读侦察子 agent（Spec Scout／Registry Scout／Context Scout，并发）＋1 个只读一致性审查子 agent（Consistency Reviewer）；主 agent 为唯一写入方并承担 Rule Designer 角色（理由：子 agent 返回预算 ≤2K tokens 装不下完整专章草案，且用户规定仅主 agent 写规约文件）。子 agent 全程零写入、未创建临时共享文件。
5. **待人工确认 1 项**：§6 关于"`execute_step` 加分支是否属红线'编排代码'"的定性——本轮依 `architecture.md` §3.3 的明文界定（编排代码＝`engine/`）修正为"不触红线"；如人工另有裁定，以裁定为准。
6. **当前等待人工下一步指令**，不进入实施阶段（不新增/修改/删除任何功能函数，不实施 W-22 任一项）。
