# RPA 引擎问题修复方案（功能函数优化除外）

> **⚠ 归档注记（2026-09-24 R10）**：本文件为历史轮次快照，正文未改写。现位于 `_temp/ledger_2026-09-24/`；文中指向已清理 `_temp` 件（GUI 细节方案／M5 设计／审计报／审计方案／运行流程简报／repo-context／verify 留痕）的旧路径，其章节骨架与结论沉淀位置见同夹 `CLEANUP_MANIFEST.md` §2～§3，引用对账见 §5。

> 状态：**定稿 [冻结] / Frozen，待实施**（2026-09-24 人工批准）
> 日期：2026-09-24｜依据：`_temp/RPA_engine_maturity_assessment.md`（评估态 [待审核]，P0×3/P1×11/P2×14/P3×14）
> **人工批准记录（2026-09-24）**：①D1-D10 全部按首选采纳（§四 已改裁定记录，无待决项）；②人工指令"进一步细化方案，使方案文件能准确且没有歧义地引导 agent 完成修改优化工作"→ 本文件深化为施工图级（§六 证据锚点表／§七 施工细化／§八 原子任务表／§九 门禁与中间态）。
> **实施触发**：等待人工"开始实施"指令；按 §八 批次 A→B→C→D 主线串行，E/F 穿插；实施 agent 不得二次决策——发现本文件内部矛盾或锚点漂移超出核对容差时，先报告人工再动。
> **前置条件：M5 已完成**（含 M5-a 物理名 t_{uid} 机制、M5-b 三态锚点插入）。实施证据（2026-09-24 核验）：models.py `def insert_step` L399、page_operation_config.py `def _resolve_insert_index` L452、测试三新类 PhysicalNameUidTest（test_models_data L384）/InsertStepTest（L427）/TUidEngineTest（test_engine_overwrite L109）、R5 实跑 88 用例全绿、AGENTS 锚点 R5。**本方案的 88 基线（=M5 前 79＋M5 新增 9）与全部行号锚点均以 M5 实施后版本为准**。
> 范围声明：**功能函数优化批 5 项不在本方案**（P1-1 算子单测、P1-2 失败路径用例、P1-6 返回值契约、P2-1 默认参数声明式化、P2-2 分发字段驱动化——人工另行立项）；其余 **37 项全部覆盖**（P0×3＋P1×8＋P2×12＋P3×14）。
> 本次修订：前置条件澄清 + 6 项瑕疵修复 + 方案具体化，详见 §十一/§十二。上次修订：定稿（D1-D10 裁定）＋施工图级具体化。工作量 S/M/L（S=单点小改，M=跨文件或含新用例，L=新模块或新文档）。

---

## 一、一页总览

**一句话：37 个问题分 6 批修——先止血（数据错）、再教程序说人话、再让交付可信、再防丢防卡防垃圾、再让账实相符、最后清仓库；10 个决定已全部裁定（见第四节）。**

| 批次 | 人话名称 | 解决什么 | 覆盖问题 | 量级 |
|---|---|---|---|---|
| A | 先止血：数据别写错 | 一种操作会把数据悄悄写错地方；失败也报"成功"；点一下表单悄悄丢配置 | P0-1、P2-5、P3-9、P3-10 | 中小 |
| B | 教程序说人话 | 出错时文员看不懂、被指向已删除的界面 | P0-2、P1-8、P2-14 | 中 |
| C | 交付可信 | 安装包说不清版本；重新打包会删用户数据 | P0-3、P1-9、P1-10、P3-14 | 中 |
| D | 防丢·防卡·防垃圾 | 无超时、临时文件只进不出、大数据卡死、并发收尾乱 | P1-4、P1-5、P1-7、P2-4、P2-9、P2-10、P2-12、P2-13、P3-6 | 大 |
| E | 账实相符 | 文档与实际漂移、校验纯人工、无用户手册、门禁有假绿 | P1-3、P1-11、P2-3、P2-6、P2-7、P2-8、P2-11、P3-4、P3-7、P3-8 | 中 |
| F | 仓库大扫除 | 从没被用过的接口、重复代码、注释与代码不符 | P3-1~P3-5、P3-11~P3-13 | 小 |

顺序逻辑（人话）：A 最急——数据错了别的都白搭；B 其次——用户看不见出路等于不可用；C 在需要发新包前完成即可；D 在数据量上来前完成；E、F 随时可穿插。A→B→C→D 为主线，E/F 并行。

---

## 二、逐项修法（裁定级原文，保留；施工级细化见 §七）

### 批次 A：先止血（数据正确性与诚实报告）

| 问题（人话） | 怎么修（人话） | 技术要点（落点） | 量级 |
|---|---|---|---|
| **P0-1** 把结果写回"中间表"时，数据写到错误位置还不报错 | 程序在生成执行文件时，已经知道每张中间表的真实名字（M5-a 成果）；写回目标若是中间表，直接查这张对照表填真名。修一处即可，引擎不动。**被否方案（D1 裁定采①）**：界面上禁止把中间表选作写回目标（更简单，但砍掉一种用法） | models.py to_dict 的 cp 构造处（L696 `sqlite_of.get(target) or target`）：业务口径先建 {派生表号→t_{uid}} 映射，miss 时查它再回退；新增回归用例（覆盖目标=派生表，断言 cp 步 output_table==该表 t_{uid} 且内容真被覆盖） | S＋用例 |
| **P3-9** 跳过降级仍报"正常完成"；报告"已输出文件"在执行前就收集，失败也照列 | 成功与否以真实结果为准：有步骤被跳过就标"部分完成（有跳过）"；输出清单改为执行完成后按实际产物收集 | worker.py 消费 result["success"]（当前只取 status）；models.py collect_file_stats（L921-935）调用时机移到执行后（main_window._on_workflow_finished） | S |
| **P3-10** 覆盖模式下中间表与写回结果并列显示，用户以为"多出一张表" | 报告页与画布对中间表加"（中间结果）"标注，或折叠不显示 | page_report.py L85-95 输出映射表加标注列；口径按 D9 裁定（tooltip 保留、报告页折叠进"技术详情"） | S |
| **P2-5** 切换步骤时表单"整体替换"参数：外部文件带来的"或"逻辑、注入到其他功能的覆盖模式，一经点击就静默丢失或降级（真机日志 2 分钟触发 10 次） | 表单收拢改"只更新自己管的字段"：读当前控件值合并进参数，不整包覆盖；管不到的字段原样保留 | page_operation_config.py L659-696 _harvest_current_form 改增量合并（logic 不再硬编码 AND；output_mode 仅表单持有该控件时更新）；配套用例：带 logic=OR 的模型经"点开→切走→切回"后参数不丢 | M |

批次验证（怎么算修好）：新增"覆盖派生表"专项用例绿；表单收拢参数不丢用例绿（logic=OR 往返保持）；88 项基线零回归；手工构造跳过场景，报告显示"部分完成"。

### 批次 B：教程序说人话（错误话术链）

| 问题（人话） | 怎么修（人话） | 技术要点（落点） | 量级 |
|---|---|---|---|
| **P0-2** 出错时：提示指向已删除的界面；报错是内部代号原文；报告页暴露内部表名和完整路径 | 建一张"错误翻译对照表"：每类错误对应一句人话＋一句"下一步怎么办"。所有失败提示先过这张表再给用户；查不到的错误统一说"程序遇到意外问题，请把日志发给管理员"并给出日志文件位置。报告页把内部代号折叠进"技术详情"按钮 | 新增 gui/error_messages.py（异常类型/错误关键词→人话映射）；step_executor.py L303-312 fail() 出口、main_window.py L441-446 弹窗、page_report.py L85-95、sql_safety.py L175-179（内部表名清单只进日志不进 message）；文案过 architecture §8.4 禁用词表自查 | M |
| **P1-8** 文件被 Excel 占用、磁盘满、数据库损坏时，用户看到裸异常文本 | 把这三类高发错误纳入翻译表："文件正被 Excel 打开，请关闭后重试"这类可自救话术；导入入口补齐异常捕获 | main_window.py L251-253 捕获面扩为 (ValueError, FileNotFoundError, PermissionError, OSError, sqlite3.Error)；样板已在仓（page_input_selection.py L391 正确捕获 PermissionError，统一推广） | S |
| **P2-14** "失败就停/跳过/重试"引擎支持但界面没有入口；重试用完后行为没定义 | 按"文员不需要技术细节"原则**不新增界面入口**，保持默认"失败就停"；把重试用完后的行为明确定义为"算失败"（当前是静默继续）；语义写进用户手册 | executor.py L132-140 else 分支改为走失败路径；文档口径同步 | S |

批次验证：文案评审清单——人工通读全部用户可见提示（弹窗/气泡/报告页/tooltip），逐条判"文员能否看懂并自救"；异常注入用例（占用文件/坏路径）话术断言。

### 批次 C：交付可信（打包与版本）

| 问题（人话） | 怎么修（人话） | 技术要点（落点） | 量级 |
|---|---|---|---|
| **P0-3** 安装包说不清对应哪版代码；文档说"包已失效"，构建记录却显示 09-24 已构建并真机跑过 | 打包时自动生成"身份证"：把源码指纹（全部代码文件的哈希汇总＋构建时 git 版本号若有）写进构建信息文件；界面"关于"里也显示。文档三处口径随 D10 人工确认结果一次性统一 | build.bat 增指纹注入步骤（新脚本 tools/make_fingerprint.py，D5 裁定双指纹，§7.3 C1）；BUILD_INFO.txt 增 SOURCE_HASH/GIT_REV 字段；build-guide §1.10 判据增"指纹比对"；backlog W-20 与 AGENTS §8 随确认结果更新 | M |
| **P1-9** 重新打包先删整个输出目录：用户配置、日志连带丢；构建失败连旧包都没了 | 改"先在临时目录构建，成功后才替换正式包"；替换前把旧包改名留存（.bak）；打包前先跑测试，不过就不打。用户数据四目录保护红线（D3 裁定：便携约定，paths.py 不变） | build.bat L149-159 rmdir 改临时目录方案＋原子替换（§7.3 C2 八步伪代码）；打包前置 discover＋smoke 门禁（D4 裁定①强制）；paths.py L27-39 frozen 数据目录策略不变（D3 裁定②） | M |
| **P1-10** 安装包只能放在可写目录，装到受保护目录直接启动失败 | 按 D3 裁定②执行：明确"便携版"约定（只放可写位置，写进部署指南），paths.py 数据目录策略不变；同时把启动失败提示改人话并给安置指引（被否方案：AppData 迁移／现状仅改提示，见 §四 D3） | app.py L78-93 自检项 3 提示人话化（§7.3 C3）；部署指南（批次 E）同步 | M |
| **P3-14** 依赖清单里有 2 个早已不用的库，且无版本锁定 | 清掉死依赖；把当前环境的实际版本固化成锁定文件，构建环境照单安装 | requirements.txt 删 python-docx/python-pptx；新增 requirements.lock（pip freeze 于 CPS-GPES_RPA-py311）；build-guide 同步 | S |

批次验证：按新流程完整构建一次——指纹可查、旧包 .bak 在位、构建失败注入测试（临时改坏一处再打包，应被门禁拦下且旧包无损）。

### 批次 D：防丢·防卡·防垃圾（运行健壮与规模）

| 问题（人话） | 怎么修（人话） | 技术要点（落点） | 量级 |
|---|---|---|---|
| **P1-4/P2-12** 无超时保护：大表卡住时"终止"按钮无效；数据库两个连接抢写立即报错 | 三层：①数据库设置"排队等待"（冲突时等几秒而非立刻报错，先行）；②每步执行计时告警（超上限记日志并给话术，不改成败判定——D2 裁定施工图口径，硬杀受单连接架构约束不做）；③长步骤内部支持中断（导出/导入循环里加取消检查） | ①session_db.py L74-77 加 PRAGMA busy_timeout=5000；②executor 步骤循环加计时（阈值已裁定：默认 600 秒、step_timeout_sec 可配、0=停用，见 §四 D2/§7.4 D1-4）；③exporter fetchmany 循环、table_importer 分块循环内查 cancel 标志 | M |
| **P1-5** 上一轮的慢任务会把用户"抢"回旧报告页；异常退出后数据库文件残留 | 换轮次时先处理旧任务：等待收尾或明确切断它的回调（信号断开＋代际号，撤销条已有同款先例 F3 可复用）；启动时扫描并清理上次异常残留的会话库 | main_window.py L197-211（wait 返回值消费＋finished 信号按代际断开）；启动自检或 _new_round 增陈旧 session_*.db 扫描删除（含 -wal/-shm） | M |
| **P1-7** 临时文件只进不出（实测已堆 28 个）；没有磁盘空间预检 | 临时副本"用完即清"：会话结束/程序退出清理本轮副本，启动清理超龄残留；导入大文件前先看磁盘够不够（源文件大小×安全倍数），不够就人话提示 | page_input_selection.py L39 TEMP_DIR 生命周期管理（会话级清单＋清理钩子）；导入前 shutil.disk_usage 预检；现存 28 文件首轮人工确认后清理 | S |
| **P2-4** 弃用的中间表不物理删除，长流程占内存 | 工作流正常结束后，把弃用闭包表统一物理删除（函数早已写好、只是没人调用）；不在中途删，防止后续步骤还要读 | executor.py 收尾处调用 ops/table_lifecycle.delete_table（零生产调用→接入）；时机决策已内嵌（结束后统一删） | S |
| **P2-9** 步骤一多界面就卡：每次点击整图重画，且画法本身是"步数×步数"的算法 | 三步走：①先修一处明显的算法疏漏（循环内反复全表扫描提到循环外，同行代码他处已是正确写法）；②高频操作的重画做合并（连续点击只画最后一次）；③步骤数超过警戒值时提示用户"流程较大，界面响应变慢属预期"并关闭自动缩放重置。深度优化（虚拟化/增量渲染）不做（业务规模输入证明需要后另行立项，D7 裁定） | ①node_graph.py L761-762 missing 计算外提；②_refresh_graph 13 个调用点收口经 QTimer 合并（表单收拢处已有正确节流样板 L681-683）；③阈值警戒（D7 裁定：150 步，常量 CANVAS_WARN_STEPS）；fit_to_scene 视口重置改"仅新增时" | M |
| **P2-10** 数据库从不建索引：表关联、分组统计在百万行级会到分钟级 | 需要按列匹配的操作用列，先建索引再干活；会话库即用即抛，索引无持久化负担 | mapping_matcher JOIN 前对 match 列 CREATE INDEX；aggregator GROUP BY 列同理；filter_dedup 去重分区列评估；门槛已裁定：行数超 50,000 才建（INDEX_ROW_THRESHOLD，§7.4 D6；小表建索引反而多花一步） | M |
| **P2-13** 外部手写的执行文件能让程序读任意路径、覆盖任意 Excel | 给"程序化调用"路径也装上和模板管理同款的门卫：文件路径必须在允许的目录范围内，越界拒绝并报错。界面链路本就安全，不动 | executor.py L45-60 source.file 与 exporter.py L62-66 output_path 增加包含性校验；样板=user_template_manager.py L492-531（resolve＋relative_to 穿越防护）；允许目录集已裁定（§7.4 D7）：导入=temp/input_selection 白名单＋register_import_root 显式扩展；导出=拒绝副本区路径、同名覆盖保留 | S |
| **P3-6** 批量插入逐行执行；导入一张表要打开同一个文件 3 次 | 批量插入改"一次提交多行"；打开一次文件把预览、校验、读取一起做完 | table_content.py L58-73 executemany 化；table_importer.py L55-64 与 excel_preprocessor 合并扫描（sheet 信息一次取得传递复用） | S |

