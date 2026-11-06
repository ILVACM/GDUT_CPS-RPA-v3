# W-03 完善度修复轮（批次 A-F）实施报告

> **⚠ 归档注记（2026-09-24 R10）**：本文件为历史轮次快照，正文未改写。现位于 `_temp/ledger_2026-09-24/`；文中指向已清理 `_temp` 件（GUI 细节方案／M5 设计／审计报／审计方案／运行流程简报／repo-context／verify 留痕）的旧路径，其章节骨架与结论沉淀位置见同夹 `CLEANUP_MANIFEST.md` §2～§3，引用对账见 §5。

> 轮次：R6｜日期：2026-09-24｜依据：`_temp/ledger_2026-09-24/RPA_engine_remediation_plan.md`（冻结，35 任务/89 步）
> 执行计划：`.trae/documents/完善度修复轮AF执行计划.md`（人工批准）｜task-record：`docs/task-records/2026-09-24-w03-remediation-batches.md`

## §0 基线复验（阶段 0）

- `python -m unittest discover -s tests`（conda CPS-GPES_RPA-py311，cwd=rpa_engine）→ **Ran 88 tests OK（0.083s）**。
- 双 smoke（旧路径 _temp/DAG-rebuild/）→ SMOKE_ALL_OK ×2。
- step_executor.py 外部改动核对：锚点无实质漂移（execute_step L137/fail L168/param_keys 白名单 L195/output_table 回退 L201；M5 注释块 L46-58 区域在位）。
- AGENTS.md：锚点改 R6`进行中`，§8 主线更新（exe 表述改"D10 待人工确认"口径）。

## §1 批次 E5（门禁载体迁移＋假断言修真）——完成

- **E5-S1 迁移**：新建 `rpa_engine/tools/smoke/`，smoke_m1m3.py/smoke_mb.py 复制迁入；ENGINE 常量改 `parents[2]`（原 `parents[2]/"rpa_engine"`）；docstring 更新（门禁载体定位＋新运行命令）。新位置双跑 **SMOKE_ALL_OK ×2**。
- **E5-S2 原件删除**：前置核对＝SampleCode/ 0 引用、docs/AGENTS/README 0 命中（其余引用均 _temp 历史留痕，按 E5-4 不改）→ 删除 `_temp/DAG-rebuild/smoke_m1m3.py`、`smoke_mb.py` 两原件。
- **E5-S3 假断言修真（2 处）**：L150 去 `or True`（"M2 撤销条显示"→isVisibleTo 真断言，实跑 OK）；L176 `check(...,True)`→`out1 in op._scene._table_items and len(op._last_edges)>=1`（实跑 items=True edges=9）。grep `or True` 新载体 0 命中。
- **E5-S4 治理注记**：doc-governance §8 条 2 事实校准（"无现成回归套件"→"回归套件现状"：tests 88+ 与 tools/smoke 门禁载体、_temp 一次性脚本限制保留）；frontmatter last-updated→2026-09-24；INDEX 日期同步归 E1-S3。
- **偏差留痕（A7 纪律，3 条，均非实质矛盾）**：①冻结方案 E5-3 对两处恒真断言的场景描述与实测不符（L150 实为"撤销条显示"非"R2-1e 表单挂载"；L176 实为"撞号重绘不崩"非"M2-S4c 最近使用"——最近使用断言 L197 本已为真）→ 按各自断言原意修真，方案目标（恒真清零）达成；②smoke_mb 3 处 hasattr 实为**否定存在断言**（not hasattr，H2 调序零残留验证），本身即真断言 → 方案"升级 callable"子项判定无需修改，已在 smoke_mb docstring 注明；③方案 L150 建议替换式（_current_form）与被修真断言语义不符，未采用，采用原断言去 `or True`（更忠实原意）。
- **门禁**：双 smoke（新路径）ALL_OK＋discover 88 绿（阶段 0 基线，E5 零测试面改动）。

## §2 批次 A（止血）——完成，门禁绿

