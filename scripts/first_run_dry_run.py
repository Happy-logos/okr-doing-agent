#!/usr/bin/env python3
"""Generate the first-run Logseq install dry-run preview.

This script is intentionally read-only. It models what the plugin should show
before the user confirms installation.
"""

from __future__ import annotations

import argparse
import calendar
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


FIRST_RUN_PROMPT = "你想把 OKR 系统安装到哪个 Logseq 图谱里？"

SELF_INTRO = """我是 OKR Doing Agent。

我会先帮你在 Logseq 里安装一套十年尺度的轻量 OKR 系统：
Dashboard、十年计划、年度 OKR、Q1-Q4、1-12 月、当前周入口，以及十年计划/年度 OKR/项目/大事件/daily routine/周复盘可调用模板。

我不会直接覆盖你的内容。写入前会先给你看预览。
安装完成后，我们再一起把你的第一个项目接进去。"""

SYSTEM_TEMPLATE_DIR = "templates/logseq/system"
LOGSEQ_TEMPLATE_DIR = "templates/logseq/templates"
TEMPLATE_LIBRARY_TITLE = "OKR Templates"
MONTH_LABELS = [f"{month}月" for month in range(1, 13)]


@dataclass(frozen=True)
class PlannedPage:
    title: str
    purpose: str
    parent: str | None = None
    category: str = "system_page"
    source_template: str | None = None


@dataclass(frozen=True)
class PlannedTemplate:
    title: str
    purpose: str
    source_template: str
    invoked_for: str
    default_parent: str | None = None


@dataclass(frozen=True)
class PageConflict:
    title: str
    existing_path: str


@dataclass(frozen=True)
class AppliedFile:
    title: str
    kind: str
    path: str


@dataclass(frozen=True)
class InstallResult:
    mode: str
    writes_files: bool
    graph_path: str
    files: list[AppliedFile]
    message: str
    after_install_prompt: str


@dataclass(frozen=True)
class FirstRunPreview:
    mode: str
    writes_files: bool
    can_apply: bool
    target_tool: str
    graph_path: str
    year: int
    quarter: int
    month: int
    week: int
    week_title: str
    decade_title: str
    intro: str
    first_prompt: str
    pages: list[PlannedPage]
    templates: list[PlannedTemplate]
    on_demand_pages: list[PlannedPage]
    conflicts: list[PageConflict]
    relationships: list[str]
    safety_checks: list[str]
    after_confirm: list[str]
    after_install_prompt: str


def build_preview(
    graph_path: str,
    *,
    year: int,
    quarter: int,
    month: int,
    week: int,
    decade_title: str | None = None,
) -> FirstRunPreview:
    graph = Path(graph_path).expanduser()
    if not graph_path.strip():
        raise ValueError("graph_path is required")
    if quarter < 1 or quarter > 4:
        raise ValueError("quarter must be 1..4")
    if month < 1 or month > 12:
        raise ValueError("month must be 1..12")
    if week < 1 or week > 53:
        raise ValueError("week must be 1..53")

    resolved_decade_title = (
        decade_title.strip()
        if decade_title and decade_title.strip()
        else detect_decade_title(graph, year) or default_decade_title(year)
    )
    week_title = f"{year}-W{week:02d}"

    pages = build_system_pages(
        year=year,
        month=month,
        week_title=week_title,
        decade_title=resolved_decade_title,
    )
    templates = build_logseq_templates(year=year, month=month, week_title=week_title)
    on_demand_pages = build_on_demand_pages(year=year)
    relationships = build_relationships(
        year=year,
        month=month,
        week_title=week_title,
        decade_title=resolved_decade_title,
    )
    conflicts = find_page_conflicts(graph, pages)

    return FirstRunPreview(
        mode="dry-run",
        writes_files=False,
        can_apply=not conflicts,
        target_tool="Logseq",
        graph_path=str(graph),
        year=year,
        quarter=quarter,
        month=month,
        week=week,
        week_title=week_title,
        decade_title=resolved_decade_title,
        intro=SELF_INTRO,
        first_prompt=FIRST_RUN_PROMPT,
        pages=pages,
        templates=templates,
        on_demand_pages=on_demand_pages,
        conflicts=conflicts,
        relationships=relationships,
        safety_checks=[
            "dry-run 阶段不写入任何文件",
            "确认前不覆盖已有页面",
            "如发现同名系统页面冲突，必须先处理冲突再写入",
            "首次安装不询问目标、卡点或项目内容",
            "十年计划、年度 OKR、项目 OKR、大事件、daily routine、周复盘会写入 OKR Templates 模板库",
            "项目 OKR、大事件、daily routine、周复盘是 Logseq 可调用模板，不是普通页面",
            "模板来自内置模板包，不由 Agent 临场编写",
            "安装完成后再进入第一个项目接入流程",
        ],
        after_confirm=[
            "检查 pages/ 目录是否存在",
            "再次检查同名系统页面冲突",
            "写入系统页面",
            "安装 Logseq 可调用模板",
            "输出安装完成说明",
        ],
        after_install_prompt="系统已经装好了。现在要不要把一件想做的事接进来？",
    )


