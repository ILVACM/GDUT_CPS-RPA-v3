"""
rpa_engine/ops/excel_preprocessor.py

Layer 0 — Excel 预处理模块。

提供 Excel 文件的复制入临时区、xls→xlsx 全量转换、sheet 元信息扫描
（只读名称/行列数，不读单元格内容）和按表头行读取功能。

设计要点：
- 表头行处理采用读取时 skiprows 物化（D5 决策）：用户选择第 N 行为表头时，
  读取参数 skiprows=N-1 使第 N 行上移为首行，不改临时区文件本体。
- 所有列名原样保留，不做任何改名清洗（D10 决策：所见即所得）。

依赖库：pandas>=2.0, openpyxl>=3.1, xlrd>=2.0（.xls 读取）
"""

import gc
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

# 大文件分块读取阈值（行数），超过后调用方应使用分块导入
CHUNK_ROW_THRESHOLD = 1_000_000


def validate_and_copy(file_path: str, temp_dir: str = "temp/input_selection") -> str:
    """复制 Excel 文件到临时区，返回临时副本路径。

    Args:
        file_path: 原始 Excel 文件路径（支持相对/绝对路径）。
        temp_dir: 临时目录路径，默认为 "temp/input_selection"。

    Returns:
        str: 复制后的临时文件绝对路径。

    Raises:
        FileNotFoundError: 原始文件不存在。
        PermissionError: 文件读取/写入权限不足。
        ValueError: 文件不是 Excel 格式（.xlsx/.xls）。
    """
    src = Path(file_path).resolve()

    if not src.is_file():
        raise FileNotFoundError(f"Excel 文件不存在: {file_path}")

    if src.suffix.lower() not in (".xlsx", ".xls"):
        raise ValueError(f"文件不是 Excel 格式（.xlsx/.xls）: {src.suffix}")

    temp_path = Path(temp_dir)
    if not temp_path.is_absolute():
        from paths import get_engine_root
        temp_path = get_engine_root() / temp_dir
    temp_path.mkdir(parents=True, exist_ok=True)

    # 同名冲突时加序号后缀，避免多文件同名互相覆盖
    # R11/A-12（A-18 同处）：查重口径扩展为**跨后缀**——.xls 副本的转换产物
    # 就是同名的 .xlsx；只比同后缀会让转换产物覆盖既有 .xlsx 副本。
    dst = temp_path / src.name
    counter = 1
    while dst.exists() or (temp_path / f"{dst.stem}.xlsx").exists():
        dst = temp_path / f"{src.stem}_{counter}{src.suffix}"
        counter += 1

    # R11/A-11：只复制内容、不继承源文件 mtime——超龄清理的判据必须只反映
    # "副本在本机的存活时长"；沿用 copy2 会让源文件较旧的 .xlsx 副本在下次
    # 启动时立刻被判超龄而误删。
    shutil.copyfile(src, dst)
    os.utime(dst, None)
    logger.info(f"[excel_preprocessor] 文件复制到临时区: {src.name} -> {dst.name}")
    return str(dst)


