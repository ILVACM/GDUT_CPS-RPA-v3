# 任务记录：AGENTS.md 第二轮精简（含细节下沉 docs/），使其注入字符数达标

## 摘要
- **任务目标**：精简约束层 `AGENTS.md` 至**含 CR 字符数 ≤ 8,000**，并将细节/冗余内容自适应下沉至 `docs/`；同步修正受影响的规约引用
- **任务状态**：✅ 已完成
- **开始时间**：2026-09-13 15:05 (UTC+8)
- **最后更新**：2026-09-13
- **要点摘要**：含 CR 字符数 **8,104 → 7,628**（≤8000，注入截断解除，余量 372）；行数 214 → 196；细节下沉 doc-governance §6 与 build-guide §1.10；§4.6 转 1 行核心；§5.2 转指针；§8 压 3 行；编号零重排；9 个保留块逐字一致；三步五查通过；源码零改动
- **操作人**：黄泊凯

## 用户输入

> （第 1 条）"先对 agent 规约最高宪法 `AGENTS.md` 进行精简（保证其字符不超过 8000），将细节或者多余内容自适应剥离合并到 `.\docs` 目录和 `.\knowledge` 目录中"

> （第 2 条）"所有决策点使用默认推荐方案，计划确认，开始执行"

（附：会话中另确认「既有断链 `knowledge/Instances-INDEX.md` L22 顺手一并修正」）

## Agent 理解与决策

**性质判定**：约束层（体系内最高权威）变更 → 按 AGENTS.md §2.4/§5.1 与 2026-09-02 工作方式约定，走「方案 → 人工复核 → 执行」。

**关键测量与判据（推翻 09-06 结论）**：
- 磁盘实测：214 行 / CRLF / 字节 14,100 / **含 CR 字符数 8,104** / LF 归一化 7,890
- 本会话注入实证：`<project_guidance>` 终止于 `**构建产物**：RPA_Workflow_v3.exe（2026-08-3`；按 8,000 截断丢弃尾部**恰 104 字符**（8,104−8,000）且与观测逐字吻合 → **注入层按"含 CR"口径计数**
- 结论：09-06 以 `wc -m` 得 7,992 判"截断解除"系**错口径**（本机 `wc -m` 实返回字节数）；达标必须以含 CR ≤ 8,000 为准
- 行尾锁定：`.gitattributes` 不存在 + `core.autocrlf=true`（`git ls-files --eol` 实测 `i/lf w/crlf`）→ 写 LF 会在下次 `git checkout` 被展开回 CRLF，截断复发 → **必须按 CRLF 口径达标**

**编号锁定（实测活引用，只压块内文字不重排编号）**：§7.3（`docs/anchor-mechanism.md` L17，规定层不可改）、§2.5、§4.1、§4.2、§4.3、§4.5、§4.7、§5.1 条 6、§3.1、§1、§2.4、§6、§7.1、§7.2；章节名：§5「全局约束」、§7「维护与校验」、「当前任务锚点」。规定层溯源句「自 §7.6 迁入」为历史注记，**不改**；仅修 `docs/doc-governance.md` §4 Step 1 的**运行期陈旧引用** §7.6 → §7.3。

**决策（用户已确认默认项）**：D1 达标口径 = 含 CR ≤8,000 ｜ D2 下沉位置 = 全部落 `docs/`（**不落 `knowledge/`**——按 AGENTS.md §6 与四层结构，`knowledge/` 仅承载实例层索引，落规范细则会违反五项校验第 3 项）｜ D3 §8 = 压缩为 3 行保留 ｜ D4 §4.5/§4.7 标签表 = 保留在 AGENTS.md（编号被校验流程硬引用）

