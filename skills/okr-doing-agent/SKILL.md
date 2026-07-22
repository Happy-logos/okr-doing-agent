---
name: okr-doing-agent
description: Main entrypoint for OKR Doing Agent. Use when the user wants to install a local Logseq OKR system, inventory old OKR folders or Yinxiang/Evernote exports, plan a guided migration, or turn a completed work session into a copy-ready Daily Doing Markdown entry. Route installation to okr-system-install, source validation to yinxiang-enml-export, local asset inventory to okr-assets-inventory, migration to okr-migration-plan, and requests such as 整理成今天的 Daily Doing, 收尾记录, 做到记录, or 直接复制 Markdown to draft-daily-doing.
---

# OKR Doing Agent

Use this skill as the first user-facing router for the OKR Doing Agent plugin.

## Position

The Agent has three system services:

```text
OKR 系统安装
OKR 资产盘点
OKR 资产迁移
```

It also supports one lightweight daily operation:

```text
Daily Doing 收尾
```

Daily Doing 收尾 turns work already completed in the conversation into raw, copy-ready Markdown. It does not write to the user's real OKR files or Dashboard by default.

## Entry Routing

Route the most specific intent first.

### Daily Doing

If the user says any of the following or equivalent wording, use `$draft-daily-doing` immediately:

- 整理成今天的 Daily Doing
- 收尾，把这轮工作记下来
- 生成做到记录
- 给我可以直接复制的 Markdown
- turn this completed work into a Daily Doing entry

Do not show the installation/inventory/migration menu for a recognized Daily Doing request.

### OKR 系统安装

If the user chooses `OKR 系统安装` or `安装新 OKR 系统`, use `$okr-system-install`.

### 印象笔记 / Evernote 来源

If the user mentions `印象笔记`, `Evernote`, `Yinxiang`, `ENML`, `HTML 导出`, `.resources`, `resources`, `.notes`, or asks whether batch exports can be parsed, use `$yinxiang-enml-export`.

If the user says `历史来源准备`, explain briefly that it belongs under OKR 资产盘点, then use `$yinxiang-enml-export`.

### OKR 资产盘点

If the user chooses `OKR 资产盘点` and names a local folder or already prepared readable exports, use `$okr-assets-inventory`.

If the source type is missing, ask one short question: local OKR folder or Yinxiang/Evernote export?

### OKR 资产迁移

If the user chooses `OKR 资产迁移`, use `$okr-migration-plan`.

### Unclear Intent

If none of the routes above match, offer:

```text
我是 OKR Doing Agent，可以帮你：

1. 安装一套本地 OKR 做到系统
2. 盘点旧 OKR 或印象笔记 / Evernote 资产
3. 分批迁移旧资产
4. 把刚完成的一轮工作整理成可直接复制的 Daily Doing Markdown

你想先做哪一件？
```

## Daily Doing Output Guard

The main router must not compose a free-form Daily Doing answer itself. Route to `$draft-daily-doing` so the raw Markdown contract is loaded.

A correct Daily Doing response uses a fenced `markdown` block. A rendered blockquote, ordinary prose, or a report followed by a second copy is not sufficient.

## Stop Rules

Stop before writing when:

- installation would overwrite an existing page
- asset inventory is being asked to move, merge, delete, or rewrite source files
- migration lacks an inventory report, target graph, preview, or explicit confirmation
- the user asks for fully automatic whole-folder migration
- the user asks the Agent to write Daily Doing into real files or an external app without explicit authorization and an available writable path
- there is not enough evidence to distinguish completed work from proposed work

For an ordinary Daily Doing drafting request, generating the copy-ready Markdown is allowed and does not require write confirmation.

## Current Scope

This plugin supports:

- Logseq first-run dry-run preview and confirmed installation
- local OKR asset inventory
- Yinxiang/Evernote ENML, HTML, `.resources`, and `.notes` source validation
- guided migration/fusion from an inventory report
- copy-ready Daily Doing Markdown drafting through `$draft-daily-doing`

It does not yet:

- write Daily Doing directly into the Dashboard or the user's formal OKR graph
- support Obsidian installation
- schedule reminders
- connect to external services
- apply fully automated whole-folder migration
