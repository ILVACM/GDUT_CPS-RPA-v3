# 任务记录：功能函数记录表单源化与 W-22／N 系列结清

## 摘要
- **任务目标**：按 `.trae/documents/backlog-remediation-control-pack.md` 结清 B-45~B-79（35 项）＋ F4（＝B-41）＋ F5
- **任务状态**：`已完成（2026-10-19）`
- **开始时间**：2026-10-19
- **最后更新**：2026-10-19
- **要点摘要**：批 A 结账口径 → 批 B 守卫与常量 → 批 C 记录表单源化（核心）→ 批 D 环境依赖；真机/构建项登记受控例外
- **操作人**：黄泊凯

## 用户输入

> 对于上面所有提到的问题，你自适应制定方案（决策点全部采用你的推荐），然后在人工确认后执行修改，不要有遗留。

（方案经人工批准：`.trae/documents/backlog-remediation-control-pack.md`）

## Agent 理解与决策

- 范围＝35 项 B-45~B-79 ＋ F4 ＋ F5；「不要有遗留」解释为**每项有明确处置与责任方**，Agent 不可执行项（构建/真机）以受控例外登记
- 核心设计＝**唯一源 `BUILTIN_OPS.params_schema`**：引擎与界面同源，闭合 F4／B-41／B-64／B-69
- 红线④（零新依赖／无 pickle、eval、exec／相对路径）硬遵守；红线①（`engine/executor.py`）本批不动，列例外

## 执行流程

### 流程概览
- 总步骤数：6（前置 ＋ 批 A~D ＋ 收尾）
- 多 Agent 协作：否（批内串行改文件）

### 步骤记录

#### Step 1: 前置（快照＋锚点＋任务记录）
- 状态：✅ 已完成
- 执行内容：13 个待改文件快照至 `_temp/ImportData/backup/R15/`；AGENTS 锚点登记为 R15；新建本任务记录
- 涉及文件：`_temp/ImportData/backup/R15/`（13 个）、`AGENTS.md`、本文件

#### Step 2: 批 A · 结账与口径（零代码）
- 状态：✅ 已完成
- 执行内容：① `docs/function-spec-rules.md` §7 新增「R15 处置」列（18 行逐行处置）＋ R15 结清统计；§3.2 注记 4 审计注记**转正**（划除失效陈述）；② `docs/backlog.md` W-22 → 🟡 执行中 ＋ R15 执行说明 ＋ §5 统计更新（待指令 2→1）；③ `_temp/ImportData/plan.md` 台账后追加《R15 处置表》（39 行，**台账原文一字未改**）；④ AGENTS 锚点 §8 更新
- 涉及文件：`docs/function-spec-rules.md`、`docs/backlog.md`、`_temp/ImportData/plan.md`、`AGENTS.md`
- 门禁：`doc_verify PASS (links=86, failures=0)`
- 决策记录：台账「本批处置」以**加法式独立表**实现（等价于加列，但零改动 79 行原文），合 `AGENTS.md` §7.1

#### Step 3: 批 B · 守卫与口径常量
- 状态：✅ 已完成
- 执行内容：
  - `gui/models.py`：新增 `STEP_COUNT`（＝`len(STEP_CATALOG)`，B-67/B-68 单一源）、`OUTPUT_MODE_KEY`/`OUTPUT_MODE_NEW`/`OUTPUT_MODE_OVERWRITE`（B-60）、`STEP_KINDS` 值域（B-55）；`classify_step` 增值域校验（非法值报错）；`output_mode` 5 处生产引用改常量
  - `gui/app.py`：自检 4b 增 `STEP_KIND` 值域校验（B-55）与 `keywords` 非空守卫（B-58）；下限守卫与文案改引用 `STEP_COUNT`
  - `gui/forms.py`：`output_mode` 选项/默认值/输出键改引用常量（B-60，4 处）
  - `gui/page_input_selection.py`：合并单元格填充提示补「预览为原始形态、填充仅导入时生效」（B-79）
  - `ops/exporter.py`：后缀非 `.xlsx` **抛中文 `ValueError`**（B-49）
  - 测试：四处「9」断言改 `STEP_COUNT`（`test_graph_edges`/`test_translation`/`test_ops_contracts`/`smoke_m1m3`）；**新建 `tests/test_registry_guards.py`**（20 用例：B-54/55/56/57/58/66＋B-67）；`test_ops_contracts` 导出后缀用例按新契约改写（旧「静默改写」断言废止）
