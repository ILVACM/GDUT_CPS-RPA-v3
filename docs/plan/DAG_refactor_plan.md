---
title: DAG 节点图重构实施方案（Blueprint）
type: plan
scope: domain
status: active
owner: 黄泊凯
last-updated: 2026-10-24
tags: [节点图, DAG, 重构方案, 布局引擎, 交互规范, 里程碑]
binding: reference
confidence: 方案态（描述尚未实现的目标方案，不参与"文档↔代码"比对校验；全部规范附行号证据或实测探测；9 项定稿歧义已裁定（W-02，2026-09-14，歧义正本已并入 _temp/DAG-rebuild/plan.md 附录 B）；F 批裁定 2026-09-18 回写（F-1 图例废止/F-2 起止标识/F-3 五类边词表）；binding 经 doc-governance §9 四档映射核对保持 reference——本文已无未裁定条目，W-14 关闭）
content-revision: 2026-09-01
---

# DAG 节点图重构实施方案（Blueprint）

> **依据**：`docs/analysis/DAG_visualization_analysis.md`（含 S1-S6 专项诊断）。**基线**：commit `4308a6d` + 工作区 2026-09-01 现状。
> **行号约定**：文中 file:line 基于 2026-09-01 工作区现状，仅作定位辅助；实施以函数/符号名为准（M6 适配后行号将漂移）。
> **2026-09-01 用户裁定同步**：①AGENTS.md 版本控制表述已按实际修正（.git 存在）②测试目录口径确定 `Test/unit/`（§5.8 主方案，备选作废）③备份目录已迁移至 `_temp/BackUp/`（原 Z-BackUp/，物理迁移由用户完成，本文快照路径已同步）④**Git 相关操作由人工接管，Agent 不执行**（本文 git 提交条目已全部移除）。
> **2026-09-01 复核修订**：①运行状态口径统一——结构性编辑/恢复不重置，仅执行前重置一次（§3.7/§3.10/§5.1/§5.9 联动）②§3.7 补差量删除批内顺序（端口/边键先于节点键）与场景归属校验 ③M2/M3/M4 方法级骨架清单首日交付 ④M2 加 0.5 人日缓冲（合计 19.5 人日）。
> **2026-09-14 裁定（W-02）**：9 项定稿歧义已逐条采纳，见 `_temp/DAG-rebuild/plan.md` 附录 B（原歧义正本 `plan/dag-blueprint-ambiguities.md` 已随 09-18 `_temp` 收敛清理并入）；快照/回退机制退役（R1，git+人工接管），本文「`_temp/BackUp/` 快照」「快照点 T0-T4」已移除。
> **2026-09-16 回写（D6，W-03 裁定完成）**：①新增「八、动态配置与用户视角呈现层规范」（弃用语义/输入完整性契约/表生命周期/功能元数据注册表/右参数面板与 DAG 只读/动态联动）②§3.3 数据模型扩展（kind/deprecated/params/config_state + 表集合派生规则）③调序条款同步取消（C1：§3.3/§3.5/§3.10/§4.2/§4.7/§5.2/§5.5/§5.7，W-02 A 裁定转历史标注）④W-03 P0 定稿口径同步（§4.2 row_cy=193+100·r、§4.7 卡片 70px）⑤§六 增 M-D 里程碑（已完成）。W-03 门控解除，M0 启动待人工指令（**历史状态**：M0-M7 已于 2026-09-20 全阶段闭环，见 2026-10-24 状态注记）。
> **2026-09-18 裁定回写（F 批，以 SampleCode 为准）**：①**F-1 图例废止**——§8.1/§8.5/§8.6 改为"画布无常驻图例，语义三层承载"②**F-2 起止标识**——§3.4 D2/§4.3/附录 A D2 修订为"装饰式起止标识+起止连接边"（SampleCode `_build_markers` 口径：开始 ccx−35/结束 ccx/失败避让+32/空流程空态提示；数据层仍无 markers 字段）③**F-3 五类边词表**——§4.3 末新增五类边小节、§5.8 增边视觉词表④W-15 修正（backlog 所记 L463 引用真身在本文 L536，表述准确无需改）⑤W-14 binding 核对保持 reference。C 类失效引用改道 `SampleCode/` 与 `_temp/DAG-rebuild/plan.md`。
> **2026-09-20 翻译契约裁定**：GUI 配置 ⇄ 执行参数翻译五项裁定（D-1=B 弃用前端翻译降级 / D-2=a business_desc 静态 / D-3 覆盖映射+二次确认 / D-4 演示不补转换 / D-5 E2E 纳入）——§8.1/§8.3/§8.4 加执行注；行号级执行计划与翻译契约全文见 `_temp/DAG-rebuild/plan.md` §4 与 M23-M26。
> **2026-10-24 状态注记**：M0-M7 已于 2026-09-20 全阶段闭环；实际实现为 `gui/node_graph.py` 单文件（1,087 行），`gui/graph/` 五层包方案**未采纳**（F 批裁定 2026-09-20，见 §3.2 注）；余真机回归 18 项待人工。Git 口径细化（2026-10-24）：写操作人工接管，Agent 仅只读 diff 可用于比对差异。
> **制定方式**：模式 B 多 Agent 协作——架构师/渲染专家/交互UX专家/质量保障四角色并行设计，主代理整合裁决（D1-D11，见附录 A）。
> **性质**：本文档为开发实施依据，语言全部确定性表述，开发人员无需二次确认。

---

## 一、重构目标与范围界定

### 1.1 目标（逐项绑定分析报告缺陷编号）

| 目标 | 根治的缺陷 |
|------|-----------|
| G1 视图状态与图内容分离：任何编辑操作后缩放/平移/选中/运行状态色不丢失 | P0-1、P1-5 |
| G2 内容包围盒画布：消除对角阶梯漂移与大片空白，fit 后节点可辨认 | P0-2 |
| G3 正交边路由 + 边缘端口：消除箭头刺入节点、长横线穿全图、标记同坐标堆叠 | P0-3、S4-1、S4-2 |
| G4 交互闭环：双向选中同步、hover/tooltip、焦点模式（显隐控制）、右键菜单、缩放边界 | P1-1、P1-2、P1-3、P1-4、P2-1 |
| G5 可维护架构：纯 Python 布局引擎可单测、单一坐标约定、常量/层级单一来源、注释归真 | 根因 A-E、S3①、P2-2、P2-3 |

### 1.2 范围界定

**范围内**：
- `rpa_engine/gui/node_graph.py`（789 行；**2026-10-24 现状 1,087 行**）整体重构为 `rpa_engine/gui/graph/` 包（9 文件）
- `rpa_engine/gui/page_operation_config.py` 最小适配（§3.6 改动清单，10 个位置，右侧表单区/模板区/校验区/暂存区零改动）
- `rpa_engine/gui/styles.py` 新增 GRAPH_* 配色常量组（数值迁移）
- 测试交付物（`Test/unit/` 4 文件 + README，unittest 风格）——**2026-09-20 已改址 `rpa_engine/tests/`**（见 §5.8 回写注）
- 文档同步（architecture.md §8、docs/INDEX.md、README.md、AGENTS.md §6 Test/ 行口径；AGENTS.md §1 版本控制表述修正已于 2026-09-01 裁定落地）

**范围外（红线）**：引擎层（engine/、ops/）零改动；main_window.py 运行时接线（L388/401/405/410）零改动；models.py 零改动；RPA_Workflow_v3.spec 零改动（论证见 §七 R6）；业务逻辑零改动。

> **前端/后端界定（见 architecture §8）**：本重构对象 `gui/`（DAG 可视化 + 页面临接）均属**前端**；改造仅限前端渲染/交互/可视化层。**后端（engine/ops/SQLite/JSON 参数，ETL 技术底层）零改动**——上列"范围外（红线）"即后端边界。

### 1.3 成功标准

1. §五 5.9 真机人工回归检查单 15 条全部通过（逐条绑定缺陷编号）；
2. `Test/unit/` 布局引擎/边路由/差量单测全绿（人工触发执行，见 §五 5.8）——**2026-09-20 已改址 `rpa_engine/tests/`**；
3. 全库 grep `node_graph` 零引用后旧文件删除；
4. build.bat 编译冒烟通过（验证打包不受影响）。

---

## 二、技术选型最终决议

### 2.1 决议：保留 PyQt5 QGraphicsScene/View 基座 + 自研泳道 2.0 布局引擎

### 2.2 候选方案否决表（硬性理由）

