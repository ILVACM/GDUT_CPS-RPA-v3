"""
rpa_engine/gui/forms.py

v3.1 操作参数表单：BaseParamForm 基类 + 9 类操作专用表单。

表单为可内嵌 QWidget（直接放入配置页右侧面板，无弹窗）：
- 编辑控件面向文员设计：下拉选择 / 文件浏览 / 逐行键值编辑，避免裸 JSON
- 参数收拢统一走 try_apply()（配置页在切换步骤/保存/开始时调用）

复用约定：
- 表单构造参数 (params, table_ids, conn_columns, parent)：
  table_ids: 当前可选数据表编号列表
  conn_columns: {table_id: [列名]} 供列名下拉/校验（可空 = 不校验列名）
"""

from typing import Any, Dict, List, Optional, Tuple

import re

from PyQt5.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QSpinBox,
    QVBoxLayout, QWidget,
)

# 注册表单一源（2026-09-20 M21）：操作目录与产出边标签一律取自 gui.models，
# 本文件禁止另立操作清单或标签字面量（如「复制新表」）
# R15/B-60：前端键「结果保存方式」键名与取值同样取自 gui.models 常量
from gui.models import (OUTPUT_MODE_KEY, OUTPUT_MODE_NEW, OUTPUT_MODE_OVERWRITE,
                        STEP_CATALOG, produce_label)

# 操作符白名单单一源（R6/F4，2026-09-24）：一律派生自引擎
# ops.sql_safety.SUPPORTED_OPERATORS，本文件禁止另立操作符字面量清单。
# _OPS_ORDER 仅定义界面下拉展示顺序（常用子集），不在引擎白名单内的项自动剔除。
from ops.sql_safety import SUPPORTED_OPERATORS

_OPS_ORDER = ["=", "!=", ">", "<", ">=", "<=",
              "LIKE", "NOT IN", "IN", "IS NULL", "IS NOT NULL"]
_OPS = [op for op in _OPS_ORDER if op in SUPPORTED_OPERATORS]

# 聚合函数
_AGGS = ["count", "sum", "mean", "max", "min"]

# R11/A-07（H2）：日期形态条件值——命中者不作 _maybe_number 数值转换，
# 以免把 "2026-02-20" 之类的日期值改写成数字（裁定 G8：用户输入不得被程序改写）。
_DATE_VALUE_RE = re.compile(
    r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}([ T]\d{1,2}:\d{2}(:\d{2})?)?$")

# 类型转换对
_DTYPES = ["TEXT", "INTEGER", "REAL"]

# JOIN 模式（中文显示）
_JOIN_MODES = [
    ("left_join", "保留左表全部行（未匹配补空）"),
    ("inner_join", "只保留两表都匹配的行"),
    ("right_join", "保留右表全部行（未匹配补空）"),
    ("full_join", "保留两表全部行（未匹配都补空）"),
]

# 「结果保存方式」选项（2026-09-20 M24）：前端键 output_mode，导出时由
# models.to_dict 翻译为后端参数并剔除该键；覆盖原表属破坏性操作，
# 配置页保存时须二次确认（M25）；键名/取值引用 gui.models 集中常量（R15/B-60）
_OUTPUT_MODES = [
    (OUTPUT_MODE_NEW, "另存为新表"),
    (OUTPUT_MODE_OVERWRITE, "覆盖原表"),
]


def _is_overwritable(op_key: str) -> bool:
    """该操作是否挂载「结果保存方式」下拉（R15/B-65，原编号 D3）。

    单一源＝引擎 `ops/step_executor.BUILTIN_OPS[op_key]["overwritable"]`；
    替代原先"靠哪些表单恰好调了 `_add_output_mode`"的隐式表达——新增可覆盖
    操作时只改引擎声明，表单自动跟随（守卫见 tests/test_registry_guards.py）。
    """
    from engine.registry import BUILTIN_OPS
    return bool(BUILTIN_OPS.get(op_key, {}).get("overwritable"))


