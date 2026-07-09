---
name: okr-migration-plan
description: "Use when the user wants OKR 资产迁移 or guided migration/fusion support after OKR 资产盘点: turning an inventory report into batches, destination mapping, conflict handling, previewed write-in steps, explicit-confirmation migration into the new OKR Doing Agent Logseq system, and automatic old-source archiving after successful migration. If no inventory report exists, first route to okr-assets-inventory. Do not rescan the whole project when a current inventory report is available. Do not delete or overwrite old assets; move old source files to the old folder's zzz_已迁移 area only after a confirmed migration succeeds."
---

# OKR 资产迁移

Use this skill after `OKR 资产盘点` to help the user migrate/fuse old assets into the new OKR Doing Agent Logseq system.

## Boundary

This skill owns:

```text
读取资产盘点报告
整理迁移批次
生成目标页面映射
标出冲突和人工确认项
输出迁移预览
按确认批次写入新 Logseq graph 或指导用户手动接入
迁移成功后把已处理旧源移动到旧目录 zzz_已迁移
```

It does not own:

```text
重新全量盘点旧项目
删除旧文件
无预览直接批量写入
自动覆盖现有页面
判断 OKR 质量或做 coaching
```

Write only after the user provides the target graph path, sees a per-batch preview, receives a backup reminder, and explicitly confirms that batch. After the confirmed migration succeeds, automatically move eligible old source files into the old folder's `zzz_已迁移/` holding area; never delete them automatically.

## Inputs

Prefer one of:

```text
OKR 资产盘点报告
okr_assets_inventory.py --json output
旧个人 OKR 文件夹路径 + 新 Logseq graph 路径
```

If the user gives only an old folder path, first run `$okr-assets-inventory` or the inventory script, then use its report.

Do not skip inventory by scanning the whole project inside this skill.

## Run Rules

Work user-visible batch by user-visible batch:

```text
1. Read the inventory report.
2. Pick the smallest useful batch to migrate next.
3. Show the target page map and conflicts.
4. Show a write preview before touching files.
5. Write only after explicit confirmation.
6. Archive eligible old source files into `zzz_已迁移/`.
7. Summarize changed files, source archive location, ledger status, and what remains inside the same batch.
```

Keep the user-visible batch model simple. Do not expose internal substeps such as `Batch 1A / 1B / 1C` to the user.

```text
Batch 1: 年度 OKR
Batch 2: 项目与大事件
Batch 3: 周/月复盘与行动证据
Batch 4: 模板与资源
Batch 5: 归档与暂不迁移
```

Use these actions:

```text
接入
合并前人工确认
补一条反链
归档
暂不迁移
需要拆分
```

Never pretend uncertain items are safe. Mark them `人工确认`.

## Completion Standards

A batch is not complete just because a page was created.

For `Batch 1: 年度 OKR`, completion means:

```text
- 新年度页已创建或冲突已标出
- 旧年度主页面内容已匹配到新结构
- 年度拆分文件已列出合并建议
- 旧全文已写入 `zzz_旧<原文件名去掉扩展名>` 回溯页
- 主年度页只保留 `legacy-source::` 和 `legacy-archive::` 链接,不内嵌旧全文
- `zzz_OKR迁移台账` 已记录处理状态
- 未确认项单独列出
```

If only a shell page is created and the old source is attached or archived, mark the item as `仅挂载`, not `已整理`.

Do not announce a user-visible batch as complete while any core item is only `仅挂载`. Do not suggest moving to the next user-visible batch unless the user explicitly chooses to pause the current batch and continue.

## Annual Split File Rule

Annual split files are supporting assets for an annual page by default. Do not create standalone execution pages from them unless the source file is clearly a real project, month, quarter, week, or event page.

For files such as:

```text
YYYYOKR_<维度>_KRs.md
YYYYOKR_<维度>_进度.md
YYYYOKR_<维度>_数据.md
YYYYOKR_<维度>_复盘.md
```

use this mapping first:

```text
*_KRs.md -> merge into the matching annual dimension as 原定目标 / 原定 KR / 相关证据
*_进度.md -> preserve as 原始进度证据 under the matching annual dimension
*_数据.md -> preserve as 原始数据证据 under the matching annual dimension
*_复盘.md -> merge into the matching annual dimension's 复盘 / 判断更新 section
```

Do not infer meaning from bare numbers such as `1 / 1 / 1` or `10% / 0 / 0`. Preserve them exactly and mark the interpretation as `人工确认` only if needed.

