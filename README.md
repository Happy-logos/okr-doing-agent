# OKR Doing Agent

把一套轻量、可链接、可复盘的个人 OKR 系统**安装到你本地的 Logseq**，并安全地盘点、迁移你过去的旧 OKR 资产。

> OKR 是壳，做到是内核，真实问题是入口，一周行动是交付。

这是一个**同时兼容 Claude Code 和 Codex** 的插件。两边读同一套 `skills/`，安装方式见下。

---

## 它能做三件事

| Skill | 作用 | 是否写文件 |
| --- | --- | --- |
| **OKR 系统安装** (`okr-system-install`) | 在 Logseq 里生成 Dashboard、十年计划、年度 OKR、Q1–Q4、1–12 月、当前周入口，以及一套可调用模板 | 先 dry-run 预览，**确认后**才写 |
| **OKR 资产盘点** (`okr-assets-inventory`) | 只读扫描你旧的个人 OKR 文件夹，生成「资产地图」和迁移建议 | **只读，永不写** |
| **OKR 资产迁移** (`okr-migration-plan`) | 基于盘点报告，生成分批迁移融合方案 | 只出方案，**不写** |

主入口 skill `okr-doing-agent` 会先问你想做哪一件，再路由到对应工作流。

### 安全设计

- 盘点阶段**只读**：不移动、不重命名、不删除、不改写任何旧文件。
- 安装走 **dry-run → 同名页面冲突检查 → 你确认 → apply** 两段式。
- 发现同名页面冲突会**停下来**，不覆盖你已有内容。

---

## 安装

### Claude Code

```bash
# 1. 添加这个仓库为插件市场
/plugin marketplace add Happy-logos/okr-doing-agent

# 2. 安装插件
/plugin install okr-doing-agent@candobear
```

之后直接对 Claude Code 说「帮我安装 OKR 系统」即可触发。

### Codex

```bash
# 克隆仓库到本地
git clone https://github.com/Happy-logos/okr-doing-agent.git

# 在 Codex 的插件市场配置里加入该目录（指向克隆下来的路径），
# 插件清单见 .codex-plugin/plugin.json
```

加载后用 `$okr-doing-agent` 进入主入口，或直接 `$okr-system-install` / `$okr-assets-inventory` / `$okr-migration-plan`。

---

## 环境要求

- `python3`（安装/盘点脚本用，无第三方依赖）
- 一个本地 Logseq 图谱目录（写入目标）

---

## 第一次怎么用

1. 让 agent 自我介绍，选 **OKR 系统安装**。
2. 只回答一个问题：你的 Logseq 图谱路径在哪。
3. 看 dry-run 预览（会生成哪些页面、建立哪些关系、有无冲突）。
4. 确认无误后，让它 apply 写入。
5. 装好后，再决定要不要盘点旧资产、做迁移。

> 首次安装不会问你的目标、卡点或项目——先把容器装好，再谈做什么。

---

## 仓库结构

```text
.claude-plugin/plugin.json       # Claude Code 插件清单
.claude-plugin/marketplace.json  # Claude Code 插件市场清单
.codex-plugin/plugin.json        # Codex 插件清单
skills/                          # 四个 skill（两边共用）
  okr-doing-agent/               #   主入口 / 路由
  okr-system-install/            #   新系统安装（dry-run + apply）
  okr-assets-inventory/          #   旧资产只读盘点
  okr-migration-plan/            #   迁移融合方案
scripts/first_run_dry_run.py     # 安装器（dry-run / --apply）
templates/logseq/                # 系统页面模板 + 可调用模板包
tests/                           # 单元测试
```

---

## 路线图（v0 暂不做）

- Obsidian / 纯 Markdown 安装
- 写入前自动备份策略
- 自动提醒 / 日历 / 外部服务
- 迁移阶段的真实写入（目前只出方案，写入需另行确认）

## License

MIT