def build_system_pages(*, year: int, month: int, week_title: str, decade_title: str) -> list[PlannedPage]:
    pages: list[PlannedPage] = [
        PlannedPage(
            "OKR Dashboard",
            "总入口：当前十年、年度、季度/月度、本周入口",
            source_template=f"{SYSTEM_TEMPLATE_DIR}/dashboard.md",
        ),
        PlannedPage(
            TEMPLATE_LIBRARY_TITLE,
            "模板库：承载 Logseq template:: 块，不是普通项目页",
            "OKR Dashboard",
            category="template_library",
            source_template=f"{SYSTEM_TEMPLATE_DIR}/template-library.md",
        ),
        PlannedPage(
            decade_title,
            "十年视角：长期愿景、年度年鉴、跨年复盘",
            "OKR Dashboard",
            source_template=f"{SYSTEM_TEMPLATE_DIR}/decade-plan.md",
        ),
        PlannedPage(
            f"{year} OKRs",
            "年度判断：方向、项目索引、大事件和 Bayesian Update",
            decade_title,
            source_template=f"{SYSTEM_TEMPLATE_DIR}/annual-okr.md",
        ),
    ]

    pages.extend(
        PlannedPage(
            f"{year}Q{number}",
            "季度索引：三个月、周 3 Things、阶段检查",
            f"{year} OKRs",
            source_template=f"{SYSTEM_TEMPLATE_DIR}/quarter-index.md",
        )
        for number in range(1, 5)
    )

    pages.extend(
        PlannedPage(
            f"{year} {label}",
            "月度执行：项目节奏、大事件、下月第一步",
            f"{year}Q{month_to_quarter(number)}",
            source_template=f"{SYSTEM_TEMPLATE_DIR}/month-page.md",
        )
        for number, label in enumerate(MONTH_LABELS, start=1)
    )

    pages.append(
        PlannedPage(
            week_title,
            "当前周行动入口：本周 3 Things、证据、周复盘",
            f"{year} {month}月",
            category="starter_page",
            source_template=f"{SYSTEM_TEMPLATE_DIR}/week-3things.md",
        )
    )
    return pages


def build_logseq_templates(*, year: int, month: int, week_title: str) -> list[PlannedTemplate]:
    return [
        PlannedTemplate(
            "十年计划",
            "十年尺度模板；当前十年首次安装会创建系统页，后续新十年或修补结构时调用",
            f"{LOGSEQ_TEMPLATE_DIR}/decade-plan.md",
            "十年计划（YYYY-YYYY）.md",
            "OKR Dashboard",
        ),
        PlannedTemplate(
            "年度 OKR",
            "年度判断模板；当前年度首次安装会创建系统页，后续新年度或修补结构时调用",
            f"{LOGSEQ_TEMPLATE_DIR}/annual-okr.md",
            "YYYY OKRs.md",
            "十年计划",
        ),
        PlannedTemplate(
            "项目 OKR",
            "真实项目页模板；用户接入一个项目时调用，不在首次安装时生成假项目",
            f"{LOGSEQ_TEMPLATE_DIR}/project-okr.md",
            "Project/<项目名>.md",
            f"{year} OKRs",
        ),
        PlannedTemplate(
            "大事件",
            "黑匣子数据模板；记录重大变化、失败、转折点和系统更新",
            f"{LOGSEQ_TEMPLATE_DIR}/big-event.md",
            "大事件/<事件名>.md",
            f"{year} OKRs",
        ),
        PlannedTemplate(
            "daily routine",
            "日记行动流模板；用于当天 journal，不是每日长复盘",
            f"{LOGSEQ_TEMPLATE_DIR}/daily-routine.md",
            "Journals/<today>.md",
            f"{year} {month}月",
        ),
        PlannedTemplate(
            "周复盘",
            "把本周行动转成下一周判断的 Bayesian Update 模板",
            f"{LOGSEQ_TEMPLATE_DIR}/week-review.md",
            f"{week_title}.md",
            week_title,
        ),
    ]