For each annual split file:

```text
- create `[[zzz_旧<原文件名去掉扩展名>]]` in the target graph
- update the annual page's split-file result section
- update `[[zzz_OKR迁移台账]]`
```

Use ledger statuses this way:

```text
已整理 -> content has been merged or preserved as raw evidence and archived
建议归档 -> empty, duplicate, or intentionally not useful for the annual structure, with source preserved or noted
待确认 -> content cannot be safely placed without user choice
```

The annual page should say `拆分文件处理结果` after handling the split files, not keep them as generic `待确认`.

## Pattern-Assisted Batch Mode

After the user confirms a migrated sample, the skill may reuse that pattern for low-risk files with the same structure. This is a pattern-assisted batch, not full autopilot migration.

Before writing, always show:

```text
- confirmed sample used as pattern
- candidate files included in this batch
- files excluded from this batch
- conflicts and artificial-confirmation items
- target page map
- write preview
```

Only include files that match the confirmed pattern clearly:

```text
YYYY OKRs.md -> annual page
YYYYOKR_<维度>_KRs.md -> annual dimension source
YYYYOKR_<维度>_进度.md -> raw progress evidence
YYYYOKR_<维度>_数据.md -> raw data evidence
YYYYOKR_<维度>_复盘.md -> annual dimension review / judgment update
```

Exclude from pattern-assisted batches by default:

```text
- target pages with unresolved conflicts
- pages that look like projects, events, weeklies, journals, resources, or templates
- source files whose year or dimension cannot be inferred from the filename
- items already marked `待确认`, `冲突待处理`, or `仅挂载` for reasons unrelated to the current pattern
- any destructive old-source cleanup or deletion action; moving eligible old source files to `zzz_已迁移/` is part of the confirmed migration transaction
```

Use the ledger to avoid reprocessing completed files. If a source is already `已整理`, `历史年度已整理`, `建议归档`, or `未来占位已归档` with a `legacy-archive`, skip it unless the user asks to revise it.

When presenting this mode to the user, keep the wording simple:

```text
我会按已确认的 2025 样例批量处理同类年度 OKR；冲突和不确定项会单独列出，不会硬写。
```

Do not let batch mode bypass confirmation. A batch preview still requires explicit confirmation before writing.

## Placeholder And Future Annual Rule

Do not turn empty annual shells into execution structure.

If an annual source file contains only metadata, placeholder bullets, or no real OKR content, classify it as a placeholder instead of a structured annual OKR.

Placeholder signals include:

```text
- only `-` lines
- only frontmatter-like Logseq properties such as class, alias, parent, period, iteration, tags
- no annual keywords, objectives, KRs, review notes, events, or evidence
- future years with only a copied annual template
```

For placeholders:

```text
- create or keep only a minimal annual placeholder page if it is useful for navigation
- do not generate month, quarter, or week links without source files
- preserve source text in `[[zzz_旧<原文件名去掉扩展名>]]`
- record ledger status as `建议归档` or `未来占位已归档`
```

If a placeholder year is outside the current decade, do not attach it to the wrong decade plan. Mark it `人工确认` unless a matching decade parent exists.

If a source file has inconsistent metadata, such as filename year not matching `alias::` or `period::`, mark it `人工确认` and do not write a target page until the user confirms.

When explaining this to the user, keep it brief:

```text
这些只是年度占位,本轮不生成月/季/周页面；只做归档或人工确认。
```

## Existing Annual Page Conflict Rule

If the target annual page already exists and the old source has real content, treat it as a merge conflict, not a normal batch item.

Do not overwrite the target page directly. First compare:

```text
- target page status and existing content
- old source annual keywords, events, dimensions, projects, and review logs
- whether target content is only an empty template or has user-authored content
- whether the old source should become the primary structured body or only a legacy archive
```

For annual conflicts:

```text
- show a conflict merge preview before writing
- preserve old source text in `[[zzz_旧<原文件名去掉扩展名>]]`
- keep the target page title stable unless the user chooses otherwise
- merge source content into the target structure when the target is only a blank shell
- if both sides contain real user-authored content, mark the item `冲突待处理` and ask the user which side should be primary
```

When the target page is a blank template and the old source is the only substantive version, it is safe to propose:

```text
旧源作为主内容合并；目标页仅保留标题和新系统结构。
```

Still require explicit confirmation before writing.

