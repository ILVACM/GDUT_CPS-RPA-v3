# 任务记录：M0 · M-b 画布重写 → M-c 页面集成 → M-d 校验 → M-e 文档回写（DAG 重构收尾）

> 日期：2026-09-20｜执行：模式 B（主控实施，无子 agent）｜状态：已完成（R2／M-b~M-e；M0 全阶段闭环）

## 摘要

人工复核 M-a 效果符合预期后下达「继续开发，完成所有剩余工作」。按
`_temp/DAG-rebuild/plan.md` §2.4 阶段序一次完成 **M-b（node_graph.py 按
SampleCode 蓝本整体重写，M1-M12）→ M13 调序清除 → M-c（M14 工具栏分组 /
M15 面板三态+连线说明 / M17 注释 / M25 弃用入口+覆盖确认+空流程拦截）→
M-d（自检 6 项回归 + 22 用例 + 冒烟 33 项全量验证）→ M-e（正本回写 +
doc-governance §4 + 锚点 R2）**。渲染层自本轮起直接消费表 ID + 五类边
（M-a 的 `_to_display_data` 显示名翻译层随消费点一并移除）。

## 用户输入

- 「效果符合预期，继续开发，完成所有剩余工作」（M-a 真机复核通过后）

## Agent 理解与决策（含计划外细化）

| # | 决策 | 说明 |
|---|---|---|
| D16 | `GraphLayoutData` 签名演进为 `(tables, steps, edges)` | 表列改持 `TableSpec`（key/display/is_input/producer_step/deprecated），显示名随表视图携带；删除 `table_aliases/input_count/id_to_display` 与 `_to_display_data` 翻译层（M-b 既定移除项） |
| D17 | `StepLayoutEntry` 精简为几何+文案字段 | 删 `table_roles/primary_input/kind`（交点圆点/分叉合并标记随 M5 删除，边关系全由 edges 承载）；增 `op_type`（卡片副标题经 `step_desc` 查 STEP_DESC） |
| D18 | `config_state` 轻量投影（plan §4.4 口径自定） | 渲染层直算：目标表缺失/悬空/已弃用、额外表引用已弃用 → incomplete（橙描边+「待配置」角标）；必填参数完整性由保存/开始既有校验兜底，不引入表单校验进渲染层 |
| D19 | 覆盖二次确认落点＝保存配置/开始执行前（M25② 生产化映射） | 生产内联表单无独立「保存参数」按钮（收拢发生在切换/保存/开始）；逐 overwrite 步骤弹确认、取消即阻断，避免收拢循环反复弹窗与表单 UI 回滚难题 |
| D20 | 失败人话气泡数据源＝worker message 透传 | `main_window._on_step_failed` → `set_step_runtime_status(..., message)` → 卡片气泡；空 reason 仅着色不画泡 |
| D21 | 选中态场景内实现（跨 rebuild 保持） | 蓝本 `_apply_visuals` 移植进 `NodeGraphScene`；rebuild 后 key 仍存在则保持选中（联动刷新链 selected 不丢，正本 §8.5） |

## 执行流程

1. **b0 规格加载**：重读 plan.md §3 M1-M26、SampleCode `dag_viewer.py` 全关键段（图元/rebuild 11 步/markers/_apply_visuals/_edge_summary/CanvasView/fit_all）、page/models/graph_edges/styles 接口。
2. **M-b node_graph.py 整体重写**（约 1190 行）：M1 常量集（COL_CX0/ROW_CY0/HEADER_BOTTOM/ANCHOR_DX/FLOW_*/END_AVOID_GAP/EDGE_Z…）；M2 零字面色（全引 `styles.GRAPH_*`，styles 补 5 项卡片文字常量）；M3 TableItem（160×40、y=60/78 错位、角标三态、弃用灰虚线、派生「由「X」生成」、删调序）；M4 StepCardItem（140×70 徽章+标题+副标题+角标+气泡）；M5 四边图元（Lane −5/Access −3/Produce·Flow −4，NoButton）替换五旧类；M6 `col_cx/row_cy` 定稿公式；M7 rebuild 消费 edges 11 步（ride 判定、dangling 短桩+⚠、content 包围盒）；M8 删 merge 截断；M9 箭头入边图元；M10 删 75px 阈值；M11 起止标识+空态提示；M12 缩放钳制 [0.40,2.50]+空白平移按 m11 换算+fit 边距 20。
3. **M13**：page 删 `table_reorder_requested` 接线与 `_on_table_reorder`；顺删死代码 `_on_move_step`（按钮随 M15 删除后无调用者）。
4. **M-c page 集成**：M14 顶栏 MAIN 4 主按钮+「更多功能 ▾」QMenu（注册表驱动）；M15 步骤面板删上移/下移+增「连线说明」（`_edge_summary` step 分支）；M17 is_end 唯一性注释；M25 ①表详情面板（表信息+连线说明+弃用/恢复按钮）②`_confirm_overwrite_steps`（保存/执行前）③`_confirm_active_steps`（弃用闭包全覆盖→拦截执行、允许存模板）；`_refresh_graph` 改新签名装配；状态透传 reason。
5. **main_window**：`_on_step_failed` 透传 message 至失败气泡。
6. **验证（M-d）**：22 用例回归全绿；`_temp/DAG-rebuild/smoke_mb.py`（新建，offscreen 33 项：五类边计数/图元结构/选中联动/失败气泡/弃用重绘/空态/面板三态/调序零残留/全场景截图）SMOKE_ALL_OK；截图目检结构一致（offscreen 无字体文字空白＝基线已知行为）；grep `table_reorder`/`#` 字面色/旧图元类零命中；`run_self_check()` 6 项 ALL_OK（313ms）。
7. **M-e 治理**：正本 `docs/plan/DAG_refactor_plan.md` 回写（§3.9/§3.10 取代注、§4 章首落地注、§5.8 测试落点回写 `rpa_engine/tests/`、§5.9 增 16-18 项+9/11/15 标 [已过时-待确认]、§8.5 三态落地注）；plan.md §2.4 M-b~M-e 标 ✅；AGENTS 锚点 R2+§8 主线；本记录。

