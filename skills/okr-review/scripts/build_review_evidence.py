#!/usr/bin/env python3
"""Build a read-only, traceable evidence pack for an OKR review period."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


MAX_BODY_CHARS = 4000
SKIP_PARTS = {".git", ".recycle", ".trash", ".zzz", "node_modules", "bak"}


@dataclass(frozen=True)
class Period:
    kind: str
    label: str
    start: date
    end: date

    def as_dict(self) -> dict[str, str]:
        return {
            "type": self.kind,
            "label": self.label,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
        }


def parse_period(raw: str) -> Period:
    raw = raw.strip()
    week_match = re.fullmatch(r"(\d{4})-W(\d{2})", raw, re.IGNORECASE)
    if week_match:
        year, week = map(int, week_match.groups())
        start = date.fromisocalendar(year, week, 1)
        end = date.fromisocalendar(year, week, 7)
        return Period("week", f"{year:04d}-W{week:02d}", start, end)

    month_match = re.fullmatch(r"(\d{4})-(\d{2})", raw)
    if month_match:
        year, month = map(int, month_match.groups())
        if not 1 <= month <= 12:
            raise ValueError(f"invalid month: {raw}")
        start = date(year, month, 1)
        if month == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, month + 1, 1).fromordinal(
                date(year, month + 1, 1).toordinal() - 1
            )
        return Period("month", f"{year:04d}-{month:02d}", start, end)

    quarter_match = re.fullmatch(r"(\d{4})-?Q([1-4])", raw, re.IGNORECASE)
    if quarter_match:
        year, quarter = map(int, quarter_match.groups())
        start_month = (quarter - 1) * 3 + 1
        start = date(year, start_month, 1)
        if quarter == 4:
            end = date(year, 12, 31)
        else:
            next_start = date(year, start_month + 3, 1)
            end = date.fromordinal(next_start.toordinal() - 1)
        return Period("quarter", f"{year:04d}-Q{quarter}", start, end)

    year_match = re.fullmatch(r"(\d{4})", raw)
    if year_match:
        year = int(year_match.group(1))
        return Period("year", f"{year:04d}", date(year, 1, 1), date(year, 12, 31))

    raise ValueError("period must be YYYY-Www, YYYY-MM, YYYY-Qn, or YYYY")


def parse_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    candidates = [raw, raw[:10]]
    for candidate in candidates:
        normalized = candidate.replace("_", "-").replace("/", "-")
        if re.fullmatch(r"\d{8}", normalized):
            normalized = f"{normalized[:4]}-{normalized[4:6]}-{normalized[6:]}"
        try:
            return date.fromisoformat(normalized)
        except ValueError:
            pass
    return None


def in_period(day: date | None, period: Period) -> bool:
    return day is not None and period.start <= day <= period.end


def intervals_overlap(
    start: date | None, end: date | None, period: Period
) -> bool:
    if start is None and end is None:
        return False
    start = start or end
    end = end or start
    assert start is not None and end is not None
    if end < start:
        start, end = end, start
    return start <= period.end and end >= period.start


def week_interval(label: str) -> tuple[date, date] | None:
    match = re.fullmatch(r"(\d{4})-W(\d{1,2})", label, re.IGNORECASE)
    if not match:
        return None
    try:
        year, week = map(int, match.groups())
        return date.fromisocalendar(year, week, 1), date.fromisocalendar(year, week, 7)
    except ValueError:
        return None


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        try:
            value = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            value = str(value)
    return re.sub(r"\s+", " ", value).strip()


def body_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    except TypeError:
        return str(value).strip()


def first_line(body: str, fallback: str) -> str:
    for line in body.splitlines():
        line = re.sub(r"^[#>*\-\s]+", "", line).strip()
        if line:
            return line[:160]
    return fallback


def bounded_body(body: str) -> tuple[str, bool]:
    body = body.strip()
    if len(body) <= MAX_BODY_CHARS:
        return body, False
    return body[:MAX_BODY_CHARS].rstrip() + "\n…", True


def stable_hash(*parts: Any) -> str:
    raw = "\x1f".join(normalize_text(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def source_ref(path: Path, suffix: str) -> str:
    return f"{path.resolve()}#{suffix}"


class EvidenceStore:
    def __init__(self, period: Period) -> None:
        self.period = period
        self.items: list[dict[str, Any]] = []
        self._seen: set[str] = set()
        self.warnings: list[str] = []
        self.metrics: dict[str, int] = {
            "weeklyReviewPlaceholders": 0,
        }

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)

    def add(
        self,
        *,
        source_type: str,
        occurred_at: date,
        title: str,
        body: str,
        source_reference: str,
        original_reference: str,
        stable_id: str = "",
        links: list[dict[str, Any]] | None = None,
        relations: dict[str, str] | None = None,
        date_precision: str = "day",
        interval_end: date | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not in_period(occurred_at, self.period) and not (
            interval_end
            and intervals_overlap(occurred_at, interval_end, self.period)
        ):
            return

        normalized_body = body.strip()
        if not title.strip() and not normalized_body:
            return

        identity = stable_id or stable_hash(
            source_type, occurred_at.isoformat(), title, normalized_body
        )
        dedupe_key = f"{source_type}:{identity}"
        if dedupe_key in self._seen:
            return
        self._seen.add(dedupe_key)

        excerpt, truncated = bounded_body(normalized_body)
        item_id = f"ev-{stable_hash(source_type, identity)}"
        item: dict[str, Any] = {
            "id": item_id,
            "occurredAt": occurred_at.isoformat(),
            "sourceType": source_type,
            "sourceRef": source_reference,
            "title": title.strip()[:240] or first_line(excerpt, source_type),
            "body": excerpt,
            "bodyTruncated": truncated,
            "links": links or [],
            "originalRecordRef": original_reference,
            "relations": {
                key: value
                for key, value in (relations or {}).items()
                if normalize_text(value)
            },
            "datePrecision": date_precision,
        }
        if interval_end:
            item["intervalEnd"] = interval_end.isoformat()
        if metadata:
            item["metadata"] = metadata
        self.items.append(item)

    def build_groups(self) -> dict[str, Any]:
        groups: dict[str, Any] = {
            "byWeek": {},
            "byProject": {},
            "byObjective": {},
            "byBigEvent": {},
            "unlinked": [],
        }
        for item in self.items:
            occurred = date.fromisoformat(item["occurredAt"])
            iso_year, iso_week, _ = occurred.isocalendar()
            week = f"{iso_year:04d}-W{iso_week:02d}"
            groups["byWeek"].setdefault(week, []).append(item["id"])

            relations = item.get("relations", {})
            project = relations.get("project")
            objective = relations.get("objective")
            event = relations.get("bigEvent")
            if project:
                groups["byProject"].setdefault(project, []).append(item["id"])
            if objective:
                groups["byObjective"].setdefault(objective, []).append(item["id"])
            if event:
                groups["byBigEvent"].setdefault(event, []).append(item["id"])
            if not any((project, objective, event)):
                groups["unlinked"].append(item["id"])

        for key in ("byWeek", "byProject", "byObjective", "byBigEvent"):
            groups[key] = {
                name: sorted(ids) for name, ids in sorted(groups[key].items())
            }
        groups["unlinked"].sort()
        return groups

    def coverage(self) -> dict[str, int]:
        mapping = {
            "daily": "daily",
            "weekly_thing": "weeklyThings",
            "todo": "todos",
            "weekly_review": "weeklyReviews",
            "project": "projects",
            "project_activity": "projects",
            "objective": "objectives",
            "big_event": "bigEvents",
            "markdown": "markdown",
        }
        coverage = {
            "daily": 0,
            "dailyUnlinked": 0,
            "weeklyThings": 0,
            "todos": 0,
            "todosDone": 0,
            "weeklyReviews": 0,
            "weeklyReviewPlaceholders": self.metrics["weeklyReviewPlaceholders"],
            "projects": 0,
            "objectives": 0,
            "bigEvents": 0,
            "markdown": 0,
        }
        for item in self.items:
            key = mapping.get(item["sourceType"], "markdown")
            coverage[key] += 1
            if item["sourceType"] == "daily" and not item.get("relations"):
                coverage["dailyUnlinked"] += 1
            if (
                item["sourceType"] == "todo"
                and item.get("metadata", {}).get("done") is True
            ):
                coverage["todosDone"] += 1
        return coverage


def read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def annual_for_year(data: dict[str, Any], year: int) -> tuple[dict[str, Any], str]:
    by_year = data.get("annualOkrByYear")
    if isinstance(by_year, dict) and isinstance(by_year.get(str(year)), dict):
        return by_year[str(year)], f"annualOkrByYear.{year}"
    legacy_key = f"annualOkr{year}"
    if isinstance(data.get(legacy_key), dict):
        return data[legacy_key], legacy_key
    return {}, ""


def relation_ids(record: dict[str, Any]) -> dict[str, str]:
    relations: dict[str, str] = {}
    context_links = record.get("contextLinks")
    if isinstance(context_links, list):
        for link in context_links:
            if not isinstance(link, dict):
                continue
            kind = normalize_text(link.get("type")).lower()
            link_id = normalize_text(link.get("id"))
            if kind in {"project", "program"} and link_id:
                relations["project"] = link_id
            elif kind in {"objective", "okr", "result", "kr"} and link_id:
                relations["objective"] = link_id
            elif kind in {"event", "big_event", "bigevent"} and link_id:
                relations["bigEvent"] = link_id

    relation_type = normalize_text(
        record.get("relationType") or record.get("linkType")
    ).lower()
    if relation_type == "project":
        relations.setdefault(
            "project",
            normalize_text(record.get("projectId") or record.get("targetId")),
        )
    if relation_type in {"objective", "okr", "result", "kr", "goal"}:
        relations.setdefault(
            "objective",
            normalize_text(record.get("resultId") or record.get("targetId")),
        )
    if relation_type == "event":
        relations.setdefault(
            "bigEvent",
            normalize_text(record.get("eventId") or record.get("targetId")),
        )

    direct_map = {
        "project": ("projectId", "programId"),
        "objective": ("resultId", "okrId", "oId"),
        "bigEvent": ("eventId",),
    }
    for target, keys in direct_map.items():
        for key in keys:
            value = normalize_text(record.get(key))
            if value:
                relations.setdefault(target, value)
                break
    return {key: value for key, value in relations.items() if value}


def collect_dashboard(
    path: Path, period: Period, store: EvidenceStore
) -> dict[str, Any]:
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"Dashboard export must be a JSON object: {path}")

    annual, annual_ref = annual_for_year(data, period.start.year)
    objectives = annual.get("os", []) if isinstance(annual, dict) else []
    if not isinstance(objectives, list):
        objectives = []

    for objective_index, objective in enumerate(objectives):
        if not isinstance(objective, dict):
            continue
        objective_id = normalize_text(objective.get("id")) or f"o-{objective_index}"
        objective_title = normalize_text(objective.get("title")) or objective_id
        daily_drafts = objective.get("dailyDoingDrafts", {})
        if isinstance(daily_drafts, dict):
            for day_label, day_record in sorted(daily_drafts.items()):
                day = parse_date(day_label)
                if not in_period(day, period) or not isinstance(day_record, dict):
                    continue
                entries = day_record.get("entries")
                if not isinstance(entries, list) or not entries:
                    fallback_body = body_text(
                        day_record.get("body") or day_record.get("advanced")
                    )
                    entries = (
                        [{"id": f"legacy-{day_label}", "body": fallback_body}]
                        if fallback_body
                        else []
                    )
                for entry_index, entry in enumerate(entries):
                    if not isinstance(entry, dict) or entry.get("deletedAt"):
                        continue
                    body = body_text(
                        entry.get("body") or entry.get("advanced")
                    )
                    if not body:
                        continue
                    entry_id = normalize_text(entry.get("id")) or (
                        f"{objective_id}-{day_label}-{entry_index}"
                    )
                    relations = relation_ids(entry)
                    original = (
                        f"{annual_ref}.os[{objective_id}].dailyDoingDrafts."
                        f"{day_label}.entries[{entry_id}]"
                    )
                    links = [
                        link
                        for link in entry.get("contextLinks", [])
                        if isinstance(link, dict)
                    ]
                    store.add(
                        source_type="daily",
                        occurred_at=day,
                        title=first_line(body, f"Daily Doing · {day_label}"),
                        body=body,
                        source_reference=source_ref(path, original),
                        original_reference=original,
                        stable_id=entry_id,
                        links=links,
                        relations=relations,
                        metadata={"objectiveTitle": objective_title},
                    )

        project_drafts = objective.get("projectDrafts", [])
        if isinstance(project_drafts, list):
            for index, project in enumerate(project_drafts):
                if not isinstance(project, dict):
                    continue
                start = parse_date(
                    project.get("timelineStart")
                    or project.get("date")
                    or project.get("createdAt")
                )
                end = parse_date(
                    project.get("timelineEnd")
                    or project.get("reviewedAt")
                    or project.get("snapshotAt")
                    or project.get("updatedAt")
                )
                month_matches = normalize_text(project.get("month")) == period.label
                if not intervals_overlap(start, end, period) and not month_matches:
                    continue
                occurred = end or start or period.start
                if occurred < period.start:
                    occurred = period.start
                elif occurred > period.end:
                    occurred = period.end
                project_id = normalize_text(
                    project.get("programId")
                    or project.get("resultId")
                    or project.get("id")
                ) or f"{objective_id}-project-{index}"
                title = normalize_text(
                    project.get("title")
                    or project.get("program")
                    or project.get("kr")
                ) or project_id
                body_fields = [
                    project.get("core"),
                    project.get("process"),
                    project.get("evidence"),
                    project.get("insights"),
                    project.get("personal"),
                    project.get("okrImpact"),
                    project.get("reusable"),
                ]
                body = "\n\n".join(
                    normalize_text(value) for value in body_fields if normalize_text(value)
                )
                original = f"{annual_ref}.os[{objective_id}].projectDrafts[{index}]"
                store.add(
                    source_type="project",
                    occurred_at=occurred,
                    interval_end=end,
                    title=title,
                    body=body or normalize_text(project),
                    source_reference=source_ref(path, original),
                    original_reference=original,
                    stable_id=project_id,
                    relations={
                        "project": project_id,
                        "objective": objective_id,
                    },
                    date_precision="interval" if start or end else "month",
                    metadata={"status": project.get("status", "")},
                )

        confidence_history = objective.get("confHistory", [])
        if isinstance(confidence_history, list):
            for index, item in enumerate(confidence_history):
                if not isinstance(item, dict):
                    continue
                occurred = parse_date(
                    item.get("createdAt")
                    or item.get("updatedAt")
                    or item.get("date")
                    or item.get("at")
                )
                if not in_period(occurred, period):
                    continue
                original = f"{annual_ref}.os[{objective_id}].confHistory[{index}]"
                body = normalize_text(
                    item.get("note") or item.get("reason") or item
                )
                store.add(
                    source_type="objective",
                    occurred_at=occurred,
                    title=f"{objective_title} · 判断变化",
                    body=body,
                    source_reference=source_ref(path, original),
                    original_reference=original,
                    stable_id=normalize_text(item.get("id"))
                    or stable_hash(objective_id, occurred, body),
                    relations={"objective": objective_id},
                )

    weekly_things = data.get("weeklyThingsByIso", {})
    if isinstance(weekly_things, dict):
        for week_label, things in sorted(weekly_things.items()):
            interval = week_interval(week_label)
            if not interval or not intervals_overlap(*interval, period):
                continue
            if not isinstance(things, list):
                continue
            for index, thing in enumerate(things):
                if not isinstance(thing, dict):
                    continue
                title = normalize_text(thing.get("title"))
                if not title:
                    continue
                occurred = parse_date(thing.get("backfillAt"))
                precision = "day"
                if not in_period(occurred, period):
                    occurred = max(interval[0], period.start)
                    precision = "week"
                thing_id = normalize_text(thing.get("id")) or stable_hash(
                    week_label, thing.get("no"), title
                )
                original = f"weeklyThingsByIso.{week_label}[{index}]"
                relations = relation_ids(thing.get("relations", {}))
                relations.update(
                    {
                        key: value
                        for key, value in relation_ids(thing).items()
                        if key not in relations
                    }
                )
                records = thing.get("records", [])
                record_text = "\n".join(
                    normalize_text(record.get("text") or record.get("title"))
                    for record in records
                    if isinstance(record, dict)
                    and normalize_text(record.get("text") or record.get("title"))
                )
                body = "\n".join(
                    value
                    for value in (
                        title,
                        normalize_text(thing.get("sub")),
                        record_text,
                    )
                    if value
                )
                store.add(
                    source_type="weekly_thing",
                    occurred_at=occurred,
                    title=title,
                    body=body,
                    source_reference=source_ref(path, original),
                    original_reference=original,
                    stable_id=thing_id,
                    relations=relations,
                    date_precision=precision,
                    metadata={
                        "week": week_label,
                        "done": bool(thing.get("done")),
                    },
                )

    routine_todos = data.get("routineTodosByIso", {})
    if isinstance(routine_todos, dict):
        for week_label, todos in sorted(routine_todos.items()):
            interval = week_interval(week_label)
            if not interval or not intervals_overlap(*interval, period):
                continue
            if not isinstance(todos, list):
                continue
            for index, todo in enumerate(todos):
                if not isinstance(todo, dict):
                    continue
                title = normalize_text(todo.get("title"))
                if not title:
                    continue
                occurred = parse_date(
                    todo.get("completedAt")
                    or todo.get("updatedAt")
                    or todo.get("createdAt")
                )
                precision = "day"
                if occurred and not in_period(occurred, period):
                    continue
                if occurred is None:
                    occurred = max(interval[0], period.start)
                    precision = "week"
                todo_id = normalize_text(todo.get("id")) or stable_hash(
                    week_label, title
                )
                original = f"routineTodosByIso.{week_label}[{index}]"
                store.add(
                    source_type="todo",
                    occurred_at=occurred,
                    title=title,
                    body=title,
                    source_reference=source_ref(path, original),
                    original_reference=original,
                    stable_id=todo_id,
                    relations=relation_ids(todo),
                    date_precision=precision,
                    metadata={
                        "week": week_label,
                        "done": bool(todo.get("done")),
                    },
                )

    reviews = data.get("reviewTimelineDrafts", {})
    if isinstance(reviews, dict):
        for key, review in sorted(reviews.items()):
            week_match = re.fullmatch(r"review:week:(\d{4}):(\d{1,2})", key)
            if not week_match or not isinstance(review, dict):
                continue
            week_label = f"{int(week_match.group(1)):04d}-W{int(week_match.group(2)):02d}"
            interval = week_interval(week_label)
            if not interval or not intervals_overlap(*interval, period):
                continue
            fields = review.get("fields")
            body = ""
            if isinstance(fields, dict):
                body = "\n".join(
                    f"{name}: {normalize_text(value)}"
                    for name, value in fields.items()
                    if normalize_text(value)
                )
            body = body or normalize_text(
                review.get("body") or review.get("reflection")
            )
            if not body and not normalize_text(review.get("updatedAt")):
                store.metrics["weeklyReviewPlaceholders"] += 1
                continue
            occurred = parse_date(review.get("updatedAt")) or min(
                interval[1], period.end
            )
            original = f"reviewTimelineDrafts.{key}"
            store.add(
                source_type="weekly_review",
                occurred_at=occurred,
                title=f"{week_label} 周复盘",
                body=body or "周复盘记录",
                source_reference=source_ref(path, original),
                original_reference=original,
                stable_id=key,
                date_precision="week",
                metadata={"week": week_label},
            )

    review_log = data.get("reviewLog")
    if isinstance(review_log, list):
        for index, review in enumerate(review_log):
            if not isinstance(review, dict):
                continue
            occurred = parse_date(
                review.get("date")
                or review.get("createdAt")
                or review.get("updatedAt")
            )
            if not in_period(occurred, period):
                continue
            body = normalize_text(
                review.get("body")
                or review.get("reflection")
                or review.get("content")
            )
            if not body:
                continue
            review_id = normalize_text(review.get("id")) or stable_hash(
                occurred, body
            )
            original = f"reviewLog[{index}]"
            store.add(
                source_type="weekly_review",
                occurred_at=occurred,
                title=first_line(body, "复盘记录"),
                body=body,
                source_reference=source_ref(path, original),
                original_reference=original,
                stable_id=review_id,
                relations=relation_ids(review),
            )

    events = data.get("bigEvents", [])
    if isinstance(events, list):
        for index, event in enumerate(events):
            if not isinstance(event, dict):
                continue
            start = parse_date(
                event.get("startedAt") or event.get("date") or event.get("createdAt")
            )
            end = parse_date(event.get("endedAt")) or start
            if not intervals_overlap(start, end, period):
                continue
            assert start is not None
            occurred = max(start, period.start)
            event_id = normalize_text(
                event.get("eventId") or event.get("id")
            ) or f"event-{index}"
            title = normalize_text(event.get("title")) or event_id
            original = f"bigEvents[{event_id}]"
            store.add(
                source_type="big_event",
                occurred_at=occurred,
                interval_end=end,
                title=title,
                body=normalize_text(
                    event.get("body")
                    or event.get("scope")
                    or event.get("description")
                    or title
                ),
                source_reference=source_ref(path, original),
                original_reference=original,
                stable_id=event_id,
                relations={"bigEvent": event_id},
                date_precision="interval",
            )

    if not annual_ref:
        store.warn(
            f"{path.name}: no annual OKR object found for {period.start.year}"
        )

    return {
        "type": "dashboard-json",
        "path": str(path.resolve()),
        "readOnly": True,
        "schemaVersion": data.get("schemaVersion"),
    }


PROJECT_COLLECTIONS = {
    "projects",
    "programs",
    "workItems",
    "work_items",
    "activities",
    "milestones",
    "assets",
    "evidence",
}


def iter_project_records(data: Any) -> Iterable[tuple[str, int, dict[str, Any]]]:
    if isinstance(data, list):
        for index, record in enumerate(data):
            if isinstance(record, dict):
                yield "records", index, record
        return
    if not isinstance(data, dict):
        return
    for collection, records in data.items():
        if collection not in PROJECT_COLLECTIONS or not isinstance(records, list):
            continue
        for index, record in enumerate(records):
            if isinstance(record, dict):
                yield collection, index, record


def record_interval(record: dict[str, Any]) -> tuple[date | None, date | None]:
    start = None
    end = None
    for key in ("occurredAt", "date", "startedAt", "startDate", "createdAt"):
        start = parse_date(record.get(key))
        if start:
            break
    for key in (
        "endedAt",
        "endDate",
        "completedAt",
        "updatedAt",
        "occurredAt",
        "date",
    ):
        end = parse_date(record.get(key))
        if end:
            break
    return start, end


def collect_project_json(
    path: Path, period: Period, store: EvidenceStore
) -> dict[str, Any]:
    data = read_json(path)
    found = 0
    for collection, index, record in iter_project_records(data):
        start, end = record_interval(record)
        if not intervals_overlap(start, end, period):
            continue
        occurred = start or end
        assert occurred is not None
        if occurred < period.start:
            occurred = period.start
        record_id = normalize_text(record.get("id")) or stable_hash(
            collection, index, record
        )
        title = normalize_text(
            record.get("title")
            or record.get("name")
            or record.get("label")
            or record.get("summary")
        ) or f"{collection} {index + 1}"
        body_values = [
            record.get("summary"),
            record.get("description"),
            record.get("body"),
            record.get("content"),
            record.get("result"),
            record.get("evidence"),
            record.get("status"),
        ]
        body = "\n\n".join(
            normalize_text(value) for value in body_values if normalize_text(value)
        )
        original = f"{collection}[{index}]"
        source_type = (
            "project"
            if collection in {"projects", "programs"}
            else "project_activity"
        )
        store.add(
            source_type=source_type,
            occurred_at=occurred,
            interval_end=end,
            title=title,
            body=body or normalize_text(record),
            source_reference=source_ref(path, original),
            original_reference=original,
            stable_id=record_id,
            relations=relation_ids(record),
            date_precision="interval" if start != end else "day",
            metadata={"collection": collection},
        )
        found += 1

    if found == 0:
        store.warn(
            f"{path.name}: no dated records found in supported project collections"
        )
    return {
        "type": "project-json",
        "path": str(path.resolve()),
        "readOnly": True,
    }


def markdown_roots(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    preferred = [root / "journals", root / "pages"]
    existing = [path for path in preferred if path.is_dir()]
    return existing or [root]


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for scan_root in markdown_roots(root):
        if scan_root.is_file():
            if scan_root.suffix.lower() == ".md":
                yield scan_root
            continue
        for path in scan_root.rglob("*.md"):
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            yield path


def extract_markdown_date(
    path: Path, text: str, period: Period
) -> tuple[date | None, str]:
    stem = path.stem
    for pattern in (
        r"(?<!\d)(\d{4})[_-](\d{2})[_-](\d{2})(?!\d)",
        r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)",
    ):
        match = re.search(pattern, stem)
        if match:
            try:
                return date(*map(int, match.groups())), "day"
            except ValueError:
                pass

    head = "\n".join(text.splitlines()[:100])
    property_match = re.search(
        r"(?im)^(?:date|created-at|created_at|updated-at|updated_at)::\s*([^\n]+)",
        head,
    )
    if property_match:
        parsed = parse_date(property_match.group(1))
        if parsed:
            return parsed, "day"

    period_match = re.search(r"(?im)^period::\s*([^\n]+)", head)
    period_value = period_match.group(1).strip() if period_match else stem
    normalized = period_value.replace(" ", "")

    month_match = re.search(r"(\d{4})[-年_]?(\d{1,2})(?:月)?", normalized)
    if month_match:
        year, month = map(int, month_match.groups())
        if 1 <= month <= 12:
            page_label = f"{year:04d}-{month:02d}"
            if period.kind == "month" and page_label == period.label:
                return period.start, "month"

    week_match = re.search(r"(\d{4})-?W(\d{1,2})", normalized, re.IGNORECASE)
    if week_match:
        interval = week_interval(
            f"{int(week_match.group(1)):04d}-W{int(week_match.group(2)):02d}"
        )
        if interval and intervals_overlap(*interval, period):
            return max(interval[0], period.start), "week"

    quarter_match = re.search(r"(\d{4})-?Q([1-4])", normalized, re.IGNORECASE)
    if quarter_match and period.kind == "quarter":
        label = f"{int(quarter_match.group(1)):04d}-Q{int(quarter_match.group(2))}"
        if label == period.label:
            return period.start, "quarter"

    if period.kind == "year" and re.search(rf"(?<!\d){period.label}(?!\d)", normalized):
        return period.start, "year"

    return None, ""


def classify_markdown(path: Path, text: str) -> str:
    lowered = f"{path.as_posix()}\n{text[:1200]}".lower()
    if "/journals/" in path.as_posix().lower():
        return "daily"
    if "class:: 大事件" in text or "大事件/" in path.as_posix():
        return "big_event"
    if "class:: project" in lowered or "/project/" in path.as_posix().lower():
        return "project"
    if re.search(r"(?i)\bweekly\b|周复盘|周\s*3\s*things", lowered):
        return "weekly_review"
    if "class:: okr" in lowered or " okr" in lowered or "okr " in lowered:
        return "objective"
    return "markdown"


def markdown_relations(text: str) -> dict[str, str]:
    relations: dict[str, str] = {}
    project = re.search(r"\[\[(?:Project/)?([^\]]+)\]\]", text, re.IGNORECASE)
    if project:
        relations["project"] = project.group(1).strip()
    objective = re.search(r"\[\[([^\]]*(?:OKR|OKRs)[^\]]*)\]\]", text, re.IGNORECASE)
    if objective:
        relations["objective"] = objective.group(1).strip()
    event = re.search(r"\[\[(?:大事件/)([^\]]+)\]\]", text)
    if event:
        relations["bigEvent"] = event.group(1).strip()
    return relations


def collect_logseq(
    root: Path, period: Period, store: EvidenceStore
) -> dict[str, Any]:
    matched = 0
    for path in sorted(set(iter_markdown_files(root))):
        try:
            if path.stat().st_size > 2_000_000:
                store.warn(f"{path}: skipped Markdown file larger than 2 MB")
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            store.warn(f"{path}: could not read Markdown ({exc})")
            continue
        occurred, precision = extract_markdown_date(path, text, period)
        if not in_period(occurred, period):
            continue
        assert occurred is not None
        source_type = classify_markdown(path, text)
        title = first_line(text, path.stem)
        relative = (
            str(path.resolve().relative_to(root.resolve()))
            if root.is_dir()
            else path.name
        )
        stable_id = stable_hash(path.resolve(), occurred, text)
        store.add(
            source_type=source_type,
            occurred_at=occurred,
            title=title,
            body=text,
            source_reference=str(path.resolve()),
            original_reference=relative,
            stable_id=stable_id,
            relations=markdown_relations(text),
            date_precision=precision,
        )
        matched += 1

    if matched == 0:
        store.warn(f"{root}: no dated Markdown records matched {period.label}")
    return {
        "type": "logseq-markdown",
        "path": str(root.resolve()),
        "readOnly": True,
    }


def validate_source(path_raw: str, expected: str) -> Path:
    path = Path(path_raw).expanduser().resolve()
    if expected == "file" and not path.is_file():
        raise ValueError(f"source file does not exist: {path}")
    if expected == "path" and not path.exists():
        raise ValueError(f"source path does not exist: {path}")
    return path


def generated_at() -> str:
    source_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if source_epoch:
        return datetime.fromtimestamp(int(source_epoch), tz=timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


def build_pack(args: argparse.Namespace) -> dict[str, Any]:
    period = parse_period(args.period)
    store = EvidenceStore(period)
    sources: list[dict[str, Any]] = []

    for raw in args.dashboard_json:
        path = validate_source(raw, "file")
        sources.append(collect_dashboard(path, period, store))
    for raw in args.project_json:
        path = validate_source(raw, "file")
        sources.append(collect_project_json(path, period, store))
    for raw in args.logseq_root:
        path = validate_source(raw, "path")
        sources.append(collect_logseq(path, period, store))

    if not sources:
        raise ValueError(
            "provide at least one --dashboard-json, --project-json, or --logseq-root"
        )

    store.items.sort(
        key=lambda item: (
            item["occurredAt"],
            item["sourceType"],
            item["title"],
            item["id"],
        )
    )
    return {
        "schemaVersion": 1,
        "generatedAt": generated_at(),
        "period": period.as_dict(),
        "sources": sources,
        "coverage": store.coverage(),
        "evidence": store.items,
        "groups": store.build_groups(),
        "warnings": sorted(store.warnings),
    }


def output_json(pack: dict[str, Any], args: argparse.Namespace) -> None:
    serialized = json.dumps(
        pack,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
        sort_keys=False,
    )
    if not args.output:
        print(serialized)
        return

    output = Path(args.output).expanduser().resolve()
    inputs = {
        Path(raw).expanduser().resolve()
        for raw in args.dashboard_json + args.project_json
    }
    if output in inputs:
        raise ValueError("output must not overwrite an input source")
    for raw in args.logseq_root:
        root = Path(raw).expanduser().resolve()
        if root.is_dir() and (output == root or root in output.parents):
            raise ValueError("output must not be placed inside a Logseq source root")
    if output.exists():
        raise ValueError(f"output already exists; refusing to overwrite: {output}")
    if not output.parent.is_dir():
        raise ValueError(f"output parent does not exist: {output.parent}")
    output.write_text(serialized + "\n", encoding="utf-8")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Build a read-only OKR review evidence pack."
    )
    result.add_argument(
        "--period",
        required=True,
        help="YYYY-Www, YYYY-MM, YYYY-Qn, or YYYY",
    )
    result.add_argument(
        "--dashboard-json",
        action="append",
        default=[],
        help="Dashboard draft export JSON; repeatable",
    )
    result.add_argument(
        "--project-json",
        action="append",
        default=[],
        help="Normalized project evidence JSON; repeatable",
    )
    result.add_argument(
        "--logseq-root",
        action="append",
        default=[],
        help="Authorized Logseq graph or Markdown path; repeatable",
    )
    result.add_argument(
        "--output",
        help="Optional new JSON destination outside all source roots",
    )
    result.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON",
    )
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        pack = build_pack(args)
        output_json(pack, args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
