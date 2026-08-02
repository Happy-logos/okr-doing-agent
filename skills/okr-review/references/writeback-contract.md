# Review Writeback Contract

Use this reference only after the user has confirmed a thread or the final one-page report. Confirmation of review content and authorization to write a formal host are two separate decisions.

## v0.1 Host Boundary

```text
Dashboard
→ generate Markdown plus stable metadata preview
→ do not mutate Dashboard storage

Logseq
→ resolve the existing canonical period page
→ preview one managed review-block diff
→ ask for a new explicit write confirmation
→ recheck hashes and create a backup
→ update only that managed review block
```

Never apply a review directly to:

- objective confidence, wording, or state;
- KR wording or state;
- project status, Stage, or Work Item;
- next-period plan;
- 3 Things, Daily Doing, or To-do;
- project Dashboard data;
- an old file named by `legacy-source`.

## Canonical One-Page Payload

Create this JSON outside the Logseq graph before preview:

```json
{
  "schemaVersion": "okr-review/v1",
  "period": {
    "type": "month",
    "label": "2026-07"
  },
  "status": "confirmed",
  "confirmedAt": "2026-07-31T18:30:00+08:00",
  "createdAt": "2026-07-31T18:30:00+08:00",
  "updatedAt": "2026-07-31T18:30:00+08:00",
  "onePage": {
    "facts": [
      "这个周期实际发生的事实。"
    ],
    "coachInsights": [
      "已经被用户校准的 Coach 洞察。"
    ],
    "lookback": [
      "用户确认的第一人称回看。"
    ],
    "judgments": [
      "用户确认的判断。"
    ],
    "nextActions": [
      "用户接受或修改后的下一步。"
    ],
    "modelUpdates": [
      "明确确认的模型更新，或“本周期不更新”。"
    ],
    "evidenceRefs": [
      "[[2026-W27]]",
      "[[2026-W31]]"
    ],
    "chapterTitle": "仅在用户确认时填写"
  }
}
```

Rules:

- `status` must be `confirmed`.
- `confirmedAt` is required and stable so preview and apply render identical bytes.
- `period.type` and `period.label` must match the CLI period.
- Every list contains confirmed report text, not raw source bodies.
- An empty list is allowed and renders as `（无已确认内容）`.
- `chapterTitle` may be empty. Never invent one for completeness.
- Preserve an existing managed block's `review-created-at`; only update `review-updated-at`.

## One-Page Artifact

The user-facing artifact is:

```text
《<period>复盘一页纸》
```

Default sections:

1. What actually happened.
2. Coach insight.
3. My lookback.
4. My judgment.
5. Confirmed next actions.
6. Model update or no update.
7. Evidence references.
8. Chapter title only when the user confirmed one.

Keep the full evidence directory as an appendix or stable reference. Do not paste a second copy of all source records into the report.

## Dashboard Preview

Use one stable review record per period, for example:

```text
review:month:2026:7
```

Proposed review fields may include:

```text
period
factsSnapshot
coachInsights
reviewThreads
periodReflection
confirmedUpdates
reviewReport
reviewConfirmedAt
createdAt
updatedAt
```

When editing an existing review:

- preserve `createdAt`;
- add or update `updatedAt`;
- retain stable thread and evidence IDs;
- do not replay one-time confidence or state effects;
- do not use a legacy `monthClosedAt` field to imply model updates;
- keep project evidence as references to its project source.

Dashboard v0.1 ends at Markdown and metadata preview. Never modify project status from review text. The only project-status contract is owned by the host system.

## Logseq Canonical Target

Write the report into the existing period page, not a second Review page:

| Period | Label | Canonical page title | Managed heading | Stable key example |
|---|---|---|---|---|
| week | `YYYY-Www` | `YYYY-Www` | `周复盘` | `review:week:2026:31` |
| month | `YYYY-MM` | `YYYY M月` | `月度复盘` | `review:month:2026:7` |
| quarter | `YYYY-Qn` | `YYYYQn` | `季度复盘` | `review:quarter:2026:3` |
| year | `YYYY` | `YYYY OKRs` | `年度复盘` | `review:year:2026` |

