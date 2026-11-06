---
title: 任务记录：ImportData 导入链路修复（按 plan.md 施工）
type: task-record
scope: project
status: active
owner: 黄泊凯
last-updated: 2026-10-18
tags: [ImportData, 导入链路, 多Agent, plan.md, 锚点]
---

# 任务记录：ImportData 导入链路修复（按 plan.md 施工）

## 摘要

- **任务目标**：ImportData 导入链路修复（依据 `_temp/ImportData/plan.md` 施工）
- **任务状态**：`已完成（2026-10-19）`
- **开始时间**：2026-10-18
- **最后更新**：2026-10-18
- **要点摘要**：P-0 完成（腾容量＋登记锚点）；按 P-0→P6 分批施工，每批跑门禁
- **操作人**：黄泊凯

## 用户输入

本轮提示词要点：**按 plan.md 执行 ImportData 导入链路修复（多 Agent 协作）**。规定：顺序 `P-0→P0→…→P6`；Coordinator 读 Part 0＋Part 1 按批分发，Sub-Agent 只读本批条目＋涉及源码；通信只用 4 个标记；交接经文件系统；"改前/改后"为语义示意、禁机械匹配；硬约束＝不动引擎调度／GUI 布局／步骤函数实现／不引入新依赖。

## Agent 理解与决策

- **施工依据唯一**＝`_temp/ImportData/plan.md`；本提示词不含实现细节。
- **git 不执行**：`AGENTS.md` §1「Git 操作由人工接管，Agent 不执行」优先于提示词 §七"每批建议提交" → 改为每批输出「待人工提交清单」。
- **门禁按 plan.md 用 conda**（`conda run -n CPS-GPES_RPA-py311`，置 `QT_QPA_PLATFORM=offscreen`）——人工裁定 2026-10-18。
- **跨条目耦合（关键发现）**：`A-01` 改用 `source_path` 直读原始文件 ＋ `A-10` 令 `source.file` 落为原始路径之后，阶段 3 的兜底补导（`engine/executor.py::ensure_input_tables` L105 调 `_validate_import_path`）会因原始路径不在 `_IMPORT_ROOTS`（L42-44，仅含 `temp/input_selection`）而抛 `ParserError`，且该异常**不属** L110 的捕获面 `(ValueError, FileNotFoundError)` → 会逃逸为 `failed`。**处置**：两项同批，并在导入循环内对每个源文件父目录调 `register_import_root()`（L47-51 现成钩子，不新增机制）。
- **P-0 实测修正（`[ADJUSTED]`）**：plan.md §0.3 所列"§5.4 已知阻塞摘要整段下沉"**不成立**——实测 §5.4 已是两行纯指针，无可下沉内容；实际下沉 2 处（§2.6 去重复枚举、§8 改写为 R11 上下文），并删去 §1／§2.3／§5.4 中与链接文档重复的括注。

## 执行流程

### 流程概览

- 总步骤数：按 plan.md 批次推进（P-0、P0、P1、P2、P3、P4a、P4b、P5、P6、B 类）
- 多 Agent 协作：是（Coordinator＝主 Agent；Sub-Agent：`Agent-P0`…`Agent-P6`、`Agent-B1`）

### 步骤记录

#### Step 1: P-0 腾容量 ＋ 登记本轮锚点

- 状态：✅ 已完成
- 执行内容：`AGENTS.md` 下沉 2 处（§2.6 去重复枚举、§8 改写为 R11 上下文）＋ 删 3 处与链接文档重复的括注（§1 项目概述／§2.3 编码规范／§5.4 已知阻塞）＋「当前任务锚点」改写为 R11 ＋ 头部日期改 2026-10-18
- 涉及文件：`AGENTS.md`（修改）
- 决策记录：§5.4 无内容可下沉 → 按实际记 `[ADJUSTED]`（见「Agent 理解与决策」）
- 子 Agent：无

#### Step 2: P-0 容量复测 ＋ 规约体检

- 状态：✅ 已完成
- 执行内容：测三口径 ＋ 跑 `tools/doc_verify.py`
- 实测结果：含 CR **7,622**／上限 8,000／余量 **378**；loneCR = 0；loneLF = 0；`doc_verify` **PASS**（links=86，failures=0）
- 涉及文件：`AGENTS.md`（校验）、`_temp/verify-20261018-1454.md`（体检留痕，工具自动生成）
- 决策记录：净腾仅 **106**（7,728→7,622），未达 plan.md 的 ≥400 理想值——原因是锚点与 §8 的改写本身占用了腾出的空间（AGENTS.md §7.1 条 2 要求信息不得丢失）→ 记 `[ADJUSTED-4]`
- 子 Agent：无

#### Step 3: P-0 清 8 项 P0 级 `[UNVERIFIED]` ＋ 回写 `[ADJUSTED]`

- 状态：✅ 已完成
- 执行内容：核实 8 项 P0 级占位（`engine/executor.py` L42-44/L54-68/L47-51、`gui/models.py` L756-757/L293-303/L341/L362/L855、`gui/app.py` L10-21/L146/L186、`gui/page_progress.py` L46-47/L103-104、`gui/main_window.py` L157/L480/L250/L415/L429/L445/L249-254/L414-418/L428-433/L444-448/L584-585），写入 plan.md **§0.7.1**（核实结果表 ＋ 4 条 `[ADJUSTED]`）
- 涉及文件：`_temp/ImportData/plan.md`（修改：新增 §0.7.1、§0.3 的 P-0 行补实测结果）
- 决策记录：**`[ADJUSTED-1]` 为关键发现**——`A-01`＋`A-10`＋导入白名单存在跨条目耦合，两项若不调 `register_import_root()` 则阶段 3 兜底补导必失败；`[ADJUSTED-2]` 终止按钮实为 `page_progress.py::_abort_btn`
- 子 Agent：无

#### Step 4: P0 批（解锁导入链路 ＋ 异常隔离，7 项）

- 状态：✅ 已完成
- 执行内容：18 处改动落在 7 个文件——`A-10`（`get_entries` 带出 `source_path`；`TableEntry` 新增 `source_path` 字段 ＋ `set_tables` 透传 ＋ `to_dict` 用 `(t.source_path or t.file_path)`；`main_window` registry 补键）；`A-19`（身份改**三元组**＋弹窗文案）；`A-01`（导入改 `source_path` 优先 ＋ **`register_import_root(Path(src).parent)`**；`_close_session(clear_copies=…)` 参数化，L257 传 `False`）；`A-02`（异常元组扩容 ＋ `except Exception` 兜底 ＋ `finally` 复位按钮 ＋ 提示经翻译层）；`A-13`（失败清单带类名 ＋ `_RULES` 新增 3 条）；`A-14`（`_excepthook` 过翻译层）；`A-17`（`spec` 补 `'xlrd'`／`'ops.excel_normalizer'`；`requirements.txt` 的 `xlrd` → `xlrd>=2.0`）
- 涉及文件：改 `rpa_engine/gui/models.py`、`rpa_engine/gui/page_input_selection.py`、`rpa_engine/gui/main_window.py`、`rpa_engine/gui/error_messages.py`、`rpa_engine/gui/app.py`、`RPA_Workflow_v3.spec`、`requirements.txt`；改 `_temp/ImportData/plan.md`（新增 §0.7.1／§0.7.2）；新建 `_temp/ImportData/verify_p0_scenarios.py`、`_temp/ImportData/backup/P0/`
- 实测门禁：`py_compile` 退出码 **0**；`unittest discover` **Ran 118 tests — OK**（零回归）；双 smoke `SMOKE_ALL_OK` **0／0**；启动自检 **6/6**
- 场景验证（脚本化）：3 条新话术规则均命中且兜底正常；`source.file` 有源路径→**原始路径**、无→回落副本；`_validate_import_path` **未登记必拒（ParserError）／登记后放行**；身份三元组"同一文件不误报／同名 sheet 换文件会提醒"；0 字节 xlsx 抛 `BadZipFile`（**在新元组内**，且非 `OSError` 子类）
- 决策记录：`[ADJUSTED-5]` A-10 采用"新增字段"首选路径（未用 main_window 侧替换备选）；`[ADJUSTED-6]` A-01 采用"参数化清副本"备选路径（避免回阶段 1 预览失效）；`[ADJUSTED-7]` A-01 的 GUI 侧校验以 `register_import_root()` 实现（未新增校验函数）
- 子 Agent：无（本批由 Coordinator 直接执行——含跨条目耦合，需全局判断）
- **挂起**：`P-2`（人工 exe 重建 ＋ 真机 `.xls` 验证）；S1 的真机 GUI 会话语义确认

#### Step 5: P1 批（临时区与格式转换，3 项）

