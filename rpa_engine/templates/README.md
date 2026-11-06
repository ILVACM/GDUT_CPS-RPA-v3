# 模板目录（v3.1）

本目录在 v3.1 中不再存放预设工作流模板（v3 预设已随 steps/ 的删除一并归档）。
用户模板统一存放于 `rpa_engine/templates/user/`（相对 ENGINE_ROOT，由
UserTemplateManager 自动创建；打包运行时位于 exe 同级 templates/user/，
见 paths.py）。

`outputs/` 原存放示例输出模板（docx/xlsx）——**已于 2026-09-14 宣布清理、全部失效**（用户裁定 R3）：
目录仅保留 `.gitkeep` 占位，不再提供失效示例模板。业务输出模板由业务人员在实际使用时另行准备。