批次验证：构造 200 步流程与百万行表各一次人工实测（响应与耗时记录进 REPORT）；垃圾目录清零断言（跑一轮后 temp 无残留）；拔线测试（执行中强杀进程→重启后陈旧库被清）。

### 批次 E：账实相符（治理、文档与门禁）

| 问题（人话） | 怎么修（人话） | 技术要点（落点） | 量级 |
|---|---|---|---|
| **P1-11** 文档校验纯靠人工自觉：无脚本、无留痕，已产生 6 处索引日期漂移和 2 处正文过时 | 写一个"文档体检脚本"：一键查三件事——链接都通吗、索引日期和文档头一致吗、约束文件容量达标吗；每次改文档后必跑，结果落文件留痕。同时把已发现的过时处一次改齐 | 新增 tools/doc_verify.py（链接可达/INDEX↔frontmatter 日期/AGENTS 容量三口径）；architecture.md §8.2 列名与弹窗描述、§8.3 信号表按实现修订；docs/INDEX.md 6 处日期同步；doc-governance §4 增"脚本化执行"条目 | M |
| **P1-3** 文件版本号写了但没人检查，未来新格式文件会被静默按旧格式执行 | 解析时核对版本号：认识的放行，不认识的人话拒绝（"该文件由更新版本生成，请升级程序"） | parser.py L116-120 增 schema_version 白名单判定（当前={"3.1"}）；拒绝路径进翻译表（批次 B 基建） | S |
| **P2-6** 解析对未知内容一声不吭；"保留数据库"开关是死字段 | 白名单丢弃参数键时记日志（便于排查"参数怎么没生效"）；"保留数据库"开关真接线：置真时会话库保留供排查（默认仍删） | step_executor.py L195 丢弃处 logger.debug；main_window._close_session 消费 global.keep_db（当前硬编码 False） | S |
| **P2-3** 表的"状态账本"记了一套，画布显示另算一套，两本账不互通 | 先加一道"对账测试"：每次回归自动核对两本账一致（成本低、防漂移）；是否合并成一本账，等对账测试跑稳后再裁定 | tests/ 新增一致性用例（reconcile 结果 vs graph_edges 派生态逐表比对） | S |
| **P2-11** 门禁里有 2 处"永远算通过"的假断言；3 项 fitness function 的唯一载体放在"无约束力"的临时目录 | 假断言改真断言；冒烟脚本从临时目录迁入正式工具目录，门禁地位写进文档；临时目录治理条款与现实的矛盾一并修订 | smoke_m1m3.py L150（`or True` 去除）/L176（补真条件）；双 smoke 迁 rpa_engine/tools/smoke/（D8 决定）；doc-governance §8 条 2 表述按现实修订（走 §4 校验） | M |
| **P2-8** 没有用户手册、没有部署指南——面向文员的交付文档为零 | 写两份薄文档：《用户使用手册》（四步走图文＋常见错误自救表——直接复用批次 B 翻译表内容）＋《部署指南》（一页：放哪、怎么装、怎么更新、出问题看哪个日志） | docs/ 新增两文件＋INDEX 登记＋README 导航同步；手册文案过禁用词表 | L |
| **P2-7** 高分屏无适配；窗口不能缩放，小屏办公机底栏易被裁 | 开启系统缩放适配；给窗口设最小尺寸并允许拖拉缩放；字体改随系统设置 | app.py L279 前加 AA_EnableHighDpiScaling/AA_UseHighDpiPixmaps；main_window frameless 加 QSizeGrip＋setMinimumSize；styles.py 字号改 pointSize | S |
| **P3-4** 注释与代码不符 3 处（预览行数写 20 实际 50、自检写 5 项实际 6 项、自称转发层实为重复实现） | 三处注释改齐；其中"重复实现"随批次 F 统一 | page_input_selection.py L598、app.py L4、registry.py L6-7 | S |
| **P3-7** 第一阶段增删/换文件后，表的编号按位置重排，旧步骤的引用会静默指向别的表 | 重排发生时给出提示："第 N 步引用的表已变化，请检查"；深度方案（按稳定身份编号）影响面大，先不做 | main_window.py L219-256 确认导入后比对旧编号映射，变化时列出受影响步骤（_check_step_columns 已有列级拦截，补表级提示） | M |
| **P3-8** 上次配置只在退出时保存，程序崩溃会丢现场 | 关键变更（加删步骤、改参数确认）后即写上次配置；崩溃后重启能恢复 | last_config 写点从退出单一时机改为防抖即时写（复用批次 D 的合并定时器模式） | S |

批次验证：文档体检脚本一键全绿；对账测试进 88 基线；手册/指南人工通读（文员视角评审）；高分屏真机截图核对（人工复核项，列 REPORT 真机清单）。

### 批次 F：仓库大扫除（与既有 move_step 清理轮合并）

| 问题（人话） | 怎么修（人话） | 技术要点（落点） | 量级 |
|---|---|---|---|
| **P3-1** 调序函数留着没删（已有裁定挂账） | 随本批执行既有裁定 | models.py move_step（H2：下一清理轮删除） | S |
| **P3-2** 10 个从没被调用过的对外接口仍挂在"出口清单"，其中一个是能执行任意查询语句的口子 | 出口清单收缩到真实使用的接口；危险口子从对外清单除名（施工图裁定：除名＋保留本体标内部，§7.6 F2） | ops/__init__.py L102-123 __all__ 收缩；execute_sql 等逐项核销（delete_table 保留，D4 已接生产调用） | S |
| **P3-3** 两处同样的函数各写了一份，其中一份自称"只是转发"名不副实 | 保留一份真实现，另一份改成真转发 | engine/registry.py L15-23 改为从 ops/step_executor 再导出 | S |
| **P3-5** 操作符白名单存了两份，没有互相核对 | 单一来源：界面那份改为引用引擎那份；启动自检加一道包含关系守卫（§7.6 F4 裁定两者都做） | forms.py L29 `_OPS` 引用 sql_safety.SUPPORTED_OPERATORS；app.py L160 增包含关系守卫 | S |
| **P3-11** 撞号检测有三个入口，第三个只有测试在用 | 测试改用生产入口，冗余门面删除 | graph_edges.py L315-321 及其测试引用 | S |
| **P3-12** 无持续集成、打包不跑测试 | 持续集成超出"基本完善"边界，维持人工门禁；"打包前跑测试"已并入批次 C | 说明项，不立项 | — |
| **P3-13** 三个小加固：建表时类型名未过白名单；模糊匹配的通配符未转义；运行配置文件单槽双开互覆 | 类型名过白名单再拼；模糊匹配加转义符；配置文件加实例标识 | table_schema.py L162-169；sql_safety.py L152 加 ESCAPE；main_window.py L365-370 | S |

批次验证：grep 死代码出口清单 0 残留；全量回归绿；双开实例互不覆盖实测。

---

## 三、与"功能函数优化"批的衔接

**结论：两批共享两块基建，先做本方案的批次 A/B，功能函数批随后收益最大。**

1. **错误翻译层（批次 B 产出）**是功能函数"错误提示人话化"的直接地基——功能批只需往对照表里添各自条目。
2. **假成功的显示面**（批次 A 的 P3-9"部分完成"口径）先立好；功能批定义各算子返回值契约（P1-6）后按此口径上报，两批在"报告诚实"处汇合。
3. 排除清单（本方案不碰）：P1-1、P1-2、P1-6、P2-1、P2-2。

---

## 四、人工裁定记录（D1-D10 已裁定，无待决项）

**裁定：D1-D10 全部采用首选（2026-09-24 人工批准，"所有决策点全部采用推荐"）。** 选项原文保留供追溯：

| # | 决定什么 | 选项 | 裁定 |
|---|---|---|---|
| D1 | P0-1 修法 | ①导出时解析中间表真名（保留能力）②界面禁选中间表（更简单） | **已裁定：采①**（单点修、引擎零改动、与 M5-a 机制同源；②砍掉一种合法用法） |
| D2 | 超时阈值与中断粒度 | 数值需业务规模输入（典型表行数/最大流程步数） | **已裁定：按首选**——busy_timeout=5000ms 即落；步骤超时默认 600s 先行、经 global 配置键 step_timeout_sec 可调（0=停用告警）。施工图口径（§7.4 D1）：受单连接架构约束，超时实现为"循环内中断＋事后计时告警"，硬杀线程不做（说明项） |
| D3 | 安装包用户数据放哪 | ①系统用户目录（AppData）②便携版约定（只放可写位置）③现状+失败提示人话化 | **已裁定：采②**（改动最小、符合单机办公场景）——paths.py 数据目录策略不变；"必须放可写目录"写进部署指南；自检项 3 失败提示人话化（含安置指引） |
| D4 | 打包前是否强制跑测试 | ①强制（不过不打）②提示可跳过 | **已裁定：采①**——门禁失败即中止打包；跳过仅限显式 `--skip-tests` 参数且在 BUILD_INFO 记录"跳过测试"标记 |
| D5 | 源码指纹方式 | ①文件哈希汇总 ②git 版本号 ③双份 | **已裁定：采③**——恒记文件哈希汇总（rpa_engine/**/*.py 排序 sha256 再汇总）；git 可用时并记 rev-parse HEAD，不可用记 N/A |
| D6 | 失败策略要不要界面入口 | ①暴露（停止/跳过/重试）②不暴露，默认停止 | **已裁定：采②**——不新增界面入口；重试耗尽=失败（修静默继续）；"失败即停止"语义写用户手册 |
| D7 | 画布规模保护策略 | ①算法疏漏修正+刷新合并+警戒提示（渐进）②直接上虚拟化/增量渲染（重做） | **已裁定：采①**——警戒阈值默认 150 步（模块常量 CANVAS_WARN_STEPS，可调）；虚拟化/增量渲染不做（业务规模输入证明需要后另行立项） |
| D8 | 冒烟脚本门禁载体 | ①迁入 rpa_engine/tools/smoke/ 正式化 ②维持 _temp 豁免并修订治理条款 | **已裁定：采①**——双 smoke 复制迁入 rpa_engine/tools/smoke/（路径常量适配），验证通过后删除 _temp/DAG-rebuild/ 原件（单一事实源；实施前核对原件未被 SampleCode 引用）；doc-governance §8 条 2 与门禁命令引用同步修订 |
| D9 | 画布 tooltip 物理表名去留 | ①保留（悬停层，属可见性成果）②随报告页一起折叠 | **已裁定：采①**——tooltip 保留；报告页物理名映射与绝对路径折叠进"技术详情"区 |
| D10 | 09-24 构建的包是否即交付基准 | ①是→更新三处文档并补指纹 ②否→按 W-20 重建 | **已裁定：按首选路径执行**——批次 C 开工时人工确认（评估报告 §七 第 1 条）；两种确认结果下 C1/C2 修法不变，仅文档更新表述不同（①补指纹+销 W-20；②重建走新流程自动生成指纹） |

---

## 五、每批的完成判据（人话）

| 批次 | 修好的标志 |
|---|---|
| A | "覆盖中间表"专项用例绿；跳过场景报告如实显示；88 基线零回归 |
| B | 人工通读全部用户可见提示：每条都"看得懂＋知道下一步"；异常注入用例话术断言绿 |
| C | 按新流程完整构建一次：身份证可查、旧包留存、测试不过打不出包 |
| D | 200 步/百万行人工实测记录在案；一轮跑完临时目录零残留；强杀重启后无孤儿库 |
| E | 文档体检脚本一键全绿并留痕；对账测试进基线；手册/指南过人工通读 |
| F | 出口清单死接口 0 残留；全量回归绿；双开实测互不干扰 |

全程统一门禁（每批收尾必跑）：unittest discover 全绿＋双冒烟 ALL_OK＋启动自检 6/6＋FF1-FF5＋AGENTS 容量三口径（涉文档批次）。

**基线口径说明**：文中"88 基线"＝M5 实施后基线（79＋M5 新增 9，2026-09-24 R5 实跑，见文件头前置条件声明）；本方案各批新增用例后基线数随之增长，以最近一次全量实跑数为准。

---

## 六、证据锚点与现场核对命令表（施工定位用）

**纪律**：**本表行号基于 M5 实施后版本**（M5 已完成，见文件头前置条件声明）；记录锚点为 2026-09-24 评估轮/施工图取证轮实测；实施 agent 动手前逐条跑核对命令，锚点漂移以符号定位为准。基线＝88 用例（R5）。

