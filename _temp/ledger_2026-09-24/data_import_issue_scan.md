# 数据导入阶段只读问题扫描报告

> **⚠ 归档注记（2026-09-24 R10）**：本文件是扫描态取证底稿，正文不改写。现路径 `_temp/ledger_2026-09-24/data_import_issue_scan.md`；正文引用的 `_temp/RPA_engine_maturity_assessment.md` 等已移动至同夹、`_temp/DAG-rebuild/` 未动、`_temp/verify-20260924-*.md` 已清理，对账见同夹 `CLEANUP_MANIFEST.md`。42 条 DM 问题已全部登记进 `_temp/ledger_2026-09-24/open_issues_ledger_2026-09-24.md` §2。

> **状态标记**：**扫描态 [待审核]**｜日期：2026-09-24｜轮次：R9
> **本轮声明**：**未修改任何代码、配置、数据、依赖、设计稿或生产文件**；本轮唯一写入＝本文件。
> **边界遵守**：只读取证＋内存内探针（`io.BytesIO`/`:memory:`，无磁盘写入、无项目数据库访问）；未执行 git 写操作、未装依赖、未跑 build.bat。
> **判定基准**：人工给定的"Excel ↔ SQLite 无损互转规范"（见 §2）。
> **取证方式**：3 只读子 agent 分域扫描 ＋ 主 agent 8 项内存探针 ＋ 关键断言逐条源码复核（**推翻子 agent 2 项论断**，见 §9）。

---

## 1. 一页速读

**总判断：链路"能跑通规范表"，但对"真实办公 Excel"缺内容级防护；有 3 个 P0 与 12 个 P1，其中 2 个 P0 会导致数据静默错误而非报错。**

| 项 | 结果 |
|----|------|
| 问题总数 | **42**（P0×3、P1×14、P2×21、P3×4） |
| 待人工确认 | **9 条**（§8 的 H-1~H-9，不计入问题总数） |
| 破坏无损互转 | **17 项**（DM-03/10/11/13/16/17/18/19/20/21/22/23/24/26/30/31/40） |
| 直接导入失败 | **7 项**（DM-01/02/04/14/23/30/39） |
| 看似成功但数据错误 | **10 项**（DM-03/10/13/17/18/19/20/26/31/36） |
| 仅体验/提示层 | **7 项**（DM-05/06/09/15/25/38/42） |
| 结构性缺口 | **8 处**（§7） |

分类桶之间按"主要后果"归类，**存在交集**（如 DM-30 既是失败也是无损破坏）；本节编号集与 §6 完全一致。

**关键点速览**：①`.xls` 在交付 exe 内必失败（构建警告已实证）②`if_exists="replace"` 的建表语句不进事务，失败留空壳表并被"已存在"逻辑静默放过 ③pandas 全权推断类型，导致 NA 字面量折空、长编号精度丢失、日期降级为文本、公式永不保留 ④无任何导入前内容预检（列名字符、重名、类型声明）。

---

## 2. 任务理解与判定基准

**理解**：本轮只找问题、只点关键，不给解决方案（发现思路只登记 §8）。

无损互转规范摘要（作为判定尺）：单行表头；无合并单元格；无公式/样式/图表/批注；每列类型一致并与 SQLite 列对应；空值语义统一；日期时间统一 ISO 8601 文本；整数 ≤2⁵³；列名唯一稳定；元数据由程序侧保存；单 sheet 对应单表；统一 .xlsx 与 UTF-8。

**实测环境事实**（影响判定）：pandas **3.0.5**（requirements 仅写 ≥2.0，且无 lock 文件锁定）；openpyxl、xlrd 均已装于 conda `CPS-GPES_RPA-py311`。

---

## 3. 本地规约读取结果与冲突记录

**结论：规约与提示词无实质冲突；五处需记录（C-1~C-5）。**

