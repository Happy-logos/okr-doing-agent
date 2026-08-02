import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).parents[1]
    / "skills"
    / "okr-review"
    / "scripts"
    / "write_review_logseq.py"
)
SPEC = importlib.util.spec_from_file_location("write_review_logseq", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def review_payload(**overrides):
    payload = {
        "schemaVersion": "okr-review/v1",
        "period": {"type": "month", "label": "2026-07"},
        "status": "confirmed",
        "confirmedAt": "2026-07-31T18:30:00+08:00",
        "onePage": {
            "facts": ["完成了系统结构搭建。"],
            "coachInsights": ["主要变化是从碎片推进走向 Stage 承重结构。"],
            "lookback": ["我开始能说清楚项目为什么混乱。"],
            "judgments": ["结构已形成，证据连接尚未跟上。"],
            "nextActions": ["补项目阶段设计事项与资产。"],
            "modelUpdates": ["下月验证最小证据连接契约。"],
            "evidenceRefs": ["[[2026-W27]]", "[[2026-W31]]"],
            "chapterTitle": "结构长出来的一个月",
        },
    }
    payload.update(overrides)
    return payload


def month_page(review_block=None):
    if review_block is None:
        review_block = (
            "- ## 月度复盘\n"
            "\t- 做到了什么：\n"
            "\t- 没做到什么：\n"
            "\t- 新证据是什么：\n"
            "\t- 判断如何更新：\n"
            "\t- 下月第一步：\n"
        )
    return (
        "class:: OKR, 月度计划\n"
        "alias:: 2026年7月 OKR\n"
        "parent:: [[2026 OKRs]]\n"
        "quarter:: [[2026Q3]]\n"
        "period:: 2026-M7\n"
        "legacy-source:: /private/legacy/2026 July 7月.md\n"
        "legacy-archive:: [[zzz_旧2026 July 7月]]\n"
        "\n"
        "- ## 本月入口\n"
        "\t- 年度 OKR:: [[2026 OKRs]]\n"
        "- ## 本月项目\n"
        "\t- 真正在推进的项目：[[OKR Doing Dashboard]]\n"
        "- ## 本月大事件\n"
        "\t- [[持续照护与恢复]]\n"
        "- ## 周入口\n"
        "\t- [[2026-W27]]\n"
        f"{review_block}"
        "- ## 迁移记录\n"
        "\t- 保留原始迁移说明。\n"
    )


class LogseqReviewWritebackTests(unittest.TestCase):
    def make_graph(self, root: Path, page_text=None):
        pages = root / "graph" / "pages"
        pages.mkdir(parents=True)
        page = pages / "2026 7月.md"
        page.write_text(
            month_page() if page_text is None else page_text,
            encoding="utf-8",
        )
        review = root / "review.json"
        review.write_text(
            json.dumps(review_payload(), ensure_ascii=False),
            encoding="utf-8",
        )
        return root / "graph", page, review

    def test_preview_replaces_only_empty_placeholder_and_is_read_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            graph, page, review = self.make_graph(Path(temp_dir))
            before = page.read_bytes()
            plan = MODULE.build_plan(graph, "2026-07", review)

            self.assertEqual(before, page.read_bytes())
            self.assertTrue(plan["canApply"])
            self.assertEqual(plan["operation"], "replace-empty-placeholder")
            self.assertIn("review-key:: review:month:2026:7", plan["diff"])
            self.assertNotIn("-legacy-source::", plan["diff"])
            self.assertNotIn("\n-- ## 迁移记录", plan["diff"])

    def test_confirmed_apply_creates_backup_and_preserves_surrounding_page(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            graph, page, review = self.make_graph(root)
            before = page.read_bytes()
            plan = MODULE.build_plan(graph, "2026-07", review)
            result = MODULE.apply_plan(
                plan,
                graph,
                root / "backups",
                plan["sourceSha256"],
                plan["proposedSha256"],
            )
            written = page.read_text(encoding="utf-8")

            self.assertTrue(result["applied"])
            self.assertEqual(
                Path(result["backupPath"]).read_bytes(),
                before,
            )
            self.assertIn("legacy-source:: /private/legacy/", written)
            self.assertIn("- ## 本月入口", written)
            self.assertIn("- ## 迁移记录", written)
            self.assertIn("review-status:: confirmed", written)
            self.assertIn("### Coach 洞察", written)
            self.assertIn("### 我的回看", written)
            self.assertIn("### 下一步行动", written)
            self.assertNotIn("\t\t- TODO ", written)

    def test_update_is_idempotent_and_preserves_created_at(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            graph, page, review = self.make_graph(root)
            first = MODULE.build_plan(graph, "2026-07", review)
            MODULE.apply_plan(
                first,
                graph,
                root / "backups",
                first["sourceSha256"],
                first["proposedSha256"],
            )

            changed = review_payload(
                confirmedAt="2026-08-01T09:00:00+08:00",
                updatedAt="2026-08-01T09:00:00+08:00",
            )
            changed["onePage"]["judgments"] = ["新的已确认判断。"]
            review.write_text(
                json.dumps(changed, ensure_ascii=False),
                encoding="utf-8",
            )
            second = MODULE.build_plan(graph, "2026-07", review)
            MODULE.apply_plan(
                second,
                graph,
                root / "backups",
                second["sourceSha256"],
                second["proposedSha256"],
            )
            written = page.read_text(encoding="utf-8")

            self.assertEqual(second["operation"], "update-managed-review")
            self.assertEqual(
                written.count("review-key:: review:month:2026:7"),
                1,
            )
            self.assertIn(
                "review-created-at:: 2026-07-31T18:30:00+08:00",
                written,
            )
            self.assertIn(
                "review-updated-at:: 2026-08-01T09:00:00+08:00",
                written,
            )
            self.assertIn("新的已确认判断。", written)

    def test_apply_refuses_source_hash_change(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            graph, page, review = self.make_graph(root)
            plan = MODULE.build_plan(graph, "2026-07", review)
            page.write_text(
                page.read_text(encoding="utf-8") + "- 用户刚刚新增的内容\n",
                encoding="utf-8",
            )

            with self.assertRaises(MODULE.WritebackError):
                MODULE.apply_plan(
                    plan,
                    graph,
                    root / "backups",
                    plan["sourceSha256"],
                    plan["proposedSha256"],
                )
            self.assertFalse((root / "backups").exists())

    def test_user_authored_review_without_key_is_not_overwritten(self):
        custom_review = (
            "- ## 月度复盘\n"
            "\t- 这是用户自己写的复盘，不允许覆盖。\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            graph, page, review = self.make_graph(
                Path(temp_dir),
                month_page(custom_review),
            )
            before = page.read_bytes()
            plan = MODULE.build_plan(graph, "2026-07", review)

            self.assertFalse(plan["canApply"])
            self.assertEqual(plan["operation"], "conflict-user-content")
            self.assertEqual(before, page.read_bytes())

    def test_multiple_period_pages_are_a_conflict(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            graph, _, review = self.make_graph(root)
            duplicate = graph / "pages" / "July duplicate.md"
            duplicate.write_text(
                "period:: 2026-07\n\n- ## 月度复盘\n",
                encoding="utf-8",
            )

            with self.assertRaises(MODULE.WritebackError):
                MODULE.build_plan(graph, "2026-07", review)

    def test_multiple_review_blocks_are_a_conflict(self):
        duplicate_blocks = month_page() + (
            "- ## 月度复盘\n"
            "\t- 做到了什么：\n"
            "\t- 没做到什么：\n"
            "\t- 新证据是什么：\n"
            "\t- 判断如何更新：\n"
            "\t- 下月第一步：\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            graph, _, review = self.make_graph(
                Path(temp_dir),
                duplicate_blocks,
            )
            plan = MODULE.build_plan(graph, "2026-07", review)

            self.assertFalse(plan["canApply"])
            self.assertEqual(
                plan["operation"],
                "conflict-multiple-review-blocks",
            )

    def test_installed_not_started_block_is_updated_in_place(self):
        not_started = (
            "- ## 月度复盘\n"
            "\treview-key:: review:month:2026:7\n"
            "\treview-schema:: okr-review/v1\n"
            "\treview-status:: not-started\n"
            "\tartifact:: 复盘一页纸\n"
            "\t- 月底可调用 `okr-review`。\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            graph, _, review = self.make_graph(
                Path(temp_dir),
                month_page(not_started),
            )
            plan = MODULE.build_plan(graph, "2026-07", review)

            self.assertTrue(plan["canApply"])
            self.assertEqual(plan["operation"], "update-managed-review")
            self.assertIn("+\treview-status:: confirmed", plan["diff"])

    def test_missing_review_block_is_inserted_before_migration_record(self):
        page_without_review = month_page("")
        with tempfile.TemporaryDirectory() as temp_dir:
            graph, _, review = self.make_graph(
                Path(temp_dir),
                page_without_review,
            )
            plan = MODULE.build_plan(graph, "2026-07", review)
            proposed = plan["_proposedBytes"].decode("utf-8")

            self.assertTrue(plan["canApply"])
            self.assertEqual(plan["operation"], "insert-managed-review")
            self.assertLess(
                proposed.index("- ## 月度复盘"),
                proposed.index("- ## 迁移记录"),
            )

    def test_cli_preview_and_apply_use_the_same_reviewed_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            graph, page, review = self.make_graph(root)
            preview_output = io.StringIO()
            with redirect_stdout(preview_output):
                preview_code = MODULE.main(
                    [
                        "--graph",
                        str(graph),
                        "--period",
                        "2026-07",
                        "--review-json",
                        str(review),
                    ]
                )
            preview = json.loads(preview_output.getvalue())
            self.assertEqual(preview_code, 0)
            self.assertTrue(preview["canApply"])

            apply_output = io.StringIO()
            with redirect_stdout(apply_output):
                apply_code = MODULE.main(
                    [
                        "--graph",
                        str(graph),
                        "--period",
                        "2026-07",
                        "--review-json",
                        str(review),
                        "--apply",
                        "--backup-dir",
                        str(root / "backups"),
                        "--expected-source-sha256",
                        preview["sourceSha256"],
                        "--expected-proposed-sha256",
                        preview["proposedSha256"],
                    ]
                )
            applied = json.loads(apply_output.getvalue())

            self.assertEqual(apply_code, 0)
            self.assertTrue(applied["applied"])
            self.assertEqual(
                MODULE.sha256_bytes(page.read_bytes()),
                preview["proposedSha256"],
            )

    def test_backup_inside_pages_is_refused(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            graph, _, review = self.make_graph(root)
            plan = MODULE.build_plan(graph, "2026-07", review)

            with self.assertRaises(MODULE.WritebackError):
                MODULE.apply_plan(
                    plan,
                    graph,
                    graph / "pages" / "backups",
                    plan["sourceSha256"],
                    plan["proposedSha256"],
                )


if __name__ == "__main__":
    unittest.main()