class BaseParamForm(QWidget):
    """参数表单基类：QFormLayout 中文标签的可内嵌控件（无弹窗）。

    参数收拢由外部调用 try_apply()（配置页在切换步骤/保存/开始时调用）；
    子类实现 get_params() / validate_params()。
    """

    def __init__(
        self,
        params: Dict[str, Any],
        table_ids: Optional[List[str]] = None,
        conn_columns: Optional[Dict[str, List[str]]] = None,
        parent: Optional[QWidget] = None,
        source_dir: str = "",
        registry: Optional[List[Dict[str, Any]]] = None,
        target_table_id: str = "",
    ) -> None:
        super().__init__(parent)
        self._init_params = dict(params)
        self._table_ids = table_ids or []
        self._conn_columns = conn_columns or {}
        self._source_dir = source_dir
        self._registry = registry or []
        self._target_table_id = target_table_id
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._form = QFormLayout()
        self._layout.addLayout(self._form)

    def get_params(self) -> Dict[str, Any]:
        """子类实现：收集控件值，返回参数字典。

        允许抛出 ValueError（格式无法解析），由 try_apply 统一捕获。
        """
        return {}

    def validate_params(self, params: Dict[str, Any]) -> Optional[str]:
        """可覆写校验钩子：返回错误文案则校验不通过，None 表示通过。"""
        return None

    def _check_columns(self, table_id: str, columns: List[str],
                       label: str) -> Optional[str]:
        """校验列名均存在于指定表（conn_columns 数据源）。

        conn_columns 缺该表或列清单为空时跳过（派生表/旧模板，
        运行期引擎守卫兜底）；"*"（整表计数通配）放行。

        Args:
            table_id: 数据表编号。
            columns: 待校验列名列表。
            label: 错误文案中的字段名（如"匹配列"）。

        Returns:
            Optional[str]: 无问题返回 None；否则返回中文错误描述。
        """
        known = self._conn_columns.get(table_id) or []
        if not known:
            return None
        bad = [c for c in columns if c and c != "*" and c not in known]
        if bad:
            return (f"{label}不存在: {'、'.join(bad)}，"
                    f"可用列: {'、'.join(known)}")
        return None

    def _add_output_mode(self, params: Dict[str, Any]) -> QComboBox:
        """追加「结果保存方式」下拉行（2026-09-20 M24，仅产表类表单调用）。

        默认「另存为新表」（防误触）；回填沿用既有 findData + max(idx,0) 范式。

        Args:
            params: 表单初始参数（读取 output_mode）。

        Returns:
            QComboBox: 已挂载到表单的下拉控件（currentData 即 output_mode 值）。
        """
        combo = QComboBox()
        for value, text in _OUTPUT_MODES:
            combo.addItem(text, value)
        idx = combo.findData(params.get(OUTPUT_MODE_KEY, OUTPUT_MODE_NEW))
        combo.setCurrentIndex(max(idx, 0))
        self._form.addRow("结果保存方式", combo)
        return combo

    def try_apply(self) -> Tuple[bool, Any]:
        """收集并校验参数。

        Returns:
            Tuple[bool, Any]: (True, params_dict) 或 (False, 中文错误文案)。
        """
        try:
            params = self.get_params()
        except ValueError as e:
            return False, str(e)
        err = self.validate_params(params)
        if err:
            return False, err
        return True, params


# ---------------------------------------------------------------------------
# 通用编辑辅助
# ---------------------------------------------------------------------------

def parse_pair_lines(text: str) -> Dict[str, str]:
    """解析"键=值"逐行文本为字典（空行/无=行忽略）。"""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip()
        if k and v:
            result[k] = v
    return result


def parse_token_list(text: str) -> List[str]:
    """解析逗号/顿号分隔文本为列表（去空去重）。"""
    tokens = [t.strip() for t in text.replace("，", ",").split(",")]
    seen: List[str] = []
    for t in tokens:
        if t and t not in seen:
            seen.append(t)
    return seen