- 状态：✅ 已完成
- 执行内容：6 处改动落在 2 个文件——`A-11`（`excel_preprocessor.py` 补 `import os` ＋ `copy2`→`copyfile`＋`os.utime`；`main_window.py` 的 `cleanup_stale_files` 超龄循环加**引用保护**（读 `last_config.json` 的 `tables[].source.file`）＋ 启动序交换为「先恢复后清理」）；`A-12`（`validate_and_copy` 跨后缀查重 ＋ `ensure_xlsx` 产物加序号）；`A-18`（与 `A-12` 的 `ensure_xlsx` **同处**，无独立改动点）
- 涉及文件：改 `rpa_engine/ops/excel_preprocessor.py`、`rpa_engine/gui/main_window.py`；改 `_temp/ImportData/plan.md`（新增 §0.7.3）；新建 `_temp/ImportData/verify_p1_scenarios.py`、`_temp/ImportData/backup/P1/`
- 实测门禁：`py_compile` **0**；`unittest discover` **Ran 118 tests — OK**；双 smoke `SMOKE_ALL_OK` **0／0**；自检 **6/6**
- 场景验证：副本 mtime 归零（源 72h 旧 → 副本 0.000h）；`cleanup_stale_files` 只删无引用超龄项（removed=1）且**保留被引用副本**；`X.xls` 在 `X.xlsx` 存在时副本改名 **`X_1.xls`**；`ensure_xlsx(.xlsx)` 直通不回归
- 决策记录：**`[ADJUSTED-8]` `A-10` 已消解 `A-11` 主症状**（`source.file` 落原始路径 → 超龄清理不再影响恢复），仍做 `A-11` 三项以覆盖**迁移期旧配置**与防御性 mtime 归零；**`[ADJUSTED-9]` `A-18` 与 `A-12` 同处实现**；`cleanup_stale_files` 的**静态纯函数特性已保持**
- 子 Agent：无（同文件串行，由 Coordinator 直接执行）
- **挂起**：真实 `.xls` → `.xlsx` 的"产物不覆盖"实机验证 → 归入 `P-2`

#### Step 6: P2 批（表头规范化，2 项）

- 状态：✅ 已完成
- 执行内容：4 处改动落在 2 个文件——`A-03`（`table_importer.py` 插入**列名禁字符预检**，复用 `sql_safety._FORBIDDEN_IDENT_CHARS` 同源常量、报错含列号、**空列名跳过**）；`REQ-R2`（`excel_preprocessor.py` **新增 `read_header_row()`** 只读目标行 ＋ `table_importer.py` 插入**全空表头行预检**并补 imports）
- 涉及文件：改 `rpa_engine/ops/table_importer.py`、`rpa_engine/ops/excel_preprocessor.py`；改 `_temp/ImportData/plan.md`（新增 §0.7.4）；新建 `_temp/ImportData/verify_p2_scenarios.py`、`_temp/ImportData/backup/P2/`
- 实测门禁：`py_compile` **0**（含模块导入自检）；`unittest discover` **Ran 118 tests — OK**；双 smoke `SMOKE_ALL_OK` **0／0**；自检 **6/6**
- 场景验证（`openpyxl` 造样本）：换行/制表符表头报错含列号；中文/空格/括号表头不误伤；空列名不被预检拒绝；全空表头行被拒而真表头正常；`read_header_row` 全空行/越界/不存在 sheet 三种边界正确
- 决策记录：**`[ADJUSTED-10]`** `A-03` 的空列名归一/重复列名去重**留给 P5 的 `REQ-H1`**（本批预检跳过空列名）；**`[ADJUSTED-11]`** `A-03` 的话术规则**已在 P0/A-13 落地**（本批不重复添加，`error_messages.py` 未改）
- 子 Agent：无（两项同属导入入口，由 Coordinator 直接执行）

#### Step 7: P3 批（新建规范化模块，3 项）

- 状态：✅ 已完成
- 执行内容：**新建 `rpa_engine/ops/excel_normalizer.py`（366 行，0 个既有文件改动）**——落地 Part 4 契约（`NORMALIZE_RULES_VERSION="v1"`／`MERGED_SPLIT_LIMIT=10_000`／`NormalizeResult` 四字段／`normalize_sheet` 完整签名）；实现 `A-05`（`split_merged_cells` 合并格拆分，超限降级）、`REQ-R4`（`resolve_formula_cells` 公式兜底，**不引入 win32com**，绝不静默填 NULL）、`REQ-R5`（`expand_hyperlinks` 超链接替换，不展开外链）
- 涉及文件：新建 `rpa_engine/ops/excel_normalizer.py`；改 `_temp/ImportData/plan.md`（新增 §0.7.5）；新建 `_temp/ImportData/verify_p3_scenarios.py`、`_temp/ImportData/probe_p3.py`／`probe_p3b.py`／`probe_p3c.py`
- 执行第 0 步实测（决定性）：`ReadOnlyWorksheet` **无 `merged_cells`**（`AttributeError`）且 **`cell.hyperlink` 恒为 `None`** → R3/R5 必须全量开簿；`data_only=True` 对无缓存公式取 `None`（确认 bug 前提）
- 实测门禁：`py_compile` **0**；`unittest discover` **Ran 118 tests — OK**；双 smoke `SMOKE_ALL_OK` **0／0**；自检 **6/6**；`requirements.txt` 无 `pywin32`
- 场景验证：合并格拆分后 3 行全 `华东` 且分组统计 `{华东:600}` 无 NULL 分组、原文件仍为合并；超限降级只告警；无缓存公式保留 `'=1+2'`（非 NULL）＋告警；带缓存公式取 `3`（缓存优先）；超链接替换为 URL；普通表与既有读取逐格一致
- 自测暴露并修复：① R4/R5 行号换算 **off-by-one**（漏算表头行，修正为 `offset_rows+2+ri`）；② `iat` 不做 **dtype 上溯**导致 str 写 float 列抛错 → 新增 `_ensure_object_col()` 护栏（只转目标列）
- 决策记录：**`[ADJUSTED-12]`** R3/R5 需全量开簿（只读模式不可用），新增 `FULL_LOAD_MAX_ROWS=100_000` 内存护栏，超限跳过并**如实告警**；**`[ADJUSTED-13]`** 纯公式行会被 `pd.read_excel` 的 `skip_blank_lines` 丢弃 → R4 不覆盖，属 **H5/A-08（P4）** 范围，本批仅留痕
- 子 Agent：无（三项同文件串行，由 Coordinator 直接执行）
- **未接线**：`table_importer` 改调 `normalize_sheet` 归 `A-04`（P4）

#### Step 8: P4 批（类型/内容/特殊值 ＋ 写库原子，9 项）— **首次派子 Agent 执行**

- 状态：✅ 已完成（9/9），经 Coordinator 独立复核通过
- 运行方式：**C（多 Agent 协作）**——派 `Agent-P4` 子 Agent 执行（plan.md §1.1 L343 的分配），单个子 Agent **串行**；Coordinator 负责分发、验证、写回
- 执行内容：`A-04`（`read_excel_sheet` 加 `keep_default_na=False/na_values=[]/dtype=object` 保前导零 ＋ `infer_cell_type`／`normalize_column_types` ＋ **`table_importer` 改调 `normalize_sheet` 接线**）、`A-06`（`normalize_datetime_column` ＋ `exporter` ISO 回写 `number_format`）、`A-07`（`forms.py` 窄日期模式 ＋ 条件框提示）、`A-08`（`apply_na_policy` ＋ 字面 NA 保留）、`REQ-R7`（`clean_cell_text`）、`REQ-H3`（`is_bool_column`／`_bool_to_int`）、`REQ-H4`（`normalize_error_cells` ＋ 新增 `collect_workbook_errors`）、`A-15`（`import_dataframe_atomic` ＋ `guard_overwrite_target` ＋ 四处产表函数接线）、`A-16`（`ensure_input_tables` 判据改「存在且行数>0」）
- 涉及文件：改 `ops/{excel_preprocessor,excel_normalizer,table_importer,exporter,sqlite_manager,table_lifecycle,filter_dedup,aggregator,mapping_matcher}.py`、`engine/executor.py`、`gui/forms.py`（共 11 个）；改 `_temp/ImportData/plan.md`（新增 §0.7.6）；新建 `_temp/ImportData/verify_p4_scenarios.py`、`p4-subagent-report.md`、`backup/P4/`
- 门禁（子 Agent 自报 ＋ **Coordinator 亲自重跑**）：`py_compile` **0**；`unittest discover` **Ran 118 — OK**（重跑一致）；双 smoke `SMOKE_ALL_OK` **0／0**（重跑一致）；自检 **6/6**；`verify_p4_scenarios.py` **VERIFY_P4_ALL_OK**（38 条断言，重跑一致）
- **Coordinator 复核**：锚点真实性抽查 **13/13 命中**；越界核对通过（`AGENTS.md` mtime 14:54＝P-0 时间、`build/` 未动、docs 仅 Coordinator 本人写的记录）；`requirements.txt` 16 行、无 `pywin32`；未发现不实声明
- 决策记录：子 Agent 上报 **7 条 `[ADJUSTED]`**（含一处**施工图内部矛盾**：`A-04` 规则③的位数口径与其 §5 验收 `1234.56→REAL` 冲突 → 按整数部位数判定），逐条经 Coordinator 核对认可；`[ADJUSTED-13]` 缺口**保持不修**
- **计划缺陷与补救**：我的预置备份清单漏列 5 个实际被改文件（`exporter`／`filter_dedup`／`aggregator`／`mapping_matcher`／`forms`）→ 已用**只读** `git show HEAD:` 补齐改前快照；`backup/P4/` 现 **11 个快照**（可回滚）
- 子 Agent：`Agent-P4`（general-purpose，串行）；完整报告见 `_temp/ImportData/p4-subagent-report.md`

