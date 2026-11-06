# -*- coding: utf-8 -*-
"""
rpa_engine/paths.py

运行环境自适应路径解析（开发 / PyInstaller frozen 双环境）。

背景：onefile 编译版中 __file__ 指向解包临时目录（Temp\\_MEIxxxx），
退出即被 bootloader 删除——任何运行时可写数据（workspace/logs/temp/
用户模板）都不得基于 __file__ 定位。本模块是全库唯一的路径基准来源。

用法：
    from paths import get_engine_root, get_bundle_dir

    get_engine_root()   # 可写数据基准（exe 目录 / 开发环境 rpa_engine）
    get_bundle_dir()    # 只读资源基准（_MEIPASS / 开发环境同引擎根）
"""

import sys
from pathlib import Path


def is_frozen() -> bool:
    """是否运行于 PyInstaller 编译环境（frozen）。"""
    return getattr(sys, "frozen", False)


def get_engine_root() -> Path:
    """引擎根目录（运行时可写数据的基准）。

    - frozen（exe）：exe 所在目录（程序根，持久化；workspace/、logs/、
      temp/、templates/user/ 均创建于此）
    - 开发（python）：rpa_engine 源码目录

    Returns:
        Path: 引擎根目录（已 resolve）。
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_bundle_dir() -> Path:
    """只读资源基准目录（打包内置资源）。

    - frozen：PyInstaller 解包目录 sys._MEIPASS（spec datas 携带的
      templates 等预设资源位于此；目录只读且退出即销毁，禁止写入）
    - 开发：与引擎根相同

    Returns:
        Path: 只读资源基准目录（已 resolve）。
    """
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parent


def get_normalized_dir() -> Path:
    """规范化产物目录（H10，运行时可写）。

    位于引擎根的 `temp/normalized/`（与 `temp/input_selection/` 副本区分开，
    故不受副本超龄清理影响）。首次调用即按需创建。

    Returns:
        Path: 规范化产物目录（已创建，parents=True/exist_ok=True）。
    """
    d = get_engine_root() / "temp" / "normalized"
    d.mkdir(parents=True, exist_ok=True)
    return d