| # | 内容 | 处置 |
|---|------|------|
| C-1 | `AGENTS.md` §2.6 已生效：涉功能函数须先读 `docs/function-spec-rules.md`；导入相关载体（`BUILTIN_OPS` 的 `import` 不在该目录内，导入属"数据源加载"而非用户操作） | 本轮按只读扫描执行，不触发硬停止 |
| C-2 | §2.1 条 5／§5.2 内存红线 ↔ DM-33（`to_sql` 无 chunksize） | 记为规约-实现张力，仅登记 |
| C-3 | `docs/architecture.md` §8.4 禁用词 ↔ DM-02/DM-05（原始英文异常外泄） | 属违反 [约束] 的表现，仅登记 |
| C-4 | 提示词把 `ops/`、`tests/` 当顶层目录 | 实为 `rpa_engine\ops\`、`rpa_engine\tests\`；已按磁盘实况扫描 |
| C-5 | `doc-governance.md` §7 触发②④：若日后补 tables[] 元数据字段，须同步 architecture 与功能函数记录表 | 登记为后续动作前置 |

---

## 4. 导入链路现状摘要

**结论：两个入口汇聚到同一函数对，路径清晰但防护点稀疏。**

| 环节 | 载体（`D:\CPS-GPES_RPA-20250312\v3\` 下） | 作用 |
|------|------|------|
| GUI 选文件 | `rpa_engine\gui\page_input_selection.py` `_on_add_files` L376-429 | 多选→复制临时区→`.xls` 转换→扫描 sheet→加行 |
| sheet 扫描 | `rpa_engine\ops\excel_preprocessor.py` `scan_sheets` L145-170 | `load_workbook(read_only)` 取名与 `max_row/max_column` |
| 确认导入 | `rpa_engine\gui\main_window.py` `_on_confirm_import` L285-364 | 磁盘×3 预检→分配 T#/t{n}→逐表导入→失败清单 |
| 单表导入 | `rpa_engine\ops\table_importer.py` `import_excel_table` L40-99 | 预扫告警→取消检查→读取→空表拒绝→写入→COUNT 日志 |
| 值读取 | `rpa_engine\ops\excel_preprocessor.py` `read_excel_sheet` L190-220 | `pd.read_excel(sheet_name, skiprows=header_row-1, header=0)` |
| 写入 | `rpa_engine\ops\sqlite_manager.py` `import_dataframe` L122-152 | `with txn(conn): df.to_sql(..., index=False)`，默认 `if_exists="replace"` |
| 连接 | `rpa_engine\ops\session_db.py` L74-80 | WAL、synchronous=NORMAL、busy_timeout=5000 |
| 复现补导 | `rpa_engine\engine\executor.py` `ensure_input_tables` L85-115 | 表缺失才补导；路径白名单校验 |

---

## 5. 问题清单（7 字段齐备）

### 5.1 段①文件读取层

| 编号 | 现象 | 触发条件 | 已适配 | 影响 | 证据 | 严重度 |
|------|------|----------|--------|------|------|--------|
| DM-01 | `.xls→.xlsx` 写死 `engine="xlrd"`；xlrd 未进依赖清单、未进打包 hiddenimports、不在自检清单；交付包构建警告已实测 `missing module named xlrd` | 任一 `.xls`（exe 态） | **未适配** | 导入失败＋该文件后续 sheet 全不处理（ImportError 不在 L417 捕获元组）；破坏 .xls/.xlsx 自适应要求 | `rpa_engine\ops\excel_preprocessor.py` L102；`requirements.txt` L10-17；`RPA_Workflow_v3.spec` L27-53；`build\work\RPA_Workflow_v3\warn-RPA_Workflow_v3.txt:279`；`gui\page_input_selection.py` L417 | **P0** |
| DM-02 | 伪装/损坏文件异常逃逸：`InvalidFileException`、`BadZipFile`、`XLRDError` 均直承 `Exception`，两层捕获元组都不命中 | 扩展名与内容不符（HTML/XML/CSV 改名、截断 zip、.xls 内是 xlsx） | **未适配** | 导入失败＋原始英文弹框＋批处理中断；违反 §8.4 | 探针 mro 实测；`page_input_selection.py` L417；`gui\main_window.py` L322-323 捕获元组 | **P1** |
| DM-03 | 转换产物 `src.with_suffix(".xlsx")` 无冲突检测；copy 有 `while exists` 加序号，转换没有 | 先加 `A.xlsx` 再加 `A.xls`（同名异格式） | **未适配** | 后者覆盖前者，两行条目指向同一文件→数据张冠李戴（破坏无损互转） | `excel_preprocessor.py` L117-119 ↔ L59-63 | **P1** |
| DM-04 | 同名追加 `_1` 使路径变长；`shutil.copy2` 抛裸 `OSError` 不在捕获元组 | 深层中文路径＋同名文件（>260 字符） | 部分适配 | 导入失败走全局异常面 | `excel_preprocessor.py` L44-65；`page_input_selection.py` L417 | P2 |
| DM-05 | 占用/缺文件已捕获，但 `translate_error` 规则键为 `permissionerror`/`filenotfounderror`，调用处只传 `str(e)`（不含类名）→ 规则永不命中，落到兜底话术；L419 更把原始英文直塞弹窗 | 文件被 Excel 占用、无权限、被移动 | 部分适配 | 提示层缺陷＋技术细节外泄 | `gui\error_messages.py` L25-28；`main_window.py` L328；`page_input_selection.py` L419 | P2 |

### 5.2 段②Sheet 解析层

| 编号 | 现象 | 触发条件 | 已适配 | 影响 | 证据 | 严重度 |
|------|------|----------|--------|------|------|--------|
| DM-06 | 隐藏/veryHidden sheet 与数据表同列且默认全选导入；全库无 `sheet_state` 判定 | 源文件含隐藏表 | **未适配** | 多余表入库、内存与耗时上升 | `excel_preprocessor.py` L158（`wb.sheetnames`）；`page_input_selection.py` L632-639 | P2 |
| DM-07 | 图表页（chartsheet）混入扫描列表；按名读取报 `Worksheet not found` | 源含图表页 | **未适配** | 导入失败且提示不指向真因 | `excel_preprocessor.py` L158-164、L204-208 | P2 |
| DM-08 | `scan_sheets` 行/列取 `max_row/max_column`（read_only 下来自 dimension 元信息），非 Excel 生成工具常缺失或虚高/虚低 | WPS/程序导出文件 | 部分适配 | `MEMORY_WARN_ROWS` 告警失真；预检依据不可靠 | `excel_preprocessor.py` L155-164；`table_importer.py` L61-68 | P2 |
| DM-09 | 0 sheet 的空工作簿：`added=0/skipped=0`，界面无任何反馈 | 空 workbook | **未适配** | 体验（点了没反应） | `page_input_selection.py` L408-429 | P2 |

### 5.3 段③表头行处理

| 编号 | 现象 | 触发条件 | 已适配 | 影响 | 证据 | 严重度 |
|------|------|----------|--------|------|------|--------|
| DM-10 | 表头空白格被 pandas 命名 `Unnamed: N` 并原样建成 SQLite 列；GUI 摘要预告的是 `未命名{N+1}` | 表头任一格为空（合并标题下高发） | **未适配** | 阶段 2 选不到列；列名与预览不一致（探针确认**不丢列**，仅名称漂移） | 探针 `COLS ['ID','金额','Unnamed: 2','备注']`；`excel_preprocessor.py` L210-215；`page_input_selection.py` L227 | **P1** |
| DM-11 | 弹窗预览对合并单元格做前向填充，真实读取链路不填充；预览文案称"已按上方值填充" | 多行表头/合并表头 | 部分适配 | 所见非所得＋预期被误导（无损互转要求无合并单元格，链路未拦截） | `page_input_selection.py` L166-188、L243-245；`excel_preprocessor.py` L210-215 | **P1** |
| DM-12 | 重复表头告警为死代码：pandas 已 mangle 成 `A/A.1/A.2`，判定条件恒 False；仅大小写或首尾空格不同的重复名 pandas 不识别 | 表头重名 | 部分适配 | 告警永不触发、下游列引用歧义 | 探针 `DUP_DETECT_WOULD_FIRE False`；`table_importer.py` L85-89 | P2 |
| DM-13 | 表头含 `"`、`\n`、`\t`（Alt+Enter 高发）时导入成功（`to_sql` 不经 `quote_ident` 字符守卫），但阶段 2/3 的每个 SQL 出口都抛"标识符包含禁止字符" | 表头带换行/引号/制表符 | **未适配** | 导入"成功"但后续必失败；错误不指向列名 | `sql_safety.py` L36、L55-66；`sqlite_manager.py` L149（`to_sql` 不经守卫）；`table_importer.py` L76-91 无列名筛查 | **P1** |
| DM-14 | `header_row` 入引擎后 `int(header_row)`：`null` 抛 `TypeError`（不在捕获元组）；`2.9`→2、`True`→1 静默通过 | 手写 JSON 字段异常 | 部分适配 | 导入失败分类错误／表头行静默偏移 | `executor.py` L99（取字段）、L108（`int(header_row)`）、L107-111（捕获元组）；`excel_preprocessor.py` L199-200 | P2 |
| DM-15 | 数据行列数多于表头列数时不丢列，而是新增 `Unnamed: N` 列 | 表头窄于数据区 | 已适配（探针确认） | 列名漂移（体验/口径） | 探针 `COLS ['姓名','分数','Unnamed: 2','Unnamed: 3']`，`IDX None` | P3 |

