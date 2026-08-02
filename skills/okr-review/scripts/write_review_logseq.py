#!/usr/bin/env python3
"""Preview and explicitly apply one confirmed OKR review to a Logseq period page."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "okr-review/v1"
PREVIEW_SCHEMA_VERSION = "okr-review-logseq-preview/v1"
PERIOD_PATTERNS = (
    ("week", re.compile(r"^(?P<year>\d{4})-W(?P<week>\d{2})$")),
    ("month", re.compile(r"^(?P<year>\d{4})-(?P<month>0[1-9]|1[0-2])$")),
    ("quarter", re.compile(r"^(?P<year>\d{4})-Q(?P<quarter>[1-4])$")),
    ("year", re.compile(r"^(?P<year>\d{4})$")),
)
HEADING_BY_TYPE = {
    "week": "周复盘",
    "month": "月度复盘",
    "quarter": "季度复盘",
    "year": "年度复盘",
}
SECTION_FIELDS = (
    ("facts", "这个周期实际发生了什么"),
    ("coachInsights", "Coach 洞察"),
    ("lookback", "我的回看"),
    ("judgments", "我的判断"),
    ("nextActions", "下一步行动"),
    ("modelUpdates", "模型更新"),
    ("evidenceRefs", "证据索引"),
)
LEGACY_PLACEHOLDERS = {
    "做到了什么",
    "没做到什么",
    "新证据是什么",
    "判断如何更新",
    "下月第一步",
}


class WritebackError(ValueError):
    """A safe, user-actionable writeback failure."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def parse_period(label: str) -> dict[str, Any]:
    for period_type, pattern in PERIOD_PATTERNS:
        match = pattern.fullmatch(label)
        if match:
            values: dict[str, Any] = {
                key: int(value) for key, value in match.groupdict().items()
            }
            values.update({"type": period_type, "label": label})
            return values
    raise WritebackError(
        "Unsupported period. Use YYYY-Www, YYYY-MM, YYYY-Qn, or YYYY."
    )


def review_key(period: dict[str, Any]) -> str:
    if period["type"] == "year":
        return f"review:year:{period['year']}"
    if period["type"] == "week":
        suffix = str(period["week"])
    elif period["type"] == "month":
        suffix = str(period["month"])
    else:
        suffix = str(period["quarter"])
    return f"review:{period['type']}:{period['year']}:{suffix}"


def expected_page_titles(period: dict[str, Any]) -> list[str]:
    if period["type"] == "week":
        return [period["label"]]
    if period["type"] == "month":
        return [f"{period['year']} {period['month']}月"]
    if period["type"] == "quarter":
        return [f"{period['year']}Q{period['quarter']}"]
    return [f"{period['year']} OKRs"]


def acceptable_period_properties(period: dict[str, Any]) -> set[str]:
    if period["type"] == "week":
        return {period["label"]}
    if period["type"] == "month":
        year = period["year"]
        month = period["month"]
        return {f"{year}-M{month}", f"{year}-M{month:02d}", f"{year}-{month:02d}"}
    if period["type"] == "quarter":
        year = period["year"]
        quarter = period["quarter"]
        return {f"{year}-Q{quarter}", f"{year}Q{quarter}"}
    return {str(period["year"])}


def read_utf8(path: Path) -> tuple[bytes, str, str]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise WritebackError(f"Target is not valid UTF-8: {path}") from error
    newline = "\r\n" if b"\r\n" in raw else "\n"
    return raw, text.replace("\r\n", "\n").replace("\r", "\n"), newline


def extract_period_property(text: str) -> set[str]:
    values = set()
    pattern = re.compile(r"^(?:-\s*)?period::\s*(.*?)\s*$", re.MULTILINE)
    for match in pattern.finditer(text):
        value = match.group(1).strip()
        if value:
            values.add(value)
    return values


