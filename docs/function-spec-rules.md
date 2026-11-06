---
title: Function Spec Rules — 功能函数设计与变更规约
type: knowledge
scope: global
status: active
owner: 黄泊凯
last-updated: 2026-11-02
tags: [功能函数, 三位一体, 记录表, 交互位置, 变更顺序]
binding: constraint
confidence: 已校验一致（4 条规定为 2026-09-24 人工裁定；§3.2 记录表 9 行主字段逐格核对代码实况；R7 一致性审查发现的 5 项高优先偏差与 5 项口径问题已于同轮全部修正——含 t_{uid} 归属、默认值双源 B9、_STEP_META_RAW 6 元组、三处"9"等值断言、spec hiddenimports 落点、"不改编排代码"界定对齐 architecture §3.3；修正明细见 `_temp/ledger_2026-09-24/function_spec_rules_round_2026-09-24/REPORT.md` §5；2026-10-19 R14 审计同步：行号锚点与"9"断言口径（三处→四处）按代码实况刷新、§8 基线 118→191（**历史值**，2026-10-24 实测 234），逐项实测 [已校验一致]；2026-10-19 R15 结清：§7 18 行中 15 行闭合＋1 行（B5）确认已解决，B9／D2／P2-1 由 `params_schema` 单一源化闭合、D4 由 validator 弃用校验闭合、B1/B2/B3/B4/B6/B7/B8/C1/C2/D1/D3/E1/E3-A4 由守单测与常量收敛闭合，§3.2 注记 3/4/5 与 §3.3/§3.4/§5.5 同步改写，§8 基线 191→234（2026-10-24 实测 234），全部逐项实测 [已校验一致]，见 docs/task-records/2026-10-19-w22-n-remediation.md；2026-10-24 R16 行号锚点刷新（models/forms/step_executor 实测），规则条文零改动，§8 基线 234 不变）
content-revision: 2026-10-24
---

# Function Spec Rules — 功能函数设计与变更规约

> 所属层级：知识层（docs/），经 [AGENTS.md](../AGENTS.md) §2.5 背书具 **[约束]** 效力（违反即为执行错误）；与 `AGENTS.md` 冲突时以 `AGENTS.md` 为准。上位红线见 `AGENTS.md` §2.2 条 5（新增操作只在 `ops/` 实现并登记 `BUILTIN_OPS`，不改编排代码）。
> 适用范围：**功能函数**（＝用户操作／步骤类型，如"条件筛选""结果导出"）的新增、删除、修改、审计，以及任何涉及 GUI 参数配置界面的变更。
> 本轮说明：2026-09-24 R7 规约整理轮新建。4 条规定由人工裁定；§7 代码层缺口**只登记不实施**，本轮零代码改动。

## 0. 前提与概念（三位一体的三种形态）

一个功能函数在系统中同时以三种形态存在，三者是**同一事物的完整存在形态**，不是三个独立功能：

| 形态 | 载体 | 作用 |
|------|------|------|
| ① 后端 | 一个 Python 函数（或类方法），位于 `rpa_engine/ops/` | 真正执行数据处理 |
| ② 参数 | JSON 运行参数文件 `steps[]` 数组中的一个元素（含参数格式规范） | 业务逻辑唯一载体（`AGENTS.md` §2.2 条 2）；前端配置据此无损转译 |
| ③ 前端 | GUI"用户配置"阶段 DAG 可视化中的一个步骤节点（＋右侧面板参数表单） | 用户便捷设置参数，由程序转译为 ② 的 JSON 元素 |

**术语对齐**：本文件"功能函数"＝代码中的"用户操作"／"步骤类型"／`BUILTIN_OPS` 的一个键＝GUI 中的"功能步骤"。四分类固定为：筛选类／关联统计类／表结构类／输出类。

## 1. 触发条件与加载义务

**命中以下任一场景，agent 必须先加载本文件再动手**（不得凭记忆或臆测执行）：

1. 新增、删除、修改任一功能函数；
2. 改动下列任一载体：`BUILTIN_OPS`、`STEP_CATALOG`（`_STEP_META_RAW`）、`_FORM_CLASSES`、`default_params()`、`extra_input_ids()`、`STEP_KIND`、`OUTPUT_OPS`、`PRODUCE_LABEL`；
3. 改动"用户配置"阶段右侧参数面板、"添加功能步骤"弹层、参数表单类；
4. 编写或修改功能函数相关测试（含注册表一致性用例、smoke 卡片数断言）；
5. 对功能函数做审计、评估、重构或口径核对；
6. 变更 JSON 运行参数文件的参数格式规范（新增/改名/删除参数键）。

**判定依据优先级**（本文件全域适用）：`AGENTS.md` 红线 ＞ 本文件 ＞ 代码实况 ＞ 文档版记录表 ＞ `_temp/` 历史方案。涉及"事实是什么"一律**以代码为准**（见 §3.5）；涉及"GUI 该长什么样"一律**以用户说明为准**（见 §2.3）。

## 2. 规定 1：三位一体规则

### 2.1 规则本体

1. 任一功能函数由三部分组成，**三者是一个整体**：
   - a) 后端 Python 功能函数代码；
   - b) JSON 运行参数文件中的参数记录及对应格式规范（前端才能无损转译用户配置）；
   - c) 前端 GUI 交互中的设置界面（用户才能便捷设置参数，并由程序转译为 b) 的 JSON 元素）。
2. 对任一功能函数的**增／删／改，必须同时检查 a)、b)、c) 三者，缺一不可**。
3. 只改其一即视为变更未完成，不得声明任务闭环。

### 2.2 生成权限分级