| 候选 | 否决理由 |
|------|---------|
| QtWebEngine + G6/X6/React-Flow 等 Web 图库 | exe 由 ~40MB 膨胀至 150MB+（QtWebEngine 运行时）；违反 build-guide 单文件打包红线；引入浏览器进程模型，目标办公机运维复杂度不可接受 |
| pyqtgraph | 面向科学绘图（曲线/坐标系），无节点图交互模型，强行使用等于自研 |
| graphviz / networkx（布局）+ 静态渲染 | 非交互（无点击/hover/缩放语义）；graphviz 依赖外部二进制；新增依赖违反零新增约束 |
| 力导向布局算法 | 业务工作流为**严格顺序流水线**（步骤按列表序执行），力导向的物理模拟语义与文员"从上往下读流程"心智不符，且引入非确定性迭代 |
| 分层 DAG 布局（dagre 类） | 保留为 LayoutEngine 接口后的未来选项（本方案接口已兼容），当前业务规模（≤30 节点、顺序链+偶发合并）下泳道模型更贴合且实现成本低一个量级 |

### 2.3 依赖决议

零新增第三方依赖。requirements.txt 不变。布局引擎纯标准库（dataclass/typing/math/hashlib）。

---

## 三、模块架构与接口设计

### 3.1 五层架构（严格单向依赖：高层 → 低层）

```
L5 页面适配      page_operation_config.py（持 model/_table_entries；消费图信号；对 main_window API 不变）
L4 视图交互控制  gui/graph/{controller,view,widget}.py（视图状态唯一所有者；信号枢纽）
L3 场景渲染      gui/graph/{scene,items}.py（keyed registry；差量应用；统一坐标铁律）
L2 布局计算      gui/graph/layout.py（泳道 2.0；纯 Python，禁止 import PyQt5）
L1 数据组装      gui/graph/spec.py（GraphSpec 数据类 + build_graph_spec 映射）
共享常量         gui/graph/style.py（尺寸/颜色/ZLayer 枚举/LayoutConfig，零依赖）
```

依赖规则：L5→L4→L3→L2→L1；L2/L1/style 禁止 import PyQt5（单测准入断言）；L4 禁止 import page/main_window；L3 禁止出现任何坐标计算函数（现行 `_col_cx/_row_y` node_graph.py:424-432 职责整体迁入 L2）。

### 3.2 `gui/graph/` 文件清单

| 文件 | 职责 |
|------|------|
| `__init__.py` | 门面：re-export DagGraphWidget / GraphSpec / build_graph_spec / NodeStatus |
| `spec.py` | TableSpec/StepSpec/GraphSpec 数据类 + build_graph_spec(model, table_entries) |
| `layout.py` | LayoutEngine.compute(spec, config) → LayoutResult（纯函数） |
| `style.py` | ZLayer 枚举、GRAPH_* 颜色、LayoutConfig 常量（§四 4.7） |
| `items.py` | TableNodeItem/StepNodeItem/EdgeItem（折线+箭头单图元）/PortItem：只画局部几何 |
| `scene.py` | DagScene：keyed registry + apply_layout(diff) + 单点状态入口 |
| `view.py` | DagView：缩放钳制/空白平移/auto-fit 策略/resize 语义/右键事件转发 |
| `controller.py` | GraphViewController：缩放/平移/选中/运行状态四项状态 + 信号定义 |
| `widget.py` | DagGraphWidget(QWidget)：组合 view+scene+controller+28px 工具栏，页面唯一接触面 |

> 方法级签名骨架（公开+私有方法一览）作为 M3（items/scene）/M4（controller/view/widget）首日交付物，经人工确认后填充实现（见 §六）。

### 3.3 GraphSpec 契约（L1，Qt-free dataclass）

**TableSpec**：

| 字段 | 类型 | 语义 | page 侧来源 |
|------|------|------|------------|
| key | str | 表唯一键（table_id "T1"…） | entry["table_id"] / step.output_table_id |
| display | str | 列标题文本 | _table_display（page:436-437）；派生列 f"{tid} {名}·结果"（page:459/464） |
| is_input | bool | 输入列（顺序由配置页参数决定，2026-09-15 取消 DAG 调序，C1） | col < len(aliases)（page:529-532） |
| kind | str | **（2026-09-16 D6 扩展）** `input`｜`derived`——is_input 语义正式名：用户配置前导入的源数据表 / 步骤功能产生的操作表 | 由 is_input 映射 |
| deprecated | bool | **（2026-09-16 D6 扩展）** 用户显式弃用标记（§8.1）；弃用表保留显示、灰虚线 | 配置面板「弃用此表」 |
| producer_step | Optional[str] | 派生列产出步骤 key；输入列为 None | 遍历 steps 匹配 output_table_id（page:456-459） |

**StepSpec**：

| 字段 | 类型 | 语义 | page 侧来源 |
|------|------|------|------------|
| key | str | 步骤唯一键（step_id；move_step 不重编号，models.py:204-208，编辑期稳定） | step.step_id |
| name | str | 节点标题 | step.name |
| kind | str | end/merge/fork/sequential | classify_step(step.type)（models.py:40-50） |
| target_table | Optional[str] | 主输入表 key | step.target_table_id |
| extra_inputs | List[str] | 附加输入表 key（有序） | page:483-491（mapping/merge 附加表） |
| output_table | Optional[str] | 产出表 key | step.output_table_id |
| is_end | bool | 终点步骤 | step.type=="export" |
| params | dict | **（2026-09-16 D6 扩展）** 步骤参数（schema 由功能元数据注册表 §8.4 驱动） | 配置面板写回 |
| config_state | str | **（2026-09-16 D6 扩展）** `ok`｜`incomplete`——输入完整性校验结果（§8.2） | recompute 派生 |

**表集合派生规则（2026-09-16 D6）**：表集合 = 输入表（kind=input）∪ 产表步骤输出（kind∈{fork,merge} 且 output_mode≠overwrite_target）；**is_end（export）不产表**（W-02 I 裁定）；顺序类（rename_columns/convert_dtype）原地修改不新增表。派生表若无其他 producer 且其产出步骤被删除→从表集合移除，下游引用转悬空显式提示（§8.3）。

删除现行字段及理由：`status`（构造即态归 controller，根除 page:513 PENDING 硬编码）；`table_roles/primary_input/input_tables`（由 target/extra/output 推导，删 page:466-509 约 60 行双向映射）。状态档按 **W-02 F 裁定**：不设"未启动"档，未执行步骤统一为 pending（待执行灰）。

### 3.4 LayoutResult 契约（L2 输出，Qt-free）

| 字段 | 类型 | 语义 |
|------|------|------|
| node_rects | Dict[str, Rect] | 键 `node:T1`/`node:S2` → 场景坐标矩形；表节点 y=表头行，步骤节点 y=行中心-半高 |
| edges | Dict[str, EdgeLayout] | 键 `lane:T1`（泳道线）/`access:S2:T1`（横向接入段）；EdgeLayout{kind, points: List[Point], color_role, arrow: bool, arrow_tip: Point, arrow_dir: Vec} |
| ports | Dict[str, PortLayout] | 键 `port:src:T1`/`port:in:S2:T1`（含 TOP 变体 `port:top:S2`）/`port:out:S2`/`port:end:S5`；PortLayout{kind, pos: Point, owner_key: str} |
| scene_rect | Rect | node_rects∪edges 包围盒 + 四周 40px；空图 (0,0,400,300) |
| fingerprint | str | 全字段规范化序列化（坐标 round 0.1px）哈希；相等 ⇒ 布局零变化，diff 短路 |

四个 dict 键空间前缀互斥、可哈希，支撑差量比对。**整合决议 D2**：不设 markers 字段——起点/终点/分叉/合并语义全部并入端口样式（§四 4.4），独立标记图元删除，S4-1 堆叠从数据层消除。（**2026-09-18 F-2 修订**：数据层仍无 markers 字段（本决议不变）；渲染层允许**装饰式起止标识+起止连接边**——不占布局行、不可选中/删除、不进面板，口径见 §4.3 末「起止标识」条与 SampleCode `_build_markers`。）

### 3.5 信号契约（controller 定义，widget 转发）

| 信号 | 签名 | 方向 | 语义 |
|------|------|------|------|
| step_selected | (str step_key) | 图→页 | 点击步骤节点（保留现行链路） |
| table_selected | (str table_key) | 图→页 | 点击表节点（参数由 display 改 key；page 槽行为不变） |
| table_reorder_requested | (str table_key, str direction) | 图→页 | 输入列调序 left/right **（2026-09-15 取消：DAG 不提供调序入口，C1；调序语义由配置页参数顺序承载，本信号不实现）** |
| no_selection | () | 图→页 | 点击空白 |
| step_action_requested | (str step_key, str action) | 图→页 | 右键菜单动作 action∈{"up","down","delete"} |

页面→图**方法调用**（非信号，杜绝回环）：`rebuild(spec)`、`set_selection(kind, key)`、`set_step_status(key, status)`、`reset_statuses()`、`fit_view()`。
**整合决议 D8**：架构师原案的 `selection_changed` 双向广播信号取消——图→页走信号、页→图走方法，天然单向无环。

### 3.6 状态所有权矩阵

