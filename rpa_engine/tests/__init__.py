"""DAG 重构移植清单测试包（2026-09-20 M-a/M-d）。

落点依据：`_temp/DAG-rebuild/plan.md` §1.9 方案①——本目录为「测试暂缓豁免」
批准的重建验证通道（AGENTS §6 已登记），仅承载 DAG 重构移植清单：
- test_graph_edges.py：五类边契约 12 项不变量（蓝本 SampleCode EdgeModelTest）
- test_translation.py：GUI 配置 → 后端执行参数翻译 8 用例（plan.md §4.7)
- test_supervision_report.py：履职表单报告 26 用例（plan.md §6.1）
- test_gui_forms_instantiate.py：10 类表单可实例化门禁 3 用例（防初始化顺序/构造参数漂移回归）

运行：cd rpa_engine && python -m unittest discover -s tests -v
"""
