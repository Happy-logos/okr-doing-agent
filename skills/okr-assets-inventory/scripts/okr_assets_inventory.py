#!/usr/bin/env python3
"""Read-only inventory for an old personal OKR folder.

The script scans Markdown/text files, classifies likely OKR assets, and prints
a migration-planning report. It never writes to the source or target graph.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


TEXT_SUFFIXES = {".md", ".markdown", ".txt"}
MAX_EXCERPT_CHARS = 140


@dataclass(frozen=True)
class Asset:
    path: str
    title: str
    category: str
    destination: str
    confidence: str
    reason: str
    excerpt: str


@dataclass(frozen=True)
class Conflict:
    asset_path: str
    destination: str
    existing_path: str


@dataclass(frozen=True)
class InventoryReport:
    source: str
    target_graph: str | None
    total_files_seen: int
    text_files_scanned: int
    assets: list[Asset]
    conflicts: list[Conflict]
    category_counts: dict[str, int]
    destination_counts: dict[str, int]
    recommended_next_steps: list[str]


def build_inventory(source: str, target_graph: str | None = None) -> InventoryReport:
    source_path = Path(source).expanduser()
    if not source_path.exists():
        raise FileNotFoundError(f"source folder does not exist: {source_path}")
    if not source_path.is_dir():
        raise NotADirectoryError(f"source is not a folder: {source_path}")

    all_files = [path for path in source_path.rglob("*") if path.is_file()]
    text_files = [path for path in all_files if path.suffix.lower() in TEXT_SUFFIXES]
    assets = [classify_asset(path, source_path) for path in sorted(text_files)]
    conflicts = find_conflicts(assets, Path(target_graph).expanduser() if target_graph else None)

    return InventoryReport(
        source=str(source_path),
        target_graph=str(Path(target_graph).expanduser()) if target_graph else None,
        total_files_seen=len(all_files),
        text_files_scanned=len(text_files),
        assets=assets,
        conflicts=conflicts,
        category_counts=dict(Counter(asset.category for asset in assets)),
        destination_counts=dict(Counter(asset.destination for asset in assets)),
        recommended_next_steps=recommended_next_steps(assets, conflicts),
    )


def classify_asset(path: Path, source_root: Path) -> Asset:
    rel = str(path.relative_to(source_root))
    title = path.stem.replace("___", "/")
    text = read_text(path)
    haystack = f"{rel}\n{title}\n{text[:4000]}".lower()
    category, destination, confidence, reason = classify(haystack, title)
    return Asset(
        path=rel,
        title=title,
        category=category,
        destination=destination,
        confidence=confidence,
        reason=reason,
        excerpt=excerpt(text),
    )


def classify(haystack: str, title: str) -> tuple[str, str, str, str]:
    year = first_year(haystack)
    month = first_month(haystack)
    quarter = first_quarter(haystack)
    week = first_week(haystack)

    if contains_any(haystack, ["十年", "长期规划", "长期计划", "decade"]):
        return "十年/长期规划", decade_destination(year), "high", "命中十年或长期规划关键词"
    if contains_any(haystack, ["年度 okr", "年度计划", "年度目标", "yearly okr", "annual okr"]):
        return "年度 OKR", f"[[{year or 'YYYY'} OKRs]]", "high", "命中年度 OKR/年度计划关键词"
    if quarter:
        return "季度计划", f"[[{year or 'YYYY'}Q{quarter}]]", "medium", "命中季度结构"
    if month:
        return "月度计划", f"[[{year or 'YYYY'} {month}月]]", "medium", "命中月份结构"
    if week or contains_any(haystack, ["周复盘", "周报", "weekly review", "3 things", "3things"]):
        return "周计划/周复盘", f"[[{week or 'YYYY-Wxx'}]]", "medium", "命中周计划、周复盘或 3 Things"
    if contains_any(haystack, ["project/", "项目 okr", "项目页", "项目计划", "objective", "key result"]):
        return "项目资产", f"[[Project/{clean_title(title)}]]", "medium", "命中项目或 OKR 结构"
    if contains_any(haystack, ["大事件", "黑匣子", "里程碑", "转折点", "复盘事件"]):
        return "大事件", f"[[大事件/{clean_title(title)}]]", "medium", "命中大事件/里程碑/黑匣子关键词"
    if contains_any(haystack, ["复盘", "review", "bayesian", "判断更新"]):
        return "复盘材料", "[[YYYY-Wxx]] 或 [[YYYY M月]]", "low", "命中复盘关键词但周期不明确"
    if contains_any(haystack, ["template::", "模板", "template"]):
        return "模板", "[[OKR Templates]] 或归档", "medium", "命中模板关键词"
    if contains_any(haystack, ["资源", "资料", "课程", "文章", "知识库", "reference"]):
        return "资源资料", "资源索引", "low", "命中资源/资料关键词"
    if contains_any(haystack, ["journal", "daily", "日记", "行动记录", "今日"]):
        return "日记/行动流", f"[[{year or 'YYYY'} {month or 'M'}月]]", "low", "命中日记或行动流关键词"
    return "未分类", "人工确认", "low", "没有命中稳定 OKR 资产特征"


def contains_any(text: str, needles: list[str]) -> bool:
    return any(needle.lower() in text for needle in needles)


def first_year(text: str) -> str | None:
    match = re.search(r"\b(20\d{2})\b", text)
    return match.group(1) if match else None


def first_quarter(text: str) -> str | None:
    match = re.search(r"\bq([1-4])\b|第([一二三四1234])季度", text, re.IGNORECASE)
    if not match:
        return None
    value = match.group(1) or match.group(2)
    return {"一": "1", "二": "2", "三": "3", "四": "4"}.get(value, value)


def first_month(text: str) -> str | None:
    match = re.search(r"\b(1[0-2]|[1-9])月\b", text)
    return match.group(1) if match else None


def first_week(text: str) -> str | None:
    match = re.search(r"\b(20\d{2})[-_ ]?w(0?[1-9]|[1-4]\d|5[0-3])\b", text, re.IGNORECASE)
    if not match:
        return None
    return f"{match.group(1)}-W{int(match.group(2)):02d}"


def decade_destination(year: str | None) -> str:
    if not year:
        return "[[十年计划（YYYY-YYYY）]]"
    value = int(year)
    start = ((value - 1) // 10) * 10 + 1
    return f"[[十年计划（{start}-{start + 9}）]]"


def clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip() or "待确认"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def excerpt(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= MAX_EXCERPT_CHARS:
        return normalized
    return normalized[:MAX_EXCERPT_CHARS].rstrip() + "..."


def find_conflicts(assets: list[Asset], target_graph: Path | None) -> list[Conflict]:
    if not target_graph:
        return []
    pages = target_graph / "pages"
    if not pages.exists():
        return []

    conflicts: list[Conflict] = []
    for asset in assets:
        title = destination_title(asset.destination)
        if not title:
            continue
        for candidate in page_candidates(pages, title):
            if candidate.exists():
                conflicts.append(Conflict(asset.path, asset.destination, str(candidate)))
                break
    return conflicts


def destination_title(destination: str) -> str | None:
    match = re.fullmatch(r"\[\[(.+)\]\]", destination)
    return match.group(1) if match else None


def page_candidates(pages: Path, title: str) -> list[Path]:
    safe = title.replace("/", "___")
    return [pages / f"{title}.md", pages / f"{safe}.md", pages / f"{title}.markdown", pages / f"{safe}.markdown"]


def recommended_next_steps(assets: list[Asset], conflicts: list[Conflict]) -> list[str]:
    steps = ["先人工确认 low confidence 和 `人工确认` 目标的资产", "优先迁移年度 OKR、项目资产和复盘材料"]
    if conflicts:
        steps.insert(0, "先处理目标 Logseq graph 中的同名页面冲突")
    if any(asset.category == "资源资料" for asset in assets):
        steps.append("资源资料先进入资源索引,不要塞进年度页")
    steps.append("确认迁移地图后,再进入迁移 dry-run；本报告不写入文件")
    return steps


def render_markdown(report: InventoryReport) -> str:
    grouped: dict[str, list[Asset]] = defaultdict(list)
    for asset in report.assets:
        grouped[asset.category].append(asset)

    lines = [
        "# OKR 资产盘点报告",
        "",
        f"- 源文件夹: `{report.source}`",
        f"- 目标图谱: `{report.target_graph or '未提供'}`",
        f"- 文件总数: {report.total_files_seen}",
        f"- 已扫描文本文件: {report.text_files_scanned}",
        "",
        "## OKR 资产地图",
    ]

    for category in sorted(grouped):
        lines.append(f"### {category} ({len(grouped[category])})")
        for asset in grouped[category]:
            lines.append(f"- `{asset.path}` -> {asset.destination} [{asset.confidence}]")
            lines.append(f"  - 理由: {asset.reason}")

    lines.extend(["", "## 迁移建议"])
    for destination, count in sorted(report.destination_counts.items()):
        lines.append(f"- {destination}: {count} 项")

    lines.extend(["", "## 需要人工确认"])
    uncertain = [asset for asset in report.assets if asset.confidence == "low" or asset.destination == "人工确认"]
    if uncertain:
        for asset in uncertain:
            lines.append(f"- `{asset.path}`: {asset.category} -> {asset.destination}")
    else:
        lines.append("- 暂无")

    lines.extend(["", "## 风险与冲突"])
    if report.conflicts:
        for conflict in report.conflicts:
            lines.append(f"- `{conflict.asset_path}` 目标 {conflict.destination} 已存在: `{conflict.existing_path}`")
    else:
        lines.append("- 未发现目标图谱同名页面冲突")

    lines.extend(["", "## 下一步"])
    for step in report.recommended_next_steps:
        lines.append(f"- {step}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only OKR asset inventory.")
    parser.add_argument("--source", required=True, help="Old personal OKR folder")
    parser.add_argument("--target-graph", help="Optional new Logseq graph for conflict checks")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    args = parser.parse_args()

    report = build_inventory(args.source, args.target_graph)
    if args.json:
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