| 锚点 | 文件 | 记录锚点 | 现场核对命令 |
|---|---|---|---|
| to_dict 双口径（output_table 4 行分支） | rpa_engine/gui/models.py | L699-706 | `grep -n 't_{s.uid}' rpa_engine/gui/models.py` |
| sqlite_of 构建行 | 同上 | L668 区域 | `grep -n "sqlite_of = " rpa_engine/gui/models.py` |
| cp 步构造块（P0-1 改点） | 同上 | L717-735 | `grep -n "写回原表" rpa_engine/gui/models.py` |
| _harvest_current_form（P2-5 改点） | rpa_engine/gui/page_operation_config.py | L658-695（L677 整包替换） | `grep -n "_harvest_current_form" rpa_engine/gui/page_operation_config.py` |
| worker 信号定义（P3-9 改点） | rpa_engine/gui/worker.py | L26-29（workflow_finished 3 参） | `grep -n "workflow_finished" rpa_engine/gui/worker.py` |
| worker.run 结果消费段 | 同上 | L90-97/L118-119 | `grep -n 'result\["status"\]' rpa_engine/gui/worker.py` |
| _on_workflow_finished（弹窗+切页+回写） | rpa_engine/gui/main_window.py | L426-446 | `grep -n "_on_workflow_finished" rpa_engine/gui/main_window.py` |
| _on_step_failed（气泡 message） | 同上 | L418-424 | `grep -n "_on_step_failed" rpa_engine/gui/main_window.py` |
| 旧 worker 防御段（P1-5 改点） | 同上 | L196-210 | `grep -n "worker.wait" rpa_engine/gui/main_window.py` |
| _new_round/_back_to_input_selection | 同上 | L312-343 | `grep -n "_new_round\|_back_to_input" rpa_engine/gui/main_window.py` |
| 导入异常面（P1-8 改点） | 同上 | L251-253 | `grep -n "FileNotFoundError" rpa_engine/gui/main_window.py` |
| last_config 写点（P3-8） | 同上 | 退出时单一写点 | `grep -n "last_config" rpa_engine/gui/main_window.py` |
| 运行配置单槽（P3-13） | 同上 | L365-370 | `grep -n "gui_workflow.json" rpa_engine/gui/main_window.py` |
| collect_file_stats 调用点（P3-9） | gui/models.py＋调用侧 | L921-935 | `grep -rn "collect_file_stats" rpa_engine/gui/` |
| executor 步骤循环（超时/取消/清理接入） | rpa_engine/engine/executor.py | L111-140 | `grep -n "取消检查点" rpa_engine/engine/executor.py` |
| ExecutionError 捕获段（P1-4 cancelled 归并） | 同上 | L142-148 | `grep -n "except ExecutionError" rpa_engine/engine/executor.py` |
| _execute_with_retry（P2-14 改点） | 同上 | L170-199 | `grep -n "_execute_with_retry" rpa_engine/engine/executor.py` |
| ensure_input_tables（P2-13 改点） | 同上 | L45-60 | `grep -n "def ensure_input_tables" rpa_engine/engine/executor.py` |
| execute_workflow 返回段（P2-4 接入点） | 同上 | L159-167 | `grep -n '"output_tables": output_tables' rpa_engine/engine/executor.py` |
| SessionDB PRAGMA 区（busy_timeout） | rpa_engine/ops/session_db.py | L74-77 | `grep -n "journal_mode" rpa_engine/ops/session_db.py` |
| exporter fetchmany 循环（循环内取消） | rpa_engine/ops/exporter.py | L82-94 | `grep -n "fetchmany" rpa_engine/ops/exporter.py` |
| table_importer 导入链（并扫/取消） | rpa_engine/ops/table_importer.py | L55-64 | `grep -n "def import_excel_table" rpa_engine/ops/table_importer.py` |
| parser schema_version 段（P1-3） | rpa_engine/engine/parser.py | L115-122 | `grep -n "schema_version" rpa_engine/engine/parser.py` |
| 白名单丢弃处（P2-6 日志） | rpa_engine/ops/step_executor.py | L195 区域 | `grep -n "pop" rpa_engine/ops/step_executor.py` |
| fail() 原始错误出口 | 同上 | L303-312 | `grep -n "def fail" rpa_engine/ops/step_executor.py` |
| sql_safety 错误文本（表名清单外移） | rpa_engine/ops/sql_safety.py | L175-179 | `grep -n "当前可用表" rpa_engine/ops/sql_safety.py` |
| LIKE 无 ESCAPE（P3-13） | 同上 | L152 | `grep -n "LIKE" rpa_engine/ops/sql_safety.py` |
| col_type 入 DDL（P3-13） | rpa_engine/ops/table_schema.py | L162-169 | `grep -n "col_type" rpa_engine/ops/table_schema.py` |
| rename/dtype 返回值（P3-9 联动说明） | 同上 | L96-102 | `grep -n "return False" rpa_engine/ops/table_schema.py` |
| delete_table（P2-4 接入对象） | rpa_engine/ops/table_lifecycle.py | L68-92 | `grep -n "def delete_table" rpa_engine/ops/table_lifecycle.py` |
| insert_rows 逐行（P3-6） | rpa_engine/ops/table_content.py | L58-73 | `grep -n "def insert_rows" rpa_engine/ops/table_content.py` |
| JOIN 无索引（P2-10） | rpa_engine/ops/mapping_matcher.py | L82-86/L183-209 | `grep -n "JOIN" rpa_engine/ops/mapping_matcher.py` |
| GROUP BY 无索引（P2-10） | rpa_engine/ops/aggregator.py | L117-134 | `grep -n "GROUP BY" rpa_engine/ops/aggregator.py` |
| TEMP_DIR 生命周期（P1-7） | rpa_engine/gui/page_input_selection.py | L39/L315/L378 | `grep -n "TEMP_DIR" rpa_engine/gui/page_input_selection.py` |
| 编号重排段（P3-7） | rpa_engine/gui/main_window.py | L219-256 | `grep -n "_on_confirm_import" rpa_engine/gui/main_window.py` |
| 自检项 3（P1-10 提示） | rpa_engine/gui/app.py | L78-93 | `grep -n "目录可写" rpa_engine/gui/app.py` |
| QApplication 构造（P2-7） | 同上 | L279 | `grep -n "QApplication(" rpa_engine/gui/app.py` |
| 守卫②（P3-5 增守卫位） | 同上 | L159-165 | `grep -n "default_params" rpa_engine/gui/app.py` |
| rebuild missing 漏改点（P2-9①） | rpa_engine/gui/node_graph.py | L761-762 | `grep -n "missing = " rpa_engine/gui/node_graph.py` |
| fit_to_scene（P2-9③） | 同上 | L1153-1163 区域 | `grep -n "def fit_to_scene" rpa_engine/gui/node_graph.py` |
| _refresh_graph 调用点 13 处（P2-9②） | rpa_engine/gui/page_operation_config.py | L132/494/512/531/576/630/683/723/810/915/1166/1264 | `grep -n "_refresh_graph()" rpa_engine/gui/page_operation_config.py` |
| 报告页物理名段（P0-2/P3-10/D9） | rpa_engine/gui/page_report.py | L84-96 | `grep -n "物理表名" rpa_engine/gui/page_report.py` |
| build_edges 双层扫（P2-9 关联） | rpa_engine/gui/graph_edges.py | L284-293 | `grep -n "def build_edges" rpa_engine/gui/graph_edges.py` |
| 冗余门面（P3-11） | 同上 | L315-321 | `grep -n "detect_table_id_collisions" rpa_engine/gui/graph_edges.py` |
| _OPS 白名单（P3-5） | rpa_engine/gui/forms.py | L28-29 | `grep -n "_OPS" rpa_engine/gui/forms.py` |
| __all__ 死出口（P3-2） | rpa_engine/ops/__init__.py | L102-123 | `grep -n "__all__" rpa_engine/ops/__init__.py` |
| registry 双活副本（P3-3） | rpa_engine/engine/registry.py | L15-23 | `grep -n "def get_op_func" rpa_engine/engine/registry.py rpa_engine/ops/step_executor.py` |
| move_step（P3-1/F1） | rpa_engine/gui/models.py | L479-484 | `grep -n "def move_step" rpa_engine/gui/models.py` |
| 恒真断言 2 处（P2-11） | _temp/DAG-rebuild/smoke_m1m3.py（迁移后 rpa_engine/tools/smoke/） | L150/L176 | `grep -n "or True" <smoke路径>` |
| build.bat 删目录段（P1-9） | build.bat | L112-159（L152-153 rmdir） | `findstr /n "rmdir" build.bat` |
| BUILD_INFO（P0-3） | build/BUILD_INFO.txt | 全文 | 直接读取 |
| paths frozen 策略（D3） | rpa_engine/paths.py | L27-39 | `grep -n "ENGINE_ROOT" rpa_engine/paths.py` |
| requirements 死依赖（P3-14） | requirements.txt | L9/L18 | `findstr /n "docx pptx" requirements.txt` |

---

## 七、施工细化（按批次；每项＝锚点→前后对照→用例）

### 7.1 批次 A 施工细化

**A1（P0-1）覆盖派生表写真名** — 落点 models.py to_dict（D1 裁定①）
- A1-1 派生表物理名映射：在 to_dict 业务口径分支、uid 重复防御之后、`for i, s in enumerate(self.steps)` 循环之前，新增一行：
  ```python
  derived_phys = {st.output_table_id: f"t_{st.uid}"
                  for st in self.steps if st.output_table_id}
  ```
  （编辑态口径不消费该映射，构建无害；位置必须在 uid 防御之后——用修正后的 uid。）
- A1-2 cp 构造行改三级回退：L725 现状 `target_phys = sqlite_of.get(s.target_table_id) or s.target_table_id` → 改为：
  ```python
  target_phys = (sqlite_of.get(s.target_table_id)
                 or derived_phys.get(s.target_table_id)
                 or s.target_table_id)
  ```
- A1-3 模型级用例（tests/test_models_data.py 新类 OverwriteDerivedTargetTest）：夹具＝make_model()＋s1=add_step("filter")（output_table_id="T101"）＋s2=add_step("dedup")，s2.target_table_id="T101"，s2.params 含 output_mode="overwrite_target" 与 dedup 必填键；操作＝d=m.to_dict()；断言＝①len(d["steps"])==3（s1、s2、s2_cp）②s2 父步 params["output_table"]==f"t_{s2.uid}"③**s2_cp params["output_table"]==f"t_{s1.uid}"（≠"T101"）**④编辑态口径（include_deprecated=True）无 _cp 步（回归）。
- A1-4 执行级用例（tests/test_engine_overwrite.py TUidEngineTest 追加 test_overwrite_derived_target_executes）：内存 SQLite 建输入表 t1；模型＝filter(T1→T101)＋dedup(target=T101, overwrite)；to_dict→临时 JSON→parse→execute；断言＝①status completed②`SELECT name FROM sqlite_master WHERE name='T101'` 空（无游离逻辑名表）③t_{s1.uid} 存在且内容＝dedup 结果④t_{s2.uid} 存在。

**A2（P3-9）诚实报告** — 落点 worker.py＋main_window.py＋page_report.py
- A2-1 worker 信号扩参：L29 `workflow_finished = pyqtSignal(str, float, dict)` → `pyqtSignal(str, float, dict, bool)`（第 4 参 success）；run() 内 L63 区域初始化 `success = False`，L96 后加 `success = bool(result.get("success", False))`；L118 emit 改 4 参 `self.workflow_finished.emit(status, time.time() - t_start, out_tables, success)`。
- A2-2 main_window._on_workflow_finished 签名加 `success: bool = True`（末位默认参，兼容旧连接）；L432 fill 前计算显示状态：
  ```python
  display_status = status
  if status == "completed" and not success:
      display_status = "completed_partial"
  ```
  fill 第一参传 display_status；同时**输出清单后移**：collect_file_stats 调用从执行前位置（现场核对 `grep -n "collect_file_stats" rpa_engine/gui/main_window.py`）移至本函数 fill 之前，且仅 `status in ("completed",)` 时收集，failed/cancelled 传空列表。
- A2-3 page_report.fill 状态文案映射增 `"completed_partial": "部分完成（有步骤被跳过）"`（现场核对映射表位置 `grep -n "正常完成" rpa_engine/gui/page_report.py`）。
- A2-4 用例：执行级（test_engine_overwrite 或新文件）——构造必失败步（filter 条件列不存在）＋on_error="skip"（load_from_dict 外部 JSON 直构，GUI 无 skip 入口为 D6 裁定）：断言 result["status"]=="completed" 且 result["success"] is False；信号层由 smoke 断言（A2-5）。
- A2-5 smoke 联动（smoke_m1m3 报告页场景处）：断言 page_report.fill("completed_partial", ...) 后状态标签文本含"部分完成"。

**A3（P3-10）中间表标注** — 落点 page_report.py L84-96：输出映射表增加"类型"列——`output_tables` 中该表号对应步骤若为覆盖链父步（判定：模型 steps 的 output_mode=="overwrite_target"；经 fill 新增关键词参数 overwrite_ids: set = None 传入，调用侧 main_window._on_workflow_finished 组装），显示"中间结果（已写回）"；主表显示"输出"。折叠机制随 B1-4"技术详情"区实现（D9），本任务只加标注数据。

**A4（P2-5）表单收拢增量合并** — 落点 page_operation_config.py L658-695
- A4-1 L677 `step.params = result` → 增量合并：
  ```python
  merged = dict(step.params)
  merged.update(result)
  step.params = merged
  ```
  L680-682 reconcile 与 output_mode 变化刷新保留（old_mode 取值行 L674 不动）。
- A4-2 表单侧修改（**明确指令，已经现场取证 2026-09-24**：`FilterForm.get_params`（forms.py L251-254，核对命令 `grep -n '"logic"' rpa_engine/gui/forms.py`）现状**无条件输出 `"logic": "AND"`——硬编码、无对应控件**）：
  - **改**：FilterForm.get_params 删除 `"logic": "AND"` 键输出（返回值仅含 conditions 与 output_mode）；params 中原有 logic 值（含外部 JSON 的 "OR"）经 A4-1 增量合并保留。
  - **消费端等价性**：删除后 ops 消费端取默认 "AND"（实施时核对 `grep -rn '"logic"' rpa_engine/ops/` 确认消费形如 `params.get("logic", "AND")`；GUI 语义与现状一致——界面本就无 OR 控件）。
  - **output_mode 不改**：filter/dedup 表单均持有该控件（_add_output_mode，forms.py L249/L277），有控件才输出＝现状已成立；aggregate 等无控件表单不输出该键，_cp 折叠注入值经合并保留。
  - **防御核对（机械动作，非决策）**：实施 agent 跑 `grep -n "def get_params" -A 6 rpa_engine/gui/forms.py` 确认其余 7 表单 get_params 无"无控件却输出 logic/output_mode"情形，结果记 REPORT。
- A4-3 用例（smoke_m1m3 新场景节 M6-A4，offscreen）：load_from_dict 构造 filter 步 params={"conditions":[...],"logic":"OR"}→page.model 载入→_select_step(0)→_select_step(1)（需第 2 步）→_select_step(0)→断言 model.steps[0].params["logic"]=="OR"；第二段：aggregate 父步 params 含 output_mode（_cp 折叠形态）→表单切走切回→断言 output_mode 仍在。

### 7.2 批次 B 施工细化

**B1（P0-2）错误翻译层** — 新文件 gui/error_messages.py（全文骨架，实施按此落盘）：
```python
"""gui/error_messages.py — 用户可见错误话术翻译层（批次 B/P0-2）。

分层纪律：引擎/ops 保持原始错误进日志（排查用）；本模块只在 GUI 出口
（失败气泡/弹窗/报告页失败原因）把原始文本翻译成人话＋下一步动作。
文案过 architecture.md §8.4 禁用词表（SQL/表名/SQLite/物理名等不出现在
返回值中）。规则按序匹配，首个命中生效；未命中走兜底话术＋日志路径。
"""
from pathlib import Path
from paths import get_engine_root   # 现场核对：from paths import（app.py L19 同款）

_FALLBACK = "程序遇到意外问题，本次操作未完成。"
_NEXT_FALLBACK = "请把日志文件发给管理员查看。"

# (匹配子串, 人话原因, 下一步动作)——匹配大小写不敏感
_RULES = [
    ("no such column", "步骤用到的数据列不存在。",
     "请检查该列是否被改名或删除，修正后重试。"),
    ("no such table", "步骤用到的数据表不存在。",
     "请检查该表是否已被删除或弃用，修正后重试。"),
    ("permissionerror", "文件正被其他程序占用（例如 Excel 未关闭）。",
     "请关闭占用该文件的程序后重试。"),
    ("filenotfounderror", "找不到指定的文件。",
     "请确认文件没有被移动、改名或删除。"),
    ("memoryerror", "数据量超出了可用内存。",
     "请缩小数据范围或分批处理后重试。"),
    ("disk i/o error", "磁盘读写发生错误。",
     "请检查磁盘空间是否充足，然后重试。"),
    ("database is locked", "数据正忙，本次操作没有完成。",
     "请等待几秒后重试；反复出现请报告管理员。"),
    ("步骤执行超时", "本步骤处理时间超出上限。",
     "请缩小数据范围后重试，或联系管理员调整上限。"),
]

def translate_error(raw: str) -> str:
    """原始错误文本 → 人话（原因＋下一步）。空/None 走兜底。"""
    if not raw:
        return f"{_FALLBACK}{_NEXT_FALLBACK}"
    low = str(raw).lower()
    for key, reason, action in _RULES:
        if key in low:
            return f"{reason}{action}"
    return f"{_FALLBACK}{_NEXT_FALLBACK}"

def log_hint() -> str:
    """返回当前日志目录提示（供弹窗'详细日志'指引）。"""
    return str(Path(get_engine_root()) / "logs")
```
- B1-1 落盘上述新文件（import 路径现场核对：`grep -n "from paths import" rpa_engine/gui/app.py`）。
- B1-2 main_window 失败弹窗（L441-446）改：
  ```python
  if status == "failed":
      reason = translate_error(self._last_error_message)
      QMessageBox.critical(
          self, "执行失败",
          f"工作流执行失败：{reason}\n\n详细日志目录：{log_hint()}",
      )
  ```
  L442"未知原因（详见终端输出面板）"随 _last_error_message 为空走兜底话术，字面删除。