| 部分 | agent 可否自行生成 | 条件 |
|------|-------------------|------|
| a) Python 代码 | **可** | 需求描述无歧义（输入表/输出表/参数语义/失败行为已明确） |
| b) JSON 参数记录与格式规范 | **可** | 同上；且参数键须与 `param_keys` 白名单一致（见 §3.3） |
| c) 前端 GUI 交互界面 | **不可** | **必须由用户额外说明**（不说明则 agent 容易胡乱发挥） |

### 2.3 GUI 缺说明时的硬停止条款

**触发条件**：任务涉及新增/修改功能函数，且用户未说明该功能在右侧面板的交互形态。

**agent 必须执行的动作**（三项，缺一不可）：

1. **立即停止**：不得改动任何 GUI 代码（`rpa_engine/gui/**`），不得以"参照同类既有表单"为由臆测实现；
2. **输出《GUI 待确认清单》**，逐项列明待用户裁定的内容（模板见 §2.4）；
3. **等待用户说明**后再继续；用户明确授权"按同类既有表单模式实现"时，须在任务记录中留痕该授权原文。

**已完成部分的处理**：a)、b) 若已按无歧义描述完成，可保留并如实报告"后端与参数规范已就绪，GUI 待用户说明"，不得连带猜测 c)。

### 2.4 《GUI 待确认清单》模板

```
功能 key：<英文稳定标识>
中文名（拟）：<面向文员的名称，须过 architecture.md §8.4 禁用词口径>
所属分类：筛选类 / 关联统计类 / 表结构类 / 输出类
是否产生新数据表：是 / 否
右侧面板需展示的参数项（逐项）：
  1. 参数名｜人话标签｜输入形式（下拉 / 勾选 / 文本 / 文件浏览 / 逐行键值 / 多选列表）
     ｜可选项来源｜是否允许为空｜默认值
  2. ……
错误提示话术：<参数不合法时给用户看的人话，禁止技术术语>
"添加功能步骤"弹层：显示位置（分类）｜卡片副标题一句话说明｜搜索关键词
其它交互要求：<二次确认、置灰条件、联动等>
```

## 3. 规定 2：双记录表规则

### 3.1 规则本体

1. **代码版记录表**与**文档版记录表**必须各存一份，且**实时同步一致**。
2. 两者冲突时，**以代码为准**（裁定规则见 §3.5）。
3. 代码版是**强制性实现与约束**（注册表＋启动自检断言＋测试用例落地，漂移即启动失败或门禁红）。
4. 文档版（§3.2）供人类与 agent 快速查阅，不得作为实现依据单独引用。

### 3.2 文档版功能函数记录表（10 项，取值核对日期 2026-11-02）

| key | 中文名 | 分类 | 输入 | 输出 | 参数 schema（`param_keys`／默认值） | 是否产表 | 是否可弃用 | GUI 表单类 |
|-----|--------|------|------|------|-------------------------------------|----------|------------|------------|
| `filter` | 条件筛选 | 筛选类 | 单表 | 新表 | `conditions`,`logic`,`output_table` ／ `conditions=[]`,`logic="AND"` | 是 | 否 | `FilterForm` |
| `dedup` | 条件去重 | 筛选类 | 单表 | 新表 | `key_columns`,`keep`,`output_table` ／ `key_columns=[]`,`keep="first"` | 是 | 否 | `DedupForm` |
| `mapping_match` | 跨表映射匹配 | 关联统计类 | 主表＋匹配表（2 张） | 新表 | `match_table_id`,`match_columns`,`mode`,`output_table` ／ `match_table_id=""`,`match_columns={}`,`mode="left_join"` | 是 | 否 | `MappingMatchForm` |
| `aggregate` | 条件统计 | 关联统计类 | 单表 | 新表 | `group_by`,`metrics`,`conditions`,`output_table` ／ `group_by=[]`,`metrics=[]`,`conditions=[]` | 是 | 否 | `AggregateForm` |
| `merge_tables` | 数据表合并 | 关联统计类 | 多表（≥2） | 新表 | `match_table_ids`,`output_table` ／ `match_table_ids=[]` | 是 | 否 | `MergeTablesForm` |
| `copy_table` | 数据表复制 | 表结构类 | 单表 | 复制新表 | `output_table` ／ 无业务默认参数（`{}`） | 是 | 否 | `CopyTableForm` |
| `rename_columns` | 表头名称修改 | 表结构类 | 单表（原地） | 无新表 | `mapping` ／ `mapping={}` | 否 | 否 | `RenameColumnsForm` |
| `convert_dtype` | 数据类型转换 | 表结构类 | 单表（原地） | 无新表 | `column`,`from_type`,`to_type` ／ `column=""`,`from_type="TEXT"`,`to_type="INTEGER"` | 否 | 否 | `ConvertDtypeForm` |
| `export` | 结果导出 | 输出类 | 单表（终点，`STEP_KIND=end`） | 无新表（写 Excel 文件） | `output_path`,`sheet_name` ／ `output_path=""`,`sheet_name="数据"` | 否 | 否 | `ExportForm` |
| `supervision_report` | 履职表单抽查报告 | 输出类 | 1～N 张同格式表（`extra_table_ids` 可选） | 无新表（写 xlsx 3 sheet ＋ txt） | `output_path`,`workday_count`,`extra_table_ids` ／ `output_path=""`,`workday_count=0`,`extra_table_ids=[]` | 否 | 否 | `SupervisionReportForm` |

**表下注记（5 条，均为代码实况）**：

