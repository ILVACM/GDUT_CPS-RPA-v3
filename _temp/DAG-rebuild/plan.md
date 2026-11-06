# DAG 可视化正式重构计划

> 生成：2026-09-18｜载体：`_temp/DAG-rebuild/plan.md`（执行级计划，无约束力）  
> 执行路由：执行 agent 首跳 AGENTS.md §3 执行模式判定（A/B/C/D）后再开 M；本条目的文件属 `_temp/` 豁免治理。  
> 分工：**目标规范权威 = `docs/plan/DAG_refactor_plan.md`（正本，方案态）**；本文件 = 行号级执行计划（人工裁定①：并存分工）。  
> 最高依据：**`SampleCode/`（= 原 `experiments/W-03_dag_visualizer`，2026-09-17 细节优化后口径）**；旧文档与 SampleCode 冲突时以 SampleCode 为准（纠偏点见 §1.10）。  
> 提取来源（已并入本文件，原件随 09-18 清理删除）：`plan/dag-blueprint-ambiguities.md`、`experiments/W-03_DAG_visualization_plan.md`、`experiments/_agent/CONTRACTS.md`(v1.1)、`experiments/_agent/DECISIONS.md`(§7/§8)、`experiments/W-03_dag_visualizer/W-03_dynamic_dag_deep_test_PLAN.md`。  
> **2026-09-18 裁定落地**：A 类全部以 SampleCode 为准——F-1/F-2/F-3 已回写正本、M22 纳入（含 M18 前置，均已执行）；B 类人工验证关闭（N1-N15 真机 + git status）；C 类改道已执行（正本/AGENTS/backlog/analysis）；W-14/W-15 同批闭环。  
> **2026-09-20 翻译契约裁定落地**：D-1=B 弃用前端翻译降级 / D-2=a business_desc 静态 / D-3 覆盖映射+二次确认 / D-4 演示不补转换 / D-5 E2E 纳入——详见 §4 翻译契约与 M23-M26。  

---

## 1. 最终重构目标效果要求（以 SampleCode 为准）

### 1.1 设计理念已明确性结论

**已明确，且经人工真机验证（09-15）与 61 用例/11 场景自动验证（09-17）。** 核心理念（AGENTS §2.1 条 6 最高目标原则）：目标用户为无技术背景企业文员，一切交互从简、易懂，技术细节完全隐藏。落到 DAG 可视化的六条已定稿理念：

1. **业务化步骤卡片**：序号徽章 + 操作中文名 + 一句话业务说明，文员不用猜参数（SampleCode `frontend/dag_viewer.py:127-261`）。
2. **端口永不绘制**：无端口圆点、无开关、无技术视图入口；端口词表仅存生产蓝图数据结构（原 W-03 方案 P0-①，DECISIONS §7.1）。
3. **画布无常驻图例**：语义由颜色/线型/箭头/节点角标/产出边标签 + 右侧详情面板「连线说明」三层承载（ADR-1/ADR-4，09-17）。
4. **起止标识人话化且动态自适应**：「▶ 开始」/「■ 结束」装饰标识 + 起止连接边；开始锚首步、结束锚 is_end 步（无则末步 fallback）；不占布局行、不可选中/删除（ADR-2）。
5. **失败人话原因**：红色卡片下方气泡直接给出可转述的中文原因（P0-⑥）。
6. **右面板为配置唯一入口**：画布严格只读（零拖拽/零连线编辑），参数表单 schema 驱动（ADR-3/§8.5 正本口径）。

### 1.2 功能与交互要求

| # | 交互 | 要求（SampleCode 行号） |
|---|---|---|
| 1 | 缩放 | Ctrl+滚轮 ×1.15，钳制 [0.40, 2.50]，锚定鼠标（`dag_viewer.py:569,573-584`） |
| 2 | 平移 | 空白左键拖拽；按下即清选中；滚动条按缩放比换算（`:586-617`） |
| 3 | 全览 | `fit_all()` = `fitInView(content±20, KeepAspectRatio)`（`:1322-1326`） |
| 4 | 点击详情 | 点节点→右侧详情（步骤/表两套 HTML）+「连线说明」行（`:1103-1107,1215-1258,1260-1319`） |
| 5 | 选中高亮 | 步骤选中→其引用边/产出边/悬空边高亮 #2b7cd3 2.5px、其余淡化 0.3；表选中→其泳道+接入段+产出边高亮（`:1023-1093`） |
| 6 | 模拟运行 | QTimer 800ms 按执行序推进；含 fail_reason 者置 failed 并定格停止（`:1329-1366`） |
| 7 | 添加步骤 | 注册表驱动主按钮 4 项 +「更多功能 ▾」下拉 5 项；锚点三态插入（无选中=末尾且结束步前/选中步骤=其后/选中表=产出步骤或最后消费者后）（`:694-703,1159-1168`；后端 `_resolve_insert_index` `mock_backend.py:380-421`） |
| 8 | 删除步骤 | 二次确认弹窗（文职文案，含"产生的数据表也会消失"）→级联删产表→下游悬空显式（`:1170-1182`） |
| 9 | 弃用/恢复 | 表级显式弃用；弃用表灰虚线保留显示、引用边转灰虚线、消费者转待配置（`:1197-1203`） |
| 10 | 参数保存 | `ParamPanel.saved(dict)`→`update_params`→全量联动刷新；校验失败红字回填不发射信号（`:1184-1195`；`param_panel.py:99-124`） |
| 11 | 右面板三态 | 步骤=表单+删除；表=弃用/恢复；无选中=空（`:1133-1157`） |
| 12 | 顶部信息条 | 流程名（=运行参数文件名称，对用户禁用"参数文件"术语）+「已完成 N/M」+四色迷你进度条（`:528-529,746-757`；原方案 §3.5 澄清） |

**只读红线（不可偏离）**：全库无 `setFlag(ItemIsMovable)`、无连线编辑入口；`Qt.NoButton` 六处＝ProduceEdgeItem(`:446`)、FlowEdgeItem(`:502`)、悬空短桩(`:918`)、⚠(`:923`)、起止标识文字(`:993`)、空态提示(`:1014`)。

### 1.3 视觉要求