- B1-3 _on_step_failed（L418-424）气泡 message 改 `translate_error(message)`（self._last_error_message 仍存原文供日志）。
- B1-4 page_report"技术详情"折叠区（D9）：fill 的物理名映射段与输出文件绝对路径段移入新增可折叠区（QToolButton checkable"技术详情"＋默认隐藏容器）；主区仅显示别名/行数/状态/失败原因（已翻译）。锚点 page_report.py L84-96。
- B1-5 sql_safety L175-179："当前可用表: [...]"从异常 message 移入 logger.warning；异常文本改"步骤使用的数据表不存在"。既有断言兼容：test_missing_table_error_message 断言 `"不存在" in str(...)` 保持成立。
- B1-6 step_executor fail()（L303-312）不改原始文本（日志层保留原文）；GUI 出口统一经 B1-2/B1-3 翻译——分层纪律写入模块 docstring。
- B1-7 文案禁用词自查：对 error_messages.py 返回值全集跑 §8.4 禁用词表人工评审（记录进 REPORT）。
- B1-8 用例（tests/test_translation.py 追加或新文件 test_error_messages.py，纯标准库）：①translate_error("OperationalError: no such column: 区域") 含"数据列不存在"且不含"no such column"②translate_error("") 走兜底③translate_error("PermissionError: [Errno 13]") 含"Excel"或"占用"④_RULES 每条的人话与动作字段均非空且不含禁用词（遍历断言）。

**B2（P1-8）导入异常面** — main_window L251-253 捕获元组扩为 `(ValueError, FileNotFoundError, PermissionError, OSError, sqlite3.Error)`（顶部 import sqlite3，现场核对是否已有）；except 体文案改 `translate_error(str(e))`（依赖 B1）。同类捕获面走查：`grep -n "except (ValueError" rpa_engine/gui/main_window.py` 全部导入相关捕获点统一。

**B3（P2-14）重试耗尽=失败** — executor L132-140 else 分支现状＝skip 日志继续（retry 耗尽也落入）。改：
```python
else:
    if progress_callback:
        progress_callback(step.step_id, "failed", str(result.get("message", "")))
    if step.on_error == "stop":
        raise ExecutionError(result["message"])
    if step.on_error == "retry":
        raise ExecutionError(
            f"步骤 [{step.step_id}] 重试 {step.retry_count} 次后仍失败: "
            f"{result['message']}")
    # skip：记录后继续
    logger.warning(...)
```
用例：外部 JSON 构造 on_error="retry"、retry_count=2、必失败步→断言 execute_workflow 抛 ExecutionError 且日志含"重试 2 次"；on_error="skip" 场景回归（A2-4 已覆盖 success=False）。

### 7.3 批次 C 施工细化

**C1（P0-3）源码指纹** —
- C1-1 新文件 tools/make_fingerprint.py（骨架）：遍历 `rpa_engine/**/*.py` 排序→逐文件 sha256→对汇总串再 sha256 得 SOURCE_HASH；`subprocess.run(["git","rev-parse","HEAD"])` 成功记 GIT_REV 否则 "N/A"；输出两行 KEY=VALUE 到 stdout（build.bat 重定向追加进 BUILD_INFO.txt）。
- C1-2 build.bat 成功构建后追加指纹段（BUILD_INFO.txt 增 SOURCE_HASH/GIT_REV/BUILD_TIME 既有保留）。
- C1-3 界面"关于"：main_window 标题栏按钮区（现场核对 `grep -n "退出程序\|title_bar" rpa_engine/gui/main_window.py`）增"关于"小按钮→QMessageBox.information 显示版本常量＋BUILD_INFO 指纹段（frozen 读包目录 BUILD_INFO.txt；源码态显示"开发版"）。
- C1-4 build-guide §1.10 判据增第 4 条"指纹比对：BUILD_INFO SOURCE_HASH 与当前源码重算一致→包有效"；doc-governance §4 校验随 E1 脚本化。
- C1-5 D10 落地：批次开工时人工确认 09-24 包→按确认结果更新 build-guide L122/backlog W-20/AGENTS §8 三处口径（确认①：销 W-20＋标注该包无指纹属历史包、下一次构建起有指纹；确认②：W-20 维持待重建）。

**C2（P1-9）打包原子化** — build.bat 重构（伪代码，实施按现有参数体系落）：
```
1. 参数解析（现有 --build-dir/--output/--clean/--skip-tests 兼容，新增 --skip-tests）
2. 门禁（D4①）：unless --skip-tests → conda 环境校验后跑
   python -m unittest discover -s tests（cwd=rpa_engine）
   ＋ python tools\smoke\smoke_m1m3.py（E5 迁移后路径；迁移前用 _temp 原路径）
   失败 → echo 门禁未过 & exit /b 1（不动任何现有产物）
3. python tools\make_fingerprint.py > build_tmp\FINGERPRINT.txt
4. pyinstaller --distpath build_tmp\dist --workpath build_tmp\work RPA_Workflow_v3.spec
   失败 → 清 build_tmp & exit /b 1（旧包无损）
5. if exist "%BUILD_DIR%\RPA_Workflow_v3.exe" move /y → "%BUILD_DIR%\backup\RPA_Workflow_v3_%timestamp%.exe"
6. move build_tmp\dist\RPA_Workflow_v3.exe → %BUILD_DIR%\
7. BUILD_INFO.txt 重写（时间/Python/PyInstaller/指纹/SKIP_TESTS 标记）
8. 清 build_tmp；--clean 时额外清 %BUILD_DIR%\work（用户数据目录 workspace/logs/storage/temp 永不删）
```
原 L152-153 `rmdir /s /q "!BUILD_DIR!"` 整目录删除逻辑废除。**用户数据保护红线**：脚本任何分支不得触碰 build/ 下 workspace/、logs/、storage/、temp/ 四目录。

**C3（P1-10/D3②）便携约定** — paths.py 不改（裁定②）；app.py 自检项 3 失败 detail 改人话："当前文件夹不允许写入。请把程序放到可写位置（如 D:\\RPA 工具），不要放在 C:\\Program Files 或只读盘。"；部署指南（E6）写明便携约定。

**C4（P3-14）依赖清单** — requirements.txt 删 python-docx/python-pptx 两行及其注释；`conda activate CPS-GPES_RPA-py311 && pip freeze > requirements.lock`（实施轮人工环境执行，命令写入 build-guide）；build-guide §依赖基线段引用 lock 文件。

### 7.4 批次 D 施工细化

**D1（P1-4/P2-12）等待·中断·计时告警** —
- D1-1 session_db.py L74-77 PRAGMA 区追加 `conn.execute("PRAGMA busy_timeout=5000")`。
- D1-2 循环内取消：execute_step 签名增关键词参数 `cancel_check=None`（**不动 9 分支结构**——P2-2 属功能批排除）；仅 export 与 excel 导入两分支的 call_args 增 cancel_check；exporter.export_table 与 table_importer 分块循环签名增 `cancel_check=None`，fetchmany/分块每轮首行 `if cancel_check and cancel_check(): raise ExecutionError("收到终止请求，步骤已中断")`（从 engine.executor import 会成环——ops 不 import engine：改抛 `RuntimeError("CANCELLED")` 约定字符串，step_executor fail() 捕获后 message 含"收到终止请求"，executor L142 段按 D1-3 归并 cancelled）。**分层纪律**：ops 层抛 RuntimeError("步骤已取消：收到终止请求")；executor 捕获 ExecutionError 时若 cancel_check() 为真→归 cancelled。
- D1-3 executor L142-144 改：
  ```python
  except ExecutionError:
      if cancel_check is not None and cancel_check():
          status = "cancelled"
          logger.warning("[executor] 收到终止请求，执行已终止")
      else:
          status = "failed"
          raise
  ```
  cancelled 落入 finally 后正常 return（status="cancelled"，与 L114 步骤间取消同口径）；executor 调用处把 cancel_check 传入 execute_step（现场核对 execute_step 调用点 L122 区域与 _execute_with_retry 签名同步加参）。
- D1-4 事后计时告警：步骤循环内 L122 前后取 `t_step=time.time()`；返回后 `elapsed_step`；阈值 `timeout_sec = int(workflow.global_config.get("step_timeout_sec", 600) or 0)`；`timeout_sec>0 and elapsed_step>timeout_sec` → logger.warning＋progress_callback(step_id,"completed",f"耗时超过上限 {timeout_sec} 秒")（不改成败判定——硬杀受单连接架构约束不做，说明项）。
- D1-5 用例：test_engine_overwrite 追加——①外部 JSON 构造 retry/skip 不受影响回归②cancel 场景：构造 2 步流程，cancel_check 首步后返 True→断言 status=="cancelled"③阈值读取测试：实施时将阈值读取抽为 executor 模块级函数 `_step_timeout_sec(global_config: dict) -> int`（`try: return int(global_config.get("step_timeout_sec", 600) or 0)`；`except (ValueError, TypeError): logger.warning 后返回 600`——非法值防御），直接对该函数断言四分支：空配置→600／显式 "300"→300／0→0（停用）／"abc"→600＋warning。不做 sleep 型慢用例。
- D1-6 smoke 断言：main_window"终止操作"路径在慢导出场景生效属真机项（列 REPORT §真机清单）。

**D2（P1-5）陈旧回调与孤儿库** —
- D2-1 main_window 增 `self._ignore_next_finish = False`；L196-200 防御段改：
  ```python
  if self.worker.isRunning():
      self.worker.request_cancel()
      if not self.worker.wait(3000):
          logger.warning("[main] 旧任务未在 3 秒内结束，忽略其回调")
          self._ignore_next_finish = True
  ```
  同款防御段复制到 _new_round 与 _back_to_input_selection 开头（当前仅 _on_confirm_import 有）。
- D2-2 _on_workflow_finished 首行：`if self._ignore_next_finish: self._ignore_next_finish = False; logger.info("[main] 丢弃陈旧执行回调"); return`。
- D2-3 陈旧会话库清理：main_window.__init__ 增 `self._cleanup_stale_sessions()`——glob(workspace/session_*.db*) 全删（会话库即用即抛口径：启动时任何残留＝孤儿；workspace 路径经 SessionDB 同款解析，现场核对 `grep -n "workspace" rpa_engine/ops/session_db.py`）。
- D2-4 用例：单测层覆盖 _cleanup_stale_sessions（构造假 workspace 文件→调用→断言删净，需可注入路径——方法签名加 `root: Path=None` 默认取生产路径）；回调忽略逻辑列 smoke/真机清单。