- **A1（P0-1/D1①）**：models.to_dict 增 derived_phys 映射（uid 防御后）＋cp 行三级回退（sqlite_of→derived_phys→逻辑号）。用例：OverwriteDerivedTargetTest 2 个（cp 物理名=t_{s1.uid}≠T101／编辑态回归）＋OverwriteDerivedEngineTest 执行级（无游离 T101 表、t_{uid1} 内容=[2,3]、输入表 4 行未触碰）。
- **A2（P3-9）**：worker 信号扩 4 参（+success）＋run 消费 result["success"]；_on_workflow_finished +success 默认参＋display_status(completed_partial)＋输出清单执行后收集（failed/cancelled 置空）；page_report._STATUS_TEXT 增"部分完成（有步骤被跳过）"；HonestReportTest（skip→completed+success=False+1/2）。A2-S1/S2 同单元完成（§九 条 3）。
- **A3（P3-10/D9）**：fill 增 overwrite_ids 关键词参＋派生表行"（中间结果，已写回）/（输出）"标注；调用侧组装覆盖链父步表号集。
- **A4（P2-5）**：_harvest L677 整包替换→增量合并三行；FilterForm.get_params 删硬编码 "logic":"AND"（消费端 step_executor L211 默认 AND 等价，grep 已核）；output_mode 有控件才输出现状已成立不改。smoke M6-A4：logic=OR 往返不丢＋aggregate 注入 output_mode 经合并保留（实测 alias 重算证明 form 成功收拢、merge 路径真实生效）。
- **门禁**：discover **92 OK**（88+4）＋smoke_m1m3 ALL_OK（M6 8 check）＋smoke_mb ALL_OK。
- 备注：completed_partial 允许"保存本次配置"（配置有效，跳过属运行期数据问题）——施工图未显式规定，按语义补齐，记此留痕。

## §3 批次 B（人话）——完成，门禁绿

- **B1（P0-2）**：新建 gui/error_messages.py（10 规则翻译表＋translate_error＋log_hint，纯标准库+paths）；main_window 失败弹窗改 translate_error+log_hint（"终端输出面板"死指引字面全库清零，grep 0 命中）；_on_step_failed 气泡经翻译（原文只进日志）；page_report 增"技术详情"折叠区（QToolButton checkable＋_tech_browser 默认隐藏，绝对路径/物理名映射全部移入，主区仅人话摘要）；sql_safety require_table 表名清单移 logger.warning、异常文本"步骤使用的数据表不存在"。用例：tests/test_error_messages.py 5 个（已知列错/空兜底/占用自救/规则表禁用词遍历/log_hint）。smoke M6 增补：主区无物理名、技术详情默认隐藏 2 check。
- **B2（P1-8）**：导入捕获面 (ValueError,FileNotFoundError)→(+PermissionError,OSError,sqlite3.Error)；failed 清单文案经 translate_error；原始异常类型进日志；顶部 import sqlite3。
- **B3（P2-14/D6②）**：executor else 分支增 retry 耗尽 raise ExecutionError（含重试次数）；skip 语义保留。用例：test_retry_exhausted_raises（assertRaises＋"重试 2 次"）。
- **门禁**：discover **98 OK**（92+6）＋双 smoke ALL_OK（M6 10 check）＋自检 SELFCHECK_OK 6＋grep"终端输出面板"rpa_engine 0 命中。
- 文案评审（B1-7）：翻译表返回值全集过 §8.4 禁用词口径——10 规则人话/动作字段无 SQL/表名/SQLite/物理名类词（test_rules_clean_and_nonempty 遍历断言固化）；弹窗/气泡/导入失败三出口全接翻译层。

## §4 批次 C（交付）——Agent 项完成；试构建/D10 确认留人工