1. `output_table` 属**GUI 注入键**：前端表单不填、用户不可见；产表操作的物理表名由 `models.to_dict()` 固化为 `t_{uid}`（`rpa_engine/gui/models.py` L742-761，仅业务口径写入、编辑态 pop）。**引擎只消费不生成**：缺省回退为 `t_s{n}`（`rpa_engine/ops/step_executor.py` L312），该回退仅对外部手写 JSON 生效。
2. `output_mode` 属**前端键**（不在任何 `param_keys` 内），挂载由**引擎声明** `BUILTIN_OPS[k]["overwritable"]` 决定（R15/B-65；现网 `filter`／`dedup` 两项为真）；键名与取值引用 `gui.models` 集中常量（R15/B-60）。业务口径导出时由 `models.to_dict()` 翻译为"覆盖两步链"并剔除该键，编辑态口径保留。
3. **参数默认值口径＝引擎 `BUILTIN_OPS[k]["params_schema"]`（唯一源）**；GUI 侧 `default_params()` 与引擎侧 `execute_step` 的缺省回退**均派生于此**（R15/B-41＋B-64＋B-69 单一源化，原"GUI `left_join` ↔ 引擎 `inner_join`"与"GUI `TEXT`/`INTEGER` ↔ 引擎 空串"两处差异已消除）。手写 JSON 省略参数键时行为与界面**一致**。
4. "是否可弃用"现网 9 项全为 `否`（`StepMeta.deprecated` 与 `BUILTIN_OPS[k]["deprecated"]` 双端均为 `False`）；弃用机制**已可用**——GUI 侧由 B-13（R12）修复按钮并集口径（`gui/app.py` L186-192 ＋ `test_deprecated_self_check_passes` 回归保护），引擎侧由 R15/B-53 交付（`engine/validator.py` 拒绝已弃用 type，闭合"手写 JSON 仍可执行已弃用操作"缺口）。原"一启用即致自检失败"陈述**已失效**（见 §7 B5「已解决」）。
5. 引擎侧 `description` 与 GUI 侧 `display` 现网逐字相同，**已加守卫单测**（R15/B-54）；原 `StepMeta.icon` 与 `target_param`／`match_param` 三处休眠字段已按 R15 裁定**删除**（零消费者；"启用为字段驱动"与 P2-2 裁定冲突）。

### 3.3 记录表字段定义（8 必备字段＋2 补充字段）

| 字段 | 含义 | 取值口径 | 代码版载体 |
|------|------|----------|-----------|
| 功能 key | 唯一稳定标识 | 英文小写下划线；**改名只动中文名，key 永不变**（JSON `steps[].type`、`BUILTIN_OPS`、`_FORM_CLASSES`、三张平行表全以 key 为准） | `StepMeta.key`；`BUILTIN_OPS` 键 |
| 中文名 | 面向文员的显示名 | 须过 `architecture.md` §8.4 禁用词口径（禁 SQL/表名/列名/JSON/SQLite/节点/端口等） | `StepMeta.display`；`BUILTIN_OPS[k]["description"]`（双源，§7 B1） |
| 分类 | 弹层分组归属 | 四分类固定：筛选类／关联统计类／表结构类／输出类 | `StepMeta.category` |
| 输入 | 需要的输入数据表基数 | 单表／主表＋匹配表／多表（≥2） | `extra_input_ids()`（取实际输入）；**基数契约**＝`BUILTIN_OPS[k]["extra_input_min"]`（R15/B-63） |
| 输出 | 处理结果形态 | 新表／复制新表／无新表（原地）／无新表（写文件） | `PRODUCE_LABEL`；`BUILTIN_OPS[k]["output"]` |
| 参数 schema | 参数键白名单与默认值 | 键集＝`param_keys`；默认值＝`params_schema` 的 `default` | `BUILTIN_OPS[k]["params_schema"]`（**唯一源**：key／type／required／default，R15/B-64）——`default_params()` 与引擎缺省回退**均派生于此**（R15/B-69／B-41） |
| 是否产表 | 是否生成新数据表 | 是／否 | `OUTPUT_OPS`；`BUILTIN_OPS[k]["output"]`；`STEP_KIND`（fork/merge 产表，sequential/end 不产表） |
| 是否可弃用 | 能否下线该功能 | 是／否 | `StepMeta.deprecated` ＋ `BUILTIN_OPS[k]["deprecated"]`（双端须一致；引擎侧校验见 R15/B-53） |
| GUI 表单类（补充） | 三位一体第③形态的载体 | 类名；构造签名固定 `(params, table_ids, conn_columns, parent)` | `_FORM_CLASSES` → `_build_registry()` → `get_form_class()` |
| 展示序（补充） | 弹层内排序与分类代表 | `order` 全局唯一；每分类 `order` 最小者为"主按钮"派生依据。**仅代码版承载**（现网 1~9），不入 §3.2 文档版表 | `StepMeta.order`；`main_buttons()`／`more_buttons()` |

### 3.4 代码版记录表载体清单（强制实现与约束）