| 状态 | 所有者 | 写者 | 读者 | rebuild 时 |
|------|--------|------|------|-----------|
| 缩放 | controller | 用户 Ctrl+滚轮（钳制 0.40-2.50） | view | **不重置** |
| 平移 | controller | 用户空白拖拽 | view | 前记视口中心场景点，后恢复 |
| 选中 | controller | 图点击 / 页面 set_selection | scene 高亮、页 | 按 key 重放 |
| 运行状态 | controller（Dict[key,NodeStatus]） | main_window→page→controller | scene 着色 | 按存活键重放（**修复重建归零**） |
| hover | items（瞬时态） | Qt 事件 | 仅本 item | 不持久 |
| 焦点模式 | controller（_focus_key） | 表节点点击 | scene 透明度 | 结构性变化自动退出 |

### 3.7 差量刷新设计

- registry：`scene._items: Dict[key → (item, sig)]`，sig = 几何+样式元组；端口为节点子项亦入 registry（样式 diff 用）。
- **两条路径**：
  - 状态变化（选中/运行状态/hover）：controller → 单 item `set_status/set_selected` → `item.update()`。不重算布局、不 clear、不触碰 sceneRect。
  - 结构性变化（加/删/移步骤、调表序、目标表变更、模板应用、restore_config）：page `rebuild(spec)` → layout.compute → diff → apply。
- **diff 应用顺序**：①删除（旧键−新键：removeItem+deleteLater，controller 清失效状态键；**批内顺序：端口/边键 → 节点键**——先删节点会连带销毁其子端口图元，致后续对子键的 removeItem 触碰已销毁对象；removeItem 前以 item.scene() 非空校验兜底）→ ②更新（交集且几何指纹不等：setPos / setPos+setPath）→ ③新增（新键−旧键：建 item、setPos、初始状态取 controller 重放值）→ ④setSceneRect（与当前差 >0.5px 才写）→ ⑤选中重放 → ⑥视口锚点恢复。fingerprint 相等时 ②-④ 短路。
- `view.setUpdatesEnabled(False)` 包裹 ①-⑥（try/finally）；状态路径不包裹。
- **关键规则**：引擎输出不含 status 字段、sig 不含状态——状态唯一写入方为运行时信号，杜绝 diff 冲掉运行色（P1-5）。

### 3.8 数据流全景

```
用户编辑（10 触发点，page:105/272/284/296/311/339/422/434/738/784）
  → build_graph_spec(model, _table_entries) → GraphSpec          [L1]
  → LayoutEngine.compute(spec, LayoutConfig()) → LayoutResult    [L2]
  → DagScene.apply(result)  diff 应用（keyed registry）            [L3]
  → 视口/选中/运行状态保持（controller 重放）                      [L4]
用户点击节点 → item → scene → controller 信号 → widget 转发 → page 槽 [L4→L5]
worker 运行信号 → main_window → page.set_step_runtime_status → controller.set_step_status → 单点重绘
```

### 3.9 node_graph.py 处置

> **[已被 F 批裁定取代，2026-09-20 M-b 落地]**：gui/graph/ 五层包方案未采纳；
> 现行实现＝`node_graph.py` 单文件原地重写（M1-M12）+ `graph_edges.py`
> 五类边单一事实源（M16），页面适配见 §3.10 注与 §8。以下为历史蓝本口径，
> 保留供追溯：

过渡期原样留树（切换后零引用，不写适配 shim——两套数据契约不同，shim 成本高于直接切换）；真机验收通过后整文件删除（789 行），graph/ 包为唯一实现。

### 3.10 页面适配层改动清单（page_operation_config.py 最小集）

> **[已被 F 批/W-03 裁定取代，2026-09-20 M-c 落地]**：DagGraphWidget 导入与
> `_on_step_action_requested` 未采纳；现行页面适配＝`_refresh_graph` 装配
> `GraphLayoutData(tables, steps, edges)`（M16/M-b 签名）+ 面板三态
> （M15/M25）+ 工具栏分组（M14）+ 调序清除（M13/C1）。下表为历史蓝本口径，
> 保留供追溯：

| 位置 | 改动 |
|------|------|
| L40-43 | import 改 `from gui.graph import DagGraphWidget, build_graph_spec` |
| L84-96 | `self._graph = DagGraphWidget()` + 5 信号连接；`main_split.addWidget(self._graph)`；`setSizes([757,505])`；stretch 因子保留 |
| L448-537 | `_refresh_graph` 重写为约 15 行：build_graph_spec + `self._graph.rebuild(spec)`；删 roles/display 双向映射与 L537 强制 fit |
| L345-349 | `_select_step` 追加 `self._graph.set_selection("step", key)`（反向高亮） |
| L407-422 | ~~`_on_table_reorder` display 名匹配改按 table_key 定位~~ **（2026-09-15 取消，C1：调序改由配置页参数顺序承载，DAG 侧入口移除；本行作废，page 调序槽保留为配置页自身功能）** |
| L539-561 | 三个状态方法签名与转发语义不变（改转发 self._graph），main_window 调用点零改动 |
| 新增 | `_on_step_action_requested(step_key, action)`：查 idx 分发 _on_move_step/_on_delete_step |
| L298-311/L434/L738/L784 | 配置替换/恢复路径**不新增** reset 调用——运行状态随 diff 按 key 自动延续（存活步骤）/清理（失效步骤），见 §3.7；显式 reset 仅 start_workflow 执行前一处（main_window 现状，零改动） |
| 不动 | 表单区/模板区/校验区/暂存区全部零改动 |

---

## 四、坐标与布局算法详细规范

> **M-b 落地注（2026-09-20，[已校验一致]）**：本章几何口径已由
> `rpa_engine/gui/node_graph.py` 重写落地（M1-M12，蓝本
> `_temp/DAG-rebuild/SampleCode/frontend/dag_viewer.py`）。两处实现口径
> 修订（均经 F 批/W-03 裁定先行）：①**sceneRect** 按"精确内容包围盒
> ±SCENE_MARGIN(40)"实现（§4.2 原 `W/H` 撑宽公式作废——内容包围盒口径
> 消除幻影边距）；②**z 层级**按字面常量实现（LANE −5 / ACCESS −3 /
> produce·flow −4 / dangling −2 / 表 0 / 卡片 1 / 标识文字 2），§4.5
> `ZLayer(IntEnum)` 枚举未引入（简化裁定，语义等价）。验证通道：
> `rpa_engine/tests/`（22 用例）+ `_temp/DAG-rebuild/smoke_mb.py`（33 项）
> + offscreen 全场景截图目检。

### 4.1 逻辑坐标系与屏幕映射

- 逻辑坐标系：原点 (0,0) = 布局内容左上角；x 右 y 下；单位 = 逻辑像素（zoom=1.0 时 1:1 屏幕像素）。**布局系 ≡ 场景系**，无二次平移。
- 屏幕映射唯一机制：QGraphicsView 仿射变换（scale/fitInView/滚动条），场景侧零手工换算；命中判定统一 `scene.itemAt(scenePos, QTransform())`（消除现行 node_graph.py:703 与 :752-753 两处 transform 分叉）。
- **定位铁律**：一切图元 = `setPos(场景坐标)` + 局部几何 `[0,w]×[0,h]`；端口为所属节点**子图元**（局部坐标随父移动）；边图元 `setPos(折线首点)`、路径点为相对量。**禁止把场景坐标烤进 QRectF/QPolygonF/路径点。**
- 消除的现行"烤坐标"违规点：L341（_StatusDot）、L395-396（_DotMarker）、L412-417（_ForkMarker）、L401-403（子标签偏移依赖父烤坐标）、L615-620（ConnectionItem 绝对路径）、L631-638（箭头多边形）、L673-699（起点/终点标记）、L216/L502-504 与 L287/L521-522（双重 setPos）——对应类全部删除或重写。

### 4.2 泳道 2.0 布局数学

**列排序**（确定性公式）：
- 输入列 `[0, I)`：按 `_table_entries` 用户顺序（**2026-09-15 取消 DAG 调序，C1：顺序=配置页参数顺序，画布不提供调序交互**）。
- 派生列 `I..`：按首个产出步骤行号升序 `producer_row[d] = min{r : steps[r].output_table == d}`（一步最多一产出，并列不存在）；无产出者按 table_id 字典序队尾。

**坐标公式**（常量见 §4.7）：
- 列中心：`col_cx(j) = 40 + 240·j + 80`
- 表头区底线：`header_bottom = 118`（**2026-09-16 D6/C5 定稿口径**：输入表头 y=60 高 40；派生表头 y=78 高 40（错位示"由步骤产出"），边框 1px 虚线 #1a5ca8；原 18px 调序条已取消，C1）
- 行中心：`row_cy(r) = 118 + 40 + 100·r + 35 = 193 + 100·r`（**W-03 P0-② 定稿：70px 卡片**，2026-09-16 D6 同步；原 54px 口径 185+100·r 作废）；步骤节点左上 = `(anchor_cx − 70, row_cy − 35)`

**步骤锚定 x 兜底链**（依序取首个可解析项）：
1. 非 end 且 output_table 可解析 → `col_cx(output)`
2. is_end 或无 output：target_table 可解析 → `col_cx(target)`
3. [target]+extra_inputs 中首个可解析项 → `col_cx(该项)`
4. 全部不可解析 → 沿用上一行锚列；首行取 `col_cx(0)`

