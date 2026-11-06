---
title: Architecture — V3 RPA 工作流引擎架构设计
type: knowledge
scope: global
status: active
owner: 黄泊凯
last-updated: 2026-11-02
tags: [架构, 引擎, 设计, GUI, 已知阻塞]
binding: constraint
confidence: 已校验一致；2026-09-13 新增 §8.4 交互设计原则（最高目标原则）与 §10 架构刚性边界；2026-09-24 R6/E1 §8.2 阶段1列名/内联表单与 §8.3 信号表按代码实况修订；2026-09-24 R7 §2 校验段与 §3.1 字段表按代码实况修正（参数白名单为执行期过滤、target_param/match_param 休眠），并增 §3/§6/§8.2 指向 function-spec-rules.md 的 [约束] 交叉引用；2026-10-19 R15 §3.1 字段表按代码实况改写为 8 字段集（删 target_param/match_param，增 params_schema/extra_input_min/overwritable/deprecated）；2026-11-01 R17 §6 export 行标注模板化输出暂缓（W-24 裁定）；2026-10-24 R16 全库一致性收口：§2 `load_tables`→`ensure_input_tables`、§3.3 hiddenimports 口径（仅 ops/paths 显式，engine/gui 由入口静态分析收集）、§4 数据传递字段与 SessionDB 连接模型、§6 笔误、§8 DAG 落地形态（node_graph.py 单文件）、§9 #4 测试输入文件名，全部按代码/目录实测校正
content-revision: 2026-10-24
---

# Architecture — V3 RPA 工作流引擎架构设计

> 所属层级：知识层（docs/），经 AGENTS.md §2.5 背书具 [约束] 效力｜可信度状态：[已校验一致]
> 本文档详细描述引擎的核心架构设计。AGENTS.md 为精简索引，红线规则以 AGENTS.md 为准。
>
> **适用范围**：新增或修改引擎模块（engine/、ops/）前必读
> **最后更新**：2026-11-01（R17：§6 `export` 行标注模板化输出暂缓（W-24 裁定）；历史 2026-10-24：R16 文档一致性收口：按代码/目录实测校正 §2 兜底补导函数名、§3.3 打包 hiddenimports 口径、§4 数据传递字段与 SQLite 连接模型、§6 笔误、§8 DAG 落地形态、§9 #4 测试输入文件名；历史 2026-09-13：代码整理——§3.2/§3.4/层级表随 CLI 移除与 steps/ 删除同步；此前 2026-09-13 新增 §8.4 交互设计原则（最高目标原则）与 §10 架构刚性边界（ETL 底层不可偏离）；历史 v3.1 口径全量同步：§1 Schema 改为 tables[]+steps[] 数据表驱动格式、§3 改为 BUILTIN_OPS 用户操作目录与分发机制、§6 改为 9 项用户操作清单、§7 边界表、§8.0/§8.1 生命周期与引擎接口、§9 阻塞表 #3 按 v3.1 修订；内容修订日期 2026-08-24）
<!-- 同步更新 2026-08-15: 复查并修正 retry_count 默认值、模板路径示例、pandas_transform 必填参数 dtype；与 parser.py/steps 实际代码对齐 -->
<!-- 同步更新 2026-08-21: v2.2 升级——头部转 YAML 元信息区；新增 §8.0 GUI 应用生命周期与 §9 已知阻塞（自 AGENTS.md §13/§11 下沉，用户裁决 R-4 方案 A） -->
<!-- 同步更新 2026-08-24: v3.1 口径全量同步——与 engine/parser.py、ops/step_executor.py（BUILTIN_OPS 9 项）、engine/__init__.py（execute_workflow）、RPA_Workflow_v3.spec 逐一对齐；v3 表述保留为"已废弃"历史注记（§3.4），信息不丢失 -->
<!-- 同步更新 2026-10-24: R16 全库一致性收口——按 2026-10-24 实测校正：§2 `ensure_input_tables`（非 load_tables）、§3.3 spec 仅显式声明 ops/paths、§4 `target_table_id`/`output_table_id`+`params.output_table` 与 SessionDB 唯一连接点、§6 "Word/TXT" 笔误、§8 DAG 实际落地于 gui/node_graph.py 单文件、§9 #4 测试输入 0~3 -->

---