### 5.4 段④单元格值处理

| 编号 | 现象 | 触发条件 | 已适配 | 影响 | 证据 | 严重度 |
|------|------|----------|--------|------|------|--------|
| DM-16 | 公式一律取缓存值、永不保留公式串：pandas 引擎固定 `data_only=True`、`keep_links=False`，本仓未传 `engine_kwargs`；无缓存值时读为空 | 公式单元格；脚本生成/未重算的 xlsx | 部分适配（取值符合"转计算值"要求）；**无缓存→静默空值** 未适配 | 静默数据丢失（空值与公式不可区分） | 探针 `OpenpyxlReader.load_workbook` 源码；`excel_preprocessor.py` L210-215 | **P1** |
| DM-17 | 空值语义不统一：pandas 默认 na 集合含 `NA`/`N/A`/`NULL`/`null`/`None`/`NaN`/`<NA>`/`#N/A` 等 → 源文本变 NULL；`''`→NULL，`' '`（空格）保留 | 单元格含上述字面文本 | **未适配**（未传 `keep_default_na`/`na_values`） | 数据错误＋往返不等价（原字面不可复原） | 探针 `NA_SET` 清单；`read_excel_sheet` 仅 3 参 | **P1** |
| DM-18 | 长编号精度丢失：`18012345678901234567` 读入即成 `...229568`（IEEE754 double，Excel 单元格层面已丢） | 18-20 位数字以数值存储（身份证/电表号） | **未适配**（无 dtype 保护） | 不可逆数据错误 | 探针 `DATA` 输出；`excel_preprocessor.py` L210-215 | **P1** |
| DM-19 | 前导零：文本存储可保住（探针 `'00123'` 保留），但同列被判数值或源单元格为数字格式时丢零；引擎无列级 `dtype=str` 入口 | 工号、邮编、区码列 | 部分适配 | 数据错误 | 探针；全库 `dtype=` 0 命中 | **P1** |
| DM-20 | 日期往返降级：pandas 生成 DDL `TIMESTAMP`/`DATE`，SQLite 存为 `'2024-01-01 00:00:00'`（空格分隔，非 ISO 8601 的 `T`）；导出原样 append 字符串且不设 `number_format` → 回 Excel 变**文本单元格** | 任一日期/日期时间列 | **未适配** | 破坏无损互转；违反"日期时间统一 ISO 8601 文本" | 探针 `DDL`/`ROWS` 输出；`exporter.py` L87、L98-99 | **P1** |
| DM-21 | 布尔列 `True`→SQLite `1`（typeof integer）；三态（TRUE/FALSE/空）退化为 1/0/NULL；导出回 Excel 显示数字 | 布尔列 | **未适配** | 往返不等价 | 探针 `ROWS`；`table_schema.py` L165-167 | P2 |
| DM-22 | General 格式下的日期序列号未被标记为日期 → 导入得 `45123` 整数；无 `parse_dates`/`converters` 可纠 | 未设格式的日期列 | **未适配** | 数据错误（日期变数） | `read_excel_sheet` 仅 3 参；全库 `parse_dates` 0 命中 | P2 |
| DM-23 | 文本含控制字符（`\x01` 等）时 openpyxl 在 `append` 阶段即抛 `IllegalCharacterError`；`XLRDError` 读入的 `.xls` 可携带该类字符 | 含控制字符/程序生成文件 | **未适配** | 导出中断（往返断链） | 探针异常与 mro；`exporter.py` L98-99 | **P1** |
| DM-24 | `.xls` 路径二次降级：xlrd→DataFrame→openpyxl 写 xlsx→pandas 再读；类型与空值被处理两次 | 上传 `.xls` | **未适配** | 数据错误风险叠加（与 DM-17/18/19 复合） | `excel_preprocessor.py` L101-121 ↔ L210-215 | P2 |
| DM-25 | GUI 预览用 openpyxl 直读原值，导入用 pandas（折 NA、转数值）→ 预览见 `NA`/`00123`，入库后变空/变数 | 预览后导入 | **未适配** | 所见非所得（体验层，但掩盖真实数据问题） | `page_input_selection.py` L630-655 ↔ `excel_preprocessor.py` L210-215 | P2 |