| 层 | 载体 | 位置 | 约束强度 |
|----|------|------|----------|
| 引擎 | `BUILTIN_OPS`（9 条目×8 字段：`func`/`description`/`output`/`param_keys`/`params_schema`/`extra_input_min`/`overwritable`/`deprecated`） | `rpa_engine/ops/step_executor.py` L61-193 | 唯一源；`engine/registry.py` L12-25 为真转发（不得再立副本） |
| 引擎 | 参数契约查询辅助 `param_schema()`／`param_default()`／`param_defaults()`＋`GUI_INJECTED_PARAM_KEYS` | `rpa_engine/ops/step_executor.py` L59／L196-214 | GUI 与引擎回退的唯一派生入口（R15/B-41／B-64／B-69） |
| 引擎 | 参数白名单过滤（非白名单键**执行期静默丢弃**＋DEBUG 日志） | `rpa_engine/ops/step_executor.py` L301-306 | 运行时约束 |
| 引擎 | type 白名单 fail-fast 校验 ＋ **已弃用 type 拒绝** | `rpa_engine/engine/validator.py` L89-101 | 解析后校验（弃用校验见 R15/B-53） |
| GUI | `StepMeta`（7 字段，原 `icon` 已删）＋`_STEP_META_RAW`＋`STEP_CATALOG`＋`STEP_COUNT` | `rpa_engine/gui/models.py` L32-96（StepMeta 类 L32-64、`_STEP_META_RAW` L67-86、`STEP_CATALOG` L88-91、`STEP_COUNT` L96） | 单一源；派生 `STEP_DESC`/`main_buttons()`/`more_buttons()`/`active_catalog_keys()` |
| GUI | `OUTPUT_OPS`／`STEP_KIND`／`STEP_KINDS`／`PRODUCE_LABEL` | 同文件 L199-200／L207-217／L107／L248-258 | 平行表，须与 `BUILTIN_OPS` 口径一致 |
| GUI | `default_params()`／`extra_input_ids()` | 同文件 L1002-1016／L950-967 | `default_params` **派生于 `params_schema`**（R15/B-69，不再手写） |
| GUI | `_FORM_CLASSES`＋`_build_registry()`＋`get_form_class()`＋`_is_overwritable()` | `rpa_engine/gui/forms.py` L603-631 | 以 `STEP_CATALOG` 键集过滤（键集单一源）；`output_mode` 挂载读引擎 `overwritable`（R15/B-65） |
| 守卫 | 启动自检项 4／4b 共 **15 条**注册表守卫（含守卫①`output↔OUTPUT_OPS`、②`default_params⊆param_keys`、③非弃用必有表单、F4 `_OPS⊆SUPPORTED_OPERATORS`、按钮并集/交集、R15 增 `STEP_KIND` 值域与 `keywords` 非空） | `rpa_engine/gui/app.py` L48 起（项 4／4b） | 失败即弹框退出码 1，不进 GUI |
| 守卫 | 注册表一致性单测 ＋ **守卫镜像单测** | `rpa_engine/tests/test_step_catalog.py`；`rpa_engine/tests/test_registry_guards.py`（R15 新建） | 门禁（E1 缺口已由 R15/B-66 补齐） |
| 守卫 | 弹层卡片数＝`STEP_COUNT`、搜索命中、分组并集等断言 | `rpa_engine/tools/smoke/smoke_m1m3.py` L185-195 | 门禁（口径引用常量，R15/B-67） |

### 3.5 同步规则与冲突裁定

1. **同步单元**：新增／修改／删除功能函数时，代码版与文档版记录表**必须在同一提交单元内更新**（不得"先改代码、以后再补文档"）。
2. **同步范围**：文档版＝本文件 §3.2 表行；同时须同步 `docs/architecture.md` §6 的 9 项清单与 `docs/INDEX.md`（若篇数/路由变化）。
3. **冲突裁定：以代码为准**。发现两版不一致时：
   - a) 立即按代码实况修正文档版记录表；
   - b) 在当轮任务记录（`docs/task-records/`）写明"冲突来源＋处置"；
   - c) 同步登记 `_temp/conflict-log.md`（`AGENTS.md` §4.6；该文件当前不存在，首次冲突时创建）；
   - d) 若代码实况本身违反本文件或红线，则**不得改文档迁就代码**，须停止并报告人工裁定。
4. **新鲜度信号**：§3.2 表头须标注"取值核对日期"；`BUILTIN_OPS`／`STEP_CATALOG`／`_FORM_CLASSES` 任一变更而本表未更新，即判定本文件 `stale`，须在当轮修正。

## 4. 规定 3：前端交互位置固化

### 4.1 规则本体

1. **所有功能函数的参数配置，只在"用户配置"阶段 DAG 可视化的右侧区域（侧边栏／工作面板）完成。**
2. 前端交互设计只需考虑两件事：在右侧面板中**展示哪些参数项**、**以什么形式获取用户输入**。
3. "用户配置"阶段 DAG 上方的**"添加功能步骤"按钮，必须显示所有功能函数选项**（本质＝功能函数记录表；前端按 `category` 分组以便快速选择）。
4. **其他任何位置不得承担功能函数参数配置职责。**
5. "添加功能步骤"按钮的选项来源**必须是功能函数记录表（单一事实源）**，禁止硬编码功能名、禁止另立清单。
6. 新增功能函数时，**右侧面板表单与弹层选项必须同步更新**。

### 4.2 实现口径（现状已成立，作为约束固化）

| 要点 | 约束口径 | 现状载体 |
|------|----------|----------|
| 布局 | 左画布 : 右面板 ＝ 6 : 4（`QSplitter` 水平分割） | `page_operation_config.py` L105-110 |
| 面板三态 | 无选中＝空态提示；步骤态＝标题＋操作类型＋目标数据表下拉＋内联参数表单＋连线说明＋`[del]`；表态＝表信息＋弃用/恢复 | 同文件 L313-452 |
| 表单形态 | **内联可嵌入 QWidget，无弹窗**；控件面向文员（下拉／勾选／文件浏览／逐行键值），禁裸 JSON | `forms.py` L1-14 |
| 添加入口 | 顶栏唯一入口 `QToolButton "添加功能步骤 ▾"` → `Qt.Popup` 弹层（搜索框＋最近使用＋分类网格卡片） | `page_operation_config.py` L152-228 |
| 卡片文案 | 只允许取 `StepMeta.display`／`desc`，禁止硬编码功能名 | 同文件 L161-163（注释明令） |
| 弃用项 | **置灰＋标注"（已停用）"，不隐藏**（保证"显示所有选项"） | 同文件 L216-238 |
| 画布 | 严格只读：零拖拽、零连线编辑 | 既定裁定（`_temp/DAG-rebuild/plan.md` §1.1 条 6，经本文件升格为 [约束]） |

### 4.3 边界澄清（防误读，以下三处**不属**功能函数参数配置职责）