def parse_list_value(text: str) -> List[str]:
    """解析 IN/NOT IN 的值文本为列表（逗号/顿号分隔，去空，保原文本）。

    可选的圆括号包裹一并去除（"IN (a, b)" 与 "IN a、b" 等价）。返回值恒为
    字符串列表，供 build_where 的 IN/NOT IN 分支使用；与 format_conditions
    的 list 渲染共守往返一致（R11/B-14＋B-28 共用同一解析实现）。
    """
    t = text.strip()
    if t.startswith("(") and t.endswith(")"):
        t = t[1:-1]
    return [p.strip() for p in re.split(r"[，,、]", t) if p.strip()]


def parse_condition_lines(text: str) -> List[Dict[str, Any]]:
    """解析"列 操作符 值"逐行文本为条件列表（操作符两字符以上）。"""
    conditions: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        matched = False
        for op in sorted(_OPS, key=len, reverse=True):
            if f" {op} " in line:
                col, _, rest = line.partition(f" {op} ")
                col, val = col.strip(), rest.strip()
                if col and val:
                    if op in ("IN", "NOT IN"):
                        # R11/B-14：IN/NOT IN 值必须解析为 list（逗号/顿号分隔），
                        # 跳过 _maybe_number，避免被转成标量致 build_where 校验失败
                        value = parse_list_value(val)
                    else:
                        # R11/A-07：日期形态值保原始文本（不转数字，遵裁定 G8）
                        value = (val if _DATE_VALUE_RE.match(val)
                                 else _maybe_number(val))
                    conditions.append({"column": col, "op": op, "value": value})
                    matched = True
                break
        if not matched:
            # IS NULL 形态： "列 IS NULL"
            for op in ("IS NULL", "IS NOT NULL"):
                if line.upper().endswith(f" {op}"):
                    col = line[: -len(op) - 1].strip()
                    if col:
                        conditions.append({"column": col, "op": op, "value": None})
                        matched = True
                    break
        if not matched:
            raise ValueError(f"条件格式无法解析: {line}（格式：列 操作符 值，如：区域 = 东区）")
    return conditions


def _maybe_number(val: str) -> Any:
    """数值形态的字符串转为数字（否则原样返回）。"""
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        return val


def format_conditions(conditions: List[Dict[str, Any]]) -> str:
    """条件列表 → 逐行文本（表单回填）。"""
    lines = []
    for c in conditions or []:
        if c.get("op") in ("IS NULL", "IS NOT NULL"):
            lines.append(f"{c['column']} {c['op']}")
            continue
        value = c.get("value", "")
        if isinstance(value, (list, tuple)):
            # R11/B-28：list 值以顿号连接渲染（不输出 Python repr），
            # 与 parse_condition_lines 的 list 解析往返一致
            value = "、".join(str(v) for v in value)
        lines.append(f"{c['column']} {c['op']} {value}")
    return "\n".join(lines)


def format_pairs(d: Dict[str, str]) -> str:
    """字典 → "键=值" 逐行文本（表单回填）。"""
    return "\n".join(f"{k}={v}" for k, v in (d or {}).items())


# ---------------------------------------------------------------------------
# 9 类操作专用表单
# ---------------------------------------------------------------------------

class FilterForm(BaseParamForm):
    """filter：条件筛选（条件逐行编辑）。"""

    def __init__(self, params, table_ids=None, conn_columns=None,
                 parent=None, **kwargs):
        super().__init__(params, table_ids, conn_columns, parent,
                         **kwargs)
        self.setWindowTitle("条件筛选参数")
        self._edit = QPlainTextEdit(format_conditions(params.get("conditions", [])))
        self._edit.setPlaceholderText(
            "每行一个条件，格式：列名 操作符 值\n例如：\n区域 = 东区\n电费 金额 > 100\n"
            "日期请填 YYYY-MM-DD；如需精确到时刻请填 YYYY-MM-DD HH:MM:SS")
        # R11/A-07（G10 条件框加格式提示）：日期格式提示（不改写用户输入）
        self._edit.setToolTip(
            "日期条件请按 YYYY-MM-DD 填写（例：日期 = 2026-02-20）；"
            "如需精确到时刻请填 YYYY-MM-DD HH:MM:SS")
        self._form.addRow("筛选条件（全部满足）", self._edit)
        self._out_mode = (self._add_output_mode(params)
                          if _is_overwritable("filter") else None)

    def get_params(self):
        # R6/A4（P2-5）：删除硬编码 "logic": "AND" 输出——本表单无 logic
        # 控件，无控件不输出该键；params 既有 logic 值（含外部 JSON 的
        # "OR"）经表单收拢增量合并保留。消费端默认取自引擎 params_schema
        # （step_executor 的 param_default，R15/B-41 单源）。
        out = {"conditions": parse_condition_lines(self._edit.toPlainText())}
        if self._out_mode is not None:
            out[OUTPUT_MODE_KEY] = self._out_mode.currentData()
        return out

    def validate_params(self, params):
        if not params["conditions"]:
            return "至少需要一个筛选条件"
        return None


