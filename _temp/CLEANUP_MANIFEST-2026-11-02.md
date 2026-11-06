# `_temp` 清理清单（CLEANUP MANIFEST）

> **状态**：执行态｜生成：2026-11-02｜执行：AI Agent
> **用途**：本文件为本次删除动作的**唯一回退线索**。
> **判据**：目标已完成 + 受管辖文档零引用 + 纯中间产物（三者同时满足）。

**清理前**：221 个文件 / 3.91 MB
**删除**：185 个 / 2.70 MB
**保留**：36 个 / 1.20 MB

---

## §1 删除清单

| # | 路径（相对 `_temp/`） | 体积 B | git 跟踪 | 恢复方式 |
|---|----------------------|--------|---------|----------|
| 1 | `cleanup-plan-2026-11-02.txt` | 8010 | ❌ | **不可恢复**（未跟踪） |
| 2 | `cleanup_exec.py` | 5828 | ❌ | **不可恢复**（未跟踪） |
| 3 | `cleanup_plan.py` | 3334 | ❌ | **不可恢复**（未跟踪） |
| 4 | `doc-fix-agents-sink.py` | 5005 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-agents-sink.py` |
| 5 | `doc-fix-anchor.py` | 3771 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-anchor.py` |
| 6 | `doc-fix-backup-2026-10-24/AGENTS.md` | 4927 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/AGENTS.md` |
| 7 | `doc-fix-backup-2026-10-24/README.md` | 1286 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/README.md` |
| 8 | `doc-fix-backup-2026-10-24/v1/FROZEN.md` | 765 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v1/FROZEN.md` |
| 9 | `doc-fix-backup-2026-10-24/v2/FROZEN.md` | 1090 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v2/FROZEN.md` |
| 10 | `doc-fix-backup-2026-10-24/v3/AGENTS.md` | 13608 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/AGENTS.md` |
| 11 | `doc-fix-backup-2026-10-24/v3/docs/architecture.md` | 27947 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/architecture.md` |
| 12 | `doc-fix-backup-2026-10-24/v3/docs/backlog.md` | 13750 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/backlog.md` |
| 13 | `doc-fix-backup-2026-10-24/v3/docs/build-guide.md` | 11519 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/build-guide.md` |
| 14 | `doc-fix-backup-2026-10-24/v3/docs/deployment-guide.md` | 3726 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/deployment-guide.md` |
| 15 | `doc-fix-backup-2026-10-24/v3/docs/dev-spec.md` | 29540 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/dev-spec.md` |
| 16 | `doc-fix-backup-2026-10-24/v3/docs/doc-governance.md` | 19884 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/doc-governance.md` |
| 17 | `doc-fix-backup-2026-10-24/v3/docs/function-spec-rules.md` | 38921 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/function-spec-rules.md` |
| 18 | `doc-fix-backup-2026-10-24/v3/docs/INDEX.md` | 9198 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/INDEX.md` |
| 19 | `doc-fix-backup-2026-10-24/v3/docs/legacy.md` | 3778 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/legacy.md` |
| 20 | `doc-fix-backup-2026-10-24/v3/docs/plan/DAG_refactor_plan.md` | 61715 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/plan/DAG_refactor_plan.md` |
| 21 | `doc-fix-backup-2026-10-24/v3/docs/plan/INDEX.md` | 2101 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/plan/INDEX.md` |
| 22 | `doc-fix-backup-2026-10-24/v3/docs/runtime-env-spec.md` | 4864 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/runtime-env-spec.md` |
| 23 | `doc-fix-backup-2026-10-24/v3/docs/task-records/2026-09-24-temp-ledger-cleanup.md` | 9632 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/task-records/2026-09-24-temp-ledger-cleanup.md` |
| 24 | `doc-fix-backup-2026-10-24/v3/docs/task-records/2026-10-18-importdata-repair.md` | 58553 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/task-records/2026-10-18-importdata-repair.md` |
| 25 | `doc-fix-backup-2026-10-24/v3/docs/task-records/2026-10-19-func-spec-doc-sync.md` | 5998 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/task-records/2026-10-19-func-spec-doc-sync.md` |
| 26 | `doc-fix-backup-2026-10-24/v3/docs/task-records/2026-10-19-w22-n-remediation.md` | 10632 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/task-records/2026-10-19-w22-n-remediation.md` |
| 27 | `doc-fix-backup-2026-10-24/v3/docs/user-manual.md` | 5794 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/docs/user-manual.md` |
| 28 | `doc-fix-backup-2026-10-24/v3/README.md` | 7087 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/README.md` |
| 29 | `doc-fix-backup-2026-10-24/v3/rpa_engine/README.md` | 8340 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/rpa_engine/README.md` |
| 30 | `doc-fix-backup-2026-10-24/v3/rpa_engine/tests/__init__.py` | 512 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-backup-2026-10-24/v3/rpa_engine/tests/__init__.py` |
| 31 | `doc-fix-finalize-anchor.py` | 2087 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-finalize-anchor.py` |
| 32 | `doc-fix-fpnote.py` | 1452 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-fpnote.py` |
| 33 | `doc-fix-index.py` | 8923 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-index.py` |
| 34 | `doc-fix-lockpath.py` | 1129 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-lockpath.py` |
| 35 | `doc-fix-plan-and-records.py` | 4291 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-plan-and-records.py` |
| 36 | `doc-fix-rec-numbers.py` | 1266 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-rec-numbers.py` |
| 37 | `doc-fix-rec-verifier.py` | 2707 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-rec-verifier.py` |
| 38 | `doc-fix-residual.py` | 1948 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-residual.py` |
| 39 | `doc-fix-v45.py` | 931 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-v45.py` |
| 40 | `doc-fix-v6.py` | 1344 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-v6.py` |
| 41 | `doc-fix-verifier-fixes.py` | 3268 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-verifier-fixes.py` |
| 42 | `doc-fix-w25.py` | 2251 | ✅ | `git checkout HEAD -- v3/_temp/doc-fix-w25.py` |
| 43 | `docx-dump-zeng.txt` | 7735 | ❌ | **不可恢复**（未跟踪） |
| 44 | `ImportData/backup/B1/阶段0/app.py` | 13711 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段0/app.py` |
| 45 | `ImportData/backup/B1/阶段0/executor.py` | 12648 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段0/executor.py` |
| 46 | `ImportData/backup/B1/阶段0/forms.py` | 24041 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段0/forms.py` |
| 47 | `ImportData/backup/B1/阶段0/graph_edges.py` | 12234 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段0/graph_edges.py` |
| 48 | `ImportData/backup/B1/阶段0/main_window.py` | 44891 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段0/main_window.py` |
| 49 | `ImportData/backup/B1/阶段0/models.py` | 41406 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段0/models.py` |
| 50 | `ImportData/backup/B1/阶段0/page_operation_config.py` | 59917 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段0/page_operation_config.py` |
| 51 | `ImportData/backup/B1/阶段0/parser.py` | 7106 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段0/parser.py` |
| 52 | `ImportData/backup/B1/阶段0/session_db.py` | 4845 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段0/session_db.py` |
| 53 | `ImportData/backup/B1/阶段0/sql_safety.py` | 9848 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段0/sql_safety.py` |
| 54 | `ImportData/backup/B1/阶段0/table_importer.py` | 7245 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段0/table_importer.py` |
| 55 | `ImportData/backup/B1/阶段0/test_step_catalog.py` | 4344 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段0/test_step_catalog.py` |
| 56 | `ImportData/backup/B1/阶段4/graph_edges.py` | 12234 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段4/graph_edges.py` |
| 57 | `ImportData/backup/B1/阶段4/models.py` | 41877 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段4/models.py` |
| 58 | `ImportData/backup/B1/阶段5/executor.py` | 12648 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段5/executor.py` |
| 59 | `ImportData/backup/B1/阶段5/table_importer.py` | 7245 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段5/table_importer.py` |
| 60 | `ImportData/backup/B1/阶段6/parser.py` | 7106 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/B1/阶段6/parser.py` |
| 61 | `ImportData/backup/D3/exporter.py` | 4950 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/D3/exporter.py` |
| 62 | `ImportData/backup/P0/app.py` | 13525 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P0/app.py` |
| 63 | `ImportData/backup/P0/error_messages.py` | 2675 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P0/error_messages.py` |
| 64 | `ImportData/backup/P0/main_window.py` | 37488 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P0/main_window.py` |
| 65 | `ImportData/backup/P0/models.py` | 41223 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P0/models.py` |
| 66 | `ImportData/backup/P0/page_input_selection.py` | 27653 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P0/page_input_selection.py` |
| 67 | `ImportData/backup/P0/requirements.txt` | 1045 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P0/requirements.txt` |
| 68 | `ImportData/backup/P0/RPA_Workflow_v3.spec` | 3759 | ❌ | **不可恢复**（未跟踪） |
| 69 | `ImportData/backup/P1/excel_preprocessor.py` | 8377 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P1/excel_preprocessor.py` |
| 70 | `ImportData/backup/P1/main_window.py` | 39364 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P1/main_window.py` |
| 71 | `ImportData/backup/P2/excel_preprocessor.py` | 9131 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P2/excel_preprocessor.py` |
| 72 | `ImportData/backup/P2/table_importer.py` | 3864 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P2/table_importer.py` |
| 73 | `ImportData/backup/P4/aggregator_preP4.py` | 5213 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P4/aggregator_preP4.py` |
| 74 | `ImportData/backup/P4/excel_normalizer.py` | 19535 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P4/excel_normalizer.py` |
| 75 | `ImportData/backup/P4/excel_preprocessor.py` | 10668 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P4/excel_preprocessor.py` |
| 76 | `ImportData/backup/P4/executor.py` | 12249 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P4/executor.py` |
| 77 | `ImportData/backup/P4/exporter_preP4.py` | 3580 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P4/exporter_preP4.py` |
| 78 | `ImportData/backup/P4/filter_dedup_preP4.py` | 5570 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P4/filter_dedup_preP4.py` |
| 79 | `ImportData/backup/P4/forms_preP4.py` | 23744 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P4/forms_preP4.py` |
| 80 | `ImportData/backup/P4/mapping_matcher_preP4.py` | 7996 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P4/mapping_matcher_preP4.py` |
| 81 | `ImportData/backup/P4/sqlite_manager.py` | 5999 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P4/sqlite_manager.py` |
| 82 | `ImportData/backup/P4/table_importer.py` | 5371 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P4/table_importer.py` |
| 83 | `ImportData/backup/P4/table_lifecycle.py` | 7310 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P4/table_lifecycle.py` |
| 84 | `ImportData/backup/P5/excel_normalizer.py` | 36767 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P5/excel_normalizer.py` |
| 85 | `ImportData/backup/P5/main_window.py` | 40496 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P5/main_window.py` |
| 86 | `ImportData/backup/P5/paths.py` | 1837 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P5/paths.py` |
| 87 | `ImportData/backup/P5/table_importer.py` | 6008 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P5/table_importer.py` |
| 88 | `ImportData/backup/P6/main_window.py` | 41532 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P6/main_window.py` |
| 89 | `ImportData/backup/P6/table_importer.py` | 6091 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/P6/table_importer.py` |
| 90 | `ImportData/backup/R15/AGENTS.md` | 13571 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/AGENTS.md` |
| 91 | `ImportData/backup/R15/app.py` | 15728 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/app.py` |
| 92 | `ImportData/backup/R15/exporter.py` | 7694 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/exporter.py` |
| 93 | `ImportData/backup/R15/forms.py` | 25206 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/forms.py` |
| 94 | `ImportData/backup/R15/models.py` | 44076 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/models.py` |
| 95 | `ImportData/backup/R15/page_input_selection.py` | 29198 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/page_input_selection.py` |
| 96 | `ImportData/backup/R15/requirements.txt` | 1138 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/requirements.txt` |
| 97 | `ImportData/backup/R15/smoke_m1m3.py` | 31518 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/smoke_m1m3.py` |
| 98 | `ImportData/backup/R15/step_executor.py` | 12601 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/step_executor.py` |
| 99 | `ImportData/backup/R15/test_graph_edges.py` | 9523 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/test_graph_edges.py` |
| 100 | `ImportData/backup/R15/test_ops_contracts.py` | 27005 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/test_ops_contracts.py` |
| 101 | `ImportData/backup/R15/test_translation.py` | 9879 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/test_translation.py` |
| 102 | `ImportData/backup/R15/validator.py` | 5138 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/backup/R15/validator.py` |
| 103 | `ImportData/d3_artifacts/no_meta.xlsx` | 4969 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/d3_artifacts/no_meta.xlsx` |
| 104 | `ImportData/d3_artifacts/with_meta.xlsx` | 4963 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/d3_artifacts/with_meta.xlsx` |
| 105 | `ImportData/lock_header.txt` | 903 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/lock_header.txt` |
| 106 | `ImportData/p4-subagent-report.md` | 11164 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/p4-subagent-report.md` |
| 107 | `ImportData/p5-subagent-report.md` | 10678 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/p5-subagent-report.md` |
| 108 | `ImportData/p5_artifacts/h9/failed_list.json` | 161 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/p5_artifacts/h9/failed_list.json` |
| 109 | `ImportData/p5_artifacts/h9/failed_list.txt` | 92 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/p5_artifacts/h9/failed_list.txt` |
| 110 | `ImportData/p5_artifacts/h9/T1_normalize.json` | 137 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/p5_artifacts/h9/T1_normalize.json` |
| 111 | `ImportData/p5_artifacts/h9/T1_normalize.txt` | 74 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/p5_artifacts/h9/T1_normalize.txt` |
| 112 | `ImportData/p6-subagent-report.md` | 11964 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/p6-subagent-report.md` |
| 113 | `ImportData/p6_artifacts/h9/T1_normalize.json` | 131 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/p6_artifacts/h9/T1_normalize.json` |
| 114 | `ImportData/p6_artifacts/h9/T1_normalize.txt` | 68 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/p6_artifacts/h9/T1_normalize.txt` |
| 115 | `ImportData/plan.md.bak_v1` | 316082 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/plan.md.bak_v1` |
| 116 | `ImportData/plan.md.bak_v2` | 421708 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/plan.md.bak_v2` |
| 117 | `ImportData/probe_p3.py` | 2626 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/probe_p3.py` |
| 118 | `ImportData/probe_p3b.py` | 2186 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/probe_p3b.py` |
| 119 | `ImportData/probe_p3c.py` | 1061 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/probe_p3c.py` |
| 120 | `ImportData/probe_p6_chunk.py` | 1392 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/probe_p6_chunk.py` |
| 121 | `ImportData/problem.md` | 94933 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/problem.md` |
| 122 | `ImportData/verify_d3_scenarios.py` | 3078 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/verify_d3_scenarios.py` |
| 123 | `ImportData/verify_p0_scenarios.py` | 3092 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/verify_p0_scenarios.py` |
| 124 | `ImportData/verify_p1_scenarios.py` | 3380 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/verify_p1_scenarios.py` |
| 125 | `ImportData/verify_p2_scenarios.py` | 3303 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/verify_p2_scenarios.py` |
| 126 | `ImportData/verify_p3_scenarios.py` | 6370 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/verify_p3_scenarios.py` |
| 127 | `ImportData/verify_p4_scenarios.py` | 9365 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/verify_p4_scenarios.py` |
| 128 | `ImportData/verify_p5_scenarios.py` | 11538 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/verify_p5_scenarios.py` |
| 129 | `ImportData/verify_p6_scenarios.py` | 14657 | ✅ | `git checkout HEAD -- v3/_temp/ImportData/verify_p6_scenarios.py` |
| 130 | `r17-backlog-anchor.py` | 9465 | ❌ | **不可恢复**（未跟踪） |
| 131 | `r17-dates.py` | 4071 | ❌ | **不可恢复**（未跟踪） |
| 132 | `r17-index-readme.py` | 4134 | ❌ | **不可恢复**（未跟踪） |
| 133 | `r17-w24-docs.py` | 3757 | ❌ | **不可恢复**（未跟踪） |
| 134 | `read_docx_zeng.py` | 1926 | ❌ | **不可恢复**（未跟踪） |
| 135 | `verify-20260928-1402.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20260928-1402.md` |
| 136 | `verify-20261019-0137.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0137.md` |
| 137 | `verify-20261019-0138.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0138.md` |
| 138 | `verify-20261019-0139.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0139.md` |
| 139 | `verify-20261019-0155.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0155.md` |
| 140 | `verify-20261019-0156.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0156.md` |
| 141 | `verify-20261019-0208.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0208.md` |
| 142 | `verify-20261019-0210.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0210.md` |
| 143 | `verify-20261019-0212.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0212.md` |
| 144 | `verify-20261019-0213.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0213.md` |
| 145 | `verify-20261019-0227.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0227.md` |
| 146 | `verify-20261019-0229.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0229.md` |
| 147 | `verify-20261019-0235.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0235.md` |
| 148 | `verify-20261019-0236.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0236.md` |
| 149 | `verify-20261019-0242.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0242.md` |
| 150 | `verify-20261019-0244.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0244.md` |
| 151 | `verify-20261019-0255.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0255.md` |
| 152 | `verify-20261019-0314.md` | 362 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0314.md` |
| 153 | `verify-20261019-0315.md` | 360 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0315.md` |
| 154 | `verify-20261019-0323.md` | 452 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0323.md` |
| 155 | `verify-20261019-0324.md` | 362 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0324.md` |
| 156 | `verify-20261019-0341.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0341.md` |
| 157 | `verify-20261019-0353.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0353.md` |
| 158 | `verify-20261019-0358.md` | 362 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261019-0358.md` |
| 159 | `verify-20261023-1801.md` | 362 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261023-1801.md` |
| 160 | `verify-20261023-1808.md` | 362 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261023-1808.md` |
| 161 | `verify-20261024-1456.md` | 362 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261024-1456.md` |
| 162 | `verify-20261024-1519.md` | 362 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261024-1519.md` |
| 163 | `verify-20261024-1633.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261024-1633.md` |
| 164 | `verify-20261024-1643.md` | 1155 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261024-1643.md` |
| 165 | `verify-20261024-1645.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261024-1645.md` |
| 166 | `verify-20261024-1647.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261024-1647.md` |
| 167 | `verify-20261024-1649.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261024-1649.md` |
| 168 | `verify-20261024-1702.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261024-1702.md` |
| 169 | `verify-20261024-1709.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261024-1709.md` |
| 170 | `verify-20261024-1713.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261024-1713.md` |
| 171 | `verify-20261024-1714.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261024-1714.md` |
| 172 | `verify-20261024-1715.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261024-1715.md` |
| 173 | `verify-20261025-1401.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261025-1401.md` |
| 174 | `verify-20261101-1743.md` | 297 | ✅ | `git checkout HEAD -- v3/_temp/verify-20261101-1743.md` |
| 175 | `verify-20261101-1914.md` | 462 | ❌ | **不可恢复**（未跟踪） |
| 176 | `verify-20261101-1915.md` | 297 | ❌ | **不可恢复**（未跟踪） |
| 177 | `verify_zeng_calc.py` | 2822 | ❌ | **不可恢复**（未跟踪） |
| 178 | `zeng-headers.json` | 1561 | ❌ | **不可恢复**（未跟踪） |
| 179 | `zeng-media/image1.png` | 66760 | ❌ | **不可恢复**（未跟踪） |
| 180 | `zeng-media/image2.png` | 43262 | ❌ | **不可恢复**（未跟踪） |
| 181 | `zeng-media/image3.png` | 107842 | ❌ | **不可恢复**（未跟踪） |
| 182 | `zeng-media/image4.png` | 91708 | ❌ | **不可恢复**（未跟踪） |
| 183 | `zeng-media/image5.png` | 66365 | ❌ | **不可恢复**（未跟踪） |
| 184 | `zeng-media/image6.png` | 26145 | ❌ | **不可恢复**（未跟踪） |
| 185 | `zeng-media/image7.png` | 40792 | ❌ | **不可恢复**（未跟踪） |