| 位置 | 实际职责 | 是否受本条约束 |
|------|----------|----------------|
| 阶段 1"输入数据选择"表格 | **数据表级**配置（选择、标识名称、来源文件、源数据表、表头行、删除） | 否 |
| 右侧面板"表态"（点选数据表节点） | **表级**状态操作（弃用此表／恢复使用） | 否 |
| 底部／顶栏模板与配置存取（保存配置、清空、保存本次配置） | **整份配置的存取**，不编辑单个参数 | 否 |

## 5. 规定 4：变更工作流顺序

### 5.1 前置铁律（适用于增／删／改全部三类）

**任何变更动手前，agent 必须先列出该变更涉及 a) Python 代码、b) JSON 参数与格式规范、c) GUI 交互 三者中的哪几项**（影响面清单，写入回复或任务记录），**再按顺序执行；不得跳步**。未列影响面即动手，视为执行错误。

### 5.2 新增功能函数（顺序固定）

1. **后端**：在 `rpa_engine/ops/` 实现 Python 功能函数（纯函数式，接收引擎传入的共享 `conn`，禁自建连接——`AGENTS.md` §2.2 条 4）；
2. **记录表与参数规范**：更新代码版记录表（§3.4 全部载体）＋文档版记录表（§3.2 增行）＋JSON 参数格式规范（参数键、取值、默认值、失败行为）；
3. **前端**：更新 GUI 交互（右侧面板表单类＋`_FORM_CLASSES` 登记＋"添加功能步骤"弹层选项自动随 `STEP_CATALOG` 出现）；
4. **回归**：按 §8 跑全部门禁。

> 第 3 步受 §2.3 硬停止条款约束：用户未说明 GUI 形态时不得执行。

### 5.3 删除功能函数（先查依赖，顺序自适应）

1. **先检查依赖与引用**：谁在用该功能（既有 JSON 参数文件／用户模板／最近使用记录）；谁引用它的产出表；谁是它的下游步骤；测试与 smoke 是否断言其存在；
2. **自适应调整操作顺序**：典型序＝先解除 GUI 入口（弹层不再出现、表单类下线）→ 再更新 JSON 参数格式规范与文档版记录表 → 最后删除 Python 实现；实际按影响面调整；
3. **整体原则**：**不留残缺引用、不破坏记录表同步**（两版记录表在删除后仍须一致，且 `architecture.md` §6 清单同步）；
4. **兼容处置**：历史 JSON／模板中仍含该功能时，须明确迁移或拒绝策略（人话提示，经 `gui/error_messages.py` 翻译层），不得静默失败；
5. **回归**：按 §8 跑全部门禁。

### 5.4 修改功能函数

1. **先定位影响面**：a)／b)／c) 三者中哪几项受影响（含参数键改名、默认值变化、产表口径变化、分类调整）；
2. **按"后端 → JSON → 前端"顺序推进**；
3. **三者同步更新后再回归验证**（不得先跑测试再补同步）；
4. **key 稳定性铁律**：`key` 为唯一稳定标识，改中文名只动 `StepMeta.display`（并同步 `BUILTIN_OPS[k]["description"]`，见 §7 B1），**不得改 key**（改 key＝删除＋新增，走 §5.2/§5.3）。

### 5.5 canonical 登记清单（13 项，新增 1 个功能函数的全部落点）

> 本清单为**唯一口径**，取代历史"6 处"（`_temp/W-03_GUI_detail_optimization_plan.md` §6.5，已随 R10 `_temp` 清理，骨架见 `_temp/ledger_2026-09-24/CLEANUP_MANIFEST.md` §2.1）与"7 处＋9 分支"（`_temp/ledger_2026-09-24/RPA_engine_maturity_assessment.md` P2-2）两套并存表述。

| # | 落点 | 内容 | 序 |
|---|------|------|----|
| 1 | `rpa_engine/ops/<模块>.py` | 实现函数（纯函数式，共享 conn）。**若新建 ops 模块**：还须在 `ops/step_executor.py` 顶部增 import 行、在 `RPA_Workflow_v3.spec` 的 `hiddenimports` 增 1 条（否则 exe 场景 ImportError；权限见 `build-guide.md` §1.7） | 后端 |
| 2 | `rpa_engine/ops/step_executor.py` | `BUILTIN_OPS` 增条目（**8 字段齐备**：`func`/`description`/`output`/`param_keys`/`params_schema`/`extra_input_min`/`overwritable`/`deprecated`）；`params_schema` 为参数契约唯一源（R15/B-64） | 后端 |
| 3 | `rpa_engine/ops/step_executor.py` | `execute_step` 增分发分支（现状 10 分支，L319-417；**不属红线"编排代码"**，界定见 §6 与 `architecture.md` §3.3；消除手写分支属 §7 P2-2） | 后端 |
| 4 | `rpa_engine/gui/models.py` | `_STEP_META_RAW` 增 **1 行 6 元组**（`key`/`display`/`desc`/`category`/`keywords`/`order`；类型标注见 L67，解包见 L88-91）；`deprecated` 由 `StepMeta` 默认值承载（`icon` 已于 R15/B-61 删除），**不得填 7 个值**（会致导入期 `ValueError` 解包失败、GUI 起不来） | 记录表 |
| 5 | `rpa_engine/gui/models.py` | `OUTPUT_OPS`（若产表） | 记录表 |
| 6 | `rpa_engine/gui/models.py` | `STEP_KIND`（end／merge／fork／sequential） | 记录表 |
| 7 | `rpa_engine/gui/models.py` | `PRODUCE_LABEL`（产出边标签） | 记录表 |
| 8 | `rpa_engine/gui/models.py` | ~~`default_params()` 增分支~~ **无需手改**：`default_params()` 已改为派生于引擎 `params_schema`（R15/B-69），新功能的默认值只在落点 2 声明一次 | 记录表 |
| 9 | `rpa_engine/gui/models.py` | `extra_input_ids()`（若需多输入表）＋ 引擎侧声明 `extra_input_min`（R15/B-63；`mapping_match`／`merge_tables`＝2） | 记录表 |
| 10 | `rpa_engine/gui/forms.py` | 新表单类＋`_FORM_CLASSES` 登记 | 前端 |
| 11 | `docs/function-spec-rules.md` §3.2 ＋ `docs/architecture.md` §6 | 文档版记录表增行＋9 项清单同步 | 记录表 |
| 12 | `rpa_engine/tests/` | 注册表一致性用例（分类数／键集断言）＋功能函数专属用例 | 回归 |
| 13 | **「总数」口径已收敛为单一常量 `gui.models.STEP_COUNT`（R15/B-67＋B-68）**：四处等值断言已改为引用它——`tests/test_graph_edges.py`、`tests/test_translation.py`、`tests/test_ops_contracts.py`、`tools/smoke/smoke_m1m3.py`；`gui/app.py` 下限守卫同样引用该常量。⇒ **新增/删除功能函数无需再手改这些断言**（自动同步）；仅需复核带数字的**文案**（若仍有硬编码「9」） | 回归 |