## 1. Parameter File Schema（JSON 工作流定义文件，v3.1 数据表驱动）

参数文件是业务逻辑的唯一载体。v3.1（自 v3 预设步骤架构迭代而来）采用"数据表驱动"结构：`tables[]` 声明阶段 1 确认导入的数据表，`steps[]` 声明阶段 2 配置的操作（每步必含目标表编号）。结构如下（以 engine/parser.py v3.1 定稿与 GUI 实际产物为基准）：

```json
{
  "__meta": {
    "schema_version": "3.1",
    "created": "2026-08-24 12:49:28"
  },
  "name": "本轮操作",
  "global": {
    "keep_db": false
  },
  "tables": [
    {
      "table_id": "T1",
      "alias": "电费表-sheet_1月",
      "source": {
        "file": "D:/data/电费表.xlsx",
        "sheet": "1月",
        "header_row": 1
      },
      "sqlite_table": "t1"
    }
  ],
  "steps": [
    {
      "step_id": "S1",
      "type": "filter",
      "name": "筛选大额",
      "target_table_id": "T1",
      "output_table_id": "T2",
      "params": {
        "conditions": [{"column": "电费", "op": ">", "value": 10000}],
        "logic": "AND"
      },
      "on_error": "stop",
      "retry_count": 3
    },
    {
      "step_id": "S2",
      "type": "export",
      "name": "结果导出",
      "target_table_id": "T2",
      "output_table_id": "",
      "params": {
        "output_path": "output/月度汇总.xlsx",
        "sheet_name": "数据"
      },
      "on_error": "stop",
      "retry_count": 3
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `__meta.schema_version` | string | ✅ | Schema 版本号，v3.1 定稿为 `"3.1"` |
| `__meta.created` | string | ❌ | 参数文件创建时间戳 |
| `name` | string | ❌ | 本轮操作名称（用于日志标识，默认"未命名操作"） |
| `global` | object | ❌ | 全局配置，如 `keep_db`（执行后是否保留会话库，默认 false） |
| `tables[].table_id` | string | ✅ | 数据表编号（T1, T2, ...），全文件唯一 |
| `tables[].alias` | string | ❌ | 表别名（面向用户显示） |
| `tables[].source` | object | ❌ | 数据源复现信息：`file`（Excel 路径）/`sheet`（工作表名）/`header_row`（表头行号）；解析器缺省宽容为 `{}`，但实际导入数据表必须提供，GUI 始终写出 |
| `tables[].sqlite_table` | string | ❌ | 导入后的 SQLite 表名（如 `t1`）；缺省时解析器回退为 `table_id.lower()` |
| `steps[].step_id` | string | ✅ | 步骤唯一标识 |
| `steps[].type` | string | ✅ | 操作类型（须在 `BUILTIN_OPS` 用户操作目录中，见 §6；由 validator 白名单校验） |
| `steps[].name` | string | ❌ | 步骤名称（用于日志标识） |
| `steps[].target_table_id` | string | ✅ | 操作目标数据表编号（引用 `tables[]` 或前序步骤的派生表编号） |
| `steps[].output_table_id` | string | ❌ | 派生表编号（产出输出表的操作可指定，供后续步骤引用；缺省时引擎自动命名） |
| `steps[].params` | object | ❌ | 操作参数（按操作类型的 `param_keys` 白名单校验，见 §3.1） |
| `steps[].on_error` | string | ❌ | 异常策略：`stop`/`skip`/`retry`（默认 `stop`） |
| `steps[].retry_count` | int | ❌ | 重试次数（`on_error=retry` 时有效，默认 3）<!-- 同步更新 2026-08-15: parser 默认值 0→3（08-12 代码修正），文档同步；2026-08-24 v3.1 parser.py StepDef.retry_count 默认 3 仍一致 --> |

> ⚠️ **D4 决策（v3.1 定稿）**：v3 旧格式（`workflow{}` 包裹、`steps[].type=extract_excel` 等）**不再兼容执行**，解析器遇旧格式明确抛出 `ParserError`。v3 七类步骤的历史说明见 §3.4 与 §6 尾注。

---

## 2. 三段式执行流程

```text
参数文件(JSON路径)
    │
    ▼
[第一段：解析] parse_workflow()
    │  读取JSON → 解析为 WorkflowDef 对象
    │  - JSON 语法校验
    │  - 必填字段校验
    │
    ▼
