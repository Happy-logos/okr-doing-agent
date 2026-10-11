---
name: draft-daily-doing
description: Turn work that just finished in the current conversation into a concise, copy-ready Daily Doing Markdown entry. Use when the user says 整理成今天的 Daily Doing, 收尾记录, 记到 Daily Doing, 做到记录, 今日记录, 帮我整理成可以直接复制的 Markdown, or asks for a Markdown entry summarizing completed work. Return raw Markdown in a fenced markdown block by default; do not write to the user's real OKR files or Dashboard unless separately authorized.
---

# Draft Daily Doing

Convert a completed work session into one small Daily Doing moment. Preserve what actually happened; do not turn it into a report, questionnaire, or retrospective.

## Workflow

1. Read the current conversation first.
2. Separate completed actions from discussion, proposals, and unverified plans.
3. Write the title as one sentence that still makes sense on its own when the user looks back at the day: the object plus what got done or decided, about 30 Chinese characters or fewer. Use 「定了：……」 for a decision, 「读《……》：……」 for something learned, 「卡住：……」 for a blocker. The Daily Doing review shows only this line, so a topic without a result (「同步 ③-2 手机拉取」), a bare book title, a date header, a project name, or a list item is not a title.
4. Keep 2-5 bullets covering only useful facts:
   - what changed or was completed
   - the concrete result
   - evidence or verification, when available
5. Remove implementation chatter, repeated history, and speculative next steps.
6. Return the copy-ready Markdown using the output contract below.

Do not scan the whole workspace when the conversation already contains enough evidence. Read a named artifact only when needed to confirm a fact.

## Output Contract

By default, the final answer must contain exactly one fenced `markdown` block and no prose before or after it, unless a higher-level instruction requires a disclosure or citation.

Inside the block:

- Put the title sentence on the first line. Do not prefix it with `#` or `-`, and do not put a date or project name there.
- One block covers one piece of work. If the conversation advanced several unrelated things, write one block per thing instead of a whole-day summary.
- Leave one blank line after the title.
- Use short Markdown bullets for the body.
- Do not use blockquotes, tables, frontmatter, or nested explanatory sections.
- Do not include the date; the Daily Doing page already supplies it.
- Do not add “下一步行动”, “复盘”, “启发”, or “学到了什么” unless the user explicitly asks.
- Do not invent an O, project, 3 Things, To-do, result, or verification.
- Do not place relation suggestions in the body unless the user explicitly asks for them.
- Keep the entry compact enough to paste without editing.

Use this exact shape:

````markdown
```markdown
对象：做成了什么（或「定了：……」）

- 已完成的事实。
- 得到的结果。
- 验证或证据。
```
````

The fenced block matters: rendered Markdown, a blockquote, or ordinary prose is not considered copy-ready output.

## Content Rules

### Prefer

- “完成”“调整”“确认”“验证”等已经发生的事实。
- 用户和产品当前使用的名称。
- 能帮助以后回看的一条结果或证据。
- 一轮工作只保留一个中心。

### Avoid

- 把讨论过的方案写成已经完成。
- 把多个无关事项拼成长周报。
- 重复用户已经知道的背景。
- 为了显得完整而补新的判断。
- 写成 “今天我们……” 的会议纪要口吻。
- 在代码块外再次复述同一内容。

## Relation Handling

Daily Doing 的正文与关系选择分开处理。

- 默认只输出正文代码块。
- 如果用户同时询问关联对象，先给正文代码块，再用一行列出建议关联。
- 只有在当前对话中已经明确出现对应名称时，才建议 O、项目、3 Things、To-do 或大事件。
- 关系建议不是正文的一部分，不要让用户复制后还需要删除。

## Missing Evidence

If the conversation does not establish what was actually completed, ask one short question instead of fabricating an entry.

If some items were completed and others only discussed, include only the completed items. Mention unverified work only when the user explicitly wants a work log that records uncertainty.

## Regression Example

User:

`收尾，把这轮工作整理成今天的 Daily Doing。`

Correct output:

````markdown
```markdown
OKR Dashboard：完成本周工作台的一轮交互收敛

- 统一 3 Things 与 Daily Doing 的连接方式。
- 历史周可以回看并分别复盘 Thing 与 To-do。
- To-do 支持每周重复，相关操作收进三点菜单。
- 迁移测试页已通过脚本静态检查。
```
````

Incorrect:

- a rendered blockquote
- a prose summary followed by a second copy
- “建议关联” mixed into the body
- planned work presented as completed