#### Step 9: P5 批（元数据与报告，6 REQ）— 子 Agent 执行

- 状态：✅ **5 项完成 ＋ `REQ-H9` 部分完成**（报告/元数据表落盘函数已建并直测，**自动写入接线归 P6**），经 Coordinator 独立复核通过
- 运行方式：**C（多 Agent 协作）**——派 `Agent-P5`（§1.1 分配），**串行**（`REQ-H9` 依赖前四项产出）；**备份责任下放给子 Agent**（修正 P4 缺陷）
- 执行内容：`REQ-H1`（`dedup_columns`：重复名 `_2/_3` ＋ **空列名 `未命名列_N`**，承接 P2 的 `[ADJUSTED-10]`）、`REQ-H5`（`handle_empty_cols_rows`：全空列标 `all_empty`／尾空行裁剪）、`REQ-H6`（`detect_non_cell_content` 图片/图表 ＋ `cell.comment` 批注，改在全量开簿阶段，**告知用户**）、`REQ-H7`（`detect_precision_loss`：>15 位**提示不改数据**）、`REQ-H9`（`write_normalize_report`／`write_meta_table`（`__normalize_meta`）／`write_failed_list` ＋ `main_window` 的 `failed` 改 `List[Dict]` 并**真接线落盘**）、`REQ-H10`（`paths.get_normalized_dir()` ＋ `normalized_cache_key`／缓存读写）
- 涉及文件：改 `rpa_engine/ops/excel_normalizer.py`、`ops/table_importer.py`、`rpa_engine/paths.py`、`gui/main_window.py`（共 **4** 个，全部已备份到 `backup/P5/`）；改 `_temp/ImportData/plan.md`（新增 §0.7.7）；新建 `_temp/ImportData/verify_p5_scenarios.py`、`p5-subagent-report.md`、`p5_artifacts/h9/*`
- 门禁（子 Agent 自报 ＋ **Coordinator 亲自重跑**）：`py_compile` **0**；`unittest discover` **Ran 118 — OK**（重跑一致）；双 smoke `SMOKE_ALL_OK`（重跑一致）；`verify_p5_scenarios.py` **VERIFY_P5_ALL_OK**（26 条断言，重跑一致）
- **Coordinator 复核**：锚点抽查 **10/10 命中**；**`backup/P5/` 覆盖＝4 个修改文件（与报告清单一致，P4 缺口未复现）**；H9 落盘产物磁盘可见；越界干净（`AGENTS.md` mtime 14:54、`build/` 未动、`requirements.txt` 16 行无 pywin32）
- 跨批交互实测：`temp/normalized/` **不会**被 `A-11` 超龄清理误删（`_cleanup_stale_sessions` 只扫 `temp/input_selection`）；**未改清理逻辑**
- 决策记录：子 Agent 上报 4 条 `[ADJUSTED]`（H1 落地位移、**H6 因只读模式 `_images/_charts/_comments` 缺失**而改全量阶段、H10 缓存 JSON 化、`paths.py` 的 `[UNVERIFIED]` 已核实）；`[ADJUSTED-13]` 缺口保持不修
- **遗留**：`REQ-H9` 报告/元数据表的"每次导入自动写"接线 → **P6**；H10 缓存无自动 pruning；H6 超大表跳过批注探测
- 子 Agent：`Agent-P5`（general-purpose，串行）；完整报告见 `_temp/ImportData/p5-subagent-report.md`

#### Step 10: P6 批（接入导入流程与端到端联调）— 子 Agent 执行 · **A 链收官**

- 状态：✅ `A-09` ②③ 落地 ＋ **① 依 §6 降级**；✅ 新建模块接线完成（P5 遗留闭环），经 Coordinator 独立复核通过
- 运行方式：**C**——派 `Agent-P6`（§1.1 分配），串行；**备份责任下放给子 Agent**
- 执行内容：`A-09` ②（`main_window`：`LARGE_TABLE_ROWS=200_000`／`MEM_WARN_MB=2048`、`_import_progress_label()` 大表预告、导前预扫行数＋`processEvents()`、导后 `psutil` RSS 检查）；③（显式 `setCancelButton(None)` ＋ 冻结预告）；**① 降级**（实测 `pd.read_excel` 无 `chunksize` 形参也无 `**kwds` → §6「仅提示＋阈值修正」；`excel_preprocessor.py` **未改**，A-04 的 `dtype=object` 原样保留）；**接线**（`write_normalize_report` 落 `workspace/normalize_report/<session_id>`＋`write_meta_table` 写 `__normalize_meta`；`table_importer` 增设桥接槽＋`take_last_normalize_result()`，既有签名不变；落盘后释放 DataFrame）
- 涉及文件：改 `rpa_engine/gui/main_window.py`、`rpa_engine/ops/table_importer.py`（共 **2** 个，均已备份到 `backup/P6/`）；改 `_temp/ImportData/plan.md`（新增 §0.7.8）；新建 `_temp/ImportData/verify_p6_scenarios.py`、`probe_p6_chunk.py`、`p6-subagent-report.md`
- 门禁（子 Agent 自报 ＋ **Coordinator 亲自重跑**）：`py_compile` **OK**；`unittest discover` **Ran 118 — OK**（重跑一致）；双 smoke `SMOKE_ALL_OK`（重跑一致）；自检 **ok=True**；`verify_p6_scenarios.py` **VERIFY_P6_ALL_OK**（37 条断言，重跑一致）
- **Coordinator 复核**：锚点抽查 **7/7 命中**（且 `excel_preprocessor.py` 的 `chunksize` 命中 **0**，降级未留残留）；**`backup/P6/` 覆盖＝2 个修改文件**；**线程模型未改证据＝`worker.py` mtime 09-24（全程未动）**；越界干净
- 大表样本（子 Agent 实测，**如实采信**）：5 万行×10 列（33.4s）＋ **200,001 行×2 列**（11.7s，真实触发预告文案）＋ 常规 1 万行×5 列
- 决策记录：子 Agent 上报 **5 条 `[ADJUSTED]`**（分块降级、预告阈值口径、抽纯函数、桥接槽回传、预扫复用 `sheet_info`）；**`[P4-7]`／`[P4-4]` 未做 → 列"留待人工裁定"＋各 3 选项**（按 D4 纪律，未扩范围）
- **遗留**：`A-09`① 分块未实现（技术路线需人工裁定：升级 pandas／openpyxl 流式／其它读取器）；`[P4-7]`／`[P4-4]` 待裁定；预扫失败静默跳过预告；桥接槽单线程假设；**`P-2` 始终挂起**
- 子 Agent：`Agent-P6`（general-purpose，串行）；完整报告见 `_temp/ImportData/p6-subagent-report.md`

#### Step 11: 三项遗留决策落地（D3）— Coordinator 直接执行