- **C1-S1**：新建 `tools/make_fingerprint.py`（D5③ 双指纹：文件哈希汇总＋git）；试运行输出 `SOURCE_HASH=a75c1249820c7525 / FILES=48 / GIT_REV=7a5703a2…`（git 可用，非 N/A）。
- **C1-S2＋C2-S1~S4**：build.bat 全量重写（八步流程落地）：测试门禁前置（discover＋双 smoke，失败中止零改动；--skip-tests 显式跳过并记 TESTS_SKIPPED）→ 指纹注入（Step 3）→ `_build_tmp` 临时目录构建（Step 4）→ 旧包 backup 留存＋原子替换（Step 5）→ BUILD_INFO 重写（SOURCE_HASH/GIT_REV/TESTS_SKIPPED 新字段）→ 清理仅删中间产物（Step 6）。**用户数据五目录（workspace/logs/storage/temp/backup）永不删红线**在脚本尾部显式声明；原 L152-153 `rmdir /s /q build/` 逻辑废除。参数接口保留（--build-dir/--output/--clean/裸路径兼容＋新增 --skip-tests），validate_path 子程序原样保留。
- **偏差留痕（编码）**：原 build.bat 为 GBK 编码中文消息，直接编辑会致编码损坏 → 重写为**纯 ASCII 英文消息**（编码无关安全）；参数接口/行为契约不变；build-guide §2 增备注条目。重写后经 PowerShell 固化 CRLF＋ASCII。
- **C1-S3**：TitleBar 增"关于"按钮＋_show_about（frozen 读同目录 BUILD_INFO 指纹段；源码态"开发版"）。
- **C1-S4**：build-guide §1.10 增"指纹判据"条（第 4 判据：SOURCE_HASH 重算比对）＋"当前状态"条补 D10 待人工确认注记（09-24 05:32 构建记录与"已失效"表述的矛盾呈报人工）。
- **C3-S1**：app.py 自检项 3 失败 detail 人话化（安置指引：可写位置/勿放 Program Files，D3② 便携约定；paths.py 未动）。
- **C4-S1**：requirements.txt 删 python-docx/python-pptx 死依赖＋注释更新（steps/ 已删事实、lock 指引）；`requirements.lock` 生成（conda py311 pip freeze，ASCII）。
- **人工门禁（挂 §9）**：C0-S1（D10 确认）＋试构建与失败注入测试（R2：Agent 不执行 build.bat）＋部署指南便携约定条目（随 E6-S2）。
- **门禁**：discover＋双 smoke＋自检（本批仅 bat/文档/GUI 按钮与提示文案改动，测试结果见 §8 汇总矩阵）。

## §5 批次 D（健壮）——完成，门禁绿