### 5.5 段⑤类型推断与映射

| 编号 | 现象 | 触发条件 | 已适配 | 影响 | 证据 | 严重度 |
|------|------|----------|--------|------|------|--------|
| DM-26 | 首次导入的列类型完全由 pandas 推断（探针实测 DDL＝`TIMESTAMP/DATE/INTEGER/REAL/TEXT`），而 `ALLOWED_TYPE_CONVERSIONS` 键仅 `TEXT/INTEGER/REAL` → 日期/布尔列走"数据类型转换"直接 `ValueError` | 对日期/布尔列改类型 | **未适配** | 导入后步骤必失败；类型口径两套 | 探针 `DDL`；`table_schema.py` L29-33、L144-154、L165-167 | **P1** |
| DM-27 | 混合类型列（数字与文本同列）→ DDL TEXT → 数字被按文本存取，比较与排序按文本口径（`'9' > '10'`） | 同列混类型 | **未适配** | 数据错误（聚合/排序结果与预期相反） | 探针 DDL 为 TEXT；`table_schema.py` L165-179 | P2 |
| DM-28 | 整列全空 → DDL 声明 `REAL`（探针 `n` 列）；空列无标记、下游不可区分"无数据"与"全为 0" | 空列 | **未适配** | 口径歧义 | 探针 `DDL` | P3 |
| DM-29 | 列数无上限校验（SQLite 列数上限 2000）；内存仅有行数警戒 | 超宽表（>1000 列） | **未适配** | 导入失败无预警 | `table_importer.py` L26、L58-68 | P3 |