## 6. 与既有红线的关系

| 本文件条款 | 对应红线 | 关系 |
|------------|----------|------|
| §2 三位一体（a 后端实现） | `AGENTS.md` §2.2 条 5：新增操作只在 `ops/` 实现并登记 `BUILTIN_OPS` | **细化**：本文件给出登记落点与顺序，不改变红线 |
| §2 三位一体（b JSON 参数） | §2.2 条 1/2：禁硬编码业务逻辑；JSON 是业务逻辑唯一载体 | **一致** |
| §3 双记录表（代码版为准） | §2.2 条 5；`doc-governance.md` §7 源码↔规约同步 | **一致**：文档服从代码 |
| §4 交互位置固化（右侧面板唯一入口、内联表单、禁技术词） | §2.1 条 6 最高目标原则；`architecture.md` §8.4 禁用词口径 | **细化** |
| §4.2 画布只读 | `AGENTS.md` §2.1 条 6 最高目标原则（出处＝`_temp/DAG-rebuild/plan.md` §1.1 条 6＋ADR-3，属**历史裁定出处**而非规范依据，经本文件升格为 [约束]） | **一致**。注：`architecture.md` §10.5 只界定"DAG 可视化属前端、后端零改动"，**无画布只读条款**，故不以 §10 为对应红线 |
| §5 变更顺序（步骤不得自建连接） | §2.2 条 4 | **一致** |
| §5.5 第 3 项（`execute_step` 加分支） | §2.2 条 5"**不改编排代码**" | **一致（不触红线）**：`architecture.md` §3.3 明文界定"新增用户操作不修改引擎编排代码（**`engine/`**）"，而分发分支位于 `ops/step_executor.py`（§3.1 标题即"操作目录定义（ops/step_executor.py）"、§10.1 称 `BUILTIN_OPS` 为唯一操作扩展点）。历史 `_temp/ledger_2026-09-24/RPA_engine_maturity_assessment.md` P2-2 曾记为"张力"（`_temp/` 无约束力），经与 architecture §3.3 对表后**修正为不冲突**；P2-2 的真实价值＝消除 9 分支手写分发的可维护性收益。如人工另有裁定，以裁定为准 |

**冲突裁定**：本文件任何条款与 `AGENTS.md` §2.1／§2.2 红线冲突时，**一律以红线为准**；agent 须在任务记录与 `_temp/conflict-log.md` 登记冲突来源与处置，不得自行变通。

## 7. 待补强项 / 待实施项登记（本轮只登记，不实施）

> **禁令**：任何 agent 不得据本节自行修改代码。本节为人工立项依据，处置状态由人工更新。
> 性质定义：**待补强**＝规约已有要求但代码缺守卫/缺字段；**待实施**＝已评估但人工另行立项的工作。
> **R15 例外说明（2026-10-19）**：经人工批准（方案＝`.trae/documents/backlog-remediation-control-pack.md`），本轮据本节**实施**并回写处置状态；「R15 处置」列为该授权的留痕，后续仍由人工更新。