def build_on_demand_pages(*, year: int) -> list[PlannedPage]:
    return [
        PlannedPage(
            "后续十年计划（YYYY-YYYY）",
            "进入下一个十年周期时按需生成；首次只创建当前十年系统页",
            "OKR Dashboard",
            category="on_demand",
            source_template=f"{LOGSEQ_TEMPLATE_DIR}/decade-plan.md",
        ),
        PlannedPage(
            "后续 YYYY OKRs",
            "后续年度按需生成；首次只创建当前年度系统页",
            "十年计划",
            category="on_demand",
            source_template=f"{LOGSEQ_TEMPLATE_DIR}/annual-okr.md",
        ),
        PlannedPage(
            "Project/<项目名>",
            "真实项目接入后生成；项目页才是执行战场",
            f"{year} OKRs",
            category="on_demand",
            source_template=f"{LOGSEQ_TEMPLATE_DIR}/project-okr.md",
        ),
        PlannedPage(
            "大事件/<事件名>",
            "真实大事件发生后生成；失败和意外进入黑匣子数据",
            f"{year} OKRs",
            category="on_demand",
            source_template=f"{LOGSEQ_TEMPLATE_DIR}/big-event.md",
        ),
        PlannedPage(
            "后续 YYYY-Wxx",
            "后续周页按周生成；首次只创建当前周入口，避免一次生成 52 个空页面",
            "YYYY M月",
            category="on_demand",
            source_template=f"{SYSTEM_TEMPLATE_DIR}/week-3things.md",
        ),
    ]


def default_decade_title(year: int) -> str:
    start = ((year - 1) // 10) * 10 + 1
    end = start + 9
    return f"十年计划（{start}-{end}）"


def month_to_quarter(month: int) -> int:
    return (month - 1) // 3 + 1


def detect_decade_title(graph: Path, year: int) -> str | None:
    pages_dir = graph / "pages"
    if not pages_dir.exists():
        return None

    candidates: list[tuple[int, str]] = []
    paths = sorted(pages_dir.glob("*.md")) + sorted(pages_dir.glob("*.markdown"))
    for path in paths:
        title = path.stem.replace("___", "/")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = ""

        haystack = f"{title}\n{text}"
        if "十年" not in haystack and "decade" not in haystack.lower():
            continue
        if not covers_year(haystack, year):
            continue

        score = 0
        if "class:: 十年计划" in text:
            score += 3
        if "十年" in title:
            score += 2
        if "OKR" in text:
            score += 1
        candidates.append((score, title))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][1]


def covers_year(text: str, year: int) -> bool:
    for match in re.finditer(r"(?P<start>20\d{2})\s*[-—–]\s*(?P<end>20\d{2})", text):
        start = int(match.group("start"))
        end = int(match.group("end"))
        if start <= year <= end:
            return True
    return False