**独立评审采纳（3 阻断 + 4 建议 + 3 提示）**：
1. 【阻断】§8 必须显式保留"零培训不能理解 → 改造方案 P0 6 项/P1 3 项待拍板"（该结论在受管辖文档中**无第二载体**）
2. 【阻断】§4.6 条 2「以本文件为准」搬迁后指代错位 → 改写为「以 `AGENTS.md`（约束层）为准」
3. 【阻断】执行硬约束：一次全量 Write / Python 计码点 / CRLF 口径下达标
4. 【建议】§7.2 指向 `doc-governance.md` §1~**§6**（原方案误写 §1~§7）
5. 【建议】§5.2 保留 1 行指针而非整节删（避免编号空洞；不并入 §2.1——原文已完整包含）
6. 【建议】`build-guide.md` 承接内容须标注时点，防时点状态被误读为长期约束
7. 【建议】既有断链本轮修正（用户已确认），使校验可合法报告全过
8. 【提示】§4.6 标题须保留（§5.1 条 1 活引用）

## 执行流程

### 流程概览
- 总步骤数：9
- 多 Agent 协作：是（子 Agent 3 个：2 × Explore 负责引用清单与承载核对，1 × Plan 负责方案压测）

### 步骤记录

#### Step 1: 备份受控文件
- 状态：✅ 已完成
- 执行内容：6 个受控文件备份至 `_temp/BackUp/*.bak-20260913-pre-slim2`
- 涉及文件：`AGENTS.md`、`docs/doc-governance.md`、`docs/build-guide.md`、`docs/INDEX.md`、`README.md`、`knowledge/Instances-INDEX.md`

#### Step 2: 改造 docs 承接文件
- 状态：✅ 已完成
- 执行内容：
  - `docs/doc-governance.md`：新增 **§6「冲突解决与豁免」**（承接原 AGENTS.md §4.6，条 2 指代改写为 `AGENTS.md`）；§4 Step 1 陈旧运行期引用 §7.6 → **§7.3**；迁移来源补 §4.6；frontmatter `last-updated`/`content-revision` → 2026-09-13
  - `docs/build-guide.md`：新增 **§1.10「构建产物有效性判定」**（判据长期有效；"exe 仍有效"状态标注"截至 2026-09-13"）；frontmatter 与头部同步
  - `docs/INDEX.md`：`doc-governance` 摘要补 §6、`build-guide` 摘要补 §1.10；两行最后更新与本文件 `last-updated` → 2026-09-13；§3 关键词路由补"冲突解决、豁免"
  - `knowledge/Instances-INDEX.md`：**修正 L22 真断链**（`../doc-governance.md` → `../docs/doc-governance.md`）+ `last-updated` → 2026-09-13（W-04 与 W-05 一并关闭）
- 决策记录：全部改用 Python 脚本做字符串替换并显式保持各文件原行尾（`docs/doc-governance.md` = LF；`docs/build-guide.md` / `docs/INDEX.md` / `knowledge/Instances-INDEX.md` = CRLF），规避 Edit 工具对 CRLF 的不稳定行为；写后二进制复验 `lone_CR == 0`
- 复验结果：doc-governance 161 行 LF ／ build-guide 158 行 CRLF ／ docs/INDEX 51 行 CRLF ／ Instances-INDEX 22 行 CRLF，均 `lone_CR = 0`

#### Step 3: 新建本轮任务记录
- 状态：✅ 已完成
- 执行内容：按 `TEMPLATE.md` 六节结构创建本文件（先有后写）
- 涉及文件：`docs/task-records/2026-09-13-agents-slim-v2.md`（新建，LF 行尾，与既有任务记录一致）

#### Step 4: 重写 AGENTS.md（一次全量 Write）
- 状态：✅ 已完成
- 执行内容：按处置表生成精简版并整文件写入（CRLF 保真）。保留块（§2.1/§2.2/§2.3/§4.1/§4.4/§4.5/§4.7/§5.1/§7.3）逐字未改；§2.4/§2.5/§3/§4.2/§4.3/§4.6/§5.2/§5.3/§5.4/§6/§7.1/§7.2/§8 压缩；§1 去重；锚点层覆写为本任务
- 涉及文件：`AGENTS.md`
- 决策记录：不采用 Edit 逐处修改（历史实证同文件多 Edit 会竞态覆盖，且 Edit 对 CRLF 处理不稳定），改用一次性整文件生成；临时生成脚本 `_temp/_gen_agents.py` 用后即删
- 复验：首次写入含 CR = 7,609 ≤ 8,000（达成硬约束）；逐字复核发现 §4.7 末行漏加粗标记，已回补，随后 9 个保留块全部逐字一致 ✅

