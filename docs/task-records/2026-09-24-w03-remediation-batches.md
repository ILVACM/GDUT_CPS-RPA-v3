# 任务记录：W-03 完善度修复轮（批次 A-F）

> 轮次：R6｜开始：2026-09-24｜操作人：黄泊凯（人工裁定）＋ AI Agent（TRAE，实施）
> 依据：`_temp/RPA_engine_maturity_assessment.md`（评估）→ `_temp/RPA_engine_remediation_plan.md`（冻结施工图，D1-D10 已裁定，35 任务/89 步）
> 执行计划：`.trae/documents/完善度修复轮AF执行计划.md`（人工批准）

## 1. 任务目标

实施 37 项完善度修复（功能函数优化批 5 项除外）：E5 首批（门禁载体迁移+假断言修真）→ A 止血（P0-1 覆盖派生表/诚实报告/表单增量合并）→ B 人话（错误翻译层）→ C 交付（指纹/打包原子化，人工构建项挂起）→ D 健壮（超时取消/清理/性能/索引/沙箱）→ E 治理（doc_verify/版本门禁/手册/DPI）→ F 大扫除（死码/单源）。

## 2. 范围与边界

触碰面：rpa_engine 代码与测试、tools/（新：doc_verify/make_fingerprint/smoke）、docs/ 五文档+两新文档、README、AGENTS、requirements.*、build.bat。不动：SampleCode 冻结基线、engine 架构、K/M5 裁定产物；不执行 git、不执行 build.bat（R2 裁定）。

## 3. 执行日志（逐批追加）

- 阶段 0（完成）：基线复验 88 用例 OK（0.083s）＋双 smoke ALL_OK（旧路径）；step_executor 外部改动核对＝锚点无实质漂移（execute_step L137/fail L168/白名单 L195/output_table L201）；AGENTS 锚点 R6 开立。
- 批次 E5（完成）：双 smoke 迁 `rpa_engine/tools/smoke/`（新位置双跑 ALL_OK）→ _temp 原件删除（SampleCode 0 引用核验）→ 恒真断言修真 2 处（撤销条 isVisibleTo／撞号重绘 items+edges 实断言）→ doc-governance §8 条 2 事实校准。偏差 3 条留痕 REPORT §1（场景描述与实测不符按断言原意修；smoke_mb not-hasattr 为真断言无需升级）。
- 批次 A（完成）：P0-1 覆盖派生表三级回退（models derived_phys＋cp 行）／P3-9 诚实报告（worker 信号扩 4 参＋completed_partial＋输出清单后移）／P3-10 中间表标注（fill overwrite_ids）／P2-5 表单增量合并＋FilterForm logic 硬编码删。门禁 92 绿。备注留痕：completed_partial 允许"保存本次配置"（施工图未显式规定，按语义补齐）。
- 批次 B（完成）：新建 gui/error_messages.py（10 规则翻译层）；弹窗/气泡/导入失败三出口接翻译；page_report 技术详情折叠区（技术路径全部移入，主区仅人话）；require_table 表名清单移日志；导入捕获面扩 5 类；retry 耗尽 raise ExecutionError。门禁 98 绿＋自检 6/6。
- 批次 C（Agent 项完成）：tools/make_fingerprint.py（双指纹）；build.bat 全量重写（测试门禁前置/指纹注入/_build_tmp 原子发布/.bak 回退/五目录永不删红线/ASCII 化——GBK 编码偏差留痕）；标题栏"关于"按钮；自检项 3 提示人话化（D3② 安置指引）；requirements 死依赖删＋lock 生成；build-guide §1.10 指纹判据＋D10 注记。试构建/D10 留人工（REPORT §9）。
- 批次 D（完成，25 步全量）：busy_timeout=5000／cancel_check 传链（export 分支＋导入链，循环内每批检查）／_step_timeout_sec 四分支＋计时告警／陈旧回调丢弃＋四入口 wait 消费／cleanup_stale_files 静态化＋启动接线／_temp_copies 会话清理＋磁盘预检（×3）／完成态中间表清理＋protected 保护集＋keep_db／画布性能（missing_by_dst 外提＋50ms 合并刷新 13 调用点＋CANVAS_WARN_STEPS=150＋fit 仅步骤数变化）／INDEX_ROW_THRESHOLD=50000＋ensure_index 三处／_IMPORT_ROOTS 白名单＋副本区拒绝／insert_rows executemany 分桶＋sheet_info 传参并扫。新增 test_engine_robustness.py。门禁 110→113 绿（中途 1 失败＝测试自身断言缺陷已修）。偏差 4 条留痕 REPORT §5。
- 批次 E（完成）：E1 tools/doc_verify.py 三查脚本＋首跑 8 项修复（INDEX 6 处日期/AGENTS 行尾 loneLF=196 转回 CRLF/architecture §8.2 §8.3 实况修订/models docstring 矛盾/doc-governance §4 脚本化条目）；E2 版本门禁（_SUPPORTED_SCHEMA_VERSIONS，3 用例）；E3 丢弃键日志＋keep_db 两端接线；E4 test_states_consistency.py 对账 5 用例（overwritten 口径按 models L571-574 实况修正）；E6 user-manual.md＋deployment-guide.md＋INDEX 登记＋README 导航；E7 HighDpi 双属性＋最小尺寸＋QSizeGrip；E8 注释三改；E9 编号重排提示；E10 last_config 防抖（2s）。门禁 118 绿＋doc_verify PASS（links=77）。
- 批次 F（完成）：F1 move_step 删除（H2 执行）＋smoke M5a 改 remove+insert 等效序列；F2 ops __all__ 收缩 9 项（delete_table 保留）＋execute_sql 内部标注；F3 registry 真转发（调用方零改动验证）；F4 _OPS 引擎单一源派生＋app.py ⊆ 守卫；F5 detect_table_id_collisions 门面删除＋两处测试改生产入口；F6 col_type 白名单（9+3 类）＋LIKE ESCAPE 转义＋gui_workflow.json instance_id 写前读校验（save_json extra_meta）。门禁 118 绿＋双 smoke＋自检 6/6＋专项 grep 三项 0 命中。偏差 2 条留痕 REPORT §7。

