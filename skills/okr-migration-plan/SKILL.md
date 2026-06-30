---
name: okr-migration-plan
description: "Use when the user wants OKR 资产迁移 or guided migration/fusion support after OKR 资产盘点: turning an inventory report into batches, destination mapping, conflict handling, previewed write-in steps, and explicit-confirmation migration into the new OKR Doing Agent Logseq system. If no inventory report exists, first route to okr-assets-inventory. Do not rescan the whole project when a current inventory report is available. Do not move, delete, or overwrite old assets; write to the new graph only after preview, backup advice, and explicit confirmation."
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
```

It does not own:

```text
重新全量盘点旧项目
移动、重命名、删除旧文件
无预览直接批量写入
自动覆盖现有页面
判断 OKR 质量或做 coaching
```

Write only to the new graph after the user provides the target graph path, sees a per-batch preview, receives a backup reminder, and explicitly confirms that batch.

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

Work batch by batch:

```text
1. Read the inventory report.
2. Pick the smallest useful batch to migrate next.
3. Show the target page map and conflicts.
4. Show a write preview before touching files.
5. Write only after explicit confirmation.
6. Summarize changed files and the next batch.
```

Group migration into batches:

```text
Batch 1: 年度 / 十年骨架
Batch 2: 项目资产
Batch 3: 周复盘 / 月度复盘 / Bayesian Update 材料
Batch 4: 大事件 / 里程碑 / 黑匣子数据
Batch 5: 模板和资源资料
Batch 6: 暂不迁移 / 归档
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
确认口令 / 下一步
```

Before confirmation, keep the final next step preview-first:

```text
确认后我只处理这一批；旧文件不移动、不删除。
```

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