> **（W-02 I 裁定，2026-09-14）**：`is_end` 步骤（export 终点）**不进入 producer_row 计算**、不产出派生表；其下不落派生表列、不画"已导出"假节点。producer_row 仅对非 is_end 步骤统计。

**节点尺寸**：表 160×40；步骤 **140×70**（W-03 P0-② 定稿，2026-09-16 D6 同步；原 54 作废）。不变量：列距 240 − 节点宽 140 = 100（单侧净空 50px）保证"泳道永不穿节点体"；行距 100 − 节点高 70 = 30 > 端口堆叠最大 ±24（k≤4；路由锚点口径，端口图元 GUI 不绘制，§8.4/2026-09-15 收敛）。

**场景矩形**：`sceneRect = (0, 0, W+40, H+40)`；`W = 40 + 240·(n_cols−1) + 160`；`H = row_cy(n_rows−1) + 35 + 24`（35 = 卡片半高 70/2；24 = END 口外环 d=14 + 余量）；空图 (0,0,400,300)。**删除现行按表总数撑宽逻辑（node_graph.py:543-548）**。

### 4.3 端口体系（6 类，全部节点子图元）

| 端口 | 语义 | 形状 | 颜色 | 锚点（节点局部坐标） |
|------|------|------|------|---------------------|
| SRC 表底出口 | 起点 | 实心圆 d=8，白描边 1px | #2ecc71 | 表节点 (80, 58) |
| IN 侧缘输入口 | 输入（有效输入=1） | 实心圆 d=8 | #2b7cd3 | (0 或 140, y_stack) |
| IN-M 侧缘输入口 | 合并（有效输入≥2 时该步**全部**输入口升级） | 双环：外圆 d=8 线宽 2 + 内实心 d=3.5 | #e67e22 | 同 IN |
| TOP 顶缘输入口 | 骑线输入（源列=锚列） | 同 IN / IN-M | 同上 | (70, 0) |
| OUT 底部输出口 | 分叉（派生泳道起点） | 实心菱形对角线 10×10 | #2ecc71 | (70, 70) |
| END 底部终止口 | 终点（export） | 实心圆 d=8 + 外环 d=14 线宽 1.5 | #d9534f | (70, 70) |

- 多输入纵向堆叠：左右缘各自独立；`port_y(i) = row_cy + (i − (k−1)/2)·16`（i=0..k−1，按 target→extra 序）；k≤4 间距 16，k≥5 压缩 `42/(k−1)`（端口群不越出节点高 70−12）。
- 端口-边绑定：每 IN/TOP 口绑一条 access 边（键 `access:{step}:{table}`）；每 SRC/OUT 口为一条 lane 边起点（键 `lane:{table}`）；END 口无出边；OUT 与 END 互斥（is_end 优先）。
- 颜色迁入 styles.py 新增 `GRAPH_*` 常量组（数值沿用 node_graph.py L54-85 现值）。
- **"终点/起点"端口圆点标记取消**（现 L697 label 及 _DotMarker/_ForkMarker 图元）——端口语义不单独绘制圆点标记（W-03 P0-① 端口不绘制）。**2026-09-18 F-2 修订**：改采**装饰式起止文字标识+起止连接边（flow）**——「▶ 开始」锚首步卡片顶边左锚点（ccx−35）、「■ 结束」锚结束步（is_end 步，无则末步 fallback）卡片底边中心（ccx）；失败气泡避让整体下移 32；空流程不画标识、改画空态提示；标识不占布局行（row_cy 公式不变）、不可选中/删除、`Qt.NoButton`（SampleCode `_build_markers`/`_add_marker` 为准）。
- **五类边词表（2026-09-18 F-3 新增，契约=SampleCode edges v1.1）**：

  | type | 语义 | 几何 | 视觉 |
  |------|------|------|------|
  | reference | 数据引用边：表→步骤 | 列内竖直泳道（输入表 y0=118 / 派生表 y0=producer 卡片底+2）+ 横向接入段；ride（k==1 且同列）时仅泳道、末端 tap=卡片顶−2 | 输入列 #999999 / 派生列 #4a90d9 实线 2.0/1.5 + 末端箭头；z=−5/−3 |
  | produce | 数据产出边：步骤→操作表 | 竖直向上：卡片顶边右锚点 (ccx+35, rect.top) → (ccx+35, 118) | 绿 #2ecc71 实线 2.0 + 向上箭头 + 白底标签「新表」/copy_table「复制新表」；z=−4 |
  | flow | 起止连接边 | 开始 (ccx−35, top−6)→(ccx−35, top−18)；结束 (ccx, bottom+6)→(ccx, bottom+18)（避让态 +32） | 开始绿 #2ecc71 / 结束红 #d9534f 实线 1.5 + 箭头；z=−4 |
  | dangling | 悬空标记边：缺失表→步骤 | 卡片左缘 40px 短桩（多缺失按 16 堆叠） | 红 #d9534f DashLine 1.5 + ⚠ + 角标「输入缺失」；z=−2 |
  | deprecated | 弃用引用边（reference 变体） | 同 reference（只改样式不移动） | #757575 DashLine 1.5；表节点另加「已弃用」角标 |

  **边字段契约（7 字段）**：`key/type/from/to/role/label/missing`；key=`type:from:to[:role]` 冲突加 `#n`，全集唯一且 recompute 幂等。**4 条计数不变量**：count(flow)=2（steps 非空）或 0（空）；count(produce)=产表步骤数；count(reference)+count(deprecated)=Σ 有效引用数；count(dangling)=Σ len(missing_refs)。**missing_refs 口径**严格限定"表不存在"（弃用/缺参/输入不足不计入）。**边样式优先级**：高亮 > deprecated > 常态色（dangling 独立图元不参与）。

### 4.4 正交边路由算法

EdgeItem 单图元内绘制折线+箭头（取消独立 QGraphicsPolygonItem 箭头，根治 L636 z=6 刺节点）；pos=折线首点，路径点为局部相对量。

**纵向泳道线（lane，纯竖直）**：
- 起点：输入泳道 = SRC 口 `(col_cx, 118)`；派生泳道 = OUT 口 `(col_cx(out), row_cy(prod)+35)`。
- 终点：对表 T 每个消费步骤 c 求 tap：骑线（`|node_cx − col_cx| < 0.5`）→ `row_cy(c) − 39`（TOP 口上缘=卡片顶−4）；非骑线 → `port_y(c, T)`；`lane_end_y = max(tap)`；无消费者不画。
- **删除现行 merge_consume 提前截断（L604-605）**——合并行后仍有引用时泳道必须延续到最低 tap。
- 末位消费者骑线 → 泳道末端画下向箭头（tip=TOP 口上缘）；骑线者非末位 → 泳道连续、被节点体遮蔽穿越，仅显 TOP 口不画箭头。

**横向接入段（access，纯水平单段）**：
- 侧选择：`col_cx(src) < node_cx` → 左缘口（dir=+1）；`>` → 右缘口（dir=−1）；`=` → 骑线归 lane 终止（无横向段）。
- 构造：`(col_cx(src), port_y) → (node_edge_x − dir·4, port_y)`。
- 不变量：列距 240 > 节点宽 140 ⇒ 相邻列最短接入 170px 无退化短桩；每行唯一节点 ⇒ 接入段不可能命中第三节点。删除 L655 的 75px 骑线阈值（精确等值判定替代）。

**箭头**：长 9、半宽 4.5；位置=端口外侧尖端贴端口外缘（水平接入 tip=`(node_edge_x − dir·4, port_y)`，底=tip−9·dir；骑线终止 tip=`(col_cx, node_top−4)` 底=tip 上方 9）；朝向=末段方向单位向量；起点侧（SRC/OUT/END）一律无箭头。

**交叉策略：平交不架桥**。理由：业务规模 <20 步交叉个位数；桥接弧违背扁平无装饰原则；泳道线宽 2.0 浅色平交损失可忽略。**降级预案**：实测交叉 >10 处时改"被穿泳道交叉点前后 3px 断口"，不动架构。

### 4.5 z 层级枚举（单一来源 `ZLayer(IntEnum)`，整合决议 D1）

| 层 | 值 | 用途 |
|----|----|------|
| BACKGROUND | −10 | 背景网格/水印（预留） |
| LANE | −5 | 纵向泳道线 |
| EDGE | −4 | 横向接入段 |
| ARROW | −3 | 箭头（低于节点：即使出错也不遮节点文字，防御 L636 类缺陷） |
| TABLE_NODE | 0 | 表节点 |
| STEP_NODE | 1 | 步骤节点（不透明体遮蔽穿越泳道） |
| PORT | 5 | 全部端口（节点子图元随父叠加） |
| HIGHLIGHT | 10 | 选中/hover 高亮 |

### 4.6 文本预计算

