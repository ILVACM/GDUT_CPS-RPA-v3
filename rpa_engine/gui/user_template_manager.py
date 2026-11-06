"""
rpa_engine/gui/user_template_manager.py

用户历史配置模板管理器（GUI 纯逻辑层）。

负责：用户配置另存为历史模板、加载、列表、删除，以及生成
"用户模板 + 预设模板"的合并列表。与 models.py 同风格：
纯逻辑层，仅依赖标准库 + loguru + engine.parser / engine.validator，
禁止 import 任何 Qt 模块。

存储规则（v3.1）：
1. 用户模板存于 storage_dir（默认 templates/user，相对 ENGINE_ROOT），
   文件顶层为 v3.1 配置平铺 + __meta 元信息：
   {"__meta": {"schema_version": "3.1", "source": "user",
               "created_at": "YYYY-MM-DD HH:MM:SS", "name": 显示名},
    "name": "...", "global": {...}, "tables": [...], "steps": [...]}
2. JSON 写入使用 ensure_ascii=False, indent=2, encoding="utf-8"
3. load 时剥离 __meta，返回 v3.1 配置 dict（与 model.to_dict() 同构）
4. parser/validator 忽略 __meta 额外键，落盘文件可直接通过双重校验
5. 预设模板扫描为递归：templates/ 下任意子目录的 .json 与 .jsonc（支持
   注释的 JSON，读取时剥离注释后按标准 JSON 处理）均可加载。
"""

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from engine.parser import parse_workflow, ParserError
from engine.validator import validate_workflow, ValidationError
from paths import get_engine_root, get_bundle_dir

ENGINE_ROOT = get_engine_root()
BUNDLE_DIR = get_bundle_dir()

# 模板名非法字符（含空白字符），统一替换为下划线
_ILLEGAL_NAME_PATTERN = re.compile(r'[\\/:*?"<>|\s]+')
_NAME_MAX_LEN = 30       # 模板名清洗后的截断长度
# 保存对话框默认名（时间戳占位名）经清洗后的形态，用于文件名去重
_DEFAULT_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}_\d{2}_\d{2}$")
_DEFAULT_NAME = "未命名"  # 清洗后为空时的兜底显示名

# 可加载的模板文件扩展名（预设递归扫描与导入共用）
_TEMPLATE_SUFFIXES = (".json", ".jsonc")


def _strip_jsonc_comments(text: str) -> str:
    """剥离 JSONC 注释（// 行注释、/* */ 块注释），保留字符串字面量。

    采用字符级状态机，仅剥离字符串外部的注释；字符串内的 "//"（如 URL）
    与转义序列 \" 不受影响。行注释保留换行符以维持结构。

    Args:
        text: 原始 JSONC 文本。

    Returns:
        str: 剥离注释后的标准 JSON 文本。
    """
    result: List[str] = []
    i, n = 0, len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            result.append(ch)
            if ch == "\\" and i + 1 < n:
                result.append(text[i + 1])   # 转义字符原样保留
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            result.append(ch)
            i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "/":
            # 行注释：跳到行尾（保留 \n）
            while i < n and text[i] != "\n":
                i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "*":
            # 块注释：跳到 */
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
        else:
            result.append(ch)
            i += 1
    return "".join(result)


def parse_template_file(path: Path) -> dict:
    """读取并解析模板文件（支持 .json/.jsonc），经引擎 parse_workflow 校验。

    .json 直接校验原文件；.jsonc 先剥离注释，经临时文件中转校验
    （引擎 parser 仅接受标准 JSON 文件）。

    Args:
        path: 模板文件路径。

    Returns:
        dict: 顶层为对象的 JSON 内容。

    Raises:
        ValueError: 文件不存在 / 读取失败 / JSON 解析失败 / 根节点非对象 /
            引擎校验未通过（均附中文说明）。
    """
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"模板文件不存在: {path.name}")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ValueError(f"模板文件读取失败: {path.name}: {e}") from e

    tmp_path: Optional[str] = None
    try:
        if path.suffix.lower() == ".jsonc":
            text = _strip_jsonc_comments(text)
            with tempfile.NamedTemporaryFile(
                "w", suffix=".json", delete=False, encoding="utf-8"
            ) as f:
                f.write(text)
                tmp_path = f.name
            validate_target = tmp_path
        else:
            validate_target = str(path)

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"模板文件损坏（JSON 解析失败）: {path.name}: {e}") from e
        if not isinstance(data, dict):
            raise ValueError(f"模板文件结构无效（根节点必须是对象）: {path.name}")
        try:
            parse_workflow(validate_target)
        except ParserError as e:
            raise ValueError(f"模板校验未通过: {path.name}: {e}") from e
        return data
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