class DedupForm(BaseParamForm):
    """dedup：条件去重。"""

    def __init__(self, params, table_ids=None, conn_columns=None,
                 parent=None, **kwargs):
        super().__init__(params, table_ids, conn_columns, parent,
                         **kwargs)
        self.setWindowTitle("条件去重参数")
        self._keys = QLineEdit("，".join(params.get("key_columns", [])))
        self._keys.setPlaceholderText("用于判断重复的列名，逗号分隔，如：名称, 日期")
        self._form.addRow("去重依据列", self._keys)
        self._keep = QComboBox()
        self._keep.addItem("保留第一次出现", "first")
        self._keep.addItem("保留最后一次出现", "last")
        idx = self._keep.findData(params.get("keep", "first"))
        self._keep.setCurrentIndex(max(idx, 0))
        self._form.addRow("保留策略", self._keep)
        self._out_mode = (self._add_output_mode(params)
                          if _is_overwritable("dedup") else None)

    def get_params(self):
        out = {"key_columns": parse_token_list(self._keys.text()),
               "keep": self._keep.currentData()}
        if self._out_mode is not None:
            out[OUTPUT_MODE_KEY] = self._out_mode.currentData()
        return out

    def validate_params(self, params):
        if not params["key_columns"]:
            return "至少需要一列作为去重依据"
        return None


class MappingMatchForm(BaseParamForm):
    """mapping_match：跨表映射匹配。"""

    def __init__(self, params, table_ids=None, conn_columns=None,
                 parent=None, **kwargs):
        super().__init__(params, table_ids, conn_columns, parent,
                         **kwargs)
        self.setWindowTitle("跨表映射匹配参数")
        self._match_table = QComboBox()
        for tid in (table_ids or []):
            self._match_table.addItem(tid, tid)
        cur = params.get("match_table_id", "")
        idx = self._match_table.findData(cur)
        self._match_table.setCurrentIndex(max(idx, 0))
        self._form.addRow("匹配的数据表（编号）", self._match_table)

        self._columns = QPlainTextEdit(format_pairs(params.get("match_columns", {})))
        self._columns.setPlaceholderText("每行一对匹配列，格式：本表列=匹配表列\n例如：\n名称=名称\n编号=单号")
        self._form.addRow("匹配列对应", self._columns)

        self._mode = QComboBox()
        for data, text in _JOIN_MODES:
            self._mode.addItem(text, data)
        idx = self._mode.findData(params.get("mode", "left_join"))
        self._mode.setCurrentIndex(max(idx, 0))
        self._form.addRow("匹配方式", self._mode)

    def get_params(self):
        return {
            "match_table_id": self._match_table.currentData() or "",
            "match_columns": parse_pair_lines(self._columns.toPlainText()),
            "mode": self._mode.currentData(),
        }

    def validate_params(self, params):
        if not params["match_table_id"]:
            return "请选择匹配的数据表"
        if not params["match_columns"]:
            return "至少需要一对匹配列"
        # 匹配表（右表）列存在性校验（表单知道 match_table_id）；
        # 本表（左表）列由配置页按目标表统一校验
        err = self._check_columns(
            params["match_table_id"],
            list(params["match_columns"].values()),
            "匹配表的匹配列",
        )
        if err:
            return err
        return None