- 状态：✅ 三项全部落地（①②纯文档、③代码＋文档），回归全绿
- **决策①（`A-09`① 分块读取 → 走 §6 降级，维持现状）**：**纯文档**。在 plan.md 的 **`A-09` 条目内**（§6 之后）新增 `[ADJUSTED]` 标注：原因＝pandas 3.0.5 的 `pd.read_excel` 无 `chunksize` 形参也无 `**kwds`（架构上不可实现）／走法＝只做②③、不做分块／影响＝`excel_preprocessor.py` 无需修改、`CHUNK_ROW_THRESHOLD` 保留但降级路径下无消费方、A-04 的 `dtype=object` 原样保留／验收口径＝§7 三判据在降级路径下同样成立
- **决策②（`[P4-7]` JSON 全局配置 → 维持默认，留待后续专项）**：**纯文档**。§0.7.6 新增「遗留项终态」：原因＝接线需改 `import_excel_table` 签名（受 §0.2 条 2 硬约束保护）→ 架构死锁；当前默认值（5 位／preserve）**不导致数据错误**；后续专项＝先设计完整 `global_config` 透传链路
- **决策③（`[P4-4]` 导出侧日期列判定 → 二者并存）**：**代码＋文档**。落点 `rpa_engine/ops/exporter.py`：新增 `_LOOSE_DATE_RE`／`_LOOSE_DATETIME_RE`（无歧义限定）＋ `_parse_datetime_loose()`（严格 ISO 优先→宽松形态→失败一律原样）＋ `_datetime_columns(conn, table_name)`（查 `__normalize_meta`，**表不存在／异常→空集**）；`export_table` 内注入 `dt_cols` 并在写入循环按「标记列→宽松解析／未标记列→严格值形态」分支。**签名未变**、**回落必留**、**无新依赖**
- 涉及文件：改 `rpa_engine/ops/exporter.py`；改 `_temp/ImportData/plan.md`（`A-09` `[ADJUSTED]` ＋ §0.7.6 遗留项终态）；新建 `_temp/ImportData/verify_d3_scenarios.py`、`backup/D3/`
- 实测验收：`py_compile` **0**；**V4a** 有元数据时宽松形态 `2026/1/5` → **datetime ＋ `yyyy-mm-dd`**；**V4b** 严格 ISO → datetime；**V4c** 无元数据时 `2026/1/5` **仍为字符串（不回归）**；**V4d** 无元数据＋严格 ISO → 仍转日期（现状保留）；**V4e** 6 个非法形态**全部不解析**；**V2** `export_table` 签名保持 5 参数
- 回归四件套：`unittest discover` **Ran 118 — OK**；双 smoke `SMOKE_ALL_OK`；自检 **ok=True**
- 决策记录：**执行机制偏离并披露** —— 本计划原拟派 `Agent-D3`，因 Coordinator 已把 `exporter.py` 全文与 `__normalize_meta` DDL 读入上下文，派子 Agent 反而增加有损往返 → 改为 **Coordinator 直接执行③**（仍守 D1/D2/D4 全部约束）；**`git` 未执行**（见下）
- **git 冲突处置**：人工指令附"建议版本控制"，与 `AGENTS.md` §1「Git 操作由人工接管，Agent 不执行」冲突 → 按**约束层优先**：Agent **不执行 git**，仅输出「待人工提交清单」
- **范围**：未动 B 类任何内容；未引入新依赖；未改引擎调度／GUI 布局／步骤函数

#### Step 12: 三项遗留决策「查证＋落定」— Coordinator 直接执行

- 状态：✅ 查证完成（三项**内容**均已在 Step 11／D3 落地）；本次**补齐 2 处"条目本体"标注**；**零代码改动**
- **逐项查证结论**
  - **遗留项1（`A-09`① 降级）** → ✅ **已落地**：`[ADJUSTED]` 降级标注**已在条目本体**（§6 降级策略段之后）→ **仅确认，无需改**
  - **遗留项2（`[P4-7]` 维持默认）** → ⚠️ 内容已裁定，但原标注仅在 §0.7.6 → **本次补标**于 **`A-04` 的"阈值来源"段之后**（新增 `[裁定]` 块，含结论／原因／默认值合理性／后续专项建议）
  - **遗留项3（`[P4-4]` 二者并存）** → ✅ **代码已落地**（D3，`ops/exporter.py`）且已实测，但原标注仅在 §0.7.6 → **本次补标**于 **`A-06` 状态字段之后**（新增 `[已落地]` 块）＋ **`A-06` §7 末尾**（状态备注）
- 涉及文件：改 `_temp/ImportData/plan.md`（`A-04`／`A-06` 新增标注；`A-09` 无需改）；**未改任何源码文件**
- 实测验收：`py_compile` **0**；`unittest discover` **Ran 118 — OK**；双 smoke `SMOKE_ALL_OK`；自检 **ok=True**；`export_table` 签名经 `inspect` 复核 ＝ `['conn','table_name','output_path','sheet_name','cancel_check']`（**未变**）；`exporter.py` 六处锚点齐备（`_LOOSE_DATE_RE`／`_parse_datetime_loose`／`_datetime_columns`／`__normalize_meta`／`dt_cols`／`is_dt_col`）
- 越界核对：**B 类条目仍 79 个（未被触碰）**；`requirements.txt` 16 行、无 `pywin32`
- 残留标记：plan.md **1 处**（`§6.2` 自检清单的**禁止性表述本身**，非实质残留）；任务记录与 `exporter.py` **均 0**
- **git 未执行**（同 Step 11：人工建议与 `AGENTS.md` §1 冲突 → 按约束层优先，仅出「待人工提交清单」）
- **决策**：**未改写**条目的 `判定：【缺失实现】` 字段（保留原编写时语义；真实状态由新增标注块承载）

#### Step 13: B 类 Plan 重构（标注保留 ＋ 合规分类 ＋ 方案补全）— **零代码** · 多 Agent

- 状态：✅ 完成；**仅改 `_temp/ImportData/plan.md`**（Part 3 头部新增分类台账），**未改任何源码**
- **三点人工裁定**（本轮口径）：① §3.1 的"直接删除"→ **改为标注保留**（合 `AGENTS.md` §7.1 条 2「内容必须保留、不得删除」）；② 范围 **仅 Part 3**；③ **只做文档**（零代码，合指令 §7#5）
- **多 Agent**：`[TASK_SPLIT]` → 3 个**只读分类** Sub-Agent（`Agent-B3.1` B-01~B-13／`Agent-B3.2` B-14~B-44／`Agent-B3.34` B-45~B-79）；**单一写者**＝Coordinator 汇入。**首轮派发失败并已披露**：误用 `Explore` 类型（该类型只返回检索片段、不产表格）→ 改用 `general-purpose` 重派并成功
- **交付**：Part 3 头部插入 **《B 类分类台账》79 行** ＋ 图例/口径块 ＋ **《方案补全建议》27 行**
- **分类合计**：`[ACTION]` **45** ｜ `[BLOCKED-真机依赖]` **9** ｜ `[BLOCKED-越界]` **14** ｜ 兼有 **7** ｜ `[已覆盖]` **4**（另 8 项"部分重叠"）⇒ **合计 79** ✓；**施工清单约 41 项**（ACTION 45 减去已覆盖 4）；`[BLOCKED-*]` 30 项**移出施工清单但原文保留**
- **判据纪律**：分类**只引 §0.1 四条红线原文**，**未自造新红线**；3.4 标题"本次范围外"**未一刀切**（逐条核原文理由后仅 B-57 判越界）
- **子 Agent 反向纠正我两处错误前提（已采纳）**：① `ops/step_executor.py` L299 **仍**丢弃返回值（我此前"已被 A 链修"的假设**不成立** → B-18/B-44 未标已覆盖）；② `ops/exporter.py` L163 **仍为普通 `Workbook()`**（"流式化"未实施 → B-03 仅"重叠"、B-49/B-76/B-79 **实测未覆盖**）
- **实测验收**：台账 **79 行**（=108−27 补全−2 附录A）；`^### B-\d\d` 仍 **79**（**零删除**）；`^### A-\d\d` 仍 **19**（A 类未动）；§0.3 的 `P-2` 前置**仍在**；`§0.7.x` 施工记录 **8 段**齐；`unittest discover` **Ran 118 — OK**（**零代码**证据）；`requirements.txt` 16 行、无 `pywin32`
- 残留标记：plan.md **1 处**（`§6.2` 禁性表述本身）｜**git 未执行**（`AGENTS.md` §1）
- **决策**：`[CODE_PATCH]`／`[REVIEW_PASS]`／`[MERGE_DONE]` 三标记**本轮不适用**（无代码补丁）；条目**正文一字未删**，`判定：` 字段**未改写**

#### Step 14: B 类 Plan 整理定稿（7 项原子操作）— **零代码** · 3 只读 Classifier 交叉复核

- 状态：✅ 7 项操作全部落地；**仅改 `_temp/ImportData/plan.md`**，**零源码改动**
- **交叉复核（裁定①：只出差异，不重造台账）**：3 个只读 Classifier（`B-01~B-26`／`B-27~B-53`／`B-54~B-79`）
  - **段① 5 处差异** —— 根因单一：台账对「`ops/` 内**守卫/写盘实现**型改动是否计入 §0.1 ③」**自相矛盾**（B-25 判 ③，而 B-03/B-04/B-09/B-12 判 ACTION）
  - **段② 2 处差异** —— `B-49` 实含 ③（`exporter` 属 BUILTIN_OP `export`）；`B-44` 的"已覆盖＝是"**口径不符**（`[已覆盖]` 只认"由 A 链闭合"，且实测 `step_executor.py` L299 **仍**丢弃返回值）
  - **段③ 0 处差异**（26 项全一致；B-75/77/78 已覆盖经源码复核成立）
