import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "first_run_dry_run.py"
AGENT_ROOT = SCRIPT_PATH.parents[1]
spec = importlib.util.spec_from_file_location("first_run_dry_run", SCRIPT_PATH)
first_run = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = first_run
spec.loader.exec_module(first_run)


class FirstRunDryRunTests(unittest.TestCase):
    def test_preview_is_read_only(self):
        with tempfile.TemporaryDirectory() as graph:
            preview = first_run.build_preview(graph, year=2026, quarter=2, month=6, week=26)

        self.assertEqual(preview.mode, "dry-run")
        self.assertFalse(preview.writes_files)
        self.assertTrue(preview.can_apply)
        self.assertIn("dry-run 阶段不写入任何文件", preview.safety_checks)

    def test_first_prompt_only_asks_for_logseq_graph(self):
        self.assertEqual(first_run.FIRST_RUN_PROMPT, "你想把 OKR 系统安装到哪个 Logseq 图谱里？")
        forbidden = ["真实项目", "卡点", "为什么掉线", "最想接回"]
        for phrase in forbidden:
            self.assertNotIn(phrase, first_run.FIRST_RUN_PROMPT)

    def test_preview_generates_ten_year_okr_os_pages(self):
        with tempfile.TemporaryDirectory() as graph:
            preview = first_run.build_preview(graph, year=2026, quarter=2, month=6, week=26)
        titles = [page.title for page in preview.pages]

        self.assertIn("OKR Dashboard", titles)
        self.assertIn("OKR Templates", titles)
        self.assertIn("十年计划（2021-2030）", titles)
        self.assertIn("2026 OKRs", titles)
        for quarter in range(1, 5):
            self.assertIn(f"2026Q{quarter}", titles)
        for month in range(1, 13):
            self.assertIn(f"2026 {month}月", titles)
        self.assertIn("2026-W26", titles)

    def test_templates_are_not_regular_pages(self):
        with tempfile.TemporaryDirectory() as graph:
            preview = first_run.build_preview(graph, year=2026, quarter=2, month=6, week=26)

        page_titles = [page.title for page in preview.pages]
        template_titles = [template.title for template in preview.templates]
        on_demand_titles = [page.title for page in preview.on_demand_pages]

        self.assertNotIn("项目 OKR 模板", page_titles)
        self.assertNotIn("大事件模板", page_titles)
        self.assertNotIn("daily routine 模板", page_titles)
        self.assertIn("十年计划", template_titles)
        self.assertIn("年度 OKR", template_titles)
        self.assertIn("项目 OKR", template_titles)
        self.assertIn("大事件", template_titles)
        self.assertIn("daily routine", template_titles)
        self.assertIn("周复盘", template_titles)
        self.assertIn("后续十年计划（YYYY-YYYY）", on_demand_titles)
        self.assertIn("后续 YYYY OKRs", on_demand_titles)
        self.assertIn("Project/<项目名>", on_demand_titles)
        self.assertIn("大事件/<事件名>", on_demand_titles)

    def test_preview_detects_existing_decade_page(self):
        with tempfile.TemporaryDirectory() as graph:
            pages_dir = Path(graph) / "pages"
            pages_dir.mkdir()
            (pages_dir / "庚子十年（2021-2030）.md").write_text(
                "class:: 十年计划\nperiod:: 2021-2030\nrelated:: [[OKR]]",
                encoding="utf-8",
            )

            preview = first_run.build_preview(graph, year=2026, quarter=2, month=6, week=26)

        self.assertEqual(preview.decade_title, "庚子十年（2021-2030）")
        self.assertIn("庚子十年（2021-2030）", [page.title for page in preview.pages])

    def test_all_referenced_templates_exist(self):
        with tempfile.TemporaryDirectory() as graph:
            preview = first_run.build_preview(graph, year=2026, quarter=2, month=6, week=26)

        template_paths = []
        template_paths.extend(page.source_template for page in preview.pages if page.source_template)
        template_paths.extend(template.source_template for template in preview.templates)
        template_paths.extend(page.source_template for page in preview.on_demand_pages if page.source_template)

        for template_path in template_paths:
            self.assertTrue((AGENT_ROOT / template_path).exists(), template_path)

    def test_apply_writes_system_pages_and_template_library(self):
        with tempfile.TemporaryDirectory() as graph:
            preview = first_run.build_preview(graph, year=2026, quarter=2, month=6, week=26)
            result = first_run.apply_install(preview, agent_root=AGENT_ROOT)

            pages_dir = Path(graph) / "pages"
            dashboard = pages_dir / "OKR Dashboard.md"
            template_library = pages_dir / "OKR Templates.md"
            annual = pages_dir / "2026 OKRs.md"
            q4 = pages_dir / "2026Q4.md"
            december = pages_dir / "2026 12月.md"
            current_week = pages_dir / "2026-W26.md"

            self.assertTrue(dashboard.exists())
            self.assertTrue(template_library.exists())
            self.assertTrue(annual.exists())
            self.assertTrue(q4.exists())
            self.assertTrue(december.exists())
            self.assertTrue(current_week.exists())
            self.assertFalse((pages_dir / "Project___<项目名>.md").exists())
            self.assertFalse((pages_dir / "大事件___<事件名>.md").exists())

            dashboard_text = dashboard.read_text(encoding="utf-8")
            library_text = template_library.read_text(encoding="utf-8")

        self.assertEqual(result.mode, "apply")
        self.assertTrue(result.writes_files)
        self.assertIn("[[十年计划（2021-2030）]]", dashboard_text)
        self.assertNotIn("{{", dashboard_text)
        self.assertIn("template:: 十年计划", library_text)
        self.assertIn("template:: 年度 OKR", library_text)
        self.assertIn("template:: 项目 OKR", library_text)
        self.assertNotIn("template:: 项目OKR", library_text)
        self.assertIn("template:: 大事件", library_text)
        self.assertIn("template:: daily routine", library_text)
        self.assertIn("template:: 周复盘", library_text)
        self.assertNotIn("{{", library_text)

    def test_template_library_blocks_are_logseq_callable(self):
        with tempfile.TemporaryDirectory() as graph:
            preview = first_run.build_preview(graph, year=2026, quarter=2, month=6, week=26)
            first_run.apply_install(preview, agent_root=AGENT_ROOT)
            library_text = (Path(graph) / "pages" / "OKR Templates.md").read_text(encoding="utf-8")

        for title in ["十年计划", "年度 OKR", "项目 OKR", "大事件", "daily routine", "周复盘"]:
            self.assertIn(f"- {title}\n\ttemplate:: {title}", library_text)
        self.assertEqual(library_text.count("template:: "), 6)
        self.assertEqual(library_text.count("template-including-parent:: false"), 6)
        self.assertIn("period:: 2021-2030", library_text)
        self.assertIn("period:: 2026", library_text)
        self.assertIn("date-started:: <% today %>", library_text)
        self.assertIn("date:: <% today %>", library_text)
        self.assertIn("due:: <% today %>", library_text)

    def test_apply_stops_when_conflicts_exist(self):
        with tempfile.TemporaryDirectory() as graph:
            pages_dir = Path(graph) / "pages"
            pages_dir.mkdir()
            existing = pages_dir / "OKR Dashboard.md"
            existing.write_text("existing page", encoding="utf-8")

            preview = first_run.build_preview(graph, year=2026, quarter=2, month=6, week=26)
            with self.assertRaises(RuntimeError):
                first_run.apply_install(preview, agent_root=AGENT_ROOT)

            self.assertEqual(existing.read_text(encoding="utf-8"), "existing page")

    def test_rendered_preview_does_not_start_project_intake(self):
        with tempfile.TemporaryDirectory() as graph:
            preview = first_run.build_preview(graph, year=2026, quarter=2, month=6, week=26)
            text = first_run.render_markdown(preview)

        forbidden = ["你现在最想接回生活的一件事是什么", "它最近为什么掉线了", "当前卡点"]
        for phrase in forbidden:
            self.assertNotIn(phrase, text)
        self.assertIn("系统已经装好了。现在要不要把一件想做的事接进来？", text)

    def test_preview_detects_existing_logseq_pages(self):
        with tempfile.TemporaryDirectory() as graph:
            pages_dir = Path(graph) / "pages"
            pages_dir.mkdir()
            existing = pages_dir / "OKR Dashboard.md"
            existing.write_text("existing page", encoding="utf-8")

            preview = first_run.build_preview(graph, year=2026, quarter=2, month=6, week=26)

        self.assertFalse(preview.can_apply)
        self.assertEqual(len(preview.conflicts), 1)
        self.assertEqual(preview.conflicts[0].title, "OKR Dashboard")
        self.assertEqual(preview.conflicts[0].existing_path, str(existing))

    def test_template_named_pages_do_not_block_system_install(self):
        with tempfile.TemporaryDirectory() as graph:
            pages_dir = Path(graph) / "pages"
            pages_dir.mkdir()
            (pages_dir / "项目 OKR 模板.md").write_text("old personal template page", encoding="utf-8")

            preview = first_run.build_preview(graph, year=2026, quarter=2, month=6, week=26)

        self.assertTrue(preview.can_apply)
        self.assertEqual(preview.conflicts, [])

    def test_conflict_preview_stops_before_apply_language(self):
        with tempfile.TemporaryDirectory() as graph:
            pages_dir = Path(graph) / "pages"
            pages_dir.mkdir()
            (pages_dir / "2026 OKRs.md").write_text("existing page", encoding="utf-8")

            preview = first_run.build_preview(graph, year=2026, quarter=2, month=6, week=26)
            text = first_run.render_markdown(preview)

        self.assertIn("是否可直接写入：否", text)
        self.assertIn("发现同名页面冲突", text)
        self.assertIn("请先处理以上系统页面冲突，再继续写入。", text)
        self.assertNotIn("确认后才会执行", text)
        self.assertNotIn("系统已经装好了", text)


if __name__ == "__main__":
    unittest.main()