def build_relationships(*, year: int, month: int, week_title: str, decade_title: str) -> list[str]:
    quarter_relationships = [f"[[{year} OKRs]] -> [[{year}Q{number}]]" for number in range(1, 5)]
    month_relationships = [
        f"[[{year}Q{month_to_quarter(number)}]] -> [[{year} {number}月]]"
        for number in range(1, 13)
    ]
    return [
        f"OKR Dashboard -> [[{decade_title}]]",
        f"OKR Dashboard -> [[{TEMPLATE_LIBRARY_TITLE}]]",
        f"[[{decade_title}]] -> [[{year} OKRs]]",
        *quarter_relationships,
        *month_relationships,
        f"[[{year} {month}月]] -> [[{week_title}]]",
        f"十年计划模板 -> related:: [[OKR Dashboard]]，用于后续十年或修补当前十年结构",
        f"年度 OKR 模板 -> parent:: [[{decade_title}]]，用于后续年度或修补年度结构",
        f"项目 OKR 模板 -> parent:: [[{year} OKRs]]，按真实项目调用",
        f"大事件模板 -> related:: [[{year} OKRs]]，保留十年定位和年度定位",
        f"daily routine 模板 -> parent:: [[{year} {month}月]]，可选关联项目",
        f"周复盘模板 -> [[{week_title}]]，把结果更新为下周判断",
    ]


def logseq_page_candidates(graph: Path, title: str) -> list[Path]:
    pages_dir = graph / "pages"
    safe_title = title.replace("/", "___")
    return [
        pages_dir / f"{title}.md",
        pages_dir / f"{safe_title}.md",
        pages_dir / f"{title}.markdown",
        pages_dir / f"{safe_title}.markdown",
    ]


def logseq_page_path(graph: Path, title: str) -> Path:
    return graph / "pages" / f"{title.replace('/', '___')}.md"


def find_page_conflicts(graph: Path, pages: list[PlannedPage]) -> list[PageConflict]:
    conflicts: list[PageConflict] = []
    seen: set[tuple[str, str]] = set()
    for page in pages:
        for candidate in logseq_page_candidates(graph, page.title):
            if candidate.exists():
                key = (page.title, str(candidate))
                if key not in seen:
                    conflicts.append(PageConflict(page.title, str(candidate)))
                    seen.add(key)
    return conflicts


def apply_install(preview: FirstRunPreview, *, agent_root: Path | None = None) -> InstallResult:
    if preview.conflicts:
        conflict_titles = ", ".join(conflict.title for conflict in preview.conflicts)
        raise RuntimeError(f"cannot apply install with existing page conflicts: {conflict_titles}")

    root = agent_root or Path(__file__).resolve().parents[1]
    graph = Path(preview.graph_path)
    pages_dir = graph / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    late_conflicts = find_page_conflicts(graph, preview.pages)
    if late_conflicts:
        conflict_titles = ", ".join(conflict.title for conflict in late_conflicts)
        raise RuntimeError(f"cannot apply install with existing page conflicts: {conflict_titles}")

    written: list[AppliedFile] = []
    for page in preview.pages:
        target = logseq_page_path(graph, page.title)
        content = render_planned_page(page, preview, root)
        target.write_text(content.rstrip() + "\n", encoding="utf-8")
        written.append(AppliedFile(page.title, page.category, str(target)))

    return InstallResult(
        mode="apply",
        writes_files=True,
        graph_path=str(graph),
        files=written,
        message="OKR Doing Agent 已完成 Logseq 系统页面和模板库安装。",
        after_install_prompt=preview.after_install_prompt,
    )


def render_planned_page(page: PlannedPage, preview: FirstRunPreview, agent_root: Path) -> str:
    if not page.source_template:
        raise ValueError(f"missing source template for {page.title}")

    raw = read_template(agent_root, page.source_template)
    context = build_render_context(page, preview, agent_root)
    return render_text(raw, context)


def read_template(agent_root: Path, source_template: str) -> str:
    path = agent_root / source_template
    if not path.exists():
        raise FileNotFoundError(f"missing template: {path}")
    return path.read_text(encoding="utf-8")


