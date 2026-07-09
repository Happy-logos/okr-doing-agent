---
name: yinxiang-enml-export
description: Use when the user wants to export, inventory, validate, or prepare Yinxiang/Evernote historical notes as readable migration sources for OKR Doing Agent. Handles single-note HTML exports, local ENML/content.enml folders, exported HTML/resources folders, and .notes backup diagnosis. Use for 印象笔记, Evernote, Yinxiang, ENML, HTML export, .notes parsing questions, and preparing source material before OKR migration. Do not use for writing into Logseq or migrating data; hand off prepared material to okr-assets-inventory or okr-migration-plan after export validation.
---

# 印象笔记 ENML / HTML 导出

Use this skill to turn Yinxiang/Evernote historical notes into readable, auditable source material before OKR migration.

## Boundary

This skill owns:

```text
识别印象笔记导出物类型
判断哪些导出可读、哪些只是备份
指导或执行单条 HTML 导出
读取本地 ENML / HTML / resources
只读校验导出文件数量、大小、正文和附件目录
生成迁移前素材清单与交接报告
```

It does not own:

```text
写入 Logseq
迁移到 happy's OKR
修改 OKR 页面或台账
删除、移动、覆盖旧导出
破解加密 .notes 正文
全盘扫描用户电脑
```

After readable material is prepared, hand off to `okr-assets-inventory` for asset mapping or `okr-migration-plan` for a write preview.

## Safety Boundaries / 安全边界

This skill is designed as a local-first export cleaning helper.

It will:

- read only user-selected export folders;
- parse readable ENML / HTML files;
- preserve resource folder references;
- mark encrypted `.notes` files as backup-only;
- generate source-preparation reports, migration handoff notes, and audit records.

It will not:

- log in to Yinxiang / Evernote;
- call private or unofficial APIs;
- decrypt protected files;
- upload raw notes or attachments;
- overwrite source files;
- write into the target OKR system without user confirmation.

这个 skill 是一个本地优先的导出清洗工具。

它会：

- 只读取用户指定的导出目录；
- 解析可读的 ENML / HTML 文件；
- 保留资源附件目录引用；
- 将加密或不可读的 `.notes` 文件标记为仅备份；
- 生成迁移前素材清单、交接记录和审计记录。

它不会：

- 登录印象笔记 / Evernote；
- 调用私有或非官方接口；
- 解密受保护文件；
- 上传原始笔记或附件；
- 覆盖源文件；
- 未经用户确认写入目标 OKR 系统。

## Source Rules

Prefer sources in this order:

```text
1. Existing local `content.enml` folders
2. Single-note HTML exports with `.html` and optional `.resources`
3. Existing readable `.html` exports
4. `.notes` only as backup evidence, not as migration source
```

Treat Yinxiang batch `.notes` exports as backup archives unless proven otherwise. In this migration line, `.notes` bodies were observed as encrypted `base64:aes` content and were not suitable as direct migration sources.

Use single-note HTML export when the app can confirm format `HTML`. If the UI only offers `.notes`, or if format cannot be confirmed, stop and report instead of guessing.

## Safety Rules

- Work inside the agreed export folders, usually `~/Documents`; only check `~/Documents`, `~/Desktop`, and `~/Downloads` for recent export validation.
- Do not use broad `find /` or full-disk scans.
- Do not overwrite existing files. If the app shows an overwrite or replace dialog, stop and report.
- Do not delete or move exported files.
- Do not write into the target Logseq graph from this skill.
- Keep reports source-oriented: counts, titles, paths, short excerpts, validation status, and blockers.
- Avoid copying sensitive full text into summaries. Preserve full text only in local staged source files when the user has asked for migration preparation.

## Workflow

1. Confirm the source notebook or export folder and the intended output folder.
2. Inventory what already exists:

```bash
find "$HOME/Documents" -maxdepth 4 -type f \( -iname '*.enml' -o -iname '*.html' -o -iname '*.htm' -o -iname '*.notes' \) -print
```

3. Classify each source:

```text
content.enml present -> readable ENML
*.html plus optional *.resources -> readable HTML
*.notes with encrypted body -> backup only
missing body or tiny file -> needs re-export or manual check
```

4. If using the Yinxiang app, export one note at a time:

```text
打开印象笔记
定位 notebook
选择单条笔记
文件 / 导出笔记
格式选择 HTML
保存到 ~/Documents
```

5. Every 5-10 exported notes, pause for read-only validation:

```bash
find "$HOME/Documents" -maxdepth 4 -type f \( -iname '*.html' -o -iname '*.htm' \) -mmin -120 -print0 |
  xargs -0 ls -lt | head
```

Also check that files are non-empty, contain body text, and have `.resources` folders when attachments are referenced.

6. Produce a handoff report:

```text
source notebook / folder
export method
readable ENML count
readable HTML count
.notes backup-only count
missing / failed / blocked items
recent output paths
recommended next skill
```

## Parsing Guidance

For ENML, parse as XML/HTML-like markup and preserve the source title, created time if available, and body structure. Do not rely on brittle string splitting when a structured parser is available.

For HTML, extract the main body text and preserve links to local `.resources` assets. Keep the original HTML as the primary source of truth; derived Markdown or text is a working copy.

For `.notes`, inspect metadata and container structure only when useful. Do not spend migration time trying to decrypt encrypted note bodies without a supported app export path.

## Stop Conditions

Stop and report when:

```text
the export UI cannot confirm HTML
an overwrite / replace / delete dialog appears
the exported HTML is empty or unreadable
only encrypted .notes files are available
the notebook count is large and the user has not confirmed scope
the task shifts from source preparation to Logseq migration
```

## Handoff

Use this language when the source preparation is complete:

```text
这些素材已经可读,可以交给 OKR 资产盘点 / 迁移预览。
```

Then use `okr-assets-inventory` or `okr-migration-plan` for the next phase.