节点构造时一次性：`QFont("Microsoft YaHei")` setPixelSize(13)（与 QSS 一致）；`QFontMetrics.elidedText(name, ElideRight, W−12)`（表 148px/步骤 128px）存 `self._display`；`setToolTip(完整内容)`（规范见 §五 5.3）。paint 仅 drawText(self._display)，禁止 fontMetrics()（消除 L238-239/L311-313 逐帧测量）。重命名走 set_name() 重算+update()。

### 4.7 LayoutConfig 常量表（dataclass，替换 L42-51 散置）

| 常量 | 默认值 | 用途 |
|------|--------|------|
| TABLE_NODE_W / H | 160 / 40 | 表节点尺寸 |
| STEP_NODE_W / H | 140 / **70** | 步骤节点尺寸（**W-03 P0-② 定稿：54→70**，容纳序号徽章+标题+业务副标题；row_cy 相应 193+100·r，见 §4.2） |
| H_SPACING | 80 | 列间距（列距 240） |
| V_SPACING | 100 | 行距 |
| TOP_MARGIN / LEFT_MARGIN | 60 / 40 | 表头区 / 首列偏移 |
| ROW_GAP | 40 | 表头底→首行 |
| BTN_H / BTN_W | 18 / 44 | 调序条 **（2026-09-15 取消，C1：常量作废，不实现）** |
| PORT_D | 8 | 端口外径（原 DOT_RADIUS=12 缩小降文字侵入） |
| PORT_STACK_SPACING | 16 | 输入口堆叠间距 |
| ARROW_LEN / ARROW_HALF_W | 9 / 4.5 | 箭头 |
| SCENE_MARGIN | 40 | 包围盒右/下边距（替换 L543 "+60"与 400 下限） |
| FIT_MARGIN | 20 | fitInView 边距（修正 L736 "10%" 与 L740 ±10px 漂移） |
| CANVAS_BG | `#fafafa` | 画布背景色（W-02 C 裁定，2026-09-14） |
| LEFT_PANEL_H | 640 | 阶段2左窗格高（仅设计参考；auto-fit 实际按 `view.height()` 实算，W-02 H 裁定） |
| ZOOM_MIN / ZOOM_MAX | 0.40 / 2.50 | 缩放钳制 |

非法值（列距≤0、边距<0）构造即抛 ValueError。

---

## 五、渲染与交互流水线设计

### 5.1 渲染流水线（两条路径）

- **状态路径**（选中/运行状态/hover）：controller → 单 item set_status/set_selected → item.update()。不重布局、不 clear、不触碰 sceneRect。
- **结构路径**：rebuild(spec) → compute → fingerprint 短路判定 → diff（删→改→增）→ setSceneRect → 选中重放 → 视口恢复，全程 setUpdatesEnabled(False) 包裹。
- 运行状态四色 API 不变：`set_step_runtime_status(step_id, state)` / `reset_runtime_status()`（main_window L388/401/405/410 零改动）。**reset 语义收窄（2026-09-01 复核修订）**：显式 reset 仅 start_workflow 执行前重置一次（main_window 现状）；结构性编辑、回退恢复、模板应用不重置——存活步骤状态随 diff 延续（支撑 §5.9 检查单 #3）。**状态档（W-02 F 裁定）**：不设独立"未启动"档，未执行的后续步骤统一为 pending（待执行灰）。

### 5.2 交互语义表

| 图元素 | 悬停 | 左键单击 | 右键 | 拖拽 | 滚轮 | Ctrl+滚轮 |
|--------|------|---------|------|------|-------|----------|
| 表节点主体 | 填充 #3a8ce2 | 进入/切换/退出焦点模式；发 table_selected | 无（**2026-09-15 取消调序菜单，C1**） | 无 | 穿透→滚动 | 穿透→缩放 |
| ~~调序按钮~~ | — | — | — | — | — | **（2026-09-15 取消，C1：整行作废，不实现）** |
| 步骤节点 | 边框 #2b7cd3 2px | step_selected；退出焦点模式 | 上移/下移/删除菜单 | 无 | 穿透 | 穿透 |
| 泳道线/连线/端口 | 无反馈 | **无操作-穿透**→空白语义 | 无 | 穿透→平移 | 穿透 | 穿透 |
| 画布空白 | 箭头光标 | no_selection（清选中+退焦点）随即平移态 | 无 | 左/中键平移 | 滚动 | 缩放（锚定鼠标） |

> **（W-02 A 裁定，2026-09-14）**：调序按钮视觉定稿 = 表节点顶部内侧 `left`/`right` 文字按钮，尺寸 44×18（BTN_W/BTN_H）、填充 `#e8f2ff`。**（历史标注：2026-09-15 人工裁定取消调序按钮，C1；本裁定仅作档案保留，不实现）**

P1-4 死点根治：装饰/边图元统一 `setAcceptedMouseButtons(Qt.NoButton)` 且不启用 hover；no_selection 改由 view 空白按下路径直接触发（删 scene.mousePressEvent 的 itemAt 判定 L701-706）。

### 5.3 悬停与 tooltip

- 步骤节点 tooltip 四行：完整步骤名（不省略）/ 操作类型中文名（STEP_CATALOG）/ 目标表显示名 / 输出表显示名（有则显示）。
- 表节点 tooltip 两行：完整别名 / 属性（输入表：「输入表（第 N 列）」；派生表：「派生表（由步骤「X」产出）」；弃用表追加「已弃用」，§8.1）。
- 实现：`DagScene.helpEvent` 覆写，取 z 最高节点，QToolTip.showText(event.globalPos(), text)。tooltip 文本由 page 组装随 GraphSpec 传入（tooltip 层不反向访问 WorkflowModel）。

### 5.4 双向选中同步

- 图→表单：保留现有链路（step_selected → _on_node_step_selected → _select_step）。
- 表单→图：`_select_step(idx)` 末尾调 `set_selection("step", key)`；幂等（同 key 直接返回）；覆盖触发源：图点击/校验失败自动定位（_warn_and_focus L631-639）/右键菜单移动后索引同步。
- 视觉：选中节点描边 #2b7cd3 2px（常态 1px）+ z 提升至 HIGHLIGHT；相邻连线（输入+输出）#2b7cd3 2.5px，**含数据通路泳道 lane**（W-02 B 裁定）。
- 视口跟随（确定规则）：step_key 实际变化时——节点矩形外扩 50px 后仍被视口完全包含→不滚动；否则 `ensureVisible(rect, 50, 50)` 立即定位。无动画；缩放/平移不因跟随重置。

### 5.5 焦点模式（P1-1 显隐控制）

- 进入：左键单击任一表节点主体。
- 焦点集合（不透明度 1.0）：该表泳道全部元素（表节点+列线+该列端口）+ 直接相邻元素（读写该表的步骤节点+其全部连线+连线触及的其他列线）。
- 非焦点集合：其余全部图元 `setOpacity(0.15)`（颜色线宽不变）。
- 退出/切换（按序判定）：①再点同表→退出 ②点空白/穿透元素→退出 ③点步骤节点→退出并选中，**选中步骤回到常态不透明度 1.0、不暗化**（W-02 E 裁定）④点另一表→焦点切换重算 ⑤~~点调序按钮→不退出~~（调序按钮已取消，C1，本条失效）⑥结构性刷新→自动退出。
- 纯视图态：controller 持有 _focus_key，不发信号不写模型；可与选中叠加；瞬时切换不滚不缩。

### 5.6 缩放/平移规范

- 缩放范围 **[0.40, 2.50]**。依据（图窗格宽 757px，视口约 745px）：下限 0.4 视口纵览 ≈1863 场景 px ≈7.3 泳道列（覆盖典型流程），节点高 22px 仍可点击；上限 2.5 文字 ≈33px 低视力可用。auto-fit 受同一钳制（场景 0.4 仍放不下时按 0.4 显示左上+滚动条，可读性优先）。
- auto-fit 标志（view 持有 `_auto_fit` 布尔）：初始 True；空→非空首次构建后 fit；任一用户手动操作（Ctrl+滚轮/拖拽/滚动条）→置 False；工具栏 **[适应画布]**→置 True 并立即 fit；resizeEvent 仅 _auto_fit=True 时经 **200ms** QTimer 防抖 refit；非 auto-fit 时 resize 记录旧视口中心场景点、resize 后 centerOn 恢复，`setResizeAnchor(NoAnchor)` 消除内容漂移。**高度按实际视口 `view.height()` 实算，不硬编码 640**（W-02 H 裁定）。
- **rebuild 后一律不 fit**（P0-1 根治；替换现行 page:537 每次必调）。

### 5.7 右键菜单与工具栏

| 目标 | 菜单项 | 动作 | 可用性 |
|------|--------|------|--------|
| 步骤节点 | 上移/下移/删除步骤 | step_action_requested → page 分发 _on_move_step/_on_delete_step；**删除须二次确认弹窗（2026-09-16 D6 §8.5 定稿，文职文案）** | 边界禁用 |
| ~~输入表节点~~ | ~~左移/右移~~ | ~~table_reorder_requested~~ | **（2026-09-15 取消，C1：整行作废）** |
| 其余 | 无菜单 | — | — |

