# Period Evidence Contract

Use this reference before reading Dashboard, project, Logseq, or Markdown sources.

## Read-Only Source Rule

Read only user-authorized paths. Never modify, normalize, rename, move, or delete a source record while building evidence.

Keep these layers separate:

```text
source records = source of truth
period evidence pack = recomputable read-only index
review one-page = new confirmed interpretation
model updates = separate explicit decisions
```

## Supported Periods

```text
YYYY-Www
YYYY-MM
YYYY-Qn
YYYY
```

Include records by actual occurrence date. For interval events, include them when their interval intersects the period and keep the full interval.

Mark uncertain dates instead of inventing a day.

## Source Meanings

Do not flatten distinct sources:

```text
3 Things = intended weekly focus
completed To-do = routine or operational responsibility actually carried
Daily Doing = action, delivery, observation, or reflection
Work Item / Activity = project progress trajectory
Milestone / Asset = formed delivery or reusable result
objective judgment = model changes over time
major event = meaningful life or work interval
```

When one event appears in several sources, create one logical group with multiple evidence references. Do not increase its importance merely because it was recorded more than once.

## Script Interface

Resolve `../scripts/build_review_evidence.py` relative to this file's parent skill directory.

```bash
python3 scripts/build_review_evidence.py \
  --period 2026-07 \
  --dashboard-json "/path/to/dashboard.json" \
  --project-json "/path/to/project.json" \
  --logseq-root "/path/to/graph"
```

All source flags are repeatable. The script writes JSON to stdout unless `--output` is supplied.

An explicit output must not overwrite an input or be placed inside an authorized Logseq source root.

## Evidence Pack Shape

```text
schemaVersion
generatedAt
period
  type
  label
  start
  end
sources[]
coverage
  daily
  dailyUnlinked
  weeklyThings
  todos
  todosDone
  weeklyReviews
  weeklyReviewPlaceholders
  projects
  objectives
  bigEvents
  markdown
evidence[]
  id
  occurredAt
  sourceType
  sourceRef
  title
  body
  bodyTruncated
  links[]
  originalRecordRef
  relations
groups
  byWeek
  byProject
  byObjective
  byBigEvent
  unlinked
warnings[]
```

`body` may be a bounded excerpt. `originalRecordRef` must remain sufficient to return to the source.

## Dashboard Adapter

For a Dashboard export:

- prefer `annualOkrByYear[year]`;
- fall back to `annualOkr<year>`;
- read Daily entries from `os[].dailyDoingDrafts`;
- read weekly intent from `weeklyThingsByIso`;
- read routine responsibility from `routineTodosByIso`;
- read week reviews from `reviewTimelineDrafts`;
- read project snapshots from `os[].projectDrafts`;
- read events from `bigEvents`;
- treat `PROJECT_PROGRAMS` as a project catalog, not as a full project history.

Avoid double counting alias copies of the same annual object. Prefer stable record IDs; otherwise de-duplicate with a date, source type, and content signature.

Do not use a Dashboard export as permission to open or modify the user's formal browser draft.

## Project Export Adapter

Accept a JSON list or a JSON object containing collections such as:

```text
projects
programs
workItems
activities
milestones
assets
evidence
```

Include dated records inside the period and interval records that overlap it. Preserve their collection name and stable ID. Unknown structures should produce a warning, not invented evidence.

## Logseq / Markdown Adapter

Scan only `pages/`, `journals/`, or the exact authorized Markdown folder.

Recognize dates from:

- journal filenames such as `YYYY_MM_DD`, `YYYY-MM-DD`, or `YYYYMMDD`;
- explicit Logseq properties such as `date::`, `period::`, `created-at::`, or `updated-at::`;
- standard period labels in page names.

Use the file path as the stable original reference. Keep only a bounded excerpt in the evidence pack. Do not rewrite links or properties.

## Coverage and Warnings

Always report:

- which sources were present;
- which expected sources were absent;
- record counts by source type;
- date conflicts;
- parsing gaps;
- records that could not be associated with a project, objective, or event.

A missing source reduces completeness but does not invalidate other evidence.
