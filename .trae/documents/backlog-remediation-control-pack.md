# 功能函数记录表单源化与 W-22／N 系列结清 · 控制包与施工计划

> 计划时点：2026-10-19（R14 审计后）｜依据：`_temp/ImportData/plan.md` Part 3 台账（79 行）＋ `docs/function-spec-rules.md` §7（18 行）＋ `docs/backlog.md` W-22
> 定位：**跨面控制包**（逐项处置 ＋ 例外登记 ＋ 分批施工），非单点修复

---

## 一、摘要

把「上面提到的所有问题」一次结清：**35 项 B-45~B-79 ＋ F4（=B-41）＋ F5**。逐项给处置、分批施工、真机/构建项登记为例外（带责任方、到期、补偿控制）。核心是一条设计决定——**把功能函数的参数默认值收敛为引擎侧单一源（`params_schema`）**，一举消掉 F4/B-41/B-64/B-69 四处双源。

**通俗说明**：
- 现在「每个功能函数有哪些参数、缺省值是多少」这本账**记了两份**（引擎一份、界面一份），两份还会打架（比如"缺省怎么匹配表"，界面说"保留全部行"，引擎说"只留匹配上的行"，结果手写配置会静默少数据）。
- 本计划把它**改成只记一份（记在引擎里）**，界面和引擎都从这一份读；再补上"谁改了一侧另一侧不跟就红"的门禁测试。
- 顺带把 4 项已经做完、只是账上没划掉的（B-51/B-75/B-77/B-78）**结账**，把 8 项"守规矩"测试补齐，把依赖锁 `requirements.lock` 生成出来。

---

## 二、现状分析

### 2.1 红线口径澄清（决定"越界"是否成立）

`_temp/ImportData/plan.md` §0.1 的四项红线（① `engine/executor.py` 分发/信号/线程 ② GUI 布局 ③ `ops/` 9 项 BUILTIN_OPS 行为 ④ 新依赖/`eval`/`exec`/`pickle`/硬编码绝对路径）是**上一批次（ImportData）的自我范围限定**，非 `AGENTS.md` 永久红线：

- **①** 与 `AGENTS.md` §2.2 条 5「不改编排代码」同域（architecture §3.3 界定编排代码＝`engine/`）→ **本批不动**，列例外；
- **②** 本批只改**文案**，不动布局（布局约束源自用户裁定，继续遵守）；
- **③** `AGENTS.md` 未禁止修改既有 op 行为（其条 5 约束的是**新增** op）→ 属批次自我约束，**用户已授权本批放宽**；
- **④** 继续**硬遵守**（不引入新依赖、不用 `pickle`/`eval`/`exec`、不写绝对路径）。

### 2.2 已核验的关键代码实况（审计证据）