def ensure_xlsx(file_path: str) -> str:
    """确保文件为 xlsx 格式；xls 则全量转换（保留全部 sheet 与原始列名）。

    v3.1 修复要点：
    - 转换遍历全部 sheet（旧实现只读第一个 sheet，丢数据）
    - 列名原样写入，不做空格/横线替换（D10：所见即所得）

    Args:
        file_path: Excel 文件路径（.xlsx/.xls）。

    Returns:
        str: xlsx 文件路径（已是 xlsx 时返回原路径；转换时返回新路径）。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: 文件后缀既非 .xlsx 也非 .xls。
    """
    src = Path(file_path).resolve()

    if not src.is_file():
        raise FileNotFoundError(f"Excel 文件不存在: {file_path}")

    if src.suffix.lower() == ".xlsx":
        logger.info(f"[excel_preprocessor] 文件已是 xlsx 格式: {src.name}")
        return str(src)

    if src.suffix.lower() != ".xls":
        raise ValueError(f"不支持的文件后缀: {src.suffix}（仅支持 .xlsx/.xls）")

    logger.info(f"[excel_preprocessor] 转换 .xls -> .xlsx: {src.name}")

    # sheet_name=None 读取全部 sheet → {sheet名: DataFrame}
    sheets = pd.read_excel(src, engine="xlrd", sheet_name=None)

    from openpyxl import Workbook

    wb = Workbook()
    # 移除默认空 sheet
    wb.remove(wb.active)

    for sheet_name, df in sheets.items():
        ws = wb.create_sheet(title=str(sheet_name)[:31])  # sheet 名上限 31 字符
        # 表头原样写入（不做任何清洗替换）
        ws.append(list(df.columns))
        for row in df.itertuples(index=False, name=None):
            ws.append(list(row))

    # R11/A-12（A-18 同处）：转换产物加序号，禁止静默覆盖已存在的同名 .xlsx
    new_path = src.with_suffix(".xlsx")
    counter = 1
    while new_path.exists():
        new_path = src.with_name(f"{src.stem}_{counter}.xlsx")
        counter += 1
    sheet_count = len(wb.sheetnames)
    wb.save(str(new_path))
    wb.close()

    del sheets
    gc.collect()
    logger.info(
        f"[excel_preprocessor] 转换完成: {src.name} -> {new_path.name}"
        f"（{sheet_count} 个 sheet 全量保留）"
    )
    return str(new_path)


def scan_sheets(file_path: str) -> List[Dict[str, Any]]:
    """扫描 Excel 文件的全部数据表元信息（只读名称与行列数，不读单元格内容）。

    Args:
        file_path: xlsx 文件路径。

    Returns:
        List[Dict[str, Any]]: 每项 {"sheet_name": str, "rows": int, "cols": int}。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: 文件不是 .xlsx 格式。
    """
    src = Path(file_path)

    if not src.is_file():
        raise FileNotFoundError(f"Excel 文件不存在: {file_path}")

    if src.suffix.lower() != ".xlsx":
        raise ValueError(f"scan_sheets 仅支持 .xlsx（请先 ensure_xlsx）: {src.suffix}")

    from openpyxl import load_workbook

    # read_only 模式：只解析结构元信息，不加载单元格数据到内存
    wb = load_workbook(str(src), read_only=True, data_only=True)
    try:
        result = []
        for name in wb.sheetnames:
            ws = wb[name]
            result.append({
                "sheet_name": name,
                "rows": ws.max_row or 0,
                "cols": ws.max_column or 0,
            })
        logger.info(f"[excel_preprocessor] 扫描完成: {src.name}, {len(result)} 个数据表")
        return result
    finally:
        wb.close()


def read_header_row(file_path: str, sheet_name: str,
                    header_row: int) -> Optional[List[Any]]:
    """R11/REQ-R2：只读取出指定表头行的原始单元格值（不读整表）。

    供"指定表头行是否全空"的前置校验使用：read_only 模式只解析目标行，
    避免为一次校验而加载整表（内存安全：内存安全基线 §5.2）。

    Args:
        file_path: xlsx 文件路径。
        sheet_name: 目标 sheet 名称。
        header_row: 表头行号（1 起始）。

    Returns:
        Optional[List[Any]]: 该行的原值列表；行号越界（<1 或 > 总行数）返回 None。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: 文件不是 .xlsx，或 sheet 不存在。
    """
    src = Path(file_path)

    if not src.is_file():
        raise FileNotFoundError(f"Excel 文件不存在: {file_path}")

    if src.suffix.lower() != ".xlsx":
        raise ValueError(
            f"read_header_row 仅支持 .xlsx（请先 ensure_xlsx）: {src.suffix}")

    from openpyxl import load_workbook

    wb = load_workbook(str(src), read_only=True, data_only=True)
    try:
        if sheet_name not in wb.sheetnames:
            raise ValueError(f"数据表不存在: {sheet_name}，可用: {wb.sheetnames}")
        ws = wb[sheet_name]
        max_row = ws.max_row or 0
        if header_row < 1 or header_row > max_row:
            return None
        return [cell.value for cell in ws[header_row]]
    finally:
        wb.close()