**D3（P1-7）temp 生命周期＋磁盘预检** —
- D3-1 page_input_selection 增会话级清单 `self._temp_copies: List[Path]`；validate_and_copy 成功即登记；`clear_temp_copies()` 方法删除清单内存在文件；调用点＝main_window._close_session 与 _new_round（会话收尾）。
- D3-2 启动超龄清理：_cleanup_stale_sessions（D2-3）内并扫 temp/input_selection/*，mtime 早于 24h 的删除。
- D3-3 磁盘预检：_on_confirm_import 导入循环前 `required = sum(f.stat().st_size for f in 源文件) * 3`；`shutil.disk_usage(workspace盘).free < required` → QMessageBox.warning("磁盘空间不足：需要约 {required/1e6:.0f}MB，可用 {free/1e6:.0f}MB。请清理磁盘后重试。")＋return。
- D3-4 现存 28 文件：D3-2 上线首跑自动清（超龄）；REPORT 记录清理数。

**D4（P2-4）执行结束统一清理中间表** — executor L159 return 前：
- D4-0 **output_tables 语义声明（已核对 executor L124-129 构造处，命令 `grep -n "output_tables\[" rpa_engine/engine/executor.py`）**：登记仅发生在步骤 success 分支且 `result["output_table_id"]` 非空时——`output_tables[派生表号] = 该步实际写入的物理名`。**语义＝派生表号 → 派生表物理名**；cp 步 output_table_id 为空串→不登记；输入表号不是任何步骤的产出号→**输入表物理名不经此路径登记，清理循环天然不触碰输入表**。
- D4-1 **写回目标保护（与 P0-1/D1① 联动，必须实现）**：覆盖写回派生表场景（A1 修复的场景）中，写回目标 t_{uid} 同时是某步骤的产出、会出现在 output_tables——直接删会毁掉写回后的最终数据。清理必须排除保护集：
```python
if status == "completed" and not workflow.global_config.get("keep_db", False):
    protected = {st.params.get("output_table")
                 for st in workflow.steps
                 if st.type == "copy_table" and st.params.get("output_table")}
    for phys in list(output_tables.values()):
        if phys in protected:
            continue
        try:
            delete_table(conn, phys)   # ops.table_lifecycle（顶部 import）
        except Exception:
            logger.warning(f"[executor] 中间表清理失败（忽略）: {phys}")
```
（保护集语义＝全部 cp 步的写回目标物理名＝最终数据载体；写回目标为输入表时同样受保护且本就不在 output_tables；keep_db=True 保留全部，P2-6 接线后。）
- D4-2 执行中"用完即删"＝说明项不做（引用判定复杂、16GB 基线＋50 万行预警已兜底）。
- D4-3 用例（test_engine_overwrite 追加 3 个）：①test_cleanup_intermediate_tables——两步链执行完成后断言 sqlite_master 无任何 t_{uid} 中间表、**输入表 t1 仍在（未被误删断言）**；②test_cleanup_protects_overwrite_target——A1-4 覆盖派生表场景执行后断言 **t_{s1.uid} 仍存在且内容＝dedup 结果（写回目标保护）**、t_{s2.uid} 已清理；③test_cleanup_keep_db——global.keep_db=True 变体断言全部中间表保留。

**D5（P2-9）画布性能三步** —
- D5-1 漏改点外提：node_graph.py L761-762 `missing = [e for e in self._edges if ...]` 提出步骤循环（对照同函数 L745 dep_tables 外提写法）；循环内改集合查找（`missing_keys` 预构 set）。
- D5-2 刷新合并：page_operation_config 增
  ```python
  self._graph_timer = QTimer(self); self._graph_timer.setSingleShot(True)
  self._graph_timer.setInterval(50); self._graph_timer.timeout.connect(self._refresh_graph)
  ```
  与 `def _schedule_graph_refresh(self): self._graph_timer.start()`；13 处 `self._refresh_graph()` 调用点改 `self._schedule_graph_refresh()`（逐处现场核对；需要即时画布的场景——执行开始/回写——保留直调并注释）。smoke 场景在断言前补 `QApplication.processEvents()`＋50ms 等待（_pe() 样板扩展 `time.sleep(0.06)`）。
- D5-3 规模警戒：node_graph 模块常量 `CANVAS_WARN_STEPS = 150`；rebuild 内 `len(steps) > CANVAS_WARN_STEPS` 时 logger.warning；page 侧接线（裁定）：page_operation_config 在 _schedule_graph_refresh 内判断 `len(self.model.steps) > CANVAS_WARN_STEPS` 时 `statusBar().showMessage("流程步骤较多，界面刷新变慢属正常现象", 5000)`，实例标志 `self._canvas_warned` 去重（每会话提示一次）；fit_to_scene 自动重置改"仅新建画布/步骤数变化时"（rebuild 增关键词参数 fit: bool = True，合并刷新路径传 False）。
- D5-4 验证：200 步构造脚本（smoke 临时场景或人工）记录 rebuild 单次耗时进 REPORT；88 基线＋双 smoke 零回归。

**D6（P2-10）索引用量门槛** — ops 模块常量 `INDEX_ROW_THRESHOLD = 50_000`（sql_safety.py 集中，供 mapping_matcher/aggregator/filter_dedup import）；mapping_matcher JOIN 前：
```python
n = conn.execute(f"SELECT COUNT(*) FROM {quote_ident(right_table)}").fetchone()[0]
# 直写 SQL——已取证（2026-09-24）：ops/ 下无既有行数统计函数，不依赖
if n > INDEX_ROW_THRESHOLD:
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{quote_ident(right_table)}_{quote_ident(match_col)} ON {quote_ident(right_table)}({quote_ident(match_col)})")
```
左表同理；aggregator GROUP BY 列、filter_dedup PARTITION 列同式（标识符一律 quote_ident）。索引名规范 `idx_{table}_{col}`。会话库即用即抛无清理负担。用例：小表路径回归（不建索引，断言 sqlite_master 无 idx_）；大表路径以阈值临时调 0 注入断言索引创建＋结果不变。

**D7（P2-13）导入白名单＋导出防覆盖副本区** —
- D7-1 executor 模块级：`_IMPORT_ROOTS: List[Path] = [Path(get_engine_root()) / "temp" / "input_selection"]`＋`def register_import_root(p)`（程序化调用方显式扩展）；ensure_input_tables 内对 `t.source.file`：`Path(f).resolve()` 不在任一 root 下 → raise ParserError(f"输入文件路径不在允许范围: {f}")（GUI 链路天然满足——副本即在该目录）。
- D7-2 exporter：output_path.resolve() 位于 temp/input_selection 内 → fail 拒绝（防覆盖导入副本）；同名覆盖行为保留（用户显式选择＝覆盖意图，写入用户手册"导出会替换同名文件"）。
- D7-3 用例：外部 JSON source.file 指仓库外绝对路径→execute_workflow 抛 ParserError；output_path 指副本区→步骤失败 message 含"不在允许范围/拒绝"。

**D8（P3-6）批量与并扫** — table_content.insert_rows 改 executemany（列名 quote_ident 一次拼装、值参数化不变）；table_importer 导入链合并：scan_sheets 结果（sheet 名集＋行列数）一次取得，传参复用给 read_excel_sheet 的校验分支（签名增关键词参数 `sheet_info=None`），消除 3 次开簿。用例：insert_rows 既有用例回归＋导入结果一致性断言（同文件同 sheet 导入前后行数/列集相等）。

### 7.5 批次 E 施工细化

**E1（P1-11）文档体检脚本** — 新文件 tools/doc_verify.py（骨架）：
```python
"""tools/doc_verify.py — 文档体检脚本（批次 E/P1-11，doc-governance §4 脚本化）。
检查项：①相对链接可达（AGENTS.md、README.md、docs/**、knowledge/**）
②docs/INDEX.md 日期列 vs 各文档 frontmatter 最后更新
③AGENTS.md 容量三口径（含CR≤8000／余量≥200／CRLF 行数、loneCR/loneLF=0）
输出：退出码 0=全绿；markdown 报告写 _temp/verify-<YYYYMMDD-HHMM>.md（留痕）。
用法：python tools/doc_verify.py（仓库根执行，纯标准库）。"""
```
检查①正则提取 `\[...\](相对路径)`→resolve 后 exists（排除 http/锚点#）；②解析 INDEX 表行日期 vs frontmatter `最后更新`；③复用 AGENTS 容量口径（len(data)/非ASCII×2/CR 计数）。E1-2 首轮运行修复清单：architecture §8.2 阶段 1 列名（按 page_input_selection L304-307 实际"选择/标识名称/来源文件/源数据表/表头行/删除"）与"独立弹窗"改"内联表单"；§8.3 信号表按 worker.py L26-29 实际（含 A2-1 扩参后 4 参口径——E 批在 A 批后执行，按届时实况写）；docs/INDEX.md 6 处日期同步；models.py L665 docstring"uid 双口径均剔除"改"业务口径剔除、编辑态第 9 键"；doc-governance §4 增"脚本化：python tools/doc_verify.py，报告落 _temp/verify-*.md"条目。

**E2（P1-3）版本门禁** — parser L116-120 后：
```python
ver = str(meta.get("schema_version", "") or "")
if ver not in _SUPPORTED_SCHEMA_VERSIONS:   # 模块常量 = {"3.1"}
    raise ParserError(
        f"不支持的文件版本 schema_version={ver!r}（本程序支持 "
        f"{'/'.join(sorted(_SUPPORTED_SCHEMA_VERSIONS))}）；该文件由更新版本生成，请升级程序")
```
message 含"请升级程序"（error_messages 规则表可加对应条目）。用例：外部 JSON __meta.schema_version="3.2"→ParserError；缺失该键→按 "3.1" 缺省放行（现场核对现状缺省行为后固化断言）。

**E3（P2-6）丢弃日志＋keep_db 接线** — step_executor L195 白名单过滤处：被丢弃键集非空时 `logger.debug(f"[step_executor] {op} 丢弃非白名单参数键: {sorted(dropped)}")`。keep_db 接线（施工图裁定，两端链路）：①**引擎端中间表清理开关**＝D4-1 已消费 `workflow.global_config.get("keep_db")`（parser 已透传 global_config，外部 JSON 即达）；②**GUI 端会话库保留**＝main_window._on_start_clicked 解析成功后（parse_workflow 返回 wf 处，现场核对该函数内 parse 调用变量名）加 `self._keep_session_db = bool(wf.global_config.get("keep_db", False))`；_close_session 检查 `self._keep_session_db`：True→跳过删库＋logger.info 保留路径，False（默认）→现行删库。**GUI 模型层不加开关**（to_dict 恒写 keep_db=False 现状保留＝自配置场景默认删；外部 JSON 场景经①②生效）。用例：外部 JSON keep_db=true 加载执行后收尾→会话库文件存在；默认→删净（既有 SessionTest 口径回归）。

**E4（P2-3）两本账对账用例** — 新文件 tests/test_states_consistency.py（纯标准库；实施前核对 `grep -n "PyQt" rpa_engine/gui/graph_edges.py`——若含 Qt import 则本文件头加 offscreen 环境变量同款防护）：夹具＝make_model＋filter(T101)＋mapping_match 引用 T101＋overwrite 链；断言＝①model.reconcile() 后 table_states 的 overwritten/produced/referenced/deprecated/dangling 集合 ②与 graph_edges.build_edges 派生的边类型集合按表逐一比对相等（对照口径：overwritten↔覆盖标记边、deprecated↔deprecated_ids、dangling↔missing）。不一致即红＝防漂移门禁。

**E5（P2-11）假断言修复＋门禁载体迁移（D8①）** —
- E5-1 复制 smoke_m1m3.py、smoke_mb.py → rpa_engine/tools/smoke/（新目录）；路径常量适配：`ENGINE = Path(__file__).resolve().parents[2]`（原 `parents[2] / "rpa_engine"`，实施前现场核对原行）；运行命令改 `python tools\smoke\smoke_m1m3.py`（cwd=rpa_engine）。
- E5-2 迁移验证（新位置双跑 ALL_OK）后删除 _temp/DAG-rebuild/ 两原件（删除前核对 `grep -rn "smoke_m1m3\|smoke_mb" _temp/DAG-rebuild/SampleCode/` 0 引用；REPORT 记录删除清单）。
- E5-3 恒真断言修真：L150 `op.isVisibleTo(layer) or True` → `getattr(op, "_current_form", None) is not None`（断言选中 filter 后内联表单已挂）；L176 `check("M2-S4c …", True)` → 断言对象＝M2-S4 场景预构造并写入 recent_steps.json 的步骤条数 `>= 10`（该场景自身构造的计数，实施时以场景内构造变量断言）。smoke_mb 3 处 hasattr 存在性断言升级 `callable(getattr(...))`。
- E5-4 文档同步：doc-governance §8 条 2 补注"FF3-FF5 载体已迁 rpa_engine/tools/smoke/（2026-09-XX，D8 裁定）"；AGENTS §6 Test/ 行如需提及随 E1 校验；历轮 REPORT/task-record 中门禁命令引用不改（历史留痕），新轮起用新命令。

**E6（P2-8）用户手册＋部署指南** — docs/user-manual.md（章节骨架：①这个程序帮你做什么②四步走图文（每阶段一节，截图占位由人工补）③常见错误自救表（从 error_messages._RULES 生成，两列：看到什么/怎么办）④导出会替换同名文件等注意事项⑤找谁求助（日志目录位置））；docs/deployment-guide.md（一页：可写目录约定（D3②）、安装=复制、更新=替换 exe（旧包自动留 .bak）、指纹核对方法、出问题看 logs/）；两文件 frontmatter 按 doc-governance §3（type: knowledge／[参考]／[已校验一致]）；INDEX 登记＋README 导航同步；E1 脚本跑绿。

**E7（P2-7）高分屏与窗口** — app.py L279 QApplication 构造前：
```python
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
```
main_window：`self.setMinimumSize(1100, 700)`；bottom_bar 布局末位加 `QSizeGrip(self)`（frameless 拖拉缩放）；styles.py 字号保留 px（HighDpi 属性下自动缩放，避免 pt 换算引入回归——施工图裁定）。真机高分屏截图核对列 REPORT 人工清单。

**E8（P3-4）注释三改** — page_input_selection.py L598 docstring"前20行"→"前 50 行（_PREVIEW_ROWS）"；app.py L4 模块 docstring"5 项"→"6 项"；registry.py L6-7 自述随 F3 改造同步改"真转发层"。

**E9（P3-7）重排提示** — _on_confirm_import（L219-256）编号分配后：比对新旧 registry 的 {table_id: (source_path, sheet_name)}；对 model.steps 引用了"映射变化"表号的步骤，QMessageBox.information 列出"第 N 步「名称」引用的表已变化（旧→新来源），请检查参数"；无变化静默。首导入（无旧 registry）跳过。用例列 smoke/真机清单（弹窗交互）。

**E10（P3-8）last_config 防抖即时写** — main_window 增 `self._lc_timer = QTimer(singleShot, 2000ms)`→timeout 连既有 last_config 写函数（现场核对函数名）；触发点＝步骤增删/insert/删除表/确认导入完成/表单收拢成功（经既有信号或调用点插桩 `_lc_timer.start()`）；退出时写保留。崩溃恢复口径不变（启动读 last_config 既有链）。

### 7.6 批次 F 施工细化

- **F1（P3-1）**：删 models.py move_step（L479-484）；唯一消费者 smoke_m1m3 M5a 调序场景改 insert_step/remove_step 等效序列或删该场景段（E5 迁移后在 tools/smoke/ 内改；漂移免疫断言保留——用 remove+add 组合时对未参与调整步骤断言，或改用 insert 调序）；tests 无引用（现场核对 `grep -rn "move_step" rpa_engine/`）。
- **F2（P3-2）**：ops/__init__.py L102-123 `__all__` 收缩——移除 execute_sql/fetch_dataframe/insert_rows/update_rows/delete_rows/query_rows/create_table/get_column_info/cleanup_files 9 项（**delete_table 保留**：D4 已接生产调用）；execute_sql 函数 docstring 加"内部工具，非工作流操作，禁止接入 JSON 参数"；逐项移除前 `grep -rn "<名>" rpa_engine/` 确认零生产引用（测试引用同步改 import 路径为源模块）。
- **F3（P3-3）**：registry.py L15-23 两函数删实现改 `from ops.step_executor import get_op_func, list_ops`（再导出）；L6-7 docstring 改"薄再导出层（真转发）"；`grep -rn "from engine.registry import\|from engine import registry" rpa_engine/` 调用方零改动验证。
- **F4（P3-5）**：forms.py L28-29 `_OPS` 改 `from ops.sql_safety import SUPPORTED_OPERATORS as _OPS`（单一来源；现场核对两清单内容差集——forms 含 LIKE/IN 而 sql_safety 若缺则先补齐 sql_safety 再引用）；app.py 守卫②区增断言 `_OPS ⊆ SUPPORTED_OPERATORS`（引用后恒等，防御回退）。
- **F5（P3-11）**：graph_edges.py L315-321 detect_table_id_collisions 删除；`grep -rn "detect_table_id_collisions" rpa_engine/` 测试引用改走 models.validate_table_ids_unique 或 validator 生产入口。
- **F6（P3-13）**：table_schema.py L162-169 col_type 过白名单 `_TYPE_WHITELIST={"TEXT","INTEGER","REAL","BLOB","NUMERIC","VARCHAR","DATE","DATETIME","BOOLEAN"}`（不在→回退 TEXT＋logger.warning）；sql_safety L152 LIKE 分支值转义 `%`/`_`（`value.replace("\\","\\\\").replace("%","\\%").replace("_","\\_")`＋SQL 加 `ESCAPE '\\'`）；main_window L365-370 gui_workflow.json 写点：实例标识方案（施工图裁定）——写前读校验：文件存在且 mtime 晚于本实例启动时间且内容 instance_id≠本实例 → 放弃写＋logger.warning（低成本防互覆；instance_id=启动时间戳，写入 JSON __meta）。
- **F7（P3-12）**：说明项不立项（CI 超边界，理由见 §二 F 表）。

### 7.7 施工图增补总表（本轮具体化：维度 3/4/6 与维度 5/7 补全）

#### 7.7.1 新增/修改数据结构字段表（维度 3）

| 结构/字段 | 载体 | 类型 | 默认值 | 语义 | 持久化/序列化口径 |
|---|---|---|---|---|---|
| success（信号第 4 参） | EngineWorker.workflow_finished | bool | run 内初始 False | executor result["success"]（completed 且全步成功） | 不持久化；信号参数→显示状态 |
| display_status | main_window._on_workflow_finished 局部 | str | ＝status | completed＋not success → "completed_partial" | 仅传 page_report.fill |
| overwrite_ids | page_report.fill 关键词参数 | set 或 None | None | 覆盖链父步的派生表号集（"中间结果"标注用） | 仅传显示；调用侧组装 |
| _RULES | gui/error_messages.py 模块常量 | list[(str,str,str)] | 8 条（B1 骨架） | (匹配子串小写, 人话原因, 下一步动作)；按序首个命中 | 代码常量，不持久化 |
| _IMPORT_ROOTS | engine/executor.py 模块级 | List[Path] | [ENGINE_ROOT/temp/input_selection] | 导入路径白名单 | 进程内状态 |
| step_timeout_sec | 工作流 JSON global 段 | int（容忍字符串） | 600 | 步骤计时告警阈值秒；0=停用 | 业务 JSON 键（parser 透传 global_config） |
| keep_db | 工作流 JSON global 段 | bool | False | True=完成后保留中间表与会话库 | 同上（E3 两端接线） |
| busy_timeout | SessionDB 连接 PRAGMA | int(ms) | 5000 | 写锁冲突等待上限 | 连接级设置，不落盘 |
| _ignore_next_finish | main_window 实例属性 | bool | False | 丢弃下一次陈旧 finished 回调 | 进程内状态 |
| _temp_copies | page_input_selection 实例属性 | List[Path] | [] | 本会话导入副本清单（清理钩子消费） | 进程内状态 |
| _keep_session_db | main_window 实例属性 | bool | False | GUI 端会话库保留标志 | 进程内状态 |
| _lc_timer / _graph_timer | main_window / page_operation_config | QTimer(singleShot) | 2000ms / 50ms | 配置防抖写 / 画布合并刷新 | 进程内状态 |
| _canvas_warned | page_operation_config 实例属性 | bool | False | 规模警戒提示去重（每会话一次） | 进程内状态 |
| CANVAS_WARN_STEPS | node_graph 模块常量 | int | 150 | 画布步数警戒阈值（D7 裁定） | 代码常量 |
| INDEX_ROW_THRESHOLD | sql_safety 模块常量 | int | 50_000 | 建索引行数门槛（D2/§7.4 D6 裁定） | 代码常量 |
| _step_timeout_sec() | executor 模块函数 | (dict)->int | — | 阈值读取（默认 600/显式/0 停用/非法回退 600+warning） | 可直测纯函数 |
| protected | executor D4-1 局部 | set | — | cp 步写回目标物理名集（清理保护） | 执行内状态 |
| derived_phys | models.to_dict 局部（A1-1） | dict | — | 派生表号→t_{uid}（cp 写回解析，uid 防御后构建） | 序列化内状态 |
| SOURCE_HASH / GIT_REV / SKIP_TESTS | build/BUILD_INFO.txt 字段 | str | — / —（git 不可用=N/A）/ 缺省=未跳过 | 源码指纹 / git 修订 / 测试跳过标记 | 构建产物元数据（D5 裁定双指纹） |
| instance_id | gui_workflow.json __meta | str | 启动时间戳 | 双开互覆防护标识（F6） | 运行配置保存时写入 |
| _TYPE_WHITELIST | table_schema 模块常量 | set | TEXT/INTEGER/REAL/BLOB/NUMERIC/VARCHAR/DATE/DATETIME/BOOLEAN | DDL 类型白名单（大小写不敏感，先 upper() 再查） | 代码常量 |
| doc_verify 报告 | _temp/verify-<YYYYMMDD-HHMM>.md | 文件 | — | 文档体检留痕（doc-governance §4 证据） | 每次运行生成，不覆盖历史 |

#### 7.7.2 接口契约与调用链表（维度 4）

| 接口 | 签名（新/改） | 入参约束 | 出参/异常 | 副作用 | 调用方 | 被调用方 | 兼容性影响 |
|---|---|---|---|---|---|---|---|
| translate_error | (raw: str) -> str（新） | 任意串；None/空→兜底话术 | 人话串（原因＋下一步），不含 §8.4 禁用词 | 无 | main_window 弹窗/气泡、page_report 失败原因 | _RULES | 新增，无兼容面 |
| log_hint | () -> str（新） | 无 | 日志目录绝对路径串 | 无 | 失败弹窗文案 | paths.get_engine_root | 新增 |
| EngineWorker.workflow_finished | pyqtSignal(str, float, dict, bool)（改：+success） | 第 4 参 run 内 result["success"] | — | emit | main_window 一次性接线 | execute_workflow | **签名变更**：A2-S1/S2 同一提交单元，连接端同步 |
| MainWindow._on_workflow_finished | (status, duration, output_tables=None, success=True)（改） | 末位默认参 | 无 | 切页/弹窗/回写/输出清单后移收集 | worker 信号 | translate_error、collect_file_stats、fill | 默认参兼容旧 3 参调用 |
| page_report.fill | (..., overwrite_ids=None)（改：末位关键词参） | 表号 set | 无 | 标注列显示 | _on_workflow_finished | — | 默认 None 兼容既有调用 |
| execute_step | (..., cancel_check=None)（改：末位关键词参） | callable 或 None | 返回 dict 口径不变；取消→success=False 且 message 含"收到终止请求" | 无新增 | executor._execute_with_retry | BUILTIN_OPS | 默认 None 兼容，88 基线零改动 |
| export_table / import 链 | (..., cancel_check=None) / (..., sheet_info=None, cancel_check=None)（改） | 同上 / dict 或 None | RuntimeError("步骤已取消：收到终止请求")（取消时） | — | step_executor export/导入分支 | fetchmany/分块循环 | 关键词默认参兼容 |
| execute_workflow | 行为变更（签名不变）：①循环内取消归并 status="cancelled"（不抛）②completed 且非 keep_db 时清理中间表（保护集除外）③步骤计时告警 | — | return dict 键口径不变 | 新增 delete_table 调用 | worker、程序化调用方 | delete_table、_step_timeout_sec | 外部 JSON 行为面：完成后中间表即清（写入用户手册） |
| register_import_root | (p: Path) -> None（新） | 绝对路径 | 无 | _IMPORT_ROOTS 追加 | 程序化调用方 | — | 新增 |
| _step_timeout_sec | (global_config: dict) -> int（新） | — | ≥0；非法值回退 600＋warning | 无 | executor 步骤循环 | — | 新增，可直测 |
| _schedule_graph_refresh | (self) -> None（新） | — | 无 | 启动 50ms 单发定时器 | 13 处原 _refresh_graph 调用点 | _graph_timer→_refresh_graph | 时序：smoke 断言前补 processEvents＋60ms |
| _cleanup_stale_sessions | (self, root: Path = None) -> int（新） | root 可注入（测试） | 删除文件数 | 删 session_*.db*＋超龄 24h temp 副本 | main_window.__init__ | glob/unlink | 新增 |
| clear_temp_copies | (self) -> None（新） | — | 无 | 删 _temp_copies 清单文件 | _close_session、_new_round | — | 新增 |
| FilterForm.get_params | 返回值删 "logic" 键（改） | — | dict（conditions/output_mode） | — | _harvest_current_form | 控件 | logic 经增量合并保留原值；消费端默认 AND |
| _harvest_current_form | 行为变更：整包替换→增量合并（签名/返回值不变） | — | bool 口径不变 | reconcile/条件刷新保留 | 既有调用点不变 | form.try_apply | 非表单管理键不再丢失（P2-5 修复本体） |
| registry.get_op_func / list_ops | 改真转发（签名不变） | — | 同源实现 | — | 既有调用方 | ops.step_executor | 调用方零改动（F3 DoD） |
| tools/make_fingerprint.py | CLI 无参（新） | — | stdout 两行 KEY=VALUE；退出码 0 | 读源码与 git | build.bat | hashlib/subprocess | 新增 |
| tools/doc_verify.py | CLI 无参（新） | — | 退出码 0=全绿/1=有项；写 _temp/verify-*.md | 读 AGENTS/docs/knowledge/README | 人工＋涉文档批次门禁 | re/pathlib | 新增 |

#### 7.7.3 边界矩阵（维度 6：条件→预期→验证）

| 改动 | 边界条件 | 预期行为 | 验证方式 |
|---|---|---|---|
| A1 | 写回目标＝输入表 | cp 物理名走 sqlite_of（现状回归） | A1-3④＋既有 88 |
| A1 | 写回目标＝派生表 | cp 物理名＝该表 t_{uid}，内容真被覆盖 | A1-3③/A1-4 |
| A1 | 写回目标＝不存在表号 | 到不了 cp（validator 前向引用拦截） | 既有 validator 用例 |
| A1 | uid 重复场景 | derived_phys 用防御修正后的 uid（构建序保证） | A1-3 前置防御回归 |
| A2 | status=failed | 弹窗走翻译话术＋日志目录指引 | B1-8＋人工评审 |
| A2 | status=cancelled | 不弹失败弹窗；显示"已终止"口径（fill 现有映射） | A2-5 场景扩展 |
| A2 | completed＋success=False | 显示"部分完成（有步骤被跳过）"；输出清单空 | A2-4/A2-5 |
| A4 | params 含表单未管理键 | 合并后原样保留 | A4-3 两段 |
| A4 | 无内联表单（idx<0/form None） | 返回 True 原路径不动 | 既有 88 |
| B1 | raw 为空/None | 兜底话术 | B1-8② |
| B1 | 多规则可命中 | 按 _RULES 表序首个生效（特异→一般排列） | B1-8④ 遍历断言 |
| B3 | retry 中途成功 | 正常返回不抛 | B3-S2 变体 |
| B3 | retry 耗尽 | ExecutionError（message 含重试次数） | B3-S2 |
| D1 | 写锁冲突 | busy_timeout 等待≤5s 再报错 | 双连接并发用例（人工构造） |
| D1 | cancel 竞态（检查后立刻取消） | 下一轮循环检查点退出；不损坏已写数据（事务回滚既有） | D1-5② |
| D1 | step_timeout_sec 非法（"abc"/null） | 回退 600＋warning | D1-5③四分支 |
| D2 | wait(3000) 成功 | 不置忽略标志，正常收尾 | 代码走查＋smoke |
| D2 | wait 超时 | 置标志；下一次 finished 回调被丢弃且标志复位 | 真机清单项 |
| D3 | 磁盘充足/不足（界=源大小×3） | 放行 / 人话提示并中止导入 | D3-3 假不足构造 |
| D3 | temp 目录不存在/文件被占用 | 清理钩子静默跳过/warning 继续 | D3-1 单测 |
| D4 | 保护集为空（无 cp 步） | output_tables 全清 | D4-3① |
| D4 | 清理单表失败 | warning 忽略，status 不变 | D4-3 变体（坏表名注入） |
| D4 | keep_db=True | 全保留 | D4-3③ |
| D5 | 步数 150/151 | 警戒提示恰在 >150 触发且每会话一次 | D5-3 构造脚本 |
| D5 | 50ms 内连续触发 | 仅重画一次 | smoke 时序断言 |
| D6 | 行数 50000/50001 | 恰在 >50000 建索引 | D6-S3 阈值 0 注入变体 |
| D6 | 索引已存在 | IF NOT EXISTS 幂等 | D6-S3 |
| D7 | 相对路径/UNC 网络路径 | resolve 后按白名单判定；越界拒绝 | D7-3 |
| D7 | 白名单 root 不存在 | 判定为越界拒绝（不放行） | D7-3 变体 |
| E2 | schema_version 缺失/空串/"3.10" | 缺失→缺省放行（现状核对后固化）；空串与 "3.10"→拒绝 | E2-S2 |
| E3 | keep_db 非布尔值 | bool() 转换；缺失默认 False | E3 双态用例 |
| F6 | 类型名小写（"text"） | upper() 后查白名单命中 | F6-S1 用例 |
| F6 | LIKE 值含 % / _ | 转义后按字面匹配（ESCAPE '\\'） | F6-S2 用例 |
| F6 | gui_workflow.json 不存在/他实例新写 | 直接写 / 放弃写＋warning | F6-S2 双开实测 |

#### 7.7.4 任务↔用例↔回退映射表（维度 5/7 补全：§八 每任务的测试用例 ID 与回退要点）

| 任务 | 测试用例/验证 ID | 回退要点 |
|---|---|---|
| A1 | A1-3（模型级 4 断言）＋A1-4（执行级 4 断言） | models.py 单文件还原 |
| A2 | A2-4（skip→success=False）＋A2-5（smoke 部分完成） | worker/main_window/page_report 三文件同单元还原 |
| A3 | 报告场景 smoke（标注列） | page_report.py 还原 |
| A4 | M6-A4 smoke 两段（logic=OR/output_mode 注入往返） | forms.py＋page_operation_config.py 还原 |
| B1 | B1-8 四断言＋文案评审清单（人工，记 REPORT） | 删除 error_messages.py＋还原三消费点 |
| B2 | 异常注入用例（占用文件模拟）＋捕获面 grep | main_window.py 还原 |
| B3 | B3-S2 retry 耗尽用例＋skip 回归 | executor.py 还原 |
| C1 | 指纹脚本试运行（两行输出）＋BUILD_INFO 比对（人工构建） | 删 make_fingerprint.py＋build.bat 还原 |
| C2 | 构建失败注入测试（人工：门禁拦下＋旧包无损＋四目录原样） | build.bat git 还原 |
| C3 | 文案评审（人工） | app.py 还原 |
| C4 | lock 文件在位＋build-guide 同步核对 | requirements.txt 还原＋删 lock |
| D1 | D1-5 三用例（cancel/retry-skip 回归/阈值四分支）＋busy_timeout 并发人工项 | session_db/executor/step_executor/exporter/table_importer 五文件还原 |
| D2 | _cleanup_stale_sessions 单测（注入 root）＋真机清单（陈旧回调） | main_window.py 还原 |
| D3 | 清理后零残留断言＋磁盘假不足用例 | page_input_selection/main_window 还原 |
| D4 | D4-3 三用例（清理/保护/keep_db，含输入表保留断言） | executor.py 还原 |
| D5 | 200 步耗时记录（REPORT）＋smoke 时序断言 | node_graph/page_operation_config 还原 |
| D6 | D6-S3 双路径用例（小表不建/阈值注入建） | ops 三文件＋sql_safety 还原 |
| D7 | D7-3 两用例（越界拒绝/副本区拒绝） | executor/exporter 还原 |
| D8 | 导入一致性用例＋insert_rows 回归 | table_content/table_importer/excel_preprocessor 还原 |
| E1 | doc_verify 一键全绿＋留痕文件在位 | 删 tools/doc_verify.py＋docs 修订 git 还原 |
| E2 | E2-S2 双用例（3.2 拒绝/缺省放行） | parser.py 还原 |
| E3 | keep_db 双态用例＋丢弃日志走查 | step_executor/main_window 还原 |
| E4 | 对账用例（进基线） | 删新测试文件 |
| E5 | 新位置双跑 ALL_OK＋grep `or True` 0 | 迁移回退＝tools/smoke/ 删除＋_temp 原件恢复（删除发生在验证后，git 历史兜底） |
| E6 | 人工通读（文员视角评审，记 REPORT） | 删两文档＋INDEX/README 还原 |
| E7 | 启动回归＋真机截图（人工清单） | app.py/main_window/styles 还原 |
| E8 | 文实一致核对（3 处） | 3 处注释还原 |
| E9 | 变化场景提示（smoke/真机清单） | main_window.py 还原 |
| E10 | 2s 内 last_config 更新＋强杀恢复（人工清单） | main_window.py 还原 |
| F1 | grep move_step 0＋漂移免疫断言保留（smoke M5a 改等效序列） | models.py＋smoke 还原 |
| F2 | 出口清单 grep 核对（9 项除名、delete_table 保留） | ops/__init__.py 还原 |
| F3 | 88 绿＋调用方零改动 grep | registry.py 还原 |
| F4 | 自检 6/6＋差集核对记录 | forms.py/app.py/sql_safety 还原 |
| F5 | grep 0 生产外引用 | graph_edges.py＋测试引用还原 |
| F6 | 类型回退/ESCAPE/双开三验证 | table_schema/sql_safety/main_window 还原 |

---

## 八、原子任务表（35 任务 / 89 步）

**纪律**：**执行序以 §九 为准，本节按批次归类**（例：E5 提前至 C 批之前执行，见 §九 条 2）。每步独立可验证；依赖列任务内线性、任务间沿批次序（A→B→C→D 主线，E/F 穿插，显式跨批依赖已标注）；回退＝该步编辑前快照还原（git diff 单文件级，人工执行——Agent 不做 git）；每步对应的测试用例 ID 与回退要点见 §7.7.4 映射表。

### 8.1 批次 A（12 步）

| 步 | 锚点（核对） | 改动点 | 依赖 | DoD |
|---|---|---|---|---|
| A1-S1 | models.to_dict 循环前（§六 sqlite_of 行） | 新增 derived_phys 映射行 | — | grep `derived_phys` 命中 1；88 绿 |
| A1-S2 | models L725（写回原表块） | target_phys 三级回退 | A1-S1 | grep 三级 or 链命中 |
| A1-S3 | test_models_data 新类 | OverwriteDerivedTargetTest（A1-3 四断言） | A1-S2 | 新用例绿 |
| A1-S4 | test_engine_overwrite | test_overwrite_derived_target_executes（A1-4） | A1-S2 | 用例绿＋无游离 T101 |
| A2-S1 | worker L29/L96/L118 | 信号扩 4 参＋success 消费 | — | grep `pyqtSignal(str, float, dict, bool)` 命中 |
| A2-S2 | main_window._on_workflow_finished | 签名+display_status+输出清单后移 | A2-S1 | 代码走查＋88 绿 |
| A2-S3 | page_report.fill 映射 | completed_partial 文案 | A2-S2 | grep "部分完成" 命中 |
| A2-S4 | test/smoke | skip 场景 success=False 断言（A2-4/5） | A2-S2 | 用例绿 |
| A3-S1 | page_report L84-96 | 中间表"类型"标注列（overwrite_ids 关键词参数） | A2-S3 | 报告场景 smoke 绿 |
| A4-S1 | page_operation_config L677 | _harvest_current_form 增量合并 | — | 88 绿 |
| A4-S2 | forms FilterForm.get_params L251-254 | 删 "logic" 键硬编码输出（§7.1 A4-2 明确指令） | A4-S1 | grep `"logic"` forms.py get_params 区 0 输出命中 |
| A4-S3 | smoke_m1m3 新场景 M6-A4 | logic=OR＋output_mode 注入往返用例 | A4-S2 | 场景 ALL_OK；logic=OR 往返不丢 |

### 8.2 批次 B（9 步）

| 步 | 锚点 | 改动点 | 依赖 | DoD |
|---|---|---|---|---|
| B1-S1 | 新文件 gui/error_messages.py | §7.2 骨架全文落盘 | — | import 成功＋B1-S5 用例绿 |
| B1-S2 | main_window L441-446 | 弹窗改 translate_error+log_hint | B1-S1 | grep "终端输出面板" 全库 0 命中 |
| B1-S3 | main_window._on_step_failed | 气泡 message 翻译 | B1-S1 | 代码走查 |
| B1-S4 | page_report L84-96 | 技术详情折叠区（D9） | A3-S1 | 默认主区无物理名/绝对路径 |
| B1-S5 | tests/test_error_messages.py | 4 断言（§7.2 B1-8） | B1-S1 | 用例绿 |
| B1-S6 | sql_safety L175-179 | 表名清单移日志 | — | test_missing_table_error_message 仍绿 |
| B2-S1 | main_window L251-253 | 捕获面扩 5 类＋翻译 | B1-S1 | grep PermissionError 命中该段 |
| B3-S1 | executor L132-140 | retry 耗尽 raise | — | 88 绿 |
| B3-S2 | test_engine_overwrite | retry 耗尽抛 ExecutionError 用例 | B3-S1 | 用例绿 |

### 8.3 批次 C（12 步）

| 步 | 锚点 | 改动点 | 依赖 | DoD |
|---|---|---|---|---|
| C0-S1 | （开工前置） | D10 人工确认 09-24 包状态并记录 | — | REPORT 记录确认结果 |
| C1-S1 | 新文件 tools/make_fingerprint.py | 指纹脚本（§7.3 C1-1） | — | 运行输出 SOURCE_HASH/GIT_REV 两行 |
| C1-S2 | build.bat 成功段 | 追加指纹进 BUILD_INFO | C1-S1 | 试构建 BUILD_INFO 含指纹 |
| C1-S3 | main_window 标题栏 | "关于"按钮＋指纹弹窗 | C1-S1 | 源码态显示"开发版" |
| C1-S4 | build-guide §1.10／三处口径 | 判据第 4 条＋D10 结果落地 | C0-S1 | doc_verify（E1 后）或人工核对 |
| C2-S1 | build.bat L149-159 | 门禁前置（discover＋smoke） | E5-S1* | 门禁失败注入→中止且旧包在 |
| C2-S2 | build.bat | build_tmp 构建＋失败清理 | C2-S1 | 失败注入旧包无损 |
| C2-S3 | build.bat | 旧包 backup＋原子替换 | C2-S2 | .bak 在位 |
| C2-S4 | build.bat | 用户数据四目录永不删红线＋BUILD_INFO 重写 | C2-S3 | workspace/logs/storage/temp 试构建后原样 |
| C3-S1 | app.py 自检项 3 | 失败 detail 人话化（D3②） | B1-S1 | 文案评审通过 |
| C3-S2 | deployment-guide（E6 联动） | 便携约定条目 | E6-S1 | 文档在位 |
| C4-S1 | requirements.txt＋lock＋build-guide | 死依赖删＋freeze 锁定 | — | lock 文件在位、doc 同步 |

（*C2-S1 依赖 E5-S1 迁移后路径；若 C 批先于 E 批执行则暂用 _temp 原路径并在 E5 完成后回来改一行——执行序：E5 提前至 C 批之前，见 §九 条 2。）

### 8.4 批次 D（25 步）

| 步 | 锚点 | 改动点 | 依赖 | DoD |
|---|---|---|---|---|
| D1-S1 | session_db L74-77 | busy_timeout=5000 | — | grep 命中；88 绿 |
| D1-S2 | step_executor/execute_step 签名 | cancel_check 关键词参数＋export/导入两分支传递 | — | 签名核对；88 绿 |
| D1-S3 | exporter/table_importer 循环 | 循环内取消检查抛 RuntimeError 约定文本 | D1-S2 | 取消用例（D1-S5）绿 |
| D1-S4 | executor L142-148＋_execute_with_retry | ExecutionError 捕获按 cancel 归并 cancelled＋cancel_check 传链 | D1-S3 | cancelled 口径与 L114 一致 |
| D1-S5 | tests | cancel→status=="cancelled" 用例 | D1-S4 | 用例绿 |
| D1-S6 | executor 步骤循环 | 事后计时告警（step_timeout_sec 默认 600，0=停用） | — | 阈值读取分支用例绿 |
| D2-S1 | main_window L196-210 | wait 消费＋_ignore_next_finish | — | grep 命中 |
| D2-S2 | _new_round/_back 开头 | 同款防御段复制 | D2-S1 | 三入口防御一致 |
| D2-S3 | _on_workflow_finished 首行 | 陈旧回调丢弃 | D2-S1 | 代码走查 |
| D2-S4 | main_window.__init__ | _cleanup_stale_sessions（含 D3-2 超龄 temp 并扫） | — | 单测（可注入 root）绿 |
| D3-S1 | page_input_selection | _temp_copies 清单＋clear_temp_copies | — | 会话收尾删净断言 |
| D3-S2 | main_window._close_session/_new_round | 清理钩子接线 | D3-S1 | 一轮跑完 temp 零残留 |
| D3-S3 | _on_confirm_import 前 | 磁盘预检（×3 系数） | — | 假不足场景人话提示 |
| D4-S1 | executor return 前 | 统一清理中间表（keep_db 联动） | E3-S2* | 执行后无 t_{uid}、输入表在 |
| D4-S2 | tests | 清理/写回目标保护/keep_db 三用例（D4-3，**含"输入表 t1 未被误删"断言**） | D4-S1 | 用例绿 |
| D5-S1 | node_graph L761-762 | missing 外提＋集合化 | — | 88＋smoke 绿；耗时记录 |
| D5-S2 | page 13 处调用点 | _schedule_graph_refresh＋50ms 合并 | D5-S1 | smoke 补 processEvents 后全绿 |
| D5-S3 | node_graph rebuild/fit | CANVAS_WARN_STEPS=150 警戒＋fit 仅新增时 | D5-S2 | 200 步构造记录进 REPORT |
| D6-S1 | sql_safety | INDEX_ROW_THRESHOLD=50_000 常量 | — | grep 命中 |
| D6-S2 | mapping_matcher/aggregator/filter_dedup | JOIN/GROUP BY/PARTITION 列条件建索引（quote_ident） | D6-S1 | 阈值 0 注入用例：索引建＋结果不变 |
| D6-S3 | tests | 小表不建/大表建双路径用例 | D6-S2 | 用例绿 |
| D7-S1 | executor ensure_input_tables | _IMPORT_ROOTS 白名单＋register_import_root | — | 越界 JSON 拒绝用例绿 |
| D7-S2 | exporter | 副本区拒绝＋同名覆盖保留（手册注记） | D7-S1 | 用例绿 |
| D8-S1 | table_content.insert_rows | executemany 化 | — | 既有导入用例回归绿 |
| D8-S2 | table_importer/excel_preprocessor | sheet_info 传递并扫（3 次开簿→1 次） | D8-S1 | 导入一致性用例绿 |

（*D4-S1 依赖 E3-S2 keep_db 接线；若 D 先于 E，D4-S1 暂以 `global_config.get("keep_db", False)` 直读实现，E3-S2 完成后核对口径一致。）

### 8.5 批次 E（22 步）

| 步 | 锚点 | 改动点 | 依赖 | DoD |
|---|---|---|---|---|
| E1-S1 | 新文件 tools/doc_verify.py | 三查脚本（§7.5 骨架） | — | 运行输出报告＋退出码正确 |
| E1-S2 | architecture §8.2/§8.3 | 列名/弹窗/信号表按实况修订 | A2-S1 | doc_verify ②绿 |
| E1-S3 | docs/INDEX.md 6 处＋models L665 docstring | 日期同步＋矛盾注释修正 | E1-S1 | doc_verify 全绿 |
| E1-S4 | doc-governance §4 | 增脚本化条目 | E1-S1 | §4 校验走一遍留痕 |
| E2-S1 | parser L116-120 | _SUPPORTED_SCHEMA_VERSIONS 门禁 | — | grep 命中 |
| E2-S2 | tests | "3.2" 拒绝＋缺省放行用例 | E2-S1 | 用例绿 |
| E3-S1 | step_executor L195 | 丢弃键 logger.debug | — | 日志断言或走查 |
| E3-S2 | main_window._on_start_clicked/_close_session | keep_db 两端接线（_keep_session_db 标志，§7.5 E3） | — | 双态用例绿 |
| E4-S1 | 新文件 tests/test_states_consistency.py | 两本账对账用例（§7.5 E4） | — | 用例绿并入基线 |
| E5-S1 | rpa_engine/tools/smoke/（新目录） | 双 smoke 复制迁移＋路径常量适配；**执行序：提前至 C 批之前（§九 条 2）** | — | 新位置双跑 ALL_OK |
| E5-S2 | _temp/DAG-rebuild 原件 | 验证后删除（先核 SampleCode 零引用） | E5-S1 | REPORT 记录删除清单 |
| E5-S3 | tools/smoke/smoke_m1m3 L150/L176＋smoke_mb 3 处 | 恒真断言修真 | E5-S1 | grep `or True` 0 命中；双跑绿 |
| E5-S4 | doc-governance §8 条 2＋门禁命令引用 | 载体迁移注记 | E5-S2 | doc_verify 绿 |
| E6-S1 | 新文件 docs/user-manual.md | 手册（骨架五章，自救表由 _RULES 生成） | B1-S1 | 人工通读通过 |
| E6-S2 | 新文件 docs/deployment-guide.md | 部署指南一页（含 D3② 便携约定） | C3-S1 | 人工通读通过 |
| E6-S3 | docs/INDEX.md＋README | 登记与导航同步 | E6-S2 | doc_verify 绿 |
| E7-S1 | app.py L279 前 | 双 HighDpi 属性 | — | 启动无回归 |
| E7-S2 | main_window | setMinimumSize(1100,700)＋QSizeGrip | E7-S1 | 真机拖拉缩放（人工清单） |
| E8-S1 | 注释三处 | page_input_selection L598/app L4/registry L6-7 | F3-S1（registry 项） | 文实一致 |
| E9-S1 | _on_confirm_import | 编号重排比对提示 | — | 变化场景弹提示（smoke/真机） |
| E10-S1 | main_window | _lc_timer 防抖 2000ms＋触发点插桩 | — | 变更后 2s 内 last_config 更新 |
| E10-S2 | 验证 | 模拟崩溃（强杀）重启恢复现场 | E10-S1 | 人工清单记录 |

### 8.6 批次 F（9 步）

| 步 | 锚点 | 改动点 | 依赖 | DoD |
|---|---|---|---|---|
| F1-S1 | models L479-484＋smoke M5a 调序段 | move_step 删除＋场景改等效序列 | E5-S1 | grep move_step 全库 0（除历史文档） |
| F2-S1 | ops/__init__ L102-123 | __all__ 收缩 9 项（delete_table 保留） | D4-S1 | grep 出口清单核对 |
| F2-S2 | execute_sql docstring | 内部工具标注 | F2-S1 | 标注在位 |
| F3-S1 | registry L15-23 | 改真转发 | — | 双活副本消除；88 绿 |
| F4-S1 | forms L28-29 | _OPS 引用 SUPPORTED_OPERATORS（差集先补齐 sql_safety） | — | 单一来源 |
| F4-S2 | app.py 守卫② | ⊆ 守卫断言 | F4-S1 | 自检 6/6 绿 |
| F5-S1 | graph_edges L315-321 | 冗余门面删除＋测试改生产入口 | — | grep 0 生产外引用 |
| F6-S1 | table_schema L162-169 | col_type 白名单 | — | 非白名单回退 TEXT＋warning |
| F6-S2 | sql_safety L152＋main_window L365-370 | LIKE ESCAPE＋实例标识防互覆 | — | 通配符转义用例；双开实测 |

---

## 九、实施门禁、执行序与中间态

1. **统一门禁（每批收尾必跑，全绿才进下一批）**：`python -m unittest discover -s tests`（cwd=rpa_engine）＋双 smoke ALL_OK（E5 迁移前用 _temp 原路径，迁移后用 tools/smoke/）＋启动自检 6/6＋FF1-FF5 落点用例＋涉文档批次加 `python tools/doc_verify.py`（E1 落地后）＋AGENTS 容量三口径（涉 AGENTS 时）。
2. **执行序**：A→B→C→D 主线；**E5（smoke 迁移）提前至 C 批之前执行**（C2-S1 打包门禁直接引用新路径，避免回改）；E 其余任务与 F 批在 D 后穿插；显式跨批依赖已在 §八 标注（C2-S1←E5-S1；D4-S1←E3-S2；E8-S1←F3-S1；E6-S1←B1-S1；C3-S2←E6-S1）。
3. **中间态预期失败**：A2-S1 信号扩参后、A2-S2 完成前，main_window 旧签名连接报错——A2-S1/S2 必须同一提交单元完成；D5-S2 刷新合并后 smoke 时序断言需补 processEvents——同步骤内完成；E5-S3 修真断言若暴露真实缺陷，按缺陷单独登记 REPORT 再修（不掩盖）。
4. **治理（锚点义务）**：首批开工即触发任务定义①（非 _temp 文件修改）——AGENTS 锚点开 R6（任务目标"完善度修复轮 A-F"，状态进行中）＋新建 docs/task-records/2026-09-XX-remediation-batches.md（TEMPLATE 八节）；每批收尾追加 REPORT 节＋记录轮内门禁输出；全部批次完成后 doc-governance §4 全局校验（用 E1 脚本）＋AGENTS §8 主线更新＋backlog 销项（W-20 随 C 批）。
5. **红线自检（每批）**：AGENTS §2.1-6 技术细节隐藏（B 批文案禁用词表评审留痕）；§2.1-5 内存安全（D4/D6 不引入全量入内存路径）；§2.2-4 共享连接（D 批不新建连接）；§2.2-5 不改编排代码（D1-S2 仅加关键词参数不动分支结构；P2-2 字段驱动化仍属功能批排除）。
6. **禁止事项**：不改 K/M5 既有裁定产物（t_{uid} 机制、insert_step 三态、is_end 消费者排除）；不动 _temp/DAG-rebuild/SampleCode 冻结基线；不执行 git（人工接管）；除 §八 锚点外不扩面。

---

## 十、声明

- 本文件为**定稿 [冻结] / Frozen，待实施**：D1-D10 已裁定（§四），施工图已固化（§六~§九），本轮完成前置条件澄清＋6 项瑕疵修复＋8 维度具体化（§十一/§十二）。
- 本轮零代码修改、零配置修改；唯一写入＝本方案文件（覆盖自身，人工授权）。
- 问题编号与证据行号沿用 `_temp/RPA_engine_maturity_assessment.md`（附录 8.3 行号索引）；§六 锚点表为本方案施工定位权威（记录锚点＋现场核对命令双保险，行号基于 M5 实施后版本）。
- 功能函数优化批（P1-1、P1-2、P1-6、P2-1、P2-2）待人工另行立项；衔接见 §三。

---

## 十一、本轮修复说明（前置条件澄清＋6 项瑕疵＋附带修正）

**前置条件判定结论：M5 已实施（分支 b）**。证据（2026-09-24 现场核验，只读）：models.py `def insert_step` L399、page_operation_config.py `def _resolve_insert_index` L452、to_dict 含 t_{uid} 写入与 uid 防御（L682-706）、测试三新类在位（PhysicalNameUidTest L384/InsertStepTest L427/TUidEngineTest L109）、AGENTS 锚点 R5"88 用例全绿"、task-record `docs/task-records/2026-09-24-w03-m5-tuid-insert-anchor.md`。处置：文件头增前置条件声明；88 基线与 M5 后行号锚点全部保留；§六 表首加版本声明；§五 加基线口径说明。

| # | 瑕疵 | 原表述 | 修改后表述 | 位置 | 校验方式 |
|---|---|---|---|---|---|
| 1 | M5 前置条件假设不明确 | 多处默认 M5-a 已实施而无声明（§一"利用 M5-a 成果"、§五 88 基线、§六 L699-706/L668 锚点） | 文件头新增"**前置条件：M5 已完成**"声明（含 5 项实施证据与核验日期）；§五 增基线口径说明（88=79+9，随各批新增用例增长）；§六 纪律行增"本表行号基于 M5 实施后版本" | 文件头/§五/§六 | 三处声明在位；证据可复跑（grep insert_step 等） |
| 2 | 批次 A 标题步数与表格不符 | "### 8.1 批次 A（10 步）"（A4 合并行实含 3 步） | 标题改"（12 步）"；A4-S1/2/3 拆为 3 独立行（各含锚点/改动/依赖/DoD），全表 4+4+1+3=12 行 | §八 8.1 | 标题=表格行数=12 |
| 3 | 总步数基于错误假设 | "35 任务 / 87 步"（按 A=10 计） | "35 任务 / 89 步"（12+9+12+25+22+9=89）；各批标题与行数三方核对一致 | §八 标题 | 三方计数一致（A12/B9/C12/D25/E22/F9） |
| 4 | D4-S1 清理逻辑缺防误删说明 | "输入表物理名不在 output_tables → 天然不误删"（未覆盖写回目标为派生表的交互） | ①D4-0 语义声明（已核对 executor L124-129：语义＝派生表号→派生表物理名，cp 步 output_table_id 空串不登记，输入表不经此路径）；②**D4-1 新增写回目标保护集**（cp 步 params.output_table 物理名不删——修复 P0-1 后写回目标本身在 output_tables 中，直删会毁最终数据）；③D4-3 用例扩为 3 个（含"输入表 t1 未被误删"与"t_{s1.uid} 写回目标保护"断言）；④8.4 D4-S2 行同步 | §7.4 D4/§八 8.4 | 语义与 executor 实测一致；保护集代码在位；用例含双保留断言 |
| 5 | A4-2 是核查任务而非施工指令 | "表单侧核查：…若在无对应控件时仍输出 logic 键…改为仅当控件存在才输出" | 已取证（FilterForm.get_params L251-254 无条件输出硬编码 `"logic": "AND"`，无 OR 控件；dedup 表单不输出 logic；output_mode 均为有控件表单输出）→ 改明确指令：**删除 FilterForm.get_params 的 logic 键输出**；output_mode 不改；消费端默认 AND 等价性论证＋防御核对（机械动作）入文 | §7.1 A4-2/§八 A4-S2 | 无"核查类"模糊措辞；指令唯一确定 |
| 6 | D6 依赖不存在的行数函数 | `n = count_rows(conn, right_table)  # 既有行数函数（现场核对…）` | 已取证（ops/ 无 `def count_rows`，COUNT(*) 仅内联两处）→ 改直写 SQL：`conn.execute(f"SELECT COUNT(*) FROM {quote_ident(...)}").fetchone()[0]`＋注释"不依赖既有行数函数" | §7.4 D6 | 代码块无未确定项 |
| 7（附带） | E5-S1 执行序未在 §八 体现 | §九 说"E5 提前至 C 批前"，§八 E5-S1 行无标注 | ①E5-S1 行加"**执行序：提前至 C 批之前（§九 条 2）**"；②§八 纪律行加"执行序以 §九 为准，本节按批次归类" | §八 标题下/8.5 | 两处注记在位，与 §九 一致 |

**附带修正（维度 8 措辞确定化与矛盾清理，不改实质）**：①§二 P0-1"备选"→"被否方案（D1 裁定采①）"；②§二 P1-4"超时算失败"→"计时告警不改成败判定"（消除与 §四 D2 裁定/§7.4 D1-4 施工图口径的矛盾）＋"阈值待 D2 决定"→已裁定值；③§二 P2-9"再定/D7 决定数值"→"不做（D7 裁定）/150 步"；④§二 P2-10"随 D8 定门槛"→"已裁定 50,000 行"；⑤§二 P3-10/P1-9/P1-10/P2-13/P3-2/P3-5 六处"随 D× 决定/三选一/决策小项/推荐/或/若保留双份"→按 §四 裁定与 §七 施工图口径改写为唯一确定指令；⑥批次 E 验证"（待人工）"→"（人工复核项，列 REPORT 真机清单）"；⑦§7.1 A3、§7.4 D1-2/D8、§八 两行"可选参"→"关键词参数"；⑧§7.4 D1-5③"实施按可测性落最小断言"→确定化（_step_timeout_sec 四分支直测，含非法值防御）；⑨§7.4 D5-3"rebuild 返回步数或 page 判断"二选一→裁定 page 侧判断＋状态栏提示＋去重标志；⑩§7.5 E3 keep_db"现场核对更直接口径"→确定化两端链路（引擎端 D4 消费＋GUI 端 _keep_session_db 标志）；⑪§7.5 E5-3"变量名现场核对"→断言对象确定化；⑫§7.6 F6"文件锁或实例标识"→实例标识方案（裁定）；⑬§8.3 脚注/§九"执行序建议"→"执行序："。

**冲突记录**：无——本提示词与本地规约无冲突（AGENTS §2.1-6/§2.2-5、doc-governance、build-guide 口径已在 §九 条 5 红线自检内嵌）。

**自检**：7 项全部"已修"（无"无需修改"项）；步数三方计数一致（12/9/12/25/22/9=89）；方案实质零改动（37 项覆盖、修法方向、批次划分、D1-D10 裁定、任务依赖与 DoD 语义均保留——瑕疵 4 的保护集为 D4"防误删"语义的内部一致性修复，非新增决策；瑕疵 5/6 为取证后的指令确定化，方向未变）。

---

## 十二、具体化说明（本轮，8 维度）

### 12.1 八维度落地表

| 维度 | 落地位置 | 覆盖证据 |
|---|---|---|
| 1 文件路径与锚点级定位 | §六 锚点表（约 55 行：文件+记录行号+核对命令）＋§七 每项落点＋§7.7.4 回退文件清单 | 全部 35 任务均有路径+函数/类+锚点+核对命令；新增文件写明插入位置（error_messages.py/doc_verify.py/make_fingerprint.py/两手册/新测试文件） |
| 2 改动前后对照（函数级） | §七 各项"现状→改后"（A1-2 三级回退、A2-1 信号扩参、A4-1 三行替换、B3 else 分支、D1-3 捕获段、D4-1 保护集、E2 门禁、E3 两端链路等均为精确前后对照）＋§7.7.2 兼容性影响列 | 每处修改含原逻辑/新逻辑/调用方衔接（中间态预期失败清单 §九 条 3） |
| 3 数据结构与字段定义 | §7.7.1（22 行：字段/载体/类型/默认值/语义/持久化口径） | 覆盖全部新增结构（信号参/常量/标志位/JSON 键/BUILD_INFO 字段/instance_id） |
| 4 接口契约与调用链 | §7.7.2（18 接口×8 列：签名/入参/出参异常/副作用/调用方/被调用方/兼容性） | 新增与行为变更接口全量；签名变更项标注"同一提交单元" |
| 5 测试用例级描述 | §七 各项用例（文件+类/方法名+夹具+操作+断言值：A1-3/A1-4/A2-4/B1-8/B3/D1-5/D4-3/D6/D7-3/E2/E3/E4）＋§7.7.4 任务↔用例映射＋§7.7.3 边界验证列 | 35 任务全部映射到用例 ID 或人工验证项（人工项显式标注"列 REPORT 真机清单"） |
| 6 边界与异常路径 | §7.7.3 边界矩阵（34 条边界×4 列：改动×条件×预期×验证） | 覆盖空值/竞态/阈值边界（150/151、50000/50001）/非法输入（"abc"/空串/"3.10"/UNC 路径）/资源占用/双开/幂等 |
| 7 里程碑任务原子化 | §八 35 任务/89 步（步 ID+锚点+改动+依赖+DoD）＋§7.7.4 补用例 ID 与回退要点两列语义 | 任务划分/依赖/DoD 语义与上轮冻结版一致（仅 A4 合并行拆为 3 独立行＝表述细化）；无循环依赖（任务内线性、跨批依赖 5 条显式标注） |
| 8 写作与自洽性 | 全文措辞确定化（§十一 附带修正 13 处清单）；九禁词正文（§一~§十）0 命中（留痕引号例外见 §12.3）；表格优先；行号引用全部附核对命令 | grep 复验记录见 §12.3 |

### 12.2 修改前后对照摘要

上轮版（663 行，35 任务/87 步）→ 本轮版（新增 §7.7 四总表 131 行＋§十一/§十二；89 步）：①前置条件声明三处落位；②A4 行拆分与双计数修正；③D4 增语义声明+保护集+第 3 用例；④A4-2/D6/E3/D1-5/D5-3/F6 六处指令确定化；⑤E5-S1 执行序双注记；⑥§二 裁定级表 13 处措辞与裁定同步；⑦维度 3/4/6 总表与维度 5/7 映射表新增。修法方向、批次划分、D1-D10 裁定、37 项覆盖、任务依赖与 DoD 语义全部未变。

### 12.3 是否改动方案实质：**否**

K 级裁定（D1-D10）、37 项问题覆盖与编号、六批次划分、§八 任务依赖与 DoD 语义均保留原状；本轮全部修改属"澄清/确定化/增补对照与边界"性质（瑕疵 4 保护集＝D4 防误删语义的内部一致性修复，瑕疵 5/6＝取证后指令确定化，均非新增决策点）。禁词复验（2026-09-24 grep）：**正文（§一~§十）禁词（可能/也许/视情况/大致/推荐/备选/待定/建议/可选）0 命中**；唯一例外＝§四 批准记录引语（"所有决策点全部采用推荐"为人工指令原文引用）、§十一 附带修正留痕与 §12.1/§12.3 复验说明行的引号内原词（留痕必要性，同 M5 方案 §11.1 例外条款模式）。

### 12.4 未落地留白（3 项，均属实施期人工/真机验证项，非设计缺口）

| # | 留白 | 原因 |
|---|---|---|
| 1 | 高分屏真机截图核对、200 步/百万行实测、双开互覆实测、强杀恢复实测 | 需真机环境，列 REPORT 人工清单（§7.7.4 已标注对应任务） |
| 2 | C2 构建失败注入测试 | 需人工执行 build.bat（Agent 不执行构建，build-guide 红线） |
| 3 | 手册/指南截图占位 | 图文素材由人工补充（E6 骨架已定） |

**当前停止，等待人工"开始实施"指令，不擅自进入实施。**
