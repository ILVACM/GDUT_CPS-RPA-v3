"""
rpa_engine/engine/executor.py

工作流编排器（v3.1 定稿）。

职责边界（与 ops/step_executor.py）：
- 本文件：编排器——接收共享连接（D8），兜底补导缺失数据源（D2），
  维护 table_id_map（含派生表注册），步骤循环 + 异常策略 + 取消检查点
- ops/step_executor.py：单步翻译与分发，不感知工作流全局状态

执行流程：
1. 校验引用链（validate_table_references）
2. 兜底补导：会话库中缺失的输入表按 source 补充导入（D2）
3. 步骤循环：execute_step 分发 → 派生表注册 → on_error 策略 → 取消检查点
4. 返回汇总结果（不负责连接关闭——连接由调用方/SessionDB 管理）
"""

import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil
import sqlite3
from loguru import logger

from engine.parser import ParserError, WorkflowDef
from engine.validator import validate_table_references
from ops.sql_safety import table_exists
from ops.sqlite_manager import table_row_count
from ops.step_executor import execute_step
from ops.table_importer import import_excel_table
from ops.table_lifecycle import delete_table
from paths import get_engine_root


class ExecutionError(Exception):
    """步骤执行异常（stop 策略触发）。"""
    pass


# ---- R6/D7（P2-13）：导入路径白名单（程序化调用沙箱；GUI 链路的
# 副本天然位于 temp/input_selection，不受影响）----
_IMPORT_ROOTS: List[Path] = [
    Path(get_engine_root()) / "temp" / "input_selection"
]


def register_import_root(root) -> None:
    """显式扩展导入路径白名单（程序化调用方使用）。"""
    p = Path(root).resolve()
    if p not in _IMPORT_ROOTS:
        _IMPORT_ROOTS.append(p)


def _validate_import_path(file: str) -> None:
    """source.file 必须位于白名单目录之一，否则拒绝（防任意路径读取）。

    Raises:
        ParserError: 路径越界（相对路径/UNC 一律 resolve 后判定；
            白名单目录不存在时同样判越界拒绝，不放行）。
    """
    rp = Path(file).resolve()
    for root in _IMPORT_ROOTS:
        try:
            rp.relative_to(root.resolve())
            return
        except ValueError:
            continue
    raise ParserError(f"输入文件路径不在允许范围: {file}")


def _step_timeout_sec(global_config: dict) -> int:
    """步骤计时告警阈值秒（R6/D1-4）：默认 600；0=停用；非法值回退 600。"""
    try:
        return int((global_config or {}).get("step_timeout_sec", 600) or 0)
    except (ValueError, TypeError):
        logger.warning("[executor] step_timeout_sec 非法，回退默认 600 秒")
        return 600


def ensure_input_tables(workflow: WorkflowDef, conn: sqlite3.Connection,
                        cancel_check: Optional[Callable[[], bool]] = None
                        ) -> None:
    """兜底补导：会话库中缺失的输入表按 source 信息补充导入（D2）。

    GUI 流程下阶段 1 已导入全部表，此函数通常空转。

    Raises:
        ExecutionError: source 信息不完整且表缺失，或收到终止请求。
        ParserError: source.file 越出导入白名单（R6/D7-P2-13）。
    """
    for t in workflow.tables:
        # R11/A-16（G-5③）：有效判据＝「表存在且行数 > 0」；上一轮失败留下的
        # 空壳表（存在但 0 行）视为需补导，不再静默跳过（否则下游在空表上运算）。
        if (table_exists(conn, t.sqlite_table)
                and table_row_count(t.sqlite_table, conn) > 0):
            continue
        # R6/D1（P1-4）：补导表间取消检查
        if cancel_check is not None and cancel_check():
            raise ExecutionError("收到终止请求，停止补导输入表")
        src_file = t.source.get("file", "")
        src_sheet = t.source.get("sheet", "")
        header_row = t.source.get("header_row", 1)
        if not src_file or not src_sheet:
            raise ExecutionError(
                f"数据表 {t.table_id}({t.alias}) 不在会话库中，"
                f"且缺少 source 复现信息（file/sheet），无法补导"
                f"（该表可能为空表，需要重新导入）"
            )
        _validate_import_path(src_file)   # R6/D7（P2-13）白名单校验
        logger.info(f"[executor] 兜底补导: {t.table_id} <- {src_file}[{src_sheet}]")
        try:
            import_excel_table(conn, src_file, src_sheet, int(header_row),
                               t.sqlite_table, cancel_check=cancel_check)
        except (ValueError, FileNotFoundError) as e:
            raise ExecutionError(f"数据表 {t.table_id} 补导失败: {e}")
        except RuntimeError as e:
            # R11/B-33：导入入口的取消以 RuntimeError 抛出（table_importer
            # 起止取消检查），须与循环内取消同口径归并为 cancelled；用
            # cancel_check() 二次判定区分取消与真实运行错误，避免放宽捕获
            # 面时吞掉真实错误——非取消则原样上抛（归为失败）。
            if cancel_check is not None and cancel_check():
                raise ExecutionError(f"收到终止请求，停止补导输入表: {e}")
            raise