class AggregateForm(BaseParamForm):
    """aggregate：条件统计。"""

    def __init__(self, params, table_ids=None, conn_columns=None,
                 parent=None, **kwargs):
        super().__init__(params, table_ids, conn_columns, parent,
                         **kwargs)
        self.setWindowTitle("条件统计参数")
        self._group = QLineEdit("，".join(params.get("group_by", [])))
        self._group.setPlaceholderText("按哪些列分组统计，逗号分隔（留空 = 整表汇总）")
        self._form.addRow("分组列", self._group)

        self._metrics = QPlainTextEdit(
            "\n".join(
                f"{m.get('column', '*')}:{m.get('func', 'count')}"
                for m in params.get("metrics", [])
            )
        )
        self._metrics.setPlaceholderText(
            "每行一个统计指标，格式：列名:函数\n函数：count(计数)/sum(求和)/mean(平均)/max/min\n"
            "整表计数可用 *:count\n例如：\n*:count\n电费 金额:sum"
        )
        self._form.addRow("统计指标", self._metrics)

        self._conditions = QPlainTextEdit(
            format_conditions(params.get("conditions", []))
        )
        self._conditions.setPlaceholderText("统计前过滤条件（可留空），格式同条件筛选")
        self._form.addRow("过滤条件", self._conditions)

    def get_params(self):
        metrics = []
        for line in self._metrics.toPlainText().splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            col, _, func = line.partition(":")
            col, func = col.strip(), func.strip().lower()
            if col and func:
                metrics.append({"column": col, "func": func,
                                "alias": f"{col}_{func}" if col != "*" else "计数"})
        conditions = []
        cond_text = self._conditions.toPlainText().strip()
        if cond_text:
            conditions = parse_condition_lines(cond_text)
        return {"group_by": parse_token_list(self._group.text()),
                "metrics": metrics, "conditions": conditions}

    def validate_params(self, params):
        if not params["metrics"]:
            return "至少需要一个统计指标（如 *:count）"
        for m in params["metrics"]:
            if m["func"] not in _AGGS:
                return f"不支持的统计函数: {m['func']}（可选: {'/'.join(_AGGS)}）"
        return None


class ExportForm(BaseParamForm):
    """export：结果导出。"""

    def __init__(self, params, table_ids=None, conn_columns=None,
                 parent=None, **kwargs):
        super().__init__(params, table_ids, conn_columns, parent,
                         **kwargs)
        self.setWindowTitle("结果导出参数")
        row = QHBoxLayout()
        # 空路径默认锚定引擎根（frozen 下为 exe 目录），避免落 cwd/缓存区
        from paths import get_engine_root
        default_path = str(params.get("output_path", "")).strip()
        if not default_path:
            default_path = str(get_engine_root() / "导出结果.xlsx")
        self._path = QLineEdit(default_path)
        browse = QPushButton("浏览…")
        browse.clicked.connect(self._browse)
        row.addWidget(self._path)
        row.addWidget(browse)
        self._form.addRow("导出文件路径", row)
        self._sheet = QLineEdit(str(params.get("sheet_name", "数据")))
        self._form.addRow("工作表名称", self._sheet)

    def _browse(self) -> None:
        # 起始目录取当前文本所在目录（存在则用，否则引擎根）
        from pathlib import Path
        from paths import get_engine_root
        cur = Path(self._path.text().strip())
        start = str(cur.parent) if str(cur) and cur.parent.is_dir() \
            else str(get_engine_root())
        path, _ = QFileDialog.getSaveFileName(
            self, "选择导出位置", start, "Excel 文件 (*.xlsx)"
        )
        if path:
            self._path.setText(path)

    def get_params(self):
        return {"output_path": self._path.text().strip(),
                "sheet_name": self._sheet.text().strip() or "数据"}

    def validate_params(self, params):
        if not params["output_path"]:
            return "请填写导出文件路径"
        return None


