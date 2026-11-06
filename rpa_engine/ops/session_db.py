"""
rpa_engine/ops/session_db.py

Layer 0 — 会话数据库管理器。

SessionDB 是引擎中唯一有权创建 SQLite 连接的地方（AGENTS.md §2.2 条 4 红线：
步骤不得自行创建连接）。生命周期：阶段 1 确认导入时创建 → 阶段 2/3 共用 →
阶段 4 结束或"新一轮操作"时清理。

依赖库：sqlite3（内置）
"""

import sqlite3
from pathlib import Path
from typing import Optional

import gc

from loguru import logger


class SessionDB:
    """一轮操作专属的 SQLite 会话数据库。

    职责（单轨连接管理）：
    - 惰性创建连接并一次性启用 WAL + synchronous=NORMAL
    - 对外暴露 .conn 供各功能函数共享使用
    - 统一收口关闭与文件清理（.db/.db-wal/.db-shm）

    用法：
        sdb = SessionDB("session_20260823_153000")
        conn = sdb.conn            # 首次访问时建连
        ...
        sdb.close(keep_db=False)   # 关闭并清理文件
    """

    def __init__(self, session_id: str, db_dir: str = "workspace") -> None:
        """初始化会话数据库（不立即建连）。

        Args:
            session_id: 会话唯一标识（用作数据库文件名）。
            db_dir: 数据库文件存放目录，相对 rpa_engine 根解析。

        Raises:
            ValueError: session_id 为空。
        """
        if not session_id or not session_id.strip():
            raise ValueError("SessionDB: session_id 不能为空")

        self.session_id = session_id
        self._conn: Optional[sqlite3.Connection] = None

        from paths import get_engine_root
        engine_root = get_engine_root()
        db_dir_path = Path(db_dir)
        self.db_path = str(
            (db_dir_path if db_dir_path.is_absolute() else engine_root / db_dir_path)
            / f"{session_id}.db"
        )

        # 确保目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def new_connection(self) -> sqlite3.Connection:
        """创建新的 WAL 连接（线程亲和：供调用线程专属使用）。

        worker 线程执行工作流时必须用本方法在自己的线程内开连接，
        禁止跨线程传递 .conn（SQLite check_same_thread 限制）。
        WAL 模式天然支持多连接并发读写同一库文件。

        Returns:
            sqlite3.Connection: 已初始化 WAL 的新连接（调用方负责关闭）。
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        # R6/D1（P1-4/P2-12）：写锁冲突等待上限——双连接并存写同库时
        # 排队 5s 再报 SQLITE_BUSY，不再立即抛"未预期异常"
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    @property
    def conn(self) -> sqlite3.Connection:
        """主线程共享连接（惰性创建，WAL 模式只初始化一次）。

        注意：仅限创建线程使用（GUI 场景为主线程）；其他线程
        （如 worker QThread）请调 new_connection() 自建。
        """
        if self._conn is None:
            self._conn = self.new_connection()
            logger.info(f"[session_db] 会话数据库已连接: {self.db_path}（WAL）")
        return self._conn

    def table_id_map(self) -> dict:
        """返回 {sqlite表名: 表名} 映射的占位说明。

        实际 table_id → sqlite_table 映射由引擎层（parser 解析 tables[]）维护，
        SessionDB 不感知业务编号，保持 L0 纯净。
        """
        return {}

    def close(self, keep_db: bool = False) -> None:
        """关闭连接，按 keep_db 决定是否清理数据库文件。

        Args:
            keep_db: True 保留 .db 文件（调试/留存数据）；False 删除全部相关文件。
        """
        if self._conn is not None:
            try:
                self._conn.commit()
            except sqlite3.Error as e:
                logger.warning(f"[session_db] 关闭前 commit 失败（忽略）: {e}")
            self._conn.close()
            self._conn = None
            logger.info(f"[session_db] 连接已关闭: {self.db_path}")

        if keep_db:
            logger.info(f"[session_db] 保留数据库文件: {self.db_path}")
            return

        removed = 0
        for suffix in ("", "-wal", "-shm"):
            file_path = Path(self.db_path + suffix)
            if file_path.is_file():
                try:
                    file_path.unlink()
                    removed += 1
                except OSError as e:
                    logger.warning(f"[session_db] 清理失败 {file_path}: {e}")
        if removed:
            logger.info(f"[session_db] 已清理 {removed} 个数据库相关文件")
        gc.collect()
