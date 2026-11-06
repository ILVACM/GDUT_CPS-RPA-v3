---
title: INDEX — 领域索引（实例层）
type: index
scope: global
status: active
owner: 黄泊凯
last-updated: 2026-08-21
tags: [索引, 实例层, 领域索引]
confidence: 已校验一致（清单与 knowledge/ 实际文件及 Instances-INDEX.md 登记一致）
---

# INDEX — 领域索引（实例层）

> knowledge/ 为实例层的索引与注册所在地；实例文档本体位于项目自然归属位置，不集中存放，不存在独立 `instances/` 目录。
> 通用知识文档（含本目录原通用规范 runtime-env-spec.md，2026-08-21 迁出）位于知识层 docs/，见 [docs/INDEX.md](../docs/INDEX.md)。

## 1. 领域清单

| 领域 | 所属项目 | 实例文档（自然位置） | 注册入口 |
|------|----------|----------------------|----------|
| RPA 工作流引擎 | V3 引擎（rpa_engine/） | [rpa_engine/README.md](../rpa_engine/README.md) | [Instances-INDEX.md](./Instances-INDEX.md) |

## 2. 说明

- 实例注册与生命周期维护：见 [Instances-INDEX.md](./Instances-INDEX.md)；维护规则统一见 AGENTS.md「维护与校验」章
- 原"下游实例清单"（通用规范 → 实例映射）由实例文档元信息区 `inherits_from` 字段承载（单一事实源，可反向定位），不再设独立清单