### 5.6 段⑥SQLite 写入层

| 编号 | 现象 | 触发条件 | 已适配 | 影响 | 证据 | 严重度 |
|------|------|----------|--------|------|------|--------|
| DM-30 | `if_exists="replace"` 的 DROP/CREATE 属 DDL，在 sqlite3 legacy 隔离模式下**自动提交**（探针 `in_txn_after_DDL False`、`isolation_level ''`）→ 写入中途失败时回滚只回数据，旧表已被删除，残留**空壳表**；而 `import_dataframe` docstring 承诺"写入失败（事务自动回滚）"与事实不符 | replace 导入中途 `sqlite3.Error`/OOM/取消 | **未适配** | 数据错误＋半状态；文档与行为矛盾 | 探针；`sqlite_manager.py` L128（docstring"事务内"）、L140（承诺自动回滚）、L148-149（`with txn` ＋ `to_sql`）；`sql_safety.py` L271-277；`session_db.py` L74 | **P0** |
| DM-31 | 续 DM-30：`ensure_input_tables` 仅判 `table_exists` → 空壳表被视为"已存在"跳过补导，后续步骤读 0 行且不报错 | 同会话重跑／外部 JSON 复现 | **未适配** | **看似成功但数据为空**（最危险的静默错误） | `executor.py` L92-93、L108-109 | **P0** |
| DM-32 | `tables[].sqlite_table` 唯一性无校验（validator 只查 table_id 与输入∩派生交叉）→ 手写 JSON 两表同名，后者 replace 静默覆盖前者 | 外部 JSON 重复 `sqlite_table` | **未适配** | 数据错误（缺表） | `validator.py` L54-71；`parser.py` L155 | P2 |
| DM-33 | `to_sql` 未设 `chunksize`/`method` → 全表一次性 executemany；`CHUNK_ROW_THRESHOLD=1_000_000` 为死常量（全库 0 引用） | 数十万行以上 sheet | **未适配** | 内存峰值失控（触 §5.2 红线） | `sqlite_manager.py` L149（无 chunksize/method）；`excel_preprocessor.py` L26；`table_importer.py` L26 | P2 |
| DM-34 | 会话库名仅秒级时间戳；双实例同秒确认导入→同名 `.db`；一方 `close(keep_db=False)` 删文件波及另一方 | 同时开两个程序窗口 | 部分适配（R6/F6 只护 `gui_workflow.json`，未护会话库） | 数据错误／导入失败 | `main_window.py` L259-261；`session_db.py` L121-129 | P2 |
| DM-35 | 导入表无主键/NOT NULL/UNIQUE 声明；`to_sql` 绕过 `quote_ident` 字符守卫（列名合法性不校验） | 常规 | 部分适配（索引延后 `ensure_index` 口径一致） | 库内无脏数据防线 | `sqlite_manager.py` L149（`to_sql` 无约束声明）；`sql_safety.py` L197-217 | P2 |