def find_period_page(graph_root: Path, period: dict[str, Any]) -> Path:
    graph = graph_root.resolve()
    pages = graph / "pages"
    if not pages.is_dir():
        raise WritebackError(f"Logseq pages directory not found: {pages}")
    if pages.is_symlink():
        raise WritebackError("Refusing a symlinked Logseq pages directory.")

    expected_titles = set(expected_page_titles(period))
    acceptable_properties = acceptable_period_properties(period)
    candidates: set[Path] = set()

    for title in expected_titles:
        safe_title = title.replace("/", "___")
        for suffix in (".md", ".markdown"):
            direct = pages / f"{safe_title}{suffix}"
            if direct.is_file():
                candidates.add(direct)

    for path in pages.iterdir():
        if path.suffix.lower() not in {".md", ".markdown"} or not path.is_file():
            continue
        if path.is_symlink():
            continue
        try:
            _, text, _ = read_utf8(path)
        except WritebackError:
            continue
        if extract_period_property(text) & acceptable_properties:
            candidates.add(path)

    if not candidates:
        expected = " / ".join(expected_titles)
        raise WritebackError(
            f"No canonical period page found for {period['label']} "
            f"(expected title {expected} or a matching period:: property)."
        )
    if len(candidates) > 1:
        names = ", ".join(sorted(str(path) for path in candidates))
        raise WritebackError(
            f"Multiple period pages match {period['label']}; resolve the conflict first: "
            f"{names}"
        )

    target = next(iter(candidates))
    if target.is_symlink():
        raise WritebackError("Refusing to write through a symlinked period page.")
    resolved_target = target.resolve()
    if not is_within(resolved_target, pages.resolve()):
        raise WritebackError("Resolved period page is outside the Logseq pages directory.")
    return target