def read_excel_sheet(
    file_path: str,
    sheet_name: str,
    header_row: int = 1,
    sheet_info: Optional[List[Dict[str, Any]]] = None,
) -> pd.DataFrame:
    """读取指定 sheet，按表头行物化为标准格式（首行恒为表头）。

    表头行处理（D5）：header_row 为用户视角的 1 起始行号；skiprows=header_row-1
    使该行上移为首行，等效于"删除前 N-1 行"，但不改临时文件本体。

    Args:
        file_path: xlsx 文件路径。
        sheet_name: 目标 sheet 名称。
        header_row: 表头所在行号（1 起始，默认 1）。

    Returns:
        pd.DataFrame: 首行为表头的标准数据。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: header_row < 1 或 sheet 不存在。
    """
    src = Path(file_path)

    if not src.is_file():
        raise FileNotFoundError(f"Excel 文件不存在: {file_path}")

    if not isinstance(header_row, int) or header_row < 1:
        raise ValueError(f"header_row 必须为 ≥1 的整数，当前值: {header_row}")

    # 先校验 sheet 存在（给出明确报错而非 pandas 的 KeyError）
    # R6/D8（P3-6）：调用方已扫描时经 sheet_info 复用，消除重复开簿
    names = [s["sheet_name"]
             for s in (sheet_info if sheet_info is not None
                       else scan_sheets(str(src)))]
    if sheet_name not in names:
        raise ValueError(f"数据表不存在: {sheet_name}，可用: {names}")

    # R11/A-08：把"什么算空值"的决定权从 pandas 收回本程序——字面文本
    # （NA／N/A／None／null/#N/A 等）读取时原样保留，交由 normalizer 的
    # apply_na_policy 按策略决定（否则 pandas 默认 STR_NA_VALUES 会静默
    # 把它们吞成 NULL，原文彻底消失）。read_excel_sheet 的签名与返回值不变。
    # R11/A-04：dtype=object 抑制 pandas 的数值强转——文本型数字列（前导零
    # 编码如 "007"、超长数字如身份证/订单号）在读取阶段不得被转成 int/float
    # （原缺陷：无 dtype 约束 → pandas 强转 int64 → 前导零不可逆丢失）。
    # 类型推断交由 normalizer 的 infer_cell_type 按 R6 阈值完成。
    df = pd.read_excel(
        str(src),
        sheet_name=sheet_name,
        skiprows=header_row - 1,   # 物化"删前 N-1 行"
        header=0,                  # 跳过后的首行作为表头
        keep_default_na=False,     # R11/A-08：字面 NA 原样保留
        na_values=[],              # R11/A-08：不把任何字面文本当作缺失值
        dtype=object,              # R11/A-04：抑制数值强转（保留前导零/长数字）
    )
    logger.info(
        f"[excel_preprocessor] 读取: {src.name}[{sheet_name}], "
        f"表头行: {header_row}, 行数: {len(df)}, 列数: {len(df.columns)}"
    )
    return df


def clean_alias_name(raw_name: str, max_len: int = 50) -> str:
    """清洗默认标识名称：剔除易致渲染异常的字符并截断长度。

    仅用于生成"默认别名"（{文件名}-sheet_{sheet名}）；用户自定义名称
    不经过本函数（所见即所得，仅 GUI 层限长）。

    Args:
        raw_name: 原始名称。
        max_len: 最大长度（中文字符计），默认 50。

    Returns:
        str: 清洗后的名称（可能为空串，调用方需兜底）。
    """
    import re

    # 剔除空白、控制字符及常见易致渲染/路径异常的符号，保留中英文/数字/下划线/横线
    cleaned = re.sub(r"[\s\x00-\x1f\"'<>|:*?/\\{}()\[\]#$%@!^&+=~`;,]+", "", str(raw_name))
    cleaned = cleaned.strip("_-")

    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    return cleaned