- **口径裁定（写入台账图例，消解矛盾）**：`ops/` 守卫/写盘实现变更**一律计入 ③**（＝§0.1 ③ 字面「BUILTIN_OPS **行为**」）；`[已覆盖]` 唯一口径＝「由**已完成 A 链**闭合」；`B-49` 双标 `[BLOCKED-越界＋本轮不施工]`
- **重算（决定性）**：`[ACTION]` **40** ｜ 真机 **9** ｜ 越界 **17** ｜ 兼有 **7** ｜ 已覆盖 **5** ｜ 本轮不施工 **1** ⇒ 相加 **79** ✓；**本轮可施工 ＝ 13 项**（`B-01/02/13/14/15/16/21/28/31/33/39/42/43`）
- **落地改动**：`§0.0` 速查表（Part 0 头）；合计段重算（6 项恒等式＋13 项名单）；`B-03/B-04/B-09` → `[BLOCKED-越界]`；`B-12` → `[已覆盖]`；`B-49` 双标；`B-44` 已覆盖 → 否；图例＋**口径裁定块**；**4 处组标题横幅**（3.1/3.2 提示 ＋ 3.3/3.4 不施工）
- 实测验收：**逐类实数全部命中**（40/9/17/7/5/1）；`^### B-` 仍 **79**、`^### A-` 仍 **19**（**零删除、零移动**）；`本组提示` **4**、不施工横幅 **2**；`[ADJUSTED]` 编号 **1~13 连续无跳号**；`P-2` 前置**在 L61 未动**；`[TODO]` 1 处（禁性表述本身）；`requirements.txt` **16 行**（零代码）
- **遗留发现（未改，供后续轮次）**：条目原文**行号失准** —— `B-33` 引 `L221-224` 实为 `L217-225`、`B-38` 引 executor `L191` 实为 `L196`、`B-49` 引 `L66-67` 实为 `L143-144`（属"位置失准"，非分类差异；本轮零删除/最小改动故不改）
- **git 未执行**（`AGENTS.md` §1）

#### Step 15: plan.md 定稿整理（6 项操作）— **零代码** · 1 穷举 Sub ＋ 1 执行 Sub

- 状态：✅ 6 项全部处理完毕；**仅改 `_temp/ImportData/plan.md`**，**零源码改动**
- **6 项逐项结论**：**操作 1（B-12）＝已完成**（上轮即改 `[已覆盖]`，合计已含，且不在 13 项名单）⇒ **仅核实**；**操作 4（速查表）＝已完成**（`§0.0` 13 项与台账一致）⇒ **仅核实**；**操作 2（P2/P3 噪音）＝按人工裁定① 不改**（维持上轮"原位保留、零删除"，且那些概要/代码块是上上轮要求补的）；**操作 3（真机措辞）＝本轮实质工作**；**操作 5（B-49 单点标注）＝已加**；**操作 6（报告计数）＝实测核实 ＋ 补口径说明**
- **穷举 Sub（只读）关键发现**：全文"真机/实机"字样实为 **56 处**（远超我 grep 的 12 处）；其中性质＝**Agent 任务 14**／历史记录 2／活前置 10／**已规范 30** ⇒ 仅 14 处需改
- **操作 3 落地（14 处 ＋ 校正错引）**：L131／L3483／L3538／L3548／L3613／L3620／L3635／L3685／L3695／L3780／L3848／L3888／L3898／L6526 ⇒ 统一为「**人工验证（Agent 不可执行）**」或「**人工会话验证**（**人工执行，Agent 跳过**）」；并**修正原错引**（指令称 §5.1，实为 **§5.2 场景矩阵**）—— **L131 与 L6526 两处 §5.1→§5.2**（实测校正命中 2）
- **操作 5 落地**：`#### B-49 …` 行后新增 `> **[本轮不施工]** 人工裁定（2026-10-19）… 分类＝[BLOCKED-越界＋本轮不施工]`（与台账一致）
- **操作 6 落地（裁定②以实测为准）**：`新建 4 ✓`／`§4.2 表 29 行 ✓`／`总计 33 ✓`／`[UNVERIFIED] 20 ✓`／`闭合表 101 ✓` **内部自洽**；**新增《口径说明》**—— `git` 受跟踪源码**实变更 ＝ 17 个**（另 `.spec` 被 `.gitignore:33` 忽略、`build.bat` 未改、`AGENTS.md`／`docs`／任务记录等非源码不计），与"修改 29"（**计划清单**口径）**不同源，非计数错误**
- **不动清单（实测确认未被触碰）**：L19（排除声明）／**L61（`P-2` 活前置）**／L189／L191／L192／L223／L441／L551／L554／**L566（§5.2 门禁行）**／L2963~L3103（台账区）／L5562／L5578／L5599／**L5695（职责边界）**／L5843／L5943／L6305／L6567
- 实测验收：残留 `真机会话` **仅 3 处且全在"不动"清单内**（L566／L2963／L5695）⇒ **无误伤**；`^### B-` 仍 **79**、`^### A-` 仍 **19**、`^#### B-` 仍 **35**（**零删除、零移动**）；两处新增命中各 1；`plan.md 5497→5499`（＋2 插入）；代码围栏 **154＝偶数**（Markdown 可解析）；`[TODO]` 1；`requirements.txt` 16 行（**零代码**）
- **git 未执行**（`AGENTS.md` §1）

#### Step 16: B 链代码执行 阶段 0／1（R12，2026-10-19）— **首次改源码**

- 状态：✅ **阶段 0（备份）＋ 阶段 1（`B-01`／`B-02`／`B-13`）完成并复核**；阶段 2~7 待续
- **依据**：人工上传《B 类操作执行提示词》（§一/§八 只认 **13 项**）；本文件 Part 3 条目；附件 §二 硬约束 8 条 ＋ §三 不做 6 条
- **口径（我自行消解的两处冲突）**：① 附件 §四 虽含 `B-01~B-44` 全文复本，**只执行 13 项，越界项一律不碰**；② 附件 §五 允许"阶段 4 与阶段 2 并行"，但 `B-21` 与 `B-13` 同改 `gui/models.py` ⇒ **不并行**；③ `B-01` 与 `B-13` 同改 `gui/app.py` ⇒ **同一 Sub-Agent 串行**（阶段 1 实为 2 个 Sub：`A1`／`A2`）
- **阶段 0**：12 文件改前快照 → `_temp/ImportData/backup/B1/阶段0/`；改前基线 **Ran 118 tests — OK**
- **阶段 1 交付**：改 **4 个文件**
  - `gui/app.py`（`B-01`：`import tempfile`；`_setup_gui_logging` 包 try＋回退临时目录；`launch_gui` 改「**自检先取 → 日志包 try**」；`B-13`：导入 `active_catalog_keys`＋并集比对同源）
  - `gui/main_window.py`（`B-02`：`import os`；新增 `_is_stale_session()`；会话库命名加 `pid`；`cleanup_stale_files` 删库加守卫＋docstring 更正）
  - `gui/models.py`（`B-13`：**新增** `active_catalog_keys()`，`main_buttons`/`more_buttons` 共用过滤）
  - `tests/test_step_catalog.py`（`B-13`：新增 `test_deprecated_self_check_passes`）
  - **`ops/session_db.py` 经核实按附件"本项不改"⇒ 未改**
- **`[ADJUSTED]`（附件行号失准，已按实改正）**：`B-01` 函数 L246-256／调用 L277-278 → 实为 L246 起／原 L281-282；`B-02` cleanup L679-707／命名 L259-261／调用 L236 → 实为 L800-855（删库 L817-827）／L278-280／L256
- **Coordinator 独立复核（哈希比对，不采信自报）**：与本阶段快照比 → **恰好 4 文件被改**（与自报范围逐字吻合）；`session_db.py` **未改**；**其余 8 文件（`forms`／`sql_safety`／`page_operation_config`／`graph_edges`／`table_importer`／`executor`／`parser`）全部未碰**
- **门禁（我本人重跑）**：`Ran 119 tests — OK`（**+1 用例**）｜双冒烟 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **越界核对**：`engine/executor.py` 与 `engine/parser.py` **哈希未变**；`requirements.txt` 16 行、**无新依赖**（仅标准库 `tempfile`／`os` ＋ 已在册 `psutil`）
- **`git` 未执行**（`AGENTS.md` §1）；**真机验证属 `P-2`，仍待人工**
- **阶段 2~7**：⏸️ **待续**（阶段边界停手）

#### Step 17: B 链代码执行 阶段 2（`B-14` → `B-28`）— 串行 · 已复核

