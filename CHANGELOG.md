# Changelog

All notable changes to OKR Doing Agent are documented here.
本项目遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Changed
- Claude Code Marketplace 名称由 `candobear` 改为 `happy-logos-okr`,与 Codex 侧保持一致(`candobear` 让位给小能熊官方发布渠道 candobear/agent)。安装 ID 相应改为 `okr-doing-agent@happy-logos-okr`;已装用户需先 `claude plugin marketplace remove candobear`,再按 README 重新添加与安装。

## [1.0.0] - 2026-08-02

### Added
- 新增 `okr-review` skill:从用户授权的 Dashboard、项目导出和 Logseq / Markdown 记录中汇集周、月、季、年真实证据,完成事实回放、Coach 洞察、复盘线索与《复盘一页纸》。
- 新增确定性的 Logseq 写回脚本:定位既有周期页,生成受管复盘块差异预览,在独立确认后执行备份、双哈希复核、原子写入与写后校验。
- 新增 2026 年 7 月完整复盘样本与 Logseq 写回回归测试。

### Changed
- 主入口增加周期复盘路由。
- 新安装的月度页使用稳定 `review-key` 和 `not-started` 受管复盘块。

### Safety
- Dashboard v0.1 只生成 Markdown 写回预览。
- Logseq 只更新周期页受管复盘块,不覆盖无 `review-key` 的用户原文,不跟随 `legacy-source`,也不从复盘正文自动修改目标、KR、项目、Stage、Work Item、3 Things、Daily Doing 或 To-do。

## [0.1.4] - 2026-07-13

### Added
- 新增 `draft-daily-doing` skill:将当前对话中已经完成的工作整理成可直接复制的 Daily Doing Markdown。

### Changed
- 主入口识别“整理成今天的 Daily Doing / 收尾记录 / 做到记录 / 直接复制 Markdown”等请求并路由到新 skill。
- Daily Doing 默认只输出一个 fenced `markdown` 代码块;禁止渲染引用块、重复解释和把讨论方案写成已完成事实。

## [0.1.3] - 2026-07-09

### Docs
- README 增加 `Disclaimer / 免责声明`,说明 OKR Doing Agent 是独立非官方工具,只处理用户本地导出或主动选择的文件。
- `yinxiang-enml-export` 增加 `Safety Boundaries / 安全边界`,明确本地优先、只读校验、资源目录保留、`.notes` 备份-only、不会登录或解密。

### Safety
- 明确不登录印象笔记 / Evernote,不调用私有或非官方接口,不上传原始笔记或附件,不绕过访问控制,不声称与相关服务存在官方合作、认证或背书。

## [0.1.2] - 2026-07-09

### Changed
- 主入口自我介绍改为三件用户能直接理解的事:OKR 系统安装、OKR 资产盘点、OKR 资产迁移。
- 将原“历史来源准备”并入公开的“OKR 资产盘点”介绍；内部仍通过 `yinxiang-enml-export` 处理印象笔记 / Evernote 的 `content.enml`、HTML、`.resources`、`.notes` 来源校验。
- 明确说明:必要时,在支持 computer use 的环境里,Agent 可以帮用户从印象笔记导出 HTML 并校验可读性。
- README、Codex 插件元数据、Claude marketplace 元数据同步改为三件事版本。

## [0.1.1] - 2026-07-09

### Added
- **印象笔记 ENML / HTML 导出** `yinxiang-enml-export`:盘点印象笔记 / Evernote 的 `content.enml`、单条 HTML 导出、`.resources` 附件目录和 `.notes` 备份,确认哪些素材可作为迁移源。
- 主入口 `okr-doing-agent` 增加“历史来源准备”入口,遇到 `印象笔记`、`Evernote`、`Yinxiang`、`ENML`、`HTML 导出`、`.notes` 时路由到 `yinxiang-enml-export`。
- 插件 metadata 增加 `yinxiang`、`evernote`、`enml` 相关描述和关键词,便于在 Codex / Claude Code 插件界面中发现。

### Changed
- README 的工作流从三条扩展为四条:系统安装、历史来源准备、资产盘点、资产迁移。
- 迁移说明改为“预览 -> 确认 -> 写入”,与当前迁移 skill 的确认写入能力保持一致。

### Safety
- 印象笔记来源准备不写入 Logseq,不删除、不移动、不覆盖旧导出。
- `.notes` 批量导出默认视为备份证据；若正文为加密内容,不作为直接迁移源。

## [0.1.0] - 2026-06-30

首个公开版本 —— 同时兼容 Claude Code 与 Codex 的双插件。

### Added
- **主入口 skill** `okr-doing-agent`:理解用户意图并路由到三条工作流。
- **OKR 系统安装** `okr-system-install`:两段式 dry-run 预览 → 同名冲突检查 → 确认后 `--apply` 写入。
- **OKR 资产盘点** `okr-assets-inventory`:旧个人 OKR 文件夹的只读扫描,生成资产地图。
- **OKR 资产迁移** `okr-migration-plan`:基于盘点报告生成分批迁移融合方案(只出方案,不写入)。
- 确定性安装器 `scripts/first_run_dry_run.py`,十年尺度的 Logseq OKR 系统页面 + 可调用模板包。
- Claude Code 清单(`.claude-plugin/plugin.json` + `marketplace.json`)与 Codex 清单(`.codex-plugin/plugin.json`)。
- 单元测试覆盖 dry-run、冲突停止、apply 写入与资产盘点。

### Safety
- 盘点阶段只读,永不写入。
- 安装遇到同名页面冲突即停止,绝不覆盖已有内容。
- 迁移真实写入需用户单独确认。

### Not yet
- Obsidian / 纯 Markdown 安装。
- 写入前自动备份策略。
- 迁移阶段的真实落盘。
