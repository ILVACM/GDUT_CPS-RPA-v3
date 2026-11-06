# 任务记录：M0 启动 · M-a 数据层落地（graph_edges + 翻译层 + 注册表补齐）

> 日期：2026-09-20｜执行：模式 B（1 个只读探查子 agent + 主控实施）｜状态：已完成（R1／M-a；M-b~M-e 待续）

## 摘要

人工下达 M0 启动指令（「根据方案执行操作」）。按 `_temp/DAG-rebuild/plan.md` §2.4 阶段序执行 **M-a 数据层**：新建 `gui/graph_edges.py`（五类边单一事实源）与 `rpa_engine/tests/`（豁免通道），补齐 `models.py` 注册表与翻译层（弃用闭包、覆盖两步链、STEP_DESC、produces_table），`forms.py` 增 output_mode 控件与注册表单一源，`styles.py` 落 GRAPH_* 常量组，`node_graph.py`/`page_operation_config.py` 做 ID 口径与 edges 装配的最小改动，`main_window.py` 编辑态导出改未过滤。**本轮零渲染行为变更**（edges 仅承载不消费，M-b 才切换）。

## 用户输入

- 「好，根据方案执行操作。」（三项裁定问题被跳过 → 按推荐锁定：只做 M-a 后停 / 批准 tests 豁免 / StepLayoutEntry 改持 ID）

## Agent 理解与决策（含计划外细化）

| # | 决策 | 说明 |
|---|---|---|
| D1 | 本轮范围＝M-a | node_graph 789 行重写（M-b）留下一轮，风险分离 |
| D2 | 批准新建 `rpa_engine/tests/` | 豁免登记于 AGENTS §6 + architecture §9 #4（端到端业务测试仍暂缓） |
| D3 | StepLayoutEntry 表字段改持表 ID | 与边契约同源；渲染层经 `_to_display_data` 单点翻译保视觉等价 |
| D4 | M-a 不改渲染行为 | `GraphLayoutData.edges` 仅承载；rebuild 不消费 |
| D12 | **STEP_DESC 由 STEP_CATALOG 派生**（非另立文案） | 计划原文"文案新拟"会产生第二语义源，与 M21 禁双源原则冲突；改为派生视图 + `step_desc()` 访问器，语义等价且零漂移风险 |
| D13 | `extra_input_ids()` 落 **models.py**（计划原定 graph_edges） | 弃用闭包也需该派生，落数据层可被闭包与边派生共用，避免双实现 |
| D14 | `EdgeSpec` 属性名 `src/dst`，`to_dict()` 输出契约键 `from/to` | `from` 为 Python 关键字；契约以字典形态为准（测试断言 7 键恰等） |
| D15 | 派生表显示名统一走 `alias_of`（格式改 `·结果`） | 消除 `(结果)`/`·结果` 双格式；page 改调 alias_of，视觉与改前一致 |

## 执行流程

1. **探查**（只读子 agent）：核实 models/forms/styles/page/node_graph/main_window 全部锚点与 4 处生产落差（命名空间、produces_table 缺失、派生表名双格式、extra_inputs 未收敛）。
2. **E2/E3 models.py**：typing 补 `Set`；新增 `STEP_DESC`/`step_desc()`/`produces_table()`/`extra_input_ids()`；`__init__` 增 `deprecated_tables`；`reset` 同步清理；新增 `deprecate_table()`/`_deprecated_closure()`（传递闭包）；`to_dict(include_deprecated=False)` 重写（闭包过滤 + output_mode 翻译 + 前端键剔除 + overwrite 两步链合成 copy_table 步）；`load_from_dict` 清弃用态 + 兼容遗留键；M19 两处注释；`alias_of` 格式统一。
3. **E1 graph_edges.py**（新建）：`START_KEY/END_KEY`、`EDGE_TYPES/EDGE_FIELDS`、`TableSpec/StepSpec/EdgeSpec`、`missing_refs/normalize_end/end_step/specs_from_model/build_edges/edges_to_dicts`；生成顺序 flow→reference|deprecated（表列序→消费者序）→produce→dangling；key 唯一防重。
4. **E4 forms.py**：新增 `_OUTPUT_MODES` 与 `BaseParamForm._add_output_mode()`；FilterForm/DedupForm 增「结果保存方式」并在 `get_params` 返回 `output_mode`；CopyTableForm 文案取 `produce_label("copy_table")`；`_FORM_REGISTRY` 改由 `STEP_CATALOG` 键集派生（`_FORM_CLASSES` + `_build_registry()`）。
5. **E5 styles.py**：新增 GRAPH_* 常量组 28 项（画布/表节点/五类边/起止/状态描边/气泡/详情文字），取值以 SampleCode 视觉词表为准；L8 注释改「节点态+图态唯一来源」。
6. **E6 node_graph.py + page_operation_config.py**：`GraphLayoutData` 增 `edges`/`id_to_display` 可选参；`StepLayoutEntry` 文档改 ID 口径；新增 `_to_display_data()` 单点翻译并在 `rebuild` 入口调用；page 导入 `build_edges/specs_from_model/extra_input_ids`，`_refresh_graph` 改传 ID、派生名走 `alias_of`、额外输入走 `extra_input_ids`、装配 edges 与映射传入。
7. **E7 main_window.py**：`_save_last_config`、`_staged_config`、`restore_config` 三处编辑态导出改 `include_deprecated=True`；`save_json`/`_last_run_config`/存模板保持默认过滤。
8. **E8 tests**：新建 `rpa_engine/tests/{__init__,test_graph_edges,test_translation}.py`。
9. **E9 治理**：AGENTS §6 豁免登记 + 锚点 + §8 主线；architecture §9 #4 豁免登记；rpa_engine/README 目录树；plan.md §1.9/§2.4 完成态标注；本记录。

