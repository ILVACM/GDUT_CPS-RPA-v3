"""W-03 动态 DAG 演示——右侧参数配置面板（仿 rpa_engine/gui/forms.py 模式）。

由 backend/func_registry.py 的 params schema 驱动动态生成表单控件：
    text→QLineEdit；enum:a|b→QComboBox；table→QComboBox(当前表)
保留键控件：target_table（目标表）、extra_inputs（附加输入表，merge 类）。
「保存参数」按钮收拢校验（try_apply）后发射 saved(dict) 信号；
校验失败红字提示具体缺失项，不发射信号。
DAG 画布严格只读：本面板是唯一的配置入口。
"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QComboBox, QFormLayout, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QWidget)

from backend.func_registry import get_op


class ParamPanel(QWidget):
    """步骤参数编辑面板；saved 信号携带待写回字段字典。"""

    saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._controls = {}
        self._schema = []
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.form = QFormLayout()
        self.form.setContentsMargins(0, 0, 0, 0)
        root.addLayout(self.form)
        self.err = QLabel("")
        self.err.setStyleSheet("color:#c62828;font-size:11px;")
        self.err.setWordWrap(True)
        self.err.hide()
        root.addWidget(self.err)
        self.btn = QPushButton("保存参数")
        self.btn.clicked.connect(self._on_save)
        root.addWidget(self.btn)

    # ---------------- 构建 ----------------
    def build(self, step, tables):
        """按注册表 schema 重建表单；step 为 get_dag 的步骤 dict。"""
        while self.form.rowCount():
            self.form.removeRow(0)
        self._controls = {}
        self._schema = []
        self.err.hide()
        meta = get_op(step.get("op_type")) or {}
        self._table_options = [(t["key"], "%s %s" % (t["key"], t.get("display", "")))
                               for t in tables]

        schema = [("target_table", "目标数据表", "table", True)]
        if meta.get("inputs", {}).get("extra_min", 0) > 0 \
                and step.get("op_type") != "mapping_match":
            schema.append(("extra_inputs", "附加输入表", "table", True))
        schema += list(meta.get("params", []))
        self._schema = schema

        params = step.get("params") or {}
        for item in schema:
            key, label, spec = item[0], item[1], item[2]
            if key == "target_table":
                value = step.get("target_table") or ""
            elif key == "extra_inputs":
                extras = step.get("extra_inputs") or []
                value = extras[0] if extras else ""
            else:
                value = params.get(key, item[4] if len(item) > 4 else "")
            ctrl = self._make_control(spec, value)
            self._controls[key] = ctrl
            self.form.addRow(label, ctrl)

    def _make_control(self, spec, value):
        if spec.startswith("enum:"):
            combo = QComboBox()
            combo.addItems(spec[len("enum:"):].split("|"))
            idx = combo.findText(str(value))
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            return combo
        if spec == "table":
            combo = QComboBox()
            combo.addItem("（请选择）", "")
            for k, disp in self._table_options:
                combo.addItem(disp, k)
            i = combo.findData(str(value or ""))
            combo.setCurrentIndex(i if i >= 0 else 0)
            return combo
        edit = QLineEdit(str(value or ""))
        return edit

    # ---------------- 校验与收拢 ----------------
    def _read_value(self, key, spec):
        ctrl = self._controls[key]
        if spec.startswith("enum:") or spec == "table":
            return ctrl.currentData() if spec == "table" else ctrl.currentText()
        return ctrl.text().strip()

    def try_apply(self):
        """收集并校验；返回 (ok, fields, errors)。"""
        fields, errors = {}, []
        table_keys = {k for k, _ in self._table_options}
        for item in self._schema:
            key, label, spec, req = item[0], item[1], item[2], item[3]
            v = self._read_value(key, spec)
            fields[key] = v
            if req and not str(v).strip():
                errors.append("请填写「%s」" % label)
            elif spec == "table" and v and v not in table_keys:
                errors.append("「%s」选择的表不存在" % label)
        return (not errors, fields, errors)

    def show_errors(self, errors):
        if errors:
            self.err.setText("；".join(errors))
            self.err.show()
        else:
            self.err.hide()

    def _on_save(self):
        ok, fields, errors = self.try_apply()
        self.show_errors(errors)
        if ok:
            self.saved.emit(fields)