实现：节点覆写 contextMenuEvent → controller 信号 → page 构建 QMenu，`menu.exec_(event.screenPos())`。

图工具栏（28px，左窗格顶部）：[适应画布] 按钮 + 缩放百分比只读 QLabel（如"62%"，缩放/fit 后更新）。

### 5.8 视觉反馈标准表与测试策略

> **设计意图（W-02 D 裁定）**：步骤节点用浅色承载状态色变化、表节点用深色突出"泳道起点"，一深一浅为**有意对比**，非遗漏统一。

**步骤节点视觉**（整合决议 D3：浅色填充+#222 文字，与进度页配色统一）：

| 状态 | 填充 | 边框 | 线宽 | 不透明度 |
|------|------|------|------|---------|
| 常态 | #ffffff | #aaaaaa | 1px | 1.0 |
| 悬停 | 同当前填充 | #2b7cd3 | 2px | 1.0 |
| 选中 | #cfe8ff | #2b7cd3 | 2px | 1.0 |
| 运行中 | #fdf3c0 | #f0ad4e | 2px | 1.0 |
| 完成 | #c8f0c8 | #5cb85c | 1px | 1.0 |
| 失败 | #f6caca | #d9534f | 2px | 1.0 |
| 焦点暗化 | 色不变 | 色不变 | 不变 | 0.15 |

叠加优先级：填充=失败>运行中>完成>选中>常态；描边=选中>悬停>状态描边>常态；暗化正交叠加。表节点：常态 #2b7cd3/#1a5ca8 1px 白字，悬停 #3a8ce2，焦点表描边 #0d47a1 2px（唯一新增 hex），暗化 0.15。

> **端口角色（W-02 G 裁定）**：端口保持固定中性色词表（§4.3 六类），**不随步骤选中/hover 变色**；配合 W-03 P0#4 端口默认隐藏，端口染色无必要。

**边视觉词表（2026-09-18 F-3 新增，与 §4.3 五类边词表配套）**：LANE_IN #999999｜LANE_DEV #4a90d9｜ACCESS #888888｜PRODUCE #2ecc71｜PRODUCE_LABEL #2e7d32（白底衬底深绿字）｜DEPRECATED 边 #757575｜DANGLING #d9534f｜START #2ecc71｜END #d9534f｜HIGHLIGHT #2b7cd3 2.5px。**画布无常驻图例**（F-1）：语义由颜色×线型×箭头×角标×产出边标签 + 详情面板「连线说明」承载；任两类边至少两维可辨（差异矩阵见 `_temp/DAG-rebuild/plan.md` §1.3）。

**测试策略**（QA 子代理核验，整合决议 D5；**2026-09-01 裁定：`Test/unit/` 目录口径确认，R4 备选方案作废**；**2026-09-20 裁定改址：DAG 重建验证通道落 `rpa_engine/tests/`，见下注**）：
- 政策口径：架构阻塞 #4 原文"测试工作暂不在本仓库**执行**"——边界是执行非编写；测试代码作为交付物编写，docstring 固化人工触发命令（先例脚本已随 09-18 `_temp` 收敛清理，先例结论见 `_temp/DAG-rebuild/plan.md` 附录 C），执行由人工在真机 conda 环境触发、输出粘贴 task-record 作验收证据。
- 工具：**unittest**（conda 环境实测无 pytest；写成 TestCase 风格未来可被 pytest 直接收集）。
- 分层：纯 Python（LayoutEngine/LayoutConfig/路由/diff 计算——准入断言：模块不含 PyQt5 字样）→ unittest 纯逻辑；Qt 场景/视图 → offscreen fixture（QT_QPA_PLATFORM=offscreen 前置于任何 PyQt5 import，先例方法见 `_temp/DAG-rebuild/plan.md` 附录 C；现行参照 `SampleCode/run.bat --offscreen`）；文字/tooltip/鼠标手势 → 真机人工清单。
- 测试文件（Test/unit/ 新目录）：test_dag_layout_engine.py（golden G1 5 步典型/G2 12 步压力/G3 退化 + 7 项不变量：两两不相交/端口贴边界/折线轴对齐/sceneRect⊇包围盒/确定性/列行距与锚定不变量/Config 边界）、test_dag_edge_router.py（端口侧 9 格真值表/箭头出界断言/堆叠无重叠/避障）、test_dag_diff_registry.py（增删改 id 快照比对/状态路径 rebuild 计数为 0）、test_dag_scene_view_offscreen.py（视角保持 6 元素断言/auto-fit 取消/缩放钳制循环）、README.md（政策声明+执行命令 `python -m unittest discover -s Test/unit -v`）。
- 附带规约同步：AGENTS.md §6 Test/ 行口径更新（M7 执行）。

> **测试落点回写（2026-09-20 M-a/M-d 落地，[已校验一致]）**：09-20 裁定
> DAG 重建验证通道改址 **`rpa_engine/tests/`**（豁免登记见 AGENTS.md §6 与
> architecture.md §9 #4；上表 `Test/unit/` 目录口径对该通道作废，其余政策
> 口径不变）。现行交付：`test_graph_edges.py`（14 项：五类边 schema/计数
> 不变量/生成顺序/键唯一/弃用变体）、`test_translation.py`（8 项 E2E：
> roundtrip/弃用级联×2/new_table 剔除/overwrite 两步链/STEP_DESC 同源/
> 全弃用空流程/load 回归），执行命令
> `cd rpa_engine && python -m unittest discover -s tests -v`（22 用例全绿，
> 09-20 实测）。Qt 渲染层验证走 `_temp/DAG-rebuild/smoke_mb.py`（offscreen
> 33 项：图元计数/选中联动/失败气泡/弃用重绘/空态/截图），真机文字与手势
> 走 §5.9 清单。

### 5.9 真机人工回归检查单（15 条，绑定缺陷编号）

| # | 缺陷 | 操作步骤 | 预期结果 |
|---|------|---------|---------|
| 1 | P0-1 | 导入 2 表配 5 步，Ctrl+滚轮缩至约 150% 并平移，修改任一步骤参数并确认 | 视角不跳变不回 fit，原选中仍高亮 |
| 2 | P0-1 | 同上状态下切换某步骤目标表下拉并确认 | 视角保持；仅相关连线/节点更新 |
| 3 | P0-1/P1-5 | 运行至中段失败→放弃→回阶段 1→重新确认导入→恢复配置 | 节点运行色按恢复前呈现，不归零为灰（验收依据：§3.7 状态随 key 延续机制 + §5.1 reset 收窄） |
| 4 | P0-2 | 搭 12 步含 2 次跨表合并压力流程，首次进入触发 fit | 文字可辨认；画布无大片空白 |
| 5 | P0-2 | 观察上述流程排布 | 行对齐、每步锚定输出列中心，无阶梯漂移 |
| 6 | P0-3/S4-2 | 任意缩放级别检查全部箭头 | 箭头贴节点边界端口，不遮标题；merge 无"蝴蝶结" |
| 7 | P0-3 | 观察跨表 merge 输入连线 | 正交折线，无斜线不穿中间节点 |
| 8 | S4-1 | 检查 merge 输出交点 | 输入口双环样式清晰，无两个独立标记叠一点 |
| 9 | P1-1 | 单击某表节点→再单击空白 | 焦点模式进入（其余 15% 暗化）/退出正确 **[已过时-待确认]**（W-03 收敛：无独立焦点模式；现行＝选中步骤关联边高亮+无关 30% 淡化，选表不整图淡化；空白点击清选中） |
| 10 | P1-2 | 在右侧选中一步 | 图节点高亮（双向闭环）；点图节点右面板切回 |
| 11 | P1-2 | hover 超长名节点 | tooltip 显示完整名称+操作类型+目标表 **[已过时-待确认]**（W-03 收敛：无 tooltip；超长名由卡片省略号+右面板详情承载） |
| 12 | P1-3 | Ctrl+滚轮缩放到极限 | 停在 [0.4,2.5] 边界 |
| 13 | P1-3 | 拖拽改变窗口尺寸 | 手动视角不被覆盖；[适应画布] 可恢复全景 |
| 14 | P1-4 | 逐一左键点击泳道线/端口/连线 | 无死点：一律按空白语义响应 |
| 15 | P1-4 | 步骤右键菜单/输入表右键菜单/空白拖拽 | 菜单动作生效；平移正常 **[已过时-待确认]**（W-03 收敛/D6：画布严格只读，无右键菜单；空白拖拽平移保留） |
| 16 | M25① | 点击画布输入表节点→右面板点「弃用此表」→再点「恢复使用」 | 弃用：表灰填充虚线边+角标「已弃用」+引用边转灰虚线+下游卡片「待配置」橙角标；恢复：全部还原；全程可逆无弹窗 |
| 17 | M25② | filter 步骤「结果保存方式」选「覆盖原表」→保存配置（或开始执行） | 弹二次确认（含目标表名+"原表数据将被替换且不可恢复"）；取消→阻断保存/执行且配置不变；确认→正常继续 |
| 18 | M25③ | 弃用全部被引用输入表使闭包覆盖所有步骤→点「开始执行」 | 拦截弹窗（提示恢复弃用表或改存模板），不进入执行；「保存配置」仍允许 |