- **D1（P1-4/P2-12）**：session_db busy_timeout=5000；execute_step/export_table/import_excel_table/ensure_input_tables 增 cancel_check 关键词参（仅 export 与导入链传递，9 分支结构未动）；exporter fetchmany 每批、importer 起点取消检查（RuntimeError 约定文本）；executor 捕获段 cancel→cancelled 归并（与步骤间检查点同口径）；_step_timeout_sec 抽函数（默认 600/显式/0 停用/非法回退四分支）＋步骤事后计时告警。
- **D2（P1-5）**：wait 返回值消费＋_ignore_next_finish（_on_confirm_import/_back/_new_round/_discard 四入口一致）；_on_workflow_finished 首行丢弃陈旧回调；cleanup_stale_files 静态纯函数（孤儿 session_*.db* 全删＋超龄 24h 副本）＋启动接线。
- **D3（P1-7）**：page _temp_copies 登记（copied＋ensure_xlsx 产物）＋clear_temp_copies；_close_session 接线；导入前磁盘预检（源大小×3，人话提示中止）。
- **D4（P2-4）**：executor 完成态统一清理中间表；**protected 保护集**（cp 写回目标物理名不删，与 A1 联动）；keep_db=True 跳过；失败/取消不清理。
- **D5（P2-9）**：node_graph missing_by_dst 预分组外提（O(S×E)→O(E)）；CANVAS_WARN_STEPS=150 警戒（rebuild 日志＋page 状态栏一次性提示）；_graph_timer 50ms 合并刷新（13 调用点批量收口，公共 refresh_graph 保留即时直调）；fit_to_scene 改"仅步骤数变化时"。
- **D6（P2-10）**：sql_safety.INDEX_ROW_THRESHOLD=50_000＋ensure_index（幂等/quote_ident/表缺失静默）；mapping_matcher JOIN 双侧、aggregator GROUP BY、filter_dedup PARTITION 列条件建索引。
- **D7（P2-13）**：executor _IMPORT_ROOTS 白名单＋register_import_root＋_validate_import_path（resolve 后 relative_to 判定，越界 ParserError）；exporter 拒绝导出到导入副本区。
- **D8（P3-6）**：insert_rows 列集分桶 executemany 化；导入链 sheet_info 一次扫描传参复用。
- **用例**：新增 tests/test_engine_robustness.py 12 个（阈值四分支/步骤间取消/循环内取消归并/清理+输入表保留/keep_db/白名单拒绝+register 放行/索引双路径+幂等+缺表静默/孤儿清理纯函数/导入一致性/副本区拒绝）。
- **门禁**：discover **110 OK**（98+12；中途 1 失败为测试自身无意义断言，已修）＋双 smoke ALL_OK＋自检 OK 6。
- **偏差留痕（4 条，A7 纪律）**：①导入侧无行级循环（CHUNK_ROW_THRESHOLD 属死常量，无分块实现）→ 取消粒度＝表间＋起点检查（导出侧为每 5000 行）；②计时告警仅日志承载——不重复调 progress_callback（防 done_count 双计），"话术"由日志文件+报告页技术详情承载；③smoke 即时断言与 50ms 合并定时器冲突→双 smoke 头部加类级补丁 `_schedule_graph_refresh=_refresh_graph`（仅测试通道；较"逐场景补 processEvents"更稳健）；④导入并扫 3 次开簿→2 次（scan+read 合并；pd.read_excel 的开簿不可并入 openpyxl 扫描，完全单次需重构读取路径，收益/风险不成比例——超出"传参复用"裁定范围不做）。
- **人工真机项（挂 §9）**：慢导出"终止操作"生效、200 步画布耗时记录、拔线（强杀）重启孤儿清理、双连接 busy_timeout 并发场景。

## §6 批次 E（治理余量）——完成，门禁绿

