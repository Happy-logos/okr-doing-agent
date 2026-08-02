import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).parents[1]
    / "skills"
    / "okr-review"
    / "scripts"
    / "build_review_evidence.py"
)
SPEC = importlib.util.spec_from_file_location("build_review_evidence", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ReviewEvidenceTests(unittest.TestCase):
    def test_dashboard_month_boundary_and_alias_deduplication(self):
        annual = {
            "os": [
                {
                    "id": "o-1",
                    "title": "年度目标",
                    "dailyDoingDrafts": {
                        "2026-07-31": {
                            "entries": [
                                {
                                    "id": "daily-july",
                                    "body": "完成 7 月交付",
                                    "relationType": "project",
                                    "targetId": "project-1",
                                }
                            ]
                        },
                        "2026-08-01": {
                            "entries": [
                                {
                                    "id": "daily-august",
                                    "body": "8 月记录不得进入 7 月",
                                }
                            ]
                        },
                    },
                    "projectDrafts": [],
                    "confHistory": [],
                }
            ]
        }
        payload = {
            "schemaVersion": 9,
            "annualOkr2026": annual,
            "annualOkrByYear": {"2026": annual},
            "weeklyThingsByIso": {
                "2026-W31": [
                    {
                        "title": "完成月末交付",
                        "backfillAt": "2026-07-31",
                        "relations": {"projectId": "project-1"},
                    }
                ]
            },
            "routineTodosByIso": {
                "2026-W31": [
                    {
                        "id": "todo-1",
                        "title": "完成运营责任",
                        "done": True,
                        "createdAt": "2026-07-30",
                    }
                ]
            },
            "reviewTimelineDrafts": {},
            "bigEvents": [
                {
                    "eventId": "event-1",
                    "title": "跨月事件",
                    "startedAt": "2026-07-30",
                    "endedAt": "2026-08-02",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "dashboard.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            period = MODULE.parse_period("2026-07")
            store = MODULE.EvidenceStore(period)
            MODULE.collect_dashboard(path, period, store)

        source_types = [item["sourceType"] for item in store.items]
        bodies = [item["body"] for item in store.items]
        self.assertEqual(source_types.count("daily"), 1)
        self.assertIn("完成 7 月交付", bodies)
        self.assertNotIn("8 月记录不得进入 7 月", bodies)
        self.assertEqual(source_types.count("weekly_thing"), 1)
        self.assertEqual(source_types.count("todo"), 1)
        self.assertEqual(source_types.count("big_event"), 1)

    def test_logseq_scan_is_read_only_and_period_limited(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            journals = root / "journals"
            pages = root / "pages"
            journals.mkdir()
            pages.mkdir()
            july = journals / "2026_07_15.md"
            august = journals / "2026_08_01.md"
            month = pages / "2026 7月.md"
            july.write_text("- 完成真实工作\n- [[Project/Alpha]]", encoding="utf-8")
            august.write_text("- 8 月记录", encoding="utf-8")
            month.write_text(
                "period:: 2026-07\n\n## 月度复盘\n\n保持原文。",
                encoding="utf-8",
            )
            before = {
                path: path.read_bytes()
                for path in (july, august, month)
            }

            period = MODULE.parse_period("2026-07")
            store = MODULE.EvidenceStore(period)
            MODULE.collect_logseq(root, period, store)

            after = {
                path: path.read_bytes()
                for path in (july, august, month)
            }

        self.assertEqual(before, after)
        self.assertEqual(len(store.items), 2)
        self.assertTrue(any("完成真实工作" in item["body"] for item in store.items))
        self.assertFalse(any("8 月记录" in item["body"] for item in store.items))
        self.assertTrue(
            any(
                item["relations"].get("project") == "Alpha"
                for item in store.items
            )
        )

    def test_project_json_is_a_separate_dated_evidence_source(self):
        payload = {
            "workItems": [
                {
                    "id": "work-1",
                    "title": "完成项目阶段设计",
                    "completedAt": "2026-07-20",
                    "projectId": "project-dashboard",
                    "result": "形成 Stage 定义",
                }
            ],
            "assets": [
                {
                    "id": "asset-august",
                    "title": "8 月资产",
                    "createdAt": "2026-08-01",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "projects.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            period = MODULE.parse_period("2026-07")
            store = MODULE.EvidenceStore(period)
            MODULE.collect_project_json(path, period, store)

        self.assertEqual(len(store.items), 1)
        self.assertEqual(store.items[0]["sourceType"], "project_activity")
        self.assertEqual(
            store.items[0]["relations"].get("project"),
            "project-dashboard",
        )
        self.assertIn("形成 Stage 定义", store.items[0]["body"])

    def test_output_refuses_existing_or_source_root_destination(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.json"
            source.write_text("{}", encoding="utf-8")
            pack = {"schemaVersion": 1}

            args = type(
                "Args",
                (),
                {
                    "pretty": False,
                    "output": str(source),
                    "dashboard_json": [str(source)],
                    "project_json": [],
                    "logseq_root": [],
                },
            )()
            with self.assertRaises(ValueError):
                MODULE.output_json(pack, args)


if __name__ == "__main__":
    unittest.main()