class MergeTablesForm(BaseParamForm):
    """merge_tables：数据表合并。"""

    def __init__(self, params, table_ids=None, conn_columns=None,
                 parent=None, **kwargs):
        super().__init__(params, table_ids, conn_columns, parent,
                         **kwargs)
        self.setWindowTitle("数据表合并参数")
        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.MultiSelection)
        selected = set(params.get("match_table_ids", []) or [])
        for tid in (table_ids or []):
            item = QListWidgetItem(tid)
            item.setData(256, tid)  # UserRole
            self._list.addItem(item)
            if tid in selected:
                item.setSelected(True)
        self._form.addRow("合并的其他数据表", self._list)

    def get_params(self):
        ids = [item.data(256) for item in self._list.selectedItems()]
        return {"match_table_ids": ids}

    def validate_params(self, params):
        if not params["match_table_ids"]:
            return "请勾选至少一张其他数据表（目标表本身自动参与合并）"
        return None


class CopyTableForm(BaseParamForm):
    """copy_table：数据表复制（无额外参数；产出一张新表＝新分支）。"""

    def __init__(self, params, table_ids=None, conn_columns=None,
                 parent=None, **kwargs):
        super().__init__(params, table_ids, conn_columns, parent,
                         **kwargs)
        self.setWindowTitle("数据表复制参数")
        # 标签文案取自注册表（禁字面量散落，2026-09-20 M20）
        label = produce_label("copy_table") or "新表"
        self._form.addRow(
            "说明", QLineEdit(f"复制出一张新表（新分支），流程图中将标注「{label}」"))

    def get_params(self):
        return {}


class RenameColumnsForm(BaseParamForm):
    """rename_columns：表头名称修改。"""

    def __init__(self, params, table_ids=None, conn_columns=None,
                 parent=None, **kwargs):
        super().__init__(params, table_ids, conn_columns, parent,
                         **kwargs)
        self.setWindowTitle("表头名称修改参数")
        self._mapping = QPlainTextEdit(format_pairs(params.get("mapping", {})))
        self._mapping.setPlaceholderText("每行一处改名，格式：原列名=新列名\n例如：\n名称=客户名称\namt=金额")
        self._form.addRow("改名对应", self._mapping)

    def get_params(self):
        return {"mapping": parse_pair_lines(self._mapping.toPlainText())}

    def validate_params(self, params):
        if not params["mapping"]:
            return "至少需要一处改名（原列名=新列名）"
        return None


class ConvertDtypeForm(BaseParamForm):
    """convert_dtype：数据类型转换。"""

    def __init__(self, params, table_ids=None, conn_columns=None,
                 parent=None, **kwargs):
        super().__init__(params, table_ids, conn_columns, parent,
                         **kwargs)
        self.setWindowTitle("数据类型转换参数")
        self._column = QLineEdit(str(params.get("column", "")))
        self._column.setPlaceholderText("要转换的列名")
        self._form.addRow("列名", self._column)

        self._from = QComboBox()
        self._to = QComboBox()
        for t in _DTYPES:
            self._from.addItem(t, t)
            self._to.addItem(t, t)
        fi = self._from.findData(params.get("from_type", "TEXT"))
        ti = self._to.findData(params.get("to_type", "INTEGER"))
        self._from.setCurrentIndex(max(fi, 0))
        self._to.setCurrentIndex(max(ti, 0))
        self._form.addRow("原类型", self._from)
        self._form.addRow("目标类型", self._to)

    def get_params(self):
        return {"column": self._column.text().strip(),
                "from_type": self._from.currentData(),
                "to_type": self._to.currentData()}

    def validate_params(self, params):
        if not params["column"]:
            return "请填写要转换的列名"
        if params["from_type"] == params["to_type"]:
            return "原类型与目标类型相同，无需转换"
        return None