---

## 六、开发里程碑与任务拆解（合计 19.5 人日）

> 开发模式：单人开发 + AI Agent 协作。里程碑完成即 py_compile + 对应单测（版本控制/快照回退由 **git + 人工** 接管，R1）。**Git 写操作（提交/推送/分支/合并/回退等）由人工接管，Agent 不执行**；Agent 仅在比对差异时使用只读 `git status`/`git diff`/`git show`/`git log`（2026-10-24 口径细化；整合决议 D6，2026-09-01 裁定；回退机制 2026-09-14 R1 退役 `_temp/BackUp/`）。**M0-M7 已于 2026-09-20 全阶段闭环**（实际实现为 `gui/node_graph.py` 单文件，`gui/graph/` 包未采纳）。

| 里程碑 | 内容 | 人日 | 交付物与验收标准 | 版本交接（git 人工） |
|--------|------|------|----------------|--------|
| **M0 奠基** | graph/ 包骨架（9 文件空壳+头注释）；style.py（ZLayer/LayoutConfig/GRAPH_* 全常量）+ Config 边界单测；GraphSpec/LayoutResult dataclass 定义 | 1 | LayoutConfig 非法值抛 ValueError 单测过；包骨架 py_compile 过 | 动首文件前提请人工提交基线 |
| **M1 布局引擎核心** | spec.py build_graph_spec（model/entries→GraphSpec）；layout.py 列排序/col_cx/row_cy/节点矩形/锚定兜底链/scene_rect/fingerprint | 2 | test_dag_layout_engine.py golden G1/G3 + 不变量 1-6 全绿（纯 Python，零 PyQt5） | — |
| **M2 端口与边路由** | 首日交付路由模块方法级骨架清单（先行评审）；端口 6 类计算（含堆叠公式）；lane 起终点/tap 规则；access 侧选择/单段构造；箭头几何；test_dag_edge_router.py（9 格真值表/箭头出界/堆叠/避障） | 3.5 | G2 压力用例 golden 钉死；路由单测全绿 | 完成时请人工提交 |
| **M3 图元与差量场景** | 首日交付 items/scene 方法级骨架清单（先行评审）；items.py（TableNodeItem/StepNodeItem/EdgeItem/PortItem：局部几何+文本预计算+视觉词表+浅色填充）；scene.py keyed registry + apply(diff) + 单点状态入口；test_dag_diff_registry.py | 3 | 增删改 id 快照断言过；状态路径 rebuild 计数 0 断言过；offscreen 渲染 PNG 人工比对（方法参照 `SampleCode/run.bat --offscreen` 通道） | 完成时请人工提交 |
| **M4 视图与控制器** | 首日交付 controller/view/widget 方法级骨架清单（先行评审）；view.py（缩放钳制/平移/auto-fit 标志/resize 语义/右键转发）；controller.py（四状态+五信号+重放）；widget.py 组合+工具栏；test_dag_scene_view_offscreen.py | 3 | 视角保持 6 元素断言过；auto-fit 取消断言过；缩放循环钳制断言过 | — |
| **M5 交互闭环** | hover+tooltip；双向选中同步+相邻连线高亮+ensureVisible；焦点模式；右键菜单；splitter setSizes([757,505]) | 3 | 交互语义表逐项 offscreen 可测部分覆盖；其余进真机清单 | — |
| **M6 页面集成切换** | page_operation_config.py 按 §3.10 清单适配（node_graph.py 留树零引用）；offscreen 全流程冒烟；**真机人工回归 15 条执行**（用户参与） | 2 | 15 条全过；main_window/表单区/模板区零改动核验（grep 比对） | 切换前 / 验收后请人工各提交一次 |
| **M7 收尾** | 删 node_graph.py（先 grep 零引用）；Test/unit/README + AGENTS.md §6 口径同步（**2026-09-20 已改址 `rpa_engine/tests/`**）；architecture.md §8/INDEX/README 文档同步；build.bat 编译冒烟；全局更新校验机制（docs/doc-governance.md §4）；任务记录归档 | 2 | 全库 grep node_graph=0；exe 产出且启动自检过；五项校验通过 | — |
| **M-D 动态配置示范验证（已完成 2026-09-16；09-17 细节优化、09-18 固化 SampleCode）** | 示范区内（`_temp/DAG-rebuild/SampleCode/`）：功能元数据注册表、后端 6 动态接口、右参数面板、弃用/悬空/待配置渲染、五类边与起止标识、三态插入、无图例三层语义；设计回写 §八 | 0（示范区，不计入 19.5） | 61 单测 + 11 场景截图全绿（09-18 人工真机验证通过）；W-03 门控解除 | — |

> M2 含 0.5 人日技术密度缓冲（全计划最高复杂度段：端口体系+正交路由+单测）。
>
> 依赖关系：M0→M1→M2→M3→M4→M6 严格串行；M5 可与 M4 后半并行（交互项依赖 view/controller 就绪）；M6 依赖 M3-M5 全部完成；M7 依赖 M6 真机验收通过。

---

## 七、风险预判与备选方案

| # | 风险 | 概率/影响 | 缓解措施 | 备选方案 |
|---|------|----------|---------|---------|
| R1 | 差量刷新实现复杂度超预期（diff+重放+视口恢复三态交织） | 中/高 | M3/M4 各带 offscreen 断言；fingerprint 短路先做（大部分编辑场景布局局部变化） | 降级为"全量重建+状态保持"：仍 clear 重建但 controller 重放缩放/平移/选中/运行色（P0-1 用户感知已消除，仅牺牲 item 复用） |
| R2 | 正交路由在极端拓扑（输入列远于输出列且多交叉）可读性仍差 | 中/中 | G2 压力用例先行钉死；交叉计数进 golden 断言 | 交叉点前后 3px 断口方案（§4.4 已预留，不动架构） |
| R3 | offscreen 文字 0 像素限制自动化视觉验证 | 高/低 | 断言一律几何化（boundingRect/pos/路径点/数量）；文字项进真机清单 | 无需备选（策略已规避） |
| R4 | 测试政策边界（不在本仓库执行） | 确定/中 | 测试代码交付+人工触发命令固化+输出粘贴 task-record；开发中自检沿用 _temp/ 验证脚本先例 | 【已作废】2026-09-01 裁定 Test/unit 口径确定 |
| R5 | PyInstaller 打包遗漏新子包 | 低/高 | 全部顶部静态 import（QA 已核验 spec L27-53：gui 包本就不在 hiddenimports，靠静态链发现）；M7 build.bat 冒烟强制验证 | 若冒烟失败：spec L27-53 追加 'gui.graph' 等顶层包名（pathex=['rpa_engine']） |
| R6 | 重构中断/回退 | 中/高 | 版本回退由 **git + 人工** 接管（R1），Agent 不执行 git；里程碑完成前确保工作区可被人工回溯（提交点见 §六「版本交接」列） | — |
| R7 | 视觉规范变更（浅色填充+#222 文字）引发用户不适应 | 低/低 | 与进度页四色完全同源（styles.py 常量），风格一致性增强 | 保留一键回退：StepNodeItem 填充色映射表集中一处可整体切回饱和色方案 |

---

## 八、动态配置与用户视角呈现层规范（2026-09-16 D6 裁定回写）

> **示范验证基线**：`_temp/DAG-rebuild/SampleCode/`（61 单测 + 11 场景截图，2026-09-18 人工真机验证通过；`_temp` 无约束力，仅作验证证据）。
> **总原则**：DAG 画布**严格只读**（仅呈现与查看交互），配置全部经右侧参数面板完成（对齐 AGENTS §2.2 条 3「GUI 只生成和编辑参数文件」与 architecture §8 前端/后端边界）；面向无技术背景文职用户（AGENTS §2.1 条 6）。

### 8.1 弃用语义

- **定义**：用户显式标记某表「已无作用」；入口=右面板「弃用此表/恢复使用」（选中表节点时）。
- **渲染**：灰 #9e9e9e 填充 + 虚线边 + 角标「已弃用」+ 其引用连线转 #757575 虚线 + 详情面板「连线说明」标注（2026-09-18 F-1：画布无常驻图例）；弃用表**保留显示、位置稳定**（只改样式不移动）。
- **底层语义**（正式重构）：执行时跳过该表生成、释放对应内存（对齐 AGENTS §2.1 条 5 内存安全）。**（2026-09-20 D-1=B 执行注：执行级实现＝前端翻译不生成弃用闭包内步骤与闭包输入表＋会话结束清理兜底（SessionDB close 删库）；单表粒度释放列 v3.2 待办；翻译契约见 `_temp/DAG-rebuild/plan.md` §4.2）**
- **约束**：下游步骤引用弃用表 = 校验错误（config_state=incomplete + 提示"引用了已弃用的表『X』"），**不允许静默**。