- 门禁：`Ran 213 tests — OK`（191→213，+22）｜双 `SMOKE_ALL_OK`｜自检 `ok=True`（6/6）
- 决策记录：**B-59 顺延至批 C**（其判据「`param_keys` ⊇ 契约键」需 `params_schema` 先落地，与批 C 同批更自然）——记 `[ADJUSTED]`

#### Step 4: 批 C · 记录表单源化（核心）
- 状态：✅ 已完成
- 执行内容：
  - `ops/step_executor.py`：`BUILTIN_OPS` 9 条目改 **8 字段集**（新增 `params_schema`／`extra_input_min`／`overwritable`／`deprecated`；**删除** `target_param`／`match_param`）＋新增 `GUI_INJECTED_PARAM_KEYS`／`param_schema()`／`param_default()`／`param_defaults()`；`execute_step` 全部分支缺省回退**改取 schema**（B-41：`mode`→`left_join`、`from_type/to_type`→`TEXT`/`INTEGER`）
  - `gui/models.py`：`StepMeta` **删除 `icon`**；`default_params()` 改为派生自引擎 `param_defaults`（不再手写，B-69）
  - `gui/forms.py`：`_is_overwritable()`（读引擎声明）驱动 `output_mode` 挂载（B-65）；filter／dedup 两表单 `get_params` 支持未挂载分支
  - `engine/validator.py`：已弃用 type **拒绝执行**（B-53）
  - `ops/exporter.py`：`Workbook(write_only=True)`＋`WriteOnlyCell` 保 `number_format`（B-03）；L9-11 注释更正（B-76）
  - 测试：**新建 `tests/test_registry_single_source.py`**（16 用例：三方一致／引擎回退≡schema／left_join 行为／convert_dtype 缺省成功／`extra_input_min`／`overwritable`／弃用拒绝／导出 write_only 日期格式回归）
- 门禁：`Ran 229 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`
- 决策记录：B-03 **未触发降级预案**——导出日期格式逐格等价验证通过（`yyyy-mm-dd`／`yyyy-mm-dd hh:mm:ss` 均保留），故按完整实现落地（`write_only` 已落地 ⇒ B-76 注释成立）

#### Step 5: 批 D · 环境与依赖
- 状态：✅ 已完成
- 执行内容：① 生成 `requirements.lock`（51 行：15 行抬头 ＋ 36 行 `pip freeze` 原样；抬头含**废弃包告警**，B-50/B-71/B-72）；② `requirements.txt`：`pandas>=2.0,<4`＋`PyQt5>=5.15,<6` 上界，回写实测版本（pandas 3.0.5／PyQt5 5.15.11／openpyxl 3.1.5／xlrd 2.0.2／loguru 0.7.3／psutil 7.2.2，B-74）；③ **新建 `tests/test_dependency_contract.py`**（5 用例：生产 import ⊆ 标准库∪本仓库∪requirements∪spec hiddenimports；A-17 回归；lock 含 pandas，B-52）；④ **B-73 核验通过零改动**——全库复扫**零** `CPS-GPES-RPA-py311`（连字符）形式，命令清单已是正确下划线口径
- 门禁：`Ran 234 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS`