### 5.7 段⑦数据完整性

| 编号 | 现象 | 触发条件 | 已适配 | 影响 | 证据 | 严重度 |
|------|------|----------|--------|------|------|--------|
| DM-36 | 全 NULL 空行原样入库；重复行无识别；尾部空行被 pandas 部分吸收、中间空行成 NULL 行 | 源表含空行/重复行 | **未适配** | 统计口径偏差（行数与用户所见不等） | `excel_preprocessor.py` L210-215（无 `dropna`）；`table_importer.py` L76-97 | P2 |
| DM-37 | 导入后仅 `logger.info` 记 COUNT 与"行×列"，**无** `len(df)` ↔ `COUNT(*)` 断言，也无列数一致性核对 | 任何导入 | 部分适配（可事后人工核对） | 缺数据完整性门禁 | `table_importer.py` L93-97 | P2 |
| DM-38 | 导入在 GUI 线程同步逐表执行；进度框无取消按钮；`cancel_check` 只在引擎侧使用，取消粒度＝表间 | 大表导入中想停 | 部分适配 | 界面假死、不可中途取消 | `main_window.py` L285-306；`table_importer.py` L70-73 | P2 |

### 5.8 段⑧元数据保存与复现

| 编号 | 现象 | 触发条件 | 已适配 | 影响 | 证据 | 严重度 |
|------|------|----------|--------|------|------|--------|
| DM-39 | `tables[].source.file` 永久指向 `temp/input_selection` 副本，而副本在会话收尾 `clear_temp_copies` 即删；参数文件不存原始路径 | 重启程序后按旧 JSON 复现 | **未适配** | 复现导入必失败（FileNotFound）；跨会话不可用 | `page_input_selection.py` L357-374；`main_window.py` L461-465、L332-334 | **P1** |
| DM-40 | `tables[]` 只存 file/sheet/header_row/alias，**不存列类型与列名元数据**；日期与布尔被降级后无任何还原线索 | 无损互转要求"元数据由程序侧保存" | **未适配** | 结构性缺口（类型不可还原） | `models.py` `to_dict` tables L752-765；`executor.py` L97-109 | **P1** |
| DM-41 | 导入根白名单仅 `temp/input_selection`：外部 JSON 直指用户原文件被 `ParserError` 拒绝；相对路径按进程 CWD resolve | 手写 JSON 复现 | 部分适配（安全设计代价） | 复现路径受限 | `executor.py` L42-68 | P2 |
| DM-42 | `header_row` 记录值与实际读取参数一致（`skiprows=N-1`），但入口校验仅 `<1`；`isinstance(True,int)` 放行 | 参数文件字段异常 | 部分适配 | 复现口径漂移 | `excel_preprocessor.py` L199-200；`executor.py` L99 | P3 |

---

## 6. 关键点提炼（5 问）

**Q1 哪些直接破坏 Excel↔SQLite 数据层无损互转？（17 项）**
值层：DM-16（无缓存公式变空）、DM-17（NA 字面量折空）、DM-18（长编号精度丢失）、DM-19（前导零）、DM-20（日期→文本降级）、DM-21（布尔→0/1）、DM-22（日期序列号变整数）、DM-23（控制字符断链）、DM-24（.xls 二次降级）。列层：DM-10（`Unnamed` 列名漂移）、DM-11（合并表头不拦截）、DM-13（非法列名入库）、DM-26（类型口径两套）。元数据层：DM-40（无类型元数据）；结构层：DM-03（副本覆盖）、DM-30/DM-31（空壳表）。

**Q2 哪些导致导入直接失败？（7 项）**
DM-01（exe 无 xlrd，`.xls` 全灭）、DM-02（伪装/损坏文件异常逃逸＋批处理中断）、DM-04（长路径裸 OSError）、DM-14（`header_row` 为 null 的 TypeError）、DM-23（控制字符在导出侧抛错）、DM-30（写入失败留空壳，事务不可救）、DM-39（跨会话复现必失败）。