| 事实 | 位置 | 含义 |
|---|---|---|
| `BUILTIN_OPS` 9 条目 × 6 字段 | [step_executor.py](file:///d:/CPS-GPES_RPA-20250312/v3/rpa_engine/ops/step_executor.py#L52-L109) | 参数白名单唯一源 |
| 引擎回退 `mode="inner_join"`；GUI 默认 `left_join` | [step_executor.py L240](file:///d:/CPS-GPES_RPA-20250312/v3/rpa_engine/ops/step_executor.py#L240) ／ [models.py L985](file:///d:/CPS-GPES_RPA-20250312/v3/rpa_engine/gui/models.py#L985) | **F4 核心**：手写 JSON 省略 `mode` → 静默丢主表未匹配行 |
| 引擎回退 `from_type=""`；`convert_dtype` 拒绝空串 | [step_executor.py L292-293](file:///d:/CPS-GPES_RPA-20250312/v3/rpa_engine/ops/step_executor.py#L292-L293) ／ [table_schema.py L144-148](file:///d:/CPS-GPES_RPA-20250312/v3/rpa_engine/ops/table_schema.py#L144-L148) | 手写 JSON 省略该键 → **保证抛错**（非"语义不同"，是硬失败） |
| `target_param`/`match_param` 零消费者 | step_executor L41-49 注释自证 | B-62 可删 |
| `Workbook()` 普通模式（非 `write_only`） | [exporter.py L163](file:///d:/CPS-GPES_RPA-20250312/v3/rpa_engine/ops/exporter.py#L163) | B-03 未落地 ⇒ L9-11 注释失实（B-76） |
| 后缀静默改写 `.xlsx` | [exporter.py L143-144](file:///d:/CPS-GPES_RPA-20250312/v3/rpa_engine/ops/exporter.py#L143-L144) | B-49 |
| `validator` 仅校验白名单，无弃用校验 | [validator.py L89-93](file:///d:/CPS-GPES_RPA-20250312/v3/rpa_engine/engine/validator.py#L89-L93) | B-53（D4）缺口 |
| `requirements.lock` 不存在，头注已指向 | [requirements.txt L5](file:///d:/CPS-GPES_RPA-20250312/v3/requirements.txt#L5) | B-50 |
| 三处「9」断言 ＋ 一处 `len(list_ops())` | test_graph_edges L200／test_translation L149／test_ops_contracts L334／smoke_m1m3 L188 | B-67/B-68（R14 已同步为四处） |

---

## 三、逐项处置表（决策点＝推荐，全部采用）

### A. 直接结账（4 项，无代码改动）

| 项 | 处置 | 依据 |
|---|---|---|
| **B-51** | 关闭（已覆盖） | A-15（`import_dataframe_atomic`）＋ A-16（`ensure_input_tables`）已落地两式 |
| **B-75** | 关闭（已覆盖） | A-17 已补 `xlrd>=2.0` ＋ spec `hiddenimports` |
| **B-77** / **B-78** | 关闭（已覆盖） | A-15 落地时 `sqlite_manager` 注释/docstring 已更正（实测） |

### B. 施工项（Agent 可执行）

| 项 | 处置（推荐） | 批次 |
|---|---|---|
| **B-41**（=F4） | **引擎回退对齐单源**：`mapping_match.mode` → `left_join`（不丢行）；`convert_dtype.from_type/to_type` → `TEXT`/`INTEGER`（消硬失败） | C |
| **B-64**（D2） | 在 `BUILTIN_OPS` 增 **`params_schema`**（引擎为单一源：键/类型/必填/默认值） | C |
| **B-69**（P2-1） | `default_params()` **改为派生于 `params_schema`**（界面不再另立清单） | C |
| **B-63**（D1） | 新增 **`extra_input_min`** 字段（mapping_match/merge_tables=2，余 0） | C |
| **B-65**（D3） | 新增 **`overwritable`** 字段（filter/dedup=True），表单挂载由其驱动 | C |
| **B-61**（C1） | **删除** `StepMeta.icon`（零消费者、无图标方案） | C |
| **B-62**（C2） | **删除** `target_param`/`match_param`（零消费者；启用即撞 P2-2 裁定） | C |
| **B-53**（D4） | `BUILTIN_OPS` 增 **`deprecated`** 字段 ＋ `validator` **拒绝已弃用 type** | C |
| **B-03** | `export_table` 改 **`write_only=True`**＋`WriteOnlyCell` 保 `number_format`（**降级预案**：若日期格式回归，则退回「仅更正注释」并把 B-03 转例外） | C |
| **B-76** | 随 B-03 更正 `exporter.py` L9-11 注释（裁定 G14） | C |
| **B-49** | 后缀非 `.xlsx` **抛中文 `ValueError`**，不再静默改写（本版默认口径已裁定） | B |
| **B-48** | **维持现状**（有意设计）→ 标「已裁定关闭」，不施工 | A |
| **B-79** | 预览摘要文案按 A-05 落地后的真实口径更新（仅文案） | B |
| **B-60**（B8） | `output_mode` 键与取值**集中声明常量**于 `gui/models.py`，替换 4 处生产引用 | B |
| **B-54**（B1） | 单测断言 `BUILTIN_OPS[k]["description"]` ≡ `StepMeta.display` | B |
| **B-55**（B2） | `STEP_KIND` **值域校验**（非法值报错，不再静默回退）＋单测 | B |
| **B-56**（B3） | 单测断言 `OUTPUT_OPS` ≡ `STEP_KIND` 的 fork∪merge | B |
| **B-57**（B4） | 「目录键 ↔ 表单类」**双向断言**单测（孤儿表单/缺表单皆红） | B |
| **B-58**（B6） | 自检项扩展：`keywords` **空 tuple 判失败** | B |
| **B-59**（B7） | 单测断言 `param_keys` ⊇ 目录声明的 schema 键 | B |
| **B-66**（E1） | 为**剩余 10 条**自检规则补单测镜像（自检 15 条并集全覆） | B |
| **B-67**（E3） | 四处「9」等值断言改**引用单一常量**（由 `len(STEP_CATALOG)` 派生） | B |
| **B-68**（A4） | 10+ 处非门禁「9 项」文案统一引用该常量 | B |
| **B-52** | 新增**交叉校验单测**：每个生产 `import` 模块 ⊆ 标准库 ∪ `requirements.txt` ∪ spec `hiddenimports` | D |
| **B-50** | 生成 **`requirements.lock`**（`conda run -n CPS-GPES_RPA-py311 pip freeze` 原样写入） | D |
| **B-71** / **B-72** | lock 必含 pandas（不手工删）；头部注明「含 2 个已声明废弃包，勿安装」 | D |
| **B-73** | 命令清单统一 `CPS-GPES_RPA-py311`（下划线） | D |
| **B-74** | `pandas` 加**上界** ＋ 回写实测版本 | D |
| **B-70**（P2-2） | **维持「不改 9 分支」既有裁定** → 标「已裁定关闭」 | A |
| **F5** | §7 B5 标「已解决（B-13，R12）」；§3.2 注记 4 审计注记转正；backlog W-22 关联项更新（D4＝B-53 本批已实施） | A |

### C. 例外登记（本批不施工，登记为受控例外）

| 项 | 例外理由 | 责任方 | 到期/触发 | 补偿控制 |
|---|---|---|---|---|
| **B-45** | `build.bat` 属构建域，Agent 不碰（裁定 R2/`AGENTS.md` §1） | 人工 | 下次真机构建窗口 | 现有备份逻辑未引入新失败；构建后核对 `backup/` 时间戳 |
| **B-46** | `engine/executor.py` 进度回调契约（红线①）＋须真机断言 | 人工（真机批） | 真机批立项时 | 现状为"仅日志"不误报、不中断 |
| **B-01~B-44 中其余 `[BLOCKED-真机依赖]`/`[BLOCKED-越界①]` 项**（B-05~B-11、B-17、B-20、B-22~B-23、B-26~B-27、B-29~B-30、B-32、B-34~B-36、B-40、B-37 等） | 同上（executor 运行域/真机） | 人工（真机批） | 真机批立项时 | R12 已为失败路径补 7 用例（`test_engine_failure_paths.py`）；本次 B-43 覆盖范围记录在案 |

> 例外登记**不删除任何原文**（`AGENTS.md` §7.1）；处置字段写入 `docs/function-spec-rules.md` §7 与 `_temp/ImportData/plan.md` 台账。

---

## 四、施工批次

> 每批收尾即跑 §七 门禁；批间串行（同文件串行，避免干扰）。

### 批 A · 结账与口径（零代码）
1. `docs/function-spec-rules.md`：§7 表 B5 行 → 「已解决（B-13，R12）」；注记 4 的审计注记转正；§7 关联项状态逐行更新（含 C1/C2/D1~D4/E1/E3/A4/P2-1/P2-2 本批处置）
2. `docs/backlog.md`：W-22 状态由「⏸️ 待指令」→「执行中」，说明本批裁决范围；W-20 保持
3. `_temp/ImportData/plan.md` 台账：B-51/B-75/B-77/B-78/B-48/B-70 标「结账/已裁定关闭」；全部 35 项补「本批处置」列（原文不删）
4. 任务记录新建 ＋ AGENTS 锚点登记（含容量腾挪）

### 批 B · 守卫与口径常量（低风险）
1. `gui/models.py`：新增单一常量 `STEP_COUNT = len(STEP_CATALOG)`；新增前端键常量（`OUTPUT_MODE_KEY`/`OUTPUT_MODE_NEW`/`OUTPUT_MODE_OVERWRITE`）
2. `gui/models.py`：`STEP_KIND` 值域校验（非法值 `raise`，不再静默回退）
3. `gui/app.py`：自检项扩 `keywords` 非空判定；修正「9」下限守卫引用常量
4. `gui/forms.py`：`output_mode` 引用集中常量（4 处生产引用）
5. `gui/page_input_selection.py`：预览摘要文案更新（B-79）
6. `ops/exporter.py`：后缀非 `.xlsx` 抛中文 `ValueError`（B-49）
7. 测试：四处「9」断言改引用常量；新增 `test_registry_guards.py`（B-54/55/56/57/58/59/66 六类守卫镜像 ＋ B-67/B-68 常量断言）；10+ 处文案统一

### 批 C · 记录表单源化（核心，风险最高）
> 唯一源＝`ops/step_executor.BUILTIN_OPS`；GUI 从引擎派生（保持"引擎不依赖 GUI"方向）
1. `ops/step_executor.py`：`BUILTIN_OPS` 9 条目重定义字段集：
   - 新增 `params_schema`（逐键：类型/必填/默认值）、`extra_input_min`、`overwritable`、`deprecated`
   - 删除 `target_param`/`match_param`
   - 各分支回退值改从 `params_schema` 的默认值取（**B-41**：`mode`→`left_join`，`from_type/to_type`→`TEXT/INTEGER`）
2. `gui/models.py`：`StepMeta` 删除 `icon`；`default_params()` 改为**派生于 `BUILTIN_OPS`**（**B-69**）；`_STEP_META_RAW` 增 `overwritable`/`extra_input_min` 承载
3. `gui/forms.py`：`output_mode` 挂载由 `overwritable` 驱动（**B-65**）
4. `engine/validator.py`：`deprecated=True` 的 type **拒绝执行**并给中文提示（**B-53**）
5. `ops/exporter.py`：`write_only=True` ＋ `WriteOnlyCell` 保 `number_format`（**B-03**）＋ L9-11 注释更正（**B-76**）
6. 测试：新增 `test_registry_single_source.py`（schema↔param_keys↔default_params 三方一致 ＋ 引擎回退≡schema 默认值 ＋ 弃用拒绝 ＋ 导出日期格式回归）

### 批 D · 环境与依赖（N 系列）
1. 生成 `requirements.lock`（`conda run -n CPS-GPES_RPA-py311 pip freeze`）；头部加「含 2 个已声明废弃包，勿安装」
2. `requirements.txt`：`pandas>=2.0,<3`（上界）＋ 回写实测版本；命令清单统一下划线（B-73）
3. 新增交叉校验单测（B-52）
4. `docs/`：`runtime-env-spec.md`/`build-guide.md` 命令清单口径核查

---

## 五、假设与决策（本计划不再回头讨论）

1. **解释口径**：「不要有遗留」＝**每项都有明确处置与责任方**；Agent 不可执行项（构建/真机）以**受控例外**登记，不作为"未决"。
2. **批 C 采用"单一源"方案**，而非只改两处回退值——因为只有单源才能同时闭合 F4/B-41/B-64/B-69，且防复发。
3. **B-62/B-61 采取删除**而非"启用"：启用 `target_param` 会与既有 P2-2「不改 9 分支」裁定冲突。
4. **B-03 有降级预案**：以"导出日期格式逐格等价"为硬判据；不达标则只更正注释并把 B-03 转例外。
5. **不触碰**：`engine/executor.py`（红线①）、`build/`、`build.bat`、`v2/`、`SampleCode` 冻结基线、git。
6. **红线④ 继续硬遵守**：零新依赖、无 `pickle`/`eval`/`exec`、路径全相对。

---

## 六、影响的文档与门禁

**同步文档**：`docs/function-spec-rules.md`（§3.2 注记 3 改写／§3.3 字段定义／§3.4 载体清单／§5.5 项 4、13／§7 各行／§9 变更记录）、`docs/backlog.md`（W-22）、`docs/INDEX.md`（日期同步）、`docs/runtime-env-spec.md`、`_temp/ImportData/plan.md`（台账处置列）、任务记录、`AGENTS.md`（锚点＋容量）。

**门禁（每批必跑）**：
1. `conda run -n CPS-GPES_RPA-py311 python -m unittest discover -s tests`（cwd＝`rpa_engine`）→ 全绿，用例数 ≥191＋新增
2. `smoke_m1m3.py` ＋ `smoke_mb.py`（`QT_QPA_PLATFORM=offscreen`）→ `SMOKE_ALL_OK` ×2
3. `run_self_check()` → `ok=True`（含新增守卫）
4. `python tools/doc_verify.py`（仓库根）→ `PASS`
5. `AGENTS.md` 容量（含 CR ≤8,000、余量 ≥200、纯 CRLF）

**回滚**：每批施工前取快照至 `_temp/ImportData/backup/R15-<批>/`；纯文档批删改即可回退。

---

## 七、验收标准

- [ ] 35 项 ＋ F4 ＋ F5 逐项有处置且与代码/文档实况一致（无"悬空"项）
- [ ] 四处「9」断言改引用单一常量，新增第 10 个功能不再需要手改门禁
- [ ] `params_schema` 为唯一源；`default_params` 与引擎回退同源；三方一致单测通过
- [ ] 引擎回退 `mode=left_join`、`from_type/to_type=TEXT/INTEGER`（手写 JSON 不再静默丢行/硬报错）
- [ ] `deprecated=True` 的 type 被 validator 拒绝（D4 闭合）
- [ ] `requirements.lock` 存在且含 pandas、头部有废弃包告警
- [ ] 批 A~D 门禁全绿；例外项在文档中带责任方与触发条件
- [ ] 规约变更后 `doc_verify` PASS，AGENTS 容量达标
