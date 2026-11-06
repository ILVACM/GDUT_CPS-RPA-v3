---
title: Legacy — 遗留系统说明与 v2 关系
type: knowledge
scope: global
status: active
owner: 黄泊凯
last-updated: 2026-10-24
tags: [遗留, 迁移, 边界, v1, v2]
binding: constraint
confidence: 已校验一致；2026-10-24 R16 全库一致性收口：§3 引擎范围改「9 项用户操作 BUILTIN_OPS」、§4 v2 树按实测改为 `A-docs/`、§6 迁移建议按 v3.1 现行操作（阶段 1 导入 + filter/aggregate + export）校正，Word 报告标注为能力缺口
content-revision: 2026-10-24
---

# Legacy — 遗留系统说明与 v2 关系

> 所属层级：知识层（docs/），经 AGENTS.md §2.5 背书具 [约束] 效力｜可信度状态：[已校验一致]
> 本文档说明 v3 引擎与遗留 v1、v2 模块的关系、冻结策略及迁移边界。
>
> **适用范围**：涉及 v2 遗留脚本维护或理解引擎开发边界时查阅
> **最后更新**：2026-10-24（R16 文档一致性收口：§3/§4/§6 按 v3.1 现行操作目录与 v2 实际目录树校正；历史 2026-08-21：v2.2 升级新增 YAML 元信息区；内容修订日期 2026-08-15）
<!-- 同步更新 2026-08-15: 例行复查，v1/v2 冻结关系与迁移边界未受近期变更（build.bat 重构、GUI 修复、模板键名/路径修复）影响，内容无需修改 -->
<!-- 同步更新 2026-10-24: R16 收口——§3「7 个步骤类型」→「9 项用户操作 BUILTIN_OPS」；§4 v2 树 AcceptanceReport/ → A-docs/；§6 迁移建议改按阶段 1 导入 + filter/aggregate + export，Word 报告标为能力缺口 -->

---

## 1. Relation to v2（与现有仓库的关系）

1. 本引擎为新建模块，**不修改**现有各部门 RPA 程序（位于 `v2/` 目录，已冻结）
2. `v1/BaseDEMO` 中的 `functions/` 模块（`office.py`、`Log.py`）可被引擎复用
3. v3 引擎中的 ETL 规则、SQLite 规则、Pandas 红线等同时适用于新旧架构
4. v1/v2 目录已冻结，仅供历史参考；新架构开发集中于 `v3/rpa_engine/`

---

## 2. Legacy RPA Program Template

> ⚠️ **此模板仅用于维护已有部门级脚本（位于 `v2/` 目录）。所有新开发必须使用上方工作流引擎架构。**

标准遗留脚本目录结构：

```text
{Department}/{Requirement}/
├── main.py
├── config/
│   ├── settings.json
├── functions/
│   ├── office.py
│   └── Log.py
├── input/
├── output/
└── workspace/
```

---

## 3. Engine Development Boundary（引擎开发边界）

| 项目 | v3 引擎范围 | 保留位置 |
|------|-----------|---------|
| 通用 ETL 能力 | 实现（9 项用户操作 BUILTIN_OPS：filter/dedup/mapping_match/aggregate/export/merge_tables/copy_table/rename_columns/convert_dtype） | `v3/rpa_engine/` |
| 业务场景配置 | 通过 JSON 参数文件 | 用户/业务人员维护 |
| 部门特有业务逻辑 | **不迁出** | `v2/ConsultDepartment/`、`v2/FinanceDepartment/` 等 |
| 可复用工具函数 | `v1/BaseDEMO/functions/` 中的 `office.py`、`Log.py` | 保持原状 |

---

## 4. v2 目录结构概览

```text
v2/
├── FROZEN.md               ← 冻结声明
├── A-docs/                 ← 验收/方案文档归档（操作手册、方案设计、需求规格说明书等）
├── ConsultDepartment/      ← 咨询部脚本（需求1/2/3）
├── FinanceDepartment/      ← 财务部脚本
├── SafetyandQualityDepartment/ ← 安质部脚本
├── ScienceandTechnologyInnovationDepartment/ ← 科创部脚本
└── SuperVisionDepartment/  ← 监理部脚本（feng/zeng）
```

---

## 5. v1 目录可复用资产

| 模块 | 路径 | 可复用性 |
|------|------|---------|
| `office.py` | `v1/BaseDEMO/functions/` | 高（Excel/Word 操作封装） |
| `Log.py` | `v1/BaseDEMO/functions/` | 高（日志封装） |
| `Invoke.py` | `v1/BaseDEMO/functions/` | 中（子进程调用） |
| `Web.py` | `v1/BaseDEMO/functions/` | 中（Selenium 封装） |
| `WeChat.py` | `v1/BaseDEMO/functions/` | 中（微信自动化） |

---

## 6. 迁移建议（非强制）

未来可将 v2 中通用逻辑逐步提取为 v3 用户操作（`BUILTIN_OPS`）：

1. **日报/周报数据处理** → 可抽象为"阶段 1 数据表导入 + `filter`/`aggregate` + `export`"组合
2. **Excel 报表生成** → 已可由现有操作组合实现（`export` 无模板流式直出 xlsx）
3. **Word 报告生成** → **v3.1 无对应操作（能力缺口）**：原 v3 `export_word` 已随 `steps/` 删除，如需恢复须按功能函数规约在 `ops/` 新增操作并登记 `BUILTIN_OPS`（届时引入 python-docx）

> **2026-10-24 注记**：原第 1/3 条按 v3 旧步骤名（`extract_excel`/`sql_transform`/`export_excel`/`export_word`）表述，v3.1 已无这些步骤类型（见 architecture.md §3.4/§6）；上表已按现行 9 项用户操作改写，能力边界如实标注。
>
> 当前策略：**v2 保持冻结，新需求在 v3 中通过 JSON 配置实现**。不主动迁移已有脚本。
