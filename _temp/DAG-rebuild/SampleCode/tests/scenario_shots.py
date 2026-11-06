"""W-03 动态演示场景 offscreen 截图驱动（A-G + J-M，工程内部验证通道）。

运行（在 SampleCode 目录下）：
    python tests/scenario_shots.py
产出：artifacts/dyn-A.png .. dyn-G.png、dyn-J.png .. dyn-M.png

场景：A 初始态 / B 无选中加条件筛选 / C 选中 S1 后插条件统计 /
D 选中 T2 插数据表复制（新列 + 绿色产出边 + "复制新表"标签）/
E 删 S1→T3 消失+S2 悬空 / F 弃用 T3+下游提示（引用边转灰虚线）/
G S1 改参 overwrite_target→T3 消失。
2026-09-17 细节优化新增：J 删首步→开始标识跟随 / K 删结束步→结束标识 fallback 到末步 /
L 删后新增导出→结束标识跳到新结束步 / M 删复制步骤→产表消失+下游悬空。
（artifacts 下 dyn-H.png / dyn-I.png 为历史孤儿产物，全库零引用，本脚本不产出也不覆盖。）
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "frontend"))

from backend import mock_backend as mb                      # noqa: E402
from PyQt5.QtWidgets import QApplication                    # noqa: E402
import dag_viewer as dv                                     # noqa: E402


def main():
    app = QApplication(sys.argv)
    art = _ROOT / "artifacts"
    art.mkdir(parents=True, exist_ok=True)
    results = []

    def new_win():
        mb.reset_state()
        w = dv.DagViewerWindow()
        w.resize(1280, 800)
        w.show()
        for _ in range(5):
            app.processEvents()
        w.fit_all()
        for _ in range(3):
            app.processEvents()
        return w

    def shot(w, name):
        w.fit_all()
        for _ in range(3):
            app.processEvents()
        p = art / ("dyn-%s.png" % name)
        ok = w.canvas.viewport().grab().save(str(p))
        results.append((name, ok))

    def step_of(key):
        """按 key 取当前步骤字典（取不到返回空 dict）。"""
        for s in mb.get_dag()["steps"]:
            if s["key"] == key:
                return s
        return {}

    # A 初始态
    w = new_win()
    shot(w, "A")

    # B 无选中添加条件筛选（插到 export 前 + 新操作表 + 待配置橙）
    w = new_win()
    k = mb.add_step("filter", None)
    w.reload_data()
    w.selected = ("step", k)
    w._apply_visuals()
    shot(w, "B")

    # C 选中 S1 后插入条件统计
    w = new_win()
    k = mb.add_step("aggregate", ("step", "S1"))
    w.reload_data()
    w.selected = ("step", k)
    w._apply_visuals()
    shot(w, "C")

    # D 选中输入表 T2 插入数据表复制（最后消费者 S4 之后）
    w = new_win()
    k = mb.add_step("copy_table", ("table", "T2"))
    w.reload_data()
    w.selected = ("step", k)
    w._apply_visuals()
    shot(w, "D")

    # E 删除 S1 → T3 消失、S2 输入悬空（红虚线+⚠+输入缺失角标）
    w = new_win()
    mb.remove_step("S1")
    w.reload_data()
    shot(w, "E")

    # F 弃用 T3 → 灰虚线+已弃用角标；S2 待配置
    w = new_win()
    mb.deprecate_table("T3", True)
    w.reload_data()
    shot(w, "F")

    # G S1 改参 overwrite_target → T3 消失、S1 不再产表
    w = new_win()
    mb.update_params("S1", {"conditions": "电费>500",
                            "output_mode": "overwrite_target"})
    w.reload_data()
    shot(w, "G")

    # J 删首步 → 开始标识跟随新首步（起止标识自适应）
    w = new_win()
    mb.remove_step("S0")
    w.reload_data()
    shot(w, "J")

    # K 删结束步 → 无 is_end，结束标识 fallback 到新末步 S4
    w = new_win()
    mb.remove_step("S5")
    w.reload_data()
    shot(w, "K")

    # L 删结束步后再加导出步骤 → 新步骤拿到 is_end，结束标识跳到它
    w = new_win()
    mb.remove_step("S5")
    k = mb.add_step("export", None)
    mb.update_params(k, {"target_table": "T6", "file_name": "月度报表.xlsx"})
    w.reload_data()
    w.selected = ("step", k)
    w._apply_visuals()
    shot(w, "L")

    # M 复制步骤被删 → 其产表消失、下游引用转悬空（红虚线 + ⚠ + 输入缺失角标）
    w = new_win()
    kc = mb.add_step("copy_table", ("table", "T2"))
    out = step_of(kc).get("output_table")
    kd = mb.add_step("filter", ("step", kc))
    mb.update_params(kd, {"target_table": out, "conditions": "电费>0"})
    mb.remove_step(kc)
    w.reload_data()
    shot(w, "M")

    for name, ok in results:
        print("[scenario] dyn-%s.png save=%s" % (name, ok))
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(main())
