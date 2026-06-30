# Changelog

All notable changes to OKR Doing Agent are documented here.
本项目遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

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