## 涉及文件

| 文件 | 改动 |
|---|---|
| rpa_engine/gui/graph_edges.py | **新建**（约 300 行，五类边单一源） |
| rpa_engine/gui/models.py | 注册表 4 符号 + 翻译层（弃用/闭包/to_dict 两步链）+ M19 注释 + alias_of |
| rpa_engine/gui/forms.py | `_OUTPUT_MODES`/`_add_output_mode`/Filter·Dedup output_mode/CopyTable 文案/registry 单一源 |
| rpa_engine/gui/styles.py | GRAPH_* 常量组 28 项 + 注释 |
| rpa_engine/gui/node_graph.py | GraphLayoutData 2 参 + StepLayoutEntry 文档 + `_to_display_data` + rebuild 入口翻译 |
| rpa_engine/gui/page_operation_config.py | 导入 + `_refresh_graph` ID 口径/alias_of/extra_input_ids/edges 装配 |
| rpa_engine/gui/main_window.py | 3 处编辑态导出 include_deprecated=True |
| rpa_engine/tests/ | **新建**（__init__ + 2 测试文件，22 用例） |
| AGENTS.md / docs/architecture.md / rpa_engine/README.md / _temp/DAG-rebuild/plan.md | 豁免登记、锚点、主线、目录树、完成态标注 |

engine/ops 与 SampleCode **零改动**（两步链方案确保零后端改动；SampleCode 为冻结基线）。

## 验收

- ✅ `py_compile` 7 个改动文件 exit 0。
- ✅ `cd rpa_engine && python -m unittest discover -s tests -v` → **Ran 22 tests OK**（test_graph_edges 14：12 项契约不变量 + 生成顺序 + 目录键集；test_translation 8：plan §4.7 全用例）。
- ✅ 启动自检 `run_self_check()` **ALL_OK=True**（6 项，含项4b）。
- ✅ **零视觉回归**（offscreen 实测）：ID 新口径 vs 显示名旧口径渲染 **44 图元逐项全等**（identical=True）；分类计数全等（tables 5/steps 5/conn 10/dots 9/markers 4/forks 2/arrows 6）；sceneRect 全等（1300×718）。
- ✅ 边派生实测：11 条 = flow 2 / reference 6 / produce 3 / deprecated 0 / dangling 0；`to_dict()` 字段恰为 7 键 `from/key/label/missing/role/to/type`。
- ✅ 契约断言：两步链导出 6 步（S2 filter 保留 T3 + S2_cp copy_table→`{"output_table":"t1"}` 物理名）、下游引用不变、parse+validate 全通；弃用级联（输入表→仅余 aggregate／派生表→余 convert+aggregate）；全弃用→steps/tables 皆空；load 回归剔除遗留键且不还原弃用态。
- ✅ grep 对账：`gui/` 内 produces_table/STEP_DESC/deprecated_tables/_deprecated_closure/include_deprecated/build_edges 均命中；`output_mode` 不入导出结构（用例④⑤断言）。
- ✅ doc-governance §4：Step1 AGENTS 自洽（锚点/§8/日期一致；容量三口径实测＝含 CR **7,679**、LF 归一 7,483、行数 196、**余量 321≥200**；行尾按 §10.3 复归 CRLF——首轮编辑后余量曾降至 140，按 §10.2 下沉锚点/§8 冗余明细后达标）；Step2 五项校验（链接：新 task-record 与 tests 路径存在；元信息：architecture last-updated→09-20；层级一致；INDEX 无涉本轮；无约束力误标）；Step3 README 同步（rpa_engine/README 目录树已更新 graph_edges 与 tests；根 README 无涉）。
- ✅ 残留清零：`display_to_id`（page 旧映射）与旧 `_FORM_REGISTRY` 字面量字典均 0 命中；新符号 grep 命中数为 produces_table 6 / STEP_DESC 2 / deprecated_tables 10 / _deprecated_closure 2 / include_deprecated 7 / build_edges 5 / extra_input_ids 8 / GRAPH_ 32 / _add_output_mode 3 / _to_display_data 4。

## 关闭标识

**本轮（R1／M-a）完成，待续**：M-b 画布重写（M1-M13：node_graph 图元/布局/边消费/起止标识，`_to_display_data` 翻译随消费点移除）→ M-c 页面集成（M14/M15/M17/M25：工具栏分组、连线说明、表详情面板与弃用按钮、覆盖二次确认、空流程拦截）→ M-d 校验（M22 已执行；补 produces_table 自检可选）→ M-e 文档回写（正本 §5.8 测试口径同步 `rpa_engine/tests/` + doc-governance §4）。

**待人工**：真机复核 M-a 后配置页视觉（应与改前完全一致）；W-20 exe 重建；M-b 启动指令。
