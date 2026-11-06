"""
rpa_engine/main.py

工作流引擎入口（GUI 唯一交互入口）。

用法:
    python rpa_engine/main.py        # 启动 GUI 四阶段应用
    python -m rpa_engine.main

说明:
    CLI 交互已废弃并移除（见 docs/backlog.md W-18）。
    引擎仍可被程序化调用（engine.executor.execute_workflow），不依赖 GUI。
"""

import sys


def main() -> int:
    """GUI 入口。"""
    from gui.app import launch_gui

    return launch_gui()


if __name__ == "__main__":
    sys.exit(main())