#### Step 5: 同步 README.md
- 状态：✅ 已完成
- 执行内容：核对 README 全部既有引用（§全局约束 章名、9 篇知识文档、architecture.md §9）均仍有效；按 §4 Step 3「有变化则更新」补记一行 2026-09-13 状态速览
- 涉及文件：`README.md`（CRLF 保真，39 行）

#### Step 6: 执行全局更新校验（doc-governance §4）
- 状态：✅ 已完成
- 执行内容：
  - Step 1 AGENTS.md 自洽性：七类章节齐备 ✅／编号锁定清单 17 项全部存在 ✅／§4.5 四标签齐备 ✅／§4.7 六标签齐备 ✅／路由 5 条链接可达 ✅
  - Step 2 索引一致性 + 五项校验：链接（42 篇，真断链 **0**；`dev-spec.md -> df` 为代码片段伪命中）✅／元信息（15 篇适用文档 0 不合规；首次检查范围过宽已按 §3 重跑）✅／层级一致性 ✅／INDEX 同步（docs 9 篇、plan 1 篇、knowledge 2 文件、实例登记一一对应）✅／约束力合规 ✅
  - Step 3 README 同步：已按上一步处理
- 涉及文件：`_temp/verify-agents-slim2.md`
- 决策记录：首次元信息检查把约束层/导航/详情层文件误纳入适用范围，按 §3 规定（仅知识层与实例层文档 + INDEX）重跑后 0 不合规；未据此改动任何文件

#### Step 7: 锚点层收尾
- 状态：✅ 已完成
- 执行内容：锚点层状态 `执行中` → `已完成`；要点摘要回填实测终值（含 CR 7,628）；等长替换校正数字，避免"记录值≠终值"
- 涉及文件：`AGENTS.md`
- 复验：最终 196 行 / 含 CR **7,628 ≤ 8,000** ✅ / CRLF 196 行 / lone_CR = 0

## 涉及文件汇总
| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 备份 | `_temp/BackUp/*.bak-20260913-pre-slim2`（AGENTS.md / doc-governance.md / build-guide.md / docs-INDEX.md / README.md / Instances-INDEX.md） | 执行前快照 |
| 修改 | `AGENTS.md` | 重写：8,104 → 7,628（含 CR），214 → 196 行；锚点层覆写 |
| 修改 | `docs/doc-governance.md` | 新增 §6「冲突解决与豁免」；§4 Step 1 的 §7.6 → §7.3；frontmatter 同步 |
| 修改 | `docs/build-guide.md` | 新增 §1.10「构建产物有效性判定」 |
| 修改 | `docs/INDEX.md` | doc-governance / build-guide 两行摘要与最后更新同步 |
| 修改 | `knowledge/Instances-INDEX.md` | L22 断链修正（`../docs/doc-governance.md`）+ last-updated（**关闭 W-04、W-05**） |
| 修改 | `README.md` | 补记一行 2026-09-13 状态速览 |
| 新建 | `docs/task-records/2026-09-13-agents-slim-v2.md` | 本记录 |
| 新建 | `_temp/verify-agents-slim2.md` | 全局更新校验报告 |
| 新建（即删） | `_temp/_gen_agents.py` | 一次性生成脚本，用后删除 |

## 关闭标识
- **完成时间**：2026-09-13 15:35 (UTC+8)
- **最终状态**：✅ 全部完成
- **关闭说明**：AGENTS.md 含 CR 字符数 8,104 → 7,628（≤8000，注入截断解除），细节下沉 docs/，编号零重排，保留块逐字一致，三步五查通过，源码零改动；**关闭 W-01、W-04、W-05**
