# 任务记录：W-19 裁定落地——移除 ConsolePanel（GUI 引擎日志面板）

> 日期：2026-09-18｜执行：单 Agent｜状态：已完成

## 摘要

人工裁定 **W-19=移除**：运行追踪页/结果报告页不再向面向文职用户的主界面呈现引擎技术日志。实现：删除 `rpa_engine/gui/widgets.py`（ConsolePanel 类）；`worker.py` 移除 loguru→GUI 转发与 `log_message` 信号；`page_progress.py`/`page_report.py` 移除右侧容器与 `attach_console`、页面改独占布局；日志改由 `logs/gui_*.log` 文件承载（开发者排查入口）。关联文档 architecture/dev-spec/backlog/plan.md/AGENTS/INDEX 同步口径。

## 用户输入

- 问「W-19是什么」后裁定：「采用`移除`，修改方案」。

## Agent 理解与决策

- 移除范围＝GUI 呈现层（widgets.py 整删、worker 转发、两页容器），**保留** loguru 文件日志（app.py `_setup_gui_logging` 不动）——满足 architecture §8.4 条 4「另行提供」。
- worker 内部 `from loguru import logger` 继续使用（异常/连接关闭记录），仅移除 GUI sink 与信号。
- dev-spec §5/§17[8]-[13]/§18 同文 8 处统一改口径（replace_all 增量改写，保留条目结构）。
- architecture §8.4 第 4 条旧「待评估」句改作划线历史注 + 裁定结论（doc-governance §7.1 保留原文）。

## 执行流程

### Step 1：代码移除（rpa_engine/gui/）
- `widgets.py`：整文件删除（仅含 ConsolePanel，全库引用已澄清为仅 main_window.py:40）。
- `main_window.py`：删导入 `from gui.widgets import ConsolePanel`、实例 `self.console`、信号接线 `worker.log_message.connect(...)`、两处 `attach_console(...)` 调用；失败原因注释「详情见终端输出」→「详情见 logs/ 日志文件」。
- `worker.py`：删 `log_message` 信号、`_sink_id` 初始化、run() 内 sink 注册、finally 内 sink 移除、`_loguru_sink` 方法；finally 补注释说明日志出口=文件。
- `page_progress.py` / `page_report.py`：删 `QSplitter` 导入与左右分割结构，页面主体独占（`root.addWidget(left, 1)`）；删 `attach_console` 方法；类与模块 docstring 同步。

### Step 2：文档同步
- `architecture.md`：§8.1 日志句改「loguru→logs 文件、不进入 GUI」；§8.2 阶段 3/4 布局改独占；§8.4 第 4 条三句改写+裁定结论；§17 措辞「print 重定向」→「print 输出规范」；last-updated→09-18。
- `dev-spec.md`：§5 与 §17[8]-[13] 八处「重定向到 GUI 终端输出面板」→「经 loguru 落盘 logs/ 文件（W-19 移除）」；last-updated→09-18。
- `rpa_engine/README.md`：L31 日志口径、gui 树移除 `widgets`。
- `docs/INDEX.md`：architecture/dev-spec 行摘要+日期、frontmatter 日期。

### Step 3：治理闭环
- `backlog.md`：W-19 → ✅ 已裁定关闭（09-18，含实现摘要）；统计 待指令 2→1（W-20）、已完成 18→19；建议顺序与主线提示同步。
- `_temp/DAG-rebuild/plan.md` 附录 E：W-19 由「仍待人工」移至「已裁定关闭」。
- `AGENTS.md`：锚点块覆写为 W-19 任务；§8 主线去除「W-19 需单独裁定」。
- 本记录新建；doc-governance §4 确认（见验收）。

## 涉及文件汇总

| 文件 | 改动 |
|---|---|
| rpa_engine/gui/widgets.py | 删除（ConsolePanel） |
| rpa_engine/gui/main_window.py | 删导入/实例/接线/attach×2；注释 |
| rpa_engine/gui/worker.py | 删信号/sink/`_loguru_sink` |
| rpa_engine/gui/page_progress.py | 独占布局；删 attach_console |
| rpa_engine/gui/page_report.py | 独占布局；删 attach_console |
| docs/architecture.md | §8.1/8.2/8.4 §17 口径 + 日期 |
| docs/dev-spec.md | §5/§17[8]-[13]/§18 口径 + 日期 |
| docs/INDEX.md | architecture/dev-spec 行 + 日期 |
| rpa_engine/README.md | 日志口径 + gui 树 |
| docs/backlog.md | W-19 关闭 + 统计 |
| _temp/DAG-rebuild/plan.md | 附录 E W-19 状态 |
| AGENTS.md | 锚点 + §8 |
| docs/task-records/2026-09-18-w19-consolepanel-removal.md | 新建（本文件） |

## 验收

- ✅ 代码：六个文件 py_compile exit 0；`rpa_engine` 内 grep `ConsolePanel|console|log_message|attach_console|from gui.widgets` 仅剩注释性提及（worker/page_progress/page_report 各 1 处历史注）。
- ✅ 启动自检 6 项 `run_self_check()` ALL_OK=True（含项4b）。
- ✅ SampleCode 回归：`python -m unittest discover -s tests` 61 全绿。
- ✅ doc-governance §4 全局更新校验（2026-09-18）：Step1 AGENTS 自洽（锚点/§8/日期一致；三口径复测）；Step2 索引+五项校验（链接：task-record 新建、architecture/dev-spec/INDEX 同步；元信息 last-updated 齐；层级一致）；Step3 README 同步（根 README 无 ConsolePanel 相关行，零改动合理）。
- ✅ backlog 统计：待指令=1（W-20）、已完成/裁定关闭=19。
- ✅ AGENTS 行尾/容量：doc-governance §10 三口径复测——含 CR **7,748**（余量 252≥200）、行数 196、行尾按 §10.3 保持/恢复 CRLF（Edit 混入 LF 后已统一复归一）。

## 关闭标识

本轮完成。待办收敛：W-20（exe 人工重建）、M0 启动指令、D-2 漂移项（M0 移植前裁定）。