[第二段：校验] validate_workflow()
    │  全量校验（任一失败则终止，不执行任何步骤）
    │  - tables[] 表编号唯一性、sqlite 表名合法性
    │  - steps[].type 是否在 BUILTIN_OPS 用户操作目录白名单中
    │  - 步骤表引用链校验（target_table_id/output_table_id 引用有效）
    │  注（R7 按代码实况修正）：参数白名单**不在本阶段校验**——
    │  `validator.py` 只做 type 白名单与结构/引用校验；params 非白名单键
    │  在**执行期**由 `ops/step_executor.py` 过滤（静默丢弃＋DEBUG 日志）
    │
    ▼
[第三段：执行] execute_workflow()
    │  数据源加载（ensure_input_tables：tables[] → SQLite；旧称 load_tables，2026-10-24 按代码实测正名）
    │  → 按 steps 列表顺序逐步执行（execute_step 单步分发）
    │  - 异常处理：stop→终止 / skip→跳过 / retry→重试
    │  - 取消检查点：步骤间响应用户终止
    │  - 记录耗时、行数、内存峰值
    │
    ▼
[清理] finally 块
    │  - 关闭 SQLite 连接
    │  - del df + gc.collect()
    │  - 清理 .db、.db-wal、.db-shm
    │  - 记录总日志
    │
    ▼
[输出] 返回执行结果元数据
```

**设计要点**：校验阶段独立于执行阶段，确保"全部通过才执行"，避免脏数据污染中间状态。

---

## 3. User Operation Catalog and Step Dispatch Mechanism (v3.1)

v3.1 不再使用"步骤类 + 装饰器注册"机制。用户操作以**函数目录**形式集中登记于 `ops/step_executor.BUILTIN_OPS`，引擎经薄再导出层查找并由 `execute_step()` 单步分发。

> **[约束] 交叉引用（R7，2026-09-24）**：功能函数（＝用户操作）的三位一体规则、双记录表同步与冲突裁定、前端交互位置固化、增/删/改变更顺序与 canonical 登记清单（13 项），见 [function-spec-rules.md](./function-spec-rules.md)。本节只描述注册与分发机制本身。

### 3.1 操作目录定义（ops/step_executor.py）

```python
# ops/step_executor.py（v3.1 现行，10 项；R15 字段集：8 字段）
BUILTIN_OPS: Dict[str, Dict[str, Any]] = {
    "filter": {
        "func": filter_table, "description": "条件筛选",
        "output": True,
        "param_keys": {"conditions", "logic", "output_table"},
        "params_schema": [
            {"key": "conditions", "type": "list", "required": False, "default": []},
            {"key": "logic", "type": "enum", "required": False, "default": "AND"},
        ],
        "extra_input_min": 0,
        "overwritable": True,
        "deprecated": False,
    },
    # ... 其余 8 项见 §6 清单
}
```

条目字段语义：

| 字段 | 含义 |
|------|------|
| `func` | 操作实现函数（ops/ 各模块） |
| `description` | 中文说明（GUI 操作目录展示用）；与 GUI 侧 `StepMeta.display` 须逐字一致（守单测见 `function-spec-rules.md` §7 B1 闭合） |
| `output` | 是否产出输出表（True 时缺省自动命名 `t_s{n}`；GUI 链路经 `params.output_table` 固化为 `t_{uid}`——M5-a，`t_s{n}` 仅外部 JSON 缺省回退） |
| `param_keys` | 参数白名单（防 `**params` 混入保留键，如 `conn`）。**过滤发生在执行期而非校验期**——非白名单键静默丢弃并记 DEBUG 日志（`ops/step_executor.py` L301-306） |
| `params_schema` | **参数契约唯一源**（R15/B-64）：逐键声明 `key`/`type`/`required`/`default`；`execute_step` 的缺省回退与 GUI `default_params()` **均派生于此**（R15/B-41／B-69，消原双源差异） |
| `extra_input_min` | 除目标表外的最小额外输入表数（R15/B-63；`mapping_match`／`merge_tables`＝2，其余 0） |
| `overwritable` | 可否覆盖原表（R15/B-65；GUI「结果保存方式」下拉的挂载依据，现网 `filter`／`dedup`） |
| `deprecated` | 功能级弃用（R15/B-53）：`engine/validator.py` 据此**拒绝**已弃用 type，闭合"GUI 置灰但手写 JSON 仍可执行"缺口 |

### 3.2 再导出与查找接口（engine/registry.py）

```python
# engine/registry.py —— 薄再导出层（唯一定义在 ops/step_executor）
from ops.step_executor import BUILTIN_OPS