- 状态：✅ **阶段 2 完成并复核**；累计 **5/13**（`B-01`／`B-02`／`B-13`／`B-14`／`B-28`）
- **为何串行**：附件 **§十 第 6 条**明定「`B-28` 的修改方案引用 `B-14` 的改动点 2」＋ 两者**共用 `gui/forms.py`** ⇒ 1 个 Sub-Agent 顺序执行
- **交付（2 文件）**
  - `gui/forms.py`：`_OPS_ORDER` **补 `"NOT IN"` 并前置**（L35-36）＋ 长度降序匹配 ⇒ **`NOT IN` 不再被切成错列名**；**新增 `parse_list_value()`**（L188-198，逗号/顿号/圆括号切分＋strip、**跳过数值化**）⇒ `IN` 收 list 而非标量（**"IN 必现失败"消除**）；`format_conditions`（L251-264）list 值改 `"、".join` 渲染、**去 Python repr** ⇒ **"打开即退化"消除**
  - `ops/sql_safety.py`：`build_where` 的 IN/NOT IN 标量输入 → **中文可操作提示**「需要多个值，请用逗号分隔」（L136-146），**不静默改写**；**签名与 `SUPPORTED_OPERATORS` 未动**
- **`[ADJUSTED]`（附件行号失准，已按实改正）**：`_OPS_ORDER` L33→实 L35-36；`parse_condition_lines` L196→实 L204-206；`_maybe_number` L214→实 L223；`build_where` IN 分支 L74→实 L137-145；`format_conditions` L226→实 L235（改前）／L251（改后）
- **`[ADJUSTED]（范围约束下的偏差）**：`B-28` 改动点 3「新增往返单测」因"仅改这两个文件"的硬约束**未落地为测试文件**，改以**行内往返断言**验证（list→文本→list 恒等、无 repr）
- **Coordinator 独立复核（哈希比对）**：本阶段**只新增改动 2 文件**；**其余 6 文件（`page_operation_config`／`graph_edges`／`table_importer`／`executor`／`parser`／`session_db`）全部未碰**；锚点 `parse_list_value`／`NOT IN`／`format_conditions`／`需要多个值` 均命中
- **门禁（我本人重跑）**：`Ran 119 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **越界核对**：`engine/executor.py` 与 `engine/parser.py` **哈希未变**；`requirements.txt` 16 行、**无新依赖**
- **`git` 未执行**；**阶段 3~7**：⏸️ 待续

#### Step 18: B 链代码执行 阶段 3（`B-15` → `B-16` → `B-31`）— 串行 · 已复核

- 状态：✅ **阶段 3 完成并复核**；累计 **8/13**（`B-01`／`B-02`／`B-13`／`B-14`／`B-28`／`B-15`／`B-16`／`B-31`）
- **为何串行**：附件 **§五** / **§十 第 7 条** —— 三项**都涉及 `gui/page_operation_config.py`，必须串行**；每项做完**即跑门禁**（逐条验收）
- **交付（1 文件）** `rpa_engine/gui/page_operation_config.py`（**+98 / −12**）
  - `B-15`：`_harvest_current_form` 改为按 **`uid` 稳定标识**回写（新增 `_form_step_uid`）；`_on_add_step` 插入后按**实际对象位置**重算 `idx_new` ⇒ **"上一被选步骤参数灌进新步骤／导出路径 100% 失效"消除**
  - `B-16`：目标表未命中时**不改写** `target_table_id`（遵裁定 G4）、置空态 ＋ **新增 `_notify_missing_target()`** 中文提示 ＋ 走**既有**刷新通道 ＋ `_push_undo` ⇒ **"静默改写＋无提示＋不刷新＋不入栈"消除**
  - `B-31`：**新增压栈后状态指纹** —— `_undo_last` 比对当前指纹，不一致则**拒绝撤销**并提示「检测到撤销后有新的改动，已取消本次撤销」；栈满改**记 warning**（不再静默丢最老快照）⇒ **"撤销静默吞掉窗口期改动"消除**
- **`[ADJUSTED]`（附件行号失准，已按实改正）**：`B-15` v7 记 L501-513／L674-698／L477-480 ⇒ 实为 **L516-529／L746-786／L479-514**；`B-16` L346-354 ⇒ 实为 **L345-366**；`B-31` `_undo_last` L567 起 ⇒ 实为 **L593 起**
- **Coordinator 独立复核（哈希比对）**：本阶段**只新增改动 1 文件**；其余 5 文件（`session_db`／`graph_edges`／`table_importer`／`executor`／`parser`）**全部未碰**；八处关键方法**全部仍在**（无整段删除）
- **行数核实**：快照 **1167** → 当前 **1247**（净 **+80**）；`git diff --stat` **+98 / −12** —— 与自报一致（**"1315 行"系我计划内数字失准，已更正**）
- **门禁（我本人重跑）**：`Ran 119 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **越界核对**：未增删控件／未重排布局／未改样式表（"刷新画布"只调既有通道）；`executor.py`／`parser.py` **哈希未变**；`requirements.txt` 16 行、**无新依赖**
- **`git` 未执行**；**阶段 4~7**：⏸️ 待续

#### Step 19: B 链代码执行 阶段 4（`B-21`）· 已复核

- 状态：✅ **阶段 4 完成并复核**；累计 **9/13**（＋`B-21`）
- **交付（2 文件）**：`gui/models.py`（+81/−14 内含）＋ `gui/graph_edges.py`
  - **根因**：覆盖模式（`overwrite_target`）的产出编号被 `specs_from_model` 排除出表节点，而 `build_edges` 用**表节点集**判悬空 ⇒ 误判 dangling；同时 `reconcile` 的 alive 账本记为 `overwritten`（存活）⇒ **两本账分叉**
  - **修法**：新增 `models.py::alive_table_ids(tables, steps)`（存活集＝输入表 ∪ 全部步骤产出编号，**与 `reconcile` 同源**）＋ `models.py::edge_state(table_id)->str`；`build_edges` 悬空判定基准改用它；`reconcile` 的 alive **复用同一函数**（口径单源化）⇒ **假悬空告警消除**
- **`[ADJUSTED]`（附件行号失准）**：`graph_edges` 悬空判定 v7 记 L203 ⇒ 实为 **L302-305（改前）／L307-311（改后）**；`models` overwritten v7 记 L568-571 ⇒ 实为 `reconcile` 覆盖分支 **L579-582（改前）**（`reconcile` 整体 L553-595）
- **回滚点卫生（我新增的措施）**：因 `models.py` 已被**阶段 1**（`B-13`）改过，**未**复用会连带回滚 `B-13` 的 `阶段0` 快照 → 本阶段**先取** `backup/B1/阶段4/{models.py(819行),graph_edges.py(265行)}`（**且已确认快照内含阶段 1 成果**）
- **Coordinator 独立复核（精确比对）**：两文件相对 `阶段4` 快照**均已改**；其余 10 文件相对 `阶段0` 的 6 个已改**均为阶段 1~3 既有成果**（本阶段未新增）⇒ 跨阶段零误伤
- **阶段 1 成果保全**:`active_catalog_keys` 命中 **4 ＝ 基线 4** ⇒ **`B-13` 成果未被回退** ✓
- **门禁（我本人重跑）**：`Ran 119 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **越界核对**：**五类边契约七字段仍在**（`config_state`／`deprecated` 命中 53）；未增删控件/未重排布局/未改样式；`executor.py`／`parser.py` **哈希未变**；`requirements.txt` 16 行、**无新依赖**
- **复现自证**：`T102`（overwrite 中间表）**`dangling=[]`**（改前为假悬空 `[(T102,S3)]`）；**真悬空场景仍正常判 dangling** ⇒ 除假阳性但**未放宽真告警**
- **`git` 未执行**；**阶段 5~7**：⏸️ 待续

#### Step 20: B 链代码执行 阶段 5（`B-33`）· 已复核 · **逐 hunk 零越界**

- 状态：✅ **阶段 5 完成并复核**；累计 **10/13**（＋`B-33`）
- **本阶段风险最高**：13 项中**唯一触及 `engine/`**。计划**写死边界**：`executor.py` 内**只许改 `ensure_input_tables`**；碰分发/信号/线程即 `[SUB_AGENT_BLOCKED]`（本次未触发）
- **交付（1 文件）**：`rpa_engine/engine/executor.py`（**仅 +8 / −0**，L115-124）；**`ops/table_importer.py` 未改一行**（经核实其消息已含「收到终止请求」⇒ 改动点 2 为 no-op）
  - **修法**：`ensure_input_tables` 补导段在原 `except (ValueError, FileNotFoundError)` 后**新增 `except RuntimeError as e:`**；以 **`cancel_check()` 二次判定**区分：真 → 抛 `ExecutionError("收到终止请求，停止补导输入表…")` ⇒ 由既有 `except ExecutionError` 归并 `status="cancelled"`；假 → **原样上抛**（真实错误仍归 `failed`，**不放宽捕获面吞错**）⇒ **"补导终止被降级为执行失败"消除**