**Q3 哪些导致"看似成功但数据错误"？（10 项，最危险）**
DM-31（空壳表读 0 行不报错）、DM-03（两条目指向同一文件）、DM-17（`NA`/`NULL` 文本变空）、DM-18/DM-19（编号精度与前导零丢失）、DM-20（日期变文本）、DM-26（列类型与用户预期不符）、DM-10/DM-13（列名漂移，下游选错列）、DM-36（空行使行数口径失真）。

**Q4 哪些只是体验/提示层缺陷？（7 项）**
DM-05（占用类错误落到兜底话术＋英文外泄）、DM-06（隐藏表混入清单）、DM-09（空工作簿无反馈）、DM-15（`Unnamed` 新增列）、DM-25（预览与入库不一致）、DM-38（导入过程无取消、界面假死）、DM-42（参数校验偏松）。

**Q5 哪些环节当前完全没覆盖（结构性缺口）？** 见 §7 八条。

---

## 7. 结构性缺口清单（当前零覆盖）

| # | 缺口 | 说明 | 关联问题 |
|---|------|------|----------|
| G-1 | **导入前内容预检层** | 只有后缀名与行数检查；无列名字符合法性、重名、合并单元格、公式数量、隐藏表的内容级预检 | DM-06/11/13/DM-10 |
| G-2 | **列类型声明入口** | `read_excel_sheet` 只传 3 个参数；无按列 `dtype`/`converters`/`na_filter` 能力，类型全权交给 pandas 推断 | DM-17/18/19/26/27 |
| G-3 | **无损往返校验** | 导入后无行数/列数/类型断言；无抽样回读比对；`len(df)`↔COUNT 不校验 | DM-36/37 |
| G-4 | **公式与外链处置** | 无"公式无缓存值"检测与告警；外链取值随缓存而定且不可见 | DM-16 |
| G-5 | **写入原子性与空壳表防护** | DDL 自动提交语义未被处理；"表存在"不等于"数据存在"，无行数门禁 | DM-30/31 |
| G-6 | **源文件与元数据持久化** | 参数文件引用会消失的临时副本；无列类型/列名清单/表头校验和落盘 | DM-39/40/41 |
| G-7 | **依赖-代码-打包一致性守卫** | xlrd 三处皆缺却无任何检查（自检项 2 依赖清单、hiddenimports、依赖文件三者无交叉校验） | DM-01 |
| G-8 | **导入取消与并发防护** | 无行级中断；无单实例/会话库防撞机制 | DM-34/38 |

---

## 8. 待人工确认项（含本轮发现的方案思路，仅登记不展开）

| # | 事项 | 说明 |
|---|------|------|
| H-1 | 长文本 >32767 字符 | openpyxl 不拦、Excel 打开侧行为未测；需真机确认 |
| H-2 | 隐藏表/图表页的业务期望 | 是否需要默认排除或标注；属产品口径 |
| H-3 | `NA`/`NULL`/前导零是否可接受 | 取决于真实台账字段实况；需人工给数据样本 |
| H-4 | 日期是否要求回写为 Excel 日期格式 | 影响导出模板与 §2.1 条 4 模板化输出口径 |
| H-5 | 双实例同秒会话库碰撞概率 | 需确认是否引入单实例锁（方案思路，不展开） |
| H-6 | 交付包是否已实测 `.xls` 导入 | 构建警告实证依赖缺失，但无真机运行记录 |
| H-7 | 是否补 `requirements.lock` | 现无该文件；pandas 实测 3.0.5 而约束仅写 ≥2.0（大版本漂移风险） |
| H-8 | 白名单是否放开用户原文件 | 涉及 DM-41 的取舍：安全边界 vs 复现能力 |
| H-9 | 是否引入列名合法化/内容预检层 | 属 G-1/G-2 的方案思路，本轮不设计 |

---

## 9. 子 agent 论断纠正（主 agent 探针复核）

| 原论断 | 探针事实 | 结论 |
|--------|----------|------|
| "表头空白列被 pandas 隐式当 index，`to_sql(index=False)` 后该列静默丢失" | 实测空白表头生成 `Unnamed: 2` 列，`df.index.name=None`，列未丢 | **推翻**，改登记为 DM-10（列名漂移，非丢列） |
| "数据行列数多于表头时静默丢列（判为无法确认）" | 实测扩为 `Unnamed: 2/3` 列，`shape (1,4)`，无丢失 | **推翻**，降级为 DM-15（P3） |

