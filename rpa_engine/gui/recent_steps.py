"""
rpa_engine/gui/recent_steps.py

最近使用功能步骤持久化（2026-09-21 定稿 Q2/M3-T4）。

落盘 ``storage/recent_steps.json``（范式参照 user_template_manager：
storage_dir + JSON，不引 QSettings）；≤5 项、去重、文件缺失/损坏静默
回退空列表（降级不崩）。
"""

import json
from pathlib import Path
from typing import List

from loguru import logger

from paths import get_engine_root

_MAX_RECENT = 5


def _recent_file() -> Path:
    return get_engine_root() / "storage" / "recent_steps.json"


def load_recent() -> List[str]:
    """读取最近使用 key 列表（新→旧）；任何异常回退空列表。"""
    path = _recent_file()
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [str(x) for x in data if isinstance(x, str)][:_MAX_RECENT]
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
        logger.debug(f"[recent_steps] 读取失败（回退空列表）: {e}")
    return []


def push_recent(key: str) -> None:
    """将 key 置顶写入最近使用（去重、截断 ≤5）；写失败仅记 DEBUG。"""
    if not key:
        return
    items = [k for k in load_recent() if k != key]
    items.insert(0, key)
    items = items[:_MAX_RECENT]
    path = _recent_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(items, ensure_ascii=False),
                        encoding="utf-8")
    except OSError as e:
        logger.debug(f"[recent_steps] 写入失败（忽略）: {e}")
