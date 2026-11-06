---
title: Deployment Guide — RPA 数据处理工具部署指南（便携版）
type: knowledge
scope: global
status: active
owner: 黄泊凯
last-updated: 2026-10-24
tags: [部署, 便携版, 更新, 指纹, 日志]
binding: reference
confidence: 已校验一致（初版按 2026-09-24 build.bat/paths.py/BUILD_INFO 实况编写，R6/E6；2026-10-24 R16 按 paths.py/build.bat 实测修正运行数据目录与备份落点；人工通读验证挂 REPORT §9 人工门禁清单）
---

# Deployment Guide — RPA 数据处理工具部署指南（便携版）

> 面向部署/管理员的一页指南。构建细节见 [build-guide.md](./build-guide.md)；环境基线见 [runtime-env-spec.md](./runtime-env-spec.md)。

## 1. 便携版约定（重要，D3② 裁定）

- **安装＝复制**：把交付包整个目录复制到目标机即可，无安装器、不写注册表、不依赖系统目录
- **必须放在可写位置**（如 `D:\RPA 工具`）：程序运行期在自身目录下创建并写入 4 个运行数据目录——`workspace/`、`logs/`、`storage/`、`temp/`（另 `templates/user/` 用户模板目录）；`build/backup/` 为构建备份目录，非运行目录。放入 `C:\Program Files` 等受保护目录或只读盘会启动失败，启动自检第 3 项将提示：「当前文件夹不允许写入。请把程序放到可写位置（如 D:\RPA 工具），不要放在 C:\Program Files 或只读盘。」
- 桌面快捷方式：直接对 exe 创建即可，无参数要求

## 2. 更新＝替换 exe

- 正式构建由 `build.bat` 完成，采用**原子发布**：在临时目录构建、测试门禁（unittest discover＋双 smoke）通过后才替换正式产物；旧包自动移入 `build/backup/RPA_Workflow_v3_<时间戳>.exe`
- 更新部署机：用新交付包覆盖 exe（或整包复制）即可；更新前建议保留旧版备份以便回退
- **用户数据永不删除红线**：`build.bat` 保护 `build/` 下 `workspace/`、`logs/`、`storage/`、`temp/`、`backup/` 五个目录（若存在）在构建与更新流程中一律不动（Step 6 仅清理构建中间产物）
- 手工替换（不经 build.bat）时，务必同时核对第 3 节指纹，防止 exe 与构建记录脱节

## 3. 指纹核对（交付包身份自证）

- 交付包内 `BUILD_INFO.txt` 记录：`SOURCE_HASH`（源码文件哈希指纹前 16 位）、`GIT_REV`（构建时 git 修订）、构建时间、`TESTS_SKIPPED`（测试是否被跳过）
- 程序内核对：标题栏 **[关于]** 按钮 → 弹窗显示同一段指纹信息；两处一致＝运行的 exe 与构建记录同源
- 源码侧复算：在 `v3` 目录执行 `python tools/make_fingerprint.py`，输出 `SOURCE_HASH=...`／`GIT_REV=...` 与 BUILD_INFO 比对
- 指纹不一致的交付包视为**失效产物**（判据见 build-guide §1.10），禁止交付

## 4. 出问题看哪里

| 症状 | 排查入口 |
|------|----------|
| 启动失败 | 启动自检 6 项提示（Python 版本/依赖/目录可写/操作目录/注册表字段/上次配置）；目录不可写按第 1 节迁移 |
| 运行报错 | `logs/gui_*.log`（loguru 按日滚动）；GUI 结果页「技术详情」折叠区有原始错误与文件路径 |
| 需要保留现场 | 外部运行配置 `global.keep_db` 置 `true`：会话数据库保留在 `workspace/` 供排查（默认执行完自动删除） |
| 双开冲突提示 | 属正常防护（写前读校验＋实例标识）：关闭另一窗口后重试 |
| 磁盘不足提示 | 导入前预检需约源文件总大小 3 倍空间；清理 `temp/` 过期副本后重试（程序启动时也会自动清理超 24h 的陈旧副本）；`build/backup/` 由构建流程维护，非运行期目录 |

## 5. 环境要求

- Windows 10+ 64 位办公机；内存基线 16GB（Pandas 峰值管控见 dev-spec §2.3）
- 交付包自带运行时（PyInstaller 冻结），部署机**无需**安装 Python/conda
- 源码开发环境（仅开发者需要）：conda `CPS-GPES_RPA-py311`，依赖锁见 `v3/requirements.lock`