class UserTemplateManager:
    """用户历史配置模板管理器（纯逻辑层，不依赖 GUI/Qt）。

    - 用户模板以 JSON 文件存于 storage_dir（默认 templates/user，相对
      ENGINE_ROOT 解析），文件头携带 __meta 元信息（source / created_at / name）。
    - 预设模板为只读资源，递归扫描 templates_root（默认 ENGINE_ROOT/templates）
      下任意子目录的 .json 与 .jsonc。
    - 保存前对配置执行 parse_workflow + validate_workflow 双重校验，
      校验失败时回滚已落盘文件，不留垃圾模板。
    """

    def __init__(self, storage_dir: str = "templates/user", templates_root: str = ""):
        """初始化模板管理器。

        Args:
            storage_dir: 用户模板存储目录；相对路径基于 ENGINE_ROOT 解析；
                默认 "templates/user"。目录不存在时自动创建
                （mkdir parents=True, exist_ok=True）。
            templates_root: 模板扫描根目录（递归扫描 .json/.jsonc）；相对路径
                基于 ENGINE_ROOT 解析；传空时默认 ENGINE_ROOT/"templates"。

        异常行为：mkdir 失败（磁盘/权限异常）时不抛出，仅记 logger.error，
        后续 save/list/delete 将按"目录不可用"返回失败或空结果。
        """
        self._storage_dir = self._resolve_dir(storage_dir, ENGINE_ROOT / "templates" / "user")
        # 预设模板为打包只读资源：frozen 下位于 _MEIPASS（datas 携带），
        # 开发环境与引擎根相同；用户模板始终落可写持久的 storage_dir
        self._templates_root = self._resolve_dir(templates_root, BUNDLE_DIR / "templates")
        try:
            self._storage_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"[user_template] 创建模板存储目录失败 {self._storage_dir}: {e}")

    @property
    def storage_dir(self) -> Path:
        """用户模板存储目录（保存成功提示展示路径用）。"""
        return self._storage_dir

    # ------------------------------------------------------------------ #
    # 公开 API
    # ------------------------------------------------------------------ #

    def save(self, name: str, config: dict, overwrite: bool = False) -> tuple[bool, str]:
        """保存用户配置为历史模板。

        Args:
            name: 模板显示名；非法字符与空白替换为下划线后用于文件名；
                为空时兜底为 "未命名"。
            config: v3.1 配置 dict（与 model.to_dict() 同构，含
                tables/steps 顶层键）。
            overwrite: 是否允许覆盖同名模板（按已有文件的 __meta.name 判定）。

        Returns:
            tuple[bool, str]: (是否成功, 消息)。
            - 重名且未授权覆盖：(False, "duplicate")
            - 结构非法 / 校验失败 / I/O 失败：(False, 中文错误信息)
            - 成功：(True, 文件名字符串)

        流程说明：先落盘 → parse_workflow + validate_workflow 双重校验 →
        任一失败则删除已落盘文件并返回失败。覆盖场景写入临时副本校验，
        通过后才替换原文件（保留原文件名与 created_at），原文件全程不受
        校验失败影响。
        """
        # 1. 入参结构检查（v3.1：tables 与 steps 必须为列表）
        if (not isinstance(config, dict)
                or not isinstance(config.get("tables"), list)
                or not isinstance(config.get("steps"), list)):
            logger.warning("[user_template] 保存失败：配置必须是 v3.1 结构（缺少 tables/steps）")
            return False, "保存失败：配置必须是 v3.1 结构（缺少 tables/steps）"

        display_name = str(name).strip() if name else ""
        if not display_name:
            display_name = _DEFAULT_NAME
        safe_name = self._sanitize_name(display_name)

        # 2. 重名判定（按已有文件的 __meta.name 精确匹配）
        existing_path = self._find_by_name(display_name)
        if existing_path is not None and not overwrite:
            logger.info(f"[user_template] 模板重名，已拒绝保存: {display_name}")
            return False, "duplicate"

        # 3. 构造目标路径与 __meta（覆盖时保留原 created_at）
        now = datetime.now()
        if existing_path is not None:
            created_at = self._read_created_at(existing_path) or now.strftime("%Y-%m-%d %H:%M:%S")
            target_path = existing_path
            tmp_path = existing_path.with_name(existing_path.name + ".tmp")
        else:
            created_at = now.strftime("%Y-%m-%d %H:%M:%S")
            target_path = self._alloc_filename(now, safe_name)
            tmp_path = target_path

        # v3.1 平铺存储：完整复制配置后，__meta 键最后写入（合并 config 自带的
        # schema_version，叠加 source/created_at/name；后写防止被 config 内
        # 的 __meta 覆盖）
        payload: Dict[str, Any] = dict(config)
        merged_meta: Dict[str, Any] = dict(config.get("__meta") or {})
        merged_meta.update({
            "source": "user",
            "created_at": created_at,
            "name": display_name,
        })
        payload["__meta"] = merged_meta

        # 4. 先落盘（覆盖场景写入临时副本，避免校验失败损坏原模板）
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except (OSError, TypeError, ValueError) as e:
            logger.error(f"[user_template] 模板文件写入失败 {tmp_path}: {e}")
            self._remove_quietly(tmp_path)
            return False, f"保存失败：模板文件写入失败（{e}）"

        # 5. 双重校验：解析 + 全量校验；失败即删除已落盘文件（回滚）
        try:
            workflow_def = parse_workflow(str(tmp_path))
            validate_workflow(workflow_def)
        except (ParserError, ValidationError) as e:
            logger.warning(f"[user_template] 模板校验失败，已回滚 {tmp_path.name}: {e}")
            self._remove_quietly(tmp_path)
            return False, f"保存失败：配置校验未通过（{e}）"
        except Exception as e:  # 兜底：防止意外异常遗留孤儿临时文件
            logger.error(
                f"[user_template] 校验过程意外异常，已回滚 {tmp_path.name}: {type(e).__name__}: {e}"
            )
            self._remove_quietly(tmp_path)
            return False, f"保存失败：校验过程异常（{e}）"

        # 6. 覆盖场景：校验通过后才原子替换原文件
        if existing_path is not None:
            try:
                os.replace(str(tmp_path), str(target_path))
            except OSError as e:
                logger.error(f"[user_template] 覆盖原模板失败 {target_path.name}: {e}")
                self._remove_quietly(tmp_path)
                return False, f"保存失败：覆盖原模板失败（{e}）"

        logger.info(f"[user_template] 模板已保存: {target_path.name}（显示名: {display_name}, 覆盖: {overwrite}）")
        return True, target_path.name

    def load(self, filename: str) -> dict:
        """加载指定用户模板，剥离 __meta 后返回 v3.1 配置 dict。

        Args:
            filename: 模板文件名（纯文件名，不允许包含目录分隔符）。

        Returns:
            dict: v3.1 配置结构（与 model.to_dict() 同构，含 tables/steps）。

        Raises:
            ValueError: 文件名非法 / 路径穿越 / 文件不存在 / 文件损坏（非 JSON）/
                结构无效（缺少 tables/steps），均附中文说明。
        """
        target = self._resolve_template_path(filename)  # 非法名/路径穿越在此抛 ValueError
        if not target.is_file():
            raise ValueError(f"模板文件不存在: {filename}")
        data = self._read_file(target)  # 损坏/非 JSON 在此抛 ValueError
        data.pop("__meta", None)
        if not isinstance(data.get("tables"), list):
            raise ValueError(f"模板文件结构无效（缺少 tables，非 v3.1 结构）: {filename}")
        return data

    def list_templates(self) -> list[dict]:
        """列出全部用户模板。

        Returns:
            list[dict]: 每项 {"name": 显示名, "filename": 文件名,
            "created_at": "YYYY-MM-DD HH:MM:SS", "source": "user"}，
            按 created_at 降序（缺失时视为空串排最后）。

        异常行为：存储目录不可用返回空列表；损坏/无法解析/缺少 __meta 的
        文件跳过并记 logger.warning，不抛异常。
        """
        items: List[Dict[str, Any]] = []
        if not self._storage_dir.is_dir():
            logger.warning(f"[user_template] 模板存储目录不存在: {self._storage_dir}")
            return items
        try:
            files = list(self._storage_dir.glob("*.json"))
        except OSError as e:
            logger.warning(f"[user_template] 扫描模板存储目录失败: {e}")
            return items

        for path in files:
            try:
                data = self._read_file(path)
            except ValueError as e:
                logger.warning(f"[user_template] 跳过不可读模板文件: {e}")
                continue
            meta = data.get("__meta")
            if not isinstance(meta, dict):
                logger.warning(f"[user_template] 跳过缺少 __meta 的模板文件: {path.name}")
                continue
            created_at = meta.get("created_at")
            items.append({
                "name": meta.get("name") or path.stem,
                "filename": path.name,
                "created_at": created_at if isinstance(created_at, str) else "",
                "source": "user",
            })

        # "YYYY-MM-DD HH:MM:SS" 格式可直接按字符串排序
        items.sort(key=lambda x: x["created_at"], reverse=True)
        return items

    def delete(self, filename: str) -> tuple[bool, str]:
        """删除指定用户模板。

        Args:
            filename: 模板文件名（纯文件名，不允许包含目录分隔符）。

        Returns:
            tuple[bool, str]: (是否成功, 中文消息)。
            文件名非法 / 路径穿越 / 文件不存在 / 删除时 I/O 异常均返回 (False, 原因)。

        异常行为：不抛出；路径穿越防护与 load 一致，仅允许删除
        storage_dir 内的文件。
        """
        try:
            target = self._resolve_template_path(filename)
        except ValueError as e:
            logger.warning(f"[user_template] 删除被拒绝: {e}")
            return False, str(e)
        if not target.is_file():
            logger.warning(f"[user_template] 删除失败，模板文件不存在: {filename}")
            return False, f"删除失败：模板文件不存在（{filename}）"
        try:
            target.unlink()
        except OSError as e:
            logger.error(f"[user_template] 删除模板文件失败 {filename}: {e}")
            return False, f"删除失败：{e}"
        logger.info(f"[user_template] 模板已删除: {filename}")
        return True, f"删除成功：{filename}"

    def get_merged_list(self) -> list[dict]:
        """生成"用户模板 + 预设模板"合并列表。

        Returns:
            list[dict]: 用户模板在前（即 list_templates 结果，created_at 降序），
            预设模板在后。预设模板为递归扫描 templates_root 全目录的
            .json/.jsonc 文件（任意子目录结构，排除用户模板目录），
            按相对路径升序。
            预设项结构: {"name": 不含扩展名的文件名, "filename": 文件名,
            "rel_path": 相对 templates_root 的路径（posix 格式）,
            "created_at": None, "source": "preset"}。

        异常行为：模板根目录不存在或扫描失败时仅记 logger.warning，
        返回仅含用户模板的列表，不抛异常。
        """
        merged: List[Dict[str, Any]] = list(self.list_templates())
        if not self._templates_root.is_dir():
            logger.warning(f"[user_template] 模板根目录不存在: {self._templates_root}")
            return merged
        try:
            candidates = sorted(self._templates_root.rglob("*"))
        except OSError as e:
            logger.warning(f"[user_template] 扫描模板根目录失败: {e}")
            return merged
        for path in candidates:
            if not path.is_file() or path.suffix.lower() not in _TEMPLATE_SUFFIXES:
                continue
            if self._is_within(path, self._storage_dir):
                continue   # 用户模板目录单独列出，避免重复
            try:
                rel = path.relative_to(self._templates_root).as_posix()
            except ValueError:
                continue
            merged.append({
                "name": path.stem,
                "filename": path.name,
                "rel_path": rel,
                "created_at": None,
                "source": "preset",
            })
        return merged

    def load_preset(self, rel_path: str) -> dict:
        """加载预设模板（支持 .json 与 .jsonc，templates_root 下任意子目录）。

        Args:
            rel_path: 模板文件相对 templates_root 的路径（来自合并列表的
                "rel_path" 字段）。

        Returns:
            dict: v3.1 配置结构（含 tables/steps；预设文件无 __meta）。

        Raises:
            ValueError: 路径穿越/越界 / 文件不存在 / 解析或校验失败 /
                缺少 tables（非 v3.1 结构）（均附中文说明）。
        """
        target = (self._templates_root / rel_path).resolve()
        if not self._is_within(target, self._templates_root):
            raise ValueError(f"模板路径非法（超出模板根目录）: {rel_path}")
        if not target.is_file():
            raise ValueError(f"模板文件不存在: {rel_path}")
        data = parse_template_file(target)
        if not isinstance(data.get("tables"), list):
            raise ValueError(f"模板文件结构无效（缺少 tables，非 v3.1 结构）: {rel_path}")
        return data

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #

    @staticmethod
    def _is_within(path: Path, directory: Path) -> bool:
        """判断 path 是否位于 directory 内（resolve 后比对）。

        Args:
            path: 待判定路径。
            directory: 参照目录。

        Returns:
            bool: 位于目录内返回 True；越界或解析异常返回 False。
        """
        try:
            path.resolve().relative_to(directory.resolve())
            return True
        except (ValueError, OSError):
            return False

    @staticmethod
    def _resolve_dir(dir_str: str, default: Path) -> Path:
        """解析目录参数：空值取默认目录；相对路径基于 ENGINE_ROOT 解析。

        Args:
            dir_str: 外部传入的目录字符串（可为空）。
            default: 为空时使用的默认目录（绝对路径）。

        Returns:
            Path: 解析后的绝对目录路径。
        """
        if dir_str:
            p = Path(dir_str)
            return p if p.is_absolute() else ENGINE_ROOT / p
        return default

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """模板名清洗（用于文件名部分）。

        规则：将 \\ / : * ? " < > | 及空白字符替换为下划线，截断至 30 字符，
        清洗后为空则返回 "未命名"。

        Args:
            name: 原始模板名（调用方保证非 None）。

        Returns:
            str: 可安全用于文件名的字符串。
        """
        cleaned = _ILLEGAL_NAME_PATTERN.sub("_", str(name))
        cleaned = cleaned[:_NAME_MAX_LEN]
        return cleaned if cleaned else _DEFAULT_NAME

    def _resolve_template_path(self, filename: str) -> Path:
        """路径穿越防护：将文件名解析为 storage_dir 内的安全路径。

        Args:
            filename: 外部传入的文件名。

        Returns:
            Path: 解析后的绝对路径（不要求文件存在）。

        Raises:
            ValueError: 文件名为空/非字符串、包含目录分隔符或 "."/".."，
                或解析后落在 storage_dir 之外。
        """
        if not filename or not isinstance(filename, str):
            raise ValueError("模板文件名无效（不能为空）")
        if filename in (".", "..") or "/" in filename or "\\" in filename:
            raise ValueError(f"模板文件名非法（不允许包含目录分隔符）: {filename}")
        target = (self._storage_dir / filename).resolve()
        try:
            target.relative_to(self._storage_dir.resolve())
        except ValueError as e:
            raise ValueError(f"模板文件路径非法（超出存储目录）: {filename}") from e
        return target

    def _read_file(self, path: Path) -> Dict[str, Any]:
        """读取并解析模板 JSON 文件。

        Args:
            path: 模板文件绝对路径。

        Returns:
            dict: 顶层为对象的 JSON 内容。

        Raises:
            ValueError: 文件不存在 / 非 JSON / 读取失败 / 根节点非对象（附中文说明）。
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as e:
            raise ValueError(f"模板文件不存在: {path.name}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"模板文件损坏（JSON 解析失败）: {path.name}: {e}") from e
        except OSError as e:
            raise ValueError(f"模板文件读取失败: {path.name}: {e}") from e
        if not isinstance(data, dict):
            raise ValueError(f"模板文件结构无效（根节点必须是对象）: {path.name}")
        return data

    def _find_by_name(self, display_name: str) -> Optional[Path]:
        """按 __meta.name 精确查找已有用户模板。

        Args:
            display_name: 模板显示名。

        Returns:
            Optional[Path]: 首个匹配文件的路径；无匹配或目录不可用时返回 None。
            损坏文件静默跳过（不参与重名判定）。
        """
        if not self._storage_dir.is_dir():
            return None
        try:
            candidates = sorted(self._storage_dir.glob("*.json"))
        except OSError as e:
            logger.warning(f"[user_template] 扫描存储目录失败（重名判定跳过）: {e}")
            return None
        for path in candidates:
            try:
                meta = self._read_file(path).get("__meta")
            except ValueError:
                continue
            if isinstance(meta, dict) and meta.get("name") == display_name:
                return path
        return None

    def _read_created_at(self, path: Path) -> str:
        """读取已有模板的 created_at（覆盖保存时保留原值）。

        Args:
            path: 已有模板文件路径。

        Returns:
            str: created_at 字符串；读取失败或字段缺失时返回空串（由调用方兜底）。
        """
        try:
            meta = self._read_file(path).get("__meta")
            if isinstance(meta, dict) and isinstance(meta.get("created_at"), str):
                return meta["created_at"]
        except ValueError as e:
            logger.warning(f"[user_template] 读取被覆盖模板的 created_at 失败 {path.name}: {e}")
        return ""

    def _alloc_filename(self, now: datetime, safe_name: str) -> Path:
        """生成不重复的模板文件名：{YYYYMMDD_HHmmss}_{sanitized_name}.json。

        默认名（保存对话框的时间戳占位名，如 2026-08-24_00_15_30，经
        _sanitize_name 清洗后形态）与文件名前缀时间戳重复，此时仅用
        {stamp}.json，不重复拼接。

        Args:
            now: 当前时间（决定文件名时间戳）。
            safe_name: 已清洗的模板名。

        Returns:
            Path: storage_dir 内尚不存在的目标文件路径
            （同秒极端碰撞时追加 _2/_3 序号后缀）。
        """
        stamp = now.strftime("%Y%m%d_%H%M%S")
        # 默认时间戳形态（%Y-%m-%d_%H:%M:%S 经清洗后的样子）
        if _DEFAULT_NAME_RE.match(safe_name):
            candidate = self._storage_dir / f"{stamp}.json"
        else:
            candidate = self._storage_dir / f"{stamp}_{safe_name}.json"
        seq = 2
        while candidate.exists():
            candidate = self._storage_dir / f"{stamp}_{safe_name}_{seq}.json"
            seq += 1
        return candidate

    @staticmethod
    def _remove_quietly(path: Path) -> None:
        """静默删除文件（校验失败回滚/写入失败清理用）。

        Args:
            path: 待删除文件路径；不存在时直接跳过。

        异常行为：删除失败仅记 logger.warning，不抛出。
        """
        try:
            if path.exists():
                path.unlink()
        except OSError as e:
            logger.warning(f"[user_template] 清理临时文件失败 {path}: {e}")