def build_render_context(page: PlannedPage, preview: FirstRunPreview, agent_root: Path) -> dict[str, str]:
    decade_start, decade_end = decade_range_for_title(preview.decade_title, preview.year)
    page_quarter = quarter_from_title(page.title) or preview.quarter
    page_month = month_from_title(page.title) or preview.month
    context = {
        "year": str(preview.year),
        "quarter": str(page_quarter),
        "month": str(page_month),
        "week": str(preview.week),
        "week_title": preview.week_title,
        "decade_title": preview.decade_title,
        "decade_start": str(decade_start),
        "decade_end": str(decade_end),
        "decade_year_links": continuation_bullets(
            [f"[[{year} OKRs]]" for year in range(decade_start, decade_end + 1)]
        ),
        "quarter_month_links": continuation_bullets(
            [f"[[{preview.year} {month}月]]" for month in months_for_quarter(page_quarter)]
        ),
        "quarter_week_links": continuation_bullets(week_links_for_quarter(preview.year, page_quarter)),
        "month_week_links": continuation_bullets(week_links_for_month(preview.year, page_month)),
    }
    if page.title == TEMPLATE_LIBRARY_TITLE:
        context["template_blocks"] = render_template_blocks(preview, agent_root)
    return context


def render_text(raw: str, context: dict[str, str]) -> str:
    rendered = raw
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    unresolved = sorted(set(re.findall(r"{{[^{}]+}}", rendered)))
    if unresolved:
        raise ValueError(f"unresolved template placeholders: {', '.join(unresolved)}")
    return rendered


def render_template_blocks(preview: FirstRunPreview, agent_root: Path) -> str:
    blocks = []
    context = build_template_context(preview)
    for template in preview.templates:
        raw = render_text(read_template(agent_root, template.source_template), context)
        blocks.append(template_block_for_library(template.title, raw))
    return "\n".join(blocks)


def build_template_context(preview: FirstRunPreview) -> dict[str, str]:
    decade_start, decade_end = decade_range_for_title(preview.decade_title, preview.year)
    return {
        "year": str(preview.year),
        "quarter": str(preview.quarter),
        "month": str(preview.month),
        "week": str(preview.week),
        "week_title": preview.week_title,
        "decade_title": preview.decade_title,
        "decade_start": str(decade_start),
        "decade_end": str(decade_end),
        "decade_year_links": continuation_bullets(
            [f"[[{year} OKRs]]" for year in range(decade_start, decade_end + 1)]
        ),
    }


def template_block_for_library(title: str, raw: str) -> str:
    lines = raw.strip().splitlines()
    property_lines: list[str] = []
    body_start = 0
    for index, line in enumerate(lines):
        if not line.strip():
            body_start = index + 1
            break
        property_lines.append(line.strip())
    else:
        body_start = len(lines)

    block_lines = [f"- {title}"]
    block_lines.extend(f"\t{line}" for line in property_lines)
    body_lines = lines[body_start:]
    if body_lines:
        block_lines.extend(indent_template_body_line(line) for line in body_lines)
    return "\n".join(block_lines)


def indent_template_body_line(line: str) -> str:
    if not line:
        return "\t"
    if line.startswith(("\t", " ")):
        return line
    return f"\t{line}"