- **E1（P1-11 文档体检）**：新建 `tools/doc_verify.py`（纯标准库三查：①相对链接可达（AGENTS/README/docs/**/knowledge/**，代码块与行内代码剔除防误报）②docs/INDEX 日期列 ↔ frontmatter last-updated ③AGENTS 容量三口径＋行尾约束；报告落 `_temp/verify-<YYYYMMDD-HHMM>.md`，退出码 0=全绿）。首跑暴露 8 项并已修复：dev-spec 伪链接 1（脚本侧修：代码内 `[op](df)` 误报）；INDEX 6 处日期漂移（architecture/build-guide/runtime-env-spec/doc-governance/backlog/DAG 分析 → 按 frontmatter 实况同步）；**AGENTS.md 行尾漂移 loneLF=196**（本轮早期编辑引入，已 PowerShell 全量转回 CRLF，复测 loneCR/loneLF=0、含CR 7754≤8000、余量 246≥200）。E1-S2：architecture §8.2 阶段 1 六列按 page_input_selection 实况修订（选择/标识名称/来源文件/源数据表/表头行/删除）、"独立弹窗"改"内联表单"；§8.3 信号表按 worker.py 实况（step_completed 2 参、workflow_finished 4 参、log_message 已随 W-19 移除、取消机制补导出循环内检查点）；frontmatter→2026-09-24。E1-S3：models.py to_dict docstring"uid 双口径均剔除"矛盾修正（业务口径剔除；编辑态第 9 键持久化，M5-a 实况）。E1-S4：doc-governance §4 增"脚本化辅助"条目。
- **E2（P1-3 版本门禁）**：parser `_SUPPORTED_SCHEMA_VERSIONS={"3.1"}`（模块常量）＋parse_workflow 门禁——键缺失→缺省 "3.1" 放行（现状固化）；显式给出（含空串/"3.10"）→人话拒绝（含"请升级程序"，error_messages 规则表已有对应条目）。用例 3 个（在 test_engine_robustness.py）。
- **E3（P2-6）**：step_executor 白名单丢弃键 logger.debug（含 op 与 sorted(dropped)）；keep_db 两端接线——引擎端＝D4-1 清理开关已消费 global_config.keep_db；GUI 端＝start_workflow 解析成功后 `self._keep_session_db=bool(wf.global_config.get("keep_db",False))`→_close_session 决定保留/删除会话库（保留时 logger.info 路径）。模型层不加开关（to_dict 恒写 False 现状保留）。用例：keep_db 双态（robustness）。
- **E4（P2-3 两本账对账）**：新建 `tests/test_states_consistency.py` 5 用例——model.reconcile() 的 table_states 五态集合 ↔ graph_edges.build_edges 派生边类型逐表比对（produce/reference/deprecated/dangling/输入表）。口径修正留痕：overwritten＝**产出步自身持 overwrite 模式**（models L571-574 实况），覆盖父步不产 produce 边、其目标表按引用口径；首版 API 误用（deprecated_tables 属性当方法调、specs_from_model 元组签名）已按真实签名重写。
- **E6（P2-8 两手册）**：新建 `docs/user-manual.md`（五章：做什么/四步走（截图占位×4）/自救表（与 error_messages._RULES 同源 10+1 行）/注意事项 6 条/求助渠道）＋`docs/deployment-guide.md`（一页：D3② 便携约定/更新=替换 exe＋五目录红线/指纹核对三处闭环/排查表/环境要求）；frontmatter 按 doc-governance §3（type: knowledge/binding: reference）；INDEX 登记 2 行＋路由关键词 2 行＋篇数口径 10→12；README 导航同步（含技术栈行 python-docx 移除事实、R6 状态行）。实况校准：阶段 1 添加按钮字面为 `[add]`（英文遗留），手册如实描述并登记 §9 遗留项。
- **E7（P2-7）**：app.py QApplication 构造前双 HighDpi 属性；main_window setMinimumSize(1100,700)＋底栏 QSizeGrip（frameless 拖拉缩放）；styles.py 字号保留 px（施工图裁定）。
- **E8（P3-4 注释三改）**：page_input_selection "前20行"→"前 50 行（_PREVIEW_ROWS）"；app.py docstring"5 项"→"6 项"；registry.py 自述随 F3 改"真转发层"。
- **E9（P3-7 重排提示）**：_on_confirm_import 编号分配后比对新旧 registry {table_id:(source,sheet)}，映射变化的表号被步骤引用时 QMessageBox.information 列出受影响步骤（旧→新来源）；无变化/首导入静默。
- **E10（P3-8 last_config 防抖）**：_lc_timer（singleShot 2000ms→_save_last_config）；触发＝operation_config_page.on_model_changed 回调＋确认导入完成后；退出直写保留；崩溃恢复口径不变。
- **门禁**：discover **118 OK**（113+5 对账）＋双 smoke ALL_OK＋自检 6/6＋doc_verify **PASS**（links=77, failures=0）。

## §7 批次 F（大扫除）——完成，门禁绿

- **F1（P3-1/H2 执行）**：models.py move_step 删除（替换为裁定注释块：H2"调序 UI 不恢复、留下一清理轮"本轮执行；调序等效＝remove_step＋insert_step；漂移免疫由 t_{uid} 保证）。唯一消费者 smoke_m1m3 M5a 调序场景改等效序列（remove+insert；uid_agg 物理名 t_{uid} 双断言＋类型序 ["aggregate","filter"] 断言保留）；tests 零引用（grep 核对）。grep `def move_step` rpa_engine 0 命中。
- **F2（P3-2）**：ops/__init__.py 导入块＋`__all__` 收缩 9 项（cleanup_files/execute_sql/fetch_dataframe/create_table/get_column_info/delete_rows/insert_rows/query_rows/update_rows；**delete_table 保留**——D4 生产调用）；除名处留 R6/F2 注释（死 API 定性＋生产写入唯一通道）；sqlite_manager.execute_sql docstring 加"内部工具，非工作流操作，禁止接入 JSON 参数"。除名前后全库 grep：9 名仅定义模块自持，零生产/测试断链。
- **F3（P3-3）**：engine/registry.py 重写为**真转发**（`from ops.step_executor import BUILTIN_OPS, get_op_func, list_ops`；get_op_description 保留本地实现）；双活副本消除；调用方（app.py×3/test_step_catalog×2/engine/__init__）零改动验证通过。
- **F4（P3-5）**：forms.py `_OPS` 改引擎单一源派生——`from ops.sql_safety import SUPPORTED_OPERATORS`＋`_OPS=[op for op in _OPS_ORDER if op in SUPPORTED_OPERATORS]`（_OPS_ORDER 仅定义展示顺序）；app.py 守卫区增 `_OPS ⊆ SUPPORTED_OPERATORS` 断言（自检项 4b）。差集核对：_OPS 10 项全部 ∈ SUPPORTED_OPERATORS 12 键（无需补 sql_safety）。**偏差留痕**：施工图字面为 `SUPPORTED_OPERATORS as _OPS` 直接引用——直引会把 "<>"/"NOT LIKE"/"NOT IN" 3 项带入界面下拉（行为扩面）且类型由 list 变 dict（消费端 ComboBox 遍历顺序依赖）；采"引擎源过滤派生"实现单一来源语义，界面行为零变化。
- **F5（P3-11）**：graph_edges.py detect_table_id_collisions 门面删除（留注释指向唯一生产入口 validate_table_ids_unique）＋`__all__` 移除；测试改生产入口：test_models_data CollisionTest→test_facade_removed_production_entry（assertFalse hasattr）；test_graph_edges CollisionDetectionTest 3 用例改用 m.validate_table_ids_unique()。grep 门面名：仅注释与"断言不存在"字面，0 生产引用。
- **F6（P3-13 三加固）**：①table_schema convert_dtype col_type 过 `_TYPE_WHITELIST`（施工图 9 类＋FLOAT/TIMESTAMP/INT 偏差补充＝现场取证既有调用面；`split("(")[0]` 容忍 VARCHAR(50)；非白名单回退 TEXT＋logger.warning）；②sql_safety build_where LIKE/NOT LIKE 值转义（`\`/`%`/`_`→转义＋SQL 加 `ESCAPE '\'`，通配符按字面匹配）；③main_window gui_workflow.json 双开互覆防护——`_instance_id`（启动时间戳）＋`_instance_started`；start_workflow 写前读校验（文件存在且 mtime 晚于本实例启动且 __meta.instance_id≠本实例 → 放弃写＋logger.warning）；models.save_json 增 `extra_meta` 关键词参（instance_id 写入 __meta，不覆盖 schema_version/created）。**偏差留痕**：检测到互覆时除"放弃写＋warning"外**同步中止本次启动并弹窗提示**——若放弃写后继续 parse，将执行他实例配置（与防互覆本意相悖）；save_json 增参为施工图未明示的最小实现载体。
- **门禁**：discover **118 OK**（F 批零新增/零删除用例：CollisionTest 改名等量替换）＋双 smoke ALL_OK＋自检 6/6＋专项 grep（`def move_step` 0／`detect_table_id_collisions` 生产 0／`or True` 0）。

## §8 治理收尾汇总

**门禁矩阵（用例数演进）**：

| 批次 | discover | 双 smoke | 自检 | 附加门禁 |
|------|----------|----------|------|----------|
| 阶段 0 基线 | 88 OK | ALL_OK×2 | — | — |
| E5 | 88 OK | ALL_OK×2（新路径） | — | grep `or True` 0 |
| A | 92 OK | ALL_OK×2 | — | — |
| B | 98 OK | ALL_OK×2 | 6/6 | grep"终端输出面板"0 |
| C | （随 D 复跑） | — | 6/6 | make_fingerprint 试运行 OK |
| D | 110→113 OK | ALL_OK×2 | 6/6 | 中途 1 失败＝测试自身断言缺陷，已修 |
| E | 118 OK | ALL_OK×2 | 6/6 | doc_verify PASS（links=77） |
| F | 118 OK | ALL_OK×2 | 6/6 | 专项 grep 三项 0 命中 |

**终态**：118 用例（88 基线＋30 新增：A4/B6/D12+3/E2 门禁 3 已计入 robustness 15/E4 对账 5）＋双 smoke＋自检 6/6＋doc_verify PASS 全绿；AGENTS.md 容量三口径复测（锚点收尾后终值，报告 `_temp/verify-20260924-1020.md`）：**含CR 7774/上限 8000（余量 226≥200）/行数 196；loneCR=0 loneLF=0（纯 CRLF）**——收尾编辑曾致余量 119<200，按 doc-governance §10.2 下沉压缩锚点/§8 表述后恢复；本轮编辑引入的行尾漂移（loneLF）已两次 PowerShell 复固化 CRLF。

**偏差留痕总表**（全轮 12 条，均非实质矛盾、不触红线）：E5×3（§1）＋A×1（completed_partial 允许保存配置，§2）＋C×1（build.bat GBK→ASCII 重写，§4）＋D×4（§5）＋E×2（E4 口径修正/E1 脚本代码块防误报为脚本自身修复，§6）＋F×2（_OPS 派生式单一源/F6 中止启动与 save_json 增参，§7）。

**排除项确认**：功能函数优化批 5 项（P1-1/P1-2/P1-6/P2-1/P2-2）按裁定未实施；F7（CI）说明项不立项；H2 move_step 清理已随 F1 执行完毕（backlog 对应条目可关闭，待人工确认）。

## §9 人工门禁清单（移交）

> **验收记录（2026-09-24）**：以上清单全部经人工确认，符合预期（D10/试构建与失败注入/真机项/文档通读/git 提交）。R6 修复轮就此闭环；后续更全面的测试审计另起轮次。第 5 条 `[add]` 按钮遗留登记建议随下轮裁定。

1. **D10 确认**：09-24 05:32 构建记录与"exe 已失效"表述的矛盾——确认该构建包是否为交付基准；结果落地 build-guide §1.10／backlog W-20／AGENTS §8 三处口径。
2. **build.bat 试构建＋失败注入测试**（R2：Agent 不执行构建）：①正常构建→BUILD_INFO 含 SOURCE_HASH/GIT_REV；②门禁失败注入（临时改坏一用例）→构建中止且旧包无损；③五目录（workspace/logs/storage/temp/backup）试构建后原样。
3. **真机验证项**：高分屏截图核对＋最小尺寸/QSizeGrip 拖拉（E7）；双开互覆实测（F6：第二窗口启动执行人话提示）；强杀重启孤儿清理（D2）；200 步画布耗时记录（D5）；慢导出"终止操作"循环内生效（D1）；E9 重排弹窗交互；E10 防抖 2s 落盘现场；双连接 busy_timeout 并发场景。
4. **文档人工项**：user-manual/deployment-guide 人工通读（E6 DoD）；user-manual 4 处截图占位补图；C3-S1 自检提示文案评审确认。
5. **遗留登记建议**：阶段 1 添加按钮英文字面 `[add]` 违反 §8.4 文员口径（历史遗留，不在本轮 37 项范围）——建议纳入 backlog 排期改"添加文件"。
6. **git 提交**：Agent 不执行 git；本轮全部变更（rpa_engine 源码/tests/tools、docs 6 文件、README、AGENTS、build.bat、requirements、新增 tools/ 2 脚本）待人工审阅提交。
