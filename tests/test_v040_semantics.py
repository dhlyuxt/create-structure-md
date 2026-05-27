import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.v040_package import load_manifest_package
from scripts.v040_semantics import semantic_validation_result
from tests.helpers_v040 import write_json, write_valid_package


class V040SemanticTests(unittest.TestCase):
    def validate(self, mutator=None, *, include_mermaid=False):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir, include_mermaid=include_mermaid)
            if mutator:
                mutator(Path(tmpdir))
            package = load_manifest_package(manifest_path)
            return semantic_validation_result(package)

    def test_valid_fixture_has_no_semantic_errors(self):
        result = self.validate()

        self.assertEqual([], [issue.format() for issue in result.errors])

    def test_warns_when_more_than_three_main_flows_are_selected(self):
        def mutate(root):
            data = _read(root / "chapters/04-main-flows.json")
            flow = data["main_flows"]["flows"][0]
            data["main_flows"]["flows"] = [
                {**flow, "title": f"主线 {index}"} for index in range(4)
            ]
            write_json(root / "chapters/04-main-flows.json", data)

        result = self.validate(mutate)

        self.assertWarningCode(result, "semantics.main_flows.too_many")

    def test_warns_when_module_entry_looks_like_file_only_listing(self):
        def mutate(root):
            data = _read(root / "chapters/05-module-details.json")
            data["module_details"]["modules"][0].update(
                {
                    "name": "src/storage.py",
                    "purpose": "src/storage.py",
                    "blocks": [],
                    "mechanisms": [],
                }
            )
            write_json(root / "chapters/05-module-details.json", data)

        result = self.validate(mutate)

        self.assertWarningCode(result, "semantics.module.file_only")

    def test_errors_when_process_metadata_appears_in_text_content(self):
        def mutate(root):
            data = _read(root / "chapters/01-overview.json")
            data["overview"]["repository_intro"]["blocks"][0][
                "content"
            ] = "subagent report: implementation notes"
            write_json(root / "chapters/01-overview.json", data)

        result = self.validate(mutate)

        self.assertErrorCode(result, "semantics.process_metadata")

    def test_errors_when_process_metadata_appears_in_extra_subsection_title(self):
        def mutate(root):
            data = _read(root / "chapters/01-overview.json")
            data["overview"]["extra_subsections"].append(
                {
                    "key": "execution_notes",
                    "title": "执行记录",
                    "blocks": [{"type": "text", "content": "reader-facing note"}],
                }
            )
            write_json(root / "chapters/01-overview.json", data)

        result = self.validate(mutate)

        self.assertErrorCode(result, "semantics.process_metadata")

    def test_warns_when_mermaid_block_source_uses_legacy_graph(self):
        def mutate(root):
            data = _read(root / "chapters/01-overview.json")
            data["overview"]["repository_intro"]["blocks"][-1][
                "source"
            ] = "graph LR\n  app[应用] --> api[公共 API]"
            write_json(root / "chapters/01-overview.json", data)

        result = self.validate(mutate, include_mermaid=True)

        self.assertWarningCode(result, "semantics.mermaid.legacy_graph")

    def test_warns_when_mermaid_visible_labels_expose_internal_ids(self):
        def mutate(root):
            data = _read(root / "chapters/01-overview.json")
            data["overview"]["repository_intro"]["blocks"][-1][
                "source"
            ] = "flowchart LR\n  api_node[api_node] --> ui[用户界面]"
            write_json(root / "chapters/01-overview.json", data)

        result = self.validate(mutate, include_mermaid=True)

        self.assertWarningCode(result, "semantics.mermaid.internal_label")

    def test_warns_when_source_like_locations_are_missing_under_repo_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = write_valid_package(tmpdir)
            package = load_manifest_package(manifest_path)

            result = semantic_validation_result(package, repo_root=tmpdir)

        missing_location_paths = {
            issue.path
            for issue in result.warnings
            if issue.code == "semantics.location.missing"
        }
        self.assertEqual(
            {
                "$.overview.overview.core_components.component_table.rows[0].location",
                "$.architecture_overview.architecture_overview.layers.layer_table.rows[0].location",
                "$.architecture_overview.architecture_overview.module_map.module_table.rows[0].location",
                "$.main_flows.main_flows.flows[0].entry.location",
                "$.module_details.module_details.modules[0].location",
            },
            missing_location_paths,
        )

    def assertErrorCode(self, result, code):
        self.assertTrue(
            any(issue.code == code for issue in result.errors),
            [issue.format() for issue in result.errors],
        )

    def assertWarningCode(self, result, code):
        self.assertTrue(
            any(issue.code == code for issue in result.warnings),
            [issue.format() for issue in result.warnings],
        )


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
