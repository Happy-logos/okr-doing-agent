---
name: okr-review
description: Review a week, month, quarter, or year from real local evidence and coach the user toward their own understanding, judgment, and next action. Use when the user says 开始月复盘, 开始 7 月复盘, 本周我做了什么, 季度复盘, 年度回看, 帮我汇集 Daily Doing / 每周 3 Things / To-do / 项目记录, 继续上次复盘, 生成复盘一页纸, 写回复盘到 Logseq, or wants to review authorized Dashboard JSON, project exports, Logseq, or Markdown records. Keep evidence gathering read-only, distinguish facts from Coach inference and user decisions, preview every writeback, and only update the managed review block of an authorized Logseq period page after a separate explicit confirmation.
---

# OKR Review

Use real records to reduce recall work, then coach the user through a bounded review. Treat the user as the owner of first-person meaning and every final decision.

## Choose the Operation

Match the narrowest requested mode:

1. **事实回放** — Answer questions such as “本周我做了什么？” and stop after a traceable evidence summary.
2. **引导复盘** — Build the evidence pack, offer a Coach insight, review one meaningful thread at a time, and produce a confirmed one-page report.
3. **写回复盘** — For a previously confirmed one-page report, preview the exact Logseq target and diff. Apply only after a separate explicit confirmation, a source-hash recheck, and a successful backup. Dashboard remains preview-only.

When the user says “开始复盘” without narrowing the mode, use 引导复盘.

## Keep the Boundary

- Read only from paths and files the user has placed in scope.
- Do not scan the whole home directory, vault, or Logseq graph when the authorized source is unclear.
- Do not copy project Dashboard data into the main Dashboard JSON. Preserve it as a second source with stable references.
- Do not write to a formal Dashboard draft, project file, objective, KR, Stage, Work Item, 3 Things, Daily Doing, or To-do.
- The only supported formal write is one managed review block in an authorized Logseq period page, after the host-specific preview and confirmation gate in Step 10.
- Do not turn every life insight into an OKR or action.
- Do not present Coach inference as fact or as the user's first-person voice.
- Do not continue into project implementation after the review thread has reached a judgment.

Read [references/evidence-contract.md](references/evidence-contract.md) before gathering files. Read [references/review-method.md](references/review-method.md) before entering Coach mode. Read [references/writeback-contract.md](references/writeback-contract.md) completely before preparing, previewing, or applying any writeback.

## Workflow

### 1. Resolve the Period

Infer the period when the user has already named it. Ask one short question only when the period is genuinely ambiguous.

Supported labels:

```text
week     YYYY-Www
month    YYYY-MM
quarter  YYYY-Qn
year     YYYY
```

Use the record's actual occurrence date for inclusion. A week may cross a month boundary, but a monthly review must not count next month's Daily entries.

### 2. Discover Authorized Sources

Prefer sources in this order:

1. Dashboard draft export JSON explicitly supplied by the user.
2. Project Dashboard or normalized project export explicitly supplied by the user.
3. Authorized Logseq graph or Markdown folder.
4. Material the user adds in the current review conversation.

Tell the user which sources are being read and which expected sources are missing. Missing sources lower confidence; they do not block the review.

### 3. Build the Evidence Pack

Resolve `scripts/build_review_evidence.py` relative to this `SKILL.md`.

Dashboard export:

```bash
python3 scripts/build_review_evidence.py \
  --period 2026-07 \
  --dashboard-json "/path/to/dashboard-export.json"
```

Dashboard plus a Logseq graph:

```bash
python3 scripts/build_review_evidence.py \
  --period 2026-07 \
  --dashboard-json "/path/to/dashboard-export.json" \
  --logseq-root "/path/to/logseq-graph"
```

Add `--project-json "/path/to/project-export.json"` for a separately exported project evidence source. Use `--output` only for an explicit preview destination outside the source graph; otherwise read JSON from stdout.

Do not expose large private bodies in the chat. Use counts, titles, dates, short excerpts, relationship labels, and source references. Open original records only when needed to verify a claim.

### 4. Present the Fact Playback

Show a layered overview before analysis:

```text
周期与来源覆盖
实际发生的主要事情
周节奏或时间变化
项目 / 目标 / 大事件 / 未关联线索
持续责任与 To-do
未闭环事项
信息缺口
```

Facts must be traceable. Keep Agent-generated summaries visibly separate from original text. Offer the full evidence directory as an expandable appendix rather than dumping it into the main review.

If the user requested facts only, stop here.

### 5. Give One Coach Insight

Use this reasoning path:

```text
表面现象
→ 排除泛化诊断
→ 找到主要矛盾或阶段变化
→ 提出核心判断
→ 给出证据链与不确定性
→ 请用户校准
```

Default to:

