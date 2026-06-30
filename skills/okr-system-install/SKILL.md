---
name: okr-system-install
description: "Use when the user wants to install, preview, dry-run, apply, or test a new local Logseq OKR Doing system. This skill handles only the new-system installation workflow: ask for the Logseq graph path if missing, run the deterministic first-run dry-run preview, detect existing page conflicts, and run --apply only after explicit user confirmation. Do not use for old OKR asset scanning, migration planning, OKR coaching, or diagnosing goal quality."
---

# OKR 系统安装

Use this skill to install a new lightweight Logseq OKR OS.

It is a wrapper around the bundled deterministic installer:

```text
../../scripts/first_run_dry_run.py
```

Resolve that path relative to this `SKILL.md`.

## Boundary

This skill only owns:

```text
新系统安装
dry-run 预览
同名页面冲突检查
用户确认后的 --apply 写入
```

It does not own:

```text
旧 OKR 资产盘点
旧系统迁移融合
OKR 质量诊断
项目策略 coaching
```

For old-system scanning, route to `$okr-assets-inventory`.

## First-Run Rule

On first run, do not ask for goals, blockers, projects, life plans, or why something fell off track.

Ask only:

```text
你想把 OKR 系统安装到哪个 Logseq 图谱里？
```

## Dry-Run

Run:

```bash
python3 ../../scripts/first_run_dry_run.py \
  --graph "<logseq graph path>" \
  --year 2026 \
  --quarter 2 \
  --month 6 \
  --week 26
```

The dry-run must not write files.

The preview must show:

```text
是否写入文件：否
是否可直接写入：是/否
系统页面清单
Logseq 可调用模板清单
按需生成页面清单
关系预览
安全检查
冲突列表
```

If conflicts exist, stop and ask the user to resolve them before writing.

## Apply

Only after the user explicitly confirms writing, run:

```bash
python3 ../../scripts/first_run_dry_run.py \
  --graph "<logseq graph path>" \
  --year 2026 \
  --quarter 2 \
  --month 6 \
  --week 26 \
  --apply
```

`--apply` writes:

```text
OKR Dashboard
OKR Templates
当前十年计划
当前年度 OKR
Q1-Q4
1-12 月
当前周入口
```

It installs these callable templates in `OKR Templates.md`:

```text
十年计划
年度 OKR
项目 OKR
大事件
daily routine
周复盘
```

It must not create:

```text
后续十年计划
后续年度 OKR
Project/<项目名>
大事件/<事件名>
后续 YYYY-Wxx
```

## Completion

After a successful apply, say:

```text
系统已经装好了。现在要不要把一件想做的事接进来？
```

If the user mentions an old personal OKR folder after installation, route to `$okr-assets-inventory`.