- **`[ADJUSTED]`（附件行号失准）**：导入段附件记 L107-111 ⇒ 实为 **L112-116（改前）**；兜底 `except` 附件记 L221-224 ⇒ 实为 **L217-225（改前）**
- **🔴 越界核对（Coordinator 逐 hunk）**：唯一 hunk 头 ＝ **`@@ -115,4 +115,12 @@ def ensure_input_tables(...)`** ⇒ **改动完全在该函数内**，无 `execute_workflow`／信号／线程／重试／清理段 hunk；def 清单另证 `execute_workflow` L127／`_execute_with_retry` L275 **未触碰** ⇒ **零越界**
- **`table_importer.py` 零 diff**：与 `阶段5` 快照**逐字一致** ⇒ 子 Agent"未改"自报属实；`import_dataframe_atomic` L147 仍在
- **A 链成果保全**：上述 hunk 直接证明 **`A-16` 判据行（`table_exists(...) and table_row_count(...) > 0`）未被触碰** ✓
- **门禁（我本人重跑）**：`Ran 119 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **回滚点（卫生措施）**：两文件**均已被 A 链改过** ⇒ **先取** `backup/B1/阶段5/{table_importer.py(131行),executor.py(255行)}`（**未**用会连带撤销 A 链成果的 `阶段0` 版本）
- **`git` 未执行**；**阶段 6~7**：⏸️ 待续

#### Step 21: B 链代码执行 阶段 6（`B-39`）· 已复核 · **逐 hunk 零越界 ＋ 零误伤**

- 状态：✅ **阶段 6 完成并复核**；累计 **11/13**（＋`B-39`）
- **本阶段目标**：`engine/parser.py` 的 `schema_version` **数字 `3.1` 静默放行**（第二个触及 `engine/` 的阶段，但 §0.1 ①"不动引擎调度"**字面只限 `executor.py`** ⇒ 本项属**参数校验**，台账判 `[ACTION]`）
- **交付（1 文件）**：`rpa_engine/engine/parser.py`（162 → **169 行**，+7）
  - **修法**：删除原 `str(meta.get("schema_version") or "")` 归一，改为 **`isinstance(raw_version, str)` 严格判定**；**非字符串**（数字／`null` 等）抛**既有 `ParserError`**，中文人话「版本号必须写成字符串 "3.1"，不能写数字或其它类型…」；**字符串路径保持原样**（再过 `_SUPPORTED_SCHEMA_VERSIONS` 白名单）⇒ **数字型不再静默放行**。未新增异常类型／未改白名单／签名与返回值不变；注释同步更正
- **🔴 越界核对（逐 hunk）**：唯一 hunk 头 ＝ **`@@ -120,7 +120,14 @@ def parse_workflow(...)`** ⇒ 改动**完全在版本门禁块内**；**无**表解析／步骤解析／返回构造段 hunk（`table_id = str`／`step_id = str` 锚点各仍 1 处）
- **✅ 不误伤（Coordinator 本人实测）**：`3.1`(数字)→**REJECT**（新提示）｜`3`／`None`→**REJECT**｜**`'3.1'`→PASS**｜`'3.2'`／`''`→**REJECT**（原白名单不变）⇒ **症状消除且既有字符串配置零误伤**
- **基线依据（Phase 1 采集）**：`git grep schema_version -- '*.json'` **零命中**（仓库无 .json 配置）；**全部既有测试均用字符串 `"3.1"`**（`test_engine_overwrite` ×3／`test_engine_robustness` L34＋L141 设 `"3.2"`／L147 设 `""`／`test_models_data` L297／`test_translation` L80）
- **门禁（我本人重跑）**：`Ran 119 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **回滚点（卫生措施）**：另存 `backup/B1/阶段6/parser.py`（该文件至今未改，与 `阶段0` 内容同）
- **`git` 未执行**；**阶段 7**：⏸️ 待续

#### Step 22: B 链代码执行 阶段 7（`B-42` ∥ `B-43`）· 收官 · **13/13 全部完成**

- 状态：✅ **阶段 7 完成并复核** ⇒ **13 项全部落地**
- **交付（2 个新建测试文件，零源码改动）**
  - `rpa_engine/tests/test_ops_contracts.py`（**460 行／60 用例**）：9 项 BUILTIN_OPS 逐操作契约（含前导零按原文本传参、aggregate 指标解析、export 路径校验、`guard_overwrite_target`）＋ `step_executor` 契约（`param_keys` 白名单、缺省口径、输出表命名、返回值键集合、失败口径）＋ 三解析器一致性与往返
  - `rpa_engine/tests/test_engine_failure_paths.py`（**144 行／7 用例**）：`stop`／**retry 耗尽**／`skip`／**步骤间取消→cancelled**／**导出循环内取消→cancelled（`B-33`）**／**真实失败仍抛错且 `progress_callback` 如实上报 `failed`**／完成后中间表清理路径
- **风格合规（对齐既有约定，Coordinator 实测）**：纯 `unittest`、**禁 Qt（PyQt5 命中 0）**、直导 `ops.*`／`engine.*`、docstring 含执行命令、无 `eval/exec/pickle`、无 `sys.path` hack
- **用例数（我本人实测）**：**119 → 186**（**+67**，>119 ✓）；仅新文件 `Ran 67 — OK`
- **零源码改动（git 取证）**：`rpa_engine/tests/` 面**仅 1 个既有 `M`（`test_step_catalog.py`＝阶段 1 成果）＋ 2 个 `??`（新文件）** ⇒ **无既有测试被改**；本阶段**无任何新增 `M`**
- **门禁（我本人重跑）**：`Ran 186 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **子 Agent 如实标注（属预期的未落地项）**：`B-20`（skip 分支 `status` 仍 `completed`）与 `B-36`（`output_tables` 清理后仍留派生表映射）**均为台账 `[BLOCKED-越界]` 项、本轮不施工** ⇒ 测试**按现状断言**并注释待修面（**未**制造红测）
- **回滚**：新建型 ⇒ 删除两文件即可

### 🏁 B 链 13 项收官声明（R12，2026-10-19）

- ✅ **13 项全部落地**：`B-01`／`B-02`／`B-13`｜`B-14`／`B-28`｜`B-15`／`B-16`／`B-31`｜`B-21`｜`B-33`｜`B-39`｜`B-42`／`B-43`
- **改动面**：**10 个文件被改**（阶段 1~6）＋ **2 个测试新建**（阶段 7）＋ `ops/excel_normalizer.py`（A 链 P3 新建）；**未改既有测试**
- **门禁**：`Ran 186 — OK`（基线 118 → **+68**）｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS`｜AGENTS 容量达标
- **越界**：**零**（`engine/` 两处改动经**逐 hunk** 证实仅在 `ensure_input_tables`／版本门禁块）
- **回滚点**：`_temp/ImportData/backup/B1/阶段0`~`阶段6` 分阶段快照齐备
- **`git` 未执行**（人工接管）；**仍待人工**：**`P-2`（exe 重建 ＋ 真实 `.xls` 真机验证）**

### 🏁 A 链收官声明（R11，2026-10-18）

- ✅ **A 类 19 项全部闭环**：`A-01`~`A-19`（P0 7 ＋ P1 3 ＋ P2 1 ＋ P3 1 ＋ P4 6 ＋ P6 1）
- **REQ 侧全部落地**：`R2`／`R3`／`R4`／`R5`／`R6`（由 A-04 承载）／`R7` ＋ `H1`／`H3`／`H4`／`H5`／`H6`／`H7`／`H9`（**接线由 P6 补齐**）／`H10`
- **未闭环项（如实，已于 Step 11 处理 3 项）**：`A-09`① —— **已裁定维持 §6 降级**（技术路线留待人工另立专项）；`[P4-7]` —— **已裁定维持默认、留待后续专项**；`[P4-4]` —— **已落地（二者并存）**；**仍待完成**：**B 类 `B-01`~`B-44` 未施工**；人工 **`P-2`（exe 重建 ＋ 真机 `.xls` 验证）**
- **规约侧**：`AGENTS.md` 锚点 **R11 状态仍为"进行中"**（因 B 类未完成），本轮仅记录进度，**未改锚点状态**

#### Step 23: R13 · B-28 改动点 3 往返单测补录（2026-10-19）

