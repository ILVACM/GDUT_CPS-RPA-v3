# 任务记录：修复 v4 第三轮真机试用反馈（SQLite 跨线程使用报错）

## 摘要
- **任务目标**：修复 worker 执行必现的 SQLite ProgrammingError（跨线程使用连接）
- **任务状态**：已完成
- **开始时间**：2026-08-23 23:20 (UTC+8)
- **最后更新**：2026-08-23 23:30 (UTC+8)
- **要点摘要**：线程亲和连接方案；3 PASS 新验证（含报错原场景钉子）+ 39 PASS 回归
- **操作人**：黄泊凯

## 用户输入
> 23:18:46|ERROR|[executor] 未预期异常: ProgrammingError: SQLite objects created in a thread can only be used in that same thread. The object was created in thread id 22748 and this is thread id 26540.
> 报错输出分析，继续修改

## Agent 理解与决策

### 根因链
1. `_on_confirm_import`（阶段 1 确认导入）在**主线程**首次访问 `sdb.conn` → 连接惰性创建于主线程（thread 22748）
2. `start_workflow` 将该连接经 `worker.prepare(workflow, conn)` 传入 worker
3. `worker.run()` 在 **QThread**（thread 26540）中调 `execute_workflow(conn)` → SQLite 默认 `check_same_thread=True` → 必现 ProgrammingError

**定性**：100% 程序 BUG（v4 重做引入的线程模型缺陷），GUI 执行路径必然失败。此前离屏测试未启动 worker 线程故未暴露——测试盲区即此处。

### 决策
- **采用线程亲和连接**（谁使用谁创建）：主线程用 `sdb.conn`；worker 线程在 `run()` 内经 `sdb.new_connection()` 建专属连接、finally 关闭。WAL 模式天然支持多连接并发读写同一库文件
- **否决 `check_same_thread=False`**（一行改法）：允许跨线程共享但并发使用不安全，属脆弱捷径
- 附带防御：`_on_confirm_import` 开头若 worker 仍在运行则先取消并等待 3000ms（防"放弃后秒确认导入"边缘竞态）
- 计划经 Plan Mode 人工确认（.trae/documents/bugfix3-sqlite-thread-affinity.md）

## 执行流程

### 流程概览
- 总步骤数：3（修复/验证/收尾）
- 多 Agent 协作：否

### 步骤记录

#### Step 1: 三文件修复
- 状态：✅ 已完成
- 执行内容：
  - [session_db.py] 新增 `new_connection()`（线程亲和 WAL 连接，调用方负责关闭）；`.conn` 属性复用之并注明仅限创建线程
  - [worker.py] `prepare(workflow, sdb)` 改收 SessionDB 对象；`run()` 内 `conn = sdb.new_connection()`，finally 中 commit+close
  - [main_window.py] `worker.prepare(workflow, self._sdb)`；`_on_confirm_import` 开头加 worker 运行中防御（取消+等待）
- 涉及文件：rpa_engine/ops/session_db.py、rpa_engine/gui/worker.py、rpa_engine/gui/main_window.py

#### Step 2: 验证
- 状态：✅ 已完成
- 执行内容：新建 `_temp/bugfix3-verify-test.py`：
  - T1 复现钉子（报错原场景端到端）：MainWindow 离屏 → 主线程确认导入（主线程建连）→ 配置 → parse/validate → worker.start() → 断言 completed（修复前必现 ProgrammingError）
  - T2 线程亲和：另一线程 new_connection 可查询主线程建的表（WAL 跨连接可见）
  - T3 防御路径：worker 运行中再确认导入触发取消且导入继续
- 验证结果：3 PASS / 0 FAIL；回归 19+7+6+7=39 PASS / 0 FAIL；py_compile 3 文件 OK

#### Step 3: 收尾
- 状态：✅ 已完成
- 执行内容：锚点层覆写 + 本记录创建

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 修改 | rpa_engine/ops/session_db.py | 新增 new_connection()（线程亲和） |
| 修改 | rpa_engine/gui/worker.py | prepare 收 sdb；run 内自建连接并关闭 |
| 修改 | rpa_engine/gui/main_window.py | prepare 传 sdb；确认导入防御 |
| 创建 | _temp/bugfix3-verify-test.py | 验证脚本（3 项，含原场景钉子） |
| 修改 | AGENTS.md | 锚点层覆写 |
| 创建 | 本记录 | 任务详情 |

## 关闭标识
- **完成时间**：2026-08-23 23:30 (UTC+8)
- **最终状态**：✅ 全部完成
- **关闭说明**：SQLite 线程亲和缺陷根治（worker 执行链路打通）；CLI/引擎层零改动；GUI 真机复测移交用户