def load_review(path: Path, period: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WritebackError(f"Cannot read confirmed review JSON: {path}") from error

    if payload.get("schemaVersion") != SCHEMA_VERSION:
        raise WritebackError(f"Review schemaVersion must be {SCHEMA_VERSION}.")
    if payload.get("status") != "confirmed":
        raise WritebackError("Review status must be confirmed before writeback.")

    payload_period = payload.get("period")
    if not isinstance(payload_period, dict):
        raise WritebackError("Review period must be an object.")
    if (
        payload_period.get("type") != period["type"]
        or payload_period.get("label") != period["label"]
    ):
        raise WritebackError("Review period does not match --period.")

    confirmed_at = payload.get("confirmedAt")
    if not isinstance(confirmed_at, str) or not confirmed_at.strip():
        raise WritebackError(
            "A stable confirmedAt timestamp is required so preview and apply are identical."
        )

    one_page = payload.get("onePage")
    if not isinstance(one_page, dict):
        raise WritebackError("Review onePage must be an object.")
    for field, _ in SECTION_FIELDS:
        value = one_page.get(field)
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise WritebackError(f"onePage.{field} must be an array of strings.")
    chapter_title = one_page.get("chapterTitle", "")
    if not isinstance(chapter_title, str):
        raise WritebackError("onePage.chapterTitle must be a string when present.")
    return payload


def one_line(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def property_value(block: str, name: str) -> str | None:
    pattern = re.compile(
        rf"^\s*{re.escape(name)}::\s*(.*?)\s*$",
        re.MULTILINE,
    )
    match = pattern.search(block)
    return match.group(1).strip() if match else None


def render_review_block(
    payload: dict[str, Any],
    period: dict[str, Any],
    existing_created_at: str | None,
) -> str:
    one_page = payload["onePage"]
    confirmed_at = one_line(payload["confirmedAt"])
    created_at = existing_created_at or one_line(
        payload.get("createdAt") or confirmed_at
    )
    updated_at = one_line(payload.get("updatedAt") or confirmed_at)
    heading = HEADING_BY_TYPE[period["type"]]

    lines = [
        f"- ## {heading}",
        f"\treview-key:: {review_key(period)}",
        f"\treview-schema:: {SCHEMA_VERSION}",
        "\treview-status:: confirmed",
        "\tartifact:: 复盘一页纸",
        f"\treview-created-at:: {created_at}",
        f"\treview-updated-at:: {updated_at}",
    ]

    chapter_title = one_line(one_page.get("chapterTitle", ""))
    if chapter_title:
        lines.extend(
            [
                "\t- ### 章节标题",
                f"\t\t- {chapter_title}",
            ]
        )

    for field, title in SECTION_FIELDS:
        lines.append(f"\t- ### {title}")
        values = [one_line(value) for value in one_page[field] if one_line(value)]
        if not values:
            lines.append("\t\t- （无已确认内容）")
            continue
        for value in values:
            if field == "nextActions" and re.match(
                r"^(TODO|DOING|NOW|LATER|WAITING|DONE|CANCELED|CANCELLED)\b",
                value,
                flags=re.IGNORECASE,
            ):
                value = f"行动：{value}"
            lines.append(f"\t\t- {value}")

    return "\n".join(lines) + "\n"


def indentation_width(value: str) -> int:
    return sum(4 if character == "\t" else 1 for character in value)


def find_review_blocks(text: str, heading: str) -> list[tuple[int, int]]:
    lines = text.splitlines(keepends=True)
    bullet_pattern = re.compile(
        rf"^(?P<indent>[ \t]*)-\s+##\s+{re.escape(heading)}\s*$"
    )
    markdown_pattern = re.compile(
        rf"^(?P<indent>[ \t]*)##\s+{re.escape(heading)}\s*$"
    )
    blocks: list[tuple[int, int]] = []

    for index, raw_line in enumerate(lines):
        line = raw_line.rstrip("\n")
        bullet_match = bullet_pattern.fullmatch(line)
        markdown_match = markdown_pattern.fullmatch(line)
        if not bullet_match and not markdown_match:
            continue

        base_width = indentation_width(
            (bullet_match or markdown_match).group("indent")
        )
        end = len(lines)
        for cursor in range(index + 1, len(lines)):
            candidate = lines[cursor].rstrip("\n")
            if not candidate.strip():
                continue
            if bullet_match:
                peer = re.match(r"^(?P<indent>[ \t]*)-\s+", candidate)
                top_heading = re.match(r"^(?P<indent>[ \t]*)#{1,2}\s+", candidate)
                match = peer or top_heading
            else:
                match = re.match(
                    r"^(?P<indent>[ \t]*)#{1,2}\s+",
                    candidate,
                )
            if match and indentation_width(match.group("indent")) <= base_width:
                end = cursor
                break
        blocks.append((index, end))
    return blocks


def is_legacy_placeholder(block: str) -> bool:
    lines = block.splitlines()[1:]
    labels: set[str] = set()
    for raw_line in lines:
        value = raw_line.strip()
        if not value:
            continue
        if not value.startswith("- "):
            return False
        label = value[2:].strip()
        label = re.sub(r"[：:]\s*$", "", label).strip()
        if label not in LEGACY_PLACEHOLDERS:
            return False
        labels.add(label)
    return labels == LEGACY_PLACEHOLDERS


def find_insert_index(text: str) -> int:
    lines = text.splitlines(keepends=True)
    migration_pattern = re.compile(r"^[ \t]*-\s+##\s+迁移记录\s*$")
    for index, raw_line in enumerate(lines):
        if migration_pattern.fullmatch(raw_line.rstrip("\n")):
            return sum(len(line) for line in lines[:index])
    return len(text)


def replace_or_append_review(
    source: str,
    payload: dict[str, Any],
    period: dict[str, Any],
) -> tuple[str, str, list[str], bool]:
    heading = HEADING_BY_TYPE[period["type"]]
    blocks = find_review_blocks(source, heading)
    key = review_key(period)
    warnings: list[str] = []

    if len(blocks) > 1:
        return (
            source,
            "conflict-multiple-review-blocks",
            [f"Found {len(blocks)} {heading} blocks; no write is safe."],
            False,
        )

    if blocks:
        lines = source.splitlines(keepends=True)
        start, end = blocks[0]
        existing = "".join(lines[start:end])
        existing_key = property_value(existing, "review-key")
        existing_created_at = property_value(existing, "review-created-at")
        if existing_key and existing_key != key:
            return (
                source,
                "conflict-review-key",
                [f"Existing review-key is {existing_key}, expected {key}."],
                False,
            )
        if existing_key == key:
            operation = "update-managed-review"
        elif is_legacy_placeholder(existing):
            operation = "replace-empty-placeholder"
            existing_created_at = None
        else:
            return (
                source,
                "conflict-user-content",
                [
                    f"The existing {heading} block has user content and no matching "
                    "review-key; it will not be overwritten."
                ],
                False,
            )
        rendered = render_review_block(payload, period, existing_created_at)
        proposed = "".join(lines[:start]) + rendered + "".join(lines[end:])
        return proposed, operation, warnings, True

    rendered = render_review_block(payload, period, None)
    insert_at = find_insert_index(source)
    prefix = source[:insert_at]
    suffix = source[insert_at:]
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    if prefix and not prefix.endswith("\n\n"):
        prefix += "\n"
    proposed = prefix + rendered
    if suffix:
        if not proposed.endswith("\n\n"):
            proposed += "\n"
        proposed += suffix
    warnings.append(f"No {heading} block existed; a new managed block will be inserted.")
    return proposed, "insert-managed-review", warnings, True


def public_plan(plan: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in plan.items() if not key.startswith("_")}


def build_plan(
    graph_root: Path,
    period_label: str,
    review_json: Path,
) -> dict[str, Any]:
    period = parse_period(period_label)
    target = find_period_page(graph_root, period)
    payload = load_review(review_json, period)
    source_raw, source, newline = read_utf8(target)
    proposed, operation, warnings, can_apply = replace_or_append_review(
        source,
        payload,
        period,
    )
    proposed_text = proposed if newline == "\n" else proposed.replace("\n", newline)
    proposed_raw = proposed_text.encode("utf-8")
    relative_target = str(target.resolve().relative_to(graph_root.resolve()))
    diff = "".join(
        difflib.unified_diff(
            source.splitlines(keepends=True),
            proposed.splitlines(keepends=True),
            fromfile=f"a/{relative_target}",
            tofile=f"b/{relative_target}",
        )
    )

    return {
        "schemaVersion": PREVIEW_SCHEMA_VERSION,
        "mode": "preview",
        "host": "logseq",
        "period": period["label"],
        "reviewKey": review_key(period),
        "targetPath": str(target),
        "targetRelativePath": relative_target,
        "operation": operation,
        "canApply": can_apply,
        "requiresExplicitConfirmation": True,
        "backupRequired": True,
        "sourceSha256": sha256_bytes(source_raw),
        "proposedSha256": sha256_bytes(proposed_raw),
        "preserves": [
            "page properties",
            "本月入口 / 本月项目 / 本月大事件 / 周入口",
            "迁移记录",
            "all content outside the managed review block",
            "legacy-source and legacy-archive references",
        ],
        "doesNotApply": [
            "objective or KR updates",
            "project status or Stage changes",
            "Work Item, 3 Things, Daily Doing, or To-do creation",
            "Dashboard mutations",
        ],
        "warnings": warnings,
        "diff": diff,
        "_sourceBytes": source_raw,
        "_proposedBytes": proposed_raw,
        "_target": target,
    }


def validate_backup_dir(backup_dir: Path, graph_root: Path) -> Path:
    expanded_backup = backup_dir.expanduser()
    if expanded_backup.exists() and expanded_backup.is_symlink():
        raise WritebackError("Refusing a symlinked backup directory.")
    backup = expanded_backup.resolve()
    graph = graph_root.expanduser().resolve()
    for protected in (graph / "pages", graph / "journals"):
        if is_within(backup, protected.resolve()):
            raise WritebackError(
                "Backup directory must be outside Logseq pages/ and journals/."
            )
    backup.mkdir(parents=True, exist_ok=True)
    return backup


def create_backup(target: Path, source: bytes, backup_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup_name = (
        f"{target.name}.{stamp}.{sha256_bytes(source)[:12]}.before-okr-review.bak"
    )
    backup_path = backup_dir / backup_name
    counter = 1
    while backup_path.exists():
        backup_path = backup_dir / f"{backup_name}.{counter}"
        counter += 1
    with backup_path.open("xb") as handle:
        handle.write(source)
        handle.flush()
        os.fsync(handle.fileno())
    return backup_path


def atomic_replace(target: Path, proposed: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.okr-review.",
        dir=target.parent,
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(proposed)
            handle.flush()
            os.fsync(handle.fileno())
        shutil.copymode(target, temporary_name)
        os.replace(temporary_name, target)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def apply_plan(
    plan: dict[str, Any],
    graph_root: Path,
    backup_dir: Path,
    expected_source_sha256: str,
    expected_proposed_sha256: str,
) -> dict[str, Any]:
    if not plan["canApply"]:
        raise WritebackError("Preview contains a conflict and cannot be applied.")
    if plan["sourceSha256"] != expected_source_sha256:
        raise WritebackError("Expected source hash does not match the preview.")
    if plan["proposedSha256"] != expected_proposed_sha256:
        raise WritebackError("Expected proposed hash does not match the preview.")

    target: Path = plan["_target"]
    current = target.read_bytes()
    if sha256_bytes(current) != expected_source_sha256:
        raise WritebackError(
            "The period page changed after preview. Generate a new preview first."
        )

    safe_backup_dir = validate_backup_dir(backup_dir, graph_root)
    backup_path = create_backup(target, current, safe_backup_dir)
    try:
        atomic_replace(target, plan["_proposedBytes"])
        verified = target.read_bytes()
        if sha256_bytes(verified) != expected_proposed_sha256:
            raise WritebackError("Post-write verification failed.")
    except Exception:
        if target.read_bytes() != current:
            atomic_replace(target, current)
        raise

    result = public_plan(plan)
    result.update(
        {
            "mode": "apply",
            "applied": True,
            "backupPath": str(backup_path),
            "verifiedSha256": sha256_bytes(verified),
        }
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or explicitly apply a confirmed OKR review to a Logseq period page."
        )
    )
    parser.add_argument("--graph", required=True, help="Authorized Logseq graph root.")
    parser.add_argument(
        "--period",
        required=True,
        help="YYYY-Www, YYYY-MM, YYYY-Qn, or YYYY.",
    )
    parser.add_argument(
        "--review-json",
        required=True,
        help="Confirmed okr-review/v1 one-page report JSON.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply only after reviewing the default preview.",
    )
    parser.add_argument("--backup-dir", help="Required for --apply.")
    parser.add_argument("--expected-source-sha256", help="Required for --apply.")
    parser.add_argument("--expected-proposed-sha256", help="Required for --apply.")
    parser.add_argument("--pretty", action="store_true")
    return parser


def emit(payload: dict[str, Any], pretty: bool) -> None:
    json.dump(
        payload,
        sys.stdout,
        ensure_ascii=False,
        indent=2 if pretty else None,
        sort_keys=pretty,
    )
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        graph = Path(args.graph).expanduser()
        plan = build_plan(
            graph,
            args.period,
            Path(args.review_json).expanduser(),
        )
        if not args.apply:
            emit(public_plan(plan), args.pretty)
            return 0

        missing = [
            name
            for name, value in (
                ("--backup-dir", args.backup_dir),
                ("--expected-source-sha256", args.expected_source_sha256),
                ("--expected-proposed-sha256", args.expected_proposed_sha256),
            )
            if not value
        ]
        if missing:
            raise WritebackError(
                f"{', '.join(missing)} required when --apply is used."
            )
        result = apply_plan(
            plan,
            graph,
            Path(args.backup_dir),
            args.expected_source_sha256,
            args.expected_proposed_sha256,
        )
        emit(result, args.pretty)
        return 0
    except (OSError, WritebackError) as error:
        emit(
            {
                "schemaVersion": PREVIEW_SCHEMA_VERSION,
                "mode": "apply" if args.apply else "preview",
                "canApply": False,
                "error": str(error),
            },
            args.pretty,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