- 状态：✅ **完成**（用户授权补录；R13 轮）
- **背景**：R12 阶段 2 因「仅改两文件」硬约束，`B-28` 改动点 3（往返单测）未落地为测试文件（记 `[ADJUSTED]`，行内断言替代）；`test_ops_contracts.py` 既有 `test_condition_list_round_trip` 仅覆盖与 B-30 共用的基础 IN 用例，未覆盖 B-28 §5 验收口径
- **交付（1 测试文件，零源码改动）**：`rpa_engine/tests/test_ops_contracts.py` 新增 5 用例（**186 → 191**）：
  ① 前导零 list 往返（`["0123","0456"]` 不数值化）；② `NOT IN` 往返；③ list＋标量＋日期＋`IS NULL` 混合条件往返恒等且顺序保持；④ 渲染文本无 Python repr 显式断言（期望 `电表号 IN 0123、0456`）；⑤ 圆括号输入形态解析后二次往返幂等
- **B-28 §7 验收标准全勾**：list 条件往返后仍为 list ✓；与 `B-14` 共用同一解析实现 ✓（`parse_condition_lines` 的 IN/NOT IN 分支走 `parse_list_value`）；往返单测通过 ✓
- **门禁（Coordinator 实测）**：`Ran 191 tests — OK`｜双 `SMOKE_ALL_OK`｜自检 `ok=True`｜`doc_verify PASS (links=86, failures=0)`
- **过程处置**：AGENTS.md 锚点编辑曾引入 200 处 loneLF 行尾，`doc_verify` 门禁如实拦截，行尾归一为 CRLF 后复跑通过（门禁有效性的一次实证）
- **同日人工事项确认（用户口头告知）**：**P-2 已人工验收通过**（exe 重建 02:58＋真机 `.xls` 导入链路验证）；**git 已人工提交**
- **遗留（移交人工）**：`B-45`~`B-79`（35 项）需人工立项（含 `B-20`／`B-36` 越界裁定），台账仍在 `_temp/ImportData/plan.md` Part 3，**未登记入 `docs/backlog.md`**

## 涉及文件汇总

| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 修改 | `AGENTS.md` | R11 锚点登记 ＋ 容量下沉 2 处＋删 3 处重复括注（P-0）；**R13**：锚点更新至收官 ＋ 行尾归一 CRLF |
| 修改 | `rpa_engine/tests/test_ops_contracts.py` | **R13/B-28 改动点 3 补录**：新增 5 往返用例（前导零／NOT IN／混合顺序／无 repr／圆括号幂等），**186 → 191** |
| 修改 | `requirements.txt` | `xlrd` → `xlrd>=2.0` ＋ 来源注释（P0/A-17） |
| 修改 | `RPA_Workflow_v3.spec` | `hiddenimports` ＋`'xlrd'`／`'ops.excel_normalizer'`（P0/A-17）；**注意：该文件被 `.gitignore` 的 `*.spec` 规则忽略，不进常规提交** |
| 修改 | `rpa_engine/gui/models.py` | `TableEntry.source_path` 字段 ＋ `set_tables` 透传 ＋ `to_dict` 取值（P0/A-10） |
| 修改 | `rpa_engine/gui/page_input_selection.py` | `get_entries` 带出 `source_path`（P0/A-10）；`_on_add_files` 异常隔离＋按钮复位（P0/A-02） |
| 修改 | `rpa_engine/gui/main_window.py` | P0：A-10 registry／A-19 身份三元组／A-01 导入路径＋白名单＋`clear_copies`／A-13 失败清单；P1：`cleanup_stale_files` 引用保护＋启动序交换；P5：`failed` → `List[Dict]` ＋ 失败清单落盘；**P6**：`A-09` ②③（大表预告文案／`psutil` RSS／`setCancelButton(None)`）＋ **REQ-H9 报告/元数据表接线** |
| 修改 | `rpa_engine/gui/error_messages.py` | `_RULES` 新增 3 条（P0/A-13） |
| 修改 | `rpa_engine/gui/app.py` | `_excepthook` 过翻译层（P0/A-14） |
| 修改 | `_temp/ImportData/plan.md` | 新增 **§0.7.1~§0.7.7**（各批施工留痕与实测证据） |
| 新建 | `rpa_engine/ops/excel_normalizer.py` | P3 新建（Part 4 契约 ＋ R3/R4/R5）；P4 补齐管线（`infer_cell_type`／`normalize_datetime_column`／`apply_na_policy`／`clean_cell_text`／`is_bool_column`／`normalize_error_cells`／`collect_workbook_errors`）；**P5**：`dedup_columns`（含空列名归一）／`handle_empty_cols_rows`／`detect_non_cell_content`／`detect_precision_loss`／`write_normalize_report`／`write_meta_table`／`write_failed_list`／缓存读写 |
| 修改 | `rpa_engine/ops/excel_preprocessor.py` | P1＋P2；**P4**：`read_excel_sheet` 的 `pd.read_excel` 追加 `keep_default_na=False, na_values=[], dtype=object`（A-04 前导零） |
| 修改 | `rpa_engine/ops/table_importer.py` | P2 两处预检；P4：改调 `normalize_sheet`（接线）＋ `import_dataframe_atomic`；P5：重复表头段改为防御性残留日志；**P6**：增设桥接槽 ＋ `take_last_normalize_result()`（既有签名不变） |
| 修改 | `rpa_engine/ops/sqlite_manager.py` | **P4/A-15**：新增 `import_dataframe_atomic`（写库原子性） |
| 修改 | `rpa_engine/ops/table_lifecycle.py` | **P4/A-15**：新增 `guard_overwrite_target` ＋ `merge_tables` 接线 |
| 修改 | `rpa_engine/ops/filter_dedup.py`／`aggregator.py`／`mapping_matcher.py` | **P4/A-15**：产表处接线活表覆盖守卫 |
| 修改 | `rpa_engine/ops/exporter.py` | **P4/A-06**：`_iso_to_datetime` ＋ 逐格 `ws.cell` 设 `number_format`（日期回写）；**D3［P4-4］**：新增 `_datetime_columns()`／`_parse_datetime_loose()` ＋ 写入循环「元数据优先／值形态兜底」分支（签名未变、无元数据时逐格等价） |
| 修改 | `rpa_engine/engine/executor.py` | **P4/A-16**：`ensure_input_tables` 判据改「表存在且行数>0」＋ 文案 |
| 修改 | `rpa_engine/gui/forms.py` | **P4/A-07**：`_DATE_VALUE_RE` 窄日期模式 ＋ 条件框格式提示 |
| 修改 | `rpa_engine/paths.py` | **P5/REQ-H10**：新增 `get_normalized_dir()`（`temp/normalized` ＋ mkdir）；**既有 API 未动** |
| 新建 | `docs/task-records/2026-10-18-importdata-repair.md` | 本轮任务记录（本文件） |
| 新建 | `_temp/ImportData/backup/P0`／`P1`／`P2`／`P4`／`P5`／`P6`／`D3` | 各批改前快照（回滚用）；P4 含 11 个（6 预置 ＋ 5 用只读 `git show HEAD:` 补齐）；P5 含 4 个、P6 含 2 个、**D3 含 1 个** |
| 新建 | `_temp/ImportData/verify_p0_scenarios.py`～`verify_p6_scenarios.py` ＋ `verify_d3_scenarios.py` | 各批脚本化验收产物（P4 38 条／P5 26 条／P6 37 条断言；**D3 含 V4a~V4e**） |
| 新建 | `_temp/ImportData/probe_p3.py`／`probe_p3b.py`／`probe_p3c.py`／`probe_p6_chunk.py` | P3 第 0 步能力实测与归因探针、**P6 的分块可行性探针**（证明 `chunksize` 不可用） |
| 新建 | `_temp/ImportData/p4-subagent-report.md`／`p5-subagent-report.md`／`p6-subagent-report.md` | 各子 Agent 完整报告（含 `[ADJUSTED]`、遗留与判断项选项） |
| 新建 | `_temp/ImportData/p5_artifacts/h9/*` | P5 落盘产物样例（`T1_normalize.json/.txt`、`failed_list.json/.txt`） |

## 关闭标识

- **完成时间**：2026-10-19
- **最终状态**：✅ **已完成**——A 链 19 项（R11）＋ B 链 13 项（R12）全部落地收官；B-28 改动点 3 往返单测补录（R13，191 tests OK）；**P-2（exe 重建＋真机 `.xls` 验证）已人工验收通过**；**git 已人工提交**
- **关闭说明**：`plan.md` 可施工项全部闭环；三项遗留决策（`A-09`① 维持降级／`[P4-7]` 维持默认／`[P4-4]` 二者并存）已裁定落地；**唯一移交事项**＝`B-45`~`B-79`（35 项）人工立项（含 `B-20`／`B-36` 越界裁定），台账在 `_temp/ImportData/plan.md` Part 3，未登记入 `docs/backlog.md`