## Monthly And Project Conflict Rule

When migrating monthly pages, normalize duplicate month naming before writing.

Common duplicate patterns:

```text
YYYY January 1月.md -> [[YYYY 1月]]
YYYY February 2月.md -> [[YYYY 2月]]
YYYY March 3月.md -> [[YYYY 3月]]
YYYY April 4月.md -> [[YYYY 4月]]
YYYY May 5月.md -> [[YYYY 5月]]
YYYY June 6月.md -> [[YYYY 6月]]
YYYY July 7月.md -> [[YYYY 7月]]
YYYY August 8月.md -> [[YYYY 8月]]
YYYY September 9月.md -> [[YYYY 9月]]
YYYY October 10月.md -> [[YYYY 10月]]
YYYY November 11月.md -> [[YYYY 11月]]
YYYY December 12月.md -> [[YYYY 12月]]
```

For monthly conflicts:

```text
- if the target month page is a blank template and the old source month has real content, merge old source into the target month title
- preserve the old source text in `[[zzz_旧<原文件名去掉扩展名>]]`
- do not create both English-month and Chinese-month pages in the target graph
- fix obvious template metadata only inside the page being merged, such as January pointing to Q2
- keep unrelated target month, quarter, week, and project pages untouched
```

If an old month source is empty and another source for the same month has real content, mark the empty source `建议归档`.

Project-like files found during monthly migration should not be embedded wholesale into the month page. Instead:

```text
- create or preview a target project/event page only when the file is clearly a project/event
- link it from the month page under 本月项目 or 本月大事件
- preserve original text in a `zzz_旧...` archive page
```

If both the target month and old month contain real user-authored content, keep status `冲突待处理` and ask which source should be primary.

## Project Support Material Rule

When a group contains a main project/event source and related copy, detail pages, strategy notes, or evidence files, migrate the group as one project family.

Use this mapping:

```text
大事件_YYYY ... 活动.md -> [[Project/YYYY ... 活动名]]
YYYY年...营销活动文案.md -> support material under the matching project
YYYY年...详情页.md -> support material under the matching project
深度思考 / 学习计划 / 策略草稿 -> strategy or knowledge asset; exclude unless the user confirmed it belongs to this project batch
```

For each confirmed project family:

```text
- create one structured `Project/...` page
- preserve each old source in a separate `[[zzz_旧...]]` archive page
- link support material from the project page instead of creating standalone execution pages
- update annual/monthly project indexes to point to the `Project/...` page when the old link is only an alias
- move all processed old sources to `zzz_已迁移/`
```

Do not infer missing revenue, dates, or outcomes. If a project source only has a year/month in the filename and no explicit date range, preserve that limitation in `未确认项`.

## Training And Operations Asset Rule

Training camps, community operations, award campaigns, promotion copy, announcement collections, and activity plans should be migrated as historical project/operations assets.

Use this mapping:

```text
YYYY*训练营*.md -> [[Project/YYYY <训练营或活动名>]]
YYYY*转化活动复盘.md -> [[Project/YYYY <转化活动名>]]
YYYY*推文素材.md -> support material under the matching project or [[OKR运营资产库]]
YYYY*群公告合集.md -> support material under the matching project, even when it only contains an external link
YYYY*活动方案.md -> support material under the matching project
YYYY*金熊奖*.md -> [[Project/YYYY 金熊奖]]
```

For each confirmed operations project family:

```text
- create or update [[OKR运营资产库]] as the index
- create one structured `Project/...` page per coherent activity family
- group copy, announcement links, plans, and review data under 支持材料 / 原始证据
- preserve each old full source in a separate `[[zzz_旧...]]` archive page
- move processed old sources to `zzz_已迁移/` after the confirmed batch succeeds
```

Do not create annual, monthly, or weekly execution pages from historical operations assets unless the file is explicitly a period review page for the user's personal OKR system. If a file is mainly personal review, learning goal, or family/life project, exclude it from this batch.

## Membership Strategy Asset Rule

Membership strategy, community-group analysis, learning-plan design, and AI-generated strategy drafts should be grouped as operations strategy project families.

Use this mapping:

```text
YYYY*会员*运营方案*.md -> [[Project/YYYY <会员运营主题>]]
YYYY*熊小组分析*.md -> support material under the matching community/membership operations project
YYYY*大会员深度思考*.md -> [[Project/YYYY 小能熊大会员服务升级策略]]
YYYY*大会员学习计划*.md -> support material under the matching membership strategy project
*GPT版.md / *deepseek版.md -> AI draft evidence under the matching strategy project
```