## 4. 关键决策与偏差留痕

- 执行序细化：E5 提前至首批（§九 仅要求 C 前；避免 A 批 smoke 场景二次迁移）——记 REPORT §1。
- 全轮偏差 12 条（E5×3/A×1/C×1/D×4/E×2/F×2），均非实质矛盾、不触红线，逐条见 REPORT §1-§7 与 §8 总表。要点：build.bat GBK→ASCII 重写；F4 采"引擎源过滤派生"而非字面直引（防界面下拉扩面）；F6 互覆检测同步中止启动（防执行他实例配置）；col_type 白名单补 FLOAT/TIMESTAMP/INT。
- AGENTS.md 行尾漂移（loneLF=196，本轮编辑工具引入）→ E1 脚本首跑暴露，PowerShell 全量转回 CRLF，复测三口径合格。

## 5. 验证与门禁

- 用例演进：88（基线）→92（A）→98（B）→110→113（D）→118（E/F 终态）；每批双 smoke ALL_OK（E5 后新路径）＋自检 6/6（B 批起）。
- 终态复跑（E/F 收尾）：discover 118 OK＋SMOKE_ALL_OK×2＋SELFCHECK OK 6＋doc_verify PASS（links=77, failures=0，终版报告 `_temp/verify-20260924-1020.md`）。
- AGENTS 容量三口径（锚点收尾后终值）：含CR 7774/上限 8000（余量 226≥200）/行数 196；loneCR=0 loneLF=0（纯 CRLF）。收尾编辑曾致余量 119<200，按 doc-governance §10.2 下沉压缩后恢复；行尾漂移两次 PowerShell 复固化。

## 6. 产出物清单

- 新文件：rpa_engine/gui/error_messages.py、rpa_engine/tests/test_error_messages.py、test_engine_robustness.py、test_states_consistency.py、rpa_engine/tools/smoke/（双 smoke 迁入）、tools/make_fingerprint.py、tools/doc_verify.py、docs/user-manual.md、docs/deployment-guide.md、requirements.lock、build.bat（重写）。
- 修改：rpa_engine 源码（models/worker/main_window/page_report/page_operation_config/page_input_selection/forms/app/node_graph/graph_edges/parser/executor/step_executor/session_db/exporter/table_importer/excel_preprocessor/sql_safety/table_schema/table_content/sqlite_manager/registry/ops __init__）、tests（test_models_data/test_engine_overwrite/test_graph_edges）、docs（architecture/doc-governance/build-guide/INDEX）、README、AGENTS、requirements.txt。
- 治理载体：REPORT（`_temp/W-03_Remediation_round_2026-09-24/REPORT.md` §0-§9 全量）＋本记录。

## 7. 人工门禁项移交（REPORT §9 同步）

①D10 确认 09-24 包状态→C1-S4 三处口径+W-20 处置；②build.bat 试构建+失败注入测试；③真机项（高分屏/双开/强杀/200 步实测/慢导出终止/E9-E10 交互/手册通读+截图占位）；④"[add]" 按钮英文字面遗留登记建议；⑤git 提交。

## 8. 收尾结论

37 项修复（功能函数优化批 5 项除外）全部落地：批次 E5/A/B/C（Agent 项）/D/E/F 完成，终态门禁全绿（118 用例＋双 smoke＋自检 6/6＋doc_verify PASS＋AGENTS 容量三口径合格）。人工门禁项（D10/试构建/真机验证/文档通读/git）移交 REPORT §9。本轮完成，待续＝人工门禁项闭环。

**人工验收（2026-09-24）**：REPORT §9 清单全部经人工确认，符合预期，R6 修复轮闭环；后续更全面的测试审计另起轮次。