## 涉及文件

| 文件 | 改动 |
|---|---|
| rpa_engine/gui/node_graph.py | **整体重写**（M1-M12；约 1190 行） |
| rpa_engine/gui/styles.py | 补 5 项卡片/表文字常量（GRAPH_CARD_TITLE 等） |
| rpa_engine/gui/page_operation_config.py | M13/M14/M15/M17/M25 + `_refresh_graph` 新签名 + 状态透传 + 死代码清理 |
| rpa_engine/gui/main_window.py | 失败原因透传（1 处） |
| _temp/DAG-rebuild/smoke_mb.py | **新建**（offscreen 冒烟 33 项 + 全场景截图） |
| _temp/DAG-rebuild/plan.md | §2.4 M-b~M-e 完成态标注 |
| docs/plan/DAG_refactor_plan.md | §3.9/§3.10/§4/§5.8/§5.9/§8.5 回写 |
| AGENTS.md | 锚点 R2 + §8 主线更新 |

engine/ops 与 SampleCode **零改动**（冻结基线不受影响）。

## 验收

- ✅ `py_compile` 7 个改动文件 exit 0。
- ✅ `cd rpa_engine && python -m unittest discover -s tests -v` → **Ran 22 tests OK**（无回归）。
- ✅ smoke_mb 33 项 **SMOKE_ALL_OK**：edges={flow 2, reference 6, produce 5, dangling 1}；图元 steps 6/tables 7/lanes 5/access 5/produce 5/flow 2/markers 2；选中淡化 0.3/恢复 1.0；弃用→deprecated 边 1+表灰化、恢复→0；空态提示文案命中；截图 1717×776 保存。
- ✅ 截图目检：起止箭头（首步顶左/末步底中）、produce 绿线+标签衬底、泳道灰/蓝+access 箭头、dangling 红虚桩+橙描边+红角标、输入/派生表头错位——与蓝本结构一致（文字空白＝offscreen 无字体，基线已知）。
- ✅ M2 验证：`node_graph.py` grep `#[0-9a-f]{3,8}` **0 命中**；M13 验证：`table_reorder` 全库 0 命中；旧图元类（TableNode/StepNode/_StatusDot/ConnectionItem/_DotMarker/_ForkMarker/_arrow_polygon）0 命中。
- ✅ 启动自检 `run_self_check()` 6 项 ALL_OK（313ms，含项4b 注册表字段完整性）。
- ✅ 真机清单增补：正本 §5.9 新增 16（弃用可逆恢复）/17（覆盖确认与取消回退）/18（全弃用启动拦截）三项，弹窗交互留人工真机验收。

## 关闭标识

**本轮（R2／M-b~M-e）完成，M0 全阶段闭环**：M-a 数据层 → M-b 画布 → M-c 页面 →
M-d 校验 → M-e 文档，plan.md §2.4 五阶段全 ✅。

**待人工**：①真机验收正本 §5.9 清单（18 项，重点 16-18 新增交互与文字渲染）；
②W-20 exe 重建（判据 docs/build-guide.md §1.10）；③[已过时-待确认] 三项
（§5.9 #9/#11/#15）人工裁定归档。