class SupervisionReportForm(BaseParamForm):
    """supervision_report：履职表单抽查报告（3 张统计表 + 1 段总结）。

    三参数：保存到（GUI 预填）/ 实际工作日天数（1~366）/ 追加数据表（多选）。
    默认路径与期间提示随目标表/追加表联动（refresh_context）。
    """

    def __init__(self, params, table_ids=None, conn_columns=None, parent=None,
                 source_dir="", registry=None, target_table_id=""):
        super().__init__(params, table_ids, conn_columns, parent,
                         source_dir=source_dir, registry=registry,
                         target_table_id=target_table_id)
        self.setWindowTitle("履职表单抽查报告参数")
        self._auto_path = ""
        # 0. 先建「追加数据表」控件——期间提示与工作日默认值都要读它的勾选态，
        #    故必须先于下方第 2 段创建（否则 AttributeError: _list）
        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.MultiSelection)
        # 1. 保存到（范式抄 ExportForm：文本框 + 浏览…）
        row = QHBoxLayout()
        self._auto_path = self._build_default_path()
        cur = str(params.get("output_path", "")).strip()
        self._path = QLineEdit(cur or self._auto_path)
        browse = QPushButton("浏览…")
        browse.clicked.connect(self._browse)
        row.addWidget(self._path)
        row.addWidget(browse)
        self._form.addRow("保存到", row)
        # 2. 期间提示 + 实际工作日天数（此时 _list 已存在，读到空勾选 → 按目标表算）
        self._wd_default = self._union_workday_default()
        self._hint = QLabel(self._period_text())
        self._form.addRow("数据期间", self._hint)
        self._spin = QSpinBox()
        self._spin.setRange(1, 366)
        self._spin.setValue(self._wd_default if self._wd_default else 1)
        self._spin.valueChanged.connect(self._refresh_warn)
        self._form.addRow("实际工作日天数", self._spin)
        self._warn = QLabel("")
        self._warn.setWordWrap(True)
        self._form.addRow("", self._warn)
        self._refresh_warn()
        # 3. 追加数据表（显示 别名（编号），D2；控件已在第 0 段创建）
        self._list.itemSelectionChanged.connect(self._refresh_context_view)
        self._rebuild_list()
        self._form.addRow("追加数据表", self._list)

    # ---- 上下文与派生 ----
    def _meta(self, tid: str) -> Dict[str, Any]:
        for e in self._registry:
            if e.get("table_id") == tid:
                return e
        return {}

    def _selected_ids(self) -> List[str]:
        if not hasattr(self, "_list"):
            return []   # 防御：控件尚未创建时按"未勾选"处理
        ids = [i.data(256) for i in self._list.selectedItems()]
        return [str(x) for x in ids if str(x)]

    def _union_range(self):
        tids = ([self._target_table_id] if self._target_table_id else [])
        tids += self._selected_ids()
        mins, maxs = [], []
        for tid in tids:
            dr = (self._meta(tid) or {}).get("date_range") or {}
            if dr.get("min") and dr.get("max"):
                mins.append(str(dr["min"]))
                maxs.append(str(dr["max"]))
        if not mins:
            return None
        return min(mins), max(maxs)

    def _union_workday_default(self) -> Optional[int]:
        rng = self._union_range()
        if rng is None:
            return None
        from datetime import datetime as _dt, timedelta as _td
        d0 = _dt.strptime(rng[0], "%Y-%m-%d").date()
        d1 = _dt.strptime(rng[1], "%Y-%m-%d").date()
        n, cur = 0, d0
        while cur <= d1:
            if cur.weekday() < 5:
                n += 1
            cur += _td(days=1)
        return n

    def _period_text(self) -> str:
        rng = self._union_range()
        if rng is None:
            return "未能识别日期范围"
        n = self._union_workday_default() or 0
        return (f"数据涉及时间段：{rng[0]} ~ {rng[1]}，"
                f"其中周一至周五 {n} 天（未扣除法定节假日）")

    def _build_default_path(self) -> str:
        import os
        from datetime import datetime as _dt
        from paths import get_engine_root
        from ops.supervision_report import OUTPUT_NAME_PREFIX, OUTPUT_TIME_FMT
        base_dir = self._source_dir
        if not base_dir:
            src = ""
            if self._target_table_id:
                m = self._meta(self._target_table_id)
                src = str(m.get("source_path") or m.get("file_path") or "")
            if src:
                base_dir = os.path.dirname(src)
        if not base_dir:
            base_dir = str(get_engine_root())
        name = (OUTPUT_NAME_PREFIX + "-"
                + _dt.now().strftime(OUTPUT_TIME_FMT) + ".xlsx")
        return os.path.join(base_dir, name)

    def _rebuild_list(self) -> None:
        if not hasattr(self, "_list"):
            return      # 防御：控件尚未创建
        selected = set(self._selected_ids())
        self._list.clear()
        for tid in self._table_ids:
            if tid == self._target_table_id:
                continue
            alias = (self._meta(tid) or {}).get("alias") or tid
            item = QListWidgetItem(f"{alias}（{tid}）")
            item.setData(256, tid)  # UserRole
            self._list.addItem(item)
            if tid in selected:
                item.setSelected(True)

    def _refresh_context_view(self) -> None:
        self._hint.setText(self._period_text())
        self._refresh_warn()

    def _refresh_warn(self) -> None:
        msg = None
        try:
            from ops.supervision_report import workday_hint
            msg = workday_hint(int(self._spin.value()),
                               self._union_workday_default())
        except Exception:  # noqa: BLE001 提示失败不阻断
            msg = None
        self._warn.setText(msg or "")

    def refresh_context(self, source_dir="", registry=None,
                        target_table_id="") -> None:
        """目标表/数据表变更后刷新默认路径与期间提示（D1-B 联动）。"""
        if source_dir:
            self._source_dir = source_dir
        if registry is not None:
            self._registry = registry
        if target_table_id:
            self._target_table_id = target_table_id
        if self._path.text().strip() in ("", self._auto_path):
            self._auto_path = self._build_default_path()
            self._path.setText(self._auto_path)
        old_default = self._wd_default
        self._wd_default = self._union_workday_default()
        if self._spin.value() == (old_default if old_default else 1):
            self._spin.setValue(self._wd_default if self._wd_default else 1)
        self._rebuild_list()
        self._refresh_context_view()

    # ---- 参数收拢 ----
    def _browse(self) -> None:
        import os
        cur = self._path.text().strip()
        start = os.path.dirname(cur) if cur else ""
        if not start or not os.path.isdir(start):
            from paths import get_engine_root
            start = str(get_engine_root())
        path, _ = QFileDialog.getSaveFileName(
            self, "选择报告保存位置", start, "Excel 文件 (*.xlsx)")
        if path:
            self._path.setText(path)

    def get_params(self):
        wc = int(self._spin.value())
        return {
            "output_path": self._path.text().strip(),
            "workday_count": 0 if wc == self._wd_default else wc,
            "extra_table_ids": self._selected_ids(),
        }

    def validate_params(self, params):
        if not params.get("output_path"):
            return "请先选择报告要保存到哪里"
        return None