def get_op_func(op_name): ...      # 按操作名取实现函数
def list_ops(): ...                # 返回全部操作名（排序）
def get_op_description(op_name): ...
```

`engine/__init__.py` 统一导出 `parse_workflow` / `validate_workflow` / `execute_workflow` / `BUILTIN_OPS` / `get_op_func` / `list_ops` 等，GUI 经此接入（CLI 分支已移除，见 docs/backlog.md W-18）。

### 3.3 校验与分发

- **校验**：`engine/validator.py` 校验 `steps[].type in BUILTIN_OPS`（白名单），并校验表编号唯一性与步骤引用链
- **分发**：`engine/executor.py` 编排执行，单步经 `ops.step_executor.execute_step()` 查 `BUILTIN_OPS` 调用对应函数；操作函数统一接收引擎传入的共享 SQLite 连接

> ⚠️ **关键规则**：新增用户操作**不修改引擎编排代码**（engine/），只需在 `ops/` 下实现操作函数并在 `BUILTIN_OPS` 登记条目。
>
> **打包口径（2026-10-24 按 spec 实测校正）**：`RPA_Workflow_v3.spec` 的 `hiddenimports` **仅显式声明项目内动态导入面 `paths`、`ops`（含 ops 全模块）**，外加 `xlrd`／`openpyxl`／`PyQt5.sip` 等第三方隐式依赖；`engine/`、`gui/` 未列入 hiddenimports，由入口 `rpa_engine/main.py` 的静态导入分析自动收集。

### 3.4 v3 注册机制（已废弃）

> 历史说明，仅作重构参考，**禁止调用**。

v3 曾采用"步骤类 + 装饰器注册"机制：所有步骤类型继承 `steps/base.BaseStep` 抽象基类（`validate()`/`execute()`），经 `@register_step("type_name")` 装饰器写入 `engine/registry.STEP_REGISTRY` 全局字典，`steps/__init__.py` 导入全部步骤模块以触发注册。v3.1 重构后：`STEP_REGISTRY` 与 `register_step` 已删除，`steps/` 下 9 个文件曾全部标注 `[DEPRECATED v3]` 并禁用（含 `export_ppt` 预留占位）；**2026-09-13 已物理删除**（纯死代码，生产代码零引用；历史实现见 git 历史，原归档 `_temp/BackUp/` 已于 2026-09-14 清理）。

---

## 4. 步骤间数据传递规则

1. 步骤间数据**统一通过 SQLite 传递**，禁止在步骤间直接传递 DataFrame。
2. 每步显式声明 `target_table_id`（操作目标表）/ `output_table_id`（派生表编号）；产出输出表的操作另经 `params.output_table` 固化实际表名（GUI 链路写 `t_{uid}`）。
3. SQLite 连接由 `ops/session_db.SessionDB` **统一创建**（唯一连接创建点，WAL 模式）；执行线程（QThread worker）因 SQLite 线程亲和须经 `new_connection()` 自建连接，各步骤不得自行 `sqlite3.connect()`。
4. 任务结束后 `finally` 中清理 `.db`、`.db-wal`、`.db-shm`。

### 数据流示意（v3.1）

```text
[阶段1 导入]      Excel → 预处理 → SQLite("t1")            ← tables[T1]
                                          │
[filter]                                 ▼
                  SQLite("t1") → SQL WHERE → SQLite("t_{uid}") ← 派生表（output；GUI 链路 t_{uid}，外部 JSON 缺省回退 t_s{n}）
                                                       │
[export]                                               ▼
                  SQLite("t_{uid}") → 流式写出 → Excel 输出文件（无模板直出）