- 1 core insight
- 0–2 secondary observations only when materially useful
- at least 2 independent evidence references, or a clear plan-versus-reality gap
- 1 question that can change the user's understanding or choice

Do not use “事情太多”“需要聚焦”“坚持下去” as a substitute for analysis.

### 6. Offer Review Threads

Offer 1–4 candidate threads selected by this standard:

```text
值得深入
会改变认识
可能改变选择
或需要保存人生意义
```

Do not create one thread per project. A thread may be a project, objective, event, relationship, body signal, recurring pattern, or contradiction across sources.

Let the user choose. Review one thread at a time.

### 7. Coach One Thread

For the selected thread:

1. Replay only the evidence relevant to it.
2. Ask one question at a time.
3. Mirror the user's response without adding a personality diagnosis.
4. Let the user correct the Coach insight.
5. Continue until the user has an understanding and a judgment, or explicitly says the evidence is insufficient.

Usually ask 2–3 questions at most. Ask more only when the user actively wants to deepen the thread and the next question could change the result.

First-person text may only be drafted from the user's already expressed and confirmed meaning.

### 8. Close the Thread

Stop questioning when:

- the user has said what the thread means;
- the core insight has been confirmed, corrected, or rejected;
- the user has made a judgment or chosen to keep observing;
- the conversation starts drifting into feature design, architecture, or implementation;
- the user says “先写下来”, “收尾”, or equivalent wording.

The Coach may suggest at most:

- 1 immediate capture action;
- 1 next-period validation action.

Keep suggestions separate from decisions. Ask the user to accept, modify, reject, or choose no action.

Use this completion card:

```markdown
## 本条复盘完成

### 我的认识

### 我的判断

### Coach 建议

#### 现在可以做

#### 下个周期可以验证

### 我的决定

### 暂不展开
```

After confirmation, return to the remaining thread list. The user may continue or finish the period. Stopping after one useful thread is valid.

### 9. Produce the One-Page Report

When the user ends the period review, generate `《<周期>复盘一页纸》`:

```text
这个周期实际发生了什么
Coach 洞察
我的回看
我的判断
下一步行动
模型更新 / 本周期不更新
章节标题（仅在用户确认时）
```

Keep the full evidence directory outside the one-page body as a referenced appendix.

Do not call this output “收月”. Do not invent a chapter title for completeness.

### 10. Preview and Confirm Writeback

Do not treat confirmation of the review text as permission to write a file. Start a separate host writeback gate.

For Dashboard, show the Markdown and stable metadata preview, then stop. Dashboard apply is not implemented.

For Logseq:

1. Serialize the confirmed one-page report as `okr-review/v1` JSON outside the Logseq graph. Use the exact schema in [references/writeback-contract.md](references/writeback-contract.md).
2. Resolve `scripts/write_review_logseq.py` relative to this `SKILL.md`.
3. Generate a read-only preview:

```bash
python3 scripts/write_review_logseq.py \
  --graph "/path/to/authorized-logseq-graph" \
  --period 2026-07 \
  --review-json "/path/to/confirmed-review.json" \
  --pretty
```

4. Show the exact period page, operation, managed block diff, preserved sections, warnings, source hash, proposed hash, and backup destination.
5. Ask for a new explicit confirmation that names this Logseq write. A previous “确认” used to close a review thread or approve the report does not count.
6. Only after that confirmation, apply the unchanged preview:

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

If the source page changed after preview, the script must stop. Generate a new preview; never force the old diff through.

The Logseq apply may only replace the empty legacy review placeholders, update a block with the same `review-key`, or insert a new managed review block when none exists. It must not overwrite an unkeyed block containing user prose.

## Success Conditions

A useful run must satisfy all applicable conditions:

- the evidence period is correct;
- facts can return to source records;
- Daily, 3 Things, To-do, projects, objectives, and events keep distinct meanings;
- the user can reject the Coach insight;
- first-person text belongs to the user;
- every confirmed action is visibly different from a suggestion;
- the review can end with no model update;
- implementation questions are parked rather than expanded;
- the final artifact is a concise one-page report plus evidence references.
- any Logseq apply matches the reviewed diff, has a verified backup, and changes only the managed review block.

## Safety Stops

Stop and explain the boundary when:

- the requested path is not authorized or the source type is unclear;
- a proposed output would overwrite a source record;
- the period page is missing or more than one page matches the period;
- the existing review block contains unkeyed user prose or a different `review-key`;
- the page hash no longer matches the preview, or the backup destination is unsafe;
- the evidence contains conflicting dates that materially change the review;
- the user requests medical, legal, financial, or mental-health diagnosis from review evidence;
- the user asks for silent edits to formal records;
- the user asks the Agent to interpret private life evidence as a definitive personality judgment.

When evidence is insufficient, say so and offer either a narrower fact playback or one short request for the missing source.