### 8.2 输入完整性契约

- **强制校验**（类比函数编译期参数检查）：每步执行/重算时校验——target_table 存在且非弃用；extra_inputs 有效数 ≥ 注册表 extra_min（mapping_match/merge_tables 需 ≥1）；必填参数非空。
- **违规呈现**：config_state=incomplete → 卡片橙描边 #f0ad4e 2px + 角标「待配置」+ 右面板红字缺失清单（具体到"label"级）。
- **悬空引用**（引用不存在的表，如产表步骤被删除）：红虚线短桩（卡片左缘 40px）+「⚠」+ 角标「输入缺失」；**绝不静默忽略**。

### 8.3 表节点生命周期

| 阶段 | 规则 |
|------|------|
| 创建 | 产表步骤（fork/merge 且非 overwrite）添加或改参 new_table → recompute 生成 derived 表（display=操作中文名+"结果"） |
| 引用 | 步骤 target/extra 指向；连线/泳道由引用推导 |
| 覆盖 | 顺序类（rename_columns/convert_dtype）与 overwrite_target 模式原地修改，不新增表 |
| 删除 | 产表步骤删除 → 其表若无其他 producer 则从表集合移除 → 下游引用悬空（§8.2 显式提示） |
| 弃用 | 用户显式标记（§8.1）；保留显示（**09-20 D-1=B 执行注：to_dict 过滤弃用闭包，见 §8.1 注**） |
| 顶部表区联动 | 全部经 recompute 重算；输入表头 y=60 高 40 / 派生表头 y=78 高 40（错位示"由步骤产出"），header_bottom=118 |

### 8.4 功能元数据注册表

- **正式层级=后端 ops 侧**：`gui/models.py` 的 `STEP_CATALOG`（9 项中文目录）/`OUTPUT_OPS`（产表集合）/`STEP_KIND`（end/merge/fork/sequential）为雏形；扩展字段：`params_schema`（key/label/类型/必填/默认）、`produces_table`、`output_mode` 支持、`deprecatable`、**`STEP_DESC`（操作类型级静态业务描述，2026-09-20 D-2=a 裁定新增）**。
- **GUI 只读取**注册表（前端/后端边界，architecture §8）；工具栏功能按钮与右面板表单**全部由注册项驱动**——新增功能=加一条注册项，禁止硬编码按钮/表单。
- **output_mode**（`new_table`｜`overwrite_target`）仅 filter/dedup 拥有；overwrite 时该步骤不产新表（行为等同 sequential）。
- 演示实现参照：`_temp/DAG-rebuild/SampleCode/backend/func_registry.py`（同源对齐，不 import 生产代码；生产侧字段扩展见 M18：`gui/models.py` 增 `PRODUCE_LABEL`/`produce_label()`/`is_end_op()`/`MAIN_BUTTONS`/`MORE_BUTTONS`）。

### 8.5 右侧参数配置面板与 DAG 只读原则

- **面板=配置唯一入口**：schema 驱动 QFormLayout 动态表单（text→QLineEdit、enum→QComboBox、table→QComboBox）；「保存参数」触发 try_apply 收拢校验（复用 `gui/forms.py` 的 get_params/validate_params/try_apply 注册模式）后写回步骤 params/target/extra。
- **三态**：选中步骤=参数表单+「删除此步骤」（二次确认，文职文案）；选中表=表信息+弃用/恢复；无选中=操作提示。**（2026-09-20 M15/M25 落地注：三态已实现于 `page_operation_config.py`——步骤态另含「连线说明」行、删除无二次确认沿用 [del] 即删口径；表态＝表信息+连线说明+弃用/恢复按钮（可逆无确认）；步骤「上移/下移」随 C1 删除）**。
- **DAG 画布严格只读**：仅保留缩放（钳制）/平移/全览/点击选中/高亮上下游；**零拖拽、零连线编辑、零画布内参数修改**。边界澄清（2026-09-16 D6）：「只读」= 禁止参数编辑与拖拽/连线编辑；**查看类交互与结构性菜单仍按 §5.2/§5.3/§5.5/§5.7 保留**（hover/tooltip、焦点模式、步骤右键上移/下移/删除——删除须二次确认，经 page 分发，不在画布内直接改数据）。
- **联动刷新链**：保存/删除/弃用 → recompute() → 全量重绘（表节点/连线箭头/顶部表区/起止标识/弃用与待配置样式）→ selected 保持（位置稳定、高亮不丢）。

### 8.6 动态重算与布局联动

- **recompute() 全量重算**：seq 按数组序重排 1..n；表集合派生（§3.3 规则）；每步 config_state（§8.2）。演示级=全量重算+全量重绘（生产级差量刷新沿用 §3.7，状态保持不丢）。
- **插入三态锚点**：无选中→流程末尾（末步 is_end 则插其前）；选中步骤→其后；选中操作表→其产出步骤后；选中输入表→其最后消费者步骤后（无消费者→末尾，同 is_end 保护）。
- **列序稳定**：新派生表插产出步骤锚列+1，后续列顺延；未受影响节点视觉位置不变。
- **画布无常驻图例（2026-09-18 F-1 废止原"右下角固定 7 词条"口径）**：语义三层承载——①颜色×线型×箭头×角标（输入表/结果表/已弃用/待配置/输入缺失）②产出边标签（「新表」/「复制新表」）③详情面板「连线说明」行；原 7 词条（待执行/执行中/已完成/已失败/待配置/已弃用/输入缺失）保留为**详情面板与角标用词**，不再以常驻图例块呈现；边视觉词表见 §5.8、五类边见 §4.3。

---

## 附录 A：主代理整合决议（D1-D11）

| # | 冲突点 | 裁决 |
|---|--------|------|
| D1 | z 层级三版不一（架构师 0-50 / 渲染 -10~10 / UX 沿用现值） | 采渲染专家 8 级枚举；箭头 -3 置节点之下为防御性设计 |
| D2 | 独立标记图元存废（架构师保留 markers 字段+防重叠偏移 / 渲染删除并入端口） | 采删除方案：LayoutResult 无 markers 字段，S4-1 从数据层根除（**2026-09-18 F-2 修订**：数据层无 markers 不变；渲染层允许装饰式起止标识+起止连接边 flow，不占布局行/不可交互，见 §4.3 五类边词表） |
| D3 | 步骤节点配色（现行饱和填充+白字 / UX 浅色填充+#222） | 采 UX 方案，与进度页配色统一；R7 保留回退 |
| D4 | 契约命名（架构师 GraphSpec / 渲染 GraphLayoutData 混用） | 统一 GraphSpec/LayoutResult（架构师命名），数学规范从渲染专家 |
| D5 | 测试框架（pytest 假设 / QA 实测无 pytest） | unittest（TestCase 风格兼容未来 pytest 收集） |
| D6 | 版本控制表述（AGENTS.md §1 称无 VCS / QA 实测 .git 存在） | 【2026-09-01 已裁定·含补充】AGENTS.md §1/§2.4/§7.2 表述已按实际修正；备份惯例曾迁移为 `_temp/BackUp/`（**2026-09-14 R1 已退役**）；**Git 写操作由人工接管，Agent 不执行**；Agent 仅在比对差异时使用只读 `git status`/`git diff`/`git show`/`git log`（2026-10-24 口径细化）。追溯单轨 = git + 人工 + task-records |
| D7 | 焦点模式不透明度 | UX 专家 0.15，6 条退出规则全套采纳 |
| D8 | 选中同步机制（架构师 selection_changed 双向信号+防环 / UX 直调方法） | 页→图方法调用单向，删双向信号，天然无环 |
| D9 | 缩放边界与 auto-fit 语义 | UX 专家 [0.40,2.50] + 标志位 + 200ms 防抖全套采纳 |
| D10 | 工具栏与 splitter | [适应画布]+缩放百分比标签 28px 工具栏；setSizes([757,505]) |
| D11 | 表 selected 信号参数 | 由 display 别名改 table_key（页面槽行为不变，语义更稳） |

## 附录 B：设计输入来源

- 分析报告：docs/analysis/DAG_visualization_analysis.md（P0-P2/根因 A-E/S1-S6/R1-R6）
- 架构师设计：5 层分层/9 文件/GraphSpec/LayoutResult/信号契约/状态矩阵/差量刷新/页面适配清单/过渡策略
- 渲染专家设计：坐标铁律/泳道 2.0 数学/端口 6 类词表/正交路由/ZLayer/LayoutConfig/增量管线/文本预计算
- 交互UX专家设计：交互语义表/双向选中/hover+tooltip/焦点模式/缩放规范/右键菜单/视觉反馈表/工具栏与 splitter
- 质量保障设计：测试政策核验（原文引用）/unittest 分层可测性/核心覆盖点/15 条真机回归单/可行性风险/Test 布局