| 编号 | 问题 | 证据 | 性质 | 可信度 | R15 处置 |
|------|------|------|------|--------|----------|
| B5 | `deprecated=True` 一启用即致启动自检失败：`main_buttons()`／`more_buttons()` 排除弃用项，而自检按钮并集校验拿并集与**未过滤弃用的** `catalog_keys` 比对 → 功能级弃用通路实际不可用 | `gui/models.py` L135/L148；`gui/app.py` L185-188；`tests/test_step_catalog.py` L60-63 | 待补强（最高优先） | [推断] | ✅ **已解决（B-13，R12）**：校验改用 `active_catalog_keys()`（`app.py` L186-192）＋ `test_deprecated_self_check_passes` 回归保护；R15 复核确认，§3.2 注记 4 审计注记转正 |
| B1 | 中文名双源无守卫（`BUILTIN_OPS[k]["description"]` vs `StepMeta.display`），任一侧改名不报错 | `ops/step_executor.py` L52-109；`gui/models.py` L69-88 | 待补强 | [已校验一致] | ✅ 本批闭合（B-54 守卫单测：两源逐键等同） |
| B2 | `STEP_KIND` 值域无守卫（仅判真值），错值静默回退 `sequential` | `gui/app.py` L152；`gui/models.py` L208 | 待补强 | [已校验一致] | ✅ 本批闭合（B-55 值域校验＋单测） |
| B3 | `OUTPUT_OPS` ↔ `STEP_KIND(fork∪merge)` 等式无守卫（现网恰好成立） | `gui/models.py` L176-194 | 待补强 | [已校验一致] | ✅ 本批闭合（B-56 等式单测） |
| B4 | 孤儿表单类无反向守卫：`_build_registry()` 静默过滤不在 `STEP_CATALOG` 的键，下线功能后残留表单类不被发现 | `gui/forms.py` L568；`gui/app.py` L180-184 | 待补强 | [已校验一致] | ✅ 本批闭合（B-57 目录键↔表单类双向断言） |
| B6 | `keywords` 非空无守卫（自检仅判 tuple 类型），空 tuple 会使弹层搜索退化为仅 `display`＋`key` | `gui/app.py` L159-160；`gui/page_operation_config.py` L221 | 待补强 | [已校验一致] | ✅ 本批闭合（B-58 自检扩展：空 tuple 判失败） |
| B7 | 白名单反向覆盖无守卫：`param_keys` 有键但表单无控件 → 静默走 `.get()` 默认，用户无感知 | `gui/app.py` L163-169；`ops/step_executor.py` L217 | 待补强 | [已校验一致] | ✅ 本批闭合（B-59 `param_keys` ⊇ schema 键单测） |
| B8 | 前端键（`output_mode`）无集中声明，散落 4 处 | `gui/models.py` L701-702 等 | 待补强 | [已校验一致] | ✅ 本批闭合（B-60 常量集中声明于 `gui/models.py`） |
| B9 | **参数默认值双源无守卫**：`default_params()`（GUI）与 `execute_step` 的 `.get()` 回退（引擎）各自维护，且 `mapping_match.mode`（`left_join` ↔ `inner_join`）与 `convert_dtype.from_type/to_type`（`TEXT`/`INTEGER` ↔ 空串）**取值不同** → 手写 JSON 省略键时行为与文档版记录表宣称相反 | `gui/models.py` L921-924/L933-934；`ops/step_executor.py` L240/L292-293 | 待补强（R7 审查新发现） | [已校验一致] | ✅ 本批闭合（B-41＋B-64＋B-69 **单源化**：`params_schema` 为唯一源，引擎回退≡界面默认值） |
| C1 | `StepMeta.icon` 全为空串、零消费者、自检不校验 | `gui/models.py` L51 | 待补强 | [已校验一致] | ✅ 本批闭合（B-61 **删除字段**；无图标方案，启用无收益） |
| C2 | `target_param`／`match_param` 为零消费者休眠元数据，改造属引擎专项；裁定入口此前缺失，**已随本轮 W-22 登记** | `ops/step_executor.py` L47-49 | 待补强 | [已校验一致] | ✅ 本批闭合（B-62 **删除字段**；"启用为字段驱动"会与 P2-2「不改 9 分支」裁定冲突） |
| D1 | 无 `inputs.extra_min` 字段，输入基数契约无载体（`extra_input_ids()` 硬编码两个操作） | `gui/models.py` L897-914 | 待补强 | [已校验一致] | ✅ 本批闭合（B-63 新增 `extra_input_min`） |
| D2 | 无 `params_schema`（key／label／类型／必填／默认），§3.3"参数 schema"字段现由 `param_keys`＋`default_params()`＋表单类三处拼出 | `ops/step_executor.py` L52-109；`gui/models.py` L917-937 | 待补强 | [已校验一致] | ✅ 本批闭合（B-64 `params_schema` 落地为唯一源） |
| D3 | 无"可覆盖操作集"字段（基线 `_OVERWRITABLE=("filter","dedup")` 未落地），生产靠"哪些表单调 `_add_output_mode`"隐式表达 | `_temp/DAG-rebuild/SampleCode/backend/func_registry.py` L68；`gui/forms.py` L255/L286 | 待补强 | [已校验一致] | ✅ 本批闭合（B-65 新增 `overwritable`，表单挂载由其驱动） |
| D4 | 弃用口径前后端不闭合：引擎侧无弃用字段，手写 JSON 仍可执行已弃用操作 | `engine/validator.py` L89 | 待补强 | [已校验一致] | ✅ 本批闭合（B-53 `BUILTIN_OPS` 增 `deprecated`＋validator 拒绝已弃用 type） |
| E1 | 守卫规则双写：自检 15 条仅 5 条有单测镜像（F4 操作符守卫无镜像），规则演进易单侧更新 | `tests/test_step_catalog.py` L84-111 | 待补强 | [已校验一致] | ✅ 本批闭合（B-66 为剩余自检规则补齐单测镜像） |
| E3/A4 | "9 项"口径散落：**四处等值断言**（`len(STEP_CATALOG)==9`、`len(STEP_DESC)==9`、`len(list_ops())==9`（`tests/test_ops_contracts.py` L334，R12 阶段 7 新增）、弹层卡片数＝9）新增第 10 项即红；`gui/app.py` L109 为**下限守卫**（`registered < 9`，增至 10 项不失败）；另有非门禁口径面（`step_executor.py` L8/L37、`models.py` L26、`forms.py` L4/L243、`app.py` L51/L99、`architecture.md` §3.1/§6/§10、`docs/INDEX.md`、`AGENTS.md` §1、本文件 §3.2 标题） | `tests/test_graph_edges.py` L200；`tests/test_translation.py` L149；`tests/test_ops_contracts.py` L334；`tools/smoke/smoke_m1m3.py` L188；`gui/app.py` L109 | 待实施 | [已校验一致] | ✅ 本批闭合（B-67/B-68 四处断言与非门禁文案改**引用单一常量**） |
| P1-1／P1-2／P1-6 | 功能函数专属单测缺失；失败／重试／取消／解析报错路径零测试；部分列处理失败仍报"步骤成功"（返回值契约未定：函数返回值被丢弃，成功返回块无条件成立） | `_temp/ledger_2026-09-24/RPA_engine_maturity_assessment.md` L119-137；`ops/step_executor.py` L299（返回值丢弃）／L306-311（成功返回） | 待实施（人工另行立项） | [已校验一致] | ⚠️ **部分闭合**：P1-1／P1-2 已由 B-42／B-43（R12）落地；**P1-6（返回值消费）仍属红线③**，随 B-18／B-44 登记为受控例外 |
| P2-1／P2-2 | 默认参数手写清单（独立硬编码源，与 B9 双源问题同源）；分发 9 分支手写（**不触红线**，界定见 §6；本项价值＝可维护性与"新增功能只加 1 条注册项"的目标态） | 同上 L135-136；`ops/step_executor.py` L209-294 | 待实施（人工另行立项） | [已校验一致] | P2-1 ✅ 本批闭合（B-69 `default_params` 派生于 `params_schema`）；P2-2 **维持既有裁定**（B-70：不改 9 分支，标已裁定关闭） |