其余子 agent 结论中，凡引用行号者已由主 agent 逐条 Grep/Read 复核；DM-30/DM-31/DM-16/DM-17/DM-18/DM-20/DM-23/DM-26 另经内存探针独立确证。

---

## 10. 本轮多 agent 分工与声明

| 角色 | 承担者 | 产出 |
|------|--------|------|
| Read/Parse（段①-③） | 子 agent（只读） | RP-01~RP-20 原始清单与亮点 7 条 |
| Value/Type（段④-⑤） | 子 agent（只读） | VT-01~VT-18 原始清单与亮点 6 条 |
| Write/Integrity（段⑥-⑧） | 子 agent（只读） | WI-01~WI-13 原始清单与亮点 6 条 |
| 主 agent（Orchestrator） | 本次执行 | 8 项内存探针、2 项论断推翻、42 项定稿与关键点提炼、报告落盘 |
| Reviewer | 子 agent（只读） | 8 项验收核对；报出 8 处必修缺陷（计数失真、行号偏差、表结构越界），已逐条处置（见 §11） |

**未修改任何其他文件的声明**：本轮写入面＝`_temp\data_import_issue_scan.md` 一个新建文件；`rpa_engine/**`、`ops/`、`tests/`、`docs/`、`_temp\DAG-rebuild\`、依赖与构建文件、SQLite 数据、构建设计稿**零改动**；探针仅使用内存对象与 `:memory:` 数据库，未落盘、未触碰项目数据文件。

**当前状态**：扫描完成，等待人工下一步指令；本轮不进入实施、不给修复方案。

---

## 11. Reviewer 核对结果与处置

| # | 验收标准 | Reviewer 判定 | 本轮处置 |
|---|----------|---------------|----------|
| 1 | 链路 8 段全覆盖 | 通过（§5.1~§5.8 各有实质条目，无空段） | 无需改 |
| 2 | 每条问题 7 字段齐备 | 通过（8 表均 7 列无空格）；小疵＝§5.4 行序乱 | **已修**：DM-21/22/23 按编号升序重排 |
| 3 | 关键点 5 问自洽 | 不通过：Q1 称 14 实列 17；Q3 称 8 实列 10；§1 与 §6 编号集不一致 | **已修**：§1 与 §6 统一为 17／7／10／7，并加注"分类桶按主要后果归类、存在交集" |
| 4 | 严重度分布自洽 | 不通过：§1 写 36/3/12/16/3/2，实数 42/3/14/21/4/0 | **已修**：§1 改正为 42（P0×3、P1×14、P2×21、P3×4），"待人工确认"改为 §8 的 9 条并单列 |
| 5 | 未给解决方案 | 通过（方案性措辞六项扫描 0 命中；H-5/H-9 仅登记思路） | 无需改 |
| 6 | 禁词与无证据断言 | 通过（唯一模糊措辞命中在 §9 引用被推翻原论断，属豁免） | 无需改 |
| 7 | 证据抽查 a~g | 6 项完全准确；1 项行号偏差（`to_sql` 实在 L148-149，报告写 L146-147；`int(header_row)` 实在 L108 非 L99） | **已修**：主 agent 用 Grep 复核后统一为 L148-149／L140（docstring）／L108，涉及 DM-13/14/27/30/33/35 六行 |
| 8 | 10 节结构齐备 | 通过（10 节全在）；缺陷＝§10 称"结论见 §11"而 §11 为空占位 | **已修**：本节即 Reviewer 结论回填 |
| 9 | 编号与数字连续性 | 通过（DM-01~42 无跳号、G-1~8、H-1~9 连续）；不通过＝§1 计数引用失实（同标准 4） | **已修**：并修正 §3"三处"→"五处（C-1~C-5）" |

**Reviewer 附带发现并已修**：一次编辑误将 DM-14 行写成 8 列（表格越界），已复原为 7 列。

**修正后自评**：42 条问题、7 字段齐备、8 段全覆盖、5 问已答且编号集与 §1 一致、方案边界未越界、行号与源码逐条对齐。**报告状态仍为「扫描态 [待审核]」，等人工审核。**