#### Step 6: 文档同步与收尾
- 状态：✅ 已完成
- 执行内容：`docs/function-spec-rules.md`（§3.2 注记 3/4/5 改写／§3.3 字段载体／§3.4 载体清单＋行号／§5.5 项 2/4/8/9/13／§7 R15 处置列＋结清统计／§8 基线 234／§9 R15 变更行／frontmatter）；`docs/architecture.md`（§3.1 字段表改 8 字段集／frontmatter）；`docs/backlog.md`（W-22 🟡 执行中＋R15 说明＋统计）；`docs/INDEX.md`（architecture／function-spec-rules／runtime-env-spec 三行日期与摘要同步）；`docs/runtime-env-spec.md`（§3 依赖基线回写实测版本＋废弃包说明＋lock 指针／frontmatter）；`_temp/ImportData/plan.md`（《R15 处置表》）；`AGENTS.md`（锚点 R15 已完成／§8／行尾 CRLF）
- 决策记录：root `README.md` L47 与 `docs/task-records/2026-09-24-*.md` 中提及 `target_param`／`match_param` 者**不改**——属**历史变更记录**（记录当时实况），非当前事实陈述；`rpa_engine/README.md` forms 说明行未含休眠字段，无需改

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 新建 | `_temp/ImportData/backup/R15/` | 批前快照（13 文件，回滚点） |
| 新建 | `docs/task-records/2026-10-19-w22-n-remediation.md` | 本文件 |
| 修改 | `rpa_engine/ops/step_executor.py` | 8 字段集＋`params_schema` 唯一源＋派生辅助＋分支回退改取 schema（B-41/B-62/B-63/B-64/B-65/B-53） |
| 修改 | `rpa_engine/gui/models.py` | `STEP_COUNT`／`OUTPUT_MODE_*`／`STEP_KINDS`；`classify_step` 值域；删 `icon`；`default_params` 派生；`output_mode` 5 处改常量（B-55/B-60/B-61/B-69） |
| 修改 | `rpa_engine/gui/app.py` | 自检增 `STEP_KIND` 值域＋`keywords` 非空；下限守卫与文案引用 `STEP_COUNT`（B-55/B-58/B-67） |
| 修改 | `rpa_engine/gui/forms.py` | `_is_overwritable()`＋挂载改由引擎声明驱动；`output_mode` 常量引用（B-60/B-65） |
| 修改 | `rpa_engine/gui/page_input_selection.py` | 预览摘要补「填充仅在导入时生效」（B-79） |
| 修改 | `rpa_engine/ops/exporter.py` | 后缀非 `.xlsx` 报错（B-49）；`write_only` 导出（B-03）；抬头注释更正（B-76） |
| 修改 | `rpa_engine/engine/validator.py` | 已弃用 type 拒绝（B-53） |
| 修改 | `rpa_engine/tests/test_graph_edges.py`／`test_translation.py`／`test_ops_contracts.py`／`tools/smoke/smoke_m1m3.py` | 四处「9」断言改引用 `STEP_COUNT`；导出后缀用例按新契约改写（B-67） |
| 新建 | `rpa_engine/tests/test_registry_guards.py` | 守卫镜像 20 用例（B-54/B-55/B-56/B-57/B-58/B-66/B-67） |
| 新建 | `rpa_engine/tests/test_registry_single_source.py` | 单一源 16 用例（B-41/B-59/B-63/B-64/B-65/B-69/B-53/B-03/B-76） |
| 新建 | `rpa_engine/tests/test_dependency_contract.py` | 依赖交叉校验 5 用例（B-52/B-50/B-71/B-72） |
| 新建 | `requirements.lock` | 实测版本锁定＋废弃包告警（B-50/B-71/B-72/B-74） |
| 修改 | `requirements.txt` | 上界＋实测版本回写（B-74） |
| 修改 | `docs/function-spec-rules.md` | §3.2/§3.3/§3.4/§5.5/§7/§8/§9＋frontmatter 全面同步 |
| 修改 | `docs/architecture.md` | §3.1 字段表 8 字段集＋frontmatter |
| 修改 | `docs/backlog.md` | W-22 状态与说明＋统计 |
| 修改 | `docs/INDEX.md` | 三行日期/摘要同步（doc_verify 门禁强制） |
| 修改 | `docs/runtime-env-spec.md` | §3 依赖基线＋frontmatter |
| 修改 | `AGENTS.md` | 锚点 R15＋§8＋行尾归一 |
| 修改 | `_temp/ImportData/plan.md` | 《R15 处置表》（台账原文零改动） |

## 关闭标识
- **完成时间**：2026-10-19
- **最终状态**：✅ 全部完成（批 A~D 落地；W-22 结清；门禁全绿；真机/构建项以受控例外登记）
- **关闭说明**：功能函数参数契约已收敛为引擎单一源（`params_schema`），原四处双源与「开箱即不一致」的行为差异消除；B-45~B-79 中 Agent 可执行项全部办结，不可执行项（`build.bat`／`engine/executor.py` 运行域／真机断言）在 `docs/function-spec-rules.md` §7 与 `_temp/ImportData/plan.md`《R15 处置表》中带**责任方与触发条件**登记，无悬空项。**git 提交由人工接管**。