---

## §2 保留清单

| 路径（相对 `_temp/`） | 体积 B | 保留理由 |
|----------------------|--------|----------|
| `CLEANUP_MANIFEST-2026-11-02.md` | 35795 | 本文件 |
| `DAG-rebuild/artifacts/mb-preview.png` | 18610 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/M5_kickoff_plan.md` | 5194 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/plan.md` | 65684 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/backend/__pycache__/func_registry.cpython-311.pyc` | 6392 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/backend/__pycache__/mock_backend.cpython-311.pyc` | 27795 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/backend/func_registry.py` | 5569 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/backend/mock_backend.py` | 19533 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/data/workflow_demo.json` | 3862 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/frontend/dag_viewer.py` | 62014 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/frontend/param_panel.py` | 4941 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/README.md` | 9277 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/run.bat` | 449 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/tests/__pycache__/test_backend.cpython-311.pyc` | 15161 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/tests/__pycache__/test_dynamic.cpython-311.pyc` | 44499 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/tests/scenario_shots.py` | 4734 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/tests/test_backend.py` | 6501 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `DAG-rebuild/SampleCode/tests/test_dynamic.py` | 17695 | 冻结基线：SampleCode 被 DAG_refactor_plan.md 等 12 处引用；plan.md 被 13 处引用 |
| `doc-fix-factsheet-2026-10-24.md` | 8304 | 2026-10-24 任务记录 3 处引用（事实基线） |
| `doc-fix-stale-check-2026-10-24.md` | 21134 | 2026-10-24 任务记录 2 处引用（Verifier 报告） |
| `ImportData/plan.md` | 510520 | 被 backlog.md L83 与 3 篇任务记录共 17 处引用；B 类台账唯一载体 |
| `ledger_2026-09-24/CLEANUP_MANIFEST.md` | 20926 | 被 backlog.md / function-spec-rules.md / docs/INDEX.md 共 16 处引用 |
| `ledger_2026-09-24/data_import_issue_scan.md` | 29147 | 被 backlog.md / function-spec-rules.md / docs/INDEX.md 共 16 处引用 |
| `ledger_2026-09-24/function_spec_rules_round_2026-09-24/REPORT.md` | 18936 | 被 backlog.md / function-spec-rules.md / docs/INDEX.md 共 16 处引用 |
| `ledger_2026-09-24/HANDOVER_2026-09-24.md` | 39006 | 被 backlog.md / function-spec-rules.md / docs/INDEX.md 共 16 处引用 |
| `ledger_2026-09-24/open_issues_ledger_2026-09-24.md` | 51491 | 被 backlog.md / function-spec-rules.md / docs/INDEX.md 共 16 处引用 |
| `ledger_2026-09-24/RPA_engine_maturity_assessment.md` | 31927 | 被 backlog.md / function-spec-rules.md / docs/INDEX.md 共 16 处引用 |
| `ledger_2026-09-24/RPA_engine_remediation_plan.md` | 108436 | 被 backlog.md / function-spec-rules.md / docs/INDEX.md 共 16 处引用 |
| `ledger_2026-09-24/W-03_fix_round_2026-09-21/REPORT.md` | 11828 | 被 backlog.md / function-spec-rules.md / docs/INDEX.md 共 16 处引用 |
| `ledger_2026-09-24/W-03_fix_round_S1S3_2026-09-21/REPORT.md` | 9575 | 被 backlog.md / function-spec-rules.md / docs/INDEX.md 共 16 处引用 |
| `ledger_2026-09-24/W-03_M5_round_2026-09-24/REPORT.md` | 8627 | 被 backlog.md / function-spec-rules.md / docs/INDEX.md 共 16 处引用 |
| `ledger_2026-09-24/W-03_Remediation_round_2026-09-24/REPORT.md` | 24084 | 被 backlog.md / function-spec-rules.md / docs/INDEX.md 共 16 处引用 |
| `repo-scan-2026-10-23.md` | 12911 | backlog.md W-23 证据 |
| `verify-20260928-1354.md` | 297 | 2026-09-24-temp-ledger-cleanup.md L106 引用 |
| `verify-20261018-1454.md` | 297 | 2026-10-18-importdata-repair.md L56 引用 |
| `verify-20261025-1402.md` | 297 | 2026-10-24-doc-consistency... L139/L166 引用 |

---

## §3 引用校验（完整相对路径匹配）

- 活跃知识文档中对删除项的引用：**0 处**
  - 无（零引用）

> 注：`docs/task-records/` 历史引用不改写（先例：2026-09-24 R10 清理）。

---

## §4 回滚

```powershell
cd D:\cps-gpes_rpa-20250312
git checkout HEAD -- v3/_temp    # 恢复全部被跟踪项
```