For each confirmed membership strategy family:

```text
- create or update [[OKR运营资产库]] as the index
- create one structured `Project/...` strategy page
- group AI drafts, learning plans, analysis notes, and operations plans under 支持材料 / 原始证据
- preserve each old full source in a separate `[[zzz_旧...]]` archive page
- link related execution project pages only as 相关执行项目; do not merge strategy drafts into existing monthly campaign pages
- move processed old sources to `zzz_已迁移/` after the confirmed batch succeeds
```

If a strategy source contains recommendations without confirmed implementation data, keep them as strategy/evidence and list unresolved execution status under `未确认项`.

## Residual Singleton Asset Rule

At the end of a migration, remaining isolated files should be classified conservatively instead of forced into annual structure.

Use this mapping:

```text
personal letters or relationship notes -> archive only, status 建议归档, no public project/person page by default
dated operations data or weekly operations analysis -> [[Project/YYYY <operations evidence title>]] and [[OKR运营资产库]]
family, finance, health, or life planning notes with objectives/results -> [[Project/<personal project title>]]
learning goals with KRs -> [[Project/<learning project title>]]
quarterly or work reviews without a clear year -> [[复盘/<title>_年份待确认]], not [[YYYYQn]]
```

For each residual singleton:

```text
- preserve the old full source in `[[zzz_旧<原文件名去掉扩展名>]]`
- create a structured target only when the destination is clear
- add `未确认项` when the year, owner, or execution relationship is unclear
- move processed old sources to `zzz_已迁移/` after the confirmed batch succeeds
```

Do not create person pages, public case pages, or yearly/quarterly/monthly pages from residual files unless the source clearly requires that destination.

## Major Event Rule

Standalone major-event sources should become event pages, not project pages.

Use this mapping:

```text
大事件_YYYY ... .md -> [[大事件/YYYY ...]]
大事件_<非年份事件名>.md -> [[大事件/<事件名>]]
```

For each confirmed major event:

```text
- create one structured `大事件/...` page
- preserve source properties such as class, date, tags, impact, type, trigger, and related when present
- structure the body as 事件概况 / 事实与数据 / 影响与后续 / 相关链接 / 未确认项 / 迁移记录
- preserve the old full text in `[[zzz_旧<原文件名去掉扩展名>]]`
- update annual or monthly indexes only when they already reference the old event
- move the processed old source to `zzz_已迁移/` after the confirmed batch succeeds
```

If an event is also referenced by an old project-style alias, add that alias to the event page instead of creating a duplicate project page, unless the source clearly contains a full project execution plan.

Do not create ghost event pages for missing sources. If an annual page references an event but no old source exists, leave the link as an unresolved follow-up or mark it `未确认项`.

For tiny one-line event sources, create a minimal event page only when the event is referenced by an annual/monthly index or has a clear date in the line or filename; preserve the limitation in `未确认项`.

## Monthly Placeholder Rule

Do not treat metadata-only month files as substantive monthly plans.

A month source is a monthly placeholder when it contains only:

```text
class / alias / author / parent / period / tags properties
blank lines
no bullets other than empty template bullets
```

For monthly placeholders:

```text
- normalize the target month title, such as `YYYY February 2月.md -> [[YYYY 2月]]`
- fix obvious target metadata such as `quarter::`
- create `[[zzz_旧<原文件名去掉扩展名>]]`
- record the source as `建议归档`
- move the old source to `zzz_已迁移/` after the confirmed batch succeeds
- do not add invented projects, events, week links, or review text
```

If the source contains one or more real bullets, such as `0205 [[大事件_...]]`, preserve those bullets under the target month's matching section and mark the source `已整理`.

When a same-month empty file exists beside a substantive month source, archive the empty file as `建议归档` and mention it in the target month's migration record.

## Time Evidence Batch Rule

Use a single user-visible time-evidence batch when the remaining sources are month, quarter, week, and directly referenced event evidence for the same migration area.

This batch may combine:

```text
YYYY EnglishMonth M月.md -> [[YYYY M月]]
YYYYQn.md -> [[YYYYQn]]
YYYY_Wnn.md -> [[YYYY-Wnn]]
one directly referenced `大事件_...md` -> [[大事件/...]]
```

Keep the implementation internally separated:

```text
- month pages normalize naming and preserve real monthly plans / projects / events
- quarter pages preserve quarter dashboards and only link months/weeks that are explicitly present in the source
- week pages preserve 3 Things / weekly action evidence
- event pages follow Major Event Rule
```

Do not create ghost month, quarter, or week pages just because a dashboard table mentions them. Create a target page only when an old source exists for that exact period, or an existing target page already needs a confirmed link update.

If a quarter source only contains a copied dashboard line, a bare `-`, or mismatched months from another quarter, mark it `建议归档`. A minimal target quarter page may be kept only for navigation when the annual page already links it, with the mismatch listed under `未确认项`.

For this batch, old source archiving still follows Old Source Archive Rule: write target/archive pages first, update the ledger, then move old sources to `zzz_已迁移/`.

## Method And Resource Asset Rule

System-method, concept, template, and reusable explanation sources should become method/resource pages, not annual OKR execution pages.

Use this mapping:

```text
系统_系统_个人OKR系统_*.md -> [[方法/个人OKR系统_<主题>]]
系统_系统方法_*.md -> [[方法/<主题>]]
*时间ROI*.md -> [[方法/时间ROI]]
自我卡片分类*.md -> [[方法/自我卡片分类_4维度和3圈层]]
generic summary or transcript files with OKR method content -> [[方法/<content-derived title>]]
```

For each confirmed method/resource asset:

```text
- create or update [[OKR方法库]] as the index
- create one structured `方法/...` page with 定位 / 核心要点 / 可用场景 / 迁移记录
- preserve the old full text in `[[zzz_旧<原文件名去掉扩展名>]]`
- link the method page from [[OKR方法库]]
- move the processed old source to `zzz_已迁移/` after the confirmed batch succeeds
```

Do not attach method assets to annual, monthly, quarterly, weekly, project, or event pages unless the source already has an explicit execution-period relationship.

If a file mixes method material with personal review, operations data, learning goals, or project planning, exclude it from the method batch and mark it for a later batch or manual confirmation.

## Historical Decade Rule

Do not create ghost execution pages for historical years.

When migrating assets from a previous decade, use a retrospective structure:

```text
[[十年计划（2011-2020）]]
- 十年判断
- 年度年鉴
  - [[2017 OKRs]]
  - [[2018 OKRs]]
  - [[2020 OKRs]]
- 历史主题
- 十年复盘
- 未迁移说明
```

For historical annual pages:

```text
- Create or structure the annual page, such as [[2018 OKRs]].
- Put month-like information inside the annual page as `年度大事件与月份线索`.
- Do not create [[2018 1月]], [[2018Q1]], [[2018-W01]], or similar pages unless an actual source file for that period exists.
- Preserve old full text in [[zzz_旧<原文件名去掉扩展名>]].
- Record the source status in [[zzz_OKR迁移台账]] as `历史年度已整理`, `历史年度仅挂载`, or `历史年度待确认`.
```

Use this historical annual page structure:

```text
class:: OKR, 历史年度回溯
parent:: [[十年计划（2011-2020）]]
period:: YYYY
status:: #历史年度已整理
legacy-source::
legacy-archive::
tags:: #OKR #历史回溯

- ## 年度定位
- ## 年度关键词
- ## 年度大事件与月份线索
- ## 当年目标 / OKR
- ## 维度复盘
- ## 判断更新
- ## 未确认项
```

Historical matching rules:

```text
旧年度展望 / 年度定位 / 十年以后的自己 -> 年度定位
年度关键词 / 年度词汇 -> 年度关键词
1月、2月、0101、Q1 等时间线索 -> 年度大事件与月份线索, not new month pages
年度计划 / 目标 / O / KR / 项目 -> 当年目标 / OKR
工作总结 / 学习总结 / 生活总结 / 财务总结 / 七维度复盘 -> 维度复盘
Q1-Q4 年度问答 / 经验教训 / 对后来十年的影响 -> 判断更新
unclear images, broken embeds, ambiguous old links -> 未确认项
```

Current-decade annual pages and historical annual pages use different templates:

```text
2021-2030 current decade -> execution annual structure with quarterly/monthly/week links only when appropriate.
previous decade -> retrospective annual structure; no generated execution layer unless source files exist.
```

When presenting the diagnosis or preview to the user, mention this boundary briefly:

```text
历史年份只做年度回溯,不会生成没有来源的月/周页面。
```