```

---

## 5. SQLite 连接初始化（引擎职责）

引擎在创建连接后**立即**执行：

```python
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;");
```

**说明**：
- **WAL 模式**：提高并发读写性能，允许读操作不阻塞写操作
- **synchronous=NORMAL**：在 WAL 模式下是安全的，提升写入性能
- **2026-10-24 注记（按 `ops/session_db.py` L64-80 实测）**：连接创建点统一为 `SessionDB`；除上述两条 PRAGMA 外还设置 `busy_timeout=5000`（避免并发写瞬时锁冲突直接报错）

---

## 6. 用户操作目录清单（BUILTIN_OPS）

> v3.1 现行口径，与 `ops/step_executor.BUILTIN_OPS`（D3 决策，10 项）逐一对应；由 `engine/validator.py` 白名单校验、`ops/step_executor.execute_step()` 分发。
>
> **[约束] 文档版功能函数记录表**（含分类、输入基数、参数默认值、GUI 表单类、是否可弃用等全字段）以 [function-spec-rules.md](./function-spec-rules.md) §3.2 为唯一载体；本表仅保留引擎视角摘要，两者冲突时**以代码为准**（裁定规则见该文件 §3.5）。新增/删除功能函数时两处必须同一提交单元内同步（登记清单见该文件 §5.5）。

| 操作标识 | 层级 | 职责 | 产出输出表 | 主要参数（param_keys） |
|---------|------|------|:---:|----------------------|
| `filter` | L2 业务 | 条件筛选（WHERE 过滤） | ✅ | conditions, logic, output_table |
| `dedup` | L2 业务 | 条件去重 | ✅ | key_columns, keep, output_table |
| `mapping_match` | L2 业务 | 跨表映射匹配（SQL JOIN） | ✅ | match_table_id, match_columns, mode, output_table |
| `aggregate` | L2 业务 | 条件统计（GROUP BY + 聚合） | ✅ | group_by, metrics, conditions, output_table |
| `export` | L2 业务 | 结果导出（SQLite → xlsx 流式直出，无模板；模板化输出**暂缓**，W-24 已裁定） | ❌ | output_path, sheet_name |
| `supervision_report` | L2 业务 | 履职表单抽查报告（3 张统计 sheet + 1 段总结 txt，写 2 文件） | ❌ | output_path, workday_count, extra_table_ids |
| `merge_tables` | 表级 | 数据表合并 | ✅ | match_table_ids, output_table |
| `copy_table` | 表级 | 数据表复制 | ✅ | output_table |
| `rename_columns` | 表级 | 表头名称修改 | ❌ | mapping |
| `convert_dtype` | 表级 | 数据类型转换 | ❌ | column, from_type, to_type |

**尾注**：
- v3 的 7 种预设步骤类型（`extract_excel`/`sql_transform`/`pandas_transform`/`export_excel`/`export_word`/`export_txt`/`export_ppt`）已全部废弃（见 §3.4），其 ETL 能力由"阶段 1 数据表导入 + 上表 9 项用户操作"覆盖；Word/TXT 导出暂无 v3.1 对应操作（能力缺口）
- `export_ppt` 无 v3.1 对应操作：PPT 导出仍为**预留能力**，见 §9 #3
- 层级说明：L0 基础设施（sql_safety/session_db/excel_preprocessor/sqlite_manager）、L1 表操作（引擎内部用）、L2 业务操作、L3 分发（step_executor）；本清单仅列**面向用户**的 9 项操作

---

## 7. 引擎与业务分离的边界说明

| 层级 | 职责 | 示例 |
|------|------|------|
| **引擎层** | 通用框架逻辑：解析JSON、校验步骤、调度执行、异常处理、资源清理 | `engine/parser.py`、`engine/validator.py`、`engine/executor.py` |
| **操作函数层** | 用户操作实现：L0 基础设施/L1 表操作/L2 业务操作/L3 分发 | `ops/*.py`（原 `steps/*.py` 已删除，2026-09-13） |
| **业务层** | 具体业务逻辑：操作参数、文件路径、列名映射、筛选条件 | JSON 参数文件 |

> 前后端归属：**引擎层 + 操作函数层 + 业务层（JSON）= 后端**（ETL 技术底层）；**GUI 交互层（含 DAG 可视化）= 前端**（界定权威见 §8）。

**判定标准**：如果某段代码在 2 个以上业务场景中需要相同逻辑 → 引擎层/操作函数层；如果某段代码专属于某个部门/某个报表 → 业务层（JSON）。

---

## 8. GUI 架构

> 来源：长任务提示词 §5-§6。本节描述 GUI 与引擎的集成方式、四阶段页面的布局规格及线程模型。
> 生命周期概览见本文 §8.0。

> **前端/后端概念界定（唯一权威载体，2026-09-14）**：规约体系其余文档一律经引用本页，避免多源。

- **后端** = ETL 架构技术底层：`engine/`、`ops/`、SQLite 中间层、JSON 参数机制（业务逻辑唯一载体）。负责解析、校验、执行、资源清理。
- **前端** = GUI 交互层（`rpa_engine/gui/`）：**含 DAG 可视化组件**。负责用户交互、参数文件生成、视图与可视化渲染、交互形态。前端经 §8.1 集成边界调用后端（GUI → `gui/worker.py` EngineWorker → `engine.executor.execute_workflow()`），不直接触碰操作函数。
- **DAG 可视化组件（`gui/node_graph.py`）属前端**；对其的重构 = 前端能力扩展，后端零改动（见 §10）。
  - **2026-10-24 注记**：原文所写"重构后 `gui/graph/`"的**五层包方案未采纳**（F 批裁定 2026-09-20），DAG 重构实际在 `gui/node_graph.py` **单文件**落地（1,087 行；`gui/graph/` 目录不存在）。

### 8.0 GUI 应用生命周期（全流程）

> 来源：长任务提示词 §4；2026-08-21 自 AGENTS.md §13 下沉（v2.2 升级，用户裁决 R-4 方案 A）；2026-08-24 按 v3.1 四阶段页面口径修订。

```
启动 → 自检（环境/权限/用户操作目录注册扫描）
     → 加载配置文件（后台，不阻塞，首次可能无配置）
     → 显示【阶段1 输入数据选择】（添加/确认并导入数据表）
     → 切换【阶段2 操作配置】（节点图 + 参数面板，保存/载入配置）
     → 用户点击"开始执行"
     → 切换【阶段3 运行追踪】（提供"终止操作/放弃执行"按钮）
     → 操作结束（正常/用户终止/异常）
     → 切换【阶段4 结果报告】（提供"确定"按钮）
     → 用户点击"确定"
     → 返回【阶段1 输入数据选择】，准备下一轮
```

### 8.1 前端（GUI）与后端（引擎）集成边界

- 前端（GUI）通过 `gui/worker.py` 的 EngineWorker（QThread）调用后端 `engine.executor.execute_workflow()` 启动引擎，不直接调用操作函数
- 引擎内部流程 parse → validate → execute 对 GUI 透明
- GUI 在后台线程（QThread）中运行引擎，通过 Qt 信号获取步骤级状态回调
- 日志由 loguru 输出到 `logs/gui_*.log` 文件，**不进入 GUI**（2026-09-18 W-19 裁定：GUI 终端面板 ConsolePanel 已移除）
- GUI 生成的 JSON 必须符合本文 §1 的 v3.1 Schema（tables[] + steps[]）

### 8.2 四阶段布局规格

| 阶段 | 页面 | 布局 | 主要组件 |
|------|------|------|---------|
| 阶段 1 | 输入数据选择 | 全页列表 | [add] 按钮 + [确认并导入] 按钮 + QTableWidget（6 列：选择、标识名称、来源文件、源数据表、表头行、删除；R6/E1 按 page_input_selection 实况修订） |
| 阶段 2 | 操作配置 | 左右分割 | 左侧节点图（60%）+ 右侧参数面板（40%）+ 底部模板区域。**[约束]（R7）功能函数参数配置的唯一入口＝右侧面板**（画布只读、内联表单无弹窗）；顶部"添加功能步骤"弹层必须显示全部功能函数选项（按分类分组，弃用项置灰不隐藏）——细则见 [function-spec-rules.md](./function-spec-rules.md) §4 |
| 阶段 3 | 运行追踪 | 全页列表 | 步骤状态列表（独占）+ [终止操作]/[放弃执行] 底栏 |
| 阶段 4 | 结果报告 | 全页文本 | 结果统计（独占）+ [确定]/[新一轮操作]/[保存本次配置] 底栏 |

通用规则：

- 自绘标题栏（最小化/全屏还原/关闭），无系统默认边框
- 所有组件动态响应窗口缩放
- 选中态浅蓝色背景
- 参数编辑通过**内联表单**（可内嵌 QWidget，直接放入配置页右侧面板，无弹窗；R6/E1 按 forms.py 实况修订），文件路径调 Windows 文件对话框
- 详见长任务提示词 §5.1-§5.4

### 8.3 线程模型

- 主线程：QApplication + GUI 渲染 + 用户交互
- 工作线程：EngineWorker(QThread)，运行 `execute_workflow()`
- 通信方式：Qt Signal/Slot（R6/E1 按 worker.py 实况修订；原 `log_message` 已随 W-19 ConsolePanel 移除）
  - `step_started(step_id, step_name)`
  - `step_completed(step_id, duration_sec)`
  - `step_failed(step_id, error_msg)`
  - `workflow_finished(status, total_duration_sec, output_tables, success)`（R6/A2 扩为 4 参：第 4 参 success＝全步成功判定，支撑"部分完成"诚实报告）
- 取消机制：设置标志位，引擎在步骤间检查点＋导出循环内每批检查点响应（R6/D1）

### 8.4 交互设计原则（最高目标原则）

> 效力来源：经 `AGENTS.md` §2.5 背书具 **[约束]** 效力；上位红线见 `AGENTS.md` §2.1 条 6。本节是 DAG 重构「用户视角改造方案」的评估基准。

**1. 目标用户与验收判据**

- 目标用户：**无技术背景的企业文员**（零培训即用）
- 可理解性验收判据（须逐条满足）：
  - 新用户**零培训**可独立完成一次完整的数据处理流程（导入 → 配置 → 运行 → 查看结果）
  - 面向用户的主界面**不得出现**以下技术术语：`SQL`、表名、列名、`JSON`、`schema`、参数文件、主键、外键、`DataFrame`、`SQLite`、端口、泳道、节点、`Z` 值、坐标、线程、回调
  - 术语须替换为业务语言（示例：数据表 A → 待处理的数据；步骤节点 → 处理环节；端口/连线 → 数据流向）

**2. 交互从简**

- 每屏只承载一个决策；提供合理默认值，减少必填项
- 错误提示使用业务语言，并给出「下一步该做什么」的可执行动作

**3. 转换全部由程序代码完成**

- 用户语义（如「按客户编号把这两张表合并」）→ 操作序列与参数的翻译，全部由 GUI 层代码生成
- 用户**不编写、不接触、不需要看见** JSON 参数文件或任何技术参数（与 §10 第 4 条的关系见 §10）

**4. 技术细节隐藏**

- 引擎日志、SQL 语句、异常堆栈等技术性信息**不得出现在面向用户的主界面**；日志已统一落盘 `logs/gui_*.log` 文件，不经 GUI 呈现
- 面向开发者的诊断信息另行提供（日志文件），不与用户主流程混排
- ~~待评估：§8.2 阶段 3 的 ConsolePanel 当前将引擎日志直接呈现在主界面，与本条存在潜在冲突~~ → **2026-09-18 W-19 裁定：ConsolePanel 已移除**（GUI 不再呈现引擎日志；开发者经 `logs/gui_*.log` 文件排查；实现见 `gui/worker.py` 移除 loguru→GUI 转发、`gui/page_progress.py`/`gui/page_report.py` 移除右侧容器、`gui/widgets.py` 删除）

**5. 与既有条款的关系**

- `docs/dev-spec.md` §14（GUI 界面规范 [28]-[32]）与 §17（print 输出规范）继续有效；本节为其**上位原则**，冲突时以本节为准

---

## 9. 已知阻塞与规避策略（复核于 2026-08-18，2026-08-24 按 v3.1 口径修订）

> 来源：代码实际行为 + 审计结论；2026-08-21 自 AGENTS.md §11 下沉（v2.2 升级，用户裁决 R-4 方案 A）。这些阻塞不影响 GUI 框架实现，但 GUI 生成 JSON 和操作目录展示时需主动规避。

| # | 阻塞描述 | 状态 / 规避策略 |
|---|----------|----------------|
| 1 | 模板 JSON 用 `column_mapping`/`new_column`，代码读 `mapping`/`column` | ✅ 已修复（2026-08-15）：8 个工作流模板与 workspace/last_config.json 键名已统一为代码侧 `mapping`/`column`（依据 gui/forms.py#294、steps 代码）；注：该批 v3 模板已随架构重构归档清理（原 `_temp/BackUp/workflows-v3-20260822/` 已于 2026-09-14 清理） |
| 2 | `pandas_transform` 模板缺 `dtype` 字段 | ✅ 已修复（2026-08-15，v3 口径历史记录）：test_pandas_transform.json 与 test_full_etl.json 已补 dtype（keys 即 SELECT 列）；该步骤已随 v3 steps/ 废弃，事项关闭 |
| 3 | PPT 导出为预留能力：v3 `export_ppt` 步骤 validate 阶段抛 `NotImplementedError`；v3.1 重构后该步骤随 `steps/` 废弃，`BUILTIN_OPS` 用户操作目录无 PPT 导出操作 | 仍有效（能力预留性质不变）：GUI 操作目录中不显示 PPT 导出；实现时在 `ops/` 新增操作函数并登记 `BUILTIN_OPS`（见 §3.3 关键规则），届时引入 python-pptx 依赖 |
| 4 | `test_data/` 和 `templates/outputs/` 资源为空 | ✅ 已修复（2026-08-15）：模板输入路径已统一指向 `../Test/input/测试输入0~3.xlsx`（2026-10-24 按目录实测校正：`Test/input/` 现有 `测试输入0.xlsx`～`测试输入3.xlsx` 四个文件）；`templates/outputs/` 已创建最小占位模板。⏸️ 测试暂缓（2026-08-18 用户裁决）：测试输入为通用占位数据（列1-列10），与模板 SQL 引用的业务列名（区域/电费/月份）不匹配；按相关规定测试工作暂不在本仓库执行，端到端验证事项暂缓。**注**（2026-09-14，R3）：该批占位模板已宣布清理、全部失效，`outputs/` 现仅留 `.gitkeep`。**豁免登记**（2026-09-20，人工批准）：DAG 可视化重构新建 `rpa_engine/tests/` 作为「重建验证通道」，仅承载重构移植清单（五类边契约不变量 + GUI→执行参数翻译 E2E），纯 parse/validate 层、不依赖测试输入数据，与本条「端到端业务测试暂缓」并行不冲突；端到端业务测试仍暂缓 |

## 10. 架构刚性边界（ETL 底层不可偏离）

> 效力来源：经 `AGENTS.md` §2.5 背书具 **[约束]** 效力；上位红线见 `AGENTS.md` §2.2 条 9。本节是红线的细则化，冲突时以 `AGENTS.md` 为准。

**1. 架构基线（不可替换）**

- 数据表驱动参数文件（`tables[]` + `steps[]`，见 §1）
- **SQLite** 为中间数据载体与步骤间传递枢纽（见 §4、§5）
- **JSON 参数文件为业务逻辑唯一载体**（引擎与业务逻辑分离，见 §7）
- 三段式执行：parse → validate → execute（见 §2）
- `ops/` 的 `BUILTIN_OPS`（10 项）为**唯一**操作扩展点（见 §3、§6）

**2. 允许的扩展方式**

- 新增 `ops/` 操作函数并登记 `BUILTIN_OPS`
- 新增 GUI 页面、控件、交互形态
- 新增参数字段（向后兼容，经 `schema_version` 管理）
- **新增渲染与交互层能力（不改数据流）**

**3. 禁止的替换方式**

- 绕过 JSON 参数文件、在代码中硬编码业务逻辑
- 以 DataFrame 直接传递替代 SQLite 表名传递
- 替换或移除 SQLite 中间层
- 把 ETL 主流程搬进 GUI 层——GUI 只能经 `gui/worker.py` 的 EngineWorker 调用 `engine.executor.execute_workflow()`（见 §8.1）

**4. 与「最高目标原则」（§8.4）的关系**

- JSON 参数文件仍是业务逻辑唯一载体，只是**由 GUI 代码生成与维护、对用户隐藏**；两条约束互补，不冲突

**5. 对本次 DAG 可视化重构的约束**

- **DAG 可视化组件属前端**（GUI 交互层，见 §8）；对 DAG 的重构属于第 2 条第 4 项（**前端**渲染/交互层能力扩展），**后端（ETL 技术底层）零改动**——不得改动数据流、引擎契约与 §8.1 集成边界。
