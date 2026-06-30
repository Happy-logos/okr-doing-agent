import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "okr-assets-inventory"
    / "scripts"
    / "okr_assets_inventory.py"
)
spec = importlib.util.spec_from_file_location("okr_assets_inventory", SCRIPT_PATH)
inventory = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = inventory
spec.loader.exec_module(inventory)


class OkrAssetsInventoryTests(unittest.TestCase):
    def test_inventory_classifies_old_okr_assets(self):
        with tempfile.TemporaryDirectory() as old_system:
            root = Path(old_system)
            (root / "2026 年度 OKR.md").write_text("年度 OKR\nObjective\nKR", encoding="utf-8")
            (root / "Project" ).mkdir()
            (root / "Project" / "写书项目.md").write_text("项目 OKR\nObjective: 完成书稿", encoding="utf-8")
            (root / "2026-W26 周复盘.md").write_text("周复盘\nResult\nEvidence", encoding="utf-8")
            (root / "资源索引.md").write_text("课程资料和文章索引", encoding="utf-8")

            report = inventory.build_inventory(old_system)

        categories = {asset.path: asset.category for asset in report.assets}
        self.assertEqual(report.text_files_scanned, 4)
        self.assertEqual(categories["2026 年度 OKR.md"], "年度 OKR")
        self.assertEqual(categories["Project/写书项目.md"], "项目资产")
        self.assertEqual(categories["2026-W26 周复盘.md"], "周计划/周复盘")
        self.assertEqual(categories["资源索引.md"], "资源资料")

    def test_inventory_detects_target_graph_conflicts(self):
        with tempfile.TemporaryDirectory() as old_system, tempfile.TemporaryDirectory() as graph:
            old_root = Path(old_system)
            graph_pages = Path(graph) / "pages"
            graph_pages.mkdir()
            (old_root / "2026 年度 OKR.md").write_text("年度 OKR", encoding="utf-8")
            (graph_pages / "2026 OKRs.md").write_text("existing", encoding="utf-8")

            report = inventory.build_inventory(old_system, graph)

        self.assertEqual(len(report.conflicts), 1)
        self.assertEqual(report.conflicts[0].destination, "[[2026 OKRs]]")

    def test_cli_outputs_json_without_writing_source(self):
        with tempfile.TemporaryDirectory() as old_system:
            root = Path(old_system)
            (root / "十年计划.md").write_text("十年计划\n2021-2030", encoding="utf-8")
            before = sorted(path.relative_to(root) for path in root.rglob("*"))

            report = inventory.build_inventory(old_system)
            output = json.dumps(inventory.asdict(report), ensure_ascii=False)
            after = sorted(path.relative_to(root) for path in root.rglob("*"))

        self.assertIn("十年/长期规划", output)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
