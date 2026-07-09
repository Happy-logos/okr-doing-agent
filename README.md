<div align="center">

# OKR Doing Agent

**Don't just track your OKRs. Do them.**

一个运行在 **Codex / Claude Code** 上的 OKR 执行 Agent。
OKR 不止追踪,更要做到。

`OKR` · `Doing Agent` · `Codex Plugin` · `Claude Code Plugin` · `Logseq` · `Yinxiang / Evernote` · `Personal Operating System`

</div>

---

## Why · 为什么要一个"做到" Agent

大多数 OKR 工具都停在**追踪目标**:你写下 Objective、列出 Key Results,然后……就没有然后了。

> Traditional OKR **tracks** goals.
> Doing Agent **builds** execution.

真正的问题从来不是"目标写得好不好",而是:

- 系统搭起来太累 —— 手动建页面、打双链,目标还没开始,人先被绕晕。
- 写完就断 —— 年度目标和这一周的行动之间,没有通路。
- 复盘变审判 —— 没做到 = 自我否定,而不是更新判断。

OKR Doing Agent 的立场只有一句:

```text
OKR 是壳,做到是内核,真实问题是入口,一周行动是交付。
```

它把"长期方向 → 年度判断 → 项目战场 → 周/月执行 → 日记证据 → 复盘更新"接成一条**可以真的走下去**的回路,并安装进你本地的 Logseq。

---

## Architecture · 它由什么构成

不是一个提示词,而是一套**可安装、可调用、可复盘**的本地系统:

```text
okr-doing-agent/
├── skills/                 # Agent 的能力(= 真正的 prompts)
│   ├── okr-doing-agent/    #   主入口:理解你想做哪件事,再路由
│   ├── okr-system-install/ #   新系统安装(dry-run 预览 → 确认 → 写入)
│   ├── yinxiang-enml-export/#  印象笔记 / Evernote ENML、HTML、.notes 来源校验
│   ├── okr-assets-inventory/#  旧资产只读盘点
│   └── okr-migration-plan/ #   迁移融合(预览 → 确认 → 写入)
├── scripts/                # 确定性安装器(dry-run / --apply)
├── templates/logseq/       # 系统页面 + 可调用模板包
├── .claude-plugin/         # Claude Code 清单
└── .codex-plugin/          # Codex 清单
```

同一套 `skills/`,**Claude Code 和 Codex 通吃**。

---

## How it thinks · 它的判断规则

这是这个 Agent 和"模板生成器"的根本区别 —— 它带着一套**反馈原则**在工作,会主动拦住你把系统做坏:

| 原则 | 含义 |
|---|---|
| 年度页不要做重 | 年度页只放方向、KR、项目链接和复盘日志,不堆执行细节 |
| 项目页才是战场 | 真正的执行、障碍、证据,都在项目页发生 |
| 周/月是执行单位 | 落不到这一周的目标,等于没落地 |
| 日记是行动流 | 允许很短,它记录的是真实动作,不是每日长复盘 |
| 复盘是 Bayesian Update | 复盘=用新证据更新判断,不是给自己定罪 |
| 失败是黑匣子数据 | 失败和意外进入"大事件"页,成为下一次决策的输入 |

它还有明确的 **stop rules**:来源准备和盘点阶段**永不写目标图谱**;安装遇到同名页面冲突会**停下来**,绝不覆盖你已有内容;迁移必须先出预览,真实写入需要你单独确认。

> 安全设计不是附加项,而是这个 Agent 敢碰你真实知识库的前提。

---

## Workflow · 三件事

### 1 · OKR 系统安装

帮你在 Logseq 里搭起一套个人 OKR 做到系统:Dashboard、十年计划、年度 OKR、季度、月份、当前周入口,以及十年计划 / 年度 OKR / 项目 OKR / 大事件 / daily routine / 周复盘模板。

底层双向链接在生成那一刻就已经接通。写入前先给你 dry-run 预览,确认后才落盘。


![OKR Dashboard](http://img.candobear.com/2026-06-29-d04dc9ab6ee4e1281e0955a5ec5c433f.png)

### 2 · OKR 资产盘点

盘清两类旧资料:本地 OKR 文件夹里的年度、项目、复盘、模板和资料;以及印象笔记 / Evernote 里的 `content.enml`、HTML、`.resources` 和 `.notes`。必要时,在支持 computer use 的环境里,Agent 可以帮你从印象笔记导出 HTML,并校验可读性。

`OKR 资产盘点` 会生成一份「OKR 资产地图」和「可迁移源清单」:哪些还值得用、哪些适合归档、哪些需要人工确认、哪些刚好是你重新出发的起点。

![资产地图](http://img.candobear.com/2026-06-29-bea7c652c924a36e8e608864ec32f402.png)

### 3 · OKR 资产迁移

根据资产盘点结果,Agent 陪你分批把旧资产接进新系统:哪些保留、哪些合并、哪些归档、哪些先不动。每一批都会先给你看清楚,再按确认结果处理。

![迁移后的年度 OKR](http://img.candobear.com/2026-06-30-8ed2d05ea076433786cc2101cc233a44.png)

---

## Examples · 真实样例

想先看它实际长什么样,不必安装。`examples/` 里有脱敏的真实输出:

- [`examples/01-install-preview.md`](examples/01-install-preview.md) —— 安装前的 dry-run 预览
- [`examples/02-asset-inventory.md`](examples/02-asset-inventory.md) —— 一份 OKR 资产地图
- [`examples/03-weekly-review.md`](examples/03-weekly-review.md) —— 一次 Bayesian Update 式周复盘

---

## Install · 安装(需要的人占 10%)

> 真正安装的人是少数;但少数人,值得一份能一次跑通的说明。

**环境要求:** `python3`(无第三方依赖)+ 一个本地 Logseq 图谱目录。

### Claude Code

终端 CLI(任何环境都能用,推荐):

```bash
claude plugin marketplace add Happy-logos/okr-doing-agent
claude plugin install okr-doing-agent@candobear
```

或在 Claude Code 交互界面里(若该环境支持 `/plugin`):

```text
/plugin marketplace add Happy-logos/okr-doing-agent
/plugin install okr-doing-agent@candobear
```

安装后**重启 Claude Code** 加载 skills,然后对它说「帮我安装 OKR 系统」即可触发。

### Codex

```bash
git clone https://github.com/Happy-logos/okr-doing-agent.git
# 将该目录加入 Codex 插件市场,清单见 .codex-plugin/plugin.json
```

加载后用 `$okr-doing-agent` 进主入口,或直接调用
`$okr-system-install` / `$yinxiang-enml-export` / `$okr-assets-inventory` / `$okr-migration-plan`。

### 第一次怎么用

1. 选 **OKR 系统安装**,只回答一个问题:你的 Logseq 图谱路径。
2. 看 dry-run 预览(生成哪些页面、建立哪些关系、有无冲突)。
3. 确认后 apply 写入。
4. 装好后,再决定要不要盘点旧资产、整理印象笔记 / Evernote 来源、做迁移。

> 首次安装不会问你的目标、卡点或项目 —— 先把容器装好,再谈做什么。

---

## Roadmap

- [ ] Obsidian / 纯 Markdown 安装
- [ ] 写入前自动备份策略
- [ ] 更完整的印象笔记批量导出自动化
- [ ] 周/月复盘的提醒回路

## About

Built by **HappyGoFox** —— 一个持续构建 Personal Agent OS 的个人产品实验。
OKR Doing Agent 是其中"做到"这一层。

## License

[MIT](LICENSE)
