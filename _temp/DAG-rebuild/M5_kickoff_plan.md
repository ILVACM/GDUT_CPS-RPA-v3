# M5 立项方案框架（M5-a 物理名 t_{uid} ／ M5-b 插入锚点语义）

> 状态：**方案态 [待审核]**（AGENTS §4.5：未经人工裁定不得据此实施）｜日期：2026-09-21
> 立项依据：人工裁定 H4=要（W-03 审计修复轮治理收尾）；前身=冻结方案 D-C3/D-B3 两项"独立议题"。
> 审核通过后：迁入 docs/plan/ 注册（下一治理轮）并另行批准实施排期。本文件当前零实施。

---

## M5-a 派生表物理名 t_{uid}（原 D-C3）

### 背景（问题本质）
执行期派生表物理名 `t_s{step_index}` 按**执行序**命名（ops/step_executor.py L192 区）：
- 覆盖模式合成步 `S{n}_cp` 占执行序号 → 其后所有派生表物理名整体后移（S2 得 t_s3）；
- 增删/调序步骤后同一逻辑表的物理名跨轮次漂移；
- 现有缓解：`output_tables` 回写 tooltip+报告页映射列（可见性补丁，非根治）。

### 目标
物理名与步骤稳定 ID 绑定：`t_{uid}`（uid=models `_new_uid()` 8 位短码），执行序变化不再改物理名；T#↔物理名映射跨轮次稳定。

### 关键决策点（实施前须逐项裁定）
| # | 决策点 | 现状 | 待裁定内容 |
|---|---|---|---|
| K1 | **uid 持久化策略**（前置阻塞项） | uid 为前端键：to_dict 双口径剔除、load_from_dict 重生成（跨持久化不稳定，R1 休眠字段） | 三选一：①uid 写入 v3.1 JSON steps[]（schema 扩键，parser 兼容忽略未知键——需核验）②独立映射文件（workspace/uid_map.json，GUI 侧维护）③业务口径剔除但编辑态保留（last_config/模板含 uid，执行文件不含——执行期仍需从某处取 uid，论证闭合性） |
| K2 | step_executor 命名分支 | `clean_params.pop("output_table") or f"t_s{step_index}"` | 改 `or f"t_{uid}"` 的 uid 传递通道（StepDef 增 uid 字段 vs params 携带 vs table_id_map 预注册） |
| K3 | 存量兼容 | 会话库即用即抛（session_*.db 随轮生灭） | 论证无迁移负担；gui_workflow.json 旧文件 t_s{n} 无残留引用（物理名仅执行期内存映射）——核验后记录 |
| K4 | 引用链核对 | executor table_id_map/output_tables、validator、tooltip 回写、报告页映射列 | 全链路以 T#→物理名映射消费，物理名生成点唯一（step_executor）——走查确认改造面收敛 |

### 影响面
ops/step_executor.py（命名分支）+ gui/models.py（uid 持久化，按 K1）+ engine/parser.py（若 K1=①，StepDef 扩字段）+ tests/smoke 扩例；GUI 渲染层零改动（tooltip 消费 output_tables 不变）。红线核对：§2.2-5（改动在 ops/ 内）、§2.2-2（JSON 唯一载体——K1=①时 schema 扩键需同步 architecture.md 参数文件 Schema 节，触发 doc-governance §4）。

### 里程碑建议
M5-a-1 K1-K4 裁定与详设（施工图级）→ M5-a-2 uid 持久化落地+单测 → M5-a-3 命名切换+引擎实测（test_engine_overwrite 扩 t_{uid} 断言）→ M5-a-4 全量回归+文档同步。

## M5-b 插入锚点语义（原 D-B3）

### 背景
现状"顺序即添加顺序"（新步骤恒追加末尾，调序 UI 已删且 H2 裁定不恢复）；删除重加是当前唯一调序手段，多步骤流程配置效率低。

### 目标
三态锚点插入（冻结方案 §8.6 既定语义）：无选中→流程末尾（末步 is_end 则插其前）；选中步骤→其后；选中操作表→其产出步骤后；选中输入表→其最后消费者步骤后（无消费者→末尾，同 is_end 保护）。

### 关键决策点
| # | 决策点 | 待裁定内容 |
|---|---|---|
| K5 | 模型接口 | add_step 增 insert_at 参数 vs 新增 model.insert_step(index, type)——倾向后者（add_step 签名已稳、调用点多） |
| K6 | 锚点解析落点 | page 层解析选中态→index（模型不感知 GUI 选中）；_on_add_step 增锚点计算分支 |
| K7 | 画布联动 | 插入后 _select_step(new_index)+select_node；列序/行序经 rebuild 自然重排（row_cy 按数组序）——核验 is_end 步保护 |
| K8 | 撤销兼容 | 插入为可撤销操作？（现 _push_undo 仅挂破坏性操作；插入非破坏——倾向不压栈，删除即回退，裁定确认） |

### 影响面
gui/models.py（insert_step）+ gui/page_operation_config.py（锚点解析+_on_add_step）；node_graph/graph_edges 零改动（rebuild 按数组序全量重排）；tests 扩插入位序用例。

### 里程碑建议
M5-a 完成后启动（uid 稳定键先就位，插入引起的重排不牵动物理名——两议题解耦收益）：M5-b-1 K5-K8 裁定详设 → M5-b-2 insert_step+锚点解析 → M5-b-3 联动与回归。

## 风险与边界
- 两子议题均不触 ETL 架构刚性（数据表驱动+SQLite 中间层+JSON 唯一载体不变）；K1=①为唯一 schema 触碰点，需 architecture.md 同步（治理轮放行）。
- 排期依赖：M5-a 先行（M5-b 解耦收益）；exe 重建（W-20）建议在 M5 实施完成后再做，避免二次打包。
- 本文件为框架级（背景/目标/决策点/影响面/里程碑），施工图级详设在 K1-K8 裁定后另行产出（沿用 W-03 方案具体化模式）。