**治理登记**：以上 **18 行**＝代码层缺口 **16 项**（B1~B9 共 9、C1/C2 共 2、D1~D4 共 4、E1 共 1）＋ E3/A4 与 P 系列 2 行（P 系列合并 5 个编号：P1-1／P1-2／P1-6／P2-1／P2-2，承 R6 排除清单），全部已在 [docs/backlog.md](./backlog.md) 登记为 **W-22**（待人工裁定立项）。
**R15 结清统计（2026-10-19）**：18 行中 **15 行闭合**（B1~B9 共 9、C1/C2、D1~D4、E1、E3/A4）、**1 行已解决（B5，B-13 承载）**、**2 行部分/维持**（P 系列：P2-1 闭合、P2-2 维持裁定、P1-6 转入例外）。

## 8. 校验与门禁（功能函数变更后必跑）

| # | 命令／动作 | 期望 |
|---|-----------|------|
| 1 | `conda run -n CPS-GPES_RPA-py311 python -m unittest discover -s tests`（cwd＝`rpa_engine`） | 全绿（基线 **263** 用例，2026-11-03 实测；R15 新增 `test_registry_guards.py`／`test_registry_single_source.py`／`test_dependency_contract.py`） |
| 2 | `python tools/smoke/smoke_m1m3.py` ＋ `python tools/smoke/smoke_mb.py`（cwd＝`rpa_engine`，`QT_QPA_PLATFORM=offscreen`） | `SMOKE_ALL_OK` ×2 |
| 3 | 启动自检 6 项（offscreen 调 `gui.app.run_self_check()`） | 6/6；项 4／4b 的 15 条注册表守卫全绿 |
| 4 | `python tools/doc_verify.py`（仓库根） | `PASS`；报告落 `_temp/verify-<时间戳>.md` |
| 5 | `AGENTS.md` 容量与行尾（涉 AGENTS 时；口径见 `doc-governance.md` §10.2/§10.3） | 含 CR ≤8,000、余量 ≥200、纯 CRLF（`loneCR=loneLF=0`） |
| 6 | §3.2 文档版记录表 ↔ 代码逐项核对 | 一致；不一致按 §3.5 处置 |

## 9. 变更记录

| 日期 | 轮次 | 变更 |
|------|------|------|
| 2026-09-24 | R7 | 新建本文件：人工裁定 4 条规定（三位一体／双记录表／交互位置固化／变更顺序）固化为 [约束]；§3.2 文档版记录表按代码实况建表；§5.5 canonical 登记清单 13 项取代历史 6/7 处口径；§7 登记待补强/待实施（backlog W-22）。本轮零代码改动 |
| 2026-09-24 | R7（同轮审查修正） | 只读 Consistency Reviewer 审查后修正 10 项：①§3.2 注记 1 `t_{uid}` 归属改 GUI（`models.py` L708）＋补引擎回退 `t_s{n}`（`step_executor.py` L207）②新增注记 3 与 §7 B9（默认值双源，2 项取值不同）③§5.5 项 4 "8 字段"改"6 元组行"（防导入期解包失败）④§5.5 项 13 改三处等值断言＋`app.py` L108 定性为下限守卫 ⑤§5.5 项 1 补 `step_executor` import 与 `RPA_Workflow_v3.spec` hiddenimports 落点 ⑥§6 "张力"改"一致（不触红线）"，对齐 `architecture.md` §3.3"编排代码＝`engine/`"界定；画布只读对应红线改指 §2.1 条 6 ⑦§7 补 B6 行、统一计数口径（18 行＝16 项＋P 系列 2 行）⑧§3.3 展示序注明仅代码版承载 ⑨修正 3 处行号漂移（`models.py` ±2、`step_executor` 分发区 L209-294、assessment L119-137）⑩§8 项 5 术语对齐 doc-governance §10.2/§10.3、§3.5 conflict-log 注"不存在则创建" |
| 2026-10-19 | R15 | **W-22／N 系列结清＋记录表单源化**（方案＝`.trae/documents/backlog-remediation-control-pack.md`，经人工批准）：①核心＝`BUILTIN_OPS.params_schema` **唯一源**落地，GUI `default_params()` 与 `execute_step` 缺省回退**均派生于此**（闭合 B9／D2／P2-1）；②`mapping_match.mode` 缺省 `inner_join`→`left_join`（消"静默丢主表未匹配行"）、`convert_dtype.from_type/to_type` 空串→`TEXT`/`INTEGER`（消"必然报错"）；③删除 `StepMeta.icon` 与 `target_param`／`match_param` 休眠字段；④新增 `extra_input_min`／`overwritable`／`deprecated` 声明（`validator` 拒绝已弃用 type，闭合 D4）；⑤`STEP_COUNT` 单一常量替代四处「9」断言与 10+ 处文案；⑥补守卫镜像单测（闭合 E1）；⑦`output_mode` 前端键集中声明；⑧B5 复核确认已由 B-13 解决；§3.2 注记 3／4／5 与 §3.3／§3.4／§5.5 同步改写，§8 基线 191→234 |
| 2026-10-24 | R16 | 行号锚点刷新（models/forms/step_executor 实测）；基线 234 不变；W-22 已关闭 |
