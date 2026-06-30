---
name: okr-assets-inventory
description: Use when the user wants to scan, inventory, audit, or plan migration for an existing local personal OKR folder or old OKR system. This skill only reads local files, classifies OKR assets such as decade plans, annual OKRs, projects, reviews, templates, resources, events, and journals, then produces an OKR asset map and migration planning report. Use for "OKR 资产盘点", old personal OKR folders, migration maps, and fusion planning into OKR Doing Agent. Do not use for coaching a user's current OKR quality, project strategy, or personal blockers.
---

# OKR 资产盘点

Use this skill to inspect an old local personal OKR system and produce a read-only asset map for migration planning.

## Boundary

This skill is not OKR coaching.

It should answer:

```text
旧 OKR 文件夹里有什么?
哪些资产能接进新 OKR OS?
哪些适合归档?
哪些需要人工确认?
迁移融合时有哪些风险?
```

It should not answer:

```text
这个目标写得好不好?
用户为什么做不到?
这周该怎么调整人生策略?
是否应该进入契约或 1v1 咨询?
```

Those belong to a future OKR Coach / consultation workflow.

## Safety Rules

- Read only. Do not write into the old folder or the new Logseq graph.
- Do not move, rename, delete, normalize, or rewrite user files.
- Do not copy private OKR content into public docs.
- Prefer file counts, titles, paths, short excerpts, and classification labels.
- If migration is requested, produce a plan or dry-run report only.
- Stop before apply/write behavior unless a separate migration skill and explicit confirmation exist.

## Workflow

1. Ask for the old OKR folder path if it is missing.
2. Optionally ask for the new Logseq graph path if the user wants conflict/routing checks.
3. Run the bundled script:

```bash
python3 scripts/okr_assets_inventory.py --source "<old OKR folder>"
```

With a target graph:

```bash
python3 scripts/okr_assets_inventory.py \
  --source "<old OKR folder>" \
  --target-graph "<new Logseq graph>"
```

Resolve `scripts/okr_assets_inventory.py` relative to this `SKILL.md`.

4. Read the report and summarize the highest-signal migration map.
5. If the user wants next steps, propose a migration plan. Do not write files.

## Report Shape

The user-facing summary should use these sections:

```text
OKR 资产地图
迁移建议
建议归档
需要人工确认
风险与冲突
下一步
```

Use short Chinese labels:

```text
可接入
建议归档
人工确认
暂不迁移
```

## Routing Heuristics

Prefer these new-system destinations:

```text
旧十年/长期规划 -> [[十年计划（YYYY-YYYY）]]
旧年度 OKR -> [[YYYY OKRs]]
旧季度/月度计划 -> [[YYYYQn]] 或 [[YYYY M月]]
旧项目页 -> [[Project/<项目名>]]
旧大事件/转折点 -> [[大事件/<事件名>]]
旧周报/周复盘 -> [[YYYY-Wxx]]
旧模板 -> [[OKR Templates]] 或归档
旧资源资料 -> 资源索引,不塞进年度页
```

When uncertain, mark `人工确认` instead of inventing a destination.

## Output Tone

Use asset language, not judgment language.

Say:

```text
这些是可以接回新系统的资产。
这些内容更适合归档,不需要搬进执行层。
这部分需要你确认它属于项目、资源,还是复盘材料。
```

Avoid:

```text
你的旧系统很混乱。
这些目标质量不好。
你过去执行力不足。
```