# ---------------------------------------------------------------------------
# 表单注册表（2026-09-20 M21：键集单一源 = gui.models.STEP_CATALOG）
# ---------------------------------------------------------------------------

# 操作类型 → 表单类（仅声明"哪个类处理哪个操作"，不作为操作清单的权威来源）
_FORM_CLASSES: Dict[str, type] = {
    "filter": FilterForm,
    "dedup": DedupForm,
    "mapping_match": MappingMatchForm,
    "aggregate": AggregateForm,
    "export": ExportForm,
    "supervision_report": SupervisionReportForm,
    "merge_tables": MergeTablesForm,
    "copy_table": CopyTableForm,
    "rename_columns": RenameColumnsForm,
    "convert_dtype": ConvertDtypeForm,
}


def _build_registry() -> Dict[str, type]:
    """按 STEP_CATALOG 键集构造注册表（新增操作＝改 models + 补表单类，禁双源）。

    Returns:
        Dict[str, type]: 操作类型 → 表单类；models 中未提供表单类的操作不入表
        （get_form_class 返回 None，由调用侧兜底）。
    """
    return {op: _FORM_CLASSES[op] for op in STEP_CATALOG if op in _FORM_CLASSES}


_FORM_REGISTRY: Dict[str, type] = _build_registry()


def get_form_class(op_type: str):
    """按操作类型返回表单类；未知类型返回 None。"""
    return _FORM_REGISTRY.get(op_type)
