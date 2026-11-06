"""gui/error_messages.py — 用户可见错误话术翻译层（R6/B1，P0-2）。

分层纪律：引擎/ops 保持原始错误进日志（排查用）；本模块只在 GUI 出口
（失败气泡/弹窗/报告页失败原因/导入失败清单）把原始文本翻译成人话＋
下一步动作。文案遵守 architecture.md §8.4 禁用词口径（SQL/表名/SQLite/
物理名等技术词不出现在返回值中）。规则按序匹配，首个命中生效；未命中
走兜底话术＋日志目录指引。

纯标准库＋paths，禁 Qt（可被 tests/ 直接单测）。
"""

from pathlib import Path

from paths import get_engine_root

_FALLBACK = "程序遇到意外问题，本次操作未完成。"
_NEXT_FALLBACK = "请把日志文件发给管理员查看。"

# (匹配子串小写, 人话原因, 下一步动作)——按序匹配，特异规则在前
_RULES = [
    ("modulenotfounderror", "程序缺少读取该文件所需的功能组件。",
     "请把日志文件发给管理员（此为交付包不完整，非文件问题）。"),
    ("标识符包含禁止字符", "该数据表的表头里有不可用的字符（常见为换行或制表符）。",
     "请在 Excel 中清理该表头后重新导入。"),
    ("文件不是 excel 格式", "所选文件不是 Excel 格式，无法读取。",
     "请确认文件为 .xlsx 或 .xls 后重试。"),
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
    ("收到终止请求", "本次操作已按您的要求终止。",
     "如需继续，请重新开始执行。"),
    ("步骤执行超时", "本步骤处理时间超出上限。",
     "请缩小数据范围后重试，或联系管理员调整上限。"),
    ("请升级程序", "该文件由更新版本的程序生成。",
     "请升级程序后再打开此文件。"),
]


def translate_error(raw) -> str:
    """原始错误文本 → 人话（原因＋下一步）。空/None 走兜底。"""
    if not raw:
        return f"{_FALLBACK}{_NEXT_FALLBACK}"
    low = str(raw).lower()
    for key, reason, action in _RULES:
        if key in low:
            return f"{reason}{action}"
    return f"{_FALLBACK}{_NEXT_FALLBACK}"


def log_hint() -> str:
    """返回当前日志目录提示（供弹窗"详细日志"指引）。"""
    return str(Path(get_engine_root()) / "logs")