**色板全表**（`dag_viewer.py:82-104`）：STATUS_FILL{pending #ffffff/running #fdf3c0/done #c8f0c8/failed #f6caca/selected #cfe8ff}；STATUS_STROKE{pending(#aaaaaa,1.0)/running(#f0ad4e,2.0)/done(#5cb85c,1.0)/failed(#d9534f,2.0)}；SEL=HOVER=(#2b7cd3,2.0)；HIGHLIGHT=(#2b7cd3,2.5)；TABLE_FILL #2b7cd3/TABLE_STROKE #1a5ca8/TABLE_HOVER #3a8ce2/TABLE_FOCUS #0d47a1；LANE_IN #999999/LANE_DEV #4a90d9/ACCESS_C #888888；BUBBLE_BG #fdeceb/BUBBLE_BORDER #d9534f；INCOMPLETE_STROKE(#f0ad4e,2.0)；DEPRECATED_FILL #9e9e9e/DEPRECATED_EDGE #757575；DANGLING_C #d9534f；PRODUCE_C #2ecc71/PRODUCE_LABEL_C #2e7d32；START_C #2ecc71/END_C #d9534f；CANVAS_BG #fafafa（歧义 C 定稿）。

**五类边词表**（ADR-3，契约见 §1.4）：

| type | 视觉 | 语义 |
|---|---|---|
| reference | 灰(输入列)/蓝(派生列)实线 2.0/1.5 + 末端箭头 | 步骤使用某表（自上而下汇入卡片） |
| produce | 绿 #2ecc71 实线 2.0 **竖直向上** + 白底标签「新表」/「复制新表」 | 步骤产出新操作表（卡片顶边右锚点 ccx+35 → 表头底线 118） |
| flow | 绿/红实线 1.5 + 箭头 | 开始→首步（ccx−35）；末步→结束（ccx，失败避让 +32） |
| dangling | 红 #d9534f DashLine 1.5 短桩 + ⚠ + 角标「输入缺失」 | 下游输入缺失（绝不静默） |
| deprecated | #757575 DashLine 1.5 | 引用已弃用表（reference 的样式变体） |

**优先级**：边样式＝高亮 > deprecated > 常态色（dangling 独立图元不参与）；节点描边＝选中 > 悬停 > 待配置(橙) > 状态色；角标＝「输入缺失」(红) > 「待配置」(橙)；填充链＝failed > running > done > selected > pending。

**可辨识差异矩阵**（无图例验收依据）：reference↔produce＝颜色+方向+标签(3 维)；reference↔deprecated＝线型+线色+角标(3 维)；reference↔dangling＝线型+颜色+伴随符号+几何(4 维)；produce↔flow＝宽度+端点+标签(3 维)；flow(结束)↔dangling＝线型+箭头+伴随符号(3 维)。

### 1.4 数据模型要求

- **tables 字段全集**：`key/display/is_input/producer_step/deprecated/business_desc`（`mock_backend.py:8-15,281-288`）。
- **steps 字段全集**：`key/seq/name/op_type/business_desc/target_table/extra_inputs/output_table/is_end/params/config_state` + 派生 `missing_refs`（`:58-69,436-449`）。
- **edges 契约（v1.1，前后端边界）**：`get_dag()["edges"]` 深拷贝；五类 type；**7 字段** `key/type/from/to/role/label/missing`；key=`type:from:to[:role]` 冲突加 `#n`，全集唯一且 recompute 幂等；生成顺序 flow→reference|deprecated(表列序→消费者序)→produce(步骤序)→dangling(步骤序)（`:176-253,326-338`）。
- **4 条计数不变量**：count(flow)=2(steps 非空)或 0(空)；count(produce)=产表步骤数；count(reference)+count(deprecated)=Σ有效引用数；count(dangling)=Σlen(missing_refs)。
- **派生规则**：`missing_refs` 口径严格限定"表不存在"（弃用/缺参/输入不足不计入，`:134-148`）；`is_end`＝数组中最后一个 kind=="end" 步骤（`_normalize_end :151-163`，对齐生产 `page_operation_config.py:525`）；结束锚点＝is_end 步否则末步（`_end_step :166-173`）；虚拟 key `__start__/__end__` 避开 T/S+数字命名空间且不入 `get_node`（`:43-44`）。
- **recompute 六步**：seq 重排→表集合派生(新产出建表/孤儿回收)→match_table↔extra_inputs 同步→is_end 规范化→missing_refs+config_state→重建 edges（`:256-316`；模块加载即重算一次 `:532`）。
- **功能元数据注册表**（`func_registry.py:18-61`）：9 项 `filter/dedup/mapping_match/aggregate/copy_table/merge_tables/rename_columns/convert_dtype/export`；字段 `name_cn/kind(end|merge|fork|sequential)/produces_table/produce_label("新表"|copy_table="复制新表"|不产表=None)/inputs{target,extra_min}/params[(key,中文标签,类型,必填[,默认])]`；类型 text→QLineEdit、table→QComboBox、enum:a|b→QComboBox；`MAIN_BUTTONS` 4 / `MORE_BUTTONS` 5；`_OVERWRITABLE=(filter,dedup)`（output_mode=overwrite_target 不产表）。**正式层级=后端 ops 侧（STEP_CATALOG/OUTPUT_OPS/STEP_KIND 扩展），GUI 只读**。

### 1.5 布局与渲染要求

**常量全表**（`dag_viewer.py:60-79,99`）：`COL_CX0=120, COL_DX=240`（col_cx=120+240j）；`HEADER_BOTTOM=118`；`TABLE_W/H=160/40`；`STEP_W/H=140/70`；`ROW_CY0=193, ROW_DX=100`（row_cy=193+100r）；`STACK_SP=16`；`ARROW_L/HW=9.0/4.5`；`SCENE_MARGIN=40, FIT_MARGIN=20`；`ZOOM 0.40~2.50`；`ANCHOR_DX=35`；`FLOW_LEN=12, FLOW_GAP=6, MARKER_TEXT_H=16, END_AVOID_GAP=32`；`EDGE_Z=-4`；表头 y：输入 60 / 派生 78 错位（示"由步骤产出"）。

**rebuild 11 步顺序与 z 层级**（`:759-938`）：①clear+容器重置 ②状态刷新 ③步骤几何+content 包围盒 ④reference/deprecated 泳道 z=−5 ⑤横向接入段 z=−3 ⑥produce 产出边 z=−4 ⑦表节点 z=0 ⑧步骤卡片 z=1 ⑨悬空短桩+⚠ z=−2 ⑩起止标识或空态提示 z=2 ⑪sceneRect(±40)+高亮刷新。**穿越处置**：边 z<节点 z，被不透明卡片遮蔽（同正本 §4.5 L297）。

### 1.6 状态与事件要求

- 状态四值 `pending/running/done/failed`，**无"未启动"档**（歧义 F 定稿；`mock_backend.py:40`）。
- 事件：`ParamPanel.saved=pyqtSignal(dict)`（`param_panel.py:21,124`）；图元 `on_click(kind,key)` 回调约定（StepCardItem→("step",key)、TableItem→("table",key)）；窗口级 `reload_data()/rebuild_scene()/_apply_visuals()/fit_all()/selected`。
- 模拟运行定格语义：遇 fail_reason 置 failed 并停止推进。

### 1.7 API / 依赖 / 性能要求

- **mock_backend 公共 API（11）**：`get_meta/get_dag/get_node/set_status/reset_state/recompute/add_step(op,anchor)/remove_step/update_params→(ok,state,missing)/deprecate_table/export_workflow`（导出剔除 missing_refs、不含 edges）。
- **依赖**：零第三方新增；伪后端纯标准库（copy/json/pathlib）；前端仅 PyQt5 5.15.2；Python 3.11.15；conda `CPS-GPES_RPA-py311`。
- **性能口径**：演示为全量重绘（6-20 步无压力）；**生产需差量刷新/虚拟化渲染/焦点模式，列入 M 里程碑（正本 M0-M5），不在本轮行号级范围**。
- **数据可替换**：换 `data/workflow_demo.json` 即换流程，接口不变。

### 1.8 与 RPA 引擎 GUI 的集成边界

- **前端**＝GUI 交互层（含 DAG 可视化）；**后端**＝ETL 技术底层（engine/ops/SQLite）（AGENTS §2.2 条 9、architecture §8）。
- **边界契约**＝edges 五类边 + 注册表字段：GUI 只消费 `get_dag()` 形态数据，不 import 生产代码（SampleCode `func_registry.py:3-4` 自述同源对齐）。
- 集成点映射：`func_registry↔models.py:19-50`；`is_end/kind↔page_operation_config.py:524-525`；`rebuild_scene+fit_all↔page_operation_config.py:510-537`；`set_status/四态↔page_operation_config.py:542-556`；`START_C/END_C↔node_graph.py:59-60`；`param_panel↔forms.py _FORM_REGISTRY/try_apply 模式`。

### 1.9 验收标准与不可偏离项

- 自动：61 用例全绿（15 静态+46 动态含 EdgeModelTest 12；11 场景 offscreen 产出；`--offscreen` 计数 steps=6 tables=6 lanes=6 access=6 produce=4 flow=2 markers=2）——示范基线留存于 SampleCode；
- 自动（生产，M-d 验收落点=方案①）：**`rpa_engine/tests/`（新建目录）＝移植清单落点**，全绿＝`test_graph_edges.py` 12 项边不变量（M16）+ `test_translation.py` 8 用例（M26，含 load 回归）；SampleCode 其余用例（静态 15+动态 34）属演示后端专属语义（mock API/reset/插入三态等），生产对应语义由 M26 E2E+M25 真机清单+自检项4b 承载，**不作 1:1 移植**，原 61 用例作为基线证据留存 SampleCode；与 AGENTS §6「Test/ 端到端测试暂缓」属并行通道，**豁免已于 09-20 人工批准并登记**（AGENTS §6 + architecture §9 #4）；目录已随 M-a 建立，实测 `test_graph_edges.py` 14 项 + `test_translation.py` 8 用例全绿。
- E2E 翻译（M-d，D-5 09-20 裁定）：**`rpa_engine/tests/test_translation.py` 全绿（8 用例）**——GUI 模型→to_dict→parse_workflow→validate_workflow 闭合可执行，弃用闭包过滤/覆盖两步链/STEP_DESC/load 回归断言通过（用例清单见 §4.7；与上行同批「测试暂缓豁免」）。
- 真机：README 人工清单 11 项 + N1-N15（文字渲染、五类边逐对指认、起止自适应、复制分支、只读红线）。
- 不可偏离：AGENTS §2 红线 9 条（ETL 分层/SQLite 核心/JSON 唯一业务载体/GUI 唯一入口/共享连接/ops 注册/禁改遗留/禁硬编码脚本/表名传递/架构刚性）；画布只读；注册表驱动禁硬编码。

### 1.10 纠偏点表（旧文档 vs SampleCode，以 SampleCode 为准）

| # | 旧文档口径 | SampleCode 现口径 | 依据（纠偏状态：已全部落地） |
|---|---|---|---|
| 1 | 画布右下角 7 词条图例（正本 §8.6 L523） | **无常驻图例**，三层补偿 | ADR-1（F-1 已回写正本 09-18） |
| 2 | "终点/起点"文字标签取消、不设 markers（正本 §4.3 L267/§3.4 L153） | 装饰式起止标识 + flow 边，动态自适应 | ADR-2（F-2 已回写 09-18） |
| 3 | lane/access 二分边 | **五类边** edges 单一事实源 | ADR-3（F-3 已回写 09-18） |
| 4 | is_end 由数据静态给定 | is_end 派生+唯一性规范化；add_step 按 kind 派生 | 09-17 语义修复 |
| 5 | 结束标识固定 bottom+8 | 失败避让 END_AVOID_GAP=32（线 +38..+50、文字 +54） | ADR-2 实施偏差登记 |
| 6 | 边样式优先级 dangling>deprecated>高亮 | 高亮>deprecated>常态；dangling 独立图元 | 09-17 复核修正 |
| 7 | STEP_NODE_H=54 | **70**（卡片含徽章+标题+业务副标题） | W-03 P0-② |
| 8 | 输入表头 58（含 18px 调序条） | **40**，调序条取消（C1） | 09-15 收敛 |
| 9 | 双视图/端口/搜索/GUI 导出/调序按钮/技术人员 GUI 分析 | **全部取消**（7 项） | DECISIONS §7.1 |

---

## 2. 修改思路

### 2.1 正式引擎六部分盘点（作用 / 现状问题 / 为何改）

| 部分 | 作用 | 现状问题 | 为何改 |
|---|---|---|---|
| `gui/node_graph.py`(789 行) | 配置页内嵌节点图：TableNode/StepNode/_StatusDot/ConnectionItem/_DotMarker/_ForkMarker + rebuild | ①STEP_NODE_H=54 无业务副标题；②TableNode 带 left/right 调序按钮（C1 已取消）；③交点圆点+独立箭头 polygon(z=6) 非边语义；④merge_consume 提前截断(592-605)与 75px 骑线阈值(655)违背正本 §4.3；⑤起点/终点文字标记(667-675/691-699)与端口语义混用；⑥无 produce/flow/deprecated/dangling 边概念；⑦颜色硬编码未迁 styles | 承载最终视觉/交互目标的唯一画布组件，须整体对齐 SampleCode |
| `gui/page_operation_config.py`(784 行) | 配置页：左图右面板 splitter、+功能按钮、参数面板、_refresh_graph、校验 | ①`table_reorder_requested` 接线(88)+槽(407-422)属已取消能力；②按钮直读 STEP_CATALOG 无 MAIN/MORE 分组；③_refresh_graph(448-537) 手工拼 StepLayoutEntry，无 edges；④面板无「连线说明」 | DAG 数据装配与交互入口，须改为 edges 驱动 |
| `gui/models.py`(393 行) | STEP_CATALOG/OUTPUT_OPS/STEP_KIND/classify_step/available_table_ids/产表编号/renumber/default_params | 缺 produce_label、is_end_op 派生；产表编号与"产表列=锚列"关系无注释 | 注册表正式层级，须补边标签/结束语义字段 |
| `gui/forms.py`(515 行) | BaseParamForm/_check_columns/try_apply/_FORM_REGISTRY/CopyTableForm | CopyTableForm 说明文案未体现"复制新表/新分支"；registry 不读 produce_label | 面板 schema 驱动与标签唯一来源 |
| `gui/styles.py`(183 行) | COLOR_* 五态 + build_qss | **无 GRAPH_* 组**；node_graph 颜色硬编码（正本 §4.3 L266 要求迁入） | 配色唯一来源收敛 |
| `gui/app.py`(255 行) | 启动自检（含操作目录注册逐键比对 95-120） | 自检不含注册表新字段 | 防漂移闸门 |
| engine/ops（集成边界，不改） | executor 表 ID 映射(106-130)、parser StepDef(39-52)/steps 解析(142-175)、validator 前向引用(94-126)、step_executor BUILTIN_OPS(46-103)/_translate_table_id(115-126)/产表名(188-202) | 无（本轮不动） | edges 的 from/to 语义须与其表 ID/顺序语义一致，仅作边界说明 |

> 注：`models.py` 现 393 行、`app.py` 现 255 行（M18 已执行追加所致 09-18）；行数随后续 M 执行继续变化，**以 grep 实测为准**。

### 2.2 目标架构

1. **edges 单一事实源进 GUI 数据层**：新增 `gui/graph_edges.py` 承载 `_build_edges()`（契约=CONTRACTS v1.1），`_refresh_graph` 改为装配 edges 传入 scene；node_graph 不再自行推导消费关系。
2. **6 图元类替换 5 旧类**：LaneItem/AccessItem/ProduceEdgeItem/FlowEdgeItem(+StepCard/TableNode 改造) 替换 _StatusDot/ConnectionItem/_arrow_polygon/_DotMarker/_ForkMarker；箭头并入边图元，z 6→−3/−4。
3. **颜色迁 styles.py GRAPH_* 组**；node_graph 仅引用。
4. **注册表增 produce_label/is_end_op**；forms/按钮/边标签全部注册表驱动。
5. **起止标识**：装饰图元+flow 边（M11，F-2 已于 09-18 裁定，可执行）。

### 2.3 SampleCode → 正式代码映射表（26 条 M 全量对账；阶段划分见 §2.4）

| Mn | SampleCode 位点 | 正式代码目标位点 | 阶段 · 一句话目标 |
|---|---|---|---|
| M1 | `dag_viewer.py:60-79,99` 常量 | `node_graph.py:42-51` | M-b · 布局常量切 SampleCode 集（卡片 70/表头 118/ROW_CY0 193…） |
| M2 | `dag_viewer.py:82-104` 色板 | `styles.py` GRAPH_*（M20 承载）+ `node_graph.py:54-60,83-85` 引用改道 | M-b · 颜色迁 styles 唯一来源 + 五类边独立色值 |
| M3 | `dag_viewer.py:264-338` TableItem | `node_graph.py:193-264` TableNode | M-b · 表节点术语化、删调序按钮/信号 |
| M4 | `dag_viewer.py:127-261` StepCardItem | `node_graph.py:266-326` StepNode | M-b · 步骤卡片化（徽章+中文名+业务副标题+气泡） |
| M5 | `dag_viewer.py:358-522` 四边图元 | `node_graph.py:328-419` 五旧类删除替换 | M-b · 边图元替换（M-a 后 M-d 移植 EdgeModelTest 12 校验） |
| M6 | —（坐标定稿口径） | `node_graph.py:424-432` col_cx/row_cy | M-b · 坐标公式 120+240j / 193+100r |
| M7 | `dag_viewer.py:759-938` rebuild_scene 11 步 | `node_graph.py:468-548` rebuild | M-b · 消费 edges 全量重绘（z/顺序同 §1.5） |
| M8 | —（泳道延伸） | `node_graph.py:577-620` 删 merge_consume 截断 | M-b · 泳道延伸到最深消费者 |
| M9 | —（箭头并入） | `node_graph.py:622-638` 删独立箭头 polygon | M-b · 箭头并入边图元、z 降层 |
| M10 | —（ride 语义） | `node_graph.py:640-661` 删 75px 阈值 | M-b · ride=单输入同列判定 |
| M11 | `dag_viewer.py:946-1018` markers/空态 | `node_graph.py:663-699` | M-b · 装饰式起止标识+flow 边（F-2 已裁定，可执行） |
| M12 | `dag_viewer.py:560-617,1322-1326` 视图 | `node_graph.py:713-789` | M-b · 缩放钳制/空白平移/全览 |
| M13 | —（调序能力清除） | `page_operation_config.py:88,407-422` | M-b（page 文件，随画布能力收敛执行）· 删 table_reorder 接线与槽 |
| M14 | `dag_viewer.py:694-703` 按钮组 | `page_operation_config.py:121-125` | M-c · MAIN 4 主按钮 +「更多功能 ▾」QMenu |
| M15 | `dag_viewer.py:1215-1258` _edge_summary | `page_operation_config.py:184-253` 面板 | M-c · 右面板连线说明行 + 删上移/下移 |
| M16 | `mock_backend.py:176-253` _build_edges | 新增 `gui/graph_edges.py`；调用侧 `page_operation_config.py:448-537` | M-a · edges 单一事实源装配 |
| M17 | —（is_end 注释） | `page_operation_config.py:524-525` | M-c · is_end 唯一性注释 |
| M18 | `func_registry.py:18-61,117-128` | `models.py:19-50`（已执行：L67-111 追加） | M-a · 注册表扩展（produce_label/is_end_op/MAIN/MORE） |
| M19 | —（产表列注释） | `models.py` add_step 产表编号（现 L229-230）、renumber_steps（现 L257-260） | M-a · 产表列=锚列 显式注释 |
| M20 | `dag_viewer.py` 卡片/色板 | `forms.py:428-437`（CopyTableForm 文案）+ `styles.py:10-14` 后（GRAPH_* 组） | M-a · copy 文案「复制新表」+ GRAPH_* 常量组 |
| M21 | —（registry 单一源） | `forms.py:500-515` `_FORM_REGISTRY` 改为读 models | M-a · 边标签不出现第二来源 |
| M22 | —（防漂移闸门；已执行） | `app.py:95-120` 后增项4b（现 L122-152） | M-d · 注册表字段完整性自检 |
| M23 | `mock_backend.py` deprecate_table L502 / `_missing_for` L102 / `export_workflow` L510 | `models.py` to_dict L266-302 / load_from_dict L311-353 + PRODUCE_LABEL L72 后（STEP_DESC） | M-a · 翻译层：STEP_DESC+弃用闭包+to_dict 过滤与 output_mode 两步链（§4.2/4.3/4.5） |
| M24 | `func_registry.py` output_mode schema（filter/dedup） | `forms.py` FilterForm L209-226 / DedupForm L229-252 | M-a · 「结果保存方式」枚举控件（前端键 output_mode，§4.3） |
| M25 | `dag_viewer.py` 弃用交互/删除确认 | `page_operation_config.py` 表详情区 + `_on_start_clicked` L567-583 | M-c · 弃用/恢复按钮+覆盖二次确认+空流程拦截（§4.2/4.3） |
| M26 | `test_dynamic.py` 弃用/覆盖用例语义（蓝本） | 新建 `rpa_engine/tests/test_translation.py` | M-d · E2E 翻译测试 8 用例（§4.7） |

### 2.4 重构顺序、风险与回滚

顺序：**M-a 数据层**（graph_edges + models/forms/styles 字段 + M23/M24 翻译层）→ **M-b node_graph 重写**（M1-M12，逐类替换、每类独立提交；M13 同步清除）→ **M-c page 集成**（M14/M15/M17/M25）→ **M-d 校验与自检**（M22、M5 引出的 12 不变量移植 + M26 test_translation 到 `rpa_engine/tests/`）→ **M-e 文档回写**（已随 09-18 F 批完成；终验后 doc-governance §4）。

阶段-条目对账表：

| 阶段 | Mn 集合 | 交付判定 |
|---|---|---|
| M-a 数据层 | M16、M18、M19、M20、M21、M23、M24 | ✅ **已完成（09-20）**：`gui/graph_edges.py` 落地并可独立单测（14 项边不变量全绿）；注册表字段/注释/文案就位（produces_table/STEP_DESC/GRAPH_*/registry 单一源）；翻译层可独立单测（弃用闭包+两步链，8 用例 E2E 全绿）；零视觉回归（44 图元全等） |
| M-b 画布 | M1-M12、M13 | ✅ **已完成（09-20）**：node_graph.py 按蓝本整体重写（常量/零字面色/四边图元/edges 驱动 11 步重绘/起止标识/缩放钳制平移）；grep `table_reorder` 与 `#` 字面色零命中；smoke_mb 33 项全过 + offscreen 截图结构目检一致 |
| M-c 页面集成 | M14、M15、M17、M25 | ✅ **已完成（09-20）**：顶栏 MAIN 4+「更多功能 ▾」/面板三态+连线说明/is_end 注释/弃用入口+覆盖二次确认+空流程拦截齐备；main_window 失败原因透传气泡 |
| M-d 校验 | M22（已执行）、M5 引出的 EdgeModelTest 不变量移植、M26 | ✅ **已完成（09-20）**：自检 6 项 ALL_OK（313ms）；**移植清单全绿**（test_graph_edges 14 项+test_translation 8 用例＝22 全绿，§1.9 口径） |
| M-e 文档 | 无 Mn | ✅ **已完成（09-20）**：正本 §3.9/§3.10/§4/§5.8/§5.9/§8.5 落地注与过时标记回写；doc-governance §4 校验 + AGENTS 锚点 R2 + task-record（见 docs/task-records/2026-09-20-m0-mb-me-canvas-page.md） |

> 归属修订记录（09-19，消除歧义优先，对齐 §2.4 原文口径）：M21 由 A1③ 草案的 M-c 改归 **M-a**（forms 字段属数据层）；M22 改归 **M-d**（app.py 自检系校验闸门，与 §2.4 原"M-d 校验与自检"一致）；M13 归 M-b（文件虽在 page，其主旨为清除画布调序能力，随 M-b 执行）。  
> 归属修订记录（09-20，翻译契约裁定）：**M23/M24 入 M-a**（翻译层属数据层）、**M25 入 M-c**（交互入口）、**M26 入 M-d**（E2E 校验）——对应 §4 翻译契约五项裁定。
风险：①node_graph 整体重写回归面大→逐类替换+每 M 跑配置页冒烟；②edges 与 executor 表 ID 语义错位→M-a 先以 validator 用例锁定；③~~F-2 未裁定→M11 保留旧 markers+TODO~~（已裁定 09-18，M11 可执行）。
回滚：git 人工（Agent 不执行 git）；每 M 独立可回退；SampleCode 为只读参照基线不受影响。

---

## 3. 具体详细修改计划方案（仅 GUI 层；行号经双重核实，0 编造）

### M1 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\node_graph.py（阶段 M-b）
- 行号：42-51
- 原代码：布局常量 `TABLE_NODE_W=160/TABLE_NODE_H=40/STEP_NODE_W=140/STEP_NODE_H=54/DOT_RADIUS=12/H_SPACING=80/V_SPACING=100/TOP_MARGIN=60/LEFT_MARGIN=40/ROW_GAP=40`
- 修改为：SampleCode 常量集——`STEP_NODE_H=70`；删 `DOT_RADIUS/BTN_H/BTN_W`；增 `HEADER_BOTTOM=118、TABLE_TOP_IN=60、TABLE_TOP_DEV=78、ROW_CY0=193、ROW_DX=100、COL_CX0=120、COL_DX=240、STACK_SP=16、ARROW_L=9.0、ARROW_HW=4.5、ANCHOR_DX=35、FLOW_LEN=12、FLOW_GAP=6、MARKER_TEXT_H=16、END_AVOID_GAP=32、EDGE_Z=-4`
- 修改原因：卡片需容纳徽章+标题+业务副标题（P0-②）；调序条取消后表头几何收敛；起止/产出边需要锚点常量
- 影响范围：node_graph 全部几何计算、page_operation_config 的 StepLayoutEntry 装配
- 验证方式：配置页冒烟截图与 SampleCode dyn-A 几何比对；单测布局公式断言
- 备注：`_row_y` 内 `TOP_MARGIN+BTN_H+TABLE_NODE_H+ROW_GAP` 组合须同步改写为 `row_cy=193+100r`
- 前置依赖：无

### M2 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\node_graph.py（阶段 M-b）
- 行号：54-60、83-85
- 原代码：`_COLOR_COLUMN="#888888"/_COLOR_DERIVED="#4a90d9"/_COLOR_LINK="#555555"/_COLOR_FORK="#2ecc71"/_COLOR_MERGE="#e67e22"/_COLOR_START="#2ecc71"/_COLOR_END="#d9534f"`；`_COLOR_INPUT/OUTPUT/BOTH`
- 修改为：删除模块级硬编码，改引用 `styles.GRAPH_*`（见 M22）；新增 `GRAPH_PRODUCE="#2ecc71"/GRAPH_LABEL="#2e7d32"/GRAPH_DEPRECATED="#757575"/GRAPH_DANGLING="#d9534f"/GRAPH_LANE_IN="#999999"/GRAPH_LANE_DEV="#4a90d9"/GRAPH_ACCESS="#888888"`
- 修改原因：正本 §4.3 L266 要求颜色迁入 styles.py 唯一来源；五类边需要独立色值
- 影响范围：node_graph 全部 paint；styles.py
- 验证方式：grep node_graph 无 `#` 字面色；配置页配色与 SampleCode 截图比对
- 备注：`_COLOR_INPUT/OUTPUT/BOTH`(83-85) 随 _StatusDot 删除一并移除
- 前置依赖：M1（常量口径）；M20（GRAPH_* 常量承载）

### M3 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\node_graph.py（阶段 M-b）
- 行号：193-264
- 原代码：`class TableNode(QGraphicsObject)`：`BTN_H=18/BTN_W=44`、`_left_rect/_right_rect`、paint 绘 "left"/"right" 按钮、`mousePressEvent` 发射 `table_moved(alias,"left"/"right")`（信号定义 202-203）
- 修改为：删除调序按钮与 `table_moved` 信号；改为 SampleCode TableItem 语义——160×40、输入 y=60/派生 y=78 错位、角标三态「输入表/结果表/已弃用」、deprecated 灰填充+DashLine、派生表虚线边+「由「X」生成」小字、hover/focus 换色
- 修改原因：C1 裁定取消调序（正本 §5.2 L341-342 作废行）；表节点术语化（P0-④）
- 影响范围：page_operation_config 的 `table_reorder_requested` 接线（M13 一并删）
- 验证方式：配置页点击表节点无调序反应；弃用表灰虚线目视
- 备注：保留 `node_clicked` 信号
- 前置依赖：无

### M4 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\node_graph.py（阶段 M-b）
- 行号：266-326
- 原代码：`class StepNode(QGraphicsObject)`：set_status(292)/boundingRect(299)/paint(302)/_darken(316)/mousePressEvent(323)，54px 高仅状态色块
- 修改为：140×70 卡片＝序号徽章(18px 圆)+操作中文名(13px bold)+业务副标题(12px 双行省略)+角标(输入缺失红/待配置橙)+失败人话气泡(≤230 宽, bottom+5 高 22)；描边链 选中>悬停>incomplete>状态；填充链 failed>running>done>selected>pending；boundingRect 左右扩 55/下扩 48 容纳气泡
- 修改原因：P0-②/P0-⑥ 业务化与失败人话； SampleCode StepCardItem(`dag_viewer.py:127-261`) 为蓝本
- 影响范围：配置页视觉全貌；`set_step_runtime_status` 映射保持
- 验证方式：与 SampleCode dyn-A 卡片逐项目视；失败步骤气泡文案比对
- 备注：副标题数据源＝STEP_DESC[type]（M23 静态映射，D-2=a 09-20 裁定；表卡副标题=alias，生产已有数据）；演示的表级/步骤级 business_desc 粒度降级为操作类型级（a 案固有，已接受，见 §4.5）
- 前置依赖：M23（STEP_DESC 副标题来源）

### M5 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\node_graph.py（阶段 M-b）
- 行号：328-419
- 原代码：`_StatusDot`(328-348)、`ConnectionItem`(351-359, z=-1)、`_arrow_polygon`(362-386)、`_DotMarker`(389-401, z=5)、`_ForkMarker`(406-419, z=6)
- 修改为：整体删除，替换为四边图元类 `LaneItem`(z=-5)/`AccessItem`(z=-3)/`ProduceEdgeItem`(z=-4)/`FlowEdgeItem`(z=-4)，实现照搬 SampleCode `dag_viewer.py:358-522`（含 `_edge_style` 优先级与 NoButton）
- 修改原因：交点圆点/独立箭头/起止圆点标记不承载边语义；五类边词表要求方向+线型+标签区分（ADR-3）
- 影响范围：rebuild 调用链（M7-M11）；`_arrows` 容器删除
- 验证方式：单测边计数不变量（对照 SampleCode EdgeModelTest 12 项移植）
- 备注：箭头几何 `ARROW_L/HW` 并入边图元 paint
- 前置依赖：M1（常量）；M2（颜色）

### M6 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\node_graph.py（阶段 M-b）
- 行号：424-432
- 原代码：`_col_cx(col)=LEFT_MARGIN+col*(TABLE_NODE_W+H_SPACING)+TABLE_NODE_W/2`；`_row_y(row)=TOP_MARGIN+BTN_H+TABLE_NODE_H+ROW_GAP+row*V_SPACING+STEP_NODE_H/2`
- 修改为：`col_cx(j)=120+240*j`；`row_cy(r)=193+100*r`
- 修改原因：与 SampleCode/正本 §4.2 L236-239 定稿口径一致
- 影响范围：全部图元定位；sceneRect 计算
- 验证方式：布局公式单测断言
- 备注：无
- 前置依赖：M1（常量集）

### M7 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\node_graph.py（阶段 M-b）
- 行号：468-548
- 原代码：`NodeGraphScene.rebuild(data)`：手工拼 columns/links/markers
- 修改为：消费 edges 的 11 步重绘（顺序与 z 同 §1.5）；步骤几何含 ride 判定(k==1 且同列)、missing 取后端 missing_refs、content 包围盒累积
- 修改原因：边语义单一事实源（ADR-3）；消除前端双算
- 影响范围：page_operation_config `_refresh_graph`（M16）
- 验证方式：lanes/access/produce/flow 计数与 SampleCode offscreen 打印一致
- 备注：蓝本 `dag_viewer.py:759-938`
- 前置依赖：M1/M4/M6；M16（edges 输入）

### M8 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\node_graph.py（阶段 M-b）
- 行号：577-620（含 592-605）
- 原代码：`_build_columns`：`usage`/`merge_consume` 收集(587-595)、`end_row=min(end_row, merge_consume[alias])` 提前截断(604-605)
- 修改为：删除 merge_consume 提前截断；泳道 y0＝输入表 HEADER_BOTTOM / 派生表 producer 卡片底+2；y1＝最深 tap
- 修改原因：正本 §4.3 L276 明确删除该截断（泳道应延伸到最深消费者）
- 影响范围：泳道长度视觉
- 验证方式：与 SampleCode dyn-A 泳道末端比对
- 备注：无
- 前置依赖：M7（rebuild 消费链）

### M9 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\node_graph.py（阶段 M-b）
- 行号：622-638
- 原代码：`_add_arrow_line`：ConnectionItem(width=1.5)+独立 `QGraphicsPolygonItem` 箭头、`setZValue(6)`(636)、`_arrows.append`(638)
- 修改为：删除该函数；箭头由各边图元 paint 内绘制，z=−3(接入段)/−4(produce/flow)
- 修改原因：正本 §4.5 L295 要求箭头并入单边图元且降层（防箭头浮于节点之上）
- 影响范围：_arrows 容器与清理逻辑
- 验证方式：截图层级目视（箭头不再覆盖卡片）
- 备注：无
- 前置依赖：M7

### M10 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\node_graph.py（阶段 M-b）
- 行号：640-661（含 655）
- 原代码：`_build_links`：输入线 650-657、输出线 659-661；骑线阈值 `if abs(cx-node_cx) < STEP_NODE_W/2+5:`(655，即 75px)
- 修改为：删除 75px 阈值；ride 判定＝`k==1 且 col_of(inputs[0])==锚列`；ride 时不生成 AccessItem、泳道末端 tap=卡片顶−2 并画下向箭头
- 修改原因：正本 §4.3 L282 删除该阈值（骑线语义改由单输入同列判定）
- 影响范围：接入段数量
- 验证方式：access 计数与 SampleCode 一致（dyn-A=6）
- 备注：无
- 前置依赖：M7

### M11 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\node_graph.py（阶段 M-b）
- 行号：663-699
- 原代码：`_build_markers`：起点 `_DotMarker(cx,y,_COLOR_START,label="起点")`(667-675)、分叉(679-684)、合并(685-690)、终点 `label="终点"`(691-699, 条件 `entry.is_end` 692)
- 修改为：装饰式起止标识+flow 边（**F-2 已于 09-18 裁定，本条可执行**）：开始 ccx−35/结束 ccx、失败避让 +32、空流程空态提示，蓝本 `SampleCode/frontend/dag_viewer.py` `_build_markers`/`_add_marker`（L946-1018）
- 修改原因：正本 §4.3 原口径为取消文字标记；**2026-09-18 F-2 裁定以 SampleCode 为准修订**（正本已回写）
- 影响范围：起止视觉；flow 边计数不变量
- 验证方式：裁定后单测 flow 恒 2/空 0 + 截图 J/K/L 比对
- 备注：分叉/合并菱形标记随 M5 一并删除（语义由 produce 边标签承载）
- 前置依赖：M16（flow 边数据）；M7（重绘链）

### M12 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\node_graph.py（阶段 M-b）
- 行号：713-789
- 原代码：`NodeGraphView`：NoDrag+自定义平移(746-780)、fit_to_scene(735-740)、wheelEvent Ctrl 缩放 1.15/0.87(782-789，无钳制)
- 修改为：缩放钳制 [0.40,2.50] 且 AnchorUnderMouse；空白左键拖拽平移并按缩放比换算滚动条、按下即清选中；`fit_to_scene` 边距=20（FIT_MARGIN）
- 修改原因：SampleCode 交互口径（§1.2 条 1-3）
- 影响范围：配置页操作手感
- 验证方式：缩放边界手测；全览复位
- 备注：无
- 前置依赖：M7/M9（图元结构先行）

### M13 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\page_operation_config.py（阶段 M-b：调序能力清除，文件属 page 但随画布能力收敛执行）
- 行号：88、407-422
- 原代码：`table_reorder_requested` 信号接线(88)；`_on_table_reorder(display,direction)` 交换 `_table_entries` 与 `model.tables` 后 `_refresh_graph()`(407-422)
- 修改为：删除接线与槽函数（M3 已删 TableNode 调序按钮，信号源消失）
- 修改原因：C1 裁定取消调序（正本 §3.5 L161 信号作废行）
- 影响范围：配置页；models.tables 顺序改由参数文件承载
- 验证方式：grep `table_reorder` 零命中；配置页启动无 AttributeError
- 备注：列序语义＝配置页参数顺序（正本 §4.2 L233）
- 前置依赖：M3（TableNode 已删按钮，信号源消失）

### M14 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\page_operation_config.py（阶段 M-c）
- 行号：121-125
- 原代码：`_build_top_bar`：`for type_name,(display_name,_) in STEP_CATALOG.items(): QPushButton(f"+{display_name}")`（9 个平铺按钮）
- 修改为：注册表驱动 MAIN 4 主按钮（filter/mapping_match/aggregate/copy_table）+「更多功能 ▾」QMenu 收纳其余 5 项（蓝本 `dag_viewer.py:694-703`）
- 修改原因：工具栏收敛（09-15 定案 5）；文员首屏只暴露高频功能
- 影响范围：配置页顶栏
- 验证方式：按钮文字仅来自注册表（grep 无硬编码 op 名）
- 备注：MAIN/MORE 分组常量放 models.py（M18）
- 前置依赖：M18（MAIN/MORE 常量，已执行）

### M15 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\page_operation_config.py（阶段 M-c）
- 行号：184-253
- 原代码：`_build_step_param_panel`：目标表 combo(204-205)、首项回写(212-216)、内联表单、上移/下移/删除按钮
- 修改为：保留表单与删除；**删除上移/下移按钮**（C1）；详情区增「连线说明」行（读取/产出/缺失，蓝本 `_edge_summary` `dag_viewer.py:1215-1258`）
- 修改原因：承接原画布图例解释职能（ADR-4 第 3 层）；调序取消
- 影响范围：右面板三态
- 验证方式：点步骤面板出现连线说明且与 edges 一致
- 备注：数据源＝M16 装配的 edges
- 前置依赖：M16（edges 数据源）

### M16 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\page_operation_config.py（阶段 M-a）
- 行号：448-537（调用侧改造）；`gui/graph_edges.py` 为新建文件
- 原代码：`_refresh_graph`：`display_to_id/derived/roles`、StepLayoutEntry 构造(510-526)、`self._scene.rebuild(...)`(534-536)、`fit_to_scene()`(537)
- 修改为：调用新增 `gui/graph_edges.build_edges(model)` 得到五类边列表，随 layout 数据一并传入 `rebuild`；不再手工拼消费关系
- 修改原因：edges 单一事实源（ADR-3）
- 影响范围：配置页刷新链路；新增文件 graph_edges.py
- 验证方式：边计数不变量单测；配置页增删步骤后连线联动
- 备注：graph_edges 契约=CONTRACTS v1.1（§1.4）
- 前置依赖：§1.4 契约；M18（produce_label 供边标签）
- **实现规格（09-19 补齐；09-20 终审修订对齐 §1.4 契约）**：
  1. **接口签名**：`def build_edges(steps: List[StepSpec], tables: List[TableSpec], deprecated_ids: Set[str]) -> List[EdgeSpec]`；`EdgeSpec` 七字段**逐字对齐 §1.4 契约**（`key/type/from/to/role/label/missing`——deprecated 为 type 枚举值而非标志位；key=`type:from:to[:role]`，冲突加 `#n`，全集唯一），DataClass + `to_dict()`。**输入＝未过滤 GUI model**（弃用态经 `deprecated_ids` 入参传入；弃用表渲染保留、仅 to_dict 导出才过滤——渲染/导出两方向互不污染）。
  2. **五类边派生规则**：reference＝步骤 inputs 引用表（`_missing_for` 判缺失 → dangling 独立图元）；produce＝`produces_table(op, params)` 为真且产表存在（copy_table→label"复制新表"）；flow＝开始/结束锚（`_normalize_end` 唯一性）；deprecated＝引用边其表 `deprecated=True`；dangling＝target 缺失/被删（红虚线短桩）。
  3. **蓝本锚点（实测行号）**：`SampleCode/backend/mock_backend.py`——`_build_edges` L205-255、`_mk_edge` L189-204、`_missing_for` L102-133、`_missing_refs` L134-150、`_uniq_edge_key` L176-188（唯一 key 防重）、`recompute` 表集合派生 L256-318；`_resolve_insert_index` L380-423。
  4. **测试要求**：移植 `SampleCode/tests/test_dynamic.py` `EdgeModelTest`（L288-399）12 项不变量（schema/ctype 枚举/reference 计数+role/produce 计数+label/flow 计数+空态/dangling 计数/missing 作用域/deprecated 边/key 稳定唯一/虚拟 key 隔离/不进 export）至 `rpa_engine/tests/test_graph_edges.py`。
  5. **产表判定（09-20 终审新增）**：`produces_table(op, params)` ＝ `op ∈ OUTPUT_OPS 且 params.output_mode != "overwrite_target"`（对齐 SampleCode mock_backend L102-114）——overwrite 步骤不产派生表节点、无 produce 边（正本 §8.3"原地修改不新增表"渲染侧落地；其 output_table_id 保留仅供 §4.3 两步链引用）。

### M17 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\page_operation_config.py（阶段 M-c）
- 行号：524-525
- 原代码：`kind=classify_step(step.type)`、`is_end=(step.type == "export")`
- 修改为：保持语义；增注释说明唯一性由数据层保证（同 SampleCode `_normalize_end`：仅最后一个 end 类步骤为结束步）
- 修改原因：与 ADR-2 结束锚点 fallback 语义对齐
- 影响范围：layout 数据
- 验证方式：删除导出步骤后结束标识落到末步（配置页目视）
- 备注：无
- 前置依赖：M16（is_end 唯一性由数据层保证）

### M18 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\models.py（阶段 M-a；已执行 09-18）
- 行号：19-50
- 原代码：`STEP_CATALOG`(19-29)、`OUTPUT_OPS`(32-33)、`STEP_KIND`(40-50)、`classify_step`(53-64)
- 修改为：STEP_CATALOG 值扩为 `(name_cn, kind, produces_table, produce_label)` 或独立 `PRODUCE_LABEL` 映射（copy_table="复制新表"、其余产表="新表"、不产表=None）；新增 `def is_end_op(type_name)`、`def produce_label(type_name)`、`MAIN_BUTTONS/MORE_BUTTONS`
- 修改原因：边标签与按钮分组的注册表唯一来源（禁硬编码）
- 影响范围：forms/page/node_graph 读取点；app.py 自检项4b
- 验证方式：app.py 启动自检 6 项全过（09-18 实测 OK）；grep 无 "复制新表" 字面量散落于 UI 代码
- 备注：**已执行（09-18）**——采独立 `PRODUCE_LABEL` 映射方案（`STEP_CATALOG` 旧二元组保持不变，零读取点改动）；追加锚点=classify_step 末（L64 后）
- 前置依赖：无（已执行）

### M19 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\models.py（阶段 M-a）
- 行号：`add_step` 产表编号分配（现 L229-230，`output_table_id=f"T{...}"`）、`renumber_steps`（现 L257-260，`"S{i}"`）——旧标注 181-183/210-213 已因 M18（09-18 执行）在其前插入而漂移 +45（09-19 校正；执行前仍以函数名 grep 复核）
- 原代码：产表编号 `output_table_id=f"T{self._next_table_num}"`；`renumber_steps` → `step_id=f"S{i}"`
- 修改为：逻辑保持；增注释「产表列=该步骤锚列（output_table 所在列），产出边自卡片顶边右锚点竖直向上连至该列表头」
- 修改原因：M7/M16 的列定位语义需要显式约定
- 影响范围：无行为变化
- 验证方式：代码评审
- 备注：无
- 前置依赖：M18（行号随其插入漂移，以函数名锚定）

### M20 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\forms.py（阶段 M-a；同条目第二落点=styles.py 块）
- 行号：428-437
- 原代码：`CopyTableForm`：说明行「将复制目标表的完整副本（无需参数）」、`get_params→{}`
- 修改为：说明行改为「复制出一张新表（新分支），产出边将标注"复制新表"」；其余保持
- 修改原因：与 produce_label 语义一致（§1.4）
- 影响范围：配置页 copy_table 面板文案
- 验证方式：面板文案目视
- 备注：文案取自注册表 produce_label 更佳（M21）
- 前置依赖：M18（produce_label）；M21（registry 单一源）

### M21 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\forms.py（阶段 M-a）
- 行号：500-515
- 原代码：`_FORM_REGISTRY`(500-510)、`get_form_class`(513-515)
- 修改为：`_FORM_REGISTRY` 9 项来源改读 `gui/models` 注册表（`STEP_CATALOG`+`produce_label` 派生），**不得双源**；若运行时导入成本高，以 `try_apply` 桥接实现，仍以 models 为唯一语义源
- 修改原因：标签唯一来源（ADR-4）
- 影响范围：M16 边装配
- 验证方式：单测 produce_label 与 edges label 一致
- 备注：已定死走 models（09-19 修订）；M18 已提供 produce_label
- 前置依赖：M18（produce_label 唯一源）

### M20（第二落点）· D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\styles.py（阶段 M-a：GRAPH_* 常量组，第一落点=forms.py 块）
- 行号：10-14 之后
- 原代码：仅 `COLOR_SELECTED/DONE/RUNNING/PENDING/FAILED`（注释声明配色唯一来源）
- 修改为：新增 `GRAPH_*` 常量组（M2 列出的 8 项）并扩展该注释为"节点态+图态配色唯一来源"
- 修改原因：正本 §4.3 L266 要求；消除 node_graph 硬编码
- 影响范围：node_graph 引用改道
- 验证方式：grep node_graph 无色值字面量
- 备注：无
- 前置依赖：无（本常量组被 M2 引用；M-a 先行落常量、M-b 改道引用——非依赖关系）

### M22 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\app.py（阶段 M-d；已执行 09-18）
- 行号：95-120
- 原代码：启动自检项4「操作目录注册」：engine BUILTIN_OPS 与 gui STEP_CATALOG 逐键比对(99-113)、registered<9 下限(104-106)
- 修改为：**已纳入并执行（09-18，M22）**：app.py 项4 后新增「项4b 注册表字段完整性」——逐项校验 produce_label/kind/produces_table 口径自洽、MAIN∪MORE=9 且无交集；自检清单 5→6 项
- 修改原因：防注册表漂移闸门（SampleCode 无此闸门，生产已有逐键比对先例）
- 影响范围：启动自检清单
- 验证方式：人为破坏注册表字段后启动应报自检失败
- 备注：**已纳入并执行（09-18）**；项4b 仅自洽性校验、失败不抛异常；破坏复测（临时改 PRODUCE_LABEL）应报 ok=False
- 前置依赖：M18（校验对象，已执行）

### M23 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\models.py（阶段 M-a：翻译层核心，09-20 裁定 D-1=B/D-2=a/D-3）
- 行号：`STEP_DESC` 追加于 `PRODUCE_LABEL` L72 区块后；`WorkflowModel.__init__`（弃用内存态）、`to_dict()` L266-302（L304-309 为 save_json，勿动）、`load_from_dict()` L311-353（执行前以函数名 grep 复核，行号随 M18 后已漂移过一次）
- 原代码：`to_dict()` 原样导出全部 tables/steps/params；无弃用概念；params 原样透传（无 output_mode 翻译）
- 修改为：①`STEP_DESC: Dict[str, str]` 9 项操作类型级一句业务说明（静态映射，§4.5）；②`WorkflowModel` 增 `deprecated_tables: set`、`deprecate_table(table_id, flag)`（可逆标记）、`_deprecated_closure()`（传递闭包：被弃用表→产出它的步骤→凡 target/extra 引用闭包内表或闭包内步骤产表的步骤递归入闭包，§4.2）；③`to_dict()` 增翻译与参数化 `include_deprecated: bool = False`（§4.2/4.3）——默认（False）＝业务导出：过滤弃用闭包＋output_mode 两步链翻译（new_table→剔除 output_table 含遗留键；overwrite_target→保留 output_table_id＋追加合成 copy_table 步骤，目标表取 `sqlite_table` 物理名）＋剔除 output_mode 键；True＝编辑态未过滤导出；④`load_from_dict()` 不还原弃用态（弃用标记不持久、重启后需重新弃用，注释说明，§4.2①）；⑤`_save_last_config`（main_window L533-541，exit_app L530/closeEvent L543-549 调用）改传 `include_deprecated=True`——last_config 保存未过滤工作流，重启恢复步骤完整（09-20 终审裁定）
- 修改原因：GUI 配置 ⇄ 后端执行参数翻译层落地（09-20 五项裁定+终审修订；此前该方向仅有既有 9 项操作的基础互转，弃用/覆盖语义无翻译）
- 影响范围：main_window save_json/start_workflow 与模板保存（过滤导出，经 to_dict 默认参自动生效）、`_save_last_config`/`_restore_last_config`（未过滤导出/载入，L533-549）、M24 控件键契约、M26 测试对象
- 验证方式：M26 用例②③④⑤；grep v3.1 导出结构无 `output_mode`/`deprecated` 键
- 备注：内存释放由会话结束清理兜底（SessionDB close 删库）；单表粒度释放列 v3.2 待办（§4.2④）
- 前置依赖：M18（注册表区锚点）

### M24 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\forms.py（阶段 M-a：覆盖模式控件，09-20 裁定 D-3）
- 行号：`FilterForm` L209-226、`DedupForm` L229-252（`__init__` 构建区；执行前以类名 grep 复核）
- 原代码：两表单仅条件字段（filter 条件表达式/dedup 去重键），get_params 不含保存方式
- 修改为：增「结果保存方式」QComboBox（`另存为新表`[默认] / `覆盖原表`），值存前端键 `params["output_mode"]`（"new_table"|"overwrite_target"，§4.3）；get_params 含该键；文案禁技术术语（不出现 output_mode 字样）
- 修改原因：filter/dedup 的另存/覆盖语义需 GUI 入口（正本 §8.4 output_mode 条款；09-18 分析缺口 G2）
- 影响范围：M23 to_dict 翻译输入；M25 二次确认触发条件
- 验证方式：面板目视（默认另存）；get_params 返回含 output_mode
- 备注：output_mode 为前端键，to_dict 翻译后剔除，不污染 v3.1 JSON（§4.3）
- 前置依赖：M23（键契约先行）

### M25 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\gui\page_operation_config.py（阶段 M-c：弃用入口+覆盖确认+空流程拦截，09-20 裁定 D-1/D-3）
- 行号：`_on_node_table_selected` L401-402（现仅清空选择）+ `_build_empty_param_panel` L174-182（空提示面板）——**生产现无表详情态，需新建**；二次确认先例 L320-327（"继续保存/取消"模式）；`_on_start_clicked` L567-583
- 原代码：表选中仅清空选择显示空提示（无表详情态、无弃用入口）；步骤保存无覆盖确认；启动校验无空流程拦截（仅"尚未配置任何操作步骤" L572）
- 修改为：①**新建表详情分支**（选中表→表信息+「弃用此表/恢复使用」按钮，可逆、无二次确认；参考步骤详情态结构 L184-252；调 `model.deprecate_table()`；悬空视觉由 M3/M5 承载，正本 §8.1/§8.5 入口口径）；②步骤保存时若 `output_mode=="overwrite_target"` → QMessageBox 二次确认（先例 L320-327；文案含目标表名 + "原表数据将被替换且不可恢复"）；③`_on_start_clicked` 增"弃用闭包过滤后步骤为空"拦截（提示改用保存模板）
- 修改原因：翻译层交互入口（09-20 裁定；缺口 G1 交互侧/G3）；覆盖为破坏性操作必须强确认（d2 决策）
- 影响范围：配置页面板三态（M15 联动；正本 §8.5"选中表=表信息+弃用/恢复"由此承载）/保存链路/启动链路
- 验证方式：真机清单补 3 项（弃用可逆恢复/覆盖确认弹窗与取消回退/全弃用启动拦截）
- 备注：弃用无二次确认（可逆）；覆盖必确认（不可逆）——对称性决策 d2
- 前置依赖：M23（deprecate_table/闭包）、M24（output_mode 值来源）

### M26 · D:\CPS-GPES_RPA-20250312\v3\rpa_engine\tests\test_translation.py（阶段 M-d：E2E 翻译测试，09-20 裁定 D-5；新建文件）
- 行号：新建（`rpa_engine/tests/` 目录，随 §1.9 方案①落点与「测试暂缓豁免」一并启用）
- 原代码：无（生产无该测试）
- 修改为：8 用例（§4.7）——①roundtrip：构造 model（2 输入表+多步）→to_dict→parse_workflow→validate_workflow 全通；②输入表弃用级联：弃用 T1→导出无 T1 且引用步骤被剔除、无关步骤保留；③派生表弃用级联：弃用派生表→产出步骤与下游消费步骤入闭包；④new_table 映射：params 无 output_table（含旧文件遗留键剔除）；⑤overwrite 两步链（§4.3）：导出＝filter 步（保留 output_table_id、无 output_mode/output_table）＋合成 copy_table 步（target=中间表 ID、output_table=目标表 `sqlite_table` 物理名），下游引用目标表 ID 不变，parse+validate 闭合；⑥STEP_DESC 9 项齐全且键集=STEP_CATALOG；⑦空流程处置：全弃用→to_dict steps 空（存模板允许）+启动拦截函数行为断言；⑧load 回归：含遗留 params.output_table 的旧 v3.1 文件→load_from_dict→to_dict(new_table) 断言该键被剔除；含弃用步骤的未过滤导出（include_deprecated=True）→load 后 steps 完整
- 修改原因：验证"GUI 配置→可执行后端参数"翻译正确性（缺口 G6；纯 parse/validate 层测试，不触 SQLite，无副作用）
- 影响范围：M-d 验收落点
- 验证方式：`python -m unittest rpa_engine.tests.test_translation -v` 全绿
- 备注：蓝本=`SampleCode/tests/test_dynamic.py` 弃用/覆盖用例语义（DeprecateTest L239/TableDerivationTest L99）
- 前置依赖：M23

---

## 4. GUI 配置 ⇄ 执行参数翻译契约（2026-09-20 裁定落地）

> 本章回答"GUI 对功能函数/数据表的配置如何翻译为后端 ETL 执行参数"（09-20 只读分析报告的 6 项缺口 G1-G6 闭环）。既有基础：生产 `WorkflowModel.to_dict()/load_from_dict()` 已承载 9 项操作的 v3.1 双向互转（models.py L266-353），`start_workflow` 经 save_json→parse_workflow→validate_workflow→worker（main_window L349-368）——本章仅补**动态语义**的翻译契约。承载条目：M23-M26。

### 4.1 领域模型对齐表（演示字段 ↔ 生产 v3.1 ↔ 处置）

| 演示字段 | 生产 v3.1 对应 | 处置（09-20 裁定） |
|---|---|---|
| `tables[].deprecated` | 无 | → 前端内存态 `deprecated_tables`（不入 JSON，§4.2） |
| `steps[].params.output_mode` | 无（仅 `output_table` 命名参数） | → to_dict 翻译为 output_table 策略（§4.3） |
| `steps[].config_state` | 无（validator 前向引用+必填校验） | → 前端校验态投影，翻译层零处理（§4.4） |
| `business_desc`（表级/步骤级，数据驱动） | 无 | → `STEP_DESC` 操作类型级静态映射（§4.5，D-2=a） |
| `missing_refs` | 无 | → 画布派生字段，不入导出（同演示 export_workflow 规则） |
| `produce_label` | `PRODUCE_LABEL`（M18 已落 L72-84） | → 已完成 |

### 4.2 弃用语义（D-1=B 前端翻译降级）

1. **GUI 内存态**：`WorkflowModel.deprecated_tables: set`（表 ID 级）；`deprecate_table(table_id, flag)` 可逆标记（恢复即清除）；**不入 v3.1 JSON**（弃用属本轮编辑意图，非持久业务逻辑——符合"JSON=业务逻辑唯一载体"红线）。
2. **弃用闭包**（`_deprecated_closure()`）：从被弃用表出发——产出该表的步骤入闭包；凡 target/extra_inputs 引用闭包内表、或引用闭包内步骤产出表的步骤，递归入闭包（传递闭包，单向下游）。
3. **to_dict 过滤**：闭包内步骤不写入 steps[]；**被弃用的输入表**（闭包根）不写入 tables[]，闭包步骤消费的**共享输入表**保留（闭包外步骤仍引用）；派生表本就不入 tables[]（由步骤链派生）。
4. **内存释放**：由会话结束清理兜底（SessionDB close 删 .db/.wal/.shm）；**单表粒度释放列 v3.2 待办**（正本 §8.1 注）。
5. **空流程处置**：闭包过滤后 steps 为空——允许保存模板；启动拦截（M25③）。
6. 正本 §8.1「底层语义」按此加执行注（B 案）。

### 4.3 覆盖/另存映射（D-3=两步链翻译，09-20 终审修订·方案 c）

- `new_table`（默认）→ `params` 剔除 `output_table`（含旧文件遗留键）→ 后端自动命名 `t_s{n}`（step_executor L187-194）。
- `overwrite_target` → **两步链导出**（零 engine/ops 改动，§2.1 边界不破）：①本步骤导出为 `filter/dedup(源→自动中间表)`（params 剔除 output_mode/output_table，**保留 output_table_id=T{n}** 供链内引用）；②自动追加**合成步骤** `copy_table(中间表 T{n}→目标表)`（params={output_table: 目标表 `sqlite_table` 物理名}，无 output_table_id）。依据：filter_dedup 先 `DROP` 后 `CREATE AS SELECT`（L79-84，同名覆盖必败）；`copy_table` 允许目标已存在（table_lifecycle L31-65 DROP+CREATE）且源≠目标恒成立（中间表≠目标表，L118 同名禁令天然满足）。
- **下游引用原地不动**：覆盖=原地语义（正本 §8.3），下游步骤仍引用目标表 ID，无需改写。
- **渲染不画两步**：两步链仅为 to_dict 导出展开；GUI 模型保持单步骤，M16 输入=未过滤 model（M16 规格第 2 条）；overwrite 步骤保留 T{n} 但渲染派生表判定跳过（M16 规格第 5 条 produces_table）。
- **UI 强制二次确认**：步骤保存时若 overwrite → QMessageBox（先例 page L320-327；文案含目标表名+"原表数据将被替换且不可恢复"）；`new_table` 为默认值防误触。
- `output_mode` 为**前端键**：M24 表单承载 → M23 to_dict 翻译后剔除，不污染 v3.1 JSON。
- 中间表占用至会话结束清理（SessionDB close，接受）；单表粒度释放仍列 v3.2 待办。

### 4.4 config_state 投影

`config_state`（ok/incomplete）= 前端校验态渲染（M3/M5 角标与橙描边）；执行前由 `_on_start_clicked` 现有校验（L567-583）+ `validate_workflow`（前向引用/必填）兜底；**翻译层零额外处理**。

### 4.5 business_desc（D-2=a 静态描述）

`STEP_DESC: Dict[str, str]` 9 项操作类型级一句业务说明（M23 落地；文案新拟，语义同源 func_registry）。粒度=操作类型级，较演示的表级/步骤级**降级**（a 案固有，裁定接受）；步骤卡副标题=`STEP_DESC[type]`（M4），表卡副标题=`alias`（生产已有）。

### 4.6 演示格式差异（D-4 不补转换）

`SampleCode export_workflow()` 保持演示格式（meta/tables/steps 含 deprecated/config_state），**不加 v3.1 转换函数**；SampleCode 冻结为只读基线；其 README L56「正式版语义=执行跳过+释放内存」为历史表述，由正本 §8.1 执行注（B 案）覆盖；真机演示导出的 JSON 不可被生产引擎直接执行（已知限制，不修）。

### 4.7 E2E 翻译测试（D-5 纳入）

`rpa_engine/tests/test_translation.py`（M26）八用例：①roundtrip ②输入表弃用级联 ③派生表弃用级联 ④new_table 映射 ⑤overwrite 两步链 ⑥STEP_DESC 齐全 ⑦空流程处置 ⑧load 回归——纯 parse/validate 层（model→to_dict→parse_workflow→validate_workflow），不触 SQLite、无运行时副作用。

---

## 附录 A：SampleCode 目录结构与关键文件说明

```
SampleCode/
  run.bat                     conda py311 启动器（L4 绝对路径=唯一机器绑定点），透传 --offscreen
  README.md                   运行方式/界面功能/五类边语义表/人工清单 11 项+N1-N15/已知限制
  backend/mock_backend.py     伪后端 532 行：JSON 内存态+recompute 六步+edges 单一事实源+11 公共 API
  backend/func_registry.py    注册表 128 行：9 项元数据+produce_label/is_end_op/produces_table
  frontend/dag_viewer.py      画布 1395 行：常量/6 图元类/rebuild 11 步/交互/模拟运行/main
  frontend/param_panel.py     参数面板 124 行：schema 驱动+try_apply+saved 信号
  data/workflow_demo.json     示例数据 148 行：6 表/6 步/initial_statuses/fail_reasons（可替换）
  tests/test_backend.py       15 用例（静态接口一致性）
  tests/test_dynamic.py       46 用例（动态 31+EdgeModelTest 12+扩展 3）
  tests/scenario_shots.py     11 场景 offscreen 截图（A-G、J-M）
```
运行：`run.bat`（真机）/`run.bat --offscreen`/`python -m unittest discover -s tests -v`（cwd=SampleCode）/`python tests\scenario_shots.py`。路径全部自相对（`mock_backend.py:37`、`dag_viewer.py:38-39,56-57`、`tests/*.py:16-23`），整目录可搬迁。

## 附录 B：正式计划合并映射表

| 原件（已删） | 关键结论 | 并入 plan.md |
|---|---|---|
| `plan/dag-blueprint-ambiguities.md` | 歧义 9 项（A 调序视觉[后取消]/B 高亮含 lane/C 背景 #fafafa/D 步骤vs表风格/E 焦点+选中暗化/F 无"未启动"档/G END 端口视觉/H 视口高度/I S5 无输出）**全部采纳并已回写正本** | §1.3/§1.6/§1.10 |
| `experiments/W-03_DAG_visualization_plan.md` | P0-①端口不绘制/②业务化卡片/③顶部信息条/④表节点术语化无调序/⑤起止标记/⑥失败人话；§3.5 流程名=运行参数文件名且对用户禁术语；§10 动态六条（已=正本 §八） | §1.1/§1.2/§1.6 |
| `experiments/_agent/CONTRACTS.md` v1.1 | edges 五类 7 字段+4 不变量+虚拟 key 隔离；布局常量；状态四值；端口词表仅 L2 数据结构 | §1.4/§1.5 |
| `experiments/_agent/DECISIONS.md` §7/§8 | 取消 7 项/保留 8 项/C1-C6/ADR-1~4/D-1~9/冲突 C-4·C-5·F-3/实施偏差 3 条 | §1.10/§2.2/附录 E |
| `W-03_dynamic_dag_deep_test_PLAN.md` | §5 回写清单已执行（D6→正本 §八）仅留指针；注册表正式层级=后端 ops 侧；§15 全推荐定案；9 处失效标注 | §1.4/§2.2/附录 C |

## 附录 C：旧方案废弃原因

- **取消 7 项**（09-15 人工真机后裁定）：双视图/数据视图/端口显示/搜索框/GUI 导出/调序按钮/面向技术人员的 GUI 分析——文员不需要且增加认知负担；技术人员经后端参数文件+日志分析。
- **旧副本 3 类**：`plan/DAG_refactor_plan.md`(489 行，落后 docs 正本 549 行)、`analysis/DAG_visualization_analysis.md`(与 docs 正本等长副本)、`task-records/`×6(docs 均有同名正本)——以 docs 正本为唯一权威。
- **孤儿/证据产物**：`artifacts/dyn-H/I.png`(脚本自述零引用)、`experiments/*.png`×7、3 个分析脚本(`dag_render_obs.py`/`dag-layout-test.py`/`dag_blueprint_preview.py`)——先例结论：offscreen 可导出验证图、docstring 固化命令可复跑、预览图仅服务歧义裁定（结论已回写正本）。
- **已消费计划**：`W-03_code_change_plan.md`(代码 09-15/16/17 已改完)。

## 附录 D：风险、回滚、验收清单

风险：①node_graph 整体重写回归→逐类替换+每 M 冒烟；②edges 与 executor 表 ID 语义错位→M-a 以 validator 用例锁定；③~~F-2 未裁定~~（已裁定 09-18，M11 可执行）；④误删正式计划→本文件附录 B 为重建源。
回滚：git 人工；每 M 独立提交可回退；SampleCode 只读基线不受影响。
验收：M-a 完成＝`gui/graph_edges.py` 可独立单测+**翻译层可独立单测（M23 闭包/两步链+M24 控件）**；M-b 完成＝配置页截图与 SampleCode dyn-A 几何/配色一致+边计数一致+**起止标识按 F-2 口径（装饰标识+flow 边+失败避让）**；M-c 完成＝增删步骤/弃用/参数保存全联动+**弃用入口/覆盖确认/空流程拦截（M25）**；**M-d 完成＝移植清单全绿（test_graph_edges 12 项+test_translation 8 用例；落点 §1.9 方案①，须先获「测试暂缓豁免」认可）**；M-e 完成＝正本回写+doc-governance §4 全局校验通过。**09-18 已闭环项**：M18/M22 生产最小改动（自检 6 项全过）、F-1/F-2/F-3 正本回写、C 类改道、W-14/W-15 闭环。**09-20 已闭环项**：翻译契约五项裁定（D-1~D-5）→ §4 翻译契约+M23-M26；终审纰漏修补 11 项（两步链/M16 契约对齐/M25 表详情纠偏/移植清单口径/闭包消歧/last_config 未过滤导出等）同日落定。

## 附录 E：裁定与失效引用处置登记（09-18 收敛）

**裁定结果（已落地）**：F-1 图例废止＝正本 §8.6/§8.1/§8.5 已改写为"画布无常驻图例、语义三层承载"；F-2 起止标识＝正本 §3.4 D2/§4.3/附录 A D2 已修订为"装饰式起止标识+flow 边"；F-3 五类边词表＝正本 §4.3 末+§5.8 已新增。  
**M22**：已纳入并执行（app.py 项4b；M18 前置同批）。  
**B 类**：已人工验证关闭（N1-N15 真机 + git status 零改动）。  
**C 类失效引用（已处置 09-18）**：正本 11 处改道/补注、AGENTS L194/L196 改道、backlog L35/L36 改道、analysis 附录 A/B 归档标注；根 README 经核实无 DAG 指引行→零改动。  
**W-14/W-15**：同批闭环（binding 经 doc-governance §9 映射核对保持 reference；W-15 真身=正本附录 A D6 裁定行、表述准确无需改正文）。  
**D-2 已裁定关闭（09-20，五项）**：D-1=B 弃用→前端翻译降级（弃用闭包不写入参数 JSON+会话清理兜底，§4.2）；D-2=a business_desc→STEP_DESC 静态映射（§4.5）；D-3=覆盖映射（overwrite→output_table 同名 DROP+CREATE）+UI 二次确认（§4.3）；D-4=演示不补 v3.1 转换（§4.6）；D-5=E2E 纳入 test_translation.py（§4.7）——承载条目 M23-M26；正本 §8.1/8.3/8.4 已同步加注（09-20）。  
**仍待人工**：W-20（exe 人工重建）、M0 启动指令。  
**W-19 已裁定关闭（09-18）**：ConsolePanel 移除——GUI 不再呈现引擎日志，日志改由 `logs/gui_*.log` 文件承载（实现：删除 `gui/widgets.py`、`worker.py` 移除 loguru→GUI 转发、`page_progress/page_report` 独占布局）。  
**历史记录不改**：docs/task-records×4、_temp/repo-context-report.md（doc-governance §1 条 4/5）。  
**机器绑定**：SampleCode/run.bat:4 conda 绝对路径（换机需改）。