Do not over-explain this unless the user asks.

## Migration Ledger

Maintain a target-graph ledger page:

```text
[[zzz_OKR迁移台账]]
```

Record every processed source file with a stable status:

```text
- [[2025 OKRs]]
  source:: /old/path/2025 OKRs.md
  batch:: 年度 OKR
  status:: 已整理 / 仅挂载 / 待确认 / 建议归档 / 冲突待处理
  migrated-at:: [[YYYY-MM-DD]]
  target:: [[2025 OKRs]]
  legacy-archive:: [[zzz_旧2025 OKRs]]
  note::
```

Use the ledger before continuing work so already processed files are not repeatedly reclassified. The ledger lives in the new graph only. Do not delete old source files; after confirmed migration, move eligible old source files to the old folder's `zzz_已迁移/` holding area and record the cleanup fields.

## Old Source Archive Rule

Migration does not delete old source files by default. It does archive eligible old source files by moving them to the old source folder's holding area after confirmed migration succeeds.

After each confirmed migration batch, automatically move an old source file into `zzz_已迁移/` only when all conditions are true:

```text
- target page exists in the new graph
- old full text exists in a `zzz_旧<原文件名去掉扩展名>` archive page, or the source is intentionally marked `建议归档`
- ledger status is `已整理`, `历史年度已整理`, `建议归档`, or `未来占位已归档`
- there are no `待确认`, `仅挂载`, or `冲突待处理` notes for that source
```

Default source archive action is to move old files into the old source folder's holding area, not to delete them:

```text
<old source folder>/zzz_已迁移/
```

Prefer this sequence after a confirmed batch:

```text
1. Write the target page and `zzz_旧...` archive page.
2. Update [[zzz_OKR迁移台账]] migrated status.
3. Move eligible old sources to `zzz_已迁移/`.
4. Update [[zzz_OKR迁移台账]] with `cleanup:: 已移动到旧源归档`, `cleanup-at::`, and `cleanup-target::`.
5. Tell the user that old sources were archived and where to trace them.
```

Never delete old source files directly unless the user explicitly confirms deletion after seeing the archived source list.

When the user asks whether migrated old files can be removed, answer briefly:

```text
可以归档；已迁移的旧源默认移动到旧目录 `zzz_已迁移/`,不直接删除。新图谱里也会保留 `zzz_旧...` 回溯页。
```

## Legacy Archive Pages

When preserving old full text, create a separate target-graph page:

```text
[[zzz_旧<原文件名去掉扩展名>]]
```

Examples:

```text
[[zzz_旧2025 OKRs]]
[[zzz_旧2025OKR_工作_KRs]]
[[zzz_旧大事件_2025手术]]
```

Main migrated pages should keep only source links and structured content. Do not paste long old full text into the main target page unless the user explicitly asks for that shape.

## Output Shape

Use this structure:

```text
OKR 资产迁移
迁移前提
本轮先接哪一批
目标页面映射
冲突与人工确认
暂不迁移 / 建议归档
写入预览
本批状态
确认口令 / 下一步
```

Before confirmation, keep the final next step preview-first:

```text
确认后我只处理这一批；迁移成功后,符合条件的旧源会自动移动到旧目录 `zzz_已迁移/`,不删除。
```

After writing, report status with these short labels:

```text
已整理
仅挂载
待确认
建议归档
冲突待处理
历史年度已整理
历史年度仅挂载
历史年度待确认
```

If any item is `仅挂载`, say clearly that the batch is still in progress and the next step is to structure-merge it, not to start the next user-visible batch.

## Destination Map

Prefer these destinations:

```text
十年/长期规划 -> [[十年计划（YYYY-YYYY）]]
年度 OKR -> [[YYYY OKRs]]
季度计划 -> [[YYYYQn]]
月度计划 -> [[YYYY M月]]
项目资产 -> [[Project/<项目名>]]
周复盘 -> [[YYYY-Wxx]]
大事件 -> [[大事件/<事件名>]]
模板 -> [[OKR Templates]] 或归档
资源资料 -> 资源索引
未分类 -> 人工确认
```

## Tone

Use calm asset language:

```text
这批可以先接入。
这批建议先归档,不进入执行层。
这几项会撞上现有页面,需要你确认是合并还是保留旧链接。
我们先把这一批接稳,再处理下一批。
```

Avoid judgment:

```text
旧系统太乱。
目标质量不高。
这些内容没有价值。
```