def execute_workflow(
    workflow: WorkflowDef,
    conn: sqlite3.Connection,
    progress_callback: Optional[Callable[[str, str, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """执行完整工作流（v3.1）。

    Args:
        workflow: 工作流定义（已通过 validate_workflow）。
        conn: 共享 SQLite 连接（D8：调用方经 SessionDB 提供）。
        progress_callback: 进度回调
            (step_id, status∈{running,completed,failed}, message)。
            message 仅 failed 时携带真实失败原因，其余为空串。
        cancel_check: 取消检查函数（返回 True 则在下一个检查点终止）。

    Returns:
        Dict[str, Any]: {"success", "message", "steps_total",
            "steps_succeeded", "status", "duration", "output_tables"}。
            status ∈ {"completed", "cancelled", "failed"}；
            output_tables 为 {派生表编号: sqlite表名}。

    Raises:
        ExecutionError: stop 策略的步骤失败（终止工作流）。
    """
    start_time = time.time()
    steps_total = len(workflow.steps)
    steps_succeeded = 0
    status = "completed"
    output_tables: Dict[str, str] = {}

    logger.info(
        f"[executor] 开始执行: {workflow.name} "
        f"({steps_total} 步, {len(workflow.tables)} 表)"
    )

    try:
        # 阶段 0：引用链校验
        validate_table_references(workflow.tables, workflow.steps)

        # 阶段 1：兜底补导（GUI 模式通常空转）
        ensure_input_tables(workflow, conn, cancel_check)

        # 阶段 2：步骤循环
        table_id_map: Dict[str, str] = {
            t.table_id: t.sqlite_table for t in workflow.tables
        }
        # R6/D1-4：步骤计时告警阈值（默认 600s，0=停用，可经 global 配置）
        timeout_sec = _step_timeout_sec(workflow.global_config)

        for idx, step in enumerate(workflow.steps, start=1):
            # 取消检查点（步骤间）
            if cancel_check is not None and cancel_check():
                status = "cancelled"
                logger.warning(f"[executor] 收到终止请求，在步骤 [{step.step_id}] 前停止")
                break

            if progress_callback:
                progress_callback(step.step_id, "running", "")

            # 单步执行（含 retry 策略；R6/D1：cancel_check 传链至长循环）
            t_step = time.time()
            result = _execute_with_retry(step, conn, table_id_map, idx,
                                         cancel_check)
            elapsed_step = time.time() - t_step
            if timeout_sec > 0 and elapsed_step > timeout_sec:
                # R6/D1-4：事后计时告警（不改成败判定；硬杀线程受单连接
                # 架构约束不做——D2 裁定说明项；仅日志承载，避免重复
                # progress_callback 导致 done_count 双计）
                logger.warning(
                    f"[executor] 步骤 [{step.step_id}] 耗时 {elapsed_step:.0f}s "
                    f"超过告警阈值 {timeout_sec}s（global.step_timeout_sec）"
                )

            if result["success"]:
                steps_succeeded += 1
                # 注册派生表（后续步骤可引用）
                if result["output_table_id"] and result["output_table"]:
                    table_id_map[result["output_table_id"]] = result["output_table"]
                    output_tables[result["output_table_id"]] = result["output_table"]
                if progress_callback:
                    progress_callback(step.step_id, "completed", "")
            else:
                if progress_callback:
                    progress_callback(step.step_id, "failed", str(result.get("message", "")))
                if step.on_error == "stop":
                    raise ExecutionError(result["message"])
                if step.on_error == "retry":
                    # R6/B3（P2-14/D6②）：重试耗尽＝失败（原为静默继续）
                    raise ExecutionError(
                        f"步骤 [{step.step_id}] 重试 {step.retry_count} 次后"
                        f"仍失败: {result['message']}"
                    )
                # skip：记录后继续
                logger.warning(
                    f"[executor] 步骤 [{step.step_id}] 失败已跳过（策略 skip）"
                )

    except ExecutionError:
        # R6/D1-3：循环内取消（exporter/importer 抛出的取消链路）归并为
        # cancelled，与步骤间检查点（L114 段）同口径；非取消照常上抛
        if cancel_check is not None and cancel_check():
            status = "cancelled"
            logger.warning("[executor] 收到终止请求，执行已终止（循环内中断）")
        else:
            status = "failed"
            raise
    except Exception as e:
        status = "failed"
        logger.error(f"[executor] 未预期异常: {type(e).__name__}: {e}")
        raise

    finally:
        elapsed = time.time() - start_time
        mem_mb = psutil.Process().memory_info().rss / 1024 / 1024
        logger.info(
            f"[executor] 执行结束: {workflow.name}, 状态: {status}, "
            f"成功: {steps_succeeded}/{steps_total}, "
            f"总耗时: {elapsed:.2f}s, 内存: {mem_mb:.1f}MB"
        )

    # R6/D4（P2-4）：正常完成后统一清理中间表——keep_db=True 保留全部；
    # protected＝cp 步写回目标物理名（最终数据载体，与 P0-1 修复联动，
    # 不删）；失败/取消不清理（保留排查现场）。输入表物理名不经
    # output_tables 登记（语义＝派生表号→派生表物理名），天然不误删。
    if status == "completed" and not workflow.global_config.get("keep_db", False):
        protected = {st.params.get("output_table")
                     for st in workflow.steps
                     if st.type == "copy_table" and st.params.get("output_table")}
        for phys in list(output_tables.values()):
            if phys in protected:
                continue
            try:
                delete_table(conn, phys)
            except Exception as e:  # noqa: BLE001 清理失败不改执行结果
                logger.warning(f"[executor] 中间表清理失败（忽略）: {phys}: {e}")

    return {
        "success": status == "completed" and steps_succeeded == steps_total,
        "message": f"{steps_succeeded}/{steps_total} 步成功，状态 {status}",
        "steps_total": steps_total,
        "steps_succeeded": steps_succeeded,
        "status": status,
        "duration": elapsed,
        "output_tables": output_tables,
    }


def _execute_with_retry(
    step,
    conn: sqlite3.Connection,
    table_id_map: Dict[str, str],
    step_index: int,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """按 on_error 策略执行单步（retry 最多 retry_count 次）。"""
    step_dict = {
        "step_id": step.step_id,
        "type": step.type,
        "name": step.name,
        "target_table_id": step.target_table_id,
        "output_table_id": step.output_table_id,
        "params": step.params,
    }

    attempts = step.retry_count if step.on_error == "retry" else 1
    last_result: Dict[str, Any] = {"success": False, "message": "未执行"}

    for attempt in range(1, attempts + 1):
        last_result = execute_step(step_dict, conn, table_id_map, step_index,
                                   cancel_check)
        if last_result["success"]:
            return last_result
        if attempt < attempts:
            logger.warning(
                f"[executor] 步骤 [{step.step_id}] 第 {attempt} 次失败，重试 "
                f"({attempt + 1}/{attempts})"
            )

    return last_result