def decade_range_for_title(title: str, year: int) -> tuple[int, int]:
    match = re.search(r"(?P<start>20\d{2})\s*[-—–]\s*(?P<end>20\d{2})", title)
    if match:
        return int(match.group("start")), int(match.group("end"))
    start = ((year - 1) // 10) * 10 + 1
    return start, start + 9


def quarter_from_title(title: str) -> int | None:
    match = re.search(r"Q([1-4])$", title)
    if not match:
        return None
    return int(match.group(1))


def month_from_title(title: str) -> int | None:
    match = re.search(r"\s(\d{1,2})月$", title)
    if not match:
        return None
    month = int(match.group(1))
    if 1 <= month <= 12:
        return month
    return None


def months_for_quarter(quarter: int) -> list[int]:
    first_month = (quarter - 1) * 3 + 1
    return [first_month, first_month + 1, first_month + 2]


def week_links_for_quarter(year: int, quarter: int) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for month in months_for_quarter(quarter):
        for link in week_links_for_month(year, month):
            if link not in seen:
                links.append(link)
                seen.add(link)
    return links


def week_links_for_month(year: int, month: int) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    days = calendar.monthrange(year, month)[1]
    for day in range(1, days + 1):
        iso_year, iso_week, _ = date(year, month, day).isocalendar()
        link = f"[[{iso_year}-W{iso_week:02d}]]"
        if link not in seen:
            links.append(link)
            seen.add(link)
    return links


def continuation_bullets(items: list[str]) -> str:
    if not items:
        return ""
    return items[0] + "".join(f"\n\t- {item}" for item in items[1:])


def render_markdown(preview: FirstRunPreview) -> str:
    lines = [
        preview.intro,
        "",
        f"模式：{preview.mode}",
        f"目标工具：{preview.target_tool}",
        f"Logseq 图谱：{preview.graph_path}",
        f"十年计划：{preview.decade_title}",
        f"是否写入文件：{'是' if preview.writes_files else '否'}",
        f"是否可直接写入：{'是' if preview.can_apply else '否'}",
        "",
        "将创建/检测这些系统页面：",
    ]
    for page in preview.pages:
        parent = f" parent:: [[{page.parent}]]" if page.parent else ""
        source = f" 来源模板：{page.source_template}" if page.source_template else ""
        label = {
            "starter_page": "当前周入口",
            "template_library": "模板库",
        }.get(page.category, "系统页面")
        lines.append(f"- [{label}] {page.title}：{page.purpose}{parent}{source}")

    lines.extend(["", "将安装这些 Logseq 可调用模板："])
    for template in preview.templates:
        parent = f" 默认 parent:: [[{template.default_parent}]]" if template.default_parent else ""
        lines.append(
            f"- {template.title}：{template.purpose} 调用场景：{template.invoked_for}{parent} 来源模板：{template.source_template}"
        )

    lines.extend(["", "不会默认创建，后续按需生成："])
    for page in preview.on_demand_pages:
        parent = f" parent:: [[{page.parent}]]" if page.parent else ""
        source = f" 来源模板：{page.source_template}" if page.source_template else ""
        lines.append(f"- {page.title}：{page.purpose}{parent}{source}")

    lines.extend(["", "将建立这些关系："])
    for relationship in preview.relationships:
        lines.append(f"- {relationship}")

    lines.extend(["", "安全检查："])
    for check in preview.safety_checks:
        lines.append(f"- {check}")

    if preview.conflicts:
        lines.extend(["", "发现同名页面冲突："])
        for conflict in preview.conflicts:
            lines.append(f"- {conflict.title} 已存在：{conflict.existing_path}")
        lines.extend(["", "请先处理以上系统页面冲突，再继续写入。"])
    else:
        lines.extend(["", "确认后才会执行："])
        for step in preview.after_confirm:
            lines.append(f"- {step}")

        lines.extend(["", "安装完成后才会问：", preview.after_install_prompt])
    return "\n".join(lines)


def render_install_result(result: InstallResult) -> str:
    lines = [
        result.message,
        "",
        f"模式：{result.mode}",
        f"Logseq 图谱：{result.graph_path}",
        f"是否写入文件：{'是' if result.writes_files else '否'}",
        "",
        "已写入：",
    ]
    for file in result.files:
        lines.append(f"- [{file.kind}] {file.title}：{file.path}")
    lines.extend(["", result.after_install_prompt])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate first-run install dry-run preview.")
    parser.add_argument("--graph", required=True, help="Logseq graph path")
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--quarter", type=int, default=2)
    parser.add_argument("--month", type=int, default=6)
    parser.add_argument("--week", type=int, default=26)
    parser.add_argument("--decade-title", help="Override detected/default decade page title")
    parser.add_argument("--apply", action="store_true", help="Write pages and templates after preview confirmation")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of Markdown")
    args = parser.parse_args()

    preview = build_preview(
        args.graph,
        year=args.year,
        quarter=args.quarter,
        month=args.month,
        week=args.week,
        decade_title=args.decade_title,
    )
    if args.apply:
        try:
            result = apply_install(preview)
        except RuntimeError as error:
            raise SystemExit(str(error)) from error
        if args.json:
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        else:
            print(render_install_result(result))
    elif args.json:
        print(json.dumps(asdict(preview), ensure_ascii=False, indent=2))
    else:
        print(render_markdown(preview))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