The resolver may also use an exact `period::` property:

```text
week:     2026-W31
month:    2026-M7 / 2026-M07 / 2026-07
quarter:  2026-Q3 / 2026Q3
year:     2026
```

If zero or multiple pages match, stop. v0.1 does not create a missing period page and does not guess between duplicates.

For the current July example, the target is:

```text
[[2026 7月]]
→ ## 月度复盘
```

Preserve all surrounding content, including:

- page properties;
- `本月入口`;
- `本月项目`;
- `本月大事件`;
- `周入口`;
- `迁移记录`;
- `legacy-source` and `legacy-archive`.

Never follow `legacy-source` and write into the historical file it names.

## Managed Logseq Block

The rendered block is an outline, not a second facts database:

```markdown
- ## 月度复盘
	review-key:: review:month:2026:7
	review-schema:: okr-review/v1
	review-status:: confirmed
	artifact:: 复盘一页纸
	review-created-at:: 2026-07-31T18:30:00+08:00
	review-updated-at:: 2026-07-31T18:30:00+08:00
	- ### 这个周期实际发生了什么
		- ...
	- ### Coach 洞察
		- ...
	- ### 我的回看
		- ...
	- ### 我的判断
		- ...
	- ### 下一步行动
		- ...
	- ### 模型更新
		- ...
	- ### 证据索引
		- [[2026-W27]]
```

The apply workflow supports only:

1. replacing the five untouched legacy placeholders under the expected review heading;
2. updating a block whose `review-key` exactly matches the period;
3. inserting a new managed block before `迁移记录`, or at the page end, when no review block exists.

Stop when:

- more than one expected review heading exists;
- an existing block contains user prose but no matching `review-key`;
- an existing block has a different `review-key`;
- the target or `pages/` directory is a symlink;
- the page changed after preview.

Do not silently convert next actions into Logseq `TODO` blocks. They remain plain report bullets. Creating a Work Item, 3 Things entry, Daily Doing entry, or To-do is a separate operation.

## Preview and Apply Commands

Resolve the script relative to `skills/okr-review/SKILL.md`.

Preview is read-only:

```bash
python3 scripts/write_review_logseq.py \
  --graph "/path/to/authorized-logseq-graph" \
  --period 2026-07 \
  --review-json "/path/to/confirmed-review.json" \
  --pretty
```

The preview must name:

```text
host
target path
stable review-key
operation
managed block diff
preserved surrounding records
sourceSha256
proposedSha256
backup requirement
warnings or conflicts
```

After a new explicit write confirmation, apply the same preview:

```bash
python3 scripts/write_review_logseq.py \
  --graph "/path/to/authorized-logseq-graph" \
  --period 2026-07 \
  --review-json "/path/to/confirmed-review.json" \
  --apply \
  --backup-dir "/path/to/explicit-backup-directory" \
  --expected-source-sha256 "<sourceSha256 from preview>" \
  --expected-proposed-sha256 "<proposedSha256 from preview>" \
  --pretty
```

Apply requirements:

- `--apply` is explicit;
- both expected hashes come from the reviewed preview;
- source hash still matches immediately before writing;
- backup directory is explicit and outside `pages/` and `journals/`;
- the original file is backed up before atomic replacement;
- the written file is re-read and verified against `proposedSha256`;
- a failed write is restored from the in-memory original.

## Decision Separation

Keep these states distinct:

```text
Coach suggestion
user accepted
user modified
user rejected
user deferred
```

Only accepted or user-modified items can enter `nextActions` or `modelUpdates`.

Even then, a confirmed item in the report is not permission to mutate its target object. Each host mutation requires a separate preview and explicit authorization.

## No-Update Outcome

Support:

```text
本周期没有足够证据，不更新判断。
```

This is a complete and valid report outcome